// The baseball stage's music: a ballpark organ over the crowd, inside the body (a bubble now and then). 16 bars at
// 132 BPM = 29.1 s, made to loop: rendered three times round, the middle one is the file (what rings over the end of
// a round is there at the start of the next). An original tune (a bouncy organ lead, off-beat organ chords, a walking
// pedal bass, light kick and clap, a shaker, and from bar 13 the crowd clapping along; the crowd's murmur all through).
window.SongsBB = (() => {
  'use strict';
  const L = SongLib, { melody, line, stabs, drums } = L;
  const BARS = 16;
  function ballpark(rounds = 3) {
    const chart = ['F', 'F', 'Bb', 'F', 'C7', 'C7', 'F', 'F', 'Bb', 'Bb', 'F', 'Dm', 'G7', 'C7', 'F', 'C7'];
    const lead = melody([
      'C5 - A4 - C5 - F5 - - - A5 - G5 - F5 -', 'C5 - - - A4 - - - C5 - D5 - C5 - A4 -',
      'D5 - F5 - Bb5 - - - A5 - G5 - F5 - D5 -', 'C5 - - - F5 - - - A4 - - - . . . .',
      'E5 - G5 - Bb5 - - - A5 - G5 - E5 - C5 -', 'D5 - E5 - G5 - - - Bb4 - - - . . C5 -',
      'A5 - - - G5 - F5 - C5 - - - A4 - C5 -', 'F5 - - - - - - - . . . . C5 - D5 -',
      'D5 - - - Bb4 - D5 - F5 - - - D5 - F5 -', 'Bb5 - - - A5 - G5 - F5 - - - D5 - - -',
      'C5 - F5 - A5 - C6 - - - A5 - F5 - - -', 'D5 - F5 - A5 - - - F5 - D5 - A4 - - -',
      'B4 - D5 - F5 - G5 - - - F5 - D5 - B4 -', 'C5 - E5 - G5 - Bb5 - - - G5 - E5 - C5 -',
      'F5 - A5 - C6 - A5 - F5 - - - C5 - - -', 'E5 - - - G5 - - - Bb5 - - - C6 - - -',
    ], 0);
    const bubbles = [];
    for (let b = 0; b < BARS; b += 2) bubbles.push({ step: b * 16 + [5, 11, 7, 13][(b >> 1) % 4], k: 'bub', v: 0.6, f: [520, 640, 760, 600][(b >> 1) % 4], pan: (b % 4 ? 0.4 : -0.4), echo: 0.25 });
    const one = {
      ch: {
        lead: { wave: 'organ', vol: 0.075, pan: -0.08, lp: 5200, echo: 0.12, rev: 0.35, gate: 0.92,
          env: { a: 0.004, d: 0.12, s: 0.82, r: 0.07 }, vib: { depth: 9, rate: 6.6, delay: 0 }, notes: lead },
        comp: { wave: 'organ', vol: 0.03, pan: 0.18, lp: 2600, rev: 0.3, gate: 0.55,
          env: { a: 0.003, d: 0.1, s: 0.7, r: 0.05 }, vib: { depth: 6, rate: 6.6, delay: 0 }, notes: stabs(chart, 0, BARS, [2, 6, 10, 14], 60) },
        bass: { wave: 'organ', vol: 0.11, lp: 900, gate: 0.85, env: { a: 0.004, d: 0.1, s: 0.8, r: 0.05 },
          notes: line(chart, (b) => (b % 2 ? 'R - - - 3 - - - 5 - - - O - - -' : 'R - - - 5 - - - 3 - - - 5 - - -'), 0, BARS, 36) },
      },
      drums: [
        ...drums(0, BARS, (b) => ({ k: 'x.......x.......', cl: b >= 12 ? '....x.......x...' : '....g.......g...', x: 'g.g.g.g.g.g.g.g.' })),
        ...drums(12, BARS, () => ({ cl: 'x.x.x.x...x.x...' }), { cl: { pan: 0.35 } }),        // the crowd claps along
        ...bubbles,
      ],
    };
    const ch = {};
    for (const [k, c] of Object.entries(one.ch)) { ch[k] = { ...c, notes: [] }; for (let r = 0; r < rounds; r++) ch[k].notes.push(...L.shift(c.notes, r * BARS)); }
    const drm = []; for (let r = 0; r < rounds; r++) drm.push(...one.drums.map((d) => ({ ...d, step: d.step + r * BARS * 16 })));
    drm.push({ step: 0, k: 'crowd', v: 1, len: rounds * BARS * 16 });            // the murmur, one long sound through every round
    return { name: '몸속 야구장', en: 'Inner Ballpark', bpm: 132, bars: BARS * rounds, loopBars: BARS, echoWet: 0.18, drumGain: 0.75, lp: 12000,
      reverb: { time: 2.4, wet: 0.28, damp: 4500 }, drumRev: { cl: 0.3, k: 0.1, bub: 0.3, crowd: 0.2 }, ch, drums: drm };
  }
  return { ballpark };
})();
