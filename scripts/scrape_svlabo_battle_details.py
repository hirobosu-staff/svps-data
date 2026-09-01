"""svlabo.jpの「Premier Series 26-27 N節 試合詳細結果＆配信時間指定URL」記事から、
節ごとの試合詳細（誰が・何節の・何ROUNDの・何バトル目で・どのクラスを使い、登録していたが
使わなかったクラスは何か・勝敗はどうだったか・配信のどの時間から見られるか）を取り込み、
data/battle_details.csv を更新する。

--- 実行方法 ---
    python scrape_svlabo_battle_details.py                      # カテゴリ巡回（毎日の自動実行用）
    python scrape_svlabo_battle_details.py <url> <section>[:<half>] ...   # URL直指定（手動）

--- カテゴリ巡回について ---
以前は「記事URL(blog-entry-XXXX.html)に規則性が無く新記事を自動発見する手段が無い」として
手動運用していたが、カテゴリページ
    https://svlabo.jp/blog-category-61.html   （プレミアシリーズ）
がJS描画ではない素のHTMLで、記事タイトルとURLがそのまま並んでいることを確認したので自動化した。
タイトルの命名が一貫している。

    Premier Series 26-27 7節 前半戦 試合詳細結果＆配信時間指定URL
    Premier Series 26-27 6節      試合詳細結果＆配信時間指定URL   ← 1日開催の節は前半/後半が付かない
    Premier Series 26-27 5節 後半戦 試合詳細結果＆配信時間指定URL

ここから節番号と前半/後半を取り出せるので、以前は引数で渡していたhalfの指定も不要になった。
同じカテゴリには「試合結果＆デッキ分布」「試合結果＆デッキリスト比較」「デッキリスト変化」等の
別記事も混ざるが、「試合詳細結果」という語で確実に絞り込める。
なおサイドバーの「最新記事」欄にも同じリンクが出るので、記事IDで重複排除する。

--- 未実施の記事を除外する仕組み（重要） ---
svlabo.jpは翌日以降の対戦分の記事を先に公開する。その時点では対戦カード・出場選手・登録クラスは
埋まっているが、結果は空になっている。

    未実施: {"pro1":"ふえた","pro2":"ミル","decks1":"567","use1":"0","use2":"0",
             "fise":"","winlose":"","URL":0}
    実施済: {"pro1":"空白","pro2":"Chappy","decks1":"247","use1":"4","use2":"3",
             "fise":"先攻","winlose":"WIN","URL":1926}

「配信URL (時間指定)」のリンク自体は未実施の記事にも出るので、リンクの有無では判定できない。
判定に使うのは次の2つ。

  1. 各バトルが実施済みか … winlose が WIN/LOSE で、use1/use2 が "0" でない
  2. 各ROUNDにチームバトルの行があるか … チーム戦は必ず1戦以上行われるため、
     決着した ROUND には pro1/pro2 が空の行（＝チームバトル）が必ず含まれる。
     未実施の記事は個人戦3枠しか用意されておらず、この行が存在しない。

1つでも未実施のバトルがある記事、またはチームバトル行が無いROUNDを含む記事は、
その記事を丸ごとスキップする（中途半端な状態で取り込まないため）。試合中に巡回して
前半だけ埋まった状態を掴んでも、翌日の巡回で完全な状態を取り込み直せる。

--- パース方式について ---
記事ページには表示用HTMLとは別に、対戦データそのものがJSオブジェクト（battle_info）として
<script>タグ内に埋め込まれている。これはブラウザで実際に開いて調査して見つけた構造で、
公式に文書化されたAPIではない（svlabo.jp側の実装が変われば取得できなくなる）。

battle_info の1要素（1バトル分）のキー:
    team1, team2   : 対戦した2チームのteam_tag（"VL"=VARREL, "RID"=RIDDLE ORDERの表記ゆれあり）
    pro1, pro2     : 選手名（チーム戦のバトルは両方とも空文字列）
    use1, use2     : 実際に使用したクラスのclass_no（1〜7。未実施は"0"）
    decks1, decks2 : そのバトルで登録していたクラスの全pool（class_noを連結した文字列。例"247"）
    fise           : team1側が先攻だったか後攻だったか（未実施は空）
    winlose        : team1側の勝敗（未実施は空）
    URL            : 配信動画のそのバトル開始時点のタイムスタンプ（秒。未実施は0）。
                      動画ID自体はbattle_infoには無く、ページ上の<a>のhrefから取る。
"""
import csv
import os
import re
import sys

