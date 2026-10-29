// 選手詳細（player.html）の「配信分析」。data/streams.json（scrape_streams.py が YouTube の
// ライブアーカイブを1本ずつ取ったもの）から、配信頻度・配信時間・再生数・タイトルの傾向を出す。
// 対象は YouTube のライブアーカイブのみ（メンバー限定・非公開と Twitch は含まない）。

const STREAMS_URL = "data/streams.json";
const STREAM_PERIODS = [
  { id: "30", label: "直近30日", days: 30 },
  { id: "90", label: "直近90日", days: 90 },
  { id: "all", label: "取得した全期間", days: null },
];
const WEEKDAYS_JA = ["日", "月", "火", "水", "木", "金", "土"];

// タイトルから拾うキーワード。表示名と、タイトルに含まれるかを判定する正規表現の組。
// クラス名と、配信の種類を表す言葉（シャドバ配信でよく使われるもの）を並べている。
const STREAM_KEYWORDS = [
  ["エルフ", /エルフ/], ["ロイヤル", /ロイヤル/], ["ウィッチ", /ウィッチ/], ["ドラゴン", /ドラゴン/],
  ["ナイトメア", /ナイトメア/], ["ビショップ", /ビショップ/], ["ネメシス", /ネメシス/],
  ["ランクマッチ", /ランクマ/], ["PS関連", /PS|プレミア/], ["大会", /大会|カップ|杯|CUP|Cup/],
  ["グランプリ", /グランプリ/], ["2Pick", /2\s*pick|２\s*pick|2ピック/i], ["BEYOND", /beyond|ビヨンド/i],
  ["ミラー・同時視聴", /ミラー|同時視聴|ウォッチパーティ/], ["観戦", /観戦/],
  ["練習・研究", /練習|研究|検証/], ["新カード", /新カード|カード評価|新弾/],
  ["ルームマッチ", /ルムマ|ルームマッチ/], ["視聴者参加", /参加型|視聴者参加/], ["コラボ", /コラボ|w\/|with/i],
  ["雑談", /雑談/], ["朝", /朝活|朝/], ["深夜", /深夜/],
];

async function loadStreams() {
  try {
    const resp = await fetch(STREAMS_URL);
    if (!resp.ok) return [];
    const data = await resp.json();
    return (data.streams || []).filter(s => s.status === "ok" && s.start_at);
  } catch (e) {
    return [];
  }
}

// 日本時間に直した Date（getUTC* で日本時間の年月日・時刻・曜日が取れる）
function toJst(iso) { return new Date(new Date(iso).getTime() + 9 * 3600 * 1000); }
function jstDateKey(iso) { return toJst(iso).toISOString().slice(0, 10); }
function fmtHours(sec) { return sec == null ? "-" : `${(sec / 3600).toFixed(1)}h`; }
function fmtHM(sec) {
  if (sec == null) return "-";
  const total = Math.round(sec / 60); // 先に分へ丸める（「1時間60分」にならないように）
  const h = Math.floor(total / 60), m = total % 60;
  return h ? `${h}時間${String(m).padStart(2, "0")}分` : `${m}分`;
}
// キーワード判定用のタイトル。多くの配信タイトルに定型で入る「Shadowverse: Worlds Beyond」を除く
// （残しておくと全配信が「BEYOND」に数えられてしまう）。
function keywordTitle(title) { return String(title || "").replace(/Shadowverse\s*:?\s*Worlds\s*Beyond|Worlds\s*Beyond/gi, ""); }
function avg(list) { return list.length ? list.reduce((a, b) => a + b, 0) / list.length : null; }

function streamsInPeriod(all, periodId) {
  const p = STREAM_PERIODS.find(x => x.id === periodId);
  if (!p.days) return all;
  const since = Date.now() - p.days * 86400 * 1000;
  return all.filter(s => new Date(s.start_at).getTime() >= since);
}

