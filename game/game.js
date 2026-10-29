// Body Run: a side-scrolling runner through the body (jump, double jump, slide). The world is 180 units tall and as
// wide as the screen's shape allows (300..420 units); it is drawn straight at the screen's own pixel resolution
// from high-resolution art (4 px per unit; the characters at the resolution of their sheet).
// Speed: from 170 units/s, +0.8 every second of running (v47), no top speed. Jump, double and triple jump (even the highest stays clear of the ceiling);
// more jumps after the third keep you up, but never above the triple jump's highest point.
// Health drains 1/s; heals +25; a hit -15 and a stumble.
(() => {
  'use strict';
  const qs = new URLSearchParams(location.search);
  const CAPTURE = qs.has('capture');            // test hook: no animation loop, the test steps the game
  const AUTO = qs.has('auto');                  // test hook: the game plays itself
  const NO_DEATH_TEST = (CAPTURE || AUTO) && !qs.has('death');   // tests: health 0 does not end the run (?death turns it on)
  const PRELOAD = qs.has('preload');            // test hook: decode every picture up front
  const PROF = qs.has('prof') ? {} : null;      // test hook: time each part of drawing (window.__prof)
  // (v47) Korean or English: the device's language (?lang=ko|en for tests); every word on screen through TR(ko, en)
  const LANG = (qs.get('lang') || navigator.language || 'en').toLowerCase().startsWith('ko') ? 'ko' : 'en';
  const TR = (ko, en) => (LANG === 'ko' ? ko : en);
  const PT = (n) => (LANG === 'ko' ? `${n.toLocaleString('en-US')}점` : `${n.toLocaleString('en-US')} pts`);   // points
  document.documentElement.lang = LANG; document.title = TR('장기런', 'Body Run');
  if (LANG !== 'ko') for (const el of document.querySelectorAll('[data-en]')) el.textContent = el.dataset.en;    // the page's own words

  // ---------------------------------------------------------------- world constants (units, seconds)
  const NH = 180, GY = 150, CEIL = 14, PX = 84;
  const GRAV = 900, JUMP = 326, JUMP2 = 226, JUMP3 = 184, FASTFALL = 2.4;   // single 59 high, double 87.4, triple ~105 (v20: single +10%)
  const JMAX = (JUMP * JUMP + JUMP2 * JUMP2 + JUMP3 * JUMP3) / (2 * GRAV);    // the triple jump at its best (106.2): the 4th and on stop there
  const V0 = 170, ACC = 0.8, VMAX = Infinity;               // (v47: +0.8/s; v43: +1/s, was 0.6; no top speed, was 900)
  const HP_MAX = 100, DRAIN = 1.0, HIT = 20, HEAL = 25, INVUL = 1.2;     // (v51: a bump costs 20, was 15)
  // (v57) a heal every 33 s of running (30 to 36; the mini-games don't count), not every so far: by distance they came
  // quicker the quicker you ran, and outran the drain (+1.5..2.7 a second against 1). Now 25 in 33 s against 33: taking
  // every one and never hit, the health runs out in about 7 minutes of running
  const HEAL_EVERY = 33, HEAL_JIT = 3;
  // the player's box: half-width and height running, sliding (the characters are drawn 0.8 of their old size)
  const PW = 5.76, PH = 17.28, SLW = 7.92, SLH = 9.36;     // (v38: 0.9 of v15's 6.4, 19.2, 8.8, 10.4, with the pictures)
  const TOPY = CEIL + 10;                       // a safety stop only: a perfect triple jump tops out at about 104 (head at y 27)
  const MAXY = GY - TOPY - PH;                  // ... as a height of the feet above the floor
  const FLOAT_BOTTOM = GY - 15.5, HANG_BOTTOM = GY - 15.5;     // under it a sliding player passes, a running one does not
  // the course: places (id, Korean name, English name, [look, length in units] ...). v43: every place the same
  // distance, 5500 (about 30 s at the start's speed; faster later, it goes by sooner; v42 had set each by time). Every place has a look of its own
  // (the pancreas and the efferent arteriole pass through two); its name shows once, on arrival. Stage 1 is the body;
  // at the anus a cut scene takes you out into the toilet: stage 2, down the drains (after its last place, for now, the
  // body again)
  const PLACES = [
    ['esophagus', '식도', 'Esophagus', ['eso', 5500]], ['stomach', '위', 'Stomach', ['stomach', 5500]],
    ['duodenum', '십이지장', 'Duodenum', ['duodenum', 5500]],
    ['liver', '간', 'Liver', ['liver', 5500]],
    ['gallbladder', '담낭', 'Gallbladder', ['gallbladder', 5500]],
    ['pancreas', '췌장', 'Pancreas', ['pancreas', 3700], ['islet', 1800]],
    ['spleen', '비장', 'Spleen', ['spleen', 5500]],
    ['capillary', '모세혈관', 'Capillary', ['adrenal', 5500]],
    ['renalArt', '신동맥', 'Renal artery', ['renalart', 5500]], ['glomerulus', '사구체', 'Glomerulus', ['glomerulus', 5500]],
    ['efferent', '수출세동맥', 'Efferent arteriole', ['efferent', 2550], ['kidney', 2950]],
    ['vein', '정맥', 'Vein', ['ivc', 5500]],
    ['ra', '우심방', 'Right atrium', ['atrium', 5500]], ['rv', '우심실', 'Right ventricle', ['ventricle', 5500]],
    ['pulmArt', '폐동맥', 'Pulmonary artery', ['pulmart', 5500]],
    ['lung', '폐', 'Lung', ['bronchiole', 5500]], ['alveoli', '폐포', 'Alveoli', ['lung', 5500]],
    ['pulmVein', '폐정맥', 'Pulmonary vein', ['pulmvein', 5500]],
    ['la', '좌심방', 'Left atrium', ['latrium', 5500]], ['lv', '좌심실', 'Left ventricle', ['lventricle', 5500]],
    ['myoCap', '심근 모세혈관', 'Myocardial capillary', ['myocard', 5500]],
    ['aorta', '대동맥', 'Aorta', ['artery', 5500]], ['carotid', '총경동맥', 'Common carotid artery', ['carotid', 5500]],
    ['thyroid', '갑상선', 'Thyroid', ['thyroid', 5500]], ['vertebral', '척추동맥', 'Vertebral artery', ['vertebral', 5500]],
    // the brain from below: in by the medulla, up round the back, the side and the top to the front, out from the middle
    ['medulla', '연수', 'Medulla oblongata', ['medulla', 5500]], ['cerebellum', '소뇌', 'Cerebellum', ['purkinje', 5500]],
    ['occipital', '후두엽', 'Occipital lobe', ['occipital', 5500]], ['temporal', '측두엽', 'Temporal lobe', ['temporal', 5500]],
    ['hippocampus', '해마', 'Hippocampus', ['hippo', 5500]], ['parietal', '두정엽', 'Parietal lobe', ['parietal', 5500]],
    ['frontal', '전두엽', 'Frontal lobe', ['arach', 5500]], ['cortex', '대뇌피질', 'Cerebral cortex', ['pyramidal', 5500]],
    ['callosum', '뇌량', 'Corpus callosum', ['fibres', 5500]],
    // out along the optic nerve into the back of the eye, then through it to the front (no blood in the clear parts)
    ['opticNerve', '시신경', 'Optic nerve', ['opticnerve', 5500]], ['retina', '망막', 'Retina', ['retina', 5500]],
    ['vitreous', '유리체', 'Vitreous body', ['vitreous', 5500]], ['lens', '수정체', 'Lens', ['lens', 5500]],
    ['pupil', '눈동자', 'Pupil', ['iris', 5500]], ['cornea', '각막', 'Cornea', ['cornea', 5500]],      // the eye blinks here
    ['jugular', '경정맥', 'Jugular vein', ['vein', 5500]],
    ['sma', '상장간막동맥', 'Superior mesenteric artery', ['sma', 5500]],
    ['jejunalWall', '공장벽', 'Jejunal wall', ['villus', 5500]], ['jejunum', '공장', 'Jejunum', ['gut', 5500]], ['ileum', '회장', 'Ileum', ['ileum', 5500]],
    ['cecum', '맹장', 'Cecum', ['cecum', 5500]], ['colon', '대장', 'Large intestine', ['colon', 5500]],
    ['rectum', '직장', 'Rectum', ['rectum', 5500]], ['anus', '항문', 'Anus', ['anus', 5500]],
  ];
  const STAGE2 = PLACES.length;                     // the first place of stage 2
  PLACES.push(['toiletBowl', '변기 물속', 'Toilet bowl', ['toilet', 5500]],
    // down the drains, the way the water really goes: out of the building, the sewers, the treatment works, the river
    ['trap', 'S자 트랩', 'S-trap', ['trap', 5500]], ['soilStack', '오수 수직관', 'Soil stack', ['stack', 5500]],
    ['drainPipe', '집 배수관', 'Drain pipe', ['drain', 5500]], ['septic', '정화조', 'Septic tank', ['septic', 5500]],
    ['chamber', '오수받이', 'Inspection chamber', ['chamber', 5500]], ['sewerPipe', '하수관', 'Sewer pipe', ['sewer', 5500]],
    ['manhole', '맨홀 아래', 'Manhole', ['manhole', 5500]], ['trunkSewer', '하수 간선', 'Trunk sewer', ['trunk', 5500]],
    ['combined', '빗물 합류', 'Combined sewer', ['combined', 5500]], ['interceptor', '차집관로', 'Interceptor', ['interceptor', 5500]],
    ['pumpStation', '중계펌프장', 'Pumping station', ['pump', 5500]], ['barScreen', '유입 스크린', 'Bar screen', ['screen', 5500]],
    ['grit', '침사지', 'Grit chamber', ['grit', 5500]], ['clarifier1', '1차 침전지', 'Primary clarifier', ['clarifier1', 5500]],
    ['aeration', '포기조', 'Aeration tank', ['aeration', 5500]], ['clarifier2', '2차 침전지', 'Secondary clarifier', ['clarifier2', 5500]],
    ['uv', '소독조', 'UV disinfection', ['uv', 5500]], ['outfall', '방류구', 'Outfall', ['outfall', 5500]]);
  // the course as stretches of one look: id, Korean name, English name, look, length, place number
  const COURSE = [];
  const PLACE_K = 0.8;                              // (v57) every place 20% shorter than the lengths above
  PLACES.forEach((p, k) => { for (const [look, len] of p.slice(3)) COURSE.push([p[0], p[1], p[2], look, Math.round(len * PLACE_K), k]); });
  const STARTS = []; let LAP = 0;
  for (const s of COURSE) { STARTS.push(LAP); LAP += s[4]; }
  const S2_I = COURSE.findIndex((st) => st[5] === STAGE2), S2_X = STARTS[S2_I];       // where stage 2 starts in the lap
  const stageOf = (lx) => (lx >= S2_X ? 2 : 1);
  const stageSpan = (st) => (st === 2 ? [S2_X, LAP] : [0, S2_X]);
  const CHAR_NAMES = LANG === 'ko' ? { tardigrade: '물곰', lacto: '유산균', paramecium: '짚신벌레', amoeba: '아메바', daphnia: '물벼룩', pillbug: '공벌레', ladybug: '무당벌레', jelly: '아기 해파리', sub: '초소형 잠수정', phage: '박테리오파지' }
    : { tardigrade: 'Water Bear', lacto: 'Lactobacillus', paramecium: 'Paramecium', amoeba: 'Amoeba', daphnia: 'Water Flea', pillbug: 'Pill Bug', ladybug: 'Ladybug', jelly: 'Baby Jellyfish', sub: 'Mini Sub', phage: 'Phage' };
  const PTS = { vitC: 10, o2: 10, iron: 30, omega: 30, fiber: 30, atp: 50, multi: 100, heal: 0, drop: 10, soap: 30 };
  // (v49) the score, as in Cookie Run: what you eat (PTS) + the distance run (1 point a metre, a metre being 10 units)
  // + the mini-games (each its own points). The parts are kept for the end card
  const M_UNITS = 10, OB_PTS = { perfect: 50, early: 25, late: 25 };
  // (v49) a mini-game's points go into the score when it ends (until then they are its own, shown on its card)
  const bankGame = (g) => { if (g && g.gain) { G.score = Math.max(0, G.score + g.gain); g.gain = 0; } };
  // (v57) combos in every mini-game: a game of a few tries (baseball, the shoot-out, the jackpot, memory, the shell
  // game) pays each success in a row 20% more of its points for each one before it in the row (the 2nd +20%, the 3rd
  // +40%, ...); a game of many quick hits (the orbit stage, the germ game) multiplies like the rhythm stage (up to 2.6
  // times at 40 in a row); the poop tower and the bird shoot had theirs already
  const COMBO_K = 0.2, comboPts = (base, k) => Math.round(base * (1 + COMBO_K * Math.max(0, k - 1)));
  const scoreParts = () => ({ dist: G.distM, items: G.itemPts, games: G.score - G.distM - G.itemPts });
  const mod = (a, n) => ((a % n) + n) % n;
  const PILOT_HUGE = 0.58;
  // the booster: every 100 things eaten (anything but a heal), 5 seconds at three times the speed, untouchable (a second's grace after)
  const BOOST_N = 100, BOOST_T = 5, BOOST_K = 3, BOOST_GRACE = 1.0;
  const boostNeed = () => BOOST_N + 50 * (G.boosts || 0);      // (v47) 100, then 120, 140, ... (late on the coins come thick) (v57: 100, 150, 200, ...)
  const MAG_R = 80;                                  // boosting, a magnetic field round the body pulls in what comes this near
  const FIRE_STYLE = Math.max(1, Math.min(5, +(qs.get('fire') || 5)));      // the look of the booster's fire (5: rainbow starlight, chosen)

  // ---------------------------------------------------------------- pictures: decoded only when near (memory)
  // window.__ASSETS = { manifest, files: { name: base64 } } (everything in the page) or window.__MANIFEST plus the
  // picture files next to the page in assets/
  const ASSETS = window.__ASSETS || null;
  const M = ASSETS ? ASSETS.manifest : window.__MANIFEST;
  const BASE = 'assets/';
  const bmp = {}, pending = {};
  function loadImage(src) { return new Promise((res, rej) => { const im = new Image(); im.onload = () => res(im); im.onerror = () => rej(new Error('load ' + src)); im.src = src; }); }
  function b64blob(b64, type) { const bin = atob(b64); const u = new Uint8Array(bin.length); for (let i = 0; i < bin.length; i++) u[i] = bin.charCodeAt(i); return new Blob([u], { type }); }
  function decode(fn) {
    if (bmp[fn]) return Promise.resolve(bmp[fn]);
    if (pending[fn]) return pending[fn];
    pending[fn] = (async () => {
      let im;
      if (ASSETS) {
        const blob = b64blob(ASSETS.files[fn], 'image/webp');
        if (window.createImageBitmap) im = await createImageBitmap(blob);
        else { const u = URL.createObjectURL(blob); im = await loadImage(u); }
      } else {
        const el = await loadImage(BASE + fn);
        im = window.createImageBitmap ? await createImageBitmap(el) : el;
      }
      bmp[fn] = im; delete pending[fn];
      return im;
    })().catch((e) => { delete pending[fn]; throw e; });
    return pending[fn];
  }
  const rimCache = {};
  function release(fn) {
    const b = bmp[fn]; if (b) { if (b.close) b.close(); delete bmp[fn]; }
    for (const k of Object.keys(rimCache)) if (rimCache[k].f === fn) delete rimCache[k];      // (its obstacles' red rims)
  }
  const themeFiles = (t) => { const th = M.themes[t]; return [th.far, th.mid, th.fx].filter(Boolean); };
  // what is kept decoded (a background picture is 14-21 MB once decoded, so not many at a time): the look you are in,
  // the one you just left while it fades, and the looks ahead as far as about MEM_LEAD seconds of running at the speed
  // now (three times that when a boost is on or near); the booster fire only near and during a boost; the baseball
  // pictures only near the jejunum and in its stage. The rest let go. Called on each new place and twice a second.
  const MEM_LEAD = 4, MEM_MIN = 1200;
  const JEJ = PLACES.findIndex((p) => p[0] === 'jejunum');
  function manageThemes() {
    if (G.station < 0) return;
    const i = G.station, s = stationAt(G.x), want = new Set([COURSE[i][3]]);
    if (G.prevTheme && G.fade < 1) want.add(G.prevTheme);
    const boosty = G.boost > 0 || G.boostHeld > 0 || G.o2n >= boostNeed() - 10;
    const reach = Math.max(MEM_MIN, G.v * (boosty ? BOOST_K : 1) * MEM_LEAD + NW);
    for (let k = i + 1, n = 0; n < COURSE.length; k++, n++) {          // the looks starting within reach
      const kk = k % COURSE.length, d = (k >= COURSE.length ? LAP : 0) + STARTS[kk] - s.lx;
      if (d > reach) break;
      want.add(COURSE[kk][3]);
    }
    const files = new Set(['common.webp']);
    for (const t of want) for (const f of themeFiles(t)) files.add(f);
    if (G.boost > 0 || G.boostHeld > 0 || G.o2n >= boostNeed() - 25) files.add('fx_fire.webp');
    if (G.magR || G.boost > 0 || G.boostHeld > 0 || G.o2n >= boostNeed() - 25) files.add('fx_mag.webp');       // (v61) the magnet's whirl
    const jx = STARTS[COURSE.findIndex((st) => st[5] === JEJ)], dj = ((jx - s.lx) % LAP + LAP) % LAP;
    const nearBB = G.bb || dj < Math.max(2500, G.v * 8);
    if (nearBB) { files.add('bb_field.webp'); files.add('bb.webp'); files.add(`bat_${G.char}.webp`); }
    const near = (id) => { const d = ((STARTS[COURSE.findIndex((st) => st[0] === id)] - s.lx) % LAP + LAP) % LAP; return d < Math.max(2500, G.v * 8); };
    if (G.wm || near('spleen')) { files.add('wm_field.webp'); files.add('wm.webp'); }       // the germ game's, near the spleen
    if (G.mem || near('hippocampus')) files.add('mem.webp');                                // the memory game's
    if (G.pk || near('manhole')) { files.add('pk_field.webp'); files.add('pk.webp'); files.add(`bat_${G.char}.webp`); }      // (v44) the penalty shoot-out's (v46: the runner kicks)
    if (G.sl || near('toiletBowl')) files.add('sl.webp');                                   // (v44) the toilet jackpot's
    if (G.yb || near('combined')) { files.add('yb.webp'); files.add('pk.webp'); files.add('sl.webp'); }     // (v52) the shell game's (its dealer, its poop)
    if (G.tw || near('clarifier1')) files.add('tw.webp');                                    // (v53) the poop tower's
    if (G.ar || near('outfall')) { files.add('ar.webp'); files.add('ar_field.webp'); files.add('ar_bird.webp'); files.add(`bat_${G.char}.webp`); }   // (v53) the archery's (v55: the bird)
    const dc = ((S2_X - s.lx) % LAP + LAP) % LAP;            // the flush cut scene's pictures, near the end of the body
    if (G.cut || G.cutTail || dc < Math.max(2500, G.v * 8)) files.add('cut_flush.webp');
    if (STAGES.bb && !CAPTURE) { if (nearBB) { SND.fetchSong(STAGES.bb).catch(() => {}); if (SND.ctx) SND.prepare(STAGES.bb).catch(() => {}); } else SND.release(STAGES.bb); }
    for (const [k, on] of [['wm', !!G.wm || near('spleen')], ['mem', !!G.mem || near('hippocampus')]]) {     // (v42) the germ and memory games' music
      if (!STAGES[k] || CAPTURE) continue;
      if (on) { SND.fetchSong(STAGES[k]).catch(() => {}); if (SND.ctx) SND.prepare(STAGES[k]).catch(() => {}); } else SND.release(STAGES[k]);
    }
    for (const f of files) decode(f).catch(() => {});
    if (!PRELOAD) for (const f of Object.keys(bmp)) if (!files.has(f) && /^(th_|fx_fire|fx_mag|bb|bat_|cut_|wm|mem|pk|sl)/.test(f)) release(f);
    manageSongs();
  }

  // ---------------------------------------------------------------- screen
  // the canvas is exactly the screen's pixels (no scaling by the browser: sharp). Held upright, the game is drawn
  // turned a quarter inside the canvas (the phone is then simply held sideways)
  const cv = document.getElementById('c'), ctx = cv.getContext('2d', { alpha: false });
  const wrap = document.getElementById('wrap');
  let NW = 390, NWf = 390, CSS = 1, RS = 1, GW = 0, GH = 0, rot = false;
  function resize() {
    const dpr = window.devicePixelRatio || 1;
    rot = innerHeight > innerWidth * 1.05;
    const w = rot ? innerHeight : innerWidth, h = rot ? innerWidth : innerHeight;
    NW = Math.max(300, Math.min(420, Math.round(NH * w / h)));
    CSS = Math.min(w / NW, h / NH);
    GW = Math.round(NW * CSS * dpr); GH = Math.round(NH * CSS * dpr);
    RS = GH / NH; NWf = GW / RS;
    const cw = rot ? GH : GW, ch = rot ? GW : GH;
    cv.width = cw; cv.height = ch;
    cv.style.width = `${cw / dpr}px`; cv.style.height = `${ch / dpr}px`;
    cv.style.left = `${Math.round((innerWidth * dpr - cw) / 2) / dpr}px`;
    cv.style.top = `${Math.round((innerHeight * dpr - ch) / 2) / dpr}px`;
    wrap.style.width = `${NW * CSS}px`; wrap.style.height = `${NH * CSS}px`;
    document.documentElement.style.setProperty('--u', `${CSS}px`);     // one unit in CSS pixels (for the labels)
    wrap.style.transform = `translate(-50%, -50%)${rot ? ' rotate(90deg)' : ''}`;
    ctx.imageSmoothingEnabled = true; ctx.imageSmoothingQuality = 'high';
    if (G.mode === 'title') renderTitle(); else if (G.mode === 'lobby') renderLobby(); else if (M && G.mode && G.mode !== 'select') render();
  }
  addEventListener('resize', resize);
  // transforms: world units, or the landscape picture's own pixels (for seamless strips)
  function world() { if (rot) ctx.setTransform(0, RS, -RS, 0, GH, 0); else ctx.setTransform(RS, 0, 0, RS, 0, 0); }
  function device() { if (rot) ctx.setTransform(0, 1, -1, 0, GH, 0); else ctx.setTransform(1, 0, 0, 1, 0, 0); }

  let GA = 1;                                        // what is drawn now is drawn this much (the HUD fading in the cut scene)
  let curO = null;                                   // (tests: the obstacle being drawn, for window.__drawLog)
  function spr(name, x, y, alpha = 1, w = null, h = null) {
    const s = M.sprites[name]; if (!s) return;
    const im = bmp[s.f]; if (!im) return;
    const a = alpha * GA;
    if (window.__drawLog && /^(ch|ob|hz)_/.test(name)) { const m = ctx.getTransform(); window.__drawLog.push([name, x, y, w ?? s.w, h ?? s.h, a, m.a, m.b, m.c, m.d, m.e, m.f, curO]); }
    if (a !== 1) ctx.globalAlpha = a;
    ctx.drawImage(im, s.r[0], s.r[1], s.r[2], s.r[3], x, y, w ?? s.w, h ?? s.h);
    if (a !== 1) ctx.globalAlpha = GA;
  }
  const SW = (n) => M.sprites[n].w, SH = (n) => M.sprites[n].h;

  // ---------------------------------------------------------------- random (deterministic per run)
  function rng(seed) { let s = seed >>> 0 || 1; return () => { s ^= s << 13; s >>>= 0; s ^= s >> 17; s ^= s << 5; s >>>= 0; return s / 4294967296; }; }

  // ---------------------------------------------------------------- course lookups
  function stationAt(x) {
    const lap = Math.floor(x / LAP), lx = x - lap * LAP;
    let i = 0; while (i + 1 < COURSE.length && STARTS[i + 1] <= lx) i++;
    return { i, lap, lx, st: COURSE[i] };
  }
  const themeAt = (x) => COURSE[stationAt(x).i][3];

  // ---------------------------------------------------------------- the run
  const G = {};
  const loadBest = () => { try { return +(localStorage.getItem('bodyrun.best') || 0); } catch (e) { return 0; } };     // (v57) the best so far, for the HUD
  function newRun(charName, opts = {}) {
    Object.assign(G, {
      mode: 'play', t: 0, x: 0, v: V0, slow: 1, hp: HP_MAX, score: 0, eaten: 0, hits: 0, dist: 0, distM: 0, itemPts: 0,
      y: 0, vy: 0, jumps: 0, onGround: true, slide: false, slideHeld: false, fastFall: false,
      invul: 0, nudge: 0, char: charName, obs: [], items: [], pops: [], puffs: [],
      genX: 520, genStation: undefined, lastGate: -1e9, R: rng(12345), runT: 0, nextHealT: HEAL_EVERY, station: -1, theme: COURSE[0][3], prevTheme: null, fade: 1, banner: 0, lapShown: 0,
      blinkAt: -1, blinkR: rng(4242), vt: 0, rh: null, orb: null, bb: null, wm: null, mem: null, pk: null, sl: null, yb: null, tw: null, ar: null, slLap: -1, cut: null, cutTail: null, bounce: false, pitObj: null,
      o2n: 0, boost: 0, boostT0: -9, boostHeld: 0, boosts: 0, fire: [], fxR: rng(9191), best0: loadBest(),
      intro: [[1950, 'spike'], [3650, 'drop'], [5420, 'pit'], [7250, 'shot'], [9130, 'door']],
    });
    // (v60) the start items; getting up again; the coins paid; the first run's lessons
    Object.assign(G, { opts, x2: !!opts.x2, magR: opts.mag ? ITEM_MAG_R : 0, hpMax: HP_MAX + (opts.hp ? 20 : 0), revived: false, coinsPaid: 0, recKept: false, timeKept: 0, final: 0, coinsAdd: 0 });
    G.hp = G.hpMax;
    G.tut = tutWanted() ? { on: true, tipsOn: true, done: {}, wait: null, tips: {}, t0: 0 } : null;
    pressed.jump = false;
  }

  // ---------------------------------------------------------------- spawning: patterns laid ahead of the player
  function obstacleSprite(theme, kind) {
    const list = (M.themes[theme].obs[kind] || []);
    if (!list.length) return null;
    return list[Math.floor(G.R() * list.length)];
  }
  function addObs(x, kind, theme, as = null) {
    const name = obstacleSprite(theme, kind);
    if (!name) return null;
    const w = SW(name), h = SH(name);
    const y = kind === 'hang' ? HANG_BOTTOM - h : kind === 'float' ? FLOAT_BOTTOM - h : GY + 2 - h;
    const o = { x, y, w, h, name, kind: as || kind, hit: false };
    G.obs.push(o);
    return o;
  }
  // a cell bobbing between the slide height (slide under it) and the floor (jump over it)
  function addBobber(x, theme) {
    const o = addObs(x, 'float', theme, 'bob'); if (!o) return null;
    o.bob = { y0: FLOAT_BOTTOM - o.h, amp: GY + 2 - FLOAT_BOTTOM, w: 2 * Math.PI / (1.5 + G.R() * 0.6), ph: G.R() * 6.28 };
    o.y = o.bob.y0;
    return o;
  }
  // a germ swimming at you (on the floor: jump; at slide height: slide); it starts once it is on the screen
  function addSwimmer(x, theme, low, d) {
    const o = addObs(x, 'float', theme, 'swim'); if (!o) return null;
    o.vx = 60 + 50 * d;
    if (low) o.y = GY + 2 - o.h;
    o.low = low;
    return o;
  }
  function moveObs(dt) {
    const cam = G.x - PX;
    for (const o of G.obs) {
      if (o.vx && o.x - cam < NWf + 4) o.x -= o.vx * dt;
      if (o.bob) o.y = o.bob.y0 + o.bob.amp * (0.5 - 0.5 * Math.cos(o.bob.w * G.t + o.bob.ph));
    }
    moveHazards(dt);
  }
  // ---------------------------------------------------------------- v19 hazards: holes, doors, drops, spikes, shots
  // what each look has: drop (mucus / bile / a blood clot / clear fluid), spike (a polyp / a calcified plaque / a nerve
  // thorn / a crystal), door (a valve's cusps in the heart and vessels, a sphincter's lips in the gut and the organs'
  // small vessels; none in the brain or the clear parts of the eye)
  const GI_L = new Set(['eso', 'stomach', 'duodenum', 'gut', 'ileum', 'cecum', 'colon', 'rectum', 'anus', 'villus']);
  const VES_L = new Set(['artery', 'vein', 'ivc', 'atrium', 'ventricle', 'pulmart', 'pulmvein', 'latrium', 'lventricle', 'carotid', 'vertebral', 'renalart', 'efferent', 'sma']);
  const BRAIN_L = new Set(['arach', 'pyramidal', 'hippo', 'purkinje', 'fibres', 'temporal', 'parietal', 'occipital', 'medulla', 'opticnerve']);
  const EYE_L = new Set(['retina', 'vitreous', 'lens', 'iris', 'cornea']);
  // stage 2 (all under water): in the building a falling wad of paper, limescale, a cleaner tablet flying; in the sewers
  // sludge, a broken rebar, a nut; at the treatment works a floc, a shard of grit, a pebble
  const S2_HOUSE = new Set(['toilet', 'trap', 'stack', 'drain']);
  const S2_SEWER = new Set(['septic', 'chamber', 'sewer', 'manhole', 'trunk', 'combined', 'interceptor', 'pump']);
  const S2_WORKS = new Set(['screen', 'grit', 'clarifier1', 'aeration', 'clarifier2', 'uv', 'outfall']);
  const S2_L = new Set([...S2_HOUSE, ...S2_SEWER, ...S2_WORKS]);
  function hzFam(look) {
    if (S2_HOUSE.has(look)) return { drop: 'paper', spike: 'scale', door: null, shot: 'tablet' };
    if (S2_SEWER.has(look)) return { drop: 'sludge', spike: 'rebar', door: null, shot: 'nut' };
    if (S2_WORKS.has(look)) return { drop: 'floc', spike: 'grit', door: null, shot: 'pebble' };
    if (GI_L.has(look)) return { drop: look === 'duodenum' ? 'bile' : 'mucus', spike: 'flesh', door: 'sph' };
    if (look === 'liver' || look === 'gallbladder') return { drop: 'bile', spike: 'flesh', door: 'sph' };
    if (VES_L.has(look)) return { drop: 'blood', spike: 'plaque', door: 'valve' };
    if (BRAIN_L.has(look)) return { drop: 'clear', spike: 'neuro', door: null };
    if (EYE_L.has(look)) return { drop: 'clear', spike: 'crystal', door: look === 'iris' ? 'sph' : null };
    if (look === 'lung' || look === 'bronchiole') return { drop: 'mucus', spike: 'flesh', door: 'sph' };
    return { drop: 'blood', spike: 'flesh', door: 'sph' };
  }
  const PIT_EDGE = PW * 0.6;                       // standing this far over a hole's edge you still stand
  const PIT_HIT = 20;                              // falling in costs more than a bump
  const PIT_DEPTH = 34, PIT_HOLD = 0.22, PIT_SLOW = 0.3;   // (v47) how deep you sink; how long you stay at the bottom; how slow you go in it
  // (v51) the pictures fitted to what hurts. The characters are drawn much bigger than their boxes, so passing a thing
  // right could still look like touching it. Sliding: the four tall characters (phage, jelly, daphnia, sub) still stood
  // 16-17 over the floor at 0.62 of their height, into what hangs at slide height (its picture down to 15.7, its red rim
  // to 14.9); their slide picture is now at most SLIDE_MAXH tall (the others are lower anyway). (Drawing what is slid
  // under higher was tried: the short characters, running, were then hurt by it with a gap between the pictures.)
  // The triple jump: a tower's picture stood 9 over what hurts; it is drawn smaller, from the floor, so its top comes to
  // about 1.4 over what hurts, like everything else
  const SLIDE_MAXH = 14.5, TRIM = { huge: 7.8 };
  const slideH = (h) => Math.min(h * 0.62, SLIDE_MAXH);
  const DROP_Y0 = 9, DROP_G = 900;                 // a drop hangs with its top here (behind the ceiling band), falls this fast
  const DOOR_UP = 131, DOOR_B = 30;                // how far a door's hanging lip draws up into the ceiling; its standing lip's rise
  const smooth3 = (k) => k * k * (3 - 2 * k);
  // a hole in the floor (w units wide)
  function addPit(x, w) { const o = { x, y: GY, w, h: 0, kind: 'pit', hit: false, seed: Math.floor(G.R() * 1000) }; G.obs.push(o); return o; }
  function pitAt(x) {
    for (const o of G.obs) if (o.kind === 'pit' && x > o.x + PIT_EDGE && x < o.x + o.w - PIT_EDGE) return o;
    return null;
  }
  // a door: a lip hanging from the ceiling and one standing on the floor take turns closing (one beat each). which: the
  // one closed when you are expected to arrive ('b': jump over the standing lip, 't': slide under the hanging one)
  function doorExt(o, t) {
    const u = mod((t + o.ph) / o.P, 1);
    let b = 0, tp = 0;
    if (u < 0.06) b = smooth3(u / 0.06); else if (u < 0.42) b = 1; else if (u < 0.48) b = 1 - smooth3((u - 0.42) / 0.06);
    else if (u < 0.5) b = 0; else if (u < 0.56) tp = smooth3((u - 0.5) / 0.06); else if (u < 0.92) tp = 1; else if (u < 0.98) tp = 1 - smooth3((u - 0.92) / 0.06);
    return [b, tp];
  }
  // under water (stage 2) the speed carried in is cut by 30% and climbs from there at the same rate as ever (G.wPen: the
  // 30% of the speed it came in at, held while in the water)
  const wPen = () => (inWater() ? G.wPen || 0 : 0);
  function curSpeed() { return G.orb || G.bb || G.wm || G.mem || G.pk || G.sl || G.yb || G.tw || G.ar || G.cut ? 0 : G.rh ? G.rh.speed : (G.v - wPen()) * (0.3 + 0.7 * G.slow) * (G.boost > 0 ? BOOST_K : 1) * pitSlow(); }
  // (v47) in a hole: slowed as you sink (you go down into it, not along to its far wall), stopped at the bottom
  function pitSlow() { return G.pitObj && G.y < 0 && !G.bounce ? (G.pitHoldT ? 0 : PIT_SLOW) : 1; }
  function arriveIn(dist, v) { return ACC > 0 ? (-v + Math.sqrt(v * v + 2 * ACC * Math.max(0, dist))) / ACC : dist / v; }
  function aimDoor(o) {                              // set its beat so the wanted lip is half way through its hold on arrival
    const ta = G.t + arriveIn(o.x + o.w / 2 - G.x, curSpeed());
    o.ph = mod((o.which === 'b' ? 0.24 : 0.74) * o.P - ta, o.P);
  }
  function addDoor(x, fam, P, which) {
    const nt = `hz_gate_${fam}_t`, nb = `hz_gate_${fam}_b`;
    const w = Math.max(SW(nt), SW(nb));
    const o = { x, y: 0, w, h: 0, kind: 'door', nt, nb, P, which, ph: 0, hit: false, eb: 0, et: 0, aimed: false };
    aimDoor(o); G.obs.push(o);
    return o;
  }
  // a drop on the ceiling: it wobbles, lets go and lands tLand seconds before you get there, as a puddle to jump
  function addDrop(x, fam, tLand) {
    const nd = `hz_drop_${fam}`, np = `hz_puddle_${fam}`;
    const o = { x, y: DROP_Y0, w: SW(np), h: SH(nd), kind: 'drop', name: nd, nd, np, st: 'hang', vy: 0, tLand, hit: false, landT: -9 };
    o.tFall = Math.sqrt(2 * (GY + 2 - SH(nd) - DROP_Y0) / DROP_G);
    G.obs.push(o);
    return o;
  }
  // a spike under the floor: the floor shakes over it, then it shoots up tPop seconds before you get there
  function addSpike(x, fam, tall, tPop, tWarn) {
    const name = `hz_spike_${fam}_${tall ? 't' : 's'}`;
    const o = { x, y: GY + 2, w: SW(name), h: SH(name), kind: 'spike', name, tall, st: 'hidden', e: 0, tPop, tWarn, hit: false, popT: -9 };
    G.obs.push(o);
    return o;
  }
  // an antibody flying at you (low: jump; high: slide), a warning at the screen's edge first; it starts on the screen
  function addShot(x, low, vx, kind) {
    const name = kind ? 'hz_shot_' + kind : 'hz_shot';
    const o = { x, y: low ? GY + 1 - SH(name) : FLOAT_BOTTOM - SH(name), w: SW(name), h: SH(name), kind: 'shot', name, low, fly: vx, hit: false, spin: G.R() * 6.28, moving: false };
    G.obs.push(o);
    return o;
  }
  // the boxes something hurts with, in world units (none for a hole: it is the falling)
  function obsBoxes(o) {
    if (o.kind === 'pit') return [];
    if (o.kind === 'door') {
      const out = [];
      if (o.et > 0.02) { const s = M.sprites[o.nt], hb = s.hb, x0 = o.x + (o.w - s.w) / 2, y0 = HANG_BOTTOM - s.h - DOOR_UP * (1 - o.et); out.push([x0 + hb[0], y0 + hb[1], x0 + hb[2], y0 + hb[3]]); }
      if (o.eb > 0.02) { const s = M.sprites[o.nb], hb = s.hb, x0 = o.x + (o.w - s.w) / 2, y0 = GY + 4 - DOOR_B * o.eb; out.push([x0 + hb[0], y0 + hb[1], x0 + hb[2], Math.min(GY + 2, y0 + hb[3])]); }
      return out;
    }
    if (o.kind === 'spike') {
      if (o.e <= 0.05) return [];
      const hb = M.sprites[o.name].hb;
      return [[o.x + hb[0], o.y + hb[1], o.x + hb[2], Math.min(GY + 2, o.y + hb[3])]];
    }
    const nm = o.kind === 'drop' ? o.name : o.name, s = M.sprites[nm], hb = s.hb;
    const ox = o.kind === 'drop' && o.st !== 'land' ? o.x + (o.w - s.w) / 2 : o.x;
    return [[ox + hb[0], o.y + hb[1], ox + hb[2], o.y + hb[3]]];
  }
  function moveHazards(dt) {
    const cam = G.x - PX;
    for (const o of G.obs) {
      const dx = o.x - G.x, vEff = curSpeed();
      if (o.kind === 'door') {
        if (!o.aimed && o.x - cam < NWf + 30) { aimDoor(o); o.aimed = true; }     // set its beat for good just before it shows
        [o.eb, o.et] = doorExt(o, G.t);
      } else if (o.kind === 'drop') {
        if (o.st === 'hang') {
          if (dx < vEff * (o.tLand + o.tFall + 0.45)) o.wob = (o.wob || 0) + dt;
          if (dx < vEff * (o.tLand + o.tFall)) { o.st = 'fall'; o.vy = 0; }
        } else if (o.st === 'fall') {
          o.vy += DROP_G * dt; o.y += o.vy * dt;
          if (o.y + SH(o.nd) >= GY + 2) {
            o.st = 'land'; o.name = o.np; o.h = SH(o.np); o.y = GY + 2 - o.h; o.landT = G.t;
            for (let i = 0; i < 4; i++) G.puffs.push({ x: o.x + o.w / 2 + (i - 1.5) * 5, y: GY - 2 - G.R() * 3, r: 1.4 + G.R() * 1.2, t: G.t });
          }
        }
      } else if (o.kind === 'spike') {
        if (o.st === 'hidden' && dx < vEff * (o.tPop + o.tWarn)) { o.st = 'warn'; o.warnT = G.t; }
        if (o.st === 'warn' && dx < vEff * o.tPop) { o.st = 'up'; o.popT = G.t; }
        if (o.st === 'up') o.e = Math.min(1, (G.t - o.popT) / 0.09);
        o.y = GY + 2 - o.h * o.e;
      } else if (o.kind === 'shot') {
        if (o.x - cam < NWf + 4) o.moving = true;
        if (o.moving) { o.x -= o.fly * dt; o.spin += dt * 9; }       // (not o.vx: moveObs would move it twice)
      }
    }
  }
  // falling into a hole: it hurts, and you are thrown back out to land just past it
  function fallOut(p) {
    G.bounce = true; G.pitHoldT = 0;                         // (first: the speed it is thrown out at is the full one)
    if (G.invul <= 0 && !(G.boost > 0)) {
      G.hits++; G.hp = Math.max(0, G.hp - PIT_HIT); SND.play('hit');
      G.lastHit = { kind: 'pit', name: 'pit', dx: Math.round(p.x - G.x), y: Math.round(G.y), vy: Math.round(G.vy), slide: false, jumps: G.jumps, v: Math.round(G.v), w: Math.round(p.w) };
    }
    G.invul = INVUL;
    const vx = curSpeed();
    const T = Math.max(0.3, (p.x + p.w + 8 - G.x) / vx);
    G.vy = (0.5 * GRAV * T * T - G.y) / T; G.jumps = 3; G.bounce = true;
  }

  function addItem(x, y, kind) { G.items.push({ x, y, kind, taken: false, ph: G.R() * 6.28 }); }
  // coins along the path of a jump starting at xs: n = 1, 2 or 3 jumps (each next one near the top of the last)
  function jumpArc(xs, v, coin, n = 1, special = null) {
    let y = 0, vy = JUMP, x = xs, t = 0, j = 1, lastX = -99, top = null;
    while (t < 3) {
      const dt = 1 / 120; t += dt;
      if (j < n && vy < (n === 3 ? 60 : 90)) { vy = j === 1 ? JUMP2 : JUMP3; j++; }
      vy -= GRAV * dt; y += vy * dt; x += v * dt;
      if (y > MAXY) { y = MAXY; if (vy > 0) vy = 0; }
      if (y <= 0) break;
      if (!top || y > top.y) top = { x, y };
      if (x - lastX >= 15) { addItem(x, GY - y - 11, coin); lastX = x; }
    }
    if (special && top) addItem(top.x, n === 3 ? GY - top.y - 11 : GY - top.y - 30, special);
  }
  function coinRow(x0, n, y, coin) { for (let i = 0; i < n; i++) addItem(x0 + i * 15, y, coin); }

  function spawnAhead() {
    const horizon = G.x + NW + 200;
    while (G.genX < horizon) {
      { const lx = mod(G.genX, LAP), q0 = S2_X - CUT_FACE - Math.max(90, curSpeed() * CUT_TJ * 1.2) - CUT_CLEAR;   // the cut scene's stretch
        const q1 = S2_X + Math.max(CUT_AFTER, G.v * 1.5);            // (and after it, time to swim up from the bottom)
        // (v42: at least a unit on: far into a long lap the step past it can be smaller than the float's precision at
        // these x values, and genX would not move: the loop went on for ever, the game hung)
        if (lx > q0 && lx < q1) { G.genX += Math.max(1, q1 - lx); continue; } }
      const theme = themeAt(G.genX), th = M.themes[theme], fam = hzFam(theme);
      const coin = th.coin, special = th.special;
      // how hard: from the speed (0 at the start .. 1 at 460/s, about 5 minutes in), then a little more up to 900
      const v = S2_L.has(theme) ? G.v - (G.wPen || 0) : G.v;          // (under water: the speed there)
      const d = Math.min(1, Math.max(0, (v - V0) / 300)), d2 = Math.min(1, Math.max(0, (v - 460) / 440));
      const gapT = 1.45 - 0.65 * d - 0.15 * d2;          // seconds between patterns
      const R = G.R;
      if (S2_L.has(theme)) {                                   // stage 2: under water
        const used = spawnSwim(G.genX, theme, fam, coin, special, v, d, d2, R);
        if (G.runT >= G.nextHealT) { addItem(G.genX + used / 2, 50 + R() * 70, 'heal'); G.nextHealT = G.runT + HEAL_EVERY - HEAL_JIT + R() * 2 * HEAL_JIT; }
        const gap = v * Math.max(gapT, 0.9) * (0.85 + 0.3 * R());     // (swimming up or down takes longer than a jump)
        // (v51) twice the things to eat under water: a run of six coins in the open water between two patterns (in a
        // line or a low arc, at any height one swims at)
        { const n = 6, gx0 = G.genX + Math.max(used, 60) + gap / 2 - 37.5, gy = 45 + R() * 80, arc = R() < 0.5 ? 0 : 8 + R() * 10;
          for (let i = 0; i < n; i++) addItem(gx0 + i * 15, gy - arc * Math.sin(Math.PI * i / (n - 1)), coin); }
        G.genX += Math.max(used, 60) + gap;
        continue;
      }
      // weights for the next pattern
      const W = [['rest', 0.14 - 0.08 * d], ['low', 0.28], ['float', 0.15], ['hang', 0.08 + 0.06 * d], ['tall', 0.08 + 0.08 * d], ['lowlow', 0.04 + 0.08 * d], ['lowfloat', 0.02 + 0.06 * d],
        // a triple jump starts ~0.6 s before the tower: above ~480/s that is off the screen, so no towers then
        ['huge', v < 480 ? 0.03 + 0.05 * d : 0], ['sky', v < 480 ? 0.03 : 0],
        // moving ones and quick combinations
        ['bob', 0.06 + 0.12 * d], ['swim', 0.06 + 0.12 * d], ['slidejump', 0.03 + 0.08 * d], ['jumpslide', 0.03 + 0.08 * d], ['lowtall', 0.02 + 0.06 * d],   // (v48: bob, swim 1.5x)
        // v19: holes, doors, drops, spikes, shots: a few from the start, more and harder as it speeds up
        ['pit', 0.05 + 0.10 * d + 0.06 * d2], ['door', fam.door ? 0.06 + 0.12 * d + 0.07 * d2 : 0], ['drop', 0.05 + 0.08 * d + 0.05 * d2],
        ['spike', 0.05 + 0.09 * d + 0.05 * d2], ['shot', 0.12 + 0.22 * d + 0.12 * d2]];        // (v38: shots twice as often; v48: shots, doors 1.5x more)
      let r = R() * W.reduce((a, b) => a + b[1], 0), pat = 'rest';
      for (const [p, w] of W) { if ((r -= w) <= 0) { pat = p; break; } }
      // the way into each new look is guarded: a gate of three in quick succession
      if (G.genStation !== undefined && theme !== G.genStation && G.genX - (G.lastGate || -1e9) > v * 12) { pat = 'gate'; G.lastGate = G.genX; }
      G.genStation = theme;
      // each new kind of hazard is first shown on its own, early on
      if (G.intro.length && G.genX > G.intro[0][0] && pat !== 'gate' && (G.intro[0][1] !== 'door' || fam.door)) pat = G.intro.shift()[1];
      if (window.__forcePat && pat !== 'gate') pat = window.__forcePat[Math.floor(R() * window.__forcePat.length)];   // (tests: only these)
      if (window.__patlog) window.__patlog[pat] = (window.__patlog[pat] || 0) + 1;
      const x = G.genX;
      const air = (2 * JUMP) / GRAV;                       // a single jump's time in the air
      let used = 0;
      const lead = () => v * (air * 0.42);                  // jump this far before an obstacle's middle
      if (pat === 'rest') {
        coinRow(x, 6, GY - 12, coin); used = 6 * 15;
      } else if (pat === 'low' || pat === 'lowlow') {
        const o = addObs(x + 40, 'low', theme);
        if (o) { jumpArc(o.x + o.w / 2 - lead(), v, coin, 1, R() < 0.25 ? special : null); used = o.w + 40; }
        if (pat === 'lowlow' && o) {
          const gap2 = Math.max(v * air * 1.15, 90);
          const o2 = addObs(o.x + gap2, 'low', theme);
          if (o2) { jumpArc(o2.x + o2.w / 2 - lead(), v, coin); used = gap2 + o2.w + 40; }
        }
      } else if (pat === 'tall') {
        const o = addObs(x + 40, 'tall', theme) || addObs(x + 40, 'low', theme);
        if (o) { jumpArc(o.x + o.w / 2 - v * (o.kind === 'tall' ? 0.45 : 0.42), v, coin, o.kind === 'tall' ? 2 : 1, R() < 0.4 ? special : null); used = o.w + 40 + v * 0.5; }
      } else if (pat === 'float' || pat === 'lowfloat') {
        let o = addObs(x + 40, 'float', theme);
        if (o) { coinRow(o.x - 20, Math.ceil((o.w + 40) / 15), GY - 7, coin); used = o.w + 60; }
        if (pat === 'lowfloat' && o) {
          const o2 = addObs(o.x + o.w + Math.max(v * 0.55, 70), 'low', theme);
          if (o2) { jumpArc(o2.x + o2.w / 2 - lead(), v, coin); used = o2.x - x + o2.w + 40; }
        }
      } else if (pat === 'huge') {
        // a towering one: only a triple jump clears it; an ATP on the top of the path
        const o = addObs(x + 40 + 0.45 * v, 'huge', theme) || addObs(x + 40, 'tall', theme);   // room to land from before and take off
        if (o) { const k = o.kind === 'huge'; jumpArc(k ? o.x - 10 - v * PILOT_HUGE : o.x + o.w / 2 - v * 0.45, v, coin, k ? 3 : 2, k ? 'atp' : null); used = o.w + 40 + v * (k ? 0.9 : 0.5); }
      } else if (pat === 'sky') {
        // a trail of coins up to the ceiling and an ATP at the top: for those who triple jump
        jumpArc(x + 20, v, coin, 3, 'atp'); used = v * 1.3;
      } else if (pat === 'hang') {
        const o = addObs(x + 40, 'hang', theme) || addObs(x + 40, 'float', theme);
        if (o) { coinRow(o.x - 20, Math.ceil((o.w + 40) / 15), GY - 7, coin); used = o.w + 60; }
      } else if (pat === 'bob') {
        const o = addBobber(x + 40, theme);
        if (o) { jumpArc(o.x + o.w / 2 - v * 0.333, v, coin); used = o.w + 60; }
      } else if (pat === 'swim') {
        const o = addSwimmer(x + 40, theme, R() < 0.5, d);
        if (o) used = o.w + 180;
      } else if (pat === 'slidejump' || pat === 'jumpslide' || pat === 'lowtall' || pat === 'gate') {
        // quick combinations: each next one is placed just where the move before it ends
        const seq = pat === 'slidejump' ? ['slide', 'low'] : pat === 'jumpslide' ? ['low', 'slide'] : pat === 'lowtall' ? ['low', 'tall'] : ['low', 'slide', 'low'];
        let at = x + 40, end = x;
        for (const k of seq) {
          if (k === 'slide') {
            const o = addObs(at, R() < 0.5 ? 'float' : 'hang', theme) || addObs(at, 'float', theme);
            if (!o) continue;
            coinRow(o.x - 15, Math.ceil((o.w + 30) / 15), GY - 7, coin);
            end = o.x + o.w; at = end + 20 + 0.3 * v;           // stand up, then jump for a following one
          } else if (k === 'low') {
            const o = addObs(at, 'low', theme); if (!o) continue;
            const c = o.x + o.w / 2;
            jumpArc(c - lead(), v, coin);
            end = c - lead() + v * air; at = end + 18 + 0.18 * v;  // where it lands; the next one after that
          } else {
            const o = addObs(at + 0.3 * v, 'tall', theme) || addObs(at, 'low', theme); if (!o) continue;
            const c = o.x + o.w / 2;
            jumpArc(c - v * (o.kind === 'tall' ? 0.45 : 0.42), v, coin, o.kind === 'tall' ? 2 : 1);
            end = c + 0.6 * v; at = end + 20;
          }
        }
        used = Math.max(60, end - x + 20);
      } else if (pat === 'pit') {
        // a hole: one jump over it; past ~3 minutes sometimes a wide one (a double jump), below the speed where they get blind
        const wide = d > 0.35 && v < 480 && R() < 0.45 * d;
        const w = wide ? v * (0.62 + 0.06 * d) : Math.min(170, Math.max(36, v * (0.22 + 0.2 * d + 0.05 * R())));
        const o = addPit(x + 40, w);
        jumpArc(o.x + w / 2 - v * (wide ? 0.47 : 0.35), v, coin, wide ? 2 : 1, R() < 0.3 ? special : null);
        used = 40 + w + v * 0.35;
      } else if (pat === 'door') {
        // a door beating faster as it speeds up
        const P = Math.max(0.95, 1.7 - 0.55 * d - 0.2 * d2);
        const o = addDoor(x + 50, fam.door, P, R() < 0.5 ? 'b' : 't');
        const c = o.x + o.w / 2;
        if (o.which === 'b') jumpArc(c - v * 0.3, v, coin); else coinRow(c - 30, 5, GY - 7, coin);
        used = 50 + o.w + 60;
      } else if (pat === 'drop') {
        const n = d > 0.5 && R() < 0.5 * d ? 2 : 1;
        let at = x + 40;
        for (let k = 0; k < n; k++) {
          const o = addDrop(at, fam.drop, Math.max(0.33, 0.62 - 0.25 * d - 0.05 * d2));
          jumpArc(o.x + o.w / 2 - lead(), v, coin);
          at = o.x + o.w / 2 - lead() + v * air + 18 + 0.25 * v;           // where that jump lands, then the next
        }
        used = at - x;
      } else if (pat === 'spike') {
        const n = d > 0.45 && R() < 0.5 * d ? 2 : 1;
        let at = x + 40;
        for (let k = 0; k < n; k++) {
          const o = addSpike(at, fam.spike, R() < 0.15 + 0.5 * d, Math.max(0.36, 0.62 - 0.22 * d - 0.05 * d2), 0.5 - 0.12 * d);
          jumpArc(o.x + o.w / 2 - lead(), v, coin);
          at = o.x + o.w / 2 - lead() + v * air + 18 + 0.22 * v;
        }
        used = at - x;
      } else if (pat === 'shot') {
        // where it meets you is about here (it waits off the screen and flies once on it)
        const vx = 110 + 120 * d + 60 * d2, shift = vx * (NWf + 4 - PX) / (v + vx);
        const n = d > 0.3 && R() < 0.65 * d ? (d2 > 0.2 && R() < 0.45 ? 3 : 2) : 1;     // (v38: pairs sooner, threes when fast)
        let meet = x + 40, low = R() < 0.5;
        for (let k = 0; k < n; k++) {
          addShot(meet + shift, low, vx, fam.shot);
          if (low) jumpArc(meet - v * 0.3, v, coin); else coinRow(meet - 30, 5, GY - 7, coin);
          meet += v * 0.75 + 30; low = !low;
        }
        used = meet - x;
      }
      // a heal now and then, a rare multivitamin
      if (G.runT >= G.nextHealT) { addItem(G.genX + used / 2, GY - 54, 'heal'); G.nextHealT = G.runT + HEAL_EVERY - HEAL_JIT + R() * 2 * HEAL_JIT; }
      else if (R() < 0.03) addItem(G.genX + used / 2, GY - 70, 'multi');
      G.genX += Math.max(used, 60) + v * gapT * (0.85 + 0.3 * R());
    }
    // forget what is far behind
    const cut = G.x - PX - 80;
    if (G.obs.length && G.obs[0].x + G.obs[0].w < cut) G.obs = G.obs.filter((o) => o.x + o.w >= cut);
    if (G.items.length > 200) G.items = G.items.filter((i) => i.x > cut);
  }

  // ---------------------------------------------------------------- input
  const pressed = { jump: false };
  const held = new Map();                                   // pointerId -> 'jump' | 'slide'
  // a touch on the screen -> world units (undoing the quarter turn when the game is shown turned)
  function toWorld(e) {
    const r = cv.getBoundingClientRect();
    const cx = (e.clientX - r.left) * cv.width / r.width, cy = (e.clientY - r.top) * cv.height / r.height;
    const X = rot ? cy : cx, Y = rot ? GH - cx : cy;
    return [X / RS, Y / RS];
  }
  // ---------------------------------------------------------------- debugging: skip to the next place (the button under the
  // pause button; a mini-game on ends there). Arriving starts what that place starts (the rhythm stage in the right
  // atrium, the orbit stage in the vertebral artery)
  const DEBUG_SKIP = true;                                 // while the game is being tuned; false takes the button away
  function skipPlace() {
    if (G.mode !== 'play') return;
    if (G.rh) { SND.spin(null); endRhythm(); }
    if (G.orb) endOrbit();
    if (G.bb) endBaseball();
    if (G.wm) endWhack();
    if (G.mem) endMemory();
    if (G.pk) endPK();
    if (G.sl) endSlot();
    if (G.yb) endYB();
    if (G.tw) endTW();
    if (G.ar) endAR();
    if (G.cut) cutDone();
    const s = stationAt(G.x), here = COURSE[s.i][5];
    let j = s.i, lap = s.lap;
    do { j++; if (j >= COURSE.length) { j = 0; lap++; } } while (COURSE[j][5] === here);
    G.x = lap * LAP + STARTS[j] + 1;
    G.obs = []; G.items = []; G.genX = G.x + NW;              // what was set out for where you were goes; new things from off the screen
    pressed.jump = false;
    SND.play('ui');
  }
  // (v48) debugging too: skip to the next stage's start (stage 1: the toilet; stage 2: round to the body's start)
  function skipStage() {
    if (G.mode !== 'play') return;
    const stg = stageOf(stationAt(G.x).lx), j = stg === 1 ? COURSE.findIndex((st) => st[5] === STAGE2) : 0;
    goToPlace(j);
  }
  // the settings: the jump and slide buttons' sides swapped (kept in this browser); the sound switches are in sound.js
  const SET = { swap: false, god: false };
  try { SET.swap = localStorage.getItem('bodyrun.swap') === '1'; SET.god = localStorage.getItem('bodyrun.god') === '1'; } catch (e) { /* storage off */ }
  // debugging too: a mini-game's mark on the progress bar, tapped, takes you to the start of its place (ahead in this
  // lap, or in the next) and it begins; a mini-game on ends first
  function barMarkAt(nx, ny) {
    if (Math.abs(ny - 32.2) > 10) return null;
    const px0 = NW / 2 - BAR_W / 2, stg = stageOf(stationAt(G.x).lx), [s0, s1] = stageSpan(stg);
    let best = null, bd = 9;
    for (const m of MINI_MARKS) { if (stageOf(m.lx) !== stg) continue; const d = Math.abs(nx - (px0 + BAR_W * (m.lx - s0) / (s1 - s0))); if (d < bd) { bd = d; best = m; } }
    return best;
  }
  function goToPlace(j) {
    if (G.mode !== 'play') return;
    if (G.rh) { SND.spin(null); endRhythm(); }
    if (G.orb) endOrbit();
    if (G.bb) endBaseball();
    if (G.wm) endWhack();
    if (G.mem) endMemory();
    if (G.pk) endPK();
    if (G.sl) endSlot();
    if (G.yb) endYB();
    if (G.tw) endTW();
    if (G.ar) endAR();
    if (G.cut) cutDone();
    const s = stationAt(G.x), lap = STARTS[j] + 1 > s.lx ? s.lap : s.lap + 1;
    G.x = lap * LAP + STARTS[j] + 1;
    G.obs = []; G.items = []; G.genX = G.x + NW;
    G.station = -1;                                         // arriving, even when it is the place you were in
    G.slLap = -1;                                           // (the toilet jackpot: again, even if played this lap)
    pressed.jump = false;
    SND.play('ui');
  }
  function doJump() { if (G.mode === 'play' && !busy()) pressed.jump = true; }
  function setSlide() { G.slideHeld = [...held.values()].includes('slide') || keySlide; }
  let keySlide = false, keyJump = false;
  cv.addEventListener('pointerdown', (e) => {
    SND.unlock();
    if (G.mode === 'title') { titleTap(); e.preventDefault(); return; }
    if (G.mode === 'lobby') { const [lx, ly] = toWorld(e); lobbyTap(lx, ly); e.preventDefault(); return; }
    if (G.mode !== 'play') return;
    const [nx, ny] = toWorld(e);
    if (nx > NW - 26 && ny < 26) { pause(); return; }
    if (nx > NW - 26 && ny >= 26 && ny < 44) { openSettings(); e.preventDefault(); return; }
    if (DEBUG_SKIP && nx > NW - 26 && ny >= 44 && ny < 66) { skipPlace(); e.preventDefault(); return; }
    if (DEBUG_SKIP && nx > NW - 44 && nx <= NW - 26 && ny >= 44 && ny < 66) { skipStage(); e.preventDefault(); return; }     // (v48)
    if (DEBUG_SKIP) { const m = barMarkAt(nx, ny); if (m) { goToPlace(m.i); e.preventDefault(); return; } }
    if (G.rh) { rhDown(e.pointerId, nx, ny); e.preventDefault(); return; }
    if (G.orb) { orbTap(); e.preventDefault(); return; }
    if (G.bb) { bbDown(e.pointerId, nx, ny); e.preventDefault(); return; }
    if (G.wm) { wmDown(nx, ny); e.preventDefault(); return; }
    if (G.mem) { memDown(nx, ny); e.preventDefault(); return; }
    if (G.pk) { pkDown(e.pointerId, nx, ny); e.preventDefault(); return; }
    if (G.sl) { slTap(nx, ny); e.preventDefault(); return; }
    if (G.yb) { ybDown(nx, ny); e.preventDefault(); return; }
    if (G.tw) { twDrop(); e.preventDefault(); return; }
    if (G.ar) { arDown(e.pointerId, nx, ny); e.preventDefault(); return; }
    const side = (nx < NW / 2) !== SET.swap ? 'jump' : 'slide';    // the left half jumps (the right, swapped)
    held.set(e.pointerId, side);
    if (side === 'jump') doJump();
    setSlide(); e.preventDefault();
  });
  const up = (e) => { held.delete(e.pointerId); setSlide(); rhUp(e.pointerId); bbUp(e.pointerId); if (G.pk && G.mode === 'play') { const [nx, ny] = e.type !== 'pointercancel' ? toWorld(e) : []; pkUp(e.pointerId, nx, ny); } if (G.ar) arUp(e.pointerId); };
  cv.addEventListener('pointerup', up); cv.addEventListener('pointercancel', up); cv.addEventListener('pointerleave', up);
  cv.addEventListener('pointermove', (e) => { if (G.mode !== 'play') return; if (G.rh) { const [nx, ny] = toWorld(e); rhMove(e.pointerId, nx, ny); } if (G.bb) { const [nx, ny] = toWorld(e); bbMove(e.pointerId, nx, ny); } if (G.pk) { const [nx, ny] = toWorld(e); pkMove(e.pointerId, nx, ny); } if (G.ar) { const [nx, ny] = toWorld(e); arMove(e.pointerId, nx, ny); } });
  document.addEventListener('visibilitychange', () => { if (document.hidden && G.mode === 'play') pause(); });
  addEventListener('keydown', (e) => {
    if (e.repeat) return;
    if (G.mode === 'title' && ['Space', 'Enter'].includes(e.code)) { SND.unlock(); titleTap(); e.preventDefault(); return; }
    if (G.mode === 'lobby' && document.getElementById('setBox').hidden) {          // (v59) the lobby: space or enter plays, escape goes back from a card
      if (LOBBY.page !== 'main' && ['Escape', 'Backspace'].includes(e.code)) { LOBBY.page = 'main'; SND.play('ui'); e.preventDefault(); return; }
      if (LOBBY.page === 'main' && ['Space', 'Enter'].includes(e.code)) { SND.unlock(); lobbyAct('start'); e.preventDefault(); return; }
      if (LOBBY.page === 'prep' && ['Space', 'Enter'].includes(e.code)) { SND.unlock(); const q = prepGo(lobbyPanel()); prepTap(q.x + q.w / 2, q.y + q.h / 2); e.preventDefault(); return; }
    }
    if (G.bb && G.mode === 'play') {                         // baseball: the arrows move the bat's ring, space (or enter) swings
      if (BB_KEY[e.code]) { bbKeys.add(BB_KEY[e.code]); e.preventDefault(); return; }
      if (['Space', 'Enter', 'KeyJ', 'KeyF'].includes(e.code)) { bbSwing(); e.preventDefault(); return; }
    }
    if (G.yb && G.mode === 'play' && ybKey(e.code)) { e.preventDefault(); return; }    // (v52) the shell game: arrows, space, 1-3
    if (G.tw && G.mode === 'play' && ['Space', 'Enter', 'ArrowDown', 'KeyJ', 'KeyF', 'KeyS'].includes(e.code)) { twDrop(); e.preventDefault(); return; }    // (v53) the tower: drop
    if (G.ar && G.mode === 'play') {                        // (v54) the archery: the arrows turn the bow (v55: left or up raises it, right or down lowers it), space shoots
      if (['ArrowUp', 'KeyW', 'ArrowLeft', 'KeyA'].includes(e.code)) { G.ar.keys.U = true; e.preventDefault(); return; }
      if (['ArrowDown', 'KeyS', 'ArrowRight', 'KeyD'].includes(e.code)) { G.ar.keys.D = true; e.preventDefault(); return; }
      if (['Space', 'Enter', 'KeyJ', 'KeyF'].includes(e.code)) { arShoot(); e.preventDefault(); return; }
    }
    const dg = /^(Digit|Numpad)([0-9])$/.exec(e.code);                // the germ and memory games: the number keys
    if (dg && G.wm && G.mode === 'play') { if (WM_KEY[dg[2]] !== undefined) wmKey(WM_KEY[dg[2]]); e.preventDefault(); return; }
    if (dg && G.mem && G.mode === 'play') { memKey(+dg[2] - 1); e.preventDefault(); return; }
    if (G.pk && G.mode === 'play') {                        // the shoot-out: the arrows aim, space (or enter) shoots
      const k = PK_KEYS[e.code]; if (k) { pkKeys.add(k); e.preventDefault(); return; }
      if (['Space', 'Enter', 'KeyJ', 'KeyF'].includes(e.code)) { pkShoot(); e.preventDefault(); return; }
    }
    if (G.sl && G.mode === 'play' && ['Space', 'Enter', 'ArrowUp', 'ArrowDown', 'KeyJ', 'KeyF'].includes(e.code)) { slTap(-99, -99); e.preventDefault(); return; }
    if (G.orb && G.mode === 'play' && ['Space', 'ArrowUp', 'ArrowDown', 'KeyW', 'KeyS', 'Enter', 'KeyJ', 'KeyF'].includes(e.code)) { orbTap(); e.preventDefault(); return; }
    if (e.code === 'Space' || e.code === 'ArrowUp' || e.code === 'KeyW') { keyJump = true; doJump(); e.preventDefault(); }
    if (e.code === 'ArrowDown' || e.code === 'KeyS') { keySlide = true; setSlide(); e.preventDefault(); }
    if (e.code === 'Escape' || e.code === 'KeyP') { if (G.mode === 'play') pause(); else if (G.mode === 'pause') resume(); }
  });
  addEventListener('keyup', (e) => { if (G.ar) { if (['ArrowUp', 'KeyW', 'ArrowLeft', 'KeyA'].includes(e.code)) G.ar.keys.U = false; if (['ArrowDown', 'KeyS', 'ArrowRight', 'KeyD'].includes(e.code)) G.ar.keys.D = false; } if (BB_KEY[e.code]) bbKeys.delete(BB_KEY[e.code]); if (PK_KEYS[e.code]) pkKeys.delete(PK_KEYS[e.code]); if (e.code === 'ArrowDown' || e.code === 'KeyS') { keySlide = false; setSlide(); } if (e.code === 'Space' || e.code === 'ArrowUp' || e.code === 'KeyW') keyJump = false; });

  // ---------------------------------------------------------------- the mini-games' songs (stages.js): five each, in turn
  // Each go of a mini-game takes the next of its songs; the turn is kept (the next run goes on from it). The songs are
  // files: fetched when the page opens, decoded once the sound is on (the next one of each, ahead of time).
  // ?rhsong=N / ?orbsong=N (1..5): always that song (tests).
  const SND = window.BodySound, STAGES = window.BodyStages;
  const ROT = { rh: 0, orb: 0 }, FIX = { rh: +qs.get('rhsong') || 0, orb: +qs.get('orbsong') || 0 };
  for (const k of ['rh', 'orb']) { try { ROT[k] = (+localStorage.getItem('bodyrun.' + k + 'Song') || 0) % STAGES[k].length; } catch (e) { /* storage off */ } }
  const songFor = (k) => STAGES[k][FIX[k] ? (FIX[k] - 1) % STAGES[k].length : ROT[k]];
  // the songs come on the way: a mini-game's next song is fetched when its place is about SONG_FETCH s of running off,
  // decoded at SONG_DECODE s off, and let go once it is behind (a decoded song is ~12 MB); see manageThemes
  const SONG_FETCH = 25, SONG_DECODE = 12;
  function getReady() { if (!CAPTURE) manageSongs(); }
  function manageSongs() {
    if (CAPTURE || G.station < 0) return;
    const lx = stationAt(G.x).lx;
    for (const [k, id, on] of [['rh', 'ra', !!G.rh], ['orb', 'vertebral', !!G.orb]]) {
      const s = songFor(k), d = ((STARTS[COURSE.findIndex((st) => st[0] === id)] - lx) % LAP + LAP) % LAP;
      if (on) continue;                                     // (in the stage: its song is playing)
      if (d < Math.max(6000, G.v * SONG_FETCH)) SND.fetchSong(s).catch(() => {});
      if (d < Math.max(3000, G.v * SONG_DECODE)) { if (SND.ctx) SND.prepare(s).catch(() => {}); } else SND.release(s);
    }
  }
  function takeSong(k) {
    const s = songFor(k);
    if (!FIX[k]) { ROT[k] = (ROT[k] + 1) % STAGES[k].length; try { localStorage.setItem('bodyrun.' + k + 'Song', String(ROT[k])); } catch (e) { /* storage off */ } }
    SND.fetchSong(s).catch(() => {}); if (SND.ctx) SND.prepare(s).catch(() => {});
    return s;
  }
  const SONG_WAIT = 4;                                     // a song not decoded yet: wait this long for it, then go on without
  // a buzz under the finger (phones that can, Android): a tap that hits on the rhythm and orbit stages, short; and
  // while you follow a ball along its track, every 0.3 s a rough little drag (two quick pulses)
  const BUZZ_TAP = 20, BUZZ_DRAG = [12, 16, 12], BUZZ_EVERY = 0.3;
  function buzz(p) { try { if (navigator.vibrate) navigator.vibrate(p); } catch (e) { /* not here */ } }

  // ---------------------------------------------------------------- the rhythm stage (in the right atrium)
  // The heart races: the run slows to a walk, the song plays, and circles come up on its tune (tap when the shrinking
  // ring meets the circle, in their numbered order), balls to follow along a track (touch, hold, drag) on its long
  // notes, and a disc to spin on the build before the chorus. The clock is the sound card's (what you hear), or the
  // game's when there is no sound (tests). The background goes on slowly enough to stay in the heart.
  const RH_R = 13, RH_AR = 0.85, RH_PERF = 0.085, RH_GOOD = 0.17, RH_LEAD = 1.2, RH_DONE = 2.4;
  const RH_COLS = [['#ff5a8a', '#ffc0d2', '#a01848'], ['#ffa03a', '#ffe0a8', '#a85a08'], ['#46b4ff', '#c4e8ff', '#1060a8'], ['#6ad25a', '#ccf4c0', '#2a7a1e']];
  // the walk through the heart: the right atrium and ventricle, less a little
  const RH_ROOM = COURSE.filter((st) => st[0] === 'ra' || st[0] === 'rv').reduce((L, st) => L + st[4], 0) - 160;
  const rhPos = (u, v) => [52 + u * (NW - 104), 52 + v * 92];
  function catmull(pts, n) {
    const out = [];
    for (let i = 0; i < pts.length - 1; i++) {
      const p0 = pts[Math.max(0, i - 1)], p1 = pts[i], p2 = pts[i + 1], p3 = pts[Math.min(pts.length - 1, i + 2)];
      for (let k = 0; k < n; k++) {
        const t = k / n, t2 = t * t, t3 = t2 * t;
        out.push([0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2 + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3),
                  0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2 + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)]);
      }
    }
    out.push(pts[pts.length - 1]);
    return out;
  }
  function rhPath(n) {                                     // a slider's track in world units (follows the screen's width)
    const P = catmull(n.ctrl.map(([u, v]) => rhPos(u, v)), 14);
    const L = [0]; for (let i = 1; i < P.length; i++) L.push(L[i - 1] + Math.hypot(P[i][0] - P[i - 1][0], P[i][1] - P[i - 1][1]));
    return { P, L, len: L[L.length - 1] };
  }
  function rhBall(path, f) {
    const d = Math.max(0, Math.min(1, f)) * path.len;
    let i = 1; while (i < path.L.length - 1 && path.L[i] < d) i++;
    const a = path.L[i - 1], b = path.L[i], k = b > a ? (d - a) / (b - a) : 0;
    return [path.P[i - 1][0] + (path.P[i][0] - path.P[i - 1][0]) * k, path.P[i - 1][1] + (path.P[i][1] - path.P[i - 1][1]) * k];
  }
  function startRhythm() {
    holdBoost();
    G.obs = G.obs.filter((o) => o.x + o.w < G.x - 12);       // clear what was set out ahead (what you passed scrolls off)
    G.items = G.items.filter((i) => i.x < G.x - 12 || i.taken);
    const song = takeSong('rh'), B = 60 / song.bpm, audio = !CAPTURE && SND.live();
    const notes = []; let num = 0, grp = -1;
    for (const m of song.map) {
      if (m[1] !== grp) { grp = m[1]; num = 0; }
      const n = { b: m[0], tn: m[0] * B, kind: m[2], num: ++num, col: RH_COLS[m[1] % RH_COLS.length], res: null };
      if (n.kind === 'c') { n.u = m[3]; n.v = m[4]; }
      if (n.kind === 's') { n.te = m[3] * B; n.ctrl = m[4]; n.u = m[4][0][0]; n.v = m[4][0][1]; n.inT = 0; n.allT = 0; n.start = null; n.ticks = 0; }
      if (n.kind === 'p') { n.te = m[3] * B; n.need = m[4]; n.turns = 0; n.ang = 0; n.rate = 0; }
      if (n.kind === 'r') { n.te = m[3] * B; n.need = m[4]; n.hits = 0; n.popT = null; n.hitT = -9; }
      notes.push(n);
    }
    for (const n of notes) {                                 // two balls at once, one each side: both hands
      const mate = n.kind === 's' && notes.find((q) => q !== n && q.kind === 's' && q.tn === n.tn);
      if (mate) { n.dual = true; n.lead = n.u < mate.u; n.mate = mate; }
    }
    const secs = RH_LEAD + song.end * B + RH_DONE;
    G.rh = { song, B, first: song.first, end: song.end, speed: Math.max(30, Math.min(60, RH_ROOM / secs)),
      gt0: G.t + RH_LEAD, a0: null, wait: audio ? G.t : null, notes, combo: 0, maxCombo: 0, n: { perfect: 0, good: 0, miss: 0 },
      pops: [], ptr: new Map(), done: false, doneT: 0, gain: 0, lastBeat: -99, flash: -9 };
    if (audio) SND.ambience(false);
    G.slideHeld = false; held.clear();
  }
  // the song is in: start it (and the stage's clock with it); or it did not come: go on by the game's clock, silent
  function rhStartSong() {
    const r = G.rh;
    if (SND.ready(r.song) && SND.live()) { r.a0 = SND.ctx.currentTime + RH_LEAD; SND.playSong(r.song, r.a0); r.wait = null; }
    else if (G.t - r.wait > SONG_WAIT) { r.gt0 = G.t + RH_LEAD; r.wait = null; G.silent = (G.silent || 0) + 1; }
  }
  function endRhythm() {
    const played = G.rh.song;
    bankGame(G.rh); G.rh = null; resumeBoost();
    SND.stopSong(0.5); SND.spin(null); SND.ambience(true);
    if (songFor('rh').file !== played.file) SND.release(played);   // (its decoded sound is big; the next is ready)
    G.genX = Math.max(G.genX, G.x + NW * 0.8);              // a moment to get going again
    G.banner = G.t;                                          // and where you are now
  }
  function rtime() {
    const r = G.rh;
    if (r.wait !== null) return -RH_LEAD;                    // the song still on its way
    return r.a0 !== null && SND.ctx ? SND.ctx.currentTime - SND.latency() - r.a0 : G.t - r.gt0;   // the sound card's clock stops while paused
  }
  function rhJudge(n, res, x, y) {
    const r = G.rh;
    n.res = res; r.n[res]++;
    if (res === 'miss') { r.combo = 0; G.hp = Math.max(0, G.hp - 3); }
    else {
      r.combo++; r.maxCombo = Math.max(r.maxCombo, r.combo);
      const base = n.kind === 'p' || n.kind === 'r' ? (res === 'perfect' ? 100 : 40) : n.kind === 's' ? (res === 'perfect' ? 50 : 20) : (res === 'perfect' ? 30 : 10);
      const pts = Math.round(base * (1 + Math.min(r.combo, 40) / 25));
      r.gain += pts;                                        // (banked when the game ends)
      G.hp = Math.min(G.hpMax, G.hp + (res === 'perfect' ? 1.5 : 0.5));
    }
    r.pops.push({ x, y, s: res === 'perfect' ? 'Perfect' : res === 'good' ? 'Good' : 'Miss', res, t: G.t });
    SND.play(res);
  }
  // a touch on the stage
  // a tap on the balloon (anywhere, while it is up): it swells; enough of them and it bursts (perfect)
  function rhRollHit(n) {
    n.hits++; n.hitT = G.t; SND.play('tick'); if (!AUTO) buzz(BUZZ_TAP);
    if (n.hits >= n.need && !n.res) { n.popT = G.t; SND.play('spinDone'); rhJudge(n, 'perfect', NWf / 2, 98); }
  }
  function rhDown(id, x, y) {
    const r = G.rh; if (!r) return;
    r.ptr.set(id, { x, y, ang: null });
    if (r.done) return;
    const t = rtime();
    const roll = r.notes.find((n) => n.kind === 'r' && !n.res && t >= n.tn - 0.06 && t <= n.te);
    if (roll) { rhRollHit(roll); return; }
    for (const n of r.notes) {
      if (n.res || n.kind === 'p') continue;
      if (n.kind === 's' && n.start) continue;
      if (Math.abs(t - n.tn) > RH_GOOD) { if (n.tn - t > RH_GOOD) break; continue; }
      const [nx, ny] = rhPos(n.u, n.v);
      if (Math.hypot(x - nx, y - ny) > RH_R * 1.3) continue;
      const res = Math.abs(t - n.tn) <= RH_PERF ? 'perfect' : 'good';
      buzz(BUZZ_TAP);
      if (n.kind === 'c') rhJudge(n, res, nx, ny);
      else { n.start = res; n.holder = id; n.buzzT = t; SND.play(res); r.pops.push({ x: nx, y: ny, s: res === 'perfect' ? 'Perfect' : 'Good', res, t: G.t, small: true }); }
      return;
    }
  }
  function rhMove(id, x, y) {
    const r = G.rh; if (!r) return;
    const p = r.ptr.get(id); if (!p) return;
    p.x = x; p.y = y;
    const sp = r.notes.find((n) => n.kind === 'p' && !n.res);
    if (sp) {
      const t = rtime();
      if (t >= sp.tn - 0.1 && t <= sp.te) {
        const [cx, cy] = [NWf / 2, 98];
        const a = Math.atan2(y - cy, x - cx);
        if (p.ang !== null && Math.hypot(x - cx, y - cy) > 6) {
          let d = a - p.ang; while (d > Math.PI) d -= 2 * Math.PI; while (d < -Math.PI) d += 2 * Math.PI;
          sp.turns += Math.abs(d) / (2 * Math.PI); sp.ang += d;
        }
        p.ang = a;
      }
    }
  }
  function rhUp(id) { const r = G.rh; if (r) r.ptr.delete(id); }
  function stepRhythm(dt) {
    const r = G.rh;
    if (r.wait !== null) rhStartSong();
    const t = rtime(), B = r.B;
    const beat = Math.floor(t / B);
    if (beat !== r.lastBeat) { r.lastBeat = beat; if (beat >= 0 && t < r.end * B) r.flash = G.t; }
    for (const n of r.notes) {
      if (n.res) continue;
      if (n.kind === 'c') {
        if (AUTO && t >= n.tn) { const [x, y] = rhPos(n.u, n.v); rhJudge(n, 'perfect', x, y); }
        else if (t > n.tn + RH_GOOD) { const [x, y] = rhPos(n.u, n.v); rhJudge(n, 'miss', x, y); }
      } else if (n.kind === 's') {
        const path = rhPath(n);
        if (AUTO && !n.start && t >= n.tn) { n.start = 'perfect'; n.holder = 'auto'; SND.play('perfect'); }
        if (t >= n.tn && t <= n.te) {
          const f = (t - n.tn) / (n.te - n.tn), [bx, by] = rhBall(path, f);
          let ok = AUTO;
          for (const p of r.ptr.values()) if (Math.hypot(p.x - bx, p.y - by) <= RH_R * 2.4) ok = true;
          n.allT += dt; if (ok) n.inT += dt;
          n.following = ok;
          if (ok && !AUTO && t - (n.buzzT ?? n.tn) >= BUZZ_EVERY) { n.buzzT = t; buzz(BUZZ_DRAG); }   // held: the drag under the finger
          const k = Math.floor((t - n.tn) / (B / 2));
          if (k > n.ticks) { n.ticks = k; if (ok) SND.play('tick'); }
        }
        if (t > n.te) {
          const ratio = n.allT > 0 ? n.inT / n.allT : 0, [ex, ey] = rhBall(path, 1);
          rhJudge(n, ratio >= 0.85 && n.start === 'perfect' ? 'perfect' : ratio >= 0.5 && n.start ? 'good' : ratio >= 0.75 ? 'good' : 'miss', ex, ey);
        }
      } else if (n.kind === 'r') {                            // the balloon: tap, tap, tap (the pilot: 7.5 a second)
        if (AUTO && t >= n.tn && t <= n.te && t - (n.autoT ?? -9) >= 1 / 7.5) { n.autoT = t; rhRollHit(n); }
        if (!n.res && t > n.te) rhJudge(n, n.hits >= n.need * 0.6 ? 'good' : 'miss', NWf / 2, 98);
      } else {                                               // the spinner
        if (t >= n.tn && t <= n.te) {
          if (AUTO) n.turns += 3.6 * dt, n.ang += 3.6 * dt * 2 * Math.PI;
          const prev = n.prevTurns || 0; n.rate = n.rate * 0.85 + ((n.turns - prev) / Math.max(dt, 1e-3)) * 0.15; n.prevTurns = n.turns;
          if (!n.doneSnd && n.turns >= n.need) { n.doneSnd = true; SND.play('spinDone'); }
          SND.spin(n.rate);
        }
        if (t > n.te) {
          SND.spin(null);
          rhJudge(n, n.turns >= n.need ? 'perfect' : n.turns >= n.need * 0.5 ? 'good' : 'miss', NWf / 2, 98);
          if (n.turns > n.need) { const extra = Math.floor(n.turns - n.need) * 20; r.gain += extra; }
        }
      }
    }
    r.pops = r.pops.filter((p) => G.t - p.t < 0.6);
    if (!r.done && t > r.end * B && r.notes.every((n) => n.res)) { r.done = true; r.doneT = G.t; }
    if (r.done && G.t - r.doneT > RH_DONE) endRhythm();
  }
  function drawRhythm() {
    const r = G.rh; if (!r) return;
    const t = rtime();
    world();
    // the stage: the scene dimmed a little, and a red pulse on every heartbeat
    ctx.fillStyle = 'rgba(14,2,10,0.32)'; ctx.fillRect(0, 0, NWf, NH);
    const fl = Math.max(0, 1 - (G.t - r.flash) / 0.3);
    if (fl > 0) {
      const g = ctx.createRadialGradient(NWf / 2, NH / 2, NH * 0.35, NWf / 2, NH / 2, NWf * 0.62);
      g.addColorStop(0, 'rgba(255,40,80,0)'); g.addColorStop(1, `rgba(255,40,80,${0.32 * fl})`);
      ctx.fillStyle = g; ctx.fillRect(0, 0, NWf, NH);
    }
    // the title (and the song's name), before the first note; a count of four into it
    const B = r.B, f0 = r.first * B;
    if (t < f0) {
      const a = Math.min(1, (t + RH_LEAD) / 0.3) * Math.min(1, (f0 - t) / 0.4);
      label(TR('심장이 두근두근!', 'Heartbeat!'), NWf / 2, 66, 17, 'center', a, '#ffd0dc');
      label(TR('원은 고리가 겹칠 때 터치 · 공은 잡고 따라가기 · 풍선은 연타 · 원판은 빙빙', 'Tap circles as the rings meet · hold and follow balls · mash balloons · spin discs'), NWf / 2, 86, 6.5, 'center', a, '#ffffff');
      label(TR(r.song.name, r.song.en || r.song.name), NWf / 2, 100, 7.5, 'center', a * 0.9, '#ffe0a8');
      const c = r.first - Math.floor(t / B);
      if (t > 0 && c >= 1 && c <= 4) label(String(c), NWf / 2, 126, 16, 'center', a * (1 - (t / B) % 1), '#ffffff');
    }
    // notes, later ones underneath
    for (let i = r.notes.length - 1; i >= 0; i--) {
      const n = r.notes[i];
      if (n.kind === 'p') { if (!n.res && t >= n.tn - 0.4) drawSpinner(n, t); continue; }
      if (n.kind === 'r') { if (t >= n.tn - 0.4 && (!n.res || (n.popT !== null && G.t - n.popT < 0.45))) drawRoll(n, t); continue; }
      const show = t >= n.tn - RH_AR - 0.15;
      if (!show) continue;
      const fade = Math.min(1, (t - (n.tn - RH_AR - 0.15)) / 0.25);
      if (n.kind === 's') {
        if (n.res && t > n.te + 0.15) continue;
        drawSlider(n, t, fade);
        if (n.dual && n.lead && t < n.tn + 0.3) {             // both hands: a word over the pair as it comes
          const [x1, y1] = rhPos(n.u, n.v), [x2, y2] = rhPos(n.mate.u, n.mate.v);
          label(TR('양손!', 'Both hands!'), (x1 + x2) / 2, Math.min(y1, y2) - 4, 10, 'center', fade * Math.min(1, (n.tn + 0.3 - t) / 0.3), '#ffe68a');
        }
      } else {
        if (n.res) continue;
        const [x, y] = rhPos(n.u, n.v);
        drawNote(x, y, n.col, n.num, fade);
        approach(x, y, n.col, (n.tn - t) / RH_AR, fade);
      }
    }
    for (const p of r.pops) {
      const u = (G.t - p.t) / 0.6;
      if (p.res !== 'miss') { ctx.beginPath(); ctx.arc(p.x, p.y, RH_R * (1 + u * 0.9), 0, 6.29); ctx.lineWidth = 2.2 * (1 - u); ctx.strokeStyle = p.res === 'perfect' ? `rgba(255,236,150,${1 - u})` : `rgba(160,220,255,${1 - u})`; ctx.stroke(); }
      label(p.s, p.x, p.y - RH_R - 4 - u * 8, p.small ? 7 : 9, 'center', 1 - u * u, p.res === 'perfect' ? '#ffe68a' : p.res === 'good' ? '#a8e0ff' : '#ff8a8a');
    }
    if (r.done) {
      const a = Math.min(1, (G.t - r.doneT) / 0.25) * Math.min(1, (RH_DONE - (G.t - r.doneT)) / 0.3);
      ctx.globalAlpha = a * 0.78; rrect(NWf / 2 - 110, 54, 220, 74, 8); ctx.fillStyle = '#1a0a14'; ctx.fill(); ctx.globalAlpha = 1;
      label(TR('리듬 끝!', 'Rhythm clear!'), NWf / 2, 70, 14, 'center', a, '#ffd0dc');
      label(`Perfect ${r.n.perfect}  ·  Good ${r.n.good}  ·  Miss ${r.n.miss}`, NWf / 2, 92, 8.5, 'center', a, '#ffffff');
      label(`${TR('최대 콤보', 'Max combo')} ${r.maxCombo}  ·  +${PT(r.gain)}`, NWf / 2, 110, 8.5, 'center', a, '#ffe68a');
    }
  }
  function drawNote(x, y, col, num, alpha, R = RH_R) {
    ctx.globalAlpha = alpha;
    ctx.beginPath(); ctx.arc(x, y, R + 1.6, 0, 6.29); ctx.fillStyle = '#1a0a14'; ctx.fill();
    const g = ctx.createRadialGradient(x - R * 0.35, y - R * 0.4, R * 0.1, x, y, R);
    g.addColorStop(0, col[1]); g.addColorStop(0.55, col[0]); g.addColorStop(1, col[2]);
    ctx.beginPath(); ctx.arc(x, y, R, 0, 6.29); ctx.fillStyle = g; ctx.fill();
    ctx.lineWidth = 1.7; ctx.strokeStyle = '#ffffff'; ctx.beginPath(); ctx.arc(x, y, R - 0.9, 0, 6.29); ctx.stroke();
    ctx.globalAlpha = 1;
    if (num) label(String(num), x, y + 0.6, 11, 'center', alpha, '#ffffff');
  }
  function approach(x, y, col, k, alpha) {
    if (k <= 0) return;
    const R = RH_R * (1 + 2.3 * Math.min(1, k));
    ctx.globalAlpha = alpha * Math.min(1, (1 - k) * 3 + 0.2);
    ctx.lineWidth = 3.2; ctx.strokeStyle = '#1a0a14'; ctx.beginPath(); ctx.arc(x, y, R, 0, 6.29); ctx.stroke();
    ctx.lineWidth = 2.0; ctx.strokeStyle = col[1]; ctx.beginPath(); ctx.arc(x, y, R, 0, 6.29); ctx.stroke();
    ctx.globalAlpha = 1;
  }
  // the balloon: a red cell that swells with every tap, the taps still to go on it, the time left in a ring round it; when
  // it bursts, its bits fly off
  function drawRoll(n, t) {
    const cx = NWf / 2, cy = 98, a = Math.min(1, (t - (n.tn - 0.4)) / 0.3);
    if (n.popT !== null) {
      const u = (G.t - n.popT) / 0.45;
      ctx.globalAlpha = Math.max(0, 1 - u);
      for (let k = 0; k < 12; k++) {
        const ang = k / 12 * 6.283 + 0.3, d = 22 + 42 * u;
        ctx.beginPath(); ctx.arc(cx + Math.cos(ang) * d, cy + Math.sin(ang) * d * 0.85, 1 + 4 * (1 - u), 0, 6.29); ctx.fillStyle = '#e8304a'; ctx.fill();
        ctx.lineWidth = 0.8; ctx.strokeStyle = '#3a0610'; ctx.stroke();
      }
      ctx.beginPath(); ctx.arc(cx, cy, 24 + 30 * u, 0, 6.29); ctx.lineWidth = 2.6 * (1 - u); ctx.strokeStyle = '#ffe68a'; ctx.stroke();
      ctx.globalAlpha = 1; return;
    }
    const k = Math.min(1, n.hits / n.need), R = 16 + 12 * k + (G.t - n.hitT < 0.08 ? 1.6 : 0);
    ctx.globalAlpha = a;
    ctx.beginPath(); ctx.ellipse(cx, cy, R + 1.2, R * 0.86 + 1.2, 0, 0, 6.29); ctx.fillStyle = '#3a0610'; ctx.fill();
    const g = ctx.createRadialGradient(cx - R * 0.3, cy - R * 0.35, R * 0.1, cx, cy, R);
    g.addColorStop(0, '#ff8a96'); g.addColorStop(0.55, '#e8304a'); g.addColorStop(1, '#a8122a');
    ctx.beginPath(); ctx.ellipse(cx, cy, R, R * 0.86, 0, 0, 6.29); ctx.fillStyle = g; ctx.fill();
    ctx.beginPath(); ctx.ellipse(cx, cy + 1, R * 0.5, R * 0.38, 0, 0, 6.29); ctx.fillStyle = 'rgba(120,10,30,0.45)'; ctx.fill();   // its middle, dipped in
    ctx.beginPath(); ctx.ellipse(cx - R * 0.4, cy - R * 0.42, R * 0.22, R * 0.11, -0.5, 0, 6.29); ctx.fillStyle = 'rgba(255,255,255,0.75)'; ctx.fill();
    const left = Math.max(0, Math.min(1, (n.te - t) / (n.te - n.tn)));
    ctx.beginPath(); ctx.arc(cx, cy, 36, -Math.PI / 2, -Math.PI / 2 + left * 2 * Math.PI); ctx.lineWidth = 1.8; ctx.strokeStyle = 'rgba(255,255,255,0.75)'; ctx.stroke();
    ctx.globalAlpha = 1;
    label(t < n.tn ? TR('준비', 'Ready') : TR('연타!', 'Tap fast!'), cx, cy - 45, 11, 'center', a, '#ffffff');
    label(String(Math.max(0, n.need - n.hits)), cx, cy + 0.5, 12, 'center', a, '#ffffff');
  }
  function drawSlider(n, t, alpha) {
    const path = rhPath(n), P = path.P;
    const line = (w, c) => { ctx.beginPath(); ctx.moveTo(P[0][0], P[0][1]); for (const p of P) ctx.lineTo(p[0], p[1]); ctx.lineWidth = w; ctx.strokeStyle = c; ctx.stroke(); };
    ctx.lineCap = 'round'; ctx.lineJoin = 'round';
    ctx.globalAlpha = alpha * (n.res ? Math.max(0, 1 - (t - n.te) / 0.15) : 1);
    line(RH_R * 2 + 3.2, '#1a0a14'); line(RH_R * 2 + 1, '#ffffff'); line(RH_R * 2 - 2.4, n.col[2]); line(RH_R * 1.2, n.col[0]);
    ctx.globalAlpha = 1;
    const e = P[P.length - 1];
    ctx.globalAlpha = alpha; ctx.lineWidth = 1.6; ctx.strokeStyle = '#ffffff'; ctx.beginPath(); ctx.arc(e[0], e[1], RH_R - 2, 0, 6.29); ctx.stroke(); ctx.globalAlpha = 1;
    if (t < n.tn || (!n.start && t < n.tn + RH_GOOD)) {
      drawNote(P[0][0], P[0][1], n.col, n.num, alpha);
      approach(P[0][0], P[0][1], n.col, (n.tn - t) / RH_AR, alpha);
    }
    if (t >= n.tn && t <= n.te + 0.05) {
      const [bx, by] = rhBall(path, (t - n.tn) / (n.te - n.tn));
      if (n.following) { ctx.globalAlpha = 0.5; ctx.lineWidth = 2; ctx.strokeStyle = n.col[1]; ctx.beginPath(); ctx.arc(bx, by, RH_R * 2.1, 0, 6.29); ctx.stroke(); ctx.globalAlpha = 1; }
      drawNote(bx, by, [n.col[1], '#ffffff', n.col[0]], null, 1, RH_R * 0.82);
    }
  }
  function drawSpinner(n, t) {
    const cx = NWf / 2, cy = 98, R = 54;
    const a = Math.min(1, (t - (n.tn - 0.4)) / 0.3);
    ctx.globalAlpha = a;
    ctx.beginPath(); ctx.arc(cx, cy, R + 2, 0, 6.29); ctx.fillStyle = 'rgba(26,10,20,0.72)'; ctx.fill();
    for (let k = 0; k < 3; k++) { ctx.beginPath(); ctx.arc(cx, cy, R - k * 13, 0, 6.29); ctx.lineWidth = 1.4; ctx.strokeStyle = k ? 'rgba(255,192,210,0.5)' : '#ffffff'; ctx.stroke(); }
    for (let k = 0; k < 6; k++) {                          // spokes turning with you
      const ang = n.ang + k * Math.PI / 3;
      ctx.beginPath(); ctx.moveTo(cx + Math.cos(ang) * 10, cy + Math.sin(ang) * 10); ctx.lineTo(cx + Math.cos(ang) * (R - 3), cy + Math.sin(ang) * (R - 3));
      ctx.lineWidth = 3; ctx.strokeStyle = k % 2 ? '#ff5a8a' : '#ffc0d2'; ctx.stroke();
    }
    const prog = Math.min(1, n.turns / n.need);
    ctx.beginPath(); ctx.arc(cx, cy, R + 5, -Math.PI / 2, -Math.PI / 2 + prog * 2 * Math.PI); ctx.lineWidth = 3.4; ctx.strokeStyle = prog >= 1 ? '#ffe68a' : '#ff8aa8'; ctx.stroke();
    const left = Math.max(0, Math.min(1, (n.te - t) / (n.te - n.tn)));
    ctx.beginPath(); ctx.arc(cx, cy, R + 9.5, -Math.PI / 2, -Math.PI / 2 + left * 2 * Math.PI); ctx.lineWidth = 1.6; ctx.strokeStyle = 'rgba(255,255,255,0.7)'; ctx.stroke();
    ctx.globalAlpha = 1;
    label(t < n.tn ? TR('준비', 'Ready') : TR('돌려!', 'Spin!'), cx, cy - 4, 12, 'center', a, '#ffffff');
    label(`${Math.min(n.need, Math.floor(n.turns))} / ${n.need}${TR('바퀴', ' turns')}`, cx, cy + 12, 7.5, 'center', a, '#ffe68a');
  }

  // ---------------------------------------------------------------- the orbit stage (the vertebral artery, on the way into the brain)
  // The runner and an oxygen bubble step along a path of tiles: one stays on its tile while the other swings round it,
  // half a turn a beat; tap as the swinging one comes over the next tile and it lands there, and then the other swings.
  // The tiles are on the song's tune (and on the beat under its long notes); the bend of the path at a tile is the
  // rhythm: straight on is one beat, a quarter turn half a beat or one and a half, an eighth of a turn three quarters
  // or one and a quarter; a swirl on a tile turns the swing round the other way. A miss (or a tap too early) stops
  // nothing: the swing goes on round, the same tile comes up again a turn (two beats) later, all after it moves on by
  // as much, and the song goes back two beats with it. The clock is the sound card's, as on the rhythm stage.
  const OB_L = 30;                                         // tile to tile, and the swing's radius (units)
  const OB_PERF = 0.055, OB_WIN = 0.12, OB_EARLY = 0.24;   // perfect / early or late (lands) / too early (a miss; earlier still: not counted)
  const OB_LEAD = 0.8, OB_DONE = 2.6;                      // before the song starts; the results (seconds)
  const OB_CS = 0.62, OB_BS = 15;                          // the runner drawn at 0.62 of its size; the bubble 15 units
  // the path of a song: tile 0 is the start; tile k (k >= 1) is landed on at beat hits[k] (tile 1 on the song's first
  // note, after the intro). Laid out once: each bend goes the way that keeps the path heading on (never back to the
  // left), off every earlier tile, with as few swirls as it can
  function planOrbit(song) {
    const beats = song.beats, n = beats.length, B = 60 / song.bpm;
    const hits = [0, song.first]; for (let k = 1; k <= n; k++) hits.push(+(hits[k] + beats[k - 1]).toFixed(6));
    const P = [[0, 0], [OB_L, 0]], head = [0], dir = [1];
    const segDist = (p, a, b) => {
      const dx = b[0] - a[0], dy = b[1] - a[1], L2 = dx * dx + dy * dy;
      const u = L2 ? Math.max(0, Math.min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L2)) : 0;
      return Math.hypot(p[0] - a[0] - u * dx, p[1] - a[1] - u * dy);
    };
    const clear = (k, np) => {
      for (let j = 0; j < k; j++) if (Math.hypot(np[0] - P[j][0], np[1] - P[j][1]) < OB_L * 0.95) return false;
      for (let j = 0; j + 1 < k; j++) for (let s = 1; s <= 4; s++) {
        const q = [P[k][0] + (np[0] - P[k][0]) * s / 4, P[k][1] + (np[1] - P[k][1]) * s / 4];
        if (segDist(q, P[j], P[j + 1]) < OB_L * 0.8) return false;
      }
      return true;
    };
    const solve = (k) => {                                 // choose the way out of tile k (tiles 0..k are placed)
      if (k > n) return true;
      const b = beats[k - 1], back = head[k - 1] + Math.PI, opts = [];
      for (const d of [dir[k - 1], -dir[k - 1]]) {
        if (d !== dir[k - 1] && Math.abs(b - 1) < 1e-6) continue;          // straight on goes the same either way
        let h = back + d * Math.PI * b; h = Math.atan2(Math.sin(h), Math.cos(h));
        if (Math.cos(h) < -1e-6) continue;
        const np = [P[k][0] + Math.cos(h) * OB_L, P[k][1] + Math.sin(h) * OB_L];
        opts.push({ d, h, np, cost: (d !== dir[k - 1] ? 1 : 0) + Math.abs(np[1]) / (OB_L * 14) });
      }
      opts.sort((a, c) => a.cost - c.cost);
      for (const o of opts) {
        if (!clear(k, o.np)) continue;
        P[k + 1] = o.np; head[k] = o.h; dir[k] = o.d;
        if (solve(k + 1)) return true;
      }
      P.length = k + 1; head.length = k; dir.length = k;
      return false;
    };
    const ok = solve(1);
    const N = P.length - 1;                                // the last tile
    const swirl = dir.map((d, k) => k > 0 && d !== dir[k - 1]);
    return { song, B, ok, P, head, dir, swirl, hits, T: hits.map((h) => h * B), N };
  }
  const OB_PLANS = {};                                     // laid out once per song, when first needed
  const orbPlan = (song) => OB_PLANS[song.id] || (OB_PLANS[song.id] = planOrbit(song));
  let OB = orbPlan(songFor('orb'));                        // the path of the stage on now (or of the next one)
  const busy = () => !!(G.rh || G.orb || G.bb || G.wm || G.mem || G.pk || G.sl || G.yb || G.tw || G.ar || G.cut);
  function otime() {
    const o = G.orb;
    if (o.wait !== null) return -OB_LEAD;                    // the song still on its way
    return o.a0 !== null && SND.ctx ? SND.ctx.currentTime - SND.latency() - o.a0 : G.t - o.gt0;
  }
  // the swinging body's angle round tile k at time t, over the next tile at time `next` (y down: + is clockwise on screen)
  function obAngle(k, t, next) { return OB.head[k] + OB.dir[k] * Math.PI * (t - next) / OB.B; }
  function obTarget(k) {                                   // where the camera looks: the tile and the next two
    const a = OB.P[k], b = OB.P[Math.min(OB.N, k + 1)], c = OB.P[Math.min(OB.N, k + 2)];
    return [(a[0] + b[0] + c[0]) / 3, (a[1] + b[1] + c[1]) / 3];
  }
  const obAnchor = () => [NWf * 0.42, NH * 0.53];
  function startOrbit() {
    holdBoost();
    OB = orbPlan(takeSong('orb'));
    G.obs = G.obs.filter((o) => o.x + o.w < G.x - 12);
    G.items = G.items.filter((i) => i.x < G.x - 12 || i.taken);
    const A = obAnchor(), h = SH('ch_' + G.char) * OB_CS;
    const cam0 = [OB.P[0][0] - (PX - A[0]), OB.P[0][1] - (GY + 1 - G.y - h / 2 - A[1])];    // tile 0 where the runner is
    const audio = !CAPTURE && SND.live();
    G.orb = { gx0: G.x, cam0, cam: cam0.slice(), gt0: G.t + OB_LEAD, a0: null, wait: audio ? G.t : null, k: 0, st: 'play', stT: G.t, combo: 0, maxCombo: 0,
      res: { perfect: 0, early: 0, late: 0, miss: 0 }, pops: [], landT: -9, inT: G.t, off: 0, next: OB.T[1] };
    G.slideHeld = false; held.clear(); pressed.jump = false;
    if (audio) SND.ambience(false);
  }
  // the song is in: start it (and the stage's clock with it); or it did not come: go on by the game's clock, silent
  function orbStartSong() {
    const o = G.orb;
    if (SND.ready(OB.song) && SND.live()) { o.a0 = SND.ctx.currentTime + OB_LEAD; SND.playSong(OB.song, o.a0); o.wait = null; }
    else if (G.t - o.wait > SONG_WAIT) { o.gt0 = G.t + OB_LEAD; o.wait = null; G.silent = (G.silent || 0) + 1; }
  }
  function endOrbit() {
    const played = OB.song;
    bankGame(G.orb); G.orb = null; G.orbits = (G.orbits || 0) + 1; resumeBoost();
    SND.stopSong(0.5); SND.ambience(true);
    if (songFor('orb').file !== played.file) SND.release(played);
    G.genX = Math.max(G.genX, G.x + NW * 0.8);
    G.banner = G.t;
  }
  // a miss: the swing carries on round and the same tile comes up again two beats later (and so does all after it);
  // the song goes back two beats, so the tile and its note come round together again
  function orbMiss(why) {
    const o = G.orb, B = OB.B;
    o.res.miss++; o.off += 2 * B; o.next += 2 * B; o.combo = 0;
    o.pops.push({ k: o.k + 1, res: 'miss', s: why === 'early' ? TR('빨라요', 'Early') : TR('놓침', 'Miss'), t: G.t });
    SND.play('miss');
    if (o.a0 !== null) SND.playSong(OB.song, o.a0 + o.off);
  }
  function orbTap() {
    const o = G.orb; if (!o || o.st !== 'play') return;
    const e = otime() - o.next;
    if (e < -OB_EARLY) return;                               // far too soon: not a try at this tile
    if (e < -OB_WIN) { orbMiss('early'); return; }
    buzz(BUZZ_TAP);
    orbLand(Math.abs(e) <= OB_PERF ? 'perfect' : e < 0 ? 'early' : 'late');
  }
  function orbLand(res) {
    const o = G.orb;
    o.k++; o.res[res]++; o.landT = G.t;
    o.combo++; o.maxCombo = Math.max(o.maxCombo, o.combo);   // (v57) a combo, as in the rhythm stage: up to 2.6 times at 40 in a row
    { const pts = Math.round((OB_PTS[res] || 0) * (1 + Math.min(o.combo, 40) / 25)); o.gain = (o.gain || 0) + pts; }       // (v49: it scores like the rest)
    o.pops.push({ k: o.k, res, t: G.t });
    SND.play('orbHit');
    if (o.k >= OB.N) { o.st = 'done'; o.stT = G.t; SND.play('orbClear'); }
    else o.next = OB.T[o.k + 1] + o.off;
  }
  function stepOrbit(dt) {
    const o = G.orb;
    if (o.wait !== null) orbStartSong();
    if (o.st === 'play') {
      const t = otime();
      if (AUTO && !window.__noAuto && t >= o.next) orbLand('perfect');           // (__noAuto: a test letting tiles go by)
      else if (t > o.next + OB_WIN) orbMiss('late');
    } else if (o.st === 'done' && G.t - o.stT > OB_DONE) { endOrbit(); return; }
    {
      const A = obTarget(o.k), q = 1 - Math.exp(-dt * 4);
      o.cam[0] += (A[0] - o.cam[0]) * q; o.cam[1] += (A[1] - o.cam[1]) * q;
    }
    G.x = o.gx0 + Math.max(0, o.cam[0] - o.cam0[0]) * 0.4;    // the place scrolls by a little as the path goes on
    o.pops = o.pops.filter((p) => G.t - p.t < 0.6);
  }
  // the stage on screen: the place dimmed, the path, the two bodies, the words
  function drawOrbit() {
    const o = G.orb; if (!o) return;
    const t = otime(), A = obAnchor();
    let al = Math.min(1, (G.t - o.inT) / 0.3);
    if (o.st === 'done') al *= Math.max(0, Math.min(1, (OB_DONE - (G.t - o.stT)) / 0.35));
    world();
    ctx.globalAlpha = al; ctx.fillStyle = 'rgba(10,4,18,0.5)'; ctx.fillRect(0, 0, NWf, NH); ctx.globalAlpha = 1;
    ctx.save();
    ctx.translate(A[0] - o.cam[0], A[1] - o.cam[1]);
    const P = OB.P, k = o.k, i0 = Math.max(0, k - 14), i1 = Math.min(OB.N, k + 18);
    // the path: a dark rim, the tiles, a sheen; what is behind you a little greyed; a seam between tiles
    ctx.lineCap = 'round'; ctx.lineJoin = 'round';
    const run = (a, b, w, c) => { if (b <= a) return; ctx.beginPath(); ctx.moveTo(P[a][0], P[a][1]); for (let i = a + 1; i <= b; i++) ctx.lineTo(P[i][0], P[i][1]); ctx.lineWidth = w; ctx.strokeStyle = c; ctx.stroke(); };
    ctx.globalAlpha = al;
    run(i0, i1, 19.5, '#1a0a14');
    run(i0, Math.min(k, i1), 16, '#b9a9bd'); run(Math.max(i0, k), i1, 16, '#f7eef4');
    run(Math.max(i0, k), i1, 9, '#fffafc');
    ctx.strokeStyle = 'rgba(26,10,20,0.55)'; ctx.lineWidth = 1.1;
    for (let i = i0; i < i1; i++) {                          // seams half way between tile centres
      const a = P[i], b = P[i + 1], mx = (a[0] + b[0]) / 2, my = (a[1] + b[1]) / 2, ang = Math.atan2(b[1] - a[1], b[0] - a[0]);
      const nx = -Math.sin(ang) * 8, ny = Math.cos(ang) * 8;
      ctx.beginPath(); ctx.moveTo(mx + nx, my + ny); ctx.lineTo(mx - nx, my - ny); ctx.stroke();
    }
    for (let i = Math.max(i0, 1); i <= i1; i++) {
      const [x, y] = P[i];
      if (i === OB.N) {                                     // the last tile: a gold ring
        ctx.beginPath(); ctx.arc(x, y, 6.5, 0, 6.29); ctx.lineWidth = 2.6; ctx.strokeStyle = '#1a0a14'; ctx.stroke();
        ctx.lineWidth = 1.6; ctx.strokeStyle = '#ffd65a'; ctx.stroke();
      } else if (OB.swirl[i]) drawSwirl(x, y, OB.dir[i]);
      else { ctx.beginPath(); ctx.arc(x, y, 1.7, 0, 6.29); ctx.fillStyle = i <= k ? 'rgba(80,60,80,0.5)' : 'rgba(150,120,150,0.75)'; ctx.fill(); }
    }
    // landing flashes
    for (const p of o.pops) {
      const u = (G.t - p.t) / 0.6, [x, y] = P[p.k], c = p.res === 'perfect' ? '255,230,140' : p.res === 'early' ? '160,220,255' : p.res === 'late' ? '255,180,110' : '255,90,110';
      ctx.beginPath(); ctx.arc(x, y, 9 + u * 10, 0, 6.29); ctx.lineWidth = 2.2 * (1 - u); ctx.strokeStyle = `rgba(${c},${1 - u})`; ctx.stroke();
    }
    // the swing: a faint ring round the tile you stand on, and a short tail behind the swinging one
    const piv = P[k], th = o.st === 'done' ? null : obAngle(k, t, o.next);
    if (th !== null) {
      ctx.setLineDash([3, 4]); ctx.beginPath(); ctx.arc(piv[0], piv[1], OB_L, 0, 6.29); ctx.lineWidth = 1; ctx.strokeStyle = 'rgba(255,255,255,0.22)'; ctx.stroke(); ctx.setLineDash([]);
      const d = OB.dir[k], tail = 0.9, steps = 9, charSwings = k % 2 === 1;
      for (let s = steps; s >= 1; s--) {
        const a = th - d * tail * s / steps, u = s / steps;
        ctx.beginPath(); ctx.arc(piv[0] + Math.cos(a) * OB_L, piv[1] + Math.sin(a) * OB_L, 4.2 * (1 - u * 0.7), 0, 6.29);
        ctx.fillStyle = charSwings ? `rgba(255,214,120,${0.42 * (1 - u)})` : `rgba(150,220,255,${0.42 * (1 - u)})`; ctx.fill();
      }
    }
    // the two bodies: the runner stands on even tiles, the bubble on odd ones
    const land = Math.max(0, 1 - (G.t - o.landT) / 0.14);
    const body = (isChar, x, y, squash) => {
      if (isChar) { const n = 'ch_' + G.char, w = SW(n) * OB_CS * (1 + 0.12 * squash), h = SH(n) * OB_CS * (1 - 0.12 * squash); spr(n, x - w / 2, y - h / 2, al, w, h); }
      else { const s = OB_BS * (1 + 0.15 * squash); spr('it_o2', x - s / 2, y - s / 2, al, s, s); }
    };
    const charOnTile = k % 2 === 0;
    if (th !== null) {
      const mx = piv[0] + Math.cos(th) * OB_L, my = piv[1] + Math.sin(th) * OB_L;
      body(!charOnTile, mx, my, 0);
      body(charOnTile, piv[0], piv[1], land);
    } else {                                                 // the end: both on the last two tiles
      body(charOnTile, piv[0], piv[1], land);
      body(!charOnTile, P[k - 1][0], P[k - 1][1], 0);
    }
    for (const p of o.pops) {
      const u = (G.t - p.t) / 0.6, [x, y] = P[p.k];
      label(p.res === 'perfect' ? TR('완벽', 'Perfect') : p.res === 'early' ? TR('빠름', 'Early') : p.res === 'late' ? TR('느림', 'Late') : p.s, x, y - 16 - u * 8, 7.5, 'center', al * (1 - u * u),
        p.res === 'perfect' ? '#ffe68a' : p.res === 'early' ? '#a8e0ff' : p.res === 'late' ? '#ffc08a' : '#ff8a9a');
    }
    ctx.restore();
    ctx.globalAlpha = 1;
    // words: the title and the song's name until the first tile; a count of three into it
    const B = OB.B;
    if (o.st === 'play' && t < OB.T[1]) {
      const a = Math.min(1, (G.t - o.stT) / 0.3) * Math.min(1, (OB.T[1] - t) / 0.3);
      label(TR('박자 맞춰 빙글빙글!', 'Spin to the beat!'), NWf / 2, 46, 15, 'center', a, '#ffe0a8');
      label(TR('돌던 쪽이 다음 칸에 닿을 때 터치 · 놓치면 한 바퀴 더 돌고 그 칸부터', 'Tap as the spinner reaches the next tile · miss and it goes round once more'), NWf / 2, 64, 7, 'center', a, '#ffffff');
      label(TR(OB.song.name, OB.song.en || OB.song.name), NWf / 2, 77, 7.5, 'center', a * 0.9, '#ffe0a8');
      if (t > 0) { const c = OB.hits[1] - Math.floor(t / B); if (c >= 1 && c <= 3) label(String(c), NWf / 2, 136, 20, 'center', a * (1 - 0.7 * ((t / B) % 1)), '#ffffff'); }
    }
    if (o.st === 'done') {
      const u = G.t - o.stT, a = Math.min(1, u / 0.25) * Math.max(0, Math.min(1, (OB_DONE - u) / 0.35));
      ctx.globalAlpha = a * 0.78; rrect(NWf / 2 - 110, 54, 220, 74, 8); ctx.fillStyle = '#1a0a14'; ctx.fill(); ctx.globalAlpha = 1;
      label(TR('통과!', 'Clear!'), NWf / 2, 70, 14, 'center', a, '#ffe0a8');
      const r = o.res, all = r.perfect + r.early + r.late + r.miss;
      label(TR(`완벽 ${r.perfect}  ·  빠름 ${r.early}  ·  느림 ${r.late}  ·  놓침 ${r.miss}`, `Perfect ${r.perfect}  ·  Early ${r.early}  ·  Late ${r.late}  ·  Miss ${r.miss}`), NWf / 2, 92, 8.5, 'center', a, '#ffffff');
      label(`${TR('정확도', 'Accuracy')} ${Math.round(100 * r.perfect / Math.max(1, all))}%  ·  ${TR('최대 콤보', 'Max combo')} ${o.maxCombo}  ·  +${PT(o.gain || 0)}`, NWf / 2, 110, 8.5, 'center', a, '#ffe68a');
    }
  }
  function drawSwirl(x, y, d) {                             // a swirl: the swing turns round here
    ctx.save(); ctx.translate(x, y); if (d < 0) ctx.scale(-1, 1);
    const r = 4.6;
    for (const [w, c] of [[3.2, '#1a0a14'], [1.8, '#c08cff']]) {
      ctx.beginPath(); ctx.arc(0, 0, r, -Math.PI * 0.15, Math.PI * 1.35); ctx.lineWidth = w; ctx.strokeStyle = c; ctx.stroke();
    }
    const ex = Math.cos(Math.PI * 1.35) * r, ey = Math.sin(Math.PI * 1.35) * r;
    ctx.beginPath(); ctx.moveTo(ex - 2.6, ey - 1.2); ctx.lineTo(ex + 1.6, ey - 2.6); ctx.lineTo(ex + 0.6, ey + 1.8); ctx.closePath();
    ctx.fillStyle = '#c08cff'; ctx.lineWidth = 1; ctx.strokeStyle = '#1a0a14'; ctx.fill(); ctx.stroke();
    ctx.restore();
  }

  // ---------------------------------------------------------------- the test pilot (?auto): looks a little ahead
  function pilot() {
    if (inWater()) { pilotSwim(); return; }
    G.pilotUp = false;
    const { jump, slide } = pilotWant();
    if (jump) pressed.jump = true;
    G.slideHeld = slide && !jump;
  }
  // (v60) what the pilot would do now (a jump, a slide), left undone: the first run's lessons stop the world there
  function pilotWant() {
    const px = G.x;
    let jump = false, slide = false;
    for (const o of G.obs) {
      const dx = o.x - (px + 10);                            // distance from the front of the player
      if (dx + o.w < -30 || dx > G.v * 0.9) continue;
      if (o.kind === 'pit') {
        const wide = o.w > G.v * 0.5, c = o.x + o.w / 2 - px;
        if (G.onGround && c < G.v * (wide ? 0.47 : 0.35) && o.x + o.w > px) jump = true;
        if (wide && !G.onGround && G.jumps === 1 && G.vy < 90 && o.x + o.w > px) jump = true;
        continue;
      }
      if (o.kind === 'door') {
        // which lip is shut while we pass it
        const vE = curSpeed(), t0 = (o.x - (px + SLW)) / vE, t1 = (o.x + o.w - (px - SLW)) / vE;
        if (t1 < 0) continue;
        let mb = 0, mt = 0;
        for (let k = 0; k <= 10; k++) { const [b, t] = doorExt(o, G.t + Math.max(0, t0 - 0.04 + (t1 - t0 + 0.08) * k / 10)); mb = Math.max(mb, b); mt = Math.max(mt, t); }
        if (mb > 0.2 && G.onGround && o.x + o.w / 2 - px < G.v * 0.3) jump = true;
        if (mt > 0.2 && dx < G.v * 0.3 && dx + o.w > -28) slide = true;
        continue;
      }
      if (o.kind === 'drop') { if (o.st === 'land' && dx + o.w / 2 < G.v * 0.294 && dx + o.w > 0 && G.onGround) jump = true; continue; }
      if (o.kind === 'spike') { if (o.st !== 'hidden' && dx + o.w / 2 < G.v * 0.294 && dx + o.w > 0 && G.onGround) jump = true; continue; }
      if (o.kind === 'shot') {
        const vc = G.v + (o.moving ? o.fly : 0);
        if (!o.low) { if (dx < vc * 0.3 && dx + o.w > -28) slide = true; }
        else if (dx + o.w / 2 < vc * 0.3 && dx + o.w > 0 && G.onGround) jump = true;
        continue;
      }
      if (o.kind === 'bob') { if (dx + o.w / 2 < G.v * 0.333 && dx + o.w > 0 && G.onGround) jump = true; continue; }
      if (o.kind === 'swim') {
        const vc = G.v + o.vx;
        if (!o.low) { if (dx < vc * 0.3 && dx + o.w > -28) slide = true; }
        else if (dx + o.w / 2 < vc * 0.333 && dx + o.w > 0 && G.onGround) jump = true;
        continue;
      }
      if (o.kind === 'float' || o.kind === 'hang') { if (dx < G.v * 0.28 && dx + o.w > -28) slide = true; }
      else {
        const tLead = o.kind === 'huge' ? PILOT_HUGE : o.kind === 'tall' ? 0.35 : 0.24;
        if (dx < G.v * tLead && dx + o.w > 0 && G.onGround) jump = true;
        if (o.kind === 'tall' && !G.onGround && G.jumps === 1 && (G.vy < 90 || (G.v > 420 && dx < G.v * 0.14 + 20)) && dx < G.v * 0.35 && dx + o.w > -4) jump = true;
        if (o.kind === 'huge' && !G.onGround && G.jumps === 1 && G.vy < 60 && dx + o.w > -4) jump = true;
        if (o.kind === 'tall' && !G.onGround && G.jumps === 2 && G.vy < 0 && dx < G.v * 0.2 && dx + o.w > -4) jump = true;      // a third to save it
        if (o.kind === 'huge' && !G.onGround && G.jumps === 2 && G.vy < 60 && dx + o.w > -4) jump = true;
      }
    }
    return { jump, slide };
  }

  // ---------------------------------------------------------------- (v60) the first run's lessons
  // The first time the run needs a jump, a second jump (in the air), a third, a slide, the world stops just there, the
  // button to press glows, a word says what to do; pressing it (holding, for the slide) lets it go on, and that is done.
  // Tips along the way that do not stop it: at the start (the health goes down by itself), the first heal in sight, the
  // first coins towards the booster. Once (kept: bodyrun.tutDone); not in tests unless ?tut
  const TUT_STEPS = ['jump', 'jump2', 'jump3', 'slide'];
  function tutWanted() {
    if (qs.has('tut')) return true;
    if (CAPTURE || AUTO) return false;
    try { return localStorage.getItem('bodyrun.tutDone') !== '1'; } catch (e) { return false; }
  }
  function tutEnd(all = true) {                               // the lessons over (the tips go on a while, unless all)
    if (G.tut) { G.tut.on = false; if (all) G.tut.tipsOn = false; }
    if (!qs.has('tut')) { try { localStorage.setItem('bodyrun.tutDone', '1'); } catch (e) { /* storage off */ } }
  }
  // true: the world stands still this step
  function tutStep(dt) {
    const T = G.tut; if (!T || !T.on || busy() || inWater() || G.boost > 0) return false;
    T.t0 += dt;
    if (T.wait) {
      const ok = T.wait === 'slide' ? G.slideHeld : pressed.jump;
      if (!ok) return true;
      T.done[T.wait] = true; T.wait = null;
      if (TUT_STEPS.every((k) => T.done[k]) || (T.done.jump && T.done.jump2 && T.done.slide && G.runT > 60)) tutEnd(false);
      return false;
    }
    const w = pilotWant();
    const need = w.slide && !w.jump ? 'slide' : w.jump ? (G.onGround ? 'jump' : G.jumps === 1 ? 'jump2' : G.jumps === 2 ? 'jump3' : null) : null;
    if (need && !T.done[need]) { T.wait = need; T.waitT = performance.now() / 1000; pressed.jump = false; return true; }
    if (G.runT > 150) tutEnd(false);                         // (enough: the rest it will find)
    return false;
  }
  function drawTut() {
    const T = G.tut; if (!T || !(T.on || T.tipsOn) || busy() || inWater()) return;
    const by = NH - BTN_M - BTN_R, bl = BTN_M + BTN_R, br = NW - BTN_M - 2 - BTN_R, now = performance.now() / 1000;
    const box = (t1, t2, y, a = 1) => {
      ctx.font = '900 10px system-ui, -apple-system, "Noto Sans KR", sans-serif'; const w1 = ctx.measureText(t1).width;
      ctx.font = '900 7px system-ui, -apple-system, "Noto Sans KR", sans-serif'; const w2 = t2 ? ctx.measureText(t2).width : 0;
      const bw = Math.min(NW - 20, Math.max(w1, w2) + 22), bh = t2 ? 30 : 19;
      ctx.globalAlpha = 0.82 * a; rrect(NW / 2 - bw / 2, y, bw, bh, 8); ctx.fillStyle = '#1a0a14'; ctx.fill(); ctx.globalAlpha = a;
      ctx.lineWidth = 1; ctx.strokeStyle = 'rgba(255,224,168,0.8)'; ctx.stroke(); ctx.globalAlpha = 1;
      label(t1, NW / 2, y + 9.5, 10, 'center', a, '#ffe0a8'); if (t2) label(t2, NW / 2, y + 21.5, 7, 'center', a, '#ffffff');
    };
    if (T.wait && T.on) {
      ctx.globalAlpha = 0.35; ctx.fillStyle = '#05030c'; ctx.fillRect(0, 0, NW, NH); ctx.globalAlpha = 1;
      const isJ = T.wait !== 'slide', bx = isJ ? (SET.swap ? br : bl) : (SET.swap ? bl : br), pulse = (now - T.waitT) % 1;
      button(bx, by, isJ ? TR('점프', 'Jump') : TR('슬라이드', 'Slide'), false);
      for (const q of [pulse, (pulse + 0.5) % 1]) { ctx.globalAlpha = 1 - q; ctx.beginPath(); ctx.arc(bx, by, BTN_R + 2 + q * 14, 0, 6.2832); ctx.lineWidth = 2.2; ctx.strokeStyle = '#ffe14a'; ctx.stroke(); }
      ctx.globalAlpha = 1;
      const msg = { jump: [TR('점프 버튼을 눌러요!', 'Press Jump!'), TR('장애물을 뛰어넘어요', 'Hop over it')],
        jump2: [TR('한 번 더 눌러요!', 'Press it again!'), TR('공중에서 누르면 2단 점프', 'In the air: a double jump')],
        jump3: [TR('한 번 더!', 'Once more!'), TR('세 번째 점프로 더 높이', 'A third jump goes higher')],
        slide: [TR('슬라이드 버튼을 누르고 있어요!', 'Hold Slide!'), TR('누르는 동안 숙여서 지나가요', 'Duck under while you hold it')] }[T.wait];
      box(msg[0], msg[1], 50);
      return;
    }
    // the tips that do not stop it (each once, for a few seconds)
    const tip = (k, on, t1, t2) => { if (on && !T.tips[k]) T.tips[k] = now; const s0 = T.tips[k]; if (!s0) return false; const v = now - s0; if (v > 3.6) return false; box(t1, t2, 50, Math.min(1, v / 0.25, (3.6 - v) / 0.4)); return true; };
    if (tip('start', true, TR('몸속을 달려요!', 'Run through the body!'), TR('체력은 시간이 지나면 줄어들어요', 'Your health goes down as you run'))) return;
    if (tip('heal', G.items.some((it) => it.kind === 'heal' && !it.taken && it.x < G.x + NW * 0.8), TR('회복 아이템!', 'A heal!'), TR('먹으면 체력이 차요', 'Take it to fill your health'))) return;
    tip('o2', G.o2n >= 12, TR('아이템을 모으면 부스터!', 'Collect for the booster!'), TR('게이지가 차면 빠르고 무적', 'A full gauge: fast and unstoppable'));
    if (['start', 'heal', 'o2'].every((k) => T.tips[k] && now - T.tips[k] > 3.6) || G.runT > 150) T.tipsOn = false;
  }

  // ---------------------------------------------------------------- the baseball stage (in the jejunum)
  // A ballpark of the gut's own tissue, seen from behind home plate. A macrophage on the mound throws five pitches; the
  // runner stands up at the plate on two legs with a bat. Drag on the left to put the bat's ring where the ball will cross
  // (a white ring shows the spot once it is thrown, closing in as it comes), tap on the right as it gets there. The ball
  // in the ring, on time, is a home run (points: each one); in the ring but a little early or late, a foul (off to the
  // left or right); anything else a miss (a swing: 헛스윙, none: 스트라이크). Five pitches, whatever happens (no
  // strike-outs); only the home runs score (no harm either way). The swing button swings any time (a
  // practice swing before the throw, to get the feel; only a swing at the ball in flight counts). The game's own clock
  // (no song here; the run's music goes on).
  const BBF = M.bb || { mound: [210, 100], plate: [210, 172] };                 // the field picture's numbers (baseball.py)
  const BB_N = 5;                                                               // pitches
  const BB_ZW = 44, BB_ZH = 50, BB_ZY = 128;                                    // the strike zone: width, height, centre y
  const BB_CR = 9, BB_BR = 4.6;                                                 // (the old ring's size), the ball at the plate
  // the bat's aim: a bat's shape BB_AL long, slanting up to the right (the knob low on the left, the barrel high on the
  // right), the aiming point at the middle of its barrel (BB_AS along it); thin at the grip, swelling to a fat barrel
  const BB_AL = 44, BB_AS = 0.75, BB_ANG = -0.38;
  const BB_AX = Math.cos(BB_ANG), BB_AY = Math.sin(BB_ANG);
  const batRad = (t) => { const e = Math.max(0, Math.min(1, (t - 0.22) / 0.5)); return t < 0.04 ? 2.8 : 1.9 + (6.6 - 1.9) * e * e * (3 - 2 * e); };
  // how far the ball's middle is outside the bat's aim (0 on it), the ball being (dx, dy) from the aiming point; it is
  // hit within half the ball's size of it
  function bbOff(dx, dy) {
    const u = dx * BB_AX + dy * BB_AY + BB_AS * BB_AL, v = -dx * BB_AY + dy * BB_AX;      // along the bat from the knob, across it
    if (u < 0) return Math.max(0, Math.hypot(u, v) - batRad(0));
    if (u > BB_AL) return Math.max(0, Math.hypot(u - BB_AL, v) - batRad(1));
    return Math.max(0, Math.abs(v) - batRad(u / BB_AL));
  }
  const BB_WIN = 0.12, BB_FOUL = 0.2;                                           // timing (s): a home run this early or late; a foul
  const BB_INTRO = 2.2, BB_WIND = 1.0, BB_AFTER = 1.5, BB_AFTER_HR = 2.4, BB_END = 2.2;
  // the pitches (thrown from the mound farther off: 1.1 times the way on the screen at the same speed): flight time,
  // the break at the plate (units; sideways ones go either way), how late it comes (the
  // power of the flight it grows with: 2 early and long, 6 all at the end), and a rise on the way (the curve's arc)
  const BB_TYPES = [                                                        // (T: the flight, v34's / 0.9 / 0.95: 10% then 5% slower)
    { name: TR('직구', 'Fastball'), T: 0.398, bx: 0, by: 0, pw: 3, rise: 0 },
    { name: TR('커브', 'Curveball'), T: 0.561, bx: 14, by: 26, pw: 2, rise: 16 },              // up first, then a long drop
    { name: TR('포크볼', 'Forkball'), T: 0.444, bx: 0, by: 34, pw: 7, rise: 0 },             // looks straight, falls off the table at the end
    { name: TR('슬라이더', 'Slider'), T: 0.456, bx: 32, by: 4, pw: 3, rise: 0 },           // late, sideways
    { name: TR('체인지업', 'Changeup'), T: 0.573, bx: 3, by: 9, pw: 2, rise: 0 },            // slow, sinking a little
  ];
  const BB_PTS = { hr: 1000 };
  // the hit: the bat meets the ball BB_DS after the tap (the swing down), the game stops a moment there (hit-stop,
  // longer for a home run) while a crack bursts out of the meeting point with rings spreading like a sound wave, and the
  // ball flies off: to the left, the middle or the right at random (a foul: off to the side, left if early, right if late)
  const BB_DS = 0.035, BB_HOLD = { hr: 0.15, foul: 0.08 }, BB_FX = 0.55;
  const BB_SWING = 0.65;                                                        // a whole swing, down, round and back
  const BB_PS = BBF.pscale || 1.45;                                            // the pitcher's picture, scaled (as far off as the mound)
  // the batter: the runner's own pictures from six sides (front 0, front-right 45, right 90, back-right 135, back 180,
  // back-left 225; 270 and 315 are 90 and 45 turned over), standing on its feet left of the plate. It waits turned
  // towards the pitcher (135) and turns with the swing (180 at the hit, 225 after), the bat in two fists of its colour
  const BB_BAT = 60, BB_FIST = 4.4;
  const BAT_COL = { tardigrade: '#f0b870', lacto: '#7cd04a', paramecium: '#3aa8e8', amoeba: '#b060d8', daphnia: '#e8b060',
    pillbug: '#a4a6ba', ladybug: '#3a3438', jelly: '#f4a0d0', sub: '#f4c430', phage: '#c0b4e8' };
  const bbKeys = new Set();
  function startBaseball() {
    holdBoost();
    G.obs = G.obs.filter((o) => o.x + o.w < G.x - 12);
    G.items = G.items.filter((i) => i.x < G.x - 12 || i.taken);
    G.bb = { st: 'intro', stT: G.t, inT: G.t, k: 0, res: [], hr: false, cur: [0, 0], drag: null, p: null, swingT: -9, gain: 0, msg: null, ball: null, pend: null, hold: 0, fx: null };
    G.slideHeld = false; held.clear(); pressed.jump = false; bbKeys.clear();
    bbMusic();
  }
  // the stage's music: the running music fades, the ballpark's comes in (when its file is decoded; tried again each step)
  function bbMusic() {
    const b = G.bb; if (!b || b.music || CAPTURE || !STAGES.bb || !SND.live()) return;
    if (!SND.ready(STAGES.bb)) { SND.prepare(STAGES.bb).catch(() => {}); return; }
    b.music = SND.playLoop(STAGES.bb); SND.ambience(false);
  }
  function endBaseball() {
    if (G.bb && G.bb.music) { SND.stopLoop(0.8); SND.ambience(true); }
    bankGame(G.bb); G.bb = null; G.games = (G.games || 0) + 1; resumeBoost();
    G.genX = Math.max(G.genX, G.x + NW * 0.8);
    G.banner = G.t;
  }
  // ---------------------------------------------------------------- the end of the body (stage 1 to 2): the end of the
  // anus is packed full of stool, floor to roof; the runner, at full speed, jumps and goes smack into its middle, stuck
  // (v37: no braking); the whole lot is pushed out (to the right) and straight into the toilet: under its water the
  // runner comes in from the top left with a lump of it (plop), sinks to the bottom, the lumps drift off and stage 2
  // begins. Times (s) from the moment it sticks
  const CUT_FACE = 200;                              // the packed stool's face: this far before the end of the anus
  const CUT_PAD = 44;                                // (its picture starts this far left of the face: the front logs' ends at the floor)
  const CUT_IN = 3;                                  // how far past the face the runner's middle goes in (about half of it in)
  const CUT_CLEAR = 150, CUT_AFTER = 300;           // nothing set out from the jump's start (less this) to this far into stage 2
  const CUT_TJ = JUMP / GRAV;                        // the jump into it: a single jump's way up (0.36 s), at whatever speed
  const CUT_Y = JUMP * JUMP / (2 * GRAV);            // ... its top (59): the runner's middle at the wall's middle
  const CUT_PUSH = [0.3, 0.95], CUT_SWAP = 0.9, CUT_DIVE = [0.95, 1.0], CUT_HIT = 0.08, CUT_END = 2.0;
  // the big chunk that comes into the toilet with the runner, stuck on its back (x, up: in the runner's size; turn)
  const CUT_STUCK = [['cut_chunk', -0.75, 0.5, 0.12]];
  const CUT_LUMP = 3;                                // (v48) the lump 3 times as big: the runner stuck in front of it, its bottom at the feet
  const cutOn = () => G.cut || (G.station >= 0 && COURSE[G.station][5] === STAGE2 - 1);      // in the anus, or in the cut
  const cutFaceX = () => (G.cut ? G.cut.faceX : Math.floor(G.x / LAP) * LAP + S2_X - CUT_FACE);
  function cutCheck() {
    const s = stationAt(G.x), stopLx = S2_X - CUT_FACE + CUT_IN, sp = curSpeed();
    if (stopLx - s.lx <= Math.max(4, sp * CUT_TJ)) startCut(s.lap * LAP + stopLx, sp);
  }
  function startCut(stopX, sp) {
    holdBoost();
    const faceX = stopX - CUT_IN;
    stopX = Math.max(stopX, G.x);
    const v0 = Math.max(sp, 60), d = stopX - G.x, th = d / v0;
    // the way there: on at the same speed, up and (wherever it is now, on the floor or in the air) into the middle
    const y0 = Math.max(0, G.y), vy = th > 0.02 ? (CUT_Y - y0 + 0.5 * GRAV * th * th) / th : 0;
    G.cut = { t0: G.t, x0: G.x, y0, vy, v0, th, stopX, faceX, ts: 0, lap: Math.floor(faceX / LAP), swap: 0, splash: 0, landed: 0 };
    if (G.onGround) SND.play('jump1');
    G.onGround = false; G.slide = false; G.jumps = 1; G.pitObj = null; G.pitHoldT = 0;
    G.obs = G.obs.filter((o) => o.x + o.w < G.x - 12);
    G.items = G.items.filter((i) => i.x < G.x - 12 || i.taken);
    G.slideHeld = false; held.clear(); pressed.jump = false;
  }
  function stepCut() {
    const c = G.cut;
    pressed.jump = false; G.slideHeld = false;
    if (!c.ts) {                                              // the jump, at full speed, to the stool's middle
      const t = G.t - c.t0;
      if (t >= c.th) { G.x = c.stopX; G.y = CUT_Y; G.vy = 0; c.ts = G.t; SND.play('splat'); }   // smack: stuck in it
      else { G.x = c.x0 + c.v0 * t; G.y = c.y0 + c.vy * t - 0.5 * GRAV * t * t; G.vy = c.vy - GRAV * t; }
      G.onGround = false;
      return;
    }
    const u = G.t - c.ts;
    if (!c.swap) { G.y = CUT_Y; G.vy = 0; G.onGround = false; }       // held there while it is all pushed out
    if (!c.swap && u >= CUT_SWAP) {                           // out of the screen: on to the start of stage 2
      c.swap = G.t;
      G.x = c.lap * LAP + S2_X + 1; G.y = 0; G.vy = 0; G.onGround = true; G.jumps = 0;
      G.obs = []; G.items = []; G.genX = G.x + NW * 0.8;
    }
    if (c.swap && !c.banner) { c.banner = true; G.banner = G.t; }
    if (!c.splash && u >= CUT_DIVE[0] + CUT_HIT) {           // through the water's surface
      c.splash = G.t; SND.play('splash');
      const R = rng(Math.floor(G.t * 1000) + 7);
      c.bub = Array.from({ length: 26 }, (_, i) => ({ k: 0.06 + 0.5 * (i / 26) ** 1.3, dx: (R() * 2 - 1) * 7, dy: (R() * 2 - 1) * 6, r: 0.8 + R() * 1.8, w: R() * 6 }));
      c.drops = Array.from({ length: 12 }, () => ({ vx: (R() * 2 - 1) * 70, vy: -60 - R() * 70, r: 0.9 + R() * 1.2 }));
    }
    if (!c.landed && u >= CUT_DIVE[0] + CUT_DIVE[1]) c.landed = G.t;
    if (u >= CUT_END) cutDone();
  }
  function cutDone() {                                        // stage 2 goes on (the lumps drift off a moment longer)
    const c = G.cut; if (!c) return;
    if (!c.swap) { G.x = c.lap * LAP + S2_X + 1; G.y = 0; G.vy = 0; G.onGround = true; G.obs = []; G.items = []; G.genX = G.x + NW * 0.8; }
    G.cut = null; G.cutTail = { landed: c.landed || G.t, splash: c.splash, bub: c.bub || [], drops: c.drops || [] };
    if (G.theme !== COURSE[S2_I][3]) G.station = -1;
    G.slow = 1; resumeBoost();                                 // (on at the water's speed at once: no slow start)
    G.genX = Math.max(G.genX, G.x + NW * 0.8);
  }
  function sprRot(name, cx, cy, rot, alpha = 1, k = 1) {
    const w = SW(name) * k, h = SH(name) * k;
    ctx.save(); ctx.translate(cx, cy); ctx.rotate(rot); spr(name, -w / 2, -h / 2, alpha, w, h); ctx.restore();
  }
  const cutReady = () => M.sprites.cut_wall && bmp[M.sprites.cut_wall.f];
  const cutPush = (u) => { const k = Math.max(0, Math.min(1, (u - CUT_PUSH[0]) / (CUT_PUSH[1] - CUT_PUSH[0]))); return k * k * (NWf + 400); };
  const cutDX = () => (G.cut && G.cut.ts && !G.cut.swap ? cutPush(G.t - G.cut.ts) : 0);
  // stuck: a little shake as it goes in
  const cutShake = () => { if (!G.cut || !G.cut.ts || G.cut.swap) return 0; const u = G.t - G.cut.ts; return u < 0.25 ? 0.7 * Math.sin(u * 110) * (1 - u / 0.25) : 0; };
  // the packed stool (world: drawn after the runner, so that going in, its front half is in it), pushed along with it
  function drawCutBack(cam) {
    if (!cutOn() || (G.cut && G.cut.swap) || !cutReady()) return;
    const x = cutFaceX() - CUT_PAD - cam + cutDX();
    if (x > NWf || x + SW('cut_wall') < 0) return;
    spr('cut_wall', x, GY + 2 - SH('cut_wall'));
  }
  // the runner with its lumps on, in one piece (into the toilet)
  const lumpAt = (cx, fy) => [cx + 16.7 * CUT_LUMP, fy - 17.7 * CUT_LUMP];   // its picture's middle: the runner in its lower left, its bottom (the lump drawn, not the picture's margin) at the feet
  function drawMass(cx, fy, rot) {
    // (v48) the big lump behind, the runner in front of its lower left, a piece of it stuck on the runner's back; the
    // whole tumbling round the big lump's middle
    const n = 'ch_' + G.char, w = SW(n), h = SH(n), [lx, ly] = lumpAt(cx, fy);
    ctx.save(); ctx.translate(lx, ly); ctx.rotate(rot); ctx.translate(-lx, -ly);
    sprRot('cut_chunk', lx, ly, 0.06, 1, CUT_LUMP);
    spr(n, cx - w / 2, fy - h);
    for (const [ln, dx, up, r] of CUT_STUCK) sprRot(ln, cx + dx * w, fy - up * h, r);
    ctx.restore();
  }
  // into the toilet: from the top left, through the surface, down to the bottom (feet at fy)
  function cutDiveAt(k) {
    const e = 1 - (1 - k) * (1 - k);
    return [PX - 62 + 62 * e, -12 + (GY + 1 + 12) * e, 0.75 * (1 - k) * (1 - k)];
  }
  function drawDive() {
    const c = G.cut, k = Math.max(0, Math.min(1, (G.t - c.ts - CUT_DIVE[0]) / CUT_DIVE[1]));
    if (G.t - c.ts < CUT_DIVE[0]) return;
    const [x, fy, rot] = cutDiveAt(k);
    drawMass(x, fy, rot);
  }
  // over the scene: the splash at the surface, the bubbles of the way down, then the stage's title
  function drawCut() {
    const c = G.cut, tail = G.cutTail;
    world();
    const sp = c ? c.splash : tail ? tail.splash : 0, bub = c ? c.bub : tail ? tail.bub : null, drops = c ? c.drops : tail ? tail.drops : null;
    if (sp && bub) {
      const v = G.t - sp, [sx] = cutDiveAt(CUT_HIT / CUT_DIVE[1]), sy = CEIL;
      for (const d of drops) {                           // thrown up above the water, falling back
        const x = sx + d.vx * v, y = sy - 1 + d.vy * v + 230 * v * v;
        if (y > sy || v > 0.8) continue;
        ctx.beginPath(); ctx.arc(x, y, d.r + 0.4, 0, 6.29); ctx.fillStyle = '#2a5a62'; ctx.fill();
        ctx.beginPath(); ctx.arc(x, y, d.r, 0, 6.29); ctx.fillStyle = '#d6f6f8'; ctx.fill();
      }
      if (v < 0.6) {                                     // the water broken at the surface: a white burst, spreading rings,
        const k = v / 0.6;                               // and the hollow it leaves behind going down, closing
        ctx.globalAlpha = 1 - k;
        for (let j = 0; j < 9; j++) {
          const a = (j / 8 - 0.5) * 2.8, r = (4 + 13 * Math.sqrt(k)) * (1 - 0.3 * Math.abs(j / 8 - 0.5));
          ctx.beginPath(); ctx.arc(sx + Math.sin(a) * r * 1.5, sy + 1 + Math.abs(Math.cos(a)) * r * 0.6, 2.8 + 3 * (1 - k), 0, 6.29);
          ctx.fillStyle = '#ffffff'; ctx.fill(); ctx.lineWidth = 0.5; ctx.strokeStyle = '#3a6a72'; ctx.stroke();
        }
        const [x1, y1] = cutDiveAt(Math.min(1, (v + CUT_HIT) / CUT_DIVE[1] * 0.6));
        ctx.globalAlpha = 0.55 * (1 - k); ctx.lineCap = 'round';
        ctx.beginPath(); ctx.moveTo(sx, sy + 2); ctx.lineTo(x1, y1 - 14); ctx.lineWidth = 7 * (1 - k); ctx.strokeStyle = '#ffffff'; ctx.stroke();
        for (let r = 0; r < 2; r++) {
          const q = (v - r * 0.12) / 0.45; if (q <= 0 || q >= 1) continue;
          ctx.globalAlpha = 1 - q; ctx.beginPath(); ctx.ellipse(sx, sy + 0.5, 8 + 50 * q, 1 + 2.5 * q, 0, 0, 6.29); ctx.lineWidth = 1.2; ctx.strokeStyle = '#ffffff'; ctx.stroke();
        }
        ctx.globalAlpha = 1;
      }
      for (const b of bub) {                             // bubbles left along the way down, rising and gone
        const t0 = b.k * CUT_DIVE[1] - CUT_HIT, q = (v - t0) / 0.9; if (q <= 0 || q >= 1) continue;
        const [x0, y0] = cutDiveAt(b.k), x = x0 + b.dx + Math.sin(q * 9 + b.w) * 1.2, y = y0 - 8 + b.dy - 22 * q;
        if (y < CEIL + 2) continue;
        ctx.globalAlpha = 1 - q * q; ctx.beginPath(); ctx.arc(x, y, b.r * (1 + 0.3 * q), 0, 6.29); ctx.fillStyle = 'rgba(235,252,252,0.6)'; ctx.fill();
        ctx.lineWidth = 0.45; ctx.strokeStyle = '#2a5a62'; ctx.stroke();
      }
      ctx.globalAlpha = 1;
    }
    const t0 = c ? (c.landed || null) : tail ? tail.landed : null;   // the title, from the landing
    if (t0 !== null) {
      const v = G.t - t0 + 0.4, ta = v < 0 ? 0 : v < 0.25 ? v / 0.25 : v < 1.6 ? 1 : Math.max(0, 1 - (v - 1.6) / 0.4);
      if (ta > 0) label(TR('스테이지 2', 'Stage 2'), NWf / 2, 70, 20, 'center', ta, '#ffffff');
      if (tail && v > 2.2) G.cutTail = null;
    }
  }
  // under the water at the start of stage 2 (world: after the runner): the lumps drift up and away off it
  function drawCutDriftPiece() {                            // (the piece on the runner's back: in front of it)
    const t0 = G.cut ? G.cut.landed : G.cutTail ? G.cutTail.landed : 0;
    if (!t0 || !cutReady()) return;
    const v = G.t - t0, n = 'ch_' + G.char, w = SW(n), h = SH(n), D = 1.1;
    if (v < 0 || v >= D) return;
    for (const [ln, dx, up, r] of CUT_STUCK) { const k = v / D; sprRot(ln, PX - G.nudge + dx * w - 22 * k, GY + 1 - G.y - up * h - 26 * k, r - 0.5 * k, 1 - k * k); }
  }
  function drawCutDrift() {
    const t0 = G.cut ? G.cut.landed : G.cutTail ? G.cutTail.landed : 0;
    if (!t0 || !cutReady()) return;
    const v = G.t - t0, n = 'ch_' + G.char, w = SW(n), h = SH(n), D = 1.1;
    if (v < 0 || v >= D) return;
    { const k = v / D, [lx, ly] = lumpAt(PX - G.nudge, GY + 1 - G.y);       // the big lump lets go and floats up and back
      sprRot('cut_chunk', lx - 40 * k, ly - 34 * k, 0.06 - 0.3 * k, 1 - k * k, CUT_LUMP); }
  }
  const bbZone = () => [NWf / 2, BB_ZY];
  function bbPitch() {                                                         // the next pitch: its kind, where it crosses
    const b = G.bb, ty = BB_TYPES[Math.floor(Math.random() * BB_TYPES.length)];
    const side = Math.random() < 0.5 ? -1 : 1;
    const tx = (Math.random() * 2 - 1) * BB_ZW * 0.38, tyy = (Math.random() * 2 - 1) * BB_ZH * 0.36;
    b.p = { type: ty, rel: G.t + BB_WIND, arr: G.t + BB_WIND + ty.T, tx, ty: tyy, bx: ty.bx * side, by: ty.by, swung: false, done: false };
    b.st = 'wind'; b.stT = G.t; b.ball = null; b.msg = null;
  }
  function bbPitcherFrame() {                                                  // set, wind-up, release, follow-through
    const b = G.bb, p = b.p, u = G.t - b.stT;
    if (b.st === 'wind') return u < 0.3 ? 0 : u < 0.8 ? 1 : 2;
    if (b.st === 'fly') return G.t - p.rel < 0.12 ? 2 : 3;
    if (b.st === 'after') return u < 0.6 ? 3 : 0;
    return 0;
  }
  function bbPitcherAt() { const [zx] = bbZone(); return [zx + (BBF.mound[0] - 210), BBF.mound[1] - 1]; }
  function bbHand(f) {
    const s = M.sprites['bb_p' + f], [mx, my] = bbPitcherAt();
    if (!s || !s.hand) return [mx, my - 30];
    return [mx + (s.hand[0] - s.foot[0]) * BB_PS, my + (s.hand[1] - s.foot[1]) * BB_PS];
  }
  // the ball in flight: s from 0 at the release to 1 at the plate (and on past it, into the catcher's mitt)
  function bbBallAt(t) {
    const p = G.bb.p, s = Math.max(0, (t - p.rel) / p.type.T);
    const [rx, ry] = bbHand(2), [zx, zy] = bbZone(), P = [zx + p.tx, zy + p.ty];
    const e = s * s * 0.35 + s * 0.65;                                         // a little faster as it comes
    const ax = P[0] - p.bx, ay = P[1] - p.by;                                  // aimed off by the break, which comes late
    const pw = p.type.pw, f = s <= 1 ? Math.pow(s, pw) : 1 + pw * (s - 1);     // (past the plate: on in a line)
    const x = rx + (ax - rx) * e + p.bx * f, y = ry + (ay - ry) * e + p.by * f - p.type.rise * Math.sin(Math.PI * Math.min(1, s));
    return { x, y, r: 1.3 + (BB_BR - 1.3) * Math.pow(s, 1.6), s };
  }
  function bbSwing() {
    const b = G.bb; if (!b || b.st === 'done') return;
    const p = b.p, live = b.st === 'fly' && !p.swung && !p.done;
    if (!live) {                                                               // a practice swing (once the last one is round)
      if (G.t - b.swingT >= BB_SWING) { b.swingT = G.t; SND.play('bbSwing'); }
      return;
    }
    p.swung = true; b.swingT = G.t; SND.play('bbSwing');
    const dt = G.t - p.arr, d = bbOff(p.tx - b.cur[0], p.ty - b.cur[1]);
    if (Math.abs(dt) > BB_FOUL || d > BB_BR / 2) return;                       // a miss is told when the ball goes by
    b.pend = { res: Math.abs(dt) <= BB_WIN ? 'hr' : 'foul', dt, d, t: G.t + BB_DS };
  }
  // where the ball is met: at the plate, or where it was at the tap if that was late; it waits there for the bat
  const bbMeetT = () => Math.min(G.t, Math.max(G.bb.p.arr, G.bb.swingT));
  function bbContact() {                                                      // the bat meets the ball (BB_DS after the tap)
    const b = G.bb, q = b.pend, B = bbBallAt(bbMeetT()), at = [B.x, B.y];
    b.pend = null;
    bbResult(q.res, at, q.dt, q.d);
    b.hold = BB_HOLD[q.res]; b.fx = { at, res: q.res, age: 0 };
  }
  function bbResult(res, at, dt = 0, d = 0) {
    const b = G.bb, p = b.p;
    p.done = true; p.res = res; p.dt = dt; p.d = d; b.res.push(res); b.st = 'after'; b.stT = G.t;
    b.ball = null;
    if (at) {
      const fly = { from: at, t0: G.t, res }, [zx] = bbZone(), dir = [-1, 0, 1][Math.floor(Math.random() * 3)];
      if (res === 'hr') { fly.to = [zx + dir * 125 + (Math.random() * 2 - 1) * 12, -24]; fly.dur = 0.85; fly.h = 60; fly.dir = dir; }
      else { const sd = dt < 0 ? -1 : 1; fly.to = [at[0] + sd * (190 + Math.random() * 40), 40 + Math.random() * 30]; fly.dur = 0.4; fly.h = 22; }
      b.ball = fly;
    }
    b.msg = { s: { hr: TR('홈런!', 'Home run!'), foul: TR('파울', 'Foul'), whiff: TR('헛스윙', 'Swing and miss'), strike: TR('스트라이크', 'Strike') }[res], t: G.t, res };
    if (res === 'hr') { b.streak = (b.streak || 0) + 1; b.bestRun = Math.max(b.bestRun || 0, b.streak); b.msg.k = b.streak; b.msg.pts = comboPts(BB_PTS.hr, b.streak); b.gain += b.msg.pts; b.hr = true; SND.play('bbHR'); buzz([40, 30, 70]); }
    else if (res === 'foul') { b.streak = 0; SND.play('bbHit'); buzz(35); }
    else { b.streak = 0; SND.play('bbMitt'); }
  }
  function stepBaseball(dt) {                                                 // (each check reads the clock afresh: one step can change the state)
    const b = G.bb;
    if (!b.music && b.st !== 'done') bbMusic();
    if (bbKeys.size) {                                                         // the arrow keys move the bat's ring
      const k = 95 * dt, mx = BB_ZW / 2 + 6, my = BB_ZH / 2 + 6;
      if (bbKeys.has('L')) b.cur[0] -= k; if (bbKeys.has('R')) b.cur[0] += k;
      if (bbKeys.has('U')) b.cur[1] -= k; if (bbKeys.has('D')) b.cur[1] += k;
      b.cur[0] = Math.max(-mx, Math.min(mx, b.cur[0])); b.cur[1] = Math.max(-my, Math.min(my, b.cur[1]));
    }
    if (b.st === 'intro') { if (G.t - b.stT > BB_INTRO) bbPitch(); return; }
    if (b.st === 'wind' && G.t >= b.p.rel) { b.st = 'fly'; b.stT = G.t; SND.play('bbPitch'); }
    if (b.st === 'fly') {
      const p = b.p;
      if (AUTO && !window.__noAuto) {                                         // the test pilot: on the spot, on time
        if (G.t >= p.arr - p.type.T * 0.5) b.cur = [p.tx, p.ty];
        if (G.t >= p.arr) bbSwing();
      }
      if (b.pend && G.t >= b.pend.t) bbContact();
      if (!p.done && !b.pend && G.t > p.arr + BB_FOUL) bbResult(p.swung ? 'whiff' : 'strike', null);
    }
    if (b.st === 'after' && G.t - b.stT > (b.p && b.p.res === 'hr' ? BB_AFTER_HR : BB_AFTER)) {
      if (b.res.length >= BB_N) { b.st = 'done'; b.stT = G.t; if (!b.hr) SND.play('bbOut'); }      // (all five thrown)
      else { b.k++; bbPitch(); }
    }
    if (b.st === 'done' && G.t - b.stT > BB_END) endBaseball();
  }
  function bbDown(id, x, y) {
    const b = G.bb; if (!b) return;
    if (x > NW * 0.6) { bbSwing(); return; }
    b.drag = { id, x, y };
  }
  function bbMove(id, x, y) {
    const b = G.bb; if (!b || !b.drag || b.drag.id !== id) return;
    const k = 1.725, mx = BB_ZW / 2 + 6, my = BB_ZH / 2 + 6;              // (1.15 at first; half again as quick)
    b.cur[0] = Math.max(-mx, Math.min(mx, b.cur[0] + (x - b.drag.x) * k));
    b.cur[1] = Math.max(-my, Math.min(my, b.cur[1] + (y - b.drag.y) * k));
    b.drag.x = x; b.drag.y = y;
  }
  function bbUp(id) { const b = G.bb; if (b && b.drag && b.drag.id === id) b.drag = null; }
  const BB_KEY = { ArrowLeft: 'L', KeyA: 'L', ArrowRight: 'R', KeyD: 'R', ArrowUp: 'U', KeyW: 'U', ArrowDown: 'D', KeyS: 'D' };

  // ---- drawing
  // the bat: a big round wooden club, thin at the grip and swelling to a fat barrel with a domed end; shaded as a
  // cylinder with a long shine down it (z: towards us, a little thicker)
  function drawBat(hx, hy, vx, vy, z) {                                         // from the knob (hx, hy) along (vx, vy)
    const l = Math.hypot(vx, vy), k = 1 + 0.25 * z;
    const rad = (t) => { const e = Math.max(0, Math.min(1, (t - 0.22) / 0.58)); return (2.1 + (5.8 - 2.1) * e * e * (3 - 2 * e)) * k; };
    if (l < 1) { ctx.beginPath(); ctx.arc(hx, hy, rad(1), 0, 6.29); ctx.fillStyle = '#d89a54'; ctx.fill(); ctx.lineWidth = 1.2; ctx.strokeStyle = '#1a0a14'; ctx.stroke(); return; }
    const ux = vx / l, uy = vy / l, nx = -uy, ny = ux, N = 20, R1 = rad(1), L = l - R1;   // the dome's centre is R1 short of the tip
    const at = (t, side) => { const r = rad(t), d = L * t; return [hx + ux * d + nx * r * side, hy + uy * d + ny * r * side]; };
    ctx.beginPath();
    for (let i = 0; i <= N; i++) { const [x, y] = at(i / N, 1); if (i) ctx.lineTo(x, y); else ctx.moveTo(x, y); }
    ctx.arc(hx + ux * L, hy + uy * L, R1, Math.atan2(ny, nx), Math.atan2(-ny, -nx), true);
    for (let i = N; i >= 0; i--) { const [x, y] = at(i / N, -1); ctx.lineTo(x, y); }
    ctx.closePath();
    const g = ctx.createLinearGradient(hx + nx * R1, hy + ny * R1, hx - nx * R1, hy - ny * R1);
    g.addColorStop(0, '#fbe2b4'); g.addColorStop(0.35, '#e8ae6c'); g.addColorStop(0.75, '#b8722e'); g.addColorStop(1, '#7a4418');
    ctx.fillStyle = g; ctx.fill(); ctx.lineJoin = 'round'; ctx.lineWidth = 1.3; ctx.strokeStyle = '#1a0a14'; ctx.stroke();
    // the shine: a soft streak along the lit side of the barrel
    ctx.beginPath();
    for (let i = 8; i <= N; i++) { const t = i / N, r = rad(t) * 0.5, d = L * t; const x = hx + ux * d + nx * r, y = hy + uy * d + ny * r; if (i > 8) ctx.lineTo(x, y); else ctx.moveTo(x, y); }
    ctx.lineCap = 'round'; ctx.lineWidth = 1.3 * k; ctx.strokeStyle = 'rgba(255,248,230,0.7)'; ctx.stroke();
    // the knob
    ctx.beginPath(); ctx.ellipse(hx - ux * 0.8, hy - uy * 0.8, 3.1 * k, 2 * k, Math.atan2(uy, ux) + Math.PI / 2, 0, 6.29);
    ctx.fillStyle = '#6a3a16'; ctx.fill(); ctx.lineWidth = 1.1; ctx.strokeStyle = '#1a0a14'; ctx.stroke();
  }
  // the batter's pose at ts seconds after the swing (or before it): the body's turn (th, degrees: 0 faces us, 90 the
  // plate, 180 the pitcher), the bat's turn round the body (phi: 0 points across the plate, + towards us) and rise (tlt),
  // the hands in the body's own frame (ha along its right, hb ahead of it, both in half widths; hh down from the top, in
  // heights), the step in. At the hit (DN, given) the bat lies across the plate to the bat's ring.
  function bbPose(ts, DN) {
    const ease = (v) => { v = Math.max(0, Math.min(1, v)); return v * v * (3 - 2 * v); };
    const ST = { th: 135, phi: 140, tlt: 60, ha: 0.55, hb: 0.05, hh: 0.42, step: 0 };
    const FO = { th: 230, phi: -170, tlt: 35, ha: -0.55, hb: 0.05, hh: 0.36, step: 1 };
    const mix = (a, b, k) => { const o = {}; for (const q in a) o[q] = a[q] + (b[q] - a[q]) * k; return o; };
    if (ts < 0 || ts > BB_SWING) return { ...ST, tlt: ST.tlt + Math.sin(G.t * 2.4) * 2.5 };   // waiting: the bat sways a little
    if (ts < BB_DS) return mix(ST, DN, ease(ts / BB_DS));                     // down to the ball, quick
    if (ts < BB_DS + 0.1) return mix(DN, FO, ease((ts - BB_DS) / 0.1));
    if (ts < 0.45) return FO;
    return mix(FO, { ...ST, phi: -220 }, ease((ts - 0.45) / (BB_SWING - 0.45)));   // and back
  }
  function bbView(th) {                                                         // the picture for a turn: nearest of the eight
    const a = ((Math.round(th / 45) * 45) % 360 + 360) % 360;
    return a === 270 ? ['90', true] : a === 315 ? ['45', true] : [String(a), false];
  }
  function drawFist(x, y, col) {
    ctx.beginPath(); ctx.arc(x, y, BB_FIST, 0, 6.29); ctx.fillStyle = col; ctx.fill(); ctx.lineWidth = 1.2; ctx.strokeStyle = '#1a0a14'; ctx.stroke();
    ctx.beginPath(); ctx.arc(x - BB_FIST * 0.3, y - BB_FIST * 0.35, BB_FIST * 0.35, 0, 6.29); ctx.fillStyle = 'rgba(255,255,255,0.45)'; ctx.fill();
  }
  function drawBatter(x0, gy) {                                                 // x0: where it stands (the middle of its feet); gy: the ground
    const b = G.bb, n = G.char, front = M.sprites[`bt_${n}_0`];
    if (!front) return;
    const Wb = front.w, Hb = front.h, col = BAT_COL[n] || '#e8b47a';
    // the hit: the hands out ahead, the bat from them through the bat's ring
    const [zx, zy] = bbZone(), tg = [zx + b.cur[0], zy + b.cur[1]];
    const handAt = (P, x) => { const t = P.th * Math.PI / 180, rx = -Math.cos(t), rz = Math.sin(t), fx = Math.sin(t), fz = Math.cos(t);
      const z = P.ha * rz + P.hb * fz;                                            // + towards us
      return [x + (P.ha * rx + P.hb * fx) * Wb * 0.5, gy - Hb + P.hh * Hb + z * 2.5, z]; };
    const DN0 = { th: 178, ha: 0.35, hb: 0.6, hh: 0.5, step: 1 };
    const hD = handAt(DN0, x0 + 6);
    const DN = { ...DN0, phi: 0, tlt: -Math.atan2(tg[1] - hD[1], tg[0] - hD[0]) * 180 / Math.PI };
    const P = bbPose(G.t - b.swingT, DN), phi = P.phi * Math.PI / 180, tlt = P.tlt * Math.PI / 180;
    const x = x0 + 6 * P.step, [hx, hy, hz] = handAt(P, x);
    const bx = Math.cos(phi) * Math.cos(tlt), bz = Math.sin(phi) * Math.cos(tlt), by = -Math.sin(tlt);
    const vx = bx * BB_BAT, vy = (by + bz * 0.14) * BB_BAT;
    const bat = () => { drawBat(hx, hy, vx, vy, bz); drawFist(hx + vx * 0.04, hy + vy * 0.04, col); drawFist(hx + vx * 0.13, hy + vy * 0.13, col); };
    const behind = hz + bz * 0.4 < -0.05;                                       // the hands and bat on the far side of the body
    if (behind) bat();
    const [v, flip] = bbView(P.th), sp = M.sprites[`bt_${n}_${v}`];
    ctx.save(); ctx.translate(x, gy); if (flip) ctx.scale(-1, 1);
    spr(`bt_${n}_${v}`, -sp.foot[0], -sp.foot[1], 1, sp.w, sp.h);
    ctx.restore();
    if (!behind) bat();
  }
  function drawBall(x, y, r, spin = 0) {
    ctx.beginPath(); ctx.arc(x, y, r + 0.7, 0, 6.29); ctx.fillStyle = '#1a0a14'; ctx.fill();
    const g = ctx.createRadialGradient(x - r * 0.35, y - r * 0.4, r * 0.1, x, y, r); g.addColorStop(0, '#ffffff'); g.addColorStop(0.7, '#f2ece4'); g.addColorStop(1, '#c8bcb0');
    ctx.beginPath(); ctx.arc(x, y, r, 0, 6.29); ctx.fillStyle = g; ctx.fill();
    if (r > 1.6) {                                                             // the seams
      ctx.lineWidth = Math.max(0.35, r * 0.16); ctx.strokeStyle = '#d23a3a';
      const c = Math.cos(spin) * 0.25;
      ctx.beginPath(); ctx.arc(x - r * (1.25 + c), y, r * 0.95, -0.36 * Math.PI, 0.36 * Math.PI); ctx.stroke();
      ctx.beginPath(); ctx.arc(x + r * (1.25 + c), y, r * 0.95, 0.64 * Math.PI, 1.36 * Math.PI); ctx.stroke();
    }
  }
  function batShape(cx, cy, k = 1) {                                            // the bat's aim as the path (k: smaller, for the pad)
    const L = BB_AL * k, ox = cx - BB_AX * BB_AS * L, oy = cy - BB_AY * BB_AS * L, nx = -BB_AY, ny = BB_AX, N = 28;
    const at = (t, side) => { const r = batRad(t) * k * side, d = L * t; return [ox + BB_AX * d + nx * r, oy + BB_AY * d + ny * r]; };
    ctx.beginPath();
    for (let i = 0; i <= N; i++) { const [x, y] = at(0.04 + 0.96 * i / N, 1); if (i) ctx.lineTo(x, y); else ctx.moveTo(x, y); }
    const ex = ox + BB_AX * L, ey = oy + BB_AY * L, a0 = Math.atan2(ny, nx);                 // the barrel's round end
    ctx.arc(ex, ey, batRad(1) * k, a0, a0 - Math.PI, true);
    for (let i = N; i >= 0; i--) { const [x, y] = at(0.04 + 0.96 * i / N, -1); ctx.lineTo(x, y); }
    ctx.arc(ox, oy, batRad(0) * k, a0 + Math.PI, a0, true);                                  // the knob
    ctx.closePath();
  }
  function drawBaseball() {
    const b = G.bb; if (!b) return;
    world();
    const u = G.t - b.inT;
    let al = Math.min(1, u / 0.35);
    if (b.st === 'done') al *= Math.max(0, Math.min(1, (BB_END - (G.t - b.stT)) / 0.35));
    ctx.globalAlpha = al;                                                      // (spr at alpha 1 keeps this)
    const [zx, zy] = bbZone();
    ctx.fillStyle = '#2a0812'; ctx.fillRect(0, 0, NWf, NH);
    spr('bb_field', zx - 210, 0, 1, 420, 180);
    // the pitcher (and the ball in its hand until it lets go)
    const f = b.p ? bbPitcherFrame() : 0, ps = M.sprites['bb_p' + f], [mx, my] = bbPitcherAt();
    if (ps) spr('bb_p' + f, mx - ps.foot[0] * BB_PS, my - ps.foot[1] * BB_PS, 1, ps.w * BB_PS, ps.h * BB_PS);
    if (b.st === 'intro' || b.st === 'wind' || (b.st === 'after' && G.t - b.stT > 0.6)) { const [hx, hy] = bbHand(f); drawBall(hx, hy, 1.4); }

    // the strike zone: a frame with thirds
    ctx.globalAlpha = al * 0.9;
    rrect(zx - BB_ZW / 2, zy - BB_ZH / 2, BB_ZW, BB_ZH, 2); ctx.fillStyle = 'rgba(255,240,246,0.07)'; ctx.fill();
    ctx.lineWidth = 0.9; ctx.strokeStyle = 'rgba(255,240,246,0.75)'; ctx.stroke();
    ctx.lineWidth = 0.45; ctx.strokeStyle = 'rgba(255,240,246,0.3)'; ctx.beginPath();
    for (const q of [1, 2]) { ctx.moveTo(zx - BB_ZW / 2 + BB_ZW * q / 3, zy - BB_ZH / 2); ctx.lineTo(zx - BB_ZW / 2 + BB_ZW * q / 3, zy + BB_ZH / 2); ctx.moveTo(zx - BB_ZW / 2, zy - BB_ZH / 2 + BB_ZH * q / 3); ctx.lineTo(zx + BB_ZW / 2, zy - BB_ZH / 2 + BB_ZH * q / 3); }
    ctx.stroke(); ctx.globalAlpha = al;
    // the batter (left of the plate, feet on the ground at the bottom)
    drawBatter(zx - 54, 178);
    // where the ball will cross: a white ring closing in to the ball's size as it comes
    const p = b.p, flying = p && b.st === 'fly' && !p.done;
    if (flying) {
      const B = bbBallAt(G.t);
      if (B.s >= 0.12 && B.s <= 1) {
        const q = (B.s - 0.12) / 0.88, R = BB_BR + 1 + (BB_CR * 2.4 - BB_BR - 1) * (1 - q);
        ctx.globalAlpha = al * Math.min(1, (B.s - 0.12) * 6);
        ctx.beginPath(); ctx.arc(zx + p.tx, zy + p.ty, R, 0, 6.29); ctx.lineWidth = 2.8; ctx.strokeStyle = 'rgba(26,10,20,0.7)'; ctx.stroke();
        ctx.lineWidth = 1.5; ctx.strokeStyle = '#ffffff'; ctx.stroke(); ctx.globalAlpha = al;
      }
    }
    // the ball on its way (over the batter's bat: it comes at us), and on past into the mitt if not hit
    if (flying || (p && b.st === 'after' && !b.ball && G.t - p.arr < 0.32)) {
      const B = bbBallAt(b.pend ? bbMeetT() : Math.min(G.t, p.arr + 0.3));    // (a ball about to be hit waits for the bat)
      if (B.s < 1.32) drawBall(B.x, B.y, B.r, G.t * 30);
    }
    // a struck ball flying off: a tapering streak along the last of its path and afterimages behind it
    if (b.ball) {
      const F = b.ball, q = Math.min(1, (G.t - F.t0) / F.dur);
      const at = (qq) => [F.from[0] + (F.to[0] - F.from[0]) * qq, F.from[1] + (F.to[1] - F.from[1]) * qq - Math.sin(qq * Math.PI) * F.h, BB_BR * (1 - 0.75 * qq)];
      if (q < 1) {
        const q0 = Math.max(0, q - 0.35), N = 16, col = F.res === 'hr' ? '#ffe680' : '#ffffff';
        ctx.lineCap = 'round';
        for (const [wk, c, ak] of [[2.6, 'rgba(26,10,20,0.35)', 1], [2.0, col, 0.85]]) {     // a dark edge under a bright streak
          for (let i = 0; i < N; i++) {
            const [x0, y0, r0] = at(q0 + (q - q0) * i / N), [x1, y1] = at(q0 + (q - q0) * (i + 1) / N), k = (i + 1) / N;
            ctx.globalAlpha = al * ak * k; ctx.lineWidth = r0 * wk * k; ctx.strokeStyle = c;
            ctx.beginPath(); ctx.moveTo(x0, y0); ctx.lineTo(x1, y1); ctx.stroke();
          }
        }
        for (let i = 5; i >= 1; i--) { const [x, y, r] = at(Math.max(0, q - i * 0.06)); ctx.globalAlpha = al * (0.75 - i * 0.12); drawBall(x, y, r * (1 - i * 0.07)); }
        ctx.globalAlpha = al; const [x, y, r] = at(q); drawBall(x, y, r, G.t * 20);
      }
    }
    // the hit's burst: a jagged crack popping out of where bat met ball, and rings spreading from it like a sound wave
    if (b.fx && b.fx.age < BB_FX) {
      const f = b.fx, a = f.age, big = f.res === 'hr', [cx, cy] = f.at, n = big ? 4 : 2;
      for (let i = 0; i < n; i++) {
        const u = (a - i * 0.06) / 0.42; if (u <= 0 || u >= 1) continue;
        const R = 5 + (big ? 48 : 32) * (1 - (1 - u) * (1 - u));
        ctx.globalAlpha = al * (1 - u) * 0.9;
        ctx.beginPath(); ctx.arc(cx, cy, R, 0, 6.29); ctx.lineWidth = (big ? 3.4 : 2.4) * (1 - u) + 0.4; ctx.strokeStyle = '#ffffff'; ctx.stroke();
      }
      const u = a / 0.28;
      if (u < 1) {
        const sc = (u < 0.25 ? 0.55 + 0.65 * u / 0.25 : 1.2 - 0.55 * (u - 0.25) / 0.75) * (big ? 1.35 : 0.8);
        const SP = [15, 10, 17, 11, 14, 9, 18, 12, 13, 10, 16, 11];
        const star = (k0) => { ctx.beginPath(); for (let k = 0; k < 24; k++) { const ang = k * Math.PI / 12 + 0.25, rr = (k % 2 ? 4.6 : SP[(k / 2) % 12]) * sc * k0;
          const x = cx + Math.cos(ang) * rr, y = cy + Math.sin(ang) * rr; if (k) ctx.lineTo(x, y); else ctx.moveTo(x, y); } ctx.closePath(); };
        ctx.globalAlpha = al * Math.min(1, (1 - u) * 2.2);
        star(1); ctx.lineJoin = 'miter'; ctx.fillStyle = '#ffd23a'; ctx.fill(); ctx.lineWidth = 1.4; ctx.strokeStyle = '#1a0a14'; ctx.stroke();
        star(0.62); ctx.fillStyle = '#fffbea'; ctx.fill();
        ctx.lineJoin = 'round';
      }
      ctx.globalAlpha = al;
    }
    // the bat's aim (where you will hit: the bat's own shape, slanting) and the middle of its barrel
    if (b.st !== 'done') {
      const cx = zx + b.cur[0], cy = zy + b.cur[1];
      batShape(cx, cy); ctx.fillStyle = 'rgba(255,214,110,0.16)'; ctx.fill();
      ctx.lineWidth = 2.8; ctx.strokeStyle = '#1a0a14'; ctx.stroke(); ctx.lineWidth = 1.5; ctx.strokeStyle = '#ffd66e'; ctx.stroke();
      ctx.beginPath(); ctx.arc(cx, cy, 1.1, 0, 6.29); ctx.fillStyle = '#ffd66e'; ctx.fill();
    }
    // the controls: the aiming pad on the left (a swipe anywhere on the left moves the ring; its knob shows where the
    // ring is in the zone), the swing button on the right
    if (b.st !== 'done') {
      const pw = 50, ph = 57, px0 = 10, py0 = NH - 10 - ph, pcx = px0 + pw / 2, pcy = py0 + ph / 2, on = !!b.drag;
      rrect(px0, py0, pw, ph, 7); ctx.fillStyle = on ? 'rgba(40,16,30,0.7)' : 'rgba(26,10,20,0.55)'; ctx.fill();
      ctx.lineWidth = 1.3; ctx.strokeStyle = on ? 'rgba(255,230,160,0.95)' : 'rgba(255,240,220,0.6)'; ctx.stroke();
      ctx.lineWidth = 0.45; ctx.strokeStyle = 'rgba(255,240,246,0.25)'; ctx.beginPath();
      for (const q of [1, 2]) { ctx.moveTo(px0 + 6 + (pw - 12) * q / 3, py0 + 6); ctx.lineTo(px0 + 6 + (pw - 12) * q / 3, py0 + ph - 6); ctx.moveTo(px0 + 6, py0 + 6 + (ph - 12) * q / 3); ctx.lineTo(px0 + pw - 6, py0 + 6 + (ph - 12) * q / 3); }
      ctx.stroke();
      const kx = pcx + b.cur[0] / (BB_ZW / 2 + 6) * (pw / 2 - 6), ky = pcy + b.cur[1] / (BB_ZH / 2 + 6) * (ph / 2 - 6);
      batShape(kx, ky, 0.42); ctx.fillStyle = on ? 'rgba(255,214,110,0.4)' : 'rgba(255,214,110,0.2)'; ctx.fill();
      ctx.lineWidth = 2.4; ctx.strokeStyle = '#1a0a14'; ctx.stroke(); ctx.lineWidth = 1.3; ctx.strokeStyle = '#ffd66e'; ctx.stroke();
      ctx.beginPath(); ctx.arc(kx, ky, 1, 0, 6.29); ctx.fillStyle = '#ffd66e'; ctx.fill();
      label(TR('조준', 'Aim'), pcx, py0 - 6, 7.5, 'center', al, '#ffffff');
      const by = NH - 30, bxr = NW - 34;
      ctx.beginPath(); ctx.arc(bxr, by, 20, 0, 6.29); ctx.fillStyle = 'rgba(26,10,20,0.6)'; ctx.fill();
      ctx.beginPath(); ctx.arc(bxr, by, 18.5, 0, 6.29); ctx.fillStyle = G.t - b.swingT < 0.25 ? 'rgba(255,214,110,0.75)' : 'rgba(255,214,110,0.38)'; ctx.fill();
      ctx.lineWidth = 1.4; ctx.strokeStyle = 'rgba(255,240,200,0.95)'; ctx.stroke();
      label(TR('스윙', 'Swing'), bxr, by + 0.5, 9, 'center', al, '#ffffff');
    }
    // the count: five balls, used ones dimmed
    for (let i = 0; i < BB_N; i++) { ctx.globalAlpha = al * (i < b.res.length ? 0.28 : 1); drawBall(20 + i * 10, 44, 3.4); }
    ctx.globalAlpha = al;
    if (b.st === 'intro') {
      const a = Math.min(1, u / 0.3) * Math.max(0, Math.min(1, (BB_INTRO - u) / 0.3));
      label(TR('공 5개, 홈런마다 점수!', '5 pitches - score with home runs!'), NWf / 2, 62, 16, 'center', a, '#ffe0a8');
      label(TR('왼쪽을 끌어 노란 고리를 공이 올 자리(흰 고리)에', 'Drag on the left: the yellow ring to where the ball comes (white ring)'), NWf / 2, 80, 7.5, 'center', a, '#ffffff');
      label(TR('흰 고리가 공만큼 줄어들 때 오른쪽 터치', 'Tap the right side as the white ring shrinks to the ball'), NWf / 2, 91, 7.5, 'center', a, '#ffffff');
    }
    if (b.msg && b.st !== 'done') {                       // the result: small, just over the zone (under the pitcher), briefly
      const v = G.t - b.msg.t, big = b.msg.res === 'hr', a = Math.min(1, v / 0.08) * Math.max(0, Math.min(1, ((big ? 1.3 : 0.95) - v) / 0.25));
      const s = big ? (b.msg.k > 1 ? TR(`${b.msg.k}연속 홈런! +${PT(b.msg.pts)}`, `${b.msg.k} home runs in a row! +${PT(b.msg.pts)}`) : `${b.msg.s} +${PT(b.msg.pts)}`) : b.msg.res === 'whiff' ? `${b.msg.s} · ${b.p.type.name}` : b.msg.s;   // (a miss: what got past you) (v57: in a row)
      label(s, zx, zy - BB_ZH / 2 - 5, 7, 'center', a, big ? '#ffe68a' : '#ffffff');
    }
    if (b.st === 'done') {
      const v = G.t - b.stT, a = Math.min(1, v / 0.25) * Math.max(0, Math.min(1, (BB_END - v) / 0.35));
      ctx.globalAlpha = a * 0.78; rrect(NWf / 2 - 110, 54, 220, 60, 8); ctx.fillStyle = '#1a0a14'; ctx.fill(); ctx.globalAlpha = 1;
      const n = (q) => b.res.filter((r) => r === q).length;
      label(TR(`홈런 ${n('hr')}개${n('hr') ? '!' : ''}`, `${n('hr')} home run${n('hr') === 1 ? '' : 's'}${n('hr') ? '!' : ''}`), NWf / 2, 70, 14, 'center', a, b.hr ? '#ffe68a' : '#ffd0dc');
      label(TR(`홈런 ${n('hr')} · 파울 ${n('foul')} · 헛스윙 ${n('whiff')} · 스트라이크 ${n('strike')}`, `HR ${n('hr')} · Foul ${n('foul')} · Miss ${n('whiff')} · Strike ${n('strike')}`), NWf / 2, 90, 7.5, 'center', a, '#ffffff');
      label(`${(b.bestRun || 0) > 1 ? TR(`최고 연속 ${b.bestRun} · `, `Best run ${b.bestRun} · `) : ''}+${PT(b.gain)}`, NWf / 2, 104, 8.5, 'center', a, '#ffe68a');
    }
    ctx.globalAlpha = 1;
  }

  // ---------------------------------------------------------------- the germ game (in the spleen) (v40)
  // The spleen's red pulp as a board seen from the front, nine openings of its sinuses in three rows (the picture and
  // where the openings are: minigames.py). Germs pop out of them for a moment: tap the bad ones (a purple E. coli, a
  // golden staph bunch, a red spiral) before they go down again, +50 each; the green lactobacillus is a good one:
  // tapping it costs 100. 45 s (v41; was 25), harder and harder as it goes. The run stands still; the
  // game has its own song (v42).
  const WMF = M.wm || { holes: [] };
  const WM_T = 45, WM_INTRO = 3.2, WM_END = 2.4;          // (v41: the intro longer, it shows the lactobacillus too)
  const WM_RISE = 0.1, WM_SINK = 0.12, WM_SQUASH = 0.11, WM_HITSINK = 0.24;
  // harder as it goes (v41), over the 45 s from start to end: how long a germ stays all the way up; the time between
  // germs; how many can be up at once (from 0, 10, 20, 32 s); how often one is the good one, and from 25 s two good ones
  // can be up together; germs coming two (from 20 s) or three (from 32 s) at a time. v40 (25 s): 1.15 -> 0.6 s up, 0.8 -> 0.38 s apart, 1/2/3 at once, 22%
  const WM_STAY = [0.85, 0.35], WM_GAP = [0.6, 0.22], WM_MAXUP = [[0, 2], [10, 3], [20, 4], [32, 5]], WM_GOOD = [0.2, 0.33];
  const WM_PTS = 50, WM_OOPS = 100;
  const WM_K = 1.1;                                        // a germ's picture at the front row, scaled (its body ~42 tall)
  const WM_BAD_KINDS = ['ecoli', 'staph', 'spiral'];
  // the number keys, laid out like the board on a number pad (7 8 9 the far row, 1 2 3 the near one)
  const WM_KEY = { 7: 0, 8: 1, 9: 2, 4: 3, 5: 4, 6: 5, 1: 6, 2: 7, 3: 8 };
  const ease = (v) => { v = Math.max(0, Math.min(1, v)); return v * v * (3 - 2 * v); };
  const lerp = (a, b, k) => a + (b - a) * Math.max(0, Math.min(1, k));
  function startWhack() {
    holdBoost();
    G.obs = G.obs.filter((o) => o.x + o.w < G.x - 12);
    G.items = G.items.filter((i) => i.x < G.x - 12 || i.taken);
    G.wm = { st: 'intro', stT: G.t, inT: G.t, t0: 0, next: 0, moles: [], free: WMF.holes.map(() => -9), caught: 0, missed: 0, oops: 0, gain: 0, fx: [], pops: [], music: false, combo: 0, maxCombo: 0 };
    G.slideHeld = false; held.clear(); pressed.jump = false;
    wmMusic();
  }
  // its song (v42, stages.js 'wm'): once through from the intro, its sections laid on the game's (the play's 0, 9.6, 19.2,
  // 32 s, the end hit at 45); the running music goes down under it. Not decoded yet: tried again each step, started as
  // far in as the game is (so it stays in time)
  function wmMusic() {
    const w = G.wm; if (!w || w.music || CAPTURE || !STAGES.wm || !SND.live()) return;
    if (!SND.ready(STAGES.wm)) { SND.prepare(STAGES.wm).catch(() => {}); return; }
    if (SND.playSong(STAGES.wm, SND.ctx.currentTime - (G.t - w.inT))) { w.music = true; SND.ambience(false); }
  }
  function endWhack() {
    if (G.wm && G.wm.music) { SND.stopSong(0.8); SND.ambience(true); }
    bankGame(G.wm); G.wm = null; G.games = (G.games || 0) + 1; resumeBoost();
    G.genX = Math.max(G.genX, G.x + NW * 0.8);
    G.banner = G.t;
  }
  // how far a germ is out of its opening (0 down in it .. 1 all the way up)
  function wmOut(m) {
    if (m.st === 'hit') { const a = G.t - m.tH; return a < WM_SQUASH ? m.qH : m.qH * (1 - ease((a - WM_SQUASH) / WM_HITSINK)); }
    const a = G.t - m.t0;
    if (a < WM_RISE) { const k = a / WM_RISE; return 1 - (1 - k) * (1 - k); }
    if (a < WM_RISE + m.stay) return 1;
    const k = (a - WM_RISE - m.stay) / WM_SINK; return Math.max(0, 1 - k * k);
  }
  const wmName = (m) => 'wm_' + m.kind + (m.st === 'hit' ? '_hit' : '');
  // where a germ is drawn: its base's x, y, its scale (its picture at full height has its base at the opening's middle
  // plus a little; down in it, the picture is wholly under the opening)
  function wmPlace(m) {
    const h = WMF.holes[m.h], zx = NWf / 2, k = WM_K * h[4], s = M.sprites[wmName(m)], q = wmOut(m);
    const up = h[1] + h[3] * 0.45, down = h[1] + h[3] + s.foot[1] * k + 1;
    return { x: zx + h[0], y: down + (up - down) * q, k, q };
  }
  function wmSpawn() {
    const w = G.wm, u = G.t - w.t0, f = u / WM_T;
    const busyH = new Set(w.moles.map((m) => m.h));
    const open = WMF.holes.map((_, i) => i).filter((i) => !busyH.has(i) && G.t - w.free[i] > 0.25);
    if (!open.length) return;
    const h = open[Math.floor(Math.random() * open.length)];
    const goodUp = w.moles.filter((m) => m.good && m.st === 'up').length;
    const good = u > 3 && goodUp < (u < 25 ? 1 : 2) && Math.random() < lerp(WM_GOOD[0], WM_GOOD[1], f);
    const kind = good ? 'lacto' : WM_BAD_KINDS[Math.floor(Math.random() * WM_BAD_KINDS.length)];
    w.moles.push({ h, kind, good, t0: G.t, stay: lerp(WM_STAY[0], WM_STAY[1], f) * (0.88 + Math.random() * 0.24), st: 'up' });
    SND.play('wmUp');
  }
  function stepWhack() {
    const w = G.wm;
    if (!w.music && w.st !== 'done') wmMusic();
    if (w.st === 'intro') { if (G.t - w.stT > WM_INTRO) { w.st = 'play'; w.stT = G.t; w.t0 = G.t; w.next = G.t + 0.3; } return; }
    if (w.st === 'play') {
      const u = G.t - w.t0, f = u / WM_T;
      const maxUp = WM_MAXUP.filter(([t0]) => u >= t0).pop()[1];
      if (u < WM_T - 0.4 && G.t >= w.next) {
        // later on they come in twos (from 20 s) and threes (from 32 s), so more are up at once
        const n = u >= 32 && Math.random() < 0.35 ? 3 : u >= 20 && Math.random() < 0.35 ? 2 : 1;
        for (let k = 0; k < n; k++) if (w.moles.filter((m) => m.st === 'up').length < maxUp) wmSpawn();
        w.next = G.t + lerp(WM_GAP[0], WM_GAP[1], f) * (0.8 + Math.random() * 0.4);
      }
      if (AUTO && !window.__noAuto) for (const m of w.moles) {      // the test pilot: a bad germ well out gets tapped where it is
        if (m.st !== 'up' || m.good || wmOut(m) < 0.6) continue;
        const p = wmPlace(m), s = M.sprites[wmName(m)];
        wmDown(p.x, p.y - s.foot[1] * p.k * 0.55);
      }
      for (const m of w.moles) {
        const gone = m.st === 'hit' ? G.t - m.tH > WM_SQUASH + WM_HITSINK : G.t - m.t0 > WM_RISE + m.stay + WM_SINK;
        if (gone) { m.gone = true; w.free[m.h] = G.t; if (m.st === 'up' && !m.good) { w.missed++; w.combo = 0; } }     // (v57: one got away: the combo is broken)
      }
      w.moles = w.moles.filter((m) => !m.gone);
      if (u >= WM_T && !w.moles.length) { w.st = 'done'; w.stT = G.t; SND.play(w.caught ? 'orbClear' : 'bbOut'); }
    }
    w.fx = w.fx.filter((e) => G.t - e.t < 0.4);
    w.pops = w.pops.filter((e) => G.t - e.t < 0.8);
    if (w.st === 'done' && G.t - w.stT > WM_END) endWhack();
  }
  // a tap on the board: the germ under it that is out far enough (the nearest, if two overlap)
  function wmDown(x, y) {
    const w = G.wm; if (!w || w.st !== 'play') return;
    let best = null, bd = 1e9;
    for (const m of w.moles) {
      if (m.st !== 'up') continue;
      const p = wmPlace(m); if (p.q < 0.25) continue;
      const s = M.sprites[wmName(m)], hw = Math.max(WMF.holes[m.h][2] * 0.72, 15 * p.k), top = p.y - s.foot[1] * p.k - 4;
      const bot = WMF.holes[m.h][1] + WMF.holes[m.h][3] + 3;
      if (Math.abs(x - p.x) > hw || y < top || y > bot) continue;
      const d = Math.hypot(x - p.x, y - (top + bot) / 2);
      if (d < bd) { bd = d; best = m; }
    }
    if (best) wmWhack(best, x, y);
  }
  function wmKey(i) { const w = G.wm; if (!w) return; const m = w.moles.find((q) => q.h === i && q.st === 'up' && wmOut(q) >= 0.25); if (m) { const p = wmPlace(m); wmWhack(m, p.x, p.y - 12 * p.k); } }
  function wmWhack(m, x, y) {
    const w = G.wm;
    m.qH = wmOut(m); m.st = 'hit'; m.tH = G.t;
    if (m.good) {
      const lose = Math.min(WM_OOPS, G.score + w.gain); w.gain -= lose; w.oops++; w.combo = 0;     // (the score never goes below 0)
      SND.play('wmOops'); buzz([30, 40, 30]);
      w.pops.push({ x, y: y - 6, s: lose ? '-' + lose : TR('앗!', 'Oops!'), t: G.t, bad: true });
    } else {
      w.combo++; w.maxCombo = Math.max(w.maxCombo, w.combo);     // (v57) a combo, as in the rhythm stage
      const pts = Math.round(WM_PTS * (1 + Math.min(w.combo, 40) / 25));
      w.gain += pts; w.caught++;
      SND.play('wmHit'); buzz(BUZZ_TAP);
      w.pops.push({ x, y: y - 6, s: '+' + pts, t: G.t });
    }
    w.fx.push({ x, y, t: G.t, good: m.good });
  }
  // ---- drawing
  function wmStar(x, y, r, col) {
    ctx.beginPath();
    for (let k = 0; k < 10; k++) { const a = -Math.PI / 2 + k * Math.PI / 5, rr = k % 2 ? r * 0.45 : r; ctx.lineTo(x + Math.cos(a) * rr, y + Math.sin(a) * rr); }
    ctx.closePath(); ctx.fillStyle = col; ctx.fill(); ctx.lineWidth = 0.7; ctx.strokeStyle = '#1a0a14'; ctx.stroke();
  }
  function drawWhack() {
    const w = G.wm; if (!w) return;
    world();
    let al = Math.min(1, (G.t - w.inT) / 0.35);
    if (w.st === 'done') al *= Math.max(0, Math.min(1, (WM_END - (G.t - w.stT)) / 0.35));
    ctx.globalAlpha = al;
    const zx = NWf / 2;
    ctx.fillStyle = '#1a0408'; ctx.fillRect(0, 0, NWf, NH);
    spr('wm_field', zx - 210, 0, 1, 420, 180);
    // the germs, far row first (a nearer one in front), each cut off where it goes down into its opening, darker inside it
    const byHole = {}; for (const m of w.moles) byHole[m.h] = m;
    WMF.holes.forEach((h, i) => {
      const m = byHole[i]; if (!m) return;
      const p = wmPlace(m), nm = wmName(m), s = M.sprites[nm], hx = zx + h[0];
      if (p.q <= 0) return;
      ctx.save();
      ctx.beginPath(); ctx.rect(hx - 70, -20, 140, h[1] + 20); ctx.ellipse(hx, h[1], h[2], h[3], 0, 0, 6.2832); ctx.clip();
      let sx = 1, sy = 1;
      if (m.st === 'hit') { const a = (G.t - m.tH) / WM_SQUASH; if (a < 1) { const b = Math.sin(Math.min(1, a) * Math.PI); sx = 1 + 0.22 * b; sy = 1 - 0.3 * b; } }
      ctx.translate(p.x, p.y); ctx.scale(p.k * sx, p.k * sy);
      spr(nm, -s.foot[0], -s.foot[1], 1, s.w, s.h);
      ctx.restore();
      ctx.save();
      ctx.beginPath(); ctx.ellipse(hx, h[1], h[2], h[3], 0, 0, 6.2832); ctx.clip();
      const g = ctx.createLinearGradient(0, h[1] - h[3] * 0.1, 0, h[1] + h[3]);
      g.addColorStop(0, 'rgba(10,0,4,0)'); g.addColorStop(1, 'rgba(10,0,4,0.6)');
      ctx.fillStyle = g; ctx.fillRect(hx - h[2], h[1] - h[3], h[2] * 2, h[3] * 2);
      ctx.restore();
      ctx.globalAlpha = al;
      // dizzy stars round a whacked bad one's head
      if (m.st === 'hit' && !m.good) {
        const a = G.t - m.tH, top = p.y - s.foot[1] * p.k * 0.92;
        for (let k = 0; k < 3; k++) { const ang = a * 9 + k * 2.094; wmStar(p.x + Math.cos(ang) * 10 * p.k, top + Math.sin(ang) * 3 * p.k, 3.4 * p.k, '#ffe04a'); }
      }
    });
    // the whack: a ring and rays bursting from the tap (white; red for the good one)
    for (const e of w.fx) {
      const u = (G.t - e.t) / 0.32; if (u >= 1) continue;
      const R = 5 + 16 * (1 - (1 - u) * (1 - u)), col = e.good ? '#ff5a6a' : '#ffffff';
      ctx.globalAlpha = al * (1 - u);
      ctx.beginPath(); ctx.arc(e.x, e.y, R, 0, 6.2832); ctx.lineWidth = 2.4 * (1 - u) + 0.4; ctx.strokeStyle = col; ctx.stroke();
      ctx.beginPath();
      for (let k = 0; k < 8; k++) { const a = k * Math.PI / 4 + 0.39; ctx.moveTo(e.x + Math.cos(a) * R * 0.55, e.y + Math.sin(a) * R * 0.55); ctx.lineTo(e.x + Math.cos(a) * R * 1.05, e.y + Math.sin(a) * R * 1.05); }
      ctx.lineWidth = 1.6 * (1 - u) + 0.3; ctx.stroke();
    }
    ctx.globalAlpha = al;
    for (const e of w.pops) { const v = G.t - e.t; label(e.s, e.x, e.y - v * 22, 9, 'center', al * Math.min(1, (0.8 - v) / 0.25), e.bad ? '#ff8a96' : '#ffe68a'); }
    ctx.globalAlpha = al;
    // the count and the time left
    if (w.st === 'play' || w.st === 'done') {
      const left = w.st === 'play' ? Math.max(0, WM_T - (G.t - w.t0)) : 0, bw = 96, bx = zx - bw / 2, by = 42;
      rrect(bx - 1, by - 1, bw + 2, 5.4, 2.7); ctx.fillStyle = '#1a0a14'; ctx.fill();
      rrect(bx, by, bw, 3.4, 1.7); ctx.fillStyle = '#4a3040'; ctx.fill();
      if (left > 0) { rrect(bx, by, Math.max(3.4, bw * left / WM_T), 3.4, 1.7); ctx.fillStyle = left < 5 ? '#ff6a6a' : '#ffd66e'; ctx.fill(); }
      label(`${Math.ceil(left)}${TR('초', 's')}`, bx + bw + 4, by + 1.8, 7, 'left', al, '#ffffff');
      label(`${TR('잡은 세균', 'Germs')} ${w.caught}`, bx - 4, by + 1.8, 7, 'right', al, '#ffe0a8');
      ctx.globalAlpha = al;
    }
    if (w.st === 'intro') {
      const u = G.t - w.stT, a = Math.min(1, u / 0.3) * Math.max(0, Math.min(1, (WM_INTRO - u) / 0.3));
      ctx.globalAlpha = al * a * 0.8; rrect(zx - 118, 46, 236, 86, 8); ctx.fillStyle = '#1a0a14'; ctx.fill(); ctx.globalAlpha = al;
      label(TR(`세균 잡기! ${WM_T}초`, `Germ Smash! ${WM_T}s`), zx, 60, 15, 'center', a, '#ffe0a8');
      label(TR('구멍에서 튀어나오는 나쁜 세균을 톡! 눌러 잡아요', 'Tap the bad germs as they pop out of the holes'), zx, 77, 7.5, 'center', a, '#ffffff');
      // the good one, shown: its picture on the left of a lighter box, what it is and what tapping it costs beside it
      ctx.globalAlpha = al * a; rrect(zx - 92, 86, 184, 40, 6); ctx.fillStyle = 'rgba(120,220,90,0.14)'; ctx.fill();
      ctx.lineWidth = 0.9; ctx.strokeStyle = 'rgba(184,240,154,0.7)'; ctx.stroke();
      const ls = M.sprites.wm_lacto;
      if (ls) { const k = 34 / ls.foot[1]; spr('wm_lacto', zx - 70 - ls.foot[0] * k, 123 - ls.foot[1] * k, a, ls.w * k, ls.h * k); ctx.globalAlpha = al; }
      label(TR('이건 착한 유산균이에요', 'This one is a good germ'), zx - 46, 99, 8.5, 'left', a, '#b8f09a');
      label(TR('잡으면 안 돼요! (누르면 -100점)', "Don't tap it! (-100 pts)"), zx - 46, 113, 7.5, 'left', a, '#ffb0b8');
    }
    if (w.st === 'done') {
      const v = G.t - w.stT, a = Math.min(1, v / 0.25) * Math.max(0, Math.min(1, (WM_END - v) / 0.35));
      ctx.globalAlpha = a * 0.78; rrect(zx - 110, 54, 220, 60, 8); ctx.fillStyle = '#1a0a14'; ctx.fill(); ctx.globalAlpha = 1;
      label(TR(`세균 ${w.caught}마리!`, `${w.caught} germs!`), zx, 70, 14, 'center', a, '#ffe68a');
      label(TR(`잡음 ${w.caught} · 놓침 ${w.missed} · 유산균 누름 ${w.oops}`, `Caught ${w.caught} · Missed ${w.missed} · Good germ tapped ${w.oops}`), zx, 90, 7.5, 'center', a, '#ffffff');
      label(`${w.maxCombo > 1 ? TR(`최대 콤보 ${w.maxCombo} · `, `Max combo ${w.maxCombo} · `) : ''}${w.gain < 0 ? '-' : '+'}${PT(Math.abs(w.gain))}`, zx, 104, 8.5, 'center', a, w.gain < 0 ? '#ff8a96' : '#ffe68a');
    }
    ctx.globalAlpha = 1;
  }

  // ---------------------------------------------------------------- the memory game (in the hippocampus) (v40)
  // Five neurons in a ring light up one after another, each with its own bell; tap them in the same order. Five
  // rounds: the first is five long (v42; was three), and each round you get right adds one more to the end of the same order. A wrong
  // tap (or 5 s without one) shows the right one, and the next round is the same order again. A round right: 100 points
  // for each neuron in it. The run stands still; its music gives way to a quiet loop of the game's own (v42) under the bells.
  const MG_N = 5, MG_ROUNDS = 5, MG_L0 = 5;
  const MG_INTRO = 2.6, MG_END = 2.6, MG_LEAD = 0.5, MG_WAIT = 5, MG_OK = 1.0, MG_BAD = 1.6, MG_TAP = 0.3;
  const MG_R = 52, MG_CY = 110, MG_HIT = 28, MG_S = 50;   // the ring (its radius, middle), a tap's reach, a neuron's size
  const MG_COL = ['#ff5a80', '#ffb21e', '#3ad060', '#3a9aff', '#a464ff'];
  const memAt = (k) => { const a = -Math.PI / 2 + k * 2 * Math.PI / MG_N; return [NWf / 2 + Math.cos(a) * MG_R * 1.18, MG_CY + Math.sin(a) * MG_R]; };
  // a neuron's light in the show, the gap after it (v41: quicker: 0.32 s in the first round down to 0.24 in the fifth,
  // 0.1 s off; v40 was 0.5 -> 0.36 and 0.17)
  const memStep = (L) => [Math.max(0.22, 0.32 - 0.02 * (L - MG_L0)), 0.1];
  // the next neuron of the order: one that has not come up yet if there is one (so the first round's five are all
  // different and by five long every neuron has lit), never the one just before it
  function memNew(seq) {
    const last = seq[seq.length - 1], all = [...Array(MG_N).keys()].filter((n) => n !== last), fresh = all.filter((n) => !seq.includes(n));
    const from = fresh.length ? fresh : all; seq.push(from[Math.floor(Math.random() * from.length)]);
  }
  function startMemory() {
    holdBoost();
    G.obs = G.obs.filter((o) => o.x + o.w < G.x - 12);
    G.items = G.items.filter((i) => i.x < G.x - 12 || i.taken);
    const seq = []; for (let i = 0; i < MG_L0; i++) memNew(seq);
    G.mem = { st: 'intro', stT: G.t, inT: G.t, seq, round: 0, res: [], k: 0, shown: -1, lastTap: 0, flash: [], pulses: [], gain: 0, why: '', music: false };
    G.slideHeld = false; held.clear(); pressed.jump = false;
    if (!CAPTURE && SND.live()) SND.ambience(false);
    memMusic();
  }
  // its music (v42, stages.js 'mem'): a quiet loop under the bells, in when decoded (tried again each step)
  function memMusic() {
    const m = G.mem; if (!m || m.music || CAPTURE || !STAGES.mem || !SND.live()) return;
    if (!SND.ready(STAGES.mem)) { SND.prepare(STAGES.mem).catch(() => {}); return; }
    m.music = SND.playLoop(STAGES.mem, 1.0);
  }
  function endMemory() {
    if (G.mem && G.mem.music) SND.stopLoop(0.8);
    bankGame(G.mem); G.mem = null; G.games = (G.games || 0) + 1; resumeBoost();
    if (!CAPTURE && SND.live()) SND.ambience(true);
    G.genX = Math.max(G.genX, G.x + NW * 0.8);
    G.banner = G.t;
  }
  function memLight(n, kind, dur) { G.mem.flash.push({ n, kind, t: G.t, dur }); SND.play('mem' + n); }
  function memShow() { const m = G.mem; m.st = 'show'; m.stT = G.t; m.shown = -1; m.k = 0; }
  function stepMemory() {
    const m = G.mem;
    if (!m.music && m.st !== 'done') memMusic();
    if (m.st === 'intro' && G.t - m.stT > MG_INTRO) memShow();
    if (m.st === 'show') {
      const [on, gap] = memStep(m.seq.length), u = G.t - m.stT - MG_LEAD, i = Math.floor(u / (on + gap));
      if (u >= 0 && i < m.seq.length && i > m.shown) {
        m.shown = i; memLight(m.seq[i], 'show', on);
        if (i > 0) m.pulses.push({ a: m.seq[i - 1], b: m.seq[i], t: G.t - gap, dur: gap + 0.06 });
      }
      if (u >= m.seq.length * (on + gap) + 0.1) { m.st = 'input'; m.stT = G.t; m.lastTap = G.t; m.k = 0; }
    } else if (m.st === 'input') {
      if (AUTO && !window.__noAuto && G.t - m.lastTap > 0.32) { const [x, y] = memAt(m.seq[m.k]); memDown(x, y); }   // the test pilot
      else if (G.t - m.lastTap > MG_WAIT) memWrong(null, TR('시간 초과', 'Time up'));
    } else if (m.st === 'ok' && G.t - m.stT > MG_OK) {
      if (++m.round >= MG_ROUNDS) memDone(); else { memNew(m.seq); memShow(); }
    } else if (m.st === 'bad' && G.t - m.stT > MG_BAD) {
      if (++m.round >= MG_ROUNDS) memDone(); else memShow();
    }
    m.flash = m.flash.filter((f) => G.t - f.t < f.dur + 0.3);
    m.pulses = m.pulses.filter((p) => G.t - p.t < p.dur + 0.1);
    if (m.st === 'done' && G.t - m.stT > MG_END) endMemory();
  }
  function memDone() { const m = G.mem; m.st = 'done'; m.stT = G.t; SND.play(m.res.includes('ok') ? 'orbClear' : 'bbOut'); }
  function memWrong(n, why) {
    const m = G.mem, right = m.seq[m.k];
    m.res.push('bad'); m.st = 'bad'; m.stT = G.t; m.why = why; m.run = 0;
    if (n !== null) m.flash.push({ n, kind: 'wrong', t: G.t, dur: MG_BAD - 0.2 });
    m.flash.push({ n: right, kind: 'right', t: G.t, dur: MG_BAD - 0.2 });
    SND.play('memBad'); buzz([30, 40, 30]);
  }
  function memDown(x, y) {
    const m = G.mem; if (!m || m.st !== 'input') return;
    let n = -1, bd = MG_HIT;
    for (let k = 0; k < MG_N; k++) { const [px, py] = memAt(k), d = Math.hypot(x - px, y - py); if (d < bd) { bd = d; n = k; } }
    if (n < 0) return;
    m.lastTap = G.t;
    if (n !== m.seq[m.k]) { memWrong(n, TR('틀렸어요', 'Wrong')); return; }
    memLight(n, 'tap', MG_TAP); buzz(BUZZ_TAP);
    if (m.k > 0) m.pulses.push({ a: m.seq[m.k - 1], b: n, t: G.t - 0.12, dur: 0.16 });
    if (++m.k >= m.seq.length) {
      m.run = (m.run || 0) + 1; m.bestRun = Math.max(m.bestRun || 0, m.run);     // (v57) rounds right in a row: +20% each
      const pts = comboPts(m.seq.length * 100, m.run); m.gain += pts; m.res.push('ok');
      m.st = 'ok'; m.stT = G.t; m.okPts = pts; m.best = Math.max(m.best || 0, m.seq.length);
      SND.play('memOk');
    }
  }
  function memKey(n) { if (G.mem && n >= 0 && n < MG_N) { const [x, y] = memAt(n); memDown(x, y); } }
  // ---- drawing
  function drawMemory() {
    const m = G.mem; if (!m) return;
    world();
    let al = Math.min(1, (G.t - m.inT) / 0.4);
    if (m.st === 'done') al *= Math.max(0, Math.min(1, (MG_END - (G.t - m.stT)) / 0.4));
    const cx = NWf / 2;
    // the place goes dark behind the ring (its own light gathered in the middle)
    ctx.globalAlpha = al * 0.86; ctx.fillStyle = '#0a0414'; ctx.fillRect(0, 0, NWf, NH);
    const bg = ctx.createRadialGradient(cx, MG_CY, 10, cx, MG_CY, 120);
    bg.addColorStop(0, 'rgba(70,40,110,0.55)'); bg.addColorStop(1, 'rgba(70,40,110,0)');
    ctx.fillStyle = bg; ctx.fillRect(0, 0, NWf, NH);
    ctx.globalAlpha = al;
    const P = []; for (let k = 0; k < MG_N; k++) P.push(memAt(k));
    // the synapses: every two neurons joined by a faint line, bright while a signal runs along it
    ctx.lineCap = 'round';
    for (let a = 0; a < MG_N; a++) for (let b = a + 1; b < MG_N; b++) {
      ctx.beginPath(); ctx.moveTo(P[a][0], P[a][1]); ctx.lineTo(P[b][0], P[b][1]);
      ctx.lineWidth = 0.8; ctx.strokeStyle = 'rgba(200,170,255,0.18)'; ctx.stroke();
    }
    for (const p of m.pulses) {
      const u = (G.t - p.t) / p.dur; if (u < 0 || u > 1.25) continue;
      const A = P[p.a], B = P[p.b], f = Math.min(1, u), col = MG_COL[p.b];
      ctx.globalAlpha = al * Math.min(1, (1.25 - u) * 4) * 0.8;
      ctx.beginPath(); ctx.moveTo(A[0], A[1]); ctx.lineTo(B[0], B[1]); ctx.lineWidth = 1.6; ctx.strokeStyle = col; ctx.stroke();
      for (let i = 0; i < 6; i++) {                                               // the signal: a bright spark with a trail
        const q = Math.max(0, f - i * 0.05), x = A[0] + (B[0] - A[0]) * q, y = A[1] + (B[1] - A[1]) * q;
        ctx.globalAlpha = al * (1 - i / 6) * (u <= 1 ? 1 : 0);
        ctx.beginPath(); ctx.arc(x, y, 2.6 - i * 0.3, 0, 6.2832); ctx.fillStyle = i ? col : '#ffffff'; ctx.fill();
      }
    }
    ctx.globalAlpha = al;
    // the neurons: dim; lit (with a glow behind and a little swell) while flashing; the wrong one shakes red, the right
    // one it should have been blinks
    for (let k = 0; k < MG_N; k++) {
      const [x, y] = P[k];
      let lit = 0, kind = null;
      for (const f of m.flash) if (f.n === k) { const a = G.t - f.t; if (a >= 0 && a < f.dur) { const v = f.kind === 'right' ? (Math.floor(a * 6) % 2 ? 0 : 1) : 1; if (v >= lit) { lit = v; kind = f.kind; } } }
      const sw = lit ? 1.08 : 1, S = MG_S * sw, sh = kind === 'wrong' ? Math.sin(G.t * 60) * 1.6 : 0;
      if (lit) {
        const g = ctx.createRadialGradient(x, y, 2, x, y, 38);
        const c = kind === 'wrong' ? '255,60,70' : hexRGB(MG_COL[k]);
        g.addColorStop(0, `rgba(${c},0.75)`); g.addColorStop(1, `rgba(${c},0)`);
        ctx.fillStyle = g; ctx.beginPath(); ctx.arc(x, y, 38, 0, 6.2832); ctx.fill();
      }
      const nm = (lit ? 'mem_n' : 'mem_d') + k, s = M.sprites[nm];
      if (s) { const kx = S / s.w; spr(nm, x + sh - s.c[0] * kx, y - s.c[1] * kx, 1, s.w * kx, s.h * kx); }
      if (kind === 'right') { ctx.beginPath(); ctx.arc(x, y, 25, 0, 6.2832); ctx.lineWidth = 1.6; ctx.strokeStyle = '#ffffff'; ctx.stroke(); }
      if (kind === 'wrong') {
        ctx.lineWidth = 2.2; ctx.strokeStyle = '#ff3a4a'; ctx.beginPath();
        ctx.moveTo(x - 7 + sh, y - 7); ctx.lineTo(x + 7 + sh, y + 7); ctx.moveTo(x + 7 + sh, y - 7); ctx.lineTo(x - 7 + sh, y + 7); ctx.stroke();
      }
    }
    // in the middle: what to do now, and how far into the order you are
    const L = m.seq.length;
    if (m.st === 'show' || m.st === 'input' || m.st === 'ok' || m.st === 'bad') {
      const t = m.st === 'show' ? TR('잘 보세요', 'Watch') : m.st === 'input' ? TR('따라 누르세요', 'Your turn') : m.st === 'ok' ? (m.run > 1 ? TR(`${m.run}연속! +${m.okPts}`, `${m.run} in a row! +${m.okPts}`) : `${TR('좋아요!', 'Nice!')} +${m.okPts}`) : m.why;
      const col = m.st === 'ok' ? '#ffe68a' : m.st === 'bad' ? '#ff9aa4' : '#ffffff';
      label(t, cx, MG_CY - 4, 8.5, 'center', al, col);
      ctx.globalAlpha = al;
      for (let i = 0; i < L; i++) {
        const dx = cx + (i - (L - 1) / 2) * 6.5, on = m.st === 'input' ? i < m.k : m.st === 'ok';
        ctx.beginPath(); ctx.arc(dx, MG_CY + 8, 2.1, 0, 6.2832); ctx.fillStyle = on ? '#ffe68a' : 'rgba(255,255,255,0.22)'; ctx.fill();
        ctx.lineWidth = 0.6; ctx.strokeStyle = '#1a0a14'; ctx.stroke();
      }
    }
    // the rounds: five dots (gold right, red wrong, the one on now ringed)
    for (let i = 0; i < MG_ROUNDS; i++) {
      const r = m.res[i], x = 20 + i * 9, y = 44;
      ctx.globalAlpha = al;
      ctx.beginPath(); ctx.arc(x, y, 3.2, 0, 6.2832); ctx.fillStyle = r === 'ok' ? '#ffd23a' : r === 'bad' ? '#ff5a6a' : 'rgba(255,255,255,0.18)'; ctx.fill();
      ctx.lineWidth = i === m.round && m.st !== 'done' ? 1.3 : 0.8; ctx.strokeStyle = i === m.round && m.st !== 'done' ? '#ffffff' : '#1a0a14'; ctx.stroke();
    }
    label(TR(`${Math.min(m.round + 1, MG_ROUNDS)}/${MG_ROUNDS} 라운드 · ${L}개`, `Round ${Math.min(m.round + 1, MG_ROUNDS)}/${MG_ROUNDS} · ${L}`), 20 + MG_ROUNDS * 9, 44.3, 6.5, 'left', al, '#e8dcff');
    ctx.globalAlpha = al;
    if (m.st === 'intro') {
      const u = G.t - m.stT, a = Math.min(1, u / 0.3) * Math.max(0, Math.min(1, (MG_INTRO - u) / 0.3));
      ctx.globalAlpha = al * a * 0.8; rrect(cx - 118, 78, 236, 54, 8); ctx.fillStyle = '#120a1e'; ctx.fill(); ctx.globalAlpha = al;
      label(TR('기억 시냅스! 5라운드', 'Memory Synapse! 5 rounds'), cx, 92, 15, 'center', a, '#e8d4ff');
      label(TR('뉴런이 빛나는 순서를 잘 보고', 'Watch the order the neurons light up'), cx, 110, 7.5, 'center', a, '#ffffff');
      label(TR('똑같은 순서로 눌러요 (맞힐수록 하나씩 길어져요)', 'then tap them in the same order (one longer each time)'), cx, 121, 7.5, 'center', a, '#ffffff');
    }
    if (m.st === 'done') {
      const v = G.t - m.stT, a = Math.min(1, v / 0.25) * Math.max(0, Math.min(1, (MG_END - v) / 0.35));
      const ok = m.res.filter((r) => r === 'ok').length;
      ctx.globalAlpha = a * 0.82; rrect(cx - 110, 76, 220, 60, 8); ctx.fillStyle = '#120a1e'; ctx.fill(); ctx.globalAlpha = 1;
      label(TR(`${ok}/${MG_ROUNDS} 라운드 성공${ok ? '!' : ''}`, `${ok}/${MG_ROUNDS} rounds cleared${ok ? '!' : ''}`), cx, 92, 14, 'center', a, ok ? '#ffe68a' : '#ffd0dc');
      label(TR(`가장 길게 맞힌 순서 ${m.best || 0}개${(m.bestRun || 0) > 1 ? ` · 최고 연속 ${m.bestRun}` : ''}`, `Longest sequence: ${m.best || 0}${(m.bestRun || 0) > 1 ? ` · best run ${m.bestRun}` : ''}`), cx, 111, 7.5, 'center', a, '#ffffff');
      label(`+${PT(m.gain)}`, cx, 125, 8.5, 'center', a, '#ffe68a');
    }
    ctx.globalAlpha = 1;
  }
  const hexRGB = (h) => [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16)).join(',');

  // ---------------------------------------------------------------- the penalty shoot-out (under the manhole) (v44, v46)
  // Down in a round brick sewer, a goal of white pipes; the keeper is the user's mouse. Five kicks. (v46) The ball on the
  // spot, your runner behind it: the left of the screen is a stick for the aim (a ring on the goal; it can be put off the
  // goal too); the right is the shoot button, and the power bar under the ball has a needle running left and right in it:
  // where the needle is when you press is how hard. Too soft (left of the green): a slow ball the keeper gets to and
  // holds. In the green: it goes where you aimed (the keeper guesses a side as you kick; it cannot reach the top
  // corners); in the bright middle of the green, a hard one it has no time for (unless straight at it). Too hard (past
  // the green): over the bar. Then your runner runs up and kicks it. A goal: 1000 points.
  const PKF = M.pk || { goal: { l: 128, r: 292, bar: 58, line: 118 }, spot: [210, 160] };
  const PK_N = 5, PK_INTRO = 3.0, PK_END = 2.6, PK_AFTER = 1.7, PK_AFTER_GOAL = 2.2, PK_WAIT = 9, PK_PTS = 1000;
  const PK_HALF = (PKF.goal.r - PKF.goal.l) / 2, PK_TALL = PKF.goal.line - PKF.goal.bar;           // 82 wide each side, 60 high
  // (v45) the keeper is the user's mouse (keeper_user.py): pk_k0 ready (front on, gloves up), pk_dR1..6 / pk_dL1..6 the
  // dive to the right / left (standing, crouching, leaping, stretched with the glove out, stretched lower, down); each
  // with its middle (c), bottom and leading glove (lead), in units
  const PK_RUN = 0.5;                                        // the run-up, s
  const PK_SWEEP = [0.8 / 1.5, 0.55 / 1.5];                  // the needle's run end to end, s: the first kick .. the last (v57: half as quick again)
  const PK_WEAK = 0.55, PK_STRONG = 0.8, PK_PERF = [0.635, 0.715];      // the power bar: soft | green (bright middle) | too hard
  const PK_AX = PK_HALF + 16, PK_AH = PK_TALL + 14, PK_AIMV = 100;      // how far the aim goes; how fast (units/s, stick right out)
  const PK_PAD = { r: 19, m: 32, y: 146 };                    // the stick (left) and the button (right): radius, in from the side, height
  const pkGX = (gx) => NWf / 2 + gx, pkGY = (gh) => PKF.goal.line - gh;              // a point on the goal's face -> screen
  const pkKeys = new Set(), PK_KEYS = { ArrowLeft: 'L', KeyA: 'L', ArrowRight: 'R', KeyD: 'R', ArrowUp: 'U', KeyW: 'U', ArrowDown: 'D', KeyS: 'D' };
  function startPK() {
    holdBoost();
    G.obs = G.obs.filter((o) => o.x + o.w < G.x - 12);
    G.items = G.items.filter((i) => i.x < G.x - 12 || i.taken);
    G.pk = { st: 'intro', stT: G.t, inT: G.t, k: 0, res: [], gain: 0, shot: null, msg: null, fx: [], aim: [0, 26], pad: null, nt: 0, power: null, kind: null, fireT: -9, pressT: -9 };
    G.slideHeld = false; held.clear(); pressed.jump = false; pkKeys.clear();
  }
  function endPK() {
    bankGame(G.pk); G.pk = null; G.games = (G.games || 0) + 1; resumeBoost();
    G.genX = Math.max(G.genX, G.x + NW * 0.8);
    G.banner = G.t;
  }
  function pkReady() {
    const p = G.pk; p.st = 'aim'; p.stT = G.t; p.shot = null; p.msg = null; p.power = null; p.kind = null; p.nt = 0; p.aim = [0, 26];
    p.pilot = [(Math.random() < 0.5 ? -1 : 1) * (40 + Math.random() * 36), 10 + Math.random() * 40];
    SND.play('pkWhistle');
  }
  // the needle: 0 .. 1 .. 0 (faster each kick)
  const pkNeedle = (p) => { const T = PK_SWEEP[0] + (PK_SWEEP[1] - PK_SWEEP[0]) * p.k / (PK_N - 1), u = (p.nt / T) % 2; return u < 1 ? u : 2 - u; };
  const pkZone = (v) => v < PK_WEAK ? 'weak' : v > PK_STRONG ? 'strong' : v >= PK_PERF[0] && v <= PK_PERF[1] ? 'perfect' : 'good';
  // the shoot button: the power is what the needle shows now; the aim is kept; the runner runs up
  function pkShoot() {
    const p = G.pk; if (!p || p.st !== 'aim') return;
    p.power = pkNeedle(p); p.kind = pkZone(p.power); p.st = 'run'; p.stT = G.t; p.pressT = G.t; p.pad = null;
    SND.play('ui'); buzz(BUZZ_TAP);
  }
  // the kick (as the runner's foot meets the ball): where it goes and how it comes out, by the aim and the power
  function pkKick(gx, gh, T, kind = 'good') {
    const p = G.pk; if (!p || !['aim', 'run'].includes(p.st)) return;
    if (kind === 'weak') gh *= 0.65;                           // (a soft one does not get up)
    if (kind === 'strong') { gh = Math.max(gh, PK_TALL) + 12 + (p.power - PK_STRONG) * 140; gx *= 1.12; }
    const side = gx < -28 ? -1 : gx > 28 ? 1 : 0;
    const right = Math.random() < 0.33 + 0.06 * p.k;                       // the keeper guesses right more often as it goes on (1 in 3 .. 4 in 7)
    const others = [-1, 0, 1].filter((s) => s !== side);
    let dive = right ? side : others[Math.floor(Math.random() * 2)];
    // can it reach? diving low and middle on its side, jumping in the middle; never the top corners. A soft one it gets to
    // anyway; a hard one only straight at it
    let reach = dive === 0 ? Math.abs(gx) < 30 && gh < 48 : Math.sign(gx) === dive && Math.abs(gx) > 14 && Math.abs(gx) < PK_HALF + 4 && gh < 46;
    if (kind === 'weak') { dive = side; reach = true; }
    if (kind === 'perfect') reach = dive === 0 && Math.abs(gx) < 20 && gh < 40;
    let res;
    if (gh > PK_TALL + 3 || Math.abs(gx) > PK_HALF + 5) res = 'miss';
    else if (Math.abs(Math.abs(gx) - PK_HALF) <= 4 || Math.abs(gh - PK_TALL) <= 3) res = 'post';
    else if (reach) res = 'save';
    else res = 'goal';
    p.shot = { gx, gh, T, t0: G.t, dive, res, done: false, kind };
    p.st = 'fly'; p.stT = G.t; p.fireT = G.t;
    SND.play('pkKick'); buzz(kind === 'perfect' ? [30, 20, 40] : BUZZ_TAP);
  }
  function pkLand() {                                       // the ball gets to the goal's face
    const p = G.pk, s = p.shot;
    s.done = true; p.res.push(s.res); p.st = 'after'; p.stT = G.t;
    const at = [pkGX(s.gx), pkGY(s.gh)];
    if (s.res === 'goal') { p.run = (p.run || 0) + 1; p.bestRun = Math.max(p.bestRun || 0, p.run); p.goalPts = comboPts(PK_PTS, p.run); p.gain += p.goalPts; SND.play('pkGoal'); buzz([40, 30, 70]); p.fx.push({ kind: 'goal', at, t: G.t }); }     // (v57: goals in a row: +20% each)
    else p.run = 0;
    if (s.res === 'save') { SND.play('pkSave'); buzz(30); }
    else if (s.res === 'post') { SND.play('pkPost'); buzz(25); p.fx.push({ kind: 'post', at, t: G.t }); }
    else if (s.res === 'miss') SND.play('pkMiss');
    p.msg = { s: { goal: TR('골!!', 'GOAL!!'), save: s.kind === 'weak' ? TR('잡혔다!', 'Caught!') : TR('막혔다!', 'Saved!'), post: TR('골대!', 'Post!'), miss: s.gh > PK_TALL ? TR('넘어갔다', 'Over the bar') : TR('빗나갔다', 'Wide') }[s.res], t: G.t, res: s.res };
  }
  function stepPK(dt) {
    const p = G.pk;
    if (p.st === 'intro') { if (G.t - p.stT > PK_INTRO) pkReady(); return; }
    if (p.st === 'aim') {
      p.nt += dt;
      let vx = 0, vy = 0;
      if (p.pad) { vx = p.pad.kx; vy = p.pad.ky; }
      if (pkKeys.has('L')) vx -= 1; if (pkKeys.has('R')) vx += 1; if (pkKeys.has('U')) vy -= 1; if (pkKeys.has('D')) vy += 1;
      if (AUTO && !window.__noAuto) {                       // the test pilot: to a corner, then the button in the green
        const dx = p.pilot[0] - p.aim[0], dy = p.aim[1] - p.pilot[1], d = Math.hypot(dx, dy);
        if (d > 2) { vx = dx / d; vy = dy / d; } else if (G.t - p.stT > 0.8 && pkZone(pkNeedle(p)) !== 'weak' && pkZone(pkNeedle(p)) !== 'strong') pkShoot();
      }
      p.aim[0] = Math.max(-PK_AX, Math.min(PK_AX, p.aim[0] + vx * PK_AIMV * dt));
      p.aim[1] = Math.max(0, Math.min(PK_AH, p.aim[1] - vy * PK_AIMV * dt));
      if (p.st === 'aim' && G.t - p.stT > PK_WAIT) pkShoot();                  // (nothing pressed: it goes as the needle is)
    }
    if (p.st === 'run' && G.t - p.stT >= PK_RUN) pkKick(p.aim[0], p.aim[1], { weak: 1.1, good: 0.55, perfect: 0.42, strong: 0.45 }[p.kind], p.kind);
    if (p.st === 'fly' && G.t - p.shot.t0 >= p.shot.T) pkLand();
    if (p.st === 'after' && G.t - p.stT > (p.shot.res === 'goal' ? PK_AFTER_GOAL : PK_AFTER)) {
      if (++p.k >= PK_N) { p.st = 'done'; p.stT = G.t; SND.play(p.res.includes('goal') ? 'orbClear' : 'bbOut'); }
      else pkReady();
    }
    p.fx = p.fx.filter((e) => G.t - e.t < 1.6);
    if (p.st === 'done' && G.t - p.stT > PK_END) endPK();
  }
  // touches: the left half is the stick (it moves from where the finger goes down), the right half the button
  function pkDown(id, x, y) {
    const p = G.pk; if (!p || p.st !== 'aim') return;
    if (x < NW / 2) p.pad = { id, ox: x, oy: y, kx: 0, ky: 0 };
    else pkShoot();
  }
  function pkMove(id, x, y) {
    const p = G.pk; if (!p || !p.pad || p.pad.id !== id) return;
    let dx = (x - p.pad.ox) / PK_PAD.r, dy = (y - p.pad.oy) / PK_PAD.r; const d = Math.hypot(dx, dy);
    if (d > 1) { dx /= d; dy /= d; }
    p.pad.kx = dx; p.pad.ky = dy;
  }
  function pkUp(id) { const p = G.pk; if (p && p.pad && p.pad.id === id) p.pad = null; }
  // ---- drawing
  function pkBallAt(s, u) {                                 // the ball u of the way (0 the spot .. 1 the goal's face, on past it)
    const zx = NWf / 2, sx = zx + (PKF.spot[0] - 210), sy = PKF.spot[1] - 7, q = Math.min(1, u);
    // going away from the eye: its size falls as 1/distance (0.36 at the goal), and it closes on the goal's point the same way
    const k0 = 1 / (1 + 1.78 * q), e = (1 - k0) / (1 - 1 / 2.78);
    let x = sx + (pkGX(s.gx) - sx) * e, y = sy + (pkGY(s.gh) - sy) * e - Math.sin(Math.PI * q) * (6 + s.gh * 0.15), k = k0;
    if (u > 1) {                                             // on past the face: into the net, off the post, saved, away
      const v = u - 1;
      if (s.res === 'goal') { k *= 1 - 0.15 * Math.min(1, v * 3); y += Math.min(6, v * 18); x += Math.sign(s.gx) * Math.min(4, v * 10); }
      else if (s.res === 'post') { const hb = Math.abs(s.gh - PK_TALL) <= 3; x += (hb ? Math.sign(s.gx) * 30 : -Math.sign(s.gx) * 120) * v; y += hb ? -40 * v + 160 * v * v : -20 * v + 150 * v * v; k *= 1 + v * 0.7; y = Math.min(y, PKF.goal.line + 26); }
      else if (s.res === 'save') {
        if (s.dive) { x += s.dive * 80 * v; y += -30 * v + 170 * v * v; k *= 1 + 0.5 * Math.min(1, v); }
        else { x += Math.sign(s.gx || 1) * 18 * v; y += -10 * v + 150 * v * v; k *= 1 + 0.3 * Math.min(1, v); }
        y = Math.min(y, PKF.goal.line + 12);
      }
      else { x += s.gx * v * 0.8; y -= s.gh > PK_TALL ? v * 50 : 0; k *= 1 - 0.4 * Math.min(1, v); }
    }
    return { x, y, k };
  }
  // the keeper at a time: which picture, and where (its middle, or for the ready pose its feet's middle). It reacts 0.1 s
  // after the kick: diving, a crouch, the leap, stretched out with the leading glove reaching where it guessed (on a
  // save, the ball, as the ball gets there), stretched lower, then down on the ground; in the middle, it jumps (gloves up
  // to the ball on a save)
  function pkKeeper(s) {
    const zx = NWf / 2, line = PKF.goal.line + 1, t = s ? G.t - s.t0 : 0, R = 0.1;
    if (!s || t < R) return { nm: 'pk_k0', x: zx + (s ? 0 : Math.sin(G.t * 3.1) * 4), y: line - (s ? 0 : Math.abs(Math.sin(G.t * 6.2)) * 1.2), at: 'feet' };
    const save = s.res === 'save', Tc = s.T;
    if (s.dive === 0) {                                     // in the middle: a jump, gloves (15 over its feet) up to the ball
      const k0 = M.sprites.pk_k0, gy = k0.bottom - k0.hands[0][1];
      const up = save ? Math.max(4, s.gh - gy + 2) : 8, tx = save ? Math.max(-14, Math.min(14, s.gx * 0.6)) : 0;
      const q = Math.min(1, (t - R) / Math.max(0.15, Tc - R)), e = 1 - (1 - q) * (1 - q);
      const down = Math.max(0, Math.min(1, (t - Tc - 0.15) / 0.3));
      return { nm: 'pk_k0', x: zx + tx * e, y: line - up * e * (1 - down * down), at: 'feet' };
    }
    const d = s.dive, f = (k) => 'pk_d' + (d > 0 ? 'R' : 'L') + k, F = (k) => M.sprites[f(k)];
    const t2 = R + 0.06, t3 = t2 + 0.45 * Math.max(0.1, Tc - t2);
    if (t < t2) { const S = F(2); return { nm: f(2), x: zx + d * 2, y: line - (S.bottom - S.c[1]), at: 'c' }; }
    // where the leading glove of the stretched picture goes, and so where its middle is then
    const S4 = F(4), hx = save ? pkGX(s.gx) : zx + d * 58, hy = save ? pkGY(s.gh) : pkGY(26);
    const cx4 = hx - (S4.lead[0] - S4.c[0]), cy4 = Math.min(line + 12 - (S4.bottom - S4.c[1]), hy - (S4.lead[1] - S4.c[1]));
    const S2 = F(2), cx2 = zx + d * 2, cy2 = line - (S2.bottom - S2.c[1]);
    if (t < Tc) {
      const q = (t - t2) / (Tc - t2), e = 1 - (1 - q) * (1 - q);
      return { nm: f(t < t3 ? 3 : 4), x: cx2 + (cx4 - cx2) * e, y: cy2 + (cy4 - cy2) * e - 4 * Math.sin(Math.PI * q), at: 'c' };
    }
    if (t < Tc + 0.1) { const q = (t - Tc) / 0.1; return { nm: f(4), x: cx4 + d * 3 * q, y: cy4 + 2 * q, at: 'c' }; }
    const S5 = F(5), cx5 = cx4 + d * 3, cy5 = cy4 + 2;
    if (t < Tc + 0.3) { const q = (t - Tc - 0.1) / 0.2; return { nm: f(5), x: cx5 + d * 4 * q, y: cy5 + 8 * q * q, at: 'c' }; }
    const S6 = F(6), cx6 = cx5 + d * 6, cy6 = Math.max(cy5 + 8, line + 3 - (S6.bottom - S6.c[1]));
    const q = Math.min(1, (t - Tc - 0.3) / 0.12);
    return { nm: f(6), x: cx5 + d * 4 + (cx6 - cx5 - d * 4) * q, y: cy5 + 8 + (cy6 - cy5 - 8) * q * q, at: 'c' };
  }
  // (v46) the runner: waiting behind the ball and to its left (turned towards it: its back-right picture), running up
  // (bobbing, getting smaller as it goes away from us), the kick (turned to the goal, a lunge and a lean), then still
  function drawKicker(p, al) {
    const n = G.char, zx = NWf / 2, bx = zx + (PKF.spot[0] - 210), by = PKF.spot[1];
    const A = { x: bx - 60, y: 178, k: 0.56 }, B = { x: bx - 16, y: by + 6, k: 0.5 };
    let x = A.x, y = A.y, k = A.k, view = '135', lean = 0, bob = Math.abs(Math.sin(G.t * 2.6)) * 0.8;
    if (p.st === 'run') {
      const q = Math.min(1, (G.t - p.stT) / PK_RUN), e = q * q * (3 - 2 * q) * 0.6 + q * 0.4;
      x = A.x + (B.x - A.x) * e; y = A.y + (B.y - A.y) * e; k = A.k + (B.k - A.k) * e;
      bob = Math.abs(Math.sin(q * Math.PI * 4)) * 4; lean = 8;
    } else if (['fly', 'after', 'done'].includes(p.st)) {
      const v = G.t - p.fireT, l = v < 0.1 ? v / 0.1 : Math.max(0, 1 - (v - 0.1) / 0.35);
      x = B.x + 6 * l; y = B.y - 2 * l; k = B.k; view = '180'; lean = 18 * l; bob = 0;
    }
    const sp = M.sprites[`bt_${n}_${view}`]; if (!sp) return;
    ctx.globalAlpha = al * 0.3; ctx.fillStyle = '#000000'; ctx.beginPath(); ctx.ellipse(x, y, sp.w * k * 0.32, 2.4 * k / 0.5, 0, 0, 6.2832); ctx.fill(); ctx.globalAlpha = al;
    ctx.save(); ctx.translate(x, y - bob); ctx.rotate(lean * Math.PI / 180); ctx.scale(k, k);
    spr(`bt_${n}_${view}`, -sp.foot[0], -sp.foot[1], 1, sp.w, sp.h); ctx.restore(); ctx.globalAlpha = al;
  }
  // the stick (left), the shoot button (right) and the power bar (under the ball)
  function drawPKControls(p, al) {
    const live = p.st === 'aim', on = ['aim', 'run', 'fly', 'after'].includes(p.st); if (!on) return;
    const R = PK_PAD.r, sx = PK_PAD.m, by = PK_PAD.y, bxr = NWf - PK_PAD.m;
    // the stick: a ring, a knob that follows the finger
    ctx.globalAlpha = al * (live ? 1 : 0.45);
    ctx.beginPath(); ctx.arc(sx, by, R, 0, 6.2832); ctx.fillStyle = 'rgba(26,10,20,0.5)'; ctx.fill(); ctx.lineWidth = 1.2; ctx.strokeStyle = 'rgba(255,255,255,0.75)'; ctx.stroke();
    const kx = p.pad ? p.pad.kx : 0, ky = p.pad ? p.pad.ky : 0;
    ctx.beginPath(); ctx.arc(sx + kx * R * 0.55, by + ky * R * 0.55, 8.5, 0, 6.2832); ctx.fillStyle = p.pad ? 'rgba(255,236,170,0.95)' : 'rgba(255,255,255,0.85)'; ctx.fill();
    ctx.lineWidth = 1; ctx.strokeStyle = '#1a0a14'; ctx.stroke();
    label(TR('조준', 'Aim'), sx, by + R + 6.5, 6.5, 'center', al * (live ? 1 : 0.45), '#ffffff');
    // the button
    const pr = G.t - p.pressT < 0.15;
    ctx.globalAlpha = al * (live ? 1 : 0.45);
    ctx.beginPath(); ctx.arc(bxr, by + (pr ? 1 : 0), R, 0, 6.2832);
    const g = ctx.createRadialGradient(bxr - 5, by - 6, 2, bxr, by, R); g.addColorStop(0, pr ? '#ffd0a0' : '#ffb070'); g.addColorStop(0.55, pr ? '#e85020' : '#ff6a2a'); g.addColorStop(1, '#a82a10');
    ctx.fillStyle = g; ctx.fill(); ctx.lineWidth = 1.4; ctx.strokeStyle = '#2a0a06'; ctx.stroke();
    label(TR('슛!', 'Shoot!'), bxr, by + (pr ? 1 : 0), 10, 'center', al * (live ? 1 : 0.55), '#ffffff');
    if (live) { ctx.globalAlpha = al * (0.25 + 0.25 * Math.sin(G.t * 6)); ctx.beginPath(); ctx.arc(bxr, by, R + 3, 0, 6.2832); ctx.lineWidth = 1.5; ctx.strokeStyle = '#ffd080'; ctx.stroke(); }
    ctx.globalAlpha = al;
    // the power bar (right of the ball, left of the button): soft (blue grey) | the green (bright in its middle) | too
    // hard (red); the needle
    const x0 = NWf / 2 + 16, W = Math.min(120, bxr - R - 10 - x0), H = 8, y0 = 168;
    rrect(x0 - 1.5, y0 - 1.5, W + 3, H + 3, 5); ctx.fillStyle = '#1a0a14'; ctx.fill();
    ctx.save(); rrect(x0, y0, W, H, 4); ctx.clip();
    const zone = (a, b, c0, c1) => { const gg = ctx.createLinearGradient(0, y0, 0, y0 + H); gg.addColorStop(0, c0); gg.addColorStop(1, c1); ctx.fillStyle = gg; ctx.fillRect(x0 + a * W, y0, (b - a) * W, H); };
    zone(0, PK_WEAK, '#9ab0d0', '#4a5a7a'); zone(PK_WEAK, PK_STRONG, '#7af08a', '#20a040'); zone(PK_PERF[0], PK_PERF[1], '#fff6a0', '#f0b020'); zone(PK_STRONG, 1, '#ff8a7a', '#c01818');
    ctx.fillStyle = 'rgba(255,255,255,0.35)'; ctx.fillRect(x0, y0, W, H * 0.35);
    ctx.restore();
    label(TR('약', 'Soft'), x0 + W * PK_WEAK / 2, y0 - 4, 5.5, 'center', al * 0.9, '#c8d8f0');
    label(TR('정타', 'Sweet'), x0 + W * (PK_PERF[0] + PK_PERF[1]) / 2, y0 - 4, 5.5, 'center', al, '#ffe68a');
    label(TR('셈', 'Hard'), x0 + W * (PK_STRONG + 1) / 2, y0 - 4, 5.5, 'center', al * 0.9, '#ffb0a8');
    const v = p.st === 'aim' ? pkNeedle(p) : p.power ?? 0, nx = x0 + v * W;
    ctx.beginPath(); ctx.moveTo(nx - 3, y0 - 3.5); ctx.lineTo(nx + 3, y0 - 3.5); ctx.lineTo(nx, y0 + 1); ctx.closePath(); ctx.fillStyle = '#ffffff'; ctx.fill(); ctx.lineWidth = 0.8; ctx.strokeStyle = '#1a0a14'; ctx.stroke();
    ctx.fillStyle = '#1a0a14'; ctx.fillRect(nx - 1.3, y0 - 1, 2.6, H + 2); ctx.fillStyle = '#ffffff'; ctx.fillRect(nx - 0.6, y0 - 0.5, 1.2, H + 1);
    // what the press came to
    if (p.kind && p.st !== 'aim') {
      const t = { perfect: [TR('정타!', 'Sweet shot!'), '#ffe14a'], good: [TR('좋아요', 'Good'), '#8af09a'], weak: [TR('약해요', 'Too soft'), '#a8c0e8'], strong: [TR('너무 세요', 'Too hard'), '#ff8a7a'] }[p.kind], v2 = G.t - p.pressT;
      label(t[0], x0 + W / 2, y0 - 13, (p.kind === 'perfect' ? 10 : 8) * (1 + 0.25 * Math.max(0, 1 - v2 / 0.2)), 'center', al, t[1]);
    }
  }
  // the aim on the goal: a ring (red off the goal), pulsing while you can move it
  function drawPKAim(p, al) {
    if (!['aim', 'run'].includes(p.st)) return;
    const x = pkGX(p.aim[0]), y = pkGY(p.aim[1]), off = Math.abs(p.aim[0]) > PK_HALF - 3 || p.aim[1] > PK_TALL - 2;
    const r = 6 + (p.st === 'aim' ? Math.sin(G.t * 7) * 0.8 : 0), c = off ? '#ff5a5a' : '#ffe68a';
    ctx.globalAlpha = al; ctx.lineWidth = 2.6; ctx.strokeStyle = '#1a0a14';
    ctx.beginPath(); ctx.arc(x, y, r, 0, 6.2832); ctx.stroke();
    ctx.lineWidth = 1.4; ctx.strokeStyle = c; ctx.beginPath(); ctx.arc(x, y, r, 0, 6.2832); ctx.stroke();
    ctx.beginPath(); for (const [a, b] of [[-1, 0], [1, 0], [0, -1], [0, 1]]) { ctx.moveTo(x + a * (r - 2.5), y + b * (r - 2.5)); ctx.lineTo(x + a * (r + 3), y + b * (r + 3)); }
    ctx.lineWidth = 1.2; ctx.stroke();
    ctx.beginPath(); ctx.arc(x, y, 1.1, 0, 6.2832); ctx.fillStyle = c; ctx.fill();
  }
  function drawPK() {
    const p = G.pk; if (!p) return;
    world();
    let al = Math.min(1, (G.t - p.inT) / 0.35);
    if (p.st === 'done') al *= Math.max(0, Math.min(1, (PK_END - (G.t - p.stT)) / 0.35));
    ctx.globalAlpha = al;
    const zx = NWf / 2;
    ctx.fillStyle = '#120a0a'; ctx.fillRect(0, 0, NWf, NH);
    spr('pk_field', zx - 210, 0, 1, 420, 180);
    const s = p.shot, u = s ? (G.t - s.t0) / s.T : 0;
    // the net bulging where a goal went in
    for (const e of p.fx) if (e.kind === 'goal') {
      const v = (G.t - e.t) / 0.6; if (v > 1) continue;
      ctx.globalAlpha = al * (1 - v) * 0.8;
      for (const r of [6, 12, 18]) { ctx.beginPath(); ctx.ellipse(e.at[0], e.at[1], r * (0.5 + v), r * 0.6 * (0.5 + v), 0, 0, 6.2832); ctx.lineWidth = 1; ctx.strokeStyle = '#ffffff'; ctx.stroke(); }
      ctx.globalAlpha = al;
    }
    // the ball when it is in or behind the goal's face (drawn before the keeper)
    const B = s ? pkBallAt(s, u) : null, behind = s && u >= 1 && (s.res === 'goal' || s.res === 'miss');
    const ball = (b, spin) => { const w = 20 * b.k; ctx.save(); ctx.translate(b.x, b.y); ctx.rotate(spin); spr('pk_ball', -w / 2, -w / 2, 1, w, w); ctx.restore(); ctx.globalAlpha = al; };
    const spin = s ? (G.t - s.t0) * 16 * (s.gx < 0 ? -1 : 1) : 0;
    if (behind) ball(B, spin);
    // the keeper
    { const K = pkKeeper(s), sp = M.sprites[K.nm];
      if (sp) {
        const x0 = K.at === 'feet' ? K.x - sp.w / 2 : K.x - sp.c[0], y0 = K.at === 'feet' ? K.y - sp.bottom : K.y - sp.c[1];
        // its shadow on the floor under it (fainter the higher it is)
        const ground = PKF.goal.line + 1, hgt = Math.max(0, ground - (y0 + sp.bottom));
        ctx.globalAlpha = al * 0.32 * Math.max(0.25, 1 - hgt / 50); ctx.fillStyle = '#000000';
        ctx.beginPath(); ctx.ellipse(x0 + sp.w / 2, Math.max(ground, y0 + sp.bottom) + 0.5, sp.w * 0.36, 2.6, 0, 0, 6.2832); ctx.fill(); ctx.globalAlpha = al;
        spr(K.nm, x0, y0, 1, sp.w, sp.h); ctx.globalAlpha = al;
      } }
    // the ball in front: on the spot, in flight, saved (knocked away), off the post
    if (!s) ball({ x: zx + (PKF.spot[0] - 210), y: PKF.spot[1] - 7, k: 1 }, 0);
    else if (!behind) ball(B, spin);
    drawKicker(p, al);
    drawPKAim(p, al);
    drawPKControls(p, al);
    // a goal: a burst of confetti from the net, the screen flashing a moment
    for (const e of p.fx) {
      const v = G.t - e.t;
      if (e.kind === 'goal') {
        if (v < 0.12) { ctx.globalAlpha = al * (1 - v / 0.12) * 0.35; ctx.fillStyle = '#fff6d8'; ctx.fillRect(0, 0, NWf, NH); }
        const R = rng(Math.round(e.t * 1000));
        for (let i = 0; i < 46; i++) {
          const a = R() * 6.2832, sp = 60 + R() * 140, x = e.at[0] + Math.cos(a) * sp * v, y = e.at[1] + Math.sin(a) * sp * v + 90 * v * v;
          ctx.globalAlpha = al * Math.max(0, 1 - v / 1.4);
          ctx.fillStyle = ['#ff5a6a', '#ffd23a', '#5ad26a', '#4aa8ff', '#ffffff', '#c47aff'][i % 6];
          ctx.save(); ctx.translate(x, y); ctx.rotate(v * 8 + i); ctx.fillRect(-1.6, -0.8, 3.2, 1.6); ctx.restore();
        }
      } else if (e.kind === 'post' && v < 0.3) {
        ctx.globalAlpha = al * (1 - v / 0.3); ctx.beginPath(); ctx.arc(e.at[0], e.at[1], 6 + v * 40, 0, 6.2832); ctx.lineWidth = 2; ctx.strokeStyle = '#ffffff'; ctx.stroke();
      }
    }
    ctx.globalAlpha = al;
    // the kicks: five balls (used ones: green for a goal, dim for the rest)
    for (let i = 0; i < PK_N; i++) {
      const r = p.res[i], x = 20 + i * 10, y = 44;
      ctx.globalAlpha = al * (r && r !== 'goal' ? 0.3 : 1);
      spr('pk_ball', x - 4, y - 4, 1, 8, 8);
      if (r === 'goal') { ctx.beginPath(); ctx.arc(x, y, 5, 0, 6.2832); ctx.lineWidth = 1.2; ctx.strokeStyle = '#5ae07a'; ctx.stroke(); }
    }
    ctx.globalAlpha = al;
    if (p.msg && p.st !== 'done') {
      const v = G.t - p.msg.t, big = p.msg.res === 'goal', a = Math.min(1, v / 0.08) * Math.max(0, Math.min(1, ((big ? 2.0 : 1.5) - v) / 0.3));
      const sc = big ? 1 + 0.25 * Math.max(0, 1 - v / 0.25) : 1;
      label(p.msg.s, zx, 50, (big ? 22 : 13) * sc, 'center', a, big ? '#ffe68a' : p.msg.res === 'save' ? '#ffb0b8' : '#ffffff');
      if (big) label(p.run > 1 ? TR(`${p.run}연속 골! +${PT(p.goalPts)}`, `${p.run} in a row! +${PT(p.goalPts)}`) : `+${PT(p.goalPts)}`, zx, 68, 9, 'center', a, '#ffe68a');
    }
    if (p.st === 'intro') {
      const v = G.t - p.stT, a = Math.min(1, v / 0.3) * Math.max(0, Math.min(1, (PK_INTRO - v) / 0.3));
      ctx.globalAlpha = al * a * 0.8; rrect(zx - 124, 50, 248, 64, 8); ctx.fillStyle = '#1a0a14'; ctx.fill(); ctx.globalAlpha = al;
      label(TR('승부차기! 5번 차요', 'Penalty Shootout! 5 kicks'), zx, 64, 15, 'center', a, '#ffe0a8');
      label(TR('왼쪽으로 골대 어디에 찰지 조준, 오른쪽 버튼으로 슛', 'Aim with the left side, shoot with the right button'), zx, 82, 7.5, 'center', a, '#ffffff');
      label(TR('세기 바의 초록 칸에서 눌러야 정타 · 약하면 잡히고 너무 세면 넘어가요', 'Press in the green for a clean strike · too soft gets caught, too hard flies over'), zx, 93, 7, 'center', a, '#ffffff');
      label(TR('골마다 1,000점 · 연속 골은 더 많이!', '1,000 pts a goal · more for goals in a row!'), zx, 104, 7, 'center', a, '#ffe68a');
    }
    if (p.st === 'done') {
      const v = G.t - p.stT, a = Math.min(1, v / 0.25) * Math.max(0, Math.min(1, (PK_END - v) / 0.35));
      const n = (q) => p.res.filter((r) => r === q).length;
      ctx.globalAlpha = a * 0.8; rrect(zx - 110, 54, 220, 60, 8); ctx.fillStyle = '#1a0a14'; ctx.fill(); ctx.globalAlpha = 1;
      label(TR(`골 ${n('goal')}개${n('goal') ? '!' : ''}`, `${n('goal')} goal${n('goal') === 1 ? '' : 's'}${n('goal') ? '!' : ''}`), zx, 70, 14, 'center', a, n('goal') ? '#ffe68a' : '#ffd0dc');
      label(TR(`골 ${n('goal')} · 막힘 ${n('save')} · 골대 ${n('post')} · 빗나감 ${n('miss')}`, `Goals ${n('goal')} · Saved ${n('save')} · Post ${n('post')} · Missed ${n('miss')}`), zx, 90, 7.5, 'center', a, '#ffffff');
      label(`${(p.bestRun || 0) > 1 ? TR(`최고 연속 ${p.bestRun} · `, `Best run ${p.bestRun} · `) : ''}+${PT(p.gain)}`, zx, 104, 8.5, 'center', a, '#ffe68a');
    }
    ctx.globalAlpha = 1;
  }

  // ---------------------------------------------------------------- the toilet jackpot (in the toilet bowl) (v44)
  // A slot machine made of a toilet tank. Three goes: tap anywhere to pull the flush lever and the reels spin; tap
  // again to stop them one by one (left to right; or a reel's own button under it). Three the same pays (a golden poop
  // is the jackpot), two the same a little. What each go comes to is drawn when the lever is pulled (like a real
  // machine; with a better chance on the last go if nothing three-of-a-kind came up); the reels stop where your taps
  // land, and slide on to it. Two alike on the first two reels: '리치' - the last reel slows down, a drum roll.
  // (v45) the machine is the user's picture (slot_user.py): its windows, marquee bar, bulbs, buttons, foot light and lever
  // found in it (M.sl, in units from its top left); its feet on the screen's bottom
  const SLF = M.sl;
  const SL_N = 3, SL_INTRO = 2.6, SL_END = 2.8, SL_SPEED = 15, SL_REACH_V = 4.5, SL_GAP = 31, SL_SYM = 31, SL_AUTO = 4;
  const slMY = () => NH - SH('sl_machine');
  const slWin = (i) => { const [x0, y0, x1, y1] = SLF.wins[i]; return { x0, y0, x1, y1, cx: (x0 + x1) / 2, cy: (y0 + y1) / 2, w2: (x1 - x0) / 2, h2: (y1 - y0) / 2 }; };
  const SL_PAY = [5000, 2000, 1500, 1000, 700, 500], SL_PAIR = 100;
  const SL_NAME = LANG === 'ko' ? ['황금똥', '고무오리', '뚫어뻥', '두루마리', '비누', '물방울'] : ['golden poops', 'rubber ducks', 'plungers', 'toilet rolls', 'soaps', 'water drops'];
  // the strips: each symbol at least twice, the cheap ones more often, the golden poop twice
  const SL_STRIP = [[5, 3, 1, 4, 0, 5, 2, 4, 3, 5, 1, 4, 2, 5, 0, 3, 4, 5], [4, 5, 0, 3, 2, 5, 4, 1, 5, 3, 4, 0, 2, 5, 3, 1, 4, 5], [3, 4, 5, 1, 0, 4, 5, 2, 3, 5, 4, 1, 3, 0, 5, 2, 4, 5]];
  const slMX = () => NWf / 2 - SW('sl_machine') / 2;
  function startSlot() {
    holdBoost();
    G.obs = G.obs.filter((o) => o.x + o.w < G.x - 12);
    G.items = G.items.filter((i) => i.x < G.x - 12 || i.taken);
    G.slLap = stationAt(G.x).lap;
    G.sl = { st: 'intro', stT: G.t, inT: G.t, k: 0, res: [], gain: 0, best3: false, reels: [0, 1, 2].map((i) => ({ pos: Math.floor(Math.random() * 18), spin: false, stop: null, strip: SL_STRIP[i].slice(), vNow: 0 })),
      want: null, msg: null, coins: [], leverT: -9, tick: 0, drum: 0, flash: -9, press: [-9, -9, -9] };
    G.slideHeld = false; held.clear(); pressed.jump = false;
  }
  function endSlot() {
    bankGame(G.sl); G.sl = null; G.games = (G.games || 0) + 1; resumeBoost();
    G.genX = Math.max(G.genX, G.x + NW * 0.8);
    G.banner = G.t;
  }
  // what this go comes to: three of a kind (which), two (which places), or nothing
  function slOutcome() {
    const s = G.sl, last = s.k === SL_N - 1 && !s.best3, r = Math.random();
    const pJack = last ? 0.15 : 0.07, p3 = last ? 0.6 : 0.3, p2 = 0.35;
    const pick = (ex) => { let v; do v = 1 + Math.floor(Math.random() * 5); while (ex.includes(v)); return v; };
    if (r < pJack) return [0, 0, 0];
    if (r < p3) { const v = [1, 1, 2, 3, 3, 4, 4, 5, 5, 5][Math.floor(Math.random() * 10)]; return [v, v, v]; }
    if (r < p3 + p2) {
      const v = Math.random() < 0.15 ? 0 : pick([]), o = pick([v]);
      return Math.random() < 0.5 ? [v, v, o] : Math.random() < 0.5 ? [v, o, v] : [o, v, v];          // (two on the left first: a reach that fails)
    }
    const a = Math.floor(Math.random() * 6); let b, c; do b = Math.floor(Math.random() * 6); while (b === a); do c = Math.floor(Math.random() * 6); while (c === a || c === b);
    return [a, b, c];
  }
  function slPull() {
    const s = G.sl; if (!s || s.st !== 'ready') return;
    s.want = slOutcome(); s.st = 'spin'; s.stT = G.t; s.leverT = G.t; s.msg = null;
    s.reels.forEach((rl, i) => { rl.spin = true; rl.stop = null; rl.t0 = G.t + 0.12 + i * 0.08; rl.v = SL_SPEED; });
    s.reach = false;
    SND.play('slLever'); buzz(25);
  }
  // stop a reel: it runs on to the next place on its strip showing what it should (at least two symbols on), easing in
  function slStop(i) {
    const s = G.sl, rl = s.reels[i]; if (!rl.spin || rl.stop || G.t < rl.t0 + 0.4) return false;
    // it stops two or three symbols on (those are above the window, out of sight): what it stops on is put there, and on a
    // reach that fails the one it needed just above it (one short: it would have come next)
    const st = rl.strip, n = st.length, ix = (k) => ((k % n) + n) % n, v = i === 2 && s.reach ? SL_REACH_V : rl.v;
    const k = Math.ceil(rl.pos) + 2;
    st[ix(k)] = s.want[i];
    if (i === 2 && s.want[0] === s.want[1] && s.want[2] !== s.want[0]) st[ix(k + 1)] = s.want[0];
    else if (st[ix(k + 1)] === s.want[i]) st[ix(k + 1)] = (s.want[i] + 1 + Math.floor(Math.random() * 5)) % 6;
    rl.stop = { from: rl.pos, to: k, t0: G.t, dur: Math.max(0.25, Math.min(2.2, 3 * (k - rl.pos) / v)) };     // (eased out: going on at the speed it had)
    return true;
  }
  function slTap(x, y) {
    const s = G.sl; if (!s) return;
    if (s.st === 'ready') { slPull(); return; }
    if (s.st !== 'spin') return;
    // a reel's own button, or else the leftmost still spinning
    const mx = slMX(), my = slMY();
    for (let i = 0; i < 3; i++) { const [bx, by, rx, ry] = SLF.btns[i]; if (Math.abs(x - (mx + bx)) < rx + 3 && Math.abs(y - (my + by)) < ry + 5) { s.press[i] = G.t; if (slStop(i)) { SND.play('ui'); buzz(BUZZ_TAP); } return; } }
    for (let i = 0; i < 3; i++) { const rl = s.reels[i]; if (rl.spin && !rl.stop) { if (slStop(i)) { s.press[i] = G.t; SND.play('ui'); buzz(BUZZ_TAP); } return; } }
  }
  function slResult() {
    const s = G.sl, w = s.want;
    let pts = 0, kind = 'none';
    if (w[0] === w[1] && w[1] === w[2]) { pts = SL_PAY[w[0]]; kind = w[0] === 0 ? 'jackpot' : 'three'; s.best3 = true; }
    else if (w[0] === w[1] || w[1] === w[2] || w[0] === w[2]) { pts = SL_PAIR; kind = 'two'; }
    if (pts > 0) { s.run = (s.run || 0) + 1; s.bestRun = Math.max(s.bestRun || 0, s.run); pts = comboPts(pts, s.run); } else s.run = 0;     // (v57) wins in a row: +20% each
    s.gain += pts; s.res.push(kind);
    s.st = 'after'; s.stT = G.t; s.flash = G.t; s.reach = false;
    s.msg = { kind, pts, k: s.run, sym: w[0] === w[1] || w[0] === w[2] ? w[0] : w[1], t: G.t, near: w[0] === w[1] && w[2] !== w[0] };
    if (kind === 'jackpot') { SND.play('slJackpot'); buzz([60, 40, 60, 40, 120]); for (let i = 0; i < 140; i++) s.coins.push({ x: Math.random() * NWf, y: -10 - Math.random() * 180, vx: (Math.random() * 2 - 1) * 20, vy: 40 + Math.random() * 60, r: Math.random() * 6.28, vr: (Math.random() * 2 - 1) * 10 }); }
    else if (kind === 'three') { SND.play('slWin'); buzz([40, 30, 60]); const w1 = slWin(1); for (let i = 0; i < 40; i++) s.coins.push({ x: slMX() + w1.cx, y: slMY() + w1.cy, vx: (Math.random() * 2 - 1) * 150, vy: -80 - Math.random() * 120, r: 0, vr: (Math.random() * 2 - 1) * 10 }); }
    else if (kind === 'two') SND.play('slSmall');
    else SND.play('miss');
  }
  function stepSlot(dt) {
    const s = G.sl;
    if (s.st === 'intro' && G.t - s.stT > SL_INTRO) { s.st = 'ready'; s.stT = G.t; }
    if (s.st === 'ready' && AUTO && !window.__noAuto && G.t - s.stT > 0.4) slPull();
    if (s.st === 'spin') {
      const u = G.t - s.stT;
      // a reach: the first two have landed alike and the last still turns (slowing right down, a drum roll; 3 s, then it stops)
      const reach = s.want[0] === s.want[1] && !s.reels[0].spin && !s.reels[1].spin && s.reels[2].spin && G.t >= s.reels[2].t0;
      if (reach && !s.reach) { SND.play('slReach'); s.reachT = G.t; }
      s.reach = reach;
      if (AUTO && !window.__noAuto) { for (let i = 0; i < 3; i++) if (u > 0.9 + i * 0.4 && (i < 2 || !reach || G.t - s.reachT > 1.4)) slStop(i); }
      else {
        if (u > SL_AUTO) { for (let i = 0; i < 2; i++) if (u > SL_AUTO + i * 0.45) slStop(i); if (u > SL_AUTO + 0.9 && !reach) slStop(2); }   // (no taps: they stop on their own)
        if (reach && G.t - s.reachT > 3) slStop(2);
      }
      let all = true;
      s.reels.forEach((rl, i) => {
        const p0 = rl.pos; rl.vNow = 0;
        if (rl.spin) { stepReel(rl, i); rl.vNow = (rl.pos - p0) / dt; }
      });
      function stepReel(rl, i) {
        if (G.t < rl.t0) { all = false; return; }
        if (rl.stop) {                                     // easing in to its place, a little past it and back (a thunk)
          const q = (G.t - rl.stop.t0) / rl.stop.dur;
          if (q < 1) rl.pos = rl.stop.from + (rl.stop.to - rl.stop.from) * (1 - Math.pow(1 - q, 3));
          else {
            if (!rl.stop.hit) { rl.stop.hit = true; SND.play('slStop'); buzz(15); }
            const r = (G.t - rl.stop.t0 - rl.stop.dur) / 0.16;
            rl.pos = rl.stop.to + 0.09 * Math.sin(Math.PI * Math.min(1, r)) * (1 - Math.min(1, r) * 0.5);
            if (r >= 1) { rl.pos = rl.stop.to; rl.spin = false; }
          }
          if (rl.spin) all = false;
        } else {
          const v = i === 2 && reach ? SL_REACH_V : rl.v;                // the reach: the last reel slows right down
          rl.pos += v * dt; all = false;
        }
      }
      // the sound of it: ticks as the symbols go by, a drum roll on a reach
      s.tick += dt * (s.reels.some((rl) => rl.spin) ? (reach ? SL_REACH_V : SL_SPEED) : 0);
      if (s.tick >= 1) { s.tick -= Math.floor(s.tick); SND.play('slTick'); }
      if (reach) { s.drum += dt; if (s.drum > 0.07) { s.drum = 0; SND.play('slDrum'); } }
      if (all) slResult();
    }
    if (s.st === 'after') {
      const hold = s.msg.kind === 'jackpot' ? 3.2 : s.msg.kind === 'three' ? 2.2 : 1.4;
      if (G.t - s.stT > hold) { if (++s.k >= SL_N) { s.st = 'done'; s.stT = G.t; } else { s.st = 'ready'; s.stT = G.t; s.msg = null; } }
    }
    for (const c of s.coins) { c.vy += 260 * dt; c.x += c.vx * dt; c.y += c.vy * dt; c.r += c.vr * dt; if (c.y > NH - 4 && c.vy > 0) { c.vy *= -0.35; c.vx *= 0.7; c.y = NH - 4; } }
    s.coins = s.coins.filter((c) => G.t - s.flash < 3.4);
    if (s.st === 'done' && G.t - s.stT > SL_END) endSlot();
  }
  // ---- drawing
  function drawSlot() {
    const s = G.sl; if (!s) return;
    world();
    let al = Math.min(1, (G.t - s.inT) / 0.35);
    if (s.st === 'done') al *= Math.max(0, Math.min(1, (SL_END - (G.t - s.stT)) / 0.35));
    const zx = NWf / 2, mx = slMX(), my = slMY();
    const win = s.st === 'after' && s.msg && (s.msg.kind === 'three' || s.msg.kind === 'jackpot');
    // the toilet water behind, darkened, a glow behind the machine
    ctx.globalAlpha = al * 0.8; ctx.fillStyle = '#04121a'; ctx.fillRect(0, 0, NWf, NH);
    const g = ctx.createRadialGradient(zx, my + 70, 20, zx, my + 70, 170); g.addColorStop(0, win ? 'rgba(255,214,110,0.4)' : 'rgba(80,180,220,0.32)'); g.addColorStop(1, 'rgba(80,180,220,0)');
    ctx.fillStyle = g; ctx.fillRect(0, 0, NWf, NH); ctx.globalAlpha = al;
    // the reels behind the windows: a white drum, the symbols going by (smeared when fast), a shadow at the top and bottom
    for (let i = 0; i < 3; i++) {
      const rl = s.reels[i], W = slWin(i), cx = mx + W.cx, cy = my + W.cy, strip = rl.strip, n = strip.length;
      ctx.save(); ctx.beginPath(); ctx.rect(mx + W.x0 - 1, my + W.y0 - 1, W.w2 * 2 + 2, W.h2 * 2 + 2); ctx.clip();
      const dg = ctx.createLinearGradient(0, my + W.y0, 0, my + W.y1); dg.addColorStop(0, '#b8aebc'); dg.addColorStop(0.45, '#ffffff'); dg.addColorStop(0.6, '#fbf8fc'); dg.addColorStop(1, '#a89eae');
      ctx.fillStyle = dg; ctx.fillRect(mx + W.x0 - 1, my + W.y0 - 1, W.w2 * 2 + 2, W.h2 * 2 + 2);
      const fast = Math.abs(rl.vNow) > 7;                       // (smeared when it goes by quickly)
      const base = Math.floor(rl.pos), fr = rl.pos - base, sz = SL_SYM;
      for (let j = -2; j <= 2; j++) {
        const sym = strip[(((base + j) % n) + n) % n], y = cy - (j - fr) * SL_GAP;     // (the strip moves down the window)
        if (fast) { for (let k = 0; k < 4; k++) spr('sl_s' + sym, cx - sz / 2, y - sz * 0.8 - k * 3.5, 0.3 * al, sz, sz * 1.6); }      // (stretched along the way it goes)
        else spr('sl_s' + sym, cx - sz / 2, y - sz / 2, 1, sz, sz);
        ctx.globalAlpha = al;
      }
      const sh = ctx.createLinearGradient(0, my + W.y0, 0, my + W.y1);
      sh.addColorStop(0, 'rgba(70,30,60,0.62)'); sh.addColorStop(0.2, 'rgba(70,30,60,0)'); sh.addColorStop(0.82, 'rgba(70,30,60,0)'); sh.addColorStop(1, 'rgba(70,30,60,0.4)');
      ctx.fillStyle = sh; ctx.fillRect(mx + W.x0 - 1, my + W.y0 - 1, W.w2 * 2 + 2, W.h2 * 2 + 2);
      ctx.restore();
    }
    // the machine itself
    spr('sl_machine', mx, my, 1, SW('sl_machine'), SH('sl_machine'));
    // a winning reel: a gold glow round its window
    for (let i = 0; i < 3; i++) {
      if (!(s.st === 'after' && s.msg && s.msg.kind !== 'none' && s.want[i] === s.msg.sym && (s.msg.kind !== 'two' || s.want.filter((v) => v === s.msg.sym).length >= 2))) continue;
      const W = slWin(i);
      ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.globalAlpha = al * (0.45 + 0.4 * Math.sin(G.t * 16));
      rrect(mx + W.x0 + 0.6, my + W.y0 + 0.6, W.w2 * 2 - 1.2, W.h2 * 2 - 1.2, SLF.winr); ctx.lineWidth = 1.6; ctx.strokeStyle = '#ffd54a'; ctx.stroke();
      ctx.restore(); ctx.globalAlpha = al;
    }
    // the bulbs round the marquee: the picture's are all lit; off ones dimmed, on ones glowing (chasing slowly, fast while
    // the reels turn, red on a reach, all flashing on a win)
    SLF.bulbs.forEach(([bx, by, br], i) => {
      const N = SLF.bulbs.length;
      const on = win ? Math.floor(G.t * 8) % 2 === 0 : s.reach ? Math.floor(G.t * 10) % 2 === i % 2 : s.st === 'spin' ? ((i - Math.floor(G.t * 22)) % N + N) % N < 4 : ((i - Math.floor(G.t * 6)) % 3 + 3) % 3 === 0;
      const x = mx + bx, y = my + by;
      if (!on) { ctx.globalAlpha = al * 0.6; ctx.beginPath(); ctx.arc(x, y, br * 1.15, 0, 6.2832); ctx.fillStyle = '#5a2a10'; ctx.fill(); ctx.globalAlpha = al; return; }
      ctx.save(); ctx.globalCompositeOperation = 'lighter';
      const gg = ctx.createRadialGradient(x, y, 0, x, y, br * 3.2); const c = s.reach ? '255,90,90' : '255,226,150';
      gg.addColorStop(0, `rgba(${c},0.85)`); gg.addColorStop(0.35, `rgba(${c},0.35)`); gg.addColorStop(1, `rgba(${c},0)`);
      ctx.globalAlpha = al; ctx.fillStyle = gg; ctx.beginPath(); ctx.arc(x, y, br * 3.2, 0, 6.2832); ctx.fill(); ctx.restore(); ctx.globalAlpha = al;
    });
    // the light at the foot: breathing; flashing on a win
    { const [gx, gy, rx, ry] = SLF.glow, k = win ? 0.55 + 0.45 * Math.sin(G.t * 18) : 0.22 + 0.12 * Math.sin(G.t * 2.4);
      ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.translate(mx + gx, my + gy); ctx.scale(1, ry / rx);
      const gg = ctx.createRadialGradient(0, 0, 0, 0, 0, rx * 1.1); gg.addColorStop(0, win ? 'rgba(255,230,140,0.9)' : 'rgba(110,200,255,0.9)'); gg.addColorStop(1, 'rgba(110,200,255,0)');
      ctx.globalAlpha = al * k; ctx.fillStyle = gg; ctx.beginPath(); ctx.arc(0, 0, rx * 1.1, 0, 6.2832); ctx.fill(); ctx.restore(); ctx.globalAlpha = al; }
    // the red buttons: glowing while their reel can be stopped, pressed in for a moment when tapped, dim when not live
    for (let i = 0; i < 3; i++) {
      const rl = s.reels[i], [bx, by, rx, ry] = SLF.btns[i], x = mx + bx, y = my + by;
      const live = s.st === 'spin' && rl.spin && !rl.stop && G.t >= rl.t0 + 0.4, pr = G.t - s.press[i] < 0.15;
      ctx.save(); ctx.translate(x, y); ctx.scale(1, ry / rx);
      if (live && !pr) {
        ctx.globalCompositeOperation = 'lighter';
        const gg = ctx.createRadialGradient(0, -rx * 0.2, 0, 0, 0, rx * 1.15); gg.addColorStop(0, 'rgba(255,150,140,0.75)'); gg.addColorStop(0.6, 'rgba(255,60,60,0.3)'); gg.addColorStop(1, 'rgba(255,60,60,0)');
        ctx.globalAlpha = al * (0.55 + 0.45 * Math.sin(G.t * 9 - i)); ctx.fillStyle = gg; ctx.beginPath(); ctx.arc(0, 0, rx * 1.15, 0, 6.2832); ctx.fill();
      } else if (pr || s.st === 'spin' || s.st === 'ready') {
        ctx.globalAlpha = al * (pr ? 0.45 : 0.3); ctx.fillStyle = '#2a0008'; ctx.beginPath(); ctx.arc(0, 0, rx * 0.98, 0, 6.2832); ctx.fill();
      }
      ctx.restore(); ctx.globalAlpha = al;
    }
    // the lever: pulled down towards you and back (the arm turning on its pivot: the stick foreshortened, the knob coming
    // nearer and bigger), then the knob and stick drawn over the drum
    { const u = G.t - s.leverT, th = 2.2 * (u < 0 ? 0 : u < 0.13 ? u / 0.13 : u < 0.22 ? 1 : Math.max(0, 1 - (u - 0.22) / 0.32));
      const e = th === 0 ? 0 : th, c = Math.cos(e), sn = Math.sin(e);
      const [px, py] = SLF.piv, st = M.sprites.sl_stick, kn = M.sprites.sl_knob;
      if (e > 0.02) { ctx.beginPath(); ctx.ellipse(mx + px, my + py, SLF.stick_w * 0.5, SLF.stick_w * 0.22, 0, 0, 6.2832); ctx.fillStyle = '#3a1a08'; ctx.fill(); }
      ctx.save(); ctx.translate(mx + px, my + py); ctx.scale(1, c); spr('sl_stick', -SLF.stick_piv[0], -SLF.stick_piv[1], 1, st.w, st.h); ctx.restore(); ctx.globalAlpha = al;
      const kx = mx + SLF.knob[0], ky = my + py + (SLF.knob[1] - py) * c, ks = 1 + 0.22 * sn;
      spr('sl_knob', kx - SLF.knob_c[0] * ks, ky - SLF.knob_c[1] * ks, 1, kn.w * ks, kn.h * ks); ctx.globalAlpha = al; }
    // the marquee bar: what is going on
    { const m = s.msg, [qx0, qy0, qw] = SLF.marquee, qx = mx + qx0, qy = my + qy0 + 0.3, blink = 0.78 + 0.22 * Math.sin(G.t * 6), fs = Math.min(8, qw / 7);
      if (s.reach) label(TR('리치!', 'REACH!'), qx, qy, fs * 1.15, 'center', al * (Math.floor(G.t * 8) % 2 ? 1 : 0.6), '#ffe3e3');
      else if (m && s.st === 'after') {
        if (m.kind === 'jackpot') label('JACKPOT', qx, qy, fs * 1.1, 'center', al * (Math.floor(G.t * 10) % 2 ? 1 : 0.55), '#ffe68a');
        else if (m.kind === 'three') label(TR('당첨!', 'WIN!'), qx, qy, fs * 1.1, 'center', al * (Math.floor(G.t * 10) % 2 ? 1 : 0.55), '#ffe68a');
        else if (m.kind === 'two') label(m.k > 1 ? TR(`${m.k}연속! +${PT(m.pts)}`, `${m.k} in a row! +${PT(m.pts)}`) : m.near ? `${TR('아깝다!', 'So close!')} +${PT(m.pts)}` : `${TR('두 개 같아요', 'Two alike')} +${PT(m.pts)}`, qx, qy, fs * 0.85, 'center', al, '#ffffff');
        else label(TR('꽝', 'No luck'), qx, qy, fs, 'center', al, '#ffd8dc');
      }
      else if (s.st === 'ready') label(TR('탭해서 레버 당기기', 'Tap to pull'), qx, qy, fs * 0.85, 'center', al * blink, '#ffffff');
      else label(TR('변기 잭팟', 'Toilet Jackpot'), qx, qy, fs, 'center', al, '#ffe68a'); }
    ctx.globalAlpha = al;
    // a win: the coins, the words (over the reels)
    for (const c of s.coins) { ctx.save(); ctx.translate(c.x, c.y); ctx.scale(Math.cos(c.r), 1); spr('sl_coin', -4, -4, 1, 8, 8); ctx.restore(); ctx.globalAlpha = al; }
    const ry = my + slWin(0).cy;
    if (s.msg && s.st !== 'done') {
      const v = G.t - s.msg.t, m = s.msg;
      if (m.kind === 'jackpot') {
        if (v < 0.5) { ctx.globalAlpha = al * (1 - v / 0.5) * 0.5; ctx.fillStyle = '#fff6c8'; ctx.fillRect(0, 0, NWf, NH); ctx.globalAlpha = al; }
        const sc = 1 + 0.3 * Math.max(0, 1 - v / 0.3) + 0.05 * Math.sin(G.t * 10);
        label('JACKPOT!!', zx, ry - 4, 26 * sc, 'center', al, ['#ffe14a', '#ff7a5a', '#7ae0ff', '#c88aff'][Math.floor(G.t * 8) % 4]);
        label(m.k > 1 ? TR(`${m.k}연속! +${PT(m.pts)}`, `${m.k} in a row! +${PT(m.pts)}`) : `+${PT(m.pts)}`, zx, ry + 16, 12, 'center', al, '#ffe68a');
      } else if (m.kind === 'three') {
        label(TR(`${SL_NAME[m.sym]} 3개! +${PT(m.pts)}`, `Three ${SL_NAME[m.sym]}! +${PT(m.pts)}`), zx, ry, 13 * (1 + 0.2 * Math.max(0, 1 - v / 0.25)), 'center', al, '#ffe68a');
        if (m.k > 1) label(TR(`${m.k}연속!`, `${m.k} in a row!`), zx, ry + 14, 9, 'center', al, '#fff3c8');
      }
    }
    // the goes: three coins at the top left
    for (let i = 0; i < SL_N; i++) { ctx.globalAlpha = al * (i < s.res.length ? 0.3 : 1); spr('sl_coin', 16 + i * 10, 40, 1, 8, 8); }
    ctx.globalAlpha = al;
    if (s.st === 'intro') {
      const v = G.t - s.stT, a = Math.min(1, v / 0.3) * Math.max(0, Math.min(1, (SL_INTRO - v) / 0.3));
      ctx.globalAlpha = al * a * 0.85; rrect(zx - 118, 72, 236, 56, 8); ctx.fillStyle = '#10141e'; ctx.fill(); ctx.globalAlpha = al;
      label(TR('변기 잭팟! 3번 돌려요', 'Toilet Jackpot! 3 spins'), zx, 86, 15, 'center', a, '#ffe0a8');
      label(TR('탭하면 레버를 당겨 돌아가고, 다시 탭해서 하나씩 멈춰요', 'Tap to pull the lever, tap again to stop each reel'), zx, 104, 7.5, 'center', a, '#ffffff');
      label(TR('같은 그림 3개면 당첨, 황금똥 3개면 잭팟 5,000점!', 'Three alike wins - three golden poops: the 5,000 pt jackpot!'), zx, 115, 7.5, 'center', a, '#ffe68a');
    }
    if (s.st === 'done') {
      const v = G.t - s.stT, a = Math.min(1, v / 0.25) * Math.max(0, Math.min(1, (SL_END - v) / 0.35));
      ctx.globalAlpha = a * 0.85; rrect(zx - 110, 74, 220, 56, 8); ctx.fillStyle = '#10141e'; ctx.fill(); ctx.globalAlpha = 1;
      const hit = s.res.filter((r) => r === 'three' || r === 'jackpot').length;
      label(s.res.includes('jackpot') ? TR('잭팟 터졌다!', 'JACKPOT!') : hit ? TR(`당첨 ${hit}번!`, `${hit} win${hit === 1 ? '' : 's'}!`) : TR('다음에 다시!', 'Better luck next time!'), zx, 90, 14, 'center', a, s.gain ? '#ffe68a' : '#ffd0dc');
      label(`${(s.bestRun || 0) > 1 ? TR(`최고 연속 ${s.bestRun} · `, `Best run ${s.bestRun} · `) : ''}+${PT(s.gain)}`, zx, 112, 9, 'center', a, '#ffe68a');
    }
    ctx.globalAlpha = 1;
  }

  // ---------------------------------------------------------------- the shell game (in the combined sewer) (v52)
  // '야바위': the user's mouse deals at a velvet-skirted table under a string of lights: three domed manhole lids
  // (yabawi.py), the golden poop under one. It lifts that lid to show you, then shuffles: two lids swapping (one passing
  // in front, the other behind) and, from the third round, all three going round at once; faster every round. Tap the
  // lid it is under (or the arrows and space, or 1-3). Right: the pot (500, doubled each round) and a choice: one more
  // round for double, or take it. Wrong: the pot is gone and it ends. Five rounds at most (8,000; v57: 14,400 with the combo). No cheating: it is
  // where the moves you saw put it.
  const YB_N = 5, YB_INTRO = 2.8, YB_LIFT = 34, YB_BASE = 500, YB_WAIT = 9, YB_ASKWAIT = 8, YB_END = 2.8, YB_REVEAL = 1.7;
  const YB_MOVES = [[5, 0.36], [7, 0.27], [9, 0.2], [11, 0.15], [13, 0.115]];     // each round: how many moves, how long each (s)
  const YB_SP = 64, YB_FOOT = 124, YB_TOP = 102;            // the lids' spacing; where their feet stand; the table's top edge
  const YB_BTN = { y: 163, w: 118, h: 25, dx: 64 };          // the double-or-take buttons (on the skirt)
  const ybX = (slot) => NWf / 2 + (slot - 1) * YB_SP;
  const ybPot = (k) => comboPts(YB_BASE * Math.pow(2, k), k + 1);     // the pot after the round k (0 ..) is won (v57: and +20% for each won before it in a row)
  function startYB() {
    holdBoost();
    G.obs = G.obs.filter((o) => o.x + o.w < G.x - 12);
    G.items = G.items.filter((i) => i.x < G.x - 12 || i.taken);
    G.yb = { st: 'intro', stT: G.t, inT: G.t, k: 0, res: [], gain: 0, pot: 0, slot: [0, 1, 2], gold: Math.floor(Math.random() * 3),
      lift: [0, 0, 0], liftTo: [0, 0, 0], mv: null, moved: 0, cur: 1, ask: 0, pick: -1, ok: null, coins: [], say: null, lean: 0, flash: -9, pressT: -9 };
    G.slideHeld = false; held.clear(); pressed.jump = false;
  }
  function endYB() {
    bankGame(G.yb); G.yb = null; G.games = (G.games || 0) + 1; resumeBoost();
    G.genX = Math.max(G.genX, G.x + NW * 0.8);
    G.banner = G.t;
  }
  const ybSay = (p, ko, en) => { p.say = { s: TR(ko, en), t: G.t }; };
  function ybRound(p) {                                      // a round: show where it is, then shuffle
    p.st = 'show'; p.stT = G.t; p.pick = -1; p.ok = null; p.moved = 0; p.mv = null; p.cur = 1;
    p.liftTo = [0, 1, 2].map((i) => (i === p.gold ? YB_LIFT : 0));
    ybSay(p, p.k ? '이번엔 더 빨라~' : '잘 봐~', p.k ? 'Faster now~' : 'Watch closely~');
    SND.play('ybLift');
  }
  // the next move of the shuffle (decided as it starts, from where things are): two lids swapping (more often with the
  // golden one), or from the third round now and then all three going round
  function ybNextMove(p) {
    const [n, dur] = YB_MOVES[p.k];
    if (p.moved >= n) { p.mv = null; p.st = 'pick'; p.stT = G.t; ybSay(p, '어디게?', 'Where is it?'); return; }
    const at = [0, 1, 2].map((s) => p.slot.indexOf(s)), gs = p.slot[p.gold];
    let paths, d = dur;
    if (p.k >= 2 && Math.random() < 0.3) {
      const dir = Math.random() < 0.5 ? 1 : -1;               // each one slot on; the end one goes across, behind
      paths = [0, 1, 2].map((s) => { const to = (s + dir + 3) % 3, far = Math.abs(to - s) === 2; return { lid: at[s], from: s, to, dy: far ? -11 : 5, ds: far ? -0.1 : 0.05 }; });
      d *= 1.2;
    } else {
      let pair = [[0, 1], [1, 2], [0, 2]][Math.floor(Math.random() * 3)];
      if (!pair.includes(gs) && Math.random() < 0.65) pair = [[0, 1], [1, 2], [0, 2]].filter((q) => q.includes(gs))[Math.floor(Math.random() * 2)];
      const far = Math.abs(pair[0] - pair[1]) === 2, front = Math.random() < 0.5, A = 7 + (far ? 3 : 0), B = -6 - (far ? 3 : 0);
      paths = [{ lid: at[pair[0]], from: pair[0], to: pair[1], dy: front ? A : B, ds: front ? 0.08 : -0.08 },
        { lid: at[pair[1]], from: pair[1], to: pair[0], dy: front ? B : A, ds: front ? -0.08 : 0.08 }];
      if (far) d *= 1.2;
    }
    p.mv = { t0: G.t, dur: d, paths }; p.moved++;
    p.lean = paths[0].to > paths[0].from ? 1 : -1;
    SND.play('ybSlide');
  }
  // where lid i is drawn: its foot's middle (lifted), its size, where its shadow lies (on the felt)
  function ybLidPos(p, i) {
    let x = ybX(p.slot[i]), y = YB_FOOT, s = 1;
    const m = p.mv, pa = m && m.paths.find((q) => q.lid === i);
    if (pa) { const u = Math.min(1, (G.t - m.t0) / m.dur), e = u * u * (3 - 2 * u), b = Math.sin(Math.PI * u);
      x = ybX(pa.from) + (ybX(pa.to) - ybX(pa.from)) * e; y += pa.dy * b; s += pa.ds * b; }
    return [x, y - p.lift[i], s, y];
  }
  function ybPick(slot) {
    const p = G.yb; if (!p || p.st !== 'pick' || slot < 0 || slot > 2) return;
    p.pick = slot; p.cur = slot; p.st = 'reveal'; p.stT = G.t; p.pressT = G.t;
    p.liftTo[p.slot.indexOf(slot)] = YB_LIFT;
    SND.play('ybLift'); buzz(20);
  }
  function ybAsk(go) {
    const p = G.yb; if (!p || p.st !== 'ask') return;
    p.ask = go ? 0 : 1; p.pressT = G.t;
    if (go) { p.k++; ybRound(p); SND.play('ui'); }
    else { p.gain = p.pot; p.st = 'done'; p.stT = G.t; SND.play('slSmall'); ybCoins(p, ybX(p.slot[p.gold]), YB_FOOT - 14, 14); }
  }
  function ybCoins(p, x, y, n) {
    for (let i = 0; i < n; i++) p.coins.push({ x, y, vx: (Math.random() - 0.5) * 140, vy: -90 - Math.random() * 110, r: Math.random() * 6.28, t: G.t });
  }
  function ybDown(x, y) {
    const p = G.yb; if (!p) return;
    if (p.st === 'pick') {                                    // a lid: anywhere in its column over the table
      for (let s = 0; s < 3; s++) if (Math.abs(x - ybX(s)) < YB_SP / 2 && y > YB_FOOT - 60 && y < YB_FOOT + 22) { ybPick(s); return; }
    } else if (p.st === 'ask') {
      for (const [go, bx] of [[true, NWf / 2 - YB_BTN.dx], [false, NWf / 2 + YB_BTN.dx]]) if (Math.abs(x - bx) < YB_BTN.w / 2 + 3 && Math.abs(y - YB_BTN.y) < YB_BTN.h / 2 + 4) { ybAsk(go); return; }
    }
  }
  function ybKey(code) {
    const p = G.yb; if (!p) return false;
    const L = ['ArrowLeft', 'KeyA'].includes(code), R = ['ArrowRight', 'KeyD'].includes(code), OK = ['Space', 'Enter', 'KeyJ', 'KeyF'].includes(code);
    const dg = /^(Digit|Numpad)([1-3])$/.exec(code);
    if (p.st === 'pick') { if (dg) ybPick(+dg[2] - 1); else if (L) p.cur = Math.max(0, p.cur - 1); else if (R) p.cur = Math.min(2, p.cur + 1); else if (OK) ybPick(p.cur); else return false; return true; }
    if (p.st === 'ask') { if (dg && +dg[2] <= 2) ybAsk(dg[2] === '1'); else if (L) p.ask = 0; else if (R) p.ask = 1; else if (OK) ybAsk(p.ask === 0); else return false; return true; }
    return L || R || OK || !!dg;
  }
  function stepYB(dt) {
    const p = G.yb; if (!p) return;
    const u = G.t - p.stT;
    for (let i = 0; i < 3; i++) p.lift[i] += (p.liftTo[i] - p.lift[i]) * Math.min(1, dt * 16);
    for (const c of p.coins) { c.vy += 420 * dt; c.x += c.vx * dt; c.y += c.vy * dt; c.r += dt * 9; }
    p.coins = p.coins.filter((c) => c.y < NH + 10);
    if (p.st === 'intro') { if (u >= YB_INTRO) ybRound(p); return; }
    if (p.st === 'show') {
      if (u >= 0.95 && p.liftTo[p.gold] > 0) { p.liftTo[p.gold] = 0; SND.play('ybDown'); }
      if (u >= 1.35) { p.st = 'shuffle'; p.stT = G.t; ybSay(p, '섞는다~!', 'Shuffling~!'); ybNextMove(p); }
      return;
    }
    if (p.st === 'shuffle') {
      if (p.mv && G.t >= p.mv.t0 + p.mv.dur) { for (const pa of p.mv.paths) p.slot[pa.lid] = pa.to; p.mv = null; }
      if (!p.mv) ybNextMove(p);
      return;
    }
    if (p.st === 'pick') {
      if (AUTO && !window.__noAuto && u > 0.45) { const g = p.slot[p.gold]; ybPick(window.__ybMiss ? (g + 1) % 3 : g); return; }
      if (u > YB_WAIT) ybPick(Math.floor(Math.random() * 3));         // (left alone: a guess)
      return;
    }
    if (p.st === 'reveal') {
      if (p.ok === null && u >= 0.38) {
        p.ok = p.slot[p.gold] === p.pick; p.flash = G.t;
        if (p.ok) { p.pot = ybPot(p.k); p.res.push('win'); SND.play('ybWin'); buzz([30, 30, 60]); ybCoins(p, ybX(p.pick), YB_FOOT - 14, 10 + p.k * 4); ybSay(p, '헉! 맞혔네...', 'What?! You got it...'); }
        else { p.res.push('lose'); SND.play('ybLose'); buzz(60); ybSay(p, '히히, 꽝~', 'Hee hee, nope~'); }
      }
      if (p.ok === false && u >= 0.8 && p.liftTo[p.gold] === 0) p.liftTo[p.gold] = YB_LIFT;      // where it was
      if (u >= YB_REVEAL) {
        if (p.ok && p.k < YB_N - 1) { p.st = 'ask'; p.stT = G.t; p.ask = 0; ybSay(p, '한 판 더?', 'Double or nothing?'); }
        else { p.gain = p.ok ? p.pot : 0; if (!p.ok) p.pot = 0; p.st = 'done'; p.stT = G.t; if (p.ok) { SND.play('slJackpot'); ybCoins(p, NWf / 2, YB_FOOT - 30, 40); } }
      }
      return;
    }
    if (p.st === 'ask') {
      if (AUTO && !window.__noAuto && u > 0.6) { ybAsk(p.k + 1 < (window.__ybStopAt || 99)); return; }
      if (u > YB_ASKWAIT) ybAsk(false);                         // (left alone: it takes the pot)
      return;
    }
    if (p.st === 'done' && u >= YB_END) endYB();
  }
  function drawYB() {
    const p = G.yb; if (!p) return;
    world();
    let al = Math.min(1, (G.t - p.inT) / 0.35);
    if (p.st === 'done') al *= Math.max(0, Math.min(1, (YB_END - (G.t - p.stT)) / 0.35));
    const zx = NWf / 2, A = (a) => { ctx.globalAlpha = al * a; };
    // the sewer behind, darkened; a warm light over the table
    A(0.82); ctx.fillStyle = '#0a0508'; ctx.fillRect(0, 0, NWf, NH);
    { const g = ctx.createRadialGradient(zx, 110, 8, zx, 110, 200); g.addColorStop(0, 'rgba(255,196,120,0.34)'); g.addColorStop(0.45, 'rgba(255,150,90,0.12)'); g.addColorStop(1, 'rgba(255,150,90,0)');
      A(1); ctx.fillStyle = g; ctx.fillRect(0, 0, NWf, NH); }
    // a string of lights across, sagging in two loops; the bulbs lit in turn (all of them flashing on a win)
    { const yAt = (x) => 41 + 9 * Math.abs(Math.sin(Math.PI * x / (NWf / 2)));
      A(0.9); ctx.beginPath(); for (let x = -4; x <= NWf + 4; x += 4) ctx.lineTo(x, yAt(x)); ctx.lineWidth = 0.9; ctx.strokeStyle = '#2a1a14'; ctx.stroke();
      const cols = ['255,214,106', '255,122,138', '122,216,255', '168,255,138'], win = p.ok && (p.st === 'reveal' || p.st === 'ask');
      for (let i = 0, x = 9; x < NWf; x += 21, i++) {
        const y = yAt(x) + 3.2, on = win ? Math.floor(G.t * 9) % 2 === 0 : ((i - Math.floor(G.t * 4)) % 3 + 3) % 3 !== 0, c = cols[i % 4];
        if (on) { const gg = ctx.createRadialGradient(x, y, 0, x, y, 9); gg.addColorStop(0, `rgba(${c},0.55)`); gg.addColorStop(1, `rgba(${c},0)`); A(1); ctx.fillStyle = gg; ctx.beginPath(); ctx.arc(x, y, 9, 0, 6.2832); ctx.fill(); }
        A(1); ctx.fillStyle = '#3a2a24'; ctx.fillRect(x - 0.9, y - 3.6, 1.8, 1.6);
        ctx.beginPath(); ctx.ellipse(x, y, 1.9, 2.5, 0, 0, 6.2832); ctx.fillStyle = on ? `rgb(${c})` : `rgba(${c},0.35)`; ctx.fill();
        if (on) { ctx.beginPath(); ctx.arc(x - 0.6, y - 0.8, 0.6, 0, 6.2832); ctx.fillStyle = '#ffffff'; ctx.fill(); }
      }
    }
    // the dealer (the user's mouse) behind the table: leaning with the moves while shuffling; shaking its head when you
    // win, hopping when you lose
    { const fr = p.st === 'shuffle' && p.mv ? (p.lean > 0 ? 'pk_dR1' : 'pk_dL1') : 'pk_k0', s = M.sprites[fr], sc = 1.2;
      let dx = 0, dy = 0;
      if (p.st === 'shuffle') dy = -Math.abs(Math.sin(G.t * 22)) * 1.4;
      if (p.ok === true && (p.st === 'reveal' || p.st === 'ask')) dx = Math.sin(G.t * 30) * 1.6 * Math.max(0, 1 - (G.t - p.flash) / 1.2);
      if (p.ok === false && p.st !== 'intro') dy = -Math.abs(Math.sin(G.t * 11)) * 4;
      A(1); spr(fr, zx - s.c[0] * sc + dx, YB_TOP + 12 - s.bottom * sc + dy, 1, s.w * sc, s.h * sc); A(1); }
    // the table, its felt lit in the middle
    spr('yb_table', zx - 145, YB_TOP, 1, 290, 78); A(1);
    { const g = ctx.createRadialGradient(zx, YB_FOOT - 2, 4, zx, YB_FOOT - 2, 120); g.addColorStop(0, 'rgba(255,230,170,0.16)'); g.addColorStop(1, 'rgba(255,230,170,0)'); ctx.fillStyle = g; ctx.fillRect(zx - 145, YB_TOP + 4, 290, 26); }
    // the lids: their shadows on the felt, the golden poop under its lid when that is up, the lids (the far ones first)
    const pos = [0, 1, 2].map((i) => ybLidPos(p, i));
    for (let i = 0; i < 3; i++) { const [x, , s, fy] = pos[i], k = Math.max(0.35, 1 - p.lift[i] / 60); A(0.42 * k); ctx.beginPath(); ctx.ellipse(x + 1.5, fy + 1.2, 24 * s * k, 6.2 * s * k, 0, 0, 6.2832); ctx.fillStyle = '#000000'; ctx.fill(); }
    if (p.lift[p.gold] > 1.5) {
      const [x, , , fy] = pos[p.gold], sh = p.ok === true ? 1 : 0;
      if (sh || p.st === 'show') { const g = ctx.createRadialGradient(x, fy - 10, 2, x, fy - 10, 30); g.addColorStop(0, 'rgba(255,220,110,0.65)'); g.addColorStop(1, 'rgba(255,220,110,0)'); A(1); ctx.fillStyle = g; ctx.beginPath(); ctx.arc(x, fy - 10, 30, 0, 6.2832); ctx.fill(); }
      A(1); spr('sl_s0', x - 14, fy - 25, 1, 28, 28); A(1);
    }
    const order = [0, 1, 2].sort((a, b) => (pos[a][3] - pos[b][3]) || (pos[a][2] - pos[b][2]));
    // (a lid is lifted by swinging it open on its right edge, like a hand tipping it: it does not cover the dealer)
    for (const i of order) { const [x, , s, fy] = pos[i], L = M.sprites.yb_lid, f = Math.min(1, p.lift[i] / YB_LIFT), hx = x + 23 * s, hy = fy - f * 6;
      ctx.save(); ctx.translate(hx, hy); ctx.rotate(f * 1.15); A(1); spr('yb_lid', -23 * s - L.foot[0] * s, -L.foot[1] * s, 1, L.w * s, L.h * s); ctx.restore(); }
    A(1);
    // picking: each lid's foot ringed, the one the keys are on brighter; the finger's hint
    if (p.st === 'pick') {
      for (let s = 0; s < 3; s++) { const x = ybX(s), on = s === p.cur; A((on ? 0.75 : 0.4) + 0.25 * Math.sin(G.t * 7));
        ctx.beginPath(); ctx.ellipse(x, YB_FOOT + 1, 27, 8, 0, 0, 6.2832); ctx.lineWidth = on ? 1.6 : 1.1; ctx.strokeStyle = '#ffe68a'; ctx.stroke(); }
      A(1); label(TR('황금똥이 든 뚜껑을 탭!', 'Tap the lid with the golden poop!'), zx, 152, 9.5, 'center', al * (0.8 + 0.2 * Math.sin(G.t * 6)), '#ffffff');
    }
    // what was picked came to: the word over the skirt, sparkles round the poop
    if (p.st === 'reveal' && p.ok !== null) {
      const v = G.t - p.flash, sc = 1 + 0.35 * Math.max(0, 1 - v / 0.25);
      if (p.ok) {
        if (v < 0.4) { A((1 - v / 0.4) * 0.35); ctx.fillStyle = '#fff4c0'; ctx.fillRect(0, 0, NWf, NH); }
        const [x, , , fy] = pos[p.gold];
        for (let k = 0; k < 6; k++) { const a = k * 1.047 + G.t * 2, r = 20 + 4 * Math.sin(G.t * 9 + k), sx = x + Math.cos(a) * r, sy = fy - 12 + Math.sin(a) * r * 0.6, z = 1.6 + 0.9 * Math.sin(G.t * 12 + k * 2);
          A(1); ctx.beginPath(); ctx.moveTo(sx, sy - z * 2); ctx.lineTo(sx + z * 0.5, sy - z * 0.5); ctx.lineTo(sx + z * 2, sy); ctx.lineTo(sx + z * 0.5, sy + z * 0.5); ctx.lineTo(sx, sy + z * 2); ctx.lineTo(sx - z * 0.5, sy + z * 0.5); ctx.lineTo(sx - z * 2, sy); ctx.lineTo(sx - z * 0.5, sy - z * 0.5); ctx.closePath(); ctx.fillStyle = '#fff6c0'; ctx.fill(); }
        label(p.k ? TR(`${p.k + 1}연속 맞혔다!`, `${p.k + 1} in a row!`) : TR('맞혔다!', 'Got it!'), zx, 150, 17 * sc, 'center', al, '#ffe14a');
        label(TR(`판돈 ${PT(p.pot)}`, `Pot ${PT(p.pot)}`), zx, 167, 9, 'center', al, '#ffffff');
      } else {
        label(TR('꽝!', 'Nope!'), zx, 150, 17 * sc, 'center', al, '#ff9aa8');
        label(p.k ? TR(`판돈 ${PT(p.pot || ybPot(p.k - 1))} 다 날렸다...`, `The pot (${PT(p.pot || ybPot(p.k - 1))}) is gone...`) : TR('여기 있었지롱~', 'It was here~'), zx, 167, 9, 'center', al, '#ffffff');
      }
    }
    // double or take: two buttons on the skirt, the pot over them
    if (p.st === 'ask') {
      label(TR(`판돈 ${PT(p.pot)}`, `Pot ${PT(p.pot)}`), zx, 144, 11, 'center', al, '#ffe14a');
      const pr = G.t - p.pressT < 0.15;
      [[true, zx - YB_BTN.dx, TR('한 판 더! ×2', 'Again! x2'), TR(`성공하면 ${PT(ybPot(p.k + 1))}`, `win ${PT(ybPot(p.k + 1))}`), ['#fff2a8', '#ffc83a', '#c07a10']],
        [false, zx + YB_BTN.dx, TR('그만! 챙기기', 'Take it'), `+${PT(p.pot)}`, ['#cfeaff', '#5aa8f0', '#1f5aa8']]].forEach(([go, bx, t1, t2, c], j) => {
        const sel = p.ask === j, y = YB_BTN.y + (pr && sel ? 1 : 0), w = YB_BTN.w, h = YB_BTN.h;
        A(1); rrect(bx - w / 2 - 1.4, y - h / 2 - 1.4, w + 2.8, h + 2.8, 8); ctx.fillStyle = '#1a0a14'; ctx.fill();
        const g = ctx.createLinearGradient(0, y - h / 2, 0, y + h / 2); g.addColorStop(0, c[0]); g.addColorStop(0.5, c[1]); g.addColorStop(1, c[2]);
        rrect(bx - w / 2, y - h / 2, w, h, 7); ctx.fillStyle = g; ctx.fill();
        A(0.45); rrect(bx - w / 2 + 3, y - h / 2 + 1.6, w - 6, h * 0.3, 4); ctx.fillStyle = '#ffffff'; ctx.fill();
        if (sel) { A(0.5 + 0.4 * Math.sin(G.t * 7)); rrect(bx - w / 2 - 3, y - h / 2 - 3, w + 6, h + 6, 9); ctx.lineWidth = 1.4; ctx.strokeStyle = '#ffffff'; ctx.stroke(); }
        A(1); label(t1, bx, y - 3.6, 9.5, 'center', al, '#ffffff');
        ctx.font = '800 6.4px system-ui, -apple-system, "Noto Sans KR", sans-serif'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
        ctx.fillStyle = go ? '#6a3200' : '#ffffff'; ctx.fillText(t2, bx, y + 6.8);         // (plain: a dark outline would blot it)
      });
    }
    A(1);
    // the coins, the dealer's words (a bubble at its head)
    for (const c of p.coins) { ctx.save(); ctx.translate(c.x, c.y); ctx.scale(Math.cos(c.r), 1); spr('sl_coin', -4.5, -4.5, 1, 9, 9); ctx.restore(); A(1); }
    if (p.say && p.st !== 'intro' && p.st !== 'done') {
      const v = G.t - p.say.t, a = Math.min(1, v / 0.12), bx = zx + 30, by = 52;
      ctx.font = '900 7.5px system-ui, -apple-system, "Noto Sans KR", sans-serif';
      const w = Math.max(40, ctx.measureText(p.say.s).width + 12), sc = 0.85 + 0.15 * Math.min(1, v / 0.12);
      ctx.save(); ctx.translate(bx, by); ctx.scale(sc, sc); A(a);
      rrect(-1.2, -9.2, w + 2.4, 18.4, 8); ctx.fillStyle = '#1a0a14'; ctx.fill();
      ctx.beginPath(); ctx.moveTo(4, 6); ctx.lineTo(-5, 15); ctx.lineTo(13, 6.5); ctx.closePath(); ctx.fill();
      rrect(0, -8, w, 16, 7); ctx.fillStyle = '#fffaf2'; ctx.fill();
      ctx.beginPath(); ctx.moveTo(5.2, 6); ctx.lineTo(-2.6, 12.8); ctx.lineTo(11.6, 6); ctx.closePath(); ctx.fill();
      ctx.fillStyle = '#3a1020'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText(p.say.s, w / 2, 0.4);   // (dark on the white: no outline)
      ctx.restore(); A(1);
    }
    // the rounds: five little poops at the top left (gold: won; the one now pulsing)
    for (let i = 0; i < YB_N; i++) { const won = p.res[i] === 'win', now = i === p.k && p.st !== 'done' && p.st !== 'intro';
      A(won ? 1 : now ? 0.6 + 0.4 * Math.sin(G.t * 6) : 0.28); spr('sl_s0', 14 + i * 8.5, 27.5, 1, 8, 8); }
    A(1);
    if (p.st === 'intro') {
      const v = G.t - p.stT, a = Math.min(1, v / 0.3) * Math.max(0, Math.min(1, (YB_INTRO - v) / 0.3));
      const bw = Math.min(268, NWf - 16), t0 = TR('야바위! 황금똥을 찾아라', 'Shell game! Find the golden poop');
      A(a * 0.86); rrect(zx - bw / 2, 66, bw, 62, 8); ctx.fillStyle = '#10141e'; ctx.fill(); A(1);
      ctx.font = '900 15px system-ui, -apple-system, "Noto Sans KR", sans-serif';
      label(t0, zx, 81, Math.min(15, 15 * (bw - 14) / ctx.measureText(t0).width), 'center', al * a, '#ffe0a8');
      label(TR('쥐가 뚜껑을 섞어요. 황금똥이 든 뚜껑을 탭!', 'The mouse shuffles the lids - tap the one hiding the golden poop'), zx, 100, 7.5, 'center', al * a, '#ffffff');
      label(TR(`맞히면 판돈 2배+연속 보너스, 틀리면 다 잃어요 (최대 ${ybPot(YB_N - 1).toLocaleString('en-US')}점)`, `Right: double the pot and a bonus. Wrong: lose it all (up to ${ybPot(YB_N - 1).toLocaleString('en-US')})`), zx, 113, 7.5, 'center', al * a, '#ffe68a');
    }
    if (p.st === 'done') {
      const v = G.t - p.stT, a = Math.min(1, v / 0.25) * Math.max(0, Math.min(1, (YB_END - v) / 0.35));
      const sweep = p.res.length === YB_N && p.res.every((r) => r === 'win');
      A(a * 0.86); rrect(zx - 112, 66, 224, 56, 8); ctx.fillStyle = '#10141e'; ctx.fill(); A(1);
      label(sweep ? TR('싹쓸이!', 'Clean sweep!') : p.gain ? TR('챙겼다!', 'Banked it!') : TR('다 털렸다...', 'Lost it all...'), zx, 82, 15, 'center', a, p.gain ? '#ffe68a' : '#ffd0dc');
      label(`+${PT(p.gain)}`, zx, 104, 10, 'center', a, '#ffe68a');
    }
    ctx.globalAlpha = 1;
  }

  // ---------------------------------------------------------------- the poop tower (in the primary clarifier) (v53, v54)
  // '똥 탑 쌓기': a crane swings a poop brick to and fro over the clarifier's concrete pier; tap (anywhere, or space) to
  // let it go. It drops straight down onto the top of the tower: square on the one below ('퍼펙트!': it snaps square,
  // and perfects in a row pay more), a little off (it stays where it lands, and the tower leans that way), its middle
  // past the edge (it lands, tips over the edge and slides off into the tank), or past it altogether. Three bricks lost
  // and it is over; the tower's weight off the pier's middle past its edge: it topples, the end too. 30 seconds; the
  // swing gets wider and faster as it grows. (v54) Smaller bricks, and the view draws back as the tower grows (down to
  // half size, then it climbs with it): you see it tall. 100 a brick, a perfect +50, +100, +150 in a row.
  // (v55) No time: it goes on as high as you can build it, the crane swinging faster and wider the higher it is. One
  // brick lost (off the edge or past it) and it is over; so it is when the tower falls: from any brick up, their weight
  // past the edge of the one under them (or the pier) and over they go. Left hanging 6 s, the brick drops by itself
  // (a ring round it counts down the last 2)
  // (pictures: minigames3.py, tw.webp). World units: x across (the screen's middle is the pier's), h up from the
  // pier's top; the screen: k (the view's size), cam (how far up it has climbed)
  const TW_INTRO = 2.6, TW_END = 2.8, TW_BW = 30, TW_BH = 10, TW_PERF = 1.6, TW_PIER = 21, TW_AUTO = 6;
  const TW_JIB = 47, TW_HANG = 70, TW_FLOOR = 170, TW_ROOM = 84, TW_G = 700, TW_KMIN = 0.5;   // the jib; the hanging brick's top (screen); the pier's top (screen); the room above it
  function startTW() {
    holdBoost();
    G.obs = G.obs.filter((o) => o.x + o.w < G.x - 12);
    G.items = G.items.filter((i) => i.x < G.x - 12 || i.taken);
    G.tw = { st: 'intro', stT: G.t, inT: G.t, t0: 0, gain: 0, blocks: [], cur: null, fall: [], streak: 0, best: 0, misses: 0, perf: 0, k: 1, kS: 1, cam: 0, camS: 0,
      ph: Math.random() * 6.28, pops: [], topple: null, why: '', pressT: -9 };      // (ph: the swing's phase, run on by its speed)
    G.slideHeld = false; held.clear(); pressed.jump = false;
  }
  function endTW() {
    bankGame(G.tw); G.tw = null; G.games = (G.games || 0) + 1; resumeBoost();
    G.genX = Math.max(G.genX, G.x + NW * 0.8);
    G.banner = G.t;
  }
  const twTopX = (p) => (p.blocks.length ? p.blocks[p.blocks.length - 1].x : NWf / 2);
  const twAmp = (p) => Math.min(NWf / 2 - 24, 40 + 2 * p.blocks.length);    // (v55) the swing, as wide as it looks (screen), wider and
  const twFreq = (p) => 1.6 + 0.07 * p.blocks.length;                         // quicker (radians a second) the higher the tower, no end to it
  const twSwing = (p) => NWf / 2 + twAmp(p) * Math.sin(p.ph) / p.kS;          // (world x)
  const twSX = (p, x) => NWf / 2 + (x - NWf / 2) * p.kS;                  // world -> screen
  const twSY = (p, h) => TW_FLOOR - (h - p.camS) * p.kS;
  const twHang = (p) => p.camS + (TW_FLOOR - TW_HANG - TW_BH * p.kS) / p.kS;   // the hanging brick's bottom (world h)
  function twNew(p) { p.cur = { v: Math.floor(Math.random() * 3), t: G.t }; }
  function twDrop() {
    const p = G.tw; if (!p || p.st !== 'play' || !p.cur) return;
    p.fall.push({ x: window.__twSnap ? twTopX(p) : twSwing(p), h: twHang(p), vy: 0, v: p.cur.v, mode: 'fall' }); p.cur = null; p.pressT = G.t;
    SND.play('twDrop');
  }
  function twLose(p) {                                       // (v55) one lost: the end
    p.streak = 0; p.misses++; SND.play('twMiss'); buzz(60);
    if (p.st === 'play') { p.st = 'over'; p.stT = G.t; p.why = 'drop'; }
  }
  // a brick reaching the top: perfect, on, tipping off the edge, or past it
  function twLand(p, f) {
    const n = p.blocks.length, top = twTopX(p), dx = f.x - top, half = n ? TW_BW / 2 : TW_PIER;
    if (n && Math.abs(dx) <= TW_PERF) {
      f.x = top; p.streak++; p.perf++; p.best = Math.max(p.best, p.streak);
      const pts = 100 + 50 * Math.min(3, p.streak); p.gain += pts; p.pops.push({ x: f.x, h: (n + 1) * TW_BH, s: `${TR('퍼펙트!', 'Perfect!')} +${pts}`, t: G.t, gold: true });
      SND.play('twPerfect'); buzz([20, 20, 30]);
    } else if (Math.abs(dx) <= half) {                        // its middle over what is under it: it stays, as it is
      p.streak = 0; p.gain += 100; p.pops.push({ x: f.x, h: (n + 1) * TW_BH, s: '+100', t: G.t, gold: false });
      SND.play('twLand'); buzz(25);
    } else if (Math.abs(dx) < half + TW_BW / 2) {             // it sits on the edge with its middle past it: it tips over and slides off
      const s = dx > 0 ? 1 : -1;
      f.mode = 'tip'; f.s = s; f.ex = top + s * half; f.eh = n * TW_BH; f.r = 0; f.vr = 0; f.t = G.t; f.h = n * TW_BH;
      SND.play('twLand'); twLose(p);
      return;
    } else { f.mode = 'off'; f.vx = 0; f.r = 0; f.vr = 0; twLose(p); return; }
    f.mode = 'done';
    p.blocks.push({ x: f.x, v: f.v, t: G.t });
    // (v55) will it stand: from each brick up (the lowest first), their weight's middle against the edge of what is under
    // them (the brick below, or the pier); past it, they go over about that edge
    const bl = p.blocks;
    for (let i = 0; i < bl.length; i++) {
      let sx = 0; for (let j = i; j < bl.length; j++) sx += bl[j].x;
      const c = sx / (bl.length - i), base = i ? bl[i - 1].x : NWf / 2, half = i ? TW_BW / 2 : TW_PIER;
      if (Math.abs(c - base) > half) { const dir = c > base ? 1 : -1; p.topple = { dir, t: G.t, lv: i, px: base + dir * half }; p.st = 'over'; p.stT = G.t; p.why = 'topple'; SND.play('twTopple'); buzz([60, 40, 120]); break; }
    }
  }
  function stepTW(dt) {
    const p = G.tw; if (!p) return;
    // the view: as big as fits the tower under the room left (down to half), then climbing with it
    const H = p.blocks.length * TW_BH;
    p.k = Math.max(TW_KMIN, Math.min(1, TW_ROOM / (H + 12)));
    p.cam = Math.max(0, H + 12 - TW_ROOM / p.k);
    p.kS += (p.k - p.kS) * Math.min(1, dt * 4); p.camS += (p.cam - p.camS) * Math.min(1, dt * 5);
    if (p.st === 'play') p.ph += twFreq(p) * dt;
    for (const f of p.fall) {
      if (f.mode === 'fall') { f.vy += TW_G * dt; f.h -= f.vy * dt; if (f.h <= p.blocks.length * TW_BH) twLand(p, f); continue; }
      if (f.mode === 'tip') {                                   // turning over the edge, faster and faster; then off it
        f.vr += 9 * dt; f.r += f.vr * dt;
        if (f.r > 0.9) { f.mode = 'off'; f.vx = f.s * 40; f.vy = 20; f.vr = f.s * 5; f.x = f.ex + f.s * TW_BW * 0.3; f.h = f.eh - 2; f.r = f.s * f.r; }
        continue;
      }
      if (f.mode === 'off') { f.vy += TW_G * dt; f.h -= f.vy * dt; f.x += (f.vx || 0) * dt; f.r += (f.vr || 0) * dt; }
    }
    p.fall = p.fall.filter((f) => f.mode !== 'done' && !(f.mode === 'off' && twSY(p, f.h) > NH + 40));
    const u = G.t - p.stT;                                    // (after the landings: one may have ended it just now)
    if (p.st === 'intro') { if (u >= TW_INTRO) { p.st = 'play'; p.stT = G.t; p.t0 = G.t; twNew(p); } return; }
    if (p.st === 'play') {
      const busy_ = p.fall.some((f) => f.mode === 'fall' || f.mode === 'tip');
      if (!p.cur && !busy_ && G.t - p.pressT > 0.35) twNew(p);
      if (AUTO && !window.__noAuto && p.cur && G.t - p.cur.t > 0.3) {     // the test pilot (__twMiss: off the edge; __twOff: this far off), at the frame nearest
        const dx = twSwing(p) - twTopX(p), half = p.blocks.length ? TW_BW / 2 : TW_PIER;
        const tol = Math.max(1.0, Math.abs(twAmp(p) * twFreq(p) * Math.cos(p.ph) / p.kS) * dt * 0.55);
        if (window.__twMiss ? Math.abs(dx) > half + TW_BW / 2 + 2 : window.__twOff !== undefined ? Math.abs(dx - window.__twOff) < tol : Math.abs(dx) < tol) twDrop();
      }
      if (p.cur && G.t - p.cur.t >= TW_AUTO) twDrop();         // (v55) left hanging: it goes by itself
      return;
    }
    if (p.st === 'over') { if (u >= (p.why === 'topple' ? 1.8 : 1.4)) { p.st = 'done'; p.stT = G.t; if (p.blocks.length >= 10) SND.play('slWin'); } return; }
    if (p.st === 'done' && u >= TW_END) endTW();
  }
  // one brick, in world units (its middle at x, its bottom at -h: drawn inside the view's transform), turned r about
  // its bottom middle (or, tipping, about the edge it tips over); a gold flash on a perfect
  function twBrick(v, x, yb, rot = 0, glow = 0, piv = null) {
    const s = M.sprites['tw_block' + v], kx = TW_BW / 44, ky = TW_BH / 15.2;   // (the picture: a 44 x 15.2 body, its bottom 17.8 down a 48 x 19 canvas)
    ctx.save();
    if (piv) { ctx.translate(piv[0], piv[1]); ctx.rotate(rot); ctx.translate(x - piv[0], yb - piv[1]); }
    else { ctx.translate(x, yb); if (rot) { ctx.translate(0, -TW_BH / 2); ctx.rotate(rot); ctx.translate(0, TW_BH / 2); } }
    spr('tw_block' + v, -s.w * kx / 2, -17.8 * ky, 1, s.w * kx, s.h * ky);
    if (glow > 0) { ctx.globalCompositeOperation = 'lighter'; const a = ctx.globalAlpha; ctx.globalAlpha = a * glow * 0.6; rrect(-TW_BW / 2, -TW_BH, TW_BW, TW_BH, 3); ctx.fillStyle = '#ffd860'; ctx.fill(); ctx.globalAlpha = a; ctx.globalCompositeOperation = 'source-over'; }
    ctx.restore();
  }
  function drawTW() {
    const p = G.tw; if (!p) return;
    world();
    let al = Math.min(1, (G.t - p.inT) / 0.35);
    if (p.st === 'done') al *= Math.max(0, Math.min(1, (TW_END - (G.t - p.stT)) / 0.35));
    const zx = NWf / 2, A = (a) => { ctx.globalAlpha = al * a; }, k = p.kS;
    // the tank: dark green water, its concrete walls going up (ribs that move with the view), lighter in the middle
    { const g = ctx.createLinearGradient(0, 0, 0, NH); g.addColorStop(0, '#0a1c1e'); g.addColorStop(1, '#04100f'); A(1); ctx.fillStyle = g; ctx.fillRect(0, 0, NWf, NH);
      const wx = Math.min(150, NWf * 0.42) * Math.max(0.75, k);
      A(0.5); ctx.fillStyle = '#16302f'; for (const sx of [-1, 1]) ctx.fillRect(zx + sx * wx - 9, 0, 18, NH);
      A(0.35); ctx.fillStyle = '#2a4a46'; const step = 40 * k; for (let y = (twSY(p, 0) % step) - step; y < NH; y += step) for (const sx of [-1, 1]) ctx.fillRect(zx + sx * wx - 9, y, 18, 2);
      const r = ctx.createRadialGradient(zx, 120, 10, zx, 120, 190); r.addColorStop(0, 'rgba(150,210,195,0.2)'); r.addColorStop(1, 'rgba(150,210,195,0)'); A(1); ctx.fillStyle = r; ctx.fillRect(0, 0, NWf, NH);
      A(0.25); for (let i = 0; i < 14; i++) { const bx = ((i * 53.7) % NWf), by = NH - ((G.t * (9 + i % 4 * 3) + i * 31) % (NH + 10)); ctx.beginPath(); ctx.arc(bx, by, 0.8 + (i % 3) * 0.5, 0, 6.2832); ctx.fillStyle = '#bfeee6'; ctx.fill(); } }
    // height marks up the right side (every 5 bricks)
    for (let n5 = 5; n5 < 300; n5 += 5) { const y = twSY(p, n5 * TW_BH); if (y < 74) break; if (y > NH) continue;
      A(0.55); ctx.fillStyle = '#9ad8d0'; ctx.fillRect(NWf - 46, y - 0.4, 10, 0.8); label(TR(`${n5}층`, `${n5}`), NWf - 49, y, 6, 'right', al * 0.7, '#bff0e8'); }
    // the world: the pier, the tower (leaning a little with its weight off the middle; going over when it topples), the
    // bricks falling or tipping off
    ctx.save(); ctx.translate(zx, twSY(p, 0)); ctx.scale(k, k); ctx.translate(-zx, 0);
    { const s = M.sprites.tw_base, sc = (2 * TW_PIER + 2) / s.w; A(1); spr('tw_base', zx - s.w * sc / 2, -s.top * sc, 1, s.w * sc, s.h * sc); A(1); }
    const n = p.blocks.length, com = n ? p.blocks.reduce((a, b) => a + b.x, 0) / n - zx : 0;
    const lean = p.topple ? 0 : com / 900 * Math.min(1, n / 6) + Math.sin(G.t * 2.6) * 0.0012 * Math.min(n, 25), tp = p.topple, lv = tp ? tp.lv : n;
    ctx.save(); ctx.translate(zx, 0); ctx.rotate(lean);
    p.blocks.forEach((b, i) => { if (i >= lv) return; const gl = i === n - 1 && G.t - b.t < 0.4 && p.pops.length && p.pops[p.pops.length - 1].gold ? 1 - (G.t - b.t) / 0.4 : 0;
      A(1); twBrick(b.v, b.x - zx, -i * TW_BH, 0, gl); });
    ctx.restore(); A(1);
    if (tp) {                                                  // (v55) the bricks from the one that gave way up, going over its edge
      const v = G.t - tp.t, r = tp.dir * Math.min(1.6, 0.4 * v + 1.6 * v * v);
      ctx.save(); ctx.translate(tp.px, -lv * TW_BH); ctx.rotate(r);
      A(Math.max(0, 1 - v / 1.6)); for (let i = lv; i < n; i++) twBrick(p.blocks[i].v, p.blocks[i].x - tp.px, -(i - lv) * TW_BH);
      ctx.restore(); A(1);
    }
    for (const f of p.fall) {
      if (f.mode === 'tip') twBrick(f.v, f.x, -f.h, f.s * f.r, 0, [f.ex, -f.eh]);
      else twBrick(f.v, f.x, -f.h, f.r || 0);
    }
    ctx.restore();
    // the crane: its jib across the top (a yellow lattice), the trolley, the cable, the hook, the brick on it (the view's size)
    { const y = TW_JIB; A(1);
      rrect(-4, y - 4.5, NWf + 8, 9, 2); ctx.fillStyle = '#1a1006'; ctx.fill();
      const g = ctx.createLinearGradient(0, y - 3.5, 0, y + 3.5); g.addColorStop(0, '#ffe27a'); g.addColorStop(0.5, '#f0a800'); g.addColorStop(1, '#a86400');
      ctx.fillStyle = g; ctx.fillRect(-4, y - 3.5, NWf + 8, 7);
      ctx.strokeStyle = '#5a3200'; ctx.lineWidth = 0.9; ctx.beginPath();
      for (let x = -4; x < NWf + 8; x += 9) { ctx.moveTo(x, y - 3.2); ctx.lineTo(x + 4.5, y + 3.2); ctx.lineTo(x + 9, y - 3.2); } ctx.stroke();
      if (p.cur && p.st === 'play') {
        const tx = twSX(p, twSwing(p)), hk = M.sprites.tw_hook, hs = 0.7 * Math.max(0.75, k), hy = TW_HANG - hk.hang[1] * hs + 1;
        rrect(tx - 7, y - 5.5, 14, 6.5, 2); ctx.fillStyle = '#2a2e38'; ctx.fill();
        ctx.strokeStyle = '#1a1a1a'; ctx.lineWidth = 0.9; ctx.beginPath(); ctx.moveTo(tx - 1, y + 1); ctx.lineTo(tx - 1, hy + 1); ctx.moveTo(tx + 1, y + 1); ctx.lineTo(tx + 1, hy + 1); ctx.stroke();
        ctx.save(); ctx.translate(tx, TW_HANG + TW_BH * k); ctx.scale(k, k); twBrick(p.cur.v, 0, 0); ctx.restore(); A(1);
        spr('tw_hook', tx - hk.hang[0] * hs, hy, 1, hk.w * hs, hk.h * hs); A(1);
        const wait = G.t - p.cur.t;                             // (v55) the last 2 s before it drops by itself: a ring running out
        if (wait > TW_AUTO - 2) { const f = Math.max(0, (TW_AUTO - wait) / 2), cy = TW_HANG + TW_BH * k / 2;
          A(0.85); ctx.beginPath(); ctx.arc(tx, cy, TW_BW * k / 2 + 5, -Math.PI / 2, -Math.PI / 2 + f * 6.2832); ctx.lineWidth = 1.6; ctx.strokeStyle = '#ffe68a'; ctx.stroke(); A(1); }
        A(0.22); ctx.setLineDash([2, 3]); ctx.strokeStyle = '#ffffff'; ctx.beginPath(); ctx.moveTo(tx, TW_HANG + TW_BH * k + 2); ctx.lineTo(tx, twSY(p, n * TW_BH)); ctx.stroke(); ctx.setLineDash([]); A(1);
      } }
    // what each landing came to; the height, the score, the lives, the time
    for (const q of p.pops) { const v = G.t - q.t; if (v > 0.9 || p.st === 'over') continue;
      label(q.s, twSX(p, q.x), twSY(p, q.h) - 8 - v * 18, q.gold ? 9 : 7.5, 'center', al * Math.min(1, (0.9 - v) / 0.3), q.gold ? '#ffe14a' : '#ffffff'); }
    p.pops = p.pops.filter((q) => G.t - q.t < 0.9);
    if (p.st === 'play' || p.st === 'over') {
      label(TR(`${n}층`, `${n} high`), 16, 63, 11, 'left', al, '#ffe0a8');
      label(`${PT(p.gain)}`, 16, 75, 7.5, 'left', al, '#ffe68a');
      if (p.st === 'play' && n === 0 && !p.fall.length) label(TR('탭해서 떨어뜨리기!', 'Tap to drop!'), zx, 112, 9.5, 'center', al * (0.75 + 0.25 * Math.sin(G.t * 6)), '#ffffff');
      if (p.st === 'over') label(p.why === 'topple' ? TR('무너졌다!', 'It fell!') : TR('떨어졌다!', 'Dropped!'), zx, 100, 15, 'center', al, '#ff9aa8');
    }
    if (p.st === 'intro') {
      const v = G.t - p.stT, a = Math.min(1, v / 0.3) * Math.max(0, Math.min(1, (TW_INTRO - v) / 0.3)), bw = Math.min(262, NWf - 16);
      A(a * 0.86); rrect(zx - bw / 2, 70, bw, 58, 8); ctx.fillStyle = '#10141e'; ctx.fill(); A(1);
      label(TR('똥 탑 쌓기!', 'Poop tower!'), zx, 85, 15, 'center', al * a, '#ffe0a8');
      label(TR('흔들리는 똥을 탭해서 떨어뜨려 높이 쌓아요', 'Tap to drop each swinging brick - stack them high'), zx, 103, 7.5, 'center', al * a, '#ffffff');
      label(TR('하나라도 떨어지거나 무너지면 끝! 갈수록 빨라져요', 'One dropped, or the tower falls: the end! It gets quicker'), zx, 116, 7.5, 'center', al * a, '#ffe68a');
    }
    if (p.st === 'done') {
      const v = G.t - p.stT, a = Math.min(1, v / 0.25) * Math.max(0, Math.min(1, (TW_END - v) / 0.35));
      A(a * 0.86); rrect(zx - 112, 66, 224, 62, 8); ctx.fillStyle = '#10141e'; ctx.fill(); A(1);
      label(TR(`${n}층 쌓았다!`, `${n} high!`), zx, 81, 14, 'center', a, '#ffe68a');
      label(TR(`퍼펙트 ${p.perf}번 · 최고 연속 ${p.best}`, `Perfect ${p.perf} · best run ${p.best}`), zx, 98, 7.5, 'center', a, '#ffffff');
      label(`+${PT(p.gain)}`, zx, 113, 10, 'center', a, '#ffe68a');
    }
    ctx.globalAlpha = 1;
  }

  // ---------------------------------------------------------------- the bird shoot (at the outfall) (v53, v54, v55)
  // '새 사격': out of the pipe at last, under the sky. (v55) One bird at a time flies across the sky from the right to
  // the left, ten of them, each quicker than the last (the user's bird: ar_bird.webp, bird_user.py). Your runner stands
  // at the bottom left, face on, with a bow. The left of the screen is a stick for the bow's angle: push it left and
  // the bow turns up, right and it turns down (or the arrow keys); the right is the shoot button (or space); a short
  // dotted line shows where the arrow goes (it drops a little). A bird hit: 100 x its stage, and from the second in a
  // row on, 100 more for each in the row before it; one missed (off the left): nothing, and the row is broken.
  // (pictures: minigames3.py's ar.webp (the bow, the arrow, the clouds) + ar_field.webp, drawn mirrored so the pipe is
  // on the right; the runner: bat_<char>.webp's 45, face on, turned right)
  const AR_STAGES = 10, AR_INTRO = 2.8, AR_END = 3.0, AR_V = 430, AR_GA = 150, AR_COOL = 0.3, AR_RIVER = 124;
  const AR_A0 = 0.08, AR_A1 = 1.35, AR_AV = 1.7, AR_CX = 94, AR_PAD = { r: 19, m: 30, y: 146 };
  const AR_BV0 = 80, AR_BV1 = 290, AR_GAP = 0.7;             // the first bird's and the tenth's speed; between birds
  const AR_FLAP = [9, 8, 7, 6, 7, 8];                         // the sheet's frames, wings down to up and back
  const arBirdV = (s) => AR_BV0 + (AR_BV1 - AR_BV0) * (s - 1) / (AR_STAGES - 1);
  const arBow = () => [AR_CX + 14, 147];                      // the bow's grip, at the runner's right side
  function startAR() {
    holdBoost();
    G.obs = G.obs.filter((o) => o.x + o.w < G.x - 12);
    G.items = G.items.filter((i) => i.x < G.x - 12 || i.taken);
    G.ar = { st: 'intro', stT: G.t, inT: G.t, t0: 0, gain: 0, aim: 0.6, fireT: -9, pressT: -9, arrows: [], bird: null, feathers: [], rings: [], pops: [],
      stage: 0, next: 0, res: [], hits: 0, shots: 0, streak: 0, best: 0,
      clouds: [[0.15, 30, 0], [0.62, 18, 1], [0.95, 40, 0]], keys: { U: false, D: false }, pad: null };
    G.slideHeld = false; held.clear(); pressed.jump = false;
  }
  function endAR() {
    bankGame(G.ar); G.ar = null; G.games = (G.games || 0) + 1; resumeBoost();
    G.genX = Math.max(G.genX, G.x + NW * 0.8);
    G.banner = G.t;
  }
  // a bird: in from past the right edge at a height, a little up or down by the left edge; it bobs as it flaps
  function arSpawn(p) {
    p.stage++;
    const s = p.stage, y0 = 56 + Math.random() * 44, y1 = Math.max(52, Math.min(104, y0 + (Math.random() - 0.5) * 36));
    p.bird = { s, t0: G.t, x0: NWf + 24, y0, y1, vx: -arBirdV(s), fr: 2.3 + 1.4 * (s - 1) / (AR_STAGES - 1), st: 'fly', x: NWf + 24, y: y0 };
    p.loaded = true; p.loadT = G.t;                           // (v59) one arrow a bird: it goes on the bow now
  }
  // where the bird is at the time t (it keeps to its line: the test pilot leads it by this)
  function arBirdAt(b, t) {
    const x = b.x0 + b.vx * (t - b.t0), pr = (b.x0 - x) / (b.x0 + 30), ph = (t - b.t0) * b.fr;
    return [x, b.y0 + (b.y1 - b.y0) * pr - 1.8 * Math.sin(ph * 6.2832)];
  }
  const arBirdR = () => { const s = M.sprites.ar_bird0; return (s ? s.rb : 8.6) + 1.2; };     // its body (round), hit by an arrow's tip
  const arReady = (p) => p.loaded && G.t - p.loadT >= AR_COOL && p.bird && p.bird.st === 'fly';
  function arShoot() {
    const p = G.ar; if (!p || p.st !== 'play' || !arReady(p)) return;       // (v59: one arrow a bird)
    const [bx, by] = arBow(), dx = Math.cos(p.aim), dy = -Math.sin(p.aim);
    p.arrows.push({ x: bx + dx * 5, y: by + dy * 5, vx: dx * AR_V, vy: dy * AR_V, t: G.t, s: p.bird.s });
    p.fireT = G.t; p.pressT = G.t; p.shots++; p.loaded = false;
    SND.play('arBow');
  }
  function arHit(p, a, b) {
    a.dead = true; b.st = 'hit'; b.hitT = G.t; b.vx2 = b.vx * 0.25 + a.vx * 0.12; b.vy2 = -45 + a.vy * 0.1; b.r = 0; b.vr = (Math.random() < 0.5 ? -1 : 1) * 7;
    p.hits++; p.streak++; p.best = Math.max(p.best, p.streak); p.res.push(1);
    const base = 100 * b.s, bonus = p.streak > 1 ? 100 * (p.streak - 1) : 0, pts = base + bonus; p.gain += pts;
    p.pops.push({ x: b.x, y: b.y, s: p.streak > 1 ? TR(`${p.streak}연속! +${pts}`, `${p.streak} in a row! +${pts}`) : `+${pts}`, t: G.t, big: p.streak > 1 });
    const cols = ['#8cc8ff', '#ffffff', '#5aa4f0', '#ffffff'];
    for (let i = 0; i < 9; i++) { const t = Math.random() * 6.28, v = 25 + Math.random() * 55; p.feathers.push({ x: b.x, y: b.y, vx: Math.cos(t) * v, vy: Math.sin(t) * v - 20, r: Math.random() * 6.28, vr: (Math.random() - 0.5) * 8, c: cols[i % 4], t: G.t }); }
    SND.play(p.streak >= 3 ? 'arGold' : 'arHit'); buzz(p.streak >= 3 ? [30, 30, 50] : 18);
  }
  // the controls: the left half a stick for the angle (left: up, right: down), the right half the shoot button
  function arDown(id, x, y) { const p = G.ar; if (!p || p.st !== 'play') return; if (x < NWf / 2) p.pad = { id, x0: x, kx: 0 }; else arShoot(); }
  function arMove(id, x, y) { const p = G.ar; if (!p || !p.pad || p.pad.id !== id) return; p.pad.kx = Math.max(-1, Math.min(1, (x - p.pad.x0) / AR_PAD.r)); }
  function arUp(id) { const p = G.ar; if (p && p.pad && p.pad.id === id) p.pad = null; }
  // an arrow let go at the angle a, `wait` seconds from now: [how near it comes to the bird, when (after letting go)]
  function arTry(b, a, wait = 0) {
    const [bx, by] = arBow(), vx = Math.cos(a) * AR_V, vy = -Math.sin(a) * AR_V; let best = [1e9, 0];
    for (let t = 0.02; t < 1.2; t += 0.015) {
      const ax = bx + vx * t, ay = by + vy * t + 0.5 * AR_GA * t * t, [fx, fy] = arBirdAt(b, G.t + wait + t);
      if (ay > AR_RIVER + 30 || ax > NWf + 30) break; const d = Math.hypot(ax - fx, ay - fy); if (d < best[0]) best = [d, t];
    }
    return best;
  }
  function stepAR(dt) {
    const p = G.ar; if (!p) return;
    for (const c of p.clouds) { c[0] += dt * (0.004 + 0.003 * c[2]); if (c[0] > 1.15) c[0] = -0.15; }
    const b = p.bird;
    if (b && b.st === 'fly') { [b.x, b.y] = arBirdAt(b, G.t); if (b.x < -30) { b.st = 'gone'; p.streak = 0; p.res.push(0); p.pops.push({ x: NWf / 2, y: 104, s: TR('놓쳤다', 'Missed'), t: G.t, miss: true }); SND.play('arMiss'); p.bird = null; p.next = G.t + AR_GAP; } }
    if (b && b.st === 'fly' && !p.loaded && !p.arrows.some((a) => a.s === b.s)) {     // (v59) its one arrow gone by: missed; it flies off fast
      b.st = 'flee'; b.fleeT = G.t; b.vx2 = b.vx * 2.6; b.vy2 = -45; p.streak = 0; p.res.push(0);
      p.pops.push({ x: NWf / 2, y: 104, s: TR('빗나갔다', 'Missed'), t: G.t, miss: true }); SND.play('arMiss');
    }
    if (b && b.st === 'flee') { b.x += b.vx2 * dt; b.y += b.vy2 * dt; if (b.x < -30 || b.y < -30) { p.bird = null; p.next = G.t + AR_GAP; } }
    if (b && b.st === 'hit') {                                  // hit: it tumbles down into the river
      b.vy2 += 320 * dt; b.x += b.vx2 * dt; b.y += b.vy2 * dt; b.r += b.vr * dt;
      if (b.y > AR_RIVER + 4) { p.rings.push({ x: b.x, y: AR_RIVER + 2, t: G.t }); SND.play('arSplash'); p.bird = null; p.next = G.t + AR_GAP * 0.6; }
    }
    for (const a of p.arrows) {
      const steps = 3; for (let k = 0; k < steps; k++) {        // (in small steps: quick arrows)
        a.vy += AR_GA * dt / steps; a.x += a.vx * dt / steps; a.y += a.vy * dt / steps;
        const q = p.bird; if (q && q.st === 'fly' && a.s === q.s && !a.dead && Math.hypot(q.x - a.x, q.y - a.y) < arBirdR()) arHit(p, a, q);
      }
    }
    for (const f of p.feathers) { f.vx *= Math.exp(-2.2 * dt); f.vy = f.vy * Math.exp(-2.2 * dt) + 60 * dt; f.x += (f.vx + Math.sin((G.t - f.t) * 7 + f.r) * 10) * dt; f.y += f.vy * dt; f.r += f.vr * dt; }
    p.arrows = p.arrows.filter((a) => !a.dead && a.y > -40 && a.y < NH + 10 && a.x > -30 && a.x < NWf + 30);
    p.feathers = p.feathers.filter((f) => G.t - f.t < 1.4); p.rings = p.rings.filter((r) => G.t - r.t < 0.7); p.pops = p.pops.filter((q) => G.t - q.t < 0.9);
    const u = G.t - p.stT;
    if (p.st === 'intro') { if (u >= AR_INTRO) { p.st = 'play'; p.stT = G.t; p.t0 = G.t; p.next = G.t + 0.5; } return; }
    if (p.st === 'play') {
      if (!p.bird && G.t >= p.next) {
        if (p.stage < AR_STAGES) arSpawn(p);
        else { p.st = 'done'; p.stT = G.t; if (p.gain >= 3000) SND.play('slWin'); return; }
      }
      const v = (p.keys.U ? 1 : 0) - (p.keys.D ? 1 : 0) - (p.pad ? p.pad.kx : 0);
      p.aim = Math.max(AR_A0, Math.min(AR_A1, p.aim + v * AR_AV * dt));
      const q = p.bird;
      if (AUTO && !window.__noAuto && q && q.st === 'fly') {    // the test pilot: the angle that meets the bird soonest, turning to it at the stick's speed (leading it by the turn)
        if (p.want === null || p.want === undefined || G.t - p.wantT > 0.2) {
          p.want = null; p.wantT = G.t; let best = null; const R = arBirdR() * 0.6;
          for (let a = AR_A0; a <= AR_A1; a += 0.01) { const w = Math.max(Math.abs(a - p.aim) / AR_AV, AR_COOL - (G.t - p.loadT), 0), [d, t] = arTry(q, a, w); if (d < R && (!best || w + t < best.c)) best = { a, c: w + t }; }
          if (best) p.want = best.a;
        }
        if (p.want !== null && p.want !== undefined) { const d = p.want - p.aim; p.aim += Math.sign(d) * Math.min(Math.abs(d), AR_AV * dt); if (Math.abs(d) < 0.01 && arReady(p)) { arShoot(); p.want = null; } }
      }
      return;
    }
    if (p.st === 'done' && u >= AR_END) endAR();
  }
  function drawARControls(p, al) {
    const live = p.st === 'play', R = AR_PAD.r, sx = AR_PAD.m, by = AR_PAD.y, bxr = NWf - AR_PAD.m;
    ctx.globalAlpha = al * (live ? 1 : 0.45);
    ctx.beginPath(); ctx.arc(sx, by, R, 0, 6.2832); ctx.fillStyle = 'rgba(26,10,20,0.5)'; ctx.fill(); ctx.lineWidth = 1.2; ctx.strokeStyle = 'rgba(255,255,255,0.75)'; ctx.stroke();
    ctx.fillStyle = 'rgba(255,255,255,0.7)';                    // left and right marks
    for (const s of [-1, 1]) { ctx.beginPath(); ctx.moveTo(sx + s * (R - 3), by); ctx.lineTo(sx + s * (R - 7.5), by - 3.2); ctx.lineTo(sx + s * (R - 7.5), by + 3.2); ctx.closePath(); ctx.fill(); }
    const kx = p.pad ? p.pad.kx : 0;
    ctx.beginPath(); ctx.arc(sx + kx * R * 0.55, by, 8.5, 0, 6.2832); ctx.fillStyle = p.pad ? 'rgba(255,236,170,0.95)' : 'rgba(255,255,255,0.85)'; ctx.fill(); ctx.lineWidth = 1; ctx.strokeStyle = '#1a0a14'; ctx.stroke();
    label(TR('각도', 'Angle'), sx, by + R + 6.5, 6.5, 'center', al * (live ? 1 : 0.45), '#ffffff');
    label(TR('위', 'up'), sx - R - 2, by - R + 2, 5.5, 'center', al * (live ? 0.9 : 0.4), '#ffffff');
    label(TR('아래', 'down'), sx + R + 3, by - R + 2, 5.5, 'center', al * (live ? 0.9 : 0.4), '#ffffff');
    const pr = G.t - p.pressT < 0.15, ready = arReady(p);
    ctx.globalAlpha = al * (live ? 1 : 0.45);
    ctx.beginPath(); ctx.arc(bxr, by + (pr ? 1 : 0), R, 0, 6.2832);
    const g = ctx.createRadialGradient(bxr - 5, by - 6, 2, bxr, by, R); g.addColorStop(0, pr ? '#ffd0a0' : '#ffb070'); g.addColorStop(0.55, pr ? '#e85020' : '#ff6a2a'); g.addColorStop(1, '#a82a10');
    ctx.fillStyle = g; ctx.fill(); ctx.lineWidth = 1.4; ctx.strokeStyle = '#2a0a06'; ctx.stroke();
    label(TR('발사!', 'Shoot!'), bxr, by + (pr ? 1 : 0), 9.5, 'center', al * (live && ready ? 1 : 0.55), '#ffffff');
    if (live && ready) { ctx.globalAlpha = al * (0.25 + 0.25 * Math.sin(G.t * 6)); ctx.beginPath(); ctx.arc(bxr, by, R + 3, 0, 6.2832); ctx.lineWidth = 1.5; ctx.strokeStyle = '#ffd080'; ctx.stroke(); }
    ctx.globalAlpha = al;
  }
  function drawAR() {
    const p = G.ar; if (!p) return;
    world();
    let al = Math.min(1, (G.t - p.inT) / 0.35);
    if (p.st === 'done') al *= Math.max(0, Math.min(1, (AR_END - (G.t - p.stT)) / 0.35));
    const zx = NWf / 2, A = (a) => { ctx.globalAlpha = al * a; };
    // the place, mirrored (the pipe on the right): the sky, the hills, the river, the pipe, the bank
    { const s = M.sprites.ar_field; ctx.save(); ctx.translate(zx, 0); ctx.scale(-1, 1); A(1); spr('ar_field', -s.w / 2, 0, 1, s.w, s.h); ctx.restore(); A(1); }
    for (const [cx, cy, k] of p.clouds) { const s = M.sprites['ar_cloud' + k]; A(0.95); spr('ar_cloud' + k, cx * (NWf + 80) - 40 - s.w / 2, cy, 1, s.w, s.h); }
    // the water out of the pipe: a few white streaks running down it
    { const fx = zx + 172; A(0.5); ctx.strokeStyle = '#ffffff'; ctx.lineWidth = 0.9; ctx.beginPath();
      for (let i = 0; i < 6; i++) { const x = fx - 12 + i * 5, ph = ((G.t * 1.6 + i * 0.37) % 1), y0 = 121 + ph * 22; ctx.moveTo(x - ph * (i - 2.5) * 1.2, y0); ctx.lineTo(x - (ph + 0.12) * (i - 2.5) * 1.2, y0 + 5); } ctx.stroke();
      A(1); }
    // the bird: flapping across (lined up by its body), or hit and tumbling down
    { const b = p.bird;
      if (b) { const nm = b.st === 'hit' ? 'ar_bird1' : 'ar_bird' + AR_FLAP[Math.floor((G.t - b.t0) * b.fr * AR_FLAP.length) % AR_FLAP.length], s = M.sprites[nm];
        if (s) { ctx.save(); ctx.translate(b.x, b.y); if (b.st === 'hit') ctx.rotate(b.r); A(1); spr(nm, -s.c[0], -s.c[1], 1, s.w, s.h); ctx.restore(); } } }
    // the feathers, the rings on the water
    for (const f of p.feathers) { const v = (G.t - f.t) / 1.4; A(1 - v * v); ctx.save(); ctx.translate(f.x, f.y); ctx.rotate(f.r); ctx.beginPath(); ctx.ellipse(0, 0, 2.8, 1.1, 0, 0, 6.2832); ctx.fillStyle = f.c; ctx.fill(); ctx.lineWidth = 0.35; ctx.strokeStyle = '#1a2a4a'; ctx.stroke(); ctx.restore(); }
    for (const r of p.rings) { const v = (G.t - r.t) / 0.7; A(0.6 * (1 - v)); ctx.beginPath(); ctx.ellipse(r.x, r.y, 3 + v * 12, 1 + v * 3, 0, 0, 6.2832); ctx.lineWidth = 1; ctx.strokeStyle = '#ffffff'; ctx.stroke(); }
    A(1);
    // the arrows (pointing the way they fly)
    for (const a of p.arrows) { const s = M.sprites.ar_arrow, sc = 0.75; ctx.save(); ctx.translate(a.x, a.y); ctx.rotate(Math.atan2(a.vy, a.vx) + Math.PI / 2); A(1); spr('ar_arrow', -s.w * sc / 2, 0, 1, s.w * sc, s.h * sc); ctx.restore(); }
    // where the arrow will go: a short dotted line (it drops a little) (v56: red dots)
    if (p.st === 'play') { const [bx, by] = arBow(), vx = Math.cos(p.aim) * AR_V, vy = -Math.sin(p.aim) * AR_V;
      for (let i = 2; i < 13; i++) { const t = i * 0.022, x = bx + vx * t, y = by + vy * t + 0.5 * AR_GA * t * t; A(1 - i / 22); ctx.beginPath(); ctx.arc(x, y, 1.6, 0, 6.2832); ctx.fillStyle = '#ff2626'; ctx.fill(); ctx.lineWidth = 0.5; ctx.strokeStyle = '#3a0008'; ctx.stroke(); } A(1); }
    // the runner at the bottom left, face on (turned right), the bow in front of it at the angle, the string drawn
    // back and let go, an arrow on it when it is ready
    { const nm = `bt_${G.char}_45`, s = M.sprites[nm], sc = 0.62, [bx, by] = arBow(), since = G.t - p.fireT;
      if (s) { A(1); spr(nm, AR_CX - s.foot[0] * sc - (since < 0.08 ? 1 : 0), 181 - s.foot[1] * sc, 1, s.w * sc, s.h * sc); }
      const bw = M.sprites.ar_bow, k = 0.62, pull = p.st === 'play' && p.loaded ? Math.min(1, (G.t - p.loadT) / AR_COOL) : 0;     // (v59: drawn back only with its one arrow on)
      ctx.save(); ctx.translate(bx, by); ctx.rotate(Math.PI / 2 - p.aim);
      const tipY = (bw.tips[0][1] - bw.grip[1]) * k, tipX = (bw.tips[1][0] - bw.grip[0]) * k, nock = tipY + 3 + 5 * pull;
      A(1); ctx.strokeStyle = '#f4f0e8'; ctx.lineWidth = 0.7; ctx.beginPath(); ctx.moveTo(-tipX, tipY); ctx.lineTo(0, nock); ctx.lineTo(tipX, tipY); ctx.stroke();
      spr('ar_bow', -bw.grip[0] * k, -bw.grip[1] * k, 1, bw.w * k, bw.h * k);
      if (pull > 0.95 && p.st === 'play' && p.loaded) { const s2 = M.sprites.ar_arrow, sc2 = 0.75; A(1); spr('ar_arrow', -s2.w * sc2 / 2, nock - s2.h * sc2 + 1, 1, s2.w * sc2, s2.h * sc2); }
      ctx.restore(); A(1); }
    if (p.st !== 'intro') drawARControls(p, al);
    // the points; the stage, the score, the ten (hit, missed, to come)
    for (const q of p.pops) { const v = G.t - q.t; label(q.s, q.x, q.y - 8 - v * 20, q.big ? 10 : q.miss ? 10 : 8, 'center', al * Math.min(1, (0.9 - v) / 0.3), q.miss ? '#ffb0b8' : q.big ? '#ffe14a' : '#ffffff'); }
    if (p.st === 'play') {
      label(TR(`${Math.max(1, p.stage)}단계 / ${AR_STAGES}`, `Stage ${Math.max(1, p.stage)} / ${AR_STAGES}`), 16, 46, 10, 'left', al, '#ffe0a8');
      label(`${PT(p.gain)}`, 16, 58, 7.5, 'left', al, '#ffe68a');
      for (let i = 0; i < AR_STAGES; i++) { const x = 19 + i * 6.4, y = 66, r = p.res[i];
        A(1); ctx.beginPath(); ctx.arc(x, y, 2.3, 0, 6.2832);
        if (r === 1) { ctx.fillStyle = '#ffd84a'; ctx.fill(); } else if (r === 0) { ctx.fillStyle = 'rgba(40,20,30,0.75)'; ctx.fill(); }
        ctx.lineWidth = 0.7; ctx.strokeStyle = i === p.res.length && p.bird ? `rgba(255,255,255,${0.6 + 0.4 * Math.sin(G.t * 8)})` : 'rgba(255,255,255,0.8)'; ctx.stroke(); }
      A(1);
    }
    if (p.st === 'intro') {
      const v = G.t - p.stT, a = Math.min(1, v / 0.3) * Math.max(0, Math.min(1, (AR_INTRO - v) / 0.3)), bw = Math.min(262, NWf - 16);
      A(a * 0.86); rrect(zx - bw / 2, 66, bw, 60, 8); ctx.fillStyle = '#10141e'; ctx.fill(); A(1);
      label(TR('새 사격! 10단계', 'Bird shoot! 10 stages'), zx, 81, 15, 'center', al * a, '#ffe0a8');
      label(TR('왼쪽을 좌우로 밀어 활 각도, 오른쪽 버튼으로 발사! (새마다 한 발)', 'Push the left side sideways to aim, right button: shoot! (one arrow a bird)'), zx, 99, 7.5, 'center', al * a, '#ffffff');
      label(TR('단계마다 빨라져요. 연속으로 맞히면 보너스!', 'Quicker every stage. Hit them in a row for a bonus!'), zx, 112, 7.5, 'center', al * a, '#ffe68a');
    }
    if (p.st === 'done') {
      const v = G.t - p.stT, a = Math.min(1, v / 0.25) * Math.max(0, Math.min(1, (AR_END - v) / 0.35));
      A(a * 0.86); rrect(zx - 112, 66, 224, 62, 8); ctx.fillStyle = '#10141e'; ctx.fill(); A(1);
      label(TR(`${p.hits}마리 명중!`, `${p.hits} of ${AR_STAGES} hit!`), zx, 81, 14, 'center', a, '#ffe68a');
      label(TR(`최고 연속 ${p.best} · 화살 ${p.shots}발`, `Best run ${p.best} · ${p.shots} arrows`), zx, 98, 7.5, 'center', a, '#ffffff');
      label(`+${PT(p.gain)}`, zx, 113, 10, 'center', a, '#ffe68a');
    }
    ctx.globalAlpha = 1;
  }

  // ---------------------------------------------------------------- stage 2: under water
  // Holding (either button, anywhere on the screen, the up key) swims up; let go and you sink slowly; you can rest on
  // the bottom; the surface stops you. Things are in the water at every height: columns from the bottom and paper hung
  // from the surface with a gap between to swim through, things floating, bobbing, coming at you
  const SWIM_ACC = 600, SWIM_MAX = 135, SINK_ACC = 380, SINK_MAX = 105;
  const inWater = () => S2_L.has(G.theme) && !G.cut;
  const swimHeld = () => held.size > 0 || keyJump || keySlide || (AUTO && !!G.pilotUp);
  function stepSwim(dt) {
    pressed.jump = false;
    const up = swimHeld();
    G.vy = Math.max(-SINK_MAX, Math.min(SWIM_MAX, G.vy + (up ? SWIM_ACC : -SINK_ACC) * dt));
    G.y += G.vy * dt;
    if (G.y <= 0) { G.y = 0; if (G.vy < 0) G.vy = 0; G.onGround = true; } else G.onGround = false;
    if (G.y >= MAXY) { G.y = MAXY; if (G.vy > 0) G.vy = 0; }
    G.slide = false; G.jumps = 0; G.pitObj = null; G.bounce = false; G.pitHoldT = 0;
    G.swimBub = (G.swimBub || []).filter((b) => G.t - b.t < 0.7);
    if (up && G.t - (G.swimBubT || 0) > 0.12) {               // (looks only: Math.random, not the course's own random)
      G.swimBubT = G.t; G.swimBub.push({ x: G.x - 5 + Math.random() * 3, y: GY - G.y - SH('ch_' + G.char) * 0.55, r: 0.8 + Math.random() * 1.1, t: G.t });
    }
  }
  // a floor piece, its hit box's top above the floor (world y of it)
  const hbTop = (o) => o.y + M.sprites[o.name].hb[1];
  // one pattern under water at x; returns how far it reaches
  function spawnSwim(x, theme, fam, coin, special, v, d, d2, R) {
    const W = [['rest', 0.1], ['gate', 0.3 + 0.08 * d], ['gate2', 0.04 + 0.1 * d], ['float', 0.16], ['bob', 0.1 + 0.09 * d], ['swim', 0.09 + 0.09 * d],
      ['tall', 0.07], ['drop', 0.04 + 0.05 * d + 0.03 * d2], ['spike', 0.04 + 0.05 * d + 0.03 * d2], ['shot', 0.135 + 0.2 * d + 0.1 * d2]];      // (v38: shots twice as often; v48: shots, bob, swim 1.5x)
    let r = R() * W.reduce((a, b) => a + b[1], 0), pat = 'rest';
    for (const [p, w] of W) { if ((r -= w) <= 0) { pat = p; break; } }
    if (window.__patlog) window.__patlog['s2:' + pat] = (window.__patlog['s2:' + pat] || 0) + 1;
    const clear = Math.max(24, 38 - 12 * d - 2 * d2);           // the gap: the body's height and this much
    const midY = (y0, y1) => (y0 + y1) / 2;
    const coinsAt = (x0, n, y, dx = 15) => { for (let i = 0; i < n; i++) addItem(x0 + i * dx, y, coin); };
    const gate = (gx) => {                                      // a column from the bottom (or none) and paper from the surface: the gap between
      const kinds = ['none', 'low', 'tall'], kind = kinds[Math.floor(R() * kinds.length)];      // (the gap low, middle or high)
      let gBot = GY, w = 22, cx = gx + 11;
      if (kind !== 'none') { const o = addObs(gx, kind, theme); if (o) { gBot = hbTop(o); w = o.w; cx = o.x + o.w / 2; } }
      const gTop = gBot - PH - clear;
      if (gTop > 26) {
        const h = addObs(cx, 'hang', theme);
        if (h) { h.x = cx - h.w / 2; h.y = gTop - M.sprites[h.name].hb[3]; }
      }
      coinsAt(cx - 34, 5, midY(Math.max(gTop, 20), gBot), 17);
      return cx + w / 2 - x + 30;
    };
    let used = 60;
    if (pat === 'rest') { const y = 40 + R() * 90; coinsAt(x, 6, y); used = 90; }
    else if (pat === 'gate') used = gate(x + 40);
    else if (pat === 'gate2') { const a = gate(x + 40); used = gate(x + a + Math.max(v * 0.85, 120)); }
    else if (pat === 'float' || pat === 'bob' || pat === 'swim') {
      const o = addObs(x + 40, 'float', theme, pat === 'float' ? null : pat); if (o) {
        const yTop = 30 + R() * (GY - 30 - o.h - 6);              // anywhere in the water
        o.y = yTop;
        if (pat === 'bob') { const amp = Math.max(20, Math.min(40 + R() * 40, GY - 28 - o.h - PH - 30)); o.bob = { y0: yTop < (28 + GY - o.h - amp) / 2 ? 28 : GY - o.h - amp, amp, w: 2 * Math.PI / (2 + R() * 0.8), ph: R() * 6.28 }; o.y = o.bob.y0; }
        if (pat === 'swim') o.vx = 50 + 45 * d;
        const above = yTop > 80;                                   // coins on the open side
        coinsAt(o.x - 10, 4, above ? yTop - 22 : yTop + o.h + 18, 15);
        if (R() < 0.25) addItem(o.x + o.w / 2, above ? yTop - 40 : Math.min(GY - 12, yTop + o.h + 36), special);
        used = o.w + (pat === 'swim' ? 200 : 80);
      }
    } else if (pat === 'tall') {
      const o = addObs(x + 40, R() < 0.5 ? 'tall' : 'huge', theme);
      if (o) { coinsAt(o.x - 15, 4, hbTop(o) - 20, 15); used = o.w + 70; }
    } else if (pat === 'drop') {
      const o = addDrop(x + 50, fam.drop, Math.max(0.33, 0.62 - 0.25 * d - 0.05 * d2));
      coinsAt(x + 30, 4, 60 + R() * 30); used = (o ? o.w : 24) + 90;
    } else if (pat === 'spike') {
      const o = addSpike(x + 50, fam.spike, R() < 0.5, Math.max(0.36, 0.62 - 0.22 * d - 0.05 * d2), 0.5 - 0.12 * d);
      coinsAt(x + 40, 4, GY - 50); used = (o ? o.w : 16) + 90;
    } else if (pat === 'shot') {                                // one, or (faster) two or three at changing heights
      const vx = 110 + 120 * d + 60 * d2, shift = vx * (NWf + 4 - PX) / (v + vx);
      const n = d > 0.3 && R() < 0.65 * d ? (d2 > 0.2 && R() < 0.45 ? 3 : 2) : 1;
      let meet = x + 40, y = 34 + R() * (GY - 54);
      for (let k = 0; k < n; k++) {
        const o = addShot(meet + shift, true, vx, fam.shot);
        if (o) { o.y = Math.max(30, Math.min(GY - 6 - o.h, y)); coinsAt(meet, 4, o.y > 90 ? o.y - 30 : o.y + o.h + 26); }
        meet += Math.max(v * 0.9, 110);                          // (time to swim clear of the next one)
        y = y > 90 ? y - (40 + R() * 30) : y + (40 + R() * 30);
      }
      used = meet - x + 40;
    }
    return used;
  }
  // the pilot under water: the clear heights (feet above the floor) at the nearest thing ahead; swim up while below
  // the middle of the one it is in (or the nearest), as it will be in a moment
  function pilotSwim() {
    const px = G.x, look = Math.max(130, G.v * 0.95), m = 3.5;
    let near = null;
    const boxes = [];
    for (const o of G.obs) {
      let bx;
      if (o.kind === 'door' || o.kind === 'spike' || o.kind === 'drop' || o.kind === 'shot') bx = obsBoxes(o);
      else if (o.kind === 'pit') continue;
      else { const hb = M.sprites[o.name].hb; bx = [[o.x + hb[0], o.y + hb[1], o.x + hb[2], o.y + hb[3]]]; }
      if (o.kind === 'spike' && o.e <= 0.05 && o.x - px < look) bx = [[o.x, GY + 2 - (o.tall ? 34 : 22), o.x + o.w, GY + 2]];   // (coming up: keep off the bottom there)
      if (o.kind === 'drop' && o.st === 'hang' && o.x - px < look) bx = [[o.x, GY - 12, o.x + o.w, GY + 2]];
      if (o.kind === 'bob' && o.bob) bx = [[o.x + 2, o.bob.y0, o.x + o.w - 2, o.bob.y0 + o.bob.amp + o.h]];    // (its whole range)
      for (const b of bx) { if (b[2] < px - PW - 1 || b[0] > px + PW + look) continue; boxes.push(b); if (!near || b[0] < near[0]) near = b; }
    }
    let target = 30;
    if (near) {
      const span = [near[0] - 4, near[2] + 4], blocked = [];
      // the feet heights each blocks: the body (PH tall above the feet) would touch it between these
      for (const b of boxes) if (b[0] < span[1] + 30 && b[2] > span[0]) blocked.push([GY - PH - b[3] - m, GY - b[1] + m]);
      const free = []; let y0 = 0;
      blocked.sort((a, b) => a[0] - b[0]);
      for (const [a, b] of blocked) { if (a > y0) free.push([y0, a]); y0 = Math.max(y0, b); }
      if (y0 < MAXY) free.push([y0, MAXY]);
      let best = null;
      for (const f of free) { const c = Math.max(f[0] + 2, Math.min(f[1] - 2, G.y)); const cost = Math.abs(c - G.y) - (f[1] - f[0]) * 0.05; if (f[1] - f[0] > 4 && (!best || cost < best.cost)) best = { cost, c: (f[0] + f[1]) / 2, f }; }
      if (best) target = best.f[1] - best.f[0] > 40 ? Math.max(best.f[0] + 14, Math.min(best.f[1] - 14, G.y)) : best.c;
    }
    const yp = G.y + G.vy * 0.2;
    G.pilotUp = yp < target;
  }
  // ---------------------------------------------------------------- step
  // (v43) with no top speed the run can get very fast: a step that would move more than 8 units is done as several
  // smaller ones, so nothing thin is passed through between two steps
  function step(dt) {
    const n = G.mode === 'play' ? Math.ceil(Math.abs(curSpeed()) * dt / 8) : 1;
    if (n > 1) { for (let i = 0; i < n; i++) stepOnce(dt / n); return; }
    stepOnce(dt);
  }
  function stepOnce(dt) {
    if (G.mode !== 'play') return;
    if (G.bb && G.bb.fx) G.bb.fx.age += dt;                  // the baseball hit's burst runs on its own clock ...
    if (G.bb && G.bb.hold > 0) { G.bb.hold -= dt; return; }  // ... through the hit-stop, when all else stands still
    if (G.tut && G.tut.on && tutStep(dt)) return;             // (v60) the first run's lessons: stopped till the button is pressed
    if (AUTO && !busy() && !(G.boost > 0) && !window.__noPilot) pilot();      // (__noPilot: tests, run into everything)
    G.t += dt;
    G.magA = ((G.magA || 0) + dt * (G.boost > 0 ? 3.4 : 1.8)) % 6.2832;      // (v61) the magnet's whirl turning
    if (!busy()) G.vt += dt;                                // the speed does not climb during the rhythm and orbit stages
    G.v = Math.min(VMAX, V0 + ACC * G.vt);
    G.slow = Math.min(1, G.slow + dt / 0.6);                 // after a hit, back to full speed in 0.6 s (v43; was 0.8)
    if (G.boost > 0) {                                       // the booster running out: a second of grace
      G.boost -= dt; G.slow = 1;
      if (G.boost <= 0) { G.boost = 0; G.invul = Math.max(G.invul, BOOST_GRACE); }
    }
    { const v = curSpeed(); G.x += v * dt; G.dist += v * dt; }
    { const m = Math.floor(G.dist / M_UNITS); if (m > G.distM) { G.score += m - G.distM; G.distM = m; } }   // (v49) a point a metre
    stepFire(dt);
    if (G.rh) stepRhythm(dt);
    if (G.orb) stepOrbit(dt);
    if (G.bb) stepBaseball(dt);
    if (G.wm) stepWhack();
    if (G.mem) stepMemory();
    if (G.pk) stepPK(dt);
    if (G.sl) stepSlot(dt);
    if (G.yb) stepYB(dt);
    if (G.tw) stepTW(dt);
    if (G.ar) stepAR(dt);
    if (G.cut) stepCut(dt);
    else if (!busy() && G.station >= 0 && COURSE[G.station][5] === STAGE2 - 1) cutCheck();
    G.nudge = Math.max(0, G.nudge - dt * 30);
    moveObs(dt);
    if (inWater()) stepSwim(dt);
    else if (G.cut) { pressed.jump = false; G.slide = false; }     // (the cut scene moves the runner itself)
    else {
    // jump / double jump / slide
    if (pressed.jump) {
      if (G.onGround || (G.jumps === 0 && G.y > -6)) { G.vy = JUMP; G.jumps = 1; G.onGround = false; SND.play('jump1'); }
      else if (G.jumps < 3) { G.vy = G.jumps === 1 ? JUMP2 : JUMP3; G.jumps++; SND.play('jump' + G.jumps); }
      else {                                                 // the 4th and on: like the third, up to the third's best height
        const room = JMAX - G.y;
        if (room > 0.5) { G.vy = Math.max(G.vy, Math.min(JUMP3, Math.sqrt(2 * GRAV * room))); G.jumps++; SND.play('jump3'); }
      }
      pressed.jump = false;
    }
    // a hole under the feet: off you go
    if (G.onGround && !busy() && !(G.boost > 0)) { const p = pitAt(G.x); if (p) { G.onGround = false; G.vy = 0; G.jumps = 0; G.pitObj = p; } }
    const g = GRAV * (!G.onGround && G.slideHeld && !G.bounce ? FASTFALL : 1);
    if (!G.onGround) {
      G.vy -= g * dt; G.y += G.vy * dt;
      if (G.y > MAXY) { G.y = MAXY; if (G.vy > 0) G.vy = 0; }        // the head bumps the ceiling
      if (G.y <= 0 && G.vy <= 0) {
        const p = G.boost > 0 ? null : pitAt(G.x);                    // boosting, you run straight over holes
        if (!p && G.y > -5) { G.y = 0; G.vy = 0; G.onGround = true; G.jumps = 0; G.bounce = false; G.pitObj = null; G.pitHoldT = 0; puff(G.x - 6, 3); }
        else if (!p) fallOut(G.pitObj || { x: G.x - 20, w: 0 });         // under the floor past the hole: its far wall
        else {                                               // down in it: to the bottom, a moment there, then thrown out
          G.pitObj = p;
          if (G.y <= -PIT_DEPTH) { G.y = -PIT_DEPTH; G.vy = 0; if (!G.pitHoldT) G.pitHoldT = G.t; if (G.t - G.pitHoldT >= PIT_HOLD) fallOut(p); }
        }
      }
    }
    const wasSlide = G.slide;
    G.slide = G.slideHeld && G.onGround && !busy();
    if (G.slide && !wasSlide) SND.play('slide');
    }
    // health
    if (!busy()) { G.hp = Math.max(0, G.hp - DRAIN * dt); G.runT += dt; }     // (v57: the running time, for the heals)
    G.invul = Math.max(0, G.invul - dt);
    // hits
    const b = playerBox();
    if (G.invul <= 0 && !(G.boost > 0)) for (const o of G.obs) {
      if (o.hit || o.x > b[2] + 40 || o.kind === 'pit') continue;
      let touch = false;
      if (o.kind === 'door' || o.kind === 'spike' || o.kind === 'drop' || o.kind === 'shot') {
        for (const [ox0, oy0, ox1, oy1] of obsBoxes(o)) if (b[0] < ox1 && b[2] > ox0 && b[1] < oy1 && b[3] > oy0) touch = true;
      } else {
        const hb = M.sprites[o.name].hb;
        const ox0 = o.x + hb[0], oy0 = o.y + hb[1], ox1 = o.x + hb[2], oy1 = o.y + hb[3];
        touch = b[0] < ox1 && b[2] > ox0 && b[1] < oy1 && b[3] > oy0;
      }
      if (touch) {
        o.hit = true; G.hits++; G.hp = Math.max(0, G.hp - HIT); G.invul = INVUL; G.slow = 0; G.nudge = 14; SND.play('hit');
        G.lastHit = { kind: o.kind, name: o.name, dx: Math.round(o.x - G.x), y: Math.round(G.y), vy: Math.round(G.vy), slide: G.slide, jumps: G.jumps, v: Math.round(G.v) };
        break;
      }
    }
    // the booster's magnet: what comes within MAG_R is caught and drawn in (and finishes coming even if the boost ends)
    {
      const pcy = GY + 1 - G.y - SH('ch_' + G.char) * (G.slide ? 0.31 : 0.5);
      for (const it of G.items) {
        if (it.taken) continue;
        if (!it.mag && (G.boost > 0 || G.magR)) { const R = G.boost > 0 ? MAG_R : G.magR, dx = it.x - G.x, dy = it.y - pcy; if (dx * dx + dy * dy < R * R && dx > -40) { it.mag = true; it.magT = 0; } }     // (v60: or the start item's smaller one)
        if (it.mag) { it.magT += dt; const q = Math.min(1, dt * (7 + 40 * it.magT)); it.x += (G.x - it.x) * q; it.y += (pcy - it.y) * q; }
      }
    }
    // eating
    for (const it of G.items) {
      if (it.taken || it.x < b[0] - 12 || it.x > b[2] + 12) continue;
      const cx = (b[0] + b[2]) / 2, cy = (b[1] + b[3]) / 2;
      if (Math.abs(it.x - cx) < (b[2] - b[0]) / 2 + 6 && Math.abs(it.y - cy) < (b[3] - b[1]) / 2 + 6) {
        it.taken = true; it.t = G.t;
        if (it.kind === 'heal') G.hp = Math.min(G.hpMax, G.hp + HEAL);
        if (it.kind !== 'heal' && !(G.boost > 0) && !busy() && ++G.o2n >= boostNeed()) startBoost();     // everything but the heal counts
        G.score += PTS[it.kind]; G.itemPts += PTS[it.kind]; G.eaten++; if (it.kind === 'atp') G.atp = (G.atp || 0) + 1;
        SND.play(it.kind === 'heal' ? 'heal' : it.kind === 'atp' ? 'atp' : PTS[it.kind] >= 30 ? 'special' : 'coin');
        if (PTS[it.kind] >= 30 || it.kind === 'heal') G.pops.push({ x: it.x, y: it.y - 8, s: it.kind === 'heal' ? '+' + HEAL : '+' + PTS[it.kind], t: G.t });
      }
    }
    if (G.onGround && !G.slide && !inWater() && Math.floor(G.t * 8) !== Math.floor((G.t - dt) * 8)) puff(G.x - 10, 1);
    G.puffs = G.puffs.filter((p) => G.t - p.t < 0.45);
    G.pops = G.pops.filter((p) => G.t - p.t < 0.8);
    // where we are
    const s = stationAt(G.x);
    if (s.i !== G.station) {
      const arrived = G.station < 0 || COURSE[G.station][5] !== s.st[5];       // a new place (not just a new look in it)
      G.station = s.i;
      const th = s.st[3];
      if (th !== G.theme) {
        G.prevTheme = G.theme; G.theme = th; G.fade = G.cut && G.cut.swap ? 1 : 0;      // (out of the anus: straight in)
        if (S2_L.has(th) && !S2_L.has(G.prevTheme)) G.wPen = 0.3 * G.v;                 // into the water: 30% slower from here
        else if (!S2_L.has(th)) G.wPen = 0;
      }
      if (!themeFiles(th).every((f) => bmp[f])) { G.missing = (G.missing || 0) + 1; (G.missList = G.missList || []).push(th); }   // (tests: a look not ready on arrival)
      if (arrived) { if (!busy()) G.banner = G.t; setLabel(s.st, s.lap); if (s.st[0] === 'ra' && !busy()) startRhythm(); if (s.st[0] === 'vertebral' && !busy()) startOrbit(); if (s.st[0] === 'jejunum' && !busy()) startBaseball();
        if (s.st[0] === 'spleen' && !busy()) startWhack(); if (s.st[0] === 'hippocampus' && !busy()) startMemory(); if (s.st[0] === 'manhole' && !busy()) startPK(); if (s.st[0] === 'combined' && !busy()) startYB(); if (s.st[0] === 'clarifier1' && !busy()) startTW(); if (s.st[0] === 'outfall' && !busy()) startAR(); }
      manageThemes(); G.memT = G.t;
    }
    // (v44) the toilet jackpot: in the toilet bowl, once the flush has settled (arriving there is in the cut scene)
    if (!busy() && !G.cutTail && G.station >= 0 && COURSE[G.station][0] === 'toiletBowl' && G.slLap !== stationAt(G.x).lap) startSlot();
    G.fade = Math.min(1, G.fade + dt / 0.7);
    if (!(G.t - G.memT < 0.5)) { G.memT = G.t; manageThemes(); }
    // passing the cornea the eye blinks now and then (sometimes twice quickly); its own random, so the course is unchanged
    if (COURSE[G.station][0] === 'cornea') {
      if (G.blinkAt < 0) G.blinkAt = G.t + 0.6;
      else if (G.t > G.blinkAt + BLINK) G.blinkAt = G.t + (G.blinkR() < 0.25 ? 0.12 : 0.9 + G.blinkR() * 1.5);
    } else G.blinkAt = -1;
    if (G.hp <= 0 && !NO_DEATH_TEST && !SET.god) gameOver();       // (v49: the settings' debug switch keeps you alive)
    if (!busy()) spawnAhead();
  }
  function playerBox() {
    const x = G.x, feet = GY - G.y;
    return G.slide ? [x - SLW, GY - SLH, x + SLW, GY] : [x - PW, feet - PH, x + PW, feet];
  }
  function startBoost() {
    G.boost = BOOST_T; G.boostT0 = G.t; G.o2n = 0; G.boosts++; G.slow = 1; G.nudge = 0;
    if (AUTO) G.slideHeld = false;
    for (let i = 0; i < 16; i++) addSpark(true);
  }
  // a mini-game (rhythm, orbit) arriving mid-boost: what is left of the boost is kept, and lit again when it ends
  function holdBoost() { if (G.boost > 0) G.boostHeld = G.boost; G.boost = 0; }
  function resumeBoost() {
    if (!(G.boostHeld > 0)) return;
    G.boost = G.boostHeld; G.boostHeld = 0; G.boostT0 = G.t; G.slow = 1; G.nudge = 0;
    if (AUTO) G.slideHeld = false;
    for (let i = 0; i < 16; i++) addSpark(true);
  }
  // fire behind the body while boosting: embers and smoke thrown back (in screen units, their own random)
  function addSpark(burst) {
    const R = G.fxR, n = 'ch_' + G.char, w = SW(n), h = G.slide ? slideH(SH(n)) : SH(n);
    const smoke = !burst && R() < 0.22;
    G.fire.push({ x: PX - w * 0.38 + R() * 4, y: GY + 1 - G.y - h * (0.25 + 0.5 * R()), vx: -(70 + R() * (burst ? 160 : 110)), vy: (R() - 0.5) * (burst ? 90 : 36) - 10,
      age: 0, life: smoke ? 0.55 + R() * 0.2 : 0.22 + R() * 0.2, r: smoke ? 2.2 + R() * 1.5 : 0.7 + R() * 1.1, smoke });
  }
  function stepFire(dt) {
    if (G.boost > 0) {
      G.fireAcc = (G.fireAcc || 0) + dt * 130; while (G.fireAcc >= 1) { addSpark(false); G.fireAcc -= 1; }
      const h = G.slide ? slideH(SH('ch_' + G.char)) : SH('ch_' + G.char);
      G.trail = (G.trail || []).filter((q) => G.t - q.t < 0.5); G.trail.push({ t: G.t, y: GY + 1 - G.y - h * 0.5 });
    } else if (G.trail && G.trail.length) G.trail = [];
    for (const p of G.fire) { p.age += dt; p.x += p.vx * dt; p.y += p.vy * dt; p.vy -= (p.smoke ? 22 : 8) * dt; }
    if (G.fire.length) G.fire = G.fire.filter((p) => p.age < p.life);
  }
  // a tongue of fire streaming back from (ax, ay): L long, H tall at the body, wavy, to a point
  function flamePath(ax, ay, L, H, ph) {
    const w1 = Math.sin(ph * 1.7) * H * 0.12, w2 = Math.sin(ph * 2.3 + 1) * H * 0.16, tipY = ay + Math.sin(ph * 1.3) * H * 0.22;
    ctx.beginPath();
    ctx.moveTo(ax + H * 0.12, ay - H / 2);
    ctx.bezierCurveTo(ax - L * 0.32, ay - H * 0.66 + w1, ax - L * 0.72, ay - H * 0.22 + w2, ax - L, tipY);
    ctx.bezierCurveTo(ax - L * 0.72, ay + H * 0.28 - w2, ax - L * 0.32, ay + H * 0.62 - w1, ax + H * 0.12, ay + H / 2);
    ctx.quadraticCurveTo(ax + H * 0.42, ay, ax + H * 0.12, ay - H / 2);
    ctx.closePath();
  }
  // ------------------------------------------------ the booster's fire, five looks (FIRE_STYLE)
  const hash = (a, b) => { const v = Math.sin(a * 127.1 + b * 311.7) * 43758.5453; return v - Math.floor(v); };
  function glowAt(x, y, r, rgb, a) {
    const g = ctx.createRadialGradient(x, y, 0.5, x, y, r); g.addColorStop(0, `rgba(${rgb},${a})`); g.addColorStop(1, `rgba(${rgb},0)`);
    ctx.fillStyle = g; ctx.beginPath(); ctx.arc(x, y, r, 0, 6.29); ctx.fill();
  }
  function star4(x, y, r, rot) {
    ctx.beginPath(); for (let i = 0; i < 8; i++) { const a = rot + i * Math.PI / 4, rr = i % 2 ? r * 0.3 : r; ctx.lineTo(x + Math.cos(a) * rr, y + Math.sin(a) * rr); } ctx.closePath();
  }
  function bolt(x0, y0, x1, y1, n, jit, seed) {
    ctx.beginPath(); ctx.moveTo(x0, y0);
    for (let i = 1; i < n; i++) { const t = i / n; ctx.lineTo(x0 + (x1 - x0) * t + (hash(seed, i) - 0.5) * jit, y0 + (y1 - y0) * t + (hash(seed + 7, i) - 0.5) * jit); }
    ctx.lineTo(x1, y1);
  }
  // the main flame: two side tongues, then four layers from the outside in (cols: outer .. core)
  function flameStack(ax, ay, L, H, ph, cols, outline) {
    for (const [dy, kl, kh, off] of [[-0.34, 0.66, 0.5, 2.1], [0.32, 0.58, 0.45, 4.2]]) {
      flamePath(ax - 1, ay + dy * H, L * kl, H * kh, ph + off); ctx.fillStyle = cols[1]; ctx.fill();
      ctx.lineWidth = 0.8; ctx.strokeStyle = outline; ctx.stroke();
    }
    [[1.0, 1.0], [0.8, 0.78], [0.58, 0.56], [0.34, 0.34]].forEach(([kl, kh], i) => {
      flamePath(ax + (1 - kl) * 2, ay, L * kl, H * kh, ph + i * 0.9); ctx.fillStyle = cols[i]; ctx.fill();
      if (i === 0) { ctx.lineWidth = 0.9; ctx.strokeStyle = outline; ctx.stroke(); }
    });
  }
  const WARM = ['#e8321a', '#ff7a1e', '#ffc23a', '#fff6c8'], BLUE = ['#1c36e8', '#2f8bff', '#8fe6ff', '#ffffff'];
  // where the body was a moment ago (the trails follow it), a: seconds back
  function pastY(a, now) {
    const tr = G.trail || [], t = G.t - a;
    for (let i = tr.length - 1; i >= 0; i--) if (tr[i].t <= t) return tr[i].y;
    return tr.length ? tr[0].y : now;
  }
  function speedLines(k) {
    ctx.lineCap = 'round';
    for (let i = 0; i < 9; i++) {
      const ph = (G.t * 2.6 + hash(i, 3)) % 1, y = 26 + hash(i, Math.floor(G.t * 2.6 + hash(i, 3))) * 118, x = NWf * (1.15 - ph * 1.5), L = 26 + hash(i, 9) * 40;
      ctx.strokeStyle = `rgba(255,255,255,${0.5 * k * Math.sin(ph * Math.PI)})`; ctx.lineWidth = 1.2;
      ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x + L, y); ctx.stroke();
    }
  }
  function afterImages(sx, feet, w, h, k, n) {
    const nm = 'ch_' + G.char;
    for (let j = n; j >= 1; j--) {
      const y = pastY(j * 0.05, feet - h * 0.5) + h * 0.5;
      if (G.slide) spr(nm, sx - j * 9 - w * 1.12 / 2, GY + 1 - h, 0.38 * k * (1 - j / (n + 1.5)), w * 1.12, h);
      else spr(nm, sx - j * 9 - w / 2, y - h, 0.42 * k * (1 - j / (n + 1.5)));
    }
  }
  // ---- the rainbow look (5): a glossy six-band ribbon following where you were, outlined like everything else,
  // stars twinkling along it, rainbow-tinted afterimages, a prism flame at the back
  const RAINBOW = ['#ff4a5e', '#ff9a2a', '#ffe14a', '#4ad66a', '#3aa0ff', '#9a5aff'];
  const tintCache = {};
  // v38: what hurts and what you eat told apart at a glance: every obstacle has a red rim (a bright line round its
  // outline and a faint glow beyond), every item a soft light round it that breathes and now and then a twinkle.
  // The rim is made once per picture (at half its resolution: it is soft anyway) and dropped with the picture
  const RIM = 0.85, RIM2 = 1.9;
  function rimOf(name) {
    if (rimCache[name]) return rimCache[name];
    const s0 = M.sprites[name]; if (!s0) return null; const im = bmp[s0.f]; if (!im) return null;
    const k = (s0.r[2] / s0.w) / 2, w = Math.max(1, Math.round(s0.r[2] / 2)), h = Math.max(1, Math.round(s0.r[3] / 2));
    const pad = Math.ceil(RIM2 * k) + 2;
    const sil = document.createElement('canvas'); sil.width = w; sil.height = h;
    const sx = sil.getContext('2d'); sx.drawImage(im, s0.r[0], s0.r[1], s0.r[2], s0.r[3], 0, 0, w, h);
    sx.globalCompositeOperation = 'source-in'; sx.fillStyle = '#ff2a2a'; sx.fillRect(0, 0, w, h);
    const c = document.createElement('canvas'); c.width = w + 2 * pad; c.height = h + 2 * pad;
    const x = c.getContext('2d');
    for (const [rad, a] of [[RIM2 * k, 0.22], [RIM * k, 1]]) {
      x.globalAlpha = a;
      for (let i = 0; i < 16; i++) { const t = i / 16 * 6.2832; x.drawImage(sil, pad + Math.cos(t) * rad, pad + Math.sin(t) * rad); }
    }
    x.globalAlpha = 1; x.globalCompositeOperation = 'destination-out'; x.drawImage(sil, pad, pad);   // (round it, not on it)
    return (rimCache[name] = { c, pad: pad / k, f: s0.f });
  }
  function rim(name, x, y, w = null, h = null) {                // drawn just before the obstacle's own picture
    const r = rimOf(name); if (!r) return;
    const s0 = M.sprites[name], fx = (w ?? s0.w) / s0.w, fy = (h ?? s0.h) / s0.h;
    ctx.drawImage(r.c, x - r.pad * fx, y - r.pad * fy, (s0.w + 2 * r.pad) * fx, (s0.h + 2 * r.pad) * fy);
  }
  const rspr = (name, x, y, alpha = 1, w = null, h = null) => { rim(name, x, y, w, h); spr(name, x, y, alpha, w, h); };
  let glowC = null;
  function glowOf() {
    if (glowC) return glowC;
    const c = document.createElement('canvas'); c.width = c.height = 64; const x = c.getContext('2d');
    const g = x.createRadialGradient(32, 32, 0, 32, 32, 32);
    g.addColorStop(0, 'rgba(255,250,215,0.95)'); g.addColorStop(0.45, 'rgba(255,240,170,0.45)'); g.addColorStop(1, 'rgba(255,240,170,0)');
    x.fillStyle = g; x.fillRect(0, 0, 64, 64);
    return (glowC = c);
  }
  function itemGlow(cx, cy, size, ph) {                          // the light round an item and its twinkle
    const a = 0.42 + 0.18 * Math.sin(G.t * 5 + ph), d = size * 2.1;
    ctx.globalAlpha = a * GA; ctx.drawImage(glowOf(), cx - d / 2, cy - d / 2, d, d); ctx.globalAlpha = GA;
    const q = ((G.t * 0.7 + ph / 6.2832) % 1 + 1) % 1;
    if (q < 0.16) {
      const k = Math.sin(q / 0.16 * Math.PI), r = size * 0.42 * k, tx = cx - size * 0.32, ty = cy - size * 0.36;
      ctx.beginPath();
      for (let i = 0; i < 8; i++) { const ang = i * Math.PI / 4, rr = i % 2 ? r * 0.22 : r; ctx.lineTo(tx + Math.cos(ang) * rr, ty + Math.sin(ang) * rr); }
      ctx.closePath(); ctx.fillStyle = '#ffffff'; ctx.globalAlpha = 0.95 * GA; ctx.fill(); ctx.globalAlpha = GA;
    }
  }
  function tinted(name, col) {                       // the sprite as a coloured silhouette (cached)
    const key = name + col; if (tintCache[key]) return tintCache[key];
    const s0 = M.sprites[name], im = bmp[s0.f]; if (!im) return null;
    const c = document.createElement('canvas'); c.width = s0.r[2]; c.height = s0.r[3];
    const x = c.getContext('2d'); x.drawImage(im, s0.r[0], s0.r[1], s0.r[2], s0.r[3], 0, 0, s0.r[2], s0.r[3]);
    x.globalCompositeOperation = 'source-atop'; x.globalAlpha = 0.72; x.fillStyle = col; x.fillRect(0, 0, c.width, c.height);
    x.globalAlpha = 0.35; x.fillStyle = '#ffffff'; x.fillRect(0, 0, c.width, c.height * 0.45);
    return (tintCache[key] = c);
  }
  // the rainbow fire itself is the user's 8-frame sheet (fx_rb0..7): it lights up over frames 0-4, then flickers
  // 4-5-6-7-6-5; drawn long behind the body (its head at your back), tilting with the jump, with two fading copies of
  // it trailing where you were a moment ago and rainbow-tinted afterimages of the body
  const RB_LOOP = [4, 5, 6, 7, 6, 5];
  function rbFrame(since) { return since < 0.3 ? Math.min(4, Math.floor(since / 0.075)) : RB_LOOP[Math.floor((since - 0.3) * 14) % RB_LOOP.length]; }
  function drawRainbow(sx, feet, w, h, k, ax, cy, ph) {
    const s0 = M.sprites.fx_rb0; if (!s0) return;
    const since = G.t - G.boostT0, fade = Math.min(1, G.boost / 0.35);
    const Wd = w * 3.8, Hd = Wd * (s0.h / s0.w) * 0.6, headY = 0.44;
    const tilt = G.onGround ? 0 : Math.max(-0.4, Math.min(0.4, -G.vy / 900 * 0.6));
    const draw = (fr, x, y, a, th) => { ctx.save(); ctx.translate(x, y); ctx.rotate(th); spr('fx_rb' + fr, -Wd, -Hd * headY, a, Wd, Hd); ctx.restore(); };
    const hx = sx - w * 0.1;
    glowAt(hx - Wd * 0.3, cy, Wd * 0.55, '255,236,255', 0.22 * fade);
    // copies of the fire trailing behind, from earlier in its flicker
    for (let j = 2; j >= 1; j--) {
      const fr = since < 0.3 ? rbFrame(Math.max(0, since - j * 0.08)) : RB_LOOP[(Math.floor((since - 0.3) * 14) + 6 - j * 2) % 6];
      draw(fr, hx - j * Wd * 0.22, pastY(j * 0.07, cy), (j === 1 ? 0.38 : 0.18) * fade, tilt * (1 - 0.3 * j));
    }
    // rainbow-tinted afterimages of the body
    const nm = 'ch_' + G.char;
    for (let j = 3; j >= 1; j--) {
      const c = tinted(nm, RAINBOW[(j * 2 + Math.floor(G.t * 10)) % 6]); if (!c) break;
      const yy = pastY(j * 0.045, cy) + h * 0.5, ww = G.slide ? w * 1.12 : w;
      ctx.globalAlpha = 0.45 * k * (1 - j / 4.2); ctx.drawImage(c, sx - j * 9 - ww / 2, (G.slide ? GY + 1 : yy) - h, ww, h); ctx.globalAlpha = 1;
    }
    draw(rbFrame(since), hx, cy, fade, tilt);
  }
  // (v61) the magnet's look: the user's golden whirl (fx_mag.webp, hdart/magnet_user.py) turning clockwise round the
  // runner, for the start item's magnet and (quicker, fully bright) the booster's. Drawn behind the obstacles and the
  // things to pick up, so it never hides one. (v62) sized to the runner, not to the reach (45, 80: unchanged): its outer
  // edge MAG_FX_K times the runner's longer side from the middle, so the hole in it (about half) sits round the body
  const MAG_FX_K = 0.8;
  function drawField(cam) {
    const n = 'ch_' + G.char, h0 = SH(n), h = G.slide ? slideH(h0) : h0;
    const sx = PX - G.nudge + cutDX() + cutShake(), cy = GY + 1 - G.y - h * 0.5;
    const kb = G.boost > 0 ? Math.min(1, (G.t - G.boostT0) / 0.2) * Math.min(1, G.boost / 0.35) : 0;
    const ki = G.magR && !busy() ? 1 : 0;
    if (kb <= 0 && ki <= 0) return;
    const R = Math.max(SW(n), h0) * MAG_FX_K * (ki ? 1 : 0.7 + 0.3 * kb) * (1 + 0.025 * Math.sin(G.t * 5));
    const D = R * 2 * 1.04;                                   // (the picture has a little room round the whirl)
    ctx.save(); ctx.translate(sx, cy); ctx.rotate(G.magA || 0);
    spr('fx_mag', -D / 2, -D / 2, Math.max(ki * 0.85, kb), D, D);
    ctx.restore();
  }
  function drawFire(sx, feet, w, h) {
    const on = G.boost > 0, k = on ? Math.min(1, (G.t - G.boostT0) / 0.15) * Math.min(1, G.boost / 0.35) : 0;
    const st = FIRE_STYLE, cy = feet - h * 0.5, ph = G.t * 22;
    if (k > 0 && (st === 1 || st === 5)) speedLines(k);
    // smoke behind everything (the warm looks only)
    if (st === 1 || st === 3) for (const p of G.fire) {
      const u = p.age / p.life;
      if (p.smoke) { ctx.fillStyle = `rgba(70,50,50,${0.26 * (1 - u)})`; ctx.beginPath(); ctx.arc(p.x - G.nudge, p.y, p.r * (1 + u * 1.6), 0, 6.29); ctx.fill(); }
    }
    if (k > 0) {
      const ax = sx - w * 0.3;
      if (st === 1) {                                       // rocket flame: long, layered, a big warm glow
        const L = (w * 2.3 + 6 * Math.sin(G.t * 31)) * k, H = h * 1.05;
        glowAt(ax - L * 0.35, cy, L * 1.1, '255,150,40', 0.5 * k);
        flameStack(ax, cy, L, H, ph, WARM, 'rgba(122,20,4,0.95)');
        for (let i = 0; i < 10; i++) {                       // spark streaks shooting back
          const u = (G.t * 4 + hash(i, 1)) % 1, y = cy + (hash(i, 2) - 0.5) * H * 1.2, x = ax - 6 - u * L * 1.4;
          ctx.strokeStyle = `rgba(255,236,160,${0.9 * (1 - u)})`; ctx.lineWidth = 0.9; ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x - 7, y); ctx.stroke();
        }
      } else if (st === 2) {                                // comet: a long glowing tail following where you were, stars in it
        afterImages(sx, feet, w, h, k, 3);
        const AMAX = 0.45, SP = 165 * k, stops = [[255, 255, 235], [255, 222, 90], [255, 140, 40], [235, 60, 70], [170, 60, 210]];
        glowAt(ax - 24, cy, 60 * k, '255,170,60', 0.45 * k);
        for (let i = 30; i >= 0; i--) {
          const a = AMAX * i / 30, q = a / AMAX, f = q * (stops.length - 1), j = Math.min(stops.length - 2, Math.floor(f)), m = f - j;
          const c = stops[j].map((v, n) => Math.round(v + (stops[j + 1][n] - v) * m));
          const r = h * 0.7 * Math.pow(1 - q, 0.7) + 0.6;
          ctx.fillStyle = `rgba(${c[0]},${c[1]},${c[2]},${0.85 * Math.pow(1 - q, 0.5) * k})`;
          ctx.beginPath(); ctx.arc(ax - a * SP, pastY(a, cy) + Math.sin(a * 30 - G.t * 14) * 1.2, r, 0, 6.29); ctx.fill();
        }
        for (let i = 0; i < 12; i++) {
          const a = AMAX * ((G.t * 1.8 + hash(i, 5)) % 1), tw = 0.5 + 0.5 * Math.sin(G.t * 18 + i * 2);
          ctx.fillStyle = i % 2 ? '#ffffff' : '#fff2a0'; star4(ax - a * SP, pastY(a, cy) + (hash(i, 6) - 0.5) * h * 1.3, 1.5 + 2.8 * tw, G.t * 3 + i); ctx.fill();
        }
        flameStack(ax + 2, cy, w * 0.75 * k, h * 0.7, ph, ['#ff9a2a', '#ffc23a', '#fff0a0', '#ffffff'], 'rgba(150,60,10,0.9)');
      } else if (st === 3) {                                // the whole body on fire: tongues licking up all round, a trailing flame
        glowAt(sx, cy, w * 1.4, '255,120,30', 0.6 * k);
        const L = (w * 1.6 + 5 * Math.sin(G.t * 29)) * k;
        flameStack(ax, cy, L, h * 0.95, ph, WARM, 'rgba(122,20,4,0.95)');
        for (let i = 0; i < 11; i++) {                        // tongues on an arc round the body, leaning back and up
          const th = Math.PI * (0.5 + 1.1 * i / 10), bx = sx + Math.cos(th) * w * 0.46, by = cy - Math.sin(th) * h * 0.52;
          const ln = (13 + 8 * hash(i, Math.floor(G.t * 14))) * k, hh = 6.5 + 2.5 * Math.sin(G.t * 25 + i);
          ctx.save(); ctx.translate(bx, by); ctx.rotate(Math.atan2(-1, -0.55) - Math.PI + 0.25 * Math.sin(G.t * 9 + i));
          flamePath(0, 0, ln, hh, ph + i); ctx.fillStyle = '#ff6a1c'; ctx.fill(); ctx.lineWidth = 0.7; ctx.strokeStyle = 'rgba(122,20,4,0.9)'; ctx.stroke();
          flamePath(1, 0, ln * 0.6, hh * 0.55, ph + i + 1); ctx.fillStyle = '#ffd04a'; ctx.fill();
          ctx.restore();
        }
      } else if (st === 4) {                                // blue plasma: a hot blue jet and crackling arcs
        const L = (w * 2.2 + 6 * Math.sin(G.t * 33)) * k, H = h * 1.0;
        glowAt(ax - L * 0.3, cy, L * 1.15, '80,170,255', 0.6 * k);
        flameStack(ax, cy, L, H, ph, BLUE, 'rgba(10,26,110,0.95)');
        const seed = Math.floor(G.t * 16);
        ctx.lineJoin = 'round';
        for (let i = 0; i < 6; i++) {
          const x0 = ax + 2, y0 = cy + (hash(seed, i) - 0.5) * H * 0.8;
          const x1 = ax - 14 - hash(seed, i + 9) * L * 0.9, y1 = cy + (hash(seed, i + 19) - 0.5) * H * 2.2;
          bolt(x0, y0, x1, y1, 6, 7, seed * 13 + i); ctx.strokeStyle = 'rgba(120,220,255,0.55)'; ctx.lineWidth = 2.4 * k; ctx.stroke();
          bolt(x0, y0, x1, y1, 6, 7, seed * 13 + i); ctx.strokeStyle = '#ffffff'; ctx.lineWidth = 0.8; ctx.stroke();
        }
      } else {                                              // rainbow starlight
        drawRainbow(sx, feet, w, h, k, ax, cy, ph);
      }
    }
    // embers on top of the flame, in the look's colours
    for (const p of G.fire) {
      if (p.smoke) continue;
      const u = p.age / p.life;
      if (st === 4) ctx.fillStyle = u < 0.4 ? '#ffffff' : u < 0.75 ? '#8fe6ff' : '#2f8bff';
      else if (st === 5) {
        const c = RAINBOW[Math.floor(hash(p.r * 97, 1) * 6)];
        ctx.globalAlpha = 1 - u * u; star4(p.x - G.nudge, p.y, (p.r + 0.9) * (1 - u * 0.4), G.t * 6 + p.r * 9);
        ctx.fillStyle = u < 0.3 ? '#ffffff' : c; ctx.fill(); ctx.globalAlpha = 1; continue;
      }
      else ctx.fillStyle = u < 0.35 ? '#fff2b0' : u < 0.7 ? '#ffb030' : '#e8481c';
      ctx.globalAlpha = 1 - u * u; ctx.beginPath(); ctx.arc(p.x - G.nudge, p.y, p.r * (1 - u * 0.5), 0, 6.29); ctx.fill(); ctx.globalAlpha = 1;
    }
  }
  function puff(x, n) { for (let i = 0; i < n; i++) G.puffs.push({ x: x - i * 4, y: GY - 2 - G.R() * 3, r: 1.5 + G.R() * 1.5, t: G.t }); }

  // ---------------------------------------------------------------- drawing
  // a tiled layer: three one-screen chunks per tile (stacked in its picture, with gutters); each chunk placed on
  // whole screen pixels so neighbours meet without a seam
  function drawLayer(theme, key, par, alpha) {
    const th = M.themes[theme]; if (!th) return false;
    let fn, rowY, rowH, wy;
    if (key === 'far') { fn = th.far; rowY = 0; rowH = th.farH; wy = 0; }
    else if (key === 'mid') { if (!th.mid) return true; fn = th.mid; rowY = 0; rowH = th.midH; wy = 0; }
    else if (key === 'floor') { fn = th.fx; rowY = th.floor.y; rowH = th.floor.h; wy = M.FY0; }
    else { if (!th.ceil) return true; fn = th.fx; rowY = th.ceil.y; rowH = th.ceil.h; wy = 0; }
    const im = bmp[fn]; if (!im) return false;
    const g = M.G, cwp = M.CW * M.SC, cell = rowH + 2 * g;
    const off = mod((G.x - PX) * par, M.WT);
    const dy0 = Math.round(wy * RS), dy1 = Math.round((wy + rowH / M.SC) * RS);
    if (alpha !== 1) ctx.globalAlpha = alpha;
    for (let tx = -off; tx < NWf; tx += M.WT) {
      for (let c = 0; c < 3; c++) {
        const x0 = tx + c * M.CW, x1 = x0 + M.CW;
        if (x1 <= 0 || x0 >= NWf) continue;
        const dx0 = Math.round(x0 * RS), dx1 = Math.round(x1 * RS);
        ctx.drawImage(im, g, rowY + c * cell + g, cwp, rowH, dx0, dy0, dx1 - dx0, dy1 - dy0);
      }
    }
    if (alpha !== 1) ctx.globalAlpha = 1;
    return true;
  }
  function drawScene() {
    const a = G.fade, th = G.theme, pv = G.prevTheme;
    const fading = pv && a < 1;
    device();
    // the far wall: if its picture is not ready yet, the theme's colour
    if (!(fading && drawLayer(pv, 'far', 0.35, 1)) && !bmp[M.themes[th].far]) { ctx.fillStyle = M.themes[th].bg || '#2a0c14'; ctx.fillRect(0, 0, GW, GH); }
    drawLayer(th, 'far', 0.35, fading ? a : 1);
    if (fading) drawLayer(pv, 'mid', 0.65, 1 - a);
    drawLayer(th, 'mid', 0.65, fading ? a : 1);
    const cam = G.x - PX;
    // hanging things go behind the ceiling band (they grow out of it); doors' lips and spikes come out of the walls
    world();
    for (const o of G.obs) {
      const sx = o.x - cam; if (sx >= NWf || sx + o.w <= 0) continue;
      curO = o;
      if (o.kind === 'hang') rspr(o.name, sx, o.y);
      else if (o.kind === 'door') drawDoor(o, sx);
      else if (o.kind === 'spike' && o.e > 0) rspr(o.name, sx, o.y);
      else if (o.kind === 'drop' && o.st === 'hang') {          // swelling on the ceiling, wobbling before it lets go
        const wob = o.wob ? Math.min(1, o.wob / 0.3) : 0, k = 1 + wob * (0.18 + 0.07 * Math.sin(G.t * 34));
        const w = SW(o.nd), h = SH(o.nd);
        rspr(o.nd, sx + (o.w - w / (0.92 + 0.08 * k)) / 2, DROP_Y0, 1, w / (0.92 + 0.08 * k), h * k);
      }
    }
    curO = null; device();
    const pits = G.obs.filter((o) => o.kind === 'pit' && o.x - cam < NWf + 6 && o.x + o.w - cam > -6);
    if (fading) drawLayer(pv, 'ceil', 1, 1);
    drawLayer(th, 'ceil', 1, fading ? a : 1);
    if (pits.length) {                                       // the floor is not drawn over the holes
      ctx.save(); world(); ctx.beginPath(); ctx.rect(-10, M.FY0 - 4, NWf + 20, NH - M.FY0 + 10);
      for (const o of pits) ctx.rect(o.x - cam + 1.2, M.FY0 - 4, o.w - 2.4, NH - M.FY0 + 10);
      ctx.clip('evenodd'); device();
    }
    if (fading) drawLayer(pv, 'floor', 1, 1);
    drawLayer(th, 'floor', 1, fading ? a : 1);
    if (pits.length) ctx.restore();
    world();
    for (const o of pits) drawPit(o, o.x - cam);
    if ((G.cut && G.cut.swap) ? G.cut.landed : (!G.orb || (G.orb.st === 'done' && G.t - G.orb.stT > OB_DONE - 0.35))) drawField(cam);   // (v61) the magnet's whirl, behind the obstacles
    ctx.fillStyle = 'rgba(0,0,0,0.26)';
    for (const o of G.obs) if (o.kind === 'low' || o.kind === 'tall' || o.kind === 'huge') { const sx = o.x - cam; if (sx < NWf && sx + o.w > 0) { ctx.beginPath(); ctx.ellipse(sx + o.w / 2, GY + 0.6, o.w * 0.46, 1.9, 0, 0, 6.29); ctx.fill(); } }
    for (const o of G.obs) {
      const sx = o.x - cam; if (sx >= NWf + 30 || sx + o.w <= -30) continue;
      curO = o;
      if (o.kind === 'hang' || o.kind === 'door' || o.kind === 'pit') continue;
      if (o.kind === 'spike') { if (o.st === 'warn' || (o.st === 'up' && G.t - o.popT < 0.25)) drawQuake(o, sx); continue; }
      if (o.kind === 'drop') { drawDrop(o, sx); continue; }
      if (o.kind === 'shot') {
        const w = SW(o.name), h = SH(o.name);
        ctx.save(); ctx.translate(sx + w / 2, o.y + h / 2); ctx.rotate(-o.spin); rspr(o.name, -w / 2, -h / 2); ctx.restore();
        continue;
      }
      if (TRIM[o.kind] && !window.__fitOff) {                    // (v51) a tower: smaller, from the floor (__fitOff: tests, as before)
        const f = (o.h - TRIM[o.kind]) / o.h, w2 = o.w * f, h2 = o.h * f;
        rspr(o.name, sx + (o.w - w2) / 2, o.y + o.h - h2, 1, w2, h2);
        continue;
      }
      rspr(o.name, sx, o.y);
    }
    curO = null;
    for (const it of G.items) {
      const sx = it.x - cam; if (sx < -20 || sx > NWf + 20) continue;
      const n = 'it_' + it.kind;
      if (it.taken) {
        const u = (G.t - it.t) / 0.18; if (u >= 1) continue;
        const k = 1 + u * 0.8; spr(n, sx - SW(n) * k / 2, it.y - SH(n) * k / 2, 1 - u, SW(n) * k, SH(n) * k); continue;
      }
      if (it.mag) {                                         // being pulled in: a short light streak behind it
        const px = PX - G.nudge, py = GY + 1 - G.y - SH('ch_' + G.char) * 0.5, dx = sx - px, dy = it.y - py, L = Math.hypot(dx, dy) || 1;
        const gr = ctx.createLinearGradient(sx, it.y, sx + dx / L * 16, it.y + dy / L * 16);
        gr.addColorStop(0, 'rgba(255,255,255,0.75)'); gr.addColorStop(1, 'rgba(255,255,255,0)');
        ctx.strokeStyle = gr; ctx.lineWidth = 2.2; ctx.lineCap = 'round';
        ctx.beginPath(); ctx.moveTo(sx, it.y); ctx.lineTo(sx + dx / L * 16, it.y + dy / L * 16); ctx.stroke();
        spr(n, sx - SW(n) / 2, it.y - SH(n) / 2); continue;
      }
      const by = Math.sin(G.t * 4 + it.ph);
      itemGlow(sx, it.y + by, Math.max(SW(n), SH(n)), it.ph || 0);
      spr(n, sx - SW(n) / 2, it.y - SH(n) / 2 + by);
    }
    // the player: a shadow, dust, the character (bobbing as it runs, squashed when sliding); not while on the orbit stage
    if ((G.cut && G.cut.landed) || G.cutTail) drawCutDrift();     // (v48: the big lump behind the runner as it lets go)
    if (G.cut && G.cut.swap) { if (!G.cut.landed) drawDive(); else drawPlayer(cam); }
    else if (!G.orb || (G.orb.st === 'done' && G.t - G.orb.stT > OB_DONE - 0.35)) drawPlayer(cam);
    drawCutBack(cam);
    if ((G.cut && G.cut.landed) || G.cutTail) drawCutDriftPiece();
    drawShotWarnings(cam);
    for (const p of G.pops) { const u = (G.t - p.t) / 0.8; label(p.s, p.x - cam, Math.max(40, p.y - u * 14), 8, 'center', 1 - u * u); }
  }
  function drawPlayer(cam) {
    const n = 'ch_' + G.char, w = SW(n), h = SH(n);
    const sx = PX - G.nudge + cutDX() + cutShake();
    const shw = Math.max(6, w * (0.8 - Math.min(0.4, G.y / 120)));
    const overPit = pitAt(G.x);
    if (!overPit && G.y >= 0) { ctx.fillStyle = 'rgba(0,0,0,0.35)'; ctx.beginPath(); ctx.ellipse(sx, GY - 1, shw / 2, 1.6, 0, 0, 6.29); ctx.fill(); }
    const inPit = G.y < 0 && G.pitObj;
    if (inPit) { const p = G.pitObj; ctx.save(); ctx.beginPath(); ctx.rect(-10, -10, NWf + 20, GY + 10); ctx.rect(p.x - cam + 1, GY, p.w - 2, NH); ctx.clip(); }
    for (const p of G.puffs) { const u = (G.t - p.t) / 0.45; ctx.fillStyle = `rgba(255,235,240,${0.5 * (1 - u)})`; ctx.beginPath(); ctx.arc(p.x - cam, p.y - u * 4, p.r + u * 2, 0, 6.29); ctx.fill(); }
    drawFire(sx, GY + 1 - G.y, w, G.slide ? slideH(h) : h);
    const blink = G.invul > 0 && !(G.boost > 0) && Math.floor(G.t * 14) % 2 === 0;
    if (!blink) {
      if (G.slide) { const sh = slideH(h), sw = w * 1.12; spr(n, sx - sw / 2, GY + 1 - sh, 1, sw, sh); }
      else if (inWater()) {                               // swimming: tilted up as it rises, down as it sinks, a slow sway
        const ang = -Math.max(-0.32, Math.min(0.32, G.vy / 330)), cy = GY + 1 - G.y - h / 2 + Math.sin(G.t * 3) * 0.6;
        ctx.save(); ctx.translate(sx, cy); ctx.rotate(ang); spr(n, -w / 2, -h / 2); ctx.restore();
      } else { const bob = G.onGround ? (Math.floor(G.t * 10) % 2) : 0; spr(n, sx - w / 2, GY + 1 - h - G.y - bob); }
    }
    for (const b of G.swimBub || []) {                        // the bubbles it leaves swimming up
      const u = (G.t - b.t) / 0.7; if (u >= 1) continue;
      ctx.globalAlpha = 1 - u; ctx.beginPath(); ctx.arc(b.x - cam + Math.sin(u * 8 + b.r * 5) * 0.8, b.y - u * 16, b.r, 0, 6.29);
      ctx.fillStyle = 'rgba(235,252,252,0.55)'; ctx.fill(); ctx.lineWidth = 0.4; ctx.strokeStyle = '#2a5a62'; ctx.stroke(); ctx.globalAlpha = 1;
    }
    if (inPit) ctx.restore();
  }
  // a hole: the floor turns down at its edges (a lip of the floor's own colour), dark below
  function drawPit(o, x0) {
    const th = M.themes[G.theme], x1 = x0 + o.w;
    const fc = th.fc || '#a04050', fk = th.fk || '#5a1a28';
    const wob = (y, k) => 0.9 * Math.sin(y * 0.45 + o.seed + k * 2.1) + 0.5 * Math.sin(y * 1.3 + o.seed * 0.7 + k);
    const path = () => {
      ctx.beginPath(); ctx.moveTo(x0 - 3.2, GY - 0.6);
      ctx.quadraticCurveTo(x0 + 0.6, GY - 0.2, x0 + 1.2, GY + 5);
      for (let y = GY + 6; y <= NH + 2; y += 3) ctx.lineTo(x0 + 1.2 + wob(y, 0), y);
      ctx.lineTo(x1 - 1.2 + wob(NH + 2, 1), NH + 2);
      for (let y = NH + 2; y >= GY + 6; y -= 3) ctx.lineTo(x1 - 1.2 + wob(y, 1), y);
      ctx.lineTo(x1 - 1.2, GY + 5); ctx.quadraticCurveTo(x1 - 0.6, GY - 0.2, x1 + 3.2, GY - 0.6);
    };
    path(); ctx.lineJoin = 'round'; ctx.lineWidth = 4.4; ctx.strokeStyle = fc; ctx.stroke();      // the lip
    path(); ctx.closePath();
    const g = ctx.createLinearGradient(0, GY - 2, 0, NH);
    const s2 = S2_L.has(G.theme);                                   // (stage 2: a drain in porcelain, dark water down it)
    g.addColorStop(0, fk); g.addColorStop(0.18, s2 ? '#16343a' : '#2a0a12'); g.addColorStop(0.55, s2 ? '#081a1e' : '#0c0306'); g.addColorStop(1, s2 ? '#020a0c' : '#030102');
    ctx.fillStyle = g; ctx.fill();
    const sh = ctx.createLinearGradient(x0, 0, x1, 0);              // the far wall side a little lit
    sh.addColorStop(0, 'rgba(0,0,0,0.35)'); sh.addColorStop(0.7, 'rgba(0,0,0,0)'); sh.addColorStop(1, s2 ? 'rgba(200,255,255,0.06)' : 'rgba(255,200,200,0.06)');
    ctx.fillStyle = sh; ctx.fill();
    path(); ctx.lineWidth = 1.3; ctx.strokeStyle = '#1a0a14'; ctx.stroke();
  }
  function drawDoor(o, sx) {
    const st = M.sprites[o.nt], sb = M.sprites[o.nb];
    if (o.et > 0.004) rspr(o.nt, sx + (o.w - st.w) / 2, HANG_BOTTOM - st.h - DOOR_UP * (1 - o.et));
    if (o.eb > 0.004) rspr(o.nb, sx + (o.w - sb.w) / 2, GY + 4 - DOOR_B * o.eb);
  }
  // the floor over a spike about to come up: it shakes, cracks and spits bits
  function drawQuake(o, sx) {
    const th = M.themes[G.theme], u = G.t - (o.warnT || G.t), c = sx + o.w / 2;
    const k = Math.min(1, u / 0.15);
    ctx.strokeStyle = '#1a0a14'; ctx.lineWidth = 1.1; ctx.lineJoin = 'round';
    ctx.beginPath(); ctx.moveTo(c - o.w * 0.55 * k, GY + 0.5);
    for (let i = -2; i <= 2; i++) ctx.lineTo(c + i * o.w * 0.24 * k, GY + 0.5 + (i % 2 ? 1.6 : -0.4) * k);
    ctx.lineTo(c + o.w * 0.55 * k, GY + 0.5); ctx.stroke();
    // dust rising off it
    for (let i = 0; i < 4; i++) {
      const ph = (G.t * 2.2 + i * 0.25) % 1, hx = c + (i - 1.5) * o.w * 0.3;
      ctx.fillStyle = `rgba(255,236,240,${0.32 * (1 - ph) * k})`; ctx.beginPath(); ctx.arc(hx + ph * (i - 1.5) * 3, GY - 2 - ph * 9, 2 + ph * 3.5, 0, 6.29); ctx.fill();
    }
    // bits of the floor jumping
    ctx.fillStyle = th.fc || '#c86070';
    for (let i = 0; i < 7; i++) {
      const ph = (G.t * 6 + i * 0.29) % 1, hx = c + (i - 3) * o.w * 0.17 + Math.sin(i * 3.1) * 1.5;
      const hy = GY - 1 - 11 * Math.sin(ph * Math.PI) * (0.55 + 0.45 * ((i * 7) % 3) / 2);
      ctx.beginPath(); ctx.arc(hx, hy, 1.1 + (i % 3) * 0.35, 0, 6.29); ctx.fill();
      ctx.lineWidth = 0.55; ctx.stroke();
    }
  }
  function drawDrop(o, sx) {
    if (o.st === 'fall') {
      // its shadow on the floor, growing as it comes down
      const p = Math.min(1, (o.y - DROP_Y0) / (GY - SH(o.nd) - DROP_Y0));
      ctx.fillStyle = `rgba(0,0,0,${0.3 + 0.35 * p})`; ctx.beginPath(); ctx.ellipse(sx + o.w / 2, GY + 0.6, 4.5 + 7.5 * p, 1.5 + 0.9 * p, 0, 0, 6.29); ctx.fill();
      const w = SW(o.nd), h = SH(o.nd);
      rspr(o.nd, sx + (o.w - w) / 2, o.y, 1, w * 0.94, h * 1.08);
    } else if (o.st === 'land') {
      const u = Math.min(1, (G.t - o.landT) / 0.14), w = SW(o.np), h = SH(o.np);
      const kx = 1.25 - 0.25 * u, ky = 0.6 + 0.4 * u;
      rspr(o.np, sx + (o.w - w * kx) / 2, GY + 2 - h * ky, 1, w * kx, h * ky);
    } else if (o.wob) {                                       // a shadow even before it falls
      ctx.fillStyle = `rgba(0,0,0,${0.25 * Math.min(1, o.wob / 0.3)})`; ctx.beginPath(); ctx.ellipse(sx + o.w / 2, GY + 0.6, 4.5, 1.5, 0, 0, 6.29); ctx.fill();
    }
  }
  // an antibody about to fly in: a warning on the screen's edge at its height
  function drawShotWarnings(cam) {
    for (const o of G.obs) {
      if (o.kind !== 'shot' || o.moving) continue;
      const sx = o.x - cam; if (sx > NWf + 4 + G.v * 0.75) continue;
      const cy = o.y + o.h / 2, cx = o.low ? NWf - 58 : NWf - 11, pulse = 0.75 + 0.25 * Math.sin(G.t * 22);   // (low: left of the slide button)
      ctx.globalAlpha = pulse;
      ctx.beginPath(); ctx.arc(cx, cy, 7.2, 0, 6.29); ctx.fillStyle = '#1a0a14'; ctx.fill();
      ctx.beginPath(); ctx.arc(cx, cy, 6, 0, 6.29); ctx.fillStyle = '#ff4a5e'; ctx.fill();
      ctx.globalAlpha = 1;
      label('!', cx, cy + 0.4, 10, 'center', pulse, '#ffffff');
      ctx.beginPath(); ctx.moveTo(cx - 9.5, cy); ctx.lineTo(cx - 13.5, cy - 3); ctx.lineTo(cx - 13.5, cy + 3); ctx.closePath(); ctx.fillStyle = '#ff4a5e'; ctx.globalAlpha = pulse; ctx.fill(); ctx.globalAlpha = 1;
    }
  }
  // text with a dark edge (score, +points)
  function label(s, x, y, size, align = 'left', alpha = 1, fill = '#fff3c8') {
    alpha *= GA;
    if (alpha !== 1) ctx.globalAlpha = alpha;
    ctx.font = `900 ${size}px system-ui, -apple-system, "Noto Sans KR", sans-serif`;
    { const mw = NWf - 14, w = ctx.measureText(s).width; if (w > mw) { size *= mw / w; ctx.font = `900 ${size}px system-ui, -apple-system, "Noto Sans KR", sans-serif`; } }   // (v47) never off the screen
    ctx.textAlign = align; ctx.textBaseline = 'middle'; ctx.lineJoin = 'round';
    ctx.lineWidth = size * 0.28; ctx.strokeStyle = '#1a0a14'; ctx.strokeText(s, x, y);
    ctx.fillStyle = fill; ctx.fillText(s, x, y);
    if (alpha !== 1) ctx.globalAlpha = GA;
  }
  function rrect(x, y, w, h, r) { ctx.beginPath(); ctx.roundRect ? ctx.roundRect(x, y, w, h, r) : ctx.rect(x, y, w, h); }
  // the jump and slide buttons: a circle with its name in it (1.2 times the old arrow buttons)
  const BTN_R = 19.2, BTN_M = 8.5;                        // radius, the gap to the screen's edges
  function button(cx, cy, text, on) {
    const r = BTN_R;
    ctx.beginPath(); ctx.arc(cx, cy, r + 0.8, 0, 6.29); ctx.fillStyle = 'rgba(26,10,20,0.55)'; ctx.fill();
    ctx.beginPath(); ctx.arc(cx, cy, r, 0, 6.29); ctx.fillStyle = on ? 'rgba(255,214,110,0.45)' : 'rgba(255,255,255,0.2)'; ctx.fill();
    ctx.lineWidth = 1.3; ctx.strokeStyle = on ? 'rgba(255,230,160,0.95)' : 'rgba(255,255,255,0.8)'; ctx.stroke();
    ctx.font = '900 9px system-ui, -apple-system, "Noto Sans KR", sans-serif';
    const fit = Math.min(9, 9 * BTN_R * 1.5 / ctx.measureText(text).width);   // the name inside the ring, however long
    label(text, cx, cy + 0.4, fit, 'center', 1, '#ffffff');
  }
  // the mini-games on the progress bar: where in the lap each comes (the start of its place), and its mark: the rhythm
  // stage a pink disc with a note, the orbit stage a violet disc with a little orbit, baseball a ball, the germ game
  // (v40) a germ, the memory game a neuron. More games: add them here.
  const BAR_W = 160, SCORE_Y = 21.4;                       // (v50: the score sits over the bar)
  const MINI_MARKS = [['spleen', 'wm'], ['ra', 'rh'], ['vertebral', 'orb'], ['hippocampus', 'mem'], ['jejunum', 'bb'], ['toiletBowl', 'sl'], ['manhole', 'pk'], ['combined', 'yb'], ['clarifier1', 'tw'], ['outfall', 'ar']].map(([id, kind]) => { const i = COURSE.findIndex((st) => st[0] === id); return { kind, i, lx: STARTS[i] }; });
  function miniMark(kind, x, y, alpha) {
    ctx.globalAlpha = alpha * GA;
    ctx.beginPath(); ctx.arc(x, y, 4.6, 0, 6.29); ctx.fillStyle = '#1a0a14'; ctx.fill();
    if (kind === 'bb') {                                    // a baseball: shaded white, two curved red seams with their stitches
      const R = 4.1;
      ctx.beginPath(); ctx.arc(x, y, R + 0.9, 0, 6.29); ctx.fillStyle = '#1a0a14'; ctx.fill();
      const g = ctx.createRadialGradient(x - R * 0.35, y - R * 0.4, R * 0.15, x, y, R);
      g.addColorStop(0, '#ffffff'); g.addColorStop(0.65, '#f1ebe2'); g.addColorStop(1, '#c9bdb0');
      ctx.beginPath(); ctx.arc(x, y, R, 0, 6.29); ctx.fillStyle = g; ctx.fill();
      ctx.save(); ctx.beginPath(); ctx.arc(x, y, R - 0.2, 0, 6.29); ctx.clip();
      for (const sd of [-1, 1]) {                          // each seam: an arc bowing in from one side
        const cx = x + sd * R * 1.32, rr = R * 0.98, a0 = sd < 0 ? -0.42 * Math.PI : 0.58 * Math.PI, a1 = a0 + 0.84 * Math.PI;
        ctx.beginPath(); ctx.arc(cx, y, rr, a0, a1); ctx.lineWidth = 0.5; ctx.strokeStyle = '#d4202c'; ctx.stroke();
        ctx.lineWidth = 0.38; ctx.beginPath();
        for (let k = 1; k <= 5; k++) {                     // the stitches: little ticks across the seam
          const a = a0 + (a1 - a0) * k / 6, px = cx + Math.cos(a) * rr, py = y + Math.sin(a) * rr, tx = -Math.sin(a), ty = Math.cos(a), nx = Math.cos(a), ny = Math.sin(a);
          ctx.moveTo(px - nx * 0.75 - tx * 0.3, py - ny * 0.75 - ty * 0.3); ctx.lineTo(px + nx * 0.75 + tx * 0.3, py + ny * 0.75 + ty * 0.3);
        }
        ctx.stroke();
      }
      ctx.restore();
      ctx.globalAlpha = GA; return;
    }
    if (kind === 'wm') {                                    // a purple germ with little spikes and two eyes
      ctx.beginPath();
      for (let k = 0; k < 16; k++) { const a = k * Math.PI / 8, r = k % 2 ? 3.0 : 3.9; ctx.lineTo(x + Math.cos(a) * r, y + Math.sin(a) * r); }
      ctx.closePath(); ctx.fillStyle = '#9a5ad0'; ctx.fill();
      ctx.beginPath(); ctx.arc(x, y, 2.7, 0, 6.29); ctx.fillStyle = '#b07ae0'; ctx.fill();
      ctx.fillStyle = '#ffffff'; ctx.beginPath(); ctx.arc(x - 1.05, y - 0.3, 0.75, 0, 6.29); ctx.arc(x + 1.05, y - 0.3, 0.75, 0, 6.29); ctx.fill();
      ctx.fillStyle = '#1a0a14'; ctx.beginPath(); ctx.arc(x - 0.95, y - 0.2, 0.38, 0, 6.29); ctx.arc(x + 1.15, y - 0.2, 0.38, 0, 6.29); ctx.fill();
      ctx.globalAlpha = GA; return;
    }
    if (kind === 'pk') {                                    // (v44) a football: white, a dark pentagon in the middle, patches at the edge
      ctx.beginPath(); ctx.arc(x, y, 3.9, 0, 6.29); ctx.fillStyle = '#f4f0ea'; ctx.fill();
      ctx.fillStyle = '#1a0a14'; ctx.beginPath();
      for (let k = 0; k < 5; k++) { const a = -Math.PI / 2 + k * 2 * Math.PI / 5; ctx.lineTo(x + Math.cos(a) * 1.45, y + Math.sin(a) * 1.45); }
      ctx.closePath(); ctx.fill();
      ctx.save(); ctx.beginPath(); ctx.arc(x, y, 3.9, 0, 6.29); ctx.clip();
      for (let k = 0; k < 5; k++) { const a = Math.PI / 2 + k * 2 * Math.PI / 5; ctx.beginPath(); ctx.arc(x + Math.cos(a) * 4.0, y + Math.sin(a) * 4.0, 1.25, 0, 6.29); ctx.fill(); }
      ctx.restore();
      ctx.globalAlpha = GA; return;
    }
    if (kind === 'sl') {                                    // (v44) a slot machine's face: a gold disc, three reels in a dark window
      ctx.beginPath(); ctx.arc(x, y, 3.9, 0, 6.29); ctx.fillStyle = '#ffc83a'; ctx.fill();
      ctx.fillStyle = '#1a0a14'; ctx.fillRect(x - 2.85, y - 1.75, 5.7, 3.5);
      ctx.fillStyle = '#fffaf0'; for (let k = -1; k <= 1; k++) ctx.fillRect(x + k * 1.85 - 0.75, y - 1.3, 1.5, 2.6);
      ctx.fillStyle = '#e8343c'; for (let k = -1; k <= 1; k++) ctx.fillRect(x + k * 1.85 - 0.45, y - 0.3, 0.9, 0.6);
      ctx.globalAlpha = GA; return;
    }
    if (kind === 'tw') {                                    // (v53) the poop tower: a teal disc, three brown bricks stacked
      ctx.beginPath(); ctx.arc(x, y, 3.9, 0, 6.29); ctx.fillStyle = '#2a9a8e'; ctx.fill();
      ctx.fillStyle = '#7a4218'; for (const [dx, dy] of [[-0.6, 1.6], [0.5, 0.1], [-0.2, -1.4]]) { rrect(x + dx - 2.2, y + dy - 0.65, 4.4, 1.3, 0.6); ctx.fill(); }
      ctx.globalAlpha = GA; return;
    }
    if (kind === 'ar') {                                    // (v53) the archery: a sky-blue disc (v55: a round blue bird, white-bellied, an orange beak), an arrow through
      ctx.beginPath(); ctx.arc(x, y, 3.9, 0, 6.29); ctx.fillStyle = '#9ad4ff'; ctx.fill();
      ctx.beginPath(); ctx.arc(x - 0.3, y + 0.5, 2.1, 0, 6.29); ctx.fillStyle = '#3a7ee0'; ctx.fill();
      ctx.beginPath(); ctx.arc(x - 0.6, y + 1.1, 1.2, 0, 6.29); ctx.fillStyle = '#ffffff'; ctx.fill();
      ctx.fillStyle = '#ffa020'; ctx.beginPath(); ctx.moveTo(x - 2.3, y + 0.3); ctx.lineTo(x - 3.4, y + 0.8); ctx.lineTo(x - 2.3, y + 1.2); ctx.closePath(); ctx.fill();
      ctx.beginPath(); ctx.arc(x - 1.3, y - 0.2, 0.4, 0, 6.29); ctx.fillStyle = '#10141e'; ctx.fill();
      ctx.strokeStyle = '#ffffff'; ctx.lineWidth = 0.55; ctx.beginPath(); ctx.moveTo(x - 2.8, y + 2.8); ctx.lineTo(x + 2.6, y - 2.6); ctx.stroke();
      ctx.fillStyle = '#ffffff'; ctx.beginPath(); ctx.moveTo(x + 3.0, y - 3.0); ctx.lineTo(x + 1.6, y - 2.6); ctx.lineTo(x + 2.6, y - 1.6); ctx.closePath(); ctx.fill();
      ctx.globalAlpha = GA; return;
    }
    if (kind === 'yb') {                                    // (v52) the shell game: a red disc, a silver lid with a gold ring
      ctx.beginPath(); ctx.arc(x, y, 3.9, 0, 6.29); ctx.fillStyle = '#c42a44'; ctx.fill();
      ctx.beginPath(); ctx.ellipse(x, y + 1.6, 3.0, 0.9, 0, 0, 6.29); ctx.fillStyle = '#5a6a84'; ctx.fill();
      ctx.beginPath(); ctx.ellipse(x, y + 1.5, 2.6, 2.9, 0, Math.PI, 0); ctx.fillStyle = '#c8d6ea'; ctx.fill();
      ctx.beginPath(); ctx.arc(x, y - 1.9, 0.75, 0, 6.29); ctx.fillStyle = '#ffc83a'; ctx.fill();
      ctx.globalAlpha = GA; return;
    }
    if (kind === 'mem') {                                   // a teal disc with a little neuron: a round body, forking branches
      ctx.beginPath(); ctx.arc(x, y, 3.7, 0, 6.29); ctx.fillStyle = '#2ab0a0'; ctx.fill();
      ctx.strokeStyle = '#ffffff'; ctx.fillStyle = '#ffffff'; ctx.lineWidth = 0.55; ctx.lineCap = 'round';
      ctx.beginPath(); ctx.arc(x, y, 1.2, 0, 6.29); ctx.fill();
      ctx.beginPath();
      for (let k = 0; k < 6; k++) { const a = -Math.PI / 2 + k * Math.PI / 3, c = Math.cos(a), sn = Math.sin(a);
        ctx.moveTo(x + c * 1.1, y + sn * 1.1); ctx.lineTo(x + c * 2.75, y + sn * 2.75);
        ctx.moveTo(x + c * 2.1, y + sn * 2.1); ctx.lineTo(x + Math.cos(a + 0.55) * 2.85, y + Math.sin(a + 0.55) * 2.85); }
      ctx.stroke();
      ctx.globalAlpha = GA; return;
    }
    ctx.beginPath(); ctx.arc(x, y, 3.7, 0, 6.29); ctx.fillStyle = kind === 'rh' ? '#ff5a8a' : '#9a6cff'; ctx.fill();
    ctx.fillStyle = '#ffffff'; ctx.strokeStyle = '#ffffff';
    if (kind === 'rh') {                                    // an eighth note
      ctx.beginPath(); ctx.ellipse(x - 0.9, y + 1.4, 1.25, 0.95, -0.4, 0, 6.29); ctx.fill();
      ctx.fillRect(x + 0.15, y - 2.3, 0.6, 3.7);
      ctx.beginPath(); ctx.moveTo(x + 0.75, y - 2.3); ctx.quadraticCurveTo(x + 2.2, y - 1.4, x + 1.7, y - 0.2); ctx.lineWidth = 0.6; ctx.stroke();
    } else {                                                // a ring and a body going round it
      ctx.beginPath(); ctx.arc(x, y, 2.1, 0, 6.29); ctx.lineWidth = 0.6; ctx.stroke();
      ctx.beginPath(); ctx.arc(x + 1.5, y - 1.5, 0.95, 0, 6.29); ctx.fill();
    }
    ctx.globalAlpha = GA;
  }
  // the HUD goes while the cut scene plays (it would hide the dive into the toilet at the top left)
  function hudAlpha() {
    const c = G.cut;
    if (c) return c.landed ? Math.min(1, (G.t - c.landed) / 0.35) : Math.max(0, 1 - (G.t - c.t0) / 0.3);
    if (G.cutTail) return Math.min(1, (G.t - G.cutTail.landed) / 0.35);
    return 1;
  }
  function drawHud() {
    GA = hudAlpha();
    document.getElementById('place').style.opacity = GA;
    if (GA > 0) { ctx.globalAlpha = GA; drawHudAll(); }
    GA = 1; ctx.globalAlpha = 1;
  }
  function drawHudAll() {
    world();
    // health bar
    const x0 = 16, y0 = 7, w = 112, h = 8;
    rrect(x0 - 1.2, y0 - 1.2, w + 2.4, h + 2.4, 3.2); ctx.fillStyle = '#1a0a14'; ctx.fill();
    rrect(x0, y0, w, h, 2.4); ctx.fillStyle = '#3a2030'; ctx.fill();
    const fw = w * Math.min(G.hp, HP_MAX) / HP_MAX;
    const low = G.hp < 25 && Math.floor(G.t * 4) % 2 === 0;
    if (fw > 0.5) {
      const gr = ctx.createLinearGradient(0, y0, 0, y0 + h); gr.addColorStop(0, low ? '#ffd0d8' : '#ffb0c0'); gr.addColorStop(0.5, '#ff5a7a'); gr.addColorStop(1, '#a8123a');
      rrect(x0, y0, fw, h, 2.4); ctx.fillStyle = gr; ctx.fill();
      rrect(x0 + 1.5, y0 + 1.1, Math.max(0, fw - 3), 1.4, 0.7); ctx.fillStyle = 'rgba(255,230,236,0.85)'; ctx.fill();
    }
    if (G.hp > HP_MAX) {                                      // (v60) health past 100 ('체력 +20'): gold over the start of the bar
      const ow = w * Math.min(1, (G.hp - HP_MAX) / HP_MAX), go = ctx.createLinearGradient(0, y0, 0, y0 + h); go.addColorStop(0, '#fff2a0'); go.addColorStop(0.5, '#ffc83a'); go.addColorStop(1, '#c87a10');
      rrect(x0, y0, ow, h, 2.4); ctx.fillStyle = go; ctx.fill();
    }
    ctx.fillStyle = 'rgba(26,10,20,0.6)'; for (let k = 1; k < 8; k++) ctx.fillRect(x0 + k * w / 8 - 0.35, y0 + h - 2.2, 0.7, 2.2);
    spr('hud_heart', x0 - 10.5, y0 - 3.2);
    label(`${Math.ceil(100 * G.hp / HP_MAX)}%`, x0 + w - 2.5, y0 + h / 2 + 0.3, 6.2, 'right', 1, '#ffffff');     // (v51) how much, in %
    {
      const gx = x0, gy = y0 + h + 4.5, gw = 62, gh = 4.6;
      rrect(gx - 1, gy - 1, gw + 2, gh + 2, 2.6); ctx.fillStyle = '#1a0a14'; ctx.fill();
      rrect(gx, gy, gw, gh, 2); ctx.fillStyle = '#26324a'; ctx.fill();
      const on = G.boost > 0, f = on ? G.boost / BOOST_T : G.o2n / boostNeed();
      if (f > 0.01) {
        const gr = ctx.createLinearGradient(0, gy, 0, gy + gh);
        if (on) { gr.addColorStop(0, '#fff2b0'); gr.addColorStop(0.5, '#ff9a2a'); gr.addColorStop(1, '#d8361a'); }
        else { gr.addColorStop(0, '#cdeeff'); gr.addColorStop(0.5, '#4aa8f0'); gr.addColorStop(1, '#1f6aa8'); }
        rrect(gx, gy, Math.max(gh, gw * f), gh, 2); ctx.fillStyle = gr; ctx.fill();
      }
      spr('it_' + (M.themes[G.theme].coin || 'o2'), gx - 10, gy - 2.6, 1, 9.2, 9.2);     // the coin of this place
      if (!on) label(`${G.o2n}/${boostNeed()}`, gx + gw + 3, gy + gh / 2 + 0.2, 6, 'left', 1, '#cdeeff');
    }
    // (v50) the score: in the middle, over the progress bar (between the place's name and the bar's marks), as points
    // with no coin by it (a coin there read as the coins you collect); how far, small, at its right
    {
      const s = PT(G.score), SC = 9.5, y = SCORE_Y;
      label(s, NW / 2, y, SC, 'center');
      ctx.font = `900 ${SC}px system-ui, -apple-system, "Noto Sans KR", sans-serif`;
      const tw = ctx.measureText(s).width;
      const ds = `${G.distM.toLocaleString('en-US')}m`;
      label(ds, NW / 2 + tw / 2 + 4, y + 0.6, 6, 'left', 1, '#d8e8ff');
      // (v57) the best (this browser's), small at its left (or, where that would run into the booster's count, at the
      // right after the distance); past it, this run is the best: it shows this run's, brighter
      const bs = Math.max(G.best0 || 0, G.score), nb = G.score > (G.best0 || 0) && G.score > 0;
      if (bs > 0) {
        const bt = `${TR('최고', 'Best')} ${bs.toLocaleString('en-US')}`;
        ctx.font = `900 6px system-ui, -apple-system, "Noto Sans KR", sans-serif`;
        const bw = ctx.measureText(bt).width, dw = ctx.measureText(ds).width, gR = x0 + 62 + 3 + ctx.measureText(`${G.o2n}/${boostNeed()}`).width;
        if (NW / 2 - tw / 2 - 4 - bw > gR + 4) label(bt, NW / 2 - tw / 2 - 4, y + 0.6, 6, 'right', 1, nb ? '#ffe14a' : '#ffe68a');
        else label(bt, NW / 2 + tw / 2 + 4 + dw + 5, y + 0.6, 6, 'left', 1, nb ? '#ffe14a' : '#ffe68a');
      }
    }
    let noteY = 30;
    { const on = [G.x2 && 'x2', G.magR && 'mag', G.opts && G.opts.hp && 'hp'].filter(Boolean);      // (v60) the start items this run
      on.forEach((k, i) => { ctx.globalAlpha = 0.75; rrect(14 + i * 15, 25.5, 13, 11, 4); ctx.fillStyle = '#1a0a14'; ctx.fill(); ctx.globalAlpha = 1; itemIcon(k, 20.5 + i * 15, 31, 0.62); });
      if (on.length) noteY = 42; }
    if (SET.god) label(TR('디버그: 안 죽음', 'Debug: no death'), 16, noteY, 6, 'left', 0.85, '#8af0ff');
    // pause
    rrect(NW - 20, 4.5, 14, 14, 3); ctx.fillStyle = '#1a0a14'; ctx.fill();
    rrect(NW - 19, 5.5, 12, 12, 2.3); ctx.fillStyle = '#f4e8ee'; ctx.fill();
    ctx.fillStyle = '#1a0a14'; ctx.fillRect(NW - 16.2, 8.5, 2, 6); ctx.fillRect(NW - 12.2, 8.5, 2, 6);
    // progress through this stage (the body, or stage 2), with where the mini-games come (a mark each; dimmed once
    // passed); the stage's number at its left end
    const p = stationAt(G.x), stg = stageOf(p.lx), [s0, s1] = stageSpan(stg), px0 = NW / 2 - BAR_W / 2, px1 = px0 + BAR_W, py = 31;
    rrect(px0 - 1, py - 1, px1 - px0 + 2, 4.4, 2.2); ctx.fillStyle = '#1a0a14'; ctx.fill();
    ctx.fillStyle = '#4a3848'; ctx.fillRect(px0, py, px1 - px0, 2.4);
    const mk = px0 + (px1 - px0) * (p.lx - s0) / (s1 - s0);
    ctx.fillStyle = '#ff6a8a'; ctx.fillRect(px0, py, mk - px0, 2.4);
    for (const m of MINI_MARKS) if (stageOf(m.lx) === stg) miniMark(m.kind, px0 + (px1 - px0) * (m.lx - s0) / (s1 - s0), py + 1.2, p.lx > m.lx + 1 || !!G[m.kind] ? 0.45 : 1);
    label(String(stg), px0 - 6, py + 1.4, 7, 'center', 1, '#ffe0a8');
    ctx.beginPath(); ctx.arc(mk, py + 1.2, 2.8, 0, 6.29); ctx.fillStyle = '#1a0a14'; ctx.fill();
    ctx.beginPath(); ctx.arc(mk, py + 1.2, 1.9, 0, 6.29); ctx.fillStyle = '#ffffff'; ctx.fill();
    // the settings (a gear), under the pause button
    {
      rrect(NW - 20, 26.5, 14, 14, 3); ctx.fillStyle = '#1a0a14'; ctx.fill();
      rrect(NW - 19, 27.5, 12, 12, 2.3); ctx.fillStyle = '#f4e8ee'; ctx.fill();
      const gx = NW - 13, gy = 33.5;
      ctx.fillStyle = '#1a0a14'; ctx.beginPath();
      for (let k = 0; k < 8; k++) { const a = k * Math.PI / 4, c = Math.cos(a), sn = Math.sin(a);
        const P = [[-1.15, -4.7], [1.15, -4.7], [1.15, -2.6], [-1.15, -2.6]].map(([x, y]) => [gx + x * c - y * sn, gy + x * sn + y * c]);
        ctx.moveTo(P[0][0], P[0][1]); for (const q of P.slice(1)) ctx.lineTo(q[0], q[1]); ctx.closePath(); }
      ctx.fill();
      ctx.beginPath(); ctx.arc(gx, gy, 3.5, 0, 6.29); ctx.fill();
      ctx.beginPath(); ctx.arc(gx, gy, 1.35, 0, 6.29); ctx.fillStyle = '#f4e8ee'; ctx.fill();
    }
    // debugging: the skip button (two arrows and a bar), under the settings
    if (DEBUG_SKIP) {
      rrect(NW - 20, 48.5, 14, 14, 3); ctx.fillStyle = '#1a0a14'; ctx.fill();
      rrect(NW - 19, 49.5, 12, 12, 2.3); ctx.fillStyle = '#f4e8ee'; ctx.fill();
      ctx.fillStyle = '#1a0a14';
      for (const ox of [0, 3.6]) { ctx.beginPath(); ctx.moveTo(NW - 17.2 + ox, 52.3); ctx.lineTo(NW - 13.4 + ox, 55.5); ctx.lineTo(NW - 17.2 + ox, 58.7); ctx.closePath(); ctx.fill(); }
      ctx.fillRect(NW - 9.6, 52.3, 1.4, 6.4);
      // (v48) and left of it the stage skip: the same, with the next stage's number
      rrect(NW - 38, 48.5, 14, 14, 3); ctx.fillStyle = '#1a0a14'; ctx.fill();
      rrect(NW - 37, 49.5, 12, 12, 2.3); ctx.fillStyle = '#ffe0a8'; ctx.fill();
      ctx.fillStyle = '#1a0a14';
      for (const ox of [0, 3.2]) { ctx.beginPath(); ctx.moveTo(NW - 35.6 + ox, 52.6); ctx.lineTo(NW - 32.4 + ox, 55.5); ctx.lineTo(NW - 35.6 + ox, 58.4); ctx.closePath(); ctx.fill(); }
      ctx.fillRect(NW - 28.6, 52.3, 1.3, 6.4);
      label(stg === 1 ? '2' : '1', NW - 31, 64.8, 5.5, 'center', 1, '#ffe0a8');
    }
    // buttons (not on the rhythm or orbit stage)
    if (busy()) return;
    const by = NH - BTN_M - BTN_R, bl = BTN_M + BTN_R, br = NW - BTN_M - 2 - BTN_R;
    if (inWater()) { const on = swimHeld(); button(bl, by, TR('헤엄', 'Swim'), on); button(br, by, TR('헤엄', 'Swim'), on); return; }     // (both swim)
    const jOn = [...held.values()].includes('jump') || (AUTO && !G.onGround);
    button(SET.swap ? br : bl, by, TR('점프', 'Jump'), jOn);
    button(SET.swap ? bl : br, by, TR('슬라이드', 'Slide'), G.slideHeld);
    drawTut();
  }
  // eyelids closing over the screen: 0 open .. 1 shut (close fast, hold, open a little slower)
  const BLINK = 0.32;
  function lidAmount() {
    if (G.blinkAt < 0) return 0;
    const u = G.t - G.blinkAt;
    if (u < 0 || u > BLINK) return 0;
    if (u < 0.08) { const k = u / 0.08; return k * k * (3 - 2 * k); }
    if (u < 0.14) return 1;
    const k = (u - 0.14) / (BLINK - 0.14); return 1 - k * k * (3 - 2 * k);
  }
  function drawLids() {
    const b = lidAmount(); if (b <= 0) return;
    world();
    const c = NWf / 2, bend = 0.32 * (1 - b), N = 32;
    for (const upper of [true, false]) {
      const reach = b * (upper ? NH * 0.6 + 2 : NH * 0.4 + 2);
      const edge = (x) => { const q = (x - c) / c; const d = reach * (1 - bend * q * q); return upper ? d : NH - d; };
      const far = upper ? -2 : NH + 2;
      ctx.beginPath(); ctx.moveTo(-2, far); ctx.lineTo(NWf + 2, far);
      for (let i = N; i >= 0; i--) { const x = (NWf + 4) * i / N - 2; ctx.lineTo(x, edge(x)); }
      ctx.closePath();
      const g = ctx.createLinearGradient(0, far, 0, upper ? reach : NH - reach);
      g.addColorStop(0, '#000000'); g.addColorStop(0.8, '#060203'); g.addColorStop(1, '#1c070a');
      ctx.fillStyle = g; ctx.fill();
    }
  }
  function render() {
    device();
    ctx.fillStyle = '#000'; ctx.fillRect(0, 0, GW, GH);
    if (PROF) {
      for (const [k, f] of [['scene', drawScene], ['lids', drawLids], ['rhythm', drawRhythm], ['orbit', drawOrbit], ['baseball', drawBaseball], ['whack', drawWhack], ['memory', drawMemory], ['pk', drawPK], ['slot', drawSlot], ['cut', drawCut], ['hud', drawHud]]) {
        const t0 = performance.now(); f(); PROF[k] = (PROF[k] || 0) + performance.now() - t0;
      }
      PROF.n = (PROF.n || 0) + 1;
    } else {
      drawScene();
      drawLids();
      drawRhythm();
      drawOrbit();
      drawBaseball();
      drawWhack();
      drawMemory();
      drawPK();
      drawSlot();
      drawYB();
      drawTW();
      drawAR();
      drawGameCombo();
      if (G.cut || G.cutTail) drawCut();
      drawHud();
    }
    // the place's name grows in for a moment when you arrive
    const u = (G.t - G.banner);
    document.getElementById('place').classList.toggle('big', u < 1.6);
  }

  // ---------------------------------------------------------------- (v59) the run in a row of the mini-game on now
  // ('3combo'), at the left side while it plays (the rhythm stage: at the bottom left, where its notes are not), from 1;
  // it pops a little bigger as it goes up, and is gone when the run is broken
  const COMBO_FX = { k: null, n: 0, t: -9 };
  function gameCombo() {
    const live = (g, off) => g && !off.includes(g.st);
    if (G.rh) return G.rh.done ? null : ['rh', G.rh.combo, 18, NH - 16];
    if (G.orb) return live(G.orb, ['done']) ? ['orb', G.orb.combo] : null;
    if (G.bb) return live(G.bb, ['intro', 'done']) ? ['bb', G.bb.streak || 0] : null;
    if (G.wm) return live(G.wm, ['intro', 'done']) ? ['wm', G.wm.combo] : null;
    if (G.mem) return live(G.mem, ['intro', 'done']) ? ['mem', G.mem.run || 0] : null;
    if (G.pk) return live(G.pk, ['intro', 'done']) ? ['pk', G.pk.run || 0] : null;
    if (G.sl) return live(G.sl, ['intro', 'done']) ? ['sl', G.sl.run || 0] : null;
    if (G.yb) return live(G.yb, ['intro', 'done']) ? ['yb', G.yb.res.includes('lose') ? 0 : G.yb.res.filter((r) => r === 'win').length] : null;
    if (G.tw) return live(G.tw, ['intro', 'done']) ? ['tw', G.tw.streak] : null;
    if (G.ar) return live(G.ar, ['intro', 'done']) ? ['ar', G.ar.streak] : null;
    return null;
  }
  function drawGameCombo() {
    const c = gameCombo(); if (!c) { COMBO_FX.k = null; COMBO_FX.n = 0; return; }
    const [k, n, x = 16, y = 92] = c;
    if (k === COMBO_FX.k && n > COMBO_FX.n) COMBO_FX.t = G.t;
    COMBO_FX.k = k; COMBO_FX.n = n;
    if (n < 1) return;
    world();
    const sz = 13 * (1 + 0.45 * Math.max(0, 1 - (G.t - COMBO_FX.t) / 0.22)), ns = String(n);
    ctx.font = `900 ${sz}px system-ui, -apple-system, "Noto Sans KR", sans-serif`;
    const w = ctx.measureText(ns).width;
    label(ns, x, y, sz, 'left', 1, '#ffe14a');
    label('combo', x + w + 1.2, y + 2.4, 7, 'left', 1, '#fff3c8');
  }

  // ---------------------------------------------------------------- labels, overlays
  function setLabel(st, lap) {
    document.getElementById('pname').textContent = TR(st[1], st[2]);       // (v47) one language
    document.getElementById('pen').textContent = lap > 0 ? TR(`${lap + 1}바퀴`, `Lap ${lap + 1}`) : '';
  }
  // (v60) a panel shown by a tap on the canvas comes up under the finger, and on a phone that same touch's click then
  // lands on it (a runner picked, the lobby back again): clicks on the panels are let through only 450 ms after one opens
  let panelT = -1e9;
  function show(id, on) { const el = document.getElementById(id); if (on && el.hidden) panelT = performance.now(); el.hidden = !on; }
  document.getElementById('ov').addEventListener('click', (e) => { if (performance.now() - panelT < 450) { e.stopPropagation(); e.preventDefault(); } }, true);
  function pause(box = 'pauseBox') { if (G.mode !== 'play') return; G.mode = 'pause'; held.clear(); G.slideHeld = false; if (G.rh) G.rh.ptr.clear(); if (G.bb) G.bb.drag = null; bbKeys.clear(); if (box === 'setBox') setLabels(); show(box, true); if (SND.ctx) SND.ctx.suspend(); }
  const openSettings = () => pause('setBox');               // the settings, from the gear on the play screen: the game waits
  function resume() { show('pauseBox', false); show('setBox', false); G.mode = 'play'; last = performance.now(); SND.unlock(); SND.play('ui'); }
  function setLabels() {                                   // the settings' buttons show how things are now
    document.getElementById('bSwap').textContent = SET.swap ? TR('왼쪽 슬라이드 · 오른쪽 점프', 'Left slide · Right jump') : TR('왼쪽 점프 · 오른쪽 슬라이드', 'Left jump · Right slide');
    { const b = document.getElementById('bGod'); b.textContent = SET.god ? TR('안 죽음 켜짐', 'No death on') : TR('안 죽음 꺼짐', 'No death off'); b.classList.toggle('off', !SET.god); }
    for (const [id, k, name] of [['bSfx', 'sfx', TR('효과음', 'Sound effects')], ['bMus', 'music', TR('배경음악', 'Music')]]) {
      const b = document.getElementById(id), off = SND.muted(k);
      b.textContent = name + (off ? TR(' 꺼짐', ' off') : TR(' 켜짐', ' on')); b.classList.toggle('off', off);
    }
  }
  function gameOver() {
    G.mode = 'over'; show('overBox', true);
    if (busy()) { for (const g of [G.rh, G.orb, G.bb, G.wm, G.mem, G.pk, G.sl, G.yb, G.tw, G.ar]) bankGame(g); G.rh = null; G.orb = null; G.bb = null; G.wm = null; G.mem = null; G.pk = null; G.sl = null; G.yb = null; G.tw = null; G.ar = null; G.cut = null; SND.stopSong(0.3); SND.stopLoop(0.3); SND.spin(null); }
    SND.ambience(false); SND.play('over');
    // (v49) the end card: the score big, where it came from, how long and how far, the best (kept in this browser)
    const P = scoreParts(), f = (n) => n.toLocaleString('en-US');
    const R = settleRun(), best = R.best, isBest = R.isBest;     // (v60) the final score (x2), the coins, the records
    if (G.tut) tutEnd();
    document.getElementById('overScore').textContent = f(R.fin);
    document.getElementById('overParts').textContent = TR(`거리 ${f(P.dist)} · 아이템 ${f(P.items)} · 미니게임 ${f(P.games)}${G.x2 ? ' · 점수 2배!' : ''}`, `Distance ${f(P.dist)} · Items ${f(P.items)} · Mini-games ${f(P.games)}${G.x2 ? ' · Score x2!' : ''}`);
    document.getElementById('overCoins').textContent = TR(`코인 +${f(R.add)}  ·  보유 ${f(WALLET.coins())}`, `Coins +${f(R.add)}  ·  ${f(WALLET.coins())} in all`);
    { const b = document.getElementById('bRevive'), ok = canRevive(), own = WALLET.has('rev');     // (v60) getting up again: once a run
      b.hidden = G.revived || CAPTURE && !qs.has('revive'); b.disabled = !ok;
      b.textContent = own > 0 ? TR(`부활 (보유 ${own})`, `Revive (${own} kept)`) : TR(`부활 · 코인 ${ITEMS.rev.price}`, `Revive · ${ITEMS.rev.price} coins`); }
    document.getElementById('overMsg').textContent = TR(`${Math.floor(G.t / 60)}분 ${Math.floor(G.t % 60)}초 · ${f(G.distM)}m · ${COURSE[G.station][1]}까지`, `${Math.floor(G.t / 60)}:${String(Math.floor(G.t % 60)).padStart(2, '0')} · ${f(G.distM)}m · reached ${COURSE[G.station][2]}`);
    document.getElementById('overBest').textContent = isBest ? TR('최고 기록!', 'New best!') : TR(`최고 기록 ${f(best)}`, `Best ${f(best)}`);
    document.getElementById('overBest').classList.toggle('new', isBest);
  }
  function startGame(c, opts = {}) {
    try { localStorage.setItem('bodyrun.char', c); } catch (e) { /* storage off */ }
    for (const f of ['title_bg.webp', 'logo_ko.webp', 'logo_en.webp', 'lobby_bg.webp']) if (bmp[f]) release(f);
    show('select', false); show('pauseBox', false); show('setBox', false); show('overBox', false); show('hudText', true);
    if (!CAPTURE) { SND.unlock(); SND.stopSong(0.2); SND.stopLoop(0.2); SND.spin(null); SND.play('ui'); SND.ambience(true); getReady(); }
    newRun(c, opts); G.station = -1; step(0); last = performance.now();
    try { if (!CAPTURE && document.documentElement.requestFullscreen && matchMedia('(pointer: coarse)').matches) document.documentElement.requestFullscreen().then(() => screen.orientation && screen.orientation.lock && screen.orientation.lock('landscape').catch(() => {})).catch(() => {}); } catch (e) { /* not allowed here */ }
  }
  function buildSelect() {
    const grid = document.getElementById('grid'); grid.innerHTML = '';
    let saved = null; try { saved = localStorage.getItem('bodyrun.char'); } catch (e) { /* storage off */ }
    const im = bmp['common.webp'];
    for (const c of M.chars) {
      const s = M.sprites['ch_' + c];
      const b = document.createElement('button'); b.className = 'card' + (c === saved ? ' last' : '');
      const cc = document.createElement('canvas'); cc.width = s.r[2]; cc.height = s.r[3];
      cc.getContext('2d').drawImage(im, s.r[0], s.r[1], s.r[2], s.r[3], 0, 0, s.r[2], s.r[3]);
      const nm = document.createElement('span'); nm.textContent = CHAR_NAMES[c] || c;
      b.append(cc, nm); b.onclick = () => { if (selectMode === 'lobby' || selectMode === 'prep') { try { localStorage.setItem('bodyrun.char', c); } catch (e) { /* storage off */ } SND.play('ui'); const m = selectMode; goLobby(); if (m === 'prep') { LOBBY.page = 'prep'; LOBBY.sel = {}; } } else startGame(c); };     // (v59: from the lobby, back to it)
      grid.append(b);
    }
  }
  document.getElementById('bResume').onclick = resume;
  document.getElementById('bRestart').onclick = () => startGame(G.char);
  document.getElementById('bChar').onclick = () => { selectMode = 'start'; buildSelect(); G.mode = 'select'; G.rh = null; G.orb = null; G.bb = null; G.cut = null; G.cutTail = null; SND.unlock(); SND.stopSong(0.2); SND.stopLoop(0.2); SND.spin(null); SND.ambience(false); show('pauseBox', false); show('overBox', false); show('hudText', false); show('select', true); };
  document.getElementById('bSetBack').onclick = () => { if (G.mode === 'lobby') { show('setBox', false); SND.play('ui'); } else resume(); };     // (v59: the lobby's settings too)
  document.getElementById('bRevive').onclick = () => revive();
  for (const id of ['bLobby', 'bLobby2', 'bSelBack']) document.getElementById(id).onclick = () => { if (SND.ctx && SND.ctx.state === 'suspended') SND.unlock(); SND.play('ui'); goLobby(); };     // (v59) to the lobby
  document.getElementById('bSwap').onclick = () => { SET.swap = !SET.swap; try { localStorage.setItem('bodyrun.swap', SET.swap ? '1' : '0'); } catch (e) { /* storage off */ } setLabels(); render(); };
  document.getElementById('bSfx').onclick = () => { SND.setMute('sfx', !SND.muted('sfx')); setLabels(); };
  document.getElementById('bGod').onclick = () => { SET.god = !SET.god; try { localStorage.setItem('bodyrun.god', SET.god ? '1' : '0'); } catch (e) { /* storage off */ } setLabels(); render(); };
  document.getElementById('bMus').onclick = () => { SND.setMute('music', !SND.muted('music')); setLabels(); };
  document.getElementById('bAgain').onclick = () => startGame(G.char);
  document.getElementById('bChar2').onclick = () => { selectMode = 'start'; buildSelect(); G.mode = 'select'; SND.ambience(false); show('overBox', false); show('hudText', false); show('select', true); };

  // ---------------------------------------------------------------- (v47) the title: the user's picture of the body
  // behind, the name (장기런 / Body Run, by the device's language) bobbing at the top, four of the runners (picked at
  // random) running about the bottom of it, hopping (now and then a big jump with a turn), '화면을 터치하세요' (v58). A tap: on
  // to picking a runner
  const TITLE = { run: [], t0: 0, tt: null };
  const ttime = () => (TITLE.tt !== null ? TITLE.tt : performance.now() / 1000 - TITLE.t0);
  function startTitle() {
    G.mode = 'title'; show('select', false); show('hudText', false);
    const pool = M.chars.slice(), lanes = [[134, 1.25], [146, 1.38], [159, 1.52], [172, 1.66]];        // feet's height, size
    TITLE.run = lanes.map(([y, k], i) => {
      const c = pool.splice(Math.floor(Math.random() * pool.length), 1)[0], dir = i % 2 ? -1 : 1;
      return { c, y, k, dir, v: 38 + Math.random() * 14, x0: i * 120 + Math.random() * 40, ph: Math.random() * 6.28, jumpEvery: 2.6 + Math.random() * 2.4, jumpAt: Math.random() * 2 };
    });
    TITLE.run.sort((a, b) => a.y - b.y);                    // (the far ones first)
    TITLE.t0 = performance.now() / 1000;
    try { TITLE.best = +(localStorage.getItem('bodyrun.best') || 0); } catch (e) { TITLE.best = 0; }
  }
  function titleTap() {
    if (ttime() < 0.35) return;                             // (a tap that was meant for something before)
    SND.play('ui'); goLobby();                               // (v59: on to the lobby)
  }
  function renderTitle() {
    device(); ctx.fillStyle = '#000'; ctx.fillRect(0, 0, GW, GH);
    world();
    const t = ttime(), bg = M.sprites.title_bg;
    // the picture, filling the screen (a slow drift in and out)
    if (bg && bmp[bg.f]) {
      const z = 1.04 + 0.03 * Math.sin(t * 0.25), sc = Math.max(NWf / bg.w, NH / bg.h) * z, w = bg.w * sc, h = bg.h * sc;
      spr('title_bg', (NWf - w) / 2 + Math.sin(t * 0.17) * 4, (NH - h) / 2 + Math.cos(t * 0.21) * 2, 1, w, h);
    } else { ctx.fillStyle = '#5a1030'; ctx.fillRect(0, 0, NWf, NH); }
    // darker at the bottom (the runners and the words read on it)
    const g = ctx.createLinearGradient(0, NH * 0.45, 0, NH); g.addColorStop(0, 'rgba(26,6,16,0)'); g.addColorStop(1, 'rgba(26,6,16,0.55)');
    ctx.fillStyle = g; ctx.fillRect(0, 0, NWf, NH);
    // the runners: across and round again, hopping as they run; now and then a big jump with a somersault; shadows
    for (const r of TITLE.run) {
      const sp = M.sprites['ch_' + r.c]; if (!sp) continue;
      const span = NWf + 80, x = ((r.x0 + r.v * t) % span + span) % span - 40, sx = r.dir > 0 ? x : NWf - x;
      const stride = (t * r.v / 9 + r.ph), hop = Math.abs(Math.sin(stride)) * 3.2 * r.k;
      const jt = (t + r.jumpAt) % r.jumpEvery, J = 0.62, jumping = jt < J, jq = jt / J;
      const big = jumping ? Math.sin(Math.PI * jq) * 30 * r.k : 0, spin = jumping ? jq * Math.PI * 2 * r.dir : 0;
      const land = !jumping && jt - J < 0.12 ? 1 - (jt - J) / 0.12 : 0;               // a squash on landing
      const w = sp.w * r.k * (1 + 0.12 * land), h = sp.h * r.k * (1 - 0.14 * land + (jumping ? 0 : 0.04 * Math.sin(stride * 2)));
      const up = jumping ? big : hop;
      ctx.globalAlpha = 0.32 * (1 - Math.min(1, up / 40)); ctx.fillStyle = '#000000';
      ctx.beginPath(); ctx.ellipse(sx, r.y + 0.5, w * 0.38, 2.4 * r.k, 0, 0, 6.2832); ctx.fill(); ctx.globalAlpha = 1;
      ctx.save(); ctx.translate(sx, r.y - up - h / 2); ctx.rotate(spin + (jumping ? 0 : Math.sin(stride) * 0.06)); if (r.dir < 0) ctx.scale(-1, 1);
      spr('ch_' + r.c, -w / 2, -h / 2, 1, w, h); ctx.restore();
    }
    // the name: bobbing, breathing a little
    const lg = M.sprites['logo_' + LANG];
    if (lg && bmp[lg.f]) {
      const W = Math.min(NWf * 0.6, 210) * (1 + 0.02 * Math.sin(t * 2.6)), H = W * lg.h / lg.w, y = 8 + Math.sin(t * 1.7) * 2;
      spr('logo_' + LANG, NWf / 2 - W / 2, y, 1, W, H);
    }
    { const a = 0.78 + 0.22 * Math.sin(t * 3.4), s2 = 1 + 0.04 * Math.sin(t * 3.4);
      ctx.globalAlpha = 0.45 * a; rrect(NWf / 2 - 52, 93, 104, 17, 8.5); ctx.fillStyle = '#1a0610'; ctx.fill(); ctx.globalAlpha = 1;
      label(TR('화면을 터치하세요', 'Touch the screen'), NWf / 2, 101.5, 10.5 * s2, 'center', a, '#ffffff'); }     // (v58: the best is not shown here any more)
  }

  // ---------------------------------------------------------------- (v60) coins, the start items, getting up again
  // A run pays a coin for each 100 points of its final score (paid when it ends; again for the extra after getting up).
  // Coins buy, in the shop, things kept for later, or, on the getting-ready page before a run, the start items for it:
  // '점수 2배' (the final score doubled), '자석' (a small magnet the whole run: things within 45 drawn in; the booster's
  // is 80), '체력 +20' (120 to start, and heals fill to 120). '부활': fallen, once a run, up again with 60 health (one
  // kept from the shop, or 500 coins there and then). A first visit is given 1,000 coins to try them. (kept in this
  // browser: bodyrun.coins, bodyrun.inv)
  const COIN_PER = 100, REVIVE_HP = 60, ITEM_MAG_R = 45;
  const ITEMS = {
    x2: { ko: '점수 2배', en: 'Score x2', dko: '이번 판 최종 점수 2배', den: 'Final score doubled', price: 600 },
    mag: { ko: '자석', en: 'Magnet', dko: '작은 자석을 달고 출발', den: 'Start with a small magnet', price: 400 },
    hp: { ko: '체력 +20', en: 'Health +20', dko: '체력 120으로 출발', den: 'Start with 120 health', price: 300 },
    rev: { ko: '부활', en: 'Revive', dko: '쓰러지면 한 번 다시 달리기', den: 'Get up once after falling', price: 500 },
  };
  const START_ITEMS = ['x2', 'mag', 'hp'];
  const WALLET = {
    coins() { try { const v = localStorage.getItem('bodyrun.coins'); if (v === null) { localStorage.setItem('bodyrun.coins', '1000'); return 1000; } return Math.max(0, +v || 0); } catch (e) { return 0; } },
    setCoins(n) { try { localStorage.setItem('bodyrun.coins', String(Math.max(0, Math.round(n)))); } catch (e) { /* storage off */ } },
    inv() { try { return JSON.parse(localStorage.getItem('bodyrun.inv') || '{}') || {}; } catch (e) { return {}; } },
    has(k) { return this.inv()[k] || 0; },
    give(k, n) { const v = this.inv(); v[k] = Math.max(0, (v[k] || 0) + n); try { localStorage.setItem('bodyrun.inv', JSON.stringify(v)); } catch (e) { /* storage off */ } },
    spend(n) { const c = this.coins(); if (c < n) return false; this.setCoins(c - n); return true; },
  };
  // a coin, drawn (gold, a rim, a star): no emoji
  function coinIcon(x, y, r) {
    ctx.save(); ctx.translate(x, y);
    ctx.beginPath(); ctx.arc(0, 0, r + 0.7, 0, 6.2832); ctx.fillStyle = '#1a0a14'; ctx.fill();
    const g = ctx.createLinearGradient(0, -r, 0, r); g.addColorStop(0, '#fff2a0'); g.addColorStop(0.5, '#ffc83a'); g.addColorStop(1, '#c87a10');
    ctx.beginPath(); ctx.arc(0, 0, r, 0, 6.2832); ctx.fillStyle = g; ctx.fill();
    ctx.beginPath(); ctx.arc(0, 0, r * 0.72, 0, 6.2832); ctx.lineWidth = r * 0.12; ctx.strokeStyle = 'rgba(160,90,10,0.7)'; ctx.stroke();
    ctx.beginPath(); for (let k = 0; k < 10; k++) { const a = -Math.PI / 2 + k * Math.PI / 5, q = k % 2 ? r * 0.22 : r * 0.5; ctx.lineTo(Math.cos(a) * q, Math.sin(a) * q); } ctx.closePath(); ctx.fillStyle = '#fff6c8'; ctx.fill();
    ctx.restore();
  }
  // the items' marks: a 'x2', a horseshoe magnet, a heart with a plus, a heart with a circling arrow (drawn)
  function itemIcon(k, x, y, s) {
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s); ctx.lineJoin = 'round'; ctx.lineCap = 'round';
    if (k === 'x2') { ctx.beginPath(); ctx.arc(0, 0, 6.5, 0, 6.2832); ctx.fillStyle = '#1a0a14'; ctx.fill(); ctx.beginPath(); ctx.arc(0, 0, 5.6, 0, 6.2832); ctx.fillStyle = '#ffb02a'; ctx.fill(); ctx.restore(); label('x2', x, y + 0.3 * s, 6.4 * s, 'center', 1, '#ffffff'); return; }
    if (k === 'mag') {
      ctx.lineWidth = 4.6; ctx.strokeStyle = '#1a0a14'; ctx.beginPath(); ctx.arc(0, -0.5, 4, Math.PI, 0); ctx.lineTo(4, 4.6); ctx.moveTo(-4, -0.5); ctx.lineTo(-4, 4.6); ctx.stroke();
      ctx.lineWidth = 2.8; ctx.strokeStyle = '#e8344a'; ctx.beginPath(); ctx.arc(0, -0.5, 4, Math.PI, 0); ctx.lineTo(4, 2.2); ctx.moveTo(-4, -0.5); ctx.lineTo(-4, 2.2); ctx.stroke();
      ctx.strokeStyle = '#e8e8f0'; ctx.beginPath(); ctx.moveTo(4, 2.6); ctx.lineTo(4, 4.4); ctx.moveTo(-4, 2.6); ctx.lineTo(-4, 4.4); ctx.stroke();
      ctx.restore(); return;
    }
    // a heart
    ctx.beginPath(); ctx.moveTo(0, 5.4); ctx.bezierCurveTo(-7.4, 0.6, -5.4, -6, 0, -2.6); ctx.bezierCurveTo(5.4, -6, 7.4, 0.6, 0, 5.4); ctx.closePath();
    ctx.lineWidth = 1.6; ctx.strokeStyle = '#1a0a14'; ctx.stroke(); ctx.fillStyle = k === 'rev' ? '#ff8ab0' : '#ff4a6a'; ctx.fill();
    ctx.strokeStyle = '#ffffff'; ctx.lineWidth = 1.3; ctx.beginPath();
    if (k === 'hp') { ctx.moveTo(-2, 0.4); ctx.lineTo(2, 0.4); ctx.moveTo(0, -1.6); ctx.lineTo(0, 2.4); ctx.stroke(); }
    else { ctx.arc(0, 0.6, 2, -0.3, 4.2); ctx.stroke(); ctx.beginPath(); ctx.moveTo(1.9, -1.2); ctx.lineTo(2.1, 0.5); ctx.lineTo(0.5, 0); ctx.stroke(); }
    ctx.restore();
  }
  // the end of a run (each time it falls: again after getting up): the final score (doubled by '점수 2배'), the coins it
  // earns (the ones paid already taken off), the best and the records (one entry a run, put right after getting up)
  function settleRun() {
    const fin = G.score * (G.x2 ? 2 : 1), earn = Math.floor(fin / COIN_PER), add = Math.max(0, earn - (G.coinsPaid || 0));
    if (!CAPTURE && !AUTO) WALLET.setCoins(WALLET.coins() + add);
    G.coinsPaid = earn; G.final = fin; G.coinsAdd = add;
    let best = 0; try { best = +(localStorage.getItem('bodyrun.best') || 0); } catch (e) { /* storage off */ }
    const isBest = fin > best && (!CAPTURE && !AUTO); if (isBest) { best = fin; try { localStorage.setItem('bodyrun.best', String(best)); } catch (e) { /* storage off */ } }
    keepRun(fin);
    return { fin, earn, add, best, isBest };
  }
  function canRevive() { return !G.revived && (WALLET.has('rev') > 0 || WALLET.coins() >= ITEMS.rev.price); }
  function revive() {
    if (G.mode !== 'over' || !canRevive()) return;
    if (WALLET.has('rev') > 0) WALLET.give('rev', -1); else if (!WALLET.spend(ITEMS.rev.price)) return;
    G.revived = true; G.hp = Math.min(G.hpMax, REVIVE_HP); G.invul = 3; G.slow = 1; G.nudge = 0;
    G.obs = G.obs.filter((o) => o.x + o.w < G.x - 12 || o.x > G.x + 260);    // the way ahead cleared a little
    G.pops.push({ x: G.x + 20, y: GY - G.y - 40, s: TR('부활!', 'Up again!'), t: G.t });
    show('overBox', false); G.mode = 'play'; last = performance.now();
    if (SND.ctx && SND.ctx.state === 'suspended') SND.unlock();
    SND.play('heal'); SND.ambience(true);
  }

  // ---------------------------------------------------------------- (v59) the lobby: after the title, before a run
  // The user's picture of a blue tunnel into the body behind (lobby_bg.webp), the name small at the top left with the
  // best under it, the runner you play standing on the water path (a tap on it, or '캐릭터': pick another), the
  // settings' gear at the top right, and down the right: '게임 시작' (big: off you go with that runner; the first time,
  // pick one first), '나의 기록' (the best, the furthest, how many runs, the last few: kept in this browser), '캐릭터',
  // '상점' (not open yet: a page that says so). The records and the shop come up as a card over it, with '뒤로'
  const LOBBY = { page: 'main', t0: 0, tt: null, press: null, bob: 0, sel: {}, flash: null };
  const ltime = () => (LOBBY.tt !== null ? LOBBY.tt : performance.now() / 1000 - LOBBY.t0);
  let selectMode = 'start';                                  // picking a runner: 'start' (then run) or 'lobby' (then back)
  const savedChar = () => { let c = null; try { c = localStorage.getItem('bodyrun.char'); } catch (e) { /* storage off */ } return c && M.chars.includes(c) ? c : null; };
  const loadJSON = (k, d) => { try { const v = JSON.parse(localStorage.getItem(k) || 'null'); return v === null ? d : v; } catch (e) { return d; } };
  // the buttons (world units): [id, x, y, w, h]; down the right
  function lobbyButtons() {
    const w = Math.min(118, NWf * 0.3), x = NWf - 14 - w;
    return [['start', x, 54, w, 36], ['records', x, 98, w, 22], ['char', x, 124, w, 22], ['shop', x, 150, w, 22], ['gear', NWf - 20, 4.5, 14, 14]];
  }
  const LB_LOOK = {
    start: { ko: '게임 시작', en: 'Play', c: ['#fff4b0', '#ffc02a', '#e07400'], ink: '#4a1c00' },
    records: { ko: '나의 기록', en: 'My records', c: ['#e2ccff', '#9a6ae8', '#5a2ab0'], ink: '#ffffff' },
    char: { ko: '캐릭터', en: 'Characters', c: ['#c8fff0', '#3ac8a0', '#13806a'], ink: '#ffffff' },
    shop: { ko: '상점', en: 'Shop', c: ['#ffd6e6', '#ff6a9a', '#c02a5a'], ink: '#ffffff' },
  };
  function goLobby() {
    G.mode = 'lobby'; LOBBY.page = 'main'; LOBBY.press = null; LOBBY.t0 = performance.now() / 1000;
    for (const k of ['rh', 'orb', 'bb', 'wm', 'mem', 'pk', 'sl', 'yb', 'tw', 'ar', 'cut', 'cutTail']) G[k] = null;
    SND.stopSong(0.2); SND.stopLoop(0.2); SND.spin(null); SND.ambience(false);
    for (const id of ['select', 'pauseBox', 'setBox', 'overBox', 'hudText']) show(id, false);
    for (const f of ['lobby_bg.webp', `logo_${LANG}.webp`]) if (!bmp[f]) decode(f).catch(() => {});
    LOBBY.best = +(loadJSON('bodyrun.best', 0)) || 0;
  }
  function openSelect(mode) { selectMode = mode; G.mode = 'select'; buildSelect(); show('select', true); }
  function lobbyAct(id) {
    SND.play('ui'); buzz(15);
    if (id === 'start') { LOBBY.sel = {}; if (savedChar()) LOBBY.page = 'prep'; else openSelect('prep'); }     // (v60: getting ready first)
    else if (id === 'records' || id === 'shop') LOBBY.page = id;
    else if (id === 'char') openSelect('lobby');
    else if (id === 'gear') { setLabels(); show('setBox', true); }
  }
  function lobbyTap(x, y) {
    if (LOBBY.page !== 'main') {                              // a card: '뒤로', or a tap off it; (v60) the shop's and getting ready's own
      const P = lobbyPanel();
      if ((x > P.x + 6 && x < P.x + 52 && y > P.y + 5 && y < P.y + 23) || x < P.x || x > P.x + P.w || y < P.y || y > P.y + P.h) { SND.play('ui'); LOBBY.page = 'main'; return; }
      if (LOBBY.page === 'shop') shopTap(x, y);
      else if (LOBBY.page === 'prep') prepTap(x, y);
      return;
    }
    for (const [id, bx, by, bw, bh] of lobbyButtons()) if (x > bx - 3 && x < bx + bw + 3 && y > by - 3 && y < by + bh + 3) { LOBBY.press = { id, t: ltime() }; lobbyAct(id); return; }
    const cx = lobbyCharX();                                  // the runner itself: pick another
    if (Math.abs(x - cx) < 26 && y > 96 && y < 170) { SND.play('ui'); openSelect('lobby'); }
  }
  const lobbyCharX = () => Math.min(NWf * 0.36, NWf - 14 - Math.min(118, NWf * 0.3) - 60);
  const lobbyPanel = () => { const w = Math.min(NWf - 24, 344); return { x: NWf / 2 - w / 2, y: 14, w, h: 154 }; };
  // a glossy button: a dark rim, the colour top to bottom, a shine along the top, pressed in for a moment
  function lobbyButton(id, x, y, w, h, t) {
    const L = LB_LOOK[id], pr = LOBBY.press && LOBBY.press.id === id && t - LOBBY.press.t < 0.14 ? 1.6 : 0, r = Math.min(10, h / 2.6);
    rrect(x, y + 2.4, w, h, r); ctx.fillStyle = 'rgba(16,6,14,0.55)'; ctx.fill();          // its shadow
    y += pr;
    rrect(x - 1.3, y - 1.3, w + 2.6, h + 2.6, r + 1.3); ctx.fillStyle = '#1a0a14'; ctx.fill();
    const g = ctx.createLinearGradient(0, y, 0, y + h); g.addColorStop(0, L.c[0]); g.addColorStop(0.45, L.c[1]); g.addColorStop(1, L.c[2]);
    rrect(x, y, w, h, r); ctx.fillStyle = g; ctx.fill();
    ctx.globalAlpha = 0.55; rrect(x + 3, y + 1.6, w - 6, h * 0.36, r * 0.7); ctx.fillStyle = '#ffffff'; ctx.fill(); ctx.globalAlpha = 1;
    // its mark at the left, its name
    const ix = x + (id === 'start' ? 17 : 13), iy = y + h / 2, s = id === 'start' ? 1.25 : 0.85;
    lobbyIcon(id, ix, iy, s);
    const big = id === 'start', name = TR(L.ko, L.en), room = w - (big ? 40 : 32);      // (the name fits right of the mark)
    ctx.font = `900 ${big ? 13 : 8.5}px system-ui, -apple-system, "Noto Sans KR", sans-serif`;
    const fs = (big ? 13 : 8.5) * Math.min(1, room / ctx.measureText(name).width);
    if (big) label(name, x + 32 + (w - 36) / 2, iy + 0.4, fs, 'center', 1, '#ffffff');
    else label(name, x + 26, iy + 0.3, fs, 'left', 1, '#ffffff');
  }
  // the marks: a play triangle, a trophy, a face, a shopping bag (drawn: no emoji)
  function lobbyIcon(id, x, y, s) {
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s);
    ctx.lineJoin = 'round'; ctx.lineWidth = 1.6; ctx.strokeStyle = '#1a0a14'; ctx.fillStyle = '#ffffff';
    ctx.beginPath();
    if (id === 'start') { ctx.moveTo(-3.6, -5.4); ctx.lineTo(5.6, 0); ctx.lineTo(-3.6, 5.4); ctx.closePath(); }
    else if (id === 'records') { ctx.moveTo(-4.4, -4.6); ctx.lineTo(4.4, -4.6); ctx.lineTo(3.6, -0.4); ctx.quadraticCurveTo(2.6, 2.2, 0.9, 2.4); ctx.lineTo(0.9, 3.6); ctx.lineTo(2.8, 3.6); ctx.lineTo(2.8, 5); ctx.lineTo(-2.8, 5); ctx.lineTo(-2.8, 3.6); ctx.lineTo(-0.9, 3.6); ctx.lineTo(-0.9, 2.4); ctx.quadraticCurveTo(-2.6, 2.2, -3.6, -0.4); ctx.closePath(); }
    else if (id === 'char') { ctx.arc(0, 0, 4.9, 0, 6.2832); }
    else if (id === 'shop') { ctx.moveTo(-4.6, -1.8); ctx.lineTo(4.6, -1.8); ctx.lineTo(3.8, 5); ctx.lineTo(-3.8, 5); ctx.closePath(); }
    ctx.stroke(); ctx.fill();
    if (id === 'char') { ctx.fillStyle = '#1a0a14'; for (const sx of [-1.7, 1.7]) { ctx.beginPath(); ctx.arc(sx, -0.8, 0.85, 0, 6.2832); ctx.fill(); } ctx.beginPath(); ctx.arc(0, 1.3, 1.6, 0.15 * Math.PI, 0.85 * Math.PI); ctx.lineWidth = 0.9; ctx.stroke(); }
    if (id === 'shop') { ctx.beginPath(); ctx.arc(0, -1.8, 2.3, Math.PI, 0); ctx.lineWidth = 1.2; ctx.stroke(); }
    if (id === 'records') { ctx.fillStyle = '#ffd23a'; ctx.beginPath(); ctx.arc(0, -1.5, 1.3, 0, 6.2832); ctx.fill(); }
    ctx.restore();
  }
  function renderLobby() {
    device(); ctx.fillStyle = '#000'; ctx.fillRect(0, 0, GW, GH);
    world();
    const t = ltime(), bg = M.sprites.lobby_bg;
    // the picture, filling the screen (breathing in and out a little)
    if (bg && bmp[bg.f]) {
      const z = 1.03 + 0.02 * Math.sin(t * 0.3), sc = Math.max(NWf / bg.w, NH / bg.h) * z, w = bg.w * sc, h = bg.h * sc;
      spr('lobby_bg', (NWf - w) / 2, (NH - h) / 2 + Math.sin(t * 0.23) * 1.5, 1, w, h);
    } else { const g = ctx.createLinearGradient(0, 0, 0, NH); g.addColorStop(0, '#1a3a8a'); g.addColorStop(1, '#0a1640'); ctx.fillStyle = g; ctx.fillRect(0, 0, NWf, NH); }
    // a shade down the right (the buttons) and along the top left (the name, the best)
    { const g = ctx.createLinearGradient(NWf * 0.55, 0, NWf, 0); g.addColorStop(0, 'rgba(10,6,30,0)'); g.addColorStop(1, 'rgba(10,6,30,0.42)'); ctx.fillStyle = g; ctx.fillRect(0, 0, NWf, NH);
      const r = ctx.createRadialGradient(40, 18, 4, 40, 18, 120); r.addColorStop(0, 'rgba(10,6,30,0.38)'); r.addColorStop(1, 'rgba(10,6,30,0)'); ctx.fillStyle = r; ctx.fillRect(0, 0, NWf, NH); }
    // the name, small, at the top left; the best under it
    const lg = M.sprites['logo_' + LANG];
    let ly = 46;
    if (lg && bmp[lg.f]) { const W = Math.min(104, NWf * 0.27), H = W * lg.h / lg.w; spr('logo_' + LANG, 10, 6 + Math.sin(t * 1.6) * 0.8, 1, W, H); ly = 8 + H + 4; }
    if (LOBBY.best > 0) {
      const s = `${TR('최고 기록', 'Best')} ${LOBBY.best.toLocaleString('en-US')}`;
      ctx.font = '900 7px system-ui, -apple-system, "Noto Sans KR", sans-serif'; const w = ctx.measureText(s).width + 12;
      ctx.globalAlpha = 0.8; rrect(12, ly, w, 12, 6); ctx.fillStyle = '#1a0a14'; ctx.fill(); ctx.globalAlpha = 1;
      label(s, 18, ly + 6.2, 7, 'left', 1, '#ffe68a');
    }
    // the runner: standing on the path, breathing, a hop now and then; its shadow; its name under it
    { const c = savedChar() || 'tardigrade', sp = M.sprites['ch_' + c];
      if (sp) {
        const x = lobbyCharX(), feet = 160, k = 2.0, ph = t % 3.2, hop = ph < 0.42 ? Math.sin(Math.PI * ph / 0.42) * 9 : 0;
        const br = Math.sin(t * 3.1), w = sp.w * k * (1 - 0.02 * br), h = sp.h * k * (1 + 0.03 * br);
        ctx.globalAlpha = 0.35 * (1 - hop / 20); ctx.fillStyle = '#000'; ctx.beginPath(); ctx.ellipse(x, feet + 0.5, w * 0.36, 3.2, 0, 0, 6.2832); ctx.fill(); ctx.globalAlpha = 1;
        spr('ch_' + c, x - w / 2, feet - hop - h, 1, w, h);
        const nm = CHAR_NAMES[c] || c; ctx.font = '900 7.5px system-ui, -apple-system, "Noto Sans KR", sans-serif'; const nw = ctx.measureText(nm).width + 14;
        ctx.globalAlpha = 0.72; rrect(x - nw / 2, feet + 4, nw, 12, 6); ctx.fillStyle = '#1a0a14'; ctx.fill(); ctx.globalAlpha = 1;
        label(nm, x, feet + 10.2, 7.5, 'center', 1, '#ffffff');
      } }
    // the buttons; the gear
    for (const [id, x, y, w, h] of lobbyButtons()) {
      if (id === 'gear') {
        rrect(x, y, w, h, 3); ctx.fillStyle = '#1a0a14'; ctx.fill(); rrect(x + 1, y + 1, w - 2, h - 2, 2.3); ctx.fillStyle = '#f4e8ee'; ctx.fill();
        const gx = x + 7, gy = y + 7; ctx.fillStyle = '#1a0a14'; ctx.beginPath();
        for (let k = 0; k < 8; k++) { const a = k * Math.PI / 4, c = Math.cos(a), sn = Math.sin(a);
          const P = [[-1.15, -4.7], [1.15, -4.7], [1.15, -2.6], [-1.15, -2.6]].map(([px, py]) => [gx + px * c - py * sn, gy + px * sn + py * c]);
          ctx.moveTo(P[0][0], P[0][1]); for (const q of P.slice(1)) ctx.lineTo(q[0], q[1]); ctx.closePath(); }
        ctx.fill(); ctx.beginPath(); ctx.arc(gx, gy, 3.5, 0, 6.29); ctx.fill(); ctx.beginPath(); ctx.arc(gx, gy, 1.35, 0, 6.29); ctx.fillStyle = '#f4e8ee'; ctx.fill();
        continue;
      }
      if (id === 'start') {                                    // a glow round the big one, breathing
        const a = 0.35 + 0.25 * Math.sin(t * 3); ctx.globalAlpha = a; rrect(x - 4, y - 4, w + 8, h + 8, 14); ctx.lineWidth = 2.4; ctx.strokeStyle = '#fff2a0'; ctx.stroke(); ctx.globalAlpha = 1;
      }
      lobbyButton(id, x, y, w, h, t);
    }
    if (LOBBY.page === 'main') lobbyCoins(NWf - 26, 11.5, 'right');      // (v60) the coins kept, by the gear
    if (LOBBY.page === 'records') drawRecords();
    else if (LOBBY.page === 'shop') drawShop();
    else if (LOBBY.page === 'prep') drawPrep();
  }
  // a card over the lobby: dimmed behind, the card, its title, '뒤로' at its top left
  function lobbyCard(title) {
    ctx.globalAlpha = 0.55; ctx.fillStyle = '#05030c'; ctx.fillRect(0, 0, NWf, NH); ctx.globalAlpha = 1;
    const P = lobbyPanel();
    rrect(P.x - 1.5, P.y - 1.5, P.w + 3, P.h + 3, 10); ctx.fillStyle = '#1a0a14'; ctx.fill();
    const g = ctx.createLinearGradient(0, P.y, 0, P.y + P.h); g.addColorStop(0, '#2c2050'); g.addColorStop(1, '#160e2c'); rrect(P.x, P.y, P.w, P.h, 9); ctx.fillStyle = g; ctx.fill();
    ctx.globalAlpha = 0.18; rrect(P.x + 3, P.y + 2, P.w - 6, 22, 7); ctx.fillStyle = '#ffffff'; ctx.fill(); ctx.globalAlpha = 1;
    label(title, P.x + P.w / 2, P.y + 14, 11, 'center', 1, '#ffe0a8');
    // '뒤로': a pill with a chevron
    rrect(P.x + 7, P.y + 6, 44, 16, 8); ctx.fillStyle = '#1a0a14'; ctx.fill(); rrect(P.x + 8, P.y + 7, 42, 14, 7); ctx.fillStyle = '#4a3a78'; ctx.fill();
    ctx.strokeStyle = '#ffffff'; ctx.lineWidth = 1.5; ctx.lineJoin = 'round'; ctx.beginPath(); ctx.moveTo(P.x + 17, P.y + 10.5); ctx.lineTo(P.x + 13.5, P.y + 14); ctx.lineTo(P.x + 17, P.y + 17.5); ctx.stroke();
    label(TR('뒤로', 'Back'), P.x + 21, P.y + 14.2, 7, 'left', 1, '#ffffff');
    return P;
  }
  const placeName = (i) => { const st = COURSE[mod(i, COURSE.length)]; return TR(st[1], st[2]); };
  function drawRecords() {
    const P = lobbyCard(TR('나의 기록', 'My records')), S = loadJSON('bodyrun.stats', {}), R = loadJSON('bodyrun.runs', []), f = (n) => (n || 0).toLocaleString('en-US');
    // the bests, down the left
    const lx = P.x + 16, cw = Math.min(118, P.w * 0.36);
    const rows = [[TR('최고 점수', 'Best score'), f(LOBBY.best), '#ffe14a'], [TR('최고 거리', 'Furthest run'), `${f(S.bestD)}m`, '#bfe8ff'],
      [TR('플레이', 'Runs'), TR(`${f(S.plays)}판`, f(S.plays)), '#ffffff'], [TR('가장 멀리 간 곳', 'Furthest place'), S.far !== undefined ? (S.far >= COURSE.length ? TR(`${Math.floor(S.far / COURSE.length) + 1}바퀴 `, `Lap ${Math.floor(S.far / COURSE.length) + 1} · `) : '') + placeName(S.far) : '-', '#ffd0e8']];
    rows.forEach(([k, v, c], i) => { const y = P.y + 36 + i * 29;
      ctx.globalAlpha = 0.35; rrect(lx - 6, y - 4, cw, 25, 6); ctx.fillStyle = '#000000'; ctx.fill(); ctx.globalAlpha = 1;
      label(k, lx, y + 3, 6.2, 'left', 1, '#c8b8e8'); label(v, lx, y + 13.5, i === 0 ? 11 : 9, 'left', 1, c); });
    // the last runs, at the right
    const rx = lx + cw + 8, rw = P.x + P.w - 12 - rx;
    label(TR('최근 기록', 'Recent runs'), rx, P.y + 37, 7.5, 'left', 1, '#ffe0a8');
    if (!R.length) label(TR('아직 기록이 없어요. 한 판 달려 봐요!', 'No runs yet. Go for a run!'), rx + rw / 2, P.y + 90, 7.5, 'center', 1, '#d8cce8');
    R.slice(0, 6).forEach((r, i) => { const y = P.y + 48 + i * 17.5, d = new Date(r.at || 0);
      ctx.globalAlpha = i % 2 ? 0.18 : 0.32; rrect(rx - 3, y - 1, rw + 6, 15.5, 5); ctx.fillStyle = '#000000'; ctx.fill(); ctx.globalAlpha = 1;
      label(`${f(r.s)}${TR('점', '')}`, rx + 2, y + 6.8, 8, 'left', 1, '#ffe68a');
      const ds = `${d.getMonth() + 1}/${d.getDate()} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`;
      ctx.font = '900 6px system-ui, -apple-system, "Noto Sans KR", sans-serif'; const dw = ctx.measureText(ds).width;
      // the distance and the place, made smaller (then cut short) to fit before the date
      let mid = `${f(r.d)}m · ${r.p !== undefined ? placeName(r.p) : ''}`, ms = 6.4; const room = rw * 0.64 - dw - 5;
      ctx.font = `900 ${ms}px system-ui, -apple-system, "Noto Sans KR", sans-serif`;
      if (ctx.measureText(mid).width > room) { ms = Math.max(5, ms * room / ctx.measureText(mid).width); ctx.font = `900 ${ms}px system-ui, -apple-system, "Noto Sans KR", sans-serif`; while (mid.length > 4 && ctx.measureText(mid).width > room) mid = mid.slice(0, -2) + '…'; }
      label(mid, rx + rw * 0.36, y + 6.8, ms, 'left', 1, '#ffffff');
      label(ds, rx + rw, y + 6.8, 6, 'right', 1, '#b8a8d8'); });
  }
  // (v60) the shop: the four things, each a row: its mark, its name and what it does, how many kept, a buy button
  const shopRows = (P) => ['x2', 'mag', 'hp', 'rev'].map((k, i) => ({ k, y: P.y + 32 + i * 29.5, h: 26, bx: P.x + P.w - 12 - 62, bw: 62 }));
  function drawShop() {
    const P = lobbyCard(TR('상점', 'Shop')), f = (n) => n.toLocaleString('en-US');
    lobbyCoins(P.x + P.w - 12, P.y + 14, 'right');
    for (const r of shopRows(P)) {
      const I = ITEMS[r.k], own = WALLET.has(r.k), can = WALLET.coins() >= I.price, pr = LOBBY.press && LOBBY.press.id === 'buy_' + r.k && ltime() - LOBBY.press.t < 0.14;
      ctx.globalAlpha = 0.35; rrect(P.x + 10, r.y, P.w - 20, r.h, 7); ctx.fillStyle = '#000000'; ctx.fill(); ctx.globalAlpha = 1;
      itemIcon(r.k, P.x + 25, r.y + r.h / 2, 1.25);
      label(TR(I.ko, I.en), P.x + 40, r.y + 8.5, 8.5, 'left', 1, '#ffffff');
      label(TR(I.dko, I.den), P.x + 40, r.y + 19, 6, 'left', 1, '#c8b8e8');
      label(TR(`보유 ${own}`, `${own} kept`), r.bx - 8, r.y + r.h / 2 + 0.3, 7, 'right', 1, own ? '#ffe68a' : '#8a7aa8');
      // the buy button: a coin and the price (dim when there are not enough coins)
      const yy = r.y + 3 + (pr ? 1 : 0);
      ctx.globalAlpha = can ? 1 : 0.45;
      rrect(r.bx - 1, yy - 1, r.bw + 2, r.h - 4, 7); ctx.fillStyle = '#1a0a14'; ctx.fill();
      const g = ctx.createLinearGradient(0, yy, 0, yy + r.h - 6); g.addColorStop(0, '#fff4b0'); g.addColorStop(0.5, '#ffc02a'); g.addColorStop(1, '#e07400');
      rrect(r.bx, yy, r.bw, r.h - 6, 6); ctx.fillStyle = g; ctx.fill();
      coinIcon(r.bx + 11, yy + (r.h - 6) / 2, 4.6);
      label(f(I.price), r.bx + 19, yy + (r.h - 6) / 2 + 0.3, 8, 'left', can ? 1 : 0.45, '#ffffff');
      ctx.globalAlpha = 1;
    }
    lobbyFlash();
  }
  function shopTap(x, y) {
    const P = lobbyPanel();
    for (const r of shopRows(P)) if (x > r.bx - 3 && x < r.bx + r.bw + 3 && y > r.y && y < r.y + r.h) {
      LOBBY.press = { id: 'buy_' + r.k, t: ltime() };
      if (WALLET.spend(ITEMS[r.k].price)) { WALLET.give(r.k, 1); SND.play('coin'); buzz(15); LOBBY.flash = { s: TR(`${ITEMS[r.k].ko} 구매!`, `${ITEMS[r.k].en} bought!`), t: ltime(), bad: false }; }
      else { SND.play('miss'); LOBBY.flash = { s: TR('코인이 모자라요', 'Not enough coins'), t: ltime(), bad: true }; }
      return true;
    }
    return false;
  }
  // a word over the card for a moment (bought; not enough coins)
  function lobbyFlash() {
    const F = LOBBY.flash; if (!F) return; const v = ltime() - F.t; if (v > 1.3 || v < 0) return;
    const a = Math.min(1, v / 0.12, (1.3 - v) / 0.3);
    label(F.s, NWf / 2, NH - 12 - v * 6, 10, 'center', a, F.bad ? '#ff9aa8' : '#ffe14a');
  }
  // the coins kept: a coin and the number, in a dark pill (right: its right end at x)
  function lobbyCoins(x, y, align = 'right') {
    const s = WALLET.coins().toLocaleString('en-US');
    ctx.font = '900 8px system-ui, -apple-system, "Noto Sans KR", sans-serif'; const w = ctx.measureText(s).width + 22, x0 = align === 'right' ? x - w : x;
    ctx.globalAlpha = 0.85; rrect(x0, y - 6.5, w, 13, 6.5); ctx.fillStyle = '#1a0a14'; ctx.fill(); ctx.globalAlpha = 1;
    coinIcon(x0 + 7.5, y, 4.4); label(s, x0 + 14, y + 0.4, 8, 'left', 1, '#ffe68a');
  }
  // (v60) getting ready: the runner at the left, the three start items (tap: on or off; one not kept is bought as it
  // starts, if there are coins enough), what it will cost, '출발!'
  const prepTiles = (P) => { const x0 = P.x + 96, w = (P.x + P.w - 12 - x0 - 12) / 3; return START_ITEMS.map((k, i) => ({ k, x: x0 + i * (w + 6), y: P.y + 33, w, h: 78 })); };
  const prepGo = (P) => ({ x: P.x + P.w - 12 - 104, y: P.y + P.h - 34, w: 104, h: 26 });
  const prepCost = () => START_ITEMS.reduce((c, k) => c + (LOBBY.sel[k] && !WALLET.has(k) ? ITEMS[k].price : 0), 0);
  function drawPrep() {
    const P = lobbyCard(TR('출발 준비', 'Get ready')), f = (n) => n.toLocaleString('en-US'), t = ltime();
    lobbyCoins(P.x + P.w - 12, P.y + 14, 'right');
    // the runner
    { const c = savedChar() || 'tardigrade', sp = M.sprites['ch_' + c];
      ctx.globalAlpha = 0.35; rrect(P.x + 10, P.y + 30, 80, 114, 8); ctx.fillStyle = '#000000'; ctx.fill(); ctx.globalAlpha = 1;
      if (sp) { const k = Math.min(64 / sp.w, 60 / sp.h), w = sp.w * k, h = sp.h * k, hop = Math.abs(Math.sin(t * 3)) * 2.5; spr('ch_' + c, P.x + 50 - w / 2, P.y + 100 - h - hop, 1, w, h); }
      label(CHAR_NAMES[c] || c, P.x + 50, P.y + 114, 7.5, 'center', 1, '#ffffff');
      label(TR('로비에서 바꿀 수 있어요', 'Change it in the lobby'), P.x + 50, P.y + 128, 5.2, 'center', 1, '#a898c8'); }
    // the items
    label(TR('시작 아이템 (눌러서 고르기)', 'Start items (tap to pick)'), P.x + 96, P.y + 32, 6.5, 'left', 1, '#c8b8e8');
    for (const q of prepTiles(P)) {
      const I = ITEMS[q.k], on = !!LOBBY.sel[q.k], own = WALLET.has(q.k);
      if (on) { ctx.globalAlpha = 0.5 + 0.25 * Math.sin(t * 5); rrect(q.x - 3, q.y + 3, q.w + 6, q.h + 6 - 6, 10); ctx.lineWidth = 2.2; ctx.strokeStyle = '#ffe14a'; ctx.stroke(); ctx.globalAlpha = 1; }
      rrect(q.x - 1, q.y + 5, q.w + 2, q.h - 4, 9); ctx.fillStyle = '#1a0a14'; ctx.fill();
      const g = ctx.createLinearGradient(0, q.y + 6, 0, q.y + q.h); g.addColorStop(0, on ? '#5a3a9a' : '#3a2a62'); g.addColorStop(1, on ? '#3a2470' : '#221844');
      rrect(q.x, q.y + 6, q.w, q.h - 6, 8); ctx.fillStyle = g; ctx.fill();
      itemIcon(q.k, q.x + q.w / 2, q.y + 24, 1.7);
      label(TR(I.ko, I.en), q.x + q.w / 2, q.y + 42, 8, 'center', 1, '#ffffff');
      label(TR(I.dko, I.den), q.x + q.w / 2, q.y + 52, 5.2, 'center', 1, '#c8b8e8');
      if (own) label(TR(`보유 ${own}`, `${own} kept`), q.x + q.w / 2, q.y + 66, 7, 'center', 1, '#ffe68a');
      else { coinIcon(q.x + q.w / 2 - 12, q.y + 66, 3.8); label(f(I.price), q.x + q.w / 2 - 6, q.y + 66.3, 7.5, 'left', 1, '#ffe68a'); }
      if (on) { ctx.beginPath(); ctx.arc(q.x + q.w - 6, q.y + 11, 5, 0, 6.2832); ctx.fillStyle = '#1a0a14'; ctx.fill(); ctx.beginPath(); ctx.arc(q.x + q.w - 6, q.y + 11, 4, 0, 6.2832); ctx.fillStyle = '#ffd23a'; ctx.fill();
        ctx.beginPath(); ctx.moveTo(q.x + q.w - 8.2, q.y + 11); ctx.lineTo(q.x + q.w - 6.5, q.y + 12.8); ctx.lineTo(q.x + q.w - 3.6, q.y + 9.2); ctx.lineWidth = 1.3; ctx.strokeStyle = '#1a0a14'; ctx.stroke(); }
    }
    // the cost, '출발!'
    const cost = prepCost(), G0 = prepGo(P);
    if (cost > 0) { coinIcon(P.x + 103, G0.y + G0.h / 2, 4.2); label(TR(`${f(cost)} 사용`, `${f(cost)} to spend`), P.x + 110, G0.y + G0.h / 2 + 0.3, 7.5, 'left', 1, '#ffe68a'); }
    else label(TR('아이템 없이 출발해도 돼요', 'You can go without any too'), P.x + 98, G0.y + G0.h / 2 + 0.3, 6.2, 'left', 1, '#a898c8');
    { const pr = LOBBY.press && LOBBY.press.id === 'go' && t - LOBBY.press.t < 0.14 ? 1.4 : 0, y = G0.y + pr;
      ctx.globalAlpha = 0.35 + 0.25 * Math.sin(t * 3); rrect(G0.x - 3, G0.y - 3, G0.w + 6, G0.h + 6, 10); ctx.lineWidth = 2; ctx.strokeStyle = '#fff2a0'; ctx.stroke(); ctx.globalAlpha = 1;
      rrect(G0.x - 1.2, y - 1.2, G0.w + 2.4, G0.h + 2.4, 9); ctx.fillStyle = '#1a0a14'; ctx.fill();
      const g = ctx.createLinearGradient(0, y, 0, y + G0.h); g.addColorStop(0, '#fff4b0'); g.addColorStop(0.45, '#ffc02a'); g.addColorStop(1, '#e07400');
      rrect(G0.x, y, G0.w, G0.h, 8); ctx.fillStyle = g; ctx.fill();
      ctx.globalAlpha = 0.5; rrect(G0.x + 3, y + 1.4, G0.w - 6, G0.h * 0.34, 6); ctx.fillStyle = '#ffffff'; ctx.fill(); ctx.globalAlpha = 1;
      lobbyIcon('start', G0.x + 16, y + G0.h / 2, 0.95);
      label(TR('출발!', 'Go!'), G0.x + G0.w / 2 + 8, y + G0.h / 2 + 0.3, 11, 'center', 1, '#ffffff'); }
    lobbyFlash();
  }
  function prepTap(x, y) {
    const P = lobbyPanel();
    for (const q of prepTiles(P)) if (x > q.x && x < q.x + q.w && y > q.y + 6 && y < q.y + q.h) {
      const k = q.k;
      if (LOBBY.sel[k]) { LOBBY.sel[k] = false; SND.play('ui'); return true; }
      if (WALLET.has(k) || WALLET.coins() >= prepCost() + ITEMS[k].price) { LOBBY.sel[k] = true; SND.play('ui'); buzz(12); }
      else { SND.play('miss'); LOBBY.flash = { s: TR('코인이 모자라요', 'Not enough coins'), t: ltime(), bad: true }; }
      return true;
    }
    const G0 = prepGo(P);
    if (x > G0.x - 3 && x < G0.x + G0.w + 3 && y > G0.y - 3 && y < G0.y + G0.h + 3) {
      LOBBY.press = { id: 'go', t: ltime() };
      const opts = {};
      for (const k of START_ITEMS) if (LOBBY.sel[k]) { if (WALLET.has(k)) { WALLET.give(k, -1); opts[k] = true; } else if (WALLET.spend(ITEMS[k].price)) opts[k] = true; }
      startGame(savedChar() || 'tardigrade', opts);
      return true;
    }
    return false;
  }
  // a run's end, kept (real runs only): the last 20, and the bests
  function keepRun(fin) {
    if (CAPTURE || AUTO) return;
    try {
      const runs = loadJSON('bodyrun.runs', []), S = loadJSON('bodyrun.stats', {}), lap = stationAt(G.x).lap, p = Math.max(0, G.station);
      const rec = { s: fin, d: G.distM, t: Math.round(G.t), p, lap, c: G.char, at: Date.now() };
      if (G.recKept && runs.length) runs[0] = rec; else { runs.unshift(rec); S.plays = (S.plays || 0) + 1; }     // (v60: after getting up, the same run)
      localStorage.setItem('bodyrun.runs', JSON.stringify(runs.slice(0, 20)));
      S.bestD = Math.max(S.bestD || 0, G.distM); S.time = (S.time || 0) + Math.round(G.t) - (G.timeKept || 0); G.timeKept = Math.round(G.t); G.recKept = true;
      const far = lap * COURSE.length + p; if (S.far === undefined || far > S.far) S.far = far;
      localStorage.setItem('bodyrun.stats', JSON.stringify(S));
    } catch (e) { /* storage off */ }
  }

  // ---------------------------------------------------------------- loop
  let last = 0, acc = 0;
  const DT = 1 / 120;
  function frame(now) {
    requestAnimationFrame(frame);
    const el = Math.min(0.1, (now - last) / 1000); last = now;
    if (G.mode === 'play') { acc += el; while (acc >= DT) { step(DT); acc -= DT; } }
    if (G.mode === 'play' || G.mode === 'pause' || G.mode === 'over') render();
    else if (G.mode === 'title') renderTitle();
    else if (G.mode === 'lobby') renderLobby();
  }

  // ---------------------------------------------------------------- start
  (async () => {
    resize();
    const at = qs.has('at') ? COURSE.findIndex((s) => s[0] === qs.get('at')) : -1;
    try {
      const first = [decode('common.webp')];
      if (!CAPTURE || qs.has('title') || qs.has('lobby')) first.push(decode('title_bg.webp'), decode(`logo_${LANG}.webp`), decode('lobby_bg.webp'));     // (v47) the title's (v59: and the lobby's)
      for (let k = -1; k <= 2; k++) for (const f of themeFiles(COURSE[mod(Math.max(at, 0) + k, COURSE.length)][3])) first.push(decode(f));
      if (PRELOAD) for (const t of Object.keys(M.themes)) for (const f of themeFiles(t)) first.push(decode(f));
      await Promise.all(first);
    } catch (e) {
      document.getElementById('loading').textContent = TR('그림을 불러오지 못했어요. 새로고침해 주세요.', "Couldn't load the pictures. Please reload.");
      return;
    }
    buildSelect();
    if (!CAPTURE) SND.setBGM(STAGES.bgm);                    // the running music's file
    getReady();                                              // the songs' files, while you pick
    document.getElementById('loading').hidden = true;
    const auto = qs.get('char');
    if (qs.has('title')) startTitle();
    else if (qs.has('lobby')) goLobby();
    else if (CAPTURE || AUTO || auto) startGame(auto && M.chars.includes(auto) ? auto : 'tardigrade');
    else startTitle();
    if (at >= 0) { G.x = STARTS[at] + 10; G.genX = G.x + 300; G.station = -1; step(0); }
    if (!CAPTURE) requestAnimationFrame((t) => { last = t; frame(t); });
    // test hooks
    window.__ready = true;
    window.__run = (sec) => { const n = Math.round(sec / DT); for (let i = 0; i < n; i++) step(DT); render(); return window.__state(); };
    window.__settle = async () => { while (Object.keys(pending).length) await Promise.all(Object.values(pending)).catch(() => {}); if (G.mode === 'lobby') renderLobby(); else if (G.mode === 'title') renderTitle(); else render(); return Object.keys(bmp).length; };
    window.__state = () => ({ mode: G.mode, t: +G.t.toFixed(2), x: Math.round(G.x), v: +G.v.toFixed(1), hp: +G.hp.toFixed(1), score: G.score, eaten: G.eaten, hits: G.hits,
      station: COURSE[Math.max(0, G.station)][0], seg: G.station, theme: G.theme, lid: +lidAmount().toFixed(2), lastHit: G.lastHit, rot, lap: stationAt(G.x).lap, y: +G.y.toFixed(1), slide: G.slide, obs: G.obs.length, items: G.items.length,
      NW, RS: +RS.toFixed(3), GW, GH, rhSong: G.rh ? G.rh.song.id : null, orbSong: G.orb ? OB.song.id : null, rotation: { ...ROT }, o2n: G.o2n, boost: +G.boost.toFixed(2), boostHeld: +G.boostHeld.toFixed(2), boosts: G.boosts, decoded: Object.keys(bmp).length, atp: G.atp || 0, orbits: G.orbits || 0, orb: G.orb ? G.orb.st : null, bb: G.bb ? G.bb.st : null, wm: G.wm ? G.wm.st : null, mem: G.mem ? G.mem.st : null, pk: G.pk ? G.pk.st : null, sl: G.sl ? G.sl.st : null, yb: G.yb ? G.yb.st : null, tw: G.tw ? G.tw.st : null, ar: G.ar ? G.ar.st : null, games: G.games || 0, huge: G.obs.filter((o) => o.kind === 'huge').length });
    window.__G = G;
    window.__parts = () => scoreParts();
    window.__die = () => { G.hp = 0; };
    window.__title = (tt) => { TITLE.tt = tt; renderTitle(); return { mode: G.mode, run: TITLE.run.map((r) => r.c) }; };
    window.__titleTap = () => titleTap();
    window.__lobby = (tt, page) => { LOBBY.tt = tt; if (page) LOBBY.page = page; renderLobby(); return { mode: G.mode, page: LOBBY.page, buttons: lobbyButtons(), charX: lobbyCharX(), panel: lobbyPanel(), saved: savedChar(), prep: prepTiles(lobbyPanel()), go: prepGo(lobbyPanel()), shop: shopRows(lobbyPanel()), sel: { ...LOBBY.sel }, coins: WALLET.coins(), inv: WALLET.inv() }; };
    window.__tut = () => G.tut && { on: G.tut.on, wait: G.tut.wait, done: { ...G.tut.done }, tips: Object.keys(G.tut.tips) };
    window.__run2 = (sec) => { const n = Math.round(sec / DT); for (let i = 0; i < n; i++) step(DT); return window.__state(); };
    window.__lobbyTap = (x, y) => { lobbyTap(x, y); return { mode: G.mode, page: LOBBY.page, select: !document.getElementById('select').hidden, set: !document.getElementById('setBox').hidden }; };
    window.__mem = () => { let px = 0; const files = {}; for (const [f, b] of Object.entries(bmp)) { const n = b.width * b.height; px += n; files[f] = +(n * 4 / 1e6).toFixed(1); } return { MB: +(px * 4 / 1e6).toFixed(1), files }; };
    window.__prof = PROF;
    window.__orb = () => { const o = G.orb; if (!o) return null; const t = otime();
      return { t: +t.toFixed(3), clock: o.a0 !== null ? 'sound' : 'game', k: o.k, N: OB.N, st: o.st, res: o.res, th: o.st === 'play' ? +(((obAngle(o.k, t, o.next) % 6.2832) + 6.2832) % 6.2832).toFixed(3) : null, off: +o.off.toFixed(3), next: +o.next.toFixed(3), cam: o.cam.map((v) => +v.toFixed(1)) }; };
    window.__orbPlan = (id) => { const pl = id ? orbPlan(STAGES.orb.find((s) => s.id === id)) : OB; return { id: pl.song.id, B: pl.B, ok: pl.ok, N: pl.N, P: pl.P, T: pl.T, hits: pl.hits, swirl: pl.swirl.map((v, i) => v ? i : -1).filter((i) => i >= 0), dir: pl.dir }; };
    window.__stages = STAGES;
    window.__marks = MINI_MARKS; window.__lap = LAP;
    window.__cut = () => (G.cut ? { u: G.cut.ts ? +(G.t - G.cut.ts).toFixed(3) : null, stopped: !!G.cut.ts, swap: !!G.cut.swap, splash: !!G.cut.splash, x: Math.round(G.x) } : null);
    window.__S2 = { STAGE2, S2_X, S2_I, LAP };
    window.__goTo = (kind) => goToPlace(MINI_MARKS.find((m) => m.kind === kind).i);   // (as tapping its mark on the bar)
    window.__orbTap = orbTap;
    window.__boost = startBoost;
    window.__bb = () => { const b = G.bb; if (!b) return null;
      return { st: b.st, k: b.k, res: b.res.slice(), hr: b.hr, gain: b.gain, cur: b.cur.slice(), p: b.p && { type: b.p.type.name, tx: +b.p.tx.toFixed(1), ty: +b.p.ty.toFixed(1), rel: +(b.p.rel - G.t).toFixed(3), arr: +(b.p.arr - G.t).toFixed(3), dt: b.p.dt, d: b.p.d, res: b.p.res } }; };
    window.__bbSwing = () => bbSwing();
    window.__wm = () => { const w = G.wm; if (!w) return null; return { st: w.st, u: w.st === 'play' ? +(G.t - w.t0).toFixed(2) : null, caught: w.caught, missed: w.missed, oops: w.oops, gain: w.gain,
      moles: w.moles.map((m) => { const p = wmPlace(m), s = M.sprites[wmName(m)]; return { h: m.h, kind: m.kind, good: m.good, st: m.st, q: +p.q.toFixed(2), x: +p.x.toFixed(1), y: +(p.y - s.foot[1] * p.k * 0.55).toFixed(1) }; }) }; };
    window.__pk = () => { const p = G.pk; if (!p) return null; return { st: p.st, k: p.k, res: p.res.slice(), gain: p.gain, shot: p.shot ? { ...p.shot } : null, aim: p.aim.slice(), power: p.power, kind: p.kind, needle: pkNeedle(p), pad: p.pad && { ...p.pad } }; };
    window.__pkForce = (gx, gh, power) => { const p = G.pk; if (!p || p.st !== 'aim') return; p.aim = [gx, gh]; pkShoot(); p.power = power; p.kind = pkZone(power); };
    window.__tw = () => { const p = G.tw; if (!p) return null; return { st: p.st, n: p.blocks.length, xs: p.blocks.map((b) => +b.x.toFixed(1)), misses: p.misses, perf: p.perf, best: p.best, gain: p.gain, why: p.why, swing: p.cur ? +twSwing(p).toFixed(1) : null, top: +twTopX(p).toFixed(1), falling: p.fall.length, modes: p.fall.map((f) => f.mode), cam: +p.camS.toFixed(1), k: +p.kS.toFixed(3) }; };
    window.__ar = () => { const p = G.ar; if (!p) return null; const b = p.bird; return { st: p.st, stage: p.stage, res: [...p.res], hits: p.hits, shots: p.shots, streak: p.streak, best: p.best, gain: p.gain, aim: +p.aim.toFixed(3), bird: b ? { st: b.st, s: b.s, x: +b.x.toFixed(1), y: +b.y.toFixed(1), vx: b.vx } : null, arrows: p.arrows.length, bow: arBow(), pad: { ...AR_PAD, bx: NWf - AR_PAD.m }, ready: arReady(p), loaded: !!p.loaded }; };
    window.__yb = () => { const p = G.yb; if (!p) return null; return { st: p.st, k: p.k, res: p.res.slice(), gain: p.gain, pot: p.pot, gold: p.gold, slot: p.slot.slice(), goldSlot: p.slot[p.gold], pick: p.pick, ok: p.ok, moved: p.moved, mv: !!p.mv, lift: p.lift.map((v) => +v.toFixed(1)), cur: p.cur, ask: p.ask, x: [0, 1, 2].map(ybX), foot: YB_FOOT, btn: { ...YB_BTN, cx: NWf / 2 } }; };
    window.__sl = () => { const s = G.sl; if (!s) return null; return { st: s.st, k: s.k, res: s.res.slice(), gain: s.gain, want: s.want && s.want.slice(), reach: !!s.reach, reels: s.reels.map((r) => ({ pos: +r.pos.toFixed(2), spin: r.spin, stop: !!r.stop })), mx: slMX(), btns: SLF.btns.map(([x, y]) => [slMX() + x, slMY() + y]) }; };
    window.__pkKick = (gx, gh) => pkKick(gx, gh, 0.5, 'good');
    window.__memg = () => { const m = G.mem; if (!m) return null; return { st: m.st, seq: m.seq.slice(), k: m.k, round: m.round, res: m.res.slice(), gain: m.gain, best: m.best || 0, at: [0, 1, 2, 3, 4].map(memAt) }; };
    window.__bbTypes = BB_TYPES; window.__bbBallAt = (t) => bbBallAt(t);
    window.__bbAim = (x, y) => { if (G.bb) G.bb.cur = [x, y]; };
    window.__rh = () => { const r = G.rh; if (!r) return null; const t = rtime();
      return { t: +t.toFixed(3), n: r.n, combo: r.combo, maxCombo: r.maxCombo, done: r.done, gain: r.gain,
        notes: r.notes.map((n) => { const o = { b: n.b, kind: n.kind, tn: n.tn, te: n.te, res: n.res, num: n.num };
          if (n.kind === 'p' || n.kind === 'r') { o.x = NWf / 2; o.y = 98; if (n.kind === 'p') o.turns = +n.turns.toFixed(2); else { o.hits = n.hits; o.need = n.need; } } else { const [x, y] = rhPos(n.u, n.v); o.x = x; o.y = y; if (n.dual) o.dual = true; }
          if (n.kind === 's') { const p = rhPath(n); o.path = p.P.filter((_, i) => i % 3 === 0 || i === p.P.length - 1); o.len = p.len; o.inT = n.inT; o.allT = n.allT; o.start = n.start; if (t >= n.tn && t <= n.te) o.ball = rhBall(p, (t - n.tn) / (n.te - n.tn)); }
          return o; }) }; };
    window.__toClient = (x, y) => { const r = cv.getBoundingClientRect(); const X = x * RS, Y = y * RS; const cx = rot ? GH - Y : X, cy = rot ? X : Y;
      return [r.left + cx * r.width / cv.width, r.top + cy * r.height / cv.height]; };
    window.__starts = STARTS;
    window.__hz = { addPit, addDoor, addDrop, addSpike, addShot, hzFam, doorExt, obsBoxes };
    window.__place = (x) => { G.x = x; G.obs = []; G.items = []; G.genX = x + 1e7; G.station = -1; G.mode = 'play'; step(0); G.fade = 1; G.prevTheme = null; render(); return window.__state(); };
  })();
})();
