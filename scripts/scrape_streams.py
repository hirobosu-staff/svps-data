"""各選手の YouTube ライブ配信アーカイブを1本ずつ取得し、data/streams.json に貯める。

選手詳細ページ（player.html）の「配信分析」（配信頻度・配信時間・再生数・タイトル）の元データ。

取得方法:
    1. チャンネルの「ライブ」タブ  https://www.youtube.com/channel/{id}/streams?hl=ja&gl=JP
       ページに埋め込まれた ytInitialData から、直近30本の動画ID・タイトル・長さを読む。
       初回だけは続き（continuation）をたどって、1年前より新しい配信までさかのぼる。
    2. 各配信の詳細（正確な開始・終了時刻、長さ、再生数）
       環境変数 YOUTUBE_API_KEY があれば YouTube Data API の videos.list（50本ずつ、1回1ユニット）で取る。
       無ければ視聴ページ（/watch?v=）の ytInitialPlayerResponse を読む。ただし GitHub Actions からは
       YouTube にボットと判定されて LOGIN_REQUIRED が返り、取れなかった（2026-10-29）。そのため
       Actions では API キーが前提。視聴ページ方式は手元で動かすとき用に残している。
       新しく見つかった配信と、開始から REFRESH_DAYS 日以内の配信（再生数がまだ伸びる）が対象。
    1. は YouTube の画面の作り（JSONの構造）に依存しているので、変わると新しい配信が見つからなくなる。
    その場合も既存の streams.json は消さずに残す（取れたチャンネル・配信だけを更新する）。

出力: data/streams.json
    {"updated": "YYYY-MM-DD",
     "channels": {channel_id: {"backfill_done": bool}},
     "streams": [ {video_id, channel_id, team_tag, player_name, title, start_at, end_at,
                   duration_sec, view_count, views_at, status, first_seen}, ... ]}
    start_at / end_at は UTC の ISO 8601。status は
      "ok"          … 視聴ページから詳細を取れた
      "pending"     … ライブタブで見つけたが詳細は未取得（1回の実行で取る件数に上限があるため）
      "unavailable" … メンバー限定・非公開などで詳細が取れない（毎日取り直さない）
"""
import json
import os
import re
import sys
import time
from datetime import datetime, timedelta, timezone

import requests

from common import DATA_DIR, JST, load_players, save_snapshot, today_str

STREAMS_JSON = os.path.join(DATA_DIR, "streams.json")
BASE = "https://www.youtube.com"
HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"),
    "Accept-Language": "ja-JP,ja;q=0.9",
}
COOKIES = {"CONSENT": "YES+cb", "SOCS": "CAI"}  # 同意画面に飛ばされないようにする

MAX_PAGES_BACKFILL = 8        # 初回のさかのぼり: 1ページ30本 × 最大8ページ
MAX_WATCH_PER_RUN = 600       # 1回の実行で視聴ページを開く上限（残りは翌日以降に回す）
REFRESH_DAYS = 14             # 開始からこの日数以内の配信は再生数を毎日取り直す
REQUEST_INTERVAL_SEC = 0.7
MAX_CONSECUTIVE_FAILS = 10    # 視聴ページがこれだけ続けて失敗したら、その日はやめる（ボット判定などを疑う）
# 視聴ページの playabilityStatus のうち「この動画はもう取れない」と判断するもの。
# UNPLAYABLE=メンバー限定など、ERROR=削除・非公開。LOGIN_REQUIRED はボット判定でも返るので含めない。
GIVE_UP_STATUSES = {"UNPLAYABLE", "ERROR"}

DURATION_RE = re.compile(r"^\d+(?::\d{2}){1,2}$")
API_VIDEOS = "https://www.googleapis.com/youtube/v3/videos"
ISO_DURATION_RE = re.compile(r"^P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?$")


def now_utc():
    return datetime.now(timezone.utc)


def extract_json(html: str, var_name: str):
    """'var ytInitialData = {...};' のような埋め込みJSONを取り出す（入れ子の括弧に強いraw_decodeを使う）。"""
    m = re.search(r"(?:var\s+)?" + re.escape(var_name) + r"\s*=\s*", html)
    if not m:
        return None
    try:
        obj, _ = json.JSONDecoder().raw_decode(html, m.end())
        return obj
    except ValueError:
        return None


def walk(obj, key):
    """入れ子のdict/listから、指定キーの値をすべて取り出す。"""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == key:
                yield v
            yield from walk(v, key)
    elif isinstance(obj, list):
        for v in obj:
            yield from walk(v, key)


def parse_duration(text: str):
    parts = [int(x) for x in text.split(":")]
    sec = 0
    for p in parts:
        sec = sec * 60 + p
    return sec