import requests
from playwright.sync_api import sync_playwright

from common import DATA_DIR, TEAM_TAG_ALIASES

BATTLE_DETAILS_CSV = os.path.join(DATA_DIR, "battle_details.csv")

CATEGORY_URL_TMPL = "https://svlabo.jp/blog-category-61{suffix}.html"
# 毎日の巡回では新しい記事しか増えないので、先頭数ページ見れば十分（1ページ5件）。
CATEGORY_PAGES = 3
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; svps-tracker-bot/1.0)"}

# 記事一覧から <a href="...blog-entry-NNNN.html" ...>タイトル</a> を拾う。
# タイトル側にタグが挟まることがあるので、中身は緩く取ってから除タグする。
ANCHOR_RE = re.compile(r'<a[^>]*blog-entry-(\d+)\.html[^>]*>([\s\S]*?)</a>')
TAG_RE = re.compile(r"<[^>]*>")
# 「試合詳細結果」を含むものだけが対象。デッキ分布・デッキリスト比較の記事は除外される。
TITLE_RE = re.compile(r"Premier Series 26-27\s+(\d+)節\s*(前半戦|後半戦)?\s*試合詳細結果")

CLASS_MAP = {1: "エルフ", 2: "ロイヤル", 3: "ウィッチ", 4: "ドラゴン", 5: "ナイトメア", 6: "ビショップ", 7: "ネメシス"}

FIELDNAMES = [
    "section", "half", "round_no", "battle_no", "team1", "team2",
    "player1", "player2", "fise", "winlose",
    "class1_used", "class1_pool", "class2_used", "class2_pool", "video_url",
]

TEAM_BATTLE_LABEL = "チームバトル"


def norm_team(tag: str) -> str:
    # TEAM_TAG_ALIASESは {自サイト表記: 外部サイト表記} なので、逆引きする
    for our_tag, alias in TEAM_TAG_ALIASES.items():
        if alias == tag:
            return our_tag
    return tag


def pool_names(digits: str) -> str:
    return "|".join(CLASS_MAP[int(d)] for d in digits if d.isdigit() and int(d) in CLASS_MAP)


# ---------- 記事の自動発見 ----------

def discover_articles():
    """カテゴリページを巡回して、[(url, section, half), ...] を新しい順で返す。"""
    found = {}
    order = []
    for page in range(CATEGORY_PAGES):
        suffix = "" if page == 0 else f"-{page}"
        url = CATEGORY_URL_TMPL.format(suffix=suffix)
        try:
            resp = requests.get(url, timeout=30, headers=HEADERS)
            resp.raise_for_status()
        except Exception as e:
            print(f"[svlabo_battle_details] カテゴリページ取得失敗 {url}: {e}", file=sys.stderr)
            continue
        for entry_id, raw_title in ANCHOR_RE.findall(resp.text):
            title = TAG_RE.sub("", raw_title).strip()
            m = TITLE_RE.search(title)
            if not m:
                continue
            if entry_id in found:   # サイドバーの「最新記事」にも同じリンクが出るため
                continue
            found[entry_id] = True
            order.append((f"https://svlabo.jp/blog-entry-{entry_id}.html",
                          int(m.group(1)), m.group(2) or "", title))
    return order


# ---------- 実施済み判定 ----------

