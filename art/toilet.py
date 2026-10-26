# Stage 2's first place: inside the toilet bowl, under the water. Drawn like the body's places: a far layer (the
# porcelain wall of the bowl in the water, light from the surface playing on it, the dark throat where it drains), a mid
# layer (bits of paper, bubbles), the porcelain bottom cut through (glaze over vitreous china) and, above, the water's
# surface seen from below under the bowl's rim. Obstacles: stool, wads and rolls of toilet paper, paper hanging down
# from the surface, foam. And the pictures of the flush cut scene at the end of the body (the pile, the lumps, the
# bowl in section).
import numpy as np
from scipy import ndimage
from art import (H, SC, px, grid, canvas, ramp, ramp_col, hexc, paint, ellipse_mask, outline, paste, over, blur, disc,
                 ellipse_soft, inner, smooth_mask, fill_rect)
import anatomy as A
import sprites as S
from tiles import WT, GY, FH, FY0, CH, TAU, wide, crop, put, per_sin, gradient, haze, pcells, wall, band_line, spots
from themes import three, drift, tower, stack, hang_len, bubble, feces

RS = np.random.RandomState
WATER = '#7fb2b8'          # the water's own colour, what everything far away fades into


# ------------------------------------------------------------------ the far layer
def caustics(far, seed, y0=0, y1=GY, k=0.5, n=420):
    """light from the rippling surface, focused into a net of bright wavy lines on the porcelain, fading with depth"""
    h = y1 - y0
    b, _, _ = pcells(h, n, seed, sy=1.5, border=1.1)
    y, x = grid(h, WT)
    wob = 0.5 + 0.5 * np.sin(x * TAU * 23 / WT + y * 0.11) * np.sin(x * TAU * 41 / WT - y * 0.07)
    c = (b ** 2.2) * (0.55 + 0.45 * wob) * np.exp(-y / 85.0) * k
    reg = far[px(y0):px(y0) + y.shape[0]]
    reg[..., :3] = reg[..., :3] * (1 - c[..., None]) + hexc('#f4ffff') * c[..., None]


def light_shafts(far, seed, n=7):
    """slanting soft beams down from the surface (wrapped across the tile)"""
    R = RS(seed)
    y, x = grid(H, WT)
    acc = np.zeros(y.shape, np.float32)
    for k in range(n):
        x0, w, a = R.uniform(0, WT), R.uniform(14, 34), R.uniform(0.18, 0.32)
        d = np.mod(x - x0 - y * a + WT / 2, WT) - WT / 2
        acc += np.exp(-(d / w) ** 2) * R.uniform(0.5, 1.0)
    acc *= np.clip(1 - y / 140.0, 0, 1) ** 1.4 * 0.16
    far[..., :3] = far[..., :3] * (1 - acc[..., None]) + 255 * acc[..., None]


def throat(c3, cx, cy, rw, rh):
    """the bowl's throat: a dark opening where the water goes down into the trap, a glazed lip round it, the water
    swirling in"""
    pad = 6
    y, x = grid(2 * rh + 2 * pad, 2 * rw + 2 * pad)
    dx, dy = (x - rw - pad) / rw, (y - rh - pad) / rh
    r = np.sqrt(dx ** 2 + dy ** 2)
    lip_r = 1 + 5.0 / rw
    spr = np.zeros(y.shape + (4,), np.float32)
    # the lip: a glazed rounded ring, lit from above
    lip = np.clip((lip_r - r) * rw * 0.9, 0, 1) * np.clip((r - 0.96) * rw * 0.9, 0, 1)
    lit = np.clip(0.55 - 0.45 * dy + 0.25 * np.clip(1 - np.abs(r - (1 + lip_r) / 2) * rw / 3, 0, 1), 0, 1)
    lipc = ramp_col(ramp('#5e8a90', '#9cc4c8', '#d4ecee', '#f6ffff', '#ffffff'), lit)
    # the hole: dark, darker deep down, a little light at the top edge
    hole = np.clip((1 - r) * rw * 0.9, 0, 1)
    deep = np.clip(0.15 + 0.5 * (-dy) * 0.5 + 0.35 * np.clip(r, 0, 1) ** 2, 0, 1) * np.clip(0.6 - 0.4 * dy, 0.2, 1)
    holec = ramp_col(ramp('#06161a', '#0c262c', '#163a42', '#2a5c64', '#4a8088'), deep)
    # the swirl: bright curved streaks turning in
    ang = np.arctan2(dy, dx)
    sw = np.clip(1 - np.abs(np.mod(ang * 2 + r * 7.5, TAU / 2) - TAU / 4) / 0.35, 0, 1) * np.clip(r - 0.25, 0, 1) * (r < 1)
    holec = holec * (1 - 0.35 * sw[..., None]) + hexc('#bfe8ec') * 0.35 * sw[..., None]
    rgb = holec * hole[..., None] + lipc * (1 - hole[..., None])
    a = np.maximum(hole, lip)
    # a dark rim line round the hole and outside the lip (the style's outline)
    edge = np.clip(1 - np.abs(r - 1.0) * rw / 0.7, 0, 1) + np.clip(1 - np.abs(r - lip_r) * rw / 0.7, 0, 1)
    rgb = rgb * (1 - 0.7 * np.clip(edge, 0, 1)[..., None]) + hexc('#18343a') * 0.7 * np.clip(edge, 0, 1)[..., None]
    spr[..., :3] = rgb; spr[..., 3] = np.clip(a, 0, 1) * 255
    put(c3, spr, cx - rw - pad, cy - rh - pad)