def parse_lockup(lv):
    """ライブタブの1件（lockupViewModel）を読む。配信済みでないもの（ライブ中・予定）は None。"""
    vid = lv.get("contentId")
    meta = (lv.get("metadata") or {}).get("lockupMetadataViewModel") or {}
    title = ((meta.get("title") or {}).get("content") or "").strip()
    texts = [t for t in walk(meta.get("metadata"), "content") if isinstance(t, str)]
    if not vid or not any(("配信済み" in t) or ("Streamed" in t) for t in texts):
        return None
    duration = None
    for badge in walk(lv.get("contentImage"), "thumbnailBadgeViewModel"):
        t = (badge or {}).get("text", "")
        if DURATION_RE.match(t):
            duration = parse_duration(t)
    relative = next((t for t in texts if ("配信済み" in t) or ("Streamed" in t)), "")
    return {"video_id": vid, "title": title, "duration_sec": duration, "relative": relative}


def grid_items_and_token(items):
    """グリッドの要素列から、配信の一覧と続きのトークンを取り出す。"""
    streams, token = [], None
    for it in items or []:
        if "continuationItemRenderer" in it:
            token = (((it["continuationItemRenderer"].get("continuationEndpoint") or {})
                      .get("continuationCommand") or {}).get("token"))
            continue
        lv = ((it.get("richItemRenderer") or {}).get("content") or {}).get("lockupViewModel")
        if lv:
            s = parse_lockup(lv)
            if s:
                streams.append(s)
    return streams, token


def fetch_live_tab(session, channel_id, backfill):
    """ライブタブの配信一覧を返す。backfill=True のときは続きをたどる。"""
    resp = session.get(f"{BASE}/channel/{channel_id}/streams", params={"hl": "ja", "gl": "JP"}, timeout=30)
    resp.raise_for_status()
    html = resp.text
    data = extract_json(html, "ytInitialData")
    if not data:
        raise RuntimeError("ytInitialData not found")
    tabs = ((data.get("contents") or {}).get("twoColumnBrowseResultsRenderer") or {}).get("tabs") or []
    grid = None
    for t in tabs:
        tr = t.get("tabRenderer") or {}
        if tr.get("selected"):
            grid = (tr.get("content") or {}).get("richGridRenderer")
    if grid is None:
        # ライブ配信をしたことがないチャンネルは「ライブ」タブが無く、ホームが選ばれる
        return []
    streams, token = grid_items_and_token(grid.get("contents"))

    if backfill:
        version = re.search(r'"INNERTUBE_CLIENT_VERSION":"([^"]+)"', html)
        pages = 1
        while token and version and pages < MAX_PAGES_BACKFILL:
            if any(("年前" in s["relative"]) or ("year" in s["relative"]) for s in streams):
                break  # 1年以上前まで来たら打ち切る
            time.sleep(REQUEST_INTERVAL_SEC)
            body = {"context": {"client": {"clientName": "WEB", "clientVersion": version.group(1),
                                           "hl": "ja", "gl": "JP"}},
                    "continuation": token}
            r = session.post(f"{BASE}/youtubei/v1/browse", params={"prettyPrint": "false"}, json=body, timeout=30)
            r.raise_for_status()
            items = []
            for action in walk(r.json(), "appendContinuationItemsAction"):
                items += action.get("continuationItems") or []
            more, token = grid_items_and_token(items)
            if not more:
                break
            streams += more
            pages += 1
    return streams


def fetch_watch(session, video_id):
    """視聴ページから詳細を取る。取れなければ (None, 理由)。"""
    resp = session.get(f"{BASE}/watch", params={"v": video_id, "hl": "ja", "gl": "JP"}, timeout=30)
    resp.raise_for_status()
    pr = extract_json(resp.text, "ytInitialPlayerResponse")
    if not pr:
        return None, "no_player_response"
    status = (pr.get("playabilityStatus") or {}).get("status")
    vd = pr.get("videoDetails") or {}
    mf = ((pr.get("microformat") or {}).get("playerMicroformatRenderer")) or {}
    live = mf.get("liveBroadcastDetails") or {}
    if live.get("isLiveNow"):
        return None, "live_now"
    if status != "OK" or vd.get("videoId") != video_id:
        return None, f"status_{status}"
    start, end = live.get("startTimestamp"), live.get("endTimestamp")
    length = vd.get("lengthSeconds") or mf.get("lengthSeconds")
    views = vd.get("viewCount") or mf.get("viewCount")
    if not start:
        start = mf.get("publishDate")
    start_dt = parse_iso(start)
    end_dt = parse_iso(end)
    duration = int((end_dt - start_dt).total_seconds()) if (start_dt and end_dt and end_dt > start_dt) else (int(length) if length else None)
    return {
        "title": vd.get("title") or "",
        "start_at": iso_utc(start_dt),
        "end_at": iso_utc(end_dt),
        "duration_sec": duration,
        "view_count": int(views) if views and str(views).isdigit() else None,
    }, "ok"


