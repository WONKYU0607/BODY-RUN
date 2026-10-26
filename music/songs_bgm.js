// The running music: light and fresh, as if under water (a vibraphone and a flute over soft pads, water-drop
// arpeggios, bubbles, a round bass, quiet woody drums, the whole a little softened and in a hall). 24 bars at
// 100 BPM = 57.6 s, made to loop: rendered three times round, the middle one is the file (so what rings over
// the end of a round is there at the start of the next).
window.SongsBGM = (() => {
  'use strict';
  const L = SongLib, { melody, line, arps, stabs, drums } = L;
  const BARS = 24;
  function innerTide(rounds = 3) {
    const chart = ['Dmaj7', 'Bm7', 'Gmaj7', 'A', 'Dmaj7', 'Bm7', 'Gmaj7', 'A',
      'Gmaj7', 'F#m7', 'Em7', 'A7', 'Gmaj7', 'F#m7', 'Bm7', 'A',
      'Bm7', 'Gmaj7', 'Dmaj7', 'A', 'Bm7', 'Gmaj7', 'Em7', 'A7'];
    const A = ['F#5 - - A5 - - D6 - - - - - A5 - - -', 'B5 - - - A5 - F#5 - - - - - D5 - - -',
      'G5 - - B5 - - D6 - - - B5 - A5 - - -', 'E5 - - - - - - - . . . . C#5 - E5 -',
      'F#5 - - A5 - - E6 - - - - - D6 - - -', 'D6 - - - C#6 - B5 - - - A5 - F#5 - - -',
      'B5 - - - A5 - G5 - - - F#5 - D5 - - -', 'E5 - - - - - - - - - - - . . . .'];
    const B = ['B5 - D6 - B5 - A5 - G5 - - - - - D5 -', 'A5 - C#6 - A5 - F#5 - E5 - - - - - C#5 -',
      'G5 - B5 - G5 - E5 - D5 - - - - - B4 -', 'C#5 - E5 - G5 - - - A5 - - - - - - -',
      'B5 - D6 - B5 - A5 - G5 - - - B5 - D6 -', 'C#6 - - - A5 - - - F#5 - - - A5 - C#6 -',
      'D6 - - - B5 - - - F#5 - - - A5 - B5 -', 'C#6 - - - - - - - E5 - - - A5 - - -'];
    const C = ['F#5 - - - - - - - - - - - D5 - E5 -', 'D5 - - - - - - - B4 - - - D5 - - -',
      'A5 - - - - - - - - - - - F#5 - A5 -', 'E5 - - - - - - - - - - - . . . .',
      'D6 - - - - - - - - - - - B5 - C#6 -', 'D6 - - - - - - - B5 - - - G5 - - -',
      'B5 - - - - - - - G5 - - - E5 - - -', 'C#6 - - - - - - - E5 - - - G5 - - -'];
    const vibe = [...melody(A, 0), ...melody(B, 8)], flute = melody(C, 16);
    // bubbles here and there (the same each round), a drip every other bar
    const bubbles = [];
    const F = [430, 520, 610, 700, 820, 940];
    for (let b = 0; b < BARS; b++) {
      const spots = [[3, 11], [6, 14], [2, 9, 13], [5, 15]][b % 4];
      spots.forEach((s, i) => bubbles.push({ step: b * 16 + s, k: 'bub', v: 0.55 + 0.25 * ((b + i) % 3) / 2, f: F[(b * 3 + i * 2) % F.length], pan: (i % 2 ? 0.45 : -0.45) * (b % 2 ? 1 : -1), echo: 0.25 }));
      if (b % 2 === 1) bubbles.push({ step: b * 16 + 12, k: 'drip', v: 0.7, f: [1500, 1800, 1650, 1950][(b >> 1) % 4], pan: 0.3, echo: 0.3 });
    }
    const one = {
      ch: {
        vibe: { wave: 'fm', fm: { ratio: 4, i0: 2.4, i1: 0.35, time: 0.5 }, vol: 0.12, pan: -0.1, echo: 0.18, rev: 0.4, gate: 0.9,
          env: { a: 0.002, d: 0.9, s: 0.15, r: 0.5 }, vib: { depth: 7, rate: 5.5, delay: 0.05 }, notes: vibe },
        flute: { wave: 'tri', vol: 0.12, pan: -0.05, lp: 3000, echo: 0.15, rev: 0.4, env: { a: 0.05, d: 0.3, s: 0.85, r: 0.2 },
          vib: { depth: 15, rate: 5, delay: 0.15 }, notes: flute },
        pad: { wave: 'ssaw', spread: 10, vol: 0.013, pan: 0.1, lp: 1500, rev: 0.5, gate: 1, env: { a: 0.5, d: 0.5, s: 0.9, r: 0.8 },
          vib: { depth: 5, rate: 0.35, delay: 0 }, notes: stabs(chart, 0, BARS, [[0, 16]], 57) },
        glass: { wave: 'p0.125', vol: 0.022, pan: 0.3, echo: 0.25, rev: 0.4, gate: 0.6, env: { a: 0.002, d: 0.3, s: 0.2, r: 0.2 }, notes: L.tr(vibe, 12) },
        plink: { wave: 'p0.25', vol: 0.035, pan: 0.45, echo: 0.3, rev: 0.35, gate: 1,
          env: { a: 0.001, d: 0.2, s: 0, r: 0.15 }, notes: [...arps(chart, 0, 16, 74, [0, 2, 3, 4, 3, 2, 1, 2], 2, 1), ...arps(chart, 16, BARS, 74, [3, 2, 4, 1], 4, 1, 0.8)] },
        bass: { wave: 'tri', vol: 0.22, lp: 900, gate: 0.8, env: { a: 0.004, d: 0.1, s: 0.8, r: 0.05 },
          notes: [...line(chart, 'R - - - . . R - O - - - 5 - . .', 0, 16, 38), ...line(chart, 'R - - - - - - - 5 - - - - - - -', 16, BARS, 38)] },
        sub: { wave: 'sine', vol: 0.05, gate: 0.9, notes: line(chart, 'R - - - - - - - R - - - - - - -', 0, BARS, 26) },
      },
      drums: [
        ...drums(0, 16, (b) => ({ k: 'x.......g..g....', ka: '....x.......x...', x: 'g.x.g.x.g.x.g.x.', h: b % 4 === 3 ? '..g...g...g...x.' : '' })),
        ...drums(16, BARS, (b) => ({ x: 'g.g.g.g.g.g.g.g.', k: b === BARS - 1 ? '........g.g.x...' : '' })),
        ...bubbles,
      ],
    };
    // round and round: the same bars again after themselves
    const ch = {};
    for (const [k, c] of Object.entries(one.ch)) { ch[k] = { ...c, notes: [] }; for (let r = 0; r < rounds; r++) ch[k].notes.push(...L.shift(c.notes, r * BARS)); }
    const drm = []; for (let r = 0; r < rounds; r++) drm.push(...one.drums.map((d) => ({ ...d, step: d.step + r * BARS * 16 })));
    return { name: '몸속 물결', en: 'Inner Tide', bpm: 100, bars: BARS * rounds, loopBars: BARS, echoWet: 0.22, drumGain: 0.8, lp: 12000,
      reverb: { time: 2.8, wet: 0.3, damp: 4200 }, drumRev: { ka: 0.25, k: 0.1, bub: 0.3, drip: 0.35 }, ch, drums: drm };
  }
  return { innerTide };
})();
