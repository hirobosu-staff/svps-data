"""公式サイト ps.shadowverse-wb.com の「SCHEDULE & RESULTS」から、
選手個人の試合結果（使用クラス・勝敗・対戦相手・節/前半後半/ROUND/BATTLE番号）を取得する。

対象ページ: https://ps.shadowverse-wb.com/26-27/schedule-results/
消化済みの各ROUNDにある「試合結果詳細」ボタンを押すとモーダルが開き、
BATTLE 1..N ごとの選手名・使用クラス・勝敗が表示される。
このデータはJS実行後に描画されるため、Playwrightでのクリック操作が必須。

--- 2026-08-27のリニューアルについて（この書き換えの理由） ---
公式サイトが全面リニューアル（Svelte製に作り直し）され、DOMもテキストの並びも変わった。
旧実装はモーダルのinnerTextを「名前/クラス/+1pt/勝敗/BATTLE n/VS/勝敗/名前/クラス」という
"並び順の決め打ち"で読んでいたため、次の2点の変更で完全に破綻した。

    旧: ふえた / ロイヤル / +1pt / WIN / BATTLE 1 / VS / LOSE / CQCQ / ウィッチ
    新: ふえた / ロイヤル / WIN / BATTLE 1 / VS / CQCQ / ウィッチ / LOSE

    1. "+1pt" バッジが廃止された
    2. 右側の並びが「勝敗→名前→クラス」から「名前→クラス→勝敗」に変わった

結果としてフィールドが1つずつズレ、player_nameにクラス名、classに勝敗、resultに選手名が
入った行が153行もCSVに混入した。さらに日付見出しが "2026.07.11(SAT) 13:00~" の1行から
"2026.07.11" / "(SAT)" / "13:00~" の3要素に分割されたため日付の正規表現も外れ、
round列が "match_0".."match_19" というダミー値になっていた。

そこで並び順に依存しない**DOM構造ベース**に作り直した。新しいモーダルは
1バトル = .battle-list__item、その中に左右2つの .-team があり、それぞれ

    .-team-score-name   … 選手名（チーム戦の枠は空文字）
    .deck-link img[alt] … 使用クラス名
    .-team-score-result … WIN / LOSE

と意味づけされた要素に分かれているので、順番ではなく要素の役割で読める。

--- 節・前半後半・ROUND番号について ---
リニューアル後のページは「第N節」「第N節・前半/後半」「ROUND n」がDOM上に明示されている。
以前はこれらを取れなかったため、表示側(rounds.html)が「round列に出てくる日付の通し番号」で
節番号を推測しており、1節が前半/後半の2日に分かれる構成を扱えず第5節を第8節と表示していた。
ここで節番号を一緒に取得してCSVに持たせることで、その推測自体を不要にしている。

--- 取り違え防止 ---
モーダルは1つの要素を使い回して中身だけ差し替える作りなので、クリック直後に読むと
前のROUNDの内容をそのまま読んでしまうことがある（実際に発生した）。そのため
「モーダルの対戦カード名が期待するチームと一致し、かつモーダル内のWIN数が一覧のスコアと
一致する」まで待ってから採用し、駄目なら開き直す。最後まで一致しなければ失敗として扱う。

出力: data/snapshots/ps_results_{today}.json に生データを保存し、
      [{section, half, round_no, battle_no, round, date, player_name, class, result, point,
        opponent_name, opponent_class}, ...] を返す。
"""
import re
import sys
import time

from playwright.sync_api import sync_playwright

from common import today_str, save_snapshot

URL = "https://ps.shadowverse-wb.com/26-27/schedule-results/"

TEAM_BATTLE_LABEL = "チームバトル"
VALID_RESULTS = {"WIN", "LOSE"}
VALID_CLASSES = {"エルフ", "ロイヤル", "ウィッチ", "ドラゴン", "ナイトメア", "ビショップ", "ネメシス"}

