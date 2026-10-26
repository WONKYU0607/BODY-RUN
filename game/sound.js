// Body Run sounds: everything is synthesized with the Web Audio API (no sound files).
//  - effects: jump (1st/2nd/3rd), slide, items, heal, hit, game over, buttons, the rhythm stage's hits and misses
//  - a quiet body ambience while running (a slow heartbeat under a soft pad)
//  - the rhythm stage's track: 110 BPM, the heartbeat as its kick drum
//  - the orbit stage's track (a stand-in until the real song): 120 BPM, its lead plays each tile's beat
// The voices take any audio context, so a test can render them offline and measure them.
window.BodySound = (() => {
  'use strict';
  const BPM = 110, BEAT = 60 / BPM;
  const ORB_BPM = 120, ORB_BEAT = 60 / ORB_BPM;
  let ctx = null, master = null, buses = null, muted = false, noiseBuf = null;
  try { muted = localStorage.getItem('bodyrun.mute') === '1'; } catch (e) { /* storage off */ }

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

  // ---------------------------------------------------------------- effects
  const SFX = {
    jump1: (c, o, t) => { tone(c, o, t, 'triangle', 330, 720, 0.13, 0.32, 0.004, 0.09); tone(c, o, t, 'square', 330, 720, 0.07, 0.05, 0.004, 0.07); },
    jump2: (c, o, t) => { tone(c, o, t, 'triangle', 440, 960, 0.13, 0.3, 0.004, 0.08); tone(c, o, t, 'square', 440, 960, 0.07, 0.05, 0.004, 0.07); },
    jump3: (c, o, t) => { tone(c, o, t, 'triangle', 560, 1240, 0.15, 0.28, 0.004, 0.08); tone(c, o, t + 0.05, 'sine', 1660, 1660, 0.12, 0.08); },
    slide: (c, o, t) => burst(c, o, t, 'bandpass', 2600, 500, 1.4, 0.22, 0.32, 0.01),
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
  };

  // ---------------------------------------------------------------- music voices
  const MUS = {
    lub: (c, o, t, v = 1) => { tone(c, o, t, 'sine', 95, 48, 0.2, 0.9 * v, 0.003, 0.12); burst(c, o, t, 'lowpass', 300, 150, 0.6, 0.06, 0.2 * v); },
    dub: (c, o, t, v = 1) => tone(c, o, t, 'sine', 80, 52, 0.16, 0.6 * v, 0.003, 0.1),
    hat: (c, o, t, v = 1) => burst(c, o, t, 'highpass', 7500, 7500, 0.7, 0.035, 0.12 * v),
    clap: (c, o, t, v = 1) => { burst(c, o, t, 'bandpass', 1800, 1400, 0.9, 0.13, 0.3 * v); tone(c, o, t, 'triangle', 190, 160, 0.06, 0.12 * v); },
    bass: (c, o, t, n, dur = BEAT / 2) => {
      const os = c.createOscillator(); os.type = 'sawtooth'; os.frequency.setValueAtTime(NOTE(n), t);
      const f = c.createBiquadFilter(); f.type = 'lowpass'; f.Q.value = 4; f.frequency.setValueAtTime(900, t); f.frequency.exponentialRampToValueAtTime(220, t + dur);
      const g = gainEnv(c, o, t, 0.2, 0.006, dur * 0.95);
      os.connect(f); f.connect(g); os.start(t); os.stop(t + dur + 0.05);
    },
    lead: (c, o, t, n, dur = BEAT / 2, v = 1) => {
      const os = c.createOscillator(); os.type = 'square'; os.frequency.setValueAtTime(NOTE(n), t);
      const f = c.createBiquadFilter(); f.type = 'lowpass'; f.frequency.setValueAtTime(3200, t); f.frequency.exponentialRampToValueAtTime(900, t + dur);
      const g = gainEnv(c, o, t, 0.07 * v, 0.004, dur * 0.9);
      os.connect(f); f.connect(g); os.start(t); os.stop(t + dur + 0.05);
    },
    pad: (c, o, t, notes, dur, v = 1) => {
      for (const n of notes) for (const det of [-6, 6]) {
        const os = c.createOscillator(); os.type = 'sawtooth'; os.frequency.setValueAtTime(NOTE(n), t); os.detune.value = det;
        const f = c.createBiquadFilter(); f.type = 'lowpass'; f.frequency.value = 1200;
        const g = c.createGain(); g.gain.setValueAtTime(0.0001, t); g.gain.linearRampToValueAtTime(0.018 * v, t + Math.min(0.4, dur * 0.3));
        g.gain.setValueAtTime(0.018 * v, t + dur * 0.8); g.gain.linearRampToValueAtTime(0.0001, t + dur);
        os.connect(f); f.connect(g); g.connect(o); os.start(t); os.stop(t + dur + 0.05);
      }
    },
    riser: (c, o, t, dur) => {
      burst(c, o, t, 'bandpass', 400, 5000, 2.0, dur, 0.22, dur * 0.85);
      const os = c.createOscillator(); os.type = 'sawtooth'; os.frequency.setValueAtTime(110, t); os.frequency.exponentialRampToValueAtTime(880, t + dur);
      const f = c.createBiquadFilter(); f.type = 'lowpass'; f.frequency.value = 2000;
      const g = c.createGain(); g.gain.setValueAtTime(0.0001, t); g.gain.linearRampToValueAtTime(0.06, t + dur * 0.9); g.gain.linearRampToValueAtTime(0.0001, t + dur);
      os.connect(f); f.connect(g); g.connect(o); os.start(t); os.stop(t + dur + 0.05);
    },
    crash: (c, o, t) => burst(c, o, t, 'highpass', 4000, 3000, 0.5, 1.2, 0.22),
    kick: (c, o, t, v = 1) => { tone(c, o, t, 'sine', 150, 45, 0.18, 0.85 * v, 0.002, 0.1); burst(c, o, t, 'lowpass', 900, 200, 0.6, 0.03, 0.15 * v); },
    count: (c, o, t, hi = false) => tone(c, o, t, 'triangle', hi ? 1568 : 1046, null, 0.07, 0.16),
    pluck: (c, o, t, n, v = 1) => {                       // the tune: a bright pluck on every tile
      for (const [type, det, pk] of [['triangle', 0, 0.16], ['square', 7, 0.035]]) {
        const os = c.createOscillator(); os.type = type; os.frequency.setValueAtTime(NOTE(n), t); os.detune.value = det;
        const f = c.createBiquadFilter(); f.type = 'lowpass'; f.frequency.setValueAtTime(5000, t); f.frequency.exponentialRampToValueAtTime(1200, t + 0.25);
        const g = gainEnv(c, o, t, pk * v, 0.003, 0.28);
        os.connect(f); f.connect(g); os.start(t); os.stop(t + 0.35);
      }
    },
  };

  // ---------------------------------------------------------------- the rhythm stage's track (beats from its start)
  const CHORDS = [[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]];   // Am F C G
  const ROOT = [45, 41, 48, 43];
  function trackEvents() {
    const ev = [];
    const add = (b, fn, ...a) => ev.push([b, fn, a]);
    const TOTAL = 42;
    for (let b = 0; b < TOTAL; b++) {
      const bar = Math.floor(b / 4), ch = bar % 4, inBar = b % 4;
      const full = b >= 4 && b < 32, spin = b >= 32 && b < 37;
      add(b, 'lub', b < 4 ? 0.8 : 1); add(b + 0.3, 'dub', b < 4 ? 0.7 : 0.85);
      if (inBar === 0) add(b, 'pad', CHORDS[ch], BEAT * 4, b < 4 ? 0.7 : 1);
      if (full || spin) { add(b, 'hat', 0.8); add(b + 0.5, 'hat', 1.2); }
      if (full && (inBar === 1 || inBar === 3)) add(b, 'clap');
      if (full || spin) { add(b, 'bass', ROOT[ch]); add(b + 0.5, 'bass', ROOT[ch] + (inBar === 3 ? 7 : 0)); }
      if (b >= 12 && b < 32) {                            // an arpeggio over the chords once it gets going
        const tones = CHORDS[ch].map((n) => n + 12);
        const seq = [0, 1, 2, 1];
        add(b, 'lead', tones[seq[inBar]], BEAT / 2, 1); add(b + 0.5, 'lead', tones[(seq[inBar] + 1) % 3] + (inBar === 3 ? 12 : 0), BEAT / 2, 0.8);
      }
    }
    add(32, 'riser', BEAT * 5);
    add(37, 'crash'); add(37, 'pad', [57, 60, 64, 69], BEAT * 4, 1.2);
    return ev.sort((a, b) => a[0] - b[0]);
  }

  // ---------------------------------------------------------------- the orbit stage's stand-in track (beats from its start)
  // hits: the beats the tiles fall on (the first after a count of four); four on the floor, claps, eighth hats, a bass
  // and a pad on Am F C G, and the tune on the tiles themselves (so you can hear when to tap). The bars count from
  // `first` (the first tile's beat as planned), so after a miss pushes the tiles on, the bars stay where they were
  function orbEvents(hits, first = hits[0]) {
    const ev = [];
    const add = (b, fn, ...a) => ev.push([b, fn, a]);
    const last = hits[hits.length - 1];
    for (let b = 0; b < first; b++) add(b, 'count', b === first - 1);
    for (let b = first; b < last; b++) {
      const k = b - first, bar = Math.floor(k / 4), ch = bar % 4, inBar = k % 4;
      add(b, 'kick', inBar === 0 ? 1 : 0.85);
      if (inBar === 1 || inBar === 3) add(b, 'clap', 0.8);
      add(b + 0.5, 'hat', 1); if (bar >= 4) add(b, 'hat', 0.6);
      add(b, 'bass', ROOT[ch], ORB_BEAT / 2); add(b + 0.5, 'bass', ROOT[ch] + (inBar === 3 ? 7 : 12), ORB_BEAT / 2);
      if (inBar === 0) add(b, 'pad', CHORDS[ch], ORB_BEAT * 4, 0.8);
    }
    hits.forEach((h, i) => {
      if (h >= last) return;
      const ch = Math.max(0, Math.floor((h - first) / 4)) % 4, tones = CHORDS[ch].map((n) => n + 24);
      add(h, 'pluck', tones[i % 3] + (i % 6 === 5 ? 12 : 0), 1);
    });
    if (last - first >= 8) add(last - 8, 'riser', ORB_BEAT * 7.5);
    add(last, 'crash'); add(last, 'pad', [57, 60, 64, 69], ORB_BEAT * 4, 0.8); add(last, 'pluck', 93, 0.7);
    return ev.sort((a, b) => a[0] - b[0]);
  }

  // ---------------------------------------------------------------- the body ambience while running: 72 BPM heartbeat, slow pad
  const AMB_BEAT = 60 / 72;
  function ambienceBar(k) {                                // events of bar k (4 beats), in seconds from the bar's start
    const ev = [];
    for (let b = 0; b < 4; b++) { ev.push([b * AMB_BEAT, 'lub', [0.45]]); ev.push([b * AMB_BEAT + 0.28, 'dub', [0.35]]); }
    if (k % 2 === 0) ev.push([0, 'pad', [CHORDS[(k / 2) % 4], AMB_BEAT * 8, 0.55]]);
    return ev;
  }

  // ---------------------------------------------------------------- the live context, buses, a little scheduler
  function unlock() {
    try {
      if (!ctx) {
        const AC = window.AudioContext || window.webkitAudioContext;
        if (!AC) return null;
        ctx = new AC({ latencyHint: 'interactive' });
        master = ctx.createGain(); master.gain.value = muted ? 0 : 1;
        const comp = ctx.createDynamicsCompressor(); comp.threshold.value = -10; comp.ratio.value = 4; comp.attack.value = 0.003; comp.release.value = 0.15;
        master.connect(comp); comp.connect(ctx.destination);
        buses = { sfx: ctx.createGain(), music: ctx.createGain(), amb: ctx.createGain() };
        buses.sfx.gain.value = 0.85; buses.music.gain.value = 0.8; buses.amb.gain.value = 0.55;
        for (const b of Object.values(buses)) b.connect(master);
        setInterval(schedule, 25);
      }
      if (ctx.state === 'suspended') ctx.resume();
    } catch (e) { return null; }
    return ctx;
  }
  const live = () => ctx && ctx.state === 'running';
  function play(name) { if (!live()) return; try { SFX[name](ctx, buses.sfx, ctx.currentTime + 0.005); } catch (e) { /* ignore */ } }

  let track = null, amb = null, spinNode = null;
  function schedule() {
    if (!live()) return;
    const until = ctx.currentTime + 0.15;
    if (track) {
      while (track.i < track.ev.length && track.t0 + track.ev[track.i][0] * track.beat < until) {
        const [b, fn, a] = track.ev[track.i++];
        const t = track.t0 + b * track.beat;
        if (t >= ctx.currentTime - 0.02) MUS[fn](ctx, buses.music, Math.max(t, ctx.currentTime), ...a);
      }
    }
    if (amb && amb.on) {
      while (amb.next < until) {
        for (const [dt, fn, a] of ambienceBar(amb.k)) if (amb.next + dt >= ctx.currentTime - 0.02) MUS[fn](ctx, buses.amb, Math.max(amb.next + dt, ctx.currentTime), ...a);
        amb.next += AMB_BEAT * 4; amb.k++;
      }
    }
  }
  function startTrack(t0) { if (!ctx) return; track = { ev: trackEvents(), i: 0, t0, beat: BEAT }; schedule(); }
  function startOrb(t0, hits, first) { if (!ctx) return; track = { ev: orbEvents(hits, first), i: 0, t0, beat: ORB_BEAT }; schedule(); }
  function stopTrack() { track = null; }
  function ambience(on) {
    if (!ctx) return;
    if (on && !(amb && amb.on)) {
      amb = { on: true, k: 0, next: ctx.currentTime + 0.3 };
      buses.amb.gain.cancelScheduledValues(ctx.currentTime); buses.amb.gain.setValueAtTime(0.0001, ctx.currentTime); buses.amb.gain.linearRampToValueAtTime(0.55, ctx.currentTime + 1.5);
    } else if (!on && amb && amb.on) {
      amb.on = false;
      buses.amb.gain.cancelScheduledValues(ctx.currentTime); buses.amb.gain.setValueAtTime(buses.amb.gain.value, ctx.currentTime); buses.amb.gain.linearRampToValueAtTime(0.0001, ctx.currentTime + 0.6);
    }
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
  function setMuted(m) {
    muted = m;
    try { localStorage.setItem('bodyrun.mute', m ? '1' : '0'); } catch (e) { /* storage off */ }
    if (master) master.gain.setTargetAtTime(m ? 0 : 1, ctx.currentTime, 0.03);
  }

  // ---------------------------------------------------------------- tests: render offline and hand back the samples
  async function renderOffline(what, secs, hits, first) {
    const sr = 44100;
    const c = new OfflineAudioContext(1, Math.ceil(sr * secs), sr);
    const comp = c.createDynamicsCompressor(); comp.threshold.value = -10; comp.ratio.value = 4; comp.attack.value = 0.003; comp.release.value = 0.15;
    comp.connect(c.destination);
    const bus = c.createGain(); bus.gain.value = what === 'sfx' ? 0.85 : what === 'amb' ? 0.55 : 0.8; bus.connect(comp);
    if (what === 'track') for (const [b, fn, a] of trackEvents()) { if (b * BEAT < secs) MUS[fn](c, bus, 0.05 + b * BEAT, ...a); }
    else if (what === 'orb') for (const [b, fn, a] of orbEvents(hits, first)) { if (b * ORB_BEAT < secs) MUS[fn](c, bus, 0.05 + b * ORB_BEAT, ...a); }
    else if (what === 'amb') { let t = 0.05, k = 0; while (t < secs) { for (const [dt, fn, a] of ambienceBar(k)) MUS[fn](c, bus, t + dt, ...a); t += AMB_BEAT * 4; k++; } }
    else { Object.keys(SFX).forEach((n, i) => SFX[n](c, bus, 0.05 + i * 0.6)); }
    const buf = await c.startRendering();
    return buf.getChannelData(0);
  }

  return {
    BPM, BEAT, ORB_BEAT, unlock, play, startTrack, startOrb, stopTrack, ambience, spin, setMuted, renderOffline,
    get muted() { return muted; },
    get ctx() { return ctx; },
    live,
    latency: () => (ctx ? (ctx.outputLatency || 0) + (ctx.baseLatency || 0) : 0),
    names: () => Object.keys(SFX),
  };
})();
