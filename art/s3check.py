# Stage 3's places composed the way the game shows them (far, mid, ceiling, floor; things in the way laid along it), a
# frame each, stacked into one sheet (to judge the look). python3 s3check.py river riffle ... [-o out.png]
import sys, time, importlib
import numpy as np
from PIL import Image
from art import H, SC, canvas, paste, to_image
from tiles import WT, GY, FY0
from themes import hang_len

def view(th, cam, w=456):
    out = canvas(w, H)
    for key, par, y0 in (('far', 0.35, 0), ('mid', 0.65, 0), ('ceil', 1.0, 0), ('floor', 1.0, FY0)):
        Ly = th.get(key)
        if Ly is None: continue
        off = (cam * par) % WT
        x = -off
        while x < w:
            paste(out, Ly, x, y0); x += WT
    return out

def find(name):
    for mod in ('river', 'sea'):
        try:
            m = importlib.import_module(mod)
        except ModuleNotFoundError:
            continue
        f = getattr(m, 'T_' + name, None)
        if f: return f
    raise SystemExit('no ' + name)

if __name__ == '__main__':
    args = sys.argv[1:]
    outp = '/tmp/claude-0/-home-claude/3a779e8a-891a-5a91-a306-4a5325e0d53e/scratchpad/s3check.png'
    if '-o' in args:
        i = args.index('-o'); outp = args[i + 1]; args = args[:i] + args[i + 2:]
    frames = []
    for n in args:
        t0 = time.time(); th = find(n)(); dt = time.time() - t0
        v = view(th, 300)
        x = 30
        for kind in ('low', 'tall', 'hang', 'float', 'huge'):
            for s in th['obs'][kind][:2 if kind != 'huge' else 1]:
                w = s.shape[1] / SC
                if kind == 'hang': paste(v, s, x, 6)
                elif kind == 'float': paste(v, s, x, GY - 40 - s.shape[0] / SC)
                else: paste(v, s, x, GY + 2 - s.shape[0] / SC)
                x += w + 10
        im = to_image(v).resize((912, 360), Image.LANCZOS)
        frames.append(im)
        print(n, '%.1fs' % dt, flush=True)
    sheet = Image.new('RGB', (912, 360 * len(frames)))
    for i, f in enumerate(frames): sheet.paste(f, (0, 360 * i))
    sheet.save(outp)
    print('saved', outp)
