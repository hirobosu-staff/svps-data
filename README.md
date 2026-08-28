# Shadowverse Premier Series 26-27 選手データ

Xフォロワー数・YouTube登録者数・配信時間・視聴時間・動画本数・PS戦績を毎日自動取得し、
GitHub Pagesで折れ線グラフとして公開するためのリポジトリ一式です。表示側（`site/`）は
選手一覧・選手詳細・ランキング・通算成績・節別結果・比較・BEYONDのページ構成（ナビは6項目、
選手詳細は各ページの選手名リンク経由）で、単にデータを溜めるだけでなく表示まで一体になっています。

ランクマッチ最高順位（svlabo.jp由来）は自動取得から外し、手動運用にしています
（理由は「なぜsvlabo.jpだけ手動にしたか」を参照）。

## 構成

```
svps-tracker/
├── .github/workflows/daily-update.yml   毎日実行されるGitHub Actions（スクレイピング〜データ更新〜Pages公開）
├── .github/workflows/deploy-pages.yml   site/やdata/history.csv・players.csv・player_images.jsonを
│                                          pushした時だけ動く、スクレイピングを伴わない即時デプロイ用ワークフロー
├── scripts/
│   ├── common.py               共通処理（選手マスタ読み込み、CSV書き出しなど）
│   ├── scrape_reference.py     shadowverse-reference.com から フォロワー数・配信関連 を取得（毎日自動）
│   ├── scrape_ps_results.py    ps.shadowverse-wb.com から PS戦績（個人） を取得（毎日自動）
│   ├── scrape_youtube.py       各選手のYouTubeチャンネル登録者数を取得（毎日自動、API/スクレイピング併用）
│   ├── scrape_player_images.py ps.shadowverse-wb.comから選手写真を取得（毎日自動。既にある選手はスキップ）
│   ├── scrape_result.py        チーム順位（result.json）を公式サイトの試合スコアから集計（毎日自動。詳細は「チーム順位について」参照）
│   ├── scrape_svlabo.py        svlabo.jp から ランクマッチ最高順位・レート を取得（★自動実行からは除外。手動で使う用に残してあるだけ）
│   ├── scrape_svlabo_battle_details.py  svlabo.jpの「N節 試合詳細結果＆配信時間指定URL」記事を取り込む
│   │                             （★自動実行からは除外。新しい節の記事が出たらURLを渡して手動実行。詳細は「節別詳細結果について」参照）
│   ├── update_history.py       上記のスナップショットを data/history.csv に統合
│   └── requirements.txt
├── data/
│   ├── players.csv             選手マスタ（8チーム37名。youtube_url/twitch_url/ps_slugを保持。
│   │                            詳細は「players.csvについて」参照）
│   ├── result.json             チーム順位（毎日自動取得。詳細は「チーム順位について」参照）
│   ├── history.csv              蓄積される日次データ（ロング形式。followers/youtube_subscribers/
│   │                             stream_duration/watch_time/video_view_count/video_upload_count/
│   │                             cr_*系のみ。PS戦績はここには入らない。下記参照）
│   ├── match_results.csv       PS公式戦の個人試合結果（1試合1行。詳細は「試合結果について」参照）
│   ├── player_images.json      選手名→写真パスのマッピング（scrape_player_images.pyが自動生成）
│   ├── svlabo_leaderboards.csv  svlabo.jpの全ユーザー分を一括取得した手動作業の成果物
│   │                             （period, class, rank, team_tag, player_name, rating の列。history.csvとは別管理・自動更新はされない。
│   │                             ranking.htmlの「CR順位 TOP N入り回数」ランキングが参照する）
│   ├── battle_details.csv      svlabo.jpの節別記事から取り込んだ試合詳細（使用/未使用クラス・配信URL付き。
│   │                             詳細は「節別詳細結果について」参照）
│   └── snapshots/               日次の生スクレイピング結果（デバッグ用、実行のたびに増える）
└── site/                        表示用ページ。ページごとにファイルを分けており、今後ページを
    ├── style.css                  増やしたり構成を変えたりしやすい作りにしてある
    ├── common.js                共通ロジック（データ読み込み・CSVパース・指標ラベル・アバター表示・
    │                             クラスアイコン表示など）
    ├── index.html               チーム一覧（トップページ）。チームをクリックすると選手カードが展開される
    │                             アコーディオン形式。並び順は通算獲得ポイント（match_results.csv集計）順
    ├── player.html              選手詳細（写真・現在値・X/YouTubeへのリンク・折れ線グラフ、
    │                             ?name=選手名 で表示選手を切替）
    ├── ranking.html             ランキング（指標×期間/しきい値で選手を順位付け表示。全選手を常に表示。
    │                             PS公式戦の勝利数/獲得ポイントもここから見られる）
    ├── rounds.html              通算成績（全選手のリーダーボード＋個人の対戦履歴。
    │                             ?name=選手名で個人成績を直接表示。旧URL rounds.html?view=sections は
    │                             sections.htmlへ転送する）
    ├── sections.html            節別結果（節ごとのROUND/BATTLE詳細・使用/未使用クラス・配信リンク。
    │                             以前はrounds.html内のページ内タブだったが、利用頻度が高いためナビ第1階層に独立）
    ├── matches.html             旧URL互換用のリダイレクトスタブ（クエリ文字列を保ったままrounds.htmlに転送するだけ）
    ├── compare.html             比較（「グラフで比較」＝選手を選んで指標の推移を折れ線で重ねる、
    │                             「表で比較」＝全選手をチーム/フォロワー数/戦績などの列でまとめた
    │                             ソート可能な一覧表）
    ├── beyond.html              BEYOND（data/svlabo_leaderboards.csvの全ユーザーランクマッチ
    │                             リーダーボード。PS出場選手・アマチュアを区別せず全掲載者が対象。
    │                             「クラス別」＝期間×クラスで絞り込んだ順位表、
    │                             「全クラス合算TOP100」＝各選手のその期間内での最高レート
    │                             （クラス問わず）で並べ直したTOP100。期間・チーム・選手名検索で
    │                             絞り込める。PS出場選手の行はplayer.htmlへのリンクになる）
    ├── images/players/          ダウンロードした選手写真（scrape_player_images.pyが生成、初回pushには含まれない）
    ├── images/teams/            8チームの公式ロゴ画像（提供されたPNG。common.jsのteamLogoHTML()が参照）
    └── images/classes/          シャドバのクラスアイコン（ユーザー提供のSVG、8種）
```

