# Real things of the body, drawn in the style of the characters (no faces), HD: what lines each lumen, and the
# obstacles (food, folds, mucus, bacteria, plaque, clots, white cells, the valve, plaques and tangles of the brain,
# axons). Laid out in world units like the pixel version.
import numpy as np
from scipy import ndimage
from art import (W, H, SC, px, grid, canvas, ramp, ramp_col, hexc, paint, dome_shade, ellipse_mask, outline, highlight,
                 paste, fill_rect, inner, over, disc, ellipse_soft, stroke as _stroke, dot as _dot, smooth_mask)
import sprites as S

LIGHT = (-0.55, -0.7, 0.45)


def rs(seed):
    return np.random.RandomState(seed)


def dot(dst, x, y, col, a=255, r=0.55):
    _dot(dst, x, y, col, a, r)


def stroke(dst, pts, wdt, col, a=255, scale=None):
    _stroke(dst, pts, wdt, col, a, scale)


def mask_sprite(m, rmp, out, soft=1.2, ambient=0.25, hl=True, hl_t=0.975, steps=7):
    spr, _ = S.blob(m, rmp, out, hl='#ffffff' if hl else None, hl_t=hl_t, soft=soft, ambient=ambient, steps=steps)
    return spr


def on(spr, x, y):
    """is the old-style point (x, y) on an opaque part of spr"""
    X, Y = px(x + 0.5), px(y + 0.5)
    return 0 <= X < spr.shape[1] and 0 <= Y < spr.shape[0] and spr[Y, X, 3] > 200


def grain(spr, seed, k=0.06, scale=0.6):
    """a little fine mottling over the opaque part (organic texture)"""
    R = rs(seed)
    h, w = spr.shape[:2]
    n = ndimage.gaussian_filter(R.uniform(-1, 1, (h, w)).astype(np.float32), scale * SC)
    n /= max(np.abs(n).max(), 1e-6)
    spr[..., :3] *= (1 + k * n[..., None])
    return spr


# ------------------------------------------------------------------ stomach / oesophagus
def food_bolus(seed=1, w=26, h=17):
    """a lump of half-digested food: brown mash with rice grains and a bit of green leaf"""
    R = rs(seed)
    y, x = grid(h, w)
    m = ((x - w / 2) / (w / 2)) ** 2 + ((y - h) / h) ** 2 <= 1
    for k in range(5):
        bx, by, br = R.uniform(4, w - 4), R.uniform(h * 0.3, h * 0.8), R.uniform(3, 5)
        by = max(by, br + 0.3); bx = min(max(bx, br + 0.3), w - 1.3 - br)
        m |= (x - bx) ** 2 + (y - by) ** 2 <= br * br
    spr = mask_sprite(m, ramp('#3a2008', '#6a3c12', '#9a6020', '#c08a40', '#e0b878'), '#1a0c02', hl_t=0.99)
    grain(spr, seed, 0.08)
    for k in range(7):                               # rice grains
        gx_, gy_ = R.uniform(5, w - 4), R.uniform(5, h - 2)
        if on(spr, gx_, gy_):
            ellipse_soft(spr, gx_ + 0.6, gy_ + 0.35, 1.25, 0.55, '#b8a888', 255, R.uniform(-0.4, 0.4))
            ellipse_soft(spr, gx_ + 0.5, gy_, 1.15, 0.5, '#f4ecd8', 255, R.uniform(-0.4, 0.4))
    for k in range(2):                               # leaf bits
        gx_, gy_ = R.uniform(6, w - 6), R.uniform(6, h - 3)
        ellipse_soft(spr, gx_ + 1.2, gy_ + 0.6, 1.7, 1.0, '#3a8a2a', 255, R.uniform(-0.8, 0.8))
        ellipse_soft(spr, gx_ + 0.8, gy_ + 0.3, 0.8, 0.4, '#7ac85a', 255)
    return spr


