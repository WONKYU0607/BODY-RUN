// Body Run sounds: the effects and the ambience are synthesized with the Web Audio API; the mini-games' songs are
// files (made with the chip engine in chip/, see stages.js):
//  - effects: jump (1st/2nd/3rd), slide, items, heal, hit, game over, buttons, the rhythm and orbit stages' hits
//  - the running music: a file that loops (light, as if under water), turned down for the mini-games
//  - the songs of the rhythm and orbit stages: fetched early, decoded once the sound is on, played from the buffer
//    (a song can be started at any point of it, which the orbit stage uses to go back two beats after a miss)
// The voices take any audio context, so a test can render them offline and measure them.
window.BodySound = (() => {
  'use strict';
  let ctx = null, master = null, buses = null, noiseBuf = null, outNode = null;
  // the settings' sound switches: the effects, and the music (the running music and the mini-games' songs), each kept
  // in this browser (the old one switch for everything, if it was on, turns both off)
  const mute = { sfx: false, music: false }, mutes = {};
  try {
    const old = localStorage.getItem('bodyrun.mute') === '1';
    for (const k of ['sfx', 'music']) { const v = localStorage.getItem('bodyrun.mute.' + k); mute[k] = v === null ? old : v === '1'; }
  } catch (e) { /* storage off */ }

  // ---------------------------------------------------------------- building blocks
  function noise(c) {
    if (c === ctx && noiseBuf) return noiseBuf;
    const b = c.createBuffer(1, Math.floor(c.sampleRate * 1.0), c.sampleRate);
    const d = b.getChannelData(0);
    let s = 7;                                          // fixed seed: the same noise every time
    for (let i = 0; i < d.length; i++) { s = (s * 16807) % 2147483647; d[i] = (s / 2147483647) * 2 - 1; }
    if (c === ctx) noiseBuf = b;
    return b;
  }
  function gainEnv(c, out, t, peak, a, d, curve = 'exp') {
    const g = c.createGain();
    g.gain.setValueAtTime(0.0001, t);
    g.gain.linearRampToValueAtTime(peak, t + a);
    if (curve === 'exp') g.gain.exponentialRampToValueAtTime(0.0001, t + a + d);
    else g.gain.linearRampToValueAtTime(0.0001, t + a + d);
    g.connect(out);
    return g;
  }
  function tone(c, out, t, type, f0, f1, dur, peak, a = 0.004, glide = null) {
    const o = c.createOscillator(); o.type = type;
    o.frequency.setValueAtTime(f0, t);
    if (f1 && f1 !== f0) o.frequency.exponentialRampToValueAtTime(f1, t + (glide || dur));
    const g = gainEnv(c, out, t, peak, a, dur);
    o.connect(g); o.start(t); o.stop(t + a + dur + 0.05);
    return o;
  }
  function burst(c, out, t, filter, f0, f1, q, dur, peak, a = 0.002) {
    const s = c.createBufferSource(); s.buffer = noise(c);
    const fl = c.createBiquadFilter(); fl.type = filter; fl.Q.value = q;
    fl.frequency.setValueAtTime(f0, t);
    if (f1 && f1 !== f0) fl.frequency.exponentialRampToValueAtTime(f1, t + dur);
    const g = gainEnv(c, out, t, peak, a, dur);
    s.connect(fl); fl.connect(g);
    s.start(t, Math.random() * 0.5); s.stop(t + a + dur + 0.05);
  }
  const NOTE = (n) => 440 * Math.pow(2, (n - 69) / 12);  // MIDI note number -> Hz
  // a wooden bat's crack (k: how hard): click, ring, thump
  function crack(c, out, t, k) {
    burst(c, out, t, 'highpass', 3600, 3600, 0.8, 0.012, 0.55 * k, 0.0005);
    burst(c, out, t, 'bandpass', 1850, 1700, 6, 0.05, 0.6 * k, 0.0008);
    tone(c, out, t, 'sine', 1080, 900, 0.04, 0.26 * k, 0.0008, 0.035);
    tone(c, out, t, 'sine', 2350, 2200, 0.025, 0.12 * k, 0.0008, 0.02);
    tone(c, out, t, 'sine', 170, 85, 0.08, 0.36 * k, 0.001, 0.07);
  }
  // under water: a lowpass the sound goes through (muffled), and a bubble (a sine whose pitch flies up as it forms)
  function water(c, out, f) { const lp = c.createBiquadFilter(); lp.type = 'lowpass'; lp.frequency.value = f; lp.Q.value = 0.7; lp.connect(out); return lp; }
  function bubble(c, out, t, f, peak) { tone(c, out, t, 'sine', f, f * 2.3, 0.055, peak, 0.003, 0.04); }
  function bloop(c, out, t, f, up, peak, bubbles) {
    const w = water(c, out, 1900);
    tone(c, w, t, 'sine', f, f * up, 0.17, peak, 0.004, 0.08);                 // the bloop
    tone(c, w, t, 'triangle', f * 2, f * 2 * up, 0.07, peak * 0.25, 0.004, 0.06);   // its edge
    for (const [dt, bf] of bubbles) bubble(c, out, t + dt, bf, peak * 0.2);
  }

  // ---------------------------------------------------------------- effects
  const SFX = {
    // jumping and sliding, as if under water: a jump is a 'bloop' (a bubble's note flying up, muffled) with little
    // bubbles after it, higher for the second and third; a slide is a swoosh of water going down, a soft thump, bubbles
    jump1: (c, o, t) => bloop(c, o, t, 210, 2.4, 0.28, [[0.05, 720], [0.1, 980]]),
    jump2: (c, o, t) => bloop(c, o, t, 290, 2.3, 0.25, [[0.045, 880], [0.085, 1180], [0.13, 1020]]),
    jump3: (c, o, t) => bloop(c, o, t, 380, 2.2, 0.23, [[0.04, 1040], [0.075, 1400], [0.11, 1240], [0.15, 1640]]),
    slide: (c, o, t) => {
      const w = water(c, o, 1500);
      burst(c, w, t, 'lowpass', 1300, 240, 0.9, 0.3, 0.3, 0.025);
      tone(c, w, t, 'sine', 150, 85, 0.16, 0.14, 0.006, 0.14);
      for (const [dt, f, pk] of [[0.06, 560, 0.06], [0.12, 700, 0.05], [0.19, 640, 0.04]]) bubble(c, o, t + dt, f, pk);
    },
    coin: (c, o, t) => { tone(c, o, t, 'triangle', NOTE(88), null, 0.06, 0.2); tone(c, o, t + 0.055, 'triangle', NOTE(93), null, 0.14, 0.2); },
    special: (c, o, t) => { [84, 88, 91, 96].forEach((n, i) => tone(c, o, t + i * 0.045, 'triangle', NOTE(n), null, 0.12, 0.17)); },
    atp: (c, o, t) => {
      [81, 85, 88, 93, 97].forEach((n, i) => tone(c, o, t + i * 0.04, 'triangle', NOTE(n), null, 0.12, 0.15));
      tone(c, o, t + 0.2, 'sine', NOTE(100), NOTE(100), 0.35, 0.08, 0.01);
    },
    heal: (c, o, t) => { tone(c, o, t, 'sine', 523, 784, 0.32, 0.24, 0.01, 0.22); tone(c, o, t + 0.12, 'sine', 1046, 1568, 0.26, 0.08, 0.01, 0.2); },
    hit: (c, o, t) => {
      tone(c, o, t, 'sine', 170, 45, 0.24, 0.62, 0.003, 0.2);
      burst(c, o, t, 'lowpass', 1100, 300, 0.7, 0.14, 0.32);
      tone(c, o, t, 'square', 320, 150, 0.1, 0.06, 0.003, 0.1);
    },
    over: (c, o, t) => { [67, 64, 60, 55].forEach((n, i) => tone(c, o, t + i * 0.2, 'triangle', NOTE(n), null, 0.3, 0.22, 0.01)); },
    ui: (c, o, t) => tone(c, o, t, 'triangle', 880, null, 0.05, 0.14),
    // the rhythm stage
    perfect: (c, o, t) => { burst(c, o, t, 'bandpass', 2600, 2600, 1.1, 0.08, 0.42); tone(c, o, t, 'sine', 1320, 1320, 0.06, 0.16); },
    good: (c, o, t) => { burst(c, o, t, 'bandpass', 1500, 1500, 1.0, 0.08, 0.32); tone(c, o, t, 'sine', 880, 880, 0.05, 0.1); },
    miss: (c, o, t) => { tone(c, o, t, 'sine', 120, 70, 0.16, 0.3, 0.004, 0.14); burst(c, o, t, 'lowpass', 420, 300, 0.7, 0.1, 0.18); },
    tick: (c, o, t) => tone(c, o, t, 'triangle', 1600, null, 0.03, 0.09),
    spinDone: (c, o, t) => { [76, 79, 83, 88].forEach((n) => tone(c, o, t, 'triangle', NOTE(n), null, 0.5, 0.09, 0.01)); },
    // the orbit stage: landing on a tile, the end (a miss sounds like the rhythm stage's)
    orbHit: (c, o, t) => { burst(c, o, t, 'bandpass', 3400, 3400, 1.6, 0.045, 0.34); tone(c, o, t, 'sine', 1760, 1760, 0.035, 0.1); },
    orbClear: (c, o, t) => { [72, 76, 79, 84, 88].forEach((n, i) => tone(c, o, t + i * 0.06, 'triangle', NOTE(n), null, 0.4, 0.13, 0.006)); },
    // baseball: the throw (a whoosh), the swing (a quicker one), the ball into the mitt (a leathery pop), bat on ball (a
    // wooden knock), a home run (a crack, a deep thump, a little fanfare and the crowd's roar rising), out (three going down)
    bbPitch: (c, o, t) => burst(c, o, t, 'bandpass', 520, 1500, 1.3, 0.3, 0.5, 0.03),
    bbSwing: (c, o, t) => { burst(c, o, t, 'bandpass', 600, 2300, 1.5, 0.17, 0.55, 0.012); tone(c, o, t, 'sine', 240, 140, 0.12, 0.05, 0.01, 0.12); },
    bbMitt: (c, o, t) => { burst(c, o, t, 'lowpass', 1100, 320, 0.8, 0.07, 0.42, 0.001); tone(c, o, t, 'sine', 160, 90, 0.09, 0.3, 0.002, 0.08); },
    // bat on ball: a wooden crack - a sharp click, the wood ringing (a couple of resonances), a low thump
    bbHit: (c, o, t) => { crack(c, o, t, 0.8); burst(c, o, t + 0.12, 'bandpass', 700, 900, 0.7, 0.55, 0.05, 0.18); },   // a foul: the crowd's "ooh"
    bbHR: (c, o, t) => {
      crack(c, o, t, 1);
      const w = water(c, o, 2600); crack(c, w, t + 0.13, 0.22);                                        // its echo round the ballpark
      [72, 76, 79, 84, 88].forEach((n, i) => tone(c, o, t + 0.28 + i * 0.075, 'triangle', NOTE(n), null, i === 4 ? 0.7 : 0.3, 0.12, 0.006));
      burst(c, o, t + 0.08, 'bandpass', 800, 1400, 0.6, 1.8, 0.16, 0.35);                               // the crowd's roar, rising
      burst(c, o, t + 0.1, 'bandpass', 2200, 2600, 0.8, 1.5, 0.05, 0.4);
    },
    // into the toilet (the end of the body): a deep plunk, the water thrown up, then bubbles under the surface
    splash: (c, o, t) => {
      tone(c, o, t, 'sine', 190, 68, 0.2, 0.5, 0.002, 0.16);
      tone(c, o, t + 0.005, 'sine', 460, 1350, 0.06, 0.22, 0.002, 0.05);
      burst(c, o, t, 'bandpass', 1300, 520, 0.9, 0.38, 0.42, 0.004);
      burst(c, o, t + 0.03, 'highpass', 4200, 3000, 0.7, 0.28, 0.16, 0.01);
      const w = water(c, o, 1600);
      [[0.16, 640], [0.24, 820], [0.31, 560], [0.4, 980], [0.5, 700], [0.62, 880]].forEach(([d, f]) => bubble(c, w, t + d, f, 0.1));
    },
    splat: (c, o, t) => {                                                 // smack into the stool: a soft, wet thud
      tone(c, o, t, 'sine', 150, 48, 0.2, 0.6, 0.002, 0.17);
      burst(c, o, t, 'lowpass', 900, 260, 0.9, 0.14, 0.5, 0.002);
      burst(c, o, t + 0.012, 'bandpass', 700, 380, 2.2, 0.12, 0.22, 0.004);
    },
    bbOut: (c, o, t) => { [67, 63, 60].forEach((n, i) => tone(c, o, t + i * 0.16, 'triangle', NOTE(n), null, 0.24, 0.18, 0.01)); },
    // the germ game (v40): a germ popping out (a small wet pop), a bad one whacked (a soft punchy thump with a squelch
    // and a bright tick on top), the good one tapped by mistake (a sad falling boing)
    wmUp: (c, o, t) => { const w = water(c, o, 2400); tone(c, w, t, 'sine', 330, 760, 0.07, 0.11, 0.003, 0.05); },
    wmHit: (c, o, t) => {
      tone(c, o, t, 'sine', 240, 70, 0.13, 0.55, 0.002, 0.11);
      burst(c, o, t, 'bandpass', 1900, 520, 1.6, 0.09, 0.38, 0.001);
      tone(c, o, t + 0.004, 'triangle', NOTE(91), null, 0.05, 0.08, 0.002);
    },
    wmOops: (c, o, t) => {
      tone(c, o, t, 'triangle', 620, 230, 0.32, 0.22, 0.004, 0.3);
      tone(c, o, t, 'square', 310, 115, 0.26, 0.05, 0.004, 0.24);
    },
    // the memory game (v40): each neuron its own bell (a pentatonic scale: C D E G A, so any order sounds fine), a round
    // right (the bells running up), wrong (two low buzzes)
    mem0: (c, o, t) => bell(c, o, t, 72), mem1: (c, o, t) => bell(c, o, t, 74), mem2: (c, o, t) => bell(c, o, t, 76),
    mem3: (c, o, t) => bell(c, o, t, 79), mem4: (c, o, t) => bell(c, o, t, 81),
    memOk: (c, o, t) => { [72, 76, 79, 84].forEach((n, i) => bell(c, o, t + i * 0.07, n, 0.6)); },
    memBad: (c, o, t) => { for (const d of [0, 0.16]) { tone(c, o, t + d, 'square', 150, 132, 0.12, 0.07, 0.004); tone(c, o, t + d, 'sine', 75, 70, 0.12, 0.25, 0.004); } },
    // the penalty shoot-out (v44): the referee's whistle (a trilling pea whistle), the kick (a leathery thump), a goal
    // (the net, the crowd's roar, a fanfare), a save (gloves on the ball, the crowd's 'ooh'), the post (a ringing clang),
    // wide or over (the crowd's 'aww')
    pkWhistle: (c, o, t) => { trill(c, o, t, 2950, 0.3, 0.16); burst(c, o, t, 'bandpass', 3000, 3000, 2.5, 0.3, 0.05, 0.01); },
    pkKick: (c, o, t) => {
      tone(c, o, t, 'sine', 150, 55, 0.11, 0.6, 0.001, 0.09);
      burst(c, o, t, 'lowpass', 2200, 380, 0.8, 0.06, 0.45, 0.0008);
      burst(c, o, t + 0.01, 'bandpass', 900, 2400, 1.2, 0.22, 0.12, 0.02);                      // the ball going off (a whoosh)
    },
    pkGoal: (c, o, t) => {
      burst(c, o, t, 'bandpass', 2400, 800, 1.1, 0.32, 0.4, 0.004);                             // into the net
      burst(c, o, t + 0.05, 'bandpass', 850, 1300, 0.6, 2.0, 0.2, 0.25);                         // the crowd's roar, rising and going on
      burst(c, o, t + 0.08, 'bandpass', 2300, 2800, 0.8, 1.7, 0.07, 0.3);
      [72, 76, 79, 84].forEach((n, i) => tone(c, o, t + 0.12 + i * 0.08, 'square', NOTE(n), null, 0.12, 0.06, 0.004));
      [72, 76, 79, 84].forEach((n) => tone(c, o, t + 0.46, 'triangle', NOTE(n), null, 0.8, 0.09, 0.01));
    },
    pkSave: (c, o, t) => {
      burst(c, o, t, 'lowpass', 1700, 360, 0.8, 0.09, 0.55, 0.0008);
      tone(c, o, t, 'sine', 210, 90, 0.1, 0.35, 0.001, 0.09);
      crowd(c, o, t + 0.1, 560, 760, 0.9, 0.11);
    },
    pkPost: (c, o, t) => {
      burst(c, o, t, 'highpass', 3000, 3000, 0.8, 0.015, 0.4, 0.0005);
      for (const [f, k, d] of [[612, 0.22, 0.9], [1188, 0.14, 0.7], [1977, 0.09, 0.5], [2906, 0.05, 0.35]]) tone(c, o, t, 'sine', f, f * 0.995, d, k, 0.001);
      crowd(c, o, t + 0.15, 520, 820, 1.0, 0.12);
    },
    pkMiss: (c, o, t) => crowd(c, o, t + 0.05, 820, 430, 1.0, 0.24),
    // the toilet jackpot (v44): the flush lever (a clunk, the water rushing), the reels going by (ticks), a reel
    // stopping (a thunk), a reach (a rising sweep, then a drum roll), two alike (a ding-ding), three (bells running up,
    // coins), the jackpot (a fanfare and a long fall of coins)
    slLever: (c, o, t) => {
      burst(c, o, t, 'bandpass', 1400, 1400, 3, 0.03, 0.3, 0.001);
      tone(c, o, t + 0.02, 'sine', 180, 90, 0.09, 0.35, 0.002, 0.08);
      const w = water(c, o, 1800); burst(c, w, t + 0.08, 'lowpass', 1600, 420, 0.8, 0.7, 0.28, 0.05);
      [[0.18, 620], [0.26, 840], [0.36, 700]].forEach(([d, f]) => bubble(c, w, t + d, f, 0.08));
    },
    slTick: (c, o, t) => tone(c, o, t, 'triangle', 2300, null, 0.012, 0.06, 0.001),
    slStop: (c, o, t) => { tone(c, o, t, 'sine', 320, 150, 0.07, 0.34, 0.001, 0.06); burst(c, o, t, 'bandpass', 1300, 900, 2, 0.04, 0.25, 0.0008); },
    slReach: (c, o, t) => { tone(c, o, t, 'sawtooth', 220, 880, 0.5, 0.08, 0.01, 0.5); tone(c, o, t, 'square', 330, 1320, 0.5, 0.05, 0.01, 0.5); },
    slDrum: (c, o, t) => { burst(c, o, t, 'bandpass', 1900, 1700, 0.8, 0.05, 0.16, 0.001); tone(c, o, t, 'sine', 190, 150, 0.04, 0.08, 0.001); },
    slSmall: (c, o, t) => { tone(c, o, t, 'triangle', NOTE(84), null, 0.1, 0.16); tone(c, o, t + 0.09, 'triangle', NOTE(88), null, 0.22, 0.16); },
    slWin: (c, o, t) => {
      [72, 76, 79, 84, 88, 91, 96].forEach((n, i) => tone(c, o, t + i * 0.05, 'square', NOTE(n), null, 0.1, 0.05, 0.003));
      [84, 88, 91].forEach((n) => tone(c, o, t + 0.38, 'triangle', NOTE(n), null, 0.7, 0.1, 0.01));
      coins(c, o, t + 0.1, 16, 0.9);
    },
    // (v52) the shell game: a lid sliding across the felt (a short scrape, a tick of iron), lifted (an iron clink),
    // set down (a soft clank), a win (the slot's), a loss (a sad 'wah wah wah')
    ybSlide: (c, o, t) => { burst(c, o, t, 'bandpass', 2600, 1300, 1.3, 0.085, 0.2, 0.004); tone(c, o, t + 0.06, 'triangle', 1900, null, 0.02, 0.05, 0.001); },
    ybLift: (c, o, t) => { tone(c, o, t, 'triangle', 1240, 1180, 0.16, 0.09, 0.001); tone(c, o, t, 'sine', 520, 380, 0.07, 0.2, 0.002, 0.06); burst(c, o, t, 'highpass', 3200, 3200, 0.8, 0.03, 0.12, 0.0008); },
    ybDown: (c, o, t) => { tone(c, o, t, 'sine', 210, 120, 0.09, 0.32, 0.001, 0.07); burst(c, o, t, 'bandpass', 1500, 900, 1.6, 0.05, 0.22, 0.0008); tone(c, o, t + 0.005, 'triangle', 980, null, 0.08, 0.05, 0.001); },
    ybWin: (c, o, t) => SFX.slWin(c, o, t),
    ybLose: (c, o, t) => {
      [67, 66, 65].forEach((n, i) => tone(c, o, t + i * 0.22, 'triangle', NOTE(n), NOTE(n) * 0.985, 0.19, 0.17, 0.01));
      tone(c, o, t + 0.66, 'triangle', NOTE(64), NOTE(61), 0.62, 0.17, 0.01, 0.6);
    },
    slJackpot: (c, o, t) => {
      for (let r = 0; r < 3; r++) [72, 76, 79, 84, 88, 91].forEach((n, i) => tone(c, o, t + r * 0.32 + i * 0.045, 'square', NOTE(n + r * 2), null, 0.09, 0.08, 0.003));
      [[0.98, [72, 76, 79, 84]], [1.3, [74, 77, 81, 86]], [1.62, [76, 79, 84, 88]]].forEach(([d, ch]) => ch.forEach((n) => tone(c, o, t + d, 'triangle', NOTE(n), null, d > 1.5 ? 1.4 : 0.3, 0.12, 0.008)));
      coins(c, o, t + 0.2, 60, 2.6);
      burst(c, o, t + 0.9, 'bandpass', 900, 1400, 0.6, 2.2, 0.12, 0.3);                           // and a cheer
    },
  };
  // a pea whistle: a high note trilling (its pitch shaken fast by a second oscillator)
  function trill(c, out, t, f, dur, peak) {
    const o = c.createOscillator(); o.type = 'sine'; o.frequency.value = f;
    const l = c.createOscillator(); l.type = 'square'; l.frequency.value = 26;
    const lg = c.createGain(); lg.gain.value = f * 0.06; l.connect(lg); lg.connect(o.frequency);
    const g = gainEnv(c, out, t, peak, 0.01, dur, 'lin');
    o.connect(g); o.start(t); l.start(t); o.stop(t + dur + 0.06); l.stop(t + dur + 0.06);
  }
  // a crowd's 'ooh' or 'aww': a band of noise sliding from f0 to f1
  function crowd(c, out, t, f0, f1, dur, peak) { burst(c, out, t, 'bandpass', f0, f1, 0.9, dur, peak, dur * 0.25); burst(c, out, t, 'bandpass', f0 * 2.1, f1 * 2.1, 1.2, dur * 0.9, peak * 0.35, dur * 0.25); }
  // coins falling: little bright chinks, n of them over dur seconds
  function coins(c, out, t, n, dur) {
    for (let i = 0; i < n; i++) { const d = Math.pow(i / n, 1.3) * dur, f = 2600 + Math.random() * 2200; tone(c, out, t + d, 'triangle', f, null, 0.05, 0.05, 0.001); tone(c, out, t + d + 0.002, 'sine', f * 1.5, null, 0.03, 0.025, 0.001); }
  }
  // a soft bell: the note, a quieter octave above and a faint inharmonic overtone, ringing out
  function bell(c, out, t, n, k = 1) {
    const f = NOTE(n);
    tone(c, out, t, 'sine', f, null, 0.7, 0.26 * k, 0.003);
    tone(c, out, t, 'triangle', f * 2, null, 0.35, 0.07 * k, 0.003);
    tone(c, out, t, 'sine', f * 2.76, null, 0.18, 0.04 * k, 0.002);
  }

  // ---------------------------------------------------------------- the live context and its buses
  function unlock() {
    try {
      if (!ctx) {
        const AC = window.AudioContext || window.webkitAudioContext;
        if (!AC) return null;
        ctx = new AC({ latencyHint: 'interactive' });
        master = ctx.createGain(); master.gain.value = 1;
        const comp = ctx.createDynamicsCompressor(); comp.threshold.value = -10; comp.ratio.value = 4; comp.attack.value = 0.003; comp.release.value = 0.15;
        master.connect(comp); comp.connect(ctx.destination); outNode = comp;
        buses = { sfx: ctx.createGain(), music: ctx.createGain(), amb: ctx.createGain() };
        buses.sfx.gain.value = 0.85; buses.music.gain.value = 0.8; buses.amb.gain.value = 0.0001;
        for (const k of ['sfx', 'music']) { mutes[k] = ctx.createGain(); mutes[k].gain.value = mute[k] ? 0 : 1; mutes[k].connect(master); }
        buses.sfx.connect(mutes.sfx); buses.music.connect(mutes.music); buses.amb.connect(mutes.music);
      }
      if (ctx.state === 'suspended') ctx.resume();
    } catch (e) { return null; }
    return ctx;
  }
  const live = () => ctx && ctx.state === 'running';
  function play(name) { if (!live()) return; try { SFX[name](ctx, buses.sfx, ctx.currentTime + 0.005); } catch (e) { /* ignore */ } }

  let spinNode = null;
  // ---------------------------------------------------------------- the songs
  // song: { file, gain, lead } (stages.js). The file's bytes are fetched as soon as asked; they are decoded once there
  // is a context (decoding gives the context's own rate). Where the song starts in the decoded buffer is found by its
  // first sound: `lead` is when that comes, in the time of the render (where song time 0 is at 0.05 s), so whatever
  // padding a decoder puts at the front does not matter.
  const bytes = {}, songs = {};
  function fetchSong(song) {
    if (!bytes[song.file]) bytes[song.file] = fetch(song.file).then((r) => { if (!r.ok) throw new Error(song.file + ' ' + r.status); return r.arrayBuffer(); });
    return bytes[song.file];
  }
  function firstSound(buf) {
    const L = buf.getChannelData(0), R = buf.numberOfChannels > 1 ? buf.getChannelData(1) : L;
    for (let i = 0; i < L.length; i++) if (Math.abs(L[i]) > 0.004 || Math.abs(R[i]) > 0.004) return i / buf.sampleRate;
    return 0;
  }
  function prepare(song) {
    if (songs[song.file]) return songs[song.file];
    const p = (async () => {
      const ab = await fetchSong(song);
      if (!ctx) throw new Error('no sound yet');
      const buf = await ctx.decodeAudioData(ab.slice(0));
      p.ready = { buf, zero: firstSound(buf) - song.lead + 0.05 };
      return p.ready;
    })();
    p.catch(() => { if (songs[song.file] === p) delete songs[song.file]; });  // to try again later
    songs[song.file] = p;
    return p;
  }
  const ready = (song) => !!(songs[song.file] && songs[song.file].ready);
  // a decoded song is big (35 s of stereo ~12 MB): let go of one not wanted soon (its file's bytes are kept, small)
  function release(song) { if (song && songs[song.file] && !(cur && cur.song.file === song.file) && !(loopCur && loopCur.song.file === song.file)) delete songs[song.file]; }
  const audioMB = () => Object.values(songs).reduce((s, p) => s + (p.ready ? p.ready.buf.length * p.ready.buf.numberOfChannels * 4 : 0), 0) / 1e6;
  let cur = null;
  // play `song` so that its time 0 (the first beat of its first bar) sounds at context time t0; when it is already
  // playing, it goes over with a quick crossfade (the orbit stage going back two beats)
  function playSong(song, t0) {
    if (!ctx || !ready(song)) return false;
    const S = songs[song.file].ready, now = ctx.currentTime, fade = cur ? 0.03 : 0;
    let when = t0, off = S.zero;                       // where song time 0 is in the buffer
    // a start already past (the orbit going back mid-song) goes a moment ahead: a source started "now" begins at the
    // sound card's next block, late by up to that block (measured: 2.9 ms here, a phone's blocks are bigger)
    const soon = now + 0.03;
    if (when < soon) { off += soon - when; when = soon; }
    stopSong(0.03, when);                              // the one playing goes out as this comes in
    const src = ctx.createBufferSource(); src.buffer = S.buf;
    const g = ctx.createGain(); src.connect(g); g.connect(buses.music);
    if (off < 0) { when -= off; off = 0; }
    if (fade) { g.gain.setValueAtTime(0.0001, when); g.gain.linearRampToValueAtTime(song.gain, when + fade); } else g.gain.value = song.gain;
    src.start(when, off);
    cur = { src, g, song, when, off, zero: S.zero };
    return true;
  }
  function stopSong(fade = 0.4, at = 0) {
    if (!cur || !ctx) { cur = null; return; }
    const { src, g } = cur, t = Math.max(ctx.currentTime, at);
    g.gain.cancelScheduledValues(t); g.gain.setValueAtTime(Math.max(0.0001, g.gain.value), t); g.gain.linearRampToValueAtTime(0.0001, t + fade);
    try { src.stop(t + fade + 0.02); } catch (e) { /* not started */ }
    cur = null;
  }
  // ---------------------------------------------------------------- a stage's own looping music (the baseball stage's):
  // song: { file, gain, loop: [start, end] s }, on the music bus, in softly; stopLoop fades it out
  let loopCur = null;
  function playLoop(song, fadeIn = 0.8) {
    if (!ctx || !ready(song)) return false;
    stopLoop(0.1);
    const S = songs[song.file].ready, src = ctx.createBufferSource();
    src.buffer = S.buf; src.loop = true; src.loopStart = song.loop[0]; src.loopEnd = song.loop[1];
    const g = ctx.createGain(), t0 = ctx.currentTime + 0.03; src.connect(g); g.connect(buses.music);
    g.gain.setValueAtTime(0.0001, t0); g.gain.linearRampToValueAtTime(song.gain, t0 + fadeIn);
    src.start(t0, song.loop[0]);
    loopCur = { src, g, song };
    return true;
  }
  function stopLoop(fade = 0.6) {
    if (!loopCur || !ctx) { loopCur = null; return; }
    const { src, g } = loopCur, t = ctx.currentTime;
    g.gain.cancelScheduledValues(t); g.gain.setValueAtTime(Math.max(0.0001, g.gain.value), t); g.gain.linearRampToValueAtTime(0.0001, t + fade);
    try { src.stop(t + fade + 0.02); } catch (e) { /* not started */ }
    loopCur = null;
  }
  // ---------------------------------------------------------------- the running music: one source looping the file's
  // loop (bgm: { file, gain, loop: [start, end] s }); it plays on (silent) through the mini-games, and comes back up
  const AMB = 0.55;                                       // its bus's level when on
  let bgm = null, bgmSrc = null, bgmWant = false;
  function setBGM(b) { bgm = b; fetchSong(b).catch(() => {}); if (ctx) prepare(b).catch(() => {}); }
  function startBGM() {
    if (!ctx || !bgm || bgmSrc) return;
    if (!ready(bgm)) { prepare(bgm).then(() => { if (bgmWant) startBGM(); }).catch(() => {}); return; }
    const S = songs[bgm.file].ready, src = ctx.createBufferSource();
    src.buffer = S.buf; src.loop = true; src.loopStart = bgm.loop[0]; src.loopEnd = bgm.loop[1];
    const g = ctx.createGain(), t0 = ctx.currentTime + 0.05; src.connect(g); g.connect(buses.amb);
    g.gain.setValueAtTime(0.0001, t0); g.gain.linearRampToValueAtTime(bgm.gain, t0 + 1.2);   // in softly, whenever it comes
    src.start(t0, bgm.loop[0]);
    bgmSrc = src;
  }
  function ambience(on) {
    bgmWant = on;
    if (!ctx) return;
    const g = buses.amb.gain, t = ctx.currentTime;
    g.cancelScheduledValues(t); g.setValueAtTime(Math.max(0.0001, g.value), t);
    if (on) { startBGM(); g.linearRampToValueAtTime(AMB, t + 1.5); } else g.linearRampToValueAtTime(0.0001, t + 0.6);
  }
  // the spinner: a hum whose pitch follows how fast you turn
  function spin(speed) {
    if (!live()) return;
    if (speed === null) { if (spinNode) { spinNode.g.gain.setTargetAtTime(0.0001, ctx.currentTime, 0.05); spinNode.o.stop(ctx.currentTime + 0.3); spinNode = null; } return; }
    if (!spinNode) {
      const o = ctx.createOscillator(); o.type = 'sawtooth';
      const f = ctx.createBiquadFilter(); f.type = 'bandpass'; f.Q.value = 3; f.frequency.value = 900;
      const g = ctx.createGain(); g.gain.value = 0.0001;
      o.connect(f); f.connect(g); g.connect(buses.sfx); o.start();
      spinNode = { o, f, g };
    }
    const s = Math.min(1, speed / 3);                         // turns per second -> 0..1
    spinNode.o.frequency.setTargetAtTime(160 + 520 * s, ctx.currentTime, 0.04);
    spinNode.f.frequency.setTargetAtTime(600 + 1800 * s, ctx.currentTime, 0.04);
    spinNode.g.gain.setTargetAtTime(0.02 + 0.09 * s, ctx.currentTime, 0.05);
  }
  function setMute(kind, on) {                               // kind: 'sfx' | 'music' (works while paused too)
    mute[kind] = on;
    try { localStorage.setItem('bodyrun.mute.' + kind, on ? '1' : '0'); localStorage.removeItem('bodyrun.mute'); } catch (e) { /* storage off */ }
    const g = mutes[kind]; if (g) { g.gain.cancelScheduledValues(0); g.gain.value = on ? 0 : 1; }
  }

  // ---------------------------------------------------------------- tests: render offline and hand back the samples
  async function renderOffline(what, secs) {                // the effects one after another (tests)
    const sr = 44100;
    const c = new OfflineAudioContext(1, Math.ceil(sr * secs), sr);
    const comp = c.createDynamicsCompressor(); comp.threshold.value = -10; comp.ratio.value = 4; comp.attack.value = 0.003; comp.release.value = 0.15;
    comp.connect(c.destination);
    const bus = c.createGain(); bus.gain.value = 0.85; bus.connect(comp);
    Object.keys(SFX).forEach((n, i) => SFX[n](c, bus, 0.05 + i * 0.6));
    const buf = await c.startRendering();
    return buf.getChannelData(0);
  }

  // ---------------------------------------------------------------- tests: record what goes out (after the master
  // compressor), each block stamped with its frame in the context's own time (an AudioWorklet), so where a sound is in
  // the recording says exactly when the game played it
  let tapNode = null, tapChunks = [];
  async function tapStart() {
    if (!ctx) return false;
    const code = `class Tap extends AudioWorkletProcessor { constructor() { super(); this.b = new Float32Array(8192); this.n = 0; this.f = -1; }
      process(ins) { const i = ins[0]; if (!i || !i[0]) return true; const L = i[0], R = i[1] || i[0];
        if (this.f < 0) this.f = currentFrame;
        for (let k = 0; k < L.length; k++) this.b[this.n++] = (L[k] + R[k]) / 2;
        if (this.n >= 8192 - 128) { this.port.postMessage({ f: this.f, d: this.b.slice(0, this.n) }); this.n = 0; this.f = -1; }
        return true; } }
      registerProcessor('tap', Tap);`;
    await ctx.audioWorklet.addModule(URL.createObjectURL(new Blob([code], { type: 'application/javascript' })));
    tapChunks = [];
    tapNode = new AudioWorkletNode(ctx, 'tap', { numberOfInputs: 1, numberOfOutputs: 1, outputChannelCount: [1] });
    tapNode.port.onmessage = (e) => tapChunks.push(e.data);
    const z = ctx.createGain(); z.gain.value = 0; outNode.connect(tapNode); tapNode.connect(z); z.connect(ctx.destination);
    return true;
  }
  function tapTake() {                                      // the recording so far: { sr, f0, data: Float32Array }
    if (!tapChunks.length) return null;
    const f0 = tapChunks[0].f, end = tapChunks[tapChunks.length - 1].f + tapChunks[tapChunks.length - 1].d.length, out = new Float32Array(end - f0);
    for (const c of tapChunks) out.set(c.d, c.f - f0);
    return { sr: ctx.sampleRate, f0, data: out };
  }

  return {
    tapStart, tapTake,
    unlock, play, fetchSong, prepare, ready, playSong, stopSong, setBGM, ambience, spin, setMute, renderOffline, release, audioMB, playLoop, stopLoop,
    get looping() { return loopCur ? loopCur.song : null; },
    get bgmOn() { return !!bgmSrc; },
    get playing() { return cur ? cur.song : null; },
    songTime: () => (cur && ctx ? ctx.currentTime - cur.when + cur.off - cur.zero : null),   // where the song is now (tests)
    songZero: (song) => (songs[song.file] && songs[song.file].ready ? songs[song.file].ready.zero : null),
    muted: (kind) => mute[kind],
    muteGain: (kind) => (mutes[kind] ? mutes[kind].gain.value : null),     // (tests)
    get ctx() { return ctx; },
    live,
    latency: () => (ctx ? (ctx.outputLatency || 0) + (ctx.baseLatency || 0) : 0),
    names: () => Object.keys(SFX),
  };
})();