def toilet_far(seed=401):
    R = RS(seed)
    far = gradient(H, ['#d2ecee', '#a6d2d6', '#80b6bc', '#5e969e'])
    y, x = grid(H, WT)
    curv = 0.08 * np.exp(-((y - 38) / 26) ** 2) - 0.14 * np.clip((y - 96) / 50, 0, 1)
    sheen = 0.07 * np.clip(per_sin(x, 7, 0.4), 0, 1) ** 3 + 0.05 * np.clip(per_sin(x, 13, 1.7), 0, 1) ** 4
    far[..., :3] = np.clip(far[..., :3] * (1 + curv + sheen)[..., None], 0, 255)
    caustics(far, seed + 1)
    light_shafts(far, seed + 2)
    ao = 0.2 * np.clip((y - 112) / 38, 0, 1) ** 1.5                      # darker down by the bottom
    far[..., :3] *= (1 - ao[..., None])
    c3 = three(far)
    for k in range(6):                                    # the glaze's glossy reflections of the light above
        rx, ry = R.uniform(26, 48), R.uniform(5, 9)
        g = canvas(2 * rx + 4, 2 * ry + 4)
        ellipse_soft(g, rx + 2, ry + 2, rx, ry, '#ffffff', 255, R.uniform(-0.15, 0.15))
        g[..., 3] = ndimage.gaussian_filter(g[..., 3], 1.6 * SC) * 0.32
        g[..., :3] = 255                                  # (white all over: only the alpha is soft)
        put(c3, g, R.uniform(0, WT), R.uniform(30, 80))
    for cx in (WT * 0.18, WT * 0.6):                      # the throats, where the water goes down
        throat(c3, cx + R.uniform(-20, 20), 112, 56, 26)
    drift(c3, 70, ['#eefcfc', '#ffffff', '#d8f0f0'], seed + 3, y0=16, y1=GY - 8, a=150)
    far = crop(c3)
    haze(far, WATER, 0.16)
    return far


# ------------------------------------------------------------------ the mid layer: bits of paper, bubbles
def paper_shred(seed, w, h, alpha=0.8):
    """a torn scrap of wet toilet paper drifting: a soft ragged sheet, pale, a little see-through, a fold or two"""
    R = RS(seed)
    y, x = grid(h, w)
    ang = np.arctan2(y - h / 2, (x - w / 2) * h / w)
    rr = np.sqrt(((x - w / 2) / (w / 2)) ** 2 + ((y - h / 2) / (h / 2)) ** 2)
    rag = 0.86 + 0.08 * np.sin(ang * 5 + R.uniform(0, 6)) + 0.05 * np.sin(ang * 11 + R.uniform(0, 6))
    m = rr <= rag
    spr = A.mask_sprite(m, ramp('#9eb4b4', '#c8dada', '#e8f2f0', '#fafcfa', '#ffffff'), '#3e5a60', soft=2.4, ambient=0.5, hl_t=0.995)
    I = inner(spr)
    for k in range(2):                                   # folds: a soft crease line, darker on one side
        a0 = R.uniform(0, np.pi); c0 = R.uniform(-0.3, 0.3) * w
        d = (x - w / 2) * np.cos(a0) + (y - h / 2) * np.sin(a0) - c0
        cr = np.clip(1 - np.abs(d) / 0.9, 0, 1) * m
        I[..., :3] *= (1 - 0.18 * cr[..., None])
    for k in range(int(w * h / 3)):                      # the paper's fibres: faint specks
        fx, fy = R.uniform(0, w), R.uniform(0, h)
        if A.on(spr, fx, fy):
            ellipse_soft(I, fx, fy, R.uniform(0.3, 0.8), 0.15, '#b8cccc', 90, R.uniform(0, 3))
    I[..., 3] *= alpha
    return spr


def toilet_mid(seed=411):
    R = RS(seed)
    mid = wide()
    for k in range(9):
        put(mid, paper_shred(seed + k, R.uniform(8, 15), R.uniform(5, 9)), R.uniform(0, WT), R.uniform(26, GY - 34), 0.9)
    for k in range(10):                                  # chains of small bubbles rising
        x0, y0 = R.uniform(0, WT), R.uniform(70, GY - 20)
        for j in range(R.randint(3, 6)):
            r = int(R.uniform(2, 4))
            b = bubble(r, k * 7 + j); b[..., 3] *= 0.75
            put(mid, b, x0 + 2.5 * np.sin(j * 1.3 + k), y0 - j * R.uniform(7, 11))
    return crop(mid)


# ------------------------------------------------------------------ the bottom (in section) and the surface above
def glaze_pat(sh, x, ld, u, shape, h, R):
    return sh + 0.12 + 0.04 * np.sin(x * TAU * 31 / WT) * np.exp(-ld / 1.2)


def china_pat(sh, x, ld, u, shape, h, R):
    n = int(0.05 * WT * h)
    P = np.c_[R.uniform(0, WT, n), R.uniform(0, h, n)]
    sp = spots(shape, P, R.uniform(0.18, 0.4, n), WT)
    return sh - 0.14 * sp + 0.03 * np.sin(x * 0.9 + ld * 1.7) * np.sin(ld * 0.5)


GLAZE = ramp('#78a8ae', '#b6dade', '#e0f4f4', '#f8ffff', '#ffffff', n=6)
CHINA = ramp('#7c888a', '#9eaaac', '#bcc6c6', '#d4dcdc', '#e8eeee', n=6)


def toilet_floor(seed=421):
    return wall([(4.2, GLAZE, glaze_pat), (40, CHINA, china_pat)], True, seed=seed, bumps=0.25, out='#24444a')


