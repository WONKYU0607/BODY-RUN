# Tileable layers for the side-scroller (HD): every theme gives a far layer (opaque, scrolls slowest), a mid layer
# (see-through, scrolls faster), a floor strip and (most) a ceiling strip, each WT units wide and wrapping seamlessly.
# Seamless: things are placed in [0, WT) and drawn three times (x - WT, x, x + WT) on a triple-wide canvas whose
# middle third is kept; fields use whole numbers of waves across WT; cell patterns measure distance with wrap.
import numpy as np
import cv2
from scipy import ndimage
from art import (H, SC, px, grid, ramp, ramp_col, hexc, paint, ellipse_mask, outline, paste, fill_rect, vgrad, over,
                 wgrad, blur)

WT = 1170           # a tile: three screens wide
GY = 150            # top of the floor
FH = 44             # floor strip: from y = H - FH (decorations above the edge) to the bottom
FY0 = H - FH
CH = 30             # ceiling strip: y 0..CH
TAU = 2 * np.pi


def wide(h=H):
    return np.zeros((px(h), 3 * px(WT), 4), np.float32)


def crop(c3):
    return c3[:, px(WT):2 * px(WT)].copy()


def tile3(arr):
    """a tile laid three times side by side (to draw things across the seam)"""
    return np.concatenate([arr, arr, arr], axis=1)


def put(c3, spr, x, y, a=1.0):
    for k in (0, 1, 2):
        paste(c3, spr, x + k * WT, y, a)


def per_sin(x, k, ph=0.0):
    return np.sin(x * TAU * k / WT + ph)


def gradient(h, cols):
    c = np.zeros((px(h), px(WT), 4), np.float32)
    vgrad(c, ramp(*cols))
    return c


def haze(arr, col, k):
    c = hexc(col)
    arr[..., :3] = arr[..., :3] * (1 - k) + c * k


def pcells(h, n, seed, sy=1.3, border=1.0, ww=None):
    """wrapped Voronoi at HD: border (0 inside .. 1 on the border), distance to the nearest seed, index of the nearest"""
    from scipy.spatial import cKDTree
    ww = ww or WT
    R = np.random.RandomState(seed)
    pts = np.c_[R.uniform(0, ww, n), R.uniform(0, h, n) * sy + 2]
    tree = cKDTree(pts, boxsize=[ww, h * sy * 4 + 10])
    y, x = grid(h, ww)
    q = np.c_[np.mod(x.ravel(), ww).astype(np.float64), (y.ravel() * sy + 2).astype(np.float64)]
    d, i = tree.query(q, k=2)
    Hh, Ww = y.shape
    d = d.reshape(Hh, Ww, 2).astype(np.float32); i = i[:, 0].reshape(Hh, Ww)
    return np.clip(1 - (d[..., 1] - d[..., 0]) / border, 0, 1), d[..., 0], i


def seeds(h, n, seed, sy=1.3):
    R = np.random.RandomState(seed)
    return np.c_[R.uniform(0, WT, n), R.uniform(0, h, n)]


def spots(shape, pts, r, wrap_w=None):
    """coverage (0..1) of anti-aliased discs at old-style points (x, y) with radius r units (scalar or per point)"""
    m = np.zeros(shape[:2], np.uint8)
    rs_ = np.broadcast_to(np.asarray(r, np.float64), (len(pts),))
    for (x, y), rr in zip(pts, rs_):
        for off in ((0,) if wrap_w is None else (-wrap_w, 0, wrap_w)):
            cx, cy = int(round((x + off + 0.5) * SC * 16)), int(round((y + 0.5) * SC * 16))
            cv2.circle(m, (cx, cy), max(1, int(round(rr * SC * 16))), 255, -1, cv2.LINE_AA, 4)
    return np.clip(ndimage.gaussian_filter(m.astype(np.float32) / 255.0, 0.55) * 1.15, 0, 1)      # round, soft-edged


def dashes(shape, pts, length, thick, ang=0.0, wrap_w=None):
    """coverage of short rounded dashes (spindle shapes) centred at old-style points"""
    m = np.zeros(shape[:2], np.uint8)
    for (x, y) in pts:
        for off in ((0,) if wrap_w is None else (-wrap_w, 0, wrap_w)):
            cx, cy = (x + off + 0.5) * SC, (y + 0.5) * SC
            cv2.ellipse(m, (int(round(cx * 16)), int(round(cy * 16))), (max(1, int(round(length / 2 * SC * 16))), max(1, int(round(thick / 2 * SC * 16)))),
                        np.degrees(ang), 0, 360, 255, -1, cv2.LINE_AA, 4)
    return m.astype(np.float32) / 255.0