function streamSummaryHTML(list, periodId, coverageStart) {
  const days = new Set(list.map(s => jstDateKey(s.start_at))).size;
  const durations = list.map(s => s.duration_sec).filter(v => v != null);
  const views = list.map(s => s.view_count).filter(v => v != null);
  const total = durations.reduce((a, b) => a + b, 0);
  const top = list.filter(s => s.view_count != null).sort((a, b) => b.view_count - a.view_count)[0];
  const period = STREAM_PERIODS.find(x => x.id === periodId);
  // 「週あたり」は期間の日数で割る。ただし取得できている最古の配信より前は数えない
  // （データの無い期間まで割る日数に入れると、回数が実際より少なく見えるため）。
  const coveredDays = (Date.now() - new Date(coverageStart).getTime()) / 86400000;
  const spanDays = period.days ? Math.min(period.days, coveredDays) : coveredDays;
  const perWeek = spanDays > 0 ? (list.length / spanDays * 7) : null;
  const tile = (label, value, sub) => `
    <div class="quick-stat"><div class="label">${label}</div><div class="value">${value}</div>${sub ? `<div class="stream-tile-sub">${sub}</div>` : ""}</div>`;
  return `<div class="quick-stats stream-tiles">
    ${tile("配信回数", `${list.length}回`, perWeek != null ? `週あたり ${perWeek.toFixed(1)}回` : "")}
    ${tile("配信した日数", `${days}日`, "")}
    ${tile("合計配信時間", fmtHours(total), "")}
    ${tile("平均配信時間", fmtHM(avg(durations)), "")}
    ${tile("平均再生数", views.length ? fmtNum(Math.round(avg(views))) : "-", "")}
    ${tile("最多再生", top ? fmtNum(top.view_count) : "-", top ? `<a href="https://www.youtube.com/watch?v=${encodeURIComponent(top.video_id)}" target="_blank" rel="noopener">${escapeAttr(top.title.slice(0, 24))}${top.title.length > 24 ? "…" : ""}</a>` : "")}
  </div>`;
}

// 曜日×時間帯（日本時間）ごとに、その時間に配信していた回数。色の濃さで多さを表す。
// 1本の配信を開始から終了まで1時間刻みでたどり、少しでも重なった時間帯をそれぞれ1回と数える
// （例: 21:30〜翌1:10 の配信は、その曜日の21・22・23時台と、翌日の0・1時台に1回ずつ）。
const HOUR_MS = 3600 * 1000;
function streamHeatmapHTML(list) {
  const grid = Array.from({ length: 7 }, () => Array(24).fill(0));
  list.forEach(s => {
    const start = new Date(s.start_at).getTime();
    let end = s.end_at ? new Date(s.end_at).getTime() : start + (s.duration_sec || 0) * 1000;
    end = Math.min(Math.max(end, start + 1), start + 48 * HOUR_MS); // 異常に長い値でも48時間で打ち切る
    for (let t = Math.floor(start / HOUR_MS) * HOUR_MS; t < end; t += HOUR_MS) {
      const d = new Date(t + 9 * HOUR_MS); // 日本時間
      grid[d.getUTCDay()][d.getUTCHours()]++;
    }
  });
  const max = Math.max(1, ...grid.flat());
  const order = [1, 2, 3, 4, 5, 6, 0]; // 月曜始まり
  const head = `<div class="stream-heat__corner"></div>` +
    Array.from({ length: 24 }, (_, h) => `<div class="stream-heat__hour">${h % 3 === 0 ? h : ""}</div>`).join("");
  const rows = order.map(wd => `<div class="stream-heat__wd">${WEEKDAYS_JA[wd]}</div>` +
    grid[wd].map((n, h) => `<div class="stream-heat__cell" style="--a:${n ? (0.15 + 0.85 * n / max).toFixed(2) : 0}"
      title="${WEEKDAYS_JA[wd]}曜 ${h}時台に配信していた回数: ${n}回"></div>`).join("")).join("");
  return `<div class="stream-heat">${head}${rows}</div>
    <div class="stream-note">配信の開始から終了までにかかった時間帯（日本時間）を、1本ごとに1回と数えています。濃いほど多い。</div>`;
}

// タイトルのキーワードごとの回数と平均再生数（期間内の全体平均との差も出す）
function streamKeywordsHTML(list) {
  const allViews = avg(list.map(s => s.view_count).filter(v => v != null));
  const rows = STREAM_KEYWORDS.map(([label, re]) => {
    const hit = list.filter(s => re.test(keywordTitle(s.title)));
    const v = avg(hit.map(s => s.view_count).filter(x => x != null));
    return { label, count: hit.length, avgViews: v };
  }).filter(r => r.count >= 2).sort((a, b) => b.count - a.count);
  if (!rows.length) return `<div class="empty-note">2回以上出てくるキーワードがありません</div>`;
  return `<table class="rank-table stream-kw">
    <thead><tr><th>キーワード</th><th class="num">配信回数</th><th class="num">平均再生数</th><th class="num">全体平均との差</th></tr></thead>
    <tbody>${rows.map(r => {
      const diff = (r.avgViews != null && allViews) ? (r.avgViews / allViews - 1) * 100 : null;
      const cls = diff == null ? "" : diff > 0 ? "change-up" : diff < 0 ? "change-down" : "change-flat";
      return `<tr><td>${r.label}</td><td class="num">${r.count}</td>
        <td class="num">${r.avgViews != null ? fmtNum(Math.round(r.avgViews)) : "-"}</td>
        <td class="num"><span class="${cls}">${diff == null ? "-" : `${diff > 0 ? "+" : ""}${diff.toFixed(0)}%`}</span></td></tr>`;
    }).join("")}</tbody></table>
    <div class="stream-note">タイトルに含まれる言葉で分類しています。1本の配信が複数のキーワードに数えられることがあります。</div>`;
}

