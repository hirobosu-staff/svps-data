"""チーム順位（win/lose/diff/battlepoint）を取得する。

このリポジトリ独自の集計ではなく、あなたが別途運用している公開ツール
https://uthomeless-public-tool.github.io/2026ps/ が公開しているJSON
（https://uthomeless-public-tool.github.io/2026ps/data/result.json）をそのまま取得して
data/result.json に保存する。スキーマはこのリポジトリのdata/result.jsonと完全に同じ
（{status, teams: [{id, win, lose, diff, battlepoint}], confirmed_odds}）なので変換不要。

id(1〜8)とteam_tagの対応は common.RESULT_ID_TO_TAG系（site/common.jsのRESULT_ID_TO_TAGと同じ）:
1=CR, 2=ZETA, 3=DFM, 4=VRL, 5=MRG, 6=RC, 7=RDL, 8=LVH

取得に失敗した場合（サイト側が落ちている、レスポンスが想定外の形式など）は、既存の
data/result.json をそのまま残す（上書きしない）。手動で編集した値を誤って空/古い値で
潰さないようにするための安全策。
"""
import json
import sys

import requests

from common import DATA_DIR
import os

SOURCE_URL = "https://uthomeless-public-tool.github.io/2026ps/data/result.json"
RESULT_JSON_PATH = os.path.join(DATA_DIR, "result.json")


def fetch_result():
    resp = requests.get(SOURCE_URL, timeout=30, headers={"User-Agent": "Mozilla/5.0 (compatible; svps-tracker-bot/1.0)"})
    resp.raise_for_status()
    data = resp.json()
    if not isinstance(data, dict) or not isinstance(data.get("teams"), list) or len(data["teams"]) != 8:
        raise ValueError(f"unexpected result.json shape: {data}")
    return data


def main():
    try:
        data = fetch_result()
    except Exception as e:
        print(f"[result] failed to fetch {SOURCE_URL}: {e}", file=sys.stderr)
        print("[result] keeping existing data/result.json untouched", file=sys.stderr)
        return

    os.makedirs(DATA_DIR, exist_ok=True)
    with open(RESULT_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"[result] saved -> {RESULT_JSON_PATH}")
    for t in data["teams"]:
        print(f"[result]   id={t.get('id')} win={t.get('win')} lose={t.get('lose')} diff={t.get('diff')} battlepoint={t.get('battlepoint')}")


if __name__ == "__main__":
    main()