## 【重要】既存リポジトリを更新するときの注意

`data/history.csv` / `data/match_results.csv` / `data/player_images.json` / `data/snapshots/` /
`site/images/players/` は、GitHub Actionsが日々の実行で書き込んでいく実データです。
そのため**このzipには含めていません**（コードだけのzipです）。

以前のバージョンではこれらを空のプレースホルダーとして同梱していましたが、それを
「リポジトリを一度空にしてから丸ごと差し替える」という手順と組み合わせたことで、
運用中のリポジトリの実データ（フォロワー数・登録者数の推移、選手写真、試合結果など）を
複数回消してしまいました。同じ事故を防ぐため、今後は次の手順にしてください。

**2回目以降の更新手順（データを消さない方法）**:

1. リポジトリを一度も消さない（`git rm -r .`や、フォルダの中身を全部消してから貼り付ける、
   といった操作はしない）
2. 代わりに、zipを展開した中の以下のファイル・フォルダだけを、既存のローカルリポジトリの
   同じ場所に上書きコピーする（Explorer上で「置き換える」を選ぶ形でOK。存在しないファイルは
   何も起きないので安全）:
   - `.github/`
   - `scripts/`
   - `site/`（このzipには`site/images/players/`は含まれていないので、既存の選手写真は
     上書きされずそのまま残る）
   - `README.md`
   - `data/players.csv`
   - `data/svlabo_leaderboards.csv`（一括取得した手動作業の成果物。日々のActionsでは更新されないため上書きしても安全）
   - `data/battle_details.csv`（svlabo.jpの節別記事から取り込んだ手動作業の成果物。日々のActionsでは更新されないため上書きしても安全）
3. `data/history.csv` / `data/match_results.csv` / `data/player_images.json` /
   `data/snapshots/` / `data/result.json`（手動更新を始めている場合）には一切触れない・
   コピー対象に含めない
4. コミット→push

このzipの中に無いファイルは、コピー元に存在しないのでコピー先（あなたのリポジトリ）に
何の影響も与えません。**「まず全部消す」という操作さえしなければ、既存データは自動的に守られます。**

## セットアップ手順

1. このフォルダの中身を、あなたのGitHubリポジトリのルートにそのままコピーしてpushする
2. リポジトリの Settings → Pages → Source を「GitHub Actions」に設定する
3. Actionsタブで `Daily stats update` を一度 `Run workflow`（手動実行）して、正常に動くか確認する
4. 以降は毎日 22:00 JST に自動実行される（`.github/workflows/daily-update.yml` の cron で変更可能）
5. 公開URLは `https://<ユーザー名>.github.io/<リポジトリ名>/` になる

