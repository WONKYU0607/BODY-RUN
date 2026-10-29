# Stage 3, the river and the estuary (places 1-8): below the outfall (river), a riffle (riffle), the weed beds (weeds),
# the weir and its fish ladder (weir), a deep pool (pool), under the bridge (bridge), the estuary reeds (reeds), the
# mudflat (mudflat). All under water, swimming. Each: a far layer of the water and what is far off in it, a mid layer
# (fish far off, bits drifting, bubbles), the bed in section, the surface from below, and what is in the way.
import numpy as np
from art import (H, SC, px, grid, canvas, ramp, ramp_col, hexc, paint, ellipse_mask, outline, paste, over, blur, disc,
                 ellipse_soft, inner, smooth_mask, fill_rect)
import anatomy as A
from tiles import WT, GY, FH, FY0, CH, TAU, wide, crop, put, per_sin, gradient, haze, pcells, wall, band_line, spots
from themes import three, drift, tower, stack, hang_len, bubble, flip_v
from variants import noise
import s3lib as L
from s3lib import (put_wrap, faded, scaled, water_far, sky_ceil, foam_extra, bed, things_on_bed, ripples_surface, pat_sand,
                   pat_mud, pat_rock, stone, boulder, rock_spire, fish, school, ribbons, ribbons_hang, weed_far, crab,
                   shell_sprite, bubbles_sprite, lerp_rgb, mul, motes, bubble_chain, pat_gravel, pat_soil,
                   pebble_surface, silt, trim, blob_mask, mass, speckle, STONES, lump)
import sewer as SW
import drains as D
import plant as PL
from s2lib import pat_concrete

RS = np.random.RandomState
GRAVEL = ramp('#4a4428', '#76704a', '#a49e74', '#c8c29a', '#e2dcb8', n=5)
SOIL_D = ramp('#2a2618', '#443e28', '#5e563a', '#7a7050', n=4)
BARK = ramp('#2a1a0e', '#4a3220', '#6e5034', '#94744e', '#b89a72')
CONC = ramp('#4a4e4a', '#6e746e', '#949a92', '#b8bcb2', '#d8dad0')


def minnow(seed):
    return fish(14, 5.5, seed, back='#3a5a4a', side='#9ab8a8', belly='#eef4ec', stripes=1, stripe_col='#2a3a34', fin='#8aa89a')


def sweetfish(seed):                                       # 은어: olive back, a yellow spot behind the gill
    f = fish(22, 7, seed, back='#4a5a2a', side='#a8b48a', belly='#f4f4e4', fin='#c8b45a', out='#141a08')
    I = f
    ellipse_soft(I, 6.5, 3.6, 1.6, 1.0, '#ffd23a', 220)
    return f


def log(w=30, h=9, seed=1):
    """a sunken log lying on the bed: bark, a cut end showing its rings"""
    R = RS(seed)
    y, x = grid(h, w)
    m = (np.abs(y - h / 2) <= h / 2 - 0.6) & (x > 0.6) & (x < w - 0.6)
    spr = A.mask_sprite(m, BARK, '#140a04', soft=1.2, ambient=0.3, hl_t=0.98)
    I = inner(spr)
    lerp_rgb(I, '#1a0e06', ((np.sin(x * 1.3 + 2 * np.sin(y * 0.8)) > 0.75) & m) * 0.45)       # the bark's furrows
    m2 = ellipse_mask(h * 0.55, h - 1.2)
    end = A.mask_sprite(m2, ramp('#6a4a28', '#a07a4a', '#c8a06a', '#e4c896'), '#2a1a0a', soft=0.8, ambient=0.5, hl=False)
    E = inner(end); yy, xx = grid(E.shape[0] / SC, E.shape[1] / SC)
    rr = np.hypot((xx - E.shape[1] / SC / 2) / (h * 0.27), (yy - E.shape[0] / SC / 2) / (h / 2 - 0.6))
    lerp_rgb(E, '#5a3a1a', (np.sin(rr * 18) > 0.6) * (E[..., 3] > 0) * 0.5)
    paste(spr, end, -0.2, 0.0)
    for k in range(int(w / 6)):                             # weed and slime growing on it
        ellipse_soft(I, R.uniform(3, w - 2), R.uniform(0.6, 2.4), R.uniform(1, 2.5), 0.6, '#4a7a3a', 150)
    return spr


def trunk(h, seed=1, w=16):
    """a drowned tree trunk standing up from the bed, its broken top, a branch stub"""
    h = int(round(h))
    y, x = grid(h, w)
    t = y / h
    half = (w / 2 - 1.2) * (0.62 + 0.38 * t) + 0.6 * np.sin(y * 0.4 + seed)
    top = 2.5 + 2.5 * (0.5 + 0.5 * np.sin(x * 2.1 + seed))
    m = (np.abs(x - w / 2) <= half) & (y >= top)
    spr = A.mask_sprite(m, BARK, '#140a04', soft=1.3, ambient=0.3, hl_t=0.98)
    I = inner(spr)
    lerp_rgb(I, '#1a0e06', ((np.sin(x * 2.6 + 0.4 * np.sin(y * 0.5)) > 0.7) & m) * 0.45)
    o = canvas(w + 10, h)
    paste(o, spr, 4, 0)
    A.stroke(o, [(w / 2 + 4 + half_mid(w), h * 0.35), (w + 8, h * 0.28)], 2.2, '#140a04', 255, scale=1.0)
    A.stroke(o, [(w / 2 + 4 + half_mid(w), h * 0.35), (w + 8, h * 0.28)], 1.5, '#6e5034', 255, scale=1.0)
    return trim(o)


