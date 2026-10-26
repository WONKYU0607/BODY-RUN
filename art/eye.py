# The eye, from the back to the front: retina, vitreous, lens, the pupil between the iris, cornea. Same layer scheme
# as themes.py (far, mid, floor, ceiling, obstacles); wrap-safe: things are drawn at x and x - WT on one tile.
import numpy as np
from scipy import ndimage
from art import (H, SC, px, grid, canvas, ramp, ramp_col, hexc, ellipse_mask, outline, paste, over, blur, disc,
                 ellipse_soft, dome_shade, highlight, smooth_mask)
import anatomy as A
from tiles import WT, GY, CH, TAU, wide, crop, put, per_sin, gradient, haze, pcells, wall, band_line
import themes as T

RS = np.random.RandomState


def putw(arr, spr, x, y, a=1.0):
    """paste on one tile, wrapping across its seam"""
    paste(arr, spr, x, y, a)
    w = spr.shape[1] / SC
    if x + w > WT:
        paste(arr, spr, x - WT, y, a)
    if x < 0:
        paste(arr, spr, x + WT, y, a)


def noise(shape, sigma, seed, wrap=True):
    R = RS(seed)
    n = ndimage.gaussian_filter(R.uniform(-1, 1, shape).astype(np.float32), sigma * SC, mode='wrap' if wrap else 'reflect')
    return n / max(np.abs(n).max(), 1e-6)


def layer_rgba(rgb, k):
    out = np.zeros(k.shape + (4,), np.float32)
    out[..., :3] = rgb; out[..., 3] = np.clip(k, 0, 1) * 255
    return out


def column_profile(L, w, parts):
    """a standing cell drawn from a radius profile: parts = [(y0, y1, r0, r1, kind)], radius eased from r0 to r1
    -> canvas, coverage, radius per row, kind index per row, x centre"""
    W_ = w + 2
    y, x = grid(L + 1, W_)
    cx = (W_ - 1) / 2
    yy = y[:, 0]
    r = np.zeros_like(yy); kind = np.full(yy.shape, -1)
    for i, (y0, y1, r0, r1, _) in enumerate(parts):
        t = np.clip((yy - y0) / max(y1 - y0, 1e-3), 0, 1)
        sel = (yy >= y0) & (yy < y1)
        rr = r0 + (r1 - r0) * (0.5 - 0.5 * np.cos(np.pi * t))
        r = np.where(sel, rr, r); kind = np.where(sel, i, kind)
    # round the very top and the very bottom
    top, bot = parts[0][0], parts[-1][1]
    r = r * np.sqrt(np.clip((yy - top) / 1.2, 0, 1)) * np.sqrt(np.clip((bot - yy) / 1.0, 0, 1))
    return y, x, cx, r, kind


def shade_column(y, x, cx, r, kind, ramps, stripes=None, grain_seed=None, out=None):
    """cylinder shading of a standing cell, one ramp per part; stripes: {part: (period, depth)}"""
    rr = np.maximum(r[:, None], 1e-3)
    u = (x - cx) / rr
    cov = np.clip((r[:, None] - np.abs(x - cx)) * SC + 0.5, 0, 1)
    lit = np.clip(0.22 + 0.78 * np.sqrt(np.clip(1 - u * u, 0, 1)) - 0.28 * u, 0, 1)
    spec = np.clip(1 - np.abs(u + 0.45) / 0.16, 0, 1) * 0.35
    rgb = np.zeros(x.shape + (3,), np.float32)
    for i, rmp in enumerate(ramps):
        sel = (kind == i)[:, None]
        sh = lit.copy()
        if stripes and i in stripes:
            per, dep = stripes[i]
            sh = sh - dep * band_line(y, per, per * 0.35)
        if grain_seed is not None and i == 0:
            n = noise(x.shape, 0.18, grain_seed, wrap=False)
            sh = sh + 0.12 * n
        c = ramp_col(rmp, np.clip(sh, 0, 1))
        rgb = np.where(sel[..., None] if sel.ndim == 2 else sel, c, rgb)
    rgb = rgb * (1 - spec[..., None]) + 255 * spec[..., None]
    spr = layer_rgba(rgb, cov)
    if out:
        spr = outline(spr, out, width=0.6)
    return spr


# ------------------------------------------------------------------ 1. retina: among the rods and cones
ROD_IS = ramp('#4a2838', '#94606e', '#d4a4ae', '#f6dce0')
ROD_OS = ramp('#2e0a2c', '#6c1c5c', '#a8408a', '#dc80bc')
CONE_OS = {'L': ramp('#3a0c14', '#7a2430', '#bc4c50', '#ec9488'), 'M': ramp('#0e2a14', '#24603a', '#46a060', '#94dca0'),
           'S': ramp('#0c1640', '#243c88', '#4870c8', '#9ab8f4')}
CONE_IS = ramp('#4a3028', '#947060', '#d4b0a0', '#f8e6dc')


def rod(L, w=4.0, seed=0, out=None):
    """a rod standing (top = inner segment, then the thin connecting cilium, then the outer segment: a stack of
    discs full of rhodopsin, 'visual purple')"""
    R = RS(seed)
    a = L * R.uniform(0.33, 0.47)
    parts = [(0, a, w * 0.46, w * 0.5, 'is'), (a, a + 1.6, w * 0.16, w * 0.16, 'cil'), (a + 1.6, L, w * 0.42, w * 0.4, 'os')]
    y, x, cx, r, kind = column_profile(L, w, parts)
    return shade_column(y, x, cx, r, kind, [ROD_IS, ROD_IS, ROD_OS], stripes={2: (0.6, 0.2)}, grain_seed=seed, out=out)


def cone(L, w=6.4, typ='L', seed=0, out=None):
    """a cone: a fat inner segment, the cilium, a short tapering outer segment"""
    R = RS(seed)
    a = L * R.uniform(0.5, 0.56)
    os_len = L * 0.3
    parts = [(0, a * 0.35, w * 0.2, w * 0.5, 'is'), (a * 0.35, a, w * 0.5, w * 0.36, 'is'), (a, a + 1.4, w * 0.13, w * 0.13, 'cil'),
             (a + 1.4, a + 1.4 + os_len, w * 0.34, w * 0.1, 'os')]
    y, x, cx, r, kind = column_profile(a + 1.4 + os_len, w, parts)
    return shade_column(y, x, cx, r, kind, [CONE_IS, CONE_IS, CONE_IS, CONE_OS[typ]], stripes={3: (0.55, 0.18)}, grain_seed=seed, out=out)


def rpe_pat(sh, x, ld, u, shape, h, R):
    """retinal pigment epithelium: a row of cells packed with melanin, the nucleus low in each"""
    xx = x + 0.9 * per_sin(x, 37, 1.0)
    border = band_line(xx, 6.5, 0.45)
    gran = noise(shape, 0.22, 501)
    gran = np.clip((gran - 0.15) * 4, 0, 1) * np.clip((0.7 - u) * 3, 0, 1)
    cxp = np.mod(xx, 6.5) - 3.25
    nuc = np.clip(1 - np.sqrt((cxp / 2.0) ** 2 + ((ld - 4.3) / 1.1) ** 2), 0, 1) ** 0.5
    return sh - 0.32 * border - 0.42 * gran + 0.35 * nuc + 0.05


