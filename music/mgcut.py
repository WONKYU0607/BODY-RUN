# the mini-games' music files (v42): the germ game's song once through (song time 0 at the file's start, ringing out
# at the end), the memory game's loop (the middle of three rounds, a quarter second either side); levelled, MP3,
# gains and loop points in music_meta.json
import numpy as np, scipy.io.wavfile as wf, json, subprocess, sys, io, contextlib, os
sys.path.insert(0, '/home/claude/work')
with contextlib.redirect_stdout(io.StringIO()):
    from loud import kweight
D = '/tmp/claude-0/-home-claude/3a779e8a-891a-5a91-a306-4a5325e0d53e/scratchpad/music/mg'
A = '/home/claude/runner_hd/assets'
ZERO, BUS = 0.062, 20 * np.log10(0.8)        # song time 0 in a render (0.05 + the compressors' 12 ms); the music bus
meta = json.load(open('/home/claude/work/music_meta.json'))
def lufs(seg, sr):
    y = kweight(seg, sr); return -0.691 + 10 * np.log10(np.mean(np.sum(y ** 2, axis=1)))
# ---- the germ game: once through
sr, x = wf.read(f'{D}/germSmash_raw.wav'); x = x.astype(np.float64) / 32768 * 2
END = 32 * 4 * 60 / 150                       # 51.2 s: the end hit is at 48 s, it rings to here
z = int(round(ZERO * sr)); seg = x[z:z + int(round((END + 0.6) * sr))].copy()
n = len(seg); fade = int(0.6 * sr); seg[n - fade:] *= np.linspace(1, 0, fade)[:, None]
pk = np.abs(seg).max(); seg *= 0.891 / pk
L = lufs(seg[:int(48.0 * sr)], sr)            # (the loudness of the playing part)
wf.write(f'{D}/wm.wav', sr, (np.clip(seg, -1, 1) * 32767).astype(np.int16))
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', f'{D}/wm.wav', '-codec:a', 'libmp3lame', '-q:a', '2', f'{A}/wmmusic.mp3'], check=True)
gain = 10 ** ((-21.0 - (L + BUS)) / 20)
meta['wm'] = {'gain': round(float(gain), 3), 'lufs': round(float(L), 1), 'secs': round(n / sr, 2)}
print('wm', meta['wm'], 'peak raw', round(float(pk), 3), 'bytes', os.path.getsize(f'{A}/wmmusic.mp3'))
# ---- the memory game: a loop
sr, x = wf.read(f'{D}/synapseReverie_raw.wav'); x = x.astype(np.float64) / 32768 * 2
LOOP, PAD = 16 * 4 * 60 / 90, 0.25
n = int(round(LOOP * sr)); r2 = int(round((ZERO + LOOP) * sr)); r3 = r2 + n
d = x[r2:r2 + n] - x[r3:r3 + n]
print('mem round 2 vs 3: rms diff / rms', round(float(np.sqrt(np.mean(d ** 2)) / np.sqrt(np.mean(x[r2:r2 + n] ** 2))), 4))
p = int(round(PAD * sr)); seg = x[r2 - p: r3 + p].copy()
pk = np.abs(seg).max(); seg *= 0.891 / pk
L = lufs(seg[p:p + n], sr)
jump = np.abs(seg[p + n] - seg[p]).max(); step = np.abs(np.diff(seg[p - 200:p + 200], axis=0)).max()
print('mem jump at the loop', round(float(jump), 4), 'vs largest step near it', round(float(step), 4))
wf.write(f'{D}/mem.wav', sr, (np.clip(seg, -1, 1) * 32767).astype(np.int16))
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', f'{D}/mem.wav', '-codec:a', 'libmp3lame', '-q:a', '2', f'{A}/memmusic.mp3'], check=True)
gain = 10 ** ((-25.0 - (L + BUS)) / 20)       # quieter than the other songs: the neurons' bells over it
meta['mem'] = {'gain': round(float(gain), 3), 'loop': [PAD, round(PAD + LOOP, 4)], 'lufs': round(float(L), 1)}
print('mem', meta['mem'], 'bytes', os.path.getsize(f'{A}/memmusic.mp3'))
json.dump(meta, open('/home/claude/work/music_meta.json', 'w'), indent=1)