def food_bit(seed=1, w=8, h=6):
    """a small lump of food drifting in the lumen: round, lumpy, a grain or two"""
    R = rs(seed)
    W_, H_ = w + 4, h + 4
    y, x = grid(H_, W_)
    m = ((x - W_ / 2 + 0.5) / (w / 2)) ** 2 + ((y - H_ / 2 + 0.5) / (h / 2)) ** 2 <= 1
    for k in range(3):
        bx, by, br = R.uniform(3, W_ - 3), R.uniform(3, H_ - 3), R.uniform(1.4, min(w, h) * 0.45)
        m |= (x - bx) ** 2 + (y - by) ** 2 <= br * br
    spr = mask_sprite(m, ramp('#3a2008', '#6a3c12', '#9a6020', '#c08a40', '#e0b878'), '#1a0c02', soft=0.8, hl_t=0.97)
    grain(spr, seed, 0.08)
    gx_, gy_ = R.uniform(W_ * 0.35, W_ * 0.65), R.uniform(H_ * 0.35, H_ * 0.6)
    ellipse_soft(spr, gx_ + 1, gy_ + 1, 0.9, 0.42, '#f4ecd8', 255, R.uniform(-0.5, 0.5))
    return spr


def fold_hang(w=30, L=90, seed=3):
    """a fold of the stomach lining bulging down from the ceiling (rugae): fleshy, dotted with pits, glazed with
    mucus, a drop of mucus at its lowest point"""
    R = rs(seed)
    y, x = grid(L, w)
    half = w / 2 * (0.62 + 0.38 * (1 - y / L) ** 1.5) * (1 + 0.06 * np.sin(y * 0.2 + seed))
    m = (np.abs(x - w / 2 + 0.5) <= half)
    tip = ((x - w / 2 + 0.5) / (w / 2 * 0.62)) ** 2 + ((y - (L - w * 0.31)) / (w * 0.31)) ** 2 <= 1
    m = (m & (y < L - w * 0.31)) | tip
    spr = mask_sprite(m, ramp('#5a1028', '#8e2240', '#b8385a', '#dc5a76', '#f48aa0', '#ffc0cc'), '#1e040c', soft=2.2, hl_t=0.985)
    I = inner(spr)
    # gastric pits: little dark dots in staggered rows
    row = np.round(y / 3.0)
    ci = np.round((x + row * 2.5) / 5.0)
    hsh = lambda a_, b_, s_: np.mod(np.sin(a_ * 12.9898 + b_ * 78.233 + s_ + seed) * 43758.5453, 1.0)
    cxp = ci * 5.0 - row * 2.5 + (hsh(row, ci, 0.0) - 0.5) * 1.6
    cyp = row * 3.0 + (hsh(row, ci, 1.3) - 0.5) * 0.9
    rad = 0.36 + 0.2 * hsh(row, ci, 2.9)
    pit = np.clip((rad - np.sqrt((x - cxp) ** 2 + ((y - cyp) * 1.3) ** 2)) * SC + 0.5, 0, 1) * (np.abs(x - w / 2) < half - 2)
    I[..., :3] = I[..., :3] * (1 - 0.75 * pit[..., None]) + hexc('#4a0a20') * 0.75 * pit[..., None]
    # mucus glaze down its lit side
    gl = np.clip(1 - np.abs(x - (w / 2 - half * 0.55)) / (half * 0.22 + 0.5), 0, 1) * (0.55 + 0.45 * np.sin(y * 0.35 + seed)) * m
    I[..., :3] = I[..., :3] * (1 - 0.45 * gl[..., None]) + hexc('#ffe4ea') * 0.45 * gl[..., None]
    grain(spr, seed + 3, 0.05)
    # a hanging drop of mucus, clear
    d = ellipse_mask(7, 9)
    ds = mask_sprite(d, ramp('#b8b8a0', '#e0e0cc', '#f4f4e8', '#ffffff'), '#4a4a3a', soft=0.6, ambient=0.5)
    ds[..., 3] *= 0.85
    paste(spr, ds, w / 2 - 3.5, L - 2)
    out = canvas(w + 2, L + 10); paste(out, spr, 0, 0)
    return out


