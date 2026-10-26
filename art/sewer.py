# Stage 2, the sewers: the inspection chamber (6), the sewer pipe (7), under a manhole (8), the brick trunk sewer
# (9), where the storm water comes in (10), the interceptor tunnel (11), the pumping station's wet well (12).
import numpy as np
from scipy import ndimage
from art import (H, SC, px, grid, canvas, ramp, ramp_col, hexc, paint, ellipse_mask, outline, paste, over, blur, disc,
                 ellipse_soft, inner, smooth_mask, fill_rect)
import anatomy as A
from tiles import WT, GY, FH, FY0, CH, TAU, wide, crop, put, per_sin, gradient, haze, pcells, wall, band_line, spots
from themes import three, drift, tower, stack, hang_len, bubble, flip_v
from variants import noise
import toilet as TT
import drains as D
from s2lib import (lerp_rgb, mul, wdx, pipe_curve, ring_joints, concrete_tex, water_line, streaks, mouth, silt, motes,
                   bubble_chain, pat_concrete, pat_soil, pat_pvc, pat_slime, pat_sludge, pat_iron, pat_brick, pat_gravel,
                   pebble_surface, surf_ceil, strands, lump, speckle, trim, blob_mask, mass)

RS = np.random.RandomState
CONC = ramp('#3a3c38', '#5a5c56', '#7c7e76', '#9c9e94', '#b8b8ac', n=5)
SOIL = ramp('#241c14', '#3a2e22', '#54442e', '#6e5c40', '#8a7656', n=5)
SILT = ramp('#3a3426', '#5a5038', '#7a6e50', '#968a68', n=4)


def beams(far, xs, seed, w=(10, 22), k=0.22, y0=0, y1=H, slant=0.06):
    """bright beams of daylight down through the water from openings above (at xs), soft and slanting a little"""
    R = RS(seed)
    y, x = grid(H, WT)
    acc = np.zeros(y.shape, np.float32)
    for x0 in xs:
        ww = R.uniform(*w)
        d = wdx(x, x0 + (y - y0) * slant)
        acc += np.exp(-(d / ww) ** 2) * np.clip((y - y0) / 6, 0, 1) * np.clip(1 - (y - y0) / (y1 - y0), 0, 1) ** 0.8
    lerp_rgb(far, '#fffbe8', np.clip(acc, 0, 1) * k)


def put_wrap(c3, spr, x, y):
    for off in (0, WT, 2 * WT):
        paste(c3, spr, x + off, y)


# ================================================================== 6. the inspection chamber (오수받이)
WATER_CH = '#6e8478'
ROOT = ramp('#5a4228', '#8a6a44', '#b4946a', '#d6bc92', '#efdcb8')
ROOT_OUT = '#2a1c0e'


def chamber_far(seed=901):
    R = RS(seed)
    far = gradient(H, ['#a8b4a4', '#8c9a8a', '#6e7e70', '#4e5c52'])
    concrete_tex(far, seed + 1, k=1.0, cols=('#2a302a', '#d8dccc'))
    y, x = grid(H, WT)
    for j in range(4):                                    # the chamber's precast rings, one on another
        lerp_rgb(far, '#1e2620', np.exp(-((y - (18 + j * 40)) / 0.7) ** 2) * 0.5)
        lerp_rgb(far, '#e8ecdc', np.exp(-((y - (19.4 + j * 40)) / 0.6) ** 2) * 0.25)
    water_line(far, 26, '#4a5a3a', k=0.35, h=12, seed=seed + 2)
    c3 = three(far)
    pipes = []
    for k in range(5):                                    # the pipes coming in: from the houses, high and low
        cx = (k + 0.5) * WT / 5 + R.uniform(-40, 40); cy = R.uniform(48, 104); mw = R.uniform(20, 32)
        pipes.append((cx, cy, mw))
        m_ = mouth(mw, mw * 0.85, ramp('#3e4440', '#7e8680', '#c4ccc2', n=3))
        put_wrap(c3, m_, cx - m_.shape[1] / SC / 2, cy - m_.shape[0] / SC / 2)
    for k in range(40):                                   # fine roots come in at the joints
        jx = R.uniform(0, WT); jy = 18 + R.randint(0, 3) * 40
        g = canvas(30, 26)
        strands(g, 5, seed + 10 + k, 13, 17, 1, 24, ['#c8ae84', '#a88a60', '#e0caa0'], w=(0.18, 0.32), curl=3.0, a=150, dx=R.uniform(-6, 6))
        put_wrap(c3, g, jx - 15, jy)
    far = crop(c3)
    for (cx, cy, mw) in pipes:
        D.falling_water(far, cx, cy + mw * 0.2, mw * 0.4, GY - 4, seed + int(cx), k=0.45)
    beams(far, [WT * 0.12, WT * 0.45, WT * 0.78], seed + 3, w=(8, 14), k=0.22)
    c3 = three(far)
    drift(c3, 90, ['#d8dcc8', '#ffffff', '#b8bca4'], seed + 4, y0=20, y1=GY - 6, a=130)
    far = crop(c3)
    haze(far, WATER_CH, 0.2)
    return far


def lid_ceil(seed=951, crown=None, slots=True, period=WT / 3):
    """a chamber's cover from below: dark cast iron with slots, the daylight through them"""
    def extra(c3, R, rim_b, surf):
        if not slots:
            return
        for j in range(int(round(WT / period))):
            cx = j * period + period * 0.4
            for i in range(-3, 4):
                sx = cx + i * 5.5
                for off in (0, WT, 2 * WT):
                    fill_rect(c3, sx + off - 1.2, 1.5, sx + off + 1.2, 5.0, '#fffbe0', 255)
                    fill_rect(c3, sx + off - 0.6, 1.8, sx + off + 0.6, 4.6, '#ffffff', 255)
    return surf_ceil(seed, crown or ramp('#1a1c1c', '#2e3232', '#464c4a', '#626a66', n=4), crown_h=7.0,
                     air=('#3a4440', '#56625c', '#76847c'), mirror='#e4ece2', out='#1e2a24', extra=extra)


