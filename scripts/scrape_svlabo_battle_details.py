"""svlabo.jpの「Premier Series 26-27 N節 試合詳細結果＆配信時間指定URL」記事
（例: https://svlabo.jp/blog-entry-1793.html）から、節ごとの試合詳細（誰が・何節の・何ROUNDの・
何バトル目で・どのクラスを使い（そして登録していたが使わなかったクラスは何か）・勝敗はどうだったか・
配信のどの時間から見られるか）を取り込み、data/battle_details.csv に追記する。

--- 自動取得ではなく手動トリガーな理由 ---
このデータはsvlabo.jpが「1節分まとまったら記事を書く」形で不定期に公開するもので、
記事URL（blog-entry-XXXX.html）に規則性が無く新記事を自動発見する手段が無い。
そのため、新しい節の記事が公開されたら、そのURLを引数で渡して手動実行する運用にしている
（scrape_svlabo.pyと同じ考え方。README「節別詳細結果について」参照）。

--- パース方式について ---
記事ページには、表示用HTMLとは別に <script> タグの中に生の対戦データがJSのオブジェクトとして
埋め込まれている（tour_info: チームごとの登録デッキ一覧、battle_info: バトルごとの結果）。
これはブラウザで実際にページを開いて調査して見つけたもので、公式に文書化されたAPIではない
（svlabo.jpのブログ実装が変われば変わりうる。取得できなくなったら再調査が必要）。

battle_info の1要素（1バトル分）のキー:
    team1, team2   : 対戦した2チームのteam_tag（"VL"=VARREL, "RID"=RIDDLE ORDERの表記ゆれあり。
                      scripts/common.pyのTEAM_TAG_ALIASESと同じ変換をここでも行う）
    pro1, pro2     : 選手名（チーム戦のバトルは両方とも空文字列。「チームバトル」として扱う）
    use1, use2     : 実際に使用したクラスのclass_no（1〜7、後述のCLASS_MAP参照）
    decks1, decks2 : そのバトルで登録していたクラスの全pool（class_noを連結した文字列。例"247"）
                      → use1/use2はこのpoolの中の1つ。pool - useが「登録したが使わなかったクラス」
    fise           : team1側が先攻だったか後攻だったか
    winlose        : team1側の勝敗（team2側はその逆）
    URL            : 配信動画のその バトル開始時点のタイムスタンプ（秒）。動画ID自体はbattle_infoには
                      無く、ページ上の実際の<a>要素のhref（youtube.com/watch?v=...&t=...）から取る

tour_info の1要素（1チーム分）:
    team, deck: [{class_no, deck_name}, ...]  ← 7クラス分（エルフ〜ネメシス、class_no 1〜7固定）
    デッキ名（アーキタイプ名）はチーム・節によって変わるが、class_no→クラスの対応(1=エルフ...7=ネメシス)
    は全チーム・全節で共通だったため、これをCLASS_MAPとしてハードコードしている。

配信URLの動画ID自体は各バトル要素からは取れないため、ページ内の「配信URL (時間指定)」
リンクの実際のhrefを順番に読み、8〜9バトル単位（前半戦/後半戦）でグルーピングしている
（1本の配信VODを前半戦・後半戦それぞれで通しで使っているため）。
"""
import re
import sys

from playwright.sync_api import sync_playwright

from common import DATA_DIR, TEAM_TAG_ALIASES
import csv
import os

BATTLE_DETAILS_CSV = os.path.join(DATA_DIR, "battle_details.csv")

CLASS_MAP = {1: "エルフ", 2: "ロイヤル", 3: "ウィッチ", 4: "ドラゴン", 5: "ナイトメア", 6: "ビショップ", 7: "ネメシス"}

FIELDNAMES = [
    "section", "half", "round_no", "battle_no", "team1", "team2",
    "player1", "player2", "fise", "winlose",
    "class1_used", "class1_pool", "class2_used", "class2_pool", "video_url",
]


def norm_team(tag: str) -> str:
    # TEAM_TAG_ALIASESは {自サイト表記: 外部サイト表記} なので、逆引きする
    for our_tag, alias in TEAM_TAG_ALIASES.items():
        if alias == tag:
            return our_tag
    return tag


def pool_names(digits: str) -> str:
    return "|".join(CLASS_MAP[int(d)] for d in digits)


