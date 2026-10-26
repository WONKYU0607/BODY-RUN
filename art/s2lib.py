# Shared drawing for stage 2's places (drains.py, sewer.py, plant.py): the water, a pipe's far wall, ring joints,
# materials in section (porcelain, PVC, concrete, brick, cast iron, soil, sand and gravel, sludge, slime), a ceiling
# that is the water's surface seen from below, and the usual small things (strands, lumps, sludge).
import numpy as np
from scipy import ndimage
from art import (H, SC, px, grid, canvas, ramp, ramp_col, hexc, paint, ellipse_mask, outline, paste, over, blur, disc,
                 ellipse_soft, inner, smooth_mask, fill_rect)
import anatomy as A
from tiles import WT, GY, FH, FY0, CH, TAU, wide, crop, put, per_sin, gradient, haze, pcells, wall, band_line, spots
from themes import three, drift, tower, stack, hang_len, bubble, flip_v
from variants import noise, putw

RS = np.random.RandomState


def lerp_rgb(arr, col, k):
    """blend arr's rgb toward col by k (k: array (h, w) or a number)"""
    c = hexc(col) if isinstance(col, str) else np.asarray(col, np.float32)
    k = np.asarray(k, np.float32)
    if k.ndim == 2:
        k = k[..., None]
    arr[..., :3] = arr[..., :3] * (1 - k) + c * k


def mul(arr, k):
    k = np.asarray(k, np.float32)
    if k.ndim == 2:
        k = k[..., None]
    arr[..., :3] = np.clip(arr[..., :3] * k, 0, 255)


def wdx(x, x0):
    """signed distance along x from x0, wrapped across the tile"""
    return np.mod(x - x0 + WT / 2, WT) - WT / 2


# ------------------------------------------------------------------ the far layer
def pipe_curve(far, top, bot, k=0.3, lit=0.55):
    """the far inside of a pipe: bright where it faces you (a little above the middle), darker round to the top and
    bottom"""
    y, x = grid(H, WT)
    c = np.clip((y - (top + (bot - top) * lit)) / ((bot - top) / 2), -1.6, 1.6)
    mul(far, 1 - k * c ** 2)


def ring_joints(far, n, seed, col='#000000', w=7.0, k=0.35, collar=None, wob=0.0, top=0, bot=H):
    """the joints between lengths of pipe on its far wall (n across the tile): a dark seam with a lit rim each side;
    collar: (width, colour) a raised band round it"""
    R = RS(seed)
    y, x = grid(H, WT)
    per = WT / n
    vis = ((y >= top) & (y <= bot)).astype(np.float32)
    for j in range(n):
        x0 = j * per + R.uniform(-0.12, 0.12) * per
        d = wdx(x, x0) + wob * np.sin(y * 0.07 + j)
        if collar:
            cw, cc = collar
            band = np.clip((cw / 2 - np.abs(d)) * SC * 0.5 + 0.5, 0, 1) * vis
            sh = np.clip(0.75 + 0.35 * np.sin(np.clip(d / cw * np.pi, -np.pi / 2, np.pi / 2)), 0, 1.2)
            lerp_rgb(far, cc, band * 0.55)
            mul(far, 1 + (sh - 0.85)[..., None][..., 0] * 0.5 * band)
        seam = np.exp(-(d / (w * 0.18)) ** 2) * vis
        lit = np.exp(-((d - w * 0.32) / (w * 0.16)) ** 2) * vis
        lerp_rgb(far, col, seam * k)
        lerp_rgb(far, '#ffffff', lit * k * 0.35)


def concrete_tex(far, seed, k=1.0, pores=900, agg=1400, y0=0, y1=H, cols=('#3a3a34', '#d8d4c4')):
    """concrete: a soft mottle, small dark pores and pale bits of aggregate"""
    R = RS(seed)
    y, x = grid(H, WT)
    mul(far, 1 + 0.08 * k * noise(y.shape, 3.0, seed))
    mul(far, 1 + 0.05 * k * noise(y.shape, 0.6, seed + 1))
    c3 = three(far)
    for i in range(int(pores * k)):
        xx, yy = R.uniform(0, WT), R.uniform(y0, y1)
        ellipse_soft(c3, xx + WT, yy, R.uniform(0.25, 0.7), R.uniform(0.2, 0.5), cols[0], int(110 * k))
    for i in range(int(agg * k)):
        xx, yy = R.uniform(0, WT), R.uniform(y0, y1)
        ellipse_soft(c3, xx + WT, yy, R.uniform(0.4, 1.1), R.uniform(0.3, 0.8), cols[1], int(40 * k), R.uniform(0, 3))
    far[:] = crop(c3)