def toilet_ceil(seed=431):
    """the water's surface from below (a bright wavy line, the mirror-bright underside of it) and, above it, the
    underside of the bowl's rim with the holes the flush water comes out of"""
    R = RS(seed)
    c3 = np.zeros((px(CH), 3 * px(WT), 4), np.float32)
    y, x = grid(CH, WT)
    surf = 13.6 + 0.7 * per_sin(x, 19, R.uniform(0, 6)) + 0.4 * per_sin(x, 47, R.uniform(0, 6))
    rim_b = 7.2 + 0.25 * per_sin(x, 9, 1.0)
    rgb = np.zeros(y.shape + (3,), np.float32); a = np.zeros(y.shape, np.float32)
    # the rim: glazed, lit from below by the water's light
    rim = np.clip((rim_b - y) * SC + 0.5, 0, 1)
    lit = np.clip(0.35 + 0.6 * (y / rim_b) ** 2, 0, 1)
    rgb += ramp_col(ramp('#6a8a90', '#a8c6ca', '#dcefef', '#ffffff'), lit) * rim[..., None]
    # the air between the rim and the water, dim
    air = np.clip((surf - y) * SC + 0.5, 0, 1) * (1 - rim)
    rgb += ramp_col(ramp('#4e6e74', '#7a9ca2', '#a6c4c8'), np.clip((y - rim_b) / 6, 0, 1)) * air[..., None]
    a = np.maximum(rim, air)
    # under the surface: its mirror-bright underside, fading into the water
    below = np.clip((y - surf) * SC + 0.5, 0, 1)
    mir = np.exp(-(y - surf).clip(0) / 3.2)
    rip = 0.5 + 0.5 * np.sin(x * TAU * 71 / WT + y * 0.9)
    mc = hexc('#e8fafa') * 1.0
    rgb += mc * below[..., None]
    a = np.maximum(a, below * mir * (0.55 + 0.25 * rip))
    # the surface line itself: bright, with a thin dark edge above (the style's outline)
    ln = np.clip(1 - np.abs(y - surf - 0.2) / 0.55, 0, 1)
    rgb = rgb * (1 - ln[..., None]) + 255 * ln[..., None]
    a = np.maximum(a, ln)
    ol = np.clip(1 - np.abs(y - surf + 0.6) / 0.4, 0, 1) * 0.6
    rgb = rgb * (1 - ol[..., None]) + hexc('#2a4a50') * ol[..., None]
    ol2 = np.clip(1 - np.abs(y - rim_b) / 0.45, 0, 1) * 0.8
    rgb = rgb * (1 - ol2[..., None]) + hexc('#2a4a50') * ol2[..., None]
    t = np.zeros((px(CH), px(WT), 4), np.float32)
    t[..., :3] = rgb; t[..., 3] = np.clip(a, 0, 1) * 255
    c3[:, px(WT):2 * px(WT)] = t
    c3[:, :px(WT)] = t; c3[:, 2 * px(WT):] = t
    for k in range(int(WT / 26)):                         # the rim's flush holes
        hx = k * 26 + 13 + R.uniform(-1, 1)
        for off in (0, WT, 2 * WT):
            ellipse_soft(c3, hx + off, 5.6, 2.2, 0.9, '#1e3a40', 230)
            ellipse_soft(c3, hx + off, 5.1, 1.6, 0.45, '#0c1c20', 230)
    return crop(c3)


# ------------------------------------------------------------------ obstacles
PAPER = ramp('#8fa6a8', '#bccfcf', '#dfeae8', '#f6faf6', '#ffffff')
PAPER_OUT = '#2c4046'


def paper_wad(seed=1, w=22, h=15):
    """a crumpled wad of wet toilet paper: an angular lump made of little flat facets, each catching the light its
    own way, with a soft dark crease between them"""
    R = RS(seed)
    y, x = grid(h, w)
    ang = np.arctan2(y - h * 0.55, (x - w / 2) * h / w)
    rr = np.sqrt(((x - w / 2) / (w / 2)) ** 2 + ((y - h * 0.55) / (h * 0.5)) ** 2)
    n = 9; rad = R.uniform(0.78, 0.98, n)
    k = (ang + np.pi) / (2 * np.pi) * n
    i0 = np.floor(k).astype(int) % n; f = k - np.floor(k)
    lim = rad[i0] * (1 - f) + rad[(i0 + 1) % n] * f                   # straight-ish edges between the corners
    m = (rr <= lim) & (y <= h - 0.6)
    spr = A.mask_sprite(m, PAPER, PAPER_OUT, soft=1.4, ambient=0.45, hl_t=0.99)
    I = inner(spr)
    from scipy.spatial import cKDTree
    pts = np.c_[R.uniform(0, w, 26), R.uniform(0, h, 26)]
    d, idx = cKDTree(pts).query(np.c_[x.ravel(), y.ravel()], k=2)
    d = d.reshape(x.shape + (2,)); idx = idx[:, 0].reshape(x.shape)
    lit = R.uniform(-0.1, 0.08, len(pts))[idx]
    crease = np.clip(1 - (d[..., 1] - d[..., 0]) / 0.45, 0, 1)
    I[..., :3] = np.clip(I[..., :3] * (1 + lit[..., None]) * (1 - 0.15 * crease[..., None]), 0, 255)
    A.grain(spr, seed, 0.03)
    return spr


def paper_roll(h=40, w=19, seed=1, flap=True):
    """a roll of toilet paper standing on end, soaked: the cylinder lit from the left, its top showing the wound layers
    and the cardboard core, a loose sheet hanging down one side"""
    R = RS(seed)
    eh = w * 0.32                                        # the top's ellipse (seen a little from above)
    y, x = grid(h, w)
    cx = w / 2 - 0.5
    body = (np.abs(x - cx) <= w / 2 - 0.6) & (y >= eh / 2) & (y <= h - 1.2)
    top = ((x - cx) / (w / 2 - 0.6)) ** 2 + ((y - eh / 2) / (eh / 2)) ** 2 <= 1
    bot = ((x - cx) / (w / 2 - 0.6)) ** 2 + ((y - (h - 1.2)) / (eh / 2 * 0.8)) ** 2 <= 1
    m = body | top | (bot & (y >= h - 1.2))
    m &= y < h - 0.4
    u = np.clip((x - cx) / (w / 2), -1, 1)
    shade = np.clip(0.75 - 0.42 * u - 0.25 * u ** 4, 0, 1)
    spr = paint(smooth_mask(m), PAPER, shade)
    I = spr
    # the wound layers on the side: faint bands across, a little wavy (soaked)
    bands = np.clip(1 - np.abs(np.mod(y + 0.4 * np.sin(x * 0.8 + seed), 3.2) - 1.6) / 0.18, 0, 1) * body
    I[..., :3] *= (1 - 0.05 * bands[..., None])
    # the top: the paper's end grain in rings, the cardboard core, the hole
    rr = np.sqrt(((x - cx) / (w / 2 - 0.6)) ** 2 + ((y - eh / 2) / (eh / 2)) ** 2)
    ringc = np.where(top, 0.82 + 0.1 * np.sin(rr * 40), 0)
    topc = ramp_col(PAPER, np.clip(ringc, 0, 1))
    core = top & (rr < 0.42); hole = top & (rr < 0.33)
    topc = np.where(core[..., None], ramp_col(ramp('#5a3c1e', '#8a6236', '#b48a58'), np.clip(0.4 + 0.6 * (y < eh / 2), 0, 1)), topc)
    topc = np.where(hole[..., None], ramp_col(ramp('#0e1a1c', '#1e3034', '#33494c'), np.clip((y - eh / 2) / eh + 0.5, 0, 1)), topc)
    I[..., :3] = np.where(top[..., None], topc, I[..., :3])
    edge = top & (rr > 0.9)
    I[..., :3] = np.where(edge[..., None], I[..., :3] * 0.8, I[..., :3])
    spr = outline(spr, PAPER_OUT)
    if flap:                                             # the loose sheet: hangs down from the top on the right
        fw = w * 0.42
        fy = grid(h, w)[0]
        I2 = inner(spr)
        xs = cx + w * 0.12 + 0.6 * np.sin(fy * 0.35)
        fm = (x >= xs) & (x <= xs + fw) & (y > eh * 0.7) & (y < h * 0.78 + 1.5 * np.sin(x * 0.9))
        sheet = A.mask_sprite(fm, PAPER, PAPER_OUT, soft=1.8, ambient=0.45, hl_t=0.99)
        Sh = inner(sheet)
        perf = np.clip(1 - np.abs(np.mod(y - eh, 11.0) - 5.5) / 0.25, 0, 1) * (np.mod(x * 2, 2) < 1) * fm
        Sh[..., :3] *= (1 - 0.3 * perf[..., None])
        over(I2, Sh[..., :3], Sh[..., 3] / 255.0)
    return spr


