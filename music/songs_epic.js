// Four epic songs, heavy on the drums (a hall, big toms, taiko, impacts, a choir, brass and strings), written at the
// length of one go of a mini-game (about 35 s): two for the rhythm stage, two for the orbit stage.
// `game` says where the playing goes: the first note's step, the last (the final hit, on a downbeat), the build.
window.SongsEpic = (() => {
  'use strict';
  const L = SongLib, { melody, tr, line, arps, stabs, drums } = L;
  const choir = (notes, o = {}) => ({ wave: 'ssaw', spread: 16, vol: 0.022, pan: 0, lp: 2600, rev: 0.55, gate: 1,
    eq: [['peaking', 650, 7, 1.8], ['peaking', 1100, 5, 2.2], ['highshelf', 2800, -9, 0.7]],
    vib: { depth: 9, rate: 5, delay: 0.25 }, env: { a: 0.22, d: 0.4, s: 0.9, r: 0.35 }, notes, ...o });
  const strings = (notes, o = {}) => ({ wave: 'saw', vol: 0.05, pan: 0.35, detune: 5, lp: 3200, rev: 0.3, gate: 0.9,
    env: { a: 0.003, d: 0.07, s: 0.35, r: 0.04 }, notes, ...o });
  const brass = (notes, o = {}) => ({ wave: 'fm', fm: { ratio: 1, iA: 0.3, i0: 2.8, i1: 1.7, attack: 0.04, time: 0.25 }, vol: 0.09, pan: 0.1, lp: 4200, rev: 0.25,
    env: { a: 0.02, d: 0.2, s: 0.85, r: 0.08 }, notes, ...o });
  const hits = (notes, o = {}) => ({ wave: 'ssaw', spread: 24, vol: 0.05, pan: 0, lp: 6500, rev: 0.45, gate: 1,
    env: { a: 0.002, d: 0.22, s: 0.06, r: 0.2 }, notes, ...o });
  const at = (chart, spots, base, len = 4) => spots.flatMap(([b, s]) => stabs(chart, b, b + 1, [[s, len]], base));   // chord hits at [bar, step]
  const roots = (chart, spots, low, len = 4) => spots.map(([b, s]) => ({ step: b * 16 + s, n: L.inRange(L.chartAt(chart, b * 16 + s).pc, low), len, vol: 1 }));
  const crashes = (bars, v = 1) => bars.map((b) => ({ step: b * 16, k: 'c', v }));
  const REV = { SB: 0.3, S: 0.3, T: 0.35, T1: 0.3, T2: 0.3, T3: 0.3, boom: 0.25, c: 0.12, ka: 0.2 };
  const FILL = { T1: '........X.X.....', T2: '............X.X.', T3: '..............XX' };

  // ================================================================ E1. 백혈구 출정 (Leukocyte Crusade): D minor -> E minor, 160 BPM
  // symphonic chip-metal: a galloping riff, double kicks under the chorus, a choir, brass doubling the tune
  function leukocyteCrusade() {
    const chart = ['Dm', 'Dm', 'Bb C', 'Dm', 'Bb', 'Gm', 'A', 'Bb', 'C', 'Dm', 'Bb', 'F', 'C', 'Gm', 'Bb', 'A', 'B', 'Em', 'C', 'G', 'D', 'Em', 'Em'];
    const riff = melody(['D5 . D5 . F5 - E5 - D5 . D5 . A5 - G5 -', 'F5 - - - D5 - - - E5 - - - G5 - - -'], 1);
    const verse = melody(['A4 - D5 - F5 - A5 - - - G5 - F5 - C5 -', 'D5 - - - - - - - F5 - - - D5 - Bb4 -',
      'G4 - Bb4 - D5 - G5 - - - F5 - D5 - Bb4 -', 'A4 - - - C#5 - - - E5 - - - A5 - - -'], 3);
    const build = melody(['Bb4 - D5 - F5 - Bb5 - - - F5 - D5 - F5 -', 'E5 - - - G5 - - - C6 - - - - - - -'], 7);
    const chorus = ['D5 - - - - - F5 - A5 - - - - - D6 -', 'D6 - - - - - - - C6 - Bb5 - - - F5 -',
      'A5 - - - - - C6 - A5 - - - F5 - A5 -', 'G5 - - - - - - - E5 - G5 - C6 - - -',
      'Bb5 - - - - - D6 - G5 - - - - - Bb5 -', 'D6 - - - - - - - F5 - - - Bb5 - - -',
      'C#6 - - - - - - - A5 - - - E5 - - -', 'D#6 - - - - - - - B5 - - - F#5 - - -'];
    const ch1 = melody(chorus, 9), lift = tr(melody(chorus.slice(0, 4), 17), 2);
    const end = melody(['E6 - - - - - - - . . B5 - E6 - - -', 'E6 - - - - - - - - - - - - - - -'], 21);
    const big = [...ch1, ...lift, ...end];
    const tune = [...riff, ...verse, ...build, ...big];
    const hitAt = [[0, 0], [1, 0], [9, 0], [17, 0], [21, 0], [21, 10], [21, 12], [22, 0]];
    return {
      name: '백혈구 출정', en: 'Leukocyte Crusade', bpm: 160, bars: 23, echoWet: 0.1, drive: 1.15, drumGain: 1.25,
      reverb: { time: 2.4, wet: 0.3, damp: 4200 }, drumRev: REV,
      game: { first: 16, last: 22 * 16, build: [7 * 16, 9 * 16] }, tune,
      ch: {
        lead: { wave: 'p0.25', vol: 0.195, pan: -0.05, echo: 0.08, rev: 0.22, vib: { depth: 12, rate: 5.8, delay: 0.14 }, notes: tune },
        lead8: { wave: 'p0.125', vol: 0.04, pan: 0.22, rev: 0.2, notes: tr(big, 12) },
        brass: brass([...tr(riff, -12), ...tr(big, -12)], { vol: 0.11 }),
        stab: brass(stabs(chart, 3, 9, [[0, 3], [6, 2], [10, 2]], 55), { vol: 0.05, pan: -0.3, gate: 0.8 }),
        choir: choir([...stabs(chart, 0, 1, [[0, 16]], 57, 16, 0.6), ...stabs(chart, 3, 9, [[0, 16]], 57, 16, 0.55), ...stabs(chart, 9, 23, [[0, 16]], 57)]),
        str: strings([...arps(chart, 1, 3, 50, [0, 0, 3, 0], 1, 1, 0.8), ...arps(chart, 3, 9, 62, [0, 2, 3, 2], 2, 1, 0.8), ...arps(chart, 9, 21, 62, [0, 2, 3, 2])]),
        hit: hits([...at(chart, hitAt, 57), ...roots(chart, hitAt, 38)]),
        bass: { wave: 'p0.5', vol: 0.11, lp: 1000, gate: 0.8, env: { a: 0.002, d: 0.08, s: 0.8, r: 0.03 },
          notes: [...line(chart, 'R - - - - - - - - - - - - - - -', 0, 1, 33), ...line(chart, 'R - R - R - R - R - R - R - R -', 1, 21, 33),
            ...line(chart, 'R - - - - - - - . . R - R - - -', 21, 22, 33), ...line(chart, 'R - - - - - - - - - - - - - - -', 22, 23, 33)] },
        sub: { wave: 'sine', vol: 0.085, gate: 0.85, notes: [...line(chart, 'R - - - R - - - R - - - R - - -', 1, 21, 21), ...line(chart, 'R - - - - - - - - - - - - - - -', 21, 23, 21)] },
      },
      drums: [
        ...drums(0, 1, { boom: 'X...............', T: '....x...X...X...', T1: '............X...', T2: '.............X..', T3: '..............XX' }),
        ...drums(1, 3, (b) => ({ K: 'X...X...X...X...', kd: '..xx..xx..xx..xx', SB: b === 2 ? '....X...X.X.XXXX' : '....X.......X...' })),
        ...drums(3, 7, (b) => ({ K: 'X.....x.X.x.....', SB: '....X.......X...', h: b === 6 ? 'x.x.x.x.........' : 'x.x.x.x.x.x.x.x.', ...(b === 6 ? FILL : {}) })),
        ...drums(7, 9, (b) => (b === 7 ? { K: 'X...X...X...X...', T: '..x...x...x...x.', SB: '....X.......X...', h: 'x.x.x.x.x.x.x.x.' }
          : { K: 'X...X...X...X...', SB: 'x.x.x.x.xxxxXXXX' })),
        ...drums(9, 21, (b) => ({ K: 'X...X...X...X...', kd: '.gxg.gxg.gxg.gxg', SB: '....X.......X...', r: 'x.x.x.x.x.x.x.x.',
          ...(b === 16 ? { SB: '....X...X.XXXXXX', r: 'x.x.x.x.........' } : b === 20 ? { ...FILL, r: 'x.x.x.x.........' } : {}) })),
        ...drums(21, 22, { K: 'X.........X.X...', SB: 'X.........X.X...', boom: 'X...............' }),
        ...drums(22, 23, { K: 'X...............', SB: 'X...............', boom: 'X...............' }),
        ...crashes([1, 3, 9, 11, 13, 15, 17, 19, 21, 22]),
        { step: 7 * 16, k: 'up', len: 32, v: 1 }, { step: 9 * 16, k: 'boom', v: 0.8 }, { step: 17 * 16, k: 'boom', v: 0.8 },
      ],
    };
  }

  // ================================================================ E2. 심장 북소리 (War Drums of the Heart): C minor, 140 BPM
  // a trailer march: taiko under a staccato string ostinato, a horn call, a half-time chorus with the choir, a break
  // where the orchestra hits with the drums
  function heartDrums() {
    const chart = ['Cm', 'Cm', 'Cm', 'Cm', 'Ab', 'Bb', 'G', 'Ab', 'Bb', 'Cm', 'Ab', 'Eb', 'Bb', 'Fm', 'Ab', 'G', 'G', 'Cm', 'Cm', 'Cm', 'Cm'];
    const horn = melody(['C5 - - - - - G4 - C5 - Eb5 - G5 - - -', 'G5 - - - F5 - Eb5 - F5 - - - G5 - - -'], 1);
    const verse = melody(['C5 - - - Eb5 - - - G5 - - - - - Bb5 -', 'C6 - - - - - - - Ab5 - - - Eb5 - - -',
      'D5 - - - F5 - - - Bb5 - - - - - D6 -', 'D6 - - - - - - - B5 - - - G5 - - -'], 3);
    const build = melody(['Eb5 - Ab5 - C6 - - - Eb5 - Ab5 - C6 - - -', 'F5 - Bb5 - D6 - - - F5 - Bb5 - D6 - - -'], 7);
    const chorus = melody(['C6 - - - - - - - G5 - - - Eb5 - G5 -', 'Ab5 - - - - - - - C6 - - - Eb6 - - -',
      'Bb5 - - - - - G5 - Eb5 - - - G5 - Bb5 -', 'D6 - - - - - - - Bb5 - - - F5 - - -',
      'C6 - - - - - - - Ab5 - - - F5 - Ab5 -', 'C6 - - - - - Eb6 - - - - - C6 - Ab5 -',
      'B5 - - - - - - - G5 - - - D6 - - -', 'D6 - - - - - - - - - - - . . . .'], 9);
    const brk = melody(['C5 - . . . . C5 - . . . . C5 - - -', 'C5 - . C5 - . C5 - C5 - C5 - C5 - C5 -'], 17);
    const fin = melody(['C6 - - - - - - - - - - - - - - -'], 19);
    const tune = [...horn, ...verse, ...build, ...chorus, ...brk, ...fin];
    const hitAt = [[1, 0], [9, 0], ...brk.map((n) => [Math.floor(n.step / 16), n.step % 16]), [19, 0]];
    return {
      name: '심장 북소리', en: 'War Drums of the Heart', bpm: 140, bars: 21, echoWet: 0.1, drive: 1.15, drumGain: 1.25,
      reverb: { time: 2.8, wet: 0.32, damp: 3800 }, drumRev: REV,
      game: { first: 16, last: 19 * 16, build: [7 * 16, 9 * 16] }, tune,
      ch: {
        lead: { wave: 'p0.5', vol: 0.17, pan: -0.05, echo: 0.08, rev: 0.25, lp: 3800, vib: { depth: 13, rate: 5.4, delay: 0.16 }, env: { a: 0.006, d: 0.18, s: 0.8, r: 0.07 },
          notes: [...verse, ...build, ...chorus, ...fin] },
        lead8: { wave: 'p0.125', vol: 0.04, pan: 0.22, rev: 0.2, notes: tr(chorus, 12) },
        horn: brass([...horn, ...tr(verse, -12), ...tr(chorus, -12), ...tr(fin, -12)], { vol: 0.11 }),
        choir: choir([...stabs(chart, 1, 9, [[0, 16]], 55, 16, 0.6), ...stabs(chart, 9, 17, [[0, 16]], 55), ...stabs(chart, 19, 20, [[0, 16]], 55)], { vol: 0.028 }),
        str: strings([...arps(chart, 1, 17, 48, [0, 0, 1, 0, 2, 0, 1, 0], 2, 1), ...arps(chart, 9, 17, 72, [0, 1, 2, 3, 2, 1, 2, 1], 1, 1, 0.55)], { lp: 2800 }),
        hit: hits([...at(chart, hitAt, 55, 4), ...roots(chart, hitAt, 36, 4)]),
        bass: { wave: 'p0.5', vol: 0.1, lp: 700, gate: 0.95, env: { a: 0.004, d: 0.1, s: 0.85, r: 0.06 },
          notes: [...line(chart, 'R - - - - - - - R - - - - - - -', 1, 17, 36), ...line(chart, 'R - - - - - - - - - - - - - - -', 19, 20, 36)] },
        sub: { wave: 'sine', vol: 0.09, gate: 0.95, notes: [...line(chart, 'R - - - - - - - R - - - - - - -', 1, 17, 24), ...line(chart, 'R - - - - - - - - - - - - - - -', 19, 20, 24)] },
      },
      drums: [
        ...drums(0, 1, { T: 'x...x...X...X...', ka: '..g...g...x...xx' }),
        ...drums(1, 3, (b) => ({ T: 'X..x..X...X.x...', K: 'X...............', ka: '..x.......x.....', ...(b === 2 ? { T1: '............X...', T2: '.............X..', T3: '..............XX' } : {}) })),
        ...drums(3, 7, (b) => ({ K: 'X.......X.......', SB: '........X.......', T: '...x..x....x.x..', r: 'x...x...x...x...', ...(b === 6 ? FILL : {}) })),
        ...drums(7, 9, (b) => (b === 7 ? { K: 'X...X...X...X...', T: 'X.X.X.X.X.X.X.X.' } : { K: 'X...X...X...X...', T: 'X...X...X...X...', SB: 'x.x.x.x.xxxxXXXX' })),
        ...drums(9, 17, (b) => ({ K: 'X.....X...X.....', SB: '........X.......', T: '..X..x.x..X..x.x', r: 'x.x.x.x.x.x.x.x.',
          ...(b === 16 ? { ...FILL, r: 'x.x.x.x.........', SB: '........X.......' } : {}) })),
        ...drums(17, 19, (b) => (b === 17 ? { T: 'X..X..X.X..X.X..', K: 'X.....X.....X...', ka: '..x..x..x..x..xx' }
          : { K: 'X..X..X.X.X.X.X.', T1: 'X.X.X.X.........', T2: '........X.X.X.X.', SB: '........xxxxXXXX' })),
        ...drums(19, 20, { K: 'X...............', SB: 'X...............', boom: 'X...............', T: 'X...............' }),
        ...crashes([1, 3, 9, 11, 13, 15, 17, 19]),
        { step: 7 * 16, k: 'up', len: 32, v: 1 }, { step: 16, k: 'boom', v: 0.9 }, { step: 9 * 16, k: 'boom', v: 1 },
      ],
    };
  }

  // ================================================================ E3. 척추 대모험 (Spine Odyssey): E minor, 128 BPM (orbit)
  // an adventure theme: a horn call, the tune on a square lead over striding strings, toms into the climb, then the
  // theme again an octave up with brass and choir
  function spineOdyssey() {
    const chart = ['Em', 'Em', 'Em', 'C', 'G', 'D', 'Em', 'C', 'D', 'B', 'C', 'D', 'Em', 'B', 'Em', 'C', 'G', 'D', 'Em', 'Em'];
    const A = ['E5 - - - B4 - E5 - G5 - - - B5 - A5 -', 'G5 - - - - - - - E5 - - - C5 - E5 -',
      'D5 - - - G5 - - - B5 - - - A5 - G5 -', 'A5 - - - - - - - F#5 - - - D5 - - -',
      'E5 - - - B4 - E5 - G5 - - - B5 - - -', 'C6 - - - G5 - A5 - G5 - - - E5 - - -',
      'F#5 - - - A5 - - - D6 - - - A5 - - -', 'B5 - - - - - - - D#5 - - - F#5 - - -'];
    const Bm = ['E5 - G5 - C6 - - - E5 - G5 - C6 - - -', 'F#5 - A5 - D6 - - - F#5 - A5 - D6 - - -',
      'G5 - B5 - E6 - - - D6 - - - B5 - - -', 'B5 - - - A5 - - - F#5 - - - D#5 - - -'];
    const a1 = melody(A, 2), b1 = melody(Bm, 10), a2 = melody(A.slice(0, 4), 14), fin = melody(['E5 - - - - - - - - - - - - - - -'], 18);
    const call = melody(['E5 - - - - - - - B4 - - - E5 - - -', 'G5 - - - - - - - E5 - - - B4 - - -'], 0);
    const tune = [...a1, ...b1, ...a2, ...fin];
    const hitAt = [[0, 0], [10, 0], [14, 0], [18, 0]];
    return {
      name: '척추 대모험', en: 'Spine Odyssey', bpm: 128, bars: 20, echoWet: 0.14, drive: 1.15, drumGain: 1.2,
      reverb: { time: 2.4, wet: 0.28, damp: 4200 }, drumRev: REV,
      game: { first: 2 * 16, last: 18 * 16 }, tune,
      ch: {
        lead: { wave: 'p0.25', vol: 0.2, pan: -0.05, echo: 0.12, rev: 0.22, vib: { depth: 12, rate: 5.6, delay: 0.16 }, notes: [...a1, ...b1, ...tr(a2, 12), ...fin] },
        lead2: { wave: 'p0.5', vol: 0.07, pan: 0.25, rev: 0.2, lp: 3000, notes: a2 },
        horn: brass([...tr(call, -12), ...tr(b1, -12), ...tr(a2, -12), ...tr(fin, -12)], { vol: 0.1 }),
        choir: choir([...stabs(chart, 0, 2, [[0, 16]], 55, 16, 0.6), ...stabs(chart, 2, 10, [[0, 16]], 55, 16, 0.5), ...stabs(chart, 10, 19, [[0, 16]], 55)]),
        str: strings([...arps(chart, 2, 10, 59, [0, 1, 2, 1], 2, 1, 0.8), ...arps(chart, 10, 18, 59, [0, 1, 2, 3, 2, 1, 2, 3], 1, 1)]),
        bell: { wave: 'fm', fm: { ratio: 3.5, i0: 2.2, i1: 0.1, time: 0.5 }, vol: 0.035, pan: 0.45, rev: 0.4, echo: 0.15, env: { a: 0.002, d: 0.5, s: 0.0, r: 0.3 }, gate: 1,
          notes: arps(chart, 14, 18, 76, [0, 1, 2, 3], 4, 3) },
        hit: hits([...at(chart, hitAt, 55), ...roots(chart, hitAt, 40)]),
        bass: { wave: 'p0.5', vol: 0.11, lp: 950, gate: 0.8, env: { a: 0.002, d: 0.08, s: 0.8, r: 0.03 },
          notes: [...line(chart, 'R - - - - - - - - - - - - - - -', 0, 2, 40), ...line(chart, 'R - R - O - R - R - R - O - R -', 2, 18, 40), ...line(chart, 'R - - - - - - - - - - - - - - -', 18, 19, 40)] },
        sub: { wave: 'sine', vol: 0.085, gate: 0.85, notes: [...line(chart, 'R - - - R - - - R - - - R - - -', 2, 18, 28), ...line(chart, 'R - - - - - - - - - - - - - - -', 18, 19, 28)] },
      },
      drums: [
        ...drums(0, 1, { boom: 'X...............', T: '....x...x...X...' }),
        ...drums(1, 2, { T: 'X...X...X...X...', T1: '........X.X.....', T2: '............X.X.', T3: '..............XX', SB: '............X...' }),
        ...drums(2, 10, (b) => ({ K: 'X.....X.X.......', SB: '....X.......X...', h: 'x.x.x.x.x.x.x.x.', ...(b === 9 ? { ...FILL, h: 'x.x.x.x.........' } : {}) })),
        ...drums(10, 14, (b) => ({ K: 'X...X...X...X...', SB: b === 13 ? 'x.x.x.x.xxxxXXXX' : '....X.......X...', T: b === 13 ? '' : '..x...x...x...x.', h: b < 12 ? 'x.x.x.x.x.x.x.x.' : '' })),
        ...drums(14, 18, (b) => ({ K: 'X.X...X.X.X...X.', kd: '.g.g.g.g.g.g.g.g', SB: '....X.......X...', r: 'x.x.x.x.x.x.x.x.', ...(b === 17 ? { ...FILL, r: 'x.x.x.x.........' } : {}) })),
        ...drums(18, 19, { K: 'X...............', SB: 'X...............', boom: 'X...............', T: 'X...............' }),
        ...crashes([0, 2, 6, 10, 14, 16, 18]),
        { step: 12 * 16, k: 'up', len: 32, v: 1 }, { step: 14 * 16, k: 'boom', v: 0.8 },
      ].filter((d) => d.k !== undefined),
    };
  }

  // ================================================================ E4. 뇌로 가는 길 (Road to the Brain): B minor, 140 BPM (orbit)
  // the last climb: a dotted, pushing tune on a saw lead, organ-like chords, a rising bridge on the brass, the theme
  // again with the choir and double kicks
  function roadToBrain() {
    const chart = ['Bm', 'Bm F#', 'Bm', 'G', 'D', 'A', 'Bm', 'G', 'Em', 'F#', 'G', 'A', 'F#', 'F#', 'Bm', 'G', 'D', 'A', 'Bm', 'Bm'];
    const A = ['B4 - - D5 - - F#5 - - - - - E5 - D5 -', 'D5 - - - - - - - B4 - - - G4 - B4 -',
      'A4 - - D5 - - F#5 - - - - - A5 - F#5 -', 'E5 - - - - - - - C#5 - - - A4 - - -',
      'B4 - - D5 - - F#5 - - - - - B5 - A5 -', 'G5 - - - D5 - - - B4 - - - D5 - G5 -',
      'E5 - - G5 - - B5 - - - - - G5 - E5 -', 'F#5 - - - - - - - A#4 - - - C#5 - - -'];
    const Bm = ['D5 - G5 - B5 - D6 - - - B5 - G5 - - -', 'E5 - A5 - C#6 - E6 - - - C#6 - A5 - - -',
      'C#5 - F#5 - A#5 - C#6 - - - A#5 - F#5 - - -', 'F#5 - - - - - - - C#5 - - - A#4 - - -'];
    const a1 = melody(A, 2), b1 = melody(Bm, 10), a2 = melody(A.slice(0, 4), 14), fin = melody(['B5 - - - - - - - - - - - - - - -'], 18);
    const call = melody(['B4 - - - - - - - F#5 - - - - - - -', 'D5 - - - - - - - C#5 - - - - - - -'], 0);
    const tune = [...a1, ...b1, ...a2, ...fin];
    const hitAt = [[0, 0], [10, 0], [14, 0], [18, 0]];
    return {
      name: '뇌로 가는 길', en: 'Road to the Brain', bpm: 140, bars: 20, echoWet: 0.14, drive: 1.15, drumGain: 1.2,
      reverb: { time: 2.6, wet: 0.3, damp: 4000 }, drumRev: REV,
      game: { first: 2 * 16, last: 18 * 16 }, tune,
      ch: {
        lead: { wave: 'saw', vol: 0.2, pan: -0.05, lp: 3200, echo: 0.12, rev: 0.25, vib: { depth: 12, rate: 5.4, delay: 0.16 }, env: { a: 0.005, d: 0.2, s: 0.75, r: 0.07 },
          notes: [...a1, ...b1, ...a2, ...fin] },
        lead8: { wave: 'p0.25', vol: 0.07, pan: 0.25, rev: 0.2, notes: tr([...a2, ...fin], 12) },
        horn: brass([...tr(call, -12), ...tr(b1, -12), ...tr(a2, -12)], { vol: 0.13 }),
        organ: { wave: 'p0.5', vol: 0.03, pan: -0.3, lp: 2400, rev: 0.35, gate: 1, env: { a: 0.01, d: 0.2, s: 0.8, r: 0.1 },
          notes: [...stabs(chart, 2, 10, [[0, 6], [6, 2], [8, 6], [14, 2]], 59), ...stabs(chart, 14, 18, [[0, 6], [6, 2], [8, 6], [14, 2]], 59)] },
        choir: choir([...stabs(chart, 0, 2, [[0, 8], [8, 8]], 54, 8, 0.6), ...stabs(chart, 10, 19, [[0, 16]], 54)]),
        str: strings([...arps(chart, 10, 18, 66, [0, 1, 2, 3], 1, 1, 0.9)], { pan: -0.35 }),
        hit: hits([...at(chart, hitAt, 54), ...roots(chart, hitAt, 35)]),
        bass: { wave: 'fm', fm: { ratio: 1, i0: 2.2, i1: 0.6, time: 0.12 }, vol: 0.17, gate: 0.8, env: { a: 0.003, d: 0.1, s: 0.8, r: 0.03 },
          notes: [...line(chart, 'R - - - - - - - - - - - - - - -', 0, 2, 35), ...line(chart, 'R - - R - - R - R - R - R - R -', 2, 18, 35), ...line(chart, 'R - - - - - - - - - - - - - - -', 18, 19, 35)] },
        sub: { wave: 'sine', vol: 0.08, gate: 0.85, notes: [...line(chart, 'R - - - R - - - R - - - R - - -', 2, 18, 23), ...line(chart, 'R - - - - - - - - - - - - - - -', 18, 19, 23)] },
      },
      drums: [
        ...drums(0, 1, { boom: 'X...............', T: '....x...x...X...' }),
        ...drums(1, 2, { T: 'X...X...X...X...', T1: '........X.X.....', T2: '............X.X.', T3: '..............XX' }),
        ...drums(2, 10, (b) => ({ K: 'X..X..X...X.....', SB: '....X.......X...', h: 'x.x.x.x.x.x.x.x.', T: '..............x.', ...(b === 9 ? { ...FILL, h: 'x.x.x.x.........', T: '' } : {}) })),
        ...drums(10, 14, (b) => ({ K: 'X...X...X...X...', T: b === 13 ? 'X.X.X.X.X.X.X.X.' : '..x...x...x...x.', SB: b === 13 ? '........xxxxXXXX' : '....X.......X...', h: b < 12 ? 'x.x.x.x.x.x.x.x.' : '' })),
        ...drums(14, 18, (b) => ({ K: 'X..X..X...X.....', kd: '.g.g.g.g.g.g.g.g', SB: '....X.......X...', r: 'x.x.x.x.x.x.x.x.', ...(b === 17 ? { ...FILL, r: 'x.x.x.x.........' } : {}) })),
        ...drums(18, 19, { K: 'X...............', SB: 'X...............', boom: 'X...............', T: 'X...............' }),
        ...crashes([0, 2, 6, 10, 14, 16, 18]),
        { step: 12 * 16, k: 'up', len: 32, v: 1 }, { step: 14 * 16, k: 'boom', v: 0.8 },
      ],
    };
  }

  return { rh: [leukocyteCrusade, heartDrums], orb: [spineOdyssey, roadToBrain] };
})();
