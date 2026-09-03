"""公式サイトのSCHEDULE & RESULTSから、シーズン全体の日程を取得して data/schedule.csv に保存する。

対象ページ: https://ps.shadowverse-wb.com/26-27/schedule-results/

このページにはレギュラーシーズン14節分の日程が最初から全部載っている（対戦カードも確定済み）。
第1節から第14節まで、開催日と曜日は未消化の節にも入っている。
一方**開催時刻は消化済みの節にしか入っていない**（直前に発表される運用）。時刻が空の行は
「日付は決まっているが時刻未定」を意味する。

一度CSVに入れた日程は、公式ページの構成が変わったり過去の節が消えたりしても残る。
取得できなかった日はCSVを書き換えずに終了するので、既存データが失われることはない。

--- 用途 ---
トップページ（index.html）の「次の節」パネルが参照する。
「未消化の試合が残っている一番小さい節」を次の節として、日付・時刻・対戦カードを表示する。

--- スキーマ ---
    section    : 節番号（1〜14）
    half       : 前半戦 / 後半戦 / 空（第3節・第6節のように1日で4ROUND開催する節は空）
    date       : 開催日（YYYY-MM-DD）
    weekday    : 曜日（SAT/SUN/WED など公式表記のまま）
    time       : 開始時刻（HH:MM）。未発表なら空
    round_no   : その日の中でのROUND番号
    team1/team2: 対戦する2チームのteam_tag
    score1/score2: バトル勝ち数。未消化なら空

注意: このページはJS描画のSPAなので、単純なHTTP GETでは日程が取れない。Playwright必須。
      クラス名に付く svelte-xxxxx というハッシュはビルドのたびに変わるので絶対に使わない。
"""
import csv
import os
import sys

from playwright.sync_api import sync_playwright

from common import DATA_DIR, load_players, normalize_name

URL = "https://ps.shadowverse-wb.com/26-27/schedule-results/"
SCHEDULE_CSV = os.path.join(DATA_DIR, "schedule.csv")

FIELDNAMES = ["section", "half", "date", "weekday", "time", "round_no",
              "team1", "team2", "score1", "score2"]

# レギュラーシーズンは8チーム総当たり2巡=14節、1節あたり4ROUND。
EXPECTED_ROWS = 56

# 「NEXT ROUND」欄にも同じ試合カードが再掲されるので、その節ブロックは除外する。
EXTRACT_JS = """
() => {
  const out = [];
  const items = Array.from(document.querySelectorAll('.rounds-list__item'))
    .filter(i => !/^NEXT ROUND/.test(i.innerText.trim()));
  for (const item of items) {
    const secM = item.innerText.match(/第(\\d+)節/);
    if (!secM) continue;
    for (const day of item.querySelectorAll('.battle-match')) {
      const flat = day.innerText.replace(/\\n/g, '');
      const ymd = (flat.match(/(\\d{4})(\\d{2})\\.(\\d{2})/) || []).slice(1);
      const wd = (flat.match(/\\d{2}\\.\\d{2}([A-Z]{3})/) || [])[1] || '';
      const time = (flat.match(/(\\d{1,2}:\\d{2})~/) || [])[1] || '';
      const halfRaw = (flat.match(/第\\d+節・(前半|後半)/) || [])[1] || '';
      for (const li of day.querySelectorAll('li.right-area__round-item')) {
        const c = li.querySelector('.battle-card');
        if (!c) continue;
        const L = c.querySelector('.battle-card__team.-left p');
        const R = c.querySelector('.battle-card__team.-right p');
        const sl = c.querySelector('.-score-value.-left');
        const sr = c.querySelector('.-score-value.-right');
        const rd = c.querySelector('.-round');
        out.push({
          section: parseInt(secM[1], 10),
          half: halfRaw ? halfRaw + '戦' : '',
          date: ymd.length === 3 ? `${ymd[0]}-${ymd[1]}-${ymd[2]}` : '',
          weekday: wd,
          time: time,
          round_no: rd ? parseInt(rd.textContent.replace(/[^0-9]/g, ''), 10) : null,
          team1: L ? L.textContent.trim() : '',
          team2: R ? R.textContent.trim() : '',
          score1: sl ? sl.textContent.trim() : '',
          score2: sr ? sr.textContent.trim() : '',
        });
      }
    }
  }
  return out;
}
"""