`daily-update.yml`は`schedule`と`workflow_dispatch`（手動実行）でしか動かないため、`site/`配下（表示用ページ）だけを直してpushしても、それだけではPagesは更新されない。この用途のために`deploy-pages.yml`を用意しており、`site/**`または`data/history.csv`・`data/players.csv`のpushをトリガーに、スクレイピングを挟まずサイトだけを即座に再デプロイする。

認証について: pushやPages公開は GitHub Actions が自動発行する `GITHUB_TOKEN` を使うので、
リポジトリのSecretsなどにあなた自身のトークンを登録する必要はありません
（workflow内の `permissions: contents: write / pages: write / id-token: write` だけで完結します）。
ただし、YouTube登録者数を1万人超でも端数まで正確に取得したい場合だけ、別途YouTube Data APIキーが
必要です（後述の「YouTube Data APIキーの取得方法」参照）。このキーはあなた自身がGoogleで発行し、
GitHubリポジトリのSecretsに直接登録するものなので、Claude側やこのチャット上でキーを
やり取りすることはありません。キーを登録しなくても`scrape_youtube.py`は動作しますが、その場合は
チャンネルページのスクレイピングにフォールバックするため、1万人超のチャンネルは概算値になります
（詳細は「YouTube Data APIキーの取得方法」末尾およびYouTube登録者数の既知の制約を参照）。

## YouTube Data APIキーの取得方法

登録者数を1万人未満まで含めて正確な数字で取得するため、YouTubeチャンネルページの
スクレイピングではなく公式のYouTube Data API v3を使っています。無料枠（1日10,000ユニット）
の範囲内で十分足ります（このリポジトリの規模なら1日1ユニットも使いません）。

1. https://console.cloud.google.com/ にアクセスし、適当な名前で新しいプロジェクトを作成する
2. 「APIとサービス」→「ライブラリ」で「YouTube Data API v3」を検索し、有効にする
3. 「APIとサービス」→「認証情報」→「認証情報を作成」→「APIキー」でキーを発行する
   （必要なら「APIの制限」で YouTube Data API v3 のみに絞っておくと安全）
4. あなたのGitHubリポジトリの Settings → Secrets and variables → Actions →
   「New repository secret」で、Name: `YOUTUBE_API_KEY` / Secret: 発行したキー を登録する
5. これで `daily-update.yml` の `scrape_youtube.py` ステップが自動的にこのSecretを読み込みます

このキーを設定していない場合や、キーが無効・クォータ超過などでAPI呼び出しそのものが失敗した場合は、
`scrape_youtube.py` は自動的に旧来のチャンネルページスクレイピング方式にフォールバックします
（エラーにはならず、登録者数の取得自体がスキップされることはありません）。ただしフォールバック時は
登録者数が概ね1万人を超えるチャンネル（12チャンネル）はYouTube側の表示自体が「1.35万人」のように
丸められるため、端数までの正確な数字は取れません。端数まで必要な場合はAPIキーの設定が必須です。
その日どちらの方式で取得されたかは `data/snapshots/youtube_*.json`（history.csv取り込み前の
生データ）の各行の `via`（"api" または "scrape"）フィールドで確認できます。

## なぜGitHub Actions方式にしたか

Cowork（Claude）側のスケジュール機能で毎日実行することも技術的には可能ですが、その場合
「GitHubに公開する」ためには結局GitHubへのpush用トークンをClaude側の実行環境に渡す必要があります。
認証情報をチャット上でやり取りしたり、外部の実行環境に持たせたりするのは避けたい方式のため、
スクレイピング〜データ更新〜コミット〜Pages公開まで**すべてGitHubのインフラ内で完結する**
GitHub Actions方式を採用しています。Claude側では初期セットアップ（このリポジトリ一式の作成）だけを行いました。

## なぜsvlabo.jpだけ手動にしたか

svlabo.jp（ランクマッチ最高順位）は当初、毎日自動取得→毎月1日のみ自動取得、と段階的に
自動化しようとしていましたが、以下の理由で完全に自動化対象から外し、手動運用に変更しました。

- 元々ランクマッチの最高順位は月1回程度しか動かないデータで、頻繁な自動更新の必要性が薄い
- 3サイトの中で唯一FC2側のボット検知に引っかかり、User-Agent偽装等の対策が必要だった
  （個人運営のFC2ブログなので、今後も同様の検知強化が入るリスクがある）
- テーブルの区切り文字（タブか改行か）が実際に動かすまで分からず、他の2サイトより
  デバッグに時間がかかった
- 取得したデータをそのまま使うのではなく手元で加工したい、という利用イメージだったため、
  自動でhistory.csvに混ぜ込む設計自体が過剰だった

