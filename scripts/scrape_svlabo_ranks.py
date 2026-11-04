"""svlabo.jp の「CRランキングまとめ」から、全期間×全クラスのランクマッチ上位（各100位前後）を取り、
data/svlabo_leaderboards.csv を丸ごと作り直す（BEYOND ページ・比較ページの BEYOND 回数の元データ）。

以前は手動運用（Chrome で開いてデータを書き出す）だったが、2026-11-04 に自動化した。

仕組み:
    1. https://svlabo.jp/blog-entry-1608.html を取得し、ページが読み込んでいるデータファイル
       https://blog-imgs-NNN.fc2.com/d/u/e/duesemi/rank_YYMMDD.js の URL を見つける
       （ファイル名の日付とサーバー番号は更新のたびに変わる）。
    2. その JS の中の rankData = { "期間名": [ {cls, rank, rate, name}, ... ], ... } を読む。
       JS を実行はせず、テキストとして切り出して JSON として読む（第三者のコードを Actions で動かさないため）。
       cls はクラス番号（1=エルフ 2=ロイヤル 3=ウィッチ 4=ドラゴン 5=ナイトメア 6=ビショップ 7=ネメシス）、
       name は「TAG｜名前」の形（最初の「｜」でチームタグと名前に分ける）。
    3. 検算に通ったときだけ CSV を書き換える。通らなければ既存の CSV をそのまま残して終了する。

svlabo は過去の期間も後から修正することがあるので、追記ではなく毎回まるごと作り直す。
"""
import csv
import json
import os
import re
import sys

import requests

from common import DATA_DIR, save_snapshot

OUT_CSV = os.path.join(DATA_DIR, "svlabo_leaderboards.csv")
ENTRY_URL = "https://svlabo.jp/blog-entry-1608.html"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; svps-tracker-bot/1.0)"}
RANK_JS_RE = re.compile(r"https?://blog-imgs-\d+\.fc2\.com/d/u/e/duesemi/rank_\d+\.js")
CLASSES = {1: "エルフ", 2: "ロイヤル", 3: "ウィッチ", 4: "ドラゴン", 5: "ナイトメア", 6: "ビショップ", 7: "ネメシス"}
FIELDS = ["period", "class", "rank", "team_tag", "player_name", "rating"]

# 検算のしきい値（これを下回ったら取得失敗とみなし、既存CSVを残す）
MIN_PERIODS = 10
MIN_ROWS_PER_CLASS = 80


def extract_object(text, var_name):
    """'rankData = { ... }' の { ... } 部分を、文字列の中の括弧に惑わされないように切り出す。"""
    m = re.search(r"\b" + re.escape(var_name) + r"\s*=\s*\{", text)
    if not m:
        return None
    start = m.end() - 1
    depth, i, quote = 0, start, None
    while i < len(text):
        c = text[i]
        if quote:
            if c == "\\":
                i += 2
                continue
            if c == quote:
                quote = None
        elif c in "\"'`":
            quote = c
        elif c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
        i += 1
    return None


def js_object_to_json(src):
    """JS のオブジェクトリテラルを JSON として読めるように直す（まず素のまま試し、だめなら整形する）。"""
    try:
        return json.loads(src)
    except ValueError:
        pass
    out, i, quote = [], 0, None
    # 1文字ずつ見て、シングルクォート文字列をダブルクォートに直す
    while i < len(src):
        c = src[i]
        if quote:
            if c == "\\" and i + 1 < len(src):
                nxt = src[i + 1]
                # シングルクォート文字列の中の \' は、ダブルクォートに直した後はただの ' でよい
                out.append("'" if (nxt == "'" and quote == "'") else c + nxt)
                i += 2
                continue
            if c == quote:
                out.append('"')
                quote = None
            elif c == '"' and quote == "'":
                out.append('\\"')
            else:
                out.append(c)
        elif c in "\"'":
            quote = c
            out.append('"')
        else:
            out.append(c)
        i += 1
    fixed = "".join(out)
    fixed = re.sub(r'([{,]\s*)([A-Za-z_$][\w$]*)\s*:', r'\1"\2":', fixed)  # 引用符なしのキー
    fixed = re.sub(r",\s*([}\]])", r"\1", fixed)                           # 末尾のカンマ
    return json.loads(fixed)


def build_rows(rank_data):
    rows = []
    for period, entries in rank_data.items():
        for e in entries:
            cls = CLASSES.get(int(e["cls"]))
            if not cls:
                continue
            # サイト側のCSV読み込み（common.js の parseCSV）はカンマを区切りとしか扱わないので、
            # 名前に含まれるカンマは全角に、改行は空白に置き換えておく
            name = str(e.get("name", "")).replace(",", "，").replace("\r", " ").replace("\n", " ")
            tag, player = (name.split("｜", 1) if "｜" in name else ("", name))
            rows.append({"period": period, "class": cls, "rank": int(e["rank"]),
                         "team_tag": tag, "player_name": player, "rating": int(e["rate"])})
    return rows


def validate(rows):
    periods = []
    for r in rows:
        if r["period"] not in periods:
            periods.append(r["period"])
    if len(periods) < MIN_PERIODS:
        return f"periods too few: {len(periods)}"
    for p in periods:
        for cls in CLASSES.values():
            n = sum(1 for r in rows if r["period"] == p and r["class"] == cls)
            if n < MIN_ROWS_PER_CLASS:
                return f"too few rows: {p} {cls} = {n}"
    return None


def main():
    page = requests.get(ENTRY_URL, headers=HEADERS, timeout=30)
    page.raise_for_status()
    m = RANK_JS_RE.search(page.text)
    if not m:
        print("[svlabo_ranks] rank_YYMMDD.js not found in the entry page. Keeping the existing CSV.", file=sys.stderr)
        sys.exit(1)
    js_url = m.group(0)
    js = requests.get(js_url, headers={**HEADERS, "Referer": ENTRY_URL}, timeout=30)
    js.raise_for_status()
    js.encoding = "utf-8"
    src = extract_object(js.text, "rankData")
    if not src:
        print(f"[svlabo_ranks] rankData not found in {js_url}. Head: {js.text[:300]!r}", file=sys.stderr)
        sys.exit(1)
    try:
        rank_data = js_object_to_json(src)
    except ValueError as e:
        print(f"[svlabo_ranks] could not parse rankData ({e}). Head: {src[:300]!r}", file=sys.stderr)
        sys.exit(1)

    rows = build_rows(rank_data)
    problem = validate(rows)
    summary = {"js_url": js_url, "periods": list(rank_data.keys()), "rows": len(rows), "problem": problem}
    save_snapshot("svlabo_ranks", [summary])
    if problem:
        print(f"[svlabo_ranks] validation failed ({problem}). Keeping the existing CSV.", file=sys.stderr)
        sys.exit(1)

    tmp = OUT_CSV + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="") as f:  # 既存ファイルと同じく CRLF・BOMなし
        w = csv.DictWriter(f, fieldnames=FIELDS, lineterminator="\r\n")
        w.writeheader()
        w.writerows(rows)
    os.replace(tmp, OUT_CSV)
    print(f"[svlabo_ranks] {js_url}: {len(rank_data)} periods, {len(rows)} rows -> {OUT_CSV}")


if __name__ == "__main__":
    main()
