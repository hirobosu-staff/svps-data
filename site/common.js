// 全ページ共通のデータ読み込み・表示ヘルパー。
// history.csv / players.csv / player_images.json を読み込んで各ページのJSに渡す。

const DATA_URL = "data/history.csv";
const PLAYERS_URL = "data/players.csv";
const IMAGES_MANIFEST_URL = "data/player_images.json";
const MATCHES_URL = "data/match_results.csv";
const BATTLE_DETAILS_URL = "data/battle_details.csv";
const RESULT_JSON_URL = "data/result.json";
const SVLABO_URL = "data/svlabo_leaderboards.csv";
// CR(ランクマッチ)順位の「TOP N入り回数」ランキングで選べるしきい値の候補
const CR_TOPN_THRESHOLDS = [10, 30, 50, 100];

// players.csv側の選手名と、外部サイト（svlabo.jp等）側の表記が一致しない既知のケース。
// 例: Chappy → svlabo.jp側は"Chappy_ttv"（Twitchハンドル込みの表記）、
//     ぱんさく → svlabo.jp側は"さくさくぱんだ"（そもそも表記が別物）。
// どちらもteam_tag=RID（RIDDLE ORDER）で本人だと裏取り済み。今後similarな表記ゆれが
// 見つかったらここに追記していく（scripts/common.pyのTEAM_TAG_ALIASESと同じ考え方）。
const NAME_ALIASES = {
  "Chappy": "Chappy_ttv",
  "ぱんさく": "さくさくぱんだ",
};

// サイト間の表記ゆれ（全角/半角スペース・大文字小文字）を吸収する緩い正規化。
// scripts/common.pyのnormalize_name()とロジックを合わせている。
function normalizeName(name) {
  return String(name == null ? "" : name).trim().replace(/[\s　]/g, "").toLowerCase();
}

// data/result.json の id (1〜8) と team_tag の対応。teams.json由来の並び順に合わせている。
const RESULT_ID_TO_TAG = {
  1: "CR", 2: "ZETA", 3: "DFM", 4: "VRL", 5: "MRG", 6: "RC", 7: "RDL", 8: "LVH",
};

// history.csvのperiod列は"jul_early_2026"や"regular_season"のような内部キー（英語）を
// そのまま保存している。以前はこれをそのままセレクトボックスやグラフの軸ラベルに出して
// いたため、UI上に生の英語キーが出てしまっていた。表示用に日本語ラベルへ変換する。
const MONTH_NUM = { jan: 1, feb: 2, mar: 3, apr: 4, may: 5, jun: 6, jul: 7, aug: 8, sep: 9, oct: 10, nov: 11, dec: 12 };
const PERIOD_LABELS = { current: "現在", regular_season: "レギュラーシーズン", cumulative_to_date: "通算" };

function periodLabel(period) {
  if (PERIOD_LABELS[period]) return PERIOD_LABELS[period];
  const m = String(period).match(/^([a-z]{3})_(early|late)_\d{4}$/);
  if (m && MONTH_NUM[m[1]]) return `${MONTH_NUM[m[1]]}月${m[2] === "early" ? "前半" : "後半"}`;
  return period; // 未知の形式はそのまま（フォールバック）
}

// 隔週periodを時系列順に並べるための数値キー。表示ラベル（"4月後半"等）の文字列ソートだと
// 桁数の関係で10月以降に順序が崩れるため、生のperiod文字列から直接計算する。
function periodSortKey(period) {
  if (period === "regular_season") return -1;
  const m = String(period).match(/^([a-z]{3})_(early|late)_(\d{4})$/);
  if (m && MONTH_NUM[m[1]]) return parseInt(m[3], 10) * 100 + MONTH_NUM[m[1]] * 10 + (m[2] === "early" ? 0 : 1);
  return 0;
}