# 消化済みROUNDの一覧を作るJS。NEXT ROUND欄は同じカードの再掲（未実施のみ）なので除外する。
# クラス名に付く svelte-xxxxx というハッシュはビルドのたびに変わるので絶対に使わない。
QUEUE_JS = """
() => {
  const allLis = Array.from(document.querySelectorAll('li.right-area__round-item'));
  const out = [];
  const items = Array.from(document.querySelectorAll('.rounds-list__item'))
    .filter(i => !/^NEXT ROUND/.test(i.innerText.trim()));
  for (const item of items) {
    const secM = item.innerText.match(/第(\\d+)節/);
    if (!secM) continue;
    for (const day of item.querySelectorAll('.battle-match')) {
      const flat = day.innerText.replace(/\\n/g, '');
      const d = (flat.match(/(\\d{4})(\\d{2})\\.(\\d{2})/) || []).slice(1);
      const half = (flat.match(/第\\d+節・(前半|後半)/) || [])[1] || '';
      for (const li of day.querySelectorAll('li.right-area__round-item')) {
        const card = li.querySelector('.battle-card');
        if (!card) continue;
        const sl = card.querySelector('.-score-value.-left');
        const sr = card.querySelector('.-score-value.-right');
        const s1 = sl ? sl.textContent.trim() : '';
        const s2 = sr ? sr.textContent.trim() : '';
        if (!/^\\d+$/.test(s1) || !/^\\d+$/.test(s2)) continue;   // 未実施
        if (!li.querySelector('button.js-modal-open-result')) continue;
        const L = card.querySelector('.battle-card__team.-left p');
        const R = card.querySelector('.battle-card__team.-right p');
        const rd = card.querySelector('.-round');
        out.push({
          li: allLis.indexOf(li),
          section: parseInt(secM[1], 10),
          half: half,
          date: d.length === 3 ? `${d[0]}-${d[1]}-${d[2]}` : '',
          round_no: parseInt((rd ? rd.textContent : '').replace(/[^0-9]/g, ''), 10) || null,
          team1: L ? L.textContent.trim() : '',
          team2: R ? R.textContent.trim() : '',
          score1: parseInt(s1, 10),
          score2: parseInt(s2, 10),
        });
      }
    }
  }
  return out;
}
"""

# 現在開いているモーダルの中身を、並び順ではなく要素の役割で読む。
READ_MODAL_JS = """
() => {
  const modal = document.querySelector('.result-modal');
  if (!modal) return null;
  const card = modal.querySelector('.battle-card');
  if (!card) return null;
  const L = card.querySelector('.battle-card__team.-left p');
  const R = card.querySelector('.battle-card__team.-right p');
  const battles = [];
  modal.querySelectorAll('.battle-list__item').forEach((bi, idx) => {
    const sides = Array.from(bi.querySelectorAll('.-team')).map(tm => {
      const nameEl = tm.querySelector('.-team-score-name');
      const clsImg = tm.querySelector('.deck-link img');
      const resEl  = tm.querySelector('.-team-score-result');
      return {
        name: nameEl ? nameEl.textContent.trim() : '',
        cls: clsImg ? (clsImg.getAttribute('alt') || '').trim() : '',
        result: resEl ? resEl.textContent.trim() : '',
      };
    });
    if (sides.length === 2) battles.push({battle_no: idx + 1, a: sides[0], b: sides[1]});
  });
  return {
    team1: L ? L.textContent.trim() : '',
    team2: R ? R.textContent.trim() : '',
    battles: battles,
  };
}
"""

CLOSE_MODAL_JS = """
() => {
  const m = document.querySelector('.modal.is-open');
  if (!m) return false;
  const b = m.querySelector('button.js-modal-close');
  if (b) { b.click(); return true; }
  return false;
}
"""


def modal_matches(modal, q):
    """モーダルの内容が、開こうとしたROUNDのものだと確信できるかを判定する。
    チーム名の一致だけでなく、モーダル内のWIN数が一覧のスコアと一致することも確認する
    （モーダルは使い回しなので、前のROUNDの中身を掴んでいないかの二重チェック）。"""
    if not modal or not modal.get("battles"):
        return False
    if modal.get("team1") != q["team1"] or modal.get("team2") != q["team2"]:
        return False
    w1 = sum(1 for b in modal["battles"] if b["a"]["result"] == "WIN")
    w2 = sum(1 for b in modal["battles"] if b["b"]["result"] == "WIN")
    return w1 == q["score1"] and w2 == q["score2"]


def open_and_read(page, q, attempts=4, timeout_sec=10):
    """1ROUND分のモーダルを開いて中身を読む。取り違えを検出したら開き直す。"""
    for _ in range(attempts):
        page.evaluate(CLOSE_MODAL_JS)
        page.wait_for_timeout(300)
        lis = page.query_selector_all("li.right-area__round-item")
        if q["li"] >= len(lis):
            return None
        btn = lis[q["li"]].query_selector("button.js-modal-open-result")
        if not btn:
            return None
        btn.click()
        deadline = time.time() + timeout_sec
        while time.time() < deadline:
            modal = page.evaluate(READ_MODAL_JS)
            if modal_matches(modal, q):
                return modal
            page.wait_for_timeout(200)
    return None


