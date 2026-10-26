// Body Run: a side-scrolling runner through the body (jump, double jump, slide). The world is 180 units tall and as
// wide as the screen's shape allows (300..420 units); it is drawn straight at the screen's own pixel resolution
// from high-resolution art (4 px per unit; the characters at the resolution of their sheet).
// Speed: from 160 units/s, +0.6 every second, up to 900. Jump, double and triple jump (even the highest stays clear of the ceiling);
// more jumps after the third keep you up, but never above the triple jump's highest point.
// Health drains 1/s; heals +25; a hit -15 and a stumble.
(() => {
  'use strict';
  const qs = new URLSearchParams(location.search);
  const CAPTURE = qs.has('capture');            // test hook: no animation loop, the test steps the game
  const AUTO = qs.has('auto');                  // test hook: the game plays itself
  const NO_DEATH = !qs.has('death');            // debugging: health 0 does not end the run (?death turns it on)
  const PRELOAD = qs.has('preload');            // test hook: decode every picture up front

  // ---------------------------------------------------------------- world constants (units, seconds)
  const NH = 180, GY = 150, CEIL = 14, PX = 84;
  const GRAV = 900, JUMP = 326, JUMP2 = 226, JUMP3 = 184, FASTFALL = 2.4;   // single 59 high, double 87.4, triple ~105 (v20: single +10%)
  const JMAX = (JUMP * JUMP + JUMP2 * JUMP2 + JUMP3 * JUMP3) / (2 * GRAV);    // the triple jump at its best (106.2): the 4th and on stop there
  const V0 = 160, ACC = 0.6, VMAX = 900;
  const HP_MAX = 100, DRAIN = 1.0, HIT = 15, HEAL = 25, INVUL = 1.2;
  // the player's box: half-width and height running, sliding (the characters are drawn 0.8 of their old size)
  const PW = 6.4, PH = 19.2, SLW = 8.8, SLH = 10.4;
  const TOPY = CEIL + 10;                       // a safety stop only: a perfect triple jump tops out at about 104 (head at y 27)
  const MAXY = GY - TOPY - PH;                  // ... as a height of the feet above the floor
  const FLOAT_BOTTOM = GY - 15.5, HANG_BOTTOM = GY - 15.5;     // under it a sliding player passes, a running one does not
  // the course: places (id, Korean name, English name, [look, length in units] ...). Every place has a look of its own
  // (the pancreas and the efferent arteriole pass through two); its name shows once, on arrival. After the anus it starts again
  const PLACES = [
    ['esophagus', '식도', 'Esophagus', ['eso', 1500]], ['stomach', '위', 'Stomach', ['stomach', 1900]],
    ['duodenum', '십이지장', 'Duodenum', ['duodenum', 2200]],
    ['liver', '간', 'Liver', ['liver', 2100]],
    ['gallbladder', '담낭', 'Gallbladder', ['gallbladder', 1700]],
    ['pancreas', '췌장', 'Pancreas', ['pancreas', 1700], ['islet', 800]],
    ['spleen', '비장', 'Spleen', ['spleen', 1800]],
    ['capillary', '모세혈관', 'Capillary', ['adrenal', 800]],
    ['renalArt', '신동맥', 'Renal artery', ['renalart', 900]], ['glomerulus', '사구체', 'Glomerulus', ['glomerulus', 800]],
    ['efferent', '수출세동맥', 'Efferent arteriole', ['efferent', 700], ['kidney', 800]],
    ['vein', '정맥', 'Vein', ['ivc', 1500]],
    ['ra', '우심방', 'Right atrium', ['atrium', 900]], ['rv', '우심실', 'Right ventricle', ['ventricle', 1000]],
    ['pulmArt', '폐동맥', 'Pulmonary artery', ['pulmart', 1100]],
    ['lung', '폐', 'Lung', ['bronchiole', 900]], ['alveoli', '폐포', 'Alveoli', ['lung', 900]],
    ['pulmVein', '폐정맥', 'Pulmonary vein', ['pulmvein', 1000]],
    ['la', '좌심방', 'Left atrium', ['latrium', 900]], ['lv', '좌심실', 'Left ventricle', ['lventricle', 1000]],
    ['myoCap', '심근 모세혈관', 'Myocardial capillary', ['myocard', 1700]],
    ['aorta', '대동맥', 'Aorta', ['artery', 1300]], ['carotid', '총경동맥', 'Common carotid artery', ['carotid', 1000]],
    ['thyroid', '갑상선', 'Thyroid', ['thyroid', 800]], ['vertebral', '척추동맥', 'Vertebral artery', ['vertebral', 1100]],
    // the brain from below: in by the medulla, up round the back, the side and the top to the front, out from the middle
    ['medulla', '연수', 'Medulla oblongata', ['medulla', 2000]], ['cerebellum', '소뇌', 'Cerebellum', ['purkinje', 1100]],
    ['occipital', '후두엽', 'Occipital lobe', ['occipital', 1000]], ['temporal', '측두엽', 'Temporal lobe', ['temporal', 1000]],
    ['hippocampus', '해마', 'Hippocampus', ['hippo', 1100]], ['parietal', '두정엽', 'Parietal lobe', ['parietal', 1000]],
    ['frontal', '전두엽', 'Frontal lobe', ['arach', 2100]], ['cortex', '대뇌피질', 'Cerebral cortex', ['pyramidal', 1100]],
    ['callosum', '뇌량', 'Corpus callosum', ['fibres', 2000]],
    // out along the optic nerve into the back of the eye, then through it to the front (no blood in the clear parts)
    ['opticNerve', '시신경', 'Optic nerve', ['opticnerve', 900]], ['retina', '망막', 'Retina', ['retina', 1200]],
    ['vitreous', '유리체', 'Vitreous body', ['vitreous', 1200]], ['lens', '수정체', 'Lens', ['lens', 1100]],
    ['pupil', '눈동자', 'Pupil', ['iris', 1000]], ['cornea', '각막', 'Cornea', ['cornea', 1300]],      // the eye blinks here
    ['jugular', '경정맥', 'Jugular vein', ['vein', 1300]],
    ['sma', '상장간막동맥', 'Superior mesenteric artery', ['sma', 2400]],
    ['jejunalWall', '공장벽', 'Jejunal wall', ['villus', 800]], ['jejunum', '공장', 'Jejunum', ['gut', 2000]], ['ileum', '회장', 'Ileum', ['ileum', 2000]],
    ['cecum', '맹장', 'Cecum', ['cecum', 1100]], ['colon', '대장', 'Large intestine', ['colon', 5700]],
    ['rectum', '직장', 'Rectum', ['rectum', 1100]], ['anus', '항문', 'Anus', ['anus', 900]],
  ];
  // the course as stretches of one look: id, Korean name, English name, look, length, place number
  const COURSE = [];
  PLACES.forEach((p, k) => { for (const [look, len] of p.slice(3)) COURSE.push([p[0], p[1], p[2], look, len, k]); });
  const STARTS = []; let LAP = 0;
  for (const s of COURSE) { STARTS.push(LAP); LAP += s[4]; }
  const CHAR_NAMES = { tardigrade: '물곰', lacto: '유산균', paramecium: '짚신벌레', amoeba: '아메바', daphnia: '물벼룩', pillbug: '공벌레', ladybug: '무당벌레', jelly: '아기 해파리', sub: '초소형 잠수정', phage: '박테리오파지' };
  const PTS = { vitC: 10, o2: 10, iron: 30, omega: 30, fiber: 30, atp: 50, multi: 100, heal: 0 };
  const mod = (a, n) => ((a % n) + n) % n;
  const PILOT_HUGE = 0.58;
  // the booster: every 100 things eaten (anything but a heal), 5 seconds at three times the speed, untouchable (a second's grace after)
  const BOOST_N = 100, BOOST_T = 5, BOOST_K = 3, BOOST_GRACE = 1.0;
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
  function release(fn) { const b = bmp[fn]; if (b) { if (b.close) b.close(); delete bmp[fn]; } }
  const themeFiles = (t) => { const th = M.themes[t]; return [th.far, th.mid, th.fx].filter(Boolean); };
  // the looks of the stations around the player (one back, three ahead) are kept; the rest let go
  function manageThemes(i) {
    const want = new Set();
    for (let k = -1; k <= 3; k++) want.add(COURSE[mod(i + k, COURSE.length)][3]);
    if (G.prevTheme) want.add(G.prevTheme);
    const files = new Set();
    for (const t of want) for (const f of themeFiles(t)) files.add(f);
    for (const f of files) decode(f).catch(() => {});
    if (!PRELOAD) for (const f of Object.keys(bmp)) if (f.startsWith('th_') && !files.has(f)) release(f);
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
    if (M && G.mode) render();
  }
  addEventListener('resize', resize);
  // transforms: world units, or the landscape picture's own pixels (for seamless strips)
  function world() { if (rot) ctx.setTransform(0, RS, -RS, 0, GH, 0); else ctx.setTransform(RS, 0, 0, RS, 0, 0); }
  function device() { if (rot) ctx.setTransform(0, 1, -1, 0, GH, 0); else ctx.setTransform(1, 0, 0, 1, 0, 0); }

  function spr(name, x, y, alpha = 1, w = null, h = null) {
    const s = M.sprites[name]; if (!s) return;
    const im = bmp[s.f]; if (!im) return;
    if (alpha !== 1) ctx.globalAlpha = alpha;
    ctx.drawImage(im, s.r[0], s.r[1], s.r[2], s.r[3], x, y, w ?? s.w, h ?? s.h);
    if (alpha !== 1) ctx.globalAlpha = 1;
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
  function newRun(charName) {
    Object.assign(G, {
      mode: 'play', t: 0, x: 0, v: V0, slow: 1, hp: HP_MAX, score: 0, eaten: 0, hits: 0,
      y: 0, vy: 0, jumps: 0, onGround: true, slide: false, slideHeld: false, fastFall: false,
      invul: 0, nudge: 0, char: charName, obs: [], items: [], pops: [], puffs: [],
      genX: 520, genStation: undefined, lastGate: -1e9, R: rng(12345), nextHeal: 1800, station: -1, theme: COURSE[0][3], prevTheme: null, fade: 1, banner: 0, lapShown: 0,
      blinkAt: -1, blinkR: rng(4242), vt: 0, rh: null, orb: null, bounce: false, pitObj: null,
      o2n: 0, boost: 0, boostT0: -9, boostHeld: 0, boosts: 0, fire: [], fxR: rng(9191),
      intro: [[1950, 'spike'], [3650, 'drop'], [5420, 'pit'], [7250, 'shot'], [9130, 'door']],
    });
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
  function hzFam(look) {
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
  function curSpeed() { return G.orb ? 0 : G.rh ? G.rh.speed : G.v * (0.3 + 0.7 * G.slow) * (G.boost > 0 ? BOOST_K : 1); }
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
  function addShot(x, low, vx) {
    const name = 'hz_shot';
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
      const theme = themeAt(G.genX), th = M.themes[theme], fam = hzFam(theme);
      const coin = th.coin, special = th.special;
      // how hard: from the speed (0 at the start .. 1 at 460/s, about 5 minutes in), then a little more up to 900
      const v = G.v;
      const d = Math.min(1, Math.max(0, (v - V0) / 300)), d2 = Math.min(1, Math.max(0, (v - 460) / 440));
      const gapT = 1.45 - 0.65 * d - 0.15 * d2;          // seconds between patterns
      const R = G.R;
      // weights for the next pattern
      const W = [['rest', 0.14 - 0.08 * d], ['low', 0.28], ['float', 0.15], ['hang', 0.08 + 0.06 * d], ['tall', 0.08 + 0.08 * d], ['lowlow', 0.04 + 0.08 * d], ['lowfloat', 0.02 + 0.06 * d],
        // a triple jump starts ~0.6 s before the tower: above ~480/s that is off the screen, so no towers then
        ['huge', v < 480 ? 0.03 + 0.05 * d : 0], ['sky', v < 480 ? 0.03 : 0],
        // moving ones and quick combinations
        ['bob', 0.04 + 0.08 * d], ['swim', 0.04 + 0.08 * d], ['slidejump', 0.03 + 0.08 * d], ['jumpslide', 0.03 + 0.08 * d], ['lowtall', 0.02 + 0.06 * d],
        // v19: holes, doors, drops, spikes, shots: a few from the start, more and harder as it speeds up
        ['pit', 0.05 + 0.10 * d + 0.06 * d2], ['door', fam.door ? 0.04 + 0.08 * d + 0.05 * d2 : 0], ['drop', 0.05 + 0.08 * d + 0.05 * d2],
        ['spike', 0.05 + 0.09 * d + 0.05 * d2], ['shot', 0.04 + 0.09 * d + 0.06 * d2]];
      let r = R() * W.reduce((a, b) => a + b[1], 0), pat = 'rest';
      for (const [p, w] of W) { if ((r -= w) <= 0) { pat = p; break; } }
      // the way into each new look is guarded: a gate of three in quick succession
      if (G.genStation !== undefined && theme !== G.genStation && G.genX - (G.lastGate || -1e9) > v * 12) { pat = 'gate'; G.lastGate = G.genX; }
      G.genStation = theme;
      // each new kind of hazard is first shown on its own, early on
      if (G.intro.length && G.genX > G.intro[0][0] && pat !== 'gate' && (G.intro[0][1] !== 'door' || fam.door)) pat = G.intro.shift()[1];
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
        const n = d > 0.5 && R() < 0.5 * d ? 2 : 1;
        let meet = x + 40, low = R() < 0.5;
        for (let k = 0; k < n; k++) {
          addShot(meet + shift, low, vx);
          if (low) jumpArc(meet - v * 0.3, v, coin); else coinRow(meet - 30, 5, GY - 7, coin);
          meet += v * 0.75 + 30; low = !low;
        }
        used = meet - x;
      }
      // a heal now and then, a rare multivitamin
      if (G.genX > G.nextHeal) { addItem(G.genX + used / 2, GY - 54, 'heal'); G.nextHeal = G.genX + 2200 + R() * 1200; }
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
  function doJump() { if (G.mode === 'play' && !busy()) pressed.jump = true; }
  function setSlide() { G.slideHeld = [...held.values()].includes('slide') || keySlide; }
  let keySlide = false;
  cv.addEventListener('pointerdown', (e) => {
    SND.unlock();
    if (G.mode !== 'play') return;
    const [nx, ny] = toWorld(e);
    if (nx > NW - 26 && ny < 26) { pause(); return; }
    if (G.rh) { rhDown(e.pointerId, nx, ny); e.preventDefault(); return; }
    if (G.orb) { orbTap(); e.preventDefault(); return; }
    const side = nx < NW / 2 ? 'jump' : 'slide';
    held.set(e.pointerId, side);
    if (side === 'jump') doJump();
    setSlide(); e.preventDefault();
  });
  const up = (e) => { held.delete(e.pointerId); setSlide(); rhUp(e.pointerId); };
  cv.addEventListener('pointerup', up); cv.addEventListener('pointercancel', up); cv.addEventListener('pointerleave', up);
  cv.addEventListener('pointermove', (e) => { if (G.rh && G.mode === 'play') { const [nx, ny] = toWorld(e); rhMove(e.pointerId, nx, ny); } });
  document.addEventListener('visibilitychange', () => { if (document.hidden && G.mode === 'play') pause(); });
  addEventListener('keydown', (e) => {
    if (e.repeat) return;
    if (G.orb && G.mode === 'play' && ['Space', 'ArrowUp', 'ArrowDown', 'KeyW', 'KeyS', 'Enter', 'KeyJ', 'KeyF'].includes(e.code)) { orbTap(); e.preventDefault(); return; }
    if (e.code === 'Space' || e.code === 'ArrowUp' || e.code === 'KeyW') { doJump(); e.preventDefault(); }
    if (e.code === 'ArrowDown' || e.code === 'KeyS') { keySlide = true; setSlide(); e.preventDefault(); }
    if (e.code === 'Escape' || e.code === 'KeyP') { if (G.mode === 'play') pause(); else if (G.mode === 'pause') resume(); }
  });
  addEventListener('keyup', (e) => { if (e.code === 'ArrowDown' || e.code === 'KeyS') { keySlide = false; setSlide(); } });

  // ---------------------------------------------------------------- the mini-games' songs (stages.js): five each, in turn
  // Each go of a mini-game takes the next of its songs; the turn is kept (the next run goes on from it). The songs are
  // files: fetched when the page opens, decoded once the sound is on (the next one of each, ahead of time).
  // ?rhsong=N / ?orbsong=N (1..5): always that song (tests).
  const SND = window.BodySound, STAGES = window.BodyStages;
  const ROT = { rh: 0, orb: 0 }, FIX = { rh: +qs.get('rhsong') || 0, orb: +qs.get('orbsong') || 0 };
  for (const k of ['rh', 'orb']) { try { ROT[k] = (+localStorage.getItem('bodyrun.' + k + 'Song') || 0) % STAGES[k].length; } catch (e) { /* storage off */ } }
  const songFor = (k) => STAGES[k][FIX[k] ? (FIX[k] - 1) % STAGES[k].length : ROT[k]];
  function getReady() {
    if (CAPTURE) return;
    for (const k of ['rh', 'orb']) { const s = songFor(k); SND.fetchSong(s).catch(() => {}); if (SND.ctx) SND.prepare(s).catch(() => {}); }
  }
  function takeSong(k) {
    const s = songFor(k);
    if (!FIX[k]) { ROT[k] = (ROT[k] + 1) % STAGES[k].length; try { localStorage.setItem('bodyrun.' + k + 'Song', String(ROT[k])); } catch (e) { /* storage off */ } }
    if (SND.ctx) SND.prepare(s).catch(() => {});
    getReady();
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
      notes.push(n);
    }
    const secs = RH_LEAD + song.end * B + RH_DONE;
    G.rh = { song, B, first: song.first, end: song.end, speed: Math.max(30, Math.min(60, RH_ROOM / secs)),
      gt0: G.t + RH_LEAD, a0: null, wait: audio ? G.t : null, notes, combo: 0, maxCombo: 0, n: { perfect: 0, good: 0, miss: 0 },
      pops: [], ptr: new Map(), done: false, doneT: 0, gain: 0, lastBeat: -99, flash: -9 };
    if (audio) SND.ambience(false);
    G.slideHeld = false; held.clear();
    for (const id of ['lj', 'ls']) document.getElementById(id).hidden = true;
  }
  // the song is in: start it (and the stage's clock with it); or it did not come: go on by the game's clock, silent
  function rhStartSong() {
    const r = G.rh;
    if (SND.ready(r.song) && SND.live()) { r.a0 = SND.ctx.currentTime + RH_LEAD; SND.playSong(r.song, r.a0); r.wait = null; }
    else if (G.t - r.wait > SONG_WAIT) { r.gt0 = G.t + RH_LEAD; r.wait = null; }
  }
  function endRhythm() {
    G.rh = null; resumeBoost();
    SND.stopSong(0.5); SND.spin(null); SND.ambience(true);
    G.genX = Math.max(G.genX, G.x + NW * 0.8);              // a moment to get going again
    G.banner = G.t;                                          // and where you are now
    for (const id of ['lj', 'ls']) document.getElementById(id).hidden = false;
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
      const base = n.kind === 'p' ? (res === 'perfect' ? 100 : 40) : n.kind === 's' ? (res === 'perfect' ? 50 : 20) : (res === 'perfect' ? 30 : 10);
      const pts = Math.round(base * (1 + Math.min(r.combo, 40) / 25));
      G.score += pts; r.gain += pts;
      G.hp = Math.min(HP_MAX, G.hp + (res === 'perfect' ? 1.5 : 0.5));
    }
    r.pops.push({ x, y, s: res === 'perfect' ? 'Perfect' : res === 'good' ? 'Good' : 'Miss', res, t: G.t });
    SND.play(res);
  }
  // a touch on the stage
  function rhDown(id, x, y) {
    const r = G.rh; if (!r) return;
    r.ptr.set(id, { x, y, ang: null });
    if (r.done) return;
    const t = rtime();
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
          if (n.turns > n.need) { const extra = Math.floor(n.turns - n.need) * 20; G.score += extra; r.gain += extra; }
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
      label('심장이 두근두근!', NWf / 2, 66, 17, 'center', a, '#ffd0dc');
      label('원은 고리가 겹칠 때 터치 · 공은 잡고 따라가기 · 원판은 빙빙', NWf / 2, 86, 7, 'center', a, '#ffffff');
      label(r.song.name, NWf / 2, 100, 7.5, 'center', a * 0.9, '#ffe0a8');
      const c = r.first - Math.floor(t / B);
      if (t > 0 && c >= 1 && c <= 4) label(String(c), NWf / 2, 126, 16, 'center', a * (1 - (t / B) % 1), '#ffffff');
    }
    // notes, later ones underneath
    for (let i = r.notes.length - 1; i >= 0; i--) {
      const n = r.notes[i];
      if (n.kind === 'p') { if (!n.res && t >= n.tn - 0.4) drawSpinner(n, t); continue; }
      const show = t >= n.tn - RH_AR - 0.15;
      if (!show) continue;
      const fade = Math.min(1, (t - (n.tn - RH_AR - 0.15)) / 0.25);
      if (n.kind === 's') {
        if (n.res && t > n.te + 0.15) continue;
        drawSlider(n, t, fade);
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
    if (r.combo >= 2 && !r.done) label(`${r.combo} 콤보`, 18, NH - 14, 10, 'left', 1, '#fff3c8');
    if (r.done) {
      const a = Math.min(1, (G.t - r.doneT) / 0.25) * Math.min(1, (RH_DONE - (G.t - r.doneT)) / 0.3);
      ctx.globalAlpha = a * 0.78; rrect(NWf / 2 - 110, 54, 220, 74, 8); ctx.fillStyle = '#1a0a14'; ctx.fill(); ctx.globalAlpha = 1;
      label('리듬 끝!', NWf / 2, 70, 14, 'center', a, '#ffd0dc');
      label(`Perfect ${r.n.perfect}  ·  Good ${r.n.good}  ·  Miss ${r.n.miss}`, NWf / 2, 92, 8.5, 'center', a, '#ffffff');
      label(`최대 콤보 ${r.maxCombo}  ·  +${r.gain.toLocaleString('en-US')}점`, NWf / 2, 110, 8.5, 'center', a, '#ffe68a');
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
    label(t < n.tn ? '준비' : '돌려!', cx, cy - 4, 12, 'center', a, '#ffffff');
    label(`${Math.min(n.need, Math.floor(n.turns))} / ${n.need}바퀴`, cx, cy + 12, 7.5, 'center', a, '#ffe68a');
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
  const busy = () => !!(G.rh || G.orb);
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
    G.orb = { gx0: G.x, cam0, cam: cam0.slice(), gt0: G.t + OB_LEAD, a0: null, wait: audio ? G.t : null, k: 0, st: 'play', stT: G.t,
      res: { perfect: 0, early: 0, late: 0, miss: 0 }, pops: [], landT: -9, inT: G.t, off: 0, next: OB.T[1] };
    G.slideHeld = false; held.clear(); pressed.jump = false;
    for (const id of ['lj', 'ls']) document.getElementById(id).hidden = true;
    if (audio) SND.ambience(false);
  }
  // the song is in: start it (and the stage's clock with it); or it did not come: go on by the game's clock, silent
  function orbStartSong() {
    const o = G.orb;
    if (SND.ready(OB.song) && SND.live()) { o.a0 = SND.ctx.currentTime + OB_LEAD; SND.playSong(OB.song, o.a0); o.wait = null; }
    else if (G.t - o.wait > SONG_WAIT) { o.gt0 = G.t + OB_LEAD; o.wait = null; }
  }
  function endOrbit() {
    G.orb = null; G.orbits = (G.orbits || 0) + 1; resumeBoost();
    SND.stopSong(0.5); SND.ambience(true);
    G.genX = Math.max(G.genX, G.x + NW * 0.8);
    G.banner = G.t;
    for (const id of ['lj', 'ls']) document.getElementById(id).hidden = false;
  }
  // a miss: the swing carries on round and the same tile comes up again two beats later (and so does all after it);
  // the song goes back two beats, so the tile and its note come round together again
  function orbMiss(why) {
    const o = G.orb, B = OB.B;
    o.res.miss++; o.off += 2 * B; o.next += 2 * B;
    o.pops.push({ k: o.k + 1, res: 'miss', s: why === 'early' ? '빨라요' : '놓침', t: G.t });
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
      label(p.res === 'perfect' ? '완벽' : p.res === 'early' ? '빠름' : p.res === 'late' ? '느림' : p.s, x, y - 16 - u * 8, 7.5, 'center', al * (1 - u * u),
        p.res === 'perfect' ? '#ffe68a' : p.res === 'early' ? '#a8e0ff' : p.res === 'late' ? '#ffc08a' : '#ff8a9a');
    }
    ctx.restore();
    ctx.globalAlpha = 1;
    // words: the title and the song's name until the first tile; a count of three into it
    const B = OB.B;
    if (o.st === 'play' && t < OB.T[1]) {
      const a = Math.min(1, (G.t - o.stT) / 0.3) * Math.min(1, (OB.T[1] - t) / 0.3);
      label('박자 맞춰 빙글빙글!', NWf / 2, 46, 15, 'center', a, '#ffe0a8');
      label('돌던 쪽이 다음 칸에 닿을 때 터치 · 놓치면 한 바퀴 더 돌고 그 칸부터', NWf / 2, 64, 7, 'center', a, '#ffffff');
      label(OB.song.name, NWf / 2, 77, 7.5, 'center', a * 0.9, '#ffe0a8');
      if (t > 0) { const c = OB.hits[1] - Math.floor(t / B); if (c >= 1 && c <= 3) label(String(c), NWf / 2, 136, 20, 'center', a * (1 - 0.7 * ((t / B) % 1)), '#ffffff'); }
    }
    if (o.st === 'done') {
      const u = G.t - o.stT, a = Math.min(1, u / 0.25) * Math.max(0, Math.min(1, (OB_DONE - u) / 0.35));
      ctx.globalAlpha = a * 0.78; rrect(NWf / 2 - 110, 54, 220, 74, 8); ctx.fillStyle = '#1a0a14'; ctx.fill(); ctx.globalAlpha = 1;
      label('통과!', NWf / 2, 70, 14, 'center', a, '#ffe0a8');
      const r = o.res, all = r.perfect + r.early + r.late + r.miss;
      label(`완벽 ${r.perfect}  ·  빠름 ${r.early}  ·  느림 ${r.late}  ·  놓침 ${r.miss}`, NWf / 2, 92, 8.5, 'center', a, '#ffffff');
      label(`정확도 ${Math.round(100 * r.perfect / Math.max(1, all))}%`, NWf / 2, 110, 8.5, 'center', a, '#ffe68a');
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
    if (jump) pressed.jump = true;
    G.slideHeld = slide && !jump;
  }

  // ---------------------------------------------------------------- step
  function step(dt) {
    if (G.mode !== 'play') return;
    if (AUTO && !busy() && !(G.boost > 0)) pilot();
    G.t += dt;
    if (!busy()) G.vt += dt;                                // the speed does not climb during the rhythm and orbit stages
    G.v = Math.min(VMAX, V0 + ACC * G.vt);
    G.slow = Math.min(1, G.slow + dt / 0.8);
    if (G.boost > 0) {                                       // the booster running out: a second of grace
      G.boost -= dt; G.slow = 1;
      if (G.boost <= 0) { G.boost = 0; G.invul = Math.max(G.invul, BOOST_GRACE); }
    }
    G.x += curSpeed() * dt;
    stepFire(dt);
    if (G.rh) stepRhythm(dt);
    if (G.orb) stepOrbit(dt);
    G.nudge = Math.max(0, G.nudge - dt * 30);
    moveObs(dt);
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
        if (!p && G.y > -5) { G.y = 0; G.vy = 0; G.onGround = true; G.jumps = 0; G.bounce = false; G.pitObj = null; puff(G.x - 6, 3); }
        else if (!p) fallOut(G.pitObj || { x: G.x - 20, w: 0 });         // under the floor past the hole: its far wall
        else { G.pitObj = p; if (G.y < -24) fallOut(p); }
      }
    }
    const wasSlide = G.slide;
    G.slide = G.slideHeld && G.onGround && !busy();
    if (G.slide && !wasSlide) SND.play('slide');
    // health
    if (!busy()) G.hp = Math.max(0, G.hp - DRAIN * dt);
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
        if (!it.mag && G.boost > 0) { const dx = it.x - G.x, dy = it.y - pcy; if (dx * dx + dy * dy < MAG_R * MAG_R && dx > -40) { it.mag = true; it.magT = 0; } }
        if (it.mag) { it.magT += dt; const q = Math.min(1, dt * (7 + 40 * it.magT)); it.x += (G.x - it.x) * q; it.y += (pcy - it.y) * q; }
      }
    }
    // eating
    for (const it of G.items) {
      if (it.taken || it.x < b[0] - 12 || it.x > b[2] + 12) continue;
      const cx = (b[0] + b[2]) / 2, cy = (b[1] + b[3]) / 2;
      if (Math.abs(it.x - cx) < (b[2] - b[0]) / 2 + 6 && Math.abs(it.y - cy) < (b[3] - b[1]) / 2 + 6) {
        it.taken = true; it.t = G.t;
        if (it.kind === 'heal') G.hp = Math.min(HP_MAX, G.hp + HEAL);
        if (it.kind !== 'heal' && !(G.boost > 0) && !busy() && ++G.o2n >= BOOST_N) startBoost();     // everything but the heal counts
        G.score += PTS[it.kind]; G.eaten++; if (it.kind === 'atp') G.atp = (G.atp || 0) + 1;
        SND.play(it.kind === 'heal' ? 'heal' : it.kind === 'atp' ? 'atp' : PTS[it.kind] >= 30 ? 'special' : 'coin');
        if (PTS[it.kind] >= 30 || it.kind === 'heal') G.pops.push({ x: it.x, y: it.y - 8, s: it.kind === 'heal' ? '+' + HEAL : '+' + PTS[it.kind], t: G.t });
      }
    }
    if (G.onGround && !G.slide && Math.floor(G.t * 8) !== Math.floor((G.t - dt) * 8)) puff(G.x - 10, 1);
    G.puffs = G.puffs.filter((p) => G.t - p.t < 0.45);
    G.pops = G.pops.filter((p) => G.t - p.t < 0.8);
    // where we are
    const s = stationAt(G.x);
    if (s.i !== G.station) {
      const arrived = G.station < 0 || COURSE[G.station][5] !== s.st[5];       // a new place (not just a new look in it)
      G.station = s.i;
      const th = s.st[3];
      if (th !== G.theme) { G.prevTheme = G.theme; G.theme = th; G.fade = 0; }
      if (arrived) { if (!busy()) G.banner = G.t; setLabel(s.st, s.lap); if (s.st[0] === 'ra' && !busy()) startRhythm(); if (s.st[0] === 'vertebral' && !busy()) startOrbit(); }
      manageThemes(s.i);
    }
    G.fade = Math.min(1, G.fade + dt / 0.7);
    // passing the cornea the eye blinks now and then (sometimes twice quickly); its own random, so the course is unchanged
    if (COURSE[G.station][0] === 'cornea') {
      if (G.blinkAt < 0) G.blinkAt = G.t + 0.6;
      else if (G.t > G.blinkAt + BLINK) G.blinkAt = G.t + (G.blinkR() < 0.25 ? 0.12 : 0.9 + G.blinkR() * 1.5);
    } else G.blinkAt = -1;
    if (G.hp <= 0 && !NO_DEATH) gameOver();
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
    const R = G.fxR, n = 'ch_' + G.char, w = SW(n), h = SH(n) * (G.slide ? 0.62 : 1);
    const smoke = !burst && R() < 0.22;
    G.fire.push({ x: PX - w * 0.38 + R() * 4, y: GY + 1 - G.y - h * (0.25 + 0.5 * R()), vx: -(70 + R() * (burst ? 160 : 110)), vy: (R() - 0.5) * (burst ? 90 : 36) - 10,
      age: 0, life: smoke ? 0.55 + R() * 0.2 : 0.22 + R() * 0.2, r: smoke ? 2.2 + R() * 1.5 : 0.7 + R() * 1.1, smoke });
  }
  function stepFire(dt) {
    if (G.boost > 0) {
      G.fireAcc = (G.fireAcc || 0) + dt * 130; while (G.fireAcc >= 1) { addSpark(false); G.fireAcc -= 1; }
      const h = SH('ch_' + G.char) * (G.slide ? 0.62 : 1);
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
  // the magnetic field while boosting: a clear, nearly invisible bubble round the body that sparkles: a thin bright
  // rim, glossy highlights, little stars twinkling round it and a glint running along the rim
  function drawField(sx, feet, w, h) {
    if (!(G.boost > 0)) return;
    const k = Math.min(1, (G.t - G.boostT0) / 0.2) * Math.min(1, G.boost / 0.35);
    const cy = feet - h * 0.5, R = Math.max(w, h) * 0.62 + 0.4 * Math.sin(G.t * 6);
    const g = ctx.createRadialGradient(sx, cy, R * 0.3, sx, cy, R);
    g.addColorStop(0, 'rgba(255,255,255,0)'); g.addColorStop(0.8, `rgba(255,255,255,${0.05 * k})`); g.addColorStop(1, `rgba(255,255,255,${0.16 * k})`);
    ctx.fillStyle = g; ctx.beginPath(); ctx.arc(sx, cy, R, 0, 6.29); ctx.fill();
    ctx.lineWidth = 3.0; ctx.strokeStyle = `rgba(255,255,255,${0.2 * k})`; ctx.stroke();
    ctx.beginPath(); ctx.arc(sx, cy, R + 0.95, 0, 6.29); ctx.lineWidth = 0.6; ctx.strokeStyle = `rgba(26,10,20,${0.3 * k})`; ctx.stroke();
    ctx.beginPath(); ctx.arc(sx, cy, R, 0, 6.29); ctx.lineWidth = 1.25; ctx.strokeStyle = `rgba(255,255,255,${0.95 * k})`; ctx.stroke();
    ctx.lineCap = 'round';
    ctx.lineWidth = 1.2; ctx.strokeStyle = `rgba(255,255,255,${0.75 * k})`;          // gloss, upper left and a dot lower right
    ctx.beginPath(); ctx.arc(sx, cy, R * 0.78, Math.PI * 1.1, Math.PI * 1.4); ctx.stroke();
    ctx.fillStyle = `rgba(255,255,255,${0.6 * k})`; ctx.beginPath(); ctx.arc(sx + R * 0.5, cy + R * 0.5, 0.8, 0, 6.29); ctx.fill();
    // the pull: dashed rings of force closing in from the reach of the magnet onto the bubble
    ctx.setLineDash([3.2, 2.6]);
    for (let i = 0; i < 3; i++) {
      const u = (G.t * 1.6 + i / 3) % 1, rr = R + (MAG_R * 0.85 - R) * (1 - u) * (1 - u);
      const a = Math.sin(u * Math.PI) * 0.55 * k;
      ctx.lineDashOffset = -G.t * 30 * (i % 2 ? 1 : -1);
      ctx.lineWidth = 0.9 + 0.8 * u; ctx.strokeStyle = `rgba(255,255,255,${a})`;
      ctx.beginPath(); ctx.arc(sx, cy, rr, 0, 6.29); ctx.stroke();
    }
    ctx.setLineDash([]); ctx.lineDashOffset = 0;
    // specks of light drawn in along curling paths
    for (let i = 0; i < 14; i++) {
      const u = (G.t * (0.9 + 0.25 * hash(i, 2)) + hash(i, 1)) % 1, ease = u * u;
      const ang = hash(i, 3) * 6.283 + ease * 2.2, rr = R + (MAG_R * 0.9 - R) * (1 - ease);
      const x = sx + Math.cos(ang) * rr, y = cy + Math.sin(ang) * rr * 0.92;
      const tx = sx + Math.cos(ang - 0.25) * (rr + 7), ty = cy + Math.sin(ang - 0.25) * (rr + 7) * 0.92;
      ctx.strokeStyle = `rgba(255,255,255,${0.7 * u * k})`; ctx.lineWidth = 0.9;
      ctx.beginPath(); ctx.moveTo(tx, ty); ctx.lineTo(x, y); ctx.stroke();
      ctx.fillStyle = `rgba(255,255,255,${0.95 * u * k})`; ctx.beginPath(); ctx.arc(x, y, 0.55 + 0.5 * u, 0, 6.29); ctx.fill();
    }
    // a glint running round the rim
    const ga = G.t * 2.4;
    glowAt(sx + Math.cos(ga) * R, cy + Math.sin(ga) * R, 3.2, '255,255,255', 0.8 * k);
    ctx.fillStyle = `rgba(255,255,255,${k})`; star4(sx + Math.cos(ga) * R, cy + Math.sin(ga) * R, 2.4, G.t * 4); ctx.fill();
    // stars twinkling on the rim, each in its own time
    for (let i = 0; i < 6; i++) {
      const tw = Math.max(0, Math.sin(G.t * (5 + i * 0.7) + i * 1.9)), a = i * 1.05 + G.t * 0.5;
      if (tw < 0.15) continue;
      const x = sx + Math.cos(a) * R * 1.02, y = cy + Math.sin(a) * R * 1.02, r = (1.1 + 1.7 * tw) * k;
      ctx.fillStyle = `rgba(255,255,255,${0.95 * tw * k})`; star4(x, y, r, a); ctx.fill();
    }
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
      if (o.kind === 'hang') spr(o.name, sx, o.y);
      else if (o.kind === 'door') drawDoor(o, sx);
      else if (o.kind === 'spike' && o.e > 0) spr(o.name, sx, o.y);
      else if (o.kind === 'drop' && o.st === 'hang') {          // swelling on the ceiling, wobbling before it lets go
        const wob = o.wob ? Math.min(1, o.wob / 0.3) : 0, k = 1 + wob * (0.18 + 0.07 * Math.sin(G.t * 34));
        const w = SW(o.nd), h = SH(o.nd);
        spr(o.nd, sx + (o.w - w / (0.92 + 0.08 * k)) / 2, DROP_Y0, 1, w / (0.92 + 0.08 * k), h * k);
      }
    }
    device();
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
    ctx.fillStyle = 'rgba(0,0,0,0.26)';
    for (const o of G.obs) if (o.kind === 'low' || o.kind === 'tall' || o.kind === 'huge') { const sx = o.x - cam; if (sx < NWf && sx + o.w > 0) { ctx.beginPath(); ctx.ellipse(sx + o.w / 2, GY + 0.6, o.w * 0.46, 1.9, 0, 0, 6.29); ctx.fill(); } }
    for (const o of G.obs) {
      const sx = o.x - cam; if (sx >= NWf + 30 || sx + o.w <= -30) continue;
      if (o.kind === 'hang' || o.kind === 'door' || o.kind === 'pit') continue;
      if (o.kind === 'spike') { if (o.st === 'warn' || (o.st === 'up' && G.t - o.popT < 0.25)) drawQuake(o, sx); continue; }
      if (o.kind === 'drop') { drawDrop(o, sx); continue; }
      if (o.kind === 'shot') {
        const w = SW(o.name), h = SH(o.name);
        ctx.save(); ctx.translate(sx + w / 2, o.y + h / 2); ctx.rotate(-o.spin); spr(o.name, -w / 2, -h / 2); ctx.restore();
        continue;
      }
      spr(o.name, sx, o.y);
    }
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
      spr(n, sx - SW(n) / 2, it.y - SH(n) / 2 + Math.sin(G.t * 4 + it.ph));
    }
    // the player: a shadow, dust, the character (bobbing as it runs, squashed when sliding); not while on the orbit stage
    if (!G.orb || (G.orb.st === 'done' && G.t - G.orb.stT > OB_DONE - 0.35)) drawPlayer(cam);
    drawShotWarnings(cam);
    for (const p of G.pops) { const u = (G.t - p.t) / 0.8; label(p.s, p.x - cam, Math.max(40, p.y - u * 14), 8, 'center', 1 - u * u); }
  }
  function drawPlayer(cam) {
    const n = 'ch_' + G.char, w = SW(n), h = SH(n);
    const sx = PX - G.nudge;
    const shw = Math.max(6, w * (0.8 - Math.min(0.4, G.y / 120)));
    const overPit = pitAt(G.x);
    if (!overPit && G.y >= 0) { ctx.fillStyle = 'rgba(0,0,0,0.35)'; ctx.beginPath(); ctx.ellipse(sx, GY - 1, shw / 2, 1.6, 0, 0, 6.29); ctx.fill(); }
    const inPit = G.y < 0 && G.pitObj;
    if (inPit) { const p = G.pitObj; ctx.save(); ctx.beginPath(); ctx.rect(-10, -10, NWf + 20, GY + 10); ctx.rect(p.x - cam + 1, GY, p.w - 2, NH); ctx.clip(); }
    for (const p of G.puffs) { const u = (G.t - p.t) / 0.45; ctx.fillStyle = `rgba(255,235,240,${0.5 * (1 - u)})`; ctx.beginPath(); ctx.arc(p.x - cam, p.y - u * 4, p.r + u * 2, 0, 6.29); ctx.fill(); }
    drawFire(sx, GY + 1 - G.y, w, G.slide ? h * 0.62 : h);
    const blink = G.invul > 0 && !(G.boost > 0) && Math.floor(G.t * 14) % 2 === 0;
    if (!blink) {
      if (G.slide) { const sh = h * 0.62, sw = w * 1.12; spr(n, sx - sw / 2, GY + 1 - sh, 1, sw, sh); }
      else { const bob = G.onGround ? (Math.floor(G.t * 10) % 2) : 0; spr(n, sx - w / 2, GY + 1 - h - G.y - bob); }
    }
    if (inPit) ctx.restore();
    drawField(sx, GY + 1 - G.y, w, G.slide ? h * 0.62 : h);
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
    g.addColorStop(0, fk); g.addColorStop(0.18, '#2a0a12'); g.addColorStop(0.55, '#0c0306'); g.addColorStop(1, '#030102');
    ctx.fillStyle = g; ctx.fill();
    const sh = ctx.createLinearGradient(x0, 0, x1, 0);              // the far wall side a little lit
    sh.addColorStop(0, 'rgba(0,0,0,0.35)'); sh.addColorStop(0.7, 'rgba(0,0,0,0)'); sh.addColorStop(1, 'rgba(255,200,200,0.06)');
    ctx.fillStyle = sh; ctx.fill();
    path(); ctx.lineWidth = 1.3; ctx.strokeStyle = '#1a0a14'; ctx.stroke();
  }
  function drawDoor(o, sx) {
    const st = M.sprites[o.nt], sb = M.sprites[o.nb];
    if (o.et > 0.004) spr(o.nt, sx + (o.w - st.w) / 2, HANG_BOTTOM - st.h - DOOR_UP * (1 - o.et));
    if (o.eb > 0.004) spr(o.nb, sx + (o.w - sb.w) / 2, GY + 4 - DOOR_B * o.eb);
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
      spr(o.nd, sx + (o.w - w) / 2, o.y, 1, w * 0.94, h * 1.08);
    } else if (o.st === 'land') {
      const u = Math.min(1, (G.t - o.landT) / 0.14), w = SW(o.np), h = SH(o.np);
      const kx = 1.25 - 0.25 * u, ky = 0.6 + 0.4 * u;
      spr(o.np, sx + (o.w - w * kx) / 2, GY + 2 - h * ky, 1, w * kx, h * ky);
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
    if (alpha !== 1) ctx.globalAlpha = alpha;
    ctx.font = `900 ${size}px system-ui, -apple-system, "Noto Sans KR", sans-serif`;
    ctx.textAlign = align; ctx.textBaseline = 'middle'; ctx.lineJoin = 'round';
    ctx.lineWidth = size * 0.28; ctx.strokeStyle = '#1a0a14'; ctx.strokeText(s, x, y);
    ctx.fillStyle = fill; ctx.fillText(s, x, y);
    if (alpha !== 1) ctx.globalAlpha = 1;
  }
  function rrect(x, y, w, h, r) { ctx.beginPath(); ctx.roundRect ? ctx.roundRect(x, y, w, h, r) : ctx.rect(x, y, w, h); }
  function button(cx, cy, up, on) {
    const r = 16;
    ctx.beginPath(); ctx.arc(cx, cy, r + 0.8, 0, 6.29); ctx.fillStyle = 'rgba(26,10,20,0.55)'; ctx.fill();
    ctx.beginPath(); ctx.arc(cx, cy, r, 0, 6.29); ctx.fillStyle = on ? 'rgba(255,214,110,0.45)' : 'rgba(255,255,255,0.2)'; ctx.fill();
    ctx.lineWidth = 1.3; ctx.strokeStyle = on ? 'rgba(255,230,160,0.95)' : 'rgba(255,255,255,0.8)'; ctx.stroke();
    // an arrow
    const s = up ? -1 : 1;
    ctx.beginPath();
    ctx.moveTo(cx, cy + s * 7); ctx.lineTo(cx + 6.5, cy + s * 0.5); ctx.lineTo(cx + 2.4, cy + s * 0.5); ctx.lineTo(cx + 2.4, cy - s * 6.5);
    ctx.lineTo(cx - 2.4, cy - s * 6.5); ctx.lineTo(cx - 2.4, cy + s * 0.5); ctx.lineTo(cx - 6.5, cy + s * 0.5); ctx.closePath();
    ctx.lineJoin = 'round'; ctx.lineWidth = 1.6; ctx.strokeStyle = '#1a0a14'; ctx.stroke();
    ctx.fillStyle = '#ffffff'; ctx.fill();
  }
  function drawHud() {
    world();
    // health bar
    const x0 = 16, y0 = 7, w = 112, h = 8;
    rrect(x0 - 1.2, y0 - 1.2, w + 2.4, h + 2.4, 3.2); ctx.fillStyle = '#1a0a14'; ctx.fill();
    rrect(x0, y0, w, h, 2.4); ctx.fillStyle = '#3a2030'; ctx.fill();
    const fw = w * G.hp / HP_MAX;
    const low = G.hp < 25 && Math.floor(G.t * 4) % 2 === 0;
    if (fw > 0.5) {
      const gr = ctx.createLinearGradient(0, y0, 0, y0 + h); gr.addColorStop(0, low ? '#ffd0d8' : '#ffb0c0'); gr.addColorStop(0.5, '#ff5a7a'); gr.addColorStop(1, '#a8123a');
      rrect(x0, y0, fw, h, 2.4); ctx.fillStyle = gr; ctx.fill();
      rrect(x0 + 1.5, y0 + 1.1, Math.max(0, fw - 3), 1.4, 0.7); ctx.fillStyle = 'rgba(255,230,236,0.85)'; ctx.fill();
    }
    ctx.fillStyle = 'rgba(26,10,20,0.6)'; for (let k = 1; k < 8; k++) ctx.fillRect(x0 + k * w / 8 - 0.35, y0 + h - 2.2, 0.7, 2.2);
    spr('hud_heart', x0 - 10.5, y0 - 3.2);
    {
      const gx = x0, gy = y0 + h + 4.5, gw = 62, gh = 4.6;
      rrect(gx - 1, gy - 1, gw + 2, gh + 2, 2.6); ctx.fillStyle = '#1a0a14'; ctx.fill();
      rrect(gx, gy, gw, gh, 2); ctx.fillStyle = '#26324a'; ctx.fill();
      const on = G.boost > 0, f = on ? G.boost / BOOST_T : G.o2n / BOOST_N;
      if (f > 0.01) {
        const gr = ctx.createLinearGradient(0, gy, 0, gy + gh);
        if (on) { gr.addColorStop(0, '#fff2b0'); gr.addColorStop(0.5, '#ff9a2a'); gr.addColorStop(1, '#d8361a'); }
        else { gr.addColorStop(0, '#cdeeff'); gr.addColorStop(0.5, '#4aa8f0'); gr.addColorStop(1, '#1f6aa8'); }
        rrect(gx, gy, Math.max(gh, gw * f), gh, 2); ctx.fillStyle = gr; ctx.fill();
      }
      spr('it_' + (M.themes[G.theme].coin || 'o2'), gx - 10, gy - 2.6, 1, 9.2, 9.2);     // the coin of this place
      if (!on) label(`${G.o2n}/${BOOST_N}`, gx + gw + 3, gy + gh / 2 + 0.2, 6, 'left', 1, '#cdeeff');
    }
    // score
    const s = G.score.toLocaleString('en-US');
    const right = NW - 27;
    ctx.font = '900 10px system-ui, -apple-system, "Noto Sans KR", sans-serif';
    const tw = ctx.measureText(s).width;
    spr('it_vitC', right - tw - 19.5, 4.5);
    label(s, right, 11.6, 10, 'right');
    // pause
    rrect(NW - 20, 4.5, 14, 14, 3); ctx.fillStyle = '#1a0a14'; ctx.fill();
    rrect(NW - 19, 5.5, 12, 12, 2.3); ctx.fillStyle = '#f4e8ee'; ctx.fill();
    ctx.fillStyle = '#1a0a14'; ctx.fillRect(NW - 16.2, 8.5, 2, 6); ctx.fillRect(NW - 12.2, 8.5, 2, 6);
    // progress through the body (this lap)
    const p = stationAt(G.x), px0 = NW / 2 - 40, px1 = px0 + 80, py = 31;
    rrect(px0 - 1, py - 1, px1 - px0 + 2, 4, 2); ctx.fillStyle = '#1a0a14'; ctx.fill();
    ctx.fillStyle = '#4a3848'; ctx.fillRect(px0, py, px1 - px0, 2);
    const mk = px0 + (px1 - px0) * p.lx / LAP;
    ctx.fillStyle = '#ff6a8a'; ctx.fillRect(px0, py, mk - px0, 2);
    ctx.beginPath(); ctx.arc(mk, py + 1, 2.6, 0, 6.29); ctx.fillStyle = '#1a0a14'; ctx.fill();
    ctx.beginPath(); ctx.arc(mk, py + 1, 1.7, 0, 6.29); ctx.fillStyle = '#ffffff'; ctx.fill();
    // buttons (not on the rhythm or orbit stage)
    if (busy()) return;
    const jOn = [...held.values()].includes('jump') || (AUTO && !G.onGround);
    button(8 + 16.5, NH - 41 + 16.5, true, jOn);
    button(NW - 43 + 16.5, NH - 41 + 16.5, false, G.slideHeld);
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
    drawScene();
    drawLids();
    drawRhythm();
    drawOrbit();
    drawHud();
    // the place's name grows in for a moment when you arrive
    const u = (G.t - G.banner);
    document.getElementById('place').classList.toggle('big', u < 1.6);
  }

  // ---------------------------------------------------------------- labels, overlays
  function setLabel(st, lap) {
    document.getElementById('pname').textContent = st[1];
    document.getElementById('pen').textContent = st[2] + (lap > 0 ? `  ·  ${lap + 1}바퀴` : '');
  }
  function show(id, on) { document.getElementById(id).hidden = !on; }
  function pause() { if (G.mode !== 'play') return; G.mode = 'pause'; held.clear(); G.slideHeld = false; if (G.rh) G.rh.ptr.clear(); show('pauseBox', true); soundLabel(); if (SND.ctx) SND.ctx.suspend(); }
  function resume() { show('pauseBox', false); G.mode = 'play'; last = performance.now(); SND.unlock(); SND.play('ui'); }
  function soundLabel() { const b = document.getElementById('bSound'); if (b) b.textContent = SND.muted ? '소리 켜기' : '소리 끄기'; }
  function gameOver() {
    G.mode = 'over'; show('overBox', true);
    if (busy()) { G.rh = null; G.orb = null; SND.stopSong(0.3); SND.spin(null); for (const id of ['lj', 'ls']) document.getElementById(id).hidden = false; }
    SND.ambience(false); SND.play('over');
    document.getElementById('overMsg').textContent = `점수 ${G.score.toLocaleString('en-US')} · ${Math.floor(G.t / 60)}분 ${Math.floor(G.t % 60)}초 · ${COURSE[G.station][1]}까지`;
  }
  function startGame(c) {
    try { localStorage.setItem('bodyrun.char', c); } catch (e) { /* storage off */ }
    show('select', false); show('pauseBox', false); show('overBox', false); show('hudText', true);
    for (const id of ['lj', 'ls']) document.getElementById(id).hidden = false;
    if (!CAPTURE) { SND.unlock(); SND.stopSong(0.2); SND.spin(null); SND.play('ui'); SND.ambience(true); getReady(); }
    newRun(c); G.station = -1; step(0); last = performance.now();
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
      b.append(cc, nm); b.onclick = () => startGame(c);
      grid.append(b);
    }
  }
  document.getElementById('bResume').onclick = resume;
  document.getElementById('bRestart').onclick = () => startGame(G.char);
  document.getElementById('bChar').onclick = () => { G.mode = 'select'; G.rh = null; G.orb = null; SND.unlock(); SND.stopSong(0.2); SND.spin(null); SND.ambience(false); show('pauseBox', false); show('overBox', false); show('hudText', false); show('select', true); };
  document.getElementById('bSound').onclick = () => { SND.setMuted(!SND.muted); soundLabel(); };
  document.getElementById('bAgain').onclick = () => startGame(G.char);
  document.getElementById('bChar2').onclick = () => { G.mode = 'select'; SND.ambience(false); show('overBox', false); show('hudText', false); show('select', true); };

  // ---------------------------------------------------------------- loop
  let last = 0, acc = 0;
  const DT = 1 / 120;
  function frame(now) {
    requestAnimationFrame(frame);
    const el = Math.min(0.1, (now - last) / 1000); last = now;
    if (G.mode === 'play') { acc += el; while (acc >= DT) { step(DT); acc -= DT; } }
    if (G.mode === 'play' || G.mode === 'pause' || G.mode === 'over') render();
  }

  // ---------------------------------------------------------------- start
  (async () => {
    resize();
    const at = qs.has('at') ? COURSE.findIndex((s) => s[0] === qs.get('at')) : -1;
    try {
      for (const f of (M.extra || [])) decode(f).catch(() => {});      // the HD booster fire: needed only after 100 items
      const first = [decode('common.webp')];
      for (let k = -1; k <= 2; k++) for (const f of themeFiles(COURSE[mod(Math.max(at, 0) + k, COURSE.length)][3])) first.push(decode(f));
      if (PRELOAD) for (const t of Object.keys(M.themes)) for (const f of themeFiles(t)) first.push(decode(f));
      await Promise.all(first);
    } catch (e) {
      document.getElementById('loading').textContent = '그림을 불러오지 못했어요. 새로고침해 주세요.';
      return;
    }
    buildSelect();
    if (!CAPTURE) SND.setBGM(STAGES.bgm);                    // the running music's file
    getReady();                                              // the songs' files, while you pick
    document.getElementById('loading').hidden = true;
    const auto = qs.get('char');
    if (CAPTURE || AUTO || auto) startGame(auto && M.chars.includes(auto) ? auto : 'tardigrade');
    else { G.mode = 'select'; show('select', true); }
    if (at >= 0) { G.x = STARTS[at] + 10; G.genX = G.x + 300; G.station = -1; step(0); }
    if (!CAPTURE) requestAnimationFrame((t) => { last = t; frame(t); });
    // test hooks
    window.__ready = true;
    window.__run = (sec) => { const n = Math.round(sec / DT); for (let i = 0; i < n; i++) step(DT); render(); return window.__state(); };
    window.__settle = async () => { while (Object.keys(pending).length) await Promise.all(Object.values(pending)).catch(() => {}); render(); return Object.keys(bmp).length; };
    window.__state = () => ({ mode: G.mode, t: +G.t.toFixed(2), x: Math.round(G.x), v: +G.v.toFixed(1), hp: +G.hp.toFixed(1), score: G.score, eaten: G.eaten, hits: G.hits,
      station: COURSE[Math.max(0, G.station)][0], seg: G.station, theme: G.theme, lid: +lidAmount().toFixed(2), lastHit: G.lastHit, rot, lap: stationAt(G.x).lap, y: +G.y.toFixed(1), slide: G.slide, obs: G.obs.length, items: G.items.length,
      NW, RS: +RS.toFixed(3), GW, GH, rhSong: G.rh ? G.rh.song.id : null, orbSong: G.orb ? OB.song.id : null, rotation: { ...ROT }, o2n: G.o2n, boost: +G.boost.toFixed(2), boostHeld: +G.boostHeld.toFixed(2), boosts: G.boosts, decoded: Object.keys(bmp).length, atp: G.atp || 0, orbits: G.orbits || 0, orb: G.orb ? G.orb.st : null, huge: G.obs.filter((o) => o.kind === 'huge').length });
    window.__G = G;
    window.__orb = () => { const o = G.orb; if (!o) return null; const t = otime();
      return { t: +t.toFixed(3), clock: o.a0 !== null ? 'sound' : 'game', k: o.k, N: OB.N, st: o.st, res: o.res, th: o.st === 'play' ? +(((obAngle(o.k, t, o.next) % 6.2832) + 6.2832) % 6.2832).toFixed(3) : null, off: +o.off.toFixed(3), next: +o.next.toFixed(3), cam: o.cam.map((v) => +v.toFixed(1)) }; };
    window.__orbPlan = (id) => { const pl = id ? orbPlan(STAGES.orb.find((s) => s.id === id)) : OB; return { id: pl.song.id, B: pl.B, ok: pl.ok, N: pl.N, P: pl.P, T: pl.T, hits: pl.hits, swirl: pl.swirl.map((v, i) => v ? i : -1).filter((i) => i >= 0), dir: pl.dir }; };
    window.__stages = STAGES;
    window.__orbTap = orbTap;
    window.__boost = startBoost;
    window.__rh = () => { const r = G.rh; if (!r) return null; const t = rtime();
      return { t: +t.toFixed(3), n: r.n, combo: r.combo, maxCombo: r.maxCombo, done: r.done, gain: r.gain,
        notes: r.notes.map((n) => { const o = { b: n.b, kind: n.kind, tn: n.tn, te: n.te, res: n.res, num: n.num };
          if (n.kind === 'p') { o.x = NWf / 2; o.y = 98; o.turns = +n.turns.toFixed(2); } else { const [x, y] = rhPos(n.u, n.v); o.x = x; o.y = y; }
          if (n.kind === 's') { const p = rhPath(n); o.path = p.P.filter((_, i) => i % 3 === 0 || i === p.P.length - 1); o.len = p.len; o.inT = n.inT; o.allT = n.allT; o.start = n.start; if (t >= n.tn && t <= n.te) o.ball = rhBall(p, (t - n.tn) / (n.te - n.tn)); }
          return o; }) }; };
    window.__toClient = (x, y) => { const r = cv.getBoundingClientRect(); const X = x * RS, Y = y * RS; const cx = rot ? GH - Y : X, cy = rot ? X : Y;
      return [r.left + cx * r.width / cv.width, r.top + cy * r.height / cv.height]; };
    window.__starts = STARTS;
    window.__hz = { addPit, addDoor, addDrop, addSpike, addShot, hzFam, doorExt, obsBoxes };
    window.__place = (x) => { G.x = x; G.obs = []; G.items = []; G.genX = x + 1e7; G.station = -1; G.mode = 'play'; step(0); G.fade = 1; G.prevTheme = null; render(); return window.__state(); };
  })();
})();