def choroid_pat(sh, x, ld, u, shape, h, R):
    """the choroid: wide vessels side by side, red cells in them"""
    lum = np.cos(x * TAU * 160 / WT + 1.3 * np.sin(ld * 0.8)) * np.cos(ld * 1.6 + 0.6 * np.sin(x * 0.31))
    lum = np.clip((lum - 0.25) * 3, 0, 1)
    cells = np.clip((noise(shape, 0.3, 502) - 0.35) * 5, 0, 1) * lum
    return sh - 0.5 * lum + 0.45 * cells


def onl_pat(sh, x, ld, u, shape, h, R):
    """the outer nuclear layer: the rods' and cones' cell bodies, nuclei packed tight"""
    cb, d, _ = pcells(h, int(WT * h / 5.2), 503, sy=1.0, border=0.5)
    nuc = np.clip(1 - d / 1.05, 0, 1) ** 0.6
    return sh + 0.1 - 0.62 * nuc - 0.12 * cb


def microvilli(c3, edge_w, e0, top_edge):
    """the pigment cells reach up between the outer segments' tips with fine processes"""
    R = RS(504)
    for k in range(int(WT / 0.8)):
        x = R.uniform(0, WT)
        ex = e0 + np.interp(x, np.arange(WT), edge_w)
        L = R.uniform(1.4, 3.0)
        for off in (0, WT, 2 * WT):
            A.stroke(c3, [(x + off, ex + 0.3), (x + off + R.uniform(-0.3, 0.3), ex - L)], 0.32, '#3a1c12', 230, scale=1.0)


def drusen(w=24, h=13, seed=1):
    """a druse: a yellow deposit of waste under the pigment layer, bulging up"""
    R = RS(seed)
    y, x = grid(h, w)
    m = np.zeros(x.shape, bool)
    for k in range(4):
        cx, cy = R.uniform(w * 0.28, w * 0.72), h * R.uniform(0.45, 0.62)
        rx, ry = R.uniform(w * 0.22, w * 0.34), h * R.uniform(0.34, 0.5)
        m |= ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1
    m &= y <= h - 1
    m |= (((x - w / 2) / (w * 0.47)) ** 2 + ((y - h) / (h * 0.6)) ** 2 <= 1) & (y <= h - 1)
    spr = A.mask_sprite(m, ramp('#6a4a08', '#a8800e', '#dcb424', '#f6dc6a', '#fff4c0'), '#2e2006', soft=1.1, hl_t=0.97)
    A.grain(spr, seed + 3, 0.07, 0.5)
    return spr


def drusen_stack(seeds_, H_):
    ws = [24, 22, 20, 19, 18, 16, 15]
    n = max(2, int(round(H_ / 13)))
    hh = (H_ + 3 * (n - 1)) / n
    return T.stack([drusen(ws[min(i, 6)], hh, s) for i, s in zip(range(n), seeds_)])


def rod_bundle(L, seed=7):
    """two rods side by side, bright and outlined (hanging from the nuclear layer above)"""
    a = rod(L, 5.2, seed); b = rod(L - 6, 4.6, seed + 1)
    out = canvas(11.5, L + 2)
    paste(out, b, 4.8, 0); paste(out, a, -0.2, 1)
    return outline(out, '#1a0618', width=0.7)


def phagosome(d=17, seed=3):
    """a phagosome: a packet of worn-out disc tips swallowed by a pigment cell, drifting"""
    m = ellipse_mask(d, d * 0.92)
    spr = A.mask_sprite(m, ramp('#6a3a10', '#a8661c', '#d89a3a', '#f4c878', '#fff0c8'), '#2a1206', soft=1.4, hl_t=0.975)
    I = spr[SC:-SC, SC:-SC]
    y, x = grid(d * 0.92, d)
    cx, cy = (d - 1) / 2, (d * 0.92 - 1) / 2
    inside = (((x - cx) / (d * 0.3)) ** 2 + ((y - cy) / (d * 0.26)) ** 2) <= 1
    discs = band_line(y + 0.25 * (x - cx), 0.9, 0.38) * inside
    k = smooth_mask(inside) * 0.85
    I[..., :3] = I[..., :3] * (1 - k[..., None]) + hexc('#7a2468') * k[..., None]
    I[..., :3] = I[..., :3] * (1 - 0.45 * discs[..., None]) + hexc('#e6a0d0') * 0.45 * discs[..., None]
    return spr


def T_retina():
    far = gradient(H, ['#0e0612', '#180a1e', '#22102a', '#1a0a20'])
    R = RS(510)
    top, bot = 13.0, GY + 3
    L = bot - top
    # the back row (thin, dim), then the front row with a cone every so often
    back = np.zeros_like(far)
    x = 0.0
    while x < WT:
        s = rod(L + R.uniform(-3, 3), R.uniform(2.8, 3.4), R.randint(1 << 20))
        putw(back, s, x, top + R.uniform(-3, 2), R.uniform(0.7, 1.0))
        x += R.uniform(3.6, 4.6)
    back[..., 3] = blur(back[..., 3], 0.25, wrap=True)
    haze(back, '#1a0a20', 0.72)
    over(far, back[..., :3], back[..., 3] / 255)
    front = np.zeros_like(far)
    x, k = 0.0, 0
    while x < WT - 2:
        if R.uniform() < 0.16:
            typ = R.choice(['L', 'L', 'M', 'M', 'S'])
            s = cone(L * R.uniform(0.62, 0.7), R.uniform(6.0, 7.0), typ, R.randint(1 << 20))
            putw(front, s, x, top + R.uniform(1, 4))
            x += R.uniform(6.6, 7.6)
        else:
            s = rod(L + R.uniform(-3, 3), R.uniform(3.6, 4.3), R.randint(1 << 20))
            putw(front, s, x, top + R.uniform(-3, 2), R.uniform(0.8, 1.0))
            x += R.uniform(5.0, 6.4)
    haze(front, '#1a0a20', 0.42)
    over(far, front[..., :3], front[..., 3] / 255)
    # light falls in from above (through the whole retina): a soft glow at the top, fading down
    yy = (np.arange(far.shape[0], dtype=np.float32) + 0.5) / SC
    g = (np.exp(-((yy - 30) / 50) ** 2) * 0.16)[:, None, None]
    far[..., :3] = far[..., :3] * (1 - g) + hexc('#ffe8f0') * g
    mid = np.zeros((px(H), px(WT), 4), np.float32)
    for k in range(70):                                  # photons coming down: a glint and its short trail
        x0, y0 = R.uniform(0, WT), R.uniform(20, GY - 20)
        tr = canvas(4, 14)
        for j in range(12):
            disc(tr, 1.5, 1 + j, 0.5 + 0.03 * j, '#fff2d0', int(18 + 9 * j))
        disc(tr, 1.5, 12.2, 1.0, '#ffffff', 230)
        b = np.zeros_like(tr); b[..., :3] = hexc('#ffd8f0'); b[..., 3] = blur(tr[..., 3], 0.9) * 0.9
        over(b, tr[..., :3], tr[..., 3] / 255)
        putw(mid, b, x0, y0, 0.85)
    floor = wall([(1.2, ramp('#3a1a10', '#6a3a22', '#8a5030', n=4), 'endo'), (7, ramp('#1a0a06', '#3a1c10', '#6a3a22', '#9a6a44', '#c8a078', n=6), rpe_pat),
                  (1.4, ramp('#b8a088', '#d8c4a8', '#f0e4cc', n=4), 'endo'), (9, ramp('#3a0408', '#6a0a12', '#9a1a20', '#c83a36', '#e8726a', n=6), choroid_pat),
                  (30, ramp('#a8988e', '#cbbcb0', '#e4d8ce', '#f6eee6', n=6), 'white')], True, seed=511, bumps=0.5, out='#140604',
                 surface=microvilli)
    ceil = wall([(1.2, ramp('#8a6aa0', '#b898cc', '#dcc4ec', n=4), 'endo'), (30, ramp('#160c2c', '#30204e', '#58407c', '#8a6aac', '#b89ad0', n=6), onl_pat)],
                False, seed=512, bumps=0.5, out='#0e0618')
    obs = {'low': [drusen(24, 13, 1), drusen(22, 12, 5)],
           'tall': [drusen_stack([11, 12, 13, 14, 15], 58)],
           'hang': [rod_bundle(T.hang_len(), 21)],
           'float': [phagosome(17, 3)],
           'huge': [T.tower(lambda h: drusen_stack(range(40, 48), h))]}
    return dict(far=far, mid=mid, floor=floor, ceil=ceil, obs=obs, coin='o2', special='omega')


