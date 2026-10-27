# (v45) the toilet jackpot's machine from the user's picture (src/slot_user.png: a toilet slot machine on magenta):
#  * keyed off the magenta (the edge pixels un-mixed from it: alpha from how far they are from magenta toward the
#    nearest solid colour, the colour with the magenta taken out)
#  * the three reel windows cut out (the reels are drawn behind them); the dark rim kept, its inner edge soft
#  * the lever's arm (the red knob and the gold stick above the gold drum) cut off into two pictures of their own (the
#    game swings it down when pulled); the stub in the drum stays
#  * found and handed to the game (manifest M.sl): the windows, the red marquee bar, the bulbs, the three red buttons,
#    the blue light at the foot, the lever's pivot and knob
# The symbols and the coin are minigames2.py's. -> runner_hd/assets/sl.webp + manifest (sl_machine, sl_stick, sl_knob,
# sl_coin, sl_s0..5; M.sl)
import json, sys, os
import numpy as np
from PIL import Image
from scipy import ndimage
sys.path.insert(0, '/home/claude/hdart')
import minigames2 as mg

SRC = '/home/claude/hdart/src/slot_user.png'
OUT, PRE = mg.OUT, '/tmp/claude-0/-home-claude/3a779e8a-891a-5a91-a306-4a5325e0d53e/scratchpad/slu'
H_UNITS = 142.0                       # the machine's height in the game (its feet on the screen's bottom, its top under the HUD)
PPU = 6.0                             # pixels per unit it is kept at (a phone held sideways: 1080 px / 180 units)
K = np.array([253.0, 2.0, 251.0])     # the magenta


def key(im):
    """alpha and colour with the magenta taken out"""
    d = np.sqrt(((im - K) ** 2).sum(-1))
    solid = d > 120
    _, (iy, ix) = ndimage.distance_transform_edt(~solid, return_indices=True)
    F = im[iy, ix]                                            # the nearest solid colour
    FK = F - K
    a = np.clip(((im - K) * FK).sum(-1) / np.maximum((FK ** 2).sum(-1), 1), 0, 1)
    a[solid] = 1; a[d < 30] = 0
    col = K + (im - K) / np.maximum(a, 0.05)[..., None]
    col = np.clip(col, 0, 255)
    col = F + (col - F) * a[..., None]                         # (faint ones: mostly the solid colour)
    col[solid] = im[solid]
    return col, a


