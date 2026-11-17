// 貢献度（contribution.html のグラフと、player.html の「貢献度」欄）。
// 第10節終了時点で集計した値を固定で持つ。毎日の自動更新の対象ではない
// （元データの取得日は各項目の出典に記載。再集計するときはこのファイルの CONTRIB_DATA を差し替える）。
// 配点は1通りに固定している（下の CONTRIB_W）。
(function () {
  const DATA = [{"p": "Toby", "t": "MURASH GAMING", "w": 8, "l": 2, "c": 44.2857, "s": 28.3362, "pr": 1, "bb": 0, "tour": [], "lad": 3, "est": false, "slug": "toby", "ls": 1026541, "ln": 29, "lm": 29796, "up": 25201, "wt": 107629.0, "ld": [["第8弾 前半戦", "ビショップ", 16, 2075], ["第8弾 後半戦", "エルフ", 53, 2031], ["第9弾 前半戦", "ビショップ", 3, 2123]], "aw": [["プロモーションスター賞", "第2回アワード（第9弾）", "P"]], "tr": [], "nt": 0, "nacc": "", "narts": [], "wq": "", "wqs": "2勝3敗", "wqt": ""}, {"p": "Era53", "t": "レバンガ北海道", "w": 6, "l": 4, "c": 33.8095, "s": 29.3251, "pr": 1, "bb": 0, "tour": [], "lad": 1, "est": false, "slug": "era53", "ls": 1429775, "ln": 59, "lm": 21031, "up": 131235, "wt": 273120.0, "ld": [["第8弾 後半戦", "ナイトメア", 72, 2060]], "aw": [["プロモーションスター賞", "第1回アワード（第8弾）", "P"]], "tr": [], "nt": 0, "nacc": "", "narts": [], "wq": "", "wqs": "2勝3敗", "wqt": ""}, {"p": "rikka", "t": "レバンガ北海道", "w": 6, "l": 4, "c": 33.8095, "s": 23.6332, "pr": 0, "bb": 1, "tour": [], "lad": 11, "est": false, "slug": "rikka", "ls": 685398, "ln": 25, "lm": 24684, "up": 0, "wt": 151079.0, "ld": [["第8弾 前半戦", "ナイトメア", 1, 2200], ["第8弾 前半戦", "ウィッチ", 2, 2308], ["第8弾 前半戦", "ビショップ", 16, 2075], ["第8弾 前半戦", "ロイヤル", 72, 2106], ["第8弾 前半戦", "ネメシス", 73, 2151], ["第8弾 後半戦", "ウィッチ", 1, 2362], ["第9弾 前半戦", "ネメシス", 1, 2224], ["第9弾 前半戦", "エルフ", 49, 2162], ["第9弾 前半戦", "ロイヤル", 62, 2018], ["第9弾 前半戦", "ウィッチ", 79, 2111], ["第9弾 前半戦", "ビショップ", 84, 2008]], "aw": [["ベストバウト賞", "第2回アワード（第8節の試合）", "B"]], "tr": [], "nt": 0, "nacc": "", "narts": [], "wq": "w3", "wqs": "3勝3敗", "wqt": ""}, {"p": "glory", "t": "MURASH GAMING", "w": 6, "l": 3, "c": 34.3878, "s": 22.4265, "pr": 0, "bb": 1, "tour": [], "lad": 12, "est": false, "slug": "glory", "ls": 878347, "ln": 43, "lm": 15767, "up": 0, "wt": 212429.0, "ld": [["第8弾 前半戦", "ウィッチ", 12, 2209], ["第8弾 前半戦", "ロイヤル", 19, 2118], ["第8弾 前半戦", "ネメシス", 29, 2159], ["第8弾 前半戦", "ビショップ", 48, 2061], ["第8弾 後半戦", "エルフ", 50, 2032], ["第8弾 後半戦", "ウィッチ", 50, 2218], ["第8弾 後半戦", "ナイトメア", 65, 2061], ["第9弾 前半戦", "ウィッチ", 18, 2130], ["第9弾 前半戦", "ビショップ", 29, 2023], ["第9弾 前半戦", "ドラゴン", 41, 2144], ["第9弾 前半戦", "エルフ", 45, 2163], ["第9弾 前半戦", "ネメシス", 86, 2107]], "aw": [["ベストバウト賞", "第1回アワード（第3節の試合）", "B"]], "tr": [], "nt": 0, "nacc": "", "narts": [], "wq": "top16", "wqs": "5勝1敗", "wqt": "1回戦 ヘイムに敗退"}, {"p": "拓海", "t": "REJECT", "w": 8, "l": 1, "c": 45.0, "s": 21.3041, "pr": 0, "bb": 0, "tour": [], "lad": 4, "est": false, "slug": "takumi", "ls": 335590, "ln": 52, "lm": 5700.5, "up": 73922, "wt": 42041.0, "ld": [["第8弾 前半戦", "ビショップ", 6, 2106], ["第8弾 前半戦", "ウィッチ", 37, 2155], ["第8弾 前半戦", "ナイトメア", 55, 2023], ["第9弾 前半戦", "ウィッチ", 79, 2111]], "aw": [], "tr": [], "nt": 0, "nacc": "", "narts": [], "wq": "w3", "wqs": "3勝3敗", "wqt": ""}, {"p": "ヘイム", "t": "ZETA DIVISION", "w": 6, "l": 4, "c": 33.8095, "s": 19.3593, "pr": 0, "bb": 1, "tour": [], "lad": 5, "est": false, "slug": "heimu", "ls": 583802, "ln": 50, "lm": 8389.5, "up": 0, "wt": 79447.0, "ld": [["第8弾 前半戦", "ドラゴン", 25, 2131], ["第8弾 前半戦", "ビショップ", 41, 2063], ["第8弾 前半戦", "ネメシス", 53, 2155], ["第8弾 前半戦", "エルフ", 71, 2066], ["第8弾 後半戦", "ウィッチ", 78, 2214]], "aw": [["ベストバウト賞", "第1回アワード（第3節の試合）", "B"]], "tr": [], "nt": 0, "nacc": "", "narts": [], "wq": "top4", "wqs": "4勝2敗", "wqt": "1回戦 glory、準々決勝 Mishadow51に勝利、準決勝 あぐのむに敗退"}, {"p": "ユーリ", "t": "DetonatioN FocusMe", "w": 6, "l": 4, "c": 33.8095, "s": 24.1695, "pr": 0, "bb": 0, "tour": [], "lad": 5, "est": false, "slug": "yuuri", "ls": 589012, "ln": 46, "lm": 11220.5, "up": 38949, "wt": 83009.0, "ld": [["第8弾 前半戦", "ナイトメア", 7, 2080], ["第8弾 後半戦", "ネメシス", 70, 2164], ["第9弾 前半戦", "エルフ", 49, 2162], ["第9弾 前半戦", "ビショップ", 65, 2012], ["第9弾 前半戦", "ウィッチ", 67, 2113]], "aw": [], "tr": [], "nt": 0, "nacc": "", "narts": [], "wq": "second", "wqs": "5勝1敗", "wqt": "1回戦シード、準々決勝 Spicies、準決勝 かなでに勝利、決勝 あぐのむに敗退"}, {"p": "Spicies", "t": "MURASH GAMING", "w": 4, "l": 3, "c": 24.881, "s": 30.8574, "pr": 0, "bb": 0, "tour": [], "lad": 3, "est": false, "slug": "spicies", "ls": 2320681, "ln": 78, "lm": 27655.0, "up": 92670, "wt": 264011.0, "ld": [["第8弾 前半戦", "ナイトメア", 6, 2091], ["第8弾 前半戦", "ネメシス", 86, 2149], ["第9弾 前半戦", "エルフ", 2, 2250]], "aw": [], "tr": [], "nt": 0, "nacc": "", "narts": [], "wq": "top8", "wqs": "4勝2敗", "wqt": "1回戦 ぱらちゃんに勝利、準々決勝 ユーリに敗退"}, {"p": "CQCQ", "t": "ZETA DIVISION", "w": 5, "l": 5, "c": 28.5714, "s": 22.2615, "pr": 0, "bb": 0, "tour": [], "lad": 7, "est": false, "slug": "cqcq", "ls": 571362, "ln": 30, "lm": 18609.0, "up": 0, "wt": 63694.0, "ld": [["第8弾 前半戦", "ウィッチ", 13, 2207], ["第8弾 前半戦", "ネメシス", 13, 2178], ["第8弾 前半戦", "エルフ", 37, 2073], ["第8弾 前半戦", "ドラゴン", 67, 2124], ["第8弾 後半戦", "ネメシス", 59, 2167], ["第9弾 前半戦", "エルフ", 22, 2169], ["第9弾 前半戦", "ナイトメア", 56, 2109]], "aw": [], "tr": [], "nt": 0, "nacc": "", "narts": [], "wq": "top16", "wqs": "4勝2敗", "wqt": "1回戦 かなでに敗退"}, {"p": "ふえた", "t": "Crazy Raccoon", "w": 7, "l": 3, "c": 39.0476, "s": 10.9699, "pr": 0, "bb": 0, "tour": [], "lad": 7, "est": false, "slug": "fueta", "ls": 32369, "ln": 11, "lm": 1686, "up": 15125, "wt": 2526.0, "ld": [["第9弾 前半戦", "ロイヤル", 23, 2027], ["第9弾 前半戦", "エルフ", 26, 2167], ["第9弾 前半戦", "ドラゴン", 34, 2145], ["第9弾 前半戦", "ウィッチ", 74, 2112], ["第9弾 前半戦", "ナイトメア", 78, 2105], ["第9弾 前半戦", "ビショップ", 84, 2008], ["第9弾 前半戦", "ネメシス", 86, 2107]], "aw": [], "tr": [], "nt": 0, "nacc": "", "narts": [], "wq": "", "wqs": "2勝3敗", "wqt": ""}, {"p": "ミル", "t": "DetonatioN FocusMe", "w": 7, "l": 3, "c": 39.0476, "s": 13.3212, "pr": 0, "bb": 0, "tour": [], "lad": 0, "est": false, "slug": "mill", "ls": 119950, "ln": 29, "lm": 3546, "up": 0, "wt": 7928.0, "ld": [], "aw": [], "tr": [], "nt": 0, "nacc": "", "narts": [], "wq": "w3", "wqs": "3勝3敗", "wqt": ""}, {"p": "マイト", "t": "MURASH GAMING", "w": 2, "l": 2, "c": 15.7143, "s": 32.6651, "pr": 0, "bb": 0, "tour": [], "lad": 2, "est": false, "slug": "maito", "ls": 1606938, "ln": 33, "lm": 44353, "up": 189679, "wt": 175561.0, "ld": [["第8弾 前半戦", "ネメシス", 5, 2212], ["第9弾 前半戦", "ネメシス", 15, 2125]], "aw": [], "tr": [], "nt": 0, "nacc": "", "narts": [], "wq": "", "wqs": "2勝3敗", "wqt": ""}, {"p": "Atom", "t": "Crazy Raccoon", "w": 5, "l": 5, "c": 28.5714, "s": 19.3154, "pr": 0, "bb": 0, "tour": ["top8"], "lad": 3, "est": false, "slug": "atom", "ls": 109686, "ln": 12, "lm": 7185.0, "up": 32882, "wt": 18733.0, "ld": [["第8弾 前半戦", "エルフ", 77, 2064], ["第8弾 後半戦", "エルフ", 13, 2065], ["第8弾 後半戦", "ウィッチ", 50, 2218]], "aw": [], "tr": [["OCS 2026 November（11月7〜15日）", "5位タイ（ベスト8）", "top8", "https://ocs.shadowverse-wb.com/ja/2026/november/results/", 1]], "nt": 0, "nacc": "", "narts": [], "wq": "w3", "wqs": "3勝3敗", "wqt": ""}, {"p": "まっつ", "t": "VARREL", "w": 4, "l": 4, "c": 24.2857, "s": 15.69, "pr": 0, "bb": 0, "tour": ["top8", "second"], "lad": 3, "est": false, "slug": "mattsu", "ls": 75999, "ln": 15, "lm": 4528, "up": 9533, "wt": 6178.0, "ld": [["第8弾 前半戦", "ウィッチ", 16, 2203], ["第8弾 前半戦", "ネメシス", 32, 2158], ["第8弾 後半戦", "ウィッチ", 5, 2270]], "aw": [], "tr": [["ICS 2026 Singapore（9月26〜27日）", "ベスト8（予選9戦全勝）", "top8", "https://onemoregame.ph/2026/10/shadowverse-international-2026-sg-chappy/"], ["RAGE JCS 2026 Season 3（10月25日決勝）", "準優勝", "second", "https://gamebiz.jp/news/434703"]], "nt": 0, "nacc": "", "narts": [], "wq": "", "wqs": "", "wqt": ""}, {"p": "Chappy", "t": "RIDDLE ORDER", "w": 2, "l": 3, "c": 15.0, "s": 20.1, "pr": 0, "bb": 0, "tour": ["win"], "lad": 2, "est": true, "slug": "chappy", "ls": 0, "ln": 0, "lm": 0, "up": 0, "wt": 29989.0, "ld": [["第8弾 前半戦", "ナイトメア", 24, 2032], ["第8弾 後半戦", "ナイトメア", 79, 2059]], "aw": [], "tr": [["ICS 2026 Singapore（9月26〜27日）", "優勝", "win", "https://ics.shadowverse-wb.com/ja/news/detail/?id=75"]], "nt": 0, "nacc": "", "narts": [], "wq": "", "wqs": "", "wqt": ""}, {"p": "Stylish_deko", "t": "RIDDLE ORDER", "w": 3, "l": 1, "c": 21.5873, "s": 14.6201, "pr": 0, "bb": 1, "tour": [], "lad": 2, "est": false, "slug": "stylishdeko", "ls": 199719, "ln": 72, "lm": 1920.0, "up": 13481, "wt": 18141.0, "ld": [["第8弾 前半戦", "ビショップ", 9, 2100], ["第8弾 前半戦", "ナイトメア", 19, 2034]], "aw": [["ベストバウト賞", "第2回アワード（第8節の試合）", "B"]], "tr": [], "nt": 0, "nacc": "", "narts": [], "wq": "", "wqs": "1勝3敗", "wqt": ""}, {"p": "たばた", "t": "REJECT", "w": 4, "l": 6, "c": 23.3333, "s": 20.432, "pr": 0, "bb": 0, "tour": [], "lad": 1, "est": false, "slug": "tabata", "ls": 168833, "ln": 26, "lm": 6257.0, "up": 75766, "wt": 17447.0, "ld": [["第8弾 後半戦", "ドラゴン", 28, 2144]], "aw": [], "tr": [], "nt": 0, "nacc": "", "narts": [], "wq": "", "wqs": "1勝3敗", "wqt": ""}, {"p": "ぱらちゃん", "t": "REJECT", "w": 1, "l": 2, "c": 10.5357, "s": 29.7746, "pr": 0, "bb": 0, "tour": ["third"], "lad": 0, "est": false, "slug": "parachan", "ls": 1060232, "ln": 42, "lm": 23513.5, "up": 231769, "wt": 137979.0, "ld": [], "aw": [], "tr": [["RAGE JCS 2026 Season 3（10月25日決勝）", "3位", "third", "https://gamebiz.jp/news/434703"]], "nt": 0, "nacc": "", "narts": [], "wq": "top16", "wqs": "4勝2敗", "wqt": "1回戦 Spiciesに敗退"}, {"p": "つきあかめん", "t": "REJECT", "w": 1, "l": 3, "c": 9.8413, "s": 26.1831, "pr": 0, "bb": 0, "tour": [], "lad": 1, "est": false, "slug": "tsukiakamen", "ls": 878016, "ln": 63, "lm": 12297, "up": 99634, "wt": 109038.0, "ld": [["第8弾 後半戦", "エルフ", 53, 2031]], "aw": [], "tr": [], "nt": 0, "nacc": "", "narts": [], "wq": "", "wqs": "1勝3敗", "wqt": ""}, {"p": "かなで", "t": "DetonatioN FocusMe", "w": 4, "l": 4, "c": 24.2857, "s": 9.6827, "pr": 0, "bb": 0, "tour": [], "lad": 2, "est": false, "slug": "kanade", "ls": 41357, "ln": 16, "lm": 2228.5, "up": 0, "wt": 1915.0, "ld": [["第8弾 後半戦", "ウィッチ", 4, 2304], ["第9弾 前半戦", "エルフ", 7, 2206]], "aw": [], "tr": [], "nt": 0, "nacc": "", "narts": [], "wq": "top4", "wqs": "4勝2敗", "wqt": "1回戦 CQCQ、準々決勝 ねぎまに勝利、準決勝 ユーリに敗退"}, {"p": "TBT", "t": "ZETA DIVISION", "w": 2, "l": 3, "c": 15.0, "s": 17.5675, "pr": 0, "bb": 0, "tour": [], "lad": 3, "est": false, "slug": "tbt", "ls": 196902, "ln": 52, "lm": 3140.0, "up": 42102, "wt": 11158.0, "ld": [["第8弾 前半戦", "ドラゴン", 32, 2130], ["第8弾 前半戦", "ビショップ", 65, 2057], ["第8弾 前半戦", "エルフ", 84, 2062]], "aw": [], "tr": [], "nt": 3, "nacc": "https://note.com/tabe_tter", "narts": [["PS観戦ガイド：PSスクリム振り返りと第1節の見どころ紹介", "7月8日", "https://note.com/tabe_tter/n/n90baab12e27f"], ["PS観戦ガイド【第8節 前半】", "10月ごろ", "https://note.com/tabe_tter/n/n7e5d1575d5a9"]], "wq": "top8", "wqs": "5勝1敗", "wqt": "1回戦シード、準々決勝 あぐのむに敗退"}, {"p": "折り紙", "t": "RIDDLE ORDER", "w": 1, "l": 5, "c": 8.8312, "s": 19.9478, "pr": 0, "bb": 0, "tour": [], "lad": 5, "est": false, "slug": "origami", "ls": 204191, "ln": 49, "lm": 4072, "up": 159797, "wt": 24936.0, "ld": [["第8弾 前半戦", "ネメシス", 40, 2157], ["第8弾 前半戦", "ドラゴン", 70, 2123], ["第8弾 後半戦", "ネメシス", 89, 2161], ["第9弾 前半戦", "ネメシス", 5, 2164], ["第9弾 前半戦", "エルフ", 81, 2157]], "aw": [], "tr": [], "nt": 0, "nacc": "", "narts": [], "wq": "", "wqs": "0勝3敗", "wqt": ""}, {"p": "空白", "t": "Crazy Raccoon", "w": 3, "l": 4, "c": 19.4048, "s": 7.1059, "pr": 0, "bb": 0, "tour": [], "lad": 10, "est": false, "slug": "kuhaku", "ls": 18710, "ln": 19, "lm": 741, "up": 5965, "wt": 3350.0, "ld": [["第8弾 前半戦", "ウィッチ", 84, 2145], ["第8弾 後半戦", "ドラゴン", 56, 2136], ["第8弾 後半戦", "ネメシス", 63, 2166], ["第8弾 後半戦", "ナイトメア", 100, 2054], ["第9弾 前半戦", "ビショップ", 17, 2033], ["第9弾 前半戦", "ウィッチ", 26, 2125], ["第9弾 前半戦", "ナイトメア", 40, 2112], ["第9弾 前半戦", "ネメシス", 45, 2115], ["第9弾 前半戦", "エルフ", 49, 2162], ["第9弾 前半戦", "ドラゴン", 80, 2138]], "aw": [], "tr": [], "nt": 0, "nacc": "", "narts": [], "wq": "", "wqs": "0勝3敗", "wqt": ""}, {"p": "もっちゃま", "t": "MURASH GAMING", "w": 0, "l": 0, "c": 0, "s": 30.4879, "pr": 0, "bb": 0, "tour": [], "lad": 0, "est": false, "slug": "mochama", "ls": 1820292, "ln": 57, "lm": 29314, "up": 80273, "wt": 328179.0, "ld": [], "aw": [], "tr": [], "nt": 0, "nacc": "", "narts": [], "wq": "", "wqs": "1勝3敗", "wqt": ""}, {"p": "Terarina", "t": "VARREL", "w": 3, "l": 7, "c": 18.0952, "s": 7.0334, "pr": 0, "bb": 0, "tour": ["third"], "lad": 12, "est": false, "slug": "terarina", "ls": 17441, "ln": 9, "lm": 1659, "up": 0, "wt": 1940.0, "ld": [["第8弾 前半戦", "エルフ", 5, 2134], ["第8弾 前半戦", "ビショップ", 32, 2065], ["第8弾 前半戦", "ドラゴン", 57, 2125], ["第8弾 前半戦", "ナイトメア", 77, 2019], ["第8弾 前半戦", "ウィッチ", 99, 2142], ["第8弾 後半戦", "ドラゴン", 12, 2162], ["第8弾 後半戦", "エルフ", 40, 2035], ["第8弾 後半戦", "ビショップ", 48, 2041], ["第9弾 前半戦", "ビショップ", 2, 2146], ["第9弾 前半戦", "エルフ", 8, 2204], ["第9弾 前半戦", "ドラゴン", 18, 2151], ["第9弾 前半戦", "ナイトメア", 84, 2104]], "aw": [], "tr": [["OCS 2026 November（11月7〜15日）", "3位タイ", "third", "https://ocs.shadowverse-wb.com/ja/2026/november/results/", 1]], "nt": 0, "nacc": "", "narts": [], "wq": "", "wqs": "2勝3敗", "wqt": ""}, {"p": "ぱんさく", "t": "RIDDLE ORDER", "w": 4, "l": 4, "c": 24.2857, "s": 5.0641, "pr": 0, "bb": 0, "tour": [], "lad": 1, "est": false, "slug": "pansaku", "ls": 16497, "ln": 16, "lm": 724.0, "up": 0, "wt": 329.0, "ld": [["第8弾 前半戦", "ナイトメア", 12, 2040]], "aw": [], "tr": [], "nt": 0, "nacc": "", "narts": [], "wq": "", "wqs": "0勝3敗", "wqt": ""}, {"p": "だーよね", "t": "レバンガ北海道", "w": 3, "l": 3, "c": 20.0, "s": 8.7123, "pr": 0, "bb": 0, "tour": [], "lad": 1, "est": false, "slug": "dayone", "ls": 25116, "ln": 10, "lm": 2187.0, "up": 0, "wt": 3670.0, "ld": [["第8弾 前半戦", "ビショップ", 32, 2065]], "aw": [], "tr": [], "nt": 0, "nacc": "", "narts": [], "wq": "top16", "wqs": "4勝2敗", "wqt": "1回戦 Mishadow51に敗退"}, {"p": "智念せいら", "t": "レバンガ北海道", "w": 0, "l": 0, "c": 0, "s": 28.9955, "pr": 0, "bb": 0, "tour": [], "lad": 0, "est": false, "slug": "seirachinen", "ls": 515288, "ln": 25, "lm": 18213, "up": 982427, "wt": 84296.0, "ld": [], "aw": [], "tr": [], "nt": 0, "nacc": "", "narts": [], "wq": "", "wqs": "1勝3敗", "wqt": ""}, {"p": "Hirobosu", "t": "レバンガ北海道", "w": 1, "l": 3, "c": 9.8413, "s": 16.3704, "pr": 0, "bb": 0, "tour": [], "lad": 4, "est": false, "slug": "hirobosu", "ls": 269312, "ln": 34, "lm": 5452.0, "up": 0, "wt": 26937.0, "ld": [["第8弾 前半戦", "ウィッチ", 32, 2156], ["第8弾 後半戦", "ナイトメア", 18, 2104], ["第8弾 後半戦", "ウィッチ", 65, 2216], ["第9弾 前半戦", "ドラゴン", 41, 2144]], "aw": [], "tr": [], "nt": 0, "nacc": "", "narts": [], "wq": "top16", "wqs": "5勝1敗", "wqt": "1回戦 ねぎまに敗退"}, {"p": "MingiGod", "t": "DetonatioN FocusMe", "w": 1, "l": 1, "c": 11.4286, "s": 15.8101, "pr": 0, "bb": 0, "tour": [], "lad": 1, "est": false, "slug": "mingigod", "ls": 125305, "ln": 32, "lm": 3093.5, "up": 17606, "wt": 9829.0, "ld": [["第9弾 前半戦", "エルフ", 39, 2164]], "aw": [], "tr": [], "nt": 0, "nacc": "", "narts": [], "wq": "", "wqs": "1勝3敗", "wqt": ""}, {"p": "あぐのむ", "t": "REJECT", "w": 0, "l": 4, "c": 3.9683, "s": 22.977, "pr": 0, "bb": 0, "tour": [], "lad": 0, "est": false, "slug": "agunomu", "ls": 223346, "ln": 18, "lm": 12274.0, "up": 48752, "wt": 33811.0, "ld": [], "aw": [], "tr": [], "nt": 0, "nacc": "", "narts": [], "wq": "win", "wqs": "4勝2敗", "wqt": "1回戦 Winter、準々決勝 TBT、準決勝 ヘイム、決勝 ユーリに勝利"}, {"p": "ふぇぐ", "t": "Crazy Raccoon", "w": 1, "l": 1, "c": 11.4286, "s": 15.1103, "pr": 0, "bb": 0, "tour": [], "lad": 0, "est": false, "slug": "feg", "ls": 49706, "ln": 17, "lm": 2641, "up": 81308, "wt": 4273.0, "ld": [], "aw": [], "tr": [], "nt": 0, "nacc": "", "narts": [], "wq": "", "wqs": "0勝3敗", "wqt": ""}, {"p": "ねぎま", "t": "ZETA DIVISION", "w": 1, "l": 4, "c": 9.2857, "s": 15.281, "pr": 0, "bb": 0, "tour": [], "lad": 3, "est": false, "slug": "negima", "ls": 237763, "ln": 53, "lm": 4314, "up": 0, "wt": 37981.0, "ld": [["第8弾 前半戦", "ドラゴン", 17, 2133], ["第9弾 前半戦", "ロイヤル", 66, 2017], ["第9弾 前半戦", "ネメシス", 76, 2109]], "aw": [], "tr": [], "nt": 0, "nacc": "", "narts": [], "wq": "top8", "wqs": "4勝2敗", "wqt": "1回戦 Hirobosuに勝利、準々決勝 かなでに敗退"}, {"p": "monakawan", "t": "VARREL", "w": 2, "l": 5, "c": 13.9286, "s": 9.3151, "pr": 0, "bb": 0, "tour": [], "lad": 6, "est": false, "slug": "monakawan", "ls": 91945, "ln": 46, "lm": 1364.5, "up": 0, "wt": 6689.0, "ld": [["第8弾 後半戦", "エルフ", 80, 2026], ["第8弾 後半戦", "ナイトメア", 81, 2058], ["第9弾 前半戦", "ドラゴン", 32, 2146], ["第9弾 前半戦", "ウィッチ", 55, 2116], ["第9弾 前半戦", "ナイトメア", 58, 2108], ["第9弾 前半戦", "ロイヤル", 74, 2015]], "aw": [], "tr": [], "nt": 2, "nacc": "https://note.com/crisp_robin8169", "narts": [["第9節後半ランプドラゴンVS海賊ロイヤル完全解説", "10月下旬ごろ", "https://note.com/crisp_robin8169/n/n4b3033183969"], ["ラピッドハットでもわかるランプドラゴン", "11月上旬ごろ", "https://note.com/crisp_robin8169"]], "wq": "w3", "wqs": "3勝3敗", "wqt": ""}, {"p": "山田レクイエム", "t": "RIDDLE ORDER", "w": 2, "l": 5, "c": 13.9286, "s": 3.4356, "pr": 0, "bb": 0, "tour": [], "lad": 5, "est": false, "slug": "ymdrequiem", "ls": 2975, "ln": 2, "lm": 1487.5, "up": 0, "wt": 146.0, "ld": [["第8弾 前半戦", "ビショップ", 72, 2056], ["第8弾 前半戦", "ウィッチ", 84, 2145], ["第8弾 後半戦", "ウィッチ", 36, 2221], ["第8弾 後半戦", "ネメシス", 54, 2168], ["第9弾 前半戦", "ビショップ", 46, 2018]], "aw": [], "tr": [], "nt": 0, "nacc": "", "narts": [], "wq": "", "wqs": "2勝3敗", "wqt": ""}, {"p": "Winter", "t": "Crazy Raccoon", "w": 0, "l": 1, "c": 5.9524, "s": 9.3618, "pr": 0, "bb": 0, "tour": [], "lad": 1, "est": false, "slug": "winter", "ls": 11850, "ln": 7, "lm": 1755, "up": 16033, "wt": 1324.0, "ld": [["第9弾 前半戦", "エルフ", 15, 2173]], "aw": [], "tr": [], "nt": 0, "nacc": "", "narts": [], "wq": "top16", "wqs": "4勝2敗", "wqt": "1回戦 あぐのむに敗退"}, {"p": "Mishadow51", "t": "VARREL", "w": 1, "l": 4, "c": 9.2857, "s": null, "pr": 0, "bb": 0, "tour": [], "lad": 2, "est": false, "slug": "mishadow51", "ls": 0, "ln": 0, "lm": 0, "up": 0, "wt": 0.0, "ld": [["第8弾 後半戦", "エルフ", 12, 2078], ["第9弾 前半戦", "ウィッチ", 28, 2124]], "aw": [], "tr": [], "nt": 0, "nacc": "", "narts": [], "wq": "top8", "wqs": "4勝2敗", "wqt": "1回戦 だーよねに勝利、準々決勝 ヘイムに敗退"}];
  const K = {"cmax": 31.5, "tmax": 2320681, "mmax": 44353, "umax": 982427, "a": -19.928387946992217, "b": 8.946682672161858, "n": 35};
  const W = { C: 45, LT: 14, LM: 14, V: 4, N: 3, P: 12, B: 4, win: 10, second: 8, third: 6, top8: 5,
              Q1: 10, Q2: 8, Q4: 6, Q8: 5, Q16: 4, Q3: 1.5, L: 5 };
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
    const lad = r1(W.L * r.lad / 12);
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
    s += `<text x="40" y="56" fill="${COL.sub}">所属選手の合計点の平均。第10節終了時点</text>`;
    s += `<text x="40" y="78" fill="${COL.sub}" font-size="12">全選手の平均は ${all.toFixed(1)} 点</text>`;
    teams.forEach((t, i) => {
      const y = y0 + i * rh;
      s += `<text x="40" y="${y + 15}" fill="${COL.ink}">${esc(t.t)}</text><text x="${x0 - 12}" y="${y + 15}" text-anchor="end" fill="${COL.sub}" font-size="11">${t.n}名</text>`;
      s += `<rect x="${x0}" y="${y}" width="${sx(t.avg).toFixed(2)}" height="20" fill="${i === 0 ? COL.comp : COL.muted}"/>`;
      s += `<text x="${(x0 + sx(t.avg) + 8).toFixed(2)}" y="${y + 15}" fill="${COL.ink}">${t.avg.toFixed(1)}</text>`;
    });
    return s + `</svg>`;
  }

  function renderPage(el) {
    const { rows } = ranking();
    el.innerHTML = `
      <h2 class="contrib-title">貢献度ランキング</h2>
      <div class="contrib-chart">${rankSVG(rows)}</div>
      <p class="contrib-note">チーム名は略称です。CRはCrazy Raccoon、ZETAはZETA DIVISION、DFMはDetonatioN FocusMe、MRGはMURASH GAMING、RIDDLEはRIDDLE ORDER、LVHはレバンガ北海道です。選手名を押すと、その選手のページで点数の計算内訳を確認できます。</p>
      <h2 class="contrib-title">チーム別の貢献度</h2>
      <div class="contrib-chart">${teamSVG(rows)}</div>`;
  }

  const SRC = {
    comp: ["Shadowverse Vision 試合結果（第10節終了時点）", "https://shadowverse-vision.com/schedule-results"],
    send: ["SVPS選手データ（YouTube Data APIで取得した配信ごとの再生数、11月4日更新）", "index.html"],
    repo: ["SVPS選手データの公開リポジトリ（data/streams.json、data/history.csv）", "https://github.com/hirobosu-staff/svps-data"],
    watch: ["SVPS選手データ（shadowverse-reference.comから取得した視聴時間、11月4日更新）", "index.html"],
    award1: ["Shadowverse Vision アワード", "https://shadowverse-vision.com/awards"],
    award2: ["Premier Series 公式サイト 第2回アワード表彰結果", "https://ps.shadowverse-wb.com/26-27/news/369/"],
    noteTag: ["noteの「#シャドバPS」タグ記事一覧", "https://note.com/hashtag/%E3%82%B7%E3%83%A3%E3%83%89%E3%83%90PS"],
    ladder: ["SVPS選手データ（svlabo.jpのランクマッチ上位100名の記録、11月4日更新）", "beyond.html"],
    rating: ["Shadowverse Vision ゲーム内レート", "https://shadowverse-vision.com/rating"],
    wq1: ["Premier Series 公式サイト WGP Qualifier 2026 大会結果のお知らせ（決勝トーナメント表）", "https://ps.shadowverse-wb.com/26-27/news/381/"],
    wq2: ["Premier Series 公式サイト WGP Qualifier 2026 開催のお知らせ（大会形式）", "https://ps.shadowverse-wb.com/26-27/news/375/"],
    wq3: ["Premier Series 公式X（11月14日 スイスドロー各回戦の結果画像）", "https://x.com/shadowversePS"],
    wq4: ["シャドラボ Premier Series WGP Qualifier 2026 結果＆デッキ分布", "https://svlabo.jp/blog-entry-2027.html"]
  };
  const link = s => /^https?:/.test(s[1]) ? `<a href="${s[1]}" target="_blank" rel="noopener">${esc(s[0])}</a>` : `<a href="${s[1]}">${esc(s[0])}</a>`;

  // player.html の「貢献度」欄。該当する選手がいなければ何も表示しない。
  function renderPlayer(el, name) {
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
      rows.push(`<tr><td class="item">配信</td><td>Twitchのみで配信しているため、YouTubeの再生数がありません。配信先を問わない視聴時間はシーズン中${fmt(r.wt)}時間です。</td><td class="f">再生数を取得できた${K.n}名で、視聴時間と配信点（35点満点）の関係を求めた式に当てはめています。<br>推計値 = −${fmt(-K.a, 2)} ＋ ${fmt(K.b, 3)} × log10(${fmt(r.wt)}) = 20.1（35点満点）<br>点数 = 20.1 ÷ 35 × (${W.LT} ＋ ${W.LM} ＋ ${W.V}) = ${fmt(x.send, 2)}</td><td class="num">${fmt(x.send, 2)}</td></tr>`);
    } else {
      const a1 = W.LT * lg(r.ls, K.tmax), a2 = W.LM * lg(r.lm, K.mmax);
      rows.push(`<tr><td class="item">配信</td><td colspan="2">YouTubeの再生数を3つの指標に分け、それぞれ全選手の最高値を満点として対数で比べます。1,000回未満は0点です。</td><td></td></tr>`);
      rows.push(`<tr><td class="item sub">ライブ合計</td><td>8月3日〜11月4日のライブ配信${r.ln}本、合計${fmt(r.ls)}回</td><td class="f">${W.LT} × log10(${fmt(r.ls)} ÷ 1,000) ÷ log10(${fmt(K.tmax)} ÷ 1,000) = ${fmt(a1, 2)}</td><td class="num">${fmt(a1, 2)}</td></tr>`);
      rows.push(`<tr><td class="item sub">1本あたり</td><td>同期間の1本あたり再生数の中央値 ${fmt(r.lm)}回</td><td class="f">${W.LM} × log10(${fmt(r.lm)} ÷ 1,000) ÷ log10(${fmt(K.mmax)} ÷ 1,000) = ${fmt(a2, 2)}</td><td class="num">${fmt(a2, 2)}</td></tr>`);
      rows.push(`<tr><td class="item sub">投稿動画</td><td>レギュラーシーズン中の投稿動画 合計${fmt(r.up)}回</td><td class="f">${W.V} × log10(${fmt(r.up)} ÷ 1,000) ÷ log10(${fmt(K.umax)} ÷ 1,000) = ${fmt(x.sp.video, 2)}</td><td class="num">${fmt(x.sp.video, 2)}</td></tr>`);
    }
    rows.push(`<tr><td class="item">note</td><td>${r.narts.length ? `7月以降の記事${r.narts.length}本<br>${r.narts.map(a => `<a href="${a[2]}" target="_blank" rel="noopener">${esc(a[0])}</a>（${esc(a[1])}）`).join("<br>")}` : "7月以降のnote記事は確認できませんでした"}</td><td class="f">${r.nt ? `評価 ${r.nt}点（3点満点）を配点に合わせて換算<br>${r.nt} ÷ 3 × ${W.N} = ${fmt(x.note, 2)}` : "0点"}</td><td class="num">${fmt(x.note, 2)}</td></tr>`);
    rows.push(`<tr><td class="item">表彰</td><td>${r.aw.length ? r.aw.map(a => `${esc(a[0])}（${esc(a[1])}）`).join("<br>") : "受賞なし"}</td><td class="f">${r.aw.length ? r.aw.map(a => `${esc(a[0])} ${a[2] === "P" ? W.P : W.B}点`).join("<br>") : "0点"}</td><td class="num">${fmt(x.award, 2)}</td></tr>`);
    rows.push(`<tr><td class="item">大会加点</td><td>${r.tr.length ? r.tr.map(t => `${esc(t[0])} ${esc(t[1])}`).join("<br>") : "7月以降の公式大会で上位入賞の記録なし"}</td><td class="f">${r.tr.length ? r.tr.map(t => `${TOUR_LABEL[t[2]]} ${W[t[2]]}点`).join("<br>") : "0点"}</td><td class="num">${fmt(x.bonus, 2)}</td></tr>`);
    const wqDesc = !r.wqs ? `出場なし（${esc(r.p)}選手はWGP 2026の出場権を獲得済み）`
      : `予選スイスドロー ${r.wqs}` + (r.wq && r.wq !== "w3" ? `、決勝トーナメント ${WQ_LABEL[r.wq]}（${esc(r.wqt)}）` : (r.wq === "w3" ? "、決勝トーナメント進出ならず" : "、3敗でドロップ"));
    const wqCalc = r.wq ? `${WQ_LABEL[r.wq]} ${W[WQKEY[r.wq]]}点` : `0点（決勝トーナメント進出 ${W.Q16}点、予選3勝 ${W.Q3}点に届かず）`;
    rows.push(`<tr><td class="item">WGP予選</td><td>${wqDesc}</td><td class="f">${r.wqs ? wqCalc : "0点"}</td><td class="num">${fmt(x.wq, 2)}</td></tr>`);
    rows.push(`<tr><td class="item">ランクマッチ補正</td><td>7月以降（第8弾前半戦・後半戦、第9弾前半戦）にクラス別トップ100へ入った回数 ${r.lad}回</td><td class="f">${W.L} × ${r.lad} ÷ 12（最多回数） = ${fmt(x.lad, 1)}</td><td class="num">${fmt(x.lad, 1)}</td></tr>`);
    rows.push(`<tr class="total"><td>合計</td><td colspan="2">競技・配信・note・表彰の合計を小数第1位で丸め、大会加点、WGP予選、ランクマッチ補正を足しています。</td><td class="num">${x.total.toFixed(1)}</td></tr>`);

    const ladderRows = r.ld.length ? r.ld.map(e => `<tr><td>${esc(e[0])}</td><td>${esc(e[1])}</td><td class="num">${e[2]}位</td><td class="num">${e[3]}</td></tr>`).join("") : `<tr><td colspan="4">記録なし</td></tr>`;
    const srcs = [SRC.comp, ["Shadowverse Vision 選手ページ", `https://shadowverse-vision.com/players/${r.slug}`]];
    if (r.est) srcs.push(SRC.watch, SRC.repo); else if (r.s !== null) srcs.push(SRC.send, SRC.repo);
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
          <div class="label">貢献度（第10節終了時点）</div>
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
      <p class="contrib-note">第9弾後半戦のランクマッチ記録は、集計時点で公開されていなかったため含めていません。noteの点数は、記事数とスキ数をもとにした評価値（TBT選手3点、monakawan選手2点）です。</p>`;
  }

  window.Contribution = { renderPage, renderPlayer, has: name => DATA.some(d => d.p === name) };
})();