`scripts/scrape_svlabo.py` 自体は動作する状態で残してあります。使いたくなったら
`cd scripts && python scrape_svlabo.py && python update_history.py` を手元やActionsの
手動実行で叩けば、今まで通り `data/history.csv` に取り込めます。使わないなら
`scripts/scrape_svlabo.py` を削除しても他のスクリプトには影響しません。

### 選手名の表記ゆれについて（NAME_ALIASES）

`data/svlabo_leaderboards.csv`はsvlabo.jp側の表記をそのまま持っているため、`data/players.csv`
の選手名と完全一致しないケースがあります（例: `Chappy` → svlabo.jp側は`Chappy_ttv`、
`ぱんさく` → svlabo.jp側は`さくさくぱんだ`。どちらも`team_tag=RID`で本人と確認済み）。

このズレは`site/common.js`の`NAME_ALIASES`にマッピングを追記することで吸収しています。
`ranking.html`の「CR順位 TOP N入り回数」ランキングはこの対応表と`normalizeName()`
（全角/半角スペース除去+小文字化。`scripts/common.py`の`normalize_name()`と同じ考え方）
を経由して選手を突き合わせているため、多少の表記ゆれなら自動的に吸収されます。
それでも一致しない新しいケースが見つかったら`NAME_ALIASES`に追記してください。

### 対戦成績について（match_results.csv・battle_details.csv / rounds.html・sections.html）

対戦まわりは主語が違う2つのページに分けています。

- **通算成績**（`rounds.html`）… 主語は「選手」。誰が何勝何敗で通算成績はどうか。
  `?name=選手名` でその選手個人の対戦履歴を表示します。データ元は`match_results.csv`。
- **節別結果**（`sections.html`）… 主語は「試合」。第N節のROUND1で誰がどのクラスを使い、
  何を登録して使わなかったか、配信のどこから見られるか。データ元は`battle_details.csv`。

一時期この2つを`rounds.html`のページ内タブ（「通算成績」「節別に見る」ボタン）にまとめて
いましたが、節別結果はナビから2階層下に埋もれる割に利用頻度が高かったため、ナビの第1階層に
独立させました。旧URL`rounds.html?view=sections`は`sections.html`へ自動転送します。

さらに古い`matches.html`は、旧URL（`matches.html`、`matches.html?name=選手名`）を共有・
ブックマークしている人のために、クエリ文字列を保ったまま`rounds.html`へ転送するだけの
リダイレクトスタブとして残してあります。

#### 通算成績・個人の対戦履歴（match_results.csv）

PS公式戦の個人成績（勝敗・獲得ポイント・使用クラス・対戦相手）は、以前は history.csv に
`ps_win`/`ps_point`として1ラウンドごとの値を記録していましたが、以下の理由で
`data/match_results.csv`という別ファイルに分離しました。

- ラウンド単位の勝敗（0/1）や獲得ポイント（0/1）は、そもそも折れ線グラフにする意味がない
- 「その時点の期間だけのランキング」を出しても、通算の強さを表さず紛らわしい
  （実際に「ある1ラウンドの獲得ポイントだけでランキングされる」という問題が起きていた）
- 見せたいのは「通算成績」と「いつ・誰と・何のクラスで戦ったか」という試合単位の情報

`match_results.csv`のスキーマ:

| 列 | 内容 |
|---|---|
| section | 節番号（1〜14） |
| half | `前半` / `後半`（第3節のように1日開催で分かれていない節は空） |
| round_no | その節（前半/後半）の中でのROUND番号 |
| battle_no | そのROUNDの中でのBATTLE番号 |
| round | 試合の開催日（例: `2026-07-22`） |
| date | この試合を最後に観測した日（スクレイピング日。参考情報） |
| team_tag / player_name | 選手側のチーム・選手名 |
| class | 選手が使用したクラス |
| result | `WIN` / `LOSE` |
| point | 獲得ポイント（勝ちなら1、負けなら0） |
| opponent_team_tag / opponent_name / opponent_class | 対戦相手のチーム・選手名・使用クラス |

重複排除のキーは `(section, half, round_no, battle_no, player_name)` です（`date`は含めません）。
同じ消化済み試合は毎日のスクレイピングで繰り返し観測されるので、`date`をキーに含めると
実行のたびに「別の試合」として重複記録されてしまうためです。

> 以前はキーが `(round, player_name)` で、`round`は試合日時の文字列でした。2026-08-27に
> 公式サイトのリニューアルでパースが崩れた際、`round`が`match_14`のようなダミー値、
> `player_name`がクラス名になった行が生成され、**毎回新しいキーになるため既存行を上書きせず
> 153行そのまま積み上がりました**。節・ROUND・BATTLE番号をキーにすることで、同じバトルは
> 必ず同じキーになり増殖しません。また`section`が数字でない行・`result`が`WIN`/`LOSE`でない行は
> マージ時に落とすので、過去に混入したゴミ行も自動的に消えます。

