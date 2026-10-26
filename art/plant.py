# Stage 2, the treatment works and out: the bar screen at the inlet (13), the grit chamber (14), the primary
# clarifier (15), the aeration tank (16), the secondary clarifier (17), UV disinfection (18), the outfall into the
# river (19).
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
import sewer as SW
from s2lib import (lerp_rgb, mul, wdx, pipe_curve, ring_joints, concrete_tex, water_line, streaks, mouth, silt, motes,
                   bubble_chain, pat_concrete, pat_soil, pat_slime, pat_sludge, pat_iron, pat_gravel, pebble_surface,
                   surf_ceil, strands, lump, speckle, trim, blob_mask, mass)

RS = np.random.RandomState
CONC = SW.CONC
SOIL = SW.SOIL
put_wrap = SW.put_wrap
STEEL = SW.STEEL
GALV = ramp('#3a4046', '#5e666e', '#868e96', '#aeb6bc', '#d4dade', '#f0f4f6', n=6)
FLOC = ramp('#3a2a14', '#5e4422', '#86663a', '#a88a58', '#c8ae80')
FLOC_OUT = '#1e1408'


def rag(w=18, h=10, seed=1, col=('#5a6a7a', '#8a9aaa', '#b4c2ce', '#dce4ea')):
    """a rag of cloth twisted up: folds, a frayed edge"""
    R = RS(seed)
    y, x = grid(h, w)
    ang = np.arctan2(y - h / 2, (x - w / 2) * h / w)
    rr = np.sqrt(((x - w / 2) / (w / 2 - 0.8)) ** 2 + ((y - h / 2) / (h / 2 - 0.8)) ** 2)
    m = rr <= 0.86 + 0.1 * np.sin(ang * 3 + seed) + 0.05 * np.sin(ang * 9)
    spr = A.mask_sprite(m, ramp(*col), '#1e242a', soft=1.2, ambient=0.4, hl_t=0.99)
    I = inner(spr); keep = I[..., 3].copy()
    for k in range(int(w * h / 12)):
        a0 = R.uniform(-0.8, 0.8); cx0, cy0 = R.uniform(1, w - 1), R.uniform(1, h - 1); l = R.uniform(3, 6)
        A.stroke(I, [(cx0, cy0), (cx0 + np.cos(a0) * l * 0.5, cy0 + np.sin(a0) * l * 0.5 + 0.6), (cx0 + np.cos(a0) * l, cy0 + np.sin(a0) * l)], 0.35, '#2a343e', 130, scale=1.0)
    I[..., 3] = keep
    lerp_rgb(I, '#7a6a40', np.clip(noise(I.shape[:2], 1.0, seed) - 0.3, 0, 1) * 0.5 * (I[..., 3] > 0))
    return spr


# ================================================================== 13. the bar screen at the inlet
WATER_SC = '#6a6e5c'


def screen_far(seed=1601):
    R = RS(seed)
    far = gradient(H, ['#a8a894', '#8c8c78', '#70705e', '#545444'])
    concrete_tex(far, seed + 1, k=0.9, cols=('#262618', '#d8d6c0'))
    y, x = grid(H, WT)
    c3 = three(far)
    for j in range(2):                                    # the screen: steel bars leaning back, rubbish caught on them
        x0 = j * WT / 2 + 80
        g = canvas(200, H)
        gy, gx = grid(H, 200)
        lean = 0.28
        for i in range(32):
            bx = 10 + i * 5.6
            A.stroke(g, [(bx, 0), (bx + lean * H, H)], 1.9, '#141812', 255, scale=1.0)
            A.stroke(g, [(bx, 0), (bx + lean * H, H)], 1.2, ['#6a7068', '#7e847a'][i % 2], 255, scale=1.0)
            A.stroke(g, [(bx - 0.35, 0), (bx - 0.35 + lean * H, H)], 0.3, '#c4c8be', 200, scale=1.0)
        for k in range(26):                               # the rubbish held against it
            ty = R.uniform(30, GY - 4); tx = 10 + R.uniform(0, 170) + lean * ty
            kind = k % 4
            if kind == 0:
                t_ = rag(R.uniform(10, 18), R.uniform(6, 10), seed + 10 + k)
            elif kind == 1:
                t_ = SW.plastic_bag(R.uniform(10, 16), R.uniform(8, 12), seed + 30 + k, dark=bool(k % 3 == 0))
            elif kind == 2:
                t_ = D.wet_wipe(seed + 50 + k, R.uniform(9, 14), R.uniform(6, 9))
            else:
                t_ = SW.pet_bottle(R.uniform(16, 22), R.uniform(6, 8), seed + 70 + k)
            paste(g, t_, tx - t_.shape[1] / SC / 2, ty - t_.shape[0] / SC / 2)
        put_wrap(c3, g, x0, 0)
    far = crop(c3)
    water_line(far, 26, '#3e3e26', k=0.45, h=12, seed=seed + 2)
    streaks(far, 50, seed + 3, '#4a4a30', k=0.25, y0=40, y1=GY, L=(60, 200), w=(0.8, 2.4))
    c3 = three(far)
    drift(c3, 140, ['#c8c6a8', '#8a8a6a', '#e8e6d0'], seed + 4, y0=20, y1=GY - 6, a=150)
    far = crop(c3)
    haze(far, WATER_SC, 0.2)
    return far


def rake(seed=1, wdt=24):
    """the screen's mechanical rake coming down: an arm from above, a steel head with a comb of teeth, rags on it"""
    L = hang_len()
    R = RS(seed)
    W = wdt + 4
    out = canvas(W, L)
    ax = W / 2
    for xr in (ax - 2.2, ax + 2.2):
        A.stroke(out, [(xr, 0), (xr, L - 22)], 2.6, '#101418', 255, scale=1.0)
        A.stroke(out, [(xr, 0), (xr, L - 22)], 1.8, '#e8b020', 255, scale=1.0)
        A.stroke(out, [(xr - 0.5, 0), (xr - 0.5, L - 22)], 0.45, '#ffe28a', 220, scale=1.0)
    for i in range(int((L - 24) / 10)):
        yy = 4 + i * 10
        A.stroke(out, [(ax - 2.2, yy), (ax + 2.2, yy + 8)], 1.0, '#101418', 255, scale=1.0)
        A.stroke(out, [(ax - 2.2, yy), (ax + 2.2, yy + 8)], 0.55, '#e8b020', 255, scale=1.0)
    fill_rect(out, 1, L - 23, W - 1, L - 16, '#101418', 255)
    fill_rect(out, 1.6, L - 22.4, W - 1.6, L - 16.6, '#e8b020', 255)                 # the head, painted
    fill_rect(out, 1.6, L - 22.4, W - 1.6, L - 21.4, '#ffe28a', 255)
    for i in range(int((wdt - 1) / 2.6)):                 # its teeth
        tx = 2.6 + i * 2.6
        A.stroke(out, [(tx, L - 16.5), (tx + 0.6, L - 1.2)], 1.5, '#101418', 255, scale=1.0)
        A.stroke(out, [(tx, L - 16.5), (tx + 0.6, L - 1.2)], 0.95, '#9aa2a8', 255, scale=1.0)
    for k in range(3):                                    # rags caught on the teeth
        g = rag(R.uniform(7, 10), R.uniform(5, 7), seed + 10 + k)
        paste(out, g, R.uniform(1, W - 10), L - 13 + R.uniform(-1, 5))
    return out


def bar_panel(h=42, seed=1, w=22):
    """a section of screen bars standing on the bottom, a rag and a bag caught in it"""
    R = RS(seed)
    h = int(round(h))
    out = canvas(w, h)
    fill_rect(out, 0.6, 0.6, w - 0.6, 3.0, '#101418', 255); fill_rect(out, 1.0, 1.0, w - 1.0, 2.6, '#7e868e', 255)
    fill_rect(out, 0.6, h - 3.0, w - 0.6, h - 0.6, '#101418', 255); fill_rect(out, 1.0, h - 2.6, w - 1.0, h - 1.0, '#7e868e', 255)
    for i in range(int((w - 2) / 3.2) + 1):
        bx = 1.6 + i * 3.2
        A.stroke(out, [(bx, 2), (bx, h - 2)], 1.5, '#101418', 255, scale=1.0)
        A.stroke(out, [(bx, 2), (bx, h - 2)], 0.95, ['#6a7068', '#868c84'][i % 2], 255, scale=1.0)
    for k in range(int(h / 14)):
        g = rag(R.uniform(8, 14), R.uniform(5, 8), seed + 10 + k) if k % 2 == 0 else SW.plastic_bag(R.uniform(8, 12), R.uniform(6, 9), seed + 20 + k)
        paste(out, g, R.uniform(0, w - 10), R.uniform(4, h - 10))
    return out