def battle_is_played(b):
    """1バトルが実施済みか。未実施の記事では use が "0"、fise/winlose が空、URLが0になる。"""
    if b.get("winlose") not in ("WIN", "LOSE"):
        return False
    return str(b.get("use1")) != "0" and str(b.get("use2")) != "0"


def article_is_complete(battle_info):
    """記事を取り込んでよいか。理由の文字列（問題なければNone）を返す。"""
    if not battle_info:
        return "battle_infoが空"

    unplayed = sum(1 for b in battle_info if not battle_is_played(b))
    if unplayed:
        return f"未実施のバトルが{unplayed}/{len(battle_info)}件ある"

    # チーム戦は必ず1戦以上行われるので、決着したROUNDには必ずチームバトルの行がある。
    # 未実施の記事は個人戦3枠しか用意されていないため、この行が無い。
    rounds = {}
    for b in battle_info:
        key = (b["team1"], b["team2"])
        rounds.setdefault(key, 0)
        if not b.get("pro1") and not b.get("pro2"):
            rounds[key] += 1
    missing = [f"{k[0]} vs {k[1]}" for k, n in rounds.items() if n == 0]
    if missing:
        return f"チームバトルの行が無いROUNDがある: {missing}"
    return None


# ---------- 記事1本のパース ----------

def scrape_section(page, url: str, section: int, half: str = None):
    """halfを指定するとその記事の全ROUNDをその前半戦/後半戦として扱う。
    Noneの場合は「1記事に4ROUND入っている」前提で自動判定する（1日開催の節向け）。"""
    page.goto(url, wait_until="networkidle")
    page.wait_for_timeout(1000)

    battle_info = page.evaluate("() => (typeof battle_info === 'undefined') ? null : battle_info")
    if battle_info is None:
        print(f"[svlabo_battle_details] battle_infoが見つからない: {url}", file=sys.stderr)
        return None

    reason = article_is_complete(battle_info)
    if reason:
        print(f"[svlabo_battle_details] SKIP {url}: {reason}")
        return None

    video_ids = page.evaluate("""
        () => Array.from(document.querySelectorAll('a'))
            .filter(a => a.textContent.includes('配信URL'))
            .map(a => new URL(a.href).searchParams.get('v'))
    """)
    if len(video_ids) != len(battle_info):
        print(
            f"[svlabo_battle_details] WARNING: 配信リンク数({len(video_ids)}) != "
            f"バトル数({len(battle_info)}) : {url}",
            file=sys.stderr,
        )

    fixed_half = half
    rows = []
    round_idx = 0
    cur_half = fixed_half or "前半戦"
    prev_pair = None
    battle_no = 0
    pair_count = 0

    for i, b in enumerate(battle_info):
        pair = (b["team1"], b["team2"])
        if pair != prev_pair:
            pair_count += 1
            round_idx += 1
            battle_no = 0
            prev_pair = pair
            if fixed_half is None and pair_count == 3:
                cur_half = "後半戦"
                round_idx = 1
        battle_no += 1

        vid = video_ids[i] if i < len(video_ids) else None
        t = b.get("URL")
        video_url = f"https://www.youtube.com/watch?v={vid}&t={t}" if vid and t else ""

        rows.append({
            "section": section,
            "half": cur_half,
            "round_no": round_idx if (fixed_half or round_idx <= 2) else round_idx - 2,
            "battle_no": battle_no,
            "team1": norm_team(b["team1"]),
            "team2": norm_team(b["team2"]),
            "player1": b.get("pro1") or TEAM_BATTLE_LABEL,
            "player2": b.get("pro2") or TEAM_BATTLE_LABEL,
            "fise": b.get("fise", ""),
            "winlose": b.get("winlose", ""),
            "class1_used": CLASS_MAP.get(int(b["use1"])),
            "class1_pool": pool_names(b.get("decks1", "")),
            "class2_used": CLASS_MAP.get(int(b["use2"])),
            "class2_pool": pool_names(b.get("decks2", "")),
            "video_url": video_url,
        })

    return rows


