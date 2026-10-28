"""各選手のXフォロワー数を FxTwitter API（api.fxtwitter.com）から取得する。

経緯:
    以前は shadowverse-reference.com（非公式ファンサイト）の「Xのフォロワー数」を取っていたが、
    あちらは元々週1回（水曜）しか更新されず、2026-10-08 を最後に更新が止まった。
    X公式APIは新規の無料枠が廃止され従量課金のみ（他人のプロフィール読み取りは1回およそ0.01ドル）、
    x.com の直接スクレイピングはログイン必須の範囲が多くサーバーからはブロックされやすい。
    そこで、Xの埋め込み表示を補うための無料・認証不要の公開API（FxTwitter）を使う。

取得元:
    GET https://api.fxtwitter.com/2/profile/{x_handle}
    -> {"code": 200, "user": {"screen_name": ..., "followers": 13315, ...}}
    公表されているレート制限は IP ごとに 1000 リクエスト/分。37人を1日1回なら十分収まる。

注意:
    - 非公式サービスなので、X側の仕様変更などで突然使えなくなる可能性がある。
    - まれに存在するアカウントでも一時的に 404 が返る（2026-10-28の試験で37人中2人）。
      そのため1人あたり最大3回まで再試行する。
    - 取れなかった選手はその日の行を書かない。古い値で埋めると推移が嘘になるため。

出力: data/snapshots/x_{today}.json
      [{date, team_tag, player_name, x_handle, value, via}, ...]
      update_history.py がこれを metric=followers, period=current として history.csv に入れる。
"""
import sys
import time

import requests

from common import load_players, save_snapshot, today_str

API = "https://api.fxtwitter.com/2/profile/{handle}"
HEADERS = {"User-Agent": "svps-data (https://github.com/hirobosu-staff/svps-data)"}
MAX_TRIES = 3
RETRY_WAIT_SEC = 5
INTERVAL_SEC = 1.0  # 選手ごとの間隔（レート制限には遠く及ばないが、短時間に集中させない）


def fetch_followers(handle: str):
    """フォロワー数(int)を返す。MAX_TRIES回試しても取れなければ None。"""
    last_err = ""
    for attempt in range(1, MAX_TRIES + 1):
        try:
            resp = requests.get(API.format(handle=handle), headers=HEADERS, timeout=20)
            data = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
            user = data.get("user") or {}
            followers = user.get("followers")
            # 別アカウントの値を取り違えないよう、返ってきた screen_name が一致することも確認する
            if (resp.status_code == 200 and data.get("code") == 200 and isinstance(followers, int)
                    and str(user.get("screen_name", "")).lower() == handle.lower()):
                return followers
            last_err = f"HTTP {resp.status_code} code={data.get('code')} message={data.get('message')}"
        except Exception as e:  # ネットワークエラー・JSONでない応答など
            last_err = repr(e)
        print(f"[x] {handle}: attempt {attempt}/{MAX_TRIES} failed ({last_err})", file=sys.stderr)
        if attempt < MAX_TRIES:
            time.sleep(RETRY_WAIT_SEC)
    return None


def main():
    date_str = today_str()
    rows, failed = [], []
    for p in load_players():
        handle = (p.get("x_handle") or "").strip().lstrip("@")
        if not handle:
            continue
        followers = fetch_followers(handle)
        if followers is None:
            failed.append(handle)
        else:
            rows.append({
                "date": date_str,
                "team_tag": p["team_tag"],
                "player_name": p["player_name"],
                "x_handle": handle,
                "value": followers,
                "via": "fxtwitter",
            })
        time.sleep(INTERVAL_SEC)

    print(f"[x] fetched {len(rows)} players, failed {len(failed)}: {failed}")
    if rows:
        save_snapshot("x", rows)
    return rows


if __name__ == "__main__":
    if not main():
        print("WARNING: no follower counts fetched. FxTwitter API may be down or blocked.", file=sys.stderr)
        sys.exit(1)
