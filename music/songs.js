// Four retro tracks for the rhythm and orbit stages (candidates). Each: intro 2 bars, A 8, B 8, A' 8 (with a
// harmony), outro 2 = 28 bars. Melodies are written out by hand (16 steps a bar); bass, arpeggios, off-beat chords
// and drums come from per-bar patterns over the chord chart.
window.Songs = (() => {
  'use strict';
  const { midi, bar } = Chip;
  const ROOTS = { C: 0, 'C#': 1, Db: 1, D: 2, 'D#': 3, Eb: 3, E: 4, F: 5, 'F#': 6, Gb: 6, G: 7, 'G#': 8, Ab: 8, A: 9, 'A#': 10, Bb: 10, B: 11 };
  const QUAL = { '': [0, 4, 7], m: [0, 3, 7], 7: [0, 4, 7, 10], m7: [0, 3, 7, 10], maj7: [0, 4, 7, 11], sus4: [0, 5, 7] };
  function chord(name) {                                   // "F#m7" -> { root pitch class, intervals }
    const m = /^([A-G][#b]?)(.*)$/.exec(name); return { pc: ROOTS[m[1]], iv: QUAL[m[2]] };
  }
  // the chord chart: one or two chords a bar ("F G"); -> a chord for each step
  function chartAt(chart, step) { const b = chart[Math.floor(step / 16)] || chart[chart.length - 1]; const p = b.split(' '); return chord(p.length > 1 && step % 16 >= 8 ? p[1] : p[0]); }
  const inRange = (pc, low) => low + (((pc - low) % 12) + 12) % 12;          // pitch class pc in the octave from `low` up
  // write a melody: bars of 16 tokens from bar index b0
  function melody(lines, b0) { const out = []; lines.forEach((l, i) => out.push(...bar(l, (b0 + i) * 16))); return out; }
  // a second voice under the melody: for each note the highest tone of the chord sounding then that is at least a
  // minor third below it (so it never rubs against the bass or the chord parts)
  function harmony(notes, chart) {
    return notes.map((nt) => {
      const c = chartAt(chart, nt.step), pcs = c.iv.map((i) => (c.pc + i) % 12);
      let n = nt.n - 3; while (!pcs.includes(((n % 12) + 12) % 12)) n--;
      return { ...nt, n };
    });
  }
  // a bass line from a 16-token pattern: R root, O octave above, 5 fifth, 3 third, 7 seventh-ish (a tone below the
  // octave), - hold, . rest
  function bassLine(chart, pat, b0, b1, low) {
    const out = [];
    for (let b = b0; b < b1; b++) {
      const P = (typeof pat === 'function' ? pat(b) : pat).trim().split(/\s+/); let cur = null;
      P.forEach((t, i) => {
        const step = b * 16 + i;
        if (t === '-') { if (cur) cur.len++; return; }
        cur = null; if (t === '.') return;
        const c = chartAt(chart, step), r = inRange(c.pc, low);
        const n = t === 'R' ? r : t === 'O' ? r + 12 : t === '5' ? r + 7 : t === '3' ? r + c.iv[1] : t === '7' ? r + 10 : r;
        cur = { step, n, len: 1 }; out.push(cur);
      });
    }
    return out;
  }
  // arpeggios: every `every` steps the next chord tone in `order` (indices into root, 3rd, 5th, octave, 10th)
  function arps(chart, b0, b1, base, order, every = 1, len = 1, vol = 1) {
    const out = [];
    for (let s = b0 * 16, k = 0; s < b1 * 16; s += every, k++) {
      const c = chartAt(chart, s), r = inRange(c.pc, base), tones = [r, r + c.iv[1], r + c.iv[2], r + 12, r + 12 + c.iv[1]];
      out.push({ step: s, n: tones[order[k % order.length]], len, vol });
    }
    return out;
  }
  // chords struck on given steps of each bar (all three notes)
  function stabs(chart, b0, b1, steps, base, len = 1, vol = 1) {
    const out = [];
    for (let b = b0; b < b1; b++) for (const i of steps) {
      const s = b * 16 + i, c = chartAt(chart, s), r = inRange(c.pc, base);
      for (const iv of c.iv.slice(0, 3)) { let n = r + iv; while (n < base) n += 12; out.push({ step: s, n, len, vol }); }
    }
    return out;
  }
  // drums: per instrument a 16-char string, X loud, x normal, g ghost, . nothing
  function drums(b0, b1, map, extra = {}) {
    const out = [];
    for (let b = b0; b < b1; b++) {
      const m = typeof map === 'function' ? map(b) : map;
      for (const [k, str] of Object.entries(m)) [...str].forEach((ch, i) => { if (ch !== '.') out.push({ step: b * 16 + i, k: ch === 'o' ? 'o' : k, v: ch === 'X' ? 1 : ch === 'x' || ch === 'o' ? 0.78 : 0.42, ...(extra[k] || {}) }); });
    }
    return out;
  }
  const roll = (b) => ({ s: '........gxxxXXXX' });                    // a snare roll into the next section
  const SCALE = (root, minor) => (minor ? [0, 2, 3, 5, 7, 8, 10] : [0, 2, 4, 5, 7, 9, 11]).map((i) => (ROOTS[root] + i) % 12);

  // ================================================================ 1. 심장 질주 (Heartbeat Rush): A minor, 132 BPM
  function heartbeatRush() {
    const chart = ['Am', 'Am',
      'Am', 'F', 'C', 'G', 'Am', 'F', 'G', 'E',
      'F', 'G', 'Em', 'Am', 'Dm', 'Em', 'F', 'E',
      'Am', 'F', 'C', 'G', 'Am', 'F', 'G', 'E',
      'Am', 'Am'];
    const A = [
      'A4 - - C5 - - E5 - D5 - C5 - D5 - - -',
      'C5 - - - - - - - A4 - G4 - A4 - C5 -',
      'G4 - - C5 - - E5 - G5 - E5 - D5 - C5 -',
      'D5 - - - - - - - B4 - - - - - . .',
      'A4 - - C5 - - E5 - D5 - C5 - D5 - E5 -',
      'F5 - - - G5 - - - A5 - - - C5 - - -',
      'B4 - - D5 - - G5 - F5 - E5 - D5 - - -',
      'E5 - - - G#4 - - - B4 - - - E5 - . .'];
    const Bm = [
      'A5 - - - G5 - F5 - - - E5 - F5 - - -',
      'G5 - - - - - D5 - - - B4 - D5 - - -',
      'E5 - - - - - B4 - - - G4 - B4 - E5 -',
      'C5 - - - - - - - . . A4 - C5 - E5 -',
      'F5 - - - - - D5 - - - A4 - D5 - F5 -',
      'G5 - - - - - E5 - - - B4 - E5 - G5 -',
      'A5 - - - G5 - F5 - - E5 - D5 - C5 - -',
      'E5 - - - - - - - G#5 - - - B5 - - -'];
    const lead = [...melody(A, 2), ...melody(Bm, 10), ...melody(A, 18), ...melody(['A5 - - - - - - - - - - - - - - -'], 26)];
    const harm = harmony(melody(A.slice(0, 7), 18), chart);
    return {
      name: '심장 질주', en: 'Heartbeat Rush', bpm: 132, bars: 28, echoWet: 0.22,
      ch: {
        lead: { wave: 'p0.25', vol: 0.22, pan: -0.08, echo: 0.2, vib: { depth: 12, rate: 5.6, delay: 0.16 }, notes: lead },
        harm: { wave: 'p0.125', vol: 0.09, pan: 0.42, echo: 0.1, vib: { depth: 10, rate: 5.6, delay: 0.16 }, notes: harm },
        arp: { wave: 'p0.125', vol: 0.055, pan: 0.5, echo: 0.12, env: { a: 0.002, d: 0.09, s: 0.25, r: 0.03 }, gate: 1,
          notes: [...arps(chart, 2, 10, 64, [0, 1, 2, 3]), ...arps(chart, 18, 26, 64, [0, 1, 2, 3])] },
        pluck: { wave: 'p0.25', vol: 0.06, pan: -0.45, echo: 0.15, env: { a: 0.002, d: 0.12, s: 0.2, r: 0.04 },
          notes: arps(chart, 10, 18, 60, [0, 2, 3, 2], 2, 2) },
        bass: { wave: 'tri', vol: 0.27, env: { a: 0.003, d: 0.08, s: 0.85, r: 0.03 }, gate: 0.82,
          notes: [...bassLine(chart, 'R - O - R - O - R - O - R - O -', 0, 10, 40),
                  ...bassLine(chart, 'R - - O - - R - R - - O - - 5 -', 10, 18, 40),
                  ...bassLine(chart, 'R - O - R - O - R - O - R - O -', 18, 26, 40),
                  ...bassLine(chart, 'R - - - - - - - - - - - - - - -', 26, 27, 40)] },
      },
      drums: [
        ...drums(0, 1, { k: 'X...x...X...x...', h: '..x...x...x...x.' }),
        ...drums(1, 2, { k: 'X...x...X...x...', h: '..x...x...x...x.', s: '........gxxxXXXX' }),
        ...drums(2, 10, (b) => ({ k: b % 2 ? 'X.......X.x.....' : 'X.......X.......', s: '....X.......X...', h: 'x.x.x.x.x.x.x.o.'.slice(0, 16) })),
        ...drums(10, 18, (b) => ({ k: 'X.....x.X.......', s: b === 17 ? '....X.......XxXX' : '....X.......X...', h: 'xgxgxgxgxgxgxgxg' })),
        ...drums(18, 26, (b) => ({ k: b % 2 ? 'X.......X.x.....' : 'X.......X.......', s: b === 25 ? '....X...gxxxXXXX' : '....X.......X...', h: 'x.x.x.x.x.x.x.o.' })),
        ...drums(26, 27, { k: 'X...............', S: 'X...............' }),
        { step: 2 * 16, k: 'c', v: 1 }, { step: 10 * 16, k: 'c', v: 0.9 }, { step: 18 * 16, k: 'c', v: 1 }, { step: 26 * 16, k: 'c', v: 1 },
      ],
    };
  }

  // ================================================================ 2. 산소 방울 퍼레이드 (Bubble Parade): F major, 136 BPM
  function bubbleParade() {
    const chart = ['F', 'F',
      'F', 'Dm', 'Bb', 'C', 'F', 'Am', 'Bb', 'C',
      'Bb', 'C', 'Am', 'Dm', 'Gm', 'C7', 'F', 'C7',
      'F', 'Dm', 'Bb', 'C', 'F', 'Am', 'Bb', 'C',
      'F', 'F'];
    const A = [
      'A4 . C5 . F5 - - . C5 . F5 . G5 - - .',
      'A5 - - . G5 . F5 . D5 - - . . . . .',
      'D5 . F5 . Bb5 - - . Bb5 . A5 . F5 - - .',
      'G5 - - - - - . . E5 - - . C5 - - .',
      'A4 . C5 . F5 - - . C5 . F5 . A5 - - .',
      'E5 - - . A5 . C6 . A5 - - . . . . .',
      'Bb5 - - . A5 . G5 . F5 - - . D5 . F5 .',
      'G5 - - - - - - . E5 . C5 . E5 . G5 .'];
    const Bm = [
      'F5 - - - D5 - - - Bb4 - - - D5 - F5 -',
      'E5 - - - C5 - - - G4 - - - C5 - E5 -',
      'E5 - - - C5 - - - A4 - - - C5 - E5 -',
      'F5 - - - - - - - . . A4 - D5 - F5 -',
      'G5 - - - Bb5 - - - D6 - - - Bb5 - G5 -',
      'E5 - - - G5 - - - C6 - - - Bb5 - G5 -',
      'A5 - - - - - - - F5 - G5 - A5 - C6 -',
      'Bb5 - - - A5 - G5 - E5 - - - . . . .'];
    const lead = [...melody(A, 2), ...melody(Bm, 10), ...melody(A.slice(0, 7), 18), ...melody(['G5 - - - - - - . E5 . C5 . E5 . G5 .', 'F5 - - - - - - - - - - - - - . .'], 25)];
    const harm = harmony(melody(A.slice(0, 7), 18), chart);
    return {
      name: '산소 방울 퍼레이드', en: 'Bubble Parade', bpm: 136, bars: 28, echoWet: 0.16, drive: 1.7,
      ch: {
        lead: { wave: 'p0.5', vol: 0.17, pan: -0.05, echo: 0.14, gate: 0.8, env: { a: 0.003, d: 0.1, s: 0.75, r: 0.04 }, vib: { depth: 9, rate: 6, delay: 0.18 }, notes: lead },
        harm: { wave: 'p0.25', vol: 0.08, pan: 0.3, echo: 0.1, gate: 0.8, notes: harm },
        chank: { wave: 'p0.25', vol: 0.045, pan: 0.42, env: { a: 0.002, d: 0.07, s: 0.3, r: 0.03 }, gate: 1,
          notes: [...stabs(chart, 2, 26, [2, 6, 10, 14], 62)] },
        bell: { wave: 'p0.125', vol: 0.045, pan: -0.5, echo: 0.25, env: { a: 0.002, d: 0.15, s: 0.15, r: 0.08 },
          notes: [...arps(chart, 0, 2, 76, [0, 1, 2, 3, 4, 3, 2, 1], 2, 2), ...arps(chart, 10, 18, 76, [4, 3, 2, 1], 4, 2)] },
        bass: { wave: 'tri', vol: 0.3, gate: 0.6, env: { a: 0.003, d: 0.06, s: 0.8, r: 0.03 },
          notes: [...bassLine(chart, (b) => (b % 4 === 3 ? 'R . . . 5 . . . R . . . 5 . 3 .' : 'R . . . 5 . . . R . . . 5 . . .'), 0, 26, 41),
                  ...bassLine(chart, 'R - - - - - - - - - - - - - - -', 26, 27, 41)] },
      },
      drums: [
        ...drums(0, 2, (b) => ({ k: 'X.......X.......', h: '..x...x...x...x.', x: b ? 'gggggggggggggggg' : '................', s: b ? '............xxXX' : '................' })),
        ...drums(2, 26, (b) => ({ k: 'X.......X.....g.', s: '....X.......X...', h: '..x...x...x...x.', x: 'g.g.g.g.g.g.g.g.' + '', ...(b === 9 || b === 17 || b === 25 ? { s: '....X.......XxXX' } : {}) })),
        ...drums(26, 27, { k: 'X.......X.......', s: 'X...............' }),
        { step: 2 * 16, k: 'c', v: 0.9 }, { step: 10 * 16, k: 'c', v: 0.8 }, { step: 18 * 16, k: 'c', v: 0.9 }, { step: 26 * 16, k: 'c', v: 1 },
      ],
    };
  }

  // ================================================================ 3. 뉴런 시냅스 (Neon Synapse): D minor, 120 BPM
  function neonSynapse() {
    const chart = ['Dm', 'Dm',
      'Dm', 'Bb', 'C', 'Am', 'Dm', 'Bb', 'Gm', 'A',
      'Gm', 'Dm', 'Bb', 'F', 'Gm', 'Dm', 'Bb C', 'A',
      'Dm', 'Bb', 'C', 'Am', 'Dm', 'Bb', 'Gm', 'A',
      'Dm', 'Dm'];
    const A = [
      'D5 - - - - - - - F5 - - - E5 - D5 -',
      'F5 - - - - - - - D5 - - - . . . .',
      'E5 - - - - - G5 - - - - - E5 - C5 -',
      'E5 - - - - - - - - - - - . . . .',
      'A5 - - - - - - - G5 - - - F5 - E5 -',
      'F5 - - - D5 - - - - - - - . . F5 -',
      'G5 - - - - - Bb5 - - - A5 - G5 - F5 -',
      'E5 - - - - - - - C#5 - - - E5 - - -'];
    const Bm = [
      'G5 - D5 - G5 - Bb5 - A5 - G5 - D5 - - -',
      'F5 - D5 - A4 - D5 - F5 - - - E5 - D5 -',
      'D5 - F5 - Bb5 - - - - - A5 - F5 - D5 -',
      'C5 - F5 - A5 - - - G5 - - - F5 - - -',
      'G5 - D5 - G5 - Bb5 - D6 - - - C6 - Bb5 -',
      'A5 - - - F5 - - - D5 - - - F5 - A5 -',
      'Bb5 - - - F5 - - - G5 - - - E5 - - -',
      'E5 - - - - - - - - - - - . . . .'];
    const lead = [...melody(A, 2), ...melody(Bm, 10), ...melody(A, 18), ...melody(['D5 - - - - - - - - - - - - - - -'], 26)];
    const harm = harmony(melody(A.slice(0, 7), 18), chart);
    return {
      name: '뉴런 시냅스', en: 'Neon Synapse', bpm: 120, bars: 28, echoWet: 0.3, echoFb: 0.38,
      ch: {
        lead: { wave: 'p0.25', vol: 0.21, pan: -0.1, echo: 0.32, vib: { depth: 16, rate: 5.2, delay: 0.2 }, env: { a: 0.006, d: 0.2, s: 0.75, r: 0.08 }, notes: lead },
        harm: { wave: 'p0.5', vol: 0.07, pan: 0.4, echo: 0.2, lp: 2600, vib: { depth: 12, rate: 5.2, delay: 0.2 }, notes: harm },
        arp: { wave: 'p0.125', vol: 0.06, pan: -0.45, echo: 0.28, env: { a: 0.002, d: 0.08, s: 0.2, r: 0.03 }, gate: 1,
          notes: [...arps(chart, 0, 26, 57, [0, 2, 1, 3, 2, 1, 3, 4]), ...arps(chart, 26, 27, 57, [0, 2, 1, 3, 2, 1, 3, 4], 1, 1, 0.6)] },
        bass: { wave: 'tri', vol: 0.27, gate: 0.85,
          notes: [...bassLine(chart, 'R - - R - - O - . . R - O - 5 -', 1, 10, 38),
                  ...bassLine(chart, 'R - - - R - - - O - - - R - 5 -', 10, 18, 38),
                  ...bassLine(chart, 'R - - R - - O - . . R - O - 5 -', 18, 26, 38),
                  ...bassLine(chart, 'R - - - - - - - - - - - - - - -', 26, 27, 38)] },
      },
      drums: [
        ...drums(0, 1, { h: 'x.g.x.g.x.g.x.g.' }),
        ...drums(1, 2, { k: 'X.....x...X.....', h: 'x.g.x.g.x.g.x.g.', s: '............gxxX' }),
        ...drums(2, 10, (b) => ({ k: 'X.....x...X.....', s: '....X.......X...', h: 'xgxgxgxgxgxgxgxg', ...(b === 9 ? { s: '....X.......XxXX' } : {}) })),
        ...drums(10, 18, (b) => ({ k: 'X..x....X..x....', s: '....X.......X...', h: 'x.x.x.x.x.x.x.x.', o: '......x.......x.', ...(b === 17 ? { s: '....X...gxxxXXXX' } : {}) })),
        ...drums(18, 26, (b) => ({ k: 'X.....x...X.....', s: '....X.......X...', h: 'xgxgxgxgxgxgxgxg', ...(b === 25 ? { s: '....X.......XxXX' } : {}) })),
        ...drums(26, 27, { k: 'X...............', S: 'X...............' }),
        { step: 2 * 16, k: 'c', v: 0.8 }, { step: 10 * 16, k: 'c', v: 0.9 }, { step: 18 * 16, k: 'c', v: 0.9 }, { step: 26 * 16, k: 'c', v: 1 },
      ],
    };
  }

  // ================================================================ 4. 레트로 오버드라이브 (Retro Overdrive): E minor, 112 BPM
  function retroOverdrive() {
    const chart = ['Em', 'Em',
      'Em', 'C', 'G', 'D', 'Em', 'C', 'Am', 'B',
      'C', 'D', 'Em', 'Em', 'C', 'D', 'B', 'B',
      'Em', 'C', 'G', 'D', 'Em', 'C', 'Am', 'B',
      'Em', 'Em'];
    const A = [
      'B4 - - - E5 - - - G5 - - - G5 - F#5 -',
      'E5 - - - - - - - D5 - - - C5 - - -',
      'B4 - - - D5 - - - G5 - - - A5 - B5 -',
      'A5 - - - - - - - F#5 - - - D5 - - -',
      'B5 - - - - - A5 - G5 - - - E5 - F#5 -',
      'G5 - - - - - - - E5 - - - C5 - E5 -',
      'A5 - - - - - G5 - E5 - - - C5 - A4 -',
      'B4 - - - D#5 - - - F#5 - - - B5 - - -'];
    const Bm = [
      'G5 - - - - - - - E5 - G5 - C6 - - -',
      'A5 - - - - - - - F#5 - A5 - D6 - - -',
      'B5 - - - - - - - - - - - G5 - A5 -',
      'B5 - - - G5 - E5 - - - - - . . . .',
      'E5 - G5 - C6 - - - - - B5 - G5 - E5 -',
      'F#5 - A5 - D6 - - - - - A5 - F#5 - - -',
      'D#6 - - - - - - - B5 - - - F#5 - - -',
      'D#5 - - - F#5 - - - A5 - - - B5 - - -'];
    const legato = (ns) => ns.map((nt, i) => (i > 0 && ns[i - 1].step + ns[i - 1].len === nt.step && Math.abs(ns[i - 1].n - nt.n) <= 7 ? { ...nt, slideFrom: ns[i - 1].n, slideT: 0.045 } : nt));
    const lead = legato([...melody(A, 2), ...melody(Bm, 10), ...melody(A, 18), ...melody(['E5 - - - - - - - - - - - - - - -'], 26)]);
    const harm = harmony(melody(A.slice(0, 7), 18), chart);
    return {
      name: '레트로 오버드라이브', en: 'Retro Overdrive', bpm: 112, bars: 28, echoWet: 0.28, echoFb: 0.35,
      ch: {
        lead: { wave: 'p0.5', vol: 0.15, pan: -0.06, echo: 0.3, lp: 4200, vib: { depth: 18, rate: 5, delay: 0.22 }, env: { a: 0.006, d: 0.25, s: 0.8, r: 0.1 }, gate: 0.97, notes: lead },
        harm: { wave: 'p0.25', vol: 0.065, pan: 0.32, echo: 0.2, lp: 3000, vib: { depth: 14, rate: 5, delay: 0.22 }, notes: harm },
        pad: { wave: 'saw', vol: 0.032, pan: 0.35, detune: 7, lp: 1700, env: { a: 0.012, d: 0.16, s: 0.35, r: 0.05 }, gate: 1,
          notes: stabs(chart, 2, 26, [0, 2, 4, 6, 8, 10, 12, 14], 55, 2) },
        pad2: { wave: 'saw', vol: 0.032, pan: -0.35, detune: -7, lp: 1700, env: { a: 0.012, d: 0.16, s: 0.35, r: 0.05 }, gate: 1,
          notes: stabs(chart, 2, 26, [0, 2, 4, 6, 8, 10, 12, 14], 55, 2) },
        arp: { wave: 'p0.25', vol: 0.05, pan: 0.5, echo: 0.3, env: { a: 0.002, d: 0.1, s: 0.2, r: 0.04 }, gate: 1,
          notes: [...arps(chart, 0, 26, 71, [0, 1, 2, 3, 4, 3, 2, 1], 2, 2)] },
        bass: { wave: 'p0.5', vol: 0.11, lp: 900, gate: 0.85, env: { a: 0.003, d: 0.1, s: 0.8, r: 0.03 },
          notes: [...bassLine(chart, 'R - O - R - O - R - O - R - O -', 1, 26, 33), ...bassLine(chart, 'R - - - - - - - - - - - - - - -', 26, 27, 33)] },
        sub: { wave: 'sine', vol: 0.1, gate: 0.85, env: { a: 0.004, d: 0.1, s: 0.85, r: 0.03 },
          notes: [...bassLine(chart, 'R - R - R - R - R - R - R - R -', 1, 26, 21), ...bassLine(chart, 'R - - - - - - - - - - - - - - -', 26, 27, 21)] },
      },
      drums: [
        ...drums(0, 1, { k: 'X.......X.......', h: '..o...o...o...o.' }),
        ...drums(1, 2, { k: 'X.......X.......', h: '..o...o...o...o.', t1: '........X.......', t2: '..........X.....', t3: '............X.X.' }),
        ...drums(2, 26, (b) => ({ k: 'X......gX.......', S: '....X.......X...', h: '..o...o...o...o.', x: 'g.g.g.g.g.g.g.g.',
          ...((b === 9 || b === 17 || b === 25) ? { t1: '........X.X.....', t2: '............X.X.', t3: '..............X.' } : {}) }), { S: { echo: 0.15 } }),
        ...drums(26, 27, { k: 'X...............', S: 'X...............' }),
        { step: 2 * 16, k: 'c', v: 0.9 }, { step: 10 * 16, k: 'c', v: 0.9 }, { step: 18 * 16, k: 'c', v: 0.9 }, { step: 26 * 16, k: 'c', v: 1 },
      ],
    };
  }

  return { all: [heartbeatRush, bubbleParade, neonSynapse, retroOverdrive], chord, SCALE };
})();
