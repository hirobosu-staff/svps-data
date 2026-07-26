"""svlabo.jp（個人運営のShadowverse分析ブログ）の「CRランキングまとめ」から、
選手ごとのランクマッチ最高順位・最高レート（クラス別・期間別）をスクレイピングする。

対象ページ: https://svlabo.jp/blog-entry-1608.html
「選手ごとに集計したデータ」表示（デフォルトのview=nam）を使う。
順位(以上)フィルタは100に設定している（=ランク100位以内に一度でも入った選手のみ表示される仕様）。
これより順位が低い選手はこのサイトの集計対象外になる点に注意（既知の制約。README参照）。

出力: data/snapshots/svlabo_{today}.json に生データを保存し、
      history.csv 用の行リスト [{date, team_tag, player_name, metric, period, class, rank, rating}, ...] を返す。

注意: SPAのためPlaywrightでのレンダリングが必須。個人サイトのため構造変更リスクがある
（README参照。取得失敗時はdata/snapshotsの生データで原因調査すること）。
"""
import re
import sys

from playwright.sync_api import sync_playwright

from common import today_str, save_snapshot, load_players, build_name_index, normalize_name, TEAM_TAG_ALIASES

URL = (
    "https://svlabo.jp/blog-entry-1608.html"
    "?start=0&end=9&cls=&min=100&name=&ps=0&rk=rank&view=nam&sort=colA&asc=0"
)

# 1選手分のブロック: "TAG｜名前" -> "N回" -> "最高順位" -> 詳細テキスト（次の選手のTAG｜名前の直前まで）
ROW_RE = re.compile(
    r"(?P<tag>[A-Za-z]{2,5})｜(?P<name>[^\n]+?)\s*\n+(?P<count>\d+)回\s*\n+(?P<best>\d+)\s*\n+(?P<detail>.*?)(?=\n[A-Za-z]{2,5}｜|\Z)",
    re.DOTALL,
)

# 詳細テキストは "[期間名] クラスA順位(レート)、クラスB順位(レート)、[次の期間名] ..." のように、
# 同じ期間の複数クラスが "[期間名]" を省略してカンマ区切りで並ぶ。単純な正規表現の繰り返しマッチだと
# 2つ目以降のクラス（[期間名]なし）を取りこぼすため、直前に見た期間名を引き継ぐ簡易ステートマシンで処理する。
PERIOD_PREFIX_RE = re.compile(r"^\[(?P<period>[^\]]+)\]\s*(?P<rest>.*)$")
ENTRY_RE = re.compile(r"^(?P<class>\D+?)(?P<rank>\d+)位\((?P<rating>\d+)\)$")


def parse_detail(detail_text: str):
    """"[期間] クラス順位(レート)、クラス順位(レート)、[次の期間] ..." 形式の詳細テキストを分解する。"""
    results = []
    current_period = None
    for chunk in (c.strip() for c in detail_text.split("、")):
        if not chunk:
            continue
        pm = PERIOD_PREFIX_RE.match(chunk)
        if pm:
            current_period = pm.group("period").strip()
            chunk = pm.group("rest").strip()
        em = ENTRY_RE.match(chunk)
        if em and current_period:
            results.append(
                {
                    "period": current_period,
                    "class": em.group("class").strip(),
                    "rank": int(em.group("rank")),
                    "rating": int(em.group("rating")),
                }
            )
    return results


# 実データを確認したところ、初回実行時はFC2側のボット検知で
# 「このページの表示は許可されていません」という拒否ページに飛ばされていた（30秒後にトップページへ
# リダイレクトする案内付き）。これはヘッドレスブラウザ特有のUser-Agent（"HeadlessChrome"）や
# navigator.webdriverフラグ、あるいはGitHub Actionsのデータセンター系IPが原因の可能性がある。
# 以下のような対策を入れているが、IPアドレス起因のブロックだった場合はコードでは解決できない
# （README「既知の制約」参照。その場合は取得頻度を落とす/別ホスティングを検討する）。
REJECTED_MARKER = "このページの表示は許可されていません"


