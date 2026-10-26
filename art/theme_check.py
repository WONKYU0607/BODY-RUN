# Compose a wide view of a theme across its tile seam (to check seams and the look), obstacles laid on top.
import sys, time
import numpy as np
from art import H, canvas, paste, to_image, fill_rect
from tiles import WT, GY, FY0
import themes as T

def view(th, cam, w=780):
    out = canvas(w, H)
    for key, par, y0 in (('far', 0.35, 0), ('mid', 0.65, 0), ('ceil', 1.0, 0), ('floor', 1.0, FY0)):
        L = th.get(key)
        if L is None: continue
        off = (cam * par) % WT
        x = -off
        while x < w:
            paste(out, L, x, y0); x += WT
    return out

if __name__ == '__main__':
    names = sys.argv[1:]
    rows = []
    for n in names:
        t0 = time.time(); th = getattr(T, 'T_' + n)(); dt = time.time() - t0
        v = view(th, WT - 390)                     # the seam of the floor in the middle
        x = 20
        for kind in ('low', 'tall', 'hang', 'float'):
            for s in th['obs'][kind][:2]:
                if kind == 'hang': paste(v, s, x, 12)
                elif kind == 'float': paste(v, s, x, GY - 24 - s.shape[0])
                else: paste(v, s, x, GY + 2 - s.shape[0])
                x += s.shape[1] + 30
        rows.append(v); print(n, 'built in %.1fs' % dt, {k: len(v) for k, v in th['obs'].items()})
    out = canvas(780, H * len(rows))
    for i, r in enumerate(rows): paste(out, r, 0, i * H)
    to_image(out, 2).convert('RGB').save('/tmp/claude-0/-home-claude/3a779e8a-891a-5a91-a306-4a5325e0d53e/scratchpad/themes_' + '_'.join(names) + '.png')