def h_pylori(w=24, h=12):
    """Helicobacter: a short spiral rod with a tuft of flagella at one end"""
    spr = canvas(w + 12, h + 4)
    xs = np.linspace(2, w - 1, 120)
    pts = [(xx, h / 2 + 2 + 3.2 * np.sin(xx * 0.42)) for xx in xs]
    for k in range(4):                                 # flagella at the tail
        fl = [(w - 1 + i, h / 2 + 2 + 3.2 * np.sin((w - 1) * 0.42) + (k - 1.5) * 1.6 + 1.2 * np.sin(i * 0.9 + k)) for i in np.linspace(0, 10, 40)]
        stroke(spr, fl, 1.2, '#2a3a14', scale=1.0)
        stroke(spr, fl, 0.6, '#7a9a3a', scale=1.0)
    stroke(spr, pts, 6.4, '#1e2a10', scale=1.0)
    stroke(spr, pts, 4.6, '#6a8a32', scale=1.0)
    stroke(spr, [(px_, py - 0.6) for px_, py in pts], 2.6, '#8aaa4a', scale=1.0)
    stroke(spr, [(px_, py - 1.1) for px_, py in pts], 1.0, '#c8e48a', scale=1.0)
    return spr


# ------------------------------------------------------------------ small intestine
def villus_real(h, w, seed, hang=False, cols=None, dim=0.0):
    """an intestinal villus: a soft finger with a white lacteal up its middle, red capillaries round it, goblet cells
    (white dots) and a fuzzy brush border along its edge"""
    R = rs(seed)
    y, x = grid(h, w)
    r = (w - 1) / 2
    wob = 0.6 * np.sin(y * 0.18 + seed)
    m = (y >= r) & (np.abs(x - r - wob) <= r * (0.82 + 0.18 * y / h))
    m |= (x - r) ** 2 + (y - r) ** 2 <= r * r
    cols = cols or ramp('#7a1e30', '#b0384a', '#d85a68', '#f08a90', '#ffb8b8')
    if hang:
        m = m[::-1]
    spr = mask_sprite(m, cols, '#2a0810', soft=1.0, ambient=0.3)
    # the brush border: a fine pale fuzz just inside the edge (microvilli)
    I = inner(spr)
    dd = ndimage.distance_transform_edt(m) / SC
    fuzz = np.clip(1 - np.abs(dd - 0.45) / 0.3, 0, 1) * m
    I[..., :3] = I[..., :3] * (1 - 0.38 * fuzz[..., None]) + hexc('#ffe0e4') * 0.38 * fuzz[..., None]
    js = np.linspace(r + 1, h, max(4, int((h - r) * 3))) if not hang else np.linspace(1, h - r - 1, max(4, int((h - r) * 3)))
    lac = [(r + 1 + 0.6 * np.sin(j * 0.18 + seed), j + 0.5) for j in js]
    stroke(spr, lac, 1.1, '#fff0e8', 190, scale=1.0)
    for k in range(int(h / 3)):                           # capillary loops (red) and goblet cells (white)
        j = R.uniform(r, h - 2) if not hang else R.uniform(2, h - r)
        side = R.choice([-1, 1])
        ellipse_soft(spr, r + 1 + side * r * 0.55, j + 1, 0.4, 0.9, '#c8102a', 200)
        if R.uniform() < 0.35:
            disc(spr, r + 1 + side * r * 0.8, j + 1, 0.5, '#ffffff', 220)
    if dim:
        al = spr[..., 3] > 0
        spr[al, :3] = spr[al, :3] * (1 - dim) + hexc('#3a0e18') * dim
    return spr


def plica(h=40, w=30, seed=3):
    """a circular fold (plica) rising from the floor, carpeted with villi: the tall one, jump twice"""
    spr = canvas(w + 8, h + 2)
    y, x = grid(h, w)
    m = ((x - w / 2) / (w / 2)) ** 2 + ((y - h) / (h * 0.85)) ** 2 <= 1
    base = mask_sprite(m, ramp('#6a1828', '#a03040', '#c84e5c', '#e8747e', '#ffa8a8'), '#2a0810', soft=1.8)
    grain(base, seed, 0.05)
    paste(spr, base, 3, 1)
    R = rs(seed)
    for k in range(9):                                   # villi standing on it
        a = R.uniform(-1.2, 1.2)
        cx = w / 2 + np.sin(a) * w * 0.38 + 4; cy = h - np.cos(a) * h * 0.78
        v = villus_real(int(R.uniform(9, 13)), 5, seed + k)
        paste(spr, v, cx - 3, cy - v.shape[0] / SC + 3)
    return spr


