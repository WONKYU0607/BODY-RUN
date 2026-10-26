// Body Run sounds: the effects and the ambience are synthesized with the Web Audio API; the mini-games' songs are
// files (made with the chip engine in chip/, see stages.js):
//  - effects: jump (1st/2nd/3rd), slide, items, heal, hit, game over, buttons, the rhythm and orbit stages' hits
//  - the running music: a file that loops (light, as if under water), turned down for the mini-games
//  - the songs of the rhythm and orbit stages: fetched early, decoded once the sound is on, played from the buffer
//    (a song can be started at any point of it, which the orbit stage uses to go back two beats after a miss)
// The voices take any audio context, so a test can render them offline and measure them.
window.BodySound = (() => {
  'use strict';
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
  };

  // ---------------------------------------------------------------- the live context and its buses
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
        buses.sfx.gain.value = 0.85; buses.music.gain.value = 0.8; buses.amb.gain.value = 0.0001;
        for (const b of Object.values(buses)) b.connect(master);
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
  let cur = null;
  // play `song` so that its time 0 (the first beat of its first bar) sounds at context time t0; when it is already
  // playing, it goes over with a quick crossfade (the orbit stage going back two beats)
  function playSong(song, t0) {
    if (!ctx || !ready(song)) return false;
    const S = songs[song.file].ready, now = ctx.currentTime, fade = cur ? 0.03 : 0;
    stopSong(0.03);
    const src = ctx.createBufferSource(); src.buffer = S.buf;
    const g = ctx.createGain(); src.connect(g); g.connect(buses.music);
    let when = t0, off = S.zero;                       // where song time 0 is in the buffer
    if (when < now) { off += now - when; when = now; }
    if (off < 0) { when -= off; off = 0; }
    if (fade) { g.gain.setValueAtTime(0.0001, when); g.gain.linearRampToValueAtTime(song.gain, when + fade); } else g.gain.value = song.gain;
    src.start(when, off);
    cur = { src, g, song, when, off, zero: S.zero };
    return true;
  }
  function stopSong(fade = 0.4) {
    if (!cur || !ctx) { cur = null; return; }
    const { src, g } = cur, t = ctx.currentTime;
    g.gain.cancelScheduledValues(t); g.gain.setValueAtTime(Math.max(0.0001, g.gain.value), t); g.gain.linearRampToValueAtTime(0.0001, t + fade);
    try { src.stop(t + fade + 0.02); } catch (e) { /* not started */ }
    cur = null;
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
  function setMuted(m) {
    muted = m;
    try { localStorage.setItem('bodyrun.mute', m ? '1' : '0'); } catch (e) { /* storage off */ }
    if (master) master.gain.setTargetAtTime(m ? 0 : 1, ctx.currentTime, 0.03);
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

  return {
    unlock, play, fetchSong, prepare, ready, playSong, stopSong, setBGM, ambience, spin, setMuted, renderOffline,
    get bgmOn() { return !!bgmSrc; },
    get playing() { return cur ? cur.song : null; },
    songTime: () => (cur && ctx ? ctx.currentTime - cur.when + cur.off - cur.zero : null),   // where the song is now (tests)
    songZero: (song) => (songs[song.file] && songs[song.file].ready ? songs[song.file].ready.zero : null),
    get muted() { return muted; },
    get ctx() { return ctx; },
    live,
    latency: () => (ctx ? (ctx.outputLatency || 0) + (ctx.baseLatency || 0) : 0),
    names: () => Object.keys(SFX),
  };
})();
