"""各選手の YouTube の「投稿動画」（ライブ配信以外）の再生数を取得し、data/uploads.json に保存する。

貢献度の「投稿動画」の項目の元データ（scripts/build_contribution.py が使う）。以前は
shadowverse-reference.com の「レギュラーシーズンの再生回数」を使っていたが、2026年10月中旬で
更新が止まったため、YouTube Data API から直接取るようにした（2026-11-17）。

取得方法（YouTube Data API v3。環境変数 YOUTUBE_API_KEY が必要）:
    1. channels.list（part=contentDetails）で各チャンネルの「アップロード」再生リストIDを取る
       （50チャンネルまで1回・1ユニット）。
    2. playlistItems.list で、そのリストを新しい順に読み、レギュラーシーズン開始日
       （schedule.csv の最初の日付）より前の動画が出てきたらやめる（1ページ50本・1ユニット）。
    3. videos.list（part=snippet,contentDetails,statistics,liveStreamingDetails）で
       再生数を取る（50本ずつ・1ユニット）。liveStreamingDetails がある動画（ライブ配信の
       アーカイブとプレミア公開）は「投稿動画」に含めない（ライブ配信は streams.json 側で数える）。
    1日の消費は100ユニット前後（上限は1日1万）。

毎日、対象期間の全動画を取り直す（再生数は伸び続けるため）。取得に失敗したチャンネルは
前回の行をそのまま残す。全チャンネルで失敗したら書き換えずに終了する。

出力: data/uploads.json
    {"updated": "YYYY-MM-DD", "since": "YYYY-MM-DD",
     "channels": {channel_id: {"player_name", "videos", "views", "fetched"}},
     "videos": [ {video_id, channel_id, team_tag, player_name, title, published_at,
                  duration_sec, view_count, views_at}, ... ]}
"""
import csv
import json
import os
import re
import sys
import time
from datetime import datetime, timezone

import requests

from common import DATA_DIR, JST, load_players, save_snapshot, today_str

UPLOADS_JSON = os.path.join(DATA_DIR, "uploads.json")
SCHEDULE_CSV = os.path.join(DATA_DIR, "schedule.csv")
API = "https://www.googleapis.com/youtube/v3/"
DEFAULT_SINCE = "2026-07-11"   # schedule.csv が読めないときのレギュラーシーズン開始日
MAX_PAGES = 20                 # 1チャンネルで読む再生リストのページ数の上限（50本 × 20）
ISO_DURATION_RE = re.compile(r"^P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?$")


def season_start():
    try:
        with open(SCHEDULE_CSV, encoding="utf-8", newline="") as f:
            dates = [r["date"] for r in csv.DictReader(f) if r.get("date")]
        return min(dates) if dates else DEFAULT_SINCE
    except OSError:
        return DEFAULT_SINCE


def api_get(endpoint, params, api_key):
    resp = requests.get(API + endpoint, params={**params, "key": api_key}, timeout=30)
    if resp.status_code != 200:
        raise RuntimeError(f"{endpoint} HTTP {resp.status_code}: {resp.text[:200]}")
    time.sleep(0.2)
    return resp.json()


def parse_iso_duration(s):
    m = ISO_DURATION_RE.match(s or "")
    if not m:
        return None
    d, h, mi, se = (int(x) if x else 0 for x in m.groups())
    return ((d * 24 + h) * 60 + mi) * 60 + se


def channel_id_of(player):
    m = re.search(r"/channel/([A-Za-z0-9_-]+)", player.get("youtube_url") or "")
    return m.group(1) if m else None


def upload_playlists(channel_ids, api_key):
    out = {}
    for i in range(0, len(channel_ids), 50):
        data = api_get("channels", {"part": "contentDetails", "id": ",".join(channel_ids[i:i + 50]),
                                    "maxResults": 50}, api_key)
        for it in data.get("items", []):
            pl = ((it.get("contentDetails") or {}).get("relatedPlaylists") or {}).get("uploads")
            if pl:
                out[it["id"]] = pl
    return out


def list_video_ids(playlist_id, since_utc, api_key):
    """再生リストを新しい順に読み、since_utc 以降に公開された動画IDを返す。"""
    ids, token = [], None
    for _ in range(MAX_PAGES):
        params = {"part": "contentDetails", "playlistId": playlist_id, "maxResults": 50}
        if token:
            params["pageToken"] = token
        data = api_get("playlistItems", params, api_key)
        older = False
        for it in data.get("items", []):
            cd = it.get("contentDetails") or {}
            published = cd.get("videoPublishedAt")
            if not published:
                continue  # 非公開・削除済みの動画
            if published < since_utc:
                older = True
                continue
            ids.append(cd["videoId"])
        token = data.get("nextPageToken")
        # アップロード再生リストは基本的に新しい順。期間より古い動画が出てきたページで打ち切る
        if older or not token:
            break
    return ids


