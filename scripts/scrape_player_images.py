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
from playwright.sync_api import sync_playwright

from common import REPO_ROOT, DATA_DIR, load_players

SITE_DIR = os.path.join(REPO_ROOT, "site")
IMAGES_DIR = os.path.join(SITE_DIR, "images", "players")
MANIFEST_PATH = os.path.join(DATA_DIR, "player_images.json")

PAGE_URL_TMPL = "https://ps.shadowverse-wb.com/26-27/teams/{slug}"

# --- 2026-08-27のリニューアルで画像の置き場所が変わった ---
# 旧: https://wb-premier-series.g.kuroco-img.app/files/user/player_details/13_Seira Chinen_profile01.avif
# 新: https://ps.shadowverse-wb.com/v=1787114317/files/user/26-27/players/atom_profile01.png
# ホストもパスも変わり、ファイル名も ps_slug ベースの規則的なものになった。
# さらにページ自体がSPA化して、HTMLを取っただけでは中身が空（imgタグが存在しない）ため、
# requestsだけでは取得できなくなった。そのためPlaywrightで描画してから探す。
#
# なお /v=<数字>/ はキャッシュバスター用のセグメントで、外しても同じ画像が取れることを
# 確認している。ページから見つけられなかった場合の保険として、この規則で組み立てたURLも試す。
IMG_RE = re.compile(
    r'https://ps\.shadowverse-wb\.com/(?:v=\d+/)?files/user/26-27/players/[^"\'<>\r\n]+?\.(?:avif|png|jpe?g|webp)'
)
FALLBACK_URL_TMPL = "https://ps.shadowverse-wb.com/files/user/26-27/players/{slug}_profile01.{ext}"
FALLBACK_EXTS = ("png", "avif", "jpg", "webp")
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; svps-tracker-bot/1.0)"}


def fetch_profile_image_url(page, slug: str):
    """選手ページを描画して、その選手のプロフィール画像URLを取り出す。
    slugを含むURLを優先し、見つからなければ規則から組み立てたURLで存在確認する。"""
    url = PAGE_URL_TMPL.format(slug=slug)
    try:
        page.goto(url, wait_until="networkidle")
        page.wait_for_timeout(800)
        srcs = page.evaluate("() => Array.from(document.images).map(i => i.src)")
    except Exception as e:
        print(f"[player_images] failed to render {url}: {e}", file=sys.stderr)
        srcs = []

    candidates = [s for s in srcs if IMG_RE.fullmatch(s or "")]
    # 同じページに他選手のサムネイルが載ることがあるので、slugが入っているものを優先する
    for s in candidates:
        if f"/{slug}_" in s:
            return s
    if candidates:
        return candidates[0]

    for ext in FALLBACK_EXTS:
        fallback = FALLBACK_URL_TMPL.format(slug=slug, ext=ext)
        try:
            r = requests.head(fallback, timeout=30, headers=HEADERS)
            if r.status_code == 200:
                print(f"[player_images] {slug}: ページから見つからなかったので規則URLを使う")
                return fallback
        except Exception:
            continue
    print(f"[player_images] no profile image found on {url}", file=sys.stderr)
    return None


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

    # 取得が必要な選手だけ先に絞る（既に写真がある選手のためにブラウザを起動しない）
    todo = []
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
        todo.append(p)

    if todo:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(locale="ja-JP")
            for p in todo:
                slug, name = p["ps_slug"], p["player_name"]
                img_url = fetch_profile_image_url(page, slug)
                if not img_url:
                    failed.append(name)
                    continue

                ext = img_url.rsplit(".", 1)[-1].split("?")[0]
                filename = f"{p['team_tag']}_{slug}.{ext}"
                dest = os.path.join(IMAGES_DIR, filename)
                try:
                    # URLに生のスペースが含まれる場合があるためパーセントエンコードする
                    # （scheme/ホスト部分の : や / は safe に指定して壊さないようにする）
                    safe_url = quote(img_url, safe=":/=")
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
            browser.close()

    save_manifest(manifest)
    print(f"[player_images] done: {downloaded} downloaded, {skipped} already cached, {len(failed)} failed")
    if failed:
        print(f"[player_images] failed players: {failed}", file=sys.stderr)


if __name__ == "__main__":
    main()
