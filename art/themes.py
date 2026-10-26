# The places of the course as tileable HD layers (see tiles.py), with the obstacles found there. Same designs and
# layout (world units) as the pixel version; drawn smooth, anti-aliased and with finer detail.
import numpy as np
from scipy import ndimage
from art import (H, SC, OUTW, px, grid, canvas, ramp, ramp_col, hexc, paint, ellipse_mask, outline, paste, fill_rect,
                 vgrad, over, wgrad, blur, inner, disc, ellipse_soft, dome_shade, highlight, smooth_mask)
import sprites as S
import anatomy as A
from tiles import (WT, GY, FH, FY0, CH, TAU, wide, crop, tile3, put, per_sin, gradient, haze, pcells, seeds, wall, spots,
                   band_line)

RS = np.random.RandomState


def aa_cov(f, thr, wrap=False):
    """anti-aliased coverage of f >= thr"""
    gy, gx = wgrad(f, wrap)
    g = np.sqrt(gx * gx + gy * gy) + 1e-4
    return np.clip((f - thr) / g + 0.5, 0, 1)


def ring_out(m, width=OUTW):
    """anti-aliased outline band just outside a hard mask (no wrap)"""
    d = ndimage.distance_transform_edt(~m) / SC
    return np.clip((width - d) * SC + 0.5, 0, 1) * (~m)


def ring_out_wrap(m, width=OUTW):
    m3 = np.concatenate([m, m, m], axis=1)
    r = ring_out(m3, width)
    w = m.shape[1]
    return r[:, w:2 * w]


def blend(dst, rgb, k):
    """dst[..., :3] toward rgb by k (h, w)"""
    dst[..., :3] = dst[..., :3] * (1 - k[..., None]) + rgb * k[..., None]


def rows(y0):
    return px(y0)


# ------------------------------------------------------------------ red cells
def rbc(d, tilt=1.0, dark=False):
    """a red blood cell: a disc with a dimple, seen at some tilt"""
    w, h = d, max(3, int(round(d * tilt)))
    m = ellipse_mask(w, h)
    sh, n = dome_shade(m, (-0.55, -0.7, 0.45), soft=1.0, ambient=0.3)
    y, x = grid(h, w)
    r = np.sqrt(((x - (w - 1) / 2) / (w / 2)) ** 2 + ((y - (h - 1) / 2) / (h / 2)) ** 2)
    sh = np.clip(sh - 0.45 * np.clip(1 - r / 0.55, 0, 1) ** 0.8 + 0.12 * np.clip(1 - np.abs(r - 0.68) / 0.12, 0, 1), 0, 1)
    rm = ramp('#5a0610', '#9a0e1e', '#d42232', '#ff5260', '#ff9aa0', n=6) if not dark else ramp('#3a0610', '#5a0c18', '#7a1422', '#962030', n=4)
    spr = paint(m, rm, sh)
    if not dark:
        spr = highlight(spr, m, n, (-0.55, -0.7, 0.45), '#ffd0d4', 0.97)
    return outline(spr, '#2a0208' if not dark else '#24040a', width=0.6)


# ------------------------------------------------------------------ shared far-layer structures (periodic)
def folds(far, y0, y1, seed, cols, out, pit_col, n=7, kmin=2, kmax=6, thick=(5, 10), glaze='#ffe8ee', longitudinal=False):
    """soft folds running along the far wall (stomach rugae, oesophageal folds): merging and parting, dotted with
    pits, glazed with mucus. Whole numbers of waves across the tile"""
    R = RS(seed)
    h = y1 - y0
    y, x = grid(h, WT)
    field = np.zeros(y.shape, np.float32)
    for k in range(n):
        yc = R.uniform(0, h); amp = R.uniform(2, 8) * (0.4 if longitudinal else 1.0)
        kk = R.randint(kmin, kmax + 1); ph = R.uniform(0, 6); th = R.uniform(*thick)
        c = yc + amp * per_sin(x, kk, ph) + amp * 0.5 * per_sin(x, kk * 2 + 1, ph * 2)
        field = np.maximum(field, np.clip(1 - ((y - c) / th) ** 2, 0, 1))
    cov = aa_cov(field, 0.12, wrap=True)
    gy, gx = wgrad(blur(field, 1.2, wrap=True), wrap=True)
    gy *= SC; gx *= SC
    lit = np.clip(0.55 + 2.2 * (-0.6 * gx - 0.8 * gy) + 0.35 * field, 0, 1)
    rgb = ramp_col(cols, lit)
    crease = np.clip((0.3 - field) / 0.12, 0, 1) * 0.4
    rgb *= (1 - crease[..., None])
    if pit_col:
        row = np.round(y / 3.0)
        ci = np.round((x + row * 1.7) / 5.0)
        hsh = lambda a, b, s: np.mod(np.sin(a * 12.9898 + np.mod(b, WT / 5) * 78.233 + s) * 43758.5453, 1.0)
        cx = ci * 5.0 - row * 1.7 + (hsh(row, ci, 0.0) - 0.5) * 1.8
        cy = row * 3.0 + (hsh(row, ci, 1.7) - 0.5) * 1.0
        rad = 0.32 + 0.22 * hsh(row, ci, 3.1)
        pit = np.clip((rad - np.sqrt((x - cx) ** 2 + ((y - cy) * 1.25) ** 2)) * SC + 0.5, 0, 1) * np.clip((field - 0.35) / 0.08, 0, 1) * 0.8
        rgb = rgb * (1 - pit[..., None]) + hexc(pit_col) * pit[..., None]
    nz = ndimage.gaussian_filter(R.uniform(-1, 1, y.shape).astype(np.float32), (0.7 * SC, 6 * SC), mode=('reflect', 'wrap'))
    nz /= max(nz.std(), 1e-6)
    g = np.clip((lit - 0.8) / 0.12, 0, 1) * np.clip(0.45 + 0.45 * nz, 0, 1) * 0.6
    rgb = rgb * (1 - g[..., None]) + hexc(glaze) * g[..., None]
    reg = far[rows(y0):rows(y0) + y.shape[0]]
    over(reg, rgb, cov[:reg.shape[0]])


