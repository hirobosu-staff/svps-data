"""svlabo.jp の「CRランキングまとめ」から、全期間×全クラスのランクマッチ上位（各100位前後）を取り、
data/svlabo_leaderboards.csv を丸ごと作り直す（BEYOND ページ・比較ページの BEYOND 回数の元データ）。

以前は手動運用（Chrome で開いてデータを書き出す）だったが、2026-11-04 に自動化した。

仕組み:
    1. https://svlabo.jp/blog-entry-1608.html を取得し、ページが読み込んでいるデータファイル
       https://blog-imgs-NNN.fc2.com/d/u/e/duesemi/rank_YYMMDD.js の URL を見つける
       （ファイル名の日付とサーバー番号は更新のたびに変わる）。
    2. その JS の中の tmpRanks = { "期間名": [ {cls, rank, rate, name}, ... ], ... } を読む。
       （ページ側は rankData という変数にこれを移して使う。JS ファイル内の変数名は tmpRanks。
       2026-11-04 の自動化時は rankData と思い込んでいて、実ファイルで確かめていなかったため毎日失敗していた。
       念のため rankData も探す。）
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
RANK_VAR_NAMES = ("tmpRanks", "rankData")  # JS ファイル内でランキングを持つ変数名（先に見つかった方を使う）
FIELDS = ["period", "class", "rank", "team_tag", "player_name", "rating"]

# 検算のしきい値（これを下回ったら取得失敗とみなし、既存CSVを残す）
MIN_PERIODS = 10
MIN_ROWS_PER_CLASS = 80


def decode_js(raw):
    """rank_YYMMDD.js のバイト列を文字列にする。

    このファイルは UTF-16（先頭に BOM 付き）で配信されている（2026-11 時点）。以前は UTF-8 と決め打ちで
    読んでいたため文字化けし、rankData が見つからずに毎日失敗していた。BOM を見て判定し、BOM が無くても
    NUL バイトが混ざっていれば UTF-16LE とみなす。どれでもなければ UTF-8。
    """
    if raw[:3] == b"\xef\xbb\xbf":
        return raw[3:].decode("utf-8")
    if raw[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return raw.decode("utf-16")
    if b"\x00" in raw[:200]:
        return raw.decode("utf-16-le")
    return raw.decode("utf-8")


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


def _skip_space_and_comments(src, j):
    n = len(src)
    while j < n:
        if src[j] in " \t\r\n":
            j += 1
        elif src.startswith("//", j):
            k = src.find("\n", j)
            j = n if k < 0 else k
        elif src.startswith("/*", j):
            k = src.find("*/", j + 2)
            j = n if k < 0 else k + 2
        else:
            break
    return j


JSON_ESCAPES = set('"\\/bfnrtu')


def js_object_to_json(src):
    """JS のオブジェクトリテラルを JSON として読めるように直す（まず素のまま試し、だめなら整形する）。

    文字列の外と中を1文字ずつ区別しながら、次を直す（文字列の中身には手を付けない）:
      - シングルクォートの文字列をダブルクォートに
      - JSON に無いエスケープ（\\' や \\x41 など）を JSON で読める形に。
        2026-11-17 に「FOR\\'E｜rairo」という名前の \\' で読み込みが失敗していた
      - 引用符の無いキー（{cls:1} の cls）に引用符を付ける
      - 閉じかっこ直前のカンマを消す、// と /* */ のコメントを消す
    """
    try:
        return json.loads(src)
    except ValueError:
        pass
    out, i, n, quote = [], 0, len(src), None
    while i < n:
        c = src[i]
        if quote:
            if c == "\\" and i + 1 < n:
                nxt = src[i + 1]
                if nxt == "'":
                    out.append("'")                       # \\' は ' でよい
                elif nxt == '"':
                    out.append('\\"')
                elif nxt in JSON_ESCAPES:
                    out.append(c + nxt)
                elif nxt == "x" and i + 3 < n:
                    out.append("\\u00" + src[i + 2:i + 4])
                    i += 4
                    continue
                elif nxt == "0":
                    out.append("\\u0000")
                elif nxt in "\r\n":
                    pass                                   # 行継続
                else:
                    out.append(nxt)                        # JS ではそのままの文字になるエスケープ
                i += 2
                continue
            if c == quote:
                out.append('"')
                quote = None
            elif c == '"':
                out.append('\\"')                          # シングルクォート文字列の中の "
            elif c in "\r\n":
                out.append("\\n")
            else:
                out.append(c)
            i += 1
            continue
        if c in "\"'":
            quote = c
            out.append('"')
            i += 1
        elif c == "/" and src.startswith("//", i):
            j = src.find("\n", i)
            i = n if j < 0 else j
        elif c == "/" and src.startswith("/*", i):
            j = src.find("*/", i + 2)
            i = n if j < 0 else j + 2
        elif c == ",":
            j = _skip_space_and_comments(src, i + 1)
            if j < n and src[j] in "}]":
                i += 1                                     # 閉じかっこ直前のカンマ
            else:
                out.append(c)
                i += 1
        elif c.isalpha() or c in "_$":
            j = i
            while j < n and (src[j].isalnum() or src[j] in "_$"):
                j += 1
            word = src[i:j]
            k = j
            while k < n and src[k] in " \t\r\n":
                k += 1
            out.append(f'"{word}"' if k < n and src[k] == ":" else word)
            i = j
        else:
            out.append(c)
            i += 1
    return json.loads("".join(out))


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
    js_text = decode_js(js.content)
    src = None
    for var_name in RANK_VAR_NAMES:
        src = extract_object(js_text, var_name)
        if src:
            break
    if not src:
        print(f"[svlabo_ranks] {'/'.join(RANK_VAR_NAMES)} not found in {js_url}. Head: {js_text[:300]!r}", file=sys.stderr)
        sys.exit(1)
    try:
        rank_data = js_object_to_json(src)
    except ValueError as e:
        print(f"[svlabo_ranks] could not parse {var_name} ({e}). Head: {src[:300]!r}", file=sys.stderr)
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