def root_line(dst, pts, w0, seed, depth=0):
    """one root along pts, tapering from w0, with forks off it (recursive)"""
    R = RS(seed)
    n = len(pts)
    for i in range(n - 1):
        w = max(0.25, w0 * (1 - i / n * 0.75))
        A.stroke(dst, [pts[i], pts[i + 1]], w + 0.55, ROOT_OUT, 255, scale=1.0)
    for i in range(n - 1):
        w = max(0.2, w0 * (1 - i / n * 0.75))
        A.stroke(dst, [pts[i], pts[i + 1]], w, ['#c8aa7c', '#b4946a', '#d8c096'][(i // 6) % 3], 255, scale=1.0)
        if w > 0.7:
            A.stroke(dst, [(pts[i][0] - w * 0.25, pts[i][1]), (pts[i + 1][0] - w * 0.25, pts[i + 1][1])], w * 0.3, '#ecdcb8', 200, scale=1.0)
    if depth < 2:
        for k in range(R.randint(1, 3)):
            j = R.randint(n // 4, n - 4); bx, by = pts[j]
            side = R.choice([-1, 1]); l = R.uniform(0.3, 0.6) * (abs(pts[-1][1] - pts[0][1]) + 1)
            up = -1 if pts[-1][1] < pts[0][1] else 1
            sub = [(bx + side * l * 0.45 * t + 1.2 * np.sin(t * 4 + k), by + up * l * t) for t in np.linspace(0, 1, 18)]
            root_line(dst, sub, max(0.4, w0 * (1 - j / n * 0.75) * 0.65), seed * 7 + k + 1, depth + 1)


def root_mass(seed=1, wdt=16):
    """tree roots grown in through a joint, hanging in the water: pale, wavy, forking, thinner as they go"""
    L = hang_len()
    R = RS(seed)
    W = wdt + 22
    out = canvas(W, L)
    for k in range(5):
        x0 = W / 2 + R.uniform(-wdt / 3, wdt / 3); ph = R.uniform(0, 6); l = R.uniform(0.7, 1.0) * (L - 2)
        pts = [(x0 + 3.0 * np.sin(t * 3.0 + ph) * t + (k - 2) * 2.5 * t, t * l) for t in np.linspace(0, 1, 40)]
        root_line(out, pts, R.uniform(2.6, 3.4), seed * 10 + k)
    g = lump(wdt * 0.9, 6, seed + 9, ROOT, ROOT_OUT, bumps=4, soft=1.0)             # where they come in: a knot at the top
    paste(out, flip_v(g), W / 2 - g.shape[1] / SC / 2, -1.5)
    return trim(out)[:px(L)]


def root_column(h, seed=3, w=22):
    """roots grown up through a crack in the floor into a tangle: forking, wavy, pale"""
    R = RS(seed)
    h = int(round(h))
    out = canvas(w + 10, h)
    for k in range(5 + int(h / 25)):
        x0 = (w + 10) / 2 + R.uniform(-3, 3); ph = R.uniform(0, 6); l = R.uniform(0.6, 1.0) * (h - 2)
        spread = R.uniform(-1, 1) * w * 0.35
        pts = [(x0 + spread * t ** 1.3 + 2.0 * np.sin(t * 3.5 + ph), h - 1.0 - t * l) for t in np.linspace(0, 1, 40)]
        root_line(out, pts, R.uniform(2.6, 3.4), seed * 10 + k)
    base = lump(w * 0.6, 5, seed + 4, ROOT, ROOT_OUT, bumps=3, soft=1.0)
    paste(out, base, (w + 10) / 2 - base.shape[1] / SC / 2, h - base.shape[0] / SC)
    return trim(out)


def pet_bottle(L=24, d=9, seed=1, upright=False):
    """a clear plastic drink bottle: its cap, the shoulders, a label round it, ribs at the bottom"""
    R = RS(seed)
    y, x = grid(d, L)
    t = x / L
    neck = 0.32 + 0.68 * np.clip((t - 0.12) / 0.18, 0, 1) ** 0.7
    half = (d / 2 - 0.6) * np.where(t < 0.12, 0.3, neck)
    m = (np.abs(y - d / 2) <= half) & (x > 0.6) & (x < L - 0.6)
    cap = (t < 0.1) & (np.abs(y - d / 2) <= d * 0.2)
    m |= cap
    u = (y - d / 2) / (d / 2)
    sh = np.clip(0.6 - 0.45 * u - 0.2 * u ** 4, 0, 1)
    spr = np.zeros(y.shape + (4,), np.float32)
    body = ramp_col(ramp('#3a7a88', '#7ab8c4', '#c4e8ee', '#f2feff'), sh)
    spr[..., :3] = body
    a = smooth_mask(m) * (0.55 + 0.35 * np.abs(u) ** 2)
    lab = (t > 0.42) & (t < 0.72) & m
    labc = np.where((np.mod(x, 3.0) < 1.5)[..., None], hexc('#d83a3a'), hexc('#f2f2f2'))
    labc = labc * (0.75 + 0.3 * (1 - np.abs(u)))[..., None]
    spr[..., :3] = np.where(lab[..., None], labc, spr[..., :3])
    a = np.where(lab, smooth_mask(m), a)
    capc = ramp_col(ramp('#0a4a1a', '#1a8a3a', '#4ac46a'), sh)
    spr[..., :3] = np.where(cap[..., None], capc, spr[..., :3]); a = np.where(cap, smooth_mask(m), a)
    rib = (t > 0.8) & m & (np.mod(x, 1.6) < 0.5)
    spr[..., :3] = np.where(rib[..., None], spr[..., :3] * 0.85, spr[..., :3])
    spr[..., 3] = a * 255
    gl = (np.abs(u + 0.45) < 0.12) & m & ~lab
    spr[..., :3] = np.where(gl[..., None], 255, spr[..., :3]); spr[..., 3] = np.where(gl, 235, spr[..., 3])
    spr = outline(spr, '#123a44', alpha_cut=0.3, width=0.6)
    if upright:
        spr = np.ascontiguousarray(np.rot90(spr, 1))
    return spr


def soju_bottle(seed=1):
    """a green glass bottle standing (the usual one), its label, a twist cap"""
    h, w = 34, 11
    y, x = grid(h, w)
    t = y / h
    shoulder = np.clip((t - 0.18) / 0.16, 0, 1)
    half = np.where(t < 0.12, 1.6, 1.6 + (w / 2 - 0.8 - 1.6) * (shoulder ** 0.8))
    m = (np.abs(x - w / 2) <= half) & (y > 0.6) & (y < h - 0.6)
    u = (x - w / 2) / (w / 2)
    sh = np.clip(0.55 - 0.45 * u - 0.2 * u ** 4, 0, 1)
    spr = np.zeros(y.shape + (4,), np.float32)
    spr[..., :3] = ramp_col(ramp('#0e4a2a', '#1e7a46', '#46b070', '#9ce4b4', '#e6fff0'), sh)
    spr[..., 3] = smooth_mask(m) * (210 + 40 * np.abs(u))
    lab = (t > 0.48) & (t < 0.78) & m
    spr[..., :3] = np.where(lab[..., None], ramp_col(ramp('#3a7a9a', '#7ab8d8', '#e8f4fa'), sh * 0.8 + 0.2), spr[..., :3])
    spr[..., 3] = np.where(lab, 255, spr[..., 3])
    cap = (t < 0.1) & m
    spr[..., :3] = np.where(cap[..., None], ramp_col(ramp('#6a6a6a', '#b4b4b4', '#f0f0f0'), sh), spr[..., :3])
    gl = (np.abs(u + 0.5) < 0.1) & m & ~lab & (t > 0.2)
    spr[..., :3] = np.where(gl[..., None], 255, spr[..., :3])
    return outline(spr, '#08261a', width=0.6)


def silt_heap(w=26, h=10, seed=1, rmp=SILT, out='#1e1a10'):
    spr = mass(w, h, seed, rmp, out, n=4, ambient=0.35, hl_t=0.995, grain_k=0.12)
    return speckle(spr, seed + 1, int(w * h * 0.25), ['#2a2418', '#b4a888', '#4a4030'], r=(0.2, 0.45), a=170)


def T_chamber():
    far = chamber_far()
    R = RS(911)
    mid = wide()
    motes(mid, 140, ['#d8dcc8', '#9aa48a', '#ffffff'], 912, r=(0.3, 0.9), a=(110, 200))
    for k in range(6):
        put(mid, TT.paper_shred(920 + k, R.uniform(6, 10), R.uniform(4, 6)), R.uniform(0, WT), R.uniform(26, GY - 30), 0.8)
    bubble_chain(mid, 6, 930, r=(1, 2), alpha=0.5)
    mid = crop(mid)
    floor = wall([(1.2, ramp('#3a4430', '#5a6448', '#7a8460', n=3), pat_slime), (9, CONC, pat_concrete), (40, SOIL, pat_soil)], True, seed=941, bumps=0.6, out='#141a14')
    ceil = lid_ceil()
    obs = {'low': [silt_heap(26, 10, 1), pet_bottle(24, 9, 2)],
           'tall': [soju_bottle(1), root_column(44, 5, 22)],
           'hang': [root_mass(1, 16), root_mass(2, 13)],
           'float': [pet_bottle(22, 8, 4), TT.paper_wad(41, 15, 11)],
           'huge': [tower(lambda h: root_column(h, 7, 24))]}
    return dict(far=far, mid=mid, floor=floor, ceil=ceil, obs=obs, coin='drop', special='soap')


# ================================================================== 7. the sewer pipe (concrete)
WATER_SEW = '#5e7068'


def sewer_far(seed=1001):
    R = RS(seed)
    far = gradient(H, ['#9aa29a', '#7e8880', '#626e66', '#46524c'])
    concrete_tex(far, seed + 1, k=1.0, cols=('#20261f', '#c8ccbc'))
    pipe_curve(far, 0, GY + 14, 0.3, lit=0.38)
    ring_joints(far, 4, seed + 2, col='#0e1410', w=8.0, k=0.6, collar=(10, '#8a9288'))
    water_line(far, 22, '#3e4a2e', k=0.6, h=14, seed=seed + 3)            # slime along the usual water level
    streaks(far, 40, seed + 4, '#e8eadc', k=0.32, y0=10, y1=90, ang=np.pi / 2, L=(10, 40), w=(0.4, 1.0))   # lime weeping from the joints
    streaks(far, 50, seed + 5, '#2a3424', k=0.25, y0=60, y1=GY, L=(60, 200), w=(0.8, 2.4))
    silt(far, 134, ('#2a2618', '#4a4430', '#6a6248', '#847a5c'), seed + 6, k=0.9)
    c3 = three(far)
    drift(c3, 120, ['#c8ccb8', '#9aa088', '#e8eadc'], seed + 7, y0=20, y1=GY - 6, a=140)
    far = crop(c3)
    haze(far, WATER_SEW, 0.22)
    return far


def sewer_ceil(seed=1051):
    def extra(c3, R, rim_b, surf):
        for k in range(160):                               # straws of lime hanging off the crown above the water
            x = R.uniform(0, WT); L = R.uniform(1.0, 4.5)
            for off in (0, WT, 2 * WT):
                A.stroke(c3, [(x + off, 6.5), (x + off + 0.1, 6.5 + L)], 0.5, '#e8e8dc', 230, scale=1.0)
                ellipse_soft(c3, x + off + 0.1, 6.6 + L, 0.35, 0.45, '#ffffff', 220)
    return surf_ceil(seed, ramp('#3e423c', '#5e625a', '#80847a', '#a0a496', n=4), crown_h=6.8,
                     air=('#2e3632', '#4a5650', '#6a7a72'), mirror='#dfe8e0', out='#1a2420', extra=extra)


def rat(w=30, h=13, seed=1, swim=False):
    """a brown rat (side view, no face but an eye): a plump body, pink ears, feet, a long bare tail"""
    R = RS(seed)
    W, Hh = w + 18, h + 4
    out = canvas(W, Hh)
    y, x = grid(h, w)
    body = ((x - w * 0.55) / (w * 0.45)) ** 2 + ((y - h * 0.58) / (h * 0.42)) ** 2 <= 1
    snout = ((x - w * 0.14) / (w * 0.16)) ** 2 + ((y - h * 0.6) / (h * 0.26)) ** 2 <= 1
    neck = ((x - w * 0.28) / (w * 0.16)) ** 2 + ((y - h * 0.55) / (h * 0.36)) ** 2 <= 1
    m = (body | snout | neck) & (y < h - 0.6)
    spr = A.mask_sprite(m, ramp('#2a1e16', '#4a3a2c', '#6e5a46', '#94806a', '#b8a48c'), '#140e0a', soft=1.6, ambient=0.3, hl_t=0.985)
    I = inner(spr)
    keep = I[..., 3].copy()
    for k in range(int(w * h * 0.6)):                     # fur: short strokes along the body
        fx, fy = R.uniform(w * 0.2, w), R.uniform(h * 0.2, h * 0.95)
        A.stroke(I, [(fx, fy), (fx + 1.0, fy + R.uniform(-0.3, 0.3))], 0.22, ['#3a2c20', '#8a7660', '#5a4836'][k % 3], 110, scale=1.0)
    I[..., 3] = keep
    ellipse_soft(I, w * 0.08, h * 0.62, 0.7, 0.6, '#e8a0a0', 255)            # its nose
    ellipse_soft(I, w * 0.2, h * 0.48, 0.75, 0.75, '#0a0606', 255)              # the eye
    ellipse_soft(I, w * 0.19, h * 0.45, 0.25, 0.25, '#ffffff', 220)
    for k in range(4):                                     # whiskers
        A.stroke(out, [(4 + w * 0.08, 2 + h * 0.62), (4 - 3, 2 + h * 0.62 + (k - 1.5) * 1.2)], 0.12, '#d8d0c8', 200, scale=1.0)
    tail = [(4 + w * 0.98 + 14 * t, 2 + h * 0.66 + 3 * np.sin(t * 3.2 + seed) * t) for t in np.linspace(0, 1, 30)]
    A.stroke(out, tail, 1.0, '#3a2020', 255, scale=1.0)
    A.stroke(out, tail, 0.6, '#d89090', 255, scale=1.0)
    ear = ellipse_mask(int(w * 0.16) + 1, int(h * 0.36) + 1)
    e = A.mask_sprite(ear, ramp('#8a4a4a', '#c87878', '#eab0b0'), '#3a1a1a', soft=0.7, ambient=0.4)
    feet = canvas(W, Hh)
    for fx in (0.3, 0.45, 0.72, 0.86):                    # feet (paddling when it swims)
        lx = 4 + w * fx; ly = 2 + h * 0.85
        dy = 1.8 if not swim else 1.2
        dx = -1.2 if swim and fx > 0.6 else 0.4
        A.stroke(feet, [(lx, ly), (lx + dx, ly + dy)], 0.9, '#2a1a14', 255, scale=1.0)
        A.stroke(feet, [(lx, ly), (lx + dx, ly + dy)], 0.55, '#d8a0a0', 255, scale=1.0)
    paste(out, feet, 0, 0)
    paste(out, spr, 3, 1)
    paste(out, e, 4 + w * 0.24, 1.5)
    return trim(out)


def concrete_chunk(w=24, h=12, seed=1):
    """a broken piece of concrete pipe: angular, the aggregate showing on the broken faces, a bit of rebar sticking out"""
    R = RS(seed)
    y, x = grid(h, w)
    n = 7
    ang = np.arctan2(y - h, x - w / 2)
    rr = np.sqrt(((x - w / 2) / (w / 2 - 1)) ** 2 + ((y - h) / (h - 1)) ** 2)
    k = (ang + np.pi) / np.pi * n
    rad = R.uniform(0.75, 1.0, n + 2)
    i0 = np.clip(np.floor(k).astype(int), 0, n); f = k - np.floor(k)
    lim = rad[i0] * (1 - f) + rad[i0 + 1] * f
    m = (rr <= lim) & (y <= h - 0.6)
    spr = A.mask_sprite(m, CONC, '#14160f', soft=0.9, ambient=0.35, hl_t=0.99)
    speckle(spr, seed + 1, int(w * h * 0.5), ['#c8c4b0', '#5a5a50', '#a49c86'], r=(0.3, 0.8), a=200)
    I = inner(spr)
    rx = w * R.uniform(0.3, 0.7)
    A.stroke(I, [(rx, h * 0.4), (rx + 3, h * 0.4 - 6)], 0.9, '#3a1e0e', 255, scale=1.0)
    A.stroke(I, [(rx, h * 0.4), (rx + 3, h * 0.4 - 6)], 0.5, '#9a5228', 255, scale=1.0)
    return spr


def slime_strands(seed=1, wdt=12):
    """biofilm hanging off the crown in the flow: long slimy grey-green streamers ('sewer snot'), drops at the ends"""
    L = hang_len()
    R = RS(seed)
    W = wdt + 10
    out = canvas(W, L)
    for k in range(6):
        x0 = W / 2 + R.uniform(-wdt / 2.5, wdt / 2.5); l = R.uniform(0.55, 1.0) * L; ph = R.uniform(0, 6)
        y, x = grid(L, W)
        cx = x0 + 1.6 * np.sin(y * 0.05 + ph) * (y / L) + 0.4 * np.sin(y * 0.3 + ph)
        half = (1.6 - 1.0 * np.clip(y / l, 0, 1)) * R.uniform(0.8, 1.2) + 0.3 * np.sin(y * 0.4 + k)
        m = (np.abs(x - cx) <= half) & (y <= l)
        drop = ((x - x0 - 1.6 * np.sin(l * 0.05 + ph) * (l / L)) ** 2 + ((y - l) / 1.3) ** 2) <= 1.4 ** 2
        m |= drop
        s = A.mask_sprite(m, ramp('#2e3a26', '#4e5e3c', '#74845a', '#a0ae84', '#d4dcbc'), '#121a0c', soft=0.8, ambient=0.35, hl_t=0.93)
        I = inner(s); I[..., 3] *= 0.92
        paste(out, s, -1, -1)
    return trim(out)[:px(L)]


def debris_pile(h, seed=5, w=24):
    """what the flow left in a heap: broken concrete, a brick, sticks, rags, held together by silt"""
    R = RS(seed)
    h = int(round(h))
    spr = mass(w, h, seed, SILT, '#1e1a10', taper=0.5, wob=0.12, ambient=0.35, hl_t=0.995, grain_k=0.12)
    I = inner(spr); keep = I[..., 3].copy()
    for k in range(int(h / 6)):
        yy = R.uniform(1, h - 5); kind = k % 3
        if kind == 0:
            g = concrete_chunk(R.uniform(8, 12), R.uniform(5, 7), seed + 20 + k)
        elif kind == 1:
            g = canvas(12, 3); A.stroke(g, [(0.5, 1.5), (11, 1.2 + R.uniform(-0.5, 0.5))], 1.4, '#3a2410', 255, scale=1.0); A.stroke(g, [(0.5, 1.5), (11, 1.4)], 0.9, '#8a6038', 255, scale=1.0)
        else:
            g = TT.paper_shred(seed + 40 + k, R.uniform(6, 9), R.uniform(3.5, 5))
            g[..., :3] = g[..., :3] * 0.7 + hexc('#8a8060') * 0.3
        paste(I, g, w / 2 - g.shape[1] / SC / 2 + R.uniform(-w * 0.25, w * 0.25), yy)
    I[..., 3] = keep
    return spr


def T_sewer():
    far = sewer_far()
    R = RS(1011)
    mid = wide()
    motes(mid, 160, ['#b8bca8', '#7a8270', '#e0e2d4', '#4a5242'], 1012, r=(0.3, 1.0), a=(110, 200))
    for k in range(5):
        put(mid, TT.paper_shred(1020 + k, R.uniform(6, 10), R.uniform(4, 6)), R.uniform(0, WT), R.uniform(26, GY - 30), 0.75)
    bubble_chain(mid, 5, 1030, r=(1, 2), alpha=0.5)
    mid = crop(mid)
    floor = wall([(2.6, SILT, pat_sludge), (8, CONC, pat_concrete), (40, SOIL, pat_soil)], True, seed=1041, bumps=0.8, out='#12160f')
    ceil = sewer_ceil()
    obs = {'low': [concrete_chunk(24, 12, 1), rat(30, 13, 2), silt_heap(28, 9, 3)],
           'tall': [debris_pile(42, 5, 23), debris_pile(48, 15, 25)],
           'hang': [slime_strands(1, 12), slime_strands(2, 10)],
           'float': [rat(28, 12, 4, swim=True), TT.paper_wad(51, 15, 11)],
           'huge': [tower(lambda h: debris_pile(h, 25, 25))]}
    return dict(far=far, mid=mid, floor=floor, ceil=ceil, obs=obs, coin='drop', special='soap')


# ================================================================== 8. under a manhole
WATER_MH = '#6e8a86'
LEAF_G = ramp('#7a5a0a', '#b8900e', '#e6c22a', '#f8e46a', '#fff4b0')      # ginkgo
LEAF_M = ramp('#5a0e08', '#8e2010', '#c43c1a', '#e8662e', '#ffa060')       # maple


def manhole_far(seed=1101):
    R = RS(seed)
    far = gradient(H, ['#9ab0aa', '#7e9690', '#627a76', '#465c5a'])
    y, x = grid(H, WT)
    concrete_tex(far, seed + 1, k=0.8, cols=('#22302c', '#d4dcd4'))
    per = WT / 2
    for j in range(2):                                    # the shaft: brick courses round where it goes up, rungs up its wall
        x0 = j * per + per * 0.4
        d = wdx(x, x0)
        sh = np.clip(1 - np.abs(d) / 60, 0, 1)
        row = np.floor(y / 5.0)
        xs = x + np.mod(row, 2) * 6
        mort = np.maximum(band_line(y, 5.0, 0.5, 0.0), band_line(xs, 12.0, 0.45, 0.0))
        brick = ramp_col(ramp('#5a2e22', '#7e4632', '#a0624a', '#bc8466'), np.clip(0.6 + 0.2 * np.sin(row * 12.9 + np.floor(xs / 12) * 78.2) ** 2 - 0.2 * (y / H), 0, 1))
        brick = brick * (1 - 0.45 * mort[..., None]) + hexc('#8a8a7e') * 0.45 * mort[..., None]
        far[..., :3] = far[..., :3] * (1 - sh[..., None]) + brick * sh[..., None]
    for j in range(2):
        x0 = j * per + per * 0.4
        lerp_rgb(far, '#000000', np.exp(-((wdx(x, x0) - 58) / 3) ** 2) * 0.3 + np.exp(-((wdx(x, x0) + 58) / 3) ** 2) * 0.3)
    c3 = three(far)
    for j in range(2):                                    # step irons: U-shaped rungs, rusty
        x0 = j * per + per * 0.4
        for i in range(6):
            ry = 18 + i * 22
            g = canvas(22, 7)
            A.stroke(g, [(2, 1), (2, 5), (20, 5), (20, 1)], 1.6, '#1a0e08', 255, scale=1.0)
            A.stroke(g, [(2, 1), (2, 5), (20, 5), (20, 1)], 1.0, ['#8a4a26', '#a85a2e'][i % 2], 255, scale=1.0)
            A.stroke(g, [(3, 4.6), (19, 4.6)], 0.35, '#e8a070', 200, scale=1.0)
            put_wrap(c3, g, x0 - 11, ry)
    far = crop(c3)
    beams(far, [per * 0.4, per * 1.4], seed + 2, w=(22, 30), k=0.55, slant=0.05)
    TT.caustics(far, seed + 3, k=0.35)
    streaks(far, 40, seed + 4, '#3a3a22', k=0.25, y0=0, y1=H, ang=np.pi / 2, L=(30, 100), w=(0.8, 2.0))
    c3 = three(far)
    drift(c3, 140, ['#fffbe0', '#ffffff', '#e8e4c8'], seed + 5, y0=10, y1=GY - 6, a=170)
    far = crop(c3)
    haze(far, WATER_MH, 0.15)
    return far


def manhole_ceil(seed=1151):
    """the road above: its slab in section, and the manhole: an iron frame, the cover's holes letting daylight in"""
    def extra(c3, R, rim_b, surf):
        for j in range(2):
            cx = j * WT / 2 + WT / 2 * 0.4
            for off in (0, WT, 2 * WT):
                fill_rect(c3, cx + off - 34, 0, cx + off + 34, 6.4, '#26262a', 255)        # the cast iron frame
                fill_rect(c3, cx + off - 32, 0, cx + off + 32, 1.2, '#4a4a50', 255)
                for i in range(-4, 5):                                                    # the cover's holes
                    disc(c3, cx + off + i * 7, 3.4, 1.5, '#fffde8', 255)
                    disc(c3, cx + off + i * 7, 3.4, 0.8, '#ffffff', 255)
    return surf_ceil(seed, ramp('#2e2e2a', '#4e4e48', '#6e6e66', '#8e8e84', n=4), crown_h=6.6,
                     air=('#40504c', '#62746e', '#90a49c'), mirror='#eef6ee', out='#1c2622', extra=extra)


def leaf(kind='g', s=12, seed=1):
    """a fallen leaf, wet: a ginkgo fan (kind g) or a maple star (kind m), its veins"""
    R = RS(seed)
    y, x = grid(s, s)
    cx, cy = s / 2, s * 0.62
    ang = np.arctan2(-(y - cy), x - cx)
    r = np.sqrt((x - cx) ** 2 + (y - cy) ** 2)
    if kind == 'g':
        ok = (ang > 0.25) & (ang < np.pi - 0.25)
        notch = np.abs(ang - np.pi / 2) < 0.08
        m = ok & (r < s * 0.5 * (0.92 + 0.06 * np.sin(ang * 18))) & ~(notch & (r > s * 0.28))
        m |= (np.abs(x - cx) < 0.4) & (y > cy) & (y < s - 0.6)
        rmp = LEAF_G
    else:
        lobes = np.abs(np.cos(ang * 2.5 - 0.4)) ** 0.6
        m = r < s * 0.5 * (0.45 + 0.55 * lobes) * (0.94 + 0.06 * np.sin(ang * 24))
        m |= (np.abs(x - cx) < 0.35) & (y > cy) & (y < s - 0.6)
        rmp = LEAF_M
    spr = A.mask_sprite(m, rmp, '#2a1a06', soft=0.8, ambient=0.4, hl_t=0.97)
    I = inner(spr)
    for a in (np.linspace(0.4, np.pi - 0.4, 7) if kind == 'g' else [np.pi / 2, np.pi / 2 + 1.2, np.pi / 2 - 1.2, np.pi / 2 + 2.3, np.pi / 2 - 2.3]):
        A.stroke(I, [(cx, cy), (cx + np.cos(a) * s * 0.42, cy - np.sin(a) * s * 0.42)], 0.18, '#5a3a08' if kind == 'g' else '#5a1008', 140, scale=1.0)
    return spr


def leaf_pile(w=26, h=9, seed=1):
    R = RS(seed)
    out = canvas(w + 6, h + 6)
    for k in range(int(w * h / 10)):
        l = leaf('g' if k % 3 else 'm', R.uniform(7, 11), seed + k)
        l = ndimage.rotate(l, R.uniform(-60, 60), reshape=True, order=1)
        paste(out, l, R.uniform(0, w - 4), h + 6 - l.shape[0] / SC - R.uniform(0, h * 0.6) * (1 - abs(k % 7 - 3) / 3.5))
    return trim(out)


def can(w=14, h=9, seed=1):
    """a crushed drink can lying on its side: aluminium, a red band, dented"""
    R = RS(seed)
    y, x = grid(h, w)
    dent = 0.8 * np.sin(x * 0.9 + seed) * np.exp(-((x - w * 0.55) / 3) ** 2)
    m = (np.abs(y - h / 2) <= h / 2 - 0.7 - np.abs(dent) - 0.6 * (x < 1.5) - 0.6 * (x > w - 1.5)) & (x > 0.6) & (x < w - 0.6)
    u = (y - h / 2) / (h / 2)
    sh = np.clip(0.6 - 0.45 * u + 0.25 * dent, 0, 1)
    band = (x > w * 0.25) & (x < w * 0.8)
    rgb = np.where(band[..., None], ramp_col(ramp('#5a0a0a', '#a81818', '#e03a2e', '#ff8a7a'), sh), ramp_col(ramp('#5a5e62', '#9aa0a6', '#d4d8dc', '#ffffff'), sh))
    spr = np.zeros(y.shape + (4,), np.float32); spr[..., :3] = rgb; spr[..., 3] = smooth_mask(m) * 255
    return outline(spr, '#1a1a1e', width=0.6)


def ladder_hang(seed=1, wdt=14):
    """a steel ladder hung down into the water from the manhole: two rails, rungs, rust where the water reaches"""
    L = hang_len()
    out = canvas(wdt + 4, L)
    for xr in (2, wdt + 2):
        A.stroke(out, [(xr, 0), (xr, L - 2)], 1.9, '#14100c', 255, scale=1.0)
        A.stroke(out, [(xr, 0), (xr, L - 2)], 1.2, '#8a8e92', 255, scale=1.0)
        A.stroke(out, [(xr - 0.3, 0), (xr - 0.3, L - 2)], 0.35, '#dfe4e8', 220, scale=1.0)
    for i in range(int((L - 6) / 9) + 1):
        ry = 5 + i * 9
        A.stroke(out, [(2, ry), (wdt + 2, ry)], 1.6, '#14100c', 255, scale=1.0)
        A.stroke(out, [(2, ry), (wdt + 2, ry)], 1.0, '#9a9ea2', 255, scale=1.0)
        A.stroke(out, [(2.5, ry - 0.3), (wdt + 1.5, ry - 0.3)], 0.3, '#e8eef2', 200, scale=1.0)
    y, x = grid(L, wdt + 4)
    rust = np.clip((y - 20) / L, 0, 1) * (0.5 + 0.5 * noise(y.shape, 0.8, seed)) * (out[..., 3] > 0)
    lerp_rgb(out, '#8a4220', rust * 0.6)
    return out


def cone(h=40, seed=1, w=None):
    """a traffic cone (it fell in): orange, two white reflective bands, a square black base"""
    w = w or h * 0.55
    y, x = grid(h, w)
    t = np.clip(y / (h - 3), 0, 1)
    half = 1.2 + (w / 2 - 3.0) * t
    body = (np.abs(x - w / 2) <= half) & (y < h - 3) & (y > 0.6)
    base = (y >= h - 3.5) & (y < h - 0.6) & (np.abs(x - w / 2) <= w / 2 - 0.6)
    u = (x - w / 2) / np.maximum(half, 1)
    sh = np.clip(0.62 - 0.42 * u - 0.2 * u ** 4, 0, 1)
    band = ((t > 0.3) & (t < 0.42)) | ((t > 0.6) & (t < 0.72))
    rgb = np.where(band[..., None], ramp_col(ramp('#8a9094', '#d0d6da', '#ffffff'), sh), ramp_col(ramp('#7a2400', '#d04800', '#ff7a1a', '#ffb066'), sh))
    rgb = np.where(base[..., None], ramp_col(ramp('#0a0a0a', '#222224', '#3e3e42'), sh * 0.5 + 0.3), rgb)
    spr = np.zeros(y.shape + (4,), np.float32); spr[..., :3] = rgb; spr[..., 3] = smooth_mask(body | base) * 255
    lerp_rgb(spr, '#3a3020', np.clip((y - h * 0.5) / h, 0, 1) * 0.25 * (noise(y.shape, 1.0, seed) > 0))   # grime
    return outline(spr, '#1a0a02', width=0.65)


def cone_stack(h, seed=1):
    """traffic cones stacked one in another, the way they are carried"""
    h = int(round(h))
    c = cone(h, seed, w=26)
    I = inner(c)
    y, x = grid(I.shape[0] / SC, I.shape[1] / SC)
    w = I.shape[1] / SC
    for k in range(1, 9):                                 # the rims of the cones inside, showing as steps
        yy = h - 3 - k * 8
        if yy < 8:
            break
        half = 1.2 + (w / 2 - 3.0) * (yy / (h - 3))
        A.stroke(I, [(w / 2 - half, yy), (w / 2 + half, yy)], 0.5, '#5a1a00', 220, scale=1.0)
        A.stroke(I, [(w / 2 - half, yy + 0.5), (w / 2 + half, yy + 0.5)], 0.3, '#ffc080', 200, scale=1.0)
    return c


def T_manhole():
    far = manhole_far()
    R = RS(1111)
    mid = wide()
    for k in range(18):                                   # leaves coming down, turning
        l = leaf('g' if k % 3 else 'm', R.uniform(6, 10), 1120 + k)
        l = ndimage.rotate(l, R.uniform(0, 360), reshape=True, order=1)
        l[..., 3] *= 0.9
        put(mid, l, R.uniform(0, WT), R.uniform(24, GY - 20))
    motes(mid, 120, ['#fffbe0', '#ffffff'], 1121, r=(0.3, 0.8), a=(120, 220))
    mid = crop(mid)
    floor = wall([(1.4, ramp('#4a3a10', '#7a6420', '#a08a3a', n=3), pat_slime), (9, CONC, pat_concrete), (40, SOIL, pat_soil)], True, seed=1141, bumps=0.6, out='#141a16')
    ceil = manhole_ceil()
    obs = {'low': [leaf_pile(26, 9, 1), can(14, 9, 2)],
           'tall': [cone(40, 1), cone(46, 2)],
           'hang': [ladder_hang(1, 14)],
           'float': [leaf('g', 15, 3), leaf('m', 16, 4)],
           'huge': [tower(lambda h: cone_stack(h, 5))]}
    return dict(far=far, mid=mid, floor=floor, ceil=ceil, obs=obs, coin='drop', special='soap')


# ================================================================== 9. the trunk sewer (an old brick arch)
WATER_TR = '#56645a'
BRICK = ramp('#4a2418', '#6e3826', '#924e36', '#b06a4c', '#c88a6a', n=5)
FATB = ramp('#5e5a46', '#8a8466', '#b4ac88', '#d4ccaa', '#ece6cc')


def trunk_far(seed=1201):
    R = RS(seed)
    far = gradient(H, ['#8e6a58', '#765646', '#5a4236', '#3e2e26'])
    y, x = grid(H, WT)
    row = np.floor(y / 6.0)
    xs = x + np.mod(row, 2) * 7 + 0.3 * np.sin(y * 0.2)
    mort = np.maximum(band_line(y, 6.0, 0.6, 0.0), band_line(xs, 14.0, 0.55, 0.0))
    tone = 0.85 + 0.15 * np.sin(row * 12.9898 + np.floor(xs / 14) * 78.233) ** 2 + 0.06 * noise(y.shape, 0.8, seed)
    mul(far, tone)
    lerp_rgb(far, '#9a9484', mort * 0.55)
    lerp_rgb(far, '#000000', np.clip(band_line(y - 0.5, 6.0, 0.35, 0.0) * 0.4, 0, 1))
    pipe_curve(far, -30, GY + 20, 0.42, lit=0.45)          # the arch: the wall curving away above
    arch = np.clip((40 - y) / 40, 0, 1)
    mul(far, 1 - 0.35 * arch)
    water_line(far, 26, '#2e3424', k=0.65, h=16, seed=seed + 1)
    lerp_rgb(far, '#2a3020', np.clip((y - 70) / 80, 0, 1) * 0.45)                      # black-green below
    streaks(far, 30, seed + 2, '#e0dccc', k=0.3, y0=20, y1=80, ang=np.pi / 2, L=(14, 50), w=(0.5, 1.3))      # lime from the mortar
    c3 = three(far)
    for k in range(14):                                   # fat stuck on the walls in grey-white crusts
        g = mass(R.uniform(10, 22), R.uniform(4, 8), seed + 20 + k, FATB, '#2a261a', n=3, ambient=0.4, grain_k=0.1)
        g[..., 3] *= 0.75
        put_wrap(c3, g, R.uniform(0, WT), R.uniform(24, 40))
    drift(c3, 120, ['#c8c0a8', '#a89c80', '#e8e2d0'], seed + 3, y0=20, y1=GY - 6, a=140)
    far = crop(c3)
    haze(far, WATER_TR, 0.22)
    return far


def fat_chunk(w=26, h=14, seed=1):
    """a piece of a fatberg: congealed fat grey-yellow, wipes and rags bound in it"""
    R = RS(seed)
    spr = mass(w, h, seed, FATB, '#2a261a', n=5, ambient=0.4, hl_t=0.99, grain_k=0.12)
    speckle(spr, seed + 1, int(w * h * 0.15), ['#6a6450', '#f4f0e0', '#8a7a50'], r=(0.25, 0.6), a=170)
    I = inner(spr); keep = I[..., 3].copy()
    for k in range(max(1, int(w * h / 90))):
        g = D.wet_wipe(seed + 10 + k, R.uniform(6, 9), R.uniform(3.5, 5))
        g[..., :3] = g[..., :3] * 0.8 + hexc('#c8bc90') * 0.2
        paste(I, g, R.uniform(0, w - 7), R.uniform(0, h - 4))
    I[..., 3] = keep
    return spr


def fatberg(h, seed=5, w=26):
    R = RS(seed)
    h = int(round(h))
    spr = mass(w, h, seed, FATB, '#2a261a', taper=0.4, wob=0.14, ambient=0.4, hl_t=0.99, grain_k=0.12)
    speckle(spr, seed + 1, int(w * h * 0.12), ['#6a6450', '#f4f0e0', '#8a7a50'], r=(0.25, 0.6), a=170)
    I = inner(spr); keep = I[..., 3].copy()
    for k in range(int(h / 6)):
        g = D.wet_wipe(seed + 10 + k, R.uniform(6, 10), R.uniform(3.5, 6))
        g[..., :3] = g[..., :3] * 0.8 + hexc('#c8bc90') * 0.2
        paste(I, g, w / 2 - 4 + R.uniform(-w * 0.25, w * 0.25), R.uniform(1, h - 5))
    I[..., 3] = keep
    return spr


def fat_icicle(seed=1, wdt=14):
    """fat dripped and set hanging from the crown: a lumpy grey-white icicle"""
    L = hang_len()
    R = RS(seed)
    W = wdt + 6
    y, x = grid(L, W)
    t = np.clip(y / L, 0, 1)
    cx = W / 2 + 1.2 * np.sin(y * 0.07 + seed) * t
    half = wdt / 2 * (1 - 0.7 * t) + 1.2 * np.sin(y * 0.3 + seed) * (1 - t) + 0.9 * np.exp(-((y - L * 0.4) / 7) ** 2) + 0.7 * np.exp(-((y - L * 0.7) / 5) ** 2)
    tip = L - 1.5 - 4 * (np.abs(x - cx) / np.maximum(half, 1)) ** 2
    m = (np.abs(x - cx) <= half) & (y <= tip)
    spr = A.mask_sprite(m, FATB, '#2a261a', soft=1.6, ambient=0.4, hl_t=0.99)
    A.grain(spr, seed, 0.12, 0.5)
    speckle(spr, seed + 2, int(L * 1.2), ['#6a6450', '#f4f0e0'], r=(0.25, 0.5), a=160)
    return spr


def T_trunk():
    far = trunk_far()
    R = RS(1211)
    mid = wide()
    for k in range(10):
        g = fat_chunk(R.uniform(5, 9), R.uniform(3, 5), 1220 + k); g[..., 3] *= 0.8
        put(mid, g, R.uniform(0, WT), R.uniform(30, GY - 20))
    motes(mid, 140, ['#c8c0a8', '#8a8068', '#e8e2d0'], 1221, r=(0.3, 0.9), a=(110, 200))
    mid = crop(mid)
    floor = wall([(2.0, ramp('#2a3020', '#424a32', '#5e6646', n=3), pat_slime), (12, BRICK, pat_brick), (40, SOIL, pat_soil)], True, seed=1241, bumps=0.5, out='#160c08')
    def bpat(lit, x, d, y, R):
        row = np.floor(np.maximum(d, 0) / 3.2)
        xs = x + np.mod(row, 2) * 7
        mort = np.maximum(band_line(d, 3.2, 0.45, 0.0), band_line(xs, 14, 0.5, 0.0))
        return lit + 0.1 * np.sin(row * 12.9 + np.floor(xs / 14) * 78.2) ** 2 - 0.35 * mort
    ceil = surf_ceil(1251, BRICK, crown_pat=bpat, crown_h=7.0, air=('#2e2a24', '#4a4238', '#6a6052'), mirror='#e2e0d4', out='#1a1410')
    obs = {'low': [fat_chunk(26, 14, 1), fat_chunk(22, 12, 2)],
           'tall': [fatberg(42, 3, 24), fatberg(48, 13, 26)],
           'hang': [fat_icicle(1, 14), fat_icicle(2, 12)],
           'float': [fat_chunk(18, 13, 4), fat_chunk(15, 11, 5)],
           'huge': [tower(lambda h: fatberg(h, 23, 28))]}
    return dict(far=far, mid=mid, floor=floor, ceil=ceil, obs=obs, coin='drop', special='soap')


# ================================================================== 10. where the storm water comes in (combined sewer)
WATER_CB = '#7a7258'


def combined_far(seed=1301):
    R = RS(seed)
    far = gradient(H, ['#a8a088', '#8c846a', '#706850', '#544c38'])
    concrete_tex(far, seed + 1, k=0.9, cols=('#2a261a', '#d8d2bc'))
    y, x = grid(H, WT)
    c3 = three(far)
    inlets = []
    for k in range(3):                                    # the storm inlets: square mouths high up, water pouring in
        cx = (k + 0.4) * WT / 3 + R.uniform(-50, 50); w_ = R.uniform(34, 44)
        inlets.append((cx, w_))
        g = canvas(w_ + 6, 24)
        fill_rect(g, 0, 0, w_ + 6, 24, '#2e2a20', 255)
        fill_rect(g, 3, 2, w_ + 3, 21, '#080806', 255)
        for i in range(int(w_ / 5)):                       # the grating's bars across it
            fill_rect(g, 4 + i * 5, 2, 5.4 + i * 5, 21, '#3e3a30', 255)
        put_wrap(c3, outline(g, '#0e0c08'), cx - w_ / 2 - 3, 8)
    far = crop(c3)
    for (cx, w_) in inlets:
        D.falling_water(far, cx, 30, w_ * 0.8, GY - 2, seed + int(cx), k=0.7)
        D.falling_water(far, cx + R.uniform(-6, 6), 30, w_ * 0.4, GY - 2, seed + int(cx) + 1, k=0.4)
    streaks(far, 60, seed + 2, '#5a4a2a', k=0.3, y0=40, y1=GY, L=(60, 220), w=(1.0, 3.0))     # mud carried along
    silt(far, 128, ('#3a2e1a', '#5a4a2c', '#7a6844', '#94825c'), seed + 3)
    c3 = three(far)
    drift(c3, 220, ['#8a7a54', '#b4a478', '#5a4c30'], seed + 4, y0=20, y1=GY - 4, a=170)
    far = crop(c3)
    haze(far, WATER_CB, 0.24)
    return far


def plastic_bag(w=20, h=16, seed=1, dark=False, hang=False):
    """a thin plastic bag, half full of water, its handles: see-through white (or black), wrinkled"""
    R = RS(seed)
    L = hang_len() if hang else h
    W = w + 4
    y, x = grid(L, W)
    if hang:
        t = np.clip(y / L, 0, 1)
        cx = W / 2 + 2.5 * np.sin(y * 0.05 + seed) * t
        half = w / 2 * (0.25 + 0.75 * np.sin(np.clip(t, 0, 1) * np.pi * 0.95) ** 0.6) + 0.8 * np.sin(y * 0.35 + seed)
        m = (np.abs(x - cx) <= half) & (y <= L - 1.5 - 2 * np.abs(np.sin((x - cx) * 0.5 + seed)))
    else:                                                  # drifting on its side, puffed with water, crumpled to the left
        xs = (x - W * 0.42) / (w * 0.42); ys = (y - L * 0.55) / (L * 0.42)
        ang = np.arctan2(ys, xs)
        rr = np.sqrt(xs ** 2 + ys ** 2)
        m = rr <= 0.9 + 0.08 * np.sin(ang * 3 + seed) + 0.05 * np.sin(ang * 7 + 2 * seed)
        nk = (x > W * 0.75) & (np.abs(y - L * 0.5 - 0.8 * np.sin(x * 0.9 + seed)) < 1.6 - 0.8 * (x - W * 0.75) / (W * 0.25)) & (x < W - 0.8)
        m |= nk                                            # the neck, twisted, trailing
    rmp = ramp('#141418', '#2a2a30', '#4a4a54', '#7a7a86') if dark else ramp('#9aa0a4', '#c8ced0', '#e8eeee', '#ffffff')
    spr = A.mask_sprite(m, rmp, '#202428', soft=1.4, ambient=0.5, hl_t=0.97)
    I = inner(spr)
    for k in range(int(L * 0.6)):                         # wrinkles
        a0 = R.uniform(-0.5, 0.5) + (np.pi / 2 if hang else 0); cx0, cy0 = R.uniform(2, W - 2), R.uniform(2, L - 2)
        l = R.uniform(2, 5)
        A.stroke(I, [(cx0, cy0), (cx0 + np.cos(a0) * l, cy0 + np.sin(a0) * l)], 0.22, '#5a6064' if not dark else '#9a9aa6', 110, scale=1.0)
    keep = I[..., 3]
    I[..., 3] = keep * (0.8 if not dark else 0.95)
    if not dark:
        ell = noise(I.shape[:2], 1.5, seed)
        I[..., :3] = I[..., :3] * (1 - 0.12 * (ell > 0.3)[..., None])
    return spr if not hang else spr[:px(L)]


def umbrella(h=42, seed=1):
    """a broken umbrella blown in, standing on its tip: black canopy turned inside out, ribs bent, the handle up"""
    R = RS(seed)
    w = 30
    out = canvas(w, h)
    cx = w / 2
    A.stroke(out, [(cx, h - 1), (cx, 8)], 1.2, '#0a0a0a', 255, scale=1.0)            # the shaft
    A.stroke(out, [(cx, h - 1), (cx, 8)], 0.7, '#8a8e92', 255, scale=1.0)
    hk = [(cx + 3 * np.sin(a), 8 - 3 + 3 * np.cos(a)) for a in np.linspace(np.pi, 2 * np.pi * 0.95, 14)]
    A.stroke(out, [(cx, 9)] + hk, 1.8, '#0a0a0a', 255, scale=1.0)
    A.stroke(out, [(cx, 9)] + hk, 1.2, '#7a3a1a', 255, scale=1.0)
    y, x = grid(h, w)                                     # the canopy, blown up into a bowl round the shaft
    t = (y - (h * 0.45)) / (h * 0.5)
    half = (w / 2 - 1) * np.clip(1 - np.abs(t) ** 1.4, 0, 1) ** 0.6 * (1 + 0.15 * np.sin(x * 0.8 + seed))
    m = (np.abs(x - cx) <= half) & (y > h * 0.2) & (y < h * 0.82)
    m &= ~((y < h * 0.3 + 3 * np.abs(np.sin((x - cx) * 0.4 + seed))) & (np.abs(x - cx) > 2))
    can_ = A.mask_sprite(m, ramp('#060608', '#18181e', '#2c2c36', '#46465a'), '#000000', soft=1.4, ambient=0.35, hl_t=0.97)
    I = inner(can_); keep = I[..., 3].copy()
    for k in range(5):                                    # the ribs
        xx = cx + (k - 2) * w * 0.18
        A.stroke(I, [(cx, h * 0.8), (xx, h * 0.22 + R.uniform(-2, 2))], 0.35, '#9aa0a8', 220, scale=1.0)
    I[..., 3] = keep
    paste(out, can_, -1, -1)
    A.stroke(out, [(cx, h * 0.84), (cx, h - 1)], 1.2, '#0a0a0a', 255, scale=1.0)
    A.stroke(out, [(cx, h * 0.84), (cx, h - 1)], 0.7, '#8a8e92', 255, scale=1.0)
    return trim(out)


def branch(h=44, seed=1):
    """a branch broken off in the storm, stuck upright in the mud: bark, a fork, wet leaves still on it"""
    R = RS(seed)
    w = 28
    out = canvas(w, h)
    cx = w / 2
    main = [(cx + 1.5 * np.sin(t * 2.5 + seed), h - 0.8 - t * (h - 6)) for t in np.linspace(0, 1, 30)]
    def bark(pts, w0):
        n = len(pts)
        for i in range(n - 1):
            ww = max(0.5, w0 * (1 - i / n * 0.6))
            A.stroke(out, [pts[i], pts[i + 1]], ww + 0.7, '#140c06', 255, scale=1.0)
        for i in range(n - 1):
            ww = max(0.4, w0 * (1 - i / n * 0.6))
            A.stroke(out, [pts[i], pts[i + 1]], ww, ['#5a3e24', '#6e4c2c', '#4a321c'][(i // 4) % 3], 255, scale=1.0)
            A.stroke(out, [(pts[i][0] - ww * 0.3, pts[i][1]), (pts[i + 1][0] - ww * 0.3, pts[i + 1][1])], ww * 0.25, '#9a7a52', 200, scale=1.0)
    bark(main, 3.0)
    for k in range(3):                                    # side branches
        j = R.randint(8, 24); bx, by = main[j]; side = 1 if k % 2 else -1
        sub = [(bx + side * t * R.uniform(8, 11), by - t * R.uniform(6, 10) + 1.0 * np.sin(t * 3)) for t in np.linspace(0, 1, 12)]
        bark(sub, 1.6)
        for q in range(3):
            lx, ly = sub[-1 - q * 3]
            l = leaf('m' if (k + q) % 3 == 0 else 'g', R.uniform(6, 8), seed * 10 + k * 3 + q)
            l = ndimage.rotate(l, R.uniform(-50, 50), reshape=True, order=1)
            paste(out, l, lx - l.shape[1] / SC / 2, ly - l.shape[0] / SC / 2)
    for q in range(3):
        lx, ly = main[-1 - q * 2]
        l = leaf('g', R.uniform(6, 8), seed * 20 + q)
        l = ndimage.rotate(l, R.uniform(-40, 40), reshape=True, order=1)
        paste(out, l, lx - l.shape[1] / SC / 2 + R.uniform(-2, 2), ly - l.shape[0] / SC / 2)
    return trim(out)


def storm_pile(h, seed=5, w=26):
    """branches, bags and mud piled up by the storm"""
    R = RS(seed)
    h = int(round(h))
    spr = mass(w, h, seed, ramp('#2e2414', '#4a3c22', '#6a5634', '#8a744c'), '#140e06', taper=0.45, wob=0.14, ambient=0.35, hl_t=0.995, grain_k=0.14)
    I = inner(spr); keep = I[..., 3].copy()
    for k in range(int(h / 5)):
        yy = R.uniform(1, h - 4); kind = k % 4
        if kind == 0:
            g = plastic_bag(R.uniform(8, 12), R.uniform(6, 9), seed + 20 + k, dark=bool(k % 8))
        elif kind == 1:
            g = leaf('g' if k % 3 else 'm', R.uniform(6, 9), seed + 30 + k)
        else:
            g = canvas(14, 4); ang = R.uniform(-0.4, 0.4)
            p0 = (0.5, 2 - 6 * np.sin(ang)); p1 = (13.5, 2 + 6 * np.sin(ang))
            A.stroke(g, [p0, p1], 1.6, '#24140a', 255, scale=1.0); A.stroke(g, [p0, p1], 1.0, '#7a5230', 255, scale=1.0)
        paste(I, g, w / 2 - g.shape[1] / SC / 2 + R.uniform(-w * 0.3, w * 0.3), yy)
    I[..., 3] = keep
    return spr


def T_combined():
    far = combined_far()
    R = RS(1311)
    mid = wide()
    for k in range(16):
        l = leaf('g' if k % 2 else 'm', R.uniform(6, 9), 1320 + k)
        l = ndimage.rotate(l, R.uniform(0, 360), reshape=True, order=1); l[..., 3] *= 0.85
        put(mid, l, R.uniform(0, WT), R.uniform(24, GY - 20))
    for k in range(6):
        b = plastic_bag(R.uniform(8, 12), R.uniform(6, 9), 1330 + k, dark=bool(k % 3 == 0)); b[..., 3] *= 0.7
        put(mid, b, R.uniform(0, WT), R.uniform(24, GY - 24))
    bubble_chain(mid, 14, 1340, y0=40, y1=GY - 10, r=(1, 3), alpha=0.6)
    motes(mid, 180, ['#8a7a54', '#b4a478', '#5a4c30'], 1341, r=(0.3, 1.0), a=(120, 210))
    mid = crop(mid)
    MUD = ramp('#2a2010', '#44361e', '#62502e', '#7e6a44', n=4)
    floor = wall([(3.0, MUD, pat_sludge), (9, CONC, pat_concrete), (40, SOIL, pat_soil)], True, seed=1351, bumps=1.0, out='#120c06')
    def extra(c3, R, rim_b, surf):                         # the street grating above: daylight between its bars
        for j in range(3):
            cx = (j + 0.4) * WT / 3
            for off in (0, WT, 2 * WT):
                for i in range(-5, 6):
                    fill_rect(c3, cx + off + i * 4 - 1.2, 0.8, cx + off + i * 4 + 1.2, 6.0, '#fffbe0', 255)
    ceil = surf_ceil(1361, ramp('#2e2a24', '#4a453c', '#6a6458', '#8a8476', n=4), crown_h=6.8, air=('#3e3a2e', '#5e584a', '#827a66'),
                     mirror='#e8e2cc', out='#1e1a12', extra=extra)
    obs = {'low': [silt_heap(28, 10, 11, rmp=MUD, out='#120c06'), can(14, 9, 12)],
           'tall': [branch(44, 1), storm_pile(46, 3, 24)],
           'hang': [plastic_bag(16, 0, 1, hang=True), plastic_bag(14, 0, 2, dark=True, hang=True)],
           'float': [plastic_bag(20, 16, 3), plastic_bag(18, 14, 4, dark=True)],
           'huge': [tower(lambda h: storm_pile(h, 13, 26))]}
    return dict(far=far, mid=mid, floor=floor, ceil=ceil, obs=obs, coin='drop', special='soap')


# ================================================================== 11. the interceptor (a huge round tunnel)
WATER_IC = '#4e5e66'


def interceptor_far(seed=1401):
    R = RS(seed)
    far = gradient(H, ['#7a8890', '#626e76', '#4c565e', '#363e46'])
    concrete_tex(far, seed + 1, k=0.7, cols=('#1a2026', '#c4ccd2'))
    y, x = grid(H, WT)
    pipe_curve(far, -120, GY + 120, 0.18, lit=0.5)         # so big its curve hardly shows
    per = WT / 5                                            # the lining's segments: rings, and joints along them
    for j in range(5):
        x0 = j * per
        d = wdx(x, x0)
        lerp_rgb(far, '#0c1014', np.exp(-(d / 0.6) ** 2) * 0.6)
        lerp_rgb(far, '#d8e0e6', np.exp(-((d - 1.0) / 0.5) ** 2) * 0.2)
    for j, yy in enumerate((30, 84, 138)):
        stag = (j % 2) * per / 2
        lerp_rgb(far, '#0c1014', np.exp(-((y - yy) / 0.6) ** 2) * 0.55)
    c3 = three(far)
    for j in range(5):                                     # bolt pockets along the joints
        for i, yy in enumerate((30, 84, 138)):
            for s in (-1, 1):
                bx = j * per + s * 9 + ((i % 2) * per / 2 if False else 0); by = yy + (6 if s > 0 else -6)
                g = canvas(6, 5); fill_rect(g, 0.5, 0.5, 5.5, 4.5, '#1a2026', 255); fill_rect(g, 1.2, 1.2, 4.8, 2.4, '#2e363e', 255)
                disc(g, 3, 3.2, 0.7, '#8a5a3a', 255)
                put_wrap(c3, g, bx - 3, by - 2.5)
    for k in range(3):                                     # a work lamp left on the wall, a cable along it
        lx = (k + 0.3) * WT / 3
        g = canvas(10, 8); ellipse_soft(g, 5, 4, 3.4, 2.4, '#3a3a2a', 255); ellipse_soft(g, 5, 3.6, 2.4, 1.6, '#fff4c0', 255); ellipse_soft(g, 5, 3.4, 1.2, 0.8, '#ffffff', 255)
        put_wrap(c3, outline(g, '#101010'), lx - 5, 14)
    far = crop(c3)
    yy = 18 + 1.2 * per_sin(x, 6, 1.0) + 0.6 * per_sin(x, 17, 2.0)
    lerp_rgb(far, '#101214', np.exp(-((y - yy) / 0.55) ** 2) * 0.8)
    for k in range(3):
        lx = (k + 0.3) * WT / 3
        glow = np.exp(-(wdx(x, lx) / 40) ** 2 - ((y - 18) / 30) ** 2)
        lerp_rgb(far, '#fff0b8', glow * 0.3)
    water_line(far, 30, '#28322a', k=0.45, h=10, seed=seed + 2)
    silt(far, 136, ('#22241e', '#3a3c32', '#56584a', '#6e705e'), seed + 3, k=0.8)
    c3 = three(far)
    drift(c3, 110, ['#aab4ba', '#d4dce0', '#7a868e'], seed + 4, y0=20, y1=GY - 6, a=130)
    far = crop(c3)
    haze(far, WATER_IC, 0.24)
    return far


def tire(w=26, h=10, seed=1, upright=False):
    """an old car tyre: lying flat (an ellipse with its hole) or standing on its tread (a round with its hole)"""
    R = RS(seed)
    if upright:
        d = w
        y, x = grid(d, d)
        r = np.sqrt((x - d / 2) ** 2 + (y - d / 2) ** 2) / (d / 2 - 0.8)
        m = (r <= 1) & (r >= 0.48)
        tread = np.clip(1 - np.abs(np.mod(np.arctan2(y - d / 2, x - d / 2) * 18 / np.pi, 1) - 0.5) / 0.18, 0, 1) * (r > 0.86)
    else:
        y, x = grid(h, w)
        r = np.sqrt(((x - w / 2) / (w / 2 - 0.8)) ** 2 + ((y - h * 0.45) / (h * 0.45 - 0.6)) ** 2)
        side = (y > h * 0.45) & (np.abs(x - w / 2) <= w / 2 - 0.8) & (y < h - 0.6)
        r_in = np.sqrt(((x - w / 2) / (w * 0.27)) ** 2 + ((y - h * 0.45) / (h * 0.22)) ** 2)
        m = ((r <= 1) | side) & ~(r_in <= 1)
        tread = side * np.clip(1 - np.abs(np.mod(x, 1.6) - 0.8) / 0.3, 0, 1)
    spr = A.mask_sprite(m, ramp('#060606', '#141416', '#26262a', '#3c3c42', '#56565e'), '#000000', soft=1.0, ambient=0.3, hl_t=0.97)
    I = inner(spr)
    I[..., :3] *= (1 - 0.35 * tread[..., None])
    lerp_rgb(I, '#6a5a3a', np.clip(noise(I.shape[:2], 1.0, seed) - 0.3, 0, 1) * 0.5 * (I[..., 3] > 0))       # silt in it
    return spr


def tire_stack(h, seed=1, w=28):
    R = RS(seed)
    parts = []; tot = 0
    while tot < h - 2:
        s = tire(w - R.uniform(0, 2), 9, seed + len(parts)); parts.append(s); tot += s.shape[0] / SC - 3.2
    return stack(parts, gap=-3.2)


def rope_hang(seed=1):
    """a rope hanging into the tunnel from a fitting above, rags and a bag snagged on it"""
    L = hang_len()
    R = RS(seed)
    out = canvas(18, L)
    pts = [(9 + 1.5 * np.sin(t * 2.5 + seed) * t, t * (L - 3)) for t in np.linspace(0, 1, 40)]
    A.stroke(out, pts, 1.6, '#1a1208', 255, scale=1.0)
    A.stroke(out, pts, 1.0, '#a08a5a', 255, scale=1.0)
    for i in range(0, 40, 2):                             # its lay: twisted strands
        x0, y0 = pts[i]
        A.stroke(out, [(x0 - 0.45, y0), (x0 + 0.45, y0 + 1.0)], 0.25, '#5a4a2a', 220, scale=1.0)
    for k in range(3):
        t = R.uniform(0.3, 0.9); x0, y0 = pts[int(t * 39)]
        g = plastic_bag(R.uniform(9, 12), R.uniform(7, 9), seed + 10 + k, dark=bool(k % 2)) if k != 1 else TT.paper_shred(seed + 20, 9, 6)
        paste(out, g, x0 - g.shape[1] / SC / 2, y0 - 2)
    knot = lump(5, 4, seed + 5, ramp('#5a4a2a', '#a08a5a', '#d0bc8a'), '#1a1208', bumps=2, flat_bottom=False, soft=0.6)
    paste(out, knot, pts[-1][0] - 2.5, L - 5)
    return out


def styrofoam(w=20, h=12, seed=1):
    """a broken block of polystyrene foam: its top face lit, the side in shade, white beads packed, one end snapped"""
    R = RS(seed)
    y, x = grid(h, w)
    top_h = h * 0.32
    brk = w - 0.8 - 2.2 * np.abs(np.sin(y * 1.1 + seed)) - 1.0 * np.abs(np.sin(y * 2.7))
    m = (x > 0.8 + 1.6 * np.clip(1 - y / top_h, 0, 1)) & (x < brk) & (y > 0.6) & (y < h - 0.6)
    face = y < top_h
    sh = np.where(face, 0.92, 0.62 - 0.15 * (y - top_h) / (h - top_h))
    spr = np.zeros(y.shape + (4,), np.float32)
    spr[..., :3] = ramp_col(ramp('#8a949a', '#bcc6ca', '#e2e8ea', '#f8fbfb', '#ffffff'), sh)
    spr[..., 3] = smooth_mask(m) * 255
    bx = np.mod(x + 0.6 * (np.floor(y / 1.2) % 2), 1.2) - 0.6; by = np.mod(y, 1.2) - 0.6
    beads = np.clip(1 - np.sqrt(bx ** 2 + by ** 2) / 0.58, 0, 1)
    spr[..., :3] *= (0.86 + 0.14 * beads[..., None])
    lerp_rgb(spr, '#5a6a70', (np.abs(y - top_h) < 0.35) * 0.6 * m)
    lerp_rgb(spr, '#8a7e5a', np.clip(noise(y.shape, 1.2, seed) - 0.35, 0, 1) * 0.5 * m)
    return outline(spr, '#3a4448', width=0.6)


def T_interceptor():
    far = interceptor_far()
    R = RS(1411)
    mid = wide()
    motes(mid, 160, ['#aab4ba', '#7a868e', '#d4dce0'], 1412, r=(0.3, 1.0), a=(100, 190))
    for k in range(5):
        g = styrofoam(R.uniform(5, 8), R.uniform(3, 5), 1420 + k); g[..., 3] *= 0.75
        put(mid, g, R.uniform(0, WT), R.uniform(30, GY - 24))
    bubble_chain(mid, 5, 1430, r=(1, 2), alpha=0.5)
    mid = crop(mid)
    floor = wall([(2.4, SILT, pat_sludge), (14, ramp('#2c3238', '#464e56', '#626c74', '#808a92', n=4), pat_concrete), (40, SOIL, pat_soil)], True, seed=1441, bumps=0.4, out='#0e1216')
    ceil = surf_ceil(1451, ramp('#20262c', '#3a4248', '#56606a', '#727e88', n=4), crown_h=7.0, air=('#202830', '#36424a', '#506068'), mirror='#dce6ea', out='#121a20')
    obs = {'low': [tire(26, 10, 1), concrete_chunk(22, 11, 2)],
           'tall': [tire(30, 0, 3, upright=True), tire_stack(40, 4, 28)],
           'hang': [rope_hang(1), rope_hang(2)],
           'float': [styrofoam(20, 12, 1), styrofoam(16, 10, 2)],
           'huge': [tower(lambda h: tire_stack(h, 9, 28))]}
    return dict(far=far, mid=mid, floor=floor, ceil=ceil, obs=obs, coin='drop', special='soap')


# ================================================================== 12. the pumping station's wet well
WATER_PS = '#4e6870'
STEEL = ramp('#2a3036', '#4a545c', '#6e7a84', '#98a4ac', '#c4ced4', '#e8eef2', n=6)
PAINT = ramp('#0e2a4a', '#1a4472', '#2e64a0', '#5a90c8', '#9cc4ea', n=5)


def pump_far(seed=1501):
    R = RS(seed)
    far = gradient(H, ['#8aa0a8', '#70868e', '#566c74', '#3e525a'])
    concrete_tex(far, seed + 1, k=0.8, cols=('#1a262c', '#ccd8dc'))
    y, x = grid(H, WT)
    c3 = three(far)
    for j in range(2):                                    # the stair down into the well: treads, stringer, handrail
        x0 = j * WT / 2 + 60
        g = canvas(130, 130)
        for i in range(12):
            tx, ty = 4 + i * 10, 4 + i * 10
            fill_rect(g, tx, ty, tx + 12, ty + 1.6, '#5a646c', 255)
            fill_rect(g, tx, ty, tx + 12, ty + 0.5, '#c4ccd2', 255)
            for k in range(5):
                fill_rect(g, tx + 1 + k * 2.2, ty + 0.3, tx + 1.8 + k * 2.2, ty + 1.4, '#2a3036', 255)
        A.stroke(g, [(4, 7), (126, 129)], 2.2, '#1a2026', 255, scale=1.0)
        A.stroke(g, [(4, 7), (126, 129)], 1.4, '#7a868e', 255, scale=1.0)
        A.stroke(g, [(4, -12), (126, 110)], 1.0, '#1a2026', 255, scale=1.0)
        A.stroke(g, [(4, -12), (126, 110)], 0.6, '#e8c020', 255, scale=1.0)
        for i in range(6):
            px0 = 8 + i * 22
            A.stroke(g, [(px0, px0 - 16 + 4), (px0, px0 + 4)], 0.8, '#1a2026', 255, scale=1.0)
            A.stroke(g, [(px0, px0 - 16 + 4), (px0, px0 + 4)], 0.45, '#e8c020', 255, scale=1.0)
        g[..., 3] *= 0.85
        put_wrap(c3, g, x0, 4)
    for j in range(2):                                    # the big pipe from the pumps, painted, its flanges and bolts
        x0 = j * WT / 2 + WT / 4 + 40
        g = canvas(36, 150)
        yy, xx = grid(150, 36)
        sh = np.clip(0.6 + 0.4 * np.cos((xx - 18) / 15 * np.pi / 2) - 0.2 * (xx > 18), 0, 1)
        col = ramp_col(PAINT, sh)
        g[..., :3] = col; g[..., 3] = ((np.abs(xx - 18) < 15) * 255).astype(np.float32)
        for fy in (30, 80, 130):
            fill_rect(g, 0.5, fy - 2.2, 35.5, fy + 2.2, '#16324e', 255)
            fill_rect(g, 0.5, fy - 2.2, 35.5, fy - 1.4, '#7aa4cc', 255)
            for b in range(5):
                disc(g, 3 + b * 7.5, fy, 0.8, '#c4ccd2', 255)
        put_wrap(c3, outline(g, '#0a1420'), x0, 0)
    for j in range(2):                                    # a pump's volute casing behind, half in shadow
        cx, cy = j * WT / 2 + WT / 4 - 60, 110
        g = canvas(70, 60)
        yy, xx = grid(60, 70)
        a_ = np.arctan2(yy - 32, xx - 35); r_ = np.sqrt((xx - 35) ** 2 + (yy - 32) ** 2)
        lim = 18 + 6 * (np.mod(a_ + np.pi, TAU) / TAU)
        m = (r_ <= lim) | ((xx > 35) & (xx < 62) & (yy > 32 - 24) & (yy < 32 - 10))
        sp = A.mask_sprite(m, PAINT, '#0a1420', soft=2.0, ambient=0.3, hl_t=0.97)
        disc(inner(sp), 35, 32, 6, '#1a3a5a', 255); disc(inner(sp), 35, 32, 3, '#9cc4ea', 255)
        sp[..., 3] *= 0.8
        put_wrap(c3, sp, cx - 35, cy - 32)
    far = crop(c3)
    water_line(far, 28, '#2a3a32', k=0.4, h=10, seed=seed + 2)
    TT.caustics(far, seed + 3, k=0.25)
    c3 = three(far)
    drift(c3, 100, ['#c4d4da', '#ffffff', '#8aa0a8'], seed + 4, y0=20, y1=GY - 6, a=130)
    far = crop(c3)
    haze(far, WATER_PS, 0.2)
    return far


def impeller(d=24, seed=1):
    """a pump's impeller: a disc with curved vanes round a hub, bronze-coloured, scratched"""
    y, x = grid(d, d)
    cx = cy = d / 2
    r = np.sqrt((x - cx) ** 2 + (y - cy) ** 2) / (d / 2 - 0.8)
    a = np.arctan2(y - cy, x - cx)
    disc_m = r <= 1
    ph = np.mod(a * 6 / TAU - r * 1.1, 1)                  # six vanes curving back
    vane = np.clip(1 - np.abs(ph - 0.3) / 0.16, 0, 1) * (r > 0.3) * (r <= 0.97)
    gap = (1 - vane) * (r > 0.32) * (r < 0.97)
    sh = np.clip(0.5 - 0.3 * (y - cy) / (d / 2) - 0.2 * (x - cx) / (d / 2) + 0.35 * vane, 0, 1)
    spr = np.zeros(y.shape + (4,), np.float32)
    spr[..., :3] = ramp_col(ramp('#4a2a0e', '#7a4a1e', '#b07a3a', '#dcae66', '#f8dca0'), sh)
    spr[..., 3] = smooth_mask(disc_m) * 255
    lerp_rgb(spr, '#1a0e04', gap * 0.75)
    lerp_rgb(spr, '#fff0c8', np.clip(1 - np.abs(ph - 0.22) / 0.03, 0, 1) * (r > 0.32) * (r < 0.95) * 0.5)
    hub = r <= 0.26
    spr[..., :3] = np.where(hub[..., None], ramp_col(STEEL, np.clip(0.6 - 0.4 * (y - cy) / (d * 0.13), 0, 1)), spr[..., :3])
    lerp_rgb(spr, '#0a0a0a', (r <= 0.1) * 1.0)
    return outline(spr, '#1a0e04', width=0.65)


def bell_pipe(seed=1, wdt=16):
    """a pump's suction pipe hanging down into the well, ending in a flared bell mouth"""
    L = hang_len()
    W = wdt + 14
    y, x = grid(L, W)
    flare = np.clip((y - (L - 14)) / 14, 0, 1) ** 2
    half = wdt / 2 + 6.5 * flare
    m = (np.abs(x - W / 2) <= half) & (y < L - 0.6)
    u = (x - W / 2) / np.maximum(half, 1)
    sh = np.clip(0.6 - 0.45 * u - 0.15 * u ** 4, 0, 1)
    spr = np.zeros(y.shape + (4,), np.float32)
    spr[..., :3] = ramp_col(PAINT, sh); spr[..., 3] = smooth_mask(m) * 255
    for fy in (24, 70):
        band = (np.abs(y - fy) < 2.0) & (np.abs(x - W / 2) <= wdt / 2 + 1.6)
        spr[..., :3] = np.where(band[..., None], ramp_col(ramp('#0e2440', '#2a5480', '#7aa4cc'), sh), spr[..., :3]); spr[..., 3] = np.where(band, 255, spr[..., 3])
    mouth_ = (y > L - 3) & (np.abs(x - W / 2) <= half - 1.2)
    spr[..., :3] = np.where(mouth_[..., None], hexc('#060a10'), spr[..., :3])
    rust = np.clip(noise(y.shape, 1.0, seed) - 0.2, 0, 1) * np.clip((y - 30) / L, 0, 1) * m
    lerp_rgb(spr, '#7a4020', rust * 0.5)
    return outline(spr, '#0a1420', width=0.65)


def flange(w=18, h=8, seed=1):
    """a loose pipe flange lying on the bottom: a thick steel ring seen edge-on, its bolt holes"""
    y, x = grid(h, w)
    m = (x > 0.6) & (x < w - 0.6) & (y > 1.0) & (y < h - 0.6)
    sh = np.clip(0.65 - 0.5 * (y - h / 2) / h, 0, 1)
    spr = np.zeros(y.shape + (4,), np.float32)
    spr[..., :3] = ramp_col(STEEL, sh); spr[..., 3] = smooth_mask(m) * 255
    for k in range(4):
        bx = 2.5 + k * (w - 5) / 3
        ellipse_soft(spr, bx, h / 2 + 0.3, 0.8, 1.2, '#1a2026', 255)
    lerp_rgb(spr, '#8a4a20', np.clip(noise(y.shape, 0.8, seed) - 0.1, 0, 1) * 0.6 * m)
    return outline(spr, '#0e1216', width=0.6)


def valve(h=40, seed=1):
    """a gate valve standing on the bottom: its body, the bonnet, the stem and a handwheel on top"""
    w = 22
    out = canvas(w + 4, h)
    cx = (w + 4) / 2
    body = canvas(w, 18)
    yy, xx = grid(18, w)
    m = (((xx - w / 2) / (w / 2 - 0.6)) ** 2 + ((yy - 10) / 8) ** 2 <= 1) | ((np.abs(yy - 11) < 4.5) & (xx > 0.6) & (xx < w - 0.6))
    b = A.mask_sprite(m, PAINT, '#0a1420', soft=1.4, ambient=0.3, hl_t=0.96)
    bon = A.mask_sprite((np.abs(grid(16, 8)[1] - 4) < 3.2), PAINT, '#0a1420', soft=0.8, ambient=0.3, hl_t=0.96)
    A.stroke(out, [(cx, 6), (cx, h - 22)], 1.2, '#0e1216', 255, scale=1.0)
    A.stroke(out, [(cx, 6), (cx, h - 22)], 0.7, '#c4ccd2', 255, scale=1.0)
    paste(out, bon, cx - 5, h - 34)
    paste(out, b, cx - w / 2 - 1, h - 19.5)
    wheel = canvas(18, 6)
    ellipse_soft(wheel, 9, 3, 8, 2.2, '#0e1216', 255); ellipse_soft(wheel, 9, 3, 7.2, 1.6, '#c42a1a', 255); ellipse_soft(wheel, 9, 3, 5.6, 0.9, '#0e1216', 255)
    for k in range(4):
        A.stroke(wheel, [(9, 3), (9 + 6.6 * np.cos(k * np.pi / 4 * 2), 3 + 1.4 * np.sin(k * np.pi / 4 * 2))], 0.5, '#c42a1a', 255, scale=1.0)
    paste(out, wheel, cx - 9, 2)
    return trim(out)


def pump_column(h, seed=1, w=22):
    """a pump's riser standing in the well: lengths of painted pipe bolted flange to flange"""
    h = int(round(h))
    out = canvas(w + 6, h)
    y, x = grid(h, w + 6)
    cx = (w + 6) / 2
    half = w / 2 - 2.5
    m = (np.abs(x - cx) <= half) & (y > 0.6) & (y < h - 0.6)
    u = (x - cx) / half
    sh = np.clip(0.6 - 0.45 * u - 0.15 * u ** 4, 0, 1)
    out[..., :3] = ramp_col(PAINT, sh); out[..., 3] = smooth_mask(m) * 255
    for fy in list(np.arange(h - 6, 4, -22)) + [3.0]:
        band = (np.abs(y - fy) < 2.2) & (np.abs(x - cx) <= w / 2)
        out[..., :3] = np.where(band[..., None], ramp_col(ramp('#0e2440', '#2a5480', '#7aa4cc'), sh * 0.8 + 0.1), out[..., :3]); out[..., 3] = np.where(band, 255, out[..., 3])
        for b in range(4):
            disc(out, cx - w / 2 + 2 + b * (w - 4) / 3, fy, 0.75, '#c4ccd2', 255)
    rust = np.clip(noise(y.shape, 1.2, seed) - 0.25, 0, 1) * (out[..., 3] > 0)
    lerp_rgb(out, '#7a4020', rust * 0.45)
    return outline(out, '#0a1420', width=0.65)


def T_pump():
    far = pump_far()
    R = RS(1511)
    mid = wide()
    motes(mid, 140, ['#c4d4da', '#ffffff', '#8aa0a8'], 1512, r=(0.3, 0.9), a=(100, 190))
    bubble_chain(mid, 12, 1513, y0=50, y1=GY - 10, r=(1, 3), alpha=0.6)
    for k in range(4):
        put(mid, TT.paper_shred(1520 + k, R.uniform(6, 9), R.uniform(4, 6)), R.uniform(0, WT), R.uniform(26, GY - 30), 0.75)
    mid = crop(mid)
    floor = wall([(1.6, ramp('#2e3832', '#46524a', '#626e66', n=3), pat_slime), (10, CONC, pat_concrete), (40, SOIL, pat_soil)], True, seed=1541, bumps=0.3, out='#0e1418')
    def extra(c3, R, rim_b, surf):                         # the steel grating walkway above, light through it
        for off in (0, WT, 2 * WT):
            for i in range(int(WT / 3)):
                fill_rect(c3, off + i * 3 + 1.0, 1.0, off + i * 3 + 2.2, 5.2, '#e8eef0', 200)
    ceil = surf_ceil(1551, ramp('#1a2026', '#323a42', '#4e5a64', '#6e7a84', n=4), crown_h=6.6, air=('#2a363c', '#46545c', '#64747c'),
                     mirror='#e0eaee', out='#121a20', extra=extra)
    obs = {'low': [flange(18, 8, 1), concrete_chunk(20, 10, 2)],
           'tall': [valve(40, 1), valve(46, 2)],
           'hang': [bell_pipe(1, 16), bell_pipe(2, 13)],
           'float': [impeller(24, 1), impeller(20, 2)],
           'huge': [tower(lambda h: pump_column(h, 3, 22))]}
    return dict(far=far, mid=mid, floor=floor, ceil=ceil, obs=obs, coin='drop', special='soap')


# ------------------------------------------------------------------ the sewers' hazards (in common.webp)
def sludge_drop():
    """a blob of sludge swelling on the crown and letting go"""
    w, h = 13, 14
    y, x = grid(h, w)
    cx = w / 2 - 0.5; r = 5.0; yt = h - 1 - r
    m = (x - cx) ** 2 + (y - yt) ** 2 <= r * r
    t = np.clip((yt - y) / (yt - 0.6), 0, 1)
    m |= (y < yt) & (y > 0.6) & (np.abs(x - cx) <= r * (1 - t) ** 1.1 + 0.6 * np.sin(y * 1.3))
    spr = A.mask_sprite(m, D.SLUDGE, D.SLUDGE_OUT, soft=1.0, ambient=0.35, hl_t=0.95)
    speckle(spr, 3, 25, ['#c8b07a', '#2a1c0c'], r=(0.2, 0.4), a=160)
    return spr


def sludge_splat(w=26, h=9):
    """the drop landed: a flat splat of sludge on the floor, spattered at its edges"""
    R = RS(7)
    y, x = grid(h, w)
    top = h - 3.8 - 1.0 * np.sin(x * 0.5 + 1) * np.sin(x * 0.19) - 0.8 * np.abs(np.sin(x * 0.8))
    m = (y >= top) & (y <= h - 0.6) & (np.abs(x - w / 2) <= w / 2 - 1.2 - 0.8 * np.sin(y * 3))
    spr = A.mask_sprite(m, D.SLUDGE, D.SLUDGE_OUT, soft=1.0, ambient=0.4, hl_t=0.96)
    return spr


def rebar_spike(size='s', seed=5):
    """a broken lump of concrete pushed up out of the floor, a rusty rebar sticking up out of it"""
    R = RS(seed + (7 if size == 't' else 0))
    w, h = (15, 21) if size == 's' else (17, 33)
    out = canvas(w, h)
    bh = h * 0.45
    y, x = grid(bh, w)
    n = 6; ang = np.arctan2(y - bh, x - w / 2); rr = np.sqrt(((x - w / 2) / (w / 2 - 0.8)) ** 2 + ((y - bh) / (bh - 0.8)) ** 2)
    k = (ang + np.pi) / np.pi * n; rad = R.uniform(0.7, 1.0, n + 2)
    i0 = np.clip(np.floor(k).astype(int), 0, n); f = k - np.floor(k)
    m = rr <= rad[i0] * (1 - f) + rad[i0 + 1] * f
    base = A.mask_sprite(m & (y <= bh - 0.6), CONC, '#14160f', soft=0.8, ambient=0.35, hl_t=0.99)
    speckle(base, seed, int(w * bh * 0.4), ['#c8c4b0', '#5a5a50'], r=(0.25, 0.6), a=190)
    for (x0, x1, top) in ((w * 0.45, w * 0.52, 0.8), (w * 0.62, w * 0.75, h * 0.3)):
        pts = [(x0, h - bh * 0.5), (x1, top)]
        A.stroke(out, pts, 1.8, '#1a0c06', 255, scale=1.0)
        A.stroke(out, pts, 1.2, '#9a4a20', 255, scale=1.0)
        for s in range(5):                                 # its ribs
            q = 0.2 + s * 0.15; rx = x0 + (x1 - x0) * q; ry = h - bh * 0.5 + (top - h + bh * 0.5) * q
            A.stroke(out, [(rx - 0.8, ry + 0.3), (rx + 0.8, ry - 0.3)], 0.35, '#5a2410', 255, scale=1.0)
    paste(out, base, -1, h - bh - 1)
    rows = np.nonzero(out[..., 3].max(axis=1) > 20)[0]
    return out[:rows.max() + 1]


def nut_shot():
    """what flies at you down the sewer, spinning: a rusty hex nut"""
    w, h = 13, 13
    out = canvas(w, h)
    y, x = grid(11, 11)
    a = np.arctan2(y - 5, x - 5); r = np.sqrt((x - 5) ** 2 + (y - 5) ** 2)
    hexr = 4.8 / np.cos(np.mod(a, np.pi / 3) - np.pi / 6)
    m = (r <= hexr) & (r >= 1.9)
    s = A.mask_sprite(m, ramp('#221e1a', '#46423c', '#6e6a62', '#9a968c', '#c8c4ba'), '#100c08', soft=0.6, ambient=0.35, hl_t=0.95)
    I = inner(s)
    lerp_rgb(I, '#9a4a1c', np.clip(noise(I.shape[:2], 0.6, 3) - 0.1, 0, 1) * 0.55 * (I[..., 3] > 0))
    paste(out, s, 0, 0)
    return out


def hazards():
    return {'hz_drop_sludge': sludge_drop(), 'hz_puddle_sludge': sludge_splat(), 'hz_spike_rebar_s': rebar_spike('s'),
            'hz_spike_rebar_t': rebar_spike('t'), 'hz_shot_nut': nut_shot()}