# ------------------------------------------------------------------ shared: a twisted strand bundle (vitreous collagen, iris trabeculae)
def rope(h, w=14, cols=None, out='#0a2a34', n=3, per=26, seed=1, fray=0.0, r=None):
    """n strands wound round each other (drawn from fields: the nearest strand in front wins, cylinder-shaded).
    fray: the last `fray` units at the bottom splay apart and thin out"""
    R = RS(seed)
    cols = cols or ramp('#0e3a48', '#2a7488', '#5aaabc', '#a8e0ec', '#e8fcff')
    r = r or w * 0.155
    y, x = grid(h, w + 4)
    cx = (w + 4 - 1) / 2
    yy = y[:, :1]
    amp = w * 0.3
    best_z = np.full(x.shape, -9.0, np.float32); rgb = np.zeros(x.shape + (3,), np.float32); cov = np.zeros(x.shape, np.float32)
    ph0 = R.uniform(0, TAU)
    for i in range(n):
        ph = TAU * yy / per + ph0 + TAU * i / n
        sp = np.clip((yy - (h - fray)) / max(fray, 1e-3), 0, 1) if fray else 0 * yy
        a_ = amp * (1 + 1.4 * sp)
        xi = cx + a_ * np.sin(ph) + (i - (n - 1) / 2) * 2.2 * sp
        zi = np.cos(ph)
        slope = a_ * TAU / per * np.cos(ph)
        ri = r * (1 - 0.55 * sp) * np.sqrt(1 + slope ** 2) * (0.92 + 0.08 * zi)
        ri = ri * np.sqrt(np.clip(yy / 1.0, 0, 1)) * np.sqrt(np.clip((h - 0.5 - yy) / 1.0, 0, 1))
        d = np.abs(x - xi)
        c = np.clip((ri - d) * SC + 0.5, 0, 1)
        u = (x - xi) / np.maximum(ri, 1e-3)
        lit = np.clip(0.25 + 0.75 * np.sqrt(np.clip(1 - u * u, 0, 1)) - 0.3 * u, 0, 1) * (0.78 + 0.22 * zi)
        lit = lit - 0.1 * band_line(yy * 0.35 + 0.9 * (x - xi) + 0.6 * np.sin(yy * 0.7 + i), 0.9, 0.25)   # fibrils along the strand
        top = (c > 0.02) & (zi > best_z)
        rgb = np.where(top[..., None], ramp_col(cols, np.clip(lit, 0, 1)), rgb)
        best_z = np.where(top, zi, best_z)
        cov = np.maximum(cov, c)
    spr = layer_rgba(rgb, cov)
    return outline(spr, out, width=0.65)


def ring_floater(d=18, th=3.6, cols=None, out='#0a2a34'):
    """a ring-shaped floater (like the ring left where the gel comes away from the optic disc)"""
    cols = cols or ramp('#2a5a68', '#5a98a8', '#a0d4e0', '#e4fbff')
    y, x = grid(d, d)
    c = (d - 1) / 2
    rr = np.sqrt((x - c) ** 2 + (y - c) ** 2)
    R0 = d / 2 - th / 2 - 0.2
    dd = np.abs(rr - R0)
    cov = np.clip((th / 2 - dd) * SC + 0.5, 0, 1)
    u = (rr - R0) / (th / 2)
    ang = np.arctan2(y - c, x - c)
    lit = np.clip(0.3 + 0.7 * np.sqrt(np.clip(1 - u * u, 0, 1)) - 0.25 * u * np.sin(ang) - 0.2 * np.cos(ang) * u, 0, 1)
    lit = lit + 0.12 * noise(x.shape, 0.4, 7, wrap=False)
    spr = layer_rgba(ramp_col(cols, np.clip(lit, 0, 1)), cov * 0.93)
    return outline(spr, out, width=0.6)


def knot(w=24, h=14, seed=1, cols=None, out='#0a2a34', fib='#2a6070'):
    """a clump: lumpy, with fibres wound through it"""
    R = RS(seed)
    y, x = grid(h, w)
    m = np.zeros(x.shape, bool)
    for k in range(5):
        cx, cy = R.uniform(w * 0.25, w * 0.75), h * R.uniform(0.45, 0.65)
        rx, ry = R.uniform(w * 0.18, w * 0.3), h * R.uniform(0.3, 0.48)
        m |= ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1
    m |= (((x - w / 2) / (w * 0.46)) ** 2 + ((y - h) / (h * 0.62)) ** 2 <= 1)
    m &= y <= h - 1
    spr = A.mask_sprite(m, cols or ramp('#3a6a78', '#78aebc', '#b8e2ec', '#ecfcff'), out, soft=1.2, hl_t=0.975)
    I = spr[SC:-SC, SC:-SC]
    tmp = np.zeros_like(I)
    for k in range(7):
        x0, y0 = R.uniform(2, w - 2), R.uniform(2, h - 2); a0 = R.uniform(0, TAU)
        pts = [(x0 + np.cos(a0 + 0.4 * np.sin(t)) * t * 2.2, y0 + np.sin(a0 + 0.4 * np.sin(t)) * t * 1.2) for t in np.linspace(-2.5, 2.5, 16)]
        A.stroke(tmp, pts, 0.45, fib, 170, scale=1.0)
    k = tmp[..., 3] / 255 * (I[..., 3] / 255)
    I[..., :3] = I[..., :3] * (1 - k[..., None]) + tmp[..., :3] * k[..., None]
    return spr