let streamListSort = { key: "start_at", desc: true };
let streamListAll = false;

function streamListHTML(list) {
  const k = streamListSort.key;
  const sorted = list.slice().sort((a, b) => {
    const va = a[k] ?? -1, vb = b[k] ?? -1;
    return (va < vb ? -1 : va > vb ? 1 : 0) * (streamListSort.desc ? -1 : 1);
  });
  const shown = streamListAll ? sorted : sorted.slice(0, 20);
  const th = (key, label, cls) => `<th class="sortable ${cls || ""} ${k === key ? "active" : ""}" data-sort="${key}">${label}<span class="sort-arrow">${k === key ? (streamListSort.desc ? "▼" : "▲") : "▼"}</span></th>`;
  return `<div class="table-scroll"><table class="rank-table stream-list">
    <thead><tr>${th("start_at", "日時")}<th>タイトル</th>${th("duration_sec", "配信時間", "num")}${th("view_count", "再生数", "num")}</tr></thead>
    <tbody>${shown.map(s => {
      const d = toJst(s.start_at);
      const date = `${d.getUTCFullYear()}/${d.getUTCMonth() + 1}/${d.getUTCDate()}(${WEEKDAYS_JA[d.getUTCDay()]}) ${String(d.getUTCHours()).padStart(2, "0")}:${String(d.getUTCMinutes()).padStart(2, "0")}`;
      return `<tr><td class="stream-list__date">${date}</td>
        <td><a href="https://www.youtube.com/watch?v=${encodeURIComponent(s.video_id)}" target="_blank" rel="noopener">${escapeAttr(s.title)}</a></td>
        <td class="num">${fmtHM(s.duration_sec)}</td><td class="num">${s.view_count != null ? fmtNum(s.view_count) : "-"}</td></tr>`;
    }).join("")}</tbody></table></div>
    ${sorted.length > 20 ? `<button type="button" class="team-select-btn stream-more" id="streamMore">${streamListAll ? "20件だけ表示" : `すべて表示（${sorted.length}件）`}</button>` : ""}`;
}

let streamCharts = [];
function drawStreamCharts(list, color) {
  streamCharts.forEach(c => c.destroy());
  streamCharts = [];
  if (typeof Chart === "undefined" || !list.length) return;
  const asc = list.slice().sort((a, b) => a.start_at < b.start_at ? -1 : 1);
  const labels = asc.map(s => { const d = toJst(s.start_at); return `${d.getUTCMonth() + 1}/${d.getUTCDate()}`; });
  const axis = { ticks: { color: "#6b7280" }, grid: { color: "#f0f1f3" } };
  // 配信ごとの再生数（棒）と配信時間（折れ線、右軸）
  streamCharts.push(new Chart(document.getElementById("streamViewsChart"), {
    data: { labels, datasets: [
      { type: "bar", label: "再生数", data: asc.map(s => s.view_count), backgroundColor: color, yAxisID: "y" },
      { type: "line", label: "配信時間 (h)", data: asc.map(s => s.duration_sec != null ? +(s.duration_sec / 3600).toFixed(2) : null),
        borderColor: "#6b7280", backgroundColor: "#6b7280", pointRadius: 2, tension: 0.2, yAxisID: "y1" },
    ] },
    options: {
      responsive: true, interaction: { mode: "index", intersect: false },
      plugins: { legend: { labels: { color: "#6b7280", boxWidth: 12 } },
        tooltip: { callbacks: { title: items => asc[items[0].dataIndex].title } } },
      scales: { x: axis, y: { ...axis, position: "left", title: { display: true, text: "再生数", color: "#6b7280" } },
        y1: { ...axis, position: "right", grid: { drawOnChartArea: false }, title: { display: true, text: "配信時間 (h)", color: "#6b7280" } } },
    },
  }));
  // 週ごとの配信時間と配信回数（月曜始まり、日本時間）
  const weeks = new Map();
  asc.forEach(s => {
    const d = toJst(s.start_at);
    const monday = new Date(Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate() - ((d.getUTCDay() + 6) % 7)));
    const key = monday.toISOString().slice(0, 10);
    const w = weeks.get(key) || { hours: 0, count: 0 };
    w.hours += (s.duration_sec || 0) / 3600; w.count++;
    weeks.set(key, w);
  });
  // 配信の無かった週も0として並べる（間が空いたことが見えるように）
  const keys = [...weeks.keys()].sort();
  const allWeeks = [];
  if (keys.length) {
    for (let t = new Date(keys[0] + "T00:00:00Z"); t <= new Date(keys[keys.length - 1] + "T00:00:00Z"); t = new Date(t.getTime() + 7 * 86400000)) {
      allWeeks.push(t.toISOString().slice(0, 10));
    }
  }
  streamCharts.push(new Chart(document.getElementById("streamWeeklyChart"), {
    type: "bar",
    data: { labels: allWeeks.map(k => `${Number(k.slice(5, 7))}/${Number(k.slice(8, 10))}週`),
      datasets: [{ label: "配信時間 (h)", data: allWeeks.map(k => +((weeks.get(k) || { hours: 0 }).hours).toFixed(1)), backgroundColor: color }] },
    options: {
      responsive: true,
      plugins: { legend: { display: false },
        tooltip: { callbacks: { afterLabel: item => `配信回数: ${(weeks.get(allWeeks[item.dataIndex]) || { count: 0 }).count}回` } } },
      scales: { x: axis, y: { ...axis, title: { display: true, text: "配信時間 (h)", color: "#6b7280" } } },
    },
  }));
}