`rounds.html`の「通算成績」は全選手の累計勝敗・勝率・獲得ポイントをランキング表示し、
選手名をクリックすると`?name=選手名`でその選手の試合履歴（日時・使用クラス・対戦相手・
相手クラス・勝敗・配信リンク）を一覧表示します。クラス表示にはユーザーから提供された
シャドウバースの公式クラスアイコン（`site/images/classes/`、8種のSVG）を使っています。
なおPS公式戦の勝利数・獲得ポイントは`ranking.html`の「PS公式戦」グループからもランキング
として見られます。

#### 節別詳細（battle_details.csv）

svlabo.jpは節（1節、2節、...）が終わるごとに「Premier Series 26-27 N節 試合詳細結果＆配信時間指定URL」
という記事を公開しています（例: `https://svlabo.jp/blog-entry-1793.html`）。この記事には公式サイトの
試合結果には無い情報が載っています。

- そのバトルで**実際に使ったクラス**と、**登録していたが使わなかったクラス**（BO1で何デッキ持ち込んだか）
- 配信の**該当バトル開始時点にジャンプするタイムスタンプ付きURL**

これを`data/battle_details.csv`に取り込み、`rounds.html`（ナビの「対戦成績」）の「節別に見る」で
表示しています。使ったクラスは通常表示、登録していたが使わなかったクラスは薄く表示することで、
一目で区別できるようにしています。

**取得方法（手動トリガー、自動実行はしていない）**: この記事はsvlabo.jpが節ごとに不定期に公開するもので、
URL（`blog-entry-XXXX.html`）に規則性が無いため新記事の自動発見ができません。新しい節の記事が公開されたら、
そのURLを教えてもらって取り込む運用です。スクリプトとしては以下のように実行します（複数節をまとめて渡すことも
できます）。

```
cd scripts
# 1記事に4ROUND全部入っている節（第3節など）はsectionだけ渡す
python scrape_svlabo_battle_details.py https://svlabo.jp/blog-entry-1834.html 3

# 前半戦/後半戦で記事が分かれている節（第4節など）は section:half の形で明示する
python scrape_svlabo_battle_details.py \
  https://svlabo.jp/blog-entry-1839.html 4:前半戦 \
  https://svlabo.jp/blog-entry-1851.html 4:後半戦

# update_history.py の実行は不要（このデータはhistory.csvとは別経路）
```

**`前半戦`/`後半戦`の指定について**: 節によって記事の作られ方が違います。第3節のように1日開催で
1記事に4ROUND全部載る場合と、第4節のように前半（8/5）・後半（8/12）で記事自体が分かれる場合があります。
`half`を省略すると「1記事に4ROUND入っている」前提の自動判定（3カード目に入ったら後半戦とみなす）に
なるため、**分割記事でこれを省略すると後半戦の記事まで前半戦として記録されます**。記事タイトルに
「前半戦」「後半戦」と入っている場合は必ず明示してください。

記事ページには表示用HTMLとは別に、対戦データそのものがJSオブジェクト（`battle_info`, `tour_info`）として
`<script>`タグ内に埋め込まれています。これは公式に文書化されたものではなく、ブラウザで実際に開いて調査して
見つけた構造なので、svlabo.jp側の実装が変わると取得できなくなる可能性があります（その場合は同じ要領で
再調査が必要）。重複排除のキーは`(section, half, round_no, battle_no)`なので、同じ節を複数回取り込んでも
行が増殖することはありません。

**通算成績（match_results.csv）との突き合わせについて**: `match_results.csv`（公式サイト由来、roundは
日時文字列）と`battle_details.csv`（svlabo.jp由来、section/half/round_no/battle_no採番）は採番方式が
別なので、共通のキーがありません。そのため`rounds.html`の個人成績表では「対戦した2チームの組み合わせ＋選手名」
（`findBattleDetail()`、`site/common.js`）で突き合わせています。取り込み済みの節に実際にその選手が
個人戦で出場していれば配信リンクと未使用クラスが表示されますが、**まだ取り込んでいない節の試合や、
その節でチームバトル枠にしか出ていない選手の試合は突き合わせが見つからず「配信: -」のままになります**
（バグではなく、単にその試合をカバーするsvlabo.jp記事をまだ取り込んでいないだけです。該当する節の
記事URLが分かれば`scrape_svlabo_battle_details.py`で追加取り込みできます）。