def thread(L, seed, wdt=1.0, col='#a8dcea', out='#0a2a34'):
    """a thread floater: a wavy strand with a few beads on it"""
    R = RS(seed)
    spr = canvas(L + 4, 14)
    f1, f2, ph = R.uniform(0.08, 0.16), R.uniform(0.25, 0.4), R.uniform(0, TAU)
    pts = [(2 + t, 7 + 3.2 * np.sin(t * f1 + ph) + 0.9 * np.sin(t * f2)) for t in np.linspace(0, L, int(L) + 2)]
    A.stroke(spr, pts, wdt * 1.9, out, 255, scale=1.0)
    A.stroke(spr, pts, wdt, col, 255, scale=1.0)
    for k in range(int(L / 12)):
        p = pts[R.randint(len(pts))]
        disc(spr, p[0], p[1], wdt * 1.4, out); disc(spr, p[0], p[1], wdt * 0.9, col)
    return spr


# ------------------------------------------------------------------ 2. vitreous: the clear gel
def beams(arr, n, seed, col, a=(0.05, 0.1), ang=(0.15, 0.35), wd=(14, 40)):
    """soft shafts of light slanting down (wrap-safe)"""
    R = RS(seed)
    y, x = grid(arr.shape[0] / SC, WT)
    acc = np.zeros(x.shape, np.float32)
    for k in range(n):
        x0, t, w_, al = R.uniform(0, WT), np.tan(R.uniform(*ang)), R.uniform(*wd), R.uniform(*a)
        d = np.mod(x - x0 - y * t + WT / 2, WT) - WT / 2
        acc += np.exp(-(d / w_) ** 2) * al * np.clip(1.15 - y / 170, 0, 1)
    k = np.clip(acc, 0, 0.5)
    arr[..., :3] = arr[..., :3] * (1 - k[..., None]) + hexc(col) * k[..., None]


def fibrils(arr, n, seed, col, y0, y1, a=(25, 60), wdt=(0.25, 0.5), L=(60, 300), amp=4):
    R = RS(seed)
    for k in range(n):
        x0, yb, Ln = R.uniform(0, WT), R.uniform(y0, y1), R.uniform(*L)
        f1, f2, ph = R.uniform(0.01, 0.03), R.uniform(0.04, 0.09), R.uniform(0, TAU)
        tt = np.linspace(0, Ln, int(Ln / 2) + 2)
        pts = [(x0 + t, yb + amp * np.sin(t * f1 + ph) + 0.8 * np.sin(t * f2)) for t in tt]
        for off in (0, -WT):
            A.stroke(arr, [(p + off, q) for p, q in pts], R.uniform(*wdt), col, int(R.uniform(*a)), scale=1.0)


def gel_pat(sh, x, ld, u, shape, h, R):
    return sh + 0.08 * band_line(ld + 0.7 * per_sin(x, 23, 0.4) + 0.4 * per_sin(x, 61, 1.1), 1.8, 0.4) + 0.05 * noise(shape, 1.2, 601)


def T_vitreous():
    far = gradient(H, ['#03101a', '#062230', '#0a2c3a', '#061e2a'])
    R = RS(610)
    n = noise(far.shape[:2], 7.0, 611)
    far[..., :3] *= (1 + 0.1 * n[..., None])
    beams(far, 6, 612, '#c8f4ff', a=(0.05, 0.11))
    fibrils(far, 150, 613, '#9adcec', 18, GY - 4)
    for k in range(26):                                  # floaters far off: rings, clumps, threads
        kind = k % 3
        if kind == 0:
            s = ring_floater(R.uniform(8, 14), R.uniform(1.6, 2.6))
        elif kind == 1:
            s = knot(R.uniform(10, 16), R.uniform(6, 9), 100 + k)
        else:
            s = thread(R.uniform(24, 50), 200 + k)
        s = s.copy(); s[..., 3] = blur(s[..., 3], 0.35) * 0.32
        putw(far, s, R.uniform(0, WT), R.uniform(20, GY - 20))
    haze(far, '#062230', 0.12)
    mid = np.zeros((px(H), px(WT), 4), np.float32)
    for k in range(13):                                  # nearer floaters, a little out of focus
        kind = k % 3
        if kind == 0:
            s = ring_floater(R.uniform(12, 20), R.uniform(2.4, 3.4))
        elif kind == 1:
            s = knot(R.uniform(14, 22), R.uniform(8, 12), 300 + k)
        else:
            s = thread(R.uniform(36, 70), 400 + k, 1.4)
        s = s.copy(); s[..., 3] = blur(s[..., 3], 0.5) * 0.42
        putw(mid, s, R.uniform(0, WT), R.uniform(28, GY - 34))
    GEL = ramp('#041c26', '#0a3442', '#145262', '#2a7686', '#5aa6b6', n=6)
    floor = wall([(1.0, ramp('#4aa0b0', '#8ad4e0', '#c8f4fa', n=4), 'endo'), (7, GEL, gel_pat), (30, ramp('#03141c', '#062430', '#0c3644', '#16505e', n=5), gel_pat)],
                 True, seed=614, bumps=1.6, out='#03141c')
    ceil = wall([(1.0, ramp('#4aa0b0', '#8ad4e0', '#c8f4fa', n=4), 'endo'), (30, GEL, gel_pat)], False, seed=615, bumps=1.6, out='#03141c')
    obs = {'low': [knot(24, 14, 1), knot(22, 13, 4)],
           'tall': [rope(58, 14, seed=5)],
           'hang': [rope(T.hang_len(), 14, seed=6, fray=14)],
           'float': [ring_floater(18, 3.8)],
           'huge': [T.tower(lambda h: rope(int(h), 18, seed=9))]}
    return dict(far=far, mid=mid, floor=floor, ceil=ceil, obs=obs, coin='o2', special='omega')


# ------------------------------------------------------------------ 3. lens: rows of fibre cells, flattened hexagons
def hex_lattice(h, a, b, warp=None):
    """lens fibres cut across: flattened hexagons with long flat faces top and bottom and pointed ends, stacked in
    columns a apart, each column shifted half a cell from the next (a must divide WT into an even count).
    -> border (0 inside .. 1 on the walls), distance to the cell centre (units, scaled), a random number per cell"""
    y, x = grid(h, WT)
    Y = y + (warp(x) if warp is not None else 0)
    k = 2 * a / (np.sqrt(3) * b)                         # vertical distances count k times: regular hexagons when scaled
    S_ = b * k
    Ys = Y * k
    i0 = np.floor(x / a)
    d1 = np.full(x.shape, 1e9, np.float32); d2 = np.full(x.shape, 1e9, np.float32); idc = np.zeros(x.shape, np.int64)
    dyc = np.zeros(x.shape, np.float32)
    ncol = int(round(WT / a))
    for di in (-1, 0, 1, 2):
        i = i0 + di
        off = np.mod(i, 2) * 0.5
        j0 = np.floor(Ys / S_ - off)
        for dj in (0, 1):
            j = j0 + dj
            cy = (j + off) * S_
            dd = np.sqrt((x - i * a) ** 2 + (Ys - cy) ** 2)
            cid = (np.mod(i, ncol).astype(np.int64) * 7919 + j.astype(np.int64) * 104729)
            closer = dd < d1
            d2 = np.where(closer, d1, np.minimum(d2, dd))
            idc = np.where(closer, cid, idc)
            dyc = np.where(closer, (Ys - cy) / k, dyc)
            d1 = np.where(closer, dd, d1)
    border = np.clip(1 - (d2 - d1) / 1.1, 0, 1)
    rnd = np.mod(np.sin(idc * 12.9898) * 43758.5453, 1.0).astype(np.float32)
    return border, d1, rnd, dyc


