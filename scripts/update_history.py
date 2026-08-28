"""当日分の data/snapshots/*.json を読み込み、ロング形式の data/history.csv に正規化して追記する。

history.csv のスキーマ:
    date, team_tag, player_name, metric, period, value

metric一覧:
    followers            : Xフォロワー数（shadowverse-reference.com, periodは"current"）
    stream_duration       : 配信時間[h]（shadowverse-reference.com, periodは隔週キー）
    watch_time            : 視聴時間[h]（同上）
    video_view_count      : 再生回数（同上）
    video_upload_count    : 動画本数（同上）
    cr_rank_{class}       : クラス別ランクマッチ最高順位（svlabo.jp, periodは隔週シーズン名）
    cr_rating_{class}     : クラス別ランクマッチ最高レート（同上）
    cr_best_rank_overall  : 全クラス通算の最高順位（svlabo.jp, periodは"cumulative_to_date"）
    cr_top100_count       : 順位100位以内に入った回数（同上）
    youtube_subscribers    : YouTubeチャンネル登録者数（各選手のYouTubeチャンネル, periodは"current"）

同じ(date, team_tag, player_name, metric, period)の組み合わせが既に存在する場合は上書きする
（1日に複数回スクリプトを実行しても重複行にならないようにするため）。

PS公式戦の個人成績（勝敗・獲得ポイント・使用クラス・対戦相手）は history.csv には含めず、
別途 data/match_results.csv に書き出す（rows_from_ps_results / merge_matches 参照）。
「ラウンドごとの1試合の勝敗」は history.csv のような日次推移データとして扱う意味がなく
（折れ線グラフにもランキングにも向かない）、通算成績・試合単位の一覧として見せる方が
実態に合っているため、スキーマを分けている。
"""
import csv
import glob
import json
import os
import sys

from common import DATA_DIR, SNAPSHOT_DIR, HISTORY_CSV, today_str, load_players, build_name_index, normalize_name

FIELDNAMES = ["date", "team_tag", "player_name", "metric", "period", "value"]

MATCH_RESULTS_CSV = os.path.join(DATA_DIR, "match_results.csv")
# section / half / round_no / battle_no は公式サイトのリニューアル後に取れるようになった項目。
# 以前は日付(round)しか持っておらず、表示側が「日付の通し番号＝節番号」と推測していたため、
# 1節が前半/後半の2日に分かれる構成を扱えず第5節を第8節と表示していた。節番号を実データとして
# 持つことでその推測を廃止した。
MATCH_FIELDNAMES = [
    "section", "half", "round_no", "battle_no",
    "round", "date", "team_tag", "player_name", "class", "result", "point",
    "opponent_team_tag", "opponent_name", "opponent_class",
]


def latest_snapshot(source: str, date_str: str):
    path = os.path.join(SNAPSHOT_DIR, f"{source}_{date_str}.json")
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def rows_from_reference(snapshot, name_index):
    rows = []
    for r in snapshot or []:
        norm = normalize_name(r["player_name"])
        player = name_index.get(norm)
        team_tag = player["team_tag"] if player else r["team_tag"]
        rows.append(
            {
                "date": r["date"],
                "team_tag": team_tag,
                "player_name": player["player_name"] if player else r["player_name"],
                "metric": r["metric"],
                "period": r["period"],
                "value": r["value"],
            }
        )
    return rows


def rows_from_svlabo(snapshot):
    rows = []
    for r in snapshot or []:
        if not r.get("matched_player"):
            continue  # players.csvにいない選手はスキップ（無関係選手のノイズを避ける）
        team_tag = r["team_tag"]
        name = r["matched_player"]
        date = r["date"]

        rows.append(
            {
                "date": date,
                "team_tag": team_tag,
                "player_name": name,
                "metric": "cr_best_rank_overall",
                "period": "cumulative_to_date",
                "value": r["best_rank_overall"],
            }
        )
        rows.append(
            {
                "date": date,
                "team_tag": team_tag,
                "player_name": name,
                "metric": "cr_top100_count",
                "period": "cumulative_to_date",
                "value": r["top100_count"],
            }
        )
        for b in r.get("breakdown", []):
            rows.append(
                {
                    "date": date,
                    "team_tag": team_tag,
                    "player_name": name,
                    "metric": f"cr_rank_{b['class']}",
                    "period": b["period"],
                    "value": b["rank"],
                }
            )
            rows.append(
                {
                    "date": date,
                    "team_tag": team_tag,
                    "player_name": name,
                    "metric": f"cr_rating_{b['class']}",
                    "period": b["period"],
                    "value": b["rating"],
                }
            )
    return rows


def rows_from_youtube(snapshot):
    rows = []
    for r in snapshot or []:
        rows.append(
            {
                "date": r["date"],
                "team_tag": r["team_tag"],
                "player_name": r["player_name"],
                "metric": "youtube_subscribers",
                "period": "current",
                "value": r["value"],
            }
        )
    return rows


