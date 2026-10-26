// Lays out the two mini-games on the ten game songs and writes runner_hd/stages.js:
//  - the rhythm stage: circles on the tune's notes, sliders on its long notes, a spinner on the last bar of the build;
//    placed to flow left and right (a turn at the edges and at each new group), higher notes higher on the screen,
//    never on top of another circle that is up at the same time
//  - the orbit stage: tiles on the tune's notes, 0.5 to 1.5 beats apart (the bends the path can make); notes held
//    longer get tiles on the beat in between; then thinned (the weakest notes first) to about 50 tiles
// node mkstages.js [--meta music_meta.json]
global.window = {};
for (const [f, g] of [['chip', 'Chip'], ['songlib', 'SongLib'], ['songs', 'Songs'], ['songs_rh', 'SongsRH'], ['songs_epic', 'SongsEpic'], ['gamesongs', 'GameSongs']]) { require(__dirname + '/' + f + '.js'); global[g] = window[g]; }
const fs = require('fs');
const META = fs.existsSync(__dirname + '/music_meta.json') ? JSON.parse(fs.readFileSync(__dirname + '/music_meta.json', 'utf8')) : {};

// ---------------------------------------------------------------- shared
const strength = (s) => (s % 16 === 0 ? 4 : s % 8 === 0 ? 3 : s % 4 === 0 ? 2 : s % 2 === 0 ? 1 : 0);   // where in the bar
function onsets(song, from, to) {                                   // the tune's notes in [from, to], one per step (the top one)
  const by = new Map();
  for (const n of song.tune) if (n.step >= from && n.step <= to) { const o = by.get(n.step); if (!o || n.n > o.n) by.set(n.step, n); }
  return [...by.values()].sort((a, b) => a.step - b.step);
}