# ---------- CSV入出力 ----------

def load_existing():
    if not os.path.exists(BATTLE_DETAILS_CSV):
        return []
    with open(BATTLE_DETAILS_CSV, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def merge(existing_rows, new_rows):
    key = lambda r: (str(r["section"]), r["half"], str(r["round_no"]), str(r["battle_no"]))
    merged = {key(r): r for r in existing_rows}
    for r in new_rows:
        merged[key(r)] = {k: str(r[k]) for k in FIELDNAMES}
    return sorted(
        merged.values(),
        key=lambda r: (int(r["section"]), r["half"] == "後半戦", int(r["round_no"]), int(r["battle_no"])),
    )


def existing_keys(rows):
    """既に取り込み済みの (section, half) の集合。巡回時に再取得を省くために使う。"""
    return {(str(r["section"]), r["half"]) for r in rows}


# ---------- エントリポイント ----------

def parse_args(args):
    """<url> <section> または <url> <section>:<half> の並びを解釈する。"""
    if len(args) % 2 != 0:
        return None
    pairs = []
    for i in range(0, len(args), 2):
        url, spec = args[i], args[i + 1]
        half = None
        if ":" in spec:
            spec, half = spec.split(":", 1)
            if half not in ("前半戦", "後半戦"):
                print(f"[svlabo_battle_details] 不正なhalf指定: {half}", file=sys.stderr)
                return None
        pairs.append((url, int(spec), half))
    return pairs


def targets_from_crawl(existing):
    """カテゴリ巡回で見つけた記事のうち、まだCSVに入っていない節だけを対象にする。"""
    have = existing_keys(existing)
    targets = []
    for url, section, half_label, title in discover_articles():
        # タイトルの「前半戦/後半戦」はCSVのhalf列と同じ表記。1日開催の節は空。
        half = half_label or None
        csv_half = half_label if half_label else "前半戦"  # 1日開催の節は前半戦/後半戦に分かれて入る
        if (str(section), csv_half) in have:
            print(f"[svlabo_battle_details] 取り込み済みなのでスキップ: {title}")
            continue
        targets.append((url, section, half, title))
    return targets


def main():
    args = sys.argv[1:]
    existing = load_existing()

    if args:
        pairs = parse_args(args)
        if pairs is None:
            print(
                "Usage: python scrape_svlabo_battle_details.py "
                "[<url1> <section1>[:<half1>] <url2> <section2>[:<half2>] ...]\n"
                "  引数なしで実行するとカテゴリページ(blog-category-61)を巡回して自動取得する。\n"
                "  <half> は 前半戦 / 後半戦。省略すると1記事に4ROUND入っている前提で自動判定する。",
                file=sys.stderr,
            )
            sys.exit(1)
        targets = [(u, s, h, u) for u, s, h in pairs]
    else:
        targets = targets_from_crawl(existing)
        if not targets:
            print("[svlabo_battle_details] 新しく取り込む記事は無し")
            return

    new_rows = []
    skipped = 0
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(locale="ja-JP")
        for url, section, half, title in targets:
            rows = scrape_section(page, url, section, half)
            if rows is None:
                skipped += 1
                continue
            label = f"第{section}節" + (half or "(前半後半は自動判定)")
            print(f"[svlabo_battle_details] {title} -> {label}: {len(rows)}バトル")
            new_rows.extend(rows)
        browser.close()

    if not new_rows:
        print(f"[svlabo_battle_details] 取り込む行が無かった（スキップ{skipped}件）。既存CSVはそのまま")
        return

    merged = merge(existing, new_rows)
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(BATTLE_DETAILS_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(merged)

    print(f"[svlabo_battle_details] battle_details.csv: {len(existing)} -> {len(merged)}行 "
          f"(新規{len(new_rows)}バトル / スキップ{skipped}記事)")


if __name__ == "__main__":
    main()