// クラス名 → アイコンファイル名（アップロードされた公式クラスアイコンを使用）
const CLASS_ICONS = {
  "エルフ": "class_elf.svg",
  "ロイヤル": "class_royal.svg",
  "ウィッチ": "class_witch.svg",
  "ドラゴン": "class_dragon.svg",
  "ナイトメア": "class_nightmare.svg",
  "ビショップ": "class_bishop.svg",
  "ネメシス": "class_nemesis.svg",
  "ニュートラル": "class_neutral.svg",
};

function classIconHTML(className, size) {
  size = size || 20;
  const file = CLASS_ICONS[className];
  if (!file) return `<span style="font-size:12px;color:var(--text-muted);">${className || "-"}</span>`;
  return `<img src="images/classes/${file}" width="${size}" height="${size}" alt="${className}" title="${className}" style="vertical-align:middle;">`;
}

const TEAM_COLORS = {
  CR: "#e11d48", ZETA: "#7c3aed", DFM: "#f97316", VRL: "#eab308",
  MRG: "#10b981", RC: "#be123c", RDL: "#6366f1", LVH: "#0891b2",
};

const METRIC_LABELS = {
  followers: "Xフォロワー数",
  youtube_subscribers: "YouTube登録者数",
  stream_duration: "配信時間 (h)",
  stream_duration_cumulative: "累積配信時間 (h)",
  watch_time: "配信視聴時間 (h)",
  video_view_count: "動画再生回数",
  video_upload_count: "動画本数",
};

function metricLabel(m) {
  if (METRIC_LABELS[m]) return METRIC_LABELS[m];
  return m;
}

function isLowerBetter(m) { return /rank/.test(m); }

function fmtNum(v) {
  const n = Number(v);
  if (Number.isNaN(n)) return v;
  return n.toLocaleString("ja-JP");
}

function parseCSV(text) {
  // svlabo_leaderboards.csv などUTF-8 BOM付きで保存されているファイルがあるため、
  // 先頭のBOMを除去してからパースする（除去しないと1列目のヘッダ名が「﻿period」の
  // ようになり、その列だけ参照できなくなる）。
  if (text.charCodeAt(0) === 0xFEFF) text = text.slice(1);
  const lines = text.replace(/\r/g, "").split("\n").filter(l => l.length > 0);
  const headers = lines[0].split(",");
  return lines.slice(1).map(line => {
    const cols = line.split(",");
    const row = {};
    headers.forEach((h, i) => row[h] = cols[i]);
    return row;
  });
}

// history.csv / players.csv / player_images.json をまとめて読み込む。
// 画像マニフェストが無い（scrape_player_images.pyをまだ一度も実行していない）場合も
// 致命的エラーにはせず、空のマッピングとして扱う。
async function loadData() {
  const [histText, playersText] = await Promise.all([
    fetch(DATA_URL).then(r => r.ok ? r.text() : Promise.reject(new Error(`history.csv fetch failed: ${r.status}`))),
    fetch(PLAYERS_URL).then(r => r.ok ? r.text() : Promise.reject(new Error(`players.csv fetch failed: ${r.status}`))),
  ]);
  let images = {};
  try {
    const imgResp = await fetch(IMAGES_MANIFEST_URL);
    if (imgResp.ok) images = await imgResp.json();
  } catch (e) { /* 画像マニフェストが無くても致命的ではない */ }

  return {
    history: parseCSV(histText),
    players: parseCSV(playersText),
    images,
  };
}

// "regular_season"（レギュラーシーズン通算）や"current"（現在値）は、月ごと/隔週ごとの
// periodとは別枠の「集計済みの合算値」であり、実際の月別periodと期間が重複している
// （例: regular_seasonの値は4月後半〜7月後半の合計を既に含んでいる）。これらを他の月別
// periodと同列に並べて積み上げてしまうと二重計上になり、グラフが意味不明な形になる。
// 累積グラフは実際の月別/隔週periodだけを対象にする。
const CUMULATIVE_EXCLUDED_PERIODS = new Set(["regular_season", "current", "cumulative_to_date"]);

