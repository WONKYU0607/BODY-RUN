// Chip: a small retro sound chip in Web Audio, for the game's music. Pulse waves (12.5 / 25 / 50 % duty), the stepped
// 4-bit triangle of the old consoles, two kinds of noise (long, and short "metallic"), saws and a detuned "supersaw",
// two-operator FM (bass, brass, bells); per-note volume and filter envelopes, vibrato, arpeggios, slides; a channel can
// be overdriven (guitar) and ducked under the kick (pumping). A song is a list of note events on a 16th-note grid; the
// same events play live (scheduled a little ahead) or render offline. Mixing: stereo pans, an echo, a compressor and a
// limiter on the bus.
window.Chip = (() => {
  'use strict';
  const NOTE = (n) => 440 * Math.pow(2, (n - 69) / 12);
  const NAMES = { C: 0, D: 2, E: 4, F: 5, G: 7, A: 9, B: 11 };
  function midi(s) {                                     // "C#5" -> 73
    const m = /^([A-G])([#b]?)(-?\d)$/.exec(s); if (!m) throw new Error('note ' + s);
    return 12 * (+m[3] + 1) + NAMES[m[1]] + (m[2] === '#' ? 1 : m[2] === 'b' ? -1 : 0);
  }
  // a bar of 16 steps: "A4 - - C5 . . E5 -": a name starts a note, "-" holds it, "." is silence
  function bar(str, at) {
    const tk = str.trim().split(/\s+/); if (tk.length !== 16) throw new Error(`bar of ${tk.length}: ${str}`);
    const out = []; let cur = null;
    tk.forEach((t, i) => {
      if (t === '-') { if (cur) cur.len++; return; }
      cur = null;
      if (t === '.') return;
      cur = { step: at + i, n: midi(t), len: 1 }; out.push(cur);
    });
    return out;
  }

  // ---------------------------------------------------------------- waves (made once per audio context)
  const cache = new WeakMap();
  function waves(c) {
    if (cache.has(c)) return cache.get(c);
    const H = 96, w = {};
    for (const d of [0.125, 0.25, 0.5]) {
      const re = new Float32Array(H), im = new Float32Array(H);
      for (let n = 1; n < H; n++) { re[n] = Math.sin(2 * Math.PI * n * d) / (n * Math.PI); im[n] = (1 - Math.cos(2 * Math.PI * n * d)) / (n * Math.PI); }
      w['p' + d] = c.createPeriodicWave(re, im, { disableNormalization: false });
    }
    {                                                     // the stepped triangle: 32 levels over a period
      const N = 1024, x = new Float32Array(N);
      for (let i = 0; i < N; i++) { const s = Math.floor(i * 32 / N), v = s < 16 ? 15 - s : s - 16; x[i] = v / 7.5 - 1; }
      const re = new Float32Array(H), im = new Float32Array(H);
      for (let n = 1; n < H; n++) { let a = 0, b = 0; for (let i = 0; i < N; i++) { const ph = 2 * Math.PI * n * i / N; a += x[i] * Math.cos(ph); b += x[i] * Math.sin(ph); } re[n] = a / N; im[n] = b / N; }
      w.tri = c.createPeriodicWave(re, im);
    }
    {                                                     // a stadium organ: drawbars on the fundamental and its harmonics
      const amp = { 1: 1, 2: 0.85, 3: 0.65, 4: 0.55, 5: 0.25, 6: 0.38, 8: 0.32 };
      const re = new Float32Array(H), im = new Float32Array(H);
      for (const [n, a] of Object.entries(amp)) im[+n] = a;
      w.organ = c.createPeriodicWave(re, im);
    }
    for (const [name, tap, len] of [['nlong', 1, 32767], ['nshort', 6, 93 * 64]]) {   // the noise channel's two modes
      const b = c.createBuffer(1, len, c.sampleRate), d = b.getChannelData(0);
      let r = 1;
      for (let i = 0; i < len; i++) { const fb = (r ^ (r >> tap)) & 1; r = (r >> 1) | (fb << 14); d[i] = (r & 1) ? 0.9 : -0.9; }
      w[name] = b;
    }
    {                                                     // a soft clip for overdrive
      const n = 2048, cv = new Float32Array(n);
      for (let i = 0; i < n; i++) { const x = (i / (n - 1)) * 2 - 1; cv[i] = Math.tanh(x * 3.2) / Math.tanh(3.2); }
      w.clip = cv;
    }
    cache.set(c, w);
    return w;
  }

  // ---------------------------------------------------------------- the bus
  function bus(c, dest, o = {}) {
    const B = { groups: new Map() };
    B.in = c.createGain(); B.in.gain.value = o.drive || 1;
    const hp = c.createBiquadFilter(); hp.type = 'highpass'; hp.frequency.value = 30; hp.Q.value = 0.6;     // no rumble under the bass
    const comp = c.createDynamicsCompressor(); comp.threshold.value = -14; comp.ratio.value = 3; comp.attack.value = 0.006; comp.release.value = 0.14; comp.knee.value = 6;
    const lim = c.createDynamicsCompressor(); lim.threshold.value = -2.5; lim.ratio.value = 20; lim.attack.value = 0.001; lim.release.value = 0.08; lim.knee.value = 0;
    const out = c.createGain(); out.gain.value = o.gain || 1;
    if (o.lp) { const lp = c.createBiquadFilter(); lp.type = 'lowpass'; lp.frequency.value = o.lp; lp.Q.value = 0.5; B.in.connect(lp); lp.connect(hp); }   // the whole mix a little softened (under water)
    else B.in.connect(hp);
    hp.connect(comp); comp.connect(lim); lim.connect(out); out.connect(dest);
    // echo: two taps left and right (ping-pong), darker each time round
    B.echo = c.createGain(); B.echo.gain.value = 1;
    const dl = c.createDelay(2), dr = c.createDelay(2), fb = c.createGain(), lp = c.createBiquadFilter(), wet = c.createGain();
    dl.delayTime.value = o.echoTime || 0.3; dr.delayTime.value = o.echoTime || 0.3; fb.gain.value = o.echoFb ?? 0.32; lp.type = 'lowpass'; lp.frequency.value = 2600; wet.gain.value = o.echoWet ?? 0.25;
    const merger = c.createChannelMerger(2);
    B.echo.connect(dl); dl.connect(lp); lp.connect(dr); dr.connect(fb); fb.connect(dl);
    dl.connect(merger, 0, 0); dr.connect(merger, 0, 1); merger.connect(wet); wet.connect(B.in);
    // the drums have a bus of their own (how hard they hit against the rest), and a song may have a hall (reverb)
    B.dr = c.createGain(); B.dr.gain.value = o.drumGain || 1; B.dr.connect(B.in);
    B.drumRev = o.drumRev || {};
    if (o.reverb) {
      const cv = c.createConvolver(); cv.buffer = impulse(c, o.reverb.time || 2.2, o.reverb.damp || 4000);
      const pre = c.createDelay(0.25); pre.delayTime.value = o.reverb.pre ?? 0.025;
      const wet = c.createGain(); wet.gain.value = o.reverb.wet ?? 0.3;
      B.rev = c.createGain(); B.rev.connect(pre); pre.connect(cv); cv.connect(wet); wet.connect(B.in);
    }
    B.out = out;
    return B;
  }
  // a hall's impulse: stereo noise dying away over `T` s (-60 dB), darker as it goes, a few early reflections first
  function impulse(c, T, damp) {
    const sr = c.sampleRate, n = Math.ceil(sr * T), b = c.createBuffer(2, n, sr);
    for (let chn = 0; chn < 2; chn++) {
      const d = b.getChannelData(chn); let s = 1234 + chn * 777, y = 0;
      for (let i = 0; i < n; i++) {
        s = (s * 16807) % 2147483647; const w = (s / 2147483647) * 2 - 1, t = i / sr;
        const f = damp * (1 - 0.8 * Math.min(1, t / T)), a = Math.exp(-2 * Math.PI * f / sr);
        y = y * a + (1 - a) * w;
        d[i] = y * Math.exp(-6.9 * t / T) * (t < 0.004 ? t / 0.004 : 1);
      }
      for (const [ms, g] of [[11, 0.5], [19, 0.35], [29, 0.3], [41, 0.22], [53, 0.16]]) { const k = Math.floor(sr * (ms + chn * 3) / 1000); if (k < n) d[k] += g * (chn ? -1 : 1); }
    }
    return b;
  }
  // a channel's strip: [overdrive -> cabinet] -> gain (ducked under the kick) -> pan -> bus (+ echo send)
  function strip(c, B, ch) {
    if (B.groups.has(ch)) return B.groups.get(ch);
    const g = c.createGain(), p = c.createStereoPanner(); p.pan.value = ch.pan || 0;
    let input = g;
    if (ch.eq) {                                          // fixed filters on the channel (formants for a choir, ...)
      let last = null;
      for (const [type, f, gain, q] of [...ch.eq].reverse()) { const fl = c.createBiquadFilter(); fl.type = type; fl.frequency.value = f; fl.gain.value = gain || 0; fl.Q.value = q || 1; fl.connect(last || g); last = fl; }
      input = last;
    }
    if (ch.drive) {
      const pre = c.createGain(); pre.gain.value = ch.drive;
      const sh = c.createWaveShaper(); sh.curve = waves(c).clip; sh.oversample = '2x';
      const cab = c.createBiquadFilter(); cab.type = 'lowpass'; cab.frequency.value = ch.cab || 3800; cab.Q.value = 0.7;
      const body = c.createBiquadFilter(); body.type = 'peaking'; body.frequency.value = 900; body.gain.value = -3; body.Q.value = 0.8;
      const post = c.createGain(); post.gain.value = ch.post ?? 0.25;            // the level after the clip
      pre.connect(sh); sh.connect(cab); cab.connect(body); body.connect(post); post.connect(input); input = pre;
    }
    g.connect(p); p.connect(B.in);
    if (ch.echo > 0) { const s = c.createGain(); s.gain.value = ch.echo; p.connect(s); s.connect(B.echo); }
    if (ch.rev > 0 && B.rev) { const s = c.createGain(); s.gain.value = ch.rev; p.connect(s); s.connect(B.rev); }
    const S = { in: input, gain: g };
    B.groups.set(ch, S);
    return S;
  }

  // ---------------------------------------------------------------- voices
  // a pitched note: wave, start t, length in seconds, midi n, volume; envelope {a, d, s, r}; vibrato {depth (cents), rate,
  // delay}; arp: semitone offsets cycled every `arpRate` s; slide: from midi n0 over `slideT` s; fenv: a filter swept
  // from `from` to `to` Hz over `time` s; fm: {ratio, i0, i1, time} (modulation index from i0 to i1)
  function tone(c, B, ch, t, dur, n, vol, ev = {}) {
    const W = waves(c), f = NOTE(n), end = t + dur;
    const env = ch.env || { a: 0.004, d: 0.12, s: 0.7, r: 0.05 };
    const S = strip(c, B, ch);
    const g = c.createGain();
    g.gain.setValueAtTime(0, t);
    g.gain.linearRampToValueAtTime(vol, t + env.a);
    g.gain.setTargetAtTime(vol * env.s, t + env.a, env.d / 3);
    g.gain.setValueAtTime(vol * env.s, Math.max(t + env.a, end - 0.001));
    g.gain.linearRampToValueAtTime(0, end + env.r);
    let out = g;
    if (ch.fenv || ch.lp) {
      const fl = c.createBiquadFilter();
      if (ch.fenv) {
        fl.type = ch.fenv.type || 'lowpass'; fl.Q.value = ch.fenv.q ?? 1;
        fl.frequency.setValueAtTime(ch.fenv.from, t); fl.frequency.exponentialRampToValueAtTime(ch.fenv.to, t + ch.fenv.time);
      } else { fl.type = 'lowpass'; fl.frequency.value = ch.lp; fl.Q.value = 0.5; }
      g.connect(fl); out = fl;
    }
    out.connect(S.in);
    const stop = end + env.r + 0.05;
    const oscs = [];
    const mk = (det = 0) => {
      const o = c.createOscillator();
      const wv = ch.wave === 'ssaw' ? 'saw' : ch.wave;
      if (wv === 'saw') o.type = 'sawtooth'; else if (wv === 'sine' || wv === 'fm') o.type = 'sine'; else if (wv === 'square') o.type = 'square'; else o.setPeriodicWave(W[wv]);
      if (ev.slideFrom !== undefined) { o.frequency.setValueAtTime(NOTE(ev.slideFrom), t); o.frequency.exponentialRampToValueAtTime(f, t + (ev.slideT || 0.06)); }
      else o.frequency.setValueAtTime(f, t);
      o.detune.value = (ch.detune || 0) + det;
      if (ev.arp) { const step = ch.arpRate || 1 / 50; let k = 0; for (let tt = t; tt < end; tt += step, k++) o.frequency.setValueAtTime(NOTE(n + ev.arp[k % ev.arp.length]), tt); }
      o.connect(g); o.start(t); o.stop(stop); oscs.push(o);
      return o;
    };
    if (ch.wave === 'ssaw') { const sp = ch.spread || 14; for (const d of [-sp, -sp * 0.4, 0, sp * 0.4, sp]) mk(d); }
    else {
      const o = mk();
      if (ch.wave === 'fm') {                             // two operators: a sine modulating the carrier's frequency
        const fm = ch.fm || { ratio: 1, i0: 2, i1: 0.5, time: 0.2 };
        const m = c.createOscillator(); m.type = 'sine'; m.frequency.setValueAtTime(f * fm.ratio, t);
        const mg = c.createGain();
        if (fm.attack) { mg.gain.setValueAtTime(f * (fm.iA ?? 0), t); mg.gain.linearRampToValueAtTime(f * fm.i0, t + fm.attack); }
        else mg.gain.setValueAtTime(f * fm.i0, t);
        mg.gain.setTargetAtTime(f * fm.i1, t + (fm.attack || 0), (fm.time || 0.2) / 3);
        m.connect(mg); mg.connect(o.frequency); m.start(t); m.stop(stop);
      }
    }
    const vib = ch.vib;
    if (vib && dur > (vib.delay || 0.15)) {
      const lfo = c.createOscillator(); lfo.frequency.value = vib.rate || 5.5;
      const lg = c.createGain(); lg.gain.setValueAtTime(0, t); lg.gain.setValueAtTime(0, t + (vib.delay || 0.15)); lg.gain.linearRampToValueAtTime(vib.depth || 14, t + (vib.delay || 0.15) + 0.2);
      lfo.connect(lg); for (const o of oscs) lg.connect(o.detune); lfo.start(t); lfo.stop(stop);
    }
  }
  // drums on the noise channel (and the triangle / sine for the bodies of kick and toms)
  function drum(c, B, kind, t, vel = 1, d = {}) {
    const W = waves(c);
    const rv = d.rev ?? B.drumRev[kind] ?? 0;
    const sendTo = (node, pan, echo) => {
      const p = c.createStereoPanner(); p.pan.value = pan || 0; node.connect(p); p.connect(B.dr || B.in);
      if (echo) { const s = c.createGain(); s.gain.value = echo; p.connect(s); s.connect(B.echo); }
      if (rv > 0 && B.rev) { const s = c.createGain(); s.gain.value = rv; p.connect(s); s.connect(B.rev); }
    };
    const noise = (buf, rate, f0, type, q, dur, vol, a = 0.001, pan = d.pan, echo = d.echo, sweepTo = null) => {
      const s = c.createBufferSource(); s.buffer = W[buf]; s.loop = true; s.playbackRate.value = rate;
      const fl = c.createBiquadFilter(); fl.type = type; fl.frequency.setValueAtTime(f0, t); fl.Q.value = q;
      if (sweepTo) fl.frequency.exponentialRampToValueAtTime(sweepTo, t + a + dur);
      const g = c.createGain(); g.gain.setValueAtTime(0, t); g.gain.linearRampToValueAtTime(vol, t + a); g.gain.exponentialRampToValueAtTime(0.0008, t + a + dur);
      s.connect(fl); fl.connect(g); sendTo(g, pan, echo); s.start(t, (t * 7.3) % 0.5); s.stop(t + a + dur + 0.05);
    };
    const body = (wave, f0, f1, dur, vol, pan = 0) => {
      const o = c.createOscillator(); if (wave === 'sine') o.type = 'sine'; else if (wave === 'square') o.type = 'square'; else o.setPeriodicWave(W.tri);
      o.frequency.setValueAtTime(f0, t); if (f1 !== f0) o.frequency.exponentialRampToValueAtTime(f1, t + dur * 0.8);
      const g = c.createGain(); g.gain.setValueAtTime(0, t); g.gain.linearRampToValueAtTime(vol, t + 0.002); g.gain.exponentialRampToValueAtTime(0.0008, t + dur);
      o.connect(g); sendTo(g, pan, 0); o.start(t); o.stop(t + dur + 0.05);
    };
    const v = vel;
    if (kind === 'k') { body('sine', 160, 45, 0.2, 0.8 * v); body('tri', 120, 50, 0.12, 0.35 * v); noise('nlong', 1, 3500, 'highpass', 0.7, 0.012, 0.25 * v, 0.001, 0, 0); }
    else if (kind === 'K') { body('sine', 190, 40, 0.28, 0.9 * v); body('tri', 140, 45, 0.15, 0.4 * v); noise('nlong', 1, 2500, 'highpass', 0.7, 0.02, 0.3 * v, 0.001, 0, 0); }   // a heavier kick
    else if (kind === 's') { noise('nlong', 0.5, 1900, 'bandpass', 0.8, 0.16, 0.55 * v); body('tri', 240, 160, 0.07, 0.3 * v); noise('nlong', 1, 6000, 'highpass', 0.7, 0.05, 0.18 * v); }
    else if (kind === 'S') { noise('nlong', 0.5, 1700, 'bandpass', 0.7, 0.42, 0.5 * v); body('tri', 220, 150, 0.08, 0.3 * v); }       // a long snare (for big hits)
    else if (kind === 'cl') {                                                                                                 // a clap: three quick bursts and a tail
      for (const [dt, a] of [[0, 0.5], [0.011, 0.45], [0.022, 0.55]]) {
        const t0 = t + dt, s = c.createBufferSource(); s.buffer = W.nlong; s.loop = true;
        const fl = c.createBiquadFilter(); fl.type = 'bandpass'; fl.frequency.value = 1300; fl.Q.value = 1.1;
        const g = c.createGain(); g.gain.setValueAtTime(0, t0); g.gain.linearRampToValueAtTime(a * v, t0 + 0.001); g.gain.exponentialRampToValueAtTime(0.001, t0 + (dt > 0.02 ? 0.18 : 0.012));
        s.connect(fl); fl.connect(g); sendTo(g, d.pan, d.echo); s.start(t0, (t0 * 5.1) % 0.5); s.stop(t0 + 0.25);
      }
    }
    else if (kind === 'cb') {                                                                                                 // a cowbell
      for (const f of [540, 800]) {
        const o = c.createOscillator(); o.type = 'square'; o.frequency.value = f;
        const fl = c.createBiquadFilter(); fl.type = 'bandpass'; fl.frequency.value = 900; fl.Q.value = 2;
        const g = c.createGain(); g.gain.setValueAtTime(0, t); g.gain.linearRampToValueAtTime(0.14 * v, t + 0.001); g.gain.exponentialRampToValueAtTime(0.001, t + 0.16);
        o.connect(fl); fl.connect(g); sendTo(g, d.pan ?? 0.3, 0); o.start(t); o.stop(t + 0.2);
      }
    }
    else if (kind === 'h') noise('nshort', 1, 8000, 'highpass', 0.7, 0.028, 0.16 * v);
    else if (kind === 'o') noise('nshort', 1, 7000, 'highpass', 0.7, 0.16, 0.13 * v);
    else if (kind === 'r') { noise('nshort', 1.4, 5200, 'bandpass', 1.2, 0.5, 0.09 * v, 0.001, d.pan ?? -0.25); noise('nlong', 1, 9000, 'highpass', 0.7, 0.04, 0.05 * v, 0.001, d.pan ?? -0.25); }
    else if (kind === 'c') noise('nlong', 1, 4500, 'highpass', 0.5, 1.3, 0.28 * v);
    else if (kind === 't1' || kind === 't2' || kind === 't3') { const f = { t1: 260, t2: 190, t3: 140 }[kind]; body('tri', f, f * 0.55, 0.2, 0.55 * v); noise('nlong', 0.3, 900, 'lowpass', 0.6, 0.06, 0.12 * v); }
    else if (kind === 'x') noise('nlong', 2, 9000, 'highpass', 0.5, 0.018, 0.12 * v);         // a shaker tick
    // the big drums (for the epic songs): a taiko, its rim, floor toms that ring, a big snare, an impact
    // water: a bubble (a little sine whose pitch flies up as it forms) and a drip (a plink falling in pitch)
    else if (kind === 'crowd') {                           // a crowd's murmur over `len`: band noise, in and out slowly, swaying
      const L = d.len || 2, a = Math.min(0.8, L / 4), vol = 0.035 * v;   // (a murmur under the music: 0.2 was the whole mix)
      for (const [rate, f0, q, k, pan] of [[0.31, 900, 0.7, 1, -0.3], [0.37, 1250, 0.8, 0.8, 0.3], [0.5, 2300, 1.0, 0.35, 0]]) {
        const s = c.createBufferSource(); s.buffer = W.nlong; s.loop = true; s.playbackRate.value = rate;
        const fl = c.createBiquadFilter(); fl.type = 'bandpass'; fl.frequency.value = f0; fl.Q.value = q;
        const g = c.createGain(); g.gain.setValueAtTime(0, t); g.gain.linearRampToValueAtTime(vol * k, t + a); g.gain.setValueAtTime(vol * k, t + L - a); g.gain.linearRampToValueAtTime(0, t + L);
        const sway = c.createOscillator(), sg = c.createGain(); sway.frequency.value = 0.21 + rate * 0.3; sg.gain.value = vol * k * 0.35;
        sway.connect(sg); sg.connect(g.gain); sway.start(t); sway.stop(t + L + 0.05);
        s.connect(fl); fl.connect(g); sendTo(g, pan, 0); s.start(t, (t * 3.1) % 0.5); s.stop(t + L + 0.05);
      }
    }
    else if (kind === 'bub') {
      const f = d.f || 520, o = c.createOscillator(); o.type = 'sine'; o.frequency.setValueAtTime(f, t); o.frequency.exponentialRampToValueAtTime(f * 2.4, t + 0.045);
      const g = c.createGain(); g.gain.setValueAtTime(0, t); g.gain.linearRampToValueAtTime(0.16 * v, t + 0.004); g.gain.exponentialRampToValueAtTime(0.0008, t + 0.07);
      o.connect(g); sendTo(g, d.pan, d.echo); o.start(t); o.stop(t + 0.1);
    }
    else if (kind === 'drip') {
      const f = d.f || 1700, o = c.createOscillator(); o.type = 'sine'; o.frequency.setValueAtTime(f, t); o.frequency.exponentialRampToValueAtTime(f * 0.45, t + 0.035);
      const g = c.createGain(); g.gain.setValueAtTime(0, t); g.gain.linearRampToValueAtTime(0.14 * v, t + 0.002); g.gain.exponentialRampToValueAtTime(0.0008, t + 0.16);
      o.connect(g); sendTo(g, d.pan, d.echo); o.start(t); o.stop(t + 0.2);
    }
    else if (kind === 'kd') { body('sine', 150, 55, 0.085, 0.62 * v); noise('nlong', 1, 4200, 'highpass', 0.7, 0.008, 0.2 * v, 0.001, 0, 0); }   // a tight kick (double-kick runs)
    else if (kind === 'T') { body('sine', 118, 50, 0.62, 0.95 * v); body('tri', 175, 85, 0.13, 0.35 * v); noise('nlong', 0.4, 700, 'lowpass', 0.7, 0.07, 0.4 * v, 0.001, d.pan ?? 0, 0); }
    else if (kind === 'ka') { body('tri', 980, 900, 0.03, 0.2 * v, d.pan ?? 0.2); noise('nlong', 1, 2600, 'bandpass', 2, 0.025, 0.3 * v, 0.001, d.pan ?? 0.2, 0); }
    else if (kind === 'T1' || kind === 'T2' || kind === 'T3') {
      const f = { T1: 230, T2: 165, T3: 112 }[kind], pan = d.pan ?? { T1: -0.3, T2: 0, T3: 0.3 }[kind];
      body('tri', f, f * 0.62, 0.4, 0.62 * v, pan); body('sine', f * 0.75, f * 0.5, 0.48, 0.5 * v, pan); noise('nlong', 0.35, 1200, 'lowpass', 0.6, 0.07, 0.22 * v, 0.001, pan, 0);
    }
    else if (kind === 'SB') { noise('nlong', 0.5, 1800, 'bandpass', 0.6, 0.3, 0.7 * v); body('tri', 205, 140, 0.1, 0.42 * v); noise('nlong', 1, 5500, 'highpass', 0.7, 0.1, 0.26 * v); }
    else if (kind === 'boom') { body('sine', 82, 26, 1.7, 1.0 * v); body('tri', 120, 40, 0.3, 0.3 * v); noise('nlong', 0.3, 1600, 'lowpass', 0.6, 1.1, 0.4 * v, 0.002, 0, 0, 90); }
    else if (kind === 'up') noise('nlong', 1, 400, 'bandpass', 1.6, (d.len || 2) * 0.08, 0.22 * v, (d.len || 2) * 0.92, d.pan, 0.2, 6000);   // a rising sweep over `len` seconds
    else if (kind === 'down') noise('nlong', 1, 5000, 'bandpass', 1.2, d.len || 1, 0.2 * v, 0.004, d.pan, 0.2, 300);                     // and a falling one
  }

  // ---------------------------------------------------------------- songs -> events
  // song = { bpm, bars, ch: { name: { wave, vol, pan, echo, env, vib, drive, duck, notes: [{step, n, len, vol?, arp?, slideFrom?}] } },
  //          drums: [{step, k, v, len? (steps, for sweeps)}] }
  function events(song) {
    const st = 60 / song.bpm / 4, ev = [];
    for (const ch of Object.values(song.ch)) {
      for (const nt of ch.notes) ev.push({ t: nt.step * st, kind: 'tone', ch, nt, dur: nt.len * st * (ch.gate || 0.92) });
    }
    for (const d of song.drums) ev.push({ t: d.step * st, kind: 'drum', d: d.k === 'up' || d.k === 'down' || d.k === 'crowd' ? { ...d, len: (d.len || 16) * st } : d });
    return ev.sort((a, b) => a.t - b.t);
  }
  function play(c, B, e, t0) {
    const t = t0 + e.t;
    if (e.kind === 'tone') tone(c, B, e.ch, t, e.dur, e.nt.n, (e.ch.vol || 0.2) * (e.nt.vol ?? 1), e.nt);
    else {
      drum(c, B, e.d.k, t, e.d.v ?? 1, e.d);
      if (e.d.k === 'k' || e.d.k === 'K') for (const [ch, S] of B.groups) if (ch.duck) {      // pump the ducked channels on the kick
        S.gain.gain.setTargetAtTime(1 - ch.duck, t, 0.003); S.gain.gain.setTargetAtTime(1, t + 0.025, 0.07);
      }
    }
  }
  async function render(song, opts = {}) {
    const sr = opts.sr || 44100, st = 60 / song.bpm / 4, secs = song.bars * 16 * st + (opts.tail ?? 2.5);
    const c = new OfflineAudioContext(2, Math.ceil(sr * secs), sr);
    const B = bus(c, c.destination, { echoTime: st * 3, echoFb: song.echoFb, echoWet: song.echoWet, gain: song.gain || 1, drive: song.drive || 1,
      drumGain: song.drumGain, drumRev: song.drumRev, reverb: song.reverb, lp: song.lp });
    for (const ch of Object.values(song.ch)) strip(c, B, ch);          // every strip made before the first kick (for the pump)
    const ev = events(song), CH = opts.chunk || 0;
    if (!CH) for (const e of ev) play(c, B, e, 0.05);
    else {                                                // a little at a time, so the page does not stall making the notes
      let i = 0;
      const feed = (until) => { while (i < ev.length && ev[i].t + 0.05 < until) play(c, B, ev[i++], 0.05); };
      feed(CH * 1.5);
      for (let s = CH; s < secs - 0.01; s += CH) { const at = s; c.suspend(at).then(() => { feed(at + CH * 1.5); c.resume(); }); }
    }
    const buf = await c.startRendering();
    return opts.buffer ? buf : [buf.getChannelData(0), buf.getChannelData(1)];
  }
  return { NOTE, midi, bar, waves, bus, impulse, strip, tone, drum, events, play, render };
})();