def water_line(far, y0, col, k=0.5, h=10.0, seed=1):
    """a band of stain or slime along a level on the far wall (where the water usually stands), its top edge wavy"""
    y, x = grid(H, WT)
    edge = y0 + 1.5 * per_sin(x, 17, seed) + 0.8 * per_sin(x, 53, seed * 2)
    band = np.clip((y - edge) * SC * 0.4, 0, 1) * np.clip(1 - (y - edge) / h, 0, 1) ** 0.7
    lerp_rgb(far, col, band * k)
    lerp_rgb(far, '#000000', np.exp(-((y - edge) / 0.6) ** 2) * k * 0.4)


def streaks(far, n, seed, col, k=0.3, y0=0, y1=H, ang=0.0, L=(40, 140), w=(1.0, 3.0)):
    """long soft streaks (flow marks, mineral stains, water running down), wrapped"""
    R = RS(seed)
    c3 = three(far)
    acc = np.zeros(c3.shape[:2], np.float32)
    for i in range(n):
        x0, yy, l, ww = R.uniform(0, WT), R.uniform(y0, y1), R.uniform(*L), R.uniform(*w)
        g = canvas(l + 4, ww * 2 + 4)
        ellipse_soft(g, l / 2 + 2, ww + 2, l / 2, ww, '#ffffff', 255, 0.0)
        g = ndimage.gaussian_filter(g[..., 3], 0.6 * SC)
        if ang:
            g = ndimage.rotate(g, np.degrees(ang), reshape=True, order=1)
        gy, gx = g.shape
        for off in (0, WT, 2 * WT):
            X, Y = px(x0 + off) - gx // 2, px(yy) - gy // 2
            xa, ya = max(0, X), max(0, Y)
            xb, yb = min(c3.shape[1], X + gx), min(c3.shape[0], Y + gy)
            if xb > xa and yb > ya:
                acc[ya:yb, xa:xb] = np.maximum(acc[ya:yb, xa:xb], g[ya - Y:yb - Y, xa - X:xb - X] / 255 * R.uniform(0.5, 1))
    lerp_rgb(c3, col, acc * k)
    far[:] = crop(c3)


def mouth(w, h, lip, deep=('#030608', '#0a1418', '#1a2a30'), lipw=2.6, flow=None):
    """the dark round mouth of a pipe coming in on the far wall, with its lit lip (and water pouring out of it)"""
    W, Hh = w + 2 * lipw + 2, h + 2 * lipw + 2
    y, x = grid(Hh, W)
    cx, cy = W / 2, Hh / 2
    r = np.sqrt(((x - cx) / (w / 2)) ** 2 + ((y - cy) / (h / 2)) ** 2)
    rl = np.sqrt(((x - cx) / (w / 2 + lipw)) ** 2 + ((y - cy) / (h / 2 + lipw)) ** 2)
    out = np.zeros(y.shape + (4,), np.float32)
    hole = np.clip((1 - r) * min(w, h) * SC * 0.25, 0, 1)
    ring = np.clip((1 - rl) * (min(w, h) + lipw) * SC * 0.25, 0, 1)
    dep = np.clip(r * 0.8 + 0.3 * (y - cy) / h, 0, 1)
    hc = ramp_col(ramp(*deep, n=3), dep)
    lit = np.clip(0.55 - 0.5 * (y - cy) / (h / 2 + lipw) + 0.2 * (x - cx) / w, 0, 1)
    lc = ramp_col(lip, lit) if not isinstance(lip, str) else ramp_col(ramp('#202020', lip, '#ffffff', n=3), lit * 0.8)
    out[..., :3] = hc * hole[..., None] + lc * (1 - hole[..., None])
    out[..., 3] = ring * 255
    edge = np.clip(1 - np.abs(r - 1) * min(w, h) * 0.5, 0, 1)
    lerp_rgb(out, '#05080a', edge * 0.7)
    return outline(out, '#0a1214')