def trash_clump(w=24, h=12, seed=1):
    """what the screen takes out: rags, a bag, a wipe, wound together"""
    R = RS(seed)
    out = canvas(w, h)
    for k in range(5):
        kind = k % 3
        g = rag(R.uniform(12, 16), R.uniform(7, 10), seed + k) if kind == 0 else SW.plastic_bag(R.uniform(11, 15), R.uniform(8, 11), seed + 10 + k, dark=bool(k % 2)) if kind == 1 else D.wet_wipe(seed + 20 + k, R.uniform(10, 14), R.uniform(7, 9))
        paste(out, g, R.uniform(0, w - g.shape[1] / SC), h - g.shape[0] / SC - R.uniform(0, h * 0.4))
    return trim(out)


def T_screen():
    far = screen_far()
    R = RS(1611)
    mid = wide()
    for k in range(10):
        g = rag(R.uniform(6, 10), R.uniform(4, 6), 1620 + k) if k % 2 else D.wet_wipe(1640 + k, R.uniform(6, 9), R.uniform(4, 6))
        g[..., 3] *= 0.8
        put(mid, g, R.uniform(0, WT), R.uniform(26, GY - 24))
    motes(mid, 150, ['#c8c6a8', '#8a8a6a', '#e8e6d0'], 1612, r=(0.3, 1.0), a=(110, 200))
    mid = crop(mid)
    floor = wall([(1.6, ramp('#34341e', '#4e4e32', '#6a6a48', n=3), pat_slime), (12, CONC, pat_concrete), (40, SOIL, pat_soil)], True, seed=1641, bumps=0.4, out='#121208')
    def extra(c3, R, rim_b, surf):
        for off in (0, WT, 2 * WT):
            for i in range(int(WT / 3)):
                fill_rect(c3, off + i * 3 + 1.0, 1.0, off + i * 3 + 2.2, 5.2, '#e8eadc', 190)
    ceil = surf_ceil(1651, ramp('#1e2018', '#363a2e', '#545848', '#727664', n=4), crown_h=6.6, air=('#34362a', '#525442', '#74765e'),
                     mirror='#e6e6d6', out='#1a1a10', extra=extra)
    obs = {'low': [trash_clump(28, 15, 1), trash_clump(25, 14, 2)],
           'tall': [bar_panel(42, 1, 22), bar_panel(48, 2, 20)],
           'hang': [rake(1, 24), rake(2, 20)],
           'float': [rag(18, 10, 3), SW.plastic_bag(18, 14, 5, dark=True)],
           'huge': [tower(lambda h: bar_panel(h, 3, 22))]}
    return dict(far=far, mid=mid, floor=floor, ceil=ceil, obs=obs, coin='drop', special='soap')


# ================================================================== 14. the grit chamber
WATER_GR = '#7a7a62'
SAND = ramp('#5a4a30', '#8a7650', '#b4a07a', '#d4c49e', '#ece0c0', n=5)
STONE = [('#4a4a46', '#7a7a72', '#a8a89c', '#d0d0c4'), ('#5a4a3a', '#8a7460', '#b49e86', '#d8c8b0'), ('#3e4a4a', '#6a7a78', '#98a8a4', '#c4d2ce')]


def pebble(w, h, seed, cols=None):
    R = RS(seed)
    cols = cols or STONE[seed % len(STONE)]
    y, x = grid(h, w)
    ang = np.arctan2(y - h / 2, (x - w / 2) * h / w)
    rr = np.sqrt(((x - w / 2) / (w / 2 - 0.7)) ** 2 + ((y - h / 2) / (h / 2 - 0.7)) ** 2)
    m = rr <= 0.94 + 0.05 * np.sin(ang * 3 + seed) + 0.03 * np.sin(ang * 5 + 2 * seed)
    spr = A.mask_sprite(m, ramp(*cols), '#161612', soft=1.0, ambient=0.35, hl_t=0.97)
    A.grain(spr, seed, 0.08, 0.4)
    speckle(spr, seed + 1, int(w * h * 0.3), ['#2a2a24', '#e8e4d8'], r=(0.15, 0.35), a=150)
    return spr


def grit_far(seed=1701):
    R = RS(seed)
    far = gradient(H, ['#b0ac94', '#94907a', '#787462', '#5c5848'])
    concrete_tex(far, seed + 1, k=0.8, cols=('#2a281e', '#dcd8c4'))
    y, x = grid(H, WT)
    silt(far, 110, ('#5a4a30', '#8a7650', '#b4a07a', '#d0c098'), seed + 2)            # sand banked against the far wall
    c3 = three(far)
    for k in range(240):                                  # gravel in the sand
        g = pebble(R.uniform(1.6, 4), R.uniform(1.2, 3), seed + 10 + k)
        put_wrap(c3, g, R.uniform(0, WT), R.uniform(118, 150))
    far = crop(c3)
    y, x = grid(H, WT)                                     # the air pipe along the wall low down, bubbles rising off it in a curtain
    lerp_rgb(far, '#2a3036', np.exp(-((y - 104) / 2.2) ** 2) * 0.8)
    lerp_rgb(far, '#c8d0d6', np.exp(-((y - 103) / 0.6) ** 2) * 0.5)
    c3 = three(far)
    for k in range(200):
        bx = R.uniform(0, WT); by = R.uniform(10, 100); r = R.uniform(0.5, 1.6)
        b = canvas(2 * r + 2, 2 * r + 2); ellipse_soft(b, r + 1, r + 1, r, r, '#f4f8f8', 150); ellipse_soft(b, r + 1, r + 1, r * 0.6, r * 0.6, '#9aa4a4', 60)
        put_wrap(c3, b, bx, by)
    drift(c3, 160, ['#d4c49e', '#ffffff', '#a89a74'], seed + 3, y0=20, y1=GY - 6, a=160)
    far = crop(c3)
    haze(far, WATER_GR, 0.18)
    return far


def gravel_heap(w=26, h=11, seed=1):
    R = RS(seed)
    base = mass(w * 0.85, h * 0.6, seed, SAND, '#2a2214', n=4, ambient=0.4, hl_t=0.995, grain_k=0.1)
    out = canvas(w, h)
    paste(out, base, w * 0.075, h - base.shape[0] / SC)
    for k in range(int(w * h / 9)):
        pw = R.uniform(3.2, 6.5); g = pebble(pw, pw * R.uniform(0.6, 0.85), seed + 10 + k)
        t = R.uniform(0, 1)
        px_ = R.uniform(1, w - pw - 1); py_ = h - g.shape[0] / SC - R.uniform(0, (h * 0.7) * (1 - abs(px_ + pw / 2 - w / 2) / (w / 2)))
        paste(out, g, px_, py_)
    return trim(out)


def cairn(h, seed=1, w=24):
    """rounded stones washed in and stacked up against each other"""
    R = RS(seed)
    sizes = []; tot = 0
    while tot < h - 3:                                     # the stones' heights, the top one cut to make up h exactly
        sh = R.uniform(8, 12); sizes.append(sh); tot += sh + 2 - 2.2
    sizes[-1] = max(4.0, sizes[-1] - (tot - (h - 3)))
    parts = []; acc = 0
    for k, sh in enumerate(sizes):
        sw = w * R.uniform(0.7, 1.0) * (1 - 0.25 * acc / max(h, 1))
        parts.append(pebble(sw, sh, seed + k)); acc += sh
    return stack(parts, gap=-2.2)


def eggshell(w=14, h=9, seed=1):
    """a broken piece of eggshell (grit chambers catch them): a curved white-brown shell, its jagged edge"""
    R = RS(seed)
    y, x = grid(h, w)
    rr = np.sqrt(((x - w / 2) / (w / 2 - 0.7)) ** 2 + ((y - h * 0.5) / (h * 0.5 - 0.7)) ** 2)
    cut = h * 0.42 + (x - w / 2) * 0.35 + 0.7 * np.abs(np.sin(x * 2.3 + seed)) + 0.4 * np.sin(x * 5.1)
    m = (rr <= 1) & (y >= cut - 2.2)
    spr = A.mask_sprite(m, ramp('#8a6a4a', '#b8987a', '#dcc4aa', '#f2e6d6', '#ffffff'), '#3a2a1a', soft=1.0, ambient=0.45, hl_t=0.97)
    I = inner(spr)
    inside = (rr <= 0.86) & (y < cut + 1.8) & (y >= cut - 2.2)          # the inside of the shell, seen over its broken rim
    lerp_rgb(I, '#fbf6ec', inside * 0.85)
    lerp_rgb(I, '#6a4a2a', (np.abs(y - cut - 1.8) < 0.3) * (rr <= 0.9) * 0.7)
    return spr