def build_team_name_index():
    """公式サイトのチーム表示名 -> team_tag。players.csvのteam_nameから作る。"""
    return {normalize_name(p["team_name"]): p["team_tag"] for p in load_players()}


def to_rows(raw, name_index):
    rows = []
    unknown = set()
    for r in raw:
        t1 = name_index.get(normalize_name(r.get("team1") or ""))
        t2 = name_index.get(normalize_name(r.get("team2") or ""))
        for name, tag in ((r.get("team1"), t1), (r.get("team2"), t2)):
            if not tag:
                unknown.add(name)
        rows.append({
            "section": r.get("section") or "",
            "half": r.get("half") or "",
            "date": r.get("date") or "",
            "weekday": r.get("weekday") or "",
            "time": r.get("time") or "",
            "round_no": r.get("round_no") or "",
            "team1": t1 or "?",
            "team2": t2 or "?",
            # 未消化の試合はスコアが "-" なので空にする
            "score1": r["score1"] if str(r.get("score1", "")).isdigit() else "",
            "score2": r["score2"] if str(r.get("score2", "")).isdigit() else "",
        })
    return rows, unknown


def validate(rows, unknown):
    errors = []
    if not rows:
        errors.append("1行も取得できなかった（ページ構造が変わった可能性）")
    if unknown:
        errors.append(f"players.csvに無いチーム名がある: {sorted(unknown)}")
    missing_date = [r for r in rows if not r["date"]]
    if missing_date:
        errors.append(f"日付が取れていない行が{len(missing_date)}件ある")
    missing_sec = [r for r in rows if not str(r["section"]).isdigit()]
    if missing_sec:
        errors.append(f"節番号が取れていない行が{len(missing_sec)}件ある")
    if rows and len(rows) != EXPECTED_ROWS:
        # 節数が変わる可能性もあるので中断せず警告に留める
        print(f"[schedule] WARNING: 行数が想定と違う (取得={len(rows)}, 想定={EXPECTED_ROWS})",
              file=sys.stderr)
    return errors


def main():
    name_index = build_team_name_index()
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(locale="ja-JP")
            page.goto(URL, wait_until="networkidle")
            page.wait_for_timeout(1500)
            raw = page.evaluate(EXTRACT_JS)
            browser.close()
    except Exception as e:
        print(f"[schedule] 取得失敗 {URL}: {e}", file=sys.stderr)
        print("[schedule] 既存の data/schedule.csv はそのまま残す", file=sys.stderr)
        return

    rows, unknown = to_rows(raw, name_index)
    errors = validate(rows, unknown)
    if errors:
        for e in errors:
            print(f"[schedule] ERROR: {e}", file=sys.stderr)
        print("[schedule] 既存の data/schedule.csv はそのまま残す", file=sys.stderr)
        sys.exit(1)

    rows.sort(key=lambda r: (int(r["section"]), r["half"] == "後半戦", int(r["round_no"] or 0)))

    os.makedirs(DATA_DIR, exist_ok=True)
    with open(SCHEDULE_CSV, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDNAMES)
        w.writeheader()
        w.writerows(rows)

    played = sum(1 for r in rows if r["score1"] != "")
    days = len({r["date"] for r in rows})
    with_time = len({r["date"] for r in rows if r["time"]})
    print(f"[schedule] {len(rows)}行 / {days}日程 を保存（消化済み {played}ROUND、時刻判明 {with_time}日）")
    print(f"[schedule] saved -> {SCHEDULE_CSV}")


if __name__ == "__main__":
    main()