def paper_strip(seed=1, wdt=13):
    """a long sheet of toilet paper hanging down from the surface, swaying, its perforations showing, torn at the end"""
    L = hang_len()
    R = RS(seed)
    y, x = grid(L, wdt + 8)
    ph = R.uniform(0, 6)
    cx = 4 + wdt / 2 + 2.2 * np.sin(y * 0.045 + ph) * (y / L)
    half = wdt / 2 * (1 - 0.12 * (y / L)) + 0.4 * np.sin(y * 0.3 + ph)
    tear = L - 2.5 - 2.0 * np.abs(np.sin((x - cx) * 1.3 + ph)) - 1.2 * np.sin((x - cx) * 3.1)
    m = (np.abs(x - cx) <= half) & (y <= tear)
    spr = A.mask_sprite(m, PAPER, PAPER_OUT, soft=3.0, ambient=0.5, hl_t=0.995)
    I = inner(spr)
    across = (x - cx) / np.maximum(half, 1)
    I[..., :3] *= (1 - 0.12 * (across ** 2)[..., None] * m[..., None])
    perf = np.clip(1 - np.abs(np.mod(y + 3, 11.0) - 5.5) / 0.22, 0, 1) * (np.mod((x - cx) * 2.2, 2) < 0.9) * m
    I[..., :3] *= (1 - 0.32 * perf[..., None])
    emb = np.clip(1 - np.abs(np.mod(x - cx + y * 0.5, 3.0) - 1.5) / 0.3, 0, 1) * np.clip(1 - np.abs(np.mod(x - cx - y * 0.5, 3.0) - 1.5) / 0.3, 0, 1) * m
    I[..., :3] *= (1 - 0.06 * emb[..., None])                 # the quilted emboss
    lo = np.clip((y - L * 0.55) / (L * 0.45), 0, 1)
    I[..., 3] *= (1 - 0.12 * lo)                              # soaked through lower down
    return spr


def foam(seed=1, w=20, h=15):
    """a clump of soap foam: bubbles of every size stuck together, white with a rainbow sheen"""
    R = RS(seed)
    out = canvas(w, h)
    for k in range(9):
        r = R.uniform(2.2, 4.6)
        bx, by = R.uniform(r + 0.6, w - r - 1.2), R.uniform(r + 0.6, h - r - 1.2)
        m = ellipse_mask(int(2 * r + 1), int(2 * r + 1))
        b = A.mask_sprite(m, ramp('#9ab4c0', '#cfe0e8', '#eef6fa', '#ffffff'), '#2e4a56', soft=1.0, ambient=0.5, hl_t=0.93)
        Ib = inner(b)
        yy, xx = grid(b.shape[0] / SC - 2, b.shape[1] / SC - 2)
        hue = np.arctan2(yy - r, xx - r) * 2 + R.uniform(0, 6)
        irid = np.stack([np.sin(hue), np.sin(hue + 2.1), np.sin(hue + 4.2)], -1) * 40
        rim = np.clip((np.sqrt((xx - r) ** 2 + (yy - r) ** 2) / r - 0.55) / 0.4, 0, 1)
        Ib[..., :3] = np.clip(Ib[..., :3] + irid * rim[..., None], 0, 255)
        paste(out, b, bx - r - 1, by - r - 1)
    return out


def scale_crust(seed=1, w=30, h=12):
    """not used as an obstacle: a lump of the bowl's limescale (urine scale), for the floor's edge"""
    return None


def T_toilet():
    far = toilet_far()
    mid = toilet_mid()
    floor = toilet_floor()
    ceil = toilet_ceil()
    obs = {'low': [feces(24, 15, 11), paper_wad(1), paper_wad(2, 24, 14)],
           'tall': [paper_roll(40, 19, 3), stack([feces(28, 22, 14), feces(24, 20, 15), feces(18, 16, 16)])],
           'hang': [paper_strip(1, 13), paper_strip(2, 11)],
           'float': [foam(1), paper_wad(4, 16, 11)],
           'huge': [tower(lambda H_: stack([paper_roll(H_ / 4 + 0.5, 20 - k, 20 + k, flap=False) for k in range(4)], gap=-0.5))]}
    return dict(far=far, mid=mid, floor=floor, ceil=ceil, obs=obs, coin='drop', special='soap')