def half_mid(w):
    return w / 2 - 2.0


def willow_hang(seed=1):
    """a willow's drooping branch dipped into the river from the bank: a stem, thin leaves along it"""
    Lh = hang_len()
    R = RS(seed)
    W = 26
    o = canvas(W, Lh)
    for b in range(3):
        x0 = W / 2 + (b - 1) * 3; ph = R.uniform(0, 6); l = Lh * R.uniform(0.75, 1.0)
        pts = [(x0 + 3 * np.sin(t * 2 + ph) * t, t * l) for t in np.linspace(0, 1, 50)]
        for i in range(49):
            A.stroke(o, [pts[i], pts[i + 1]], 0.9, '#2a1a0a', 255, scale=1.0)
            A.stroke(o, [pts[i], pts[i + 1]], 0.5, '#6a5a2a', 255, scale=1.0)
        for i in range(2, 49, 2):
            px_, py_ = pts[i]; s_ = 1 if i % 4 else -1
            lp = [(px_, py_), (px_ + s_ * 3.2, py_ + 2.4), (px_ + s_ * 4.4, py_ + 5.0)]
            A.stroke(o, lp, 1.3, '#1e3a10', 255, scale=1.0)
            A.stroke(o, lp, 0.85, ['#5a9a2a', '#7ab43a', '#4a8a24'][i % 3], 255, scale=1.0)
    return trim(o)[:px(Lh)]


def step_block(h=40, w=22, seed=1):
    """a concrete block of the fish ladder's steps: a cut face, its aggregate, a green waterline of algae"""
    y, x = grid(h, w)
    m = (x > 0.6) & (x < w - 0.6) & (y > 0.6)
    spr = A.mask_sprite(m, CONC, '#1a1c1a', soft=0.5, ambient=0.4, hl_t=0.995)
    I = inner(spr)
    n = noise(y.shape, 0.6, seed)
    lerp_rgb(I, '#2a2e2a', (n > 0.45) * m * 0.35)
    lerp_rgb(I, '#3a6a2a', (y < 5) * m * 0.55)
    lerp_rgb(I, '#ffffff', (y < 1.6) * m * 0.25)
    return spr


def pier(h, seed=1, w=26):
    """a concrete pier from the bed up: its form-work lines, stains, a skirt of weed"""
    h = int(round(h))
    y, x = grid(h, w)
    m = (np.abs(x - w / 2) <= w / 2 - 1.2) & (y > 0.6)
    spr = A.mask_sprite(m, CONC, '#1a1c1a', soft=0.9, ambient=0.35, hl_t=0.99)
    I = inner(spr)
    lerp_rgb(I, '#3a3e3a', (np.abs(np.mod(y, 12) - 6) < 0.25) * m * 0.5)
    n = noise(y.shape, 1.2, seed)
    lerp_rgb(I, '#4a5a3a', np.clip(n * 1.5, 0, 1) * m * 0.3)
    lerp_rgb(I, '#2e5a24', (y > h - 9) * m * 0.45)
    return spr


def hook_line(seed=1):
    """a fishing line hanging down from the surface: a float at the top, a sinker, a hook with bait"""
    Lh = hang_len()
    o = canvas(14, Lh)
    A.stroke(o, [(7, 0), (7.4, Lh - 9)], 0.22, '#f0f0f0', 230, scale=1.0)
    m = ellipse_mask(3.4, 3.4)
    s = A.mask_sprite(m, ramp('#3a3a3a', '#6a6a6a', '#9a9a9a', '#cacaca'), '#101010', soft=0.8, ambient=0.4)
    paste(o, s, 5.6, Lh - 18)
    hk = [(7.4, Lh - 9), (7.4, Lh - 3.5), (6.6, Lh - 1.4), (4.8, Lh - 1.6), (4.4, Lh - 3.4)]
    A.stroke(o, hk, 0.7, '#202020', 255, scale=1.0)
    A.stroke(o, hk, 0.4, '#c0c4c8', 255, scale=1.0)
    for k in range(3):                                      # a worm on it
        ellipse_soft(o, 7.6 + 0.6 * np.sin(k), Lh - 7.5 + k * 1.6, 1.1, 0.9, '#c86a6a', 240)
    return trim(o)[:px(Lh)]


