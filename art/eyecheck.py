# Preview themes as the game would frame them: far (slow), mid, ceiling, floor, the obstacles, coins, a character.
# usage: python3 eyecheck.py name [name ...]   -> scratchpad/eye_<name>.png (and the obstacles alone)
import sys, time
import numpy as np
from PIL import Image
from art import SC, H, to_image
import sprites as S
from tiles import WT, GY, FY0
import themes as T

OUTD = '/tmp/claude-0/-home-claude/3a779e8a-891a-5a91-a306-4a5325e0d53e/scratchpad'
RO = 4.0                      # output px per unit
NW = 390


def img(a):
    return to_image(a)


def place(frame, arr, x, y, scale=RO / SC):
    i = img(arr)
    i = i.resize((max(1, int(round(i.width * scale))), max(1, int(round(i.height * scale)))), Image.LANCZOS)
    c = Image.new('RGBA', frame.size, (0, 0, 0, 0)); c.paste(i, (int(round(x * RO)), int(round(y * RO)))); frame.alpha_composite(c)


def strip(arr, off):
    """a NW-wide window of a WT-wide wrapping layer starting at off"""
    a = np.concatenate([arr, arr], axis=1)
    o = int(round((off % WT) * SC))
    return a[:, o:o + int((NW + 2) * SC)]


def frame(th, cam, show_obs=True):
    f = Image.new('RGBA', (int(NW * RO), int(H * RO)), (0, 0, 0, 255))
    place(f, strip(th['far'], cam * 0.35), 0, 0)
    if th.get('mid') is not None:
        place(f, strip(th['mid'], cam * 0.65), 0, 0)
    o = th['obs']
    if show_obs:
        if o.get('hang'):
            h = o['hang'][0]; place(f, h, 268, 6)
        if o.get('float'):
            fl = o['float'][0]; place(f, fl, 172, GY - 15.5 - fl.shape[0] / SC)
    if th.get('ceil') is not None:
        place(f, strip(th['ceil'], cam), 0, 0)
    place(f, strip(th['floor'], cam), 0, FY0)
    if show_obs:
        lo = o['low'][0]; place(f, lo, 118, GY + 2 - lo.shape[0] / SC)
        ta = o['tall'][0]; place(f, ta, 222, GY + 2 - ta.shape[0] / SC)
        hu = o['huge'][0]; place(f, hu, 330, GY + 2 - hu.shape[0] / SC)
        coin = {'o2': S.bubble_o2(), 'vitC': S.coin_c()}[th['coin']]
        for i in range(5):
            place(f, coin, 20 + i * 15, GY - 40)
    ch = Image.open('/home/claude/hdart/out/charv2_tardigrade.png')
    w, h = ch.width / 8.0, ch.height / 8.0
    ch = ch.resize((int(w * RO), int(h * RO)), Image.LANCZOS)
    c = Image.new('RGBA', f.size, (0, 0, 0, 0)); c.paste(ch, (int((84 - w / 2) * RO), int((GY + 1 - h) * RO))); f.alpha_composite(c)
    return f


if __name__ == '__main__':
    for name in sys.argv[1:]:
        t0 = time.time()
        import variants as V
        th = (getattr(T, 'T_' + name, None) or getattr(V, 'T_' + name))()
        print(name, 'built %.1fs' % (time.time() - t0), {k: [s.shape[1] // SC for s in v] for k, v in th['obs'].items()}, flush=True)
        a = frame(th, 300); b = frame(th, 1600, False)
        out = Image.new('RGB', (a.width, a.height * 2))
        out.paste(a.convert('RGB'), (0, 0)); out.paste(b.convert('RGB'), (0, a.height))
        out.save(f'{OUTD}/eye_{name}.png')