def chyme_fat(seed=2):
    """fat droplets in the chyme: a cluster of glossy yellow spheres"""
    spr = canvas(26, 18)
    R = rs(seed)
    for k in range(6):
        r = R.uniform(3.5, 6.5)
        m = ellipse_mask(int(2 * r) + 1, int(2 * r) + 1)
        b = mask_sprite(m, ramp('#8a6a10', '#c8a020', '#f0d050', '#fff090', '#ffffd0'), '#3a2a04', soft=0.8, ambient=0.35, hl_t=0.93)
        paste(spr, b, R.uniform(0, 26 - 2 * r - 2), 18 - 2 * r - 2 - (R.uniform(0, 6) if k > 2 else 0))
    return spr


def e_coli(w=22, h=9):
    """E. coli: a rod with fine flagella all round"""
    spr = canvas(w + 10, h + 10)
    R = rs(5)
    for k in range(9):
        a0 = R.uniform(0, 2 * np.pi)
        sx, sy = 5 + w / 2 + np.cos(a0) * w * 0.45, 5 + h / 2 + np.sin(a0) * h * 0.45
        pts = [(sx + np.cos(a0) * i * 0.9 + 0.8 * np.sin(i * 1.3 + k), sy + np.sin(a0) * i * 0.9 + 0.8 * np.cos(i * 1.3 + k)) for i in np.linspace(0, 6, 25)]
        stroke(spr, pts, 0.8, '#c09068', 210, scale=1.0)
    y, x = grid(h, w)
    r = (h - 1) / 2
    m = ((x - r) ** 2 + (y - r) ** 2 <= r * r + 0.5) | ((x - (w - 1 - r)) ** 2 + (y - r) ** 2 <= r * r + 0.5) | ((x >= r) & (x <= w - 1 - r))
    body = mask_sprite(m, ramp('#5a3418', '#8e5a2e', '#c08a52', '#e8b884', '#ffe0c0'), '#24120a', soft=1.0)
    grain(body, 5, 0.05)
    paste(spr, body, 4, 4)
    return spr


# ------------------------------------------------------------------ blood vessel
def neutrophil(size=20, seed=1):
    """a white blood cell: pale granular cytoplasm and a dark purple nucleus in several lobes"""
    R = rs(seed)
    y, x = grid(size, size)
    m = ((x - size / 2) ** 2 + (y - size / 2) ** 2) <= (size / 2 - 0.6 * np.sin(np.arctan2(y - size / 2, x - size / 2) * 5) - 0.3) ** 2
    spr = mask_sprite(m, ramp('#8a7a98', '#b8a8c8', '#dccfe8', '#f0e8f8', '#ffffff'), '#2a1e38', soft=1.5, hl_t=0.985)
    for k in range(int(size * 2.2)):                      # granules
        gx_, gy_ = R.uniform(2, size), R.uniform(2, size)
        if on(spr, gx_, gy_):
            disc(spr, gx_, gy_, R.uniform(0.3, 0.45), '#b898d0', 200)
    for k in range(3):                                    # nuclear lobes, joined by thin strands
        a = k * 2.1 + 0.4
        cx, cy = size / 2 + np.cos(a) * size * 0.18 + 1, size / 2 + np.sin(a) * size * 0.18 + 1
        f = size / 20.0
        lm = ellipse_mask(7 * f, 6 * f)
        lb = mask_sprite(lm, ramp('#2a0a48', '#4a1a78', '#6e34a8', '#9a62d0'), '#1a0630', soft=0.6, ambient=0.4, hl=False)
        paste(spr, lb, size / 2 + np.cos(a) * size * 0.18 + 1 - 3.5 * f - 1, size / 2 + np.sin(a) * size * 0.18 + 1 - 3 * f - 1)
    return spr


def platelet(seed=1):
    R = rs(seed)
    y, x = grid(5, 7)
    m = ellipse_mask(7, 5) | (((x - R.uniform(1, 6)) / 1.3) ** 2 + ((y - R.uniform(0.5, 4)) / 1.0) ** 2 <= 1)
    spr = mask_sprite(m, ramp('#5a3a6a', '#8a5aa0', '#b88ad0', '#e0c0f0'), '#24102e', soft=0.5, ambient=0.4, hl=False)
    for k in range(3):
        disc(spr, R.uniform(2.5, 5.5), R.uniform(2, 4), 0.35, '#5a2a78', 200)
    return spr