def main():
    os.makedirs(PRE, exist_ok=True)
    im = np.array(Image.open(SRC).convert('RGB')).astype(np.float64)
    H, W = im.shape[:2]
    col, a = key(im)
    L = im.mean(-1); chroma = im.max(-1) - im.min(-1)
    info = {}

    # ---- the reel windows: the light grey inside each, filled from its middle, cut out
    light = (L > 82) & (chroma < 85)                         # (all inside the dark rim: the grey and its shadow at the top)
    lab, _ = ndimage.label(light)
    wins = []
    for cx in (462, 768, 1072):
        l = lab[590, cx]; assert l, cx
        hole = lab == l
        hole = ndimage.binary_fill_holes(hole)
        ys, xs = np.where(hole)
        wins.append((hole, xs.min(), xs.max(), ys.min(), ys.max()))
    holes = np.zeros((H, W), bool)
    for h, *_ in wins: holes |= h
    # the rim around: the pixels within 3 px that are between the inside's grey and the dark rim -> dark, part clear
    ring = ndimage.binary_dilation(holes, iterations=3) & ~holes
    Lin = 150.0
    Lout = np.percentile(L[ring], 5)
    darkc = im[ring & (L < Lout + 25)].mean(0)
    f = np.clip((Lin - L) / (Lin - Lout), 0, 1)
    soft = ring & (L > Lout + 25)
    a[holes] = 0
    a[soft] = np.minimum(a[soft], f[soft])
    col[soft] = darkc
    info['wins'] = [[int(x0), int(x1), int(y0), int(y1)] for _, x0, x1, y0, y1 in wins]

    # ---- the lever: the knob (red, a circle fitted to it) and the stick (gold, right of the body, above the drum)
    red = (im[..., 0] > 110) & (im[..., 1] < 95) & (im[..., 2] < 120) & (im[..., 0] > im[..., 1] + 60)
    lab, _ = ndimage.label(red)
    knobm = lab == lab[405, 1365]
    import cv2
    ys, xs = np.where(knobm)
    (cx_, cy_), kr = cv2.minEnclosingCircle(np.stack([xs, ys], 1).astype(np.float32))
    kc = np.array([cx_, cy_])
    yy, xx = np.mgrid[0:H, 0:W]
    fg = a > 0.02
    # its dark outline: out from the red to where the dark ends (measured straight up and right of the middle)
    def edge(dx, dy):
        r = kr
        while fg[int(kc[1] + dy * r), int(kc[0] + dx * r)]: r += 1
        return r
    KR = max(edge(0, -1), edge(1, 0), edge(0.7071, -0.7071)) + 1.5
    kdisk = np.hypot(xx - kc[0], yy - kc[1]) <= KR
    Y_CUT = 552
    # the stick: a band round its line (the line from the clean rows just above the drum)
    axis = []
    for y in range(480, Y_CUT):
        run = np.where(fg[y, 1296:1441])[0]
        segs = np.split(run, np.where(np.diff(run) > 1)[0] + 1)
        s_ = segs[-1] + 1296
        axis.append(((s_[0] + s_[-1]) / 2, y))
    axis = np.array(axis)
    p = np.polyfit(axis[:, 1], axis[:, 0], 1)                  # x = p0*y + p1 along the stick
    piv = np.array([np.polyval(p, Y_CUT), Y_CUT])
    dline = np.abs(xx - np.polyval(p, yy)) / np.sqrt(1 + p[0] ** 2)
    kdisk = np.hypot(xx - kc[0], yy - kc[1]) <= KR + 3
    kdisk2 = np.hypot(xx - kc[0], yy - kc[1]) <= KR + 9          # (its outline is thicker low on the left)
    stick = fg & (dline <= 32) & (yy < Y_CUT) & (yy > kc[1]) & (xx > 1294) & ~kdisk
    arm = ((kdisk2 & fg & (xx > 1291)) | stick) & (yy < Y_CUT)
    # where the knob's outline touched the body's (left of the knob), the body keeps those pixels too
    rest = fg & ~arm
    touch = np.zeros_like(arm)
    info['touch'] = int(touch.sum())
    # the knob's outline touches the body's: the knob gets only what is on its side of the gap line between them
    info['knob'] = [float(kc[0]), float(kc[1]), float(kr), float(KR)]
    info['piv'] = [float(piv[0]), float(piv[1])]
    info['stick_slope'] = float(p[0])

    # ---- the red marquee bar, the three red buttons, the bulbs, the blue light at the foot
    lab, _ = ndimage.label(red)
    red2 = (im[..., 0] > 150) & (im[..., 1] < 70) & (im[..., 2] < 110)
    lab2, _ = ndimage.label(red2)
    mq = ndimage.binary_fill_holes(lab2 == lab2[328, 768])
    ys, xs = np.where(mq); info['marquee'] = [int(xs.min()), int(xs.max()), int(ys.min()), int(ys.max())]
    btns = []
    for cx in (485, 768, 1052):
        l = lab[800, cx]
        if not l:
            cand = np.where(red[760:850, cx - 40:cx + 40]); l = lab[760 + cand[0][0], cx - 40 + cand[1][0]]
        m = lab == l; ys, xs = np.where(m)
        btns.append([int(xs.min()), int(xs.max()), int(ys.min()), int(ys.max())])
    info['btns'] = btns
    bright = (im[..., 0] > 238) & (im[..., 1] > 205) & (im[..., 2] > 120) & (im[..., 2] < im[..., 0] - 15)
    lab, n = ndimage.label(bright)
    bulbs = []
    for i, sl in enumerate(ndimage.find_objects(lab)):
        m = lab[sl] == i + 1; ar = m.sum()
        hh, ww = m.shape
        if 60 <= ar <= 2500 and 0.5 < hh / ww < 2:
            cy_, cx_ = ndimage.center_of_mass(m)
            bulbs.append([float(sl[1].start + cx_), float(sl[0].start + cy_), float(np.sqrt(ar / np.pi)), int(ar)])
    info['bulbs'] = bulbs = [b for b in bulbs if b[2] >= 9.5 and 255 <= b[1] <= 400]
    blue = (im[..., 2] > 200) & (im[..., 0] < 150) & (yy > 880)
    ys, xs = np.where(blue); info['glow'] = [int(xs.min()), int(xs.max()), int(ys.min()), int(ys.max())] if len(xs) else None
    json.dump(info, open(f'{PRE}/info.json', 'w'), indent=1)

    # ---- a look at it all: the cut-outs over grey, the found things marked
    from PIL import ImageDraw
    rgba = np.dstack([col, a * 255]).astype(np.uint8)
    base = Image.new('RGBA', (W, H), (90, 100, 110, 255)); base.alpha_composite(Image.fromarray(rgba))
    dr = ImageDraw.Draw(base)
    for x0, x1, y0, y1 in info['wins']: dr.rectangle((x0, y0, x1, y1), outline=(0, 255, 0, 255), width=2)
    x0, x1, y0, y1 = info['marquee']; dr.rectangle((x0, y0, x1, y1), outline=(0, 255, 255, 255), width=2)
    for x0, x1, y0, y1 in btns: dr.rectangle((x0, y0, x1, y1), outline=(255, 255, 0, 255), width=2)
    for bx, by, br, _ in bulbs: dr.ellipse((bx - br - 3, by - br - 3, bx + br + 3, by + br + 3), outline=(255, 0, 0, 255), width=2)
    dr.ellipse((kc[0] - KR, kc[1] - KR, kc[0] + KR, kc[1] + KR), outline=(0, 0, 255, 255), width=2)
    dr.ellipse((piv[0] - 6, piv[1] - 6, piv[0] + 6, piv[1] + 6), fill=(0, 0, 255, 255))
    if info['glow']: x0, x1, y0, y1 = info['glow']; dr.rectangle((x0, y0, x1, y1), outline=(255, 0, 255, 255), width=2)
    base.save(f'{PRE}/found.png')
    am = np.zeros((H, W, 4), np.uint8); am[arm] = (255, 0, 0, 255)
    b2 = Image.new('RGBA', (W, H), (90, 100, 110, 255)); b2.alpha_composite(Image.fromarray(rgba)); b2.alpha_composite(Image.fromarray(am // 2))
    b2.crop((1150, 280, 1450, 720)).save(f'{PRE}/arm.png')
    np.savez_compressed(f'{PRE}/cut.npz', col=col, a=a, arm=arm, kdisk=kdisk)

    # ---- the pictures, at PPU pixels a unit (the machine H_UNITS tall), the colour pre-multiplied while shrinking
    lab, n = ndimage.label(a > 0.5)                            # (only the machine and its two drops: specks at the border go)
    sizes = ndimage.sum(np.ones_like(a), lab, range(1, n + 1))
    keep = np.isin(lab, 1 + np.where(sizes > 1000)[0])
    keep = ndimage.binary_dilation(keep, iterations=4)
    a[~keep] = 0
    ys, xs = np.where(a > 0.02)
    X0, Y0, X1, Y1 = xs.min(), ys.min(), xs.max() + 1, ys.max() + 1
    U = H_UNITS / (Y1 - Y0)                                    # units a source pixel
    def shrink(c_, a_, box):
        x0, y0, x1, y1 = box
        pm = np.dstack([c_[y0:y1, x0:x1] * a_[y0:y1, x0:x1, None], a_[y0:y1, x0:x1] * 255])
        w = max(1, round((x1 - x0) * U * PPU)); h = max(1, round((y1 - y0) * U * PPU))
        chans = [np.array(Image.fromarray(pm[..., k].astype(np.float32), 'F').resize((w, h), Image.LANCZOS)) for k in range(4)]
        out = np.dstack(chans); al = np.clip(out[..., 3], 0, 255)
        out[..., :3] = np.clip(out[..., :3] / np.maximum(al[..., None] / 255, 1e-3), 0, 255); out[..., 3] = al
        out[al < 1] = 0
        return out, ((x1 - x0) * U, (y1 - y0) * U)
    am = a.copy(); am[arm & ~touch] = 0
    lab, n = ndimage.label(am > 0.03)                          # (crumbs the cut left: gone)
    sizes = ndimage.sum(np.ones_like(am), lab, range(1, n + 1))
    am[np.isin(lab, 1 + np.where(sizes < 400)[0])] = 0
    mach, mwh = shrink(col, am, (X0, Y0, X1, Y1))
    def box_of(m, pad=3):
        ys, xs = np.where(m); return (xs.min() - pad, ys.min() - pad, xs.max() + 1 + pad, ys.max() + 1 + pad)
    knm = arm & (kdisk | (kdisk2 & (dline > 24)))
    stm = arm & ~knm; sb = box_of(stm)
    a_st = np.where(stm, a, 0); stick, swh = shrink(col, a_st, sb)
    kb = box_of(knm)
    a_kn = np.where(knm, a, 0); knob, kwh = shrink(col, a_kn, kb)
    u = lambda x, y: [round((x - X0) * U, 3), round((y - Y0) * U, 3)]
    meta = {
        'wins': [[*u(x0, y0), *u(x1 + 1, y1 + 1)] for x0, x1, y0, y1 in info['wins']],
        'winr': round(16 * U, 3),
        'marquee': [*u((info['marquee'][0] + info['marquee'][1]) / 2, (info['marquee'][2] + info['marquee'][3]) / 2), round((info['marquee'][1] - info['marquee'][0]) * U, 3), round((info['marquee'][3] - info['marquee'][2]) * U, 3)],
        'bulbs': [[*u(bx, by), round(br * U, 3)] for bx, by, br, _ in sorted(bulbs, key=lambda b: (b[1] > 330, b[0] if b[1] < 330 else -b[0]))],
        'btns': [[*u((x0 + x1) / 2, (y0 + y1) / 2), round((x1 - x0) / 2 * U, 3), round((y1 - y0) / 2 * U, 3)] for x0, x1, y0, y1 in btns],
        'glow': [*u((info['glow'][0] + info['glow'][1]) / 2, (info['glow'][2] + info['glow'][3]) / 2), round((info['glow'][1] - info['glow'][0]) / 2 * U, 3), round((info['glow'][3] - info['glow'][2]) / 2 * U, 3)],
        'piv': u(*piv), 'knob': [*u(*kc), round(KR * U, 3)],
        'stick_piv': [round((piv[0] - sb[0]) * U, 3), round((piv[1] - sb[1]) * U, 3)],
        'knob_c': [round((kc[0] - kb[0]) * U, 3), round((kc[1] - kb[1]) * U, 3)],
        'stick_w': round(40 * U, 3),
    }
    # ---- the atlas: the machine on the left, the rest in rows beside it
    parts = [('sl_machine', mach, mwh, {}), ('sl_stick', stick, swh, {}), ('sl_knob', knob, kwh, {})]
    def thick(s_, r=3):                                        # the symbols: a thicker dark outline, like the machine's
        al = s_[..., 3] / 255
        yy_, xx_ = np.mgrid[-r:r + 1, -r:r + 1]
        ring = ndimage.binary_dilation(al > 0.4, structure=(np.hypot(yy_, xx_) <= r))
        soft = ndimage.gaussian_filter(ring.astype(np.float32), 0.8)
        base = np.zeros_like(s_); base[..., :3] = (40, 16, 22); base[..., 3] = soft * 255
        out = base.copy(); fa = al[..., None]
        out[..., :3] = s_[..., :3] * fa + base[..., :3] * (1 - fa)
        out[..., 3] = np.maximum(s_[..., 3], base[..., 3])
        return out
    import symbols_hd as sh                                    # (v45: the symbols and coin redrawn, glossy)
    syms = [(f'sl_s{k}', (f(), {})) for k, f in enumerate(sh.SYMS)]
    for nm, (s_, m_) in [('sl_coin', (sh.coin(), {}))] + syms:
        parts.append((nm, s_, (s_.shape[1] / mg.SC, s_.shape[0] / mg.SC), m_))
    X = mach.shape[1] + 4; x, y, rowh, Wmax = X, 0, 0, 0
    pos = [(0, 0)]
    for nm, s_, wh, _ in parts[1:]:
        if x + s_.shape[1] > X + 640: x, y, rowh = X, y + rowh + 4, 0
        pos.append((x, y)); x += s_.shape[1] + 4; rowh = max(rowh, s_.shape[0]); Wmax = max(Wmax, x)
    AH = max(mach.shape[0], y + rowh)
    A = np.zeros((AH, Wmax, 4), np.float32)
    m = json.load(open(f'{OUT}/manifest.json'))
    for k in ('sl_lever0', 'sl_lever1'): m['sprites'].pop(k, None)
    for (nm, s_, wh, mm), (px_, py_) in zip(parts, pos):
        A[py_:py_ + s_.shape[0], px_:px_ + s_.shape[1]] = s_
        m['sprites'][nm] = {'f': 'sl.webp', 'r': [px_, py_, s_.shape[1], s_.shape[0]], 'w': round(wh[0], 3), 'h': round(wh[1], 3), **mm}
    m['sl'] = meta
    Image.fromarray(np.clip(A, 0, 255).astype(np.uint8), 'RGBA').save(f'{OUT}/sl.webp', quality=92, alpha_quality=100, method=6)
    Image.fromarray(np.clip(A, 0, 255).astype(np.uint8), 'RGBA').save(f'{PRE}/sl_atlas.png')
    json.dump(m, open(f'{OUT}/manifest.json', 'w'), separators=(',', ':'))
    print('sl.webp', os.path.getsize(f'{OUT}/sl.webp'), A.shape, 'machine units', [round(v, 2) for v in mwh])
    print(json.dumps(meta))
    print(json.dumps({k: v for k, v in info.items() if k != 'bulbs'}), 'bulbs', len(bulbs))


if __name__ == '__main__':
    main()