def cuboid_pat(sh, x, ld, u, shape, h, R):
    """a single row of cuboidal cells with round nuclei (the lens epithelium)"""
    xx = x + 0.4 * per_sin(x, 53, 0.3)
    border = band_line(xx, 3.9, 0.35)
    cxp = np.mod(xx, 3.9) - 1.95
    nuc = np.clip(1 - np.sqrt((cxp / 1.05) ** 2 + ((ld - 1.6) / 0.9) ** 2), 0, 1) ** 0.5
    return sh - 0.3 * border - 0.38 * nuc + 0.05


def lensfib_pat(sh, x, ld, u, shape, h, R):
    """lens fibres running along: long thin cells in rows"""
    rows = band_line(ld + 0.3 * per_sin(x, 41, 0.2), 1.7, 0.28)
    ends = band_line(x + np.floor(ld / 1.7) * 7.3, 26, 0.3)
    return sh - 0.2 * rows - 0.12 * ends + 0.05 * noise(shape, 0.8, 701)


def hexprism(w=16, h=7, cols=None, out='#10283a'):
    """one lens fibre cut across: a flattened hexagon of clear protein (crystallin), its walls catching the light"""
    cols = cols or ramp('#24485e', '#4e86a4', '#8cc4dc', '#d2f0fa', '#ffffff')
    y, x = grid(h, w)
    cx, cy = (w - 1) / 2, (h - 1) / 2
    e = np.maximum(np.abs(y - cy) / (h / 2), (np.abs(x - cx) + np.abs(y - cy) * (w * 0.2) / (h / 2)) / (w / 2))
    cov = np.clip((1 - e) * min(w, h) / 2 * SC + 0.5, 0, 1)
    rim = np.clip((e - 0.72) / 0.28, 0, 1)
    lit = 0.45 + 0.35 * np.clip(-(x - cx) / w - (y - cy) / h, -1, 1) + 0.35 * rim * np.clip(-(y - cy) / (h / 2) + 0.2, 0, 1)
    lit = lit - 0.25 * rim * np.clip((y - cy) / (h / 2), 0, 1)
    rgb = ramp_col(cols, np.clip(lit, 0, 1))
    g = np.clip(1 - np.abs(e - 0.82) / 0.07, 0, 1) * np.clip(-(y - cy) / (h / 2) + 0.4, 0, 1)
    rgb = rgb * (1 - 0.7 * g[..., None]) + 255 * 0.7 * g[..., None]
    return outline(layer_rgba(rgb, cov), out, width=0.6)


def hex_column(H_, w=16, cols=None):
    n = max(2, int(round((H_ + 1) / 9)))
    hh = (H_ + 1 * (n - 1)) / n - 2                      # each outlined piece is 2 units taller than drawn
    return T.stack([hexprism(w - (k % 2) * 1.5, hh, cols) for k in range(n)], gap=-1)


def cloud(w=24, h=14, seed=1, d=None):
    """a cataract: lens protein clumped and gone milky"""
    R = RS(seed)
    if d:
        w = h = d
    y, x = grid(h, w)
    m = np.zeros(x.shape, bool)
    for k in range(6):
        cx, cy = R.uniform(w * 0.25, w * 0.75), h * R.uniform(0.35, 0.65) if d else h * R.uniform(0.45, 0.65)
        rx, ry = R.uniform(w * 0.18, w * 0.3), h * R.uniform(0.28, 0.42)
        m |= ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1
    if d:
        m |= ((x - (w - 1) / 2) / (w * 0.4)) ** 2 + ((y - (h - 1) / 2) / (h * 0.4)) ** 2 <= 1
    else:
        m |= (((x - w / 2) / (w * 0.46)) ** 2 + ((y - h) / (h * 0.62)) ** 2 <= 1)
        m &= y <= h - 1
    spr = A.mask_sprite(m, ramp('#6a6e7a', '#a4a8b4', '#d0d4dc', '#eef0f4', '#ffffff'), '#24262e', soft=1.4, hl_t=0.98)
    I = spr[SC:-SC, SC:-SC]
    n = noise(I.shape[:2], 0.7, seed + 5, wrap=False)
    I[..., :3] *= (1 + 0.1 * n[..., None])
    return spr


def T_lens():
    far = gradient(H, ['#0a0805', '#120e08', '#18130a', '#0e0b06'])
    warp = lambda x: 5 * per_sin(x, 2, 0.4) + 2.5 * per_sin(x, 5, 1.7)
    border, dc, rnd, dyc = hex_lattice(H, 15.0, 5.4, warp)
    y, x = grid(H, WT)
    light = np.clip(1.0 - np.abs(y - 84) / 92, 0, 1) ** 0.8
    shell = band_line(y + warp(x), 5.4 * 6, 0.9)                   # growth shells, like an onion's: every sixth layer
    inner_sh = np.clip(0.26 + 0.12 * rnd + 0.22 * np.clip(-dyc / 2.7, -1, 1) - 0.18 * np.clip((y - (GY - 30)) / 40, 0, 1), 0, 1) * (0.45 + 0.55 * light)
    rgb = ramp_col(ramp('#120d06', '#2e2210', '#52401e', '#7c6030', '#a8864a', n=6), inner_sh)
    # the cell walls: thin and bright, faintly split into colours where the light is bent
    disp = 0.5 + 0.5 * np.sin(x * TAU * 7 / WT + y * 0.05 + 1.5 * per_sin(x, 3, 0.2))
    wc = hexc('#fff0cc')[None, None] * (1 - 0.35 * disp[..., None]) + hexc('#c4ecff')[None, None] * 0.35 * disp[..., None]
    wallk = np.clip(border * (0.3 + 0.7 * light) * (0.55 + 0.45 * np.clip(0.5 + dyc / 2.7, 0, 1)) + 0.4 * shell * border, 0, 1)
    glow = blur(wallk, 1.0, wrap=True)
    rgb = rgb * (1 - 0.3 * glow[..., None]) + hexc('#e8c070') * 0.3 * glow[..., None]
    rgb = rgb * (1 - 0.85 * wallk[..., None]) + wc * 0.85 * wallk[..., None]
    c = np.sin(x * TAU * 3 / WT + 2.0 * np.sin(y * 0.045 + x * TAU * 2 / WT)) * np.sin(y * 0.06 + 1.6 * per_sin(x, 4, 0.3))
    ca = np.clip((c - 0.6) * 3.0, 0, 1) * 0.12 * light                # light bent by the lens: faint caustic ripples
    rgb = rgb * (1 - ca[..., None]) + hexc('#fff4d0') * ca[..., None]
    far[..., :3] = rgb
    mid = np.zeros((px(H), px(WT), 4), np.float32)
    R = RS(710)
    for k in range(34):                                  # glints of light caught in the lens
        s = canvas(12, 12)
        r_ = R.uniform(2.5, 5)
        A.stroke(s, [(5.5 - r_, 5.5), (5.5 + r_, 5.5)], 0.35, '#fff6d8', 200, scale=1.0)
        A.stroke(s, [(5.5, 5.5 - r_ * 0.7), (5.5, 5.5 + r_ * 0.7)], 0.3, '#fff6d8', 170, scale=1.0)
        g = canvas(12, 12); disc(g, 5.5, 5.5, 2.2, '#ffe8a0', 120)
        g[..., 3] = blur(g[..., 3], 0.9)
        over(g, s[..., :3], s[..., 3] / 255)
        putw(mid, g, R.uniform(0, WT), R.uniform(22, GY - 22), R.uniform(0.5, 1.0))
    CAP = ramp('#a8b8b0', '#d0e0d8', '#eef8f2', n=4)
    floor = wall([(8, ramp('#3a2a0e', '#6a5020', '#a08038', '#d0b064', '#eedc9c', n=6), lensfib_pat), (2.6, CAP, 'endo'),
                  (30, ramp('#020c10', '#06202a', '#0a2c38', n=4), 'smooth')], True, seed=711, bumps=0.6, out='#1a1004')
    ceil = wall([(3.2, ramp('#4a3a1a', '#7a6634', '#b09a5c', '#dccc94', n=5), cuboid_pat), (2.6, CAP, 'endo'),
                 (30, ramp('#020c10', '#06202a', '#0a2c38', n=4), 'smooth')], False, seed=712, bumps=0.6, out='#1a1004')
    obs = {'low': [cloud(24, 14, 1), cloud(22, 13, 3)],
           'tall': [hex_column(58)],
           'hang': [hex_column(T.hang_len(), 15)],
           'float': [cloud(d=17, seed=7)],
           'huge': [T.tower(lambda h: hex_column(h, 19))]}
    return dict(far=far, mid=mid, floor=floor, ceil=ceil, obs=obs, coin='o2', special='omega')