def atheroma(w=34, h=20, seed=2):
    """an atherosclerotic plaque bulging up from the floor: a fibrous white cap over a yellow fatty core, a few
    cholesterol crystals poking through"""
    R = rs(seed)
    y, x = grid(h, w)
    m = ((x - w / 2) / (w / 2)) ** 2 + ((y - h) / h) ** 2 <= 1
    spr = mask_sprite(m, ramp('#7a5a3a', '#b89a78', '#e0ccb4', '#f4ead8', '#ffffff'), '#2a1a0c', soft=1.6, hl_t=0.99)
    core = (((x - w / 2) / (w / 2 * 0.72)) ** 2 + ((y - h) / (h * 0.68)) ** 2 <= 1)
    noise = ndimage.gaussian_filter(R.uniform(size=core.shape).astype(np.float32), SC * 0.5)
    noise = (noise - noise.mean()) / max(noise.std(), 1e-6)
    cs = paint(smooth_mask(core), ramp('#a87a10', '#d8a820', '#f4d040', '#fff080'), np.clip(0.4 + 0.5 * (1 - y / h) + 0.08 * noise, 0, 1))
    I = inner(spr)
    over(I, cs[..., :3], cs[..., 3] / 255.0 * 0.92)
    for k in range(4):                                     # crystals: thin pale needles
        cx = R.uniform(w * 0.3, w * 0.7); a = R.uniform(-0.9, 0.9)
        pts = [(cx + 1 + np.sin(a) * t, h - 2 - h * 0.25 - np.cos(a) * t) for t in np.linspace(0, h * 0.7, 20)]
        stroke(spr, pts, 0.9, '#fffbe8', scale=1.0)
    return spr


def thrombus(w=26, h=40, seed=4):
    """a clot standing on the floor: a lumpy mass of red cells held in a mesh of pale fibrin strands"""
    R = rs(seed)
    y, x = grid(h, w)
    m = np.zeros(y.shape, bool)
    for k in range(9):                                     # a stack of lumps, narrower toward the top
        cy = h - 4 - k * (h - 8) / 8
        rr = (w / 2 - 1) * (0.95 - 0.4 * k / 8) * R.uniform(0.8, 1.0)
        cx = w / 2 + R.uniform(-2, 2)
        m |= ((x - cx) / rr) ** 2 + ((y - cy) / (rr * 0.95)) ** 2 <= 1
    m = ndimage.binary_closing(m, structure=np.ones((3, 3), bool), iterations=SC * 2)
    spr = mask_sprite(m, ramp('#3a0408', '#6a0a14', '#941828', '#b82c3c', '#d84a5a'), '#140204', soft=1.5, hl_t=0.99)
    grain(spr, seed, 0.07)
    for k in range(22):                                    # trapped red cells
        cx, cy = R.uniform(3, w - 3), R.uniform(3, h - 3)
        if all(m[min(max(px(cy + 0.5 + dy), 0), m.shape[0] - 1), min(max(px(cx + 0.5 + dx), 0), m.shape[1] - 1)] for dx in (-3.5, 3.5) for dy in (-2.5, 2.5)):
            paste(spr, rbc_small(R.uniform(0.5, 1.0)), cx - 3, cy - 2)
    for k in range(18):                                    # fibrin: fine, slightly wavy threads
        x0, y0 = R.uniform(0, w), R.uniform(0, h)
        a = R.uniform(0, np.pi); bend = R.uniform(-0.08, 0.08); L = R.uniform(4, 8)
        pts = [(x0 + np.cos(a + bend * t) * t + 1, y0 + np.sin(a + bend * t) * t + 1) for t in np.linspace(-L, L, 30)]
        pts = [(p, q) for p, q in pts if on(spr, p, q)]
        if len(pts) > 2:
            stroke(spr, pts, 0.5, '#f0dccc', 150, scale=1.0)
    return spr


def rbc_small(tilt=1.0):
    w, h = 7, max(3, int(round(7 * tilt)))
    m = ellipse_mask(w, h)
    sh, n = dome_shade(m, LIGHT, soft=0.6, ambient=0.35)
    yy, xx = grid(h, w)
    r = np.sqrt(((xx - (w - 1) / 2) / (w / 2)) ** 2 + ((yy - (h - 1) / 2) / (h / 2)) ** 2)
    sh = np.clip(sh - 0.4 * np.clip(1 - r / 0.5, 0, 1) ** 0.7, 0, 1)
    return outline(paint(m, ramp('#6a0610', '#b0141e', '#e0303a', '#ff7078'), sh), '#2a0206', width=0.55)