def silt(far, y0, cols, seed, k=1.0):
    """a soft bank of settled silt along the bottom of the far wall, from y0 down"""
    y, x = grid(H, WT)
    top = y0 + 3 * per_sin(x, 5, seed) + 1.5 * per_sin(x, 19, seed + 1) + 0.6 * per_sin(x, 61, seed + 2)
    m = np.clip((y - top) * SC * 0.35, 0, 1)
    sh = np.clip(0.75 - 0.5 * np.clip((y - top) / 18, 0, 1) + 0.12 * noise(y.shape, 0.7, seed + 3), 0, 1)
    col = ramp_col(ramp(*cols), sh)
    far[..., :3] = far[..., :3] * (1 - m[..., None] * k) + col * m[..., None] * k
    lerp_rgb(far, '#000000', np.exp(-((y - top - 0.3) / 0.5) ** 2) * 0.35 * k)


# ------------------------------------------------------------------ the mid layer: drifting bits
def motes(mid, n, cols, seed, y0=20, y1=GY - 10, r=(0.3, 0.9), a=(90, 200)):
    R = RS(seed)
    for k in range(n):
        x, y = R.uniform(0, WT), R.uniform(y0, y1)
        rr = R.uniform(*r)
        put(mid, _speck(rr, cols[k % len(cols)], R.uniform(*a)), x, y)


def _speck(r, col, a):
    s = canvas(2 * r + 2, 2 * r + 2)
    ellipse_soft(s, r + 1, r + 1, r * 1.3, r, col, int(a))
    return s


def bubble_chain(mid, n, seed, y0=60, y1=GY - 20, r=(2, 4), alpha=0.75, per=(3, 6)):
    R = RS(seed)
    for k in range(n):
        x0, yy = R.uniform(0, WT), R.uniform(y0, y1)
        for j in range(R.randint(*per)):
            rr = int(R.uniform(*r))
            b = bubble(rr, seed + k * 7 + j); b[..., 3] *= alpha
            put(mid, b, x0 + 2.5 * np.sin(j * 1.3 + k), yy - j * R.uniform(6, 11))


# ------------------------------------------------------------------ materials in section (floor and ceiling layers)
def pat_concrete(sh, x, ld, u, shape, h, R):
    n = int(0.07 * WT * h)
    P = np.c_[R.uniform(0, WT, n), R.uniform(0, h, n)]
    agg = spots(shape, P, R.uniform(0.35, 1.0, n), WT)
    m = int(0.05 * WT * h)
    Q = np.c_[R.uniform(0, WT, m), R.uniform(0, h, m)]
    pore = spots(shape, Q, R.uniform(0.15, 0.35, m), WT)
    return sh + 0.16 * agg - 0.3 * pore + 0.03 * np.sin(x * 1.7 + ld * 0.9) * np.sin(ld * 0.4)


def pat_soil(sh, x, ld, u, shape, h, R):
    n = int(0.03 * WT * h)
    P = np.c_[R.uniform(0, WT, n), R.uniform(0, h, n)]
    peb = spots(shape, P, R.uniform(0.5, 1.6, n), WT)
    m = int(0.12 * WT * h)
    Q = np.c_[R.uniform(0, WT, m), R.uniform(0, h, m)]
    grit = spots(shape, Q, R.uniform(0.15, 0.3, m), WT)
    return sh + 0.22 * peb - 0.12 * grit + 0.04 * np.sin(ld * 0.7 + 0.2 * np.sin(x * 0.05))


def pat_pvc(sh, x, ld, u, shape, h, R):
    return sh + 0.1 + 0.03 * np.sin(ld * 2.2) + 0.02 * np.sin(x * TAU * 90 / WT)


def pat_glaze(sh, x, ld, u, shape, h, R):
    return sh + 0.12 + 0.04 * np.sin(x * TAU * 31 / WT) * np.exp(-ld / 1.2)