def air_drop(seed=1, wdt=6):
    """a grit chamber's air pipe coming down from above, bubbling out at its end"""
    L = hang_len()
    R = RS(seed)
    W = wdt + 16
    out = canvas(W, L)
    ax = W / 2
    A.stroke(out, [(ax, 0), (ax, L - 4)], wdt + 0.8, '#101418', 255, scale=1.0)
    A.stroke(out, [(ax, 0), (ax, L - 4)], wdt, '#7a848c', 255, scale=1.0)
    A.stroke(out, [(ax - wdt * 0.25, 0), (ax - wdt * 0.25, L - 4)], wdt * 0.25, '#d0d8de', 220, scale=1.0)
    for fy in (20, 60, 100):
        fill_rect(out, ax - wdt / 2 - 1.2, fy - 1.2, ax + wdt / 2 + 1.2, fy + 1.2, '#101418', 255)
        fill_rect(out, ax - wdt / 2 - 0.8, fy - 0.8, ax + wdt / 2 + 0.8, fy + 0.8, '#9aa4ac', 255)
    fill_rect(out, ax - wdt / 2 - 2, L - 5, ax + wdt / 2 + 2, L - 1, '#101418', 255)
    fill_rect(out, ax - wdt / 2 - 1.5, L - 4.6, ax + wdt / 2 + 1.5, L - 1.4, '#c4ccd2', 255)       # the diffuser head
    for k in range(18):                                   # bubbles coming off it, rising round the pipe
        by = R.uniform(L * 0.5, L - 3); bx = ax + R.choice([-1, 1]) * R.uniform(wdt / 2 + 1, wdt / 2 + 6); r = R.uniform(0.7, 1.8)
        ellipse_soft(out, bx, by, r, r, '#f4fafa', 200); ellipse_soft(out, bx - r * 0.3, by - r * 0.3, r * 0.3, r * 0.3, '#ffffff', 230)
        A.stroke(out, [(bx + r * 0.7, by - r * 0.7), (bx + r * 0.9, by)], 0.25, '#4a5a5e', 160, scale=1.0)
    return out


def T_grit():
    far = grit_far()
    R = RS(1711)
    mid = wide()
    for k in range(10):
        g = eggshell(R.uniform(6, 9), R.uniform(4, 6), 1720 + k) if k % 2 else pebble(R.uniform(2, 4), R.uniform(1.6, 3), 1730 + k)
        g[..., 3] *= 0.85
        put(mid, g, R.uniform(0, WT), R.uniform(30, GY - 20))
    motes(mid, 220, ['#d4c49e', '#b4a07a', '#ffffff', '#8a7650'], 1712, r=(0.3, 0.8), a=(120, 220))
    bubble_chain(mid, 10, 1713, y0=40, y1=GY - 30, r=(1, 2), alpha=0.6)
    mid = crop(mid)
    floor = wall([(5, SAND, pat_gravel), (8, CONC, pat_concrete), (40, SOIL, pat_soil)], True, seed=1741, bumps=0.8, out='#1a140a',
                 surface=lambda c3, e, e0, top: pebble_surface(c3, e, e0, top, seed=1742, n=150, r=(0.8, 2.2)))
    ceil = surf_ceil(1751, ramp('#22221c', '#3a3a32', '#58584c', '#76766a', n=4), crown_h=6.6, air=('#3a3a30', '#58584a', '#7a7a68'), mirror='#ececdc', out='#1c1c14')
    obs = {'low': [gravel_heap(26, 11, 1), gravel_heap(22, 10, 2)],
           'tall': [cairn(40, 1, 22), cairn(46, 2, 24)],
           'hang': [air_drop(1, 6), air_drop(2, 5)],
           'float': [eggshell(15, 9, 3), eggshell(13, 8, 4)],
           'huge': [tower(lambda h: cairn(h, 5, 24))]}
    return dict(far=far, mid=mid, floor=floor, ceil=ceil, obs=obs, coin='drop', special='soap')


# ================================================================== 15. the primary clarifier
WATER_C1 = '#6a6a50'


def clar1_far(seed=1801):
    R = RS(seed)
    far = gradient(H, ['#8c8a6c', '#76745a', '#5e5c46', '#444232'])
    y, x = grid(H, WT)
    c3 = three(far)
    for j in range(2):                                    # the centre column far off, its feed well round it
        cx = j * WT / 2 + 200
        g = canvas(70, H)
        gy, gx = grid(H, 70)
        col = (np.abs(gx - 35) < 12)
        sh = np.clip(0.55 + 0.35 * np.cos((gx - 35) / 12 * np.pi / 2) - 0.25 * (gx > 35), 0, 1)
        g[..., :3] = ramp_col(ramp('#3a3a2c', '#5a5a48', '#7a7a64', '#9a9a82'), sh); g[..., 3] = col * 255
        well = (np.abs(gx - 35) < 32) & (gy > 14) & (gy < 56)
        sh2 = np.clip(0.55 + 0.35 * np.cos((gx - 35) / 32 * np.pi / 2) - 0.25 * (gx > 35), 0, 1)
        g[..., :3] = np.where(well[..., None], ramp_col(STEEL, sh2 * 0.8), g[..., :3]); g[..., 3] = np.where(well, 255, g[..., 3])
        g = outline(g, '#20201a')
        g[..., 3] *= 0.55
        put_wrap(c3, g, cx - 36, -1)
    for j in range(2):                                    # the scraper arm sweeping round the bottom, seen far off
        x0 = j * WT / 2 + 420
        g = canvas(300, 30)
        A.stroke(g, [(4, 6), (296, 24)], 2.8, '#20201a', 255, scale=1.0)
        A.stroke(g, [(4, 6), (296, 24)], 2.0, '#6e6e5a', 255, scale=1.0)
        for i in range(14):
            bx = 10 + i * 20; by = 6 + 18 * (bx / 300)
            A.stroke(g, [(bx, by), (bx + 8, by + 5)], 1.4, '#20201a', 255, scale=1.0)
            A.stroke(g, [(bx, by), (bx + 8, by + 5)], 0.8, '#8a8a72', 255, scale=1.0)
        g[..., 3] *= 0.5
        put_wrap(c3, g, x0, 118)
    far = crop(c3)
    silt(far, 132, ('#2a2414', '#46381e', '#62502e', '#7a6840'), seed + 2)              # the sludge blanket
    streaks(far, 50, seed + 3, '#4a4430', k=0.2, y0=20, y1=GY, L=(100, 300), w=(1.0, 3.0))
    c3 = three(far)
    drift(c3, 220, ['#a89a70', '#7a6e4c', '#c8bc94'], seed + 4, y0=20, y1=GY - 4, a=170)
    far = crop(c3)
    haze(far, WATER_C1, 0.3)
    return far


def skimmer(seed=1, wdt=14):
    """the scraper bridge's skimmer coming down into the water: a steel arm, a blade with a rubber edge"""
    L = hang_len()
    W = wdt + 6
    out = canvas(W, L)
    for xr in (W / 2 - 3, W / 2 + 3):
        A.stroke(out, [(xr, 0), (xr, L - 26)], 1.8, '#101418', 255, scale=1.0)
        A.stroke(out, [(xr, 0), (xr, L - 26)], 1.1, '#868e96', 255, scale=1.0)
    for i in range(int((L - 30) / 12)):
        yy = 6 + i * 12
        A.stroke(out, [(W / 2 - 3, yy), (W / 2 + 3, yy + 10)], 0.9, '#101418', 255, scale=1.0)
        A.stroke(out, [(W / 2 - 3, yy), (W / 2 + 3, yy + 10)], 0.5, '#9aa2aa', 255, scale=1.0)
    blade = canvas(W, 26)
    fill_rect(blade, 1, 0.5, W - 1, 21, '#101418', 255)
    fill_rect(blade, 1.6, 1.1, W - 1.6, 20.4, '#7a828a', 255)
    fill_rect(blade, 1.6, 1.1, W - 1.6, 2.2, '#c4ccd2', 255)
    fill_rect(blade, 1, 20.5, W - 1, 25.4, '#0a0a0a', 255)
    fill_rect(blade, 1.6, 21.0, W - 1.6, 24.8, '#2a2a2e', 255)                       # the rubber
    yy, xx = grid(26, W)
    lerp_rgb(blade, '#5a4a2a', np.clip(noise(yy.shape, 0.8, seed) - 0.1, 0, 1) * 0.5 * (blade[..., 3] > 0) * (yy > 8))
    paste(out, blade, 0, L - 26)
    return out


