# CLAUDE.md — svps-tracker 引き継ぎ書

このファイルは、**新しいセッション（Cowork / Claude Code）に作業を引き継ぐための唯一の入口**です。
このリポジトリで作業を始めるAIは、他の何よりも先にこのファイルを最後まで読んでください。

- 公開サイト: https://hirobosu-staff.github.io/svps-data/
- リポジトリ: `hirobosu-staff/svps-data`（ローカル: `C:\Users\mgtfu\Documents\GitHub\svps-data`）
- 目的: Shadowverse Premier Series 26-27 の選手・チームデータを毎日自動収集し、GitHub Pages で公開する
- 技術的な詳細（各スクリプトの仕様、スキーマ、設計理由）は **`README.md`（644行）** に全部書いてある。
  このファイルは「**どう振る舞うか**」と「**過去に何をやらかしたか**」を引き継ぐためのもの。

---

## 0. セッション開始時にやること

1. このファイルを読む
2. `README.md` の目次（`grep -n '^#' README.md`）を見て、触る領域の節だけ読む
3. ユーザーの依頼を実行する。**リポジトリのファイルは直接編集する**（後述）

---

## 1. 絶対に守るルール

これは好みの問題ではなく、**過去に実際に事故が起きた結果として決まったルール**です。

### 1-1. git コマンドを絶対に実行しない

`git status` も含め、このリポジトリに対して git を一切叩かない。
過去に `.git/index.lock` を残してユーザーの `git pull` を壊した。ユーザーの言葉:

> 「直接編集可能にしたせいかわからないがpullできなくなった。これは望んでいた形ではない。」

差分が知りたいときはファイルを読んで比較する。git は使わない。

### 1-2. commit と push はユーザーが行う

> 「コミットやpushはこちらで行う。」

作業が終わったら「コミットとpushをお願いします」で締める。自分でやらない。

### 1-3. ファイルを提示するのではなく、リポジトリを直接書き換える

> 「毎回ここにファイルをコピーしてるのがめんどくさいという話をしている。理解しろ。」

`C:\Users\mgtfu\Documents\GitHub\svps-data` 配下を Write / Edit で直接編集する。
outputs フォルダに作ってから提示する、という流れは取らない。

### 1-4. 変更したファイルは**全部**報告する

> 「どこに何を追加した？なぜここにないファイルも更新されている？意味の分からないことは言うな」

14ファイル変更して7ファイルしか報告しなかった事故がある。触ったものは漏れなく列挙する。

### 1-5. スマホ対応で PC 版の表示を変えない

> 「PC版の表示は全く変更せずにスマホでも見れるように対応してほしい」

スマホ対応は `site/style.css` 末尾の **`@media (max-width: 768px)` ブロック1つだけ**に閉じ込める。
このブロックの外を触ったら PC 表示が変わったということなので、やり直す。

### 1-6. 敬語を使う

> 「いや敬語使えやボケ」

ユーザーの口調に合わせて崩さない。常に敬語。

### 1-7. リポジトリを「一度消してから入れ替える」操作をしない

過去に実データ（history.csv・選手写真・試合結果）を複数回消している。
`README.md` の「【重要】既存リポジトリを更新するときの注意」を参照。
`data/history.csv` `data/match_results.csv` `data/battle_details.csv` `data/schedule.csv`
`data/result.json` `data/player_images.json` `data/snapshots/` `site/images/players/` は
**Actions が書き込む実データ**なので、一括上書きの対象に入れない。

### 1-8. Svelte のハッシュ付きクラス名をセレクタに使わない

公式サイト（ps.shadowverse-wb.com）は 2026-08-27 に Svelte で作り直された。
`svelte-1a2b3c` のようなクラス名はビルドのたびに変わるので、**絶対にセレクタに使わない**。
構造的なクラス名（`.battle-card`, `.rounds-list__item` 等）だけを使う。

---

## 2. 作業環境

| 項目 | 値 |
|---|---|
| ローカルリポジトリ | `C:\Users\mgtfu\Documents\GitHub\svps-data` |
| 公開URL | https://hirobosu-staff.github.io/svps-data/ |
| 自動実行 | GitHub Actions `daily-update.yml`、cron `17 3 * * *` (UTC) = **12:17 JST** |
| サイトのみ再デプロイ | `deploy-pages.yml`（`site/**` 等の push がトリガー） |
| 改行コード | リポジトリ内のファイルは **CRLF**。書き換え時は維持すること |