def match_rows_from_ps_results(snapshot, name_index):
    """ps_resultsのスナップショットから、試合結果タブ用の1試合1行データを組み立てる。
    対戦相手のteam_tagもplayers.csvから引いて付与する（相手が players.csv に無い
    ケースはteam_tagを"?"にする）。"""
    rows = []
    for r in snapshot or []:
        norm = normalize_name(r["player_name"])
        player = name_index.get(norm)
        team_tag = player["team_tag"] if player else "?"
        name = player["player_name"] if player else r["player_name"]

        opp_raw = r.get("opponent_name")
        opp_team_tag = ""
        opp_name = ""
        if opp_raw:
            opp_norm = normalize_name(opp_raw)
            opp_player = name_index.get(opp_norm)
            opp_team_tag = opp_player["team_tag"] if opp_player else "?"
            opp_name = opp_player["player_name"] if opp_player else opp_raw

        rows.append(
            {
                "section": r.get("section", ""),
                "half": r.get("half", ""),
                "round_no": r.get("round_no", ""),
                "battle_no": r.get("battle_no", ""),
                "round": r["round"],
                "date": r["date"],
                "team_tag": team_tag,
                "player_name": name,
                "class": r["class"],
                "result": r["result"],
                "point": r["point"],
                "opponent_team_tag": opp_team_tag,
                "opponent_name": opp_name,
                "opponent_class": r.get("opponent_class") or "",
            }
        )
    return rows


def load_existing_history():
    if not os.path.exists(HISTORY_CSV):
        return []
    with open(HISTORY_CSV, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def merge(existing_rows, new_rows):
    key = lambda r: (r["date"], r["team_tag"], r["player_name"], r["metric"], r["period"])
    merged = {key(r): r for r in existing_rows}
    for r in new_rows:
        merged[key(r)] = {k: str(r[k]) for k in FIELDNAMES}
    # 日付→選手→指標の順で安定ソート
    return sorted(merged.values(), key=lambda r: (r["date"], r["team_tag"], r["player_name"], r["metric"], r["period"]))


def load_existing_matches():
    if not os.path.exists(MATCH_RESULTS_CSV):
        return []
    with open(MATCH_RESULTS_CSV, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _match_key(r):
    """試合結果の重複排除キー（scrape日は含めない）。
    以前は (round, player_name) だったが、roundは日付文字列なので、パースが壊れて
    round="match_14" / player_name="ネメシス" のようなゴミ行が出た時に「毎回新しいキー」に
    なってしまい、既存行を上書きせず153行も積み上がった。節・前半後半・ROUND・BATTLE番号を
    キーにすることで、同じバトルは必ず同じキーになり増殖しない。"""
    return (str(r.get("section", "")), str(r.get("half", "")),
            str(r.get("round_no", "")), str(r.get("battle_no", "")), r["player_name"])


def _is_sane(r):
    """旧スキーマの行やパース事故で入り込んだ行を落とすための最低限の判定。
    section が数字で入っていて、resultがWIN/LOSEであることを要求する。"""
    return str(r.get("section", "")).isdigit() and r.get("result") in ("WIN", "LOSE")


def merge_matches(existing_rows, new_rows):
    """同じ試合を毎日再取得しても「新しい試合として増殖」しないように重複排除する。
    既存行のうち、節番号を持たない旧スキーマの行やパース事故のゴミ行はここで落とす。"""
    merged = {}
    for r in existing_rows:
        if _is_sane(r):
            merged[_match_key(r)] = r
    for r in new_rows:
        merged[_match_key(r)] = {k: str(r[k]) for k in MATCH_FIELDNAMES}
    return sorted(
        merged.values(),
        key=lambda r: (int(r["section"]), r["half"] == "後半", int(r["round_no"]),
                       int(r["battle_no"]), r["team_tag"], r["player_name"]),
    )


def main():
    date_str = today_str()
    players = load_players()
    name_index = build_name_index(players)

    reference_snap = latest_snapshot("reference", date_str)
    svlabo_snap = latest_snapshot("svlabo", date_str)
    ps_snap = latest_snapshot("ps_results", date_str)
    youtube_snap = latest_snapshot("youtube", date_str)

    new_rows = []
    new_rows += rows_from_reference(reference_snap, name_index)
    new_rows += rows_from_svlabo(svlabo_snap)
    new_rows += rows_from_youtube(youtube_snap)

    print(f"[update_history] {len(new_rows)} new rows from today's snapshots")
    if not new_rows:
        print("[update_history] nothing to merge (no snapshots found for today)", file=sys.stderr)

    existing = load_existing_history()
    merged = merge(existing, new_rows)

    os.makedirs(DATA_DIR, exist_ok=True)
    with open(HISTORY_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(merged)

    print(f"[update_history] history.csv now has {len(merged)} rows")

    # 試合結果は別ファイルに分けて統合する（history.csvには入れない。理由はdocstring参照）
    new_matches = match_rows_from_ps_results(ps_snap, name_index)
    existing_matches = load_existing_matches()
    merged_matches = merge_matches(existing_matches, new_matches)

    with open(MATCH_RESULTS_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=MATCH_FIELDNAMES)
        writer.writeheader()
        writer.writerows(merged_matches)

    print(f"[update_history] match_results.csv now has {len(merged_matches)} rows "
          f"({len(new_matches)} seen in today's snapshot)")


if __name__ == "__main__":
    main()