// ---------------------------------------------------------------- the rhythm stage
const RH_R = 13, AR = 0.85;
function rhythmChart(song) {
  const g = song.game, beat = 60 / song.bpm, fast = song.bpm >= 150;
  const spin = g.build ? { s: g.build[1] - 16, e: g.build[1] - 2 } : null;
  const cand = onsets(song, g.first, g.last).filter((n) => !(spin && n.step >= spin.s - 2 && n.step < g.build[1]));
  // pick the notes: no 16ths, eighths only as a pair (a triple when slower), a slider where a note is held 1.5 beats+
  const kept = []; let run = 0;
  for (let i = 0; i < cand.length; i++) {
    const n = cand[i], prev = kept[kept.length - 1], isLast = n.step === g.last;
    if (prev) {
      const gap = n.step - (prev.kind === 's' ? prev.e : prev.s);
      if (gap < 2 || (prev.kind === 's' && gap < 3)) continue;
      if (gap < 4) { if (run >= (fast ? 1 : 2)) continue; run++; } else run = 0;
    }
    const nextS = i + 1 < cand.length ? cand[i + 1].step : n.step + 99;
    const e = Math.min(n.step + Math.min(n.len, 8), nextS - 2);
    if (!isLast && n.len >= 6 && e - n.step >= 4) kept.push({ kind: 's', s: n.step, e, n: n.n });
    else kept.push({ kind: 'c', s: n.step, n: n.n });
  }
  // long rests: a circle on the big drum hits in them
  const accents = new Set(song.drums.filter((d) => ['K', 'S', 'SB', 's', 'T', 'boom'].includes(d.k) && (d.v ?? 1) >= 0.99 && d.step % 4 === 0).map((d) => d.step));
  for (let i = 0; i + 1 < kept.length; i++) {
    const a = kept[i], b = kept[i + 1], end = a.kind === 's' ? a.e : a.s;
    if (b.s - end <= 12) continue;
    const add = [...accents].filter((s) => s >= end + 4 && s <= b.s - 4 && !(spin && s >= spin.s - 2 && s <= spin.e + 2)).sort((x, y) => x - y);
    let last = end; const ins = [];
    for (const s of add) if (s - last >= 4) { ins.push({ kind: 'c', s, n: a.n, drum: true }); last = s; }
    if (ins.length) { kept.splice(i + 1, 0, ...ins); i += ins.length; }
  }
  if (spin) {
    const at = kept.findIndex((k) => k.s > spin.s);
    kept.splice(at < 0 ? kept.length : at, 0, { kind: 'p', s: spin.s, e: spin.e, turns: Math.max(2, Math.round((spin.e - spin.s) / 4 * beat * 1.25)) });
  }
  // groups (the numbers and colours): a new one every two bars, after a pause or a spinner, at most 8
  let grp = -1, inG = 0, lastBar = -99, prevEnd = -99;
  for (const k of kept) {
    const bar = Math.floor(k.s / 16);
    if (k.kind === 'p') { grp++; inG = 0; k.g = grp; prevEnd = k.e; lastBar = bar; continue; }
    const pause = k.s - prevEnd >= 8;
    if (grp < 0 || pause || inG >= 8 || (bar - lastBar >= 2 && inG >= 3) || kept[kept.indexOf(k) - 1]?.kind === 'p') { grp++; inG = 0; lastBar = bar; }
    k.g = grp; inG++; prevEnd = k.kind === 's' ? k.e : k.s;
  }
  // where they go
  const ps = kept.filter((k) => k.kind !== 'p').map((k) => k.n), lo = Math.min(...ps), hi = Math.max(...ps);
  const vOf = (p) => 0.84 - 0.68 * (p - lo) / Math.max(1, hi - lo);
  const NWmin = 300, X = (u) => 52 + u * (NWmin - 104), Y = (v) => 52 + v * 92;
  const tOf = (s) => s / 4 * beat;
  let u = 0.16, d = 1, curG = -1;
  const placed = [];
  // centre to centre (units, at the narrowest screen): an eighth pair just touching, then further for longer gaps
  const spacing = (gb) => (gb <= 0.5 ? 25 : gb <= 0.75 ? 31 : gb <= 1 ? 37 : gb <= 1.5 ? 44 : 52) / (NWmin - 104);
  const clash = (x, y, t0, self) => {                                 // the nearest circle up at the same time
    let m = 1e9;
    for (const q of placed) {
      if (q === self.prevPair) continue;
      const qEnd = q.kind === 's' ? tOf(q.e) : tOf(q.s);
      if (qEnd < t0 - AR - 0.15) continue;
      for (const [qx, qy] of q.pts) m = Math.min(m, Math.hypot(qx - x, qy - y));
    }
    return m;
  };
  // a slider's track from (u, v): along the way it is going, curving up or down, ending halfway to the next note's height
  const sliderAt = (k, u, v, d, side) => {
    const db = (k.e - k.s) / 4, L = Math.min(0.3, 0.1 + 0.07 * db);
    let ue = u + d * L; if (ue > 0.94 || ue < 0.06) { d = -d; ue = u + d * L; }
    const nxt = kept[kept.indexOf(k) + 1], v2 = Math.max(0.08, Math.min(0.92, nxt && nxt.n ? (v + vOf(nxt.n)) / 2 : v));
    const vm = Math.max(0.06, Math.min(0.94, (v + v2) / 2 + side * 0.16));
    const ctrl = [[u, v], [(u + ue) / 2, vm], [ue, v2]];
    const pts = []; for (let i = 0; i <= 8; i++) { const f = i / 8; pts.push([X(u + (ue - u) * f), Y(v + (v2 - v) * f + Math.sin(f * Math.PI) * (vm - (v + v2) / 2))]); }
    return { ctrl, pts, ue, d };
  };
  let prevK = null;
  for (const k of kept) {
    if (k.kind === 'p') { placed.push({ kind: 'p', s: k.s, e: k.e, pts: [] }); u = 0.5; prevK = null; continue; }
    if (k.g !== curG) { if (curG >= 0) d = -d; curG = k.g; }
    const gb = prevK ? (k.s - (prevK.kind === 's' ? prevK.e : prevK.s)) / 4 : 1;
    const self = { prevPair: prevK && gb <= 0.5 ? placed[placed.length - 1] : null };
    let best = null;
    for (const dv of [0, -0.15, 0.15, -0.3, 0.3, -0.45, 0.45]) for (const flip of [false, true]) for (const side of (k.kind === 's' ? [k.g % 2 ? 1 : -1, k.g % 2 ? -1 : 1] : [0])) {
      let dd = flip ? -d : d, nu = prevK ? u + dd * spacing(gb) : u;
      if (nu > 0.92 || nu < 0.08) { dd = -dd; nu = u + dd * spacing(gb); }
      nu = Math.max(0.06, Math.min(0.94, nu));
      const nv = Math.max(0.06, Math.min(0.94, vOf(k.n) + dv));
      const sl = k.kind === 's' ? sliderAt(k, nu, nv, dd, side) : null;
      const pts = sl ? sl.pts : [[X(nu), Y(nv)]];
      let m = 1e9; for (const [x, y] of pts) m = Math.min(m, clash(x, y, tOf(k.s), self));
      const score = (m >= RH_R * 2.15 ? 1000 : m * 10) - Math.abs(dv) * 30 - (flip ? 8 : 0) - (sl && side !== (k.g % 2 ? 1 : -1) ? 4 : 0);   // clear of every circle up at the time first
      if (!best || score > best.score) best = { score, nu, nv, dd, sl, pts };
    }
    d = best.dd; u = best.nu;
    if (k.kind === 'c') { k.u = u; k.v = best.nv; placed.push({ kind: 'c', s: k.s, pts: best.pts }); }
    else {
      k.ctrl = best.sl.ctrl.map(([a, b]) => [+a.toFixed(3), +b.toFixed(3)]);
      placed.push({ kind: 's', s: k.s, e: k.e, pts: best.pts });
      u = best.sl.ue; d = best.sl.d;
    }
    prevK = k;
  }
  // the check: the closest two circles (or a circle and a slider's track) up at the same time, past an eighth pair
  let worst = 1e9;
  for (let i = 0; i < placed.length; i++) for (let j = i + 1; j < placed.length; j++) {
    const A = placed[i], Bq = placed[j]; if (!A.pts.length || !Bq.pts.length) continue;
    const aEnd = A.kind === 's' ? tOf(A.e) : tOf(A.s); if (aEnd < tOf(Bq.s) - AR - 0.15) continue;
    if (j === i + 1 && Bq.s - (A.kind === 's' ? A.e : A.s) <= 2) continue;
    for (const [x1, y1] of A.pts) for (const [x2, y2] of Bq.pts) worst = Math.min(worst, Math.hypot(x1 - x2, y1 - y2));
  }
  // the map: [beat, group, kind, ...] as the game reads it
  const B = (s) => +(s / 4).toFixed(4);
  const map = kept.map((k) => (k.kind === 'c' ? [B(k.s), k.g, 'c', +k.u.toFixed(3), +k.v.toFixed(3)]
    : k.kind === 's' ? [B(k.s), k.g, 's', B(k.e), k.ctrl] : [B(k.s), k.g, 'p', B(k.e), k.turns]));
  // the closest two circles up at once (beyond an eighth pair), as a check
  return { map, end: B(g.last) + 1, first: B(g.first), worst: +worst.toFixed(1), notes: map.length, sliders: map.filter((m) => m[2] === 's').length, drumNotes: kept.filter((k) => k.drum).length,
    secs: +(tOf(g.last) - tOf(g.first)).toFixed(1) };
}