def scraper_blade(h=34, seed=1, w=26):
    """the bottom scraper: a blade on the arm's truss, pushing the sludge along; sludge piled in front of it"""
    h = int(round(h))
    out = canvas(w, h)
    for xr in (4, w - 4):
        A.stroke(out, [(xr, 0.8), (xr, h - 10)], 1.6, '#101418', 255, scale=1.0)
        A.stroke(out, [(xr, 0.8), (xr, h - 10)], 1.0, '#868e96', 255, scale=1.0)
    for i in range(int((h - 12) / 10) + 1):
        yy = 2 + i * 10
        A.stroke(out, [(4, yy), (w - 4, min(h - 10, yy + 8))], 0.9, '#101418', 255, scale=1.0)
        A.stroke(out, [(4, yy), (w - 4, min(h - 10, yy + 8))], 0.5, '#9aa2aa', 255, scale=1.0)
        A.stroke(out, [(4, yy), (w - 4, yy)], 0.9, '#101418', 255, scale=1.0)
        A.stroke(out, [(4, yy), (w - 4, yy)], 0.5, '#9aa2aa', 255, scale=1.0)
    fill_rect(out, 1, h - 11, w - 1, h - 0.6, '#101418', 255)
    fill_rect(out, 1.6, h - 10.4, w - 1.6, h - 1.2, '#7a828a', 255)
    fill_rect(out, 1.6, h - 10.4, w - 1.6, h - 9.4, '#c4ccd2', 255)
    sl = mass(w * 0.5, 7, seed, FLOC, FLOC_OUT, n=3, ambient=0.35, grain_k=0.12)
    paste(out, sl, -0.5, h - sl.shape[0] / SC)
    return trim(out)


def scum_clump(w=18, h=11, seed=1):
    """scum skimmed off the top: brown foam and grease in a floating clump"""
    R = RS(seed)
    out = canvas(w, h)
    for k in range(10):
        r = R.uniform(1.6, 3.4)
        b = A.mask_sprite(ellipse_mask(int(2 * r + 1), int(2 * r + 1)), ramp('#6a5434', '#9a7e52', '#c8ac7c', '#ecdcb8'), '#2a1e0e', soft=0.9, ambient=0.45, hl_t=0.95)
        paste(out, b, R.uniform(0, w - 2 * r - 2), R.uniform(0, h - 2 * r - 2))
    return trim(out)


def centre_column(h, seed=1, w=26):
    """the clarifier's centre column: concrete, the feed well's steel skirt round its top"""
    h = int(round(h))
    out = canvas(w, h)
    y, x = grid(h, w)
    half = w / 2 - 5
    m = (np.abs(x - w / 2) <= half) & (y > 0.6) & (y < h - 0.6)
    u = (x - w / 2) / half
    sh = np.clip(0.6 - 0.45 * u - 0.15 * u ** 4, 0, 1)
    out[..., :3] = ramp_col(CONC, sh); out[..., 3] = smooth_mask(m) * 255
    lerp_rgb(out, '#2a2414', np.clip((y - h * 0.6) / (h * 0.4), 0, 1) * 0.5 * m)
    skirt = (np.abs(x - w / 2) <= w / 2 - 0.8) & (y > 2) & (y < 20)
    out[..., :3] = np.where(skirt[..., None], ramp_col(STEEL, np.clip(0.6 - 0.45 * (x - w / 2) / (w / 2), 0, 1)), out[..., :3]); out[..., 3] = np.where(skirt, 255, out[..., 3])
    for k in range(5):
        disc(out, 3 + k * (w - 6) / 4, 4, 0.7, '#e0e6ea', 255)
    return outline(out, '#14140e', width=0.65)


def T_clarifier1():
    far = clar1_far()
    R = RS(1811)
    mid = wide()
    for k in range(8):
        g = scum_clump(R.uniform(6, 10), R.uniform(4, 6), 1820 + k); g[..., 3] *= 0.8
        put(mid, g, R.uniform(0, WT), R.uniform(26, GY - 24))
    motes(mid, 260, ['#a89a70', '#7a6e4c', '#c8bc94', '#5a4e30'], 1812, r=(0.3, 1.0), a=(120, 220))
    mid = crop(mid)
    floor = wall([(4, FLOC, pat_sludge), (12, CONC, pat_concrete), (40, SOIL, pat_soil)], True, seed=1841, bumps=0.9, out='#140e06')
    def extra(c3, R, rim_b, surf):                         # the scraper bridge above: its truss across the sky
        for off in (0, WT, 2 * WT):
            for i in range(int(WT / 14)):
                A.stroke(c3, [(off + i * 14, 1.2), (off + i * 14 + 7, 5.4), (off + i * 14 + 14, 1.2)], 0.7, '#3e464e', 255, scale=1.0)
            fill_rect(c3, off, 0.4, off + WT, 1.4, '#3e464e', 255)
            fill_rect(c3, off, 5.0, off + WT, 6.0, '#3e464e', 255)
    ceil = surf_ceil(1851, ramp('#6a7a84', '#8a9aa4', '#aabac4', '#cad6dc', n=4), crown_h=0.5, air=('#9ab0bc', '#b8cad4', '#d8e4ea'),
                     mirror='#e4e2cc', out='#2a2a1e', extra=extra)
    obs = {'low': [D.sludge_lump(24, 12, 31), D.sludge_lump(28, 11, 32)],
           'tall': [scraper_blade(34, 1, 26), scraper_blade(40, 2, 24)],
           'hang': [skimmer(1, 14)],
           'float': [scum_clump(18, 11, 1), scum_clump(16, 10, 2)],
           'huge': [tower(lambda h: centre_column(h, 1, 26))]}
    return dict(far=far, mid=mid, floor=floor, ceil=ceil, obs=obs, coin='drop', special='soap')


# ================================================================== 16. the aeration tank (the microbes)
WATER_AE = '#7a6440'


def aer_far(seed=1901):
    R = RS(seed)
    far = gradient(H, ['#a88a5a', '#8e7248', '#725a38', '#564228'])
    concrete_tex(far, seed + 1, k=0.5, cols=('#2a1e10', '#dcc8a0'))
    y, x = grid(H, WT)
    acc = np.zeros(y.shape, np.float32)                   # the diffusers' bubble plumes: columns of fine bubbles, wider up
    for k in range(9):
        x0 = (k + 0.5) * WT / 9 + R.uniform(-20, 20)
        d = wdx(x, x0 + 3 * np.sin(y * 0.05 + k))
        wdt = 6 + 16 * np.clip((GY - y) / GY, 0, 1)
        acc += np.exp(-(d / wdt) ** 2) * 0.8
    lerp_rgb(far, '#f0e4c8', np.clip(acc, 0, 1) * 0.35)
    c3 = three(far)
    for k in range(9):                                    # the diffuser discs on the bottom
        x0 = (k + 0.5) * WT / 9
        g = canvas(16, 5); ellipse_soft(g, 8, 2.5, 7, 1.8, '#2a2a2e', 255); ellipse_soft(g, 8, 2.2, 6, 1.2, '#7a7e86', 255)
        put_wrap(c3, outline(g, '#101010'), x0 - 8, 128)
    for k in range(900):                                  # the bubbles themselves
        x0 = (R.randint(9) + 0.5) * WT / 9; yy = R.uniform(4, 128)
        bx = x0 + R.normal(0, 4 + 10 * (1 - yy / 128)); r = R.uniform(0.35, 1.0)
        b = canvas(2 * r + 2, 2 * r + 2); ellipse_soft(b, r + 1, r + 1, r, r, '#fffaf0', 170)
        put_wrap(c3, b, bx, yy)
    drift(c3, 300, ['#6a5030', '#8a6a40', '#4a3820', '#b49a6a'], seed + 2, y0=10, y1=GY - 4, a=190)       # the floc
    far = crop(c3)
    haze(far, WATER_AE, 0.22)
    return far