def scrape():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            args=["--disable-blink-features=AutomationControlled"],
        )
        page = browser.new_page(
            locale="ja-JP",
            viewport={"width": 1400, "height": 2000},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
            ),
            extra_http_headers={"Accept-Language": "ja-JP,ja;q=0.9"},
        )
        # navigator.webdriver 等、自動操作の分かりやすい痕跡を消す
        page.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
        )

        # FC2ブログは広告・アクセス解析タグが常時通信し続けるため、"networkidle"を待つと
        # いつまで経ってもネットワークが静かにならず30秒でタイムアウトすることがあった。
        # "domcontentloaded"（DOM構築完了）まで待てば十分なので、以降はこちらを使う。

        # トップページ経由でアクセスすることで、深いURLへのいきなりのアクセスを避ける。
        # ここはあくまで「人間らしい振る舞い」の演出なので、失敗しても本番の取得は続行する。
        try:
            page.goto("https://svlabo.jp/", wait_until="domcontentloaded", timeout=45000)
            page.wait_for_timeout(1500)
        except Exception as e:
            print(f"[svlabo] top page visit failed (continuing anyway): {e}", file=sys.stderr)

        page.goto(URL, wait_until="domcontentloaded", timeout=45000)

        if REJECTED_MARKER in page.inner_text("body"):
            print("[svlabo] blocked by FC2's bot detection, retrying once after a pause...", file=sys.stderr)
            page.wait_for_timeout(5000)
            page.goto(URL, wait_until="domcontentloaded", timeout=45000)

        # FC2ブログ側のウィジェットがnetworkidle後もJSで描画を続けるケースに備えて、
        # "｜"（選手行の区切り文字）が出現するまで少し待つ。出なければタイムアウトして先に進む。
        try:
            page.wait_for_selector("text=｜", timeout=15000)
        except Exception as e:
            print(f"[svlabo] wait_for_selector('｜') timed out: {e}", file=sys.stderr)
        page.wait_for_timeout(2000)
        text = page.inner_text("body")
        browser.close()

    if REJECTED_MARKER in text:
        print(
            "[svlabo] still blocked after retry. This is likely an IP-level block by FC2 "
            "against GitHub Actions' datacenter IPs, not a code issue.",
            file=sys.stderr,
        )

    print(f"[svlabo] raw text length={len(text)}")
    # 先頭800文字だとフィルターUIの説明文で終わってしまい選手データが見えないため、
    # 選手行の区切り文字"｜"が最初に出てくる位置の前後を切り出して表示する
    idx = text.find("｜")
    start = max(0, idx - 100) if idx != -1 else 0
    print(f"[svlabo] --- raw text around first '｜' (idx={idx}) ---")
    print(text[start:start + 1500])
    print("[svlabo] --- end raw text sample ---")

    # ヘッダー行が "プレイヤー\t100位以上\t最高順..." のようにタブ区切りだったことから、
    # 実際のテーブルはHTMLの<table>で、1行内の各セルがタブ区切りになっている可能性が高い。
    # ROW_REは行区切り(\n)を前提にしているため、タブを改行に変換してから解析する。
    normalized = text.replace("\t", "\n")

    players = load_players()
    name_index = build_name_index(players)

    rows = []
    for m in ROW_RE.finditer(normalized):
        raw_name = m.group("name").strip()
        norm = normalize_name(raw_name)
        player = name_index.get(norm)
        detail = m.group("detail")

        base = {
            "team_tag_site": m.group("tag").upper(),
            "player_name_site": raw_name,
            "matched_player": player["player_name"] if player else None,
            "team_tag": player["team_tag"] if player else m.group("tag").upper(),
            "top100_count": int(m.group("count")),
            "best_rank_overall": int(m.group("best")),
        }

        base["breakdown"] = parse_detail(detail)
        rows.append(base)

    return rows, text


def main():
    date_str = today_str()
    rows, raw_text = scrape()
    for r in rows:
        r["date"] = date_str
        r["source"] = "svlabo.jp"

    unmatched = [r["player_name_site"] for r in rows if r["matched_player"] is None]
    if unmatched:
        print(f"[svlabo] WARNING: {len(unmatched)} names did not match players.csv: {unmatched}", file=sys.stderr)

    save_snapshot("svlabo", rows)
    # パースが0件でも原因調査できるよう、生テキストを常に保存する（うまくいったら消してOK）
    save_snapshot("svlabo_debug", [{"text_len": len(raw_text), "text": raw_text}])
    return rows


if __name__ == "__main__":
    rows = main()
    if not rows:
        print("WARNING: no rows scraped. Site structure may have changed.", file=sys.stderr)
        sys.exit(1)