// ---------------------------------------------------------------- the orbit stage
const OK_GAP = new Set([2, 3, 4, 5, 6]);                            // steps: 0.5 .. 1.5 beats
function orbitTiles(song) {
  const g = song.game, notes = onsets(song, g.first, g.last);
  // the places a tile may go: every note of the tune (every bar's first beat must have one), and the beats under a
  // held note (low weight: to bridge it)
  const cand = new Map();
  for (const n of notes) cand.set(n.step, { s: n.step, w: [0.3, 2.0, 2.4, 4, 100][strength(n.step)] + (n.len >= 4 ? 0.3 : 0), n: n.n });
  for (let s = g.first; s <= g.last; s += 4) if (!cand.has(s)) cand.set(s, { s, w: s % 16 === 0 ? 100 : s % 8 === 0 ? 1.5 : 0.5, filler: true });
  if (!cand.has(g.last)) cand.set(g.last, { s: g.last, w: 100 });
  const C = [...cand.values()].sort((a, b) => a.s - b.s);
  // the best set of a given size (as many tiles a second as the stand-in had): on the tune's notes, strong ones
  // first, a bonus for the gaps that are not a plain beat, a cost for the same gap again and again
  const beats = (g.last - g.first) / 4, secs = beats * 60 / song.bpm, want = Math.round(secs * 2.2);
  const GAPS = [2, 3, 4, 5, 6], bonus = [0.5, 0.7, 0, 0.7, 0.4], MONO = 1.2;
  const N = C.length, S = 6 * 5, NEG = -1e9;                       // state: last gap (5 kinds + none) x run (1..5)
  const idx = (c, gi, r) => (c * 6 + gi) * 5 + (r - 1);
  const best = Array.from({ length: N }, () => new Float64Array((want + 1) * S).fill(NEG));
  const from = Array.from({ length: N }, () => new Int32Array((want + 1) * S).fill(-1));
  best[0][idx(0, 5, 1)] = C[0].w;
  for (let j = 1; j < N; j++) for (let i = j - 1; i >= 0 && C[j].s - C[i].s <= 6; i--) {
    const gj = GAPS.indexOf(C[j].s - C[i].s); if (gj < 0) continue;
    for (let c = 1; c <= want; c++) for (let gi = 0; gi < 6; gi++) for (let r = 1; r <= 5; r++) {
      const v0 = best[i][idx(c - 1, gi, r)]; if (v0 === NEG) continue;
      const nr = gi === gj ? Math.min(5, r + 1) : 1;
      const pen = nr >= (gj === 2 ? 4 : 3) ? MONO : 0;
      const v = v0 + C[j].w + bonus[gj] - pen, k = idx(c, gj, nr);
      if (v > best[j][k]) { best[j][k] = v; from[j][k] = i * S * (want + 1) + idx(c - 1, gi, r); }
    }
  }
  const last = N - 1; let bk = -1, bv = NEG;
  for (let gi = 0; gi < 6; gi++) for (let r = 1; r <= 5; r++) { const v = best[last][idx(want, gi, r)]; if (v > bv) { bv = v; bk = idx(want, gi, r); } }
  if (bk < 0) throw new Error(song.en + ': no way to lay ' + want + ' gaps');
  const pick = [];
  for (let j = last, k = bk; ;) { pick.push(C[j]); const f = from[j][k]; if (f < 0) break; j = Math.floor(f / (S * (want + 1))); k = f % (S * (want + 1)); }
  pick.reverse();
  const G = pick.slice(1).map((p, i) => p.s - pick[i].s);
  return { first: pick[0].s / 4, beats: G.map((x) => x / 4), tiles: pick.length, fillers: pick.filter((p) => p.filler).length };
}
// the path, as the game lays it (game.js, OB): the same planner, to check it finds a way
function planOK(beats) {
  const OB_L = 30, n = beats.length;
  const P = [[0, 0], [OB_L, 0]], head = [0], dir = [1];
  const segDist = (p, a, b) => { const dx = b[0] - a[0], dy = b[1] - a[1], L2 = dx * dx + dy * dy; const u = L2 ? Math.max(0, Math.min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L2)) : 0; return Math.hypot(p[0] - a[0] - u * dx, p[1] - a[1] - u * dy); };
  const clear = (k, np) => {
    for (let j = 0; j < k; j++) if (Math.hypot(np[0] - P[j][0], np[1] - P[j][1]) < OB_L * 0.95) return false;
    for (let j = 0; j + 1 < k; j++) for (let s = 1; s <= 4; s++) { const q = [P[k][0] + (np[0] - P[k][0]) * s / 4, P[k][1] + (np[1] - P[k][1]) * s / 4]; if (segDist(q, P[j], P[j + 1]) < OB_L * 0.8) return false; }
    return true;
  };
  let calls = 0;
  const solve = (k) => {
    if (++calls > 2e6) return false;
    if (k > n) return true;
    const b = beats[k - 1], back = head[k - 1] + Math.PI, opts = [];
    for (const d of [dir[k - 1], -dir[k - 1]]) {
      if (d !== dir[k - 1] && Math.abs(b - 1) < 1e-6) continue;
      let h = back + d * Math.PI * b; h = Math.atan2(Math.sin(h), Math.cos(h));
      if (Math.cos(h) < -1e-6) continue;
      const np = [P[k][0] + Math.cos(h) * OB_L, P[k][1] + Math.sin(h) * OB_L];
      opts.push({ d, h, np, cost: (d !== dir[k - 1] ? 1 : 0) + Math.abs(np[1]) / (OB_L * 14) });
    }
    opts.sort((a, c) => a.cost - c.cost);
    for (const o of opts) { if (!clear(k, o.np)) continue; P[k + 1] = o.np; head[k] = o.h; dir[k] = o.d; if (solve(k + 1)) return true; }
    P.length = k + 1; head.length = k; dir.length = k;
    return false;
  };
  const ok = solve(1);
  return { ok, swirls: dir.filter((d, k) => k > 0 && d !== dir[k - 1]).length, calls };
}