def floc(w=14, h=10, seed=1, alpha=1.0):
    """a floc: bacteria clumped together in a loose brown flake, fuzzy, filaments sticking out"""
    R = RS(seed)
    y, x = grid(h, w)
    n = noise(y.shape, 0.7, seed)
    rr = np.sqrt(((x - w / 2) / (w / 2 - 1.2)) ** 2 + ((y - h / 2) / (h / 2 - 1.2)) ** 2)
    m = rr + 0.35 * n < 0.9
    spr = A.mask_sprite(m, FLOC, FLOC_OUT, soft=0.9, ambient=0.4, hl_t=0.99)
    I = inner(spr)
    speckle(spr, seed + 1, int(w * h * 0.4), ['#2a1c0c', '#c8ae80', '#4a3618'], r=(0.2, 0.45), a=170)
    for k in range(int(w / 2)):
        a0 = R.uniform(0, TAU); sx, sy = w / 2 + np.cos(a0) * w * 0.38, h / 2 + np.sin(a0) * h * 0.38
        A.stroke(I, [(sx, sy), (sx + np.cos(a0) * 2.5 + R.uniform(-0.8, 0.8), sy + np.sin(a0) * 2.5)], 0.2, '#5a4422', 200, scale=1.0)
    I[..., 3] *= alpha
    return spr


def vorticella(h=40, seed=1, n_bells=1, w=None):
    """vorticella: a bell-shaped ciliate on a long stalk (it springs into a coil when touched), its ring of cilia"""
    R = RS(seed)
    w = w or 22
    out = canvas(w, h)
    cx = w / 2
    stalk = [(cx + 1.6 * np.sin(t * 9 + seed) * t * 0.6, h - 0.8 - t * (h - 12)) for t in np.linspace(0, 1, 40)]
    A.stroke(out, stalk, 1.7, '#2a3a2a', 255, scale=1.0)
    A.stroke(out, stalk, 1.0, '#a8c0a0', 255, scale=1.0)
    A.stroke(out, [(p[0] - 0.25, p[1]) for p in stalk], 0.3, '#e0f0dc', 200, scale=1.0)
    bw, bh = (16, 14) if w >= 16 else (11, 10)
    y, x = grid(bh, bw)
    t = y / bh
    half = 0.8 + (bw / 2 - 1.2) * np.clip(np.sin(np.clip(t, 0, 1) * np.pi * 0.62) * 1.05, 0, 1)
    m = (np.abs(x - bw / 2) <= half) & (y > 0.6) & (y < bh - 0.4)
    bell = A.mask_sprite(m, ramp('#4a6a58', '#7aa08a', '#a8ccb4', '#d4ece0', '#f0fff6'), '#1a2a20', soft=1.0, ambient=0.45, hl_t=0.95)
    I = inner(bell); I[..., 3] *= 0.92
    ellipse_soft(I, bw / 2, bh * 0.55, 1.8, 1.2, '#4a6a50', 160)               # its nucleus (a curved band)
    bx, by = stalk[-1]
    fb = np.flipud(bell)                                   # the bell opens upward
    paste(out, fb, bx - fb.shape[1] / SC / 2, by - fb.shape[0] / SC + 1.2)
    for k in range(9):                                     # cilia round the rim
        ax = bx - bw / 2 + 1.4 + k * (bw - 2.8) / 8
        A.stroke(out, [(ax, by - bh + 1.2), (ax + R.uniform(-0.8, 0.8), by - bh - 1.6)], 0.22, '#c8e8d4', 220, scale=1.0)
    return trim(out)


def zoothamnium(h, seed=1, w=26):
    """a colony of bell ciliates on one branching stalk, like a little tree"""
    R = RS(seed)
    h = int(round(h))
    out = canvas(w + 14, h)
    cx = (w + 14) / 2
    trunk = [(cx + 1.0 * np.sin(t * 5 + seed), h - 0.8 - t * (h * 0.45)) for t in np.linspace(0, 1, 30)]
    A.stroke(out, trunk, 2.0, '#2a3a2a', 255, scale=1.0); A.stroke(out, trunk, 1.3, '#a8c0a0', 255, scale=1.0)
    tips = []
    def branch(x0, y0, ang, l, depth):
        x1, y1 = x0 + np.cos(ang) * l, y0 - np.sin(ang) * l
        A.stroke(out, [(x0, y0), (x1, y1)], 1.6 - depth * 0.25, '#2a3a2a', 255, scale=1.0)
        A.stroke(out, [(x0, y0), (x1, y1)], 1.0 - depth * 0.18, '#a8c0a0', 255, scale=1.0)
        if depth < 3:
            for s in (-1, 1):
                branch(x1, y1, ang + s * R.uniform(0.35, 0.6), l * 0.72, depth + 1)
        else:
            tips.append((x1, y1))
    branch(trunk[-1][0], trunk[-1][1], np.pi / 2, h * 0.13, 0)
    for (tx, ty) in tips:
        b = vorticella(11, seed + abs(int(tx * 10)) + 1, w=12)
        bh_ = b.shape[0] / SC
        paste(out, b, tx - b.shape[1] / SC / 2, ty - bh_ + 2.0)
    return trim(out)


def rotifer(w=24, h=12, seed=1):
    """a rotifer: a clear, segmented body, a forked foot behind, two wheels of beating cilia in front"""
    R = RS(seed)
    y, x = grid(h, w)
    t = x / w
    half = (h / 2 - 1) * np.maximum(np.sin(np.clip(t * 1.05, 0, 1) * np.pi), 0) ** 0.6 * (1 - 0.35 * t)
    m = (np.abs(y - h / 2) <= half) & (x > 3) & (x < w - 0.6)
    body = A.mask_sprite(m, ramp('#6a7a6a', '#9aae98', '#c8dcc4', '#eef8ea', '#ffffff'), '#1e2a1e', soft=1.2, ambient=0.5, hl_t=0.95)
    I = inner(body); I[..., 3] *= 0.85
    for k in range(4):                                     # segments
        sx = w * (0.35 + 0.13 * k)
        A.stroke(I, [(sx, h / 2 - half.max() * 0.8), (sx, h / 2 + half.max() * 0.8)], 0.25, '#4a5a4a', 120, scale=1.0)
    ellipse_soft(I, w * 0.42, h / 2, 2.4, 1.6, '#c8a050', 170)                 # its gut, food in it
    out = canvas(w + 6, h + 4)
    paste(out, body, 2, 1)
    for s in (-1, 1):                                     # the wheel organ: two crowns of cilia in front
        cx_, cy_ = 4.6, 2 + h / 2 + s * 2.2
        disc(out, cx_, cy_, 1.8, '#d8ecd4', 220)
        for k in range(10):
            a0 = k / 10 * TAU
            A.stroke(out, [(cx_ + np.cos(a0) * 1.8, cy_ + np.sin(a0) * 1.8), (cx_ + np.cos(a0) * 3.0, cy_ + np.sin(a0) * 3.0)], 0.2, '#e8f8e4', 230, scale=1.0)
    for s in (-1, 1):                                     # the toes
        A.stroke(out, [(w + 1.6, 2 + h / 2), (w + 4.6, 2 + h / 2 + s * 1.6)], 0.6, '#1e2a1e', 255, scale=1.0)
        A.stroke(out, [(w + 1.6, 2 + h / 2), (w + 4.6, 2 + h / 2 + s * 1.6)], 0.35, '#c8dcc4', 255, scale=1.0)
    return trim(out)


def filaments(seed=1, wdt=10):
    """filamentous bacteria hanging in long chains (bulking): thin beaded threads, some branching"""
    L = hang_len()
    R = RS(seed)
    W = wdt + 10
    out = canvas(W, L)
    for k in range(9):
        x0 = W / 2 + R.uniform(-wdt / 2, wdt / 2); l = R.uniform(0.6, 1.0) * L; ph = R.uniform(0, 6)
        pts = [(x0 + 2.0 * np.sin(t * l * 0.05 + ph) * t + 0.5 * np.sin(t * 20 + k), t * l) for t in np.linspace(0, 1, 60)]
        A.stroke(out, pts, 1.2, '#1e2a14', 255, scale=1.0)
        A.stroke(out, pts, 0.75, ['#8aa05a', '#a4b870', '#6e8a46'][k % 3], 255, scale=1.0)
        for i in range(0, 60, 3):                          # the cells along the thread
            px_, py_ = pts[i]
            ellipse_soft(out, px_, py_, 0.55, 0.35, '#c8dc98', 200)
    flo = floc(wdt + 4, 7, seed + 5)
    paste(out, flo, W / 2 - flo.shape[1] / SC / 2, -2)
    return trim(out)[:px(L)]