def shrimp(w=14, h=7, seed=1):
    """a little shrimp: a curled see-through body in segments, feelers forward"""
    y, x = grid(h, w)
    cx, cy = w * 0.55, h * 0.95
    rr = np.hypot((x - cx) / (w * 0.42), (y - cy) / (h * 0.85))
    ang = np.arctan2(cy - y, x - cx)
    m = (rr <= 1.0) & (rr >= 0.45) & (ang > 0.15) & (ang < 2.9)
    spr = A.mask_sprite(m, ramp('#7a5a4a', '#b48a74', '#e0bca4', '#f8e4d4'), '#3a2014', soft=0.9, ambient=0.45, hl_t=0.93)
    I = inner(spr)
    lerp_rgb(I, '#6a3a24', (np.sin(ang * 14) > 0.7) * m * 0.4)
    spr[..., 3] *= 0.9
    o = canvas(w + 6, h + 2)
    paste(o, spr, 5, 1)
    for k in range(2):
        A.stroke(o, [(5.5 + w * 0.12, 2 + h * 0.45), (2.5, 1 + k), (0.3, 0.4 + k * 1.5)], 0.18, '#3a2014', 230, scale=1.0)
    return trim(o)


def oyster_clump(w=24, h=11, seed=1):
    """oysters grown together into a rough grey clump"""
    R = RS(seed)
    o = canvas(w, h)
    for k in range(7):
        sw, sh = R.uniform(8, 12), R.uniform(4, 6)
        y, x = grid(sh, sw)
        m = ((x - sw / 2) / (sw / 2 - 0.5)) ** 2 + ((y - sh / 2) / (sh / 2 - 0.5)) ** 2 <= 1
        s = A.mask_sprite(m, ramp('#3a3a34', '#626258', '#8e8c80', '#bab6a8', '#e0dcd0'), '#141410', soft=0.7, ambient=0.35, hl_t=0.96)
        I = inner(s); lerp_rgb(I, '#2a2a24', (np.sin((x + y) * 3.4) > 0.6) * m * 0.4)
        import cv2
        Mr = cv2.getRotationMatrix2D((s.shape[1] / 2, s.shape[0] / 2), R.uniform(-35, 35), 1.0)
        s = cv2.warpAffine(s, Mr, (s.shape[1], s.shape[0]))
        paste(o, s, R.uniform(0, w - sw), h - sh - R.uniform(0, h - sh) * (k / 7))
    return trim(o)


def mud_mound(h=40, w=24, seed=1):
    """a mound of mud with a mudskipper perched on top"""
    o = canvas(w, h)
    mh = h - 9
    y, x = grid(mh, w)
    m = (np.abs(x - w / 2) <= (w / 2 - 0.8) * (0.35 + 0.65 * np.clip(y / mh, 0, 1) ** 0.6)) & (y > 0.6)
    s = A.mask_sprite(m, ramp('#2a2218', '#4a3e2c', '#6e604a', '#94866c', '#b8ac90'), '#120e08', soft=1.2, ambient=0.3, hl_t=0.99)
    I = inner(s)
    lerp_rgb(I, '#6a5a44', (noise(y.shape, 0.5, seed) > 0.4) * m * 0.3)
    for k in range(3):
        ellipse_soft(I, w / 2 + (k - 1) * 4, mh * (0.4 + 0.2 * k), 0.9, 0.6, '#0e0a06', 230)        # crab holes
    paste(o, s, 0, 9)
    g = fish(19, 7.5, seed + 3, back='#4a4030', side='#8a7a5a', belly='#e0d4b4', kind='goby', spots_col='#2a7aa0', fin='#7a6a4a', out='#1a140a')
    paste(o, g, w / 2 - 9, 9.5 - g.shape[0] / SC)
    return trim(o)


# ================================================================== 1. below the outfall
def river_far(seed=3101, cols=('#b4e0cc', '#86c4aa', '#5e9e84', '#3e7462')):
    R = RS(seed)
    far = water_far(cols, seed, caust=0.5, shafts=8)
    c3 = three(far)
    weed_far(c3, 60, seed + 3, ['#3a7a4a', '#4a8a52', '#2e6a40'])
    for j in range(2):                                     # the outfall's headwall going away behind, its pipe still pouring a cloudy plume
        x0 = j * WT / 2 + 380
        g = canvas(110, 90)
        fill_rect(g, 0, 0, 110, 90, '#7a8a80', 255)
        gy, gx = grid(90, 110)
        g[..., :3] *= (0.85 + 0.15 * noise(gy.shape, 1.0, seed + j))[..., None]
        lerp_rgb(g, '#2a3a2a', (np.clip(np.sin(gx * 0.9 + 3 * noise(gy.shape, 3.0, seed + 50 + j)), 0, 1) ** 8) * 0.35)   # water streaks
        lerp_rgb(g, '#3a6a2a', np.clip((gy - 70) / 20, 0, 1) * np.clip(noise(gy.shape, 0.8, seed + 60 + j) + 0.3, 0, 1) * 0.5)   # weed at its foot
        m_ = PL.mouth(48, 44, ramp('#4a5a52', '#9aaaa0', '#d4e0d8', n=3), deep=('#020806', '#0a1a14', '#1a3428'))
        paste(g, m_, 55 - m_.shape[1] / SC / 2, 50 - m_.shape[0] / SC / 2)
        g = outline(g, '#1a2a22')
        put_wrap(c3, faded(g, cols[2], 0.55, 0.5), x0, 60)
        for k in range(16):
            for off in (0, WT, 2 * WT):
                ellipse_soft(c3, x0 + 55 + off + 30 + k * 7 + R.uniform(-3, 3), 112 + R.uniform(-8, 8) + k * 0.6, 12 + k * 1.5, 7 + k * 0.6, '#eef8f2', int(60 - k * 3))
    far = crop(c3)
    silt(far, 140, ('#5a5a3a', '#8a8458', '#b4ac7a', '#d4ca9a'), seed + 4, k=0.9)
    c3 = three(far)
    for k in range(180):
        g = stone(R.uniform(1.6, 4), R.uniform(1.2, 3), seed + 50 + k)
        put_wrap(c3, g, R.uniform(0, WT), R.uniform(142, 152))
    drift(c3, 90, ['#ffffff', '#e8fff4', '#c4ecd8'], seed + 5, y0=20, y1=GY - 6, a=140)
    far = crop(c3)
    haze(far, cols[1], 0.08)
    return far


