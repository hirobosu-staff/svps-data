"""選手ごとのYouTubeチャンネル登録者数を取得する。

2通りの取得方法をハイブリッドで使う:

1. YouTube Data API v3（channels.list, part=statistics）… メイン方式。
   環境変数 YOUTUBE_API_KEY が設定されていればこちらを使う。
   登録者数が1万人を超えるチャンネルでも端数まで正確な整数が返る
   （チャンネル側が明示的に非表示設定にしていない限り）。
   取得手順・GitHub Secretsへの登録方法はREADMEの「YouTube Data APIキーの取得方法」を参照。
   （このキーはClaude側では一切扱わない。あなた自身がGoogle Cloud Consoleで発行し、
   GitHubリポジトリのSecretsに直接登録する）
   channels.list は1リクエストで最大50チャンネルIDをまとめて問い合わせできるため、
   このリポジトリの規模（37選手・うちYouTubeチャンネルありは36）なら1回のAPI呼び出しで済む。

2. チャンネルページの /about スクレイピング（Playwright）… フォールバック方式。
   YOUTUBE_API_KEY が未設定の場合、またはAPI呼び出し自体が失敗した場合（キー無効・
   クォータ超過など）に、このスクリプトが動かなくなってしまわないよう自動的にこちらを使う。
   チャンネルページのHTMLに埋め込まれたJSON文字列
   ("subscriberCountText":"チャンネル登録者数 8010人") を正規表現で抜き出す方式で、
   実際に37チャンネル全部で動作確認済み。ただし登録者数が概ね1万人を超えるチャンネル
   （12チャンネル）はYouTube側の表示自体が「1.35万人」のように丸められてしまい、
   端数までは取得できない（この方式そのものの限界であり、正確な数字が必須ならAPIキーの
   設定が必須）。

出力: data/snapshots/youtube_{today}.json に生データを保存し、
      history.csv用の行リスト [{date, team_tag, player_name, metric, period, value}, ...] を返す。
      どちらの方式で取得したかは各行の"via"キー（"api" または "scrape"）に記録している。

注意: players.csvのyoutube_urlが空の選手（Chappy。shadowverse-reference.com上でも
YouTubeチャンネルが確認できず、Twitchのみで配信）は両方式とも対象外。
"""
import os
import re
import sys

import requests

from common import today_str, save_snapshot, load_players

API_URL = "https://www.googleapis.com/youtube/v3/channels"
SUB_RE = re.compile(r'"subscriberCountText":"チャンネル登録者数\s*([\d,]+(?:\.\d+)?)\s*(万)?人"')


def extract_channel_id(url: str):
    """youtube_url (https://www.youtube.com/channel/UCxxxx 形式) から channel ID を取り出す。"""
    if not url:
        return None
    m = re.search(r"/channel/([A-Za-z0-9_-]+)", url)
    return m.group(1) if m else None


def parse_subscriber_count(text: str):
    m = SUB_RE.search(text)
    if not m:
        return None
    num_str, man = m.groups()
    num = float(num_str.replace(",", ""))
    if man:
        num *= 10000
    return int(num)