# ------------------------------------------------------------------ 4. the pupil, between the iris above and below
IRIS_COLS = ramp('#2a1408', '#5a3214', '#8e5a26', '#c08640', '#e6b664', '#fadc9a')
IRIS_OBS = ramp('#3a200c', '#8a5e34', '#d0a874', '#f4dcb4', '#fffaf0')


def radial_pat(sh, x, ld, u, shape, h, R):
    """the iris stroma cut along: loose fibres and pigment cells"""
    return sh + 0.12 * noise(shape, 0.45, 801) + 0.08 * noise(shape, 1.5, 803) - 0.05


def ruff_pat(sh, x, ld, u, shape, h, R):
    """the pupillary ruff: the dark pigment layer curling round the iris edge, beaded"""
    return sh - 0.25 * band_line(x + 0.3 * per_sin(x, 70), 2.2, 0.5)


def T_iris():
    far = gradient(H, ['#120a04', '#1e1008', '#2a170a', '#1a0e06'])
    n_ = noise(far.shape[:2], 2.0, 809)
    far[..., :3] *= (1 + 0.12 * n_[..., None])
    R = RS(810)
    # the iris seen face on, unrolled: the pupil's edge at the top, the collarette's zigzag ridge, then radial
    # fibres (here running up and down), crypts between them, rings of contraction furrows further out
    xs = np.arange(0, WT + 1, 1.0)
    tri = np.abs(np.mod(xs / 13.0, 1.0) - 0.5) * 2 - 0.5
    col_y = 64 + 6 * tri + 2.5 * np.sin(xs * TAU * 37 / WT + 1.3) + 1.0 * np.sin(xs * 0.9)
    PZ = ['#3a1c0c', '#4e2610', '#6a3418', '#84441e']
    CZ = ['#4a2a12', '#6a3e1a', '#8a5424', '#a86a2e', '#c8863a', '#e0a24a', '#f2c070']
    def fibre(x0, y0, y1, w_, c_, a_, tilt):
        pts = [(x0 + tilt * (t - y0) + 0.6 * np.sin(t * 0.21 + x0), t) for t in np.linspace(y0, y1, 14)]
        for off in (0, -WT, WT):
            A.stroke(far, [(p + off, q) for p, q in pts], w_, c_, a_, scale=1.0)
    for k in range(700):                                 # the pupillary zone: fine strands up to the pupil's edge, darker
        x0 = R.uniform(0, WT); yc = np.interp(x0, xs, col_y)
        fibre(x0, 10, yc, R.uniform(0.3, 0.6), R.choice(PZ), int(R.uniform(110, 190)), R.uniform(-0.05, 0.05))
    # the ciliary zone: radial cords (trabeculae) from the collarette out, each a few wavy strands, gaps between
    gaps = []
    x0 = 0.0
    while x0 < WT - 3:
        cw = R.uniform(4.5, 9.0)
        cx_ = x0 + cw / 2
        f1, f2, ph1, ph2 = R.uniform(0.03, 0.06), R.uniform(0.1, 0.18), R.uniform(0, TAU), R.uniform(0, TAU)
        a1, a2 = R.uniform(1.0, 2.6), R.uniform(0.3, 0.8)
        yc = np.interp(cx_, xs, col_y)
        tt = np.linspace(yc - 1, 162, 60)
        path = cx_ + a1 * np.sin(tt * f1 + ph1) + a2 * np.sin(tt * f2 + ph2)
        bri = R.beta(2.4, 2.2)
        for off in (0, -WT, WT):
            A.stroke(far, [(p + off, q) for p, q in zip(path, tt)], cw * 0.9, '#0e0703', 110, scale=1.0)
        for j in range(int(R.uniform(3, 7))):
            dx_ = R.uniform(-cw * 0.32, cw * 0.32); wig = R.uniform(0.2, 0.6); fj = R.uniform(0.15, 0.3)
            ci = int(np.clip(bri * 6 + R.uniform(-1.2, 1.2), 0, 6))
            pts = [(p + dx_ + wig * np.sin(q * fj + j), q) for p, q in zip(path, tt)]
            for off in (0, -WT, WT):
                A.stroke(far, [(p + off, q) for p, q in pts], R.uniform(0.5, 1.1), CZ[ci], int(R.uniform(170, 235)), scale=1.0)
            if ci >= 4 and R.uniform() < 0.5:
                for off in (0, -WT, WT):
                    A.stroke(far, [(p + off - 0.2, q) for p, q in pts], 0.3, '#ffe0a0', 110, scale=1.0)
        gaps.append(x0 + cw + 0.6)
        x0 += cw + R.uniform(0.8, 2.6)
    for k in range(80):                                  # crypts: dark almond openings between the cords
        gx = gaps[R.randint(len(gaps))]
        cy_ = (np.interp(gx, xs, col_y) + R.uniform(7, 30)) if k < 55 else R.uniform(96, 142)
        rx, ry = R.uniform(1.3, 2.6), R.uniform(3.5, 8)
        for off in (0, -WT, WT):
            ellipse_soft(far, gx + off, cy_, rx + 0.8, ry + 0.8, '#1a0c04', 150)
            ellipse_soft(far, gx + off, cy_, rx, ry, '#050200', 240)
    for fy in (104, 122, 138):                           # contraction furrows: broken dark rings
        for k in range(14):
            x0 = R.uniform(0, WT); L = R.uniform(30, 90)
            pts = [(x0 + t, fy + 2.5 * np.sin((x0 + t) * TAU * 11 / WT) + 0.8 * np.sin(t * 0.2)) for t in np.linspace(0, L, 30)]
            for off in (0, -WT):
                A.stroke(far, [(p + off, q) for p, q in pts], 1.2, '#070301', 150, scale=1.0)
    cz = [(float(x_), float(y_)) for x_, y_ in zip(xs, col_y)]
    glow = np.zeros_like(far)
    A.stroke(glow, cz, 4.0, '#e8a850', 200, scale=1.0)
    glow[..., 3] = blur(glow[..., 3], 1.6, wrap=True)
    over(far, glow[..., :3], glow[..., 3] / 255 * 0.5)
    for j in range(3):                                   # the collarette: a fuzzy ridge of thickened fibres
        jit = [(p, q + R.uniform(-0.6, 0.6)) for p, q in cz]
        for off in (0, -WT):
            A.stroke(far, [(p + off, q + (j - 1) * 0.9) for p, q in jit], 1.6, ['#a8682a', '#d89846', '#c07c36'][j], 170, scale=1.0)
    for off in (0, -WT):
        A.stroke(far, [(p + off, q - 1.1) for p, q in cz], 0.5, '#ffe2a6', 140, scale=1.0)
    for k in range(40):                                  # pigment spots and golden flecks
        cx_, cy_ = R.uniform(0, WT), R.uniform(30, 145)
        c_ = '#100602' if k % 3 else '#f0c060'
        for off in (0, -WT, WT):
            ellipse_soft(far, cx_ + off, cy_, R.uniform(0.6, 1.6), R.uniform(0.6, 1.4), c_, 170 if k % 3 else 120)
    y, x = grid(H, WT)
    # the light coming in through the pupil: a soft glow along the middle
    g = (np.exp(-((y[:, :1] - 84) / 42) ** 2) * 0.12)[..., None]
    far[..., :3] = far[..., :3] * (1 - g) + hexc('#ffe2b0') * g
    haze(far, '#0e0703', 0.3)
    mid = np.zeros((px(H), px(WT), 4), np.float32)
    for k in range(40):                                  # specks drifting in the aqueous humour, catching the light
        s = canvas(6, 6); disc(s, 2.5, 2.5, R.uniform(0.4, 0.8), '#ffe8c0', 220)
        g2 = s.copy(); g2[..., 3] = blur(s[..., 3], 0.7) * 0.6
        over(g2, s[..., :3], s[..., 3] / 255)
        putw(mid, g2, R.uniform(0, WT), R.uniform(24, GY - 20), R.uniform(0.4, 0.9))
    RUFF = ramp('#0a0402', '#1e0e06', '#3a1e0e', '#5a3218', n=4)
    SPH = ramp('#2a0e08', '#5a2416', '#8a3e26', '#b0603c', n=5)
    STROMA = ramp('#120804', '#26150a', '#3e2412', '#5e3a1c', '#80522a', n=6)
    floor = wall([(1.6, RUFF, ruff_pat), (5, SPH, 'smooth'), (30, STROMA, radial_pat)], True, seed=811, bumps=1.3, out='#080302')
    ceil = wall([(1.6, RUFF, ruff_pat), (5, SPH, 'smooth'), (30, STROMA, radial_pat)], False, seed=812, bumps=1.3, out='#080302')
    PIG = ramp('#1a0a04', '#3e200e', '#6a3a1a', '#a06a34', '#d8a462')
    obs = {'low': [knot(23, 13, 11, PIG, '#0a0402', '#2a1206'), knot(21, 12, 14, PIG, '#0a0402', '#2a1206')],
           'tall': [rope(58, 14, IRIS_OBS, '#140802', seed=15)],
           'hang': [rope(T.hang_len(), 14, IRIS_OBS, '#140802', seed=16, fray=14)],
           'float': [clump_cell(17)],
           'huge': [T.tower(lambda h: rope(int(h), 18, IRIS_OBS, '#140802', seed=19))]}
    return dict(far=far, mid=mid, floor=floor, ceil=ceil, obs=obs, coin='o2', special='omega')