def mid_fish(seed, n, maker, a=0.5, y0=30, y1=GY - 40, extra=None):
    R = RS(seed)
    mid = wide()
    for k in range(n):
        g = maker(seed + k); g = scaled(g, R.uniform(0.45, 0.7)); g[..., 3] *= a
        put(mid, g, R.uniform(0, WT), R.uniform(y0, y1))
    motes(mid, 100, ['#ffffff', '#e8fff4', '#c4ecd8'], seed + 1, r=(0.3, 0.8), a=(110, 200))
    bubble_chain(mid, 6, seed + 2, r=(1, 2), alpha=0.5)
    if extra:
        extra(mid, R)
    return crop(mid)


def T_river():
    far = river_far()
    mid = mid_fish(3111, 8, minnow)
    floor = bed(3141, GRAVEL, SOIL_D, out='#141008', surface=lambda c3, e, e0, top: pebble_surface(c3, e, e0, top, seed=3142, n=170, r=(0.8, 2.6)))
    ceil = sky_ceil(3151)
    obs = {'low': [stone(24, 11, 1), log(30, 9, 2)],
           'tall': [PL.reeds(42, 11, 20), PL.reeds(48, 12, 22)],
           'hang': [ribbons_hang(3, 12), willow_hang(4)],
           'float': [minnow(5), fish(20, 8, 6, back='#3a4a3a', side='#8aa08a', belly='#e8eee4', fin='#7a907a')],
           'huge': [tower(lambda h: rock_spire(h, 7, 26))]}
    return dict(far=far, mid=mid, floor=floor, ceil=ceil, obs=obs, coin='drop', special='pearl')


# ================================================================== 2. a riffle: shallow, quick, bright
def riffle_far(seed=3201, cols=('#d8f6ee', '#a8e2d6', '#7cc6b6', '#529e8e')):
    R = RS(seed)
    far = water_far(cols, seed, caust=0.85, shafts=10)
    y, x = grid(H, WT)
    st = np.clip(np.sin(x * TAU * 3 / WT * 7 + y * 0.35 + 3 * np.sin(y * 0.11)), 0, 1) ** 12 * 0.12      # the quick water's streaks
    lerp_rgb(far, '#ffffff', st * np.clip(1 - y / 150, 0, 1))
    c3 = three(far)
    for k in range(70):                                     # cobbles heaped along the far bed, bigger in front
        sw = R.uniform(6, 16); s = stone(sw, sw * R.uniform(0.6, 0.8), seed + 10 + k)
        put_wrap(c3, faded(s, cols[2], 0.35, 0.85), R.uniform(0, WT), R.uniform(128, 146))
    for k in range(40):
        rr = int(R.uniform(1, 3)); b = bubble(rr, seed + 200 + k); b[..., 3] *= 0.6
        put_wrap(c3, b, R.uniform(0, WT), R.uniform(30, 120))
    far = crop(c3)
    silt(far, 146, ('#6a6448', '#8e8662', '#b4ac86', '#d8d0aa'), seed + 4, k=0.8)
    return far


def T_riffle():
    far = riffle_far()
    mid = mid_fish(3211, 6, minnow, a=0.45, extra=lambda mid, R: [put(mid, bubbles_sprite(8, 3220 + k, 10, 30, (1, 2), 0.55), R.uniform(0, WT), R.uniform(30, 110)) for k in range(14)])
    COB = [STONES[0], STONES[1], STONES[2]]
    floor = bed(3241, ramp('#4a4636', '#6e6852', '#948e74', '#bab49a', '#dcd6bc', n=5), SOIL_D, out='#141008',
                surface=things_on_bed([stone(6 + k % 4, 3.6 + k % 3, 3250 + k, COB[k % 3]) for k in range(9)], 120, 3243, sink=0.6))
    ceil = sky_ceil(3251, extra=foam_extra(110, 3252))
    obs = {'low': [stone(24, 12, 21, STONES[2]), stone(20, 11, 22, STONES[1])],
           'tall': [PL.cairn(42, 23, 22), PL.cairn(48, 24, 20)],
           'hang': [willow_hang(25), willow_hang(26)],
           'float': [sweetfish(27), minnow(28)],
           'huge': [tower(lambda h: rock_spire(h, 29, 28, STONES[2]))]}
    return dict(far=far, mid=mid, floor=floor, ceil=ceil, obs=obs, coin='drop', special='pearl')


# ================================================================== 3. the weed beds
WEED_C = [('#2e7424', '#3a8a2a', '#4ea036'), ('#3e6a1a', '#5a8a24', '#7aa834'), ('#1e5a3a', '#2e7a4a', '#46965e')]