**動作確認は公開サイトで行う。** ローカルの `file://` ではなく
`https://hirobosu-staff.github.io/svps-data/` を見る。ユーザーの指示:

> 「ローカルじゃなくてこっち使って」

スマホ表示の確認は、内蔵ブラウザの `resize_window preset: mobile` を使う。
Chrome のウィンドウリサイズでは viewport が変わらず確認にならない（実際に失敗した）。

---

## 3. システム全体像

```
 [取得元]                          [スクリプト]                        [データ]                [表示]

 shadowverse-reference.com  ──→  scrape_reference.py        ─┐
 （非公式ファンサイト）                                        │
 YouTube (API or スクレイプ) ──→  scrape_youtube.py          ─┼→ snapshots/*.json
                                                             │        │
 ps.shadowverse-wb.com      ──→  scrape_ps_results.py       ─┘        │ update_history.py
 （公式・Svelte製SPA）                                                 ↓
                            ──→  scrape_result.py           ─────→ data/history.csv    ─┐
                            ──→  scrape_schedule.py         ─────→ data/result.json    ─┤
                            ──→  scrape_player_images.py    ─────→ data/schedule.csv   ─┼→ site/*.html
                                                            └────→ data/match_results.csv│   (common.js)
 svlabo.jp                  ──→  scrape_svlabo_battle_details.py ─→ data/battle_details.csv
 （非公式・FC2ブログ）        ──→  scrape_svlabo.py（手動のみ）  ─→ data/svlabo_leaderboards.csv
```

### データファイルの責務

| ファイル | 中身 | 更新 |
|---|---|---|
| `data/players.csv` | 選手マスタ（8チーム37名） | 手動 |
| `data/history.csv` | 日次の数値（ロング形式 date/team_tag/player_name/metric/period/value）約8.4万行 | 自動 |
| `data/match_results.csv` | 公式戦の個人成績（1試合1行） | 自動 |
| `data/battle_details.csv` | svlabo由来の節別対戦詳細（使用クラス等） | 自動 |
| `data/result.json` | チーム順位（公式のスコアから集計） | 自動 |
| `data/schedule.csv` | シーズン日程 56行 / 14節 | 自動 |
| `data/svlabo_leaderboards.csv` | ランクマッチCRランキング | **手動のみ** |

### ページ構成（`site/`）

| ファイル | 役割 |
|---|---|
| `index.html` | **順位表**。先頭に「次の節」パネル。チームはアコーディオン、中身は軽量な選手名リスト |
| `players.html` | **選手一覧**。チームチップで絞り込み + 検索。`?team=` `?q=` 対応 |
| `player.html` | 選手個別（折れ線グラフ + 対戦履歴）。`?name=` |
| `rounds.html` | 通算成績 |
| `sections.html` | 節別結果（**最新の節がデフォルト選択**） |
| `compare.html` | 比較表。`<body class="wide">` で横幅 1560px |
| `beyond.html` | BEYOND（CRランキング関連） |
| `ranking.html` | **廃止済み**。compare.html へのリダイレクトスタブ |
| `common.js` | データ読み込み・集計・順位付けの共通処理。**まずここを読む** |
| `style.css` | 全ページ共通。末尾に `@media (max-width: 768px)` が1ブロックだけある |

---

## 4. ドメイン知識（間違えやすいところ）

### 順位表の数字の意味

- **WIN / LOSE** = その節の **ROUND（対戦カード）** 単位の勝敗であって、個人戦の勝敗ではない
- **DIFF** = Σ(自チームのバトル勝数 − 相手チームのバトル勝数)
- **BATTLE POINT** = Σ(自チームのバトル勝数)
- **ソート優先順位は `ROUND WIN → DIFF → BATTLE POINT`**。公式もこの順。
  一度 BATTLE POINT を最優先にして公式と食い違った事故がある。

`result.json` は公式サイトの ROUND スコアから完全に再現できることを検証済み（全ラウンドで一致）。
外部ツールの JSON をコピーする方式は廃止済み。

### 節・半分・ラウンド

- 1シーズン = 14節。各節に「前半戦 / 後半戦」がある
- CSV のマージキー:
  - `battle_details.csv` → `(section, half, round_no, battle_no)`
  - `match_results.csv` → `(section, half, round_no, battle_no, player_name)`