def pat_china(sh, x, ld, u, shape, h, R):
    n = int(0.05 * WT * h)
    P = np.c_[R.uniform(0, WT, n), R.uniform(0, h, n)]
    sp = spots(shape, P, R.uniform(0.18, 0.4, n), WT)
    return sh - 0.14 * sp + 0.03 * np.sin(x * 0.9 + ld * 1.7) * np.sin(ld * 0.5)


def pat_slime(sh, x, ld, u, shape, h, R):
    return sh + 0.12 * np.sin(x * 0.6 + ld * 2.0 + np.sin(x * 0.13) * 2) * np.exp(-ld / 2)


def pat_sludge(sh, x, ld, u, shape, h, R):
    n = int(0.04 * WT * h)
    P = np.c_[R.uniform(0, WT, n), R.uniform(0, h, n)]
    bits = spots(shape, P, R.uniform(0.2, 0.6, n), WT)
    lay = band_line(ld + 0.6 * np.sin(x * 0.08) + 0.3 * np.sin(x * 0.31), 2.4, 0.5)
    return sh - 0.1 * lay + 0.12 * bits


def pat_iron(sh, x, ld, u, shape, h, R):
    n = int(0.05 * WT * h)
    P = np.c_[R.uniform(0, WT, n), R.uniform(0, h, n)]
    pit = spots(shape, P, R.uniform(0.15, 0.4, n), WT)
    return sh - 0.2 * pit + 0.04 * np.sin(x * 2.3) * np.sin(ld * 1.3)


def pat_rubber(sh, x, ld, u, shape, h, R):
    return sh + 0.05 * np.sin(ld * 3.0)


def pat_brick(sh, x, ld, u, shape, h, R, course=5.0, blen=12.0):
    row = np.floor(ld / course)
    xs = x + np.mod(row, 2) * blen / 2
    mort = np.maximum(band_line(ld, course, 0.55, 0.0), band_line(xs, blen, 0.5, 0.0))
    tone = 0.08 * np.sin(row * 12.9898 + np.floor(xs / blen) * 78.233) ** 2
    return sh + tone - 0.42 * mort


def pat_gravel(sh, x, ld, u, shape, h, R):
    n = int(0.06 * WT * h)
    P = np.c_[R.uniform(0, WT, n), R.uniform(0, h, n)]
    peb = spots(shape, P, R.uniform(0.6, 2.2, n), WT)
    m = int(0.15 * WT * h)
    Q = np.c_[R.uniform(0, WT, m), R.uniform(0, h, m)]
    sand = spots(shape, Q, R.uniform(0.12, 0.25, m), WT)
    return sh + 0.25 * peb - 0.08 * sand


def pebble_surface(c3, edge_w, e0, top_edge, seed=5, n=110, cols=('#6a6458', '#a89e88', '#d4cab0'), out='#2a2620', r=(1.0, 2.6)):
    """pebbles lying along the floor's surface (a floor's `surface` hook)"""
    R = RS(seed)
    for k in range(n):
        x = R.uniform(0, WT); rx = R.uniform(*r); ry = rx * R.uniform(0.6, 0.85)
        e = edge_w[int(x) % WT]
        y = (e0 + e) - ry * 0.55 if top_edge else (e0 - e) + ry * 0.55
        m = ellipse_mask(int(2 * rx + 2), int(2 * ry + 2))
        s = A.mask_sprite(m, ramp(*cols), out, soft=0.8, ambient=0.3, hl_t=0.97)
        for off in (0, WT, 2 * WT):
            paste(c3, s, x + off - rx - 1, y - ry - 1)