## 公式サイトのリニューアルについて（2026-08-27）

`ps.shadowverse-wb.com` が全面リニューアル（Svelte製に作り直し）され、DOMもテキストの並びも
全部変わりました。旧クラス名（`.results__game` / `.results__team-name` / `.results__score-num` など）は
1件もヒットしなくなり、これに依存していた3つのスクリプトが同時に壊れました。

| スクリプト | 壊れ方 | 対応 |
|---|---|---|
| `scrape_ps_results.py` | モーダルの並び順決め打ちが崩れ、列が1つずつズレた行を153行書き込んだ | DOM構造ベースに全面書き換え＋検算追加 |
| `scrape_result.py` | セレクタが全滅。ただし検算が効いて既存result.jsonは保護された（取得は停止） | 新セレクタに更新 |
| `scrape_player_images.py` | 画像のホスト・パスが変わり、ページもSPA化してrequestsでは読めなくなった | Playwright描画＋新URL規則に更新 |

新しいDOMではクラス名に `svelte-xxxxx` というハッシュが付きます。**これはビルドのたびに
変わるのでセレクタに使ってはいけません**。各スクリプトはハッシュを含まない部分
（`battle-card`, `-score-value`, `-team-score-name` など）だけを使っています。

このリニューアルで公式サイト側にも「残り登録デッキ」とデッキリストURLが載るようになりました
（svlabo.jpから手動で取り込んでいる`battle_details.csv`と同種の情報）。現時点では取り込んでいません。

## 既知の制約・注意点

- **shadowverse-reference.comは非公式のファンサイトです**（ps.shadowverse-wb.comは公式サイト）。
  仕様変更やサイト停止のリスクは常にあります。各スクリプトは失敗しても他のスクリプトの実行を
  妨げないように `continue-on-error: true` にしていますが、パースが崩れた場合は
  `data/snapshots/*_debug*.json` や `*_raw*.json` を見て正規表現/パーサーを調整してください。
  （各スクリプトは失敗時もこのデバッグ用の生テキストを必ず保存し、ログにも直接出力するようにしています）
- **shadowverse-reference.com**: Xフォロワー数は「現在値」のみが取得できます（このサイト自体に
  過去の履歴はない）。そのため、フォロワー数の推移グラフは このスクリプトを動かし始めた日から
  蓄積されていきます。配信時間・視聴時間・再生回数・動画本数は隔週の期間集計を過去分までさかのぼって
  取得できます。なお実データ確認の結果、各行の順位・選手名の後ろに単独のタブ文字だけの行が
  挟まっていたため、パース前にタブ文字を除去する処理を入れています。
- **ps.shadowverse-wb.com（PS戦績）**: 「試合結果詳細」モーダルは実際にGitHub Actions上で
  取得した生テキストを元に、「BATTLE Nトークンの前後を選手名/クラス/勝敗/獲得ポイントとして
  読み取る」ロジックに書き換え済みです（`parse_battles()`）。「チームバトル」という
  個人に紐づかない対戦枠は成績から除外しています。対戦相手の名前・使用クラスも
  同じトークン列から取得し、`match_results.csv`に記録しています（詳細は
  「試合結果について」参照）。
- **YouTube登録者数（scrape_youtube.py）**: メインはYouTube Data API（`channels.list`）による
  取得で、`YOUTUBE_API_KEY`が設定されていれば端数まで正確な登録者数が取れます。APIキーの
  取得方法は上記「YouTube Data APIキーの取得方法」を参照してください。
  キーが未設定の場合、またはAPI呼び出し自体が失敗した場合（キー無効・クォータ超過など）は、
  自動的にチャンネルページ（/about）のHTMLをスクレイピングする旧方式にフォールバックします。
  37チャンネル全部を実際に確認したところ、この旧方式では登録者数が概ね1万人を超えるチャンネル
  （12チャンネル）はYouTube側の表示自体が「1.35万人」のように丸められてしまい、端数まで
  取得できません（これがそもそもAPI方式に切り替えた理由です）。端数まで必要なチャンネルが
  含まれる場合は、APIキーの設定を推奨します。
  Chappyのみ、shadowverse-reference.com上でもYouTubeチャンネルが確認できず（Twitchのみで
  配信）、両方式とも対象外になります。
  このサイト自体には登録者数の推移データはなく「現在値」しか取れないため、Xフォロワー数と同様、
  このスクリプトを動かし始めた日からhistory.csvに蓄積されていきます。
