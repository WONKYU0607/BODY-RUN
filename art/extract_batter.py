# The batter views (the user's six sheets: front, back, front-right, right side, back-right, back-left; ten characters
# each, magenta ground): key out the magenta (each sheet's own ground colour, it is not quite even), unmix the dark
# outline's fringe into dark pixels with partial alpha, drop the sheet's drop shadows and loose specks, cut out each
# character at full resolution.
import json, sys
import numpy as np
from PIL import Image
from scipy import ndimage

# --hd: the sheets made twice as big by Real-ESRGAN (esr_batter.py), into out/batter_hd
HD = '--hd' in sys.argv
S = 2 if HD else 1                                            # the sheets' scale
SRC = '/home/claude/hdart/src/batter' + ('/hd' if HD else '')
OUT = '/home/claude/hdart/out/batter' + ('_hd' if HD else '')
NAMES = ['tardigrade', 'lacto', 'paramecium', 'amoeba', 'daphnia', 'pillbug', 'ladybug', 'jelly', 'sub', 'phage']
SHEETS = [('0', '35a40568'), ('180', '8fb8304d'), ('45', '88a1aad1'), ('90', '4e19342b'), ('135', '48ecfe0d'), ('225', '6e07a842')]
D = np.array([16, 6, 18], np.float32)                         # the outline colour
info = {}
for view, fn in SHEETS:
    a = np.array(Image.open(f'{SRC}/{fn}-image.png').convert('RGB')).astype(np.float32)
    import os; os.makedirs(OUT, exist_ok=True)
    H, W = a.shape[:2]
    edge = np.concatenate([a[:6].reshape(-1, 3), a[-6:].reshape(-1, 3), a[:, :6].reshape(-1, 3), a[:, -6:].reshape(-1, 3)])
    key = np.median(edge, 0)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    dist = np.sqrt(((a - key) ** 2).sum(2))
    bg = dist < 48
    magentaish = (g < 45) & (np.abs(r - b) < 45) & (np.minimum(r, b) - g > 18)
    # the drop shadow: a dark crimson-magenta (red over blue, no green), unlike any of the characters' own darks
    shadow = (g < 16) & (r > 50) & (b > 0.35 * r) & (b < 1.15 * r) & ~bg
    # what is ground (or shadow) and joins the ground round the sheet's edge is outside; ground-coloured parts the
    # character closes round (the amoeba's pink foot) are its own and stay
    T = bg | shadow | magentaish
    labT, nT = ndimage.label(T)
    border = set(np.unique(np.concatenate([labT[0], labT[-1], labT[:, 0], labT[:, -1]]))) - {0}
    outside = np.isin(labT, list(border))
    hole = T & ~outside
    hole = hole & ~ndimage.binary_dilation(outside, iterations=S)
    bg = bg & outside; magentaish = magentaish & outside; shadow = shadow & outside
    solid = (~bg & ~magentaish & ~shadow) | hole
    solid = ndimage.binary_opening(solid, iterations=S)
    near_solid = ndimage.binary_dilation(solid, iterations=2 * S)
    fringe = magentaish & ~bg & near_solid & ~ndimage.binary_dilation(shadow, iterations=S)
    KD = key - D
    t = ((a - D) * KD).sum(2) / (KD * KD).sum()
    alpha = np.zeros((H, W), np.float32)
    alpha[solid] = 1
    alpha[fringe] = np.clip(1 - t[fringe], 0, 1)
    rgb = a.copy(); rgb[fringe] = D
    # pinkish-light halo next to the ground (the picture's glow round the outline): blend it out like the fringe
    halo = solid & ndimage.binary_dilation(bg, iterations=2 * S) & (g < 120) & (r > 170) & (b > 170)
    alpha[halo] = 0
    fg = alpha > 0.5
    lab, n = ndimage.label(fg)
    sizes = ndimage.sum(fg, lab, range(1, n + 1))
    comps = [i + 1 for i in range(n) if sizes[i] > 300 * S * S]
    boxes = []
    for i in comps:
        sl = ndimage.find_objects((lab == i).astype(int))[0]
        boxes.append([sl[0].start, sl[0].stop, sl[1].start, sl[1].stop])
    # group into the 2 x 5 cells
    cells = {}
    for (y0, y1, x0, x1) in boxes:
        cy, cx = (y0 + y1) / 2, (x0 + x1) / 2
        k = (0 if cy < H / 2 else 1) * 5 + min(4, int(cx / (W / 5)))
        c = cells.setdefault(k, [y0, y1, x0, x1])
        cells[k] = [min(c[0], y0), max(c[1], y1), min(c[2], x0), max(c[3], x1)]
    for k, name in enumerate(NAMES):
        y0, y1, x0, x1 = cells[k]
        y0 -= 3 * S; x0 -= 3 * S; y1 += 3 * S; x1 += 3 * S
        al = alpha[y0:y1, x0:x1].copy()
        lab2, n2 = ndimage.label(al > 0.02)
        if n2 > 1:                                            # only what hangs together with the character
            sz = ndimage.sum(al > 0.02, lab2, range(1, n2 + 1))
            big = np.argmax(sz) + 1
            keep = np.isin(lab2, [i + 1 for i in range(n2) if sz[i] > 0.02 * sz.max()])
            al *= keep
        # the picture's soft magenta glow round the outside of the dark outline: eaten from the ground inwards, through
        # magenta-tinted light pixels only, so it stops at the outline (a few pixels at most where there is none)
        px0 = rgb[y0:y1, x0:x1]
        rr, gg, bb = px0[..., 0], px0[..., 1], px0[..., 2]
        dark = (rr + gg + bb) / 3 < 75
        tinted = (rr - gg > 50) & (bb - gg > 50) & (np.minimum(rr, bb) > 100) & (gg < 0.45 * np.minimum(rr, bb)) & ~dark   # (not the pinks)
        grow = al < 0.05
        for _ in range(3 * S):
            grow = grow | (ndimage.binary_dilation(grow) & tinted)
        eaten = grow & (al >= 0.05)
        al[eaten] = 0
        edge = ndimage.binary_dilation(grow) & ~grow & (al > 0) & ~dark      # the new rim: a little see-through
        al[edge] *= 0.55
        ys, xs = np.nonzero(al > 0.05)
        al = al[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
        px = rgb[y0 + ys.min():y0 + ys.max() + 1, x0 + xs.min():x0 + xs.max() + 1]
        out = np.zeros(al.shape + (4,), np.uint8)
        out[..., :3] = np.clip(px, 0, 255).astype(np.uint8)
        out[..., 3] = np.clip(al * 255, 0, 255).astype(np.uint8)
        out[al == 0, :3] = 0
        Image.fromarray(out).save(f'{OUT}/{name}_{view}.png')
        # where it stands: the middle of the feet (the bottom fifth of what is solid)
        A = al > 0.5; hh = A.shape[0]
        fy = np.nonzero(A[int(hh * 0.8):].any(1))[0]
        cols = np.nonzero(A[int(hh * 0.8):].any(0))[0]
        info[f'{name}_{view}'] = {'w': int(A.shape[1]), 'h': int(hh), 'foot': [float((cols.min() + cols.max()) / 2), float(hh)], 'box': [int(y0), int(y1), int(x0), int(x1)]}
    print(view, 'key', key.round(), 'cells', len(cells))
json.dump(info, open(f'{OUT}/info.json', 'w'), indent=0)
