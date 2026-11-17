"""貢献度（site/contribution.html と player.html の「貢献度」欄）の元データを毎日作り直す。

公開時（GitHub Pages のビルド）に scripts/build_site_data.py から呼ばれ、
<出力先>/contribution.json を書く。標準ライブラリだけで動く。

以前は別の場所で計算した結果を site/contribution.js に貼り付けていたため、第10節終了時点で
止まっていた。2026-11-17 から、毎日取得しているデータで自動的に計算し直す。

自動で取る項目（毎日更新）:
    競技          … data/match_results.csv の個人戦（バトル1〜3）の勝敗
    配信（ライブ） … data/streams.json のライブ配信。live_from（8月3日）から最新までの合計再生数と1本あたり中央値
    配信（投稿動画）… data/uploads.json（scrape_uploads.py）のレギュラーシーズン中の投稿動画の合計再生数。
                     無い場合は history.csv に残っている shadowverse-reference.com の値（11月4日）を使う
    ランクマッチ   … data/svlabo_leaderboards.csv で、ladder_from_period 以降の各期間・各クラスの100位以内に入った回数
手入力の項目（data/contribution_manual.json）:
    表彰・大会結果・note・WGP予選、配点、Twitchのみの選手の配信の推計値、Vision の選手ページのスラッグ

計算式は旧版（配点シミュレーターの案A）と同じ。満点の基準（全選手の最高値）も毎回計算し直す。
"""
import csv
import json
import os
import re
import statistics
from collections import defaultdict
from datetime import datetime, timedelta, timezone

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(REPO_ROOT, "data")
JST = timezone(timedelta(hours=9))


def _read_csv(name):
    path = os.path.join(DATA_DIR, name)
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def _read_json(name):
    path = os.path.join(DATA_DIR, name)
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _norm(name):
    return re.sub(r"[\s　]", "", str(name or "")).lower()


def _jst_date(iso):
    return datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(JST).strftime("%Y-%m-%d")


def _raw_comp(w, l):
    """競技の素点（旧版と同じ式）。勝ち数と、試合数で補正した勝率の組み合わせ。"""
    return 0 if w + l == 0 else 3 * w + 10 * (w + 2.5) / (w + l + 5)


def _progress_label(schedule, matches):
    """どの節まで終わっているか（「第11節前半」「第10節」など）。"""
    done = {(m["section"], m["half"]) for m in matches}
    if not done:
        return ""
    last = max(int(s) for s, _ in done)
    rows = [r for r in schedule if r["section"] == str(last)]
    if rows and all(r["score1"] != "" for r in rows):
        return f"第{last}節"
    halves = {h for s, h in done if s == str(last)}
    return f"第{last}節{'前半' if halves == {'前半'} else ''}"


