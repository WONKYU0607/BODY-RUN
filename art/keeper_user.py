# (v45) the penalty shoot-out's keeper from the user's pictures (a mouse in a yellow jersey and big white gloves, on magenta):
#  * src/keeper_ready.png: the ready pose (front on, gloves up)
#  * src/keeper_dive.png: two rows of six: diving to the right (top) and to the left (bottom): standing, crouching,
#    leaping, stretched out (glove out), stretched lower, down on the ground
# Keyed off the magenta: everything outside the dark outline that is magenta-ish is the background; there the pixels are
# un-mixed as a grey over magenta (the outline's black fringe and the white puffs' edge keep their part; the purple
# shadows on the floor go: the game draws its own); per frame only the mouse (the biggest piece: the dust puffs go).
# Each frame's middle (alpha-weighted), its bottom, and its leading glove (the white furthest the way it dives) go to
# the manifest. -> runner_hd/assets/pk.webp (with minigames2's ball) + manifest (pk_k0, pk_dR1..6, pk_dL1..6)
import json, sys, os
import numpy as np
from PIL import Image
from scipy import ndimage
sys.path.insert(0, '/home/claude/hdart')
import minigames2 as mg

OUT, PRE = mg.OUT, '/tmp/claude-0/-home-claude/3a779e8a-891a-5a91-a306-4a5325e0d53e/scratchpad/kpu'
KH = 44.0                      # the keeper standing, ears to feet, in game units
PPU = 6.0


def key(im):
    R, G, B = im[..., 0], im[..., 1], im[..., 2]
    mgish = (R - G > 55) & (B - G > 55) & (np.abs(R - B) < 60)          # (strongly: the mouse's lavender is a little magenta too)
    lab, n = ndimage.label(mgish)
    border = np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))
    outside = np.isin(lab, border[border > 0])
    a = np.ones(R.shape)
    av = 1 - ((R - G) + (B - G)) / (2 * 249.0)
    a[outside] = np.clip(av[outside], 0, 1)
    col = im.copy()
    f = np.clip(G / np.maximum(a, 0.04), 0, 255)
    col[outside] = np.stack([f, f, f], -1)[outside]
    # the shadows on the floor: dark, and away from the mouse -> gone
    solid = ~outside
    dist = ndimage.distance_transform_edt(~solid)
    a[outside & (f < 90) & (dist > 3)] = 0
    a[outside & (dist > 3) & (a < 0.5)] = 0
    return col, a


def pieces(a, thr=0.5):
    lab, n = ndimage.label(a > thr)
    sizes = ndimage.sum(np.ones_like(a), lab, range(1, n + 1))
    return lab, sizes


def frame(col, a, box, keep_largest=True):
    x0, y0, x1, y1 = box
    c, al = col[y0:y1, x0:x1].copy(), a[y0:y1, x0:x1].copy()
    if keep_largest:
        lab, sizes = pieces(al)
        big = 1 + int(np.argmax(sizes))
        m = ndimage.binary_dilation(lab == big, iterations=3)
        al[~m] = 0
    ys, xs = np.where(al > 0.02)
    X0, Y0, X1, Y1 = max(0, xs.min() - 2), max(0, ys.min() - 2), xs.max() + 3, ys.max() + 3
    return c[Y0:Y1, X0:X1], al[Y0:Y1, X0:X1]


def measure(c, al, dirx):
    """the middle, the bottom, the leading glove (the white furthest in dirx; both gloves for 0)"""
    ys, xs = np.mgrid[0:al.shape[0], 0:al.shape[1]]
    w = al
    cx, cy = (xs * w).sum() / w.sum(), (ys * w).sum() / w.sum()
    bottom = ys[al > 0.5].max()
    top = ys[al > 0.5].min()
    white = (c.min(-1) > 205) & (al > 0.9) & (c.max(-1) - c.min(-1) < 40)
    lab, n = ndimage.label(white)
    sizes = ndimage.sum(np.ones_like(al), lab, range(1, n + 1))
    gl = [i + 1 for i in np.argsort(-sizes)[:2] if sizes[i] > 60]
    hands = []
    for l in gl:
        yy, xx = np.where(lab == l)
        hands.append([float(xx.mean()), float(yy.mean()), float(xx.min()), float(xx.max()), float(yy.min())])
    if dirx:
        hands.sort(key=lambda h: -h[0] * dirx)
        h = hands[0]
        lead = [h[3] if dirx > 0 else h[2], h[1]]
    else:
        hands.sort(key=lambda h: h[0]); lead = None
    return {'c': [float(cx), float(cy)], 'bottom': float(bottom), 'top': float(top), 'hands': hands, 'lead': lead}


def shrink(c, al, s):
    pm = np.dstack([c * al[..., None], al * 255])
    w, h = max(1, round(c.shape[1] * s)), max(1, round(c.shape[0] * s))
    ch = [np.array(Image.fromarray(pm[..., k].astype(np.float32), 'F').resize((w, h), Image.LANCZOS)) for k in range(4)]
    out = np.dstack(ch); A = np.clip(out[..., 3], 0, 255)
    out[..., :3] = np.clip(out[..., :3] / np.maximum(A[..., None] / 255, 1e-3), 0, 255); out[..., 3] = A
    out[A < 1] = 0
    return out


