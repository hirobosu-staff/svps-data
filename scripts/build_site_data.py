"""公開サイト用に、ページが読む小さな集計済みファイルを作る（GitHub Pages のビルド時に実行）。

背景: 以前は全ページが data/history.csv（2026-11 時点で約8MB）を毎回読み込んでいて、
スマホ回線では表示まで数秒かかっていた。history.csv の大半は、更新が止まった
shadowverse-reference.com の期間集計を毎日記録し直した行で、画面ではもう使っていない。
選手詳細の配信分析も、全選手分の data/streams.json（約1.8MB）を読んでから1人分に絞っていた。

使い方: python build_site_data.py <出力先ディレクトリ>   （ワークフローでは _site/data を渡す）
標準ライブラリだけで動く（deploy-pages.yml では pip install をしないため）。

作るもの（いずれもリポジトリには入れず、公開用の出力先にだけ置く）:
    timeseries.json    … 選手ごとの Xフォロワー数・YouTube登録者数の日次推移（history.csv から2指標だけ）
    stream_stats.json  … 選手ごとの配信集計（直近30日・直近90日・取得した全期間）。比較ページが使う
    streams/{channel_id}.json … 選手1人分の配信一覧。選手詳細の配信分析が使う
    stream_ranking.json … 月ごとの再生数上位の配信（配信ランキングページ streams.html が使う）
    contribution.json  … 貢献度（scripts/build_contribution.py。contribution.html と選手詳細が使う）
"""
import csv
import json
import os
import re
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(REPO_ROOT, "data")
JST = timezone(timedelta(hours=9))
TIMESERIES_METRICS = ("followers", "youtube_subscribers")
STAT_WINDOWS = {"30": 30, "90": 90, "all": None}
# 配信ランキング（streams.html）: 日本時間の月ごとに、再生数の多い順に RANKING_TOP_N 本。
# RANKING_FROM_MONTH より前の月は入れない。初回取得でさかのぼれる本数に上限があり
# （scrape_streams.py の MAX_PAGES_BACKFILL）、配信の多い選手は2026年1月ごろより前が欠けているため。
RANKING_FROM_MONTH = "2026-06"
RANKING_TOP_N = 50


def write_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))


def build_timeseries(out_dir):
    series = defaultdict(lambda: defaultdict(dict))
    latest = ""
    with open(os.path.join(DATA_DIR, "history.csv"), encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            if r["metric"] not in TIMESERIES_METRICS or r["period"] != "current" or r["value"] == "":
                continue
            try:
                v = float(r["value"])
            except ValueError:
                continue
            series[r["player_name"]][r["metric"]][r["date"]] = int(v) if v.is_integer() else v
            latest = max(latest, r["date"])
    players = {name: {m: sorted(d.items()) for m, d in metrics.items()} for name, metrics in series.items()}
    write_json(os.path.join(out_dir, "timeseries.json"), {"updated": latest, "players": players})
    return sum(len(v) for m in players.values() for v in m.values())


def stream_stats(streams, now, days):
    if days is not None:
        since = now - timedelta(days=days)
        streams = [s for s in streams if datetime.fromisoformat(s["start_at"].replace("Z", "+00:00")) >= since]
    if not streams:
        return None
    durations = [s["duration_sec"] for s in streams if s.get("duration_sec") is not None]
    with_views = [s for s in streams if s.get("view_count") is not None]
    views = [s["view_count"] for s in with_views]
    timed = [s for s in with_views if s.get("duration_sec")]
    hours = sum(s["duration_sec"] for s in timed) / 3600
    jst_days = {datetime.fromisoformat(s["start_at"].replace("Z", "+00:00")).astimezone(JST).date() for s in streams}
    return {
        "count": len(streams),
        "days": len(jst_days),
        "total_sec": sum(durations),
        "avg_views": round(sum(views) / len(views)) if views else None,
        # 時間あたり再生数 = 再生数の合計 ÷ 配信時間の合計（長時間配信の多い人と短い人を公平に比べるため）
        "views_per_hour": round(sum(s["view_count"] for s in timed) / hours) if hours > 0 else None,
    }


def build_stream_ranking(streams, out_dir, updated):
    """月ごとの再生数上位。再生数が無い配信（メンバー限定など）は順位に入れず、本数だけ数える。"""
    months = defaultdict(list)
    counts = defaultdict(int)
    for s in streams:
        month = datetime.fromisoformat(s["start_at"].replace("Z", "+00:00")).astimezone(JST).strftime("%Y-%m")
        if month < RANKING_FROM_MONTH:
            continue
        counts[month] += 1
        if s.get("view_count") is not None:
            months[month].append(s)
    keep = ("video_id", "title", "player_name", "team_tag", "start_at", "duration_sec", "view_count", "views_at")
    out = {}
    for month in sorted(counts, reverse=True):
        items = sorted(months[month], key=lambda s: (-s["view_count"], s["start_at"]))
        out[month] = {
            "count": counts[month],
            "with_views": len(items),
            "top": [{k: s.get(k) for k in keep} for s in items[:RANKING_TOP_N]],
        }
    write_json(os.path.join(out_dir, "stream_ranking.json"), {
        "updated": updated, "top_n": RANKING_TOP_N, "from_month": RANKING_FROM_MONTH, "months": out,
    })


def build_streams(out_dir):
    path = os.path.join(DATA_DIR, "streams.json")
    if not os.path.exists(path):
        return 0, 0
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    by_channel = defaultdict(list)
    for s in data.get("streams", []):
        if s.get("status") != "ok" or not s.get("start_at"):
            continue
        by_channel[s["channel_id"]].append(s)

    now = datetime.now(timezone.utc)
    windows = {k: {} for k in STAT_WINDOWS}
    keep = ("video_id", "title", "start_at", "end_at", "duration_sec", "view_count")
    for cid, items in by_channel.items():
        items.sort(key=lambda s: s["start_at"], reverse=True)
        name = items[0]["player_name"]
        if not re.fullmatch(r"[A-Za-z0-9_-]+", cid):
            continue  # ファイル名に使えないIDは飛ばす（YouTubeのチャンネルIDなら必ず通る）
        write_json(os.path.join(out_dir, "streams", f"{cid}.json"), {
            "player_name": name,
            "streams": [{k: s.get(k) for k in keep} for s in items],
        })
        for key, days in STAT_WINDOWS.items():
            st = stream_stats(items, now, days)
            if st:
                windows[key][name] = st
        # 取得できている最古の配信（「全期間」がいつからなのかを画面に出すため）
        windows["all"].setdefault(name, {})["since"] = items[-1]["start_at"][:10]
    build_stream_ranking([s for items in by_channel.values() for s in items], out_dir, data.get("updated"))
    write_json(os.path.join(out_dir, "stream_stats.json"), {
        "as_of": now.astimezone(JST).strftime("%Y-%m-%d"),
        "updated": data.get("updated"),
        "windows": windows,
    })
    return len(by_channel), sum(len(v) for v in by_channel.values())


def main():
    if len(sys.argv) != 2:
        print("usage: python build_site_data.py <output dir>", file=sys.stderr)
        sys.exit(2)
    out_dir = sys.argv[1]
    points = build_timeseries(out_dir)
    channels, streams = build_streams(out_dir)
    from build_contribution import write as write_contribution  # 同じ scripts/ にある
    contrib_players = write_contribution(out_dir)
    print(f"[build_site_data] timeseries.json: {points} points / streams: {channels} channels, {streams} streams / contribution.json: {contrib_players} players -> {out_dir}")


if __name__ == "__main__":
    main()