- **Twitchのフォロワー数は今のところ自動取得していません**: 37名中8名
  （ねぎま、glory、Toby、もっちゃま、ぱらちゃん、折り紙、Chappy、Stylish_deko）は
  Twitchでも配信しており、players.csvにtwitch_url列として保持していますが、フォロワー数の
  自動取得はまだ実装していません。理由は2つあります。
  1. Twitchの公式Helix APIでフォロワー数を取得する`Get Channel Followers`エンドポイントは、
     配信者本人（またはそのモデレーター）のOAuthトークンでのアクセスしか許可されておらず、
     アプリ側の資格情報だけでは他人のチャンネルのフォロワー数を取得できない仕様になっている
     （2023年のAPI変更以降）。
  2. 非公式のGraphQL API（`gql.twitch.tv`）経由で取得する方法も試したが、フォロワー数を含む
     クエリの正しいpersisted queryハッシュ値を特定できなかった（Twitchの公式Webクライアントの
     内部実装に依存しており、頻繁に変わる可能性が高く、svlabo.jpよりもさらに壊れやすい）。
  もしTwitchのフォロワー数も追跡したい場合は、8名それぞれに自分のチャンネルでこのツール用の
  アプリを認可してもらう（現実的に厳しい）か、GraphQLの正しいクエリを別途調査する必要がある。
- **開発環境での制約**: このリポジトリのコードは、Claudeの実行サンドボックス環境ではネットワーク制限により
  Playwrightのブラウザバイナリをダウンロードできず、実際にブラウザを起動しての動作確認はできません。
  そのため、GitHub Actions上で実際に取得された生ログ（タイムスタンプ付きログファイル）を
  ダウンロードして送ってもらい、そのテキストに対してパース処理を書いて検証する、というやり方で
  デバッグしています。今後もエラーが出た場合は、Actionsの実行結果ページ右上の「...」から
  「Download log archive」でログ一式をダウンロードし、このチャットに添付してもらえれば
  同じ方法で調査できます。

## チーム順位について（result.json）

トップページ（`index.html`）はチームを現在の順位順にアコーディオン表示しますが、その順位の元データが
`data/result.json`です。もともとは別プロジェクト（予想サイト「2026ps-fixed」）で使われていた
スキーマをそのまま踏襲しています。

```json
{
  "status": "in_progress",
  "teams": [
    { "id": 1, "win": 1, "lose": 0, "diff": 2, "battlepoint": 3 },
    ...
  ]
}
```

`id`とチームの対応（`teams.json`由来、固定）:

| id | team_tag | チーム名 |
|---|---|---|
| 1 | CR | Crazy Raccoon |
| 2 | ZETA | ZETA DIVISION |
| 3 | DFM | DetonatioN FocusMe |
| 4 | VRL | VARREL |
| 5 | MRG | MURASH GAMING |
| 6 | RC | REJECT |
| 7 | RDL | RIDDLE ORDER |
| 8 | LVH | レバンガ北海道 |

各項目の意味（1ROUND＝チーム対チームの1試合。複数バトルで構成され、先に3バトル取った側が勝ち）:

- `win` / `lose`: ROUND単位の勝敗数
- `diff`: バトル単位の得失差。全ROUNDの「自分のバトル勝ち数 − 相手のバトル勝ち数」の合計
  （例: 3-1で勝ったら+2、1-3で負けたら-2）。8チーム合計は必ず0になります
- `battlepoint`: バトル単位の勝ち数の累計（負けた分は引かない。例: 3-1で勝ったら3、1-3で負けたら1）。
  この値の大小で順位を決め、同点なら`diff`で並べます

**このファイルは`scrape_result.py`が毎日自動生成します。**
取得元は公式サイト`https://ps.shadowverse-wb.com/26-27/schedule-results/`です。
各ROUNDのスコア（例「Crazy Raccoon 3 - 1 ZETA DIVISION」）だけを読み取り、上記4項目はすべて
こちら側で計算しています。この計算方法は第1〜4節の全16ROUNDで公式順位表と突き合わせ、
8チーム全項目が一致することを確認済みです。

> 以前は別プロジェクトの予想サイト（uthomeless-public-tool）が公開しているJSONをそのまま
> コピーしていましたが、公式が結果を出してもあちら側を手で更新するまで順位が古いままになる
> という問題があったため、公式から直接計算する方式に変更しました。外部ツールへの依存はありません。

取得や検算に失敗した場合は、既存の`data/result.json`を一切書き換えずに終了します。検算の内容は
「実施済みの試合が1件以上読めているか」「得失差の合計が0か」「勝敗数の合計が試合数と一致するか」
「players.csvに無いチーム名が出てきていないか」の4点です。1つでも落ちればスクリプトは異常終了し、
既存ファイルはそのまま残ります（ワークフロー側は`continue-on-error: true`なので他の処理は続きます）。