def main():
    os.makedirs(PRE, exist_ok=True)
    sprites = []                                   # (name, rgba at PPU, units per px of it, meta in units)
    # ---- the ready pose
    im = np.array(Image.open('/home/claude/hdart/src/keeper_ready.png').convert('RGB')).astype(np.float64)
    col, a = key(im)
    H, W = a.shape
    c, al = frame(col, a, (0, 0, W, H))
    m = measure(c, al, 0)
    hpx = m['bottom'] - m['top']
    U = KH / hpx                                   # units a source pixel
    sprites.append(('pk_k0', c, al, U, m))
    # ---- the dive frames: the pieces of the sheet, row (y) and column (x) by where they sit
    im = np.array(Image.open('/home/claude/hdart/src/keeper_dive.png').convert('RGB')).astype(np.float64)
    col, a = key(im)
    H, W = a.shape
    lab, sizes = pieces(a)
    boxes = []
    for i, sl in enumerate(ndimage.find_objects(lab)):
        if sizes[i] < 8000: continue
        boxes.append((sl[1].start, sl[0].start, sl[1].stop, sl[0].stop))
    assert len(boxes) == 12, len(boxes)
    rows = sorted(boxes, key=lambda b: b[1])
    top_row = sorted([b for b in boxes if (b[1] + b[3]) / 2 < H / 2], key=lambda b: b[0])
    bot_row = sorted([b for b in boxes if (b[1] + b[3]) / 2 >= H / 2], key=lambda b: b[0])
    # (the scale: the standing frame, ears to feet, KH tall)
    c1, al1 = frame(col, a, (top_row[0][0] - 6, top_row[0][1] - 6, top_row[0][2] + 6, top_row[0][3] + 6))
    m1 = measure(c1, al1, 1)
    U2 = KH * 0.96 / (m1['bottom'] - m1['top'])       # (the sheet's standing pose is a touch less tall than the ready one)
    for row, d, tag in ((top_row, 1, 'R'), (bot_row, -1, 'L')):
        for k, (x0, y0, x1, y1) in enumerate(row):
            pad = 40
            c_, al_ = frame(col, a, (max(0, x0 - pad), max(0, y0 - pad), min(W, x1 + pad), min(H, y1 + pad)))
            sprites.append((f'pk_d{tag}{k + 1}', c_, al_, U2, measure(c_, al_, d)))
    # ---- to the atlas (the ball first), the meta in units
    import symbols_hd as sh                                    # (v45: the ball redrawn: panels on a lit sphere)
    b_ = sh.ball()
    parts = [('pk_ball', b_, (24.0, 24.0), {'c': [12.0, 12.0]})]
    for nm, c_, al_, U_, m_ in sprites:
        s = U_ * PPU
        img = shrink(c_, al_, s)
        u = lambda p: [round(p[0] * U_, 3), round(p[1] * U_, 3)]
        meta = {'c': u(m_['c']), 'bottom': round(m_['bottom'] * U_, 3), 'top': round(m_['top'] * U_, 3),
                'hands': [[round(h[0] * U_, 3), round(h[1] * U_, 3), round(h[4] * U_, 3)] for h in m_['hands']]}
        if m_['lead']: meta['lead'] = u(m_['lead'])
        parts.append((nm, img, (c_.shape[1] * U_, c_.shape[0] * U_), meta))
    # shelf packing
    x = y = rowh = 0; Wmax = 1400; pos = []; AW = 0
    for nm, img, wh, meta in parts:
        if x + img.shape[1] > Wmax: x, y, rowh = 0, y + rowh + 4, 0
        pos.append((x, y)); x += img.shape[1] + 4; rowh = max(rowh, img.shape[0]); AW = max(AW, x)
    AH = y + rowh
    A = np.zeros((AH, AW, 4), np.float32)
    mf = json.load(open(f'{OUT}/manifest.json'))
    for k in ('pk_k1', 'pk_k2'): mf['sprites'].pop(k, None)
    for (nm, img, wh, meta), (px_, py_) in zip(parts, pos):
        A[py_:py_ + img.shape[0], px_:px_ + img.shape[1]] = img
        mf['sprites'][nm] = {'f': 'pk.webp', 'r': [px_, py_, img.shape[1], img.shape[0]], 'w': round(wh[0], 3), 'h': round(wh[1], 3), **meta}
    Image.fromarray(np.clip(A, 0, 255).astype(np.uint8), 'RGBA').save(f'{OUT}/pk.webp', quality=92, alpha_quality=100, method=6)
    Image.fromarray(np.clip(A, 0, 255).astype(np.uint8), 'RGBA').save(f'{PRE}/pk_atlas.png')
    json.dump(mf, open(f'{OUT}/manifest.json', 'w'), separators=(',', ':'))
    print('pk.webp', os.path.getsize(f'{OUT}/pk.webp'), A.shape)
    for nm, img, wh, meta in parts[1:]: print(nm, [round(v, 1) for v in wh], json.dumps(meta))


if __name__ == '__main__':
    main()