- キーが不足していると**上書きされずに行が増殖する**。実際にこれで153行のゴミが混入した。

### チームタグと表記ゆれ

`CR / ZETA / DFM / VRL / MRG / RC / RDL / LVH`

svlabo 側は略称が違うことがあるので `TEAM_TAG_ALIASES` で吸収している（`VL→VRL`, `RID→RDL`）。
選手名の表記ゆれは `NAME_ALIASES`（README参照）。

### クラス番号（svlabo の `battle_info`）

`1=エルフ 2=ロイヤル 3=ウィッチ 4=ドラゴン 5=ナイトメア 6=ビショップ 7=ネメシス`

### svlabo 記事の「まだ試合をやっていない」判定

svlabo は**翌日以降の対戦カードを結果が空のまま先に公開する**。取り込んではいけない。
判定は `scrape_svlabo_battle_details.py` の中:

```python
def battle_is_played(b):
    if b.get("winlose") not in ("WIN", "LOSE"): return False
    return str(b.get("use1")) != "0" and str(b.get("use2")) != "0"
```

さらに `article_is_complete()` で「全バトルが実施済み」かつ「各ラウンドに
チームバトル行（pro1/pro2が空）が1つ以上ある」ことを確認している
（ユーザー談: 「チームバトルは必ず1戦以上行われるからそこを判定基準にしてもいい」）。

---

## 5. 過去の事故と対策（再発防止リスト）

| 事故 | 原因 | 対策（実施済み） |
|---|---|---|
| `.git/index.lock` を残してユーザーの pull を破壊 | AI が git を実行した | **git 禁止**（1-1） |
| 実データを複数回消した | リポジトリを空にしてから入れ替えた | 一括上書き禁止（1-7） |
| 公式リニューアルで 153行のゴミ混入（`round=match_14`, `player_name=ネメシス`, `class=LOSE`） | トークン順序変更 + マージキー不足 | セレクタを構造ベースに書き換え、マージキー拡張、`validate()` 追加、CSV を全件再生成 |
| 順位が bogus（0-1 が rank 17、0-2 が rank 23） | ソートキーと順位キーが別物だった。勝率は wins=0 のとき常に0 | **ソートと順位に同一の `rankKey` を使う**。`assignCompetitionRanks(list, keyFn)` は入力が keyFn と同じ順に並んでいることが前提 |
| 通算成績が負け数を無視 | 勝数だけで比較していた | `sortValue: r => r.stats.wins * 100000 - r.stats.losses` |
| ハンバーガーメニューが PC でも畳まれた | `<details>` を使った | 非表示 checkbox + label 方式に変更。**`<details>` は使わない** |
| タップ領域が 34x28 で小さすぎ | — | negative margin で 44x44 に（見た目のバーは不変） |
| index.html の `<title>` が「選手一覧」で players.html と重複 | — | 「順位表」に修正済み |
| 手動編集した result.json が自動処理に上書きされた | 自動取得が走る | 現在は公式から集計する方式なので手動編集は不要 |

### 環境上のハマりどころ

- **Playwright のブラウザバイナリは AI のサンドボックスでは落とせない**。実際のスクレイプ検証は
  GitHub Actions のログを落としてもらい、その生テキストに対してパーサを書く方式で行う
- **Chrome のバックグラウンドタブはタイマーが絞られる**（`document.hidden`）。クリックループが壊れる
- `javascript_tool` の出力は **約1150文字で切られる**。大きな抽出は分割する
- `common.js` の `parseCSV()` は `\r` を除去している。自前でテストする際は同じ処理を入れないと誤検知する

---

## 6. データ補正の運用ルール

`history.csv` の数値は外部サイトの表示値をそのまま取っているため、たまに連続性から外れる値が入る。
特に **YouTube 登録者数は API キー未設定でスクレイプにフォールバックしており、表示が3桁に丸められる**
（1.35万人など）ため、丸め由来の揺れと本当の異常の区別が必要。

> ユーザー談: 「APIはめんどいからやらない。今までので十分できている」

### 実施済みの補正

| 日付 | 内容 |
|---|---|
| 2026-09-20 | `youtube_subscribers` 全36件を 9/19 の値に置換（21件が実変更）。ユーザー指示「9/20のみ全データを修正。値は9/19と同じとする」 |
| 2026-09-17 | 「9/16と9/18の**両方**から外れている行」だけを 9/16 の値に戻す（8件）。9/17 は正常に伸びている行が混在していたため一律置換はしていない |

