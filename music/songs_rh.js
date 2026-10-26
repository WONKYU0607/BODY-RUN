// Three songs for the rhythm stage (candidates): exciting, each in its own sound - chip-rock, disco-funk, eurobeat.
// Each has an intro, a verse, a build, a chorus, a break and a last chorus a step higher (the lift), and an ending.
window.SongsRH = (() => {
  'use strict';
  const L = SongLib, { melody, tr, shift, harmony, legato, line, arps, stabs, drums } = L;

  // ================================================================ R1. 세포 록 앤섬 (Cell Rock Anthem): E minor -> F# minor, 150 BPM
  function cellRock() {
    const chart = ['Em', 'C', 'D', 'B',
      'Em', 'C', 'G', 'D', 'Em', 'C', 'Am', 'B',
      'C', 'D', 'Em', 'B',
      'C', 'D', 'Em', 'Em', 'Am', 'D', 'G', 'B',
      'Am', 'Em', 'C', 'B',
      'D', 'E', 'F#m', 'F#m', 'Bm', 'E', 'A', 'C#',
      'F#m', 'F#m'];
    const intro = ['E5 - - E5 - - G5 - A5 - - B5 - - A5 -', 'G5 - - E5 - - C5 - - - - - . . . .',
      'D5 - - F#5 - - A5 - B5 - - A5 - - F#5 -', 'D#5 - - - F#5 - - - B5 - - - . . . .'];
    const verse = ['E5 - E5 - G5 - - A5 - - G5 - E5 - D5 -', 'E5 - - - - - - - . . B4 - C5 - D5 -',
      'D5 - D5 - G5 - - A5 - - B5 - A5 - G5 -', 'F#5 - - - - - - - . . D5 - E5 - F#5 -',
      'G5 - G5 - B5 - - A5 - - G5 - E5 - G5 -', 'A5 - - - G5 - - - E5 - - - C5 - E5 -',
      'A5 - - - - - G5 - E5 - - - C5 - - -', 'B4 - - - D#5 - - - F#5 - - - A5 - - -'];
    const pre = ['G4 - C5 - E5 - G5 - - - E5 - G5 - - -', 'A4 - D5 - F#5 - A5 - - - F#5 - A5 - - -',
      'B4 - E5 - G5 - B5 - - - G5 - B5 - - -', 'B5 - - - A5 - - - F#5 - - - D#5 - - -'];
    const chorus = ['G5 - - G5 - - G5 - A5 - G5 - E5 - - -', 'F#5 - - F#5 - - F#5 - A5 - F#5 - D5 - - -',
      'E5 - - - G5 - - - B5 - - - A5 - G5 -', 'B5 - - - - - - - - - - - . . . .',
      'C6 - - C6 - - C6 - A5 - - - E5 - - -', 'D6 - - D6 - - D6 - A5 - - - F#5 - - -',
      'B5 - - - A5 - - - G5 - - - D5 - - -', 'F#5 - - - - - - - D#5 - - - B4 - - -'];
    const bridge = ['E5 - - - - - - - - - - - C5 - - -', 'B4 - - - - - - - - - - - G4 - - -',
      'C5 - - - - - E5 - - - - - G5 - - -', 'F#5 - - - - - - - . . . . . . . .'];
    const ch1 = melody(chorus, 16), ch2 = tr(shift(ch1, 12), 2);
    const lead = [...melody(intro, 0), ...melody(verse, 4), ...melody(pre, 12), ...ch1, ...melody(bridge, 24), ...ch2,
      ...melody(['F#5 - - - - - - - - - - - - - - -'], 36)];
    const choruses = [...ch1, ...ch2];
    const chug = 'P . P . P . P - P . P . P . P -', open = 'P - - - - - P - P - - - - - P -';
    return {
      name: '세포 록 앤섬', en: 'Cell Rock Anthem', bpm: 150, bars: 38, echoWet: 0.18,
      ch: {
        lead: { wave: 'p0.25', vol: 0.21, pan: -0.05, echo: 0.18, vib: { depth: 13, rate: 5.8, delay: 0.14 }, notes: lead },
        lead8: { wave: 'p0.125', vol: 0.05, pan: 0.2, echo: 0.1, notes: tr(choruses, 12) },
        harm: { wave: 'p0.5', vol: 0.075, pan: 0.36, lp: 2600, echo: 0.1, vib: { depth: 10, rate: 5.8, delay: 0.14 }, notes: harmony(choruses, chart) },
        gtrL: { wave: 'saw', vol: 0.08, pan: -0.65, detune: -7, drive: 4, post: 0.2, cab: 3400, gate: 0.9, env: { a: 0.003, d: 0.2, s: 0.8, r: 0.04 },
          notes: [...line(chart, chug, 0, 4, 40, 0.8), ...line(chart, chug, 4, 12, 40, 0.5), ...line(chart, 'P - P - P - P - P - P - P - P -', 12, 16, 40, 0.75), ...line(chart, open, 16, 24, 40),
                  ...line(chart, open, 28, 36, 40), ...line(chart, 'P - - - - - - - - - - - - - - -', 36, 37, 40)] },
        gtrR: { wave: 'square', vol: 0.06, pan: 0.65, detune: 7, drive: 4, post: 0.2, cab: 3000, gate: 0.9, env: { a: 0.003, d: 0.2, s: 0.8, r: 0.04 },
          notes: [...line(chart, chug, 0, 4, 40, 0.8), ...line(chart, chug, 4, 12, 40, 0.5), ...line(chart, 'P - P - P - P - P - P - P - P -', 12, 16, 40, 0.75), ...line(chart, open, 16, 24, 40),
                  ...line(chart, open, 28, 36, 40), ...line(chart, 'P - - - - - - - - - - - - - - -', 36, 37, 40)] },
        arp: { wave: 'p0.125', vol: 0.04, pan: 0.5, echo: 0.15, env: { a: 0.002, d: 0.08, s: 0.2, r: 0.03 }, gate: 1,
          notes: [...arps(chart, 4, 12, 64, [0, 1, 2, 3]), ...arps(chart, 24, 28, 64, [3, 2, 1, 2], 2, 2)] },
        bass: { wave: 'fm', fm: { ratio: 1, i0: 2.6, i1: 0.7, time: 0.12 }, vol: 0.2, gate: 0.85, env: { a: 0.003, d: 0.1, s: 0.8, r: 0.03 },
          notes: [...line(chart, 'R - R - R - R - R - R - R - R -', 0, 4, 28), ...line(chart, 'R - R - R - R - R - R - R - R -', 4, 12, 28, 0.8), ...line(chart, 'R - R - R - R - R - R - R - R -', 12, 16, 28), ...line(chart, 'R - R - R - R - O - R - R - O -', 16, 24, 28),
                  ...line(chart, 'R - - - - - - - R - - - - - - -', 24, 28, 28), ...line(chart, 'R - R - R - R - O - R - R - O -', 28, 36, 28),
                  ...line(chart, 'R - - - - - - - - - - - - - - -', 36, 37, 28)] },
      },
      drums: [
        ...drums(0, 4, (b) => ({ k: 'X.....x.X.......', s: b === 3 ? '....X...X.X.XXXX' : '....X.......X...', h: 'x.x.x.x.x.x.x.x.' })),
        ...drums(4, 12, (b) => ({ k: 'x.....g.x.......', s: '....x.......x...', h: 'g.g.g.g.g.g.g.g.', ...(b === 11 ? { t1: '............X...', t2: '.............X..', t3: '..............XX' } : {}) })),
        ...drums(12, 16, (b) => ({ k: 'X.X.X.X.X.X.X.X.', s: b === 15 ? 'X.X.X.X.XXXXXXXX' : '....X.......X...', h: b === 15 ? '................' : 'x.x.x.x.x.x.x.x.' })),
        ...drums(16, 24, (b) => ({ k: 'X.....x.X.x.....', s: '....X.......X...', h: 'o.x.o.x.o.x.o.x.', ...(b === 23 ? { s: '....X.......XxXX' } : {}) })),
        ...drums(24, 28, (b) => ({ k: 'X...............', s: '........X.......', r: 'x...x...x...x...', ...(b === 27 ? { s: 'X.X.X.X.XXXXXXXX', r: '................' } : {}) })),
        ...drums(28, 36, (b) => ({ k: 'X.....x.X.x.....', s: '....X.......X...', h: 'o.x.o.x.o.x.o.x.', ...(b === 35 ? { t1: '........X.X.....', t2: '............X.X.', t3: '..............X.' } : {}) })),
        ...drums(36, 37, { K: 'X...............', S: 'X...............' }),
        { step: 15 * 16, k: 'up', len: 16, v: 0.9 }, { step: 27 * 16, k: 'up', len: 16, v: 1 },
        ...[0, 16, 20, 28, 32, 36].map((b) => ({ step: b * 16, k: 'c', v: 1 })),
      ],
    };
  }

  // ================================================================ R2. 플라즈마 펑크 (Plasma Funk): A dorian -> B, 124 BPM
  function plasmaFunk() {
    const chart = ['Am7', 'D7',
      'Am7', 'D7', 'Am7', 'D7', 'Am7', 'D7', 'Am7', 'D7',
      'F', 'G', 'Em7', 'E7',
      'F', 'G', 'Em', 'Am', 'F', 'G', 'E7', 'Am',
      'Am7', 'D7', 'Am7', 'D7',
      'G', 'A', 'F#m', 'Bm', 'G', 'A', 'F#7', 'Bm',
      'Bm', 'Bm'];
    const verse = ['A4 - . C5 - . D5 - E5 - . G5 - E5 - .', 'F#5 - - - E5 - D5 - - - C5 - A4 - - -',
      'A4 - . C5 - . D5 - E5 - . A5 - G5 - E5', 'F#5 - - - - - - - . . A4 - C5 - D5 -',
      'A4 - . C5 - . D5 - E5 - . G5 - E5 - .', 'F#5 - - - E5 - D5 - - - C5 - D5 - E5 -',
      'G5 - - - E5 - - - D5 - C5 - A4 - - -', 'D5 - - - - - - - . . . . . . . .'];
    const pre = ['C5 - - - F5 - - - A5 - - - G5 - F5 -', 'D5 - - - G5 - - - B5 - - - A5 - G5 -',
      'E5 - - - G5 - - - B5 - - - D6 - - -', 'B5 - - - G#5 - - - E5 - - - D5 - - -'];
    const chorus = ['A5 - - - A5 - G5 - A5 - - - C6 - - -', 'B5 - - - B5 - A5 - B5 - - - D6 - - -',
      'G5 - - - E5 - - - B5 - - - G5 - - -', 'A5 - - - - - - - . . E5 - G5 - A5 -',
      'C6 - - - A5 - - - F5 - A5 - C6 - - -', 'D6 - - - B5 - - - G5 - B5 - D6 - - -',
      'D6 - - - B5 - - - G#5 - - - E5 - - -', 'A5 - - - - - - - - - - - . . . .'];
    const ch1 = melody(chorus, 14), ch2 = tr(shift(ch1, 12), 2);
    const lead = legato([...melody(verse, 2), ...melody(pre, 10), ...ch1, ...ch2, ...melody(['B5 - - - - - - - - - - - - - - -'], 34)], 5, 0.04);
    const slap = 'R . . R O . R . . R . 7 O . 5 .';
    return {
      name: '플라즈마 펑크', en: 'Plasma Funk', bpm: 124, bars: 36, echoWet: 0.16, drive: 1.35,
      ch: {
        lead: { wave: 'p0.5', vol: 0.16, pan: -0.05, echo: 0.16, lp: 3600, vib: { depth: 14, rate: 5.4, delay: 0.18 }, env: { a: 0.005, d: 0.15, s: 0.8, r: 0.06 }, notes: lead },
        horn: { wave: 'fm', fm: { ratio: 1, iA: 0.3, i0: 2.4, i1: 1.6, attack: 0.05, time: 0.3 }, vol: 0.075, pan: 0.15, lp: 4200, echo: 0.08,
          env: { a: 0.02, d: 0.2, s: 0.85, r: 0.06 }, notes: tr([...ch1, ...ch2], -12) },
        brass: { wave: 'fm', fm: { ratio: 1, iA: 0.2, i0: 2.8, i1: 1.8, attack: 0.03, time: 0.2 }, vol: 0.05, pan: 0.3, lp: 4500, env: { a: 0.012, d: 0.12, s: 0.7, r: 0.05 }, gate: 0.8,
          notes: [...stabs(chart, 14, 22, [[0, 3], [10, 2]], 64), ...stabs(chart, 22, 26, [[0, 2], [6, 2], [10, 2]], 64), ...stabs(chart, 26, 34, [[0, 3], [10, 2]], 64),
                  ...stabs(chart, 34, 35, [[0, 12]], 64)] },
        wah: { wave: 'p0.25', vol: 0.045, pan: -0.4, fenv: { type: 'bandpass', from: 500, to: 2600, time: 0.07, q: 3 }, env: { a: 0.002, d: 0.06, s: 0.4, r: 0.02 }, gate: 0.7,
          notes: [...stabs(chart, 0, 22, [2, 6, 10, 11, 14], 60), ...stabs(chart, 26, 34, [2, 6, 10, 11, 14], 60)] },
        strings: { wave: 'ssaw', spread: 12, vol: 0.012, pan: 0.2, lp: 2200, env: { a: 0.25, d: 0.4, s: 0.9, r: 0.3 }, gate: 1,
          notes: [...stabs(chart, 10, 22, [[0, 16]], 57), ...stabs(chart, 26, 34, [[0, 16]], 57)] },
        bass: { wave: 'fm', fm: { ratio: 1, i0: 4.5, i1: 0.6, time: 0.06 }, vol: 0.2, gate: 0.7, env: { a: 0.002, d: 0.08, s: 0.75, r: 0.03 },
          notes: [...line(chart, slap, 0, 22, 33), ...line(chart, 'R . R . O . . R . R O . 7 . 5 .', 22, 26, 33), ...line(chart, slap, 26, 34, 33),
                  ...line(chart, 'R - - - - - - - - - - - - - - -', 34, 35, 33)] },
      },
      drums: [
        ...drums(0, 2, (b) => ({ k: 'X...X...X...X...', s: '....X.......X...', h: 'x.x.x.x.x.x.x.x.', ...(b === 1 ? { s: '....X.......XxXX' } : {}) })),
        ...drums(2, 10, (b) => ({ k: 'X...X...X...X...', s: '....X.......X...', h: 'xgo.xgo.xgo.xgo.', ...(b === 9 ? { t1: '..........X.....', t2: '............X...', t3: '..............X.' } : {}) })),
        ...drums(10, 14, (b) => ({ k: 'X...X...X...X...', s: b === 13 ? '....X...XxXxXXXX' : '....X.......X...', cl: '....X.......X...', h: 'xgo.xgo.xgo.xgo.' })),
        ...drums(14, 22, (b) => ({ k: 'X...X...X...X...', s: '....X.......X...', cl: '....X.......X...', h: 'xgo.xgo.xgo.xgo.', cb: '..x...x...x.x...' })),
        ...drums(22, 26, (b) => ({ k: 'X...X...X...X...', cl: '....X.......X...', cb: 'x.x..x.x..x.x...', ...(b === 25 ? { s: '........XxXxXXXX' } : {}) })),
        ...drums(26, 34, (b) => ({ k: 'X...X...X...X...', s: '....X.......X...', cl: '....X.......X...', h: 'xgo.xgo.xgo.xgo.', cb: '..x...x...x.x...' })),
        ...drums(34, 35, { K: 'X...............', S: 'X...............' }),
        { step: 13 * 16, k: 'up', len: 16, v: 0.8 }, { step: 25 * 16, k: 'up', len: 16, v: 1 },
        ...[14, 22, 26, 34].map((b) => ({ step: b * 16, k: 'c', v: 0.9 })),
      ],
    };
  }

  // ================================================================ R3. 뉴로 유로비트 (Neuro Eurobeat): D minor -> Eb minor, 155 BPM
  function neuroEurobeat() {
    const chart = ['Dm', 'Bb', 'C', 'A',
      'Dm', 'Bb', 'C', 'A', 'Dm', 'Bb', 'Gm', 'A',
      'Bb', 'C', 'Dm', 'A7',
      'Bb', 'C', 'Am', 'Dm', 'Gm', 'C', 'A', 'A',
      'Dm', 'Bb', 'C', 'A',
      'B', 'Db', 'Bbm', 'Ebm', 'Abm', 'Db', 'Bb', 'Bb',
      'Ebm', 'Ebm'];
    const riff = ['D5 - A4 - D5 - F5 - E5 - D5 - C5 - A4 -', 'Bb4 - F4 - Bb4 - D5 - C5 - Bb4 - F5 - D5 -',
      'C5 - G4 - C5 - E5 - D5 - C5 - Bb4 - G4 -', 'A4 - C#5 - E5 - A5 - G5 - E5 - C#5 - A4 -'];
    const verse = ['D5 - - - D5 - E5 - F5 - - - A5 - F5 -', 'D5 - - - - - C5 - Bb4 - - - . . . .',
      'C5 - - - C5 - D5 - E5 - - - D5 - C5 -', 'C#5 - - - - - - - E5 - - - . . . .',
      'F5 - - - F5 - G5 - A5 - - - G5 - F5 -', 'F5 - - - - - E5 - D5 - - - . . . .',
      'G5 - - - Bb5 - - - A5 - G5 - F5 - - -', 'E5 - - - - - - - C#5 - - - A4 - - -'];
    const pre = ['F5 - - F5 - - F5 - - - D5 - F5 - - -', 'G5 - - G5 - - G5 - - - E5 - G5 - - -',
      'A5 - - A5 - - A5 - - - F5 - A5 - - -', 'A5 - - - G5 - - - E5 - - - C#5 - - -'];
    const chorus = ['D6 - - - C6 - - - Bb5 - - - F5 - Bb5 -', 'C6 - - - D6 - - - E6 - - - G5 - - -',
      'E6 - - - - - - - C6 - - - A5 - - -', 'D6 - - - - - - - - - - - . . A5 -',
      'Bb5 - - - - - A5 - G5 - - - D5 - G5 -', 'C6 - - - Bb5 - - - G5 - - - E5 - G5 -',
      'A5 - - - - - - - C#6 - - - E6 - - -', 'C#6 - - - - - - - - - - - . . . .'];
    const ch1 = melody(chorus, 16), ch2 = tr(shift(ch1, 12), 1);
    const r1 = melody(riff, 0), r2 = shift(r1, 24);
    const lead = [...melody(verse, 4), ...melody(pre, 12), ...ch1, ...ch2, ...melody(['Eb5 - - - - - - - - - - - - - - -'], 36)];
    return {
      name: '뉴로 유로비트', en: 'Neuro Eurobeat', bpm: 155, bars: 38, echoWet: 0.2, drive: 1.35,
      ch: {
        lead: { wave: 'p0.5', vol: 0.16, pan: -0.05, echo: 0.2, lp: 4200, vib: { depth: 14, rate: 6, delay: 0.16 }, notes: lead },
        lead8: { wave: 'p0.125', vol: 0.045, pan: 0.25, echo: 0.12, notes: tr([...ch1, ...ch2], -12) },
        brass: { wave: 'fm', fm: { ratio: 1, iA: 0.4, i0: 3, i1: 1.8, attack: 0.025, time: 0.2 }, vol: 0.13, pan: 0.05, lp: 5000, echo: 0.12, env: { a: 0.008, d: 0.1, s: 0.8, r: 0.04 }, gate: 0.85,
          notes: [...r1, ...r2] },
        brass2: { wave: 'p0.25', vol: 0.06, pan: -0.3, gate: 0.85, notes: tr([...r1, ...r2], 12) },
        stab: { wave: 'ssaw', spread: 16, vol: 0.016, pan: 0, lp: 5000, duck: 0.5, env: { a: 0.004, d: 0.12, s: 0.5, r: 0.05 }, gate: 0.8,
          notes: [...stabs(chart, 12, 24, [2, 6, 10, 14], 57, 2), ...stabs(chart, 28, 36, [2, 6, 10, 14], 57, 2)] },
        pad: { wave: 'ssaw', spread: 20, vol: 0.008, pan: 0, lp: 2600, duck: 0.6, env: { a: 0.15, d: 0.3, s: 0.9, r: 0.2 }, gate: 1,
          notes: [...stabs(chart, 16, 24, [[0, 16]], 57), ...stabs(chart, 28, 36, [[0, 16]], 57)] },
        orch: { wave: 'ssaw', spread: 22, vol: 0.03, pan: 0, lp: 6000, env: { a: 0.002, d: 0.25, s: 0.05, r: 0.15 }, gate: 1,
          notes: [0, 16, 28].flatMap((b) => line(chart, 'C - - - - - - - . . . . . . . .', b, b + 1, 57)).concat([0, 16, 28].flatMap((b) => line(chart, 'R - - - - - - - . . . . . . . .', b, b + 1, 45))) },
        arp: { wave: 'p0.125', vol: 0.04, pan: 0.5, echo: 0.2, env: { a: 0.002, d: 0.07, s: 0.2, r: 0.03 }, gate: 1,
          notes: [...arps(chart, 4, 12, 69, [0, 1, 2, 3, 4, 3, 2, 1], 1, 1, 0.7), ...arps(chart, 16, 24, 69, [0, 1, 2, 3, 4, 3, 2, 1]), ...arps(chart, 28, 36, 69, [0, 1, 2, 3, 4, 3, 2, 1])] },
        bass: { wave: 'p0.5', vol: 0.1, lp: 1100, duck: 0.35, gate: 0.8, env: { a: 0.002, d: 0.08, s: 0.8, r: 0.03 },
          notes: [...line(chart, 'R - O - R - O - R - O - R - O -', 0, 4, 33), ...line(chart, 'R - O - R - O - R - O - R - O -', 4, 12, 33, 0.75), ...line(chart, 'R - O - R - O - R - O - R - O -', 12, 36, 33), ...line(chart, 'R - - - - - - - - - - - - - - -', 36, 37, 33)] },
        sub: { wave: 'sine', vol: 0.09, duck: 0.35, gate: 0.8, notes: [...line(chart, 'R - R - R - R - R - R - R - R -', 0, 36, 21), ...line(chart, 'R - - - - - - - - - - - - - - -', 36, 37, 21)] },
      },
      drums: [
        ...drums(0, 4, (b) => ({ k: 'X...X...X...X...', h: '..o...o...o...o.', s: b === 3 ? '....X...XxXxXXXX' : '....X.......X...' })),
        ...drums(4, 12, (b) => ({ k: 'x...x...x...x...', cl: '....x.......x...', h: 'g.g.g.g.g.g.g.g.', ...(b === 11 ? { t1: '........X.X.....', t2: '............X.X.', t3: '..............XX' } : {}) })),
        ...drums(12, 16, (b) => ({ k: 'X...X...X...X...', s: b === 15 ? 'X.X.X.X.XXXXXXXX' : b === 14 ? 'X...X...X.X.X.X.' : '....X.......X...', h: 'x.o.x.o.x.o.x.o.' })),
        ...drums(16, 24, (b) => ({ k: 'X...X...X...X...', s: '....X.......X...', cl: '....X.......X...', h: 'xxoxxxoxxxoxxxox', ...(b === 23 ? { s: '....X...XxXxXXXX' } : {}) })),
        ...drums(24, 28, (b) => ({ k: 'X...X...X...X...', cl: '....X.......X...', h: 'x.o.x.o.x.o.x.o.', ...(b === 27 ? { s: 'X.X.X.X.XXXXXXXX' } : {}) })),
        ...drums(28, 36, (b) => ({ k: 'X...X...X...X...', s: '....X.......X...', cl: '....X.......X...', h: 'xxoxxxoxxxoxxxox' })),
        ...drums(36, 37, { K: 'X...............', S: 'X...............' }),
        { step: 15 * 16, k: 'up', len: 16, v: 0.9 }, { step: 27 * 16, k: 'up', len: 16, v: 1 },
        ...[0, 16, 20, 24, 28, 32, 36].map((b) => ({ step: b * 16, k: 'c', v: 1 })),
      ],
    };
  }

  return { all: [cellRock, plasmaFunk, neuroEurobeat] };
})();