def T_aeration():
    far = aer_far()
    R = RS(1911)
    mid = wide()
    for k in range(14):
        g = floc(R.uniform(5, 9), R.uniform(4, 6), 1920 + k, alpha=0.85)
        put(mid, g, R.uniform(0, WT), R.uniform(26, GY - 20))
    for k in range(5):
        g = rotifer(R.uniform(9, 12), R.uniform(4.5, 6), 1940 + k); g[..., 3] *= 0.45
        put(mid, g, R.uniform(0, WT), R.uniform(30, GY - 30))
    bubble_chain(mid, 24, 1930, y0=40, y1=GY - 10, r=(1, 2), alpha=0.7, per=(4, 8))
    mid = crop(mid)
    floor = wall([(3, FLOC, pat_sludge), (12, CONC, pat_concrete), (40, SOIL, pat_soil)], True, seed=1941, bumps=0.5, out='#140e06')
    def extra(c3, R, rim_b, surf):                         # brown foam heaped on the surface
        for k in range(300):
            x = R.uniform(0, WT); r = R.uniform(0.8, 2.4)
            for off in (0, WT, 2 * WT):
                ellipse_soft(c3, x + off, R.uniform(8.5, 13.5), r * 1.3, r, ['#e8d8b0', '#c8b080', '#f8f0d8', '#a88a5a'][k % 4], 255)
    ceil = surf_ceil(1951, ramp('#3a3020', '#5a4a34', '#7a684c', '#9a8866', n=4), crown_h=5.0, air=('#8a7a5a', '#a8987a', '#c8b89a'),
                     mirror='#efe4c8', out='#2a1e10', extra=extra)
    obs = {'low': [floc(24, 12, 1), floc(20, 11, 2)],
           'tall': [vorticella(40, 1), vorticella(46, 2)],
           'hang': [filaments(1, 10), filaments(2, 12)],
           'float': [rotifer(24, 12, 1), floc(16, 12, 3)],
           'huge': [tower(lambda h: zoothamnium(h, 3, 26))]}
    return dict(far=far, mid=mid, floor=floor, ceil=ceil, obs=obs, coin='drop', special='soap')


# ================================================================== 17. the secondary clarifier (the water clearing)
WATER_C2 = '#6a9a96'


def clar2_far(seed=2001):
    R = RS(seed)
    far = gradient(H, ['#b4d4cc', '#94bcb4', '#76a29a', '#5a8680'])
    concrete_tex(far, seed + 1, k=0.6, cols=('#203230', '#e4f0ec'))
    y, x = grid(H, WT)
    TT.caustics(far, seed + 2, k=0.4)
    TT.light_shafts(far, seed + 3, n=8)
    c3 = three(far)
    for j in range(3):                                    # the launder: a trough along the top, its V-notch weir, water spilling over
        x0 = j * WT / 3
        g = canvas(WT / 3 + 2, 30)
        fill_rect(g, 0, 4, WT / 3 + 2, 20, '#6a7e7a', 255)
        fill_rect(g, 0, 4, WT / 3 + 2, 5.2, '#c8dcd8', 255)
        for i in range(int(WT / 3 / 6)):
            vx = i * 6 + 3
            A.stroke(g, [(vx - 3, 20), (vx, 26), (vx + 3, 20)], 1.0, '#2a3a38', 255, scale=1.0)
            A.stroke(g, [(vx - 3, 20), (vx, 26), (vx + 3, 20)], 0.6, '#a8bcb8', 255, scale=1.0)
        g[..., 3] *= 0.7
        put_wrap(c3, g, x0, 8)
    for k in range(80):                                   # flocs settling slowly, far off
        g = floc(R.uniform(2, 4), R.uniform(1.5, 3), seed + 10 + k, alpha=0.4)
        put_wrap(c3, g, R.uniform(0, WT), R.uniform(40, 140))
    far = crop(c3)
    silt(far, 138, ('#3a2e18', '#5a4626', '#7a643a', '#94804e'), seed + 4, k=0.8)
    c3 = three(far)
    drift(c3, 90, ['#ffffff', '#e8f4f0', '#c4dcd4'], seed + 5, y0=20, y1=GY - 6, a=130)
    far = crop(c3)
    haze(far, WATER_C2, 0.14)
    return far


def baffle(seed=1, wdt=10):
    """the scum baffle: a plate hanging from the surface in front of the weir, its brackets, a little scum on it"""
    L = hang_len()
    W = wdt + 8
    out = canvas(W, L)
    y, x = grid(L, W)
    m = (np.abs(x - W / 2) <= wdt / 2) & (y < L - 0.6)
    u = (x - W / 2) / (wdt / 2)
    sh = np.clip(0.62 - 0.4 * u, 0, 1)
    out[..., :3] = ramp_col(ramp('#2e3e3c', '#4e6462', '#728a86', '#9cb4ae', '#c4d8d2'), sh); out[..., 3] = smooth_mask(m) * 255
    for by in (12, 52, 92):
        fill_rect(out, 0.6, by - 1.4, W - 0.6, by + 1.4, '#1a2422', 255); fill_rect(out, 1.0, by - 1.0, W - 1.0, by + 0.6, '#8a9e9a', 255)
        disc(out, 2.2, by, 0.6, '#e0ece8', 255); disc(out, W - 2.2, by, 0.6, '#e0ece8', 255)
    lerp_rgb(out, '#6a5432', np.clip(noise(y.shape, 0.9, seed) - 0.1, 0, 1) * 0.5 * m * np.clip(1 - y / 30, 0, 1))
    lerp_rgb(out, '#4a6a3a', np.clip(noise(y.shape, 1.2, seed + 1) - 0.3, 0, 1) * 0.5 * m)
    return outline(out, '#101a18', width=0.6)[:px(L)]


def floc_pile(h, seed=1, w=24):
    h = int(round(h))
    spr = mass(w, h, seed, FLOC, FLOC_OUT, taper=0.5, wob=0.14, ambient=0.4, hl_t=0.995, grain_k=0.16)
    speckle(spr, seed + 1, int(w * h * 0.3), ['#2a1c0c', '#c8ae80', '#4a3618'], r=(0.2, 0.45), a=170)
    return spr


def T_clarifier2():
    far = clar2_far()
    R = RS(2011)
    mid = wide()
    for k in range(16):
        g = floc(R.uniform(4, 7), R.uniform(3, 5), 2020 + k, alpha=0.8)
        put(mid, g, R.uniform(0, WT), R.uniform(30, GY - 20))
    motes(mid, 90, ['#ffffff', '#d8ece6'], 2012, r=(0.3, 0.8), a=(110, 200))
    mid = crop(mid)
    floor = wall([(3, FLOC, pat_sludge), (12, CONC, pat_concrete), (40, SOIL, pat_soil)], True, seed=2041, bumps=0.6, out='#140e06')
    ceil = surf_ceil(2051, ramp('#7a9aa8', '#9ab8c4', '#bcd4de', '#dceaf0', n=4), crown_h=0.5, air=('#a8c8d4', '#c4dce6', '#e2f0f6'), mirror='#eef8f6', out='#2a3e3c')
    obs = {'low': [floc(26, 11, 11), floc_pile(12, 12, 24)],
           'tall': [floc_pile(40, 13, 22), floc_pile(46, 14, 24)],
           'hang': [baffle(1, 18)],
           'float': [floc(18, 12, 15), floc(15, 10, 16)],
           'huge': [tower(lambda h: floc_pile(h, 17, 26))]}
    return dict(far=far, mid=mid, floor=floor, ceil=ceil, obs=obs, coin='drop', special='soap')


# ================================================================== 18. UV disinfection
WATER_UV = '#4a7ea8'


def uv_tube(L, seed=1, wdt=6, glow=True):
    """a UV lamp in its quartz sleeve: a clear tube, the lamp inside glowing violet-blue, a steel cap"""
    W = wdt + 8
    out = canvas(W, L)
    y, x = grid(L, W)
    u = (x - W / 2) / (wdt / 2)
    m = (np.abs(u) <= 1) & (y < L - 0.6)
    a = smooth_mask(m)
    core = np.exp(-(u / 0.45) ** 2)
    rgb = ramp_col(ramp('#3a3a9a', '#7a6ae8', '#b8aaff', '#ece6ff', '#ffffff'), np.clip(0.35 + 0.65 * core, 0, 1))
    out[..., :3] = rgb; out[..., 3] = a * (150 + 105 * core)
    gl = (np.abs(u + 0.55) < 0.1) & m
    out[..., :3] = np.where(gl[..., None], 255, out[..., :3]); out[..., 3] = np.where(gl, 240, out[..., 3])
    out = outline(out, '#1a1a4a', alpha_cut=0.3, width=0.55)
    cap = canvas(W + 2, 6); fill_rect(cap, 1, 0, W + 1, 6, '#101418', 255); fill_rect(cap, 1.6, 0.6, W + 0.4, 5.4, '#8a929a', 255); fill_rect(cap, 1.6, 0.6, W + 0.4, 1.6, '#e0e6ea', 255)
    return out, cap