// ---------------------------------------------------------------- write it out
const out = { rh: [], orb: [] };
GameSongs.rh.forEach((f, i) => {
  const s = f(), c = rhythmChart(s), id = `rh${i + 1}`, m = META[id] || {};
  out.rh.push({ id, name: s.name, en: s.en, bpm: s.bpm, file: `assets/${id}.mp3`, gain: m.gain ?? 1, lead: m.lead ?? 0.05, first: c.first, end: c.end, map: c.map });
  console.log(`${id} ${s.en.padEnd(24)} ${s.bpm} BPM  ${c.notes} notes (${c.sliders} sliders, ${c.drumNotes} on drums) over ${c.secs}s = ${(c.notes / c.secs).toFixed(2)}/s, closest ${c.worst} units (2R = ${2 * RH_R})`);
});
GameSongs.orb.forEach((f, i) => {
  const s = f(), t = orbitTiles(s), p = planOK(t.beats), id = `orb${i + 1}`, m = META[id] || {};
  out.orb.push({ id, name: s.name, en: s.en, bpm: s.bpm, file: `assets/${id}.mp3`, gain: m.gain ?? 1, lead: m.lead ?? 0.05, first: t.first, beats: t.beats });
  const hist = {}; for (const b of t.beats) hist[b] = (hist[b] || 0) + 1;
  console.log(`${id} ${s.en.padEnd(24)} ${s.bpm} BPM  ${t.tiles} tiles (${t.fillers} off the tune), first at beat ${t.first}, ${t.beats.reduce((a, b) => a + b, 0)} beats = ${(t.beats.reduce((a, b) => a + b, 0) * 60 / s.bpm).toFixed(1)}s, gaps ${JSON.stringify(hist)}, path ${p.ok ? 'ok' : 'FAILED'} (${p.swirls} swirls)`);
});
const js = '// made by work/mkstages.js from the game songs (chip/gamesongs.js): the rhythm maps and the orbit tiles, per song\nwindow.BodyStages = ' + JSON.stringify(out) + ';\n';
if (process.argv.includes('--write')) { fs.writeFileSync(__dirname + '/../game/stages.js', js); console.log('wrote stages.js', js.length); }
module.exports = { rhythmChart, orbitTiles, planOK };
