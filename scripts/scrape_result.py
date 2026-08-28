"""チーム順位（win/lose/diff/battlepoint）を公式サイトの試合結果から自前で集計する。

--- 以前の方式との違い ---
以前は別途運用している公開ツール（uthomeless-public-tool.github.io/2026ps）が公開している
result.jsonをそのままコピーしていた。そのため公式が結果を出しても、あちら側を手で更新する
までこのサイトの順位が古いままになるという問題があった。
現在は公式サイト
    https://ps.shadowverse-wb.com/26-27/schedule-results/
の各ROUNDのスコア（例「Crazy Raccoon 3 - 1 ZETA DIVISION」）だけを読み取り、
4つの数値をすべてこちら側で計算する。外部ツールへの依存は無くなった。

--- 4つの数値の定義 ---
1ROUND（チーム対チームの1試合）は複数バトルで構成され、先に3バトル取った側がそのROUNDの勝者。
公式ページのスコアはこの「バトルの勝ち数」を表している。

    win / lose   : ROUND単位の勝敗数（スコアが大きい側がそのROUNDの勝ち）
    diff         : バトル単位の得失差。全ROUNDの (自分のバトル勝ち数 - 相手のバトル勝ち数) の合計
    battlepoint  : バトル単位の勝ち数の累計（負けた分は引かない）

この定義は第1〜4節の全16ROUNDで公式順位表と突き合わせ、8チーム全項目が一致することを
確認している。もし今後プレーオフ等で加点ルールが変わると合わなくなるため、下記の
検算（得失差の合計が0か、バトル勝ち数の合計が総バトル数と一致するか等）を必ず通す。

--- 安全策 ---
取得や検算に失敗した場合は、既存の data/result.json を一切書き換えずに終了する
（壊れた値や空の値で上書きしてしまわないため）。
status と confirmed_odds は手動で設定しうる項目なので、既存ファイルの値を引き継ぐ。

注意: このページはJS描画のSPAなので、単純なHTTP GETではスコアが取れない。Playwright必須。
"""
import json
import sys

from playwright.sync_api import sync_playwright

from common import DATA_DIR, load_players, normalize_name
import os

URL = "https://ps.shadowverse-wb.com/26-27/schedule-results/"
RESULT_JSON_PATH = os.path.join(DATA_DIR, "result.json")

# site/common.js の RESULT_ID_TO_TAG と同じ対応（サイト側の表示がこのidを前提にしている）
TAG_TO_RESULT_ID = {"CR": 1, "ZETA": 2, "DFM": 3, "VRL": 4, "MRG": 5, "RC": 6, "RDL": 7, "LVH": 8}

# レギュラーシーズンは8チーム総当たり2巡=14節、1節あたり2ROUND×前後半で4ROUND。
EXPECTED_GAME_COUNT = 56

# ページ上の1試合分を取り出すJS。
#
# 2026-08-27前後に公式サイトが全面リニューアル（Svelte製に作り直し）され、DOMが全部変わった。
# 旧: .results__list / .results__game / .results__team-name / .results__score-num
# 新: .rounds-list__item / .battle-card / .battle-card__team.-left|-right p / .-score-value.-left|-right
# 旧セレクタは1件もヒットしなくなったため更新した。
# なおクラス名に付く svelte-xxxxx というハッシュはビルドのたびに変わるので絶対に使わない。
#
# 「NEXT ROUND」欄にも同じ試合カードが出る（未実施の試合のみ）ので、二重計上を避けるため
# その節ブロックは除外する。モーダルを開くと .result-modal の中にも .battle-card が現れるが、
# ここではモーダルを開かないので .rounds-list__item に限定すれば混入しない。
EXTRACT_JS = """
() => {
  const items = Array.from(document.querySelectorAll('.rounds-list__item'))
    .filter(i => !/^NEXT ROUND/.test(i.innerText.trim()));
  const out = [];
  for (const item of items) {
    const secM = item.innerText.match(/第(\\d+)節/);
    for (const card of item.querySelectorAll('.battle-card')) {
      const L  = card.querySelector('.battle-card__team.-left p');
      const R  = card.querySelector('.battle-card__team.-right p');
      const sl = card.querySelector('.-score-value.-left');
      const sr = card.querySelector('.-score-value.-right');
      out.push({
        section: secM ? parseInt(secM[1], 10) : null,
        team1: L ? L.textContent.trim() : '',
        team2: R ? R.textContent.trim() : '',
        score1: sl ? sl.textContent.trim() : '',
        score2: sr ? sr.textContent.trim() : '',
      });
    }
  }
  return out;
}
"""


def build_team_name_index():
    """公式サイトのチーム表示名 -> 自サイトのteam_tag。players.csvのteam_nameから作る
    （公式サイトとplayers.csvのteam_nameは同じ表記なのでハードコードしない）。"""
    idx = {}
    for p in load_players():
        idx[normalize_name(p["team_name"])] = p["team_tag"]
    return idx


def parse_score(s):
    """スコアのセル文字列を整数にする。未実施の試合は '-' なのでNoneを返す。"""
    try:
        return int(str(s).strip())
    except (TypeError, ValueError):
        return None