`status`と`confirmed_odds`は手動で設定しうる項目なので、既存ファイルの値をそのまま引き継ぎます。

値を一時的に手で直したい場合は`data/result.json`を直接編集してpushすることもできますが、
次回実行時に公式サイトの値で再計算・上書きされます。恒久的に手動運用したい場合はワークフローから
該当ステップを外してください。

まだ一度もデータがない（8チーム全員 win=lose=0）場合は、`site/common.js`の
`computeTeamStandings()`が自動的に`data/match_results.csv`（選手個人の試合結果の集計）から
順位を計算するフォールバックに切り替わります。ただしこちらは個人戦の合計ポイントだけを見ており、
公式の得失差ボーナスなどは反映されないため、正式な順位としてはresult.jsonの自動取得を優先します。

## 選手写真について（scrape_player_images.py）

各選手のページ（`https://ps.shadowverse-wb.com/26-27/teams/{ps_slug}`）に掲載されている
プロフィール写真を取得し、`site/images/players/` にキャッシュして選手一覧・選手詳細ページに
表示しています。`ps_slug`は players.csv に列として持たせています（例: Atomなら`atom`）。

- 写真は基本的にシーズン中頻繁には変わらない想定のため、一度取得した選手はスキップし、
  再ダウンロードしません。差し替えたい場合は該当ファイルを`site/images/players/`から
  手動で削除してから`scrape_player_images.py`を再実行してください。
- 写真がまだ無い選手（初回push直後や、取得に失敗した選手）は、チームカラーの円に
  頭文字を表示するフォールバック表示になります（`site/common.js`の`avatarHTML()`）。
- **出典・権利について**: これらの写真は公式サイト（ps.shadowverse-wb.com、Cygames運営）に
  掲載されている選手プロフィール写真で、著作権は運営元に帰属します。本スクリプトは
  非商用の個人的なファントラッカー用途としてキャッシュ・表示するものです。公開する
  リポジトリ/サイトの性質によっては、権利者の意向を確認したり、キャッシュせず外部URLに
  直接リンクする形（写真を自分のリポジトリに置かない）に変更したりすることも検討してください。

## players.csvについて

もともとのplayers.csvは`2026ps-fixed/data/teams.json`（初期にいただいたファイル）から
抽出したものでしたが、そこに入っていたyoutube_urlは古い/一部欠落している状態でした
（Mishadow51, monakawan, 山田レクイエム, Stylish_dekoの4名は本来YouTubeチャンネルを
持っているのに空欄になっていた）。

現在のplayers.csvは、実際に配信活動状況をshadowverse-reference.comで全選手分確認し直し、
そこで使われているYouTubeチャンネルID（`/channel/UCxxxx`形式）に統一しています。
併せてtwitch_url列を新設し、Twitchでも配信している8名（ねぎま、glory、Toby、もっちゃま、
ぱらちゃん、折り紙、Chappy、Stylish_deko）のTwitch URLも入れてあります（Chappyのみ
YouTubeを持たずTwitchのみ）。

さらに`ps_slug`列を追加し、公式サイトの選手個人ページURL（`ps.shadowverse-wb.com/26-27/teams/{ps_slug}`）
のスラッグを37名分保持しています。`scrape_player_images.py`が選手写真を取得する際に使います。

## history.csv のスキーマ

| 列 | 内容 |
|---|---|
| date | 取得日（JST） |
| team_tag | チーム略称（CR/ZETA/DFM/VRL/MRG/RC/RDL/LVH） |
| player_name | 選手名（players.csv基準） |
| metric | 指標名（followers, youtube_subscribers, stream_duration, watch_time, video_view_count, video_upload_count など。svlabo.jpを手動で取り込んだ場合は cr_rank_エルフ 等も入る。PS戦績はhistory.csvには入らず match_results.csv 側） |
| period | 期間キー（current, jul_early_2026, cumulative_to_date, 隔週ラベルなど） |
| value | 数値 |

選手詳細ページ（`player.html`）の折れ線グラフは、上記のうち「推移として見る価値が薄い/
変動が少ない」ものを除いた followers・youtube_subscribers・stream_duration の3つだけを
デフォルトで表示しています。watch_time（視聴時間）・video_view_count（累積再生回数）も
継続的に伸びる指標として表示候補になり得るので、必要であれば追加できます。

## 次にやると良さそうなこと

- 過去分のバックフィル（shadowverse-reference.comの隔週データは4月前半まで遡れるので、
  初回だけ手動でperiodループを回して過去分を先に埋めておくと、公開初日からグラフに厚みが出る）
- PS戦績のクラス別勝率など、history.csvを使った追加集計ページ