def uv_hang(seed=1):
    L = hang_len()
    t, cap = uv_tube(L - 4, seed)
    out = canvas(t.shape[1] / SC + 2, L)
    paste(out, cap, -0.2, 0)
    paste(out, t, 0, 5)
    return out[:px(L)]


def uv_stand(h=40, seed=1):
    t, cap = uv_tube(h - 6, seed)
    out = canvas(t.shape[1] / SC + 2, h)
    paste(out, t, 0, 0)
    paste(out, cap, -0.2, h - 6)
    return trim(out)


def uv_rack(h, seed=1, w=26):
    """a lamp rack: a steel frame holding three lamps upright"""
    h = int(round(h))
    out = canvas(w, h)
    for k in range(3):
        t, cap = uv_tube(h - 8, seed + k, wdt=4.2)
        paste(out, t, 1.5 + k * 7.6, 3)
    for yy in (1.0, h - 4.5):
        fill_rect(out, 0.6, yy, w - 0.6, yy + 3.6, '#101418', 255); fill_rect(out, 1.2, yy + 0.6, w - 1.2, yy + 3.0, '#8a929a', 255); fill_rect(out, 1.2, yy + 0.6, w - 1.2, yy + 1.4, '#e0e6ea', 255)
    for xr in (1.2, w - 1.2):
        A.stroke(out, [(xr, 1), (xr, h - 1)], 1.4, '#101418', 255, scale=1.0); A.stroke(out, [(xr, 1), (xr, h - 1)], 0.8, '#8a929a', 255, scale=1.0)
    return out


def wiper(w=16, h=9, seed=1):
    """a lamp sleeve's wiper ring come loose: a steel collar with its rubber wiping lip"""
    y, x = grid(h, w)
    r = np.sqrt(((x - w / 2) / (w / 2 - 0.8)) ** 2 + ((y - h / 2) / (h / 2 - 0.8)) ** 2)
    m = (r <= 1) & (r >= 0.45)
    spr = A.mask_sprite(m, GALV, '#101418', soft=0.8, ambient=0.4, hl_t=0.95)
    I = inner(spr)
    lip = (r < 0.6) & (r >= 0.45)
    lerp_rgb(I, '#1a1a1e', lip * 0.9)
    return spr


def uv_far(seed=2101):
    R = RS(seed)
    far = gradient(H, ['#8cc0e8', '#6aa2d4', '#4c84ba', '#36689a'])
    concrete_tex(far, seed + 1, k=0.4, cols=('#1a2a40', '#e0ecf8'))
    y, x = grid(H, WT)
    c3 = three(far)
    for j in range(4):                                    # racks of lamps across the channel, rows of them going back
        x0 = j * WT / 4 + 40
        for k in range(7):
            t, cap = uv_tube(110, seed + j * 10 + k, wdt=4.0)
            t[..., 3] *= 0.75
            put_wrap(c3, t, x0 + k * 9, 22)
            put_wrap(c3, cap, x0 + k * 9 - 0.2, 16)
        g = canvas(70, 4); fill_rect(g, 0, 0, 70, 4, '#2a3440', 255); fill_rect(g, 0, 0.4, 70, 1.2, '#a4b4c4', 255)
        put_wrap(c3, g, x0 - 4, 14); put_wrap(c3, g, x0 - 4, 134)
    far = crop(c3)
    for j in range(4):                                    # the violet glow round them
        x0 = j * WT / 4 + 40 + 30
        glow = np.exp(-(wdx(x, x0) / 60) ** 2) * np.clip(1 - np.abs(y - 78) / 80, 0, 1)
        lerp_rgb(far, '#c8b8ff', glow * 0.35)
    TT.caustics(far, seed + 2, k=0.35)
    c3 = three(far)
    drift(c3, 70, ['#ffffff', '#e0e8ff'], seed + 3, y0=20, y1=GY - 6, a=130)
    far = crop(c3)
    haze(far, WATER_UV, 0.1)
    return far


def T_uv():
    far = uv_far()
    R = RS(2111)
    mid = wide()
    motes(mid, 80, ['#ffffff', '#d8e0ff', '#b8c4ff'], 2112, r=(0.3, 0.8), a=(120, 220))
    bubble_chain(mid, 6, 2113, r=(1, 2), alpha=0.5)
    mid = crop(mid)
    floor = wall([(1.0, ramp('#4a5a6a', '#7a8a9a', '#a8b8c8', n=3), pat_slime), (12, ramp('#3e4a58', '#5e6c7a', '#808e9c', '#a2b0bc', n=4), pat_concrete), (40, SOIL, pat_soil)],
                 True, seed=2141, bumps=0.3, out='#0e1420')
    def extra(c3, R, rim_b, surf):
        for j in range(4):
            x0 = j * WT / 4 + 40
            for off in (0, WT, 2 * WT):
                fill_rect(c3, x0 + off - 4, 1.0, x0 + off + 66, 6.2, '#2a3440', 255)
                fill_rect(c3, x0 + off - 4, 1.4, x0 + off + 66, 2.2, '#a4b4c4', 255)
    ceil = surf_ceil(2151, ramp('#1a2230', '#2e3a4a', '#4a5a6c', '#6a7c8e', n=4), crown_h=6.6, air=('#2e3c50', '#4a5c72', '#6a8098'),
                     mirror='#e8f0ff', out='#121a2a', extra=extra)
    obs = {'low': [wiper(16, 9, 1), floc(18, 9, 21)],
           'tall': [uv_stand(40, 1), uv_stand(46, 2)],
           'hang': [uv_hang(1), uv_hang(2)],
           'float': [wiper(15, 9, 3), floc(13, 9, 23, alpha=0.9)],
           'huge': [tower(lambda h: uv_rack(h, 1, 26))]}
    return dict(far=far, mid=mid, floor=floor, ceil=ceil, obs=obs, coin='drop', special='soap')


# ================================================================== 19. the outfall: out into the river
WATER_OF = '#5e9a7a'
WEED = ramp('#1e4a1a', '#2e6e26', '#4a9a3a', '#7ac460', '#b4e894')


def outfall_far(seed=2201):
    R = RS(seed)
    far = gradient(H, ['#b8e4d4', '#8ac8b0', '#64a88e', '#447e6a'])
    y, x = grid(H, WT)
    TT.caustics(far, seed + 1, k=0.55)
    TT.light_shafts(far, seed + 2, n=9)
    c3 = three(far)
    for k in range(70):                                   # water plants waving on the riverbed far off
        bx = R.uniform(0, WT); hh = R.uniform(30, 90); ph = R.uniform(0, 6)
        g = canvas(16, hh)
        for b in range(3):
            pts = [(8 + (b - 1) * 1.5 + 3 * np.sin(t * 2.5 + ph + b) * t, hh - t * hh * R.uniform(0.7, 1.0)) for t in np.linspace(0, 1, 20)]
            A.stroke(g, pts, R.uniform(0.8, 1.4), ['#3a7a4a', '#4a8a52', '#2e6a40'][b], 200, scale=1.0)
        g[..., 3] *= R.uniform(0.35, 0.6)
        put_wrap(c3, g, bx - 8, 150 - hh)
    for j in range(2):                                    # the outfall's concrete headwall behind, the pipe's mouth in it
        x0 = j * WT / 2 + 150
        g = canvas(150, 120)
        fill_rect(g, 0, 0, 150, 120, '#7a8a80', 255)
        gy, gx = grid(120, 150)
        g[..., :3] *= (0.85 + 0.15 * noise(gy.shape, 1.0, seed + j))[..., None]
        m_ = mouth(70, 64, ramp('#4a5a52', '#9aaaa0', '#d4e0d8', n=3), deep=('#020806', '#0a1a14', '#1a3428'))
        paste(g, m_, 75 - m_.shape[1] / SC / 2, 70 - m_.shape[0] / SC / 2)
        g = outline(g, '#1a2a22')
        g[..., 3] *= 0.6
        put_wrap(c3, g, x0, 30)
    far = crop(c3)
    silt(far, 140, ('#5a5a3a', '#8a8458', '#b4ac7a', '#d4ca9a'), seed + 3, k=0.9)
    c3 = three(far)
    for k in range(200):
        g = SW_pebble(R.uniform(1.6, 4), R.uniform(1.2, 3), seed + 50 + k)
        put_wrap(c3, g, R.uniform(0, WT), R.uniform(142, 152))
    drift(c3, 90, ['#ffffff', '#e8fff4', '#c4ecd8'], seed + 4, y0=20, y1=GY - 6, a=140)
    far = crop(c3)
    haze(far, WATER_OF, 0.1)
    return far