def video_details(video_ids, api_key):
    out = {}
    for i in range(0, len(video_ids), 50):
        data = api_get("videos", {"part": "snippet,contentDetails,statistics,liveStreamingDetails",
                                  "id": ",".join(video_ids[i:i + 50]), "maxResults": 50}, api_key)
        for it in data.get("items", []):
            out[it["id"]] = it
    return out


def main():
    api_key = os.environ.get("YOUTUBE_API_KEY")
    if not api_key:
        print("[uploads] YOUTUBE_API_KEY is not set. Keeping the existing uploads.json.", file=sys.stderr)
        sys.exit(1)
    date_str = today_str()
    since = season_start()
    since_utc = datetime.fromisoformat(since + "T00:00:00+09:00").astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    old = {"videos": [], "channels": {}}
    if os.path.exists(UPLOADS_JSON):
        with open(UPLOADS_JSON, encoding="utf-8") as f:
            old = json.load(f)

    players = [p for p in load_players() if channel_id_of(p)]
    try:
        playlists = upload_playlists([channel_id_of(p) for p in players], api_key)
    except Exception as e:
        print(f"[uploads] channels.list failed ({e}). Keeping the existing uploads.json.", file=sys.stderr)
        sys.exit(1)

    videos, channels, failed = [], {}, {}
    for p in players:
        cid = channel_id_of(p)
        try:
            if cid not in playlists:
                raise RuntimeError("uploads playlist not found")
            ids = list_video_ids(playlists[cid], since_utc, api_key)
            details = video_details(ids, api_key)
        except Exception as e:
            failed[p["player_name"]] = str(e)[:200]
            print(f"[uploads] {p['player_name']}: failed ({e}). Keeping the previous rows.", file=sys.stderr)
            videos += [v for v in old.get("videos", []) if v["channel_id"] == cid]
            if cid in old.get("channels", {}):
                channels[cid] = old["channels"][cid]
            continue
        mine = []
        for vid in ids:
            it = details.get(vid)
            if not it or it.get("liveStreamingDetails"):
                continue  # 非公開・削除、またはライブ配信・プレミア公開
            sn, st = it.get("snippet") or {}, it.get("statistics") or {}
            views = st.get("viewCount")
            mine.append({
                "video_id": vid, "channel_id": cid, "team_tag": p["team_tag"], "player_name": p["player_name"],
                "title": sn.get("title") or "", "published_at": sn.get("publishedAt"),
                "duration_sec": parse_iso_duration((it.get("contentDetails") or {}).get("duration")),
                "view_count": int(views) if views and str(views).isdigit() else None,
                "views_at": date_str,
            })
        videos += mine
        channels[cid] = {"player_name": p["player_name"], "videos": len(mine),
                         "views": sum(v["view_count"] or 0 for v in mine), "fetched": date_str}
        print(f"[uploads] {p['player_name']}: {len(mine)} videos, {channels[cid]['views']:,} views")

    if len(failed) == len(players):
        print("[uploads] every channel failed. Keeping the existing uploads.json.", file=sys.stderr)
        sys.exit(1)

    videos.sort(key=lambda v: (v.get("published_at") or "", v["video_id"]), reverse=True)
    head = {"updated": date_str, "since": since, "channels": channels}
    text = (json.dumps(head, ensure_ascii=False, separators=(",", ":"))[:-1] + ',"videos":[\n'
            + ",\n".join(json.dumps(v, ensure_ascii=False, separators=(",", ":")) for v in videos) + "\n]}\n")
    json.loads(text)  # 壊れたJSONを書かないための検算
    tmp = UPLOADS_JSON + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    os.replace(tmp, UPLOADS_JSON)
    save_snapshot("uploads", [{"date": date_str, "since": since, "channels": len(channels),
                               "videos": len(videos), "failed": failed}])
    print(f"[uploads] {len(channels)} channels, {len(videos)} videos -> {UPLOADS_JSON}")
    if failed:
        sys.exit(1)  # 一部失敗。書き込みは済ませたうえで、Actions の注釈に失敗を残す


if __name__ == "__main__":
    main()