// 隔週などの期間ごとの値（例: stream_duration）は、そのまま折れ線にしても
// 「期間ごとにバラバラな値を単に線でつないだだけ」になり推移として意味を持たない。
// 期間を時系列順に並べて積み上げた累積値にすることで、初めて「増え続ける推移」として意味を持つ。
// 同じ期間が複数日にわたって観測される場合は、その期間の最新（最終）観測値を採用する。
function buildCumulativeSeries(history, playerName, metric) {
  const rows = history.filter(r => r.player_name === playerName && r.metric === metric && !CUMULATIVE_EXCLUDED_PERIODS.has(r.period));
  const byPeriod = {};
  rows.forEach(r => {
    if (!byPeriod[r.period] || byPeriod[r.period].date < r.date) byPeriod[r.period] = r;
  });
  // 並び順は観測日(date)ではなく、period自体の時系列キー(periodSortKey)を正とする。
  // dateは「その期間の値をいつ取得したか」でしかなく、period自体の前後関係とは無関係
  // （取得が遅れた期間があると日付ベースの並びが崩れるため）。
  const periodRows = Object.values(byPeriod).sort((a, b) => periodSortKey(a.period) - periodSortKey(b.period));

  let cumulative = 0;
  const labels = [];
  const data = [];
  periodRows.forEach(r => {
    cumulative += parseFloat(r.value) || 0;
    labels.push(r.period);
    data.push(cumulative);
  });
  return { labels, data };
}

function latestValue(history, playerName, metric) {
  const rows = history.filter(r => r.player_name === playerName && r.metric === metric);
  if (!rows.length) return null;
  rows.sort((a, b) => a.date < b.date ? 1 : -1);
  return rows[0].value;
}