def SW_pebble(w, h, seed):
    return pebble(w, h, seed)


def reeds(h=42, seed=1, w=20):
    """a clump of reeds growing up from the riverbed: long blades, a few bending over"""
    R = RS(seed)
    h = int(round(h))
    out = canvas(w, h)
    for k in range(9):
        x0 = w / 2 + R.uniform(-4, 4); l = R.uniform(0.6, 1.0) * (h - 1); bend = R.uniform(-1, 1) * 5
        pts = [(x0 + bend * t ** 2, h - 0.6 - l * t) for t in np.linspace(0, 1, 24)]
        for i in range(23):
            ww = max(0.4, 2.0 * (1 - i / 23))
            A.stroke(out, [pts[i], pts[i + 1]], ww + 0.6, '#0e2a0e', 255, scale=1.0)
        for i in range(23):
            ww = max(0.3, 2.0 * (1 - i / 23))
            A.stroke(out, [pts[i], pts[i + 1]], ww, ['#3a8a2a', '#4ea036', '#2e7424'][k % 3], 255, scale=1.0)
            A.stroke(out, [(pts[i][0] - ww * 0.25, pts[i][1]), (pts[i + 1][0] - ww * 0.25, pts[i + 1][1])], ww * 0.3, '#a8e47a', 200, scale=1.0)
    return trim(out)


def algae(seed=1, wdt=12):
    """long green algae streaming down from the outfall's lip in the current"""
    L = hang_len()
    R = RS(seed)
    W = wdt + 12
    out = canvas(W, L)
    for k in range(10):
        x0 = W / 2 + R.uniform(-wdt / 2, wdt / 2); l = R.uniform(0.6, 1.0) * L; ph = R.uniform(0, 6)
        pts = [(x0 + 3.0 * np.sin(t * 3.0 + ph) * t, t * l) for t in np.linspace(0, 1, 40)]
        for i in range(39):
            ww = max(0.4, 1.8 * (1 - i / 39 * 0.6))
            A.stroke(out, [pts[i], pts[i + 1]], ww + 0.5, '#0e2a0e', 255, scale=1.0)
        for i in range(39):
            ww = max(0.3, 1.8 * (1 - i / 39 * 0.6))
            A.stroke(out, [pts[i], pts[i + 1]], ww, ['#3a8a2a', '#5aa83e', '#2e7424'][k % 3], 255, scale=1.0)
    return trim(out)[:px(L)]


def fish(w=24, h=10, seed=1):
    """a small river fish (a minnow): silver-green back, a dark stripe, fins, an eye"""
    R = RS(seed)
    y, x = grid(h, w)
    t = x / w
    half = (h / 2 - 1) * np.maximum(np.sin(np.clip(t * 1.1, 0, 1) * np.pi), 0) ** 0.7 * (1 - 0.3 * t)
    body = (np.abs(y - h / 2) <= half) & (x > 0.6) & (x < w * 0.86)
    tail = (x >= w * 0.8) & (x < w - 0.6) & (np.abs(y - h / 2) <= (x - w * 0.8) * 0.9 + 0.6)
    m = body | tail
    u = (y - h / 2) / (h / 2)
    spr = A.mask_sprite(m, ramp('#2a3a2a', '#5a7a5a', '#a4c0a0', '#dce8d8', '#ffffff'), '#0e1a0e', soft=1.0, ambient=0.4, hl_t=0.93)
    I = inner(spr)
    lerp_rgb(I, '#3e5a3a', (u < -0.15)[..., None][..., 0] * body * 0.5)
    lerp_rgb(I, '#1e2a1e', (np.abs(u - 0.05) < 0.12) * body * (t > 0.2) * 0.45)
    ellipse_soft(I, w * 0.16, h * 0.42, 0.9, 0.9, '#0a0a0a', 255); ellipse_soft(I, w * 0.15, h * 0.39, 0.3, 0.3, '#ffffff', 230)
    return spr


def T_outfall():
    far = outfall_far()
    R = RS(2211)
    mid = wide()
    for k in range(6):
        g = fish(R.uniform(8, 12), R.uniform(3.5, 5), 2220 + k); g[..., 3] *= 0.5
        put(mid, g, R.uniform(0, WT), R.uniform(30, GY - 40))
    motes(mid, 100, ['#ffffff', '#e8fff4', '#c4ecd8'], 2212, r=(0.3, 0.8), a=(110, 200))
    bubble_chain(mid, 6, 2213, r=(1, 2), alpha=0.5)
    mid = crop(mid)
    BED = ramp('#4a4428', '#76704a', '#a49e74', '#c8c29a', '#e2dcb8', n=5)
    floor = wall([(6, BED, pat_gravel), (40, ramp('#2a2618', '#443e28', '#5e563a', '#7a7050', n=4), pat_soil)], True, seed=2241, bumps=1.0, out='#141008',
                 surface=lambda c3, e, e0, top: pebble_surface(c3, e, e0, top, seed=2242, n=170, r=(0.8, 2.6)))
    ceil = surf_ceil(2251, ramp('#8ac4e8', '#a8d6f2', '#c8e6fa', '#e8f6ff', n=4), crown_h=0.5, air=('#a4d8f4', '#c4e8fa', '#e4f6ff'), mirror='#f2fff8', out='#2a4a3a')
    obs = {'low': [pebble(24, 11, 1), pebble(20, 10, 2)],
           'tall': [reeds(42, 1, 20), reeds(48, 2, 22)],
           'hang': [algae(1, 12), algae(2, 10)],
           'float': [fish(24, 10, 1), fish(20, 9, 2)],
           'huge': [tower(lambda h: cairn(h, 7, 24))]}
    return dict(far=far, mid=mid, floor=floor, ceil=ceil, obs=obs, coin='drop', special='soap')


# ------------------------------------------------------------------ the treatment works' hazards (in common.webp)
def floc_drop():
    """a big floc sinking: it gathers under the surface and drops"""
    return floc(13, 12, 41)


def floc_mat(w=26, h=9):
    """the floc landed: a soft brown mat on the floor"""
    y, x = grid(h, w)
    n = noise(y.shape, 0.6, 43)
    top = h - 3.6 - 0.9 * np.abs(np.sin(x * 0.7)) - 0.6 * n
    m = (y >= top) & (y <= h - 0.6) & (np.abs(x - w / 2) <= w / 2 - 1.2)
    spr = A.mask_sprite(m, FLOC, FLOC_OUT, soft=0.9, ambient=0.4, hl_t=0.99)
    return speckle(spr, 44, 40, ['#2a1c0c', '#c8ae80'], r=(0.2, 0.4), a=170)


def grit_spike(size='s', seed=6):
    """a sharp shard of stone and gravel pushed up out of the sand"""
    R = RS(seed + (5 if size == 't' else 0))
    w, h = (15, 21) if size == 's' else (17, 33)
    y, x = grid(h, w)
    t = np.clip(y / h, 0, 1)
    cx = w / 2 - 0.5 + 1.2 * (1 - t) * (1 if seed % 2 else -1)
    jag = 0.5 * np.sin(y * 1.7 + seed) + 0.35 * np.sin(y * 3.9)
    half = 0.5 + (w / 2 - 0.8) * t ** 0.85 + jag * t
    m = np.abs(x - cx) <= half
    spr = A.mask_sprite(m, ramp('#3a3a36', '#62625a', '#8e8e82', '#b8b8aa', '#dcdcd0'), '#141410', soft=0.6, ambient=0.3, hl_t=0.97)
    I = inner(spr)
    facet = (x - cx) * 0.6 + (y - h * 0.4) * 0.15 > 0
    I[..., :3] *= np.where(facet, 0.86, 1.0)[..., None]
    speckle(spr, seed, int(w * h * 0.2), ['#2a2a24', '#e8e4d8'], r=(0.2, 0.45), a=160)
    rows = np.nonzero(spr[..., 3].max(axis=1) > 20)[0]
    return spr[:rows.max() + 1]


def pebble_shot():
    """what the flow throws at you, spinning: a pebble of grit"""
    out = canvas(13, 11)
    paste(out, pebble(11, 9, 3), 0, 0)
    return out


def hazards():
    return {'hz_drop_floc': floc_drop(), 'hz_puddle_floc': floc_mat(), 'hz_spike_grit_s': grit_spike('s'),
            'hz_spike_grit_t': grit_spike('t'), 'hz_shot_pebble': pebble_shot()}