# ------------------------------------------------------------------ heart
def papillary(h=30, w=22):
    """a papillary muscle: a muscular cone rising from the floor, the cords leaving its tip"""
    y, x = grid(h, w)
    m = np.abs(x - w / 2 + 0.5) <= 1.5 + (w / 2 - 1.5) * np.clip(y / h, 0, None) ** 0.8
    spr = mask_sprite(m, ramp('#4a0a18', '#7a1628', '#a8263a', '#d0465a', '#f07a88'), '#16020a', soft=1.4)
    I = inner(spr)
    stri = np.clip(1 - np.abs(np.mod(x + y, 4.0) - 2.0) / 0.5, 0, 1) * m * (y > 3)
    I[..., :3] *= (1 - 0.15 * stri[..., None])
    return spr


def valve_leaflet(w=56, L=100):
    """a cusp of the mitral valve hanging from the top like a sail: wide where it is fixed to the ring, narrowing to
    a scalloped free edge; thin, pale, a little see-through, with fibres running down it. Returns the sprite and the
    points of its free edge where the cords attach"""
    spr = canvas(w + 2, L + 2)
    y, x = grid(L, w)
    t = np.clip(y / L, 0, None)
    half = w / 2 * (1.0 - 0.45 * t ** 1.3)
    lobe = 5 * (np.abs(np.sin((x - w / 2) / (w * 0.55) * np.pi * 1.5)))     # three scallops
    m = (np.abs(x - w / 2 + 0.5) <= half) & (y <= L - 7 - lobe)
    flap = mask_sprite(m, ramp('#9a7078', '#c49a9e', '#e4c2c0', '#f6dcd6', '#fff2ee'), '#3a1a1e', soft=2.4, hl_t=0.99)
    I = inner(flap)
    fib = np.clip(1 - np.abs(np.mod(x + y / 6.0 * 1.0, 5.0) - 2.5) / 0.35, 0, 1) * m * (y > 4)
    I[..., :3] *= (1 - 0.12 * fib[..., None])
    flap[..., 3] *= 0.95
    paste(spr, flap, 0, 0)
    pts = []
    for i in range(3, w - 2, 6):                       # the free edge, slightly thickened, and where cords leave it
        col = m[:, px(i + 0.5)]
        if col.any():
            e = (np.nonzero(col)[0].max() + 1) / SC
            ellipse_soft(spr, i + 1, e + 0.3, 1.2, 0.9, '#ecc8c0', 255)
            pts.append((i + 1, e))
    return spr, pts


# ------------------------------------------------------------------ brain
def pyramidal(dst, cx, cy, size, R, cols, glow=False):
    """a pyramidal neuron: a triangular body, one long apical dendrite going up with spines, basal dendrites
    spreading, the axon going down"""
    def path(x, y, a, L, wdt, lvl, spines=False):
        pts = [(x, y)]
        for i in range(int(L)):
            x += np.cos(a); y += np.sin(a); a += R.uniform(-0.12, 0.12)
            pts.append((x, y))
            if spines and i % 3 == 0:
                s = R.choice([-1, 1]); disc(dst, x + s * np.sin(a) * 1.4, y - s * np.cos(a) * 1.4, 0.45, cols[2])
            if lvl < 2 and R.uniform() < 0.05:
                path(x, y, a + R.choice([-1, 1]) * R.uniform(0.5, 1.0), L * 0.45, max(1, wdt - 1), lvl + 1, spines)
        stroke(dst, pts, wdt * (1.0 if lvl == 0 else 0.85), cols[1], scale=1.05)
        if glow and lvl >= 1:
            disc(dst, x, y, 0.7, cols[4]); disc(dst, x + 0.8, y, 0.5, cols[4], 150)
    path(cx, cy - size * 0.5, -np.pi / 2 + R.uniform(-0.15, 0.15), size * 5.5, 2, 0, spines=True)   # apical
    for k in range(3):
        path(cx, cy + size * 0.3, np.pi / 2 + R.uniform(-1.3, 1.3), size * 2.2, 1, 1)               # basal
    path(cx, cy + size * 0.5, np.pi / 2, size * 3.2, 1, 2)                                            # axon
    y, x = grid(size + 2, size)
    m = (y >= 0) & (np.abs(x - size / 2 + 0.5) <= (y + 1) * size / (2 * (size + 1)) + 0.6)
    sp = mask_sprite(m, ramp(cols[0], cols[1], cols[2], cols[3]), cols[5], soft=0.6, ambient=0.35)
    paste(dst, sp, cx - size / 2 - 1, cy - size / 2 - 2)
    disc(dst, cx - 0.2, cy + 0.3, size * 0.16, cols[0], 180)                                         # the nucleus