def clump_cell(d=17, seed=5):
    """a clump cell: a macrophage of the iris, stuffed with pigment it has eaten"""
    R = RS(seed)
    m = ellipse_mask(d, d * 0.94)
    spr = A.mask_sprite(m, ramp('#6a4a30', '#a07a56', '#cca884', '#ecd6b8', '#fff4e4'), '#1a0c04', soft=1.4, hl_t=0.98)
    I = spr[SC:-SC, SC:-SC]
    for k in range(60):
        a0, rr = R.uniform(0, TAU), np.sqrt(R.uniform(0, 1)) * d * 0.36
        gx, gy = (d - 1) / 2 + np.cos(a0) * rr, (d * 0.94 - 1) / 2 + np.sin(a0) * rr
        disc(I, gx, gy, R.uniform(0.45, 0.85), '#2a1206' if k % 4 else '#5a3010', 235)
    disc(I, (d - 1) / 2 + d * 0.12, (d * 0.94 - 1) / 2 + d * 0.06, d * 0.16, '#3a2a50', 200)
    return spr


# ------------------------------------------------------------------ 5. cornea: the clear window in front
def basal_pat(sh, x, ld, u, shape, h, R):
    """basal cells of the corneal epithelium: a row of tall cells, an oval nucleus in each"""
    xx = x + 0.3 * per_sin(x, 71, 0.9)
    border = band_line(xx, 2.6, 0.28)
    cxp = np.mod(xx, 2.6) - 1.3
    nuc = np.clip(1 - np.sqrt((cxp / 0.75) ** 2 + ((ld - 1.9) / 1.2) ** 2), 0, 1) ** 0.5
    return sh - 0.22 * border - 0.42 * nuc + 0.08


def wing_pat(sh, x, ld, u, shape, h, R):
    cb, d, _ = pcells(h, int(WT * h / 12), 902, sy=1.4, border=0.35)
    nuc = np.clip(1 - d / 0.85, 0, 1) ** 0.5
    return sh + 0.05 - 0.22 * cb - 0.36 * nuc


def flat_pat(sh, x, ld, u, shape, h, R):
    """the endothelium in section: one layer of flat cells, flat nuclei"""
    xx = x + 0.4 * per_sin(x, 29, 0.5)
    border = band_line(xx, 6.0, 0.3)
    cxp = np.mod(xx, 6.0) - 3.0
    nuc = np.clip(1 - np.sqrt((cxp / 1.9) ** 2 + ((ld - 0.8) / 0.45) ** 2), 0, 1) ** 0.5
    return sh - 0.25 * border - 0.45 * nuc + 0.05


def squame(w=24, h=5, seed=1, cols=None, out='#2a2440'):
    """a flattened epithelial cell: a thin cushion with a flat nucleus"""
    m = ellipse_mask(w, h)
    y, x = grid(h, w)
    m = m | ((np.abs(x - (w - 1) / 2) < w * 0.42) & (np.abs(y - (h - 1) / 2) < h * 0.36))
    spr = A.mask_sprite(m, cols or ramp('#5a5476', '#8a86a8', '#bab6d2', '#e2e0f0', '#ffffff'), out, soft=0.9, hl_t=0.975)
    I = spr[SC:-SC, SC:-SC]
    R = RS(seed)
    ellipse_soft(I, (w - 1) / 2 + R.uniform(-2, 2), (h - 1) / 2, w * 0.17, h * 0.2, '#4a3a7a', 220)
    ellipse_soft(I, (w - 1) / 2 + R.uniform(-2, 2) - 0.6, (h - 1) / 2 - 0.3, w * 0.07, h * 0.08, '#8a7ab8', 160)
    return spr