### 補正のやり方（次回もこの手順で）

1. バックアップを取る（`/tmp/history_backup_YYYYMMDD.csv`）
2. **V字/逆V字（前後両日の外側にある値）だけ**を対象にする。単調に増えている値は触らない
3. 前日の値で置き換える。ただし**前日自体が異常な場合は対象から外す**
   （例: monakawan の 9/17 は `468→479→469→483` で、外れているのは 9/16 の 479 のほう）
4. 行単位の置換で行い、**CRLF を維持**する
5. 検算: 総行数・列数・CRLF 数・置換後の推移・全期間の残存異常を出力する
6. `data/snapshots/*.json` は生ログなので**書き換えない**（証跡として残す）

### 触ってはいけないもの

- **`followers`**: 取得元が隔日更新で、9/15と9/16、9/17と9/18が全員一致するような並びになる。
  「前日と同じ」補正をかけると正常な更新を潰す
- 期間集計系（`stream_duration` / `watch_time` / `video_view_count` / `video_upload_count`）

### 現在残っている既知の異常

- 2026-09-16 monakawan `468 → 479 → 469`（外れているのは 9/16。未修正、ユーザーの承認待ち）
- 2026-09-08 かなで `582 → 588 → 587`（1.0%、丸め由来の可能性）
- 2026-09-18 Hirobosu `1680 → 1700 → 1690`（誤差10、丸め由来）

---

## 7. 変更時の検証チェックリスト

**何かを変えたら、報告する前に必ず確認する。** ユーザーの要求:

> 「まずは細心にできているかどうかを確認しろ」

### データを触ったとき

- [ ] 総行数・列数が想定どおりか
- [ ] CRLF が維持されているか（LF単独が混ざっていないか）
- [ ] 対象行だけが変わっているか（想定外の行が変わっていないか）
- [ ] 変更後の値の推移を目視で出す
- [ ] バックアップを残したか

### サイトを触ったとき

- [ ] 公開サイトの**全7ページ**を開いて崩れていないか
- [ ] スマホ（375px）で `scrollWidth == clientWidth == 375` になっているか（横スクロールが出ていないか）
- [ ] PC 表示が**一切変わっていない**か
- [ ] ページ間のリンクが全部生きているか（特に選手名 → `player.html?name=`）

### スクレイパを触ったとき

- [ ] 検算に失敗したら**既存ファイルを維持して終了**する作りになっているか
  （`scrape_result.py` は「試合が0件」「未知のチーム名」「DIFFの合計が0でない」「WIN/LOSE合計の不一致」で中断する）
- [ ] Svelte のハッシュ付きクラス名を使っていないか

---

## 8. 保留・未実装

- YouTube Data API キーの設定（ユーザーが不要と判断。設定すれば丸め問題が解消する）
- Twitch フォロワー数（API仕様上、本人のOAuthが必要で現実的に不可。README に調査結果あり）
- 過去データのバックフィル（reference側は4月前半まで遡れる）
- クラス別勝率などの追加集計ページ

---

## 9. README.md の索引

詳細が必要になったら該当節だけ読む（`grep -n '^#' README.md` で行番号が出る）。

| 知りたいこと | README の節 |
|---|---|
| 既存リポジトリ更新時の注意 | 【重要】既存リポジトリを更新するときの注意 |
| セットアップ・APIキー | セットアップ手順 / YouTube Data APIキーの取得方法 |
| 選手名の表記ゆれ | 選手名の表記ゆれについて（NAME_ALIASES） |
| 対戦成績のデータ構造 | 対戦成績について（match_results.csv・battle_details.csv） |
| 選手一覧の設計 | 選手一覧について（players.html） |
| 比較表の期間セレクタ | 比較の表について（compare.html） |
| 日程・「次の節」の定義 | 日程について（schedule.csv） |
| スマホのナビ | スマホのナビについて |
| 公式リニューアルの影響 | 公式サイトのリニューアルについて（2026-08-27） |
| 各取得元の制約 | 既知の制約・注意点 |
| 順位の計算根拠 | チーム順位について（result.json） |
| history.csv の列定義 | history.csv のスキーマ |