# ------------------------------------------------------------------ stage 2's items and hazards (in common.webp)
def drop_item():
    """the coin of stage 2: a drop of clean water (10)"""
    w, h = 11, 14
    y, x = grid(h, w)
    cx = w / 2 - 0.5; r = 4.6
    yt = (h - 1) - r                                      # the round part's centre
    m = (x - cx) ** 2 + (y - yt) ** 2 <= r * r
    t = np.clip((yt - y) / (yt - 0.6), 0, 1)
    m |= (y < yt) & (y > 0.6) & (np.abs(x - cx) <= r * (1 - t) ** 1.25)
    spr = A.mask_sprite(m, ramp('#14508e', '#2a7cc6', '#55a8ec', '#9cd4ff', '#e2f6ff'), '#08243e', soft=1.0, ambient=0.35, hl_t=0.95)
    I = inner(spr)
    pts = [(cx + np.cos(a) * r * 0.62, yt + np.sin(a) * r * 0.62) for a in np.linspace(np.pi * 1.05, np.pi * 1.5, 10)]
    A.stroke(I, pts, 1.0, '#ffffff', 235, scale=1.0)
    ellipse_soft(I, cx + 2.0, yt + 2.2, 0.7, 0.5, '#ffffff', 200)
    return spr


def soap_item():
    """the special of stage 2: a soap bubble (30), clear, a rainbow sheen round its rim, a window glint"""
    r = 6.5
    m = ellipse_mask(int(2 * r + 1), int(2 * r + 1))
    spr = A.mask_sprite(m, ramp('#6a7ab8', '#a8b4e4', '#dce2fa', '#f6f8ff', '#ffffff'), '#2a2a5a', soft=1.2, ambient=0.5, hl_t=0.93)
    I = inner(spr)
    yy, xx = grid(I.shape[0] / SC, I.shape[1] / SC)
    rr = np.sqrt((xx - r) ** 2 + (yy - r) ** 2) / r
    hue = np.arctan2(yy - r, xx - r) * 1.5 + rr * 4
    irid = np.stack([np.sin(hue), np.sin(hue + 2.1), np.sin(hue + 4.2)], -1)
    rim = np.clip((rr - 0.45) / 0.45, 0, 1)
    I[..., :3] = np.clip(I[..., :3] * (1 - 0.35 * rim[..., None]) + (150 + 100 * irid) * 0.35 * rim[..., None], 0, 255)
    see = np.clip(1 - rr / 0.7, 0, 1) * 0.45
    I[..., 3] = np.where(m, 255 * (1 - see), I[..., 3])
    pts = [(r + np.cos(a) * r * 0.66, r + np.sin(a) * r * 0.66) for a in np.linspace(np.pi * 1.1, np.pi * 1.45, 10)]
    A.stroke(I, pts, 1.1, '#ffffff', 240, scale=1.0)
    ellipse_soft(I, r + 3.0, r + 2.6, 0.9, 0.6, '#ffffff', 220)
    return spr


def soggy_sheet(seed=3, w=24, h=8):
    """a sheet of paper fallen flat and soaked on the floor (where a falling wad lands)"""
    R = RS(seed)
    y, x = grid(h, w)
    top = h - 3.6 - 1.2 * np.sin(x * 0.45 + seed) * np.sin(x * 0.17) - 0.8 * np.abs(np.sin(x * 0.9))
    m = (y >= top) & (y <= h - 0.6) & (np.abs(x - w / 2) <= w / 2 - 0.8 - 0.6 * np.sin(y * 3))
    spr = A.mask_sprite(m, PAPER, PAPER_OUT, soft=1.2, ambient=0.5, hl_t=0.99)
    I = inner(spr); I[..., 3] *= 0.92
    return spr


def scale_spike(size='s', seed=4):
    """limescale (urine scale) grown up off the porcelain: a chalky, rough, layered crust in a point"""
    R = RS(seed + (7 if size == 't' else 0))
    w, h = (14, 20) if size == 's' else (16, 32)
    y, x = grid(h, w)
    t = np.clip(y / h, 0, 1)
    cx = w / 2 - 0.5
    jag = 0.6 * np.sin(y * 1.9 + seed) + 0.45 * np.sin(y * 4.3) + 0.3 * np.sin(y * 7.7)
    half = 0.6 + (w / 2 - 0.6) * t ** 0.9 + jag * t
    m = np.abs(x - cx) <= half
    spr = A.mask_sprite(m, ramp('#6e6a5a', '#a4a08a', '#cfcab4', '#ebe7d6', '#fbfaf2'), '#262418', soft=0.9, ambient=0.3, hl_t=0.985)
    A.grain(spr, seed, 0.12, 0.35)
    I = inner(spr)
    lay = np.clip(1 - np.abs(np.mod(y + 0.5 * np.sin(x * 1.3), 2.6) - 1.3) / 0.22, 0, 1) * m * (y > 2)
    I[..., :3] *= (1 - 0.12 * lay[..., None])            # grown in layers
    for k in range(10):
        yy = R.uniform(h * 0.25, h - 1.5); hw = 0.6 + (w / 2 - 0.6) * (yy / h) ** 0.9
        ellipse_soft(I, cx + R.uniform(-0.7, 0.7) * hw, yy, R.uniform(0.4, 0.9), R.uniform(0.3, 0.6), '#c8b070', 150)
    rows = np.nonzero(spr[..., 3].max(axis=1) > 20)[0]
    return spr[:rows.max() + 1]


def tablet_shot():
    """what flies at you in the bowl, spinning: a chip of a blue toilet-cleaner tablet"""
    w, h = 15, 11
    out = canvas(w, h)
    y, x = grid(9, 13)
    m = ((x - 6) / 6.0) ** 2 + ((y - 4) / 3.6) ** 2 <= 1
    m &= ~((x > 9.5) & (y < 2.2))                         # a corner broken off
    t = A.mask_sprite(m, ramp('#0a3a8a', '#1660c8', '#2e8af0', '#7ec0ff', '#d4ecff'), '#061a40', soft=1.0, ambient=0.3, hl_t=0.97)
    It = inner(t)
    R = RS(9)
    for k in range(14):
        sx, sy = R.uniform(1, 12), R.uniform(1, 8)
        if A.on(t, sx, sy):
            ellipse_soft(It, sx, sy, 0.45, 0.35, '#ffffff', 200)
    paste(out, t, 0.5, 1)
    return out


def stage2_sprites():
    return {'it_drop': drop_item(), 'it_soap': soap_item(), 'hz_drop_paper': paper_wad(21, 12, 11), 'hz_puddle_paper': soggy_sheet(),
            'hz_spike_scale_s': scale_spike('s'), 'hz_spike_scale_t': scale_spike('t'), 'hz_shot_tablet': tablet_shot()}