def parse_iso_duration(s):
    """'PT4H24M13S' のような ISO 8601 の長さを秒にする。"""
    m = ISO_DURATION_RE.match(s or "")
    if not m:
        return None
    d, h, mi, se = (int(x) if x else 0 for x in m.groups())
    return ((d * 24 + h) * 60 + mi) * 60 + se


def fetch_details_api(api_key, video_ids):
    """videos.list で最大50本ずつ詳細を取る。
    戻り値: ({video_id: (detail or None, 理由)}, エラー文字列 or None)。
    一覧に返ってこなかった動画は削除・非公開とみなす。途中でエラーになったら、そこまでの結果を返す。"""
    out = {}
    try:
        _fetch_details_api(api_key, video_ids, out)
    except Exception as e:
        return out, str(e)[:300]
    return out, None


def _fetch_details_api(api_key, video_ids, out):
    for i in range(0, len(video_ids), 50):
        batch = video_ids[i:i + 50]
        resp = requests.get(API_VIDEOS, params={
            "part": "snippet,contentDetails,statistics,liveStreamingDetails",
            "id": ",".join(batch), "key": api_key, "maxResults": 50,
        }, timeout=30)
        if resp.status_code != 200:
            # キー無効・クォータ超過など。ここで止めて、残りは pending のまま翌日に回す
            raise RuntimeError(f"videos.list HTTP {resp.status_code}: {resp.text[:200]}")
        found = {it["id"]: it for it in resp.json().get("items", [])}
        for vid in batch:
            it = found.get(vid)
            if it is None:
                out[vid] = (None, "status_ERROR")  # 削除・非公開
                continue
            live = it.get("liveStreamingDetails") or {}
            start = parse_iso(live.get("actualStartTime"))
            end = parse_iso(live.get("actualEndTime"))
            if start and not end:
                out[vid] = (None, "live_now")
                continue
            if not start:
                out[vid] = (None, "status_UNPLAYABLE")  # ライブ配信ではない（予定のまま流れた枠など）
                continue
            views = (it.get("statistics") or {}).get("viewCount")
            duration = int((end - start).total_seconds()) if end > start else \
                parse_iso_duration((it.get("contentDetails") or {}).get("duration"))
            out[vid] = ({
                "title": (it.get("snippet") or {}).get("title") or "",
                "start_at": iso_utc(start),
                "end_at": iso_utc(end),
                "duration_sec": duration,
                "view_count": int(views) if views and str(views).isdigit() else None,
            }, "ok")
        time.sleep(0.2)


def parse_iso(s):
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None


def iso_utc(dt):
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ") if dt else None


def channel_id_of(player):
    m = re.search(r"/channel/([A-Za-z0-9_-]+)", player.get("youtube_url") or "")
    return m.group(1) if m else None


def load_store():
    if not os.path.exists(STREAMS_JSON):
        return {"updated": None, "channels": {}, "streams": []}
    with open(STREAMS_JSON, encoding="utf-8") as f:
        return json.load(f)


def write_store(store):
    """1配信1行で書く（毎日の差分が読みやすいように）。"""
    store["streams"].sort(key=lambda s: (s.get("start_at") or "", s["video_id"]), reverse=True)
    lines = [json.dumps(s, ensure_ascii=False, separators=(",", ":")) for s in store["streams"]]
    head = {k: v for k, v in store.items() if k != "streams"}
    text = (json.dumps(head, ensure_ascii=False, separators=(",", ":"))[:-1]
            + ',"streams":[\n' + ",\n".join(lines) + "\n]}\n")
    json.loads(text)  # 壊れたJSONを書かないための検算
    tmp = STREAMS_JSON + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    os.replace(tmp, STREAMS_JSON)


