# Preview stage 2's looks as the game frames them (eyecheck.py's way): far, mid, ceiling, floor, obstacles, coins, a
# character; a second frame elsewhere without obstacles; a third row: every obstacle of the look on a dark strip.
# usage: python3 s2check.py name [name ...]   (T_<name> from toilet, drains, sewer or plant)  -> scratchpad/s2_<name>.png
import sys, time, importlib
import numpy as np
from PIL import Image
from art import SC, H, to_image
from tiles import WT, GY, FY0
import themes as T
import eyecheck as E

OUTD = E.OUTD
RO = E.RO


def find(name):
    for mod in ('toilet', 'drains', 'sewer', 'plant'):
        try:
            m = importlib.import_module(mod)
        except ModuleNotFoundError:
            continue
        if hasattr(m, 'T_' + name):
            return m, getattr(m, 'T_' + name)
    raise SystemExit('no T_' + name)


def frame(m, th, cam, show_obs=True):
    f = Image.new('RGBA', (int(E.NW * RO), int(H * RO)), (0, 0, 0, 255))
    E.place(f, E.strip(th['far'], cam * 0.35), 0, 0)
    if th.get('mid') is not None:
        E.place(f, E.strip(th['mid'], cam * 0.65), 0, 0)
    o = th['obs']
    if show_obs:
        h = o['hang'][0]; E.place(f, h, 268, 6)
        fl = o['float'][0]; E.place(f, fl, 172, 70)
    if th.get('ceil') is not None:
        E.place(f, E.strip(th['ceil'], cam), 0, 0)
    E.place(f, E.strip(th['floor'], cam), 0, FY0)
    if show_obs:
        lo = o['low'][0]; E.place(f, lo, 118, GY + 2 - lo.shape[0] / SC)
        ta = o['tall'][0]; E.place(f, ta, 222, GY + 2 - ta.shape[0] / SC)
        hu = o['huge'][0]; E.place(f, hu, 330, GY + 2 - hu.shape[0] / SC)
        import toilet as TT
        coin = TT.drop_item()
        for i in range(5):
            E.place(f, coin, 20 + i * 15, GY - 60)
    ch = Image.open('/home/claude/hdart/out/charv2_tardigrade.png')
    w, h = ch.width / 8.0, ch.height / 8.0
    ch = ch.resize((int(w * RO), int(h * RO)), Image.LANCZOS)
    c = Image.new('RGBA', f.size, (0, 0, 0, 0)); c.paste(ch, (int((84 - w / 2) * RO), int((GY - 40 - h) * RO))); f.alpha_composite(c)
    return f


def obs_row(th):
    allo = [s for k in ('low', 'tall', 'hang', 'float', 'huge') for s in th['obs'][k]]
    W = int(sum(s.shape[1] / SC + 8 for s in allo) + 8)
    f = Image.new('RGBA', (int(max(W, E.NW) * RO), int(H * RO)), (40, 46, 50, 255))
    x = 8
    for s in allo:
        E.place(f, s, x, max(2, GY + 2 - s.shape[0] / SC)); x += s.shape[1] / SC + 8
    return f


if __name__ == '__main__':
    for name in sys.argv[1:]:
        t0 = time.time()
        m, fn = find(name)
        th = fn()
        print(name, 'built %.1fs' % (time.time() - t0), {k: [round(s.shape[1] / SC) for s in v] for k, v in th['obs'].items()}, flush=True)
        a = frame(m, th, 300); b = frame(m, 1600, False) if False else frame(m, th, 1600, False); c = obs_row(th)
        out = Image.new('RGB', (max(a.width, c.width), a.height * 3), (0, 0, 0))
        out.paste(a.convert('RGB'), (0, 0)); out.paste(b.convert('RGB'), (0, a.height)); out.paste(c.convert('RGB'), (0, 2 * a.height))
        out.save(f'{OUTD}/s2_{name}.png')