def snail_stone(seed=1):
    """river snails (다슬기) clinging to a stone"""
    o = canvas(24, 13)
    s = stone(22, 10, seed, STONES[1])
    paste(o, s, 0, 13 - s.shape[0] / SC)
    R = RS(seed)
    for k in range(4):
        c = shell_sprite(4.2, 6.5, seed + k, cols=('#1a1610', '#3a3222', '#5e523a', '#8a7a5a', '#b4a482'), out='#0a0806', kind='cone')
        import cv2
        Mr = cv2.getRotationMatrix2D((c.shape[1] / 2, c.shape[0] / 2), R.uniform(-60, 60), 1.0)
        c = cv2.warpAffine(c, Mr, (c.shape[1], c.shape[0]))
        paste(o, c, 3 + k * 4.5, R.uniform(0.5, 3))
    return trim(o)


def weeds_far(seed=3301, cols=('#c4ecc0', '#94d090', '#64a866', '#3e7e46')):
    R = RS(seed)
    far = water_far(cols, seed, caust=0.45, shafts=9)
    c3 = three(far)
    for layer, (n, a, hh) in enumerate([(80, (0.25, 0.4), (60, 130)), (70, (0.45, 0.65), (40, 100))]):
        weed_far(c3, n, seed + 3 + layer, ['#2e6a2a', '#3e7e34', '#4e9040'] if layer else ['#5a9a5a', '#6aaa66', '#4e8a52'], h=hh, a=a, w=1.6 if layer else 1.2)
    far = crop(c3)
    silt(far, 142, ('#4a5a2e', '#6e7a44', '#94a066', '#b8c08a'), seed + 4, k=0.9)
    haze(far, cols[1], 0.06)
    return far


def T_weeds():
    far = weeds_far()
    mid = mid_fish(3311, 10, lambda s: school(6, 14, 6, s, minnow, (34, 16)), a=0.45)
    floor = bed(3341, ramp('#3a3a1e', '#5a5a32', '#7e7c4c', '#a4a06e', '#c8c294', n=5), SOIL_D, pat_top=pat_sand, out='#121008',
                surface=things_on_bed([ribbons(7 + k % 3, 3350 + k, 8, WEED_C[k % 3], n=4, wid=0.8) for k in range(6)], 90, 3343, sink=0.2))
    ceil = sky_ceil(3351)
    obs = {'low': [snail_stone(31), snail_stone(32)],
           'tall': [ribbons(44, 33, 20, WEED_C[0]), ribbons(50, 34, 22, WEED_C[1])],
           'hang': [ribbons_hang(35, 12, WEED_C[2]), ribbons_hang(36, 14, WEED_C[0])],
           'float': [school(5, 14, 6, 37, minnow, (20, 10)), minnow(38)],
           'huge': [tower(lambda h: ribbons(h, 39, 26, WEED_C[1], n=14, wid=2.4))]}
    return dict(far=far, mid=mid, floor=floor, ceil=ceil, obs=obs, coin='drop', special='pearl')


# ================================================================== 4. the weir and its fish ladder
def weir_far(seed=3401, cols=('#b8dede', '#8cc0c4', '#62989e', '#40727a')):
    R = RS(seed)
    far = water_far(cols, seed, caust=0.5, shafts=7)
    c3 = three(far)
    for j in range(2):                                      # the weir's face across the river, its stepped fish ladder, water over its lip
        x0 = j * WT / 2 + 100
        g = canvas(420, 130)
        y, x = grid(130, 420)
        face = (y > 20)
        steps = np.zeros_like(face)
        for k in range(7):                                  # the ladder: steps going down to the right
            sx = 250 + k * 22; sy = 20 + k * 14
            steps |= (x >= sx) & (x < sx + 22) & (y >= sy)
        m = face & ((x < 250) | steps)
        g[..., :3] = ramp_col(CONC, np.clip(0.55 + 0.25 * noise(y.shape, 1.0, seed + j) - 0.2 * (y / 130), 0, 1))
        g[..., 3] = m * 255.0
        mul(g, 1 + 0.12 * noise(y.shape, 2.5, seed + 30 + j))
        stain = np.clip(noise(y.shape, 1.2, seed + 40 + j) * 2 - 0.4, 0, 1) * np.clip(1 - (y - 20) / 80, 0, 1)
        lerp_rgb(g, '#2a3a2a', (np.clip(np.sin(x * 0.9 + 3 * noise(y.shape, 3.0, seed + 50 + j)), 0, 1) ** 8) * m * 0.35)   # water streaks down it
        lerp_rgb(g, '#3a4a2e', stain * m * 0.3)
        lerp_rgb(g, '#2a2e2a', (np.abs(np.mod(x, 40) - 20) < 0.3) * m * 0.4)
        lerp_rgb(g, '#3a6a2a', ((y > 20) & (y < 26)) * m * 0.5)
        RR = RS(seed + 60 + j)
        for k in range(500):
            px_, py_ = RR.uniform(1, 419), RR.uniform(22, 129)
            if m[int(py_ * SC), int(px_ * SC)]:
                ellipse_soft(g, px_, py_, RR.uniform(0.3, 0.8), RR.uniform(0.2, 0.5), '#2a2c28', 120)
        for k in range(7):
            sx = 250 + k * 22; sy = 20 + k * 14
            lerp_rgb(g, '#e8f8ff', ((x >= sx) & (x < sx + 22) & (y >= sy) & (y < sy + 3)) * 0.5)
        g = outline(g, '#1a1e1a')
        put_wrap(c3, faded(g, cols[2], 0.45, 0.75), x0, 30)
    far = crop(c3)
    for j in range(2):                                      # water pouring over the lip
        D.falling_water(far, (j * WT / 2 + 100 + 60) % WT, 50, 180, 150, seed + 20 + j, k=0.45)
    silt(far, 144, ('#5a5a46', '#7e7c62', '#a4a284', '#c8c6a8'), seed + 4, k=0.85)
    c3 = three(far)
    drift(c3, 80, ['#ffffff', '#e8fff4'], seed + 5, y0=20, y1=GY - 6, a=130)
    return crop(c3)