def main():
    date_str = today_str()
    store = load_store()
    by_id = {s["video_id"]: s for s in store["streams"]}
    session = requests.Session()
    session.headers.update(HEADERS)
    session.cookies.update(COOKIES)

    summary = {"date": date_str, "channels": {}, "watch_fetched": 0, "watch_failed": {}}
    channels_ok = 0
    for p in load_players():
        cid = channel_id_of(p)
        if not cid:
            continue
        ch_state = store["channels"].setdefault(cid, {"backfill_done": False})
        try:
            listed = fetch_live_tab(session, cid, backfill=not ch_state["backfill_done"])
        except Exception as e:
            print(f"[streams] {p['player_name']}: live tab failed ({e!r})", file=sys.stderr)
            summary["channels"][p["player_name"]] = f"error: {e!r}"
            time.sleep(REQUEST_INTERVAL_SEC)
            continue
        channels_ok += 1
        ch_state["backfill_done"] = True
        new = 0
        for item in listed:
            rec = by_id.get(item["video_id"])
            if rec is None:
                rec = {"video_id": item["video_id"], "channel_id": cid, "team_tag": p["team_tag"],
                       "player_name": p["player_name"], "title": item["title"], "start_at": None,
                       "end_at": None, "duration_sec": item["duration_sec"], "view_count": None,
                       "views_at": None, "status": "pending", "first_seen": date_str}
                by_id[item["video_id"]] = rec
                store["streams"].append(rec)
                new += 1
            else:
                rec["title"] = item["title"] or rec["title"]
                rec["team_tag"], rec["player_name"] = p["team_tag"], p["player_name"]
        summary["channels"][p["player_name"]] = {"listed": len(listed), "new": new}
        print(f"[streams] {p['player_name']}: listed {len(listed)}, new {new}")
        time.sleep(REQUEST_INTERVAL_SEC)

    # 視聴ページで詳細を取る: 未取得（新しい順）を優先し、残りの枠で最近の配信の再生数を取り直す
    cutoff = iso_utc(now_utc() - timedelta(days=REFRESH_DAYS))
    pending = [s for s in store["streams"] if s["status"] == "pending"]
    refresh = [s for s in store["streams"] if s["status"] == "ok" and (s.get("start_at") or "") >= cutoff
               and s.get("views_at") != date_str]
    queue = pending + refresh
    api_key = os.environ.get("YOUTUBE_API_KEY")
    api_results = None
    if api_key:
        # API は1回の実行で全件取れる（50本で1ユニット）ので、件数の上限はかけない
        api_results, err = fetch_details_api(api_key, [r["video_id"] for r in queue])
        summary["via"] = "api"
        if err:
            # キー無効・クォータ超過など。取れたところまで反映し、残りは pending のまま翌日に回す
            print(f"[streams] YouTube Data API failed ({err}); got {len(api_results)} before the error", file=sys.stderr)
            summary["api_error"] = err
        queue = [r for r in queue if r["video_id"] in api_results]
    else:
        summary["via"] = "watch_page"
        queue = queue[:MAX_WATCH_PER_RUN]
    consecutive_fails = 0
    for rec in queue:
        if api_results is not None:
            detail, why = api_results.get(rec["video_id"], (None, "missing"))
        else:
            try:
                detail, why = fetch_watch(session, rec["video_id"])
            except Exception as e:
                detail, why = None, f"error_{type(e).__name__}"
            time.sleep(REQUEST_INTERVAL_SEC)
        summary["watch_fetched"] += 1
        if detail:
            consecutive_fails = 0
            rec.update({k: v for k, v in detail.items() if v is not None})
            rec["views_at"] = date_str if detail.get("view_count") is not None else rec.get("views_at")
            rec["status"] = "ok"
        else:
            summary["watch_failed"][why] = summary["watch_failed"].get(why, 0) + 1
            if why.replace("status_", "") in GIVE_UP_STATUSES and rec["status"] == "pending":
                rec["status"] = "unavailable"  # メンバー限定・非公開など。毎日は取り直さない
                consecutive_fails = 0
            else:
                consecutive_fails += 1
                if api_results is None and consecutive_fails >= MAX_CONSECUTIVE_FAILS:
                    print(f"[streams] {consecutive_fails} watch pages failed in a row ({why}); stopping for today",
                          file=sys.stderr)
                    summary["stopped_early"] = why
                    break

    summary["left_pending"] = sum(1 for s in store["streams"] if s["status"] == "pending")
    summary["total"] = len(store["streams"])
    print(f"[streams] channels ok {channels_ok}, watch fetched {summary['watch_fetched']}, "
          f"failed {summary['watch_failed']}, pending left {summary['left_pending']}, total {summary['total']}")
    save_snapshot("streams", [summary])

    detail_updates = summary["watch_fetched"] - sum(summary["watch_failed"].values())
    if channels_ok == 0 and detail_updates <= 0:
        print("WARNING: no channel could be read. YouTube page structure may have changed. streams.json is left as is.",
              file=sys.stderr)
        sys.exit(1)
    if channels_ok == 0:
        print("WARNING: live tabs could not be read (new streams are not discovered today), "
              "but details of known streams were updated.", file=sys.stderr)
    store["updated"] = date_str
    write_store(store)


if __name__ == "__main__":
    main()