def astrocyte(dst, cx, cy, size, R, col, out):
    """a star-shaped glial cell: many fine processes, some ending on the capillary"""
    for k in range(10):
        a = k / 10 * 2 * np.pi + R.uniform(-0.2, 0.2)
        L = size * R.uniform(1.5, 2.6)
        pts = [(cx + np.cos(a) * t + 0.8 * np.sin(t * 0.5 + k), cy + np.sin(a) * t) for t in np.linspace(0, L, int(L * 3))]
        stroke(dst, pts, 1, col, scale=0.7)
        disc(dst, pts[-1][0], pts[-1][1], 0.45, col)
    m = ellipse_mask(size, size)
    sp = mask_sprite(m, ramp(out, col, '#e0d0ff', '#ffffff'), out, soft=0.5, ambient=0.4, hl=False)
    paste(dst, sp, cx - size / 2 - 1, cy - size / 2 - 1)


def amyloid(w=26, h=16, seed=6):
    """an amyloid plaque on the floor: a dense dark core with a halo of fibrils"""
    R = rs(seed)
    spr = canvas(w + 6, h + 4)
    for k in range(60):
        a = R.uniform(np.pi, 2 * np.pi); L = R.uniform(4, h * 0.95)
        pts = [(w / 2 + 3 + np.cos(a) * t * 1.3, h + 2 + np.sin(a) * t + 0.6 * np.sin(t * 0.9 + k)) for t in np.linspace(2, L, int(L * 3))]
        stroke(spr, pts, 0.8, '#d89a50' if k % 3 else '#f4c888', 230, scale=1.0)
    y, x = grid(int(h * 0.75), int(w * 0.6))
    hh, ww = int(h * 0.75), int(w * 0.6)
    m = ((x - ww / 2) / (ww / 2)) ** 2 + ((y - hh) / hh) ** 2 <= 1
    core = mask_sprite(m, ramp('#3a1a04', '#6a3408', '#9a5410', '#c87a28', '#e8a860'), '#1a0a02', soft=1.0)
    grain(core, seed, 0.1)
    paste(spr, core, w / 2 + 3 - ww / 2 - 1, h + 3 - hh - 1)
    return spr


def tangle(w=18, h=40, seed=8):
    """a neurofibrillary tangle: twisted flame-shaped bundles of fibres standing up"""
    R = rs(seed)
    spr = canvas(w + 4, h + 2)
    for k in range(11):
        ph = R.uniform(0, 6); amp = R.uniform(2, 5)
        pts = [(w / 2 + 2 + amp * np.sin(t * 0.22 + ph) * (t / h) + (k - 5) * 0.6 * (1 - t / h), h - t) for t in np.linspace(0, h * R.uniform(0.75, 1.0), 80)]
        stroke(spr, pts, 2.2, '#2a1004', scale=1.0)
        stroke(spr, pts, 1.1, '#c8742a' if k % 2 else '#e8a050', scale=1.0)
    return spr


def axon_cross(L=150, seed=2):
    """a myelinated axon crossing at head height: white sheath segments with the bare nodes between them"""
    spr = canvas(L, 9)
    x = 0
    R = rs(seed)
    stroke(spr, [(0, 3.5), (L - 1, 3.5)], 2.0, '#e8a050', scale=1.0)       # the axon itself shows at the nodes
    while x < L:
        seg = int(R.uniform(16, 22))
        yy, xx = grid(7, seg)
        m = ((xx - 3) ** 2 + (yy - 3) ** 2 <= 10) | ((xx - (seg - 4)) ** 2 + (yy - 3) ** 2 <= 10) | ((xx >= 3) & (xx <= seg - 4))
        s = mask_sprite(m, ramp('#8a8098', '#c0b8d0', '#e8e2f2', '#ffffff'), '#2a2238', soft=1.0, hl_t=0.97)
        paste(spr, s, x, 0)
        x += seg + 4
    return spr