def T_weir():
    far = weir_far()
    mid = mid_fish(3411, 7, sweetfish, a=0.45)
    floor = bed(3441, CONC, SOIL_D, pat_top=pat_concrete, out='#141614', top_th=7,
                surface=lambda c3, e, e0, top: pebble_surface(c3, e, e0, top, seed=3442, n=90, r=(0.8, 2.2)))
    ceil = sky_ceil(3451, extra=foam_extra(70, 3452))
    obs = {'low': [SW.concrete_chunk(24, 12, 41), SW.concrete_chunk(20, 11, 42)],
           'tall': [step_block(40, 22, 43), step_block(46, 20, 44)],
           'hang': [D.water_column(45, 14), D.water_column(46, 18)],
           'float': [sweetfish(47), sweetfish(48)],
           'huge': [tower(lambda h: pier(h, 49, 26))]}
    return dict(far=far, mid=mid, floor=floor, ceil=ceil, obs=obs, coin='drop', special='pearl')


# ================================================================== 5. a deep pool
def pool_far(seed=3501, cols=('#6aa8a4', '#467e82', '#2a5a62', '#163a44')):
    R = RS(seed)
    far = water_far(cols, seed, caust=0.25, shafts=6, deep=True)
    c3 = three(far)
    for k in range(9):                                      # sunken logs and branches, far off in the gloom
        g = log(R.uniform(40, 80), R.uniform(8, 13), seed + 10 + k)
        import cv2
        Mr = cv2.getRotationMatrix2D((g.shape[1] / 2, g.shape[0] / 2), R.uniform(-25, 25), 1.0)
        g = cv2.warpAffine(g, Mr, (g.shape[1], g.shape[0]))
        put_wrap(c3, faded(g, cols[2], 0.6, 0.7), R.uniform(0, WT), R.uniform(100, 135))
    for k in range(6):
        g = trunk(R.uniform(70, 120), seed + 30 + k, 14)
        put_wrap(c3, faded(g, cols[2], 0.65, 0.6), R.uniform(0, WT), 150 - g.shape[0] / SC)
    far = crop(c3)
    silt(far, 142, ('#1e2a20', '#2e3e2e', '#44563e', '#5e7052'), seed + 4, k=0.9)
    c3 = three(far)
    drift(c3, 70, ['#c4e0d8', '#a0c8bc'], seed + 5, y0=20, y1=GY - 6, a=110)
    return crop(c3)


def catfish(seed):
    return fish(30, 11, seed, back='#2a2418', side='#5a4a32', belly='#c8b48a', kind='cat', out='#140e06', spots_col='#2a2010', fin='#4a3e2a')


def T_pool():
    far = pool_far()
    mid = mid_fish(3511, 5, catfish, a=0.35, y0=60, y1=GY - 30)
    LEAF = [faded(SW.leaf('m', 7, 3550 + k), '#3a3020', 0.6) for k in range(3)] + [faded(SW.leaf('g', 6, 3560 + k), '#3a3020', 0.55) for k in range(2)] + [stone(5, 3, 3565)]
    floor = bed(3541, ramp('#1a1e14', '#2e3424', '#444c36', '#5e664c', '#7a8262', n=5), SOIL_D, pat_top=pat_soil, out='#0a0c06',
                surface=things_on_bed(LEAF, 45, 3543, sink=0.5))
    ceil = sky_ceil(3551, sky=('#7aa4b4', '#96bcc8', '#b4d4dc'), mirror='#c8dcdc', out='#1e3a3a')
    obs = {'low': [log(30, 9, 51), log(26, 10, 52)],
           'tall': [SW.branch(44, 53), SW.branch(48, 54)],
           'hang': [ribbons_hang(55, 14, ('#4a3a24', '#6a5434', '#3a2c1a'), out='#140e06', wid=1.2), willow_hang(56)],
           'float': [catfish(57), catfish(58)],
           'huge': [tower(lambda h: trunk(h, 59, 18))]}
    return dict(far=far, mid=mid, floor=floor, ceil=ceil, obs=obs, coin='drop', special='pearl')