def aggregate(games, name_index):
    """試合スコアの一覧から、チームごとの win/lose/diff/battlepoint を集計する。"""
    stats = {tag: {"win": 0, "lose": 0, "diff": 0, "battlepoint": 0} for tag in TAG_TO_RESULT_ID}
    unknown_names = set()
    counted = 0

    for g in games:
        s1, s2 = parse_score(g.get("score1")), parse_score(g.get("score2"))
        if s1 is None or s2 is None:
            continue  # 未実施
        t1 = name_index.get(normalize_name(g.get("team1") or ""))
        t2 = name_index.get(normalize_name(g.get("team2") or ""))
        if not t1 or not t2:
            for raw, tag in ((g.get("team1"), t1), (g.get("team2"), t2)):
                if not tag:
                    unknown_names.add(raw)
            continue
        stats[t1]["battlepoint"] += s1
        stats[t2]["battlepoint"] += s2
        stats[t1]["diff"] += s1 - s2
        stats[t2]["diff"] += s2 - s1
        if s1 > s2:
            stats[t1]["win"] += 1
            stats[t2]["lose"] += 1
        else:
            stats[t2]["win"] += 1
            stats[t1]["lose"] += 1
        counted += 1

    return stats, counted, unknown_names


def validate(stats, counted, unknown_names, game_count):
    """集計結果の整合性を検算する。1つでも落ちたら既存ファイルを残して中断する。"""
    errors = []
    if unknown_names:
        errors.append(f"players.csvに無いチーム名がページ上にある: {sorted(unknown_names)}")
    if counted == 0:
        errors.append("実施済みの試合が1つも読み取れなかった（ページ構造が変わった可能性）")
    if game_count != EXPECTED_GAME_COUNT:
        # 節数が変わる可能性もあるので中断せず警告に留める
        print(
            f"[result] WARNING: 試合カード数が想定と違う (取得={game_count}, 想定={EXPECTED_GAME_COUNT})。"
            f"公式サイトの構成が変わったかもしれない。",
            file=sys.stderr,
        )

    total_diff = sum(s["diff"] for s in stats.values())
    if total_diff != 0:
        errors.append(f"得失差の合計が0でない ({total_diff})。片側しか集計できていない可能性がある")

    total_win = sum(s["win"] for s in stats.values())
    total_lose = sum(s["lose"] for s in stats.values())
    if total_win != total_lose or total_win != counted:
        errors.append(f"勝敗数が試合数と合わない (win計={total_win}, lose計={total_lose}, 試合数={counted})")

    return errors


def load_existing():
    if not os.path.exists(RESULT_JSON_PATH):
        return None
    try:
        with open(RESULT_JSON_PATH, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def main():
    name_index = build_team_name_index()

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(locale="ja-JP")
            page.goto(URL, wait_until="networkidle")
            page.wait_for_timeout(1500)
            games = page.evaluate(EXTRACT_JS)
            browser.close()
    except Exception as e:
        print(f"[result] failed to load {URL}: {e}", file=sys.stderr)
        print("[result] keeping existing data/result.json untouched", file=sys.stderr)
        return

    stats, counted, unknown_names = aggregate(games, name_index)
    errors = validate(stats, counted, unknown_names, len(games))
    if errors:
        for e in errors:
            print(f"[result] ERROR: {e}", file=sys.stderr)
        print("[result] keeping existing data/result.json untouched", file=sys.stderr)
        sys.exit(1)

    existing = load_existing() or {}
    data = {
        "status": existing.get("status", "interim"),
        "teams": [
            {
                "id": rid,
                "win": stats[tag]["win"],
                "lose": stats[tag]["lose"],
                "diff": stats[tag]["diff"],
                "battlepoint": stats[tag]["battlepoint"],
            }
            for tag, rid in sorted(TAG_TO_RESULT_ID.items(), key=lambda kv: kv[1])
        ],
        "confirmed_odds": existing.get("confirmed_odds"),
    }

    # 何が変わったかをログに残す（意図しない巻き戻りに気付けるようにするため）
    old_by_id = {t.get("id"): t for t in (existing.get("teams") or [])}
    id_to_tag = {v: k for k, v in TAG_TO_RESULT_ID.items()}
    print(f"[result] {counted} 試合を集計（ページ上の試合カード {len(games)} 件）")
    for t in data["teams"]:
        o = old_by_id.get(t["id"])
        now = f"{t['win']}勝{t['lose']}敗 diff={t['diff']:+d} pt={t['battlepoint']}"
        if o and (o.get("win"), o.get("lose"), o.get("diff"), o.get("battlepoint")) != (
            t["win"], t["lose"], t["diff"], t["battlepoint"]
        ):
            before = f"{o.get('win')}勝{o.get('lose')}敗 diff={o.get('diff')} pt={o.get('battlepoint')}"
            print(f"[result]   {id_to_tag[t['id']]:<5} {before}  ->  {now}")
        else:
            print(f"[result]   {id_to_tag[t['id']]:<5} {now}")

    os.makedirs(DATA_DIR, exist_ok=True)
    with open(RESULT_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"[result] saved -> {RESULT_JSON_PATH}")


if __name__ == "__main__":
    main()