def squame_pile(H_, w=24, seed=1):
    n = max(2, int(round((H_ + 1.5) / 7)))
    tot = int(round((H_ + 1.5 * (n - 1) - 2 * n) * SC))  # each outlined piece is 2 units taller than drawn
    hp = [tot // n + (1 if k < tot % n else 0) for k in range(n)]   # whole pixels, shared out so the pile is exact
    R = RS(seed)
    return T.stack([squame(w - R.uniform(0, 4), hp[k] / SC, seed + k) for k in range(n)], gap=-1.5)


def keratocyte(L=26, seed=3):
    """a keratocyte: the stroma's flat star-shaped cell, its long thin arms (faint, they do not hit) along the layers"""
    R = RS(seed)
    spr = canvas(L + 18, 16)
    cx, cy = (L + 18) / 2, 8
    for k in range(6):
        sgn = 1 if k % 2 else -1
        a0 = R.uniform(-0.35, 0.35) + (0 if sgn > 0 else np.pi)
        Ln = R.uniform(7, 10)
        pts = [(cx + sgn * L * 0.3 + np.cos(a0) * t, cy + np.sin(a0) * t + 0.6 * np.sin(t * 0.6 + k)) for t in np.linspace(0, Ln, 14)]
        A.stroke(spr, pts, 0.7, '#4a5a7a', 110, scale=1.0)
    y, x = grid(9, L)
    m = ((x - (L - 1) / 2) / (L / 2)) ** 2 + ((y - 4) / 4.5) ** 2 * (1 + 0.6 * ((x - (L - 1) / 2) / (L / 2)) ** 2) <= 1
    b = A.mask_sprite(m, ramp('#3a4a6a', '#6a7ea0', '#a4b6d0', '#dce8f4', '#ffffff'), '#121a2c', soft=1.0, hl_t=0.975)
    I = b[SC:-SC, SC:-SC]
    ellipse_soft(I, (L - 1) / 2, 4, L * 0.22, 1.5, '#2a2a5a', 220)
    paste(spr, b, cx - (L + 2) / 2, cy - 5.5)
    rows = np.nonzero(spr[..., 3].max(axis=1) > 0)[0]    # no empty rows: it floats with its body's bottom at the line
    return spr[rows.min():rows.max() + 1].copy()


def T_cornea():
    far = gradient(H, ['#a8d4e2', '#80b4c8', '#5a90a8', '#3a6a84'])
    y, x = grid(H, WT)
    R = RS(910)
    # the stroma: about two hundred flat layers of collagen fibres, in alternate directions; so regular it is clear
    lay = y + 0.8 * per_sin(x, 7, 0.3) + 0.4 * per_sin(x, 19, 1.1)
    idx = np.floor(lay / 3.4)
    ldp = lay - idx * 3.4
    along = np.mod(idx, 2) == 0
    stri = band_line(ldp + 0.15 * per_sin(x, 300, 0.0), 0.55, 0.16)                     # fibres running along
    dots = np.clip(1 - np.sqrt((np.mod(x, 0.9) - 0.45) ** 2 + (np.mod(ldp, 0.9) - 0.45) ** 2) / 0.22, 0, 1)   # fibres cut end-on
    tex = np.where(along, stri, dots)
    sep = band_line(ldp, 3.4, 0.35)
    shade = 1 + 0.05 * tex - 0.08 * sep + 0.025 * np.sin(idx * 2.1)
    far[..., :3] *= shade[..., None]
    for k in range(70):                                  # keratocytes lying flat between the layers (thin in section)
        L = R.uniform(14, 26); cx_ = R.uniform(0, WT); cy_ = np.floor(R.uniform(20, GY - 8) / 3.4) * 3.4 + 0.2
        for off in (0, -WT, WT):
            for sgn in (-1, 1):
                Ln = R.uniform(6, 12)
                A.stroke(far, [(cx_ + off + sgn * L * 0.45 + sgn * t, cy_ + 0.5 * np.sin(t * 0.5)) for t in np.linspace(0, Ln, 10)], 0.4, '#2e4a62', 70, scale=1.0)
            ellipse_soft(far, cx_ + off, cy_, L / 2, 1.1, '#5a7890', 110)
            ellipse_soft(far, cx_ + off, cy_, L * 0.24, 0.6, '#283a58', 150)
    for k in range(7):                                   # nerve fibres just under the surface, beaded
        x0 = R.uniform(0, WT); y0 = R.uniform(18, 40); Ln = R.uniform(150, 320); sl = R.uniform(-0.06, 0.06)
        pts = [(x0 + t, y0 + sl * t + 1.5 * np.sin(t * 0.05 + k)) for t in np.linspace(0, Ln, int(Ln / 2))]
        for off in (0, -WT):
            P = [(p + off, q) for p, q in pts]
            A.stroke(far, P, 0.5, '#f4fbff', 120, scale=1.0)
            for j in range(0, len(P), 6):
                disc(far, P[j][0], P[j][1], 0.55, '#ffffff', 150)
    g = (np.exp(-((y[:, :1] - 10) / 60) ** 2) * 0.25)[..., None]     # daylight coming in from the front
    far[..., :3] = far[..., :3] * (1 - g) + 255 * g
    mid = np.zeros((px(H), px(WT), 4), np.float32)
    for k in range(26):                                  # light scattered here and there
        s = canvas(10, 10); disc(s, 4.5, 4.5, R.uniform(1.6, 3.2), '#ffffff', 90)
        s[..., 3] = blur(s[..., 3], 0.9)
        putw(mid, s, R.uniform(0, WT), R.uniform(20, GY - 20), R.uniform(0.4, 0.8))
    EPI = ramp('#4a4a6a', '#7a7a9c', '#a8a8c4', '#d4d4e6', '#f4f4fa', n=6)
    ceil = wall([(1.8, ramp('#b8d8e2', '#d8eef4', '#f2fbff', n=4), 'endo'), (3.8, EPI, basal_pat), (3.2, EPI, wing_pat),
                 (2.4, EPI, 'squamous'), (0.9, ramp('#bfeeff', '#e4faff', '#ffffff', n=3), 'endo'), (30, ramp('#e8f6fc', '#f6fcff', '#ffffff', n=3), 'endo')],
                False, seed=911, bumps=0.6, out='#2a3a4e')
    floor = wall([(2.6, ramp('#a8c8d4', '#cce4ec', '#eef8fc', n=4), 'endo'), (1.6, ramp('#3a5a70', '#6a8ca4', '#a0bed0', n=4), flat_pat),
                  (30, ramp('#06141c', '#0c2632', '#163a48', n=4), 'smooth')], True, seed=912, bumps=0.6, out='#122230')
    obs = {'low': [squame_pile(16, 24, 1), squame_pile(15, 22, 7)],
           'tall': [squame_pile(58, 22, 11)],
           'hang': [squame_pile(T.hang_len(), 20, 21)[::-1].copy()],
           'float': [keratocyte(22, 31)],
           'huge': [T.tower(lambda h: squame_pile(h, 24, 41))]}
    return dict(far=far, mid=mid, floor=floor, ceil=ceil, obs=obs, coin='o2', special='omega')