def drift(c3, n, cols, seed, y0=18, y1=GY - 6, a=200):
    R = RS(seed)
    for k in range(n):
        x, y = R.uniform(0, WT), R.uniform(y0, y1)
        r = R.uniform(0.45, 0.75)
        for off in (0, WT, 2 * WT):
            ellipse_soft(c3, x + off + 0.6, y, r * 1.5, r, cols[k % len(cols)], a // 2)
            disc(c3, x + off, y, r, cols[k % len(cols)], a)


def ridge_field_sprite(field, cols, out, wrap=True, base=0.45, gain=2.0, fk=0.4, stri=True, glaze='#ffd0d8'):
    """shade a ridge field (muscle columns etc.) -> rgb, coverage, outline coverage"""
    m = field > 0.1
    cov = aa_cov(field, 0.1, wrap)
    gy, gx = wgrad(blur(field, 1.0, wrap=wrap), wrap)
    gy *= SC; gx *= SC
    lit = np.clip(base + gain * (-0.6 * gx - 0.8 * gy) + fk * field, 0, 1)
    rgb = ramp_col(cols, lit)
    if stri:
        y, x = grid(field.shape[0] / SC, field.shape[1] / SC)
        s = np.clip(1 - np.abs(np.mod(x + y, 4.0) - 2.0) / 0.45, 0, 1) * np.clip((field - 0.4) / 0.1, 0, 1)
        rgb *= (1 - 0.13 * s[..., None])
    g = np.clip((lit - 0.85) / 0.06, 0, 1) * 0.5
    rgb = rgb * (1 - g[..., None]) + hexc(glaze) * g[..., None]
    ring = ring_out_wrap(m) if wrap else ring_out(m)
    return rgb, cov, ring


def trabeculae_p(far, y0, y1, seed, cols, out, n=16):
    R = RS(seed)
    h = y1 - y0
    y, x = grid(h, WT)
    field = np.zeros(y.shape, np.float32)
    for k in range(n):
        x0 = R.uniform(0, WT); a = R.uniform(-1.1, 1.1) + np.pi / 2; th = R.uniform(3, 8)
        nx, ny = -np.sin(a), np.cos(a)
        for off in (-WT, 0, WT):
            dd = ((x - x0 - off) * nx + (y - h / 2) * ny) + 2.0 * np.sin(y * 0.08 + k)
            field = np.maximum(field, np.clip(1 - (dd / th) ** 2, 0, 1))
    rgb, cov, ring = ridge_field_sprite(field, cols, out)
    reg = far[rows(y0):rows(y0) + y.shape[0]]
    over(reg, np.broadcast_to(hexc(out), rgb.shape), ring)
    over(reg, rgb, cov)


def endothelium_p(far, y0, y1, seed, cols, nuc, n=200):
    """long flat lining cells lying along the flow, each with an oval nucleus (wrapped)"""
    from scipy.spatial import cKDTree
    R = RS(seed)
    h = y1 - y0
    y, x = grid(h, WT)
    pts = np.c_[R.uniform(0, WT, n), R.uniform(0, h, n)]
    sx = 0.32
    tree = cKDTree(np.c_[pts[:, 0] * sx, pts[:, 1] + 2], boxsize=[WT * sx, h * 4 + 10])
    q = np.c_[(np.mod(x.ravel(), WT) * sx).astype(np.float64), (y.ravel() + 2).astype(np.float64)]
    d, i = tree.query(q, k=2)
    d = d.reshape(y.shape + (2,)); idx = i[:, 0].reshape(y.shape)
    bk = np.clip((0.45 - (d[..., 1] - d[..., 0])) * SC * 0.6 + 0.5, 0, 1)
    sh = 0.5 + 0.15 * np.sin(idx * 1.7)
    col = ramp_col(cols, np.clip(sh, 0, 1))
    reg = far[rows(y0):rows(y0) + y.shape[0]]
    reg[..., :3] = reg[..., :3] * 0.45 + col * 0.55
    reg[..., :3] *= (1 - 0.25 * bk[..., None])
    for (px_, py) in pts:
        for off in (-WT, 0, WT):
            ellipse_soft(far, px_ + off, y0 + py, 2.4, 0.75, nuc, 150)


def rbc_flow(c3, n, seed, y0=20, y1=GY - 14, dark=False, size=(7, 12), alpha=1.0):
    R = RS(seed)
    for k in range(n):
        s = rbc(int(R.uniform(*size)), R.uniform(0.3, 1.0), dark=dark)
        put(c3, s, R.uniform(0, WT), R.uniform(y0, y1), alpha)


def lumen_glow(far, col, k=0.18):
    """the middle of the passage a little lighter (light down the lumen)"""
    y = (np.arange(far.shape[0], dtype=np.float32) + 0.5) / SC - 0.5
    w = (np.exp(-((y - (GY + 14) / 2) / 48.0) ** 2) * k)[:, None, None]
    far[..., :3] = far[..., :3] * (1 - w) + hexc(col) * w


def three(far):
    return tile3(far)

# ------------------------------------------------------------------ small real details (shared)
def lum(arr):
    return arr[..., 0] * 0.3 + arr[..., 1] * 0.55 + arr[..., 2] * 0.15


def wet_glints(c3, n, seed, y0=14, y1=GY, pct=70, a=150, col='#fff4f6'):
    """the wet shine of a mucous surface: small elongated highlights where the tissue is lit"""
    R = RS(seed)
    L = lum(c3[:, px(WT):2 * px(WT)])
    g = np.zeros((c3.shape[0], px(WT), 4), np.float32)
    thr = np.percentile(L, pct)
    for k in range(n):
        x, y = R.uniform(0, WT), R.uniform(y0, y1)
        X, Y = min(px(x + 0.5), px(WT) - 1), min(px(y + 0.5), c3.shape[0] - 1)
        if L[Y, X] < thr:
            continue
        rx, ry, ang = R.uniform(0.8, 2.4), R.uniform(0.22, 0.45), R.uniform(-0.25, 0.25)
        ellipse_soft(g, x, y, rx, ry, '#ffffff', int(a * R.uniform(0.5, 1.0)), ang)
    # soft-edged, like light on a wet surface, not a painted dash
    k = blur(g[..., 3] / 255.0, 0.3, wrap=True)
    k = np.clip(k * 1.25, 0, 1)
    for off in range(3):
        reg = c3[:, off * px(WT):(off + 1) * px(WT)]
        blend(reg, hexc(col), k[:reg.shape[0]])


def cell_texture(arr, y0, y1, seed, size=3.0, k=0.08, sy=1.0, wrapw=True):
    """a faint pattern of cell borders over tissue (the epithelium seen up close)"""
    h = y1 - y0
    n = int(WT * h / (size * size))
    cb, _, _ = pcells(h, n, seed, sy=sy, border=0.35)
    reg = arr[px(y0):px(y0) + cb.shape[0]]
    reg[..., :3] *= (1 - k * cb[:reg.shape[0], ..., None])


def scatter(c3, sprites, n, seed, y0, y1, a=1.0):
    R = RS(seed)
    for k in range(n):
        s = sprites[k % len(sprites)]
        put(c3, s, R.uniform(0, WT), R.uniform(y0, y1), a)


def lymphocyte(size=7, seed=1):
    """a small round white cell: a big dark nucleus, a thin rim of pale cytoplasm"""
    m = ellipse_mask(size, size)
    spr = A.mask_sprite(m, ramp('#7a7a96', '#a8a8c4', '#d0d0e4', '#f0f0fa'), '#1e1e30', soft=0.8, hl_t=0.98)
    nm = ellipse_mask(size * 0.72, size * 0.7)
    nuc = A.mask_sprite(nm, ramp('#2a1a50', '#46307a', '#6a52a0'), '#1a0e30', soft=0.5, hl=False)
    paste(spr, nuc, size * 0.14, size * 0.12)
    return spr


def kupffer(seed=1):
    """a Kupffer cell (the liver's macrophage) lying in a sinusoid: an elongated body with short processes"""
    R = RS(seed)
    spr = canvas(16, 8)
    for k in range(5):
        a0 = R.uniform(0, TAU); L = R.uniform(2.5, 4.5)
        A.stroke(spr, [(8 + np.cos(a0) * t, 4 + np.sin(a0) * t * 0.6) for t in np.linspace(0, L, 8)], 0.8, '#4a2a3a', 220, scale=1.0)
    y, x = grid(5, 9)
    m = ellipse_mask(9, 5)
    b = A.mask_sprite(m, ramp('#5a3448', '#8a5a6e', '#b48a98'), '#24101a', soft=0.6, hl=False)
    paste(spr, b, 3, 1.5)
    disc(spr, 7.6, 4.0, 1.2, '#2a1440', 230)
    return spr


def microglia(seed=1, col='#9a8ac0'):
    R = RS(seed)
    spr = canvas(18, 18)
    for k in range(7):
        a0 = R.uniform(0, TAU); L = R.uniform(4, 8)
        pts = [(9 + np.cos(a0 + 0.3 * np.sin(t)) * t, 9 + np.sin(a0 + 0.3 * np.sin(t)) * t) for t in np.linspace(0, L, 10)]
        A.stroke(spr, pts, 0.7, col, 200, scale=1.0)
    m = ellipse_mask(4, 3)
    paste(spr, A.mask_sprite(m, ramp('#3a2a60', col, '#e0d8ff'), '#1a1030', soft=0.5, hl=False), 7, 7.5)
    return spr


def red_dots(arr, mask_fn, n, seed, h=H, r=(0.4, 0.7), col='#c82a3a', a=0.85):
    """red cells seen end-on in capillaries: little red dots wherever mask_fn(x, y) says"""
    R = RS(seed)
    P = np.c_[R.uniform(0, WT, n), R.uniform(0, h, n)]
    keep = np.array([mask_fn(p[0], p[1]) for p in P], bool)
    P = P[keep]
    if not len(P):
        return
    sp = spots(arr.shape, P, R.uniform(*r, len(P)), WT)
    blend(arr, hexc(col), sp * a)



# ------------------------------------------------------------------ obstacle helpers
def stack(sprs, gap=-3):
    """put sprites one above the other (bottom first), centred"""
    w = max(s.shape[1] for s in sprs) / SC; h = sum(s.shape[0] for s in sprs) / SC + gap * (len(sprs) - 1)
    out = canvas(w, h)
    y = h
    for s in sprs:
        y -= s.shape[0] / SC
        paste(out, s, (w - s.shape[1] / SC) / 2, y)
        y -= gap
    return out


def hang_len():
    return int(GY - 15.5 - 6)  # from under the ceiling band (y 6) down to y = GY - 15.5: a sliding character passes under, a running one does not


def flip_v(spr):
    return spr[::-1].copy()


# ------------------------------------------------------------------ 1. oesophagus
ESO_L = [(3, ramp('#c8a0a0', '#e8c4c0', '#f8e0dc', n=5), 'squamous'), (6, ramp('#a87070', '#d09a98', '#ecc0bc', '#fadad4', n=6), 'squamous'),
         (2, ramp('#5a1a2a', '#8a2a3a', '#a83a4a', n=4), 'smooth'), (7, ramp('#9a6a70', '#c89aa0', '#e8c4c4', n=5), 'loose'),
         (30, ramp('#3a0810', '#6e1420', '#962032', '#b83044', n=6), 'smooth')]


def T_eso():
    far = gradient(H, ['#2e0a14', '#40101c', '#521626', '#40101c'])
    folds(far, 12, GY + 4, 101, ramp('#5a1a28', '#7e2a3a', '#a2404e', '#c45c68', '#e08488', '#f8b0b0', n=8), '#22060e', None, n=9, kmin=1, kmax=3, thick=(4, 7), longitudinal=True)
    cell_texture(far, 12, GY + 4, 104, size=4.2, k=0.07, sy=0.6)
    c3 = three(far)
    R = RS(107)
    for k in range(26):                                  # threads of mucus between the folds
        x0 = R.uniform(0, WT); y0 = R.uniform(24, 70); L = R.uniform(18, 60); dx_ = R.uniform(-10, 10)
        pts = [(x0 + dx_ * u + 1.5 * np.sin(u * 5 + k), y0 + L * u + 2 * np.sin(u * np.pi)) for u in np.linspace(0, 1, 30)]
        for off in (0, WT, 2 * WT):
            A.stroke(c3, [(p + off, q) for p, q in pts], R.uniform(0.6, 1.1), '#f4e0e4', 70, scale=1.0)
    wet_glints(c3, 900, 108)
    drift(c3, 50, ['#d0a070', '#f0d8a8'], 102)
    far = crop(c3); lumen_glow(far, '#a04050', 0.12); haze(far, '#40101c', 0.3)
    mid = wide()
    R = RS(103)
    for k in range(5):                                   # swallowed air bubbles drifting
        r = int(R.uniform(4, 8))
        b = bubble(r, k)
        b[..., 3] *= 0.7
        put(mid, b, R.uniform(0, WT), R.uniform(30, GY - 40))
    floor = wall(ESO_L, True, seed=105, bumps=1.2, out='#22060e')
    ceil = wall([(3, ESO_L[0][1], 'squamous'), (4, ESO_L[1][1], 'squamous'), (2, ESO_L[2][1], 'smooth'), (20, ESO_L[4][1], 'smooth')], False, seed=106, bumps=1.2, out='#22060e')
    obs = {'low': [A.food_bolus(seed=s, w=22, h=15) for s in (1, 4, 6)],
           'tall': [stack([A.food_bolus(seed=7, w=24, h=18), A.food_bolus(seed=8, w=20, h=16), A.food_bolus(seed=9, w=16, h=14)])],
           'hang': [A.fold_hang(26, hang_len(), seed=s) for s in (2, 5)],
           'float': [bubble(14, 11)],
           'huge': [food_tower(range(40, 46))]}
    return dict(far=far, mid=crop(mid), floor=floor, ceil=ceil, obs=obs, coin='vitC', special='fiber')


def food_tower(seeds_, maker=None):
    """a towering pile of six lumps: only a triple jump clears it"""
    maker = maker or (lambda s, w, h: A.food_bolus(seed=s, w=w, h=h))
    ws = [22, 21, 20, 19, 18, 16]
    return tower(lambda H_: stack([maker(s, w, (H_ + 15) / 6 - 2) for s, w in zip(seeds_, ws)]))


def tower(make, target=92.0):
    """build a towering obstacle so that its hit box reaches `target` above the floor (a double jump tops out at
    87.5, a triple at 104): make(h) builds it with a nominal height h"""
    from tiles import hitbox
    h = 100.0
    for it in range(8):
        spr = make(h)
        hb = hitbox(spr)
        top = spr.shape[0] / SC - 2 - hb[1]
        if abs(top - target) < 0.8:
            break
        h += target - top
    return spr


def bubble(r=12, seed=1):
    """an air bubble: a clear sphere, bright rim, a window glint"""
    m = ellipse_mask(2 * r + 1, 2 * r + 1)
    b = A.mask_sprite(m, ramp('#a090a8', '#d0c4dc', '#f0e8f8', '#ffffff'), '#3a2e48', soft=1.2, ambient=0.45, hl_t=0.93)
    I = inner(b)
    d = ndimage.distance_transform_edt(m) / SC
    see = np.clip((d - 1.6) / 1.2, 0, 1) * 0.55
    I[..., 3] = np.where(m, 255 * (1 - see), I[..., 3])
    y, x = grid(2 * r + 1, 2 * r + 1)
    a = np.arctan2(y - r, x - r)
    rr = np.sqrt((x - r) ** 2 + (y - r) ** 2)
    glint = np.clip(1 - np.abs(rr - r * 0.62) / (0.12 * r + 0.3), 0, 1) * np.clip(np.cos(a + 2.35) * 3 - 1.8, 0, 1)
    I[..., :3] = I[..., :3] * (1 - glint[..., None]) + 255 * glint[..., None]
    I[..., 3] = np.maximum(I[..., 3], glint * 255 * m)
    return b


# ------------------------------------------------------------------ 2. stomach
STOM_L = [(3, ramp('#5a1028', '#a02a48', '#d04a66', '#f07a90', n=6), 'pits'), (5, ramp('#4a0c20', '#8a2240', '#b83a58', '#de6a80', n=6), 'pits'),
          (2, ramp('#3a0818', '#6a1830', '#8a2440', n=4), 'smooth'), (8, ramp('#9a6a70', '#c89aa0', '#e8c4c4', '#f8e0dc', n=6), 'loose'),
          (30, ramp('#3a0810', '#6e1420', '#962032', '#b83044', n=6), 'smooth')]


def T_stomach():
    far = gradient(H, ['#2a0614', '#3a0a1c', '#4a0e24', '#3a0a1c'])
    folds(far, 12, GY + 4, 7, ramp('#4a0c20', '#6e1630', '#922240', '#b43452', '#d65068', '#f07e90', n=8), '#1e040c', '#3a0614')
    cell_texture(far, 12, GY + 4, 11, size=2.6, k=0.07)
    c3 = three(far)
    R = RS(12)
    Lm = lum(c3[:, px(WT):2 * px(WT)]); thr_m = np.percentile(Lm, 65)
    for k in range(60):                                  # patches of mucus gel clinging to the folds (only on the folds)
        x0, y0 = R.uniform(0, WT), R.uniform(20, GY - 10)
        if Lm[min(px(y0 + 0.5), Lm.shape[0] - 1), px(x0 + 0.5) % Lm.shape[1]] < thr_m:
            continue
        for off in (0, WT, 2 * WT):
            ellipse_soft(c3, x0 + off, y0, R.uniform(4, 11), R.uniform(1.5, 3.5), '#f8e4ea', 46, R.uniform(-0.3, 0.3))
    wet_glints(c3, 1100, 13)
    scatter(c3, [bubble(2, 1), bubble(3, 2), bubble(2, 3)], 24, 14, 20, GY - 10, 0.75)
    drift(c3, 60, ['#c89a60', '#e8c890', '#f0e0b0'], 3)
    far = crop(c3); haze(far, '#3a0a1c', 0.3)
    mid = wide()
    R = RS(9)
    for k in range(10):                                  # bits of food floating past
        put(mid, A.food_bit(seed=20 + k, w=R.uniform(6, 10), h=R.uniform(4, 7)), R.uniform(0, WT), R.uniform(24, GY - 30), 0.9)
    floor = wall(STOM_L, True, seed=15, bumps=1.3, out='#1e040c')
    ceil = wall([(3, STOM_L[0][1], 'pits'), (4, STOM_L[1][1], 'pits'), (2, STOM_L[2][1], 'smooth'), (4, STOM_L[3][1], 'loose'), (20, STOM_L[4][1], 'smooth')], False, seed=13, bumps=1.3, out='#1e040c')
    obs = {'low': [A.food_bolus(seed=s) for s in (3, 11, 12)],
           'tall': [stack([A.food_bolus(seed=13, w=28, h=22), A.food_bolus(seed=14, w=24, h=20), A.food_bolus(seed=15, w=18, h=16)])],
           'hang': [A.fold_hang(30, hang_len(), seed=s) for s in (3, 6)],
           'float': [A.h_pylori()],
           'huge': [food_tower(range(50, 56))]}
    return dict(far=far, mid=crop(mid), floor=floor, ceil=ceil, obs=obs, coin='vitC', special='fiber')


# ------------------------------------------------------------------ 3. small intestine
GUT_L = [(8, ramp('#5a1424', '#9a2e40', '#c8505c', '#e8787e', n=6), 'crypts'), (2, ramp('#3a0a18', '#6a1a2a', '#8a2a3a', n=4), 'smooth'),
         (7, ramp('#9a6a6a', '#c89a98', '#e8c4bc', '#f8e0d8', n=6), 'loose'), (30, ramp('#3a0a10', '#6e1820', '#962832', '#b83a44', n=6), 'smooth')]


def gut_surface(c3, edge, e0, top_edge):
    R = RS(5 if top_edge else 6)
    x = 0.0
    while x < WT:
        hh = int(R.uniform(5, 9)); ww = int(R.choice([6, 7]))
        v = A.villus_real(hh, ww, int(x + 40), hang=not top_edge)
        xi = int(x) % WT
        if top_edge:
            put(c3, v, x, e0 + edge[xi] - hh + 2)
        else:
            put(c3, v, x, e0 - 1 - edge[xi] - 1)
        x += R.uniform(5, 8)


def T_gut(name='gut'):
    far = gradient(H, ['#2a0812', '#3a0c1a', '#4a1222', '#3a0c1a'])
    c3 = three(far)
    R = RS(21)
    # big circular folds far behind
    for k in range(4):
        fx = k * WT / 4 + R.uniform(-40, 40)
        fold = ellipse_mask(240, 150)
        yy, _ = grid(150, 240)
        fs = paint(fold, ramp('#4a1222', '#5a1a2a', '#6a2232', n=3), np.clip(0.9 - yy / 180.0, 0, 1))
        put(c3, outline(fs, '#2a0810'), fx - 120, GY - 80)
    for layer, (n, hmin, hmax, w, dim) in enumerate([(130, 26, 50, 7, 0.62), (90, 34, 66, 9, 0.38), (54, 44, 80, 11, 0.12)]):
        xs = np.sort(R.uniform(0, WT, n))
        for xx in xs:
            hh = int(R.uniform(hmin, hmax)); hang = R.uniform() < 0.3
            v = A.villus_real(hh if not hang else int(hh * 0.6), w, int(xx * 13 + layer * 101 + 1), hang=hang, dim=dim)
            put(c3, v, xx, (GY - hh + 4) if not hang else 8)
    wet_glints(c3, 700, 26, pct=80)
    drift(c3, 80, ['#e8c070', '#f4dca0'], 8)
    far = crop(c3); haze(far, '#3a0c1a', 0.3)
    mid = wide()
    R = RS(27)
    for k in range(9):                                   # chyme: bits of digested food, fat droplets, a few bacteria
        put(mid, A.food_bit(seed=60 + k, w=R.uniform(5, 8), h=R.uniform(3.5, 5.5)), R.uniform(0, WT), R.uniform(30, GY - 40), 0.88)
    for k in range(14):
        r_ = R.uniform(1.2, 2.4); m_ = ellipse_mask(2 * r_ + 1, 2 * r_ + 1)
        put(mid, A.mask_sprite(m_, ramp('#a07a10', '#e0b830', '#fff090', '#ffffe0'), '#4a3604', soft=0.6, ambient=0.4, hl_t=0.93), R.uniform(0, WT), R.uniform(26, GY - 34), 0.85)
    floor = wall(GUT_L, True, seed=25, bumps=1.0, out='#22080a', surface=gut_surface)
    ceil = wall([(6, GUT_L[0][1], 'crypts'), (2, GUT_L[1][1], 'smooth'), (3, GUT_L[2][1], 'loose'), (20, GUT_L[3][1], 'smooth')], False, seed=23, bumps=1.0, out='#20060c', surface=gut_surface)
    obs = {'low': [A.chyme_fat(seed=s) for s in (2, 4, 5)],
           'tall': [A.plica(60, 34, seed=s) for s in (7, 9)],
           'hang': [hang_villi(seed=s) for s in (1, 2)],
           'float': [A.e_coli()],
           'huge': [tower(lambda h: A.plica(int(h), 18, seed=11))]}
    return dict(far=far, mid=crop(mid), floor=floor, ceil=ceil, obs=obs, coin='vitC', special='fiber')


def hang_villi(seed=1):
    """a fold of the ceiling hanging down, villi on its underside"""
    L = hang_len()
    spr = canvas(30, L + 4)
    y, x = grid(L - 8, 26)
    m = np.abs(x - 12.5) <= 13 * (1 - (y / (L - 8)) ** 2 * 0.45)
    base = A.mask_sprite(m, ramp('#6a1828', '#a03040', '#c84e5c', '#e8747e', '#ffa8a8'), '#2a0810', soft=1.8)
    A.grain(base, seed, 0.05)
    paste(spr, base, 1, 0)
    R = RS(seed)
    for k in range(6):
        v = A.villus_real(int(R.uniform(7, 11)), 5, seed * 10 + k, hang=True)
        paste(spr, v, 2 + k * 4.2, L - 11)
    return spr


# ------------------------------------------------------------------ 4. large intestine
COLON_L = [(7, ramp('#4a1a14', '#7e3424', '#a84e34', '#cc7050', n=6), 'crypts'), (2, ramp('#3a1010', '#5a1e1a', '#7a2a24', n=4), 'smooth'),
           (7, ramp('#8a6a5a', '#b8957e', '#dcbca2', '#f0d8c0', n=6), 'loose'), (30, ramp('#3a0c0c', '#6a1c18', '#902a22', '#b03c30', n=6), 'smooth')]


def vessels_p(c3, y0, y1, n, seed, col, a=170, wdt=1.0):
    """fine branching vessels seen through the lining (as in a colonoscopy)"""
    R = RS(seed)
    def br(x, y, ang, L, lvl):
        pts = []
        for i in range(int(L)):
            x += np.cos(ang); y += np.sin(ang); ang += R.uniform(-0.25, 0.25)
            pts.append((x, y))
            if lvl < 3 and R.uniform() < 0.06:
                br(x, y, ang + R.choice([-1, 1]) * R.uniform(0.5, 1.1), L * 0.5, lvl + 1)
        for off in (0, WT, 2 * WT):
            A.stroke(c3, [(px_ + off, py) for px_, py in pts if y0 <= py < y1], wdt * (1.0 - 0.18 * lvl), col, a, scale=0.75)
    for k in range(n):
        br(R.uniform(0, WT), R.uniform(y0, y1), R.uniform(0, TAU), R.uniform(25, 60), 0)


def T_colon():
    """the colon (variants.py: haustra and a taenia coli)"""
    from variants import colon_v
    return colon_v('colon')


def feces(w=24, h=15, seed=1):
    """a lump of stool: brown, lumpy, with fibre bits"""
    R = RS(seed)
    y, x = grid(h, w)
    m = ((x - w / 2) / (w / 2)) ** 2 + ((y - h) / h) ** 2 <= 1
    for k in range(5):
        bx, by, br = R.uniform(3, w - 3), R.uniform(h * 0.3, h * 0.85), R.uniform(2.5, 4.5)
        by = max(by, br + 0.3); bx = min(max(bx, br + 0.3), w - 1.3 - br)
        m |= (x - bx) ** 2 + (y - by) ** 2 <= br * br
    spr = A.mask_sprite(m, ramp('#2a1404', '#4a2a0e', '#6e4218', '#8e5c26', '#b07a3c'), '#140a02', hl_t=0.99)
    A.grain(spr, seed, 0.1)
    for k in range(7):
        gx, gy = R.uniform(3, w - 2), R.uniform(3, h)
        if A.on(spr, gx, gy):
            ellipse_soft(spr, gx + 0.5, gy, 1.2, 0.4, '#c8a050', 240, R.uniform(-0.6, 0.6))
    return spr


def semilunar_fold(seed=1):
    """a crescent fold of the colon wall reaching down from the ceiling: a broad fleshy lip"""
    L = hang_len()
    y, x = grid(L, 38)
    half = 18 * (1 - 0.35 * (y / L) ** 2)
    m = (np.abs(x - 18.5) <= half) & (y < L - 3 * np.abs(np.sin((x - 18.5) / 18 * np.pi / 2)))
    spr = A.mask_sprite(m, ramp('#5a2218', '#84382a', '#a8523c', '#c87256', '#e49a7c', '#f8c0a4'), '#1a0806', soft=2.4)
    A.grain(spr, seed, 0.05)
    R = RS(seed)
    def br(x, y, ang, n, wdt, lvl):
        pts = [(x, y)]
        for i in range(n):
            x += np.cos(ang) * 1.2; y += np.sin(ang) * 1.2; ang += R.uniform(-0.3, 0.3)
            ang = np.clip(ang, 0.4, np.pi - 0.4)
            pts.append((x, y))
            if lvl < 2 and R.uniform() < 0.07:
                br(x, y, ang + R.choice([-1, 1]) * R.uniform(0.5, 1.0), n // 2, wdt * 0.7, lvl + 1)
        pts = [(p, q) for p, q in pts if A.on(spr, p + 1, q + 1)]
        if len(pts) > 2:
            A.stroke(spr, [(p + 1, q + 1) for p, q in pts], wdt, '#9a2a24', 150, scale=1.0)
    for k in range(4):
        br(R.uniform(8, 28), 0, np.pi / 2 + R.uniform(-0.3, 0.3), int(L / 1.2), 1.0, 0)
    return spr


# ------------------------------------------------------------------ 5/6. arteries and veins
ART_L = [(2, ramp('#c87a80', '#f0b0b0', '#ffe0dc', n=4), 'endo'), (16, ramp('#6a1020', '#9a1c30', '#c43448', '#e0566a', n=6), 'elastic'),
         (30, ramp('#8a6458', '#b88a7a', '#dcb4a0', '#f0d4c0', n=6), 'loose')]
VEIN_L = [(2, ramp('#a87a90', '#d0a8c0', '#f0d8e8', n=4), 'endo'), (7, ramp('#4a1430', '#6e2244', '#923456', '#b04a6c', n=6), 'smooth'),
          (30, ramp('#7a6070', '#a48896', '#c8acb8', '#e4ccd4', n=6), 'loose')]


def vessel_theme(vein=False, pulm=False):
    if not vein:
        far = gradient(H, ['#2a0610', '#3e0a18', '#4e0e20', '#3e0a18'])
        endothelium_p(far, 12, GY + 2, 9, ramp('#5a1424', '#6e1a2c', '#822234', n=3), '#3a0a18')
        bg, rb_dark = '#3e0a18', True
    else:
        far = gradient(H, ['#1a0816', '#2a0c22', '#38122e', '#2a0c22'])
        endothelium_p(far, 12, GY + 2, 19, ramp('#401838', '#52203f', '#642a4c', n=3), '#28081e')
        bg, rb_dark = '#2a0c22', True
    c3 = three(far)
    R = RS(4 if not vein else 14)
    # openings of side branches on the far wall
    for k in range(3):
        bw, bh = int(R.uniform(34, 54)), int(R.uniform(20, 30))
        hm = ellipse_mask(bw, bh)
        y, x = grid(bh, bw)
        hs = np.zeros(hm.shape + (4,), np.float32)
        depth = np.clip(((x - (bw - 1) / 2) / (bw / 2)) ** 2 + ((y - (bh - 1) / 2 - 1.5) / (bh / 2 - 2)) ** 2, 0, 1)
        hs[..., :3] = ramp_col(ramp('#08010a', '#14030a', '#2a0a18', n=3), depth)[..., :3]
        hs[..., 3] = smooth_mask(hm) * 255
        lip = hm & ~ellipse_mask(bw, bh, bw / 2 - 0.5, bh / 2 + 1.5, bw / 2 - 2, bh / 2 - 2)
        lk = smooth_mask(lip)
        blend(hs, hexc('#9a2a3e' if not vein else '#7a2a5a'), lk)
        put(c3, outline(hs, '#12020a'), k * WT / 3 + R.uniform(0, 200), R.uniform(30, 90))
    if vein:
        for k in range(3):                                # venous valves: pairs of thin cusps on the far wall
            vx = k * WT / 3 + R.uniform(150, 300)
            for sgn, yy in ((1, 20), (-1, GY - 4)):
                y, x = grid(40, 26)
                cusp = (np.abs(x - 12.5) <= 12 * (1 - (y / 40) ** 2))
                cs = A.mask_sprite(cusp if sgn > 0 else cusp[::-1], ramp('#4a2040', '#6a3058', '#8a4672', '#a86090'), '#1a0614', soft=1.4, hl=False)
                put(c3, cs, vx, yy if sgn > 0 else yy - 42, 0.85)
    rbc_flow(c3, 70, 5 + vein, dark=rb_dark)
    for k in range(20):
        put(c3, A.platelet(k), R.uniform(0, WT), R.uniform(20, GY - 20))
    for k in range(7):                                   # white cells rolling along the wall (they stick and roll before leaving it)
        put(c3, A.neutrophil(int(R.uniform(9, 12)), seed=40 + k), R.uniform(0, WT), R.uniform(24, GY - 24), 0.92)
    for k in range(5):
        put(c3, lymphocyte(6, k), R.uniform(0, WT), R.uniform(24, GY - 24), 0.92)
    wet_glints(c3, 500, 44 + vein, pct=75, a=90, col='#ffe8ee')
    far = crop(c3); haze(far, bg, 0.25)
    mid = wide()
    rbc_flow(mid, 26, 7 + vein, y0=22, y1=GY - 30, size=(12, 17), alpha=0.95)
    if vein:
        haze(mid, '#401030', 0.25)
    layers = ART_L if not vein else VEIN_L
    floor = wall(layers, True, seed=5 + vein, bumps=0.8, out='#1a0308')
    ceil = wall([(2, layers[0][1], 'endo'), (8, layers[1][1], layers[1][2]), (20, layers[2][1], 'loose')], False, seed=3 + vein, bumps=0.8, out='#1a0308')
    if not vein:
        obs = {'low': [A.atheroma(32, 18, seed=s) for s in (2, 3)],
               'tall': [A.thrombus(26, 60, seed=s) for s in (4, 5)],
               'hang': [flip_v(A.thrombus(24, hang_len(), seed=6))],
               'float': [A.neutrophil(22, seed=3), platelet_clump()],
               'huge': [tower(lambda h: A.thrombus(24, int(h), seed=7))]}
    else:
        obs = {'low': [A.thrombus(24, 18, seed=8)],
               'tall': [vein_valve(60)],
               'hang': [flip_v(vein_valve(hang_len()))],
               'float': [A.neutrophil(22, seed=5)],
               'huge': [tower(lambda h: vein_valve(int(h)))]}
    return dict(far=far, mid=crop(mid), floor=floor, ceil=ceil, obs=obs, coin='o2', special='iron')


def T_artery():
    return vessel_theme(False)


def T_vein():
    return vessel_theme(True)


def platelet_clump():
    out = canvas(20, 14)
    R = RS(3)
    for k in range(8):
        paste(out, A.platelet(k + 3), R.uniform(0, 13), R.uniform(0, 9))
    return out


def vein_valve(L=60):
    """a valve cusp of a vein standing up from the wall: a thin pale flap curving with the flow"""
    y, x = grid(L, 22)
    lean = 6 * (1 - y / L) ** 2
    m = np.abs(x - 10 - lean) <= 3 + 6 * np.clip(y / L, 0, None) ** 0.7
    spr = A.mask_sprite(m, ramp('#6a3a58', '#9a6080', '#c08aa4', '#e0b4c8', '#f8dce8'), '#1a0614', soft=1.6)
    I = inner(spr)
    fib = np.clip(1 - np.abs(np.mod(x - lean * 0.8, 2.2) - 1.1) / 0.3, 0, 1) * m
    I[..., :3] *= (1 - 0.1 * fib[..., None])
    return spr


# ------------------------------------------------------------------ 7/8. heart: atria and ventricles
MYO_L = [(2, ramp('#c88088', '#f0b4b4', '#ffe0dc', n=4), 'endo'), (20, ramp('#4a0a18', '#7a1426', '#a62236', '#cc3a4c', n=6), 'striated'),
         (30, ramp('#a08030', '#d0b050', '#f0d880', '#fff0b8', n=6), 'fat')]


def T_ventricle():
    """the right ventricle (variants.py: with its moderator band)"""
    from variants import ventricle
    return ventricle(False)


def trab_ridge(w=30, h=18):
    """a muscle ridge of the ventricle wall rising from the floor"""
    y, x = grid(h, w)
    m = ((x - w / 2) / (w / 2)) ** 2 + ((y - h) / h) ** 2 <= 1
    spr = A.mask_sprite(m, ramp('#4a0a18', '#7a1628', '#a8263a', '#d0465a', '#f07a88'), '#16020a', soft=1.4)
    I = inner(spr)
    s = np.clip(1 - np.abs(np.mod(x + y, 4.0) - 2.0) / 0.45, 0, 1) * m
    I[..., :3] *= (1 - 0.15 * s[..., None])
    return spr


def T_atrium():
    far = gradient(H, ['#200410', '#300818', '#3e0c20', '#300818'])
    # pectinate muscles: parallel ridges like the teeth of a comb, over a smooth wall
    h = GY - 6
    y, x = grid(h, WT)
    per = WT / 39
    ph = np.mod(x + 6 * np.sin(y * 0.03), per) / per
    ridge = np.clip(np.sin(ph * np.pi) * 1.4 - 0.4, 0, 1) * np.clip((y - 20) * 0.5, 0, 1)
    lit = np.clip(0.25 + 0.6 * ridge - 0.3 * np.clip((ph - 0.6) * 8, 0, 1) * ridge, 0, 1)
    rgb = ramp_col(ramp('#3a0814', '#561020', '#722030', '#923242', '#b04a58', n=7), lit)
    st = np.clip(1 - np.abs(np.mod(y + x * 0.2, 2.2) - 1.1) / 0.3, 0, 1) * ridge
    rgb *= (1 - 0.1 * st[..., None])
    far[px(6):px(6) + y.shape[0], :, :3] = rgb
    c3 = three(far)
    rbc_flow(c3, 40, 41, dark=True)
    scatter(c3, [A.neutrophil(10, 50), lymphocyte(6, 51)], 6, 52, 24, GY - 24, 0.9)
    wet_glints(c3, 600, 53, pct=70, a=110, col='#ffe0e6')
    far = crop(c3); haze(far, '#300818', 0.25)
    mid = wide(); rbc_flow(mid, 16, 43, y0=22, y1=GY - 30, size=(12, 17))
    floor = wall(MYO_L, True, seed=45, bumps=0.6, out='#16020a')
    ceil = wall([(2, MYO_L[0][1], 'endo'), (24, MYO_L[1][1], 'striated')], False, seed=46, bumps=0.6, out='#16020a')
    obs = {'low': [trab_ridge(28, 16)], 'tall': [A.thrombus(24, 58, seed=9)], 'hang': [flip_v(trab_ridge(30, hang_len()))], 'float': [A.neutrophil(20, seed=9)], 'huge': [tower(lambda h: A.thrombus(24, int(h), seed=10))]}
    return dict(far=far, mid=crop(mid), floor=floor, ceil=ceil, obs=obs, coin='o2', special='iron')


# ------------------------------------------------------------------ 9. the brain's surface: subarachnoid space
PIA_L = [(2, ramp('#c890a8', '#e8b8cc', '#fadcea', n=4), 'endo'), (22, ramp('#6a4a7a', '#8a6a98', '#a888b4', '#c8a8d0', n=6), 'gray'),
         (30, ramp('#a8a0b8', '#c8c0d4', '#e4dcec', n=5), 'white')]


def T_arach():
    far = gradient(H, ['#0e1a2a', '#14243a', '#1a2e48', '#14243a'])          # clear fluid (CSF), bluish
    c3 = three(far)
    R = RS(51)
    # arachnoid trabeculae: fine pale strands spanning from the membrane above down to the brain below, a web
    for k in range(70):
        x0 = R.uniform(0, WT); x1 = x0 + R.uniform(-60, 60)
        pts = [(x0 + (x1 - x0) * t + 3 * np.sin(t * 6 + k), 14 + (GY - 14) * t) for t in np.linspace(0, 1, 80)]
        for off in (0, WT, 2 * WT):
            A.stroke(c3, [(a + off, b) for a, b in pts], 1, '#7a8aa8' if k % 3 else '#a8b4cc', 150, scale=0.6)
    # surface arteries and veins winding along
    for (yy, col, w) in ((GY - 18, '#a82838', 5), (40, '#5a2a6a', 4)):
        pts = [(x, yy + 6 * np.sin(x * TAU * 3 / WT) + 3 * np.sin(x * TAU * 11 / WT)) for x in np.arange(0, 3 * WT, 1.5)]
        A.stroke(c3, pts, w + 1.6, '#120818', scale=1.0)
        A.stroke(c3, pts, w, col, scale=1.0)
        A.stroke(c3, [(a, b + w * 0.22) for a, b in pts], w * 0.35, '#000000', 60, scale=1.0)
        A.stroke(c3, [(a, b - w * 0.22) for a, b in pts], w * 0.3, '#e88a98' if col == '#a82838' else '#9a6aaa', scale=1.0)
    for (yy, col, w, sgn) in ((GY - 18, '#a82838', 2.2, -1), (40, '#5a2a6a', 1.8, 1)):    # small branches off them
        for k in range(10):
            x0 = R.uniform(0, WT); y_ = yy + 6 * np.sin(x0 * TAU * 3 / WT) + 3 * np.sin(x0 * TAU * 11 / WT)
            a0 = sgn * np.pi / 2 + R.uniform(-0.9, 0.9); L = R.uniform(14, 34)
            pts = [(x0 + np.cos(a0) * t + 1.5 * np.sin(t * 0.3 + k), y_ + np.sin(a0) * t) for t in np.linspace(0, L, 30)]
            for off in (0, WT, 2 * WT):
                A.stroke(c3, [(p + off, q) for p, q in pts], w + 1.2, '#120818', scale=1.0)
                A.stroke(c3, [(p + off, q) for p, q in pts], w, col, scale=1.0)
    scatter(c3, [lymphocyte(5, 61), lymphocyte(6, 62), microglia(63, '#8aa0c8')], 18, 64, 30, GY - 30, 0.85)
    drift(c3, 60, ['#9ab8e0', '#d0e0ff'], 52, a=160)
    far = crop(c3); haze(far, '#14243a', 0.2)
    floor = wall(PIA_L, True, seed=55, bumps=2.4, out='#1a0e24')
    ceil = wall([(2, ramp('#8a9ab8', '#b8c4d8', '#e0e8f4', n=4), 'endo'), (6, ramp('#4a5a7a', '#6a7a98', '#8a98b4', n=4), 'loose'),
                 (20, ramp('#5a4a4a', '#7a6a66', '#9a8a84', n=4), 'loose')], False, seed=56, bumps=0.6, out='#0a1220')
    obs = {'low': [pial_arch(34, 20)], 'tall': [strand_column(60)], 'hang': [web_hang()], 'float': [macrophage()], 'huge': [tower(lambda h: strand_column(int(h)))]}
    return dict(far=far, mid=None, floor=floor, ceil=ceil, obs=obs, coin='o2', special='omega')


def pial_arch(w=34, h=20):
    """a small artery looping up off the brain's surface"""
    spr = canvas(w + 4, h + 4)
    pts = [(2 + w * t, h + 2 - h * 4 * t * (1 - t)) for t in np.linspace(0, 1, 120)]
    A.stroke(spr, pts, 6.6, '#120818', scale=1.0); A.stroke(spr, pts, 5, '#a82838', scale=1.0)
    A.stroke(spr, [(a, b + 1.2) for a, b in pts], 1.6, '#6a1020', 160, scale=1.0)
    A.stroke(spr, [(a, b - 1.2) for a, b in pts], 1.2, '#ff8a98', scale=1.0)
    return spr


def strand_column(h=60):
    """a thick arachnoid trabecula: a bundle of pale strands standing from the brain up into the fluid"""
    spr = canvas(16, h + 2)
    R = RS(3)
    for k in range(9):
        ph = R.uniform(0, 6)
        pts = [(8 + 3 * np.sin(t * 0.15 + ph) * (0.4 + t / h), h + 1 - t) for t in np.linspace(0, h, 120)]
        A.stroke(spr, pts, 2, '#3a4a68', scale=1.0); A.stroke(spr, pts, 1, '#c8d4ec', scale=1.0)
    return spr


def web_hang():
    """arachnoid strands hanging from the membrane like a curtain of cobweb"""
    L = hang_len()
    spr = canvas(34, L + 2)
    R = RS(5)
    for k in range(14):
        x0 = R.uniform(2, 32)
        pts = [(x0 + 2 * np.sin(t * 0.2 + k), t) for t in np.linspace(0, L * R.uniform(0.8, 1.0), 120)]
        A.stroke(spr, pts, 1.6, '#3a4a68', 200, scale=1.0)
        A.stroke(spr, pts, 0.8, '#c8d4ec', scale=1.0)
    for k in range(9):                                   # cross strands
        y0 = R.uniform(8, L - 4); xa, xb = R.uniform(1, 16), R.uniform(18, 33)
        pts = [(xa + (xb - xa) * t, y0 + 3 * np.sin(t * 3)) for t in np.linspace(0, 1, 30)]
        A.stroke(spr, pts, 1.3, '#3a4a68', 180, scale=1.0)
        A.stroke(spr, pts, 0.7, '#9aa8c4', scale=1.0)
    return spr


def macrophage(size=22):
    """a macrophage drifting in the fluid: a big pale cell with ruffled edges and engulfed bits"""
    R = RS(4)
    y, x = grid(size, size)
    ang = np.arctan2(y - size / 2, x - size / 2)
    m = ((x - size / 2) ** 2 + (y - size / 2) ** 2) <= (size / 2 - 1.2 - 1.2 * np.sin(ang * 7)) ** 2
    spr = A.mask_sprite(m, ramp('#6a6a80', '#9a9ab0', '#c4c4d8', '#e4e4f0', '#ffffff'), '#1e1e30', soft=1.4, hl_t=0.985)
    A.grain(spr, 4, 0.05)
    paste(spr, A.mask_sprite(ellipse_mask(7, 6), ramp('#3a2a60', '#5a4488', '#7a62a8'), '#1a0e30', soft=0.6, hl=False), size / 2 - 3, size / 2 - 2)
    for k in range(6):
        gx, gy = R.uniform(5, size - 3), R.uniform(5, size - 3)
        if A.on(spr, gx, gy):
            disc(spr, gx, gy, 0.85, '#a87a30'); disc(spr, gx - 0.2, gy - 0.2, 0.55, '#d8aa60')
    return spr


def cell_sprite(draw, w, h):
    c = canvas(w, h)
    draw(c, w / 2, h / 2)
    return c


def pyr_sprite(size, R, cols, glow=False):
    seed = R.randint(0, 1 << 30)
    def d(c, cx, cy):
        A.pyramidal(c, cx, cy + size * 1.2, size, RS(seed), cols, glow)
    return cell_sprite(d, int(size * 9), int(size * 11))


def astro_sprite(size, R, col, out):
    seed = R.randint(0, 1 << 30)
    return cell_sprite(lambda c, cx, cy: A.astrocyte(c, cx, cy, size, RS(seed), col, out), int(size * 6), int(size * 6))


def purk_sprite(R, cols):
    seed = R.randint(0, 1 << 30)
    def d(c, cx, cy):
        rr = RS(seed)
        def br(x, y, a, L, wdt, lvl):
            pts = [(x, y)]
            for i in range(int(L)):
                x += np.cos(a); y += np.sin(a); a += rr.uniform(-0.1, 0.1)
                pts.append((x, y))
                if lvl < 5 and i > 2 and rr.uniform() < 0.16:
                    br(x, y, a + rr.choice([-1, 1]) * rr.uniform(0.3, 0.7), L * 0.62, max(1, wdt - 1), lvl + 1)
            A.stroke(c, pts, wdt * (1 - 0.1 * lvl), cols[1], scale=0.8)
            if lvl >= 4:
                disc(c, x, y, 0.45, cols[2])
        br(cx, cy - 4, -np.pi / 2, 26, 2, 0)
        br(cx, cy, np.pi / 2, 30, 1, 4)
        sp = A.mask_sprite(ellipse_mask(9, 10), ramp(cols[0], cols[1], cols[2], cols[3]), cols[5], soft=0.6, ambient=0.35)
        paste(c, sp, cx - 5, cy - 5)
    return cell_sprite(d, 90, 110)


# ------------------------------------------------------------------ 10. nerve cells (pyramidal / hippocampus / Purkinje)
GRAY_L = [(2, ramp('#a07ab8', '#d0b0e8', '#f0e0ff', n=4), 'endo'), (18, ramp('#3a2a6a', '#5a4490', '#7a62b4', '#9e86d4', n=6), 'gray'),
          (30, ramp('#8a86a8', '#b0aecc', '#d4d2ea', '#f0eefc', n=6), 'white')]
NEURO_PAL = {
    'violet': (('#2a1c50', '#3a2a62', '#4a3874', '#5a4686', '#6a5498', '#14082a'), ('#5a2c98', '#8a58c8', '#b884f0', '#e0c8ff', '#7ff0ff', '#1e0a3a'), ['#0c0820', '#140e2c', '#1c1438', '#140e2c']),
    'blue': (('#1a2c50', '#243a64', '#2e4878', '#38568a', '#42649c', '#0a1428'), ('#2a5aa8', '#4a84d8', '#78b0f8', '#c4e0ff', '#a8ffe8', '#0a1a3a'), ['#080c20', '#0e1630', '#141e3e', '#0e1630']),
    'rose': (('#4a1c40', '#5a2a52', '#6a3864', '#7a4676', '#8a5488', '#200a1c'), ('#a83a7a', '#d062a2', '#f08ac4', '#ffd0ec', '#ffe08a', '#2a0a20'), ['#160818', '#200c24', '#2a1230', '#200c24']),
}


def capillary_band(c3, yy, k_waves, wall_col, lumen_col, amp=2.5):
    """a capillary running across the whole wide canvas"""
    y, x = grid(c3.shape[0] / SC, c3.shape[1] / SC)
    yc = yy + amp * np.sin(x * TAU * k_waves / WT)
    d = np.abs(y - yc)
    wall_k = np.clip((3.5 - d) * SC + 0.5, 0, 1)
    lum_k = np.clip((2.5 - d) * SC + 0.5, 0, 1)
    over(c3, np.broadcast_to(hexc(wall_col), c3.shape[:2] + (3,)), wall_k)
    sh = 1 - 0.4 * np.clip(d / 2.5, 0, 1) ** 2
    over(c3, hexc(lumen_col) * sh[..., None], lum_k)


def T_neurons(pal='violet', kind='pyramidal'):
    farC, nearC, bgC = NEURO_PAL[pal]
    far = gradient(H, bgC)
    c3 = three(far)
    R = RS(41 + len(pal))
    for k in range(260):                                 # neuropil: faint bits of dendrite everywhere
        x0, y0 = R.uniform(0, WT), R.uniform(10, GY)
        a0 = R.uniform(0, TAU); L = R.uniform(6, 22)
        pts = [(x0 + np.cos(a0) * t + 0.8 * np.sin(t * 0.4 + k), y0 + np.sin(a0) * t) for t in np.linspace(0, L, 12)]
        for off in (0, WT, 2 * WT):
            A.stroke(c3, [(p + off, q) for p, q in pts], 1, farC[2], 55, scale=0.6)
    for k in range(8):                                   # myelinated axons crossing far behind
        x0, y0 = R.uniform(0, WT), R.uniform(20, GY - 20); a0 = R.uniform(-0.5, 0.5); L = R.uniform(60, 140)
        pts = [(x0 + np.cos(a0) * t, y0 + np.sin(a0) * t + 2 * np.sin(t * 0.05 + k)) for t in np.linspace(0, L, 60)]
        for off in (0, WT, 2 * WT):
            A.stroke(c3, [(p + off, q) for p, q in pts], 2.2, farC[3], 110, scale=1.0)
            A.stroke(c3, [(p + off, q - 0.4) for p, q in pts], 0.8, '#ffffff', 60, scale=1.0)
    for k in range(500):                                 # synaptic boutons: tiny swellings on the fibres, glowing a little
        x0, y0 = R.uniform(0, WT), R.uniform(10, GY)
        for off in (0, WT, 2 * WT):
            disc(c3, x0 + off, y0, R.uniform(0.35, 0.6), nearC[4] if k % 3 == 0 else farC[3], 90)
    scatter(c3, [microglia(70 + k, farC[3]) for k in range(3)], 9, 73, 20, GY - 20, 0.8)
    for k in range(22):
        x, y = R.uniform(0, WT), R.uniform(80, GY - 6)
        s = purk_sprite(R, farC) if kind == 'purkinje' else pyr_sprite(6, R, farC)
        put(c3, s, x - s.shape[1] / SC / 2, y - s.shape[0] / SC * 0.62)
    yy = 64                                              # a capillary across, astrocytes holding on to it
    capillary_band(c3, yy, 4, '#8a2a40', '#4a0c1c')
    for k in range(40):
        x = R.uniform(0, WT); y_ = yy + 2.5 * np.sin(x * TAU * 4 / WT)
        put(c3, A.rbc_small(R.uniform(0.5, 0.9)), x - 3, y_ - 2)
    for k in range(10):
        s = astro_sprite(6, R, '#b8a0e0' if pal != 'blue' else '#a0c0f0', '#3a2a60')
        put(c3, s, R.uniform(0, WT) - s.shape[1] / SC / 2, yy + R.uniform(-22, 22) - s.shape[0] / SC / 2)
    far = crop(c3); haze(far, bgC[1], 0.25)
    mid = wide()
    for k in range(12):
        x, y = R.uniform(0, WT), R.uniform(116, GY - 4)
        s = purk_sprite(R, nearC) if kind == 'purkinje' else pyr_sprite(9, R, nearC, glow=True)
        put(mid, s, x - s.shape[1] / SC / 2, y - s.shape[0] / SC * 0.62)
    drift(mid, 60, ['#9ae8ff', '#ffffff'], 12, a=220)
    floor = wall(GRAY_L, True, seed=45, bumps=1.4, out='#0c0620')
    obs = {'low': [A.amyloid(26, 16)], 'tall': [A.tangle(18, 60)], 'hang': [], 'float': [axon_seg(90), axon_seg(60)], 'huge': [tower(lambda h: A.tangle(20, int(h), seed=9))]}
    return dict(far=far, mid=crop(mid), floor=floor, ceil=None, obs=obs, coin='o2', special='omega')


def axon_seg(L):
    return A.axon_cross(L)


def T_pyramidal():
    return T_neurons('violet', 'pyramidal')


def T_hippo():
    return T_neurons('blue', 'pyramidal')


def T_purkinje():
    return T_neurons('rose', 'purkinje')


# ------------------------------------------------------------------ 11. white matter: fibre tracts
WHITE_L = [(2, ramp('#b8b0d0', '#dcd6ec', '#f8f4ff', n=4), 'endo'), (30, ramp('#8a86a8', '#b0aecc', '#d4d2ea', '#f0eefc', n=6), 'white')]


def T_fibres():
    far = gradient(H, ['#0e0c1c', '#161428', '#1e1c36', '#161428'])
    c3 = three(far)
    R = RS(61)
    # long myelinated axons running along the way you go: continuous white sheaths, a bare node every so often,
    # in loose bundles with dark space between (far ones dimmer and thinner)
    y, x = grid(H, 3 * WT)
    lanes = [24, 31, 52, 59, 66, 88, 95, 118, 125, 132]
    bgc = hexc('#161428')
    for k, yy in enumerate(lanes):
        dim = [0.55, 0.4, 0.5, 0.3, 0.45, 0.2, 0.35, 0.1, 0.25, 0.15][k]
        th = 4 if dim > 0.3 else 5
        node = int(R.uniform(26, 40))
        xr = x[0]
        yc = yy + 1.5 * np.sin(xr * TAU * (2 + k % 3) / WT + k)              # (3WT*SC,)
        r0, r1 = px(yy - 6), px(yy + 7)
        ys = y[r0:r1, :1]
        dy = ys - yc[None, :]                                                # rows x cols
        u = np.clip((dy + th / 2) / th, 0, 1)
        top = np.array([236, 234, 248], np.float32)
        col = top * (1 - 0.45 * u[..., None]) + np.array([40, 36, 70], np.float32) * 0.45 * u[..., None]
        col = col * (1 - dim) + bgc * dim
        # nodes of Ranvier: the sheath tapers to the bare axon (orange) for a short gap
        xm = np.mod(np.mod(xr, WT), node)
        dn = np.minimum(xm, node - xm)
        rr = (th / 2) * np.sqrt(np.clip((dn - 0.9) / 1.8, 0, 1))[None, :]
        sheath = np.clip((rr - np.abs(dy)) * SC + 0.5, 0, 1) * (rr > 0)
        edge = np.clip((rr + 0.6 - np.abs(dy)) * SC + 0.5, 0, 1) * (rr > 0)
        cyl = np.sqrt(np.clip(1 - (dy / np.maximum(rr, 0.3)) ** 2, 0, 1))
        lit = np.clip(0.35 + 0.65 * cyl - 0.35 * np.clip(dy / np.maximum(rr, 0.3), 0, 1), 0, 1)
        spec = np.clip(1 - np.abs(dy / np.maximum(rr, 0.3) + 0.35) / 0.18, 0, 1) * 0.5
        col = top * lit[..., None] + np.array([40, 36, 70], np.float32) * (1 - lit[..., None])
        col = col * (1 - spec[..., None]) + 255 * spec[..., None]
        col = col * (1 - dim) + bgc * dim
        reg = c3[r0:r1]
        over(reg, np.broadcast_to(hexc('#0c0a18'), reg.shape[:2] + (3,)), edge)
        over(reg, col, sheath)
        ax = np.clip((0.9 - np.abs(dy)) * SC + 0.5, 0, 1) * (rr < 0.9)
        over(reg, np.broadcast_to(hexc('#c87a3a'), reg.shape[:2] + (3,)), ax)
    for (yy_, kw) in ((41, 3), (77, 4), (109, 5)):        # capillaries running between the bundles, red cells in them
        capillary_band(c3, yy_, kw, '#6a2a40', '#3a0c1c', amp=1.5)
        for k in range(18):
            x_ = R.uniform(0, WT); y_ = yy_ + 1.5 * np.sin(x_ * TAU * kw / WT)
            put(c3, A.rbc_small(R.uniform(0.5, 0.9)), x_ - 3, y_ - 2, 0.9)
    for k in range(14):                                   # oligodendrocytes among them
        s = astro_sprite(5, R, '#8a90c0', '#2a2a50')
        put(c3, s, R.uniform(0, WT) - s.shape[1] / SC / 2, R.uniform(20, GY - 10) - s.shape[0] / SC / 2)
    far = crop(c3); haze(far, '#161428', 0.22)
    floor = wall(WHITE_L, True, seed=65, bumps=0.8, out='#100e20')
    ceil = wall([(2, WHITE_L[0][1], 'endo'), (24, WHITE_L[1][1], 'white')], False, seed=66, bumps=0.8, out='#100e20')
    obs = {'low': [oligo()], 'tall': [cross_bundle(60)], 'hang': [flip_v(cross_bundle(hang_len()))], 'float': [macrophage(20)], 'huge': [tower(lambda h: cross_bundle(int(h)))]}
    return dict(far=far, mid=None, floor=floor, ceil=ceil, obs=obs, coin='o2', special='omega')


def oligo():
    spr = canvas(26, 18)
    R = RS(7)
    A.astrocyte(spr, 13, 11, 7, R, '#a8b0e0', '#2a2a50')
    return spr


def cross_bundle(h=60):
    """a bundle of fibres crossing the tract upright: white sheaths stacked"""
    spr = canvas(14, h + 2)
    A.stroke(spr, [(6.5, 0), (6.5, h)], 2.2, '#e8a050', scale=1.0)
    y = h
    while y > 0:
        seg = 12
        yy, xx = grid(seg, 8)
        m = ((xx - 3.5) ** 2 + (yy - 3) ** 2 <= 9) | ((xx - 3.5) ** 2 + (yy - (seg - 4)) ** 2 <= 9) | ((yy >= 3) & (yy <= seg - 4))
        s = A.mask_sprite(m, ramp('#8a8098', '#c0b8d0', '#e8e2f2', '#ffffff'), '#2a2238', soft=1.0)
        paste(spr, s, 2, y - seg)
        y -= seg + 2
    return spr


# ------------------------------------------------------------------ 12. capillary beds: the organ's own tissue seen through a thin wall
ORG = {
    'liver': ('#2a0c10', ramp('#5a2420', '#7e3a30', '#a05444', '#c07060', '#d88c78', n=6), '#3a1450'),
    'gallbladder': ('#1c1e0c', ramp('#3a3a14', '#5a5a20', '#7a7a2c', '#9a9a40', '#bcbc5a', n=6), '#2a2a50'),
    'pancreas': ('#24081a', ramp('#4a1438', '#6e2050', '#923068', '#b44882', '#d8689e', n=6), '#200a40'),
    'islet': ('#24081a', ramp('#4a1438', '#6e2050', '#923068', '#b44882', '#d8689e', n=6), '#200a40'),
    'spleen': ('#20040a', ramp('#4a0810', '#6e1018', '#921c24', '#b02c34', '#cc4448', n=6), '#2a0a3a'),
    'adrenal': ('#241a08', ramp('#5a4418', '#7e6226', '#a08238', '#c4a454', '#e0c478', n=6), '#3a2a50'),
    'kidney': ('#240a10', ramp('#5a2028', '#7e3038', '#a2464c', '#c26266', '#de8484', n=6), '#2a0a40'),
    'glomerulus': ('#240a10', ramp('#5a2028', '#7e3038', '#a2464c', '#c26266', '#de8484', n=6), '#2a0a40'),
    'lung': ('#140c18', ramp('#4a2030', '#6e3044', '#924458', '#b45c70', '#d07c8c', n=6), '#2a0a40'),
    'myocard': ('#1e040c', ramp('#4a0a18', '#6e1426', '#922034', '#b03244', '#cc4a58', n=6), '#2a0830'),
    'thyroid': ('#200810', ramp('#4a1830', '#6e2a48', '#923e60', '#b45878', '#d07894', n=6), '#200a40'),
    'villus': ('#2a0c14', ramp('#5a1e2a', '#7e2e3a', '#a2444e', '#c25e66', '#de8080', n=6), '#2a0a40'),
}


def organ_far(organ, far):
    bg, cr, nc = ORG[organ]
    h = H
    y, x = grid(h, WT)
    if organ in ('liver', 'pancreas', 'islet', 'adrenal', 'thyroid', 'kidney', 'glomerulus'):
        n = {'liver': 520, 'pancreas': 160, 'islet': 160, 'adrenal': 420, 'thyroid': 70, 'kidney': 90, 'glomerulus': 90}[organ]
        cb, d, idx = pcells(h, n, 71, sy=1.0)
        sd = seeds(h, n, 71, sy=1.0)
        R = RS(72)
        tone = R.uniform(0.35, 0.75, n)[idx]
        sh = tone - 0.25 * np.clip((cb - 0.6) / 0.3, 0, 1)
        dxs = np.mod(x - sd[idx, 0] + WT / 2, WT) - WT / 2
        dys = y - sd[idx, 1]
        if organ == 'liver':
            # sinusoids: wavy channels between the plates of cells
            ch = np.clip((1.6 - np.abs(np.mod(y + 12 * np.sin(x * TAU * 7 / WT), 26) - 13)) * SC * 0.5 + 0.5, 0, 1)
            sh = sh * (1 - ch) + 0.05 * ch
        if organ == 'thyroid':
            k2 = np.clip((17 - d) * SC * 0.5 + 0.5, 0, 1); k1 = np.clip((13 - d) * SC * 0.5 + 0.5, 0, 1)
            sh = sh * (1 - k2) + 0.45 * k2; sh = sh * (1 - k1) + 0.85 * k1                # colloid inside, a ring of cells
            sh = sh - 0.08 * np.clip(1 - np.abs(d - 13) * 2, 0, 1)
        if organ in ('kidney', 'glomerulus'):
            ang = np.arctan2(dys, dxs)
            cellb = np.clip(1 - np.abs(np.mod(ang * 13 / TAU, 1.0) - 0.5) / 0.06, 0, 1)
            epi = 0.62 - 0.16 * cellb + 0.08 * np.clip((d - 4) / 8, 0, 1)
            k2 = np.clip((12.5 - d) * SC * 0.5 + 0.5, 0, 1); k1 = np.clip((4 - d) * SC * 0.5 + 0.5, 0, 1)
            sh = sh * (1 - k2) + epi * k2; sh = sh * (1 - k1) + 0.95 * k1   # tubule: lumen and cuboidal ring
            sh = sh - 0.3 * np.clip(1 - np.abs(d - 12.8) / 0.45, 0, 1)
        if organ in ('pancreas', 'islet'):
            ang = np.arctan2(dys, dxs)
            wedge = np.clip(1 - np.abs(np.mod(ang * 7 / TAU, 1.0) - 0.5) / 0.08, 0, 1)       # the borders between the cells
            sh = 0.5 + 0.18 * np.clip(d / 12, 0, 1) - 0.18 * wedge * np.clip((d - 2.5) / 2, 0, 1)
            sh = sh + 0.35 * np.clip((3.2 - d) / 1.2, 0, 1)                                  # the pale lumen
            sh = sh - 0.25 * np.clip((cb - 0.6) / 0.3, 0, 1)
            sh = ndimage.gaussian_filter(sh, 0.3 * SC, mode=('reflect', 'wrap'))
        if organ == 'adrenal':
            RV = RS(73)
            P = np.c_[RV.uniform(0, WT, 9000), RV.uniform(0, h, 9000)]
            vac = spots(y.shape, P, RV.uniform(0.5, 1.1, 9000), WT) * np.clip((0.6 - cb) * 5, 0, 1)
            sh = sh + 0.3 * vac
        rgb = ramp_col(cr, np.clip(sh, 0, 1))
        far[..., :3] = rgb; far[..., 3] = 255
        # nuclei
        if organ not in ('thyroid', 'kidney', 'glomerulus'):
            for k, (px_, py) in enumerate(sd):
                for off in (0, WT, -WT):
                    ellipse_soft(far, px_ + off + 0.2, py + 0.2, 1.35, 1.15, nc, 215)
                    disc(far, px_ + off - 0.3, py - 0.6, 0.4, '#c8a0e0', 150)
        else:
            ang = np.arctan2(dys, dxs)
            if organ == 'thyroid':
                ring = np.clip(1 - np.abs(d - 15) * 1.2, 0, 1)
                dots = ring * np.clip((np.sin(ang * 16) - 0.2) * 3, 0, 1)
            else:
                ring = np.clip(1 - np.abs(d - 9.5) * 0.9, 0, 1)
                dots = ring * np.clip((np.cos(ang * 13) - 0.35) * 3, 0, 1)
            blend(far, hexc(nc), dots * 0.85)
        if organ == 'islet':
            for (cx_, cy_, rx_, ry_) in ((WT * 0.5, 90, 160, 70), (0, 70, 120, 50)):
                dxw = np.mod(x - cx_ + WT / 2, WT) - WT / 2
                rr_ = np.sqrt((dxw / rx_) ** 2 + ((y - cy_) / ry_) ** 2)
                e = np.clip((1 - rr_) * min(rx_, ry_) * SC * 0.5 + 0.5, 0, 1)
                cbi, di, _ = pcells(h, 900, 79 + int(cx_ > 0), sy=1.0, border=0.8)
                isl = ramp_col(ramp('#6a3a70', '#9a6aa0', '#c49ccc', n=3), np.clip(0.55 + 0.3 * np.clip(1 - di / 3, 0, 1) - 0.4 * cbi, 0, 1))
                blend(far, isl, e)
                cap = np.clip(1 - np.abs(rr_ - 1) * min(rx_, ry_) / 0.8, 0, 1)
                blend(far, hexc('#5a1a48'), cap * 0.8)
        if organ == 'glomerulus':
            # a few glomerular tufts: balls of looping capillaries
            for gx in (WT * 0.15, WT * 0.5, WT * 0.82):
                for k in range(26):
                    a = RS(int(gx) + k).uniform(0, TAU); rr_ = RS(int(gx) + k + 99).uniform(8, 34)
                    cx, cy = gx + np.cos(a) * rr_, 84 + np.sin(a) * rr_ * 0.8
                    loop = ellipse_mask(13, 13) & ~ellipse_mask(13, 13, 6, 6, 3.5, 3.5)
                    ls = np.zeros(loop.shape + (4,), np.float32); ls[..., :3] = hexc('#d04050'); ls[..., 3] = smooth_mask(loop) * 255
                    yy_, xx_ = grid(13, 13)
                    ls[..., :3] *= (0.75 + 0.35 * np.clip(1 - (yy_ - 2) / 10, 0, 1))[..., None]
                    for off in (0, WT, -WT):
                        paste(far, outline(ls, '#3a0812', width=0.6), cx - 7 + off, cy - 7)
        D_ = d
        Dat = lambda x_, y_: D_[min(px(y_ + 0.5), D_.shape[0] - 1), min(px(np.mod(x_, WT) + 0.5), D_.shape[1] - 1)]
        CBat = lambda x_, y_: cb[min(px(y_ + 0.5), cb.shape[0] - 1), min(px(np.mod(x_, WT) + 0.5), cb.shape[1] - 1)]
        if organ == 'liver':
            # bile canaliculi: fine greenish lines between the liver cells
            blend(far, hexc('#6a7a2a'), np.clip((cb - 0.82) * 6, 0, 1) * 0.16)
            # Kupffer cells (the liver's macrophages) lying in the sinusoids
            R2 = RS(91)
            for k in range(24):
                xk = R2.uniform(0, WT); kk = R2.randint(0, 7)
                yk = 13 + 26 * kk - 12 * np.sin(xk * TAU * 7 / WT)
                if 4 < yk < h - 6:
                    for off in (0, WT, -WT):
                        paste(far, kupffer(k), xk - 8 + off, yk - 4)
        if organ in ('kidney', 'glomerulus'):
            # peritubular capillaries between the tubules: red cells seen end-on
            red_dots(far, lambda x_, y_: Dat(x_, y_) > 15.5, 2600, 92, r=(0.45, 0.75))
        if organ == 'glomerulus':
            for gx in (WT * 0.15, WT * 0.5, WT * 0.82):         # Bowman's capsule round each tuft
                pts = [(gx + np.cos(a_) * 42, 84 + np.sin(a_) * 34) for a_ in np.linspace(0, TAU, 160)]
                for off in (0, WT, -WT):
                    A.stroke(far, [(p + off, q) for p, q in pts], 2.0, '#3a0812', 230, scale=1.0)
                    A.stroke(far, [(p + off, q) for p, q in pts], 1.0, '#e0a0a8', 230, scale=1.0)
        if organ == 'thyroid':
            red_dots(far, lambda x_, y_: Dat(x_, y_) > 17.5, 1400, 93, r=(0.45, 0.7))
            # resorption vacuoles: small pale bubbles at the edge of the colloid
            R2 = RS(94)
            for k in range(900):
                xk, yk = R2.uniform(0, WT), R2.uniform(0, h)
                if 10.6 < Dat(xk, yk) < 12.4:
                    for off in (0, WT, -WT):
                        disc(far, xk + off, yk, R2.uniform(0.5, 0.9), '#f4d8e4', 170)
        if organ in ('pancreas', 'islet'):
            # zymogen granules: bright little grains toward the middle of each acinus
            red_dots(far, lambda x_, y_: 2.8 < Dat(x_, y_) < 6.5, 6000, 95, r=(0.25, 0.42), col='#ffb0a0', a=0.75)
        if organ == 'islet':
            for (cx_, cy_, rx_, ry_) in ((WT * 0.5, 90, 160, 70), (0, 70, 120, 50)):
                inside = lambda x_, y_, cx_=cx_, cy_=cy_, rx_=rx_, ry_=ry_: ((np.mod(x_ - cx_ + WT / 2, WT) - WT / 2) / rx_) ** 2 + ((y_ - cy_) / ry_) ** 2 < 0.85
                red_dots(far, inside, 2500, 96 + int(cx_ > 0), r=(0.45, 0.7))
        if organ == 'adrenal':
            red_dots(far, lambda x_, y_: CBat(x_, y_) > 0.75, 5000, 97, r=(0.4, 0.65))
    elif organ == 'lung':
        # alveoli: round air sacs (dark) between septa thick with capillaries; deeper sacs show through, dimmer
        cb, d, idx = pcells(h, 120, 74, sy=1.0, border=1.0)
        gap = (1 - cb)                                                # 0 on a border .. 1 well inside
        _, d2, _ = pcells(h, 120, 74, sy=1.0, border=1.0)
        from scipy.spatial import cKDTree
        sd = seeds(h, 120, 74, sy=1.0)
        # distance to the cell border approximated from the two nearest seeds
        cbw, dd, _ = pcells(h, 120, 74, sy=1.0, border=9.0)
        wallness = np.clip((cbw - 0.62) / 0.12, 0, 1)                   # septum where the border is near
        wallness = blur(wallness, 0.8, wrap=True)
        air = np.clip(0.15 + dd / 90, 0, 0.45)
        far[..., :3] = ramp_col(ramp('#1a1428', '#241c36', '#342a4c', n=3), air); far[..., 3] = 255
        # the far side of each sac: a dim curved inner wall
        rim = np.clip((cbw - 0.45) / 0.17, 0, 1) * (1 - wallness)
        blend(far, ramp_col(ramp('#2a1a30', '#4a2a40', n=2), rim), rim * 0.7)
        sep = ramp_col(cr, np.clip(0.25 + 0.6 * wallness + 0.1 * cbw, 0, 1))
        blend(far, sep, np.clip(wallness * 1.4, 0, 1))
        R = RS(78)
        P = np.c_[R.uniform(0, WT, 5200), R.uniform(0, h, 5200)]
        caps = spots(y.shape, P, R.uniform(0.45, 0.7, 5200), WT) * np.clip((wallness - 0.5) * 3, 0, 1)
        blend(far, hexc('#d02c40'), caps * 0.9)
        P2 = np.c_[R.uniform(0, WT, 900), R.uniform(0, h, 900)]
        nuc = spots(y.shape, P2, 0.6, WT) * np.clip((wallness - 0.6) * 3, 0, 1)
        blend(far, hexc(nc), nuc * 0.8)
        # type II cells bulging from the septa (pale, foamy) and macrophages wandering in the air sacs
        P3 = np.c_[R.uniform(0, WT, 700), R.uniform(0, h, 700)]
        t2 = spots(y.shape, P3, R.uniform(0.9, 1.4, 700), WT) * np.clip((wallness - 0.3) * 3, 0, 1)
        blend(far, hexc('#e8c4cc'), t2 * 0.75)
        W_ = wallness
        R4 = RS(98)
        for k in range(16):
            xk, yk = R4.uniform(0, WT), R4.uniform(8, h - 12)
            if W_[min(px(yk + 0.5), W_.shape[0] - 1), px(xk + 0.5) % W_.shape[1]] < 0.15:
                for off in (0, WT, -WT):
                    paste(far, macrophage(int(R4.uniform(8, 11))), xk + off - 5, yk - 5)
    elif organ == 'spleen':
        far[..., :3] = ramp_col(ramp('#2a0408', '#3a0810', '#4a0c16', n=3), np.clip(0.5 + 0.2 * per_sin(x, 13) * np.sin(y * 0.1), 0, 1)); far[..., 3] = 255
        R = RS(75)
        c3 = three(far)
        for k in range(420):
            put(c3, A.rbc_small(R.uniform(0.4, 1.0)), R.uniform(0, WT), R.uniform(8, h - 10))
        for k in range(14):
            put(c3, macrophage(int(R.uniform(11, 15))), R.uniform(0, WT), R.uniform(10, h - 30), 0.55)     # far behind: dim, unlike the ones in your way
        for k in range(22):                               # the walls of the venous sinuses: long thin pale rods
            x0, y0 = R.uniform(0, WT), R.uniform(10, h - 10); a0 = R.uniform(-0.4, 0.4); L = R.uniform(40, 120)
            pts = [(x0 + np.cos(a0) * s_, y0 + np.sin(a0) * s_ + 4 * np.sin(s_ * 0.04 + k)) for s_ in np.linspace(0, L, 40)]
            for off in (0, WT, 2 * WT):
                A.stroke(c3, [(p + off, q) for p, q in pts], 1.4, '#d89aa0', 80, scale=1.0)
        far[...] = crop(c3)
    elif organ == 'myocard':
        yl = np.mod(y, 11.0)
        sh = 0.35 + 0.3 * np.sin(yl / 11 * np.pi) - 0.12 * band_line(x, 3, 0.6) - 0.3 * band_line(x + np.floor(y / 11) * 37, 90, 0.9)
        far[..., :3] = ramp_col(cr, np.clip(sh, 0, 1)); far[..., 3] = 255
        R = RS(76)
        for k in range(160):
            px_, py = R.uniform(0, WT), (int(R.uniform(0, h / 11)) * 11 + 5.5)
            for off in (0, WT, -WT):
                ellipse_soft(far, px_ + off, py, 2.6, 0.8, nc, 200)
        # capillaries between the fibres: red cells in a row along each gap
        red_dots(far, lambda x_, y_: abs(np.mod(y_, 11.0) - 0.0) < 0.9 or abs(np.mod(y_, 11.0) - 11.0) < 0.9, 9000, 99, r=(0.45, 0.65))
    elif organ in ('gallbladder', 'villus'):
        far[..., :3] = ramp_col(ramp(bg, cr[0], cr[1], n=3), np.clip(0.4 + 0.2 * per_sin(x, 17), 0, 1)); far[..., 3] = 255
        c3 = three(far)
        R = RS(77)
        for k in range(70):
            hh = int(R.uniform(30, 90))
            cols = ramp('#4a4a18', '#6e6e26', '#929238', '#b4b450', '#d4d472') if organ == 'gallbladder' else None
            v = A.villus_real(hh, int(R.uniform(8, 12)), k + 300, cols=cols, dim=0.25)
            put(c3, v, R.uniform(0, WT), GY - hh + 6)
        if organ == 'villus':                              # the lacteal running across, white, and the capillary net
            capillary_band(c3, 70, 3, '#e8dcc8', '#fff6e8', amp=4)
            # the capillary net round the lacteal: two wavy vessels along it, joined by short irregular links
            xs_ = np.arange(0, 3 * WT, 1.5)
            for sgn, ph_ in ((-1, 0.7), (1, 2.1)):
                yy_ = 70 + 4 * np.sin(xs_ * TAU * 3 / WT) + sgn * (9 + 1.6 * np.sin(xs_ * TAU * 29 / WT + ph_) + 0.8 * np.sin(xs_ * TAU * 71 / WT))
                A.stroke(c3, list(zip(xs_, yy_)), 1.1, '#c8283a', 180, scale=1.0)
            for k in range(70):
                x0 = R.uniform(0, WT); yc_ = 70 + 4 * np.sin(x0 * TAU * 3 / WT)
                pts = [(x0 + 2.5 * np.sin(u * 3 + k), yc_ - 9 + 18 * u) for u in np.linspace(0, 1, 16)]
                for off in (0, WT, 2 * WT):
                    A.stroke(c3, [(p + off, q) for p, q in pts], 0.8, '#c8283a', 120, scale=1.0)
        wet_glints(c3, 500, 100, pct=75, a=110)
        far[...] = crop(c3)
    return bg


def T_bed(organ='liver'):
    far = np.zeros((px(H), px(WT), 4), np.float32)
    bg = organ_far(organ, far)
    far[..., 3] = 255
    haze(far, bg, 0.3)
    lumen_glow(far, '#d06070', 0.1)
    mid = wide()
    rbc_flow(mid, 18, 81, y0=40, y1=GY - 30, size=(11, 15), alpha=0.95)
    cr = ORG[organ][1]
    layers = [(2, ramp('#d098a0', '#f0c4c4', '#ffe4e0', n=4), 'endo'), (1, ramp('#a06070', '#c08090', n=2), 'endo'),
              (30, cr, 'loose')]
    floor = wall(layers, True, seed=85, bumps=0.6, out='#1a0408')
    ceil = wall([(2, layers[0][1], 'endo'), (1, layers[1][1], 'endo'), (20, cr, 'loose')], False, seed=86, bumps=0.6, out='#1a0408')
    flt = macrophage(22) if organ in ('lung', 'spleen', 'liver') else A.neutrophil(20, seed=11)
    obs = {'low': [rouleaux(5), A.neutrophil(16, seed=12)],
           'tall': [rouleaux(12, upright=True)],
           'hang': [],
           'float': [flt, A.neutrophil(18, seed=13)],
           'huge': [tower(lambda h: rouleaux(int(round((h - 6) / 5)), upright=True))]}
    coin = 'vitC' if organ in ('villus',) else 'o2'
    special = {'liver': 'iron', 'spleen': 'iron', 'villus': 'fiber', 'gallbladder': 'omega'}.get(organ, 'iron')
    return dict(far=far, mid=crop(mid), floor=floor, ceil=ceil, obs=obs, coin=coin, special=special)


def rouleaux(n=5, upright=False):
    """red cells stacked like coins (rouleaux): lying (low) or standing (a column)"""
    if not upright:
        out = canvas(18, 4 + n * 3)
        for k in range(n):
            paste(out, rbc(14, 0.3), 1, out.shape[0] / SC - 7 - k * 3)
        return out
    out = canvas(18, 6 + n * 5)
    for k in range(n):
        paste(out, rbc(14, 0.42), 1, out.shape[0] / SC - 9 - k * 5)
    return out


for _o in ORG:
    globals()['T_' + _o] = (lambda o: (lambda: T_bed(o)))(_o)


# ------------------------------------------------------------------ 13. the eye (eye.py)
from eye import T_retina, T_vitreous, T_lens, T_iris, T_cornea  # noqa: E402

# ------------------------------------------------------------------ 14. looks of their own for places that shared one (variants.py)
from variants import (T_renalart, T_carotid, T_vertebral, T_sma, T_efferent, T_pulmvein, T_ivc, T_pulmart,  # noqa: E402
                      T_latrium, T_lventricle, T_bronchiole, T_temporal, T_parietal, T_occipital, T_medulla, T_opticnerve,
                      T_duodenum, T_ileum, T_cecum, T_rectum, T_anus)