# ================================================================== 6. under the bridge
def bridge_far(seed=3601, cols=('#9ac0bc', '#72a09c', '#527e7c', '#365c5e')):
    R = RS(seed)
    far = water_far(cols, seed, caust=0.35, shafts=5)
    y, x = grid(H, WT)
    for j in range(3):                                      # the bridge's shadow lying across the water
        d = np.abs(np.mod(x - j * WT / 3 - 200 + WT / 2, WT) - WT / 2)
        mul(far, 1 - 0.28 * np.clip(1 - d / 160, 0, 1) ** 0.6)
    c3 = three(far)
    for j in range(3):                                      # its piers, far off
        g = pier(140, seed + j, 34)
        put_wrap(c3, faded(g, cols[2], 0.55, 0.85), j * WT / 3 + 200 - 17, 150 - g.shape[0] / SC)
    junk = [SW.tire(26, 10, seed + 40), SW.pet_bottle(20, 7, seed + 41), SW.can(12, 8, seed + 42), SW.plastic_bag(18, 14, seed + 43),
            SW.soju_bottle(seed + 44)]
    for k in range(30):
        g = junk[k % len(junk)]
        put_wrap(c3, faded(g, cols[2], 0.5, 0.75), R.uniform(0, WT), R.uniform(138, 148) - g.shape[0] / SC * 0.5)
    far = crop(c3)
    silt(far, 144, ('#3a3e2e', '#545a44', '#727a5e', '#929a7c'), seed + 4, k=0.9)
    c3 = three(far)
    drift(c3, 70, ['#e0ece4', '#c4d8d0'], seed + 5, y0=20, y1=GY - 6, a=120)
    return crop(c3)


def T_bridge():
    far = bridge_far()
    mid = mid_fish(3611, 5, minnow, a=0.4)
    TR = [SW.can(10, 6, 3650), stone(5, 3, 3653), stone(6, 3.4, 3654), SW.pet_bottle(14, 5, 3651), stone(4, 2.6, 3655), faded(SW.leaf('m', 6, 3652), '#3a3020', 0.5)]
    floor = bed(3641, ramp('#2e3224', '#484e38', '#646c4e', '#848c6c', '#a4aa8a', n=5), SOIL_D, pat_top=pat_soil, out='#101208',
                surface=things_on_bed(TR, 36, 3643, sink=0.4))
    ceil = sky_ceil(3651, sky=('#6a8a96', '#86a2ac', '#a4bcc4'), mirror='#c4d4d8', out='#1e3436')
    obs = {'low': [SW.tire(26, 10, 61), SW.pet_bottle(24, 9, 62)],
           'tall': [SW.umbrella(42, 63), SW.tire(38, 10, 64, upright=True)],
           'hang': [hook_line(65), hook_line(66)],
           'float': [SW.plastic_bag(20, 16, 67), SW.plastic_bag(18, 14, 68, dark=True)],
           'huge': [tower(lambda h: SW.tire_stack(h, 69, 28))]}
    return dict(far=far, mid=mid, floor=floor, ceil=ceil, obs=obs, coin='drop', special='pearl')


# ================================================================== 7. the estuary: reeds, fresh water meeting the sea
def reeds_far(seed=3701, cols=('#c8caa4', '#a4a886', '#80866a', '#5e644e')):
    R = RS(seed)
    far = water_far(cols, seed, caust=0.3, shafts=6)
    y, x = grid(H, WT)
    lerp_rgb(far, '#d8d4b4', np.clip(0.5 + 0.5 * np.sin(x * TAU * 5 / WT + y * 0.05), 0, 1) ** 4 * 0.12)   # salt and fresh water mixing
    c3 = three(far)
    for k in range(160):                                    # the reeds' stems going up through the water
        x0 = R.uniform(0, WT); w = R.uniform(0.6, 1.4); a = R.uniform(0.25, 0.55)
        g = canvas(4, 150)
        A.stroke(g, [(2, 150), (2 + R.uniform(-2, 2), 0)], w, ['#4a5a2a', '#5e6a34', '#3a4a22'][k % 3], 255, scale=1.0)
        for j in range(int(R.uniform(2, 5))):
            yy = R.uniform(20, 140); A.stroke(g, [(1, yy), (3, yy)], 0.3, '#2a3016', 255, scale=1.0)
        g[..., 3] *= a
        put_wrap(c3, g, x0, 0)
    far = crop(c3)
    silt(far, 140, ('#3a3426', '#544c38', '#726850', '#92886c'), seed + 4, k=0.95)
    haze(far, cols[1], 0.1)
    return far


def goby(seed):
    return fish(18, 8, seed, back='#4a4030', side='#8a7a5a', belly='#e0d4b4', kind='goby', spots_col='#3a2e1e', fin='#7a6a4a', out='#1a140a')


