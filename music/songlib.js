// helpers for writing songs on the Chip: chord charts, written melodies, harmonies, bass lines, arpeggios, stabs,
// power chords and drum patterns, all on a 16-steps-a-bar grid
window.SongLib = (() => {
  'use strict';
  const { midi, bar } = Chip;
  const ROOTS = { C: 0, 'C#': 1, Db: 1, D: 2, 'D#': 3, Eb: 3, E: 4, F: 5, 'F#': 6, Gb: 6, G: 7, 'G#': 8, Ab: 8, A: 9, 'A#': 10, Bb: 10, B: 11 };
  const QUAL = { '': [0, 4, 7], m: [0, 3, 7], 7: [0, 4, 7, 10], m7: [0, 3, 7, 10], maj7: [0, 4, 7, 11], sus4: [0, 5, 7] };
  function chord(name) { const m = /^([A-G][#b]?)(.*)$/.exec(name); if (!(m[2] in QUAL)) throw new Error('chord ' + name); return { pc: ROOTS[m[1]], iv: QUAL[m[2]] }; }
  // the chord chart: one or two chords a bar ("F G"); -> the chord at a step
  function chartAt(chart, step) { const b = chart[Math.floor(step / 16)] || chart[chart.length - 1]; const p = b.split(' '); return chord(p.length > 1 && step % 16 >= 8 ? p[1] : p[0]); }
  const inRange = (pc, low) => low + (((pc - low) % 12) + 12) % 12;          // pitch class pc in the octave from `low` up
  function melody(lines, b0) { const out = []; lines.forEach((l, i) => out.push(...bar(l, (b0 + i) * 16))); return out; }
  const tr = (notes, k) => notes.map((n) => ({ ...n, n: n.n + k, ...(n.slideFrom !== undefined ? { slideFrom: n.slideFrom + k } : {}) }));
  const shift = (notes, bars) => notes.map((n) => ({ ...n, step: n.step + bars * 16 }));
  // a second voice: the highest chord tone at least a minor third under each melody note
  function harmony(notes, chart) {
    return notes.map((nt) => {
      const c = chartAt(chart, nt.step), pcs = c.iv.map((i) => (c.pc + i) % 12);
      let n = nt.n - 3; while (!pcs.includes(((n % 12) + 12) % 12)) n--;
      return { ...nt, n };
    });
  }
  // legato: notes that follow straight on (no gap) and are close slide into each other
  const legato = (ns, maxI = 7, t = 0.045) => ns.map((nt, i) => (i > 0 && ns[i - 1].step + ns[i - 1].len === nt.step && Math.abs(ns[i - 1].n - nt.n) <= maxI ? { ...nt, slideFrom: ns[i - 1].n, slideT: t } : nt));
  // a pattern of 16 tokens over bars b0..b1: R root, O octave, 5 fifth, 3 third, 7 flat seventh, P a power chord
  // (root, fifth, octave), C the chord (three tones), - hold, . rest
  function line(chart, pat, b0, b1, low, vol = 1) {
    const out = [];
    for (let b = b0; b < b1; b++) {
      const P = (typeof pat === 'function' ? pat(b) : pat).trim().split(/\s+/); if (P.length !== 16) throw new Error('pattern ' + pat);
      let cur = [];
      P.forEach((t, i) => {
        const step = b * 16 + i;
        if (t === '-') { for (const n of cur) n.len++; return; }
        cur = []; if (t === '.') return;
        const c = chartAt(chart, step), r = inRange(c.pc, low);
        const ns = t === 'R' ? [r] : t === 'O' ? [r + 12] : t === '5' ? [r + 7] : t === '3' ? [r + c.iv[1]] : t === '7' ? [r + 10]
          : t === 'P' ? [r, r + 7, r + 12] : t === 'C' ? c.iv.slice(0, 3).map((iv) => r + iv) : [r];
        for (const n of ns) { const o = { step, n, len: 1, vol }; cur.push(o); out.push(o); }
      });
    }
    return out;
  }
  // arpeggios: every `every` steps the next chord tone in `order` (0 root, 1 third, 2 fifth, 3 octave, 4 tenth)
  function arps(chart, b0, b1, base, order, every = 1, len = 1, vol = 1) {
    const out = [];
    for (let s = b0 * 16, k = 0; s < b1 * 16; s += every, k++) {
      const c = chartAt(chart, s), r = inRange(c.pc, base), tones = [r, r + c.iv[1], r + c.iv[2], r + 12, r + 12 + c.iv[1]];
      out.push({ step: s, n: tones[order[k % order.length]], len, vol });
    }
    return out;
  }
  // chords struck on given steps of each bar, voiced upward from `base`
  function stabs(chart, b0, b1, steps, base, len = 1, vol = 1) {
    const out = [];
    for (let b = b0; b < b1; b++) for (const st of steps) {
      const [i, L] = Array.isArray(st) ? st : [st, len];
      const s = b * 16 + i, c = chartAt(chart, s), r = inRange(c.pc, base);
      for (const iv of c.iv.slice(0, 3)) { let n = r + iv; while (n < base) n += 12; out.push({ step: s, n, len: L, vol }); }
    }
    return out;
  }
  // drums: per instrument a 16-char string: X loud, x normal, g ghost, o (on the hat line) an open hat, . nothing
  function drums(b0, b1, map, extra = {}) {
    const out = [];
    for (let b = b0; b < b1; b++) {
      const m = typeof map === 'function' ? map(b) : map;
      for (const [k, str] of Object.entries(m)) {
        if (!str) continue;                                   // '' : that drum is out this bar
        if (str.length !== 16) throw new Error(`drum line ${k} bar ${b}: ${str}`);
        [...str].forEach((ch, i) => { if (ch !== '.') out.push({ step: b * 16 + i, k: ch === 'o' ? 'o' : k, v: ch === 'X' ? 1 : ch === 'x' || ch === 'o' ? 0.78 : 0.42, ...(extra[k] || {}) }); });
      }
    }
    return out;
  }
  // a shorter cut of a song: the bars [a, b) of each segment, one after another (notes cut off at a segment's end).
  // `add`: drums to put in at the joins (steps in the new song)
  function cut(song, segs, add = [], extra = {}) {
    const map = []; let nb = 0;
    for (const [a, b] of segs) { map.push([a * 16, b * 16, nb * 16]); nb += b - a; }
    const mv = (step, len) => { for (const [s0, s1, d0] of map) if (step >= s0 && step < s1) return { step: step - s0 + d0, len: len === undefined ? undefined : Math.min(len, s1 - step) }; return null; };
    const starts = new Set(segs.map(([a]) => a * 16));
    const moveNotes = (ns) => ns.flatMap((n) => {
      const m = mv(n.step, n.len); if (!m) return [];
      const o = { ...n, step: m.step, len: m.len };
      if (starts.has(n.step)) { delete o.slideFrom; delete o.slideT; }      // no slide in from a bar that was cut
      return [o];
    });
    const ch = {};
    for (const [k, c] of Object.entries(song.ch)) ch[k] = { ...c, notes: moveNotes(c.notes) };
    const drumsOut = song.drums.flatMap((d) => { const m = mv(d.step, d.len); return m ? [{ ...d, step: m.step, ...(d.len !== undefined ? { len: m.len } : {}) }] : []; });
    return { ...song, ...extra, bars: nb, ch, drums: [...drumsOut, ...add], cutFrom: segs, ...(song.tune ? { tune: moveNotes(song.tune) } : {}), moveNotes };
  }
  return { midi, bar, chord, chartAt, inRange, melody, tr, shift, harmony, legato, line, arps, stabs, drums, cut };
})();