def scrape_section(page, url: str, section: int):
    page.goto(url, wait_until="networkidle")
    page.wait_for_timeout(1000)

    battle_info = page.evaluate("() => battle_info")
    if not battle_info:
        print(f"[svlabo_battle_details] battle_info not found on {url}", file=sys.stderr)
        return []

    # 「配信URL (時間指定)」リンクの実hrefから動画IDを順番に取得する
    video_ids = page.evaluate("""
        () => Array.from(document.querySelectorAll('a'))
            .filter(a => a.textContent.includes('配信URL'))
            .map(a => new URL(a.href).searchParams.get('v'))
    """)
    if len(video_ids) != len(battle_info):
        print(
            f"[svlabo_battle_details] WARNING: video link count ({len(video_ids)}) != "
            f"battle_info count ({len(battle_info)}) on {url}. Video links may be misaligned.",
            file=sys.stderr,
        )

    # team1/team2の組が変わるたびに新しい「ROUND」とみなす（記事の見出し前半戦/後半戦R1/R2に対応）。
    # ROUND数は4つ固定という保証はない（節によって前半/後半それぞれ何組かは変わりうる）ため、
    # 「同じチーム対戦カードが連続している間は同じROUND」というグルーピングにしている。
    rows = []
    round_idx = 0
    half = "前半戦"
    prev_pair = None
    seen_pairs_in_half = 0
    battle_no = 0
    half_switch_pair_count = None  # 前半戦のROUND数が分かった後、後半戦への切り替えは呼び出し側で明示的に指定できないので、
    # ここではチームの並びが一周して重複し始めたタイミングでは判定できない。そのため簡便に
    # 「pair(team1,team2)が変わるたび round_no を進め、round_noが3つ目に入ったら後半戦」とはせず、
    # 実際のROUND境界はチームの組が変わったタイミングのみで判定する。前半/後半の境目は
    # 「ROUNDが2つ終わったら後半戦」という前提（8チーム→4カード、前半2カード+後半2カードの構成）で扱う。
    pair_count = 0

    for i, b in enumerate(battle_info):
        pair = (b["team1"], b["team2"])
        if pair != prev_pair:
            pair_count += 1
            round_idx += 1
            battle_no = 0
            prev_pair = pair
            if pair_count == 3:
                half = "後半戦"
                round_idx = 1
        battle_no += 1

        vid = video_ids[i] if i < len(video_ids) else None
        t = b.get("URL")
        video_url = f"https://www.youtube.com/watch?v={vid}&t={t}" if vid and t is not None else ""

        rows.append({
            "section": section,
            "half": half,
            "round_no": round_idx if round_idx <= 2 else round_idx - 2,
            "battle_no": battle_no,
            "team1": norm_team(b["team1"]),
            "team2": norm_team(b["team2"]),
            "player1": b.get("pro1") or "チームバトル",
            "player2": b.get("pro2") or "チームバトル",
            "fise": b.get("fise", ""),
            "winlose": b.get("winlose", ""),
            "class1_used": CLASS_MAP.get(int(b["use1"])) if b.get("use1") else "",
            "class1_pool": pool_names(b.get("decks1", "")),
            "class2_used": CLASS_MAP.get(int(b["use2"])) if b.get("use2") else "",
            "class2_pool": pool_names(b.get("decks2", "")),
            "video_url": video_url,
        })

    return rows


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


def main():
    args = sys.argv[1:]
    if not args or len(args) % 2 != 0:
        print(
            "Usage: python scrape_svlabo_battle_details.py <url1> <section1> [<url2> <section2> ...]\n"
            "Example: python scrape_svlabo_battle_details.py "
            "https://svlabo.jp/blog-entry-1793.html 1 https://svlabo.jp/blog-entry-1800.html 2",
            file=sys.stderr,
        )
        sys.exit(1)

    pairs = [(args[i], int(args[i + 1])) for i in range(0, len(args), 2)]

    new_rows = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(locale="ja-JP")
        for url, section in pairs:
            rows = scrape_section(page, url, section)
            print(f"[svlabo_battle_details] {url} (section={section}): {len(rows)} battles parsed")
            new_rows.extend(rows)
        browser.close()

    if not new_rows:
        print("[svlabo_battle_details] nothing parsed, existing file left untouched", file=sys.stderr)
        sys.exit(1)

    existing = load_existing()
    merged = merge(existing, new_rows)

    os.makedirs(DATA_DIR, exist_ok=True)
    with open(BATTLE_DETAILS_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(merged)

    print(f"[svlabo_battle_details] battle_details.csv now has {len(merged)} rows")


if __name__ == "__main__":
    main()