def build(live_to=None, max_section=None, ladder_to_period=None, uploads_from_reference=False):
    """引数は検算用（旧版と同じ締め日で計算し直して突き合わせるため）。通常はすべて None。"""
    manual = _read_json("contribution_manual.json")
    players_csv = _read_csv("players.csv")
    team_of = {p["player_name"]: p for p in players_csv}
    W = manual["weights"]

    # --- 競技 ---
    matches = _read_csv("match_results.csv")
    if max_section is not None:
        matches = [m for m in matches if int(m["section"]) <= max_section]
    wl = defaultdict(lambda: [0, 0])
    for m in matches:
        wl[m["player_name"]][0 if m["result"] == "WIN" else 1] += 1

    # --- 配信（ライブ） ---
    streams_doc = _read_json("streams.json") or {"streams": []}
    live_from = manual["live_from"]
    if live_to is None:
        live_to = streams_doc.get("updated") or datetime.now(JST).strftime("%Y-%m-%d")
    live = defaultdict(list)
    for s in streams_doc["streams"]:
        if s.get("status") != "ok" or not s.get("start_at") or s.get("view_count") is None:
            continue
        if live_from <= _jst_date(s["start_at"]) <= live_to:
            live[s["channel_id"]].append(s["view_count"])

    # --- 配信（投稿動画） ---
    uploads_doc = None if uploads_from_reference else _read_json("uploads.json")
    up_by_channel = None
    if uploads_doc:
        up_by_channel = defaultdict(int)
        for v in uploads_doc.get("videos", []):
            up_by_channel[v["channel_id"]] += v.get("view_count") or 0
        fetched = set(uploads_doc.get("channels", {}))
    ref_up = {}
    for r in _read_csv("history.csv"):
        if r["metric"] == "video_view_count" and r["period"] == "regular_season" and r["value"] != "":
            if r["player_name"] not in ref_up or ref_up[r["player_name"]][0] < r["date"]:
                ref_up[r["player_name"]] = (r["date"], float(r["value"]))

    # --- ランクマッチ ---
    board = _read_csv("svlabo_leaderboards.csv")
    periods = list(dict.fromkeys(r["period"] for r in board))  # ファイルは新しい期間が先頭
    target = periods[:periods.index(manual["ladder_from_period"]) + 1] if manual["ladder_from_period"] in periods else []
    if ladder_to_period in target:
        target = target[target.index(ladder_to_period):]
    target_set = set(target)
    labels = manual.get("expansion_labels", {})

    def period_label(p):
        m = re.match(r"^(.*?)\s*(前半戦|後半戦)$", p)
        if m and m.group(1) in labels:
            return f"{labels[m.group(1)]} {m.group(2)}"
        return p

    aliases = manual.get("svlabo_name_aliases", {})
    ladder = defaultdict(list)
    for r in board:
        if r["period"] not in target_set:
            continue
        try:
            rank = int(r["rank"])
        except ValueError:
            continue
        if rank <= 100:
            ladder[_norm(r["player_name"])].append((target.index(r["period"]), r["period"], r["class"], rank, int(r["rating"])))

    # --- 選手ごと ---
    order = [e["player"] for e in manual["players"]]
    order += [p["player_name"] for p in players_csv if p["player_name"] not in order]
    manual_by = {e["player"]: e for e in manual["players"]}
    rows = []
    for name in order:
        if name not in team_of:
            continue  # players.csv にいない（引退など）選手は出さない
        pc, e = team_of[name], manual_by.get(name, {})
        cid_m = re.search(r"/channel/([A-Za-z0-9_-]+)", pc.get("youtube_url") or "")
        cid = cid_m.group(1) if cid_m else None
        send = e.get("send") or ("youtube" if cid else "none")
        w, l = wl[name]
        views = live.get(cid, []) if send == "youtube" else []
        if send == "youtube" and up_by_channel is not None and cid in fetched:
            up, up_src = up_by_channel.get(cid, 0), "youtube"
        else:
            up, up_src = (ref_up.get(name, (None, 0))[1], "reference")
        entries = []
        for key in {_norm(name), *[_norm(a) for a in aliases.get(name, [])]}:
            entries += ladder.get(key, [])
        # 古い期間から、同じ期間の中は順位の良い順
        entries.sort(key=lambda x: (-x[0], x[3]))
        awards = e.get("awards", [])
        tours = e.get("tournaments", [])
        note = e.get("note", {})
        wq = e.get("wgp_qualifier", {})
        rows.append({
            "p": name, "t": pc["team_name"], "slug": e.get("vision_slug", ""),
            "w": w, "l": l, "raw": _raw_comp(w, l),
            "s": None if send == "none" else (e.get("est35") if send == "twitch_est" else 0),
            "est": send == "twitch_est", "wt": e.get("watch_hours", 0),
            "ls": sum(views), "ln": len(views), "lm": statistics.median(views) if views else 0,
            "up": int(up), "up_src": up_src,
            "pr": sum(1 for a in awards if a["kind"] == "P"), "bb": sum(1 for a in awards if a["kind"] == "B"),
            "aw": [[a["name"], a["event"], a["kind"]] for a in awards],
            "tour": [t["kind"] for t in tours], "tr": [[t["event"], t["result"], t["kind"], t["url"]] for t in tours],
            "nt": note.get("score", 0), "nacc": note.get("account", ""),
            "narts": [[a["title"], a["date"], a["url"]] for a in note.get("articles", [])],
            "wq": wq.get("result", ""), "wqs": wq.get("swiss", ""), "wqt": wq.get("detail", ""),
            "lad": len(entries), "ld": [[period_label(x[1]), x[2], x[3], x[4]] for x in entries],
        })

    yt = [r for r in rows if r["s"] is not None and not r["est"]]
    est = manual["twitch_estimate"]
    K = {
        "cmax": max((r["raw"] for r in rows), default=0) or 1,
        "tmax": max((r["ls"] for r in yt), default=0) or 1,
        "mmax": max((r["lm"] for r in yt), default=0) or 1,
        "umax": max((r["up"] for r in yt), default=0) or 1,
        "a": est["a"], "b": est["b"], "n": est["n"],
        "ladmax": max((r["lad"] for r in rows), default=0) or 1,
    }
    for r in rows:
        r["c"] = r["raw"] / K["cmax"] * 45  # 画面側は c × 配点 ÷ 45 で使う（旧版と同じ持ち方）
    progress = _progress_label(_read_csv("schedule.csv"), matches)
    return {
        "updated": datetime.now(JST).strftime("%Y-%m-%d"),
        "progress": progress,
        "live_from": live_from, "live_to": live_to,
        "uploads_updated": uploads_doc.get("updated") if uploads_doc else None,
        "uploads_since": uploads_doc.get("since") if uploads_doc else None,
        "ladder_periods": [period_label(p) for p in reversed(target)],
        "W": W, "K": K, "players": rows,
    }


def write(out_dir):
    data = build()
    path = os.path.join(out_dir, "contribution.json")
    os.makedirs(out_dir, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    return len(data["players"])


if __name__ == "__main__":
    import sys
    print(write(sys.argv[1] if len(sys.argv) > 1 else "."))