def reed_root(h, seed=1, w=24):
    """a reed's rhizome and stems: the knotted root on the mud, stems going up, their joints"""
    R = RS(seed)
    h = int(round(h))
    o = canvas(w, h)
    for k in range(7):
        x0 = w / 2 + R.uniform(-w * 0.35, w * 0.35); l = R.uniform(0.7, 1.0) * (h - 2)
        A.stroke(o, [(x0, h - 1), (x0 + R.uniform(-1.5, 1.5), h - 1 - l)], 1.5, '#1e240e', 255, scale=1.0)
        A.stroke(o, [(x0, h - 1), (x0 + R.uniform(-1.5, 1.5) * 0, h - 1 - l)], 1.0, ['#7a8a3a', '#8a9a44', '#6a7a32'][k % 3], 255, scale=1.0)
        for j in range(int(l / 9)):
            yy = h - 1 - 6 - j * 9; A.stroke(o, [(x0 - 0.9, yy), (x0 + 0.9, yy)], 0.35, '#3a4418', 255, scale=1.0)
    rh = lump(w, 5, seed, ramp('#4a3a22', '#6e5a3a', '#94805a', '#b8a67e'), '#1a140a', bumps=8)
    paste(o, rh, 0, h - 5.5)
    return trim(o)


def T_reeds():
    far = reeds_far()
    mid = mid_fish(3711, 6, goby, a=0.4, y0=90, y1=GY - 15)
    floor = bed(3741, ramp('#2e2a1e', '#4a4430', '#66604a', '#868066', '#a8a288', n=5), SOIL_D, pat_top=pat_mud, out='#100e08',
                surface=things_on_bed([shell_sprite(5, 3.4, 3750 + k) for k in range(3)] + [stone(4, 2.6, 3755)], 50, 3743, sink=0.3))
    ceil = sky_ceil(3751, sky=('#b4c8d4', '#c8d8e0', '#e0ecf0'), mirror='#e8ece0', out='#3a3a2a')
    obs = {'low': [crab(20, 11, 71), crab(18, 10, 72, cols=('#3a3a1a', '#5e5e2a', '#84843e', '#a8a85a', '#d0d08a'), out='#14140a')],
           'tall': [reed_root(42, 73), reed_root(48, 74)],
           'hang': [ribbons_hang(75, 12, ('#8a8a4a', '#a4a45a', '#6e6e3a'), out='#24240e', wid=1.4), ribbons_hang(76, 10, ('#5e6a34', '#7a8a44', '#4a5a2a'), out='#1a200a')],
           'float': [goby(77), goby(78)],
           'huge': [tower(lambda h: reed_root(h, 79, 28))]}
    return dict(far=far, mid=mid, floor=floor, ceil=ceil, obs=obs, coin='drop', special='pearl')


# ================================================================== 8. the mudflat
def mudflat_far(seed=3801, cols=('#ccc4a4', '#aca486', '#8a8268', '#68604c')):
    R = RS(seed)
    far = water_far(cols, seed, caust=0.45, shafts=6)
    c3 = three(far)
    for k in range(5):                                       # long low banks of mud far off, holes in them
        w = R.uniform(160, 300); hh = R.uniform(14, 26)
        y, x = grid(hh, w)
        m = (y >= hh * (1 - np.sin(np.clip(x / w, 0, 1) * np.pi) ** 0.6)) & (y > 0.5)
        g = paint(m, ramp('#4a4232', '#6a604a', '#8a7e64', '#aa9e82'), np.clip(0.6 - 0.4 * y / hh + 0.15 * noise(y.shape, 0.8, seed + k), 0, 1))
        for j in range(int(w / 12)):
            ellipse_soft(g, R.uniform(5, w - 5), R.uniform(hh * 0.5, hh - 2), 0.8, 0.5, '#1a140c', 220)
        put_wrap(c3, faded(g, cols[2], 0.4, 0.85), R.uniform(0, WT), 150 - hh)
    far = crop(c3)
    silt(far, 146, ('#3e3628', '#5a5040', '#786c58', '#968a72'), seed + 4, k=0.9)
    c3 = three(far)
    drift(c3, 90, ['#e8e0c8', '#d4ccb0'], seed + 5, y0=20, y1=GY - 6, a=140)
    return crop(c3)


def T_mudflat():
    far = mudflat_far()
    mid = mid_fish(3811, 8, lambda s: shrimp(10, 5, s), a=0.45)
    floor = bed(3841, ramp('#2a241a', '#463e2e', '#625844', '#80765e', '#a0967c', n=5), SOIL_D, pat_top=pat_mud, out='#0e0c06', top_th=10,
                surface=things_on_bed([shell_sprite(6, 3.8, 3850 + k) for k in range(3)] + [oyster_clump(9, 4, 3855)], 40, 3843, sink=0.3))
    ceil = sky_ceil(3851, sky=('#bcc8cc', '#d0dadc', '#e6eeee'), mirror='#ecece0', out='#3a3a2a')
    obs = {'low': [oyster_clump(24, 11, 81), shell_sprite(16, 9, 82)],
           'tall': [mud_mound(40, 24, 83), mud_mound(46, 26, 84)],
           'hang': [ribbons_hang(85, 14, ('#4a9a3a', '#6ab44a', '#3a8a2e'), out='#0e2a0a', wid=2.4), ribbons_hang(86, 12, ('#5aa840', '#7ac458', '#4a9434'), out='#0e2a0a', wid=2.2)],
           'float': [shrimp(14, 7, 87), shrimp(12, 6, 88)],
           'huge': [tower(lambda h: stack([oyster_clump(26, 12, 89 + k) for k in range(int(h / 9) + 1)], gap=-3))]}
    return dict(far=far, mid=mid, floor=floor, ceil=ceil, obs=obs, coin='drop', special='pearl')