# ------------------------------------------------------------------ the flush cut scene's pictures
def poop_log(L=30, T=11, seed=1, ang=0.0, bend=2.0):
    """a log of stool: a thick rounded sausage, a little bent, bumpy along its sides, creased across, fibre bits"""
    R = RS(seed)
    pad = 2
    ca, sa = np.cos(ang), np.sin(ang)
    W_ = abs(L * ca) + abs(T * sa) + 2 * pad + 2 * bend; H_ = abs(L * sa) + abs(T * ca) + 2 * pad + 2 * bend
    y, x = grid(H_, W_)
    u = (x - W_ / 2) * ca + (y - H_ / 2) * sa                 # along
    v = -(x - W_ / 2) * sa + (y - H_ / 2) * ca                # across
    v = v - bend * (1 - (2 * u / L) ** 2)
    half = T / 2 * (1 + 0.1 * np.sin(u * 0.9 + R.uniform(0, 6)) + 0.06 * np.sin(u * 2.1 + R.uniform(0, 6)))
    cap = np.clip(1 - (np.abs(u) - (L / 2 - T / 2)) / (T / 2), 0, 1)
    endw = np.where(np.abs(u) > L / 2 - T / 2, np.sqrt(np.clip(1 - ((np.abs(u) - (L / 2 - T / 2)) / (T / 2)) ** 2, 0, 1)), 1.0)
    m = (np.abs(v) <= half * endw) & (np.abs(u) <= L / 2)
    spr = A.mask_sprite(m, ramp('#2a1404', '#4c2a0e', '#704418', '#925e28', '#b47e40'), '#140a02', soft=1.4, hl_t=0.985)
    I = inner(spr)
    cr = np.clip(1 - np.abs(np.mod(u + 1.5 * np.sin(v * 0.6), 5.5) - 2.75) / 0.35, 0, 1) * m * (np.abs(v) < half * 0.85)
    I[..., :3] *= (1 - 0.22 * cr[..., None])
    A.grain(spr, seed, 0.1)
    for k in range(int(L / 4)):
        gx, gy = R.uniform(2, W_ - 2), R.uniform(2, H_ - 2)
        if A.on(spr, gx, gy):
            ellipse_soft(spr, gx + 1, gy + 1, 1.1, 0.35, '#c8a050', 230, R.uniform(-0.6, 0.6) + ang)
    return spr


def poop_pile(seed=31):
    """the heap of stool waiting at the end of the way out: logs piled up every which way (about 100 x 52)"""
    w, h = 100, 52
    out = canvas(w, h)
    R = RS(seed)
    layout = [(18, 46, 34, 13, 0.08), (50, 47, 38, 14, -0.05), (80, 46, 32, 13, 0.1),
              (32, 36, 30, 12, -0.35), (62, 35, 34, 13, 0.3), (86, 38, 22, 11, -0.6),
              (44, 25, 28, 12, 0.25), (66, 24, 24, 11, -0.4), (54, 14, 22, 11, 0.05)]
    for i, (cx, cy, L, T, a) in enumerate(layout):
        f = poop_log(L, T, seed + i, a, bend=R.uniform(-2.5, 2.5))
        paste(out, f, cx - f.shape[1] / SC / 2, cy - f.shape[0] / SC / 2)
    return out


def cover(shape_wh, polys, ss=4):
    """anti-aliased coverage of filled polygons (world units) on a w x h area"""
    import cv2
    w, h = shape_wh
    big = np.zeros((px(h) * ss, px(w) * ss), np.uint8)
    for P in polys:
        pts = np.array([[(x + 0.5) * SC * ss, (y + 0.5) * SC * ss] for x, y in P], np.int32)
        cv2.fillPoly(big, [pts], 255, cv2.LINE_AA)
    return cv2.resize(big.astype(np.float32) / 255.0, (px(w), px(h)), interpolation=cv2.INTER_AREA)