// HTML属性値として安全に埋め込むためのエスケープ（ダブルクォート・タグ壊れ対策）。
function escapeAttr(s) {
  return String(s == null ? "" : s)
    .replace(/&/g, "&amp;")
    .replace(/"/g, "&quot;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

// 選手アバターのHTMLを返す。写真があれば<img>、無い/読み込み失敗時は
// チームカラーの四角にイニシャルを表示するフォールバックに切り替える。
// 以前はonerror属性の中にHTML文字列（ダブルクォート込み）をそのまま埋め込んでいたため、
// 属性がそこで途切れてページ上に壊れたマークアップの断片（["> のような文字列）が
// そのまま表示されてしまう不具合があった。data属性+共通関数呼び出しの形にして回避する。
function avatarFallbackHTML(player, size) {
  const color = TEAM_COLORS[player.team_tag] || "#888";
  const initial = (player.player_name || "?").trim().charAt(0);
  return `<div class="avatar-fallback" style="width:${size}px;height:${size}px;background:${color};font-size:${Math.round(size * 0.42)}px;">${escapeAttr(initial)}</div>`;
}

function avatarHTML(player, images, size) {
  const path = images[player.player_name];
  if (!path) return avatarFallbackHTML(player, size);
  return `<img class="avatar" src="${escapeAttr(path)}" width="${size}" height="${size}" alt="${escapeAttr(player.player_name)}"
    data-fallback-name="${escapeAttr(player.player_name)}" data-fallback-team="${escapeAttr(player.team_tag)}" data-fallback-size="${size}"
    onerror="handleAvatarError(this)">`;
}

// avatarHTML()のimgタグが読み込み失敗した時に呼ばれる（onerrorから参照するのでグローバルに置く）。
function handleAvatarError(imgEl) {
  const size = imgEl.getAttribute("data-fallback-size");
  const player = { player_name: imgEl.getAttribute("data-fallback-name"), team_tag: imgEl.getAttribute("data-fallback-team") };
  imgEl.outerHTML = avatarFallbackHTML(player, size);
}

// チームの略称テキストだけの色付きバッジ（チームロゴ画像が無い場合のフォールバック用）。
function teamBadgeHTML(teamTag) {
  const color = TEAM_COLORS[teamTag] || "#888";
  return `<span class="team-badge" style="background:${color}">${teamTag || "?"}</span>`;
}

// 提供された各チームの公式ロゴ画像ファイル名（site/images/teams/ 配下）。
const TEAM_LOGO_FILES = {
  CR: "cr.png", ZETA: "zeta.png", DFM: "dfm.png", VRL: "vrl.png",
  MRG: "mrg.png", RC: "rc.png", RDL: "rdl.png", LVH: "lvh.png",
};

// チームロゴ画像を表示する。対戦相手が不明("?"など)でロゴが無い場合は
// 従来の色付きテキストバッジにフォールバックする。
function teamLogoHTML(teamTag, size) {
  size = size || 28;
  const file = TEAM_LOGO_FILES[teamTag];
  if (!file) return teamBadgeHTML(teamTag);
  return `<img class="team-logo" src="images/teams/${file}" width="${size}" height="${size}" alt="${escapeAttr(teamTag)}" title="${escapeAttr(teamTag)}">`;
}

// svlabo.jp側の外部チーム表記 → 自チームの内部team_tagへの逆変換
// （scripts/common.pyのTEAM_TAG_ALIASES、自チーム→外部の逆）。
// beyond.html（ランクマッチの全ユーザーリーダーボード）で、自チーム所属選手の行を
// 自チームのロゴで表示するために使う。該当が無い（他チーム・無所属）タグはそのまま返す。
const REVERSE_TEAM_TAG_ALIASES = { RID: "RDL", VL: "VRL" };
function resolveTeamTag(tag) { return REVERSE_TEAM_TAG_ALIASES[tag] || tag; }

// data/match_results.csv を読み込む（存在しない/まだ試合が無い場合は空配列を返す）。
async function loadMatches() {
  try {
    const resp = await fetch(MATCHES_URL);
    if (!resp.ok) return [];
    return parseCSV(await resp.text());
  } catch (e) {
    return [];
  }
}

// 選手の通算成績（勝数・敗数・勝率・獲得ポイント）を試合結果の配列から集計する。
function summarizeMatches(matches, playerName) {
  const rows = matches.filter(m => m.player_name === playerName);
  const wins = rows.filter(r => r.result === "WIN").length;
  const losses = rows.filter(r => r.result === "LOSE").length;
  const points = rows.reduce((sum, r) => sum + (parseFloat(r.point) || 0), 0);
  return { played: rows.length, wins, losses, points, winRate: rows.length ? wins / rows.length : null };
}

// data/svlabo_leaderboards.csv（svlabo.jpから一括取得したランクマッチ全ユーザー分の
// period × class 別リーダーボード）を読み込む。取得できない場合は空配列を返す。
async function loadSvlaboLeaderboard() {
  try {
    const resp = await fetch(SVLABO_URL);
    if (!resp.ok) return [];
    return parseCSV(await resp.text());
  } catch (e) {
    return [];
  }
}

// 選手ごとに「ランクマッチ順位がthreshold位以内だった回数」を数える。
// 1人の選手が複数の期間・複数のクラスでtop100入りしていれば、その分だけ加算される
// （＝「通算で何回入賞級の順位を取ったか」を表す回数ランキング）。
// キーは正規化した名前にしておき、crCountForPlayer()側でエイリアス+正規化を通して引く。
function crTopNCounts(leaderboard, threshold) {
  const counts = {};
  leaderboard.forEach(r => {
    const rank = parseInt(r.rank, 10);
    if (!Number.isNaN(rank) && rank <= threshold) {
      const key = normalizeName(r.player_name);
      counts[key] = (counts[key] || 0) + 1;
    }
  });
  return counts;
}

// crTopNCounts()は「クラスごとの生のrank列」を見ているが、こちらは各期間について
// 7クラス分のリーダーボードを1つにmergeしてから（beyond.htmlの「全クラス合算」と同じ、
// クラスごとのエントリをそのまま合わせるだけで選手単位に集約はしない）順位を振り直し、
// その順位がthreshold位以内だった回数を数える（＝「全クラス合算で見た時に何回入賞級
// だったか」を表す回数ランキング）。1人の選手が同じ期間内で複数クラス分TOP入りしていれば、
// その分だけ複数回カウントされる（選手単位に丸めてしまうと本来カウントされるべき
// 2つ目以降のクラスの実績が消えてしまうため）。
// 表示件数を絞るbeyond.html側とは違い、ここでは母集団を絞らずに全員分の順位を振ってから数える
// （TOP100の回数を数えたいのに母集団を100人に絞ると、同着の関係で取りこぼす恐れがあるため）。
function crAllClassTopNCounts(leaderboard, threshold) {
  const counts = {};
  const byPeriod = {};
  leaderboard.forEach(r => {
    if (!byPeriod[r.period]) byPeriod[r.period] = [];
    byPeriod[r.period].push({ player_name: r.player_name, rating: parseFloat(r.rating) || 0 });
  });
  Object.values(byPeriod).forEach(entries => {
    const list = entries.slice().sort((a, b) => b.rating - a.rating);
    assignCompetitionRanks(list, x => x.rating);
    list.forEach(x => {
      if (x.rank <= threshold) {
        const key = normalizeName(x.player_name);
        counts[key] = (counts[key] || 0) + 1;
      }
    });
  });
  return counts;
}

// players.csv側の選手オブジェクトから、crTopNCounts()の結果を引く。
// NAME_ALIASESに登録があればそちらを優先し、無ければ本人の名前をそのまま
// 正規化して引く（全角/半角スペース・大文字小文字のゆれは自動で吸収される）。
function crCountForPlayer(counts, player) {
  const lookupName = NAME_ALIASES[player.player_name] || player.player_name;
  return counts[normalizeName(lookupName)] || 0;
}

function crTopNLabel(threshold) {
  return `CR順位 TOP${threshold}入り回数`;
}

function crAllClassTopNLabel(threshold) {
  return `全クラス${threshold}位以内 回数`;
}

// players.csv側の選手を「正規化した名前 → 選手オブジェクト」の辞書にしておく。
// beyond.html（svlabo_leaderboards.csvの全ユーザーリーダーボード）で、そこに載っている
// 選手がPS出場選手かどうかを判定し、該当すればplayer.htmlへのリンクにするために使う。
// NAME_ALIASESを経由するので表記ゆれ（Chappy/Chappy_ttv等）も吸収される。
function buildPlayerLookup(players) {
  const map = {};
  players.forEach(p => {
    const key = normalizeName(NAME_ALIASES[p.player_name] || p.player_name);
    map[key] = p;
  });
  return map;
}
function lookupPlayer(playerLookup, rawName) {
  return playerLookup[normalizeName(rawName)] || null;
}

// 選手ごとの「ランクマッチ最高順位（全期間・全クラス通じての最良値）」を
// data/svlabo_leaderboards.csv（全ユーザー分を一括取得したもの）から求める。
// 以前はhistory.csvのcr_best_rank_overallを見ていたが、これは手動scrape_svlabo.pyを
// 実行した選手にしか値が入らず、Atom以外ほぼ空という状態になっていた。
// svlabo_leaderboards.csvは全選手分が揃っているので、こちらを正とする。
function crBestRankForPlayer(leaderboard, player) {
  const lookupName = NAME_ALIASES[player.player_name] || player.player_name;
  const key = normalizeName(lookupName);
  let best = null;
  leaderboard.forEach(r => {
    if (normalizeName(r.player_name) !== key) return;
    const rank = parseInt(r.rank, 10);
    if (!Number.isNaN(rank) && (best === null || rank < best)) best = rank;
  });
  return best;
}

// data/battle_details.csv（svlabo.jpの「N節 試合詳細結果＆配信時間指定URL」記事から手動で
// 取り込んだ、節ごとの試合詳細。使用/未使用クラスの内訳と配信URL(タイムスタンプ付き)を持つ）
// を読み込む。無ければ空配列を返す。
async function loadBattleDetails() {
  try {
    const resp = await fetch(BATTLE_DETAILS_URL);
    if (!resp.ok) return [];
    return parseCSV(await resp.text());
  } catch (e) {
    return [];
  }
}

// そのバトルでチームが登録していたクラスの一覧（class1_pool等、"|"区切り）を、
// 実際に使ったクラス(usedName)だけ通常表示・それ以外は減光したアイコン列として描画する。
// 「対戦に使用していないクラスも載せてほしいが、わかりやすい形に」という要望に対応するため、
// 使ったクラスと使わなかったクラスを同じ並びの中で視覚的に区別する形にしている。
function classPoolHTML(poolStr, usedName, size) {
  size = size || 18;
  const classes = (poolStr || "").split("|").filter(Boolean);
  if (!classes.length) return "";
  return `<span class="class-pool">${classes.map(c => {
    const isUsed = c === usedName;
    return `<span class="${isUsed ? "used" : "unused"}" title="${escapeAttr(c)}${isUsed ? "（使用）" : "（未使用）"}">${classIconHTML(c, size)}</span>`;
  }).join("")}</span>`;
}

// match_results.csv（ps.shadowverse-wb.com由来、roundは日時文字列）と
// battle_details.csv（svlabo.jp由来、section/half/round_no/battle_no単位）は採番方式が
// 別々で共通のキーが無いため、「対戦したチームの組み合わせ + 選手名」で突き合わせる。
// 現状の投入データでは各(team1,team2)の組み合わせは節をまたいで重複しないため、この
// キーだけでも一意に特定できている（将来、同じ2チームが複数節で再度当たった場合は
// 突き合わせがあいまいになる可能性がある。その場合はround/日付も使った突き合わせに拡張が必要）。
// 見つかった場合、その選手側のクラスpool・使用クラス・配信URLを返す。見つからなければnull。
function findBattleDetail(battleDetails, teamTag, playerName, opponentTeamTag) {
  for (const b of battleDetails) {
    if (b.team1 === teamTag && b.team2 === opponentTeamTag && b.player1 === playerName) {
      return { pool: b.class1_pool, used: b.class1_used, video_url: b.video_url, section: b.section };
    }
    if (b.team2 === teamTag && b.team1 === opponentTeamTag && b.player2 === playerName) {
      return { pool: b.class2_pool, used: b.class2_used, video_url: b.video_url, section: b.section };
    }
  }
  return null;
}

// data/result.json を読み込む（手動更新される公式チーム順位。無ければnullを返す）。
async function loadResultJson() {
  try {
    const resp = await fetch(RESULT_JSON_URL);
    if (!resp.ok) return null;
    return await resp.json();
  } catch (e) {
    return null;
  }
}

// 順位付けされた配列に対して「同着」を考慮した順位を各要素の.rank に付与する。
// 例: 2位が2チーム同着なら両方rank=2、その次のチームはrank=4になる（一般的な競技の順位付け方）。
// list はソート済み（比較に使うキーが同じ値の要素は必ず連続している）前提。
function assignCompetitionRanks(list, keyFn) {
  let rank = 0, prevKey = null;
  list.forEach((item, i) => {
    const key = keyFn(item);
    if (prevKey === null || key !== prevKey) {
      rank = i + 1; // これまでに数えた要素数+1 = 同着を挟んだ正しい順位
      prevKey = key;
    }
    item.rank = rank;
  });
}

// 8チームを「現在の順位」で並べる。
// 優先順位:
//   1. data/result.json に実データがあればそれを使う（手動更新される公式の勝敗・得失差・獲得ポイント）
//   2. まだ入力されていない場合は match_results.csv から自動集計した値にフォールバックする
//      （各選手の獲得ポイント[point]をチーム単位で合算。公式の対戦カードの点数と一致する値なので
//      近似として妥当）
// まだ試合が無い場合はplayers.csv記載順のまま返す。
function computeTeamStandings(players, matches, resultJson) {
  const teams = {};
  players.forEach(p => {
    if (!teams[p.team_tag]) teams[p.team_tag] = { team_tag: p.team_tag, team_name: p.team_name, players: [], points: 0, wins: 0, losses: 0, diff: 0 };
    teams[p.team_tag].players.push(p);
  });

  const resultTeams = resultJson && Array.isArray(resultJson.teams) ? resultJson.teams : [];
  const resultHasData = resultTeams.some(t => (t.win || 0) + (t.lose || 0) > 0);

  if (resultHasData) {
    resultTeams.forEach(t => {
      const tag = RESULT_ID_TO_TAG[t.id];
      if (!tag || !teams[tag]) return;
      teams[tag].points = t.battlepoint || 0;
      teams[tag].wins = t.win || 0;
      teams[tag].losses = t.lose || 0;
      teams[tag].diff = t.diff || 0;
    });
    const list = Object.values(teams);
    list.sort((a, b) => b.points - a.points || b.diff - a.diff || b.wins - a.wins);
    // 同ポイント・同得失差・同勝数のチームは同着として同じ順位にする（公式の見せ方に合わせる。
    // 例: 2位が2チームなら両方2位、次のチームは3位ではなく4位になる）。
    assignCompetitionRanks(list, t => `${t.points}|${t.diff}|${t.wins}`);
    return { list, source: "result.json" };
  }

  // match_results.csvは「選手1人・個人戦1バトル」単位の行なので、そのままteam_tagごとに
  // win/loseを数えると「チームの試合単位の勝敗（2-0, 1-1など）」ではなく「個人戦バトルの
  // 勝敗数の合計」になってしまう（1つのチーム戦は複数バトルのベストオブなので数が水増しされる）。
  // round + 対戦カード（自チームと相手チームの組）でグルーピングして、チーム試合1つごとに
  // どちらが勝ったか（個人戦バトルを多く取った方）を判定し、そのチーム試合単位でwin/loseを数える。
  // battlepoint（points）はこれまで通り個人戦バトルの獲得数の合計（＝公式スコア表記と一致）。
  const cardMap = {}; // key: round + "|" + [tagA,tagB].sort().join("-")  -> { round, tagPoints: {tag: sum} }
  matches.forEach(m => {
    const t = teams[m.team_tag];
    if (!t) return;
    t.points += parseFloat(m.point) || 0;

    const oppTag = m.opponent_team_tag;
    if (!oppTag || oppTag === "?" || !teams[oppTag]) return; // 対戦相手が特定できない行は試合単位の勝敗集計からは除外
    const pairKey = m.round + "|" + [m.team_tag, oppTag].sort().join("-");
    if (!cardMap[pairKey]) cardMap[pairKey] = {};
    cardMap[pairKey][m.team_tag] = (cardMap[pairKey][m.team_tag] || 0) + (parseFloat(m.point) || 0);
  });

  Object.values(cardMap).forEach(tagPoints => {
    const tags = Object.keys(tagPoints);
    if (tags.length !== 2) return; // 想定外（相手不明の行が混ざっている等）はスキップ
    const [tagA, tagB] = tags;
    if (tagPoints[tagA] === tagPoints[tagB]) return; // 引き分けは想定していないのでスキップ
    const winner = tagPoints[tagA] > tagPoints[tagB] ? tagA : tagB;
    const loser = winner === tagA ? tagB : tagA;
    if (teams[winner]) teams[winner].wins++;
    if (teams[loser]) teams[loser].losses++;
    // result.json側のdiff（得失差の累計。例: 3-1で勝ったら+2）と同じ考え方で、
    // フォールバック側でも試合単位の得失差を積み上げる（以前はここが未実装で、
    // result.jsonが未入力の間はW/L DIFF列が常に0のままになっていた）。
    const diff = Math.abs(tagPoints[tagA] - tagPoints[tagB]);
    if (teams[winner]) teams[winner].diff += diff;
    if (teams[loser]) teams[loser].diff -= diff;
  });

  const list = Object.values(teams);
  const hasMatches = matches.length > 0;
  if (hasMatches) {
    list.sort((a, b) => b.points - a.points || b.diff - a.diff || b.wins - a.wins);
    assignCompetitionRanks(list, t => `${t.points}|${t.diff}|${t.wins}`);
  }
  return { list, source: hasMatches ? "match_results.csv" : "none" };
}