function renderStreamAnalysis(container, player, allStreams, color) {
  const mine = allStreams.filter(s => s.player_name === player.player_name);
  if (!player.youtube_url) {
    container.innerHTML = `<h2 class="stream-title">配信分析</h2><div class="empty-note">YouTube チャンネルが登録されていないため、配信分析はありません</div>`;
    return;
  }
  if (!mine.length) {
    container.innerHTML = `<h2 class="stream-title">配信分析</h2><div class="empty-note">配信のデータはまだありません</div>`;
    return;
  }
  const oldest = mine.reduce((a, s) => s.start_at < a ? s.start_at : a, mine[0].start_at);
  container.innerHTML = `
    <h2 class="stream-title">配信分析</h2>
    <div class="control-row">
      <div class="control-group">
        <label for="streamPeriod">期間</label>
        <select id="streamPeriod">${STREAM_PERIODS.map(p => `<option value="${p.id}">${p.label}</option>`).join("")}</select>
      </div>
      <div class="stream-note">YouTube のライブアーカイブが対象です（メンバー限定・Twitch は含みません）。${jstDateKey(oldest).replace(/-/g, "/")} 以降の${mine.length}本を取得済み。</div>
    </div>
    <div id="streamBody"></div>`;
  const sel = container.querySelector("#streamPeriod");
  sel.value = "90";

  function draw() {
    const list = streamsInPeriod(mine, sel.value);
    const body = container.querySelector("#streamBody");
    if (!list.length) {
      streamCharts.forEach(c => c.destroy()); streamCharts = [];
      body.innerHTML = `<div class="empty-note">この期間の配信はありません</div>`;
      return;
    }
    body.innerHTML = `
      ${streamSummaryHTML(list, sel.value, oldest)}
      <h3 class="stream-sub">配信ごとの再生数と配信時間</h3>
      <div class="chart-box"><canvas id="streamViewsChart"></canvas></div>
      <h3 class="stream-sub">週ごとの配信時間</h3>
      <div class="chart-box"><canvas id="streamWeeklyChart"></canvas></div>
      <h3 class="stream-sub">配信している曜日と時間帯</h3>
      <div class="chart-box">${streamHeatmapHTML(list)}</div>
      <h3 class="stream-sub">タイトルの傾向</h3>
      ${streamKeywordsHTML(list)}
      <h3 class="stream-sub">配信一覧</h3>
      <div id="streamList">${streamListHTML(list)}</div>`;
    drawStreamCharts(list, color);
    bindList(list);
  }
  function bindList(list) {
    const wrap = container.querySelector("#streamList");
    wrap.querySelectorAll("th[data-sort]").forEach(th => th.addEventListener("click", () => {
      const key = th.dataset.sort;
      streamListSort = { key, desc: streamListSort.key === key ? !streamListSort.desc : true };
      wrap.innerHTML = streamListHTML(list); bindList(list);
    }));
    const more = wrap.querySelector("#streamMore");
    if (more) more.addEventListener("click", () => { streamListAll = !streamListAll; wrap.innerHTML = streamListHTML(list); bindList(list); });
  }
  sel.addEventListener("change", draw);
  draw();
}