def rows_from_modal(q, modal):
    """モーダル1つ（=1ROUND）分を、選手1人1バトル1行に展開する。
    チーム戦の枠（選手名が空）は個人成績ではないので除外する。"""
    rows = []
    for b in modal["battles"]:
        pair = (b["a"], b["b"])
        for idx, side in enumerate(pair):
            name = side["name"]
            if not name or name == TEAM_BATTLE_LABEL:
                continue
            opp = pair[1 - idx]
            opp_name = opp["name"]
            rows.append({
                "section": q["section"],
                "half": q["half"],
                "round_no": q["round_no"],
                "battle_no": b["battle_no"],
                "round": q["date"],
                "player_name": name,
                "class": side["cls"],
                "result": side["result"],
                "point": 1 if side["result"] == "WIN" else 0,
                "opponent_name": opp_name if opp_name and opp_name != TEAM_BATTLE_LABEL else None,
                "opponent_class": opp["cls"] if opp_name and opp_name != TEAM_BATTLE_LABEL else None,
            })
    return rows


def validate(rows, queue, failed):
    """壊れたデータをCSVに書かないための検算。1つでも落ちたら既存CSVを残して中断する。
    旧実装は並び順がズレても黙って通り、クラス名がplayer_nameに入った行を大量に書き込んだ。"""
    errors = []
    if failed:
        errors.append(f"モーダルを正しく読めなかったROUNDがある: {failed}")
    if not rows:
        errors.append("1行も取得できなかった（ページ構造が変わった可能性）")

    for r in rows:
        if r["result"] not in VALID_RESULTS:
            errors.append(f"result列が想定外: {r}")
            break
    for r in rows:
        if r["class"] not in VALID_CLASSES:
            errors.append(f"class列がクラス名になっていない: {r}")
            break
    for r in rows:
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", str(r["round"])):
            errors.append(f"round列が日付形式でない: {r}")
            break
    for r in rows:
        if r["class"] == r["player_name"] or r["result"] == r["player_name"]:
            errors.append(f"列がずれている疑い（選手名とクラス/勝敗が同じ値）: {r}")
            break

    # 一覧のスコア合計と、展開後の勝ち星の数が矛盾しないか
    expected_wins = sum(q["score1"] + q["score2"] for q in queue)
    got_wins = sum(1 for r in rows if r["result"] == "WIN")
    # チーム戦の枠は個人成績から除外しているので、got_wins <= expected_wins になるのが正しい
    if got_wins > expected_wins:
        errors.append(f"勝ち数が一覧のスコア合計を超えている (個人={got_wins} > 一覧計={expected_wins})")
    return errors


def scrape():
    all_rows = []
    failed = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(locale="ja-JP")
        page.goto(URL, wait_until="networkidle")
        page.wait_for_timeout(1500)

        queue = page.evaluate(QUEUE_JS)
        print(f"[ps_results] 消化済みROUND: {len(queue)}件")

        for q in queue:
            modal = open_and_read(page, q)
            label = f"第{q['section']}節{q['half']} ROUND{q['round_no']} {q['team1']} {q['score1']}-{q['score2']} {q['team2']}"
            if not modal:
                print(f"[ps_results] FAILED {label}", file=sys.stderr)
                failed.append(label)
                continue
            rows = rows_from_modal(q, modal)
            print(f"[ps_results] {label}: {len(rows)}行")
            all_rows.extend(rows)

        browser.close()
    return all_rows, queue, failed


def main():
    date_str = today_str()
    rows, queue, failed = scrape()
    for r in rows:
        r["date"] = date_str
        r["source"] = "ps.shadowverse-wb.com"

    errors = validate(rows, queue, failed)
    if errors:
        for e in errors:
            print(f"[ps_results] ERROR: {e}", file=sys.stderr)
        print("[ps_results] 既存の data/match_results.csv は書き換えずに終了する", file=sys.stderr)
        sys.exit(1)

    save_snapshot("ps_results", rows)
    print(f"[ps_results] {len(rows)}行 / {len(queue)}ROUND を取得")
    return rows


if __name__ == "__main__":
    main()
