"""公式サイト ps.shadowverse-wb.com の「SCHEDULE & RESULTS」から、
選手個人の試合結果（使用クラス・勝敗・獲得ポイント）をスクレイピングする。

対象ページ: https://ps.shadowverse-wb.com/26-27/schedule-results/
消化済みの各試合カードにある「試合結果詳細」ボタンをクリックするとモーダルが開き、
選手ごとの対戦（BATTLE 1, 2, ...）の勝敗・使用クラス・獲得ポイントが表示される。
このデータはJS実行後に描画される（生HTMLには入っていない）ため、Playwrightでのクリック操作が必須。

出力: data/snapshots/ps_results_{today}.json に生データを保存し、
      [{date, round, player_name, class, result, point, opponent_name, opponent_class}, ...] を返す。
      opponent_name/opponent_classは同じBATTLE Nの対戦相手の名前・使用クラス
      （試合結果タブで「いつ・誰と・何を使って戦ったか」を表示するために追加）。

--- パース方式について ---
実際にGitHub Actions上で取得した生テキスト（data/snapshots/ps_results_raw_modals_*.json）を元に、
モーダル内の1バトル分は以下のような「空行区切りの1行ずつのトークン列」になることを確認した:

    ふえた / ロイヤル / +1pt / WIN / BATTLE 1 / VS / LOSE / CQCQ / ウィッチ
    Winter / エルフ / LOSE / BATTLE 3 / VS / +1pt / WIN / ヘイム / ビショップ

つまり「BATTLE N」トークンの直前が左側選手の結果(WIN/LOSE)、勝った側だけ結果の直前に"+1pt"が入る。
「BATTLE N」の直後は"VS"、その次が右側選手の(+1pt/)結果・名前・クラスの順。
この規則をparse_battles()でトークン列として解析している（正規表現の1発マッチではなく状態ベース）。
チームバトル枠（個人ではなく「チームバトル」という名前で選手名が入らない対戦）も存在するため、
player_nameが"チームバトル"の行は個人成績としては除外している。

注意: 非公式サイトではなく公式サイトだが、モーダルのUI実装が変わればトークンの並びが崩れる可能性がある。
取得失敗時は data/snapshots/ps_results_raw_modals_*.json とログの生テキストで原因調査すること。
"""
import re
import sys

from playwright.sync_api import sync_playwright

from common import today_str, save_snapshot

URL = "https://ps.shadowverse-wb.com/26-27/schedule-results/"

TEAM_BATTLE_LABEL = "チームバトル"


def tokenize(text: str):
    return [line.strip() for line in text.split("\n") if line.strip()]


def parse_battles(modal_text: str, round_label: str):
    """モーダルの生テキストから、BATTLE N トークンを起点に選手ごとの勝敗を復元する。"""
    # ページ末尾の共通フッター（利用規約など）以降は無関係なので切り捨てる
    cut = modal_text.find("INTERNATIONAL")
    region = modal_text[:cut] if cut != -1 else modal_text
    lines = tokenize(region)

    battles = []
    for i, line in enumerate(lines):
        bm = re.match(r"^BATTLE\s*(\d+)$", line)
        if not bm:
            continue

        # --- 左側選手（BATTLE Nの直前） ---
        if i - 1 < 0:
            continue
        result1 = lines[i - 1]
        if result1 == "WIN":
            if i - 4 < 0:
                continue
            class1, name1 = lines[i - 3], lines[i - 4]
        elif result1 == "LOSE":
            if i - 3 < 0:
                continue
            class1, name1 = lines[i - 2], lines[i - 3]
        else:
            continue  # 想定外のレイアウト。スキップして次を試す

        # --- 右側選手（BATTLE N の次はVS、その後ろ） ---
        if i + 1 >= len(lines) or lines[i + 1] != "VS":
            continue
        j = i + 2
        if j < len(lines) and lines[j] == "+1pt":
            if j + 3 >= len(lines):
                continue
            result2, name2, class2 = lines[j + 1], lines[j + 2], lines[j + 3]
        else:
            if j + 2 >= len(lines):
                continue
            result2, name2, class2 = lines[j], lines[j + 1], lines[j + 2]

        pair = ((name1, class1, result1), (name2, class2, result2))
        for idx, (name, cls, result) in enumerate(pair):
            if name == TEAM_BATTLE_LABEL:
                continue  # 個人成績ではないので除外（README参照）
            opp_name, opp_cls, _ = pair[1 - idx]
            battles.append(
                {
                    "round": round_label,
                    "player_name": name,
                    "class": cls,
                    "result": result,
                    "point": 1 if result == "WIN" else 0,
                    "opponent_name": opp_name if opp_name != TEAM_BATTLE_LABEL else None,
                    "opponent_class": opp_cls if opp_name != TEAM_BATTLE_LABEL else None,
                }
            )

    return battles


def scrape():
    all_rows = []
    raw_modals = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(locale="ja-JP")
        page.goto(URL, wait_until="networkidle")
        page.wait_for_timeout(1500)

        buttons = page.query_selector_all("text=試合結果詳細")
        print(f"[ps_results] found {len(buttons)} completed-match detail buttons")

        for i in range(len(buttons)):
            # DOM再取得のたびにindexがずれる可能性があるので都度クエリし直す
            buttons = page.query_selector_all("text=試合結果詳細")
            if i >= len(buttons):
                break
            btn = buttons[i]
            try:
                btn.click()
                page.wait_for_timeout(800)
                modal_text = page.inner_text("body")
                raw_modals.append(modal_text)

                header_match = re.search(r"(\d{4}\.\d{2}\.\d{2}\([A-Z]+\)[^\n]*)", modal_text)
                round_label = header_match.group(1) if header_match else f"match_{i}"

                rows = parse_battles(modal_text, round_label)
                print(f"[ps_results] match {i} ({round_label}): parsed {len(rows)} player-battles")
                all_rows.extend(rows)

                # モーダルを閉じる（×ボタン想定、無ければEscape）
                close_btn = page.query_selector("button[aria-label='close'], .modal-close, [class*=close]")
                if close_btn:
                    close_btn.click()
                else:
                    page.keyboard.press("Escape")
                page.wait_for_timeout(400)
            except Exception as e:
                print(f"[ps_results] failed on match {i}: {e}", file=sys.stderr)
                page.keyboard.press("Escape")
                page.wait_for_timeout(400)

        browser.close()

    return all_rows, raw_modals


def main():
    date_str = today_str()
    rows, raw_modals = scrape()
    for r in rows:
        r["date"] = date_str
        r["source"] = "ps.shadowverse-wb.com"

    save_snapshot("ps_results", rows)
    # パース失敗時の調査用に、モーダルの生テキストも別途保存する
    save_snapshot("ps_results_raw_modals", [{"index": i, "text": t} for i, t in enumerate(raw_modals)])
    if raw_modals:
        t = raw_modals[0]
        idx = t.find("BATTLE")
        idx = idx if idx != -1 else 0
        start = max(0, idx - 300)
        print(f"[ps_results] --- first modal raw text around 'BATTLE' (total length={len(t)}) ---")
        print(t[start:start + 1500])
        print("[ps_results] --- end raw text sample ---")
    return rows


if __name__ == "__main__":
    rows = main()
    if not rows:
        print(
            "WARNING: no rows parsed. Either no matches finished yet, or parse_battles() needs adjusting "
            "against data/snapshots/ps_results_raw_modals_*.json",
            file=sys.stderr,
        )
