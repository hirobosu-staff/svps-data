"""選手個人ページ（ps.shadowverse-wb.com/26-27/teams/{ps_slug}）から選手写真を取得し、
site/images/players/ に保存する。

写真は基本的にシーズン中頻繁には変わらない想定のため、既にファイルが存在する選手は
再ダウンロードせずスキップする（差し替えたい場合はそのファイルを手動で削除してから
再実行すれば再取得される）。

保存したファイル名は CDN側の命名（選手ごとに番号や大文字小文字の付き方が揺れている）
に依存させず、こちらの規則（{team_tag}_{ps_slug}.{拡張子}）で統一している。
site側はこの規則を知らなくてもいいように、data/player_images.json に
{player_name: "images/players/xxx.ext"} のマッピングを書き出し、そちらを読む。

出典について: 写真は公式サイト（ps.shadowverse-wb.com、Cygames運営）に掲載されている
選手プロフィール写真で、著作権は運営元に帰属する。本スクリプトは選手データを個人的に
追跡するファンツール用に、非商用の用途でキャッシュ・表示するものであり、権利者から
削除要請があった場合は該当ファイルをリポジトリから取り除く想定。
"""
import json
import os
import re
import sys
from urllib.parse import quote

import requests

from common import REPO_ROOT, DATA_DIR, load_players

SITE_DIR = os.path.join(REPO_ROOT, "site")
IMAGES_DIR = os.path.join(SITE_DIR, "images", "players")
MANIFEST_PATH = os.path.join(DATA_DIR, "player_images.json")

PAGE_URL_TMPL = "https://ps.shadowverse-wb.com/26-27/teams/{slug}"
# 選手によっては画像ファイル名に半角スペースが入っている（例: 智念せいら＝
# ".../13_Seira Chinen_profile01.avif"）。以前は \s をまるごと除外していたため
# スペースの手前でマッチが途切れ、この選手だけ画像が取得できていなかった。
# 除外すべきなのは属性を閉じるクォートや改行だけなので、スペース自体は許可する。
IMG_RE = re.compile(
    r'https://wb-premier-series\.g\.kuroco-img\.app/files/user/player_details/[^"\'<>\r\n]+?\.(?:avif|png|jpe?g|webp)'
)
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; svps-tracker-bot/1.0)"}


def fetch_profile_image_url(slug: str):
    url = PAGE_URL_TMPL.format(slug=slug)
    resp = requests.get(url, timeout=30, headers=HEADERS)
    if resp.status_code != 200:
        print(f"[player_images] failed to fetch {url} (status={resp.status_code})", file=sys.stderr)
        return None
    m = IMG_RE.search(resp.text)
    if not m:
        print(f"[player_images] no profile image pattern found on {url}", file=sys.stderr)
        return None
    return m.group(0)


def load_manifest():
    if not os.path.exists(MANIFEST_PATH):
        return {}
    with open(MANIFEST_PATH, encoding="utf-8") as f:
        return json.load(f)


def save_manifest(manifest):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)


def main():
    os.makedirs(IMAGES_DIR, exist_ok=True)
    players = load_players()
    manifest = load_manifest()

    downloaded = 0
    skipped = 0
    failed = []

    for p in players:
        slug = p.get("ps_slug")
        name = p["player_name"]
        if not slug:
            print(f"[player_images] no ps_slug for {name}, skipping", file=sys.stderr)
            continue

        existing_rel = manifest.get(name)
        if existing_rel and os.path.exists(os.path.join(SITE_DIR, existing_rel)):
            skipped += 1
            continue

        img_url = fetch_profile_image_url(slug)
        if not img_url:
            failed.append(name)
            continue

        ext = img_url.rsplit(".", 1)[-1]
        filename = f"{p['team_tag']}_{slug}.{ext}"
        dest = os.path.join(IMAGES_DIR, filename)

        try:
            # img_url に生のスペースが含まれる場合があるため、リクエスト前にパーセントエンコードする
            # （scheme/ホスト部分の : や / は safe に指定して壊さないようにする）
            safe_url = quote(img_url, safe=":/")
            img_resp = requests.get(safe_url, timeout=30, headers=HEADERS)
            img_resp.raise_for_status()
            with open(dest, "wb") as f:
                f.write(img_resp.content)
        except Exception as e:
            print(f"[player_images] download failed for {name}: {e}", file=sys.stderr)
            failed.append(name)
            continue

        manifest[name] = f"images/players/{filename}"
        downloaded += 1
        print(f"[player_images] saved {name} -> {filename}")

    save_manifest(manifest)
    print(f"[player_images] done: {downloaded} downloaded, {skipped} already cached, {len(failed)} failed")
    if failed:
        print(f"[player_images] failed players: {failed}", file=sys.stderr)


if __name__ == "__main__":
    main()
