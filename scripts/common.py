"""共通ユーティリティ。チーム略称の正規化やCSV書き出しなど、各スクレイピングスクリプトから使う。"""
import csv
import json
import os
import re
from datetime import date, datetime, timezone, timedelta

JST = timezone(timedelta(hours=9))

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(REPO_ROOT, "data")
SNAPSHOT_DIR = os.path.join(DATA_DIR, "snapshots")
PLAYERS_CSV = os.path.join(DATA_DIR, "players.csv")
HISTORY_CSV = os.path.join(DATA_DIR, "history.csv")

# players.csv (teams.json由来) のチーム略称と、外部サイト側の略称表記が異なる箇所の対応表。
# 例: RIDDLE ORDERは自サイトでは"RDL"、shadowverse-reference.com/svlabo.jpでは"RID"表記。
TEAM_TAG_ALIASES = {
    "RDL": "RID",   # RIDDLE ORDER
    "VRL": "VL",    # VARREL
    # CR / ZETA / DFM / MRG / RC / LVH は各サイトで表記が一致している
}


def today_str():
    return datetime.now(JST).strftime("%Y-%m-%d")


def load_players():
    """data/players.csv を読み込み、
    [{team_tag, team_name, player_name, x_handle, x_url, youtube_url, twitch_url, ps_slug}, ...] を返す。
    ps_slug は ps.shadowverse-wb.com/26-27/teams/{ps_slug} の選手個人ページURLに使うスラッグ
    （scrape_player_images.py が選手写真を取得する際に使用）。"""
    with open(PLAYERS_CSV, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def normalize_name(name: str) -> str:
    """サイト間の表記ゆれを吸収するための緩い正規化（全角/半角スペース除去、大文字化など）。
    厳密な同一判定ではなく、あくまで突き合わせの補助。"""
    if not name:
        return ""
    name = name.strip()
    name = name.replace("　", "").replace(" ", "")
    return name.lower()


def build_name_index(players):
    """player_name(正規化) -> player_dict の索引。表記ゆれ対策として複数キーを登録する。"""
    idx = {}
    for p in players:
        keys = {normalize_name(p["player_name"])}
        idx.update({k: p for k in keys if k})
    return idx


def ensure_dirs():
    os.makedirs(SNAPSHOT_DIR, exist_ok=True)


def save_snapshot(source: str, rows: list):
    """スクレイピング結果を data/snapshots/{source}_{date}.json に保存する（デバッグ・再取得用の生データ）。"""
    ensure_dirs()
    path = os.path.join(SNAPSHOT_DIR, f"{source}_{today_str()}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)
    print(f"[{source}] saved {len(rows)} rows -> {path}")
    return path


def parse_number(s: str):
    """'34,703' や '82.5' のような文字列を数値に変換する。変換できなければNoneを返す。"""
    if s is None:
        return None
    s = s.strip().replace(",", "")
    if s in ("", "-", "―", "該当データなし"):
        return None
    try:
        if "." in s:
            return float(s)
        return int(s)
    except ValueError:
        return None