def smooth_path(P, n=12):
    """a closed Catmull-Rom curve through the points"""
    out = []
    N = len(P)
    for i in range(N):
        p0, p1, p2, p3 = P[(i - 1) % N], P[i], P[(i + 1) % N], P[(i + 2) % N]
        for k in range(n):
            t = k / n; t2 = t * t; t3 = t2 * t
            out.append(tuple(0.5 * ((2 * p1[j]) + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2 +
                                    (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3) for j in (0, 1)))
    return out


BW = 440                     # the cut scene's picture: wider than any screen (centred), as tall as the game
SURF = 108                   # the water's surface in the bowl


def bowl_shapes(ox=25):
    """the toilet in section (world units, facing right): tank, lid, bowl, its hollow, the trapway, the seat"""
    o = lambda P: [(x + ox, y) for x, y in P]
    tank = o([(62, 28), (66, 22), (114, 22), (118, 28), (118, 92), (114, 98), (66, 98), (62, 92)])
    tlid = o([(57, 18), (60, 14), (120, 14), (123, 18), (123, 22), (57, 22)])
    bowl = o(smooth_path([(112, 76), (180, 74), (250, 74), (302, 75), (308, 80), (304, 90), (288, 108), (266, 126), (244, 140),
                          (236, 150), (238, 166), (160, 166), (156, 150), (134, 126), (116, 102), (110, 86)], 8))
    hollow = o(smooth_path([(136, 80), (210, 79), (286, 80), (282, 94), (266, 114), (244, 130), (220, 140), (196, 143), (180, 140),
                            (164, 128), (150, 112), (140, 96)], 10))
    c_ = [(186, 140), (180, 150), (170, 158), (166, 166)]          # the trapway: a tube from the bottom back and down
    L_, R_ = [], []
    for i, (cx_, cy_) in enumerate(c_):
        a_ = c_[min(i + 1, 3)]; b_ = c_[max(i - 1, 0)]
        tx, ty = a_[0] - b_[0], a_[1] - b_[1]; n_ = np.hypot(tx, ty); nx_, ny_ = -ty / n_, tx / n_
        L_.append((cx_ + nx_ * 5.5, cy_ + ny_ * 5.5)); R_.append((cx_ - nx_ * 5.5, cy_ - ny_ * 5.5))
    trap = o(L_ + R_[::-1])
    seatL = o([(124, 70), (148, 70), (150, 72), (150, 76), (124, 76), (122, 73)])
    seatR = o([(272, 70), (300, 70), (304, 73), (302, 76), (272, 76), (270, 73)])
    return tank, tlid, bowl, hollow, trap, seatL, seatR


def bowl_scene():
    """the bathroom and the toilet cut through (the water drawn apart: bowl_water)"""
    w, h = BW, H
    y, x = grid(h, w)
    img = np.zeros((px(h), px(w), 4), np.float32); img[..., 3] = 255
    # the wall: pale tiles, lighter up top
    wall_c = ramp_col(ramp('#c8d8d2', '#dbe8e2', '#e9f2ee'), np.clip(1 - y / 170, 0, 1))
    gx = np.clip(1 - np.abs(np.mod(x, 22) - 11) / 0.45, 0, 1); gy = np.clip(1 - np.abs(np.mod(y, 22) - 11) / 0.45, 0, 1)
    grout = np.maximum(np.clip((0.5 - np.minimum(np.mod(x, 22), 22 - np.mod(x, 22))) * 2 + 0.5, 0, 1), np.clip((0.5 - np.minimum(np.mod(y, 22), 22 - np.mod(y, 22))) * 2 + 0.5, 0, 1))
    tile_sh = 0.04 * np.sin(np.floor(x / 22) * 1.7 + np.floor(y / 22) * 2.3)
    img[..., :3] = wall_c * (1 + tile_sh[..., None])
    img[..., :3] = img[..., :3] * (1 - 0.35 * grout[..., None]) + hexc('#a8bcb4') * 0.35 * grout[..., None]
    # the floor
    fl = np.clip((y - 166) * SC + 0.5, 0, 1)
    flc = ramp_col(ramp('#8e9aa2', '#aab6bc', '#c0cad0'), np.clip((180 - y) / 14, 0, 1))
    img[..., :3] = img[..., :3] * (1 - fl[..., None]) + flc * fl[..., None]
    fline = np.clip(1 - np.abs(y - 166) / 0.5, 0, 1)
    img[..., :3] = img[..., :3] * (1 - 0.6 * fline[..., None]) + hexc('#4a5a62') * 0.6 * fline[..., None]
    tank, tlid, bowl, hollow, trap, seatL, seatR = bowl_shapes()
    # the toilet's shadow on the wall and the floor
    sh = cover((w, h), [[(px_ + 5, py + 4) for px_, py in P] for P in (tank, bowl)])
    sh = ndimage.gaussian_filter(sh, 3 * SC) * 0.22
    img[..., :3] *= (1 - sh[..., None])
    PORC = ramp('#7e9298', '#aec0c4', '#d6e2e4', '#f2f8f8', '#ffffff')
    OUT = '#1e2e34'

    from art import dome_shade

    def porcelain(cov_, soft=3.0):
        sh_, _ = dome_shade(cov_ > 0.5, (-0.5, -0.75, 0.55), soft=soft, flat=0.55, ambient=0.42)
        rgb = ramp_col(PORC, sh_)
        gl_ = np.clip((sh_ - 0.93) / 0.04, 0, 1) * 0.7      # the glaze's shine
        return rgb * (1 - gl_[..., None]) + 255 * gl_[..., None]

    def lay(cov_, rgb, out=OUT):
        hard = cov_ > 0.5
        dout = ndimage.distance_transform_edt(~hard) / SC
        ring = np.clip(0.95 + 0.5 / SC - dout, 0, 1) * SC
        ring = np.clip(ring, 0, 1)
        img[..., :3] = img[..., :3] * (1 - ring[..., None]) + hexc(out) * ring[..., None]
        img[..., :3] = img[..., :3] * (1 - cov_[..., None]) + rgb * cov_[..., None]
        din = ndimage.distance_transform_edt(hard) / SC
        edge = np.clip(0.9 - din, 0, 1) * cov_
        img[..., :3] = img[..., :3] * (1 - edge[..., None]) + hexc(out) * edge[..., None]

    for P in (tank, tlid):
        c = cover((w, h), [P]); lay(c, porcelain(c))
    c = cover((w, h), [bowl]); lay(c, porcelain(c))
    # the hollow: the inside of the bowl, glazed, in shadow at the back, lit along the front
    hc = cover((w, h), [hollow])
    d = ndimage.distance_transform_edt(hc > 0.5) / SC
    inside = ramp_col(ramp('#62767c', '#8aa0a6', '#b4c6ca', '#d8e4e6'), np.clip(0.3 + 0.07 * np.minimum(d, 6) + 0.25 * np.clip((128 - y) / 40, 0, 1), 0, 1))
    lay(hc, inside)
    gl = np.clip(1 - np.abs(d - 2.2) / 0.5, 0, 1) * (hc > 0.5) * np.clip((x - 230) / 40, 0, 1)
    img[..., :3] = img[..., :3] * (1 - 0.6 * gl[..., None]) + 255 * 0.6 * gl[..., None]     # a glint along the front wall
    tc = cover((w, h), [trap]); lay(tc, ramp_col(ramp('#62767c', '#8aa0a6'), np.full(tc.shape, 0.4)))
    for P in (seatL, seatR):
        c = cover((w, h), [P]); lay(c, ramp_col(ramp('#a8b4b8', '#e2e8ea', '#ffffff'), np.clip(0.5 + 0.5 * (y < 73), 0, 1)))
    # the lid, up against the tank (a slab leaning back from the hinge)
    import math
    hx, hy, L, T_ = 148, 70, 62, 5.5
    a = math.radians(-100)
    ux, uy = math.cos(a), math.sin(a); nx, ny = -uy, ux
    lid = [(hx + nx * -T_ / 2, hy + ny * -T_ / 2), (hx + ux * L + nx * -T_ / 2, hy + uy * L + ny * -T_ / 2),
           (hx + ux * L + nx * T_ / 2, hy + uy * L + ny * T_ / 2), (hx + nx * T_ / 2, hy + ny * T_ / 2)]
    c = cover((w, h), [lid]); lay(c, porcelain(c))
    # the flush button on the lid of the tank
    c = cover((w, h), [[(110, 10), (122, 10), (123, 14), (109, 14)]]); lay(c, ramp_col(ramp('#9aa8ae', '#e8eef0'), np.full(c.shape, 0.7)))
    return img


def bowl_water():
    """the water in the bowl and the trapway, see-through, its surface a bright line (drawn over what falls in)"""
    w, h = BW, H
    y, x = grid(h, w)
    tank, tlid, bowl, hollow, trap, seatL, seatR = bowl_shapes()
    hc = cover((w, h), [hollow]); tc = cover((w, h), [trap])
    surf = SURF + 0.4 * np.sin(x * 0.35)
    under = np.clip((y - surf) * SC + 0.5, 0, 1)
    wc = np.maximum(hc * under, tc)
    wc = ndimage.grey_erosion(wc, size=(3, 3))           # (inside the porcelain's outline)
    out = np.zeros((px(h), px(w), 4), np.float32)
    out[..., :3] = ramp_col(ramp('#2e7480', '#4e98a2', '#7cc0c8', '#b0e2e6'), np.clip(1 - (y - SURF) / 40, 0, 1))
    out[..., 3] = wc * 150
    ln = np.clip(1 - np.abs(y - surf) / 0.6, 0, 1) * hc
    out[..., :3] = out[..., :3] * (1 - ln[..., None]) + 255 * ln[..., None]
    out[..., 3] = np.maximum(out[..., 3], ln * 230)
    return out


def cut_sprites():
    # (v3: the anus packed full of a few huge logs; one big chunk comes into the toilet with the runner)
    return dict(cut_wall=poop_wall(), cut_chunk=big_log(58, 26, 77, 0.0, 3.0))


def big_log(L, T, seed, ang=0.0, bend=4.0, shade=1.0):
    """a big log of stool (poop_log's look, its bumps, creases, fibre bits and shine grown with its size)"""
    R = RS(seed)
    k = T / 11.0
    pad = 2 + 0.25 * T                                     # (its knobs reach past T / 2)
    ca, sa = np.cos(ang), np.sin(ang)
    W_ = abs(L * ca) + abs(T * sa) + 2 * pad + 2 * bend; H_ = abs(L * sa) + abs(T * ca) + 2 * pad + 2 * bend
    y, x = grid(H_, W_)
    u = (x - W_ / 2) * ca + (y - H_ / 2) * sa
    v = -(x - W_ / 2) * sa + (y - H_ / 2) * ca
    v = v - bend * (1 - (2 * u / L) ** 2)
    half = T / 2 * (1 + 0.13 * np.sin(u * 0.5 / k + R.uniform(0, 6)) + 0.07 * np.sin(u * 1.3 / k + R.uniform(0, 6))
                    + 0.04 * np.sin(u * 3.1 / k + R.uniform(0, 6))) * (1 - 0.16 * (2 * u / L) ** 2)     # knobby, thinner to its ends
    endw = np.where(np.abs(u) > L / 2 - T / 2, np.sqrt(np.clip(1 - ((np.abs(u) - (L / 2 - T / 2)) / (T / 2)) ** 2, 0, 1)), 1.0)
    m = (np.abs(v) <= half * endw) & (np.abs(u) <= L / 2)
    spr = A.mask_sprite(m, ramp('#2a1404', '#4c2a0e', '#704418', '#925e28', '#b47e40'), '#140a02', soft=1.4 * k, hl=shade > 0.9, hl_t=0.993)
    I = inner(spr)
    cr = np.clip(1 - np.abs(np.mod(u + 1.5 * k * np.sin(v * 0.6 / k), 5.5 * k) - 2.75 * k) / (0.35 * k), 0, 1) * m * (np.abs(v) < half * 0.85)
    I[..., :3] *= (1 - 0.2 * cr[..., None])
    I[..., :3] *= shade
    A.grain(spr, seed, 0.09, 0.6 * k)
    for j in range(int(L * T / 260)):
        gx, gy = R.uniform(2, W_ - 2), R.uniform(2, H_ - 2)
        if A.on(spr, gx, gy):
            ellipse_soft(spr, gx + 1, gy + 1, 1.2 * k ** 0.5, 0.38 * k ** 0.5, '#c8a050', 200, R.uniform(-0.6, 0.6) + ang)
    return spr


def poop_wall(seed=61, w=350, h=146):
    """the end of the anus packed full of stool, from the floor to the roof: a few huge logs jammed in, in three rows,
    the ones behind darker, the dark of the mass between them; its face (the left, where the runner goes in) the round
    ends of the front ones"""
    out = canvas(w, h)
    # (centre x, centre y, length, thickness, angle, bend, shade): behind first, the face's last
    logs = [(300, 36, 210, 54, 0.06, -6, 0.62), (310, 80, 210, 56, -0.08, 7, 0.6), (300, 120, 210, 52, 0.04, -5, 0.62),
            (232, 56, 130, 50, 0.42, 7, 0.74), (238, 104, 130, 50, -0.38, -7, 0.74),
            (122, 35, 175, 52, -0.07, 6, 0.95), (140, 78, 195, 56, 0.06, -7, 1.0), (124, 120, 165, 50, -0.04, 6, 0.97)]
    tmp = canvas(w, h)
    for i, (cx, cy, L, T, a, bnd, sh) in enumerate(logs):
        f = big_log(L, T, seed + 10 * i, a, bnd, sh)
        paste(tmp, f, cx - f.shape[1] / SC / 2, cy - f.shape[0] / SC / 2)
    # the dark of the mass in between (where the logs close round, not outside them)
    al = tmp[..., 3] > 128
    closed = ndimage.binary_fill_holes(ndimage.binary_closing(al, iterations=px(10)))
    base = np.zeros_like(out); base[..., :3] = hexc('#1c0d05'); base[..., 3] = ndimage.gaussian_filter(closed.astype(np.float32), 1.0) * 255
    out[:] = base
    over(out, tmp[..., :3], tmp[..., 3] / 255.0)
    out[..., 3] = np.maximum(out[..., 3], tmp[..., 3])
    out[px(h + 1):, :, 3] = 0                                   # nothing below the floor
    return out