# ------------------------------------------------------------------ a ceiling that is the water's surface from below
def surf_ceil(seed, crown, crown_pat=None, crown_h=7.0, air=('#4e6e74', '#7a9ca2', '#a6c4c8'), surf_y=13.6, mirror='#e8fafa',
              out='#2a4a50', holes=None, extra=None, mir_k=0.55):
    """the top of the strip: the pipe's crown (or a tank's cover) in section down to crown_h, a gap of air, then the
    water's surface (a bright wavy line, the mirror-bright underside fading into the water)"""
    R = RS(seed)
    c3 = np.zeros((px(CH), 3 * px(WT), 4), np.float32)
    y, x = grid(CH, WT)
    surf = surf_y + 0.7 * per_sin(x, 19, R.uniform(0, 6)) + 0.4 * per_sin(x, 47, R.uniform(0, 6))
    rim_b = crown_h + 0.3 * per_sin(x, 9, 1.0) + 0.2 * per_sin(x, 31, 2.0)
    rgb = np.zeros(y.shape + (3,), np.float32)
    rim = np.clip((rim_b - y) * SC + 0.5, 0, 1)
    lit = np.clip(0.3 + 0.6 * (y / crown_h) ** 2, 0, 1)
    if crown_pat:
        lit = np.clip(crown_pat(lit, x, crown_h - y, y, R), 0, 1)
    rgb += ramp_col(crown, lit) * rim[..., None]
    a_air = np.clip((surf - y) * SC + 0.5, 0, 1) * (1 - rim)
    rgb += ramp_col(ramp(*air), np.clip((y - rim_b) / 6, 0, 1)) * a_air[..., None]
    a = np.maximum(rim, a_air)
    below = np.clip((y - surf) * SC + 0.5, 0, 1)
    mir = np.exp(-(y - surf).clip(0) / 3.2)
    rip = 0.5 + 0.5 * np.sin(x * TAU * 71 / WT + y * 0.9)
    rgb += hexc(mirror) * below[..., None]
    a = np.maximum(a, below * mir * (mir_k + 0.25 * rip))
    ln = np.clip(1 - np.abs(y - surf - 0.2) / 0.55, 0, 1)
    rgb = rgb * (1 - ln[..., None]) + 255 * ln[..., None]
    a = np.maximum(a, ln)
    ol = np.clip(1 - np.abs(y - surf + 0.6) / 0.4, 0, 1) * 0.6
    rgb = rgb * (1 - ol[..., None]) + hexc(out) * ol[..., None]
    ol2 = np.clip(1 - np.abs(y - rim_b) / 0.45, 0, 1) * 0.8
    rgb = rgb * (1 - ol2[..., None]) + hexc(out) * ol2[..., None]
    t = np.zeros((px(CH), px(WT), 4), np.float32)
    t[..., :3] = rgb; t[..., 3] = np.clip(a, 0, 1) * 255
    for k in range(3):
        c3[:, k * px(WT):(k + 1) * px(WT)] = t
    if extra:
        extra(c3, R, rim_b, surf)
    return crop(c3)


# ------------------------------------------------------------------ small shared things
def strands(dst, n, seed, x0, x1, y0, y1, cols, w=(0.25, 0.5), curl=2.0, a=230, dx=0.0):
    """loose strands (hair, fibres, roots): wavy lines from round (x0..x1, y0) down to about y1"""
    R = RS(seed)
    for k in range(n):
        sx = R.uniform(x0, x1); L = R.uniform(0.6, 1.0) * (y1 - y0)
        ph, fr, amp = R.uniform(0, 6), R.uniform(0.08, 0.2), R.uniform(0.5, 1.0) * curl
        pts = [(sx + amp * np.sin(t * fr * L + ph) + dx * t + R.uniform(-0.1, 0.1), y0 + t * L) for t in np.linspace(0, 1, 40)]
        A.stroke(dst, pts, R.uniform(*w), cols[k % len(cols)], a, scale=1.0)


def lump(w, h, seed, rmp, out, bumps=6, flat_bottom=True, soft=1.6, ambient=0.3, hl_t=0.97, rough=0.0):
    """a soft irregular lump sitting on its bottom (or round, flat_bottom False)"""
    R = RS(seed)
    y, x = grid(h, w)
    cy = h if flat_bottom else h / 2
    ry = h if flat_bottom else h / 2 - 0.6
    m = ((x - w / 2) / (w / 2 - 0.6)) ** 2 + ((y - cy) / ry) ** 2 <= 1
    for k in range(bumps):
        bx, by = R.uniform(w * 0.15, w * 0.85), R.uniform(h * 0.25, h * 0.8)
        br = R.uniform(0.18, 0.3) * min(w, h)
        m |= ((x - bx) ** 2 + (y - by) ** 2 <= br * br) & (y < h - 0.5)
    if rough:
        n = ndimage.gaussian_filter(R.uniform(-1, 1, m.shape), 0.8 * SC)
        d = ndimage.distance_transform_edt(m) - ndimage.distance_transform_edt(~m)
        m = (d + n / np.abs(n).max() * rough * SC) > 0
    if flat_bottom:
        m &= y <= h - 0.6
    spr = A.mask_sprite(m, rmp, out, soft=soft, ambient=ambient, hl_t=hl_t)
    return spr


