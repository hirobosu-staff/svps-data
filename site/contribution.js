// 貢献度（contribution.html のグラフと、player.html の「貢献度」欄）。
// 値は公開時に scripts/build_contribution.py が毎日の取得データから計算して data/contribution.json に書く
// （2026-11-17 から。それまではこのファイルに第10節終了時点の値を直接書いていた）。
// 配点・表彰・大会結果・note・WGP予選は data/contribution_manual.json の手入力分。
(function () {
  const DATA_URL = "data/contribution.json";
  let DATA = [], K = {}, W = {}, META = {};
  let loading = null;
  function load() {
    if (!loading) {
      loading = fetch(DATA_URL).then(r => {
        if (!r.ok) throw new Error(`${DATA_URL}: HTTP ${r.status}`);
        return r.json();
      }).then(j => { DATA = j.players; K = j.K; W = j.W; META = j; });
    }
    return loading;
  }
  // "2026-11-04" を「11月4日」にする
  const md = iso => iso ? `${Number(iso.slice(5, 7))}月${Number(iso.slice(8, 10))}日` : "";
  const WQKEY = { win: "Q1", second: "Q2", top4: "Q4", top8: "Q8", top16: "Q16", w3: "Q3" };
  const WQ_LABEL = { win: "優勝", second: "準優勝", top4: "ベスト4", top8: "ベスト8", top16: "決勝トーナメント進出", w3: "予選3勝" };
  const TOUR_LABEL = { win: "優勝", second: "準優勝", third: "3位", top8: "ベスト8" };
  const ABBR = { "Crazy Raccoon": "CR", "ZETA DIVISION": "ZETA", "DetonatioN FocusMe": "DFM", "VARREL": "VARREL", "MURASH GAMING": "MRG", "REJECT": "REJECT", "RIDDLE ORDER": "RIDDLE", "レバンガ北海道": "LVH" };
  const COL = { comp: "#2A78D6", send: "#EB6834", note: "#8B5CC9", award: "#1BAF7A", bonus: "#0D366B", wgpq: "#D19A12", lad: "#D55181", muted: "#C9C8C2", ink: "#1F1E1D", sub: "#6B6A66" };
  const LEGEND = [["競技", COL.comp, 250], ["配信", COL.send, 304], ["note", COL.note, 358], ["表彰", COL.award, 414], ["大会加点", COL.bonus, 468], ["WGP予選", COL.wgpq, 546], ["ランクマッチ", COL.lad, 630]];

  const fmt = (v, d = 0) => Number(v).toLocaleString("ja-JP", { minimumFractionDigits: d, maximumFractionDigits: d });
  // 小数第1位への丸め（偶数丸め。集計時と同じ丸め方）
  const r1 = v => { const x = v * 10, f = Math.floor(x), d = x - f; if (Math.abs(d - 0.5) < 1e-9) return (f % 2 === 0 ? f : f + 1) / 10; return Math.round(x) / 10; };
  const lg = (v, max) => v < 1000 ? 0 : Math.log10(v / 1000) / Math.log10(max / 1000);
  const esc = s => String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  const playerHref = name => `player.html?name=${encodeURIComponent(name)}#contribution`;

  function sendParts(r) {
    if (r.s === null) return null;
    if (r.est) { const t = r.s / 35 * (W.LT + W.LM + W.V); return { live: t, video: 0, total: t }; }
    const live = lg(r.ls, K.tmax) * W.LT + lg(r.lm, K.mmax) * W.LM;
    const video = lg(r.up, K.umax) * W.V;
    return { live, video, total: live + video };
  }
  function parts(r) {
    const comp = r.c * W.C / 45;
    const award = r.pr * W.P + r.bb * W.B;
    const note = r.nt / 3 * W.N;
    const bonus = r.tour.reduce((s, t) => s + (W[t] || 0), 0);
    const wq = r.wq ? (W[WQKEY[r.wq]] || 0) : 0;
    const lad = r1(W.L * r.lad / K.ladmax);
    const sp = sendParts(r);
    let send = 0, conv = 0, base;
    if (sp === null) {
      const denom = W.C + W.N + W.P + W.B;
      base = (comp + note + award) * (W.C + W.LT + W.LM + W.V + W.N + W.P + W.B) / denom;
      conv = base - comp - note - award;
    } else {
      send = sp.total;
      base = comp + send + note + award;
    }
    return { comp, send, note, award, bonus, wq, lad, conv, sp, total: r1(r1(base) + bonus + wq + lad) };
  }
  let cache = null;
  function ranking() {
    if (cache) return cache;
    const rows = DATA.map(r => ({ r, ...parts(r) }));
    rows.sort((a, b) => b.total - a.total || DATA.indexOf(a.r) - DATA.indexOf(b.r));
    const pos = new Map(); rows.forEach((x, i) => pos.set(x.r.p, i + 1));
    cache = { rows, pos };
    return cache;
  }

  function rankSVG(rows) {
    const x0 = 250, w = 440, y0 = 72, rh = 22, sx = v => Math.max(v, 0) * w / 100;
    const H = y0 + rows.length * rh + 24;
    let s = `<svg viewBox="0 0 760 ${H}" role="img" aria-label="全${rows.length}選手の貢献度ランキング" font-size="12">`;
    LEGEND.forEach(([t, c, x]) => { s += `<rect x="${x}" y="20" width="12" height="12" fill="${c}"/><text x="${x + 18}" y="30" fill="${COL.sub}">${t}</text>`; });
    s += `<text x="70" y="58" fill="${COL.sub}" font-size="11">選手</text><text x="188" y="58" fill="${COL.sub}" font-size="11">チーム</text>`;
    rows.forEach((x, i) => {
      const y = y0 + i * rh, r = x.r; let cx = x0;
      const seg = (v, c, extra = "") => { const ww = sx(v); const out = ww > 0 ? `<rect x="${cx.toFixed(2)}" y="${y}" width="${ww.toFixed(2)}" height="14" fill="${c}" ${extra}/>` : ""; cx += ww; return out; };
      s += `<text x="58" y="${y + 11}" text-anchor="end" fill="${COL.sub}">${i + 1}</text>`;
      s += `<a href="${playerHref(r.p)}"><text x="70" y="${y + 11}" fill="${COL.ink}">${esc(r.p)}</text></a>`;
      s += `<text x="188" y="${y + 11}" fill="${COL.sub}" font-size="11">${ABBR[r.t] || esc(r.t)}</text>`;
      s += seg(x.comp, COL.comp);
      s += seg(x.send, COL.send, r.est ? 'fill-opacity="0.45"' : "");
      if (x.conv > 0) { const ww = sx(x.conv); s += `<rect x="${cx.toFixed(2)}" y="${y + 0.5}" width="${ww.toFixed(2)}" height="13" fill="none" stroke="${COL.muted}" stroke-dasharray="3 2"/>`; cx += ww; }
      s += seg(x.note, COL.note); s += seg(x.award, COL.award); s += seg(x.bonus, COL.bonus); s += seg(x.wq || 0, COL.wgpq); s += seg(x.lad, COL.lad);
      const end = x0 + sx(x.total);
      s += `<text x="${(end + 6).toFixed(2)}" y="${y + 11}" fill="${COL.ink}">${x.total.toFixed(1)}${r.s === null ? "（換算）" : ""}</text>`;
    });
    return s + `</svg>`;
  }
  function teamSVG(rows) {
    const names = [...new Set(DATA.map(r => r.t))];
    const teams = names.map(t => { const v = rows.filter(x => x.r.t === t); return { t, n: v.length, avg: v.reduce((a, x) => a + x.total, 0) / v.length }; }).sort((a, b) => b.avg - a.avg);
    const all = rows.reduce((a, x) => a + x.total, 0) / rows.length;
    const x0 = 230, w = 440, y0 = 100, rh = 34, sx = v => v / 100 * w;
    let s = `<svg viewBox="0 0 760 396" role="img" aria-label="チーム別の貢献度の平均" font-size="13">`;
    s += `<text x="40" y="32" font-size="17" fill="${COL.ink}">チーム平均の貢献度は ${esc(teams[0].t)} が最高</text>`;
    s += `<text x="40" y="56" fill="${COL.sub}">所属選手の合計点の平均。${esc(META.progress)}終了時点</text>`;
    s += `<text x="40" y="78" fill="${COL.sub}" font-size="12">全選手の平均は ${all.toFixed(1)} 点</text>`;
    teams.forEach((t, i) => {
      const y = y0 + i * rh;
      s += `<text x="40" y="${y + 15}" fill="${COL.ink}">${esc(t.t)}</text><text x="${x0 - 12}" y="${y + 15}" text-anchor="end" fill="${COL.sub}" font-size="11">${t.n}名</text>`;
      s += `<rect x="${x0}" y="${y}" width="${sx(t.avg).toFixed(2)}" height="20" fill="${i === 0 ? COL.comp : COL.muted}"/>`;
      s += `<text x="${(x0 + sx(t.avg) + 8).toFixed(2)}" y="${y + 15}" fill="${COL.ink}">${t.avg.toFixed(1)}</text>`;
    });
    return s + `</svg>`;
  }

  async function renderPage(el) {
    try { await load(); } catch (err) { el.innerHTML = loadErrorHTML(err); return; }
    const { rows } = ranking();
    el.innerHTML = `
      <h2 class="contrib-title">貢献度ランキング</h2>
      <div class="contrib-chart">${rankSVG(rows)}</div>
      <p class="contrib-note">チーム名は略称です。CRはCrazy Raccoon、ZETAはZETA DIVISION、DFMはDetonatioN FocusMe、MRGはMURASH GAMING、RIDDLEはRIDDLE ORDER、LVHはレバンガ北海道です。選手名を押すと、その選手のページで点数の計算内訳を確認できます。${esc(META.progress)}終了時点の成績と${md(META.live_to)}までの配信データで、毎日自動で計算し直しています。表彰・大会結果・noteは手入力です。</p>
      <h2 class="contrib-title">チーム別の貢献度</h2>
      <div class="contrib-chart">${teamSVG(rows)}</div>`;
  }

  const SRC = {
    comp: () => [`Premier Series 公式サイトの試合結果（${META.progress}終了時点。SVPS選手データの通算成績）`, "rounds.html"],
    send: () => [`SVPS選手データ（YouTube Data APIで取得した配信ごとの再生数、${md(META.live_to)}更新）`, "streams.html"],
    uploads: () => [`SVPS選手データ（YouTube Data APIで取得した投稿動画の再生数、${md(META.uploads_updated)}更新）`, "index.html"],
    uploadsRef: ["shadowverse-reference.com の投稿動画の再生回数（11月4日時点。取得元の更新停止のため固定）", "https://shadowverse-reference.com/"],
    repo: ["SVPS選手データの公開リポジトリ（data/streams.json、data/uploads.json、data/contribution_manual.json）", "https://github.com/hirobosu-staff/svps-data"],
    watch: ["SVPS選手データ（shadowverse-reference.comから取得した視聴時間、11月4日更新）", "index.html"],
    award1: ["Shadowverse Vision アワード", "https://shadowverse-vision.com/awards"],
    award2: ["Premier Series 公式サイト 第2回アワード表彰結果", "https://ps.shadowverse-wb.com/26-27/news/369/"],
    noteTag: ["noteの「#シャドバPS」タグ記事一覧", "https://note.com/hashtag/%E3%82%B7%E3%83%A3%E3%83%89%E3%83%90PS"],
    ladder: ["SVPS選手データ（svlabo.jpのランクマッチ上位100名の記録）", "beyond.html"],
    rating: ["Shadowverse Vision ゲーム内レート", "https://shadowverse-vision.com/rating"],
    wq1: ["Premier Series 公式サイト WGP Qualifier 2026 大会結果のお知らせ（決勝トーナメント表）", "https://ps.shadowverse-wb.com/26-27/news/381/"],
    wq2: ["Premier Series 公式サイト WGP Qualifier 2026 開催のお知らせ（大会形式）", "https://ps.shadowverse-wb.com/26-27/news/375/"],
    wq3: ["Premier Series 公式X（11月14日 スイスドロー各回戦の結果画像）", "https://x.com/shadowversePS"],
    wq4: ["シャドラボ Premier Series WGP Qualifier 2026 結果＆デッキ分布", "https://svlabo.jp/blog-entry-2027.html"]
  };
  const link = s => /^https?:/.test(s[1]) ? `<a href="${s[1]}" target="_blank" rel="noopener">${esc(s[0])}</a>` : `<a href="${s[1]}">${esc(s[0])}</a>`;

  // player.html の「貢献度」欄。該当する選手がいなければ何も表示しない。
  async function renderPlayer(el, name) {
    try { await load(); } catch (err) { el.innerHTML = ""; return; }
    const r = DATA.find(d => d.p === name);
    if (!r) { el.innerHTML = ""; return; }
    const { pos } = ranking();
    const x = parts(r);
    const rows = [];
    const raw = r.w + r.l === 0 ? 0 : 3 * r.w + 10 * (r.w + 2.5) / (r.w + r.l + 5);
    rows.push(`<tr><td class="item">競技</td><td>選手戦（バトル1〜3）${r.w}勝${r.l}敗</td><td class="f">${
      r.w + r.l === 0 ? "出場なしのため0点" :
      `素点 = 3 × ${r.w} ＋ 10 × (${r.w} ＋ 2.5) ÷ (${r.w} ＋ ${r.l} ＋ 5) = ${fmt(raw, 2)}<br>点数 = ${fmt(raw, 2)} ÷ ${K.cmax}（全選手の最高素点） × ${W.C} = ${fmt(x.comp, 2)}`}</td><td class="num">${fmt(x.comp, 2)}</td></tr>`);
    if (r.s === null) {
      rows.push(`<tr><td class="item">配信</td><td>主な配信先がBilibiliのため、再生数を取得できません</td><td class="f">配信は0点とせず、それ以外の項目の合計を全体の満点に換算します。<br>換算後 = (競技 ＋ note ＋ 表彰) × (${W.C} ＋ ${W.LT} ＋ ${W.LM} ＋ ${W.V} ＋ ${W.N} ＋ ${W.P} ＋ ${W.B}) ÷ (${W.C} ＋ ${W.N} ＋ ${W.P} ＋ ${W.B})<br>換算による上乗せ分 = ${fmt(x.conv, 2)}</td><td class="num">${fmt(x.conv, 2)}</td></tr>`);
    } else if (r.est) {
      rows.push(`<tr><td class="item">配信</td><td>Twitchのみで配信しているため、YouTubeの再生数がありません。配信先を問わない視聴時間はシーズン中${fmt(r.wt)}時間です。</td><td class="f">再生数を取得できた${K.n}名で、視聴時間と配信点（35点満点）の関係を求めた式に当てはめています。<br>推計値 = −${fmt(-K.a, 2)} ＋ ${fmt(K.b, 3)} × log10(${fmt(r.wt)}) = ${fmt(r.s, 1)}（35点満点）<br>点数 = ${fmt(r.s, 1)} ÷ 35 × (${W.LT} ＋ ${W.LM} ＋ ${W.V}) = ${fmt(x.send, 2)}</td><td class="num">${fmt(x.send, 2)}</td></tr>`);
    } else {
      const a1 = W.LT * lg(r.ls, K.tmax), a2 = W.LM * lg(r.lm, K.mmax);
      rows.push(`<tr><td class="item">配信</td><td colspan="2">YouTubeの再生数を3つの指標に分け、それぞれ全選手の最高値を満点として対数で比べます。1,000回未満は0点です。</td><td></td></tr>`);
      rows.push(`<tr><td class="item sub">ライブ合計</td><td>${md(META.live_from)}〜${md(META.live_to)}のライブ配信${r.ln}本、合計${fmt(r.ls)}回</td><td class="f">${W.LT} × log10(${fmt(r.ls)} ÷ 1,000) ÷ log10(${fmt(K.tmax)} ÷ 1,000) = ${fmt(a1, 2)}</td><td class="num">${fmt(a1, 2)}</td></tr>`);
      rows.push(`<tr><td class="item sub">1本あたり</td><td>同期間の1本あたり再生数の中央値 ${fmt(r.lm)}回</td><td class="f">${W.LM} × log10(${fmt(r.lm)} ÷ 1,000) ÷ log10(${fmt(K.mmax)} ÷ 1,000) = ${fmt(a2, 2)}</td><td class="num">${fmt(a2, 2)}</td></tr>`);
      rows.push(`<tr><td class="item sub">投稿動画</td><td>${r.up_src === "youtube" ? `レギュラーシーズン中（${md(META.uploads_since)}〜）の投稿動画 合計${fmt(r.up)}回` : `レギュラーシーズン中の投稿動画 合計${fmt(r.up)}回（11月4日時点の値）`}</td><td class="f">${W.V} × log10(${fmt(r.up)} ÷ 1,000) ÷ log10(${fmt(K.umax)} ÷ 1,000) = ${fmt(x.sp.video, 2)}</td><td class="num">${fmt(x.sp.video, 2)}</td></tr>`);
    }
    rows.push(`<tr><td class="item">note</td><td>${r.narts.length ? `7月以降の記事${r.narts.length}本<br>${r.narts.map(a => `<a href="${a[2]}" target="_blank" rel="noopener">${esc(a[0])}</a>（${esc(a[1])}）`).join("<br>")}` : "7月以降のnote記事は確認できませんでした"}</td><td class="f">${r.nt ? `評価 ${r.nt}点（3点満点）を配点に合わせて換算<br>${r.nt} ÷ 3 × ${W.N} = ${fmt(x.note, 2)}` : "0点"}</td><td class="num">${fmt(x.note, 2)}</td></tr>`);
    rows.push(`<tr><td class="item">表彰</td><td>${r.aw.length ? r.aw.map(a => `${esc(a[0])}（${esc(a[1])}）`).join("<br>") : "受賞なし"}</td><td class="f">${r.aw.length ? r.aw.map(a => `${esc(a[0])} ${a[2] === "P" ? W.P : W.B}点`).join("<br>") : "0点"}</td><td class="num">${fmt(x.award, 2)}</td></tr>`);
    rows.push(`<tr><td class="item">大会加点</td><td>${r.tr.length ? r.tr.map(t => `${esc(t[0])} ${esc(t[1])}`).join("<br>") : "7月以降の公式大会で上位入賞の記録なし"}</td><td class="f">${r.tr.length ? r.tr.map(t => `${TOUR_LABEL[t[2]]} ${W[t[2]]}点`).join("<br>") : "0点"}</td><td class="num">${fmt(x.bonus, 2)}</td></tr>`);
    const wqDesc = !r.wqs ? `出場なし（${esc(r.p)}選手はWGP 2026の出場権を獲得済み）`
      : `予選スイスドロー ${r.wqs}` + (r.wq && r.wq !== "w3" ? `、決勝トーナメント ${WQ_LABEL[r.wq]}（${esc(r.wqt)}）` : (r.wq === "w3" ? "、決勝トーナメント進出ならず" : "、3敗でドロップ"));
    const wqCalc = r.wq ? `${WQ_LABEL[r.wq]} ${W[WQKEY[r.wq]]}点` : `0点（決勝トーナメント進出 ${W.Q16}点、予選3勝 ${W.Q3}点に届かず）`;
    rows.push(`<tr><td class="item">WGP予選</td><td>${wqDesc}</td><td class="f">${r.wqs ? wqCalc : "0点"}</td><td class="num">${fmt(x.wq, 2)}</td></tr>`);
    rows.push(`<tr><td class="item">ランクマッチ補正</td><td>7月以降（${META.ladder_periods.map(esc).join("・")}）にクラス別トップ100へ入った回数 ${r.lad}回</td><td class="f">${W.L} × ${r.lad} ÷ ${K.ladmax}（最多回数） = ${fmt(x.lad, 1)}</td><td class="num">${fmt(x.lad, 1)}</td></tr>`);
    rows.push(`<tr class="total"><td>合計</td><td colspan="2">競技・配信・note・表彰の合計を小数第1位で丸め、大会加点、WGP予選、ランクマッチ補正を足しています。</td><td class="num">${x.total.toFixed(1)}</td></tr>`);

    const ladderRows = r.ld.length ? r.ld.map(e => `<tr><td>${esc(e[0])}</td><td>${esc(e[1])}</td><td class="num">${e[2]}位</td><td class="num">${e[3]}</td></tr>`).join("") : `<tr><td colspan="4">記録なし</td></tr>`;
    const srcs = [SRC.comp()];
    if (r.slug) srcs.push(["Shadowverse Vision 選手ページ", `https://shadowverse-vision.com/players/${r.slug}`]);
    if (r.est) srcs.push(SRC.watch, SRC.repo);
    else if (r.s !== null) srcs.push(SRC.send(), r.up_src === "youtube" ? SRC.uploads() : SRC.uploadsRef, SRC.repo);
    if (r.nacc) srcs.push([`${r.p}選手のnote`, r.nacc]);
    srcs.push(SRC.noteTag);
    if (r.aw.length) srcs.push(SRC.award1, SRC.award2);
    r.tr.forEach(t => srcs.push([t[0] + "の結果", t[3]]));
    if (r.wqs) srcs.push(SRC.wq1, SRC.wq2, SRC.wq3, SRC.wq4);
    srcs.push(SRC.ladder, SRC.rating);
    const uniq = [...new Map(srcs.map(s => [s[1] + s[0], s])).values()];

    el.innerHTML = `
      <h2 class="contrib-title">貢献度</h2>
      <div class="quick-stats">
        <div class="quick-stat">
          <div class="label">貢献度（${esc(META.progress)}終了時点）</div>
          <div class="value">${x.total.toFixed(1)}点</div>
          <div class="contrib-rank">${DATA.length}名中${pos.get(r.p)}位</div>
          <a href="contribution.html" style="font-size:12px;">ランキングを見る</a>
        </div>
      </div>
      <h3 class="contrib-sub">点数の計算</h3>
      <div class="contrib-scroll"><table class="rank-table contrib-calc"><thead><tr><th>項目</th><th>元のデータ</th><th>計算</th><th class="num">点数</th></tr></thead><tbody>${rows.join("")}</tbody></table></div>
      <h3 class="contrib-sub">ランクマッチの記録</h3>
      <div class="contrib-scroll"><table class="rank-table contrib-ladder"><thead><tr><th>期間</th><th>クラス</th><th class="num">最高順位</th><th class="num">レート</th></tr></thead><tbody>${ladderRows}</tbody></table></div>
      <h3 class="contrib-sub">データの出典</h3>
      <ul class="contrib-src">${uniq.map(s => `<li>${link(s)}</li>`).join("")}</ul>
      ${noteNote()}`;
  }

  function noteNote() {
    const scored = DATA.filter(d => d.nt > 0).sort((a, b) => b.nt - a.nt);
    if (!scored.length) return "";
    return `<p class="contrib-note">noteの点数は、記事数とスキ数をもとにした評価値（${scored.map(d => `${esc(d.p)}選手${d.nt}点`).join("、")}）です。</p>`;
  }

  window.Contribution = { renderPage, renderPlayer };
})();