def band_line(v, period, width, phase=0.0):
    """1 on thin lines every `period` units of v (width units wide, soft-edged), 0 between"""
    f = np.mod(v - phase, period)
    d = np.minimum(f, period - f)
    return np.clip((width / 2 - d) * SC + 0.5, 0, 1)


# ------------------------------------------------------------------ the organ wall in section, tileable
def wall(layers, top_edge=True, seed=1, bumps=1.0, out='#1a050c', h=None, surface=None, thickness=None):
    """the wall cut through as a strip WT wide. top_edge: a floor (lumen above), else a ceiling (lumen below).
    layers: (thickness, ramp, pattern) from the lumen outward. Returns the strip (floor: FH tall, the edge at
    y = GY - FY0; ceiling: CH tall, the edge at about y = 14)"""
    R = np.random.RandomState(seed)
    h = h or (FH if top_edge else CH)
    ph1, ph2 = R.uniform(0, 6), R.uniform(0, 6)
    y, x = grid(h, WT)
    edge = bumps * per_sin(x, 9, ph1) + 0.7 * bumps * per_sin(x, 23, ph2)          # (1, WT) continuous
    e0 = (GY - FY0) if top_edge else 14
    dep = (y - e0 - edge + 0.5) if top_edge else (e0 - 0.5 - y - edge)              # 0 on the lumen surface
    Hh, Ww = dep.shape
    rgb = np.zeros((Hh, Ww, 3), np.float32)
    shape = (Hh, Ww)
    d0 = 0.0
    RR = np.random.RandomState(seed + 31)
    for li, (th, rmp, pat) in enumerate(layers):
        last = li == len(layers) - 1
        u = np.clip((dep - d0) / max(th, 1), 0, 1)
        sh = 0.85 - 0.35 * u
        ld = dep - d0                                                            # depth within the layer
        if pat == 'pits':            # gastric pits: narrow tubes going down from the surface, cells between
            xx = x + 0.6 * per_sin(x, 41, ph1) + 0.25 * np.sin(ld * 0.9 + x * 0.7)
            tube = band_line(xx, 6, 0.9, 3.0) * (u < 0.82) * np.clip((0.82 - u) * 8, 0, 1)
            sh = sh - 0.42 * tube + 0.1 * band_line(xx, 6, 0.6, 0.0)
        elif pat == 'crypts':        # intestinal crypts: tubes in the deeper part
            xx = x + 0.5 * per_sin(x, 37, ph2)
            tube = band_line(xx, 7, 1.0, 3.5) * np.clip((u - 0.22) * 8, 0, 1)
            sh = sh - 0.38 * tube
        elif pat == 'squamous':      # stratified squamous: flattened cells in rows
            row = np.floor(ld / 1.6)
            xs_ = x + row * 4.3
            sh = sh - 0.16 * band_line(xs_, 8, 0.35) - 0.06 * band_line(ld, 1.6, 0.3)
            px_ = np.mod(xs_, 8) - 4; py_ = np.mod(ld, 1.6) - 0.8
            sh = sh - 0.22 * np.clip(1 - np.sqrt((px_ / 1.4) ** 2 + (py_ / 0.38) ** 2), 0, 1) ** 0.5
        elif pat == 'elastic':       # artery media: wavy elastic lamellae
            wave = 0.8 * np.sin(x * TAU * 130 / WT)
            lam = band_line(ld + wave, 3, 0.7)
            sh = sh - 0.25 * lam + 0.06 * (1 - lam)
        elif pat == 'smooth':        # smooth muscle: spindle cells with long nuclei
            row = np.floor(ld / 3.0)
            xs_ = x + row * 5.0
            px_ = np.mod(xs_, 10) - 5; py_ = np.mod(ld, 3.0) - 1.5
            nuc = np.clip(1 - np.sqrt((px_ / 1.9) ** 2 + (py_ / 0.42) ** 2), 0, 1) ** 0.4
            sh = sh - 0.22 * nuc - 0.05 * band_line(ld, 3.0, 0.25)
        elif pat == 'striated':      # heart muscle: fibres with cross-striations
            fib = band_line(ld, 4, 0.5)
            stri = band_line(x + 0.4 * np.sin(ld * 0.8), 1.5, 0.35)
            sh = sh - 0.22 * fib - 0.08 * stri * (1 - fib)
        elif pat == 'loose':         # loose connective tissue: pale, scattered cells, a few fibres
            n = int(0.035 * WT * h)
            P = np.c_[RR.uniform(0, WT, n), RR.uniform(0, h, n)]
            sp = spots(shape, P, RR.uniform(0.35, 0.6, n), WT)
            fib = band_line(ld + 1.2 * per_sin(x, 60, li), 2.6, 0.25)
            sh = sh - 0.24 * sp - 0.04 * fib
        elif pat == 'fat':           # fat cells: big round pale cells with thin walls
            cb, _, _ = pcells(h, 70, seed + 9, border=1.0)
            sh = 0.82 - 0.35 * cb ** 2
        elif pat == 'gray':          # grey matter: small cell bodies scattered
            n = int(0.03 * WT * h)
            P = np.c_[RR.uniform(0, WT, n), RR.uniform(0, h, n)]
            sh = sh - 0.32 * spots(shape, P, RR.uniform(0.4, 0.7, n), WT)
        elif pat == 'white':         # white matter: fibres running along
            sh = sh + 0.07 * band_line(ld + 0.5 * per_sin(x, 50, li), 2, 0.6) - 0.05 * band_line(x, 9, 0.4)
        elif pat == 'endo':          # a thin bright lining
            sh = sh + 0.1
        elif callable(pat):          # a pattern of the theme's own: pat(sh, x, ld, u, shape, h, R) -> sh
            sh = pat(sh, x, ld, u, shape, h, RR)
        col = ramp_col(rmp, np.clip(sh, 0, 1))
        if last:
            wgt = np.clip(ld * SC + 0.5, 0, 1)
        else:
            wgt = np.clip(ld * SC + 0.5, 0, 1) * np.clip((th - ld) * SC + 0.5, 0, 1)
        rgb += col * wgt[..., None]
        d0 += th
    # past the last layer: the last layer's darkest colour (fades in)
    rest = np.clip((dep - d0) * SC / 4, 0, 1)
    rgb = rgb * (1 - rest[..., None]) + np.array(layers[-1][1][0]) * rest[..., None]
    # the lumen edge: an outline, a lit wet rim, glints
    ow = 0.72
    o = np.clip((ow - dep) * SC + 0.5, 0, 1)
    rim = np.clip(1 - np.abs(dep - ow - 0.9) / 1.0, 0, 1) * 0.5
    rgb = rgb * (1 - rim[..., None]) + np.array(layers[0][1][-1]) * rim[..., None]
    gl = np.clip(1 - np.abs(dep - ow - 0.35) / 0.35, 0, 1) * np.clip(0.5 + 0.9 * np.sin(x * TAU * 117 / WT + R.uniform(0, 6)), 0, 1) * 0.6
    rgb = rgb * (1 - gl[..., None]) + 255 * gl[..., None]
    rgb = rgb * (1 - o[..., None]) + hexc(out) * o[..., None]
    alpha = np.clip(dep * SC + 0.5, 0, 1)
    spr = np.zeros((Hh, Ww, 4), np.float32)
    spr[..., :3] = rgb; spr[..., 3] = alpha * 255
    if surface:
        c3 = tile3(spr)
        xs_w = np.arange(WT)
        edge_w = bumps * per_sin(xs_w, 9, ph1) + 0.7 * bumps * per_sin(xs_w, 23, ph2)
        surface(c3, edge_w, e0, top_edge)
        spr = crop(c3)
    return spr


# ------------------------------------------------------------------ obstacles: (kind, sprite) per theme
def hitbox(spr, shrink=0.18, capx=1e9, capy=1e9):
    """[x0, y0, x1, y1] in world units of the sprite's opaque part, shrunk a little (by a share of its size, at most
    capx / capy units a side: given for hanging and floating pieces, whose bottom must reach a standing runner's head)"""
    a = spr[..., 3] > 128
    ys, xs = np.nonzero(a)
    x0, x1, y0, y1 = xs.min() / SC, (xs.max() + 1) / SC, ys.min() / SC, (ys.max() + 1) / SC
    dx, dy = min((x1 - x0) * shrink / 2, capx), min((y1 - y0) * shrink / 2, capy)
    return [round(x0 + dx, 2), round(y0 + dy, 2), round(x1 - dx, 2), round(y1 - dy, 2)]
