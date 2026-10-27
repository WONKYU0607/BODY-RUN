// The music of the two mini-games added in v40 (v42):
//  * the germ game (spleen), '세균 소탕 작전' (Germ Smash): a cartoon chase that gets harder with the game. 150 BPM,
//    a bar = 1.6 s, laid on the game's 3.2 s intro and 45 s of play: 2 bars of intro (a stab, a drum roll up), then
//    A (6 bars, the play's 0-9.6 s: a bouncy pulse tune, oom-pah bass), B (6 bars, to 19.2 s: higher, cowbell, busier
//    kick), C (8 bars, to 32 s: driving eighths, brass stabs, open hats, claps), D (8 bars, to 44.8 s: up a whole step,
//    four on the floor, the tune doubled in harmony over running arpeggios, a riser), then the end hit and a short ring.
//    Played once from the intro (not looped); the game keeps it in time with its own clock.
//  * the memory game (hippocampus), '시냅스 사색' (Synapse Reverie): calm and thoughtful under the neurons' bells. 90 BPM,
//    16 bars = 42.7 s, looped (rendered three times round, the middle one is the file). In C, on chords that hold the
//    bells' notes (C D E G A); everything kept low (a soft electric piano below C4, a pad, a sine bass), so the bells
//    (C5..A5) stand clear; a heartbeat-like soft kick, a shaker, bubbles.
window.SongsMG = (() => {
  'use strict';
  const L = SongLib, { melody, line, arps, stabs, drums } = L;

  function germSmash() {
    const chart = ['C', 'G7',
      'C', 'Am', 'F', 'G7', 'C', 'G7',
      'F', 'C', 'Dm', 'G7', 'Em A7', 'Dm G7',
      'Am', 'F', 'C', 'G', 'Am', 'F', 'G', 'G7',
      'D', 'Bm', 'G', 'A', 'D', 'Bm', 'G', 'A7',
      'D', 'D'];
    const BARS = chart.length;                                // 32
    const A = ['C5 . E5 . G5 . E5 . C6 - . . G5 . E5 .', 'A5 . G5 . E5 . C5 . A4 - . . C5 . E5 .',
      'F5 . A5 . C6 . A5 . F5 . G5 . A5 . . .', 'G5 . F5 . D5 . B4 . G4 - - - . . . .'];
    const leadNotes = [
      ...melody(['. . . . . . . . . . . . . . . .', '. . . . . . . . . . G4 . A4 . B4 .'], 0),
      ...melody([...A, 'E5 . G5 . C6 . . . B5 . A5 . G5 . . .', 'F5 . D5 . B4 . D5 . G5 - - - . . . .'], 2),
      ...melody(['A5 - . C6 . A5 . F5 - . G5 . A5 . . .', 'G5 - . E5 . C5 . E5 - . G5 . C6 . . .',
        'D6 - . C6 . A5 . F5 - . A5 . D6 . . .', 'B5 . C6 . D6 . B5 . G5 - - - . . . .',
        'E6 . D6 . B5 . G5 . A5 . C#6 . E6 . . .', 'F6 - . D6 . A5 . . G5 . B5 . D6 . . .'], 8),
      ...melody(['A5 . A5 . C6 . A5 . E6 . D6 . C6 . A5 .', 'F5 . F5 . A5 . F5 . C6 . A5 . G5 . F5 .',
        'G5 . G5 . C6 . G5 . E6 . D6 . C6 . G5 .', 'B5 . A5 . G5 . D5 . G5 - . . . . . .',
        'A5 . A5 . C6 . A5 . E6 . D6 . C6 . E6 .', 'F6 . E6 . D6 . C6 . A5 . C6 . F6 . . .',
        'G6 - . . D6 . . . B5 . . . G5 . . .', 'F5 . G5 . A5 . B5 . D6 . F6 . G6 . . .'], 14),
    ];
    const dTune = L.tr(melody([...A, ...A.slice(0, 3), 'G5 . A5 . B5 . C6 . D6 . E6 . F6 . G6 .'], 22), 2);   // A again, a whole step up
    const endTune = melody(['A5 . D6 - - - - - - - - - . . . .', '. . . . . . . . . . . . . . . .'], 30);
    const lead = [...leadNotes, ...dTune, ...endTune];
    const harm = L.harmony([...leadNotes.filter((n) => n.step >= 14 * 16), ...dTune], chart);       // a second voice from C on
    const bubbles = [];
    for (let b = 2; b < 14; b += 2) bubbles.push({ step: b * 16 + [7, 13, 5, 11][(b >> 1) % 4], k: 'bub', v: 0.55, f: [560, 700, 820, 640][(b >> 1) % 4], pan: (b % 4 ? 0.45 : -0.45), echo: 0.2 });
    return {
      name: '세균 소탕 작전', en: 'Germ Smash', bpm: 150, bars: BARS, echoWet: 0.16, drumGain: 0.85, lp: 13000,
      reverb: { time: 1.8, wet: 0.2, damp: 5000 }, drumRev: { s: 0.12, cl: 0.2, c: 0.25, cb: 0.15, bub: 0.3 },
      ch: {
        lead: { wave: 'p0.25', vol: 0.072, pan: -0.06, echo: 0.1, rev: 0.2, gate: 0.85, env: { a: 0.002, d: 0.08, s: 0.75, r: 0.04 },
          vib: { depth: 10, rate: 6.2, delay: 0.12 }, notes: lead },
        harm: { wave: 'p0.125', vol: 0.034, pan: 0.22, echo: 0.12, rev: 0.2, gate: 0.85, env: { a: 0.002, d: 0.08, s: 0.7, r: 0.04 }, notes: harm },
        bass: { wave: 'tri', vol: 0.21, lp: 1600, gate: 0.7, env: { a: 0.002, d: 0.08, s: 0.8, r: 0.03 },
          notes: [
            ...line(chart, 'R - - - . . . . . . . . . . . .', 0, 1, 36), ...line(chart, '. . . . . . . . R . R . 5 . O .', 1, 2, 36),
            ...line(chart, 'R . . . 5 . . . R . . . 5 . O .', 2, 8, 36),
            ...line(chart, 'R . . R 5 . . . R . . R O . 5 .', 8, 14, 36),
            ...line(chart, 'R . R . O . R . R . R . O . 5 .', 14, 22, 36),
            ...line(chart, 'R . O . R . O . R . O . 5 . O .', 22, 30, 36),
            ...line(chart, 'R - - - - - - - . . . . . . . .', 30, 31, 36)] },
        chords: { wave: 'p0.5', vol: 0.022, pan: 0.15, lp: 3200, gate: 0.6, env: { a: 0.002, d: 0.06, s: 0.5, r: 0.03 },
          notes: [...stabs(chart, 0, 1, [0, 6], 60, 2), ...stabs(chart, 2, 8, [4, 12], 60, 2), ...stabs(chart, 8, 14, [2, 6, 10, 14], 60, 1)] },
        brass: { wave: 'fm', fm: { ratio: 1, i0: 3.2, i1: 1.3, time: 0.16 }, vol: 0.05, pan: -0.18, rev: 0.25, gate: 0.9,
          env: { a: 0.012, d: 0.16, s: 0.6, r: 0.08 },
          notes: [...stabs(chart, 14, 22, [[0, 3], [6, 2], [10, 2], [14, 2]], 55), ...stabs(chart, 22, 30, [[0, 3], [3, 2], [6, 2], [8, 3], [11, 2], [14, 2]], 57),
            ...stabs(chart, 30, 31, [[0, 12]], 57)] },
        arp: { wave: 'p0.25', vol: 0.02, pan: 0.38, echo: 0.2, gate: 0.6, env: { a: 0.001, d: 0.06, s: 0.3, r: 0.03 },
          notes: arps(chart, 22, 30, 74, [0, 1, 2, 3, 2, 1], 1, 1) },
      },
      drums: [
        { step: 0, k: 'c', v: 0.9 }, { step: 0, k: 'K', v: 1 }, { step: 16, k: 'up', v: 0.9, len: 16 },
        ...drums(0, 2, (b) => (b === 0 ? { s: '............x...' } : { s: 'g.g.g.g.x.x.xxxx' })),
        { step: 32, k: 'c', v: 0.7 },
        ...drums(2, 8, (b) => ({ k: 'x.......x.......', s: b === 7 ? '....x.......xxxx' : '....x.......x...', h: 'g.x.g.x.g.x.g.x.' })),
        { step: 8 * 16, k: 'c', v: 0.6 },
        ...drums(8, 14, (b) => ({ k: 'x.....x.x.......', s: '....x.......x...', h: 'x.x.x.x.x.x.x.x.', cb: '..x.......x.....',
          t1: b === 13 ? '........x.......' : '', t2: b === 13 ? '..........x.x...' : '', t3: b === 13 ? '..............xx' : '' })),
        { step: 14 * 16, k: 'c', v: 0.8 },
        ...drums(14, 22, (b) => ({ k: 'x.....x.x.....x.', s: b === 21 ? 'x.x.x.x.xxxxxxxx' : '....x.......x...', h: 'xgxgo.xgxgxgo.xg', cl: '....x.......x...' })),
        { step: 21 * 16, k: 'up', v: 0.8, len: 16 },
        { step: 22 * 16, k: 'c', v: 1 }, { step: 22 * 16, k: 'K', v: 0.9 },
        ...drums(22, 30, (b) => ({ k: 'x...x...x...x...', s: b === 29 ? '....x...xxxxxxxx' : '....x.......x...', h: 'gxgogxgogxgogxgo', cl: '....x.......x...' })),
        { step: 28 * 16, k: 'up', v: 1, len: 32 },
        { step: 30 * 16, k: 'c', v: 1 }, { step: 30 * 16, k: 'boom', v: 0.9 }, { step: 30 * 16, k: 'K', v: 1 }, { step: 30 * 16, k: 'S', v: 0.9 },
        ...bubbles,
      ],
    };
  }

  function synapseReverie(rounds = 3) {
    const BARS = 16;
    const chart = ['Cmaj7', 'Am7', 'Fmaj7', 'G', 'Cmaj7', 'Em7', 'Fmaj7', 'Gsus4',
      'Am7', 'Em7', 'Fmaj7', 'Cmaj7', 'Am7', 'Fmaj7', 'Gsus4', 'G'];
    const bubbles = [];
    for (let b = 0; b < BARS; b++) if (b % 2) bubbles.push({ step: b * 16 + [9, 5, 13, 7][(b >> 1) % 4], k: 'bub', v: 0.45, f: [380, 460, 420, 520][(b >> 1) % 4], pan: (b % 4 === 1 ? -0.5 : 0.5), echo: 0.3 });
    const one = {
      ch: {
        keys: { wave: 'fm', fm: { ratio: 1, i0: 1.3, i1: 0.18, time: 0.7 }, vol: 0.06, pan: -0.12, echo: 0.28, rev: 0.5, gate: 1,
          env: { a: 0.003, d: 0.9, s: 0.18, r: 0.45 }, notes: arps(chart, 0, BARS, 48, [0, 2, 3, 1, 2, 3, 4, 2], 2, 2) },
        pad: { wave: 'ssaw', spread: 9, vol: 0.011, pan: 0.12, lp: 1000, rev: 0.55, gate: 1, env: { a: 0.9, d: 0.5, s: 0.9, r: 1.0 },
          vib: { depth: 4, rate: 0.3, delay: 0 }, notes: stabs(chart, 0, BARS, [[0, 16]], 52) },
        bass: { wave: 'sine', vol: 0.12, gate: 0.95, env: { a: 0.02, d: 0.3, s: 0.8, r: 0.3 }, notes: line(chart, 'R - - - - - - - 5 - - - - - - -', 0, BARS, 36) },
      },
      drums: [
        ...drums(0, BARS, (b) => ({ k: 'x.....g.........', x: 'g.g.g.g.g.g.g.g.', ka: b % 2 ? '....g.......g...' : '' })),
        ...bubbles,
      ],
    };
    const ch = {};
    for (const [k, c] of Object.entries(one.ch)) { ch[k] = { ...c, notes: [] }; for (let r = 0; r < rounds; r++) ch[k].notes.push(...L.shift(c.notes, r * BARS)); }
    const drm = []; for (let r = 0; r < rounds; r++) drm.push(...one.drums.map((d) => ({ ...d, step: d.step + r * BARS * 16 })));
    return { name: '시냅스 사색', en: 'Synapse Reverie', bpm: 90, bars: BARS * rounds, loopBars: BARS, echoWet: 0.22, drumGain: 0.7, lp: 9000,
      reverb: { time: 3.0, wet: 0.34, damp: 3800 }, drumRev: { k: 0.15, ka: 0.3, x: 0.2, bub: 0.35 }, ch, drums: drm };
  }
  return { germSmash, synapseReverie };
})();