def speckle(spr, seed, n, cols, r=(0.3, 0.8), a=180):
    """flecks on a sprite's opaque part"""
    R = RS(seed)
    I = inner(spr)
    h, w = spr.shape[0] / SC, spr.shape[1] / SC
    for k in range(n):
        fx, fy = R.uniform(0, w), R.uniform(0, h)
        if A.on(spr, fx, fy):
            ellipse_soft(I, fx, fy, R.uniform(*r), R.uniform(r[0] * 0.6, r[1] * 0.6), cols[k % len(cols)], a, R.uniform(0, 3))
    return spr


def trim(spr):
    """drop empty rows at the top and bottom and empty columns at the sides (keeping a pixel)"""
    al = spr[..., 3] > 6
    rows = np.nonzero(al.any(axis=1))[0]; cols = np.nonzero(al.any(axis=0))[0]
    if not len(rows):
        return spr
    return spr[max(0, rows.min() - 1):rows.max() + 2, max(0, cols.min() - 1):cols.max() + 2].copy()


def blob_mask(w, h, seed, n=None, taper=0.45, wob=0.12, flat_bottom=True, rmin=0.3):
    """one soft irregular mass, flat on the bottom: a low heap of rounds side by side (wider than tall) or a column of
    them up a wandering axis, narrower toward the top (taper); merged smooth, kept inside the canvas"""
    R = RS(seed)
    y, x = grid(h, w)
    acc = np.zeros(y.shape, np.float32)
    def add(cx, cy, rx, ry):
        nonlocal acc
        acc = np.maximum(acc, 1 - ((x - cx) / rx) ** 2 - ((y - cy) / ry) ** 2)
    half = w / 2 - 1.2
    if h < 0.85 * w:                                       # a heap
        n = n or 4
        for i in range(n):
            f = (i + 0.5) / n
            rx = half * R.uniform(0.38, 0.55); ry = (h - 1.0) * R.uniform(0.6, 0.85)
            cx = 1.2 + rx + f * (w - 2.4 - 2 * rx) + R.uniform(-1, 1) * 0.5
            add(cx, h - 0.6, rx, ry)
        add(w / 2 + R.uniform(-0.15, 0.15) * w, h - 0.6, half * 0.55, h - 1.2)       # its top
    else:                                                  # a column
        n = n or max(4, int(h / 3.5))
        for i in range(n):
            f = i / max(1, n - 1)
            rx = half * (1 - taper * f) * R.uniform(0.82, 1.0)
            rx = max(rx, w * rmin / 2)
            ry = rx * R.uniform(0.8, 1.1)
            cy = h - 0.6 - ry * 0.75 - f * (h - 1.2 - ry * 1.5)
            cx = w / 2 + R.uniform(-1, 1) * wob * w
            cx = np.clip(cx, 1.2 + rx, w - 1.2 - rx)
            add(cx, cy, rx, ry)
            for k in range(2):                              # knobs on its sides
                a = R.uniform(0, TAU); rr = rx * R.uniform(0.3, 0.45)
                kx = np.clip(cx + np.cos(a) * rx * 0.7, 1.2 + rr, w - 1.2 - rr); ky = cy + np.sin(a) * ry * 0.7
                add(kx, ky, rr, rr)
    acc = ndimage.gaussian_filter(acc, 0.7 * SC)
    m = acc > 0.05
    m &= y <= h - 0.6
    return m


def mass(w, h, seed, rmp, out, taper=0.45, wob=0.12, n=None, soft=1.8, ambient=0.32, hl_t=0.99, grain_k=0.08):
    m = blob_mask(w, h, seed, n=n, taper=taper, wob=wob)
    spr = A.mask_sprite(m, rmp, out, soft=soft, ambient=ambient, hl_t=hl_t)
    if grain_k:
        A.grain(spr, seed, grain_k, 0.5)
    return spr