def scrape_via_api(players, api_key):
    """YouTube Data APIで取得する。成功した場合は (rows, debug_entries) を返す。
    APIリクエスト自体が失敗した場合は (None, debug_entries) を返し、呼び出し側に
    フォールバックを促す。"""
    id_to_player = {}
    skipped = []
    for p in players:
        cid = extract_channel_id(p.get("youtube_url", ""))
        if cid:
            id_to_player[cid] = p
        else:
            skipped.append(p["player_name"])

    ids = list(id_to_player.keys())
    rows = []
    debug_entries = []
    any_success = False

    for i in range(0, len(ids), 50):
        batch = ids[i:i + 50]
        try:
            resp = requests.get(
                API_URL,
                params={"part": "statistics", "id": ",".join(batch), "key": api_key},
                timeout=30,
            )
            data = resp.json()
        except Exception as e:
            print(f"[youtube] API request failed: {e}", file=sys.stderr)
            debug_entries.append({"batch_size": len(batch), "error": str(e)})
            continue

        debug_entries.append({"status_code": resp.status_code, "batch_size": len(batch), "response": data})

        if resp.status_code != 200:
            print(f"[youtube] API error (status={resp.status_code}): {data}", file=sys.stderr)
            continue

        any_success = True
        found_ids = set()
        for item in data.get("items", []):
            cid = item["id"]
            found_ids.add(cid)
            player = id_to_player[cid]
            stats = item.get("statistics", {})
            if stats.get("hiddenSubscriberCount"):
                print(f"[youtube] {player['player_name']}: subscriber count is hidden by the channel owner", file=sys.stderr)
                continue
            count = stats.get("subscriberCount")
            if count is None:
                continue
            rows.append({
                "team_tag": player["team_tag"],
                "player_name": player["player_name"],
                "value": int(count),
                "via": "api",
            })

        missing = set(batch) - found_ids
        if missing:
            print(f"[youtube] no data returned for channel IDs: {missing}", file=sys.stderr)

    if skipped:
        print(f"[youtube] skipped (no resolvable channel ID in youtube_url): {skipped}")

    if not any_success:
        # 1件も成功しなかった＝APIキーが無効/クォータ超過などで機能していない可能性が高い。
        # 呼び出し側にフォールバックさせるためNoneを返す。
        return None, debug_entries

    print(f"[youtube] {len(rows)}/{len(ids)} channels scraped successfully via YouTube Data API")
    return rows, debug_entries


def scrape_via_playwright(players):
    """チャンネルページの/aboutをスクレイピングして取得する（フォールバック方式）。"""
    from playwright.sync_api import sync_playwright

    targets = [p for p in players if p.get("youtube_url")]
    skipped = [p["player_name"] for p in players if not p.get("youtube_url")]

    rows = []
    debug_entries = []

    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(
            locale="ja-JP",
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
            ),
        )
        # Googleの同意確認画面をなるべく回避する（US等のデータセンターIPで出ることがあるため）
        context.add_cookies([{
            "name": "CONSENT",
            "value": "YES+1",
            "domain": ".youtube.com",
            "path": "/",
        }])
        page = context.new_page()

        for player in targets:
            url = player["youtube_url"].rstrip("/") + "/about"
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=45000)
                page.wait_for_timeout(1000)
                text = page.content()
            except Exception as e:
                print(f"[youtube] failed to load {player['player_name']} ({url}): {e}", file=sys.stderr)
                debug_entries.append({"player_name": player["player_name"], "url": url, "error": str(e)})
                continue

            count = parse_subscriber_count(text)
            debug_entries.append({
                "player_name": player["player_name"],
                "url": url,
                "text_len": len(text),
                "parsed": count,
            })

            if count is None:
                print(f"[youtube] WARNING: could not find subscriber count for {player['player_name']} ({url})", file=sys.stderr)
                continue

            rows.append({
                "team_tag": player["team_tag"],
                "player_name": player["player_name"],
                "value": count,
                "via": "scrape",
            })

        browser.close()

    if skipped:
        print(f"[youtube] skipped (no youtube_url in players.csv): {skipped}")
    print(f"[youtube] {len(rows)}/{len(targets)} channels scraped successfully via page scraping (fallback)")

    return rows, debug_entries


def scrape():
    players = load_players()
    api_key = os.environ.get("YOUTUBE_API_KEY")

    if api_key:
        rows, debug_entries = scrape_via_api(players, api_key)
        if rows is not None:
            return rows, debug_entries
        print("[youtube] API method failed entirely, falling back to page scraping", file=sys.stderr)
    else:
        print("[youtube] YOUTUBE_API_KEY is not set, using page scraping (fallback). "
              "Subscriber counts above ~10,000 will only be approximate (e.g. '1.35万人').", file=sys.stderr)

    return scrape_via_playwright(players)


def main():
    date_str = today_str()
    rows, debug_entries = scrape()
    for r in rows:
        r["date"] = date_str
        r["source"] = "youtube"

    save_snapshot("youtube", rows)
    # APIキー未設定時やエラー時の原因調査用に、レスポンス/生テキストをそのまま保存する
    save_snapshot("youtube_debug", debug_entries)
    return rows


if __name__ == "__main__":
    rows = main()
    if not rows:
        print("WARNING: no rows scraped (both API and page-scraping fallback failed).", file=sys.stderr)
        sys.exit(1)
