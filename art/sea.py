# Stage 3, the sea (places 9-19): sandy shallows (shallows), the rocky shore (rocky), the kelp forest (kelp), the coral
# reef (coral), a bloom of jellyfish (jellies), a school of sardines (school), a wreck (wreck), the drop-off (dropoff), the
# deep sea (deep), the hydrothermal vents (vent), and into a whale's mouth (whale): down from the light to the dark,
# and back into a body.
import numpy as np
import cv2
from art import (H, SC, px, grid, canvas, ramp, ramp_col, hexc, paint, ellipse_mask, outline, paste, over, blur, disc,
                 ellipse_soft, inner, smooth_mask, fill_rect)
import anatomy as A
from tiles import WT, GY, FH, FY0, CH, TAU, wide, crop, put, per_sin, gradient, haze, pcells, wall, band_line, spots
from themes import three, drift, tower, stack, hang_len, bubble, flip_v
from variants import noise
from s3lib import (put_wrap, faded, scaled, water_far, glow_spots, sky_ceil, foam_extra, bed, things_on_bed,
                   ripples_surface, pat_sand, pat_mud, pat_rock, stone, boulder, rock_spire, fish, school, ribbons,
                   ribbons_hang, weed_far, crab, shell_sprite, starfish, urchin, anemone, jelly, kelp, coral_branch,
                   brain_coral, fan, bubbles_sprite, lerp_rgb, mul, motes, bubble_chain, pat_soil, silt, trim, blob_mask,
                   lump, speckle, STONES)
from river import mid_fish, shrimp, oyster_clump
import sewer as SW

RS = np.random.RandomState
SAND = ramp('#8a7a52', '#b4a476', '#d4c69a', '#ecdfb8', '#fff4d8', n=5)
SAND_D = ramp('#5a4e34', '#7a6c4a', '#9a8c66', '#b8aa84', n=4)
ROCK = ramp('#2a2e30', '#464c50', '#6a7276', '#8e989c', '#b4bcbe', n=5)
RUST = ramp('#2a140a', '#4a2412', '#74381a', '#9a5226', '#c07a44')


def rot(spr, deg):
    M = cv2.getRotationMatrix2D((spr.shape[1] / 2, spr.shape[0] / 2), deg, 1.0)
    return cv2.warpAffine(spr, M, (spr.shape[1], spr.shape[0]))


# ------------------------------------------------------------------ things of the sea
def hermit(w=18, h=14, seed=1):
    """a hermit crab in a whelk shell: the shell's spiral, the crab's claws and legs out of its mouth"""
    o = canvas(w, h)
    sh = shell_sprite(w * 0.7, h * 0.95, seed, cols=('#5a3a2a', '#8a5e44', '#b8886a', '#dcb496', '#f4dcc4'), out='#24140c', kind='cone')
    sh = rot(sh, -70)
    paste(o, sh, w * 0.3, h - sh.shape[0] / SC - 0.2)
    c = crab(w * 0.55, h * 0.55, seed + 3, cols=('#6a1a0a', '#a8341a', '#d0582e', '#ec8a52', '#ffc08a'))
    paste(o, c, 0.2, h - c.shape[0] / SC)
    return trim(o)


def barnacle_rock(w=24, h=13, seed=1):
    """a rock crusted with barnacles and a mussel or two"""
    r = boulder(w, h, seed, STONES[2])
    I = inner(r); R = RS(seed)
    for k in range(int(w * h / 10)):
        x, y = R.uniform(2, w - 2), R.uniform(1, h - 2)
        if A.on(r, x + 1, y + 1):
            ellipse_soft(I, x, y, 0.9, 0.7, '#e8e4d8', 240); ellipse_soft(I, x, y + 0.1, 0.35, 0.25, '#3a3a34', 240)
    for k in range(3):
        x, y = R.uniform(3, w - 4), R.uniform(h * 0.4, h - 2)
        if A.on(r, x + 1, y + 1):
            ellipse_soft(I, x, y, 1.6, 0.8, '#1a1a2e', 255, 0.5); ellipse_soft(I, x - 0.4, y - 0.3, 0.8, 0.3, '#5a5a8a', 220, 0.5)
    return r


def mussel_rope(seed=1):
    """a farm rope hanging from a buoy line, mussels thick along it"""
    Lh = hang_len()
    R = RS(seed)
    o = canvas(14, Lh)
    A.stroke(o, [(7, 0), (7, Lh - 2)], 0.9, '#1a1408', 255, scale=1.0)
    A.stroke(o, [(7, 0), (7, Lh - 2)], 0.5, '#b49a6a', 255, scale=1.0)
    for k in range(int(Lh / 2.2)):
        y = 6 + k * 2.2 + R.uniform(-0.6, 0.6)
        if y > Lh - 3:
            break
        for s_ in (-1, 1):
            if R.uniform() < 0.8:
                x = 7 + s_ * R.uniform(1.0, 3.6)
                ellipse_soft(o, x, y, 1.8, 0.9, '#0a0a14', 255, s_ * R.uniform(0.6, 1.2))
                ellipse_soft(o, x - 0.3, y - 0.3, 1.2, 0.35, '#4a4a74', 220, s_ * 0.9)
    return trim(o)[:px(Lh)]


def sea_grass(h, seed=1, w=20):
    return ribbons(h, seed, w, ('#2e7a3a', '#3e8e46', '#56a85a'), out='#0a2a12', n=11, wid=1.6, hi='#b4ecb4')


def sargassum_hang(seed=1):
    """drifting gulfweed hanging from the surface: branching yellow-brown stems, little round floats"""
    s = ribbons_hang(seed, 14, ('#8a6a1a', '#a8842a', '#6e5212'), out='#2a1e04', n=8, wid=1.1)
    R = RS(seed)
    I = s
    for k in range(80):
        x, y = R.uniform(3, s.shape[1] / SC - 3), R.uniform(2, s.shape[0] / SC - 2)
        if A.on(s, x, y):
            ellipse_soft(I, x + 0.8, y, 0.75, 0.75, '#3a2a06', 255); ellipse_soft(I, x + 0.6, y - 0.2, 0.5, 0.5, '#d8b44a', 255)
    return s


def kelp_hang(seed=1):
    """kelp blades hanging down from the canopy at the surface: broad, wavy, brown-gold"""
    return ribbons_hang(seed, 18, ('#7a5e1a', '#a8842a', '#c8a64a'), out='#1e1404', n=6, wid=3.4)


def sea_whip(h, seed=1, w=16, col='#e8b42a', out='#3a2604'):
    """sea whips: a few thin bright rods straight up from the bed"""
    R = RS(seed)
    h = int(round(h))
    o = canvas(w, h)
    for k in range(5):
        x0 = w / 2 + R.uniform(-w * 0.3, w * 0.3); l = R.uniform(0.6, 1.0) * (h - 1); b = R.uniform(-3, 3)
        pts = [(x0 + b * t ** 2, h - 0.5 - l * t) for t in np.linspace(0, 1, 20)]
        A.stroke(o, pts, 1.3, out, 255, scale=1.0)
        A.stroke(o, pts, 0.8, col, 255, scale=1.0)
        A.stroke(o, [(p[0] - 0.2, p[1]) for p in pts], 0.25, '#fff4c8', 200, scale=1.0)
    return trim(o)


def sardine(seed):
    return fish(16, 5, seed, back='#1a3a6a', side='#9ab8d0', belly='#f4f8fc', kind='sardine', spots_col='#1a2a4a', fin='#9ab0c4', out='#0a1428')


def sardine_ball(r, seed, n=None):
    """a bait ball: sardines wheeling in a tight round crowd"""
    R = RS(seed)
    n = n or int(r * r * 0.5)
    o = canvas(2 * r + 18, 2 * r + 10)
    for k in range(n):
        a = R.uniform(0, TAU); d = r * np.sqrt(R.uniform(0, 1))
        f = scaled(sardine(seed + k % 7), R.uniform(0.45, 0.7))
        if np.cos(a) > 0:                                     # going round: some this way, some that
            f = f[:, ::-1].copy()
        paste(o, f, r + 4 + np.cos(a) * d, r + 4 + np.sin(a) * d * 0.8)
    return trim(o)


def sardine_column(h, seed=1, w=26):
    """sardines in a tall twisting column"""
    R = RS(seed)
    h = int(round(h))
    o = canvas(w + 8, h)
    for k in range(int(h * 1.6)):
        y = R.uniform(2, h - 3); x = w / 2 + (w / 2 - 4) * np.sin(y * 0.14 + R.uniform(0, 0.8)) * R.uniform(0.3, 1.0)
        f = scaled(sardine(seed + k % 7), 0.6)
        if R.uniform() < 0.5:
            f = f[:, ::-1].copy()
        paste(o, f, x, y)
    return trim(o)


def barrel(w=16, h=18, seed=1):
    """an old barrel on the bed: staves, rusted hoops, weed on it"""
    y, x = grid(h, w)
    m = (np.abs(x - w / 2) <= (w / 2 - 0.8) * (0.86 + 0.14 * np.sin(np.clip(y / h, 0, 1) * np.pi))) & (y > 0.6) & (y < h - 0.6)
    s = A.mask_sprite(m, ramp('#2a1a0e', '#4a3220', '#6e5034', '#94744e', '#b89a72'), '#120a04', soft=1.0, ambient=0.3, hl_t=0.98)
    I = inner(s)
    lerp_rgb(I, '#1a0e06', (np.abs(np.mod(x, 3.0) - 1.5) < 0.18) * m * 0.5)
    for yy in (h * 0.2, h * 0.5, h * 0.8):
        lerp_rgb(I, '#7a3a1a', (np.abs(y - yy) < 0.7) * m * 0.85)
    lerp_rgb(I, '#4a6a2a', (noise(y.shape, 0.8, seed) > 0.5) * m * 0.35)
    return s


def anchor(h=44, seed=1, w=30):
    """a rusted anchor standing on its crown: the shank, the stock across the top, the curved arms and their flukes"""
    h = int(round(h))
    o = canvas(w, h)
    cx = w / 2
    arc = [(cx + np.sin(a) * w * 0.4, h - 3 - np.cos(a) * h * 0.18 * -1 - h * 0.18) for a in np.linspace(-1.35, 1.35, 30)]
    for wd, col in ((3.0, '#140804'), (2.2, '#7a3a1a')):
        A.stroke(o, [(cx, 5), (cx, h - 2)], wd, col, 255, scale=1.0)
        A.stroke(o, arc, wd, col, 255, scale=1.0)
        A.stroke(o, [(cx - w * 0.3, 7), (cx + w * 0.3, 7)], wd * 0.9, col, 255, scale=1.0)
    for s_ in (-1, 1):
        fx, fy = arc[0 if s_ < 0 else -1]
        tri = [(fx, fy), (fx + s_ * 3.4, fy - 1.4), (fx + s_ * 0.6, fy - 5.4)]
        A.stroke(o, tri + [tri[0]], 2.4, '#140804', 255, scale=1.0)
        A.stroke(o, tri + [tri[0]], 1.6, '#8a4a22', 255, scale=1.0)
    ring = [(cx + 2.2 * np.cos(a), 2.6 + 2.2 * np.sin(a)) for a in np.linspace(0, TAU, 24)]
    A.stroke(o, ring, 1.4, '#140804', 255, scale=1.0); A.stroke(o, ring, 0.8, '#7a3a1a', 255, scale=1.0)
    R = RS(seed)
    for k in range(40):
        x, y = R.uniform(0, w), R.uniform(0, h)
        if o[min(int(y * SC), o.shape[0] - 1), min(int(x * SC), o.shape[1] - 1), 3] > 200:
            ellipse_soft(o, x, y, R.uniform(0.3, 0.7), R.uniform(0.2, 0.5), ['#c07a44', '#3a1a0a', '#4a6a3a'][k % 3], 200)
    return trim(o)


def chain_hang(seed=1):
    """an anchor chain hanging down from above: big rusted links"""
    Lh = hang_len()
    o = canvas(12, Lh)
    k = 0; y = 0.0
    while y < Lh - 4:
        if k % 2 == 0:
            ring = [(6 + 2.0 * np.cos(a), y + 2.6 + 2.6 * np.sin(a)) for a in np.linspace(0, TAU, 26)]
            A.stroke(o, ring, 1.6, '#140804', 255, scale=1.0); A.stroke(o, ring, 1.0, '#8a4a22', 255, scale=1.0)
        else:
            A.stroke(o, [(6, y + 0.4), (6, y + 4.8)], 1.7, '#140804', 255, scale=1.0); A.stroke(o, [(6, y + 0.4), (6, y + 4.8)], 1.1, '#7a3a1a', 255, scale=1.0)
        y += 4.0; k += 1
    return trim(o)[:px(Lh)]


def octopus(w=22, h=16, seed=1, cols=('#5a1a1a', '#9a3a2a', '#c8644a', '#e8946e', '#ffc8a8'), out='#2a0806'):
    """an octopus swimming: a round mantle, big eyes, eight arms trailing back curling"""
    R = RS(seed)
    o = canvas(w + 4, h + 2)
    for k in range(8):
        y0 = h * 0.55 + (k - 3.5) * 0.7; ph = R.uniform(0, 6); L = w * R.uniform(0.55, 0.75)
        pts = [(w * 0.38 + L * t, y0 + 2.4 * np.sin(t * 4 + ph) * t) for t in np.linspace(0, 1, 26)]
        for i in range(25):
            A.stroke(o, [pts[i], pts[i + 1]], 1.6 * (1 - i / 30) + 0.5, out, 255, scale=1.0)
        for i in range(25):
            A.stroke(o, [pts[i], pts[i + 1]], 1.6 * (1 - i / 30), cols[2], 255, scale=1.0)
    m = ellipse_mask(w * 0.5, h * 0.75)
    mt = A.mask_sprite(m, ramp(*cols), out, soft=1.3, ambient=0.35, hl_t=0.94)
    paste(o, mt, 0.5, 0.5)
    I = o
    for s_ in (0, 1):
        ex, ey = w * 0.18 + s_ * 3.2, h * 0.5
        ellipse_soft(I, ex, ey, 1.3, 1.1, '#fff4e0', 255); ellipse_soft(I, ex, ey, 0.9, 0.35, '#0a0a0a', 255)
    return trim(o)


def mast(h, seed=1, w=22):
    """a wreck's broken mast: a thick spar up from the bed, a cross-yard, torn rigging hanging off it, weed on it"""
    h = int(round(h))
    o = canvas(w, h)
    for wd, col in ((4.2, '#140a04'), (3.4, '#5a4026')):
        A.stroke(o, [(w / 2, h - 0.5), (w / 2 + 0.8, 1.5)], wd, col, 255, scale=1.0)
    A.stroke(o, [(w / 2 - 0.6, h - 0.5), (w / 2 + 0.2, 1.5)], 0.9, '#8a6a44', 200, scale=1.0)
    for wd, col in ((2.4, '#140a04'), (1.8, '#5a4026')):
        A.stroke(o, [(1.0, h * 0.25), (w - 1.0, h * 0.22)], wd, col, 255, scale=1.0)
    R = RS(seed)
    for k in range(4):
        x0 = R.uniform(2, w - 2); y0 = h * 0.235
        A.stroke(o, [(x0, y0), (x0 + R.uniform(-2, 2), y0 + R.uniform(10, 24))], 0.3, '#c8b48a', 230, scale=1.0)
    n = noise(grid(h, w)[0].shape, 1.0, seed)
    lerp_rgb(o, '#3a6a2a', (n > 0.5) * (o[..., 3] > 200) * 0.4)
    return trim(o)


def ray(w=34, h=16, seed=1, cols=('#2a2a34', '#4a4a5a', '#6e6e80', '#9696a8', '#c4c4d4'), out='#0a0a12'):
    """a ray gliding, seen a little from above: a broad diamond of wings, its eyes, a long thin tail"""
    y, x = grid(h, w)
    cx, cy = w * 0.42, h / 2
    dx, dy = np.abs(x - cx) / (w * 0.42), np.abs(y - cy) / (h / 2 - 0.6)
    m = (dx ** 1.15 + dy ** 1.0 <= 1.0) & ~((x < cx) & (dy < 0.12) & (dx > 0.92))
    s = A.mask_sprite(m, ramp(*cols), out, soft=1.6, ambient=0.35, hl_t=0.95)
    I = inner(s)
    lerp_rgb(I, '#000000', (np.abs(y - cy) < h * 0.12) * (np.abs(x - cx) < w * 0.22) * m * 0.18)       # the body down the middle
    for k in range(14):
        ellipse_soft(I, cx + RS(seed).uniform(-w * 0.3, w * 0.3), cy + RS(seed + k).uniform(-h * 0.35, h * 0.35), 0.5, 0.5, cols[4], 120)
    o = canvas(w + 14, h)
    paste(o, s, 0, 0)
    A.stroke(o, [(cx + w * 0.38, cy + 1), (w + 13, cy + 2.2)], 0.45, out, 255, scale=1.0)
    for k in (-1, 1):
        ellipse_soft(o, cx - w * 0.06 + 1, cy + k * 1.6 + 1, 0.55, 0.45, '#e8e8f0', 240)
    return trim(o)


def sea_cucumber(w=22, h=8, seed=1):
    """a sea cucumber lying on the ooze: a soft lumpy sausage with knobs"""
    s = lump(w, h, seed, ramp('#3a1a22', '#5e2e38', '#844a52', '#a86e74', '#cc9a9e'), '#1a0a0e', bumps=9)
    I = inner(s); R = RS(seed)
    for k in range(30):
        x, y = R.uniform(1, w - 1), R.uniform(0.5, h - 1.5)
        if A.on(s, x + 1, y + 1):
            ellipse_soft(I, x, y, 0.5, 0.4, '#e8b4b8', 220)
    return s


def glass_sponge(h, seed=1, w=18):
    """a glass sponge: a tall pale vase of see-through lattice, glowing faintly"""
    h = int(round(h))
    y, x = grid(h, w)
    t = y / h
    half = (w / 2 - 1) * (0.45 + 0.55 * (1 - t) ** 0.5) * (0.8 + 0.2 * np.sin(y * 0.3 + seed))
    m = (np.abs(x - w / 2) <= half) & (y > 1.0)
    s = A.mask_sprite(m, ramp('#6a7a86', '#98aab4', '#c4d4dc', '#e8f4f8', '#ffffff'), '#22303a', soft=1.2, ambient=0.5, hl_t=0.96)
    I = inner(s)
    lat = (np.abs(np.mod(x + y * 0.5, 2.2) - 1.1) < 0.15) | (np.abs(np.mod(x - y * 0.5, 2.2) - 1.1) < 0.15)
    lerp_rgb(I, '#ffffff', lat * m * 0.5)
    lerp_rgb(I, '#22303a', (np.abs(x - w / 2) < half * 0.45) * (y < 6) * m * 0.6)       # its open top
    s[..., 3] *= 0.92
    return s


def siphonophore(seed=1, cols=('#ff6a9a', '#ffd06a', '#8ae8ff')):
    """a long glowing string hanging in the dark: a chain of little bells and lights"""
    Lh = hang_len()
    R = RS(seed)
    o = canvas(16, Lh)
    pts = [(8 + 2.4 * np.sin(t * 5 + seed), t * (Lh - 2)) for t in np.linspace(0, 1, 60)]
    A.stroke(o, pts, 0.35, '#e8f4ff', 200, scale=1.0)
    for i in range(0, 60, 2):
        x, y = pts[i]
        c = cols[(i // 2) % len(cols)]
        ellipse_soft(o, x, y, 2.8, 2.8, c, 50)
        ellipse_soft(o, x, y, 1.3, 1.0, c, 230)
        ellipse_soft(o, x - 0.3, y - 0.3, 0.45, 0.45, '#ffffff', 240)
        if i % 6 == 0:
            for s_ in (-1, 1):
                A.stroke(o, [(x, y), (x + s_ * 3.4, y + 2.2), (x + s_ * 4.0, y + 4.6)], 0.2, '#c8e8ff', 170, scale=1.0)
    return trim(o)[:px(Lh)]


def angler(w=24, h=14, seed=1):
    """an anglerfish: a dark round body, a huge jaw full of fangs, a glowing lure on a rod over its head"""
    f = fish(w, h, seed, back='#14121a', side='#2e2a34', belly='#4a4452', kind='goby', out='#000000', fin='#24202a', eye=0.8)
    o = canvas(w + 4, h + 10)
    paste(o, f, 2, 8)
    for k in range(6):                                      # fangs
        x = 3.2 + k * 1.0
        A.stroke(o, [(x, 8 + h * 0.62), (x + 0.2, 8 + h * 0.62 - 1.6)], 0.35, '#f4f0e0', 255, scale=1.0)
    rod = [(6.0, 8 + h * 0.3), (5.0, 4.0), (2.4, 2.0)]
    A.stroke(o, rod, 0.4, '#3a3440', 255, scale=1.0)
    ellipse_soft(o, 2.2, 2.0, 4.0, 4.0, '#aaffee', 70)
    ellipse_soft(o, 2.2, 2.0, 1.3, 1.3, '#eafff8', 255)
    return trim(o)


def smoker(h, seed=1, w=24):
    """a black smoker: a lumpy chimney of dark sulphide rock, orange-hot at its foot, black smoke out of its top"""
    h = int(round(h))
    R = RS(seed)
    sh = h - 14
    m = blob_mask(w, sh, seed, taper=0.55, wob=0.2)
    s = A.mask_sprite(m, ramp('#0e0a08', '#2a2018', '#4a3a2a', '#6e5a40', '#94805c'), '#000000', soft=1.4, ambient=0.25, hl_t=0.97)
    I = inner(s)
    y, x = grid(I.shape[0] / SC, I.shape[1] / SC)
    lerp_rgb(I, '#ff7a1a', np.clip((y - sh * 0.75) / (sh * 0.25), 0, 1) ** 2 * (I[..., 3] > 0) * 0.55)
    lerp_rgb(I, '#c8a04a', (noise(y.shape, 0.5, seed) > 0.55) * (I[..., 3] > 0) * 0.3)
    o = canvas(w + 10, h)
    paste(o, s, 5, h - s.shape[0] / SC)
    for k in range(14):                                     # the smoke
        yy = 14 - k * 1.2; xx = w / 2 + 5 + R.uniform(-1, 1) * k * 0.5
        ellipse_soft(o, xx, yy, 2.2 + k * 0.45, 1.8 + k * 0.3, '#14100e', int(200 - k * 12))
    return trim(o)


def tube_worms(h, seed=1, w=22):
    """giant tube worms: a clump of white tubes, red plumes out of their tops"""
    R = RS(seed)
    h = int(round(h))
    o = canvas(w, h)
    tubes = []
    for k in range(7):
        x0 = w / 2 + R.uniform(-w * 0.35, w * 0.35); l = R.uniform(0.55, 1.0) * (h - 5); b = R.uniform(-2.5, 2.5)
        tubes.append([(x0 + b * t ** 2, h - 0.5 - l * t) for t in np.linspace(0, 1, 20)])
    for pts in tubes:
        A.stroke(o, pts, 2.6, '#1a1a14', 255, scale=1.0)
    for pts in tubes:
        A.stroke(o, pts, 2.0, '#e8e4d4', 255, scale=1.0)
        A.stroke(o, [(p[0] - 0.4, p[1]) for p in pts], 0.6, '#ffffff', 200, scale=1.0)
        tx, ty = pts[-1]
        for j in range(7):
            a = -np.pi / 2 + (j - 3) * 0.32
            A.stroke(o, [(tx, ty), (tx + np.cos(a) * 3.2, ty + np.sin(a) * 3.2)], 0.9, '#3a0806', 255, scale=1.0)
            A.stroke(o, [(tx, ty), (tx + np.cos(a) * 3.0, ty + np.sin(a) * 3.0)], 0.6, '#e8243a', 255, scale=1.0)
    return trim(o)


def vent_rock(w=22, h=11, seed=1):
    """a vent's crust of dark rock, white crabs on it, a shimmer of hot water"""
    o = canvas(w, h + 2)
    r = boulder(w, h, seed, ('#0e0c0a', '#2a2420', '#4a4038', '#6e6252', '#948670'))
    paste(o, r, 0, 2)
    c = crab(8, 4.5, seed + 4, cols=('#8a8a84', '#b4b4ac', '#d8d8d0', '#f0f0e8', '#ffffff'), out='#2a2a26')
    paste(o, c, w * 0.45, 2.6)
    return trim(o)


def eelpout(seed):
    return fish(26, 7, seed, back='#4a3a44', side='#8a7a84', belly='#d4c8cc', kind='goby', out='#1a1016', fin='#6a5a64', spots_col='#3a2a34')


def baleen_hang(seed=1):
    """the whale's baleen: a long curtain of plates hanging from the roof of its mouth, a hairy fringe at their edge"""
    Lh = hang_len()
    R = RS(seed)
    W = 22
    o = canvas(W, Lh)
    for k in range(9):
        x0 = 2 + k * 2.2; l = Lh * (0.75 + 0.25 * np.sin(k / 8 * np.pi))
        pts = [(x0 + 1.2 * t, l * t) for t in np.linspace(0, 1, 16)]
        A.stroke(o, pts, 2.2, '#140c08', 255, scale=1.0)
        A.stroke(o, pts, 1.6, ['#3a2e24', '#4a3c2e', '#2e241c'][k % 3], 255, scale=1.0)
        A.stroke(o, [(p[0] - 0.4, p[1]) for p in pts], 0.4, '#7a6a5a', 180, scale=1.0)
        for j in range(18):                                  # the fringe
            yy = l * (0.3 + 0.7 * j / 17)
            A.stroke(o, [(x0 + 1.2 * yy / l + 0.8, yy), (x0 + 1.2 * yy / l + 2.8, yy + 1.6)], 0.25, '#c8b48a', 200, scale=1.0)
    return trim(o)[:px(Lh)]


def krill(w=9, h=4, seed=1):
    return shrimp(w, h, seed)


def krill_pile(w=24, h=8, seed=1):
    """a heap of krill on the tongue"""
    R = RS(seed)
    o = canvas(w, h)
    for k in range(26):
        s = krill(R.uniform(5, 7), R.uniform(2.4, 3.2), seed + k)
        s = rot(s, R.uniform(-40, 40))
        yy = h - s.shape[0] / SC - R.uniform(0, h * 0.6) * (1 - abs(k / 26 - 0.5) * 2)
        paste(o, s, R.uniform(0, w - 6), max(0, yy))
    return trim(o)


def krill_column(h, seed=1, w=24):
    """krill being drawn in, in a tall swirling column"""
    R = RS(seed)
    h = int(round(h))
    o = canvas(w + 8, h)
    for k in range(int(h * 2.2)):
        y = R.uniform(1, h - 3); x = w / 2 + (w / 2 - 3) * np.sin(y * 0.16 + R.uniform(0, 1.2)) * R.uniform(0.2, 1.0)
        f = rot(krill(R.uniform(6, 8), R.uniform(2.6, 3.4), seed + k), R.uniform(-60, 60))
        paste(o, f, x, y)
    return trim(o)


def tongue_bump(h=12, w=26, seed=1):
    """the whale's tongue heaving up in a soft ridge"""
    y, x = grid(h, w)
    m = (((x - w / 2) / (w / 2 - 0.8)) ** 2 + ((y - h) / (h - 0.8)) ** 2 <= 1) & (y > 0.8)
    s = A.mask_sprite(m, ramp('#5a1a2a', '#8a2e40', '#b44a5a', '#d8707e', '#f4a8b0'), '#240810', soft=1.8, ambient=0.32, hl_t=0.96)
    I = inner(s)
    lerp_rgb(I, '#5a1a2a', (np.abs(np.mod(y + 0.3 * x, 4) - 2) < 0.2) * m * 0.35)
    return s


# ================================================================== 9. sandy shallows
def shallows_far(seed=4101, cols=('#cff6f2', '#98e6e6', '#60c8d8', '#38a0bc')):
    R = RS(seed)
    far = water_far(cols, seed, caust=0.9, shafts=11)
    c3 = three(far)
    weed_far(c3, 50, seed + 3, ['#3e9a6a', '#4eaa74', '#2e8a5a'], h=(14, 40), a=(0.3, 0.55), w=1.3)
    for k in range(18):
        g = boulder(R.uniform(20, 46), R.uniform(10, 22), seed + 20 + k, STONES[1])
        put_wrap(c3, faded(g, cols[2], 0.55, 0.8), R.uniform(0, WT), 150 - g.shape[0] / SC)
    far = crop(c3)
    silt(far, 146, ('#a89a6e', '#c8ba8e', '#e2d6ae', '#f6ecd0'), seed + 4, k=0.9)
    c3 = three(far)
    drift(c3, 70, ['#ffffff', '#e8fffc'], seed + 5, y0=20, y1=GY - 6, a=130)
    return crop(c3)


def T_shallows():
    far = shallows_far()
    mid = mid_fish(4111, 9, lambda s: fish(14, 6, s, back='#3a7a8a', side='#a8dce4', belly='#f4fcfc', stripes=1, stripe_col='#f0d04a', fin='#9ad0d8'), a=0.45)
    floor = bed(4141, SAND, SAND_D, pat_top=pat_sand, pat_deep=pat_sand, out='#3a301a', top_th=10,
                surface=lambda c3, e, e0, top: (ripples_surface(4142)(c3, e, e0, top),
                                                things_on_bed([shell_sprite(5, 3.4, 4150 + k) for k in range(3)] + [starfish(7, 3, 4155)], 40, 4143, sink=0.3)(c3, e, e0, top)))
    ceil = sky_ceil(4151)
    obs = {'low': [starfish(18, 8, 91), hermit(18, 14, 92)],
           'tall': [sea_grass(44, 93), sea_grass(50, 94)],
           'hang': [ribbons_hang(95, 12, ('#3e9a4a', '#5ab45a', '#2e8a3e'), out='#0a2a10', wid=2.0), sargassum_hang(96)],
           'float': [fish(20, 8, 97, back='#3a7a8a', side='#a8dce4', belly='#f4fcfc', stripes=1, stripe_col='#f0d04a', fin='#9ad0d8'),
                     fish(18, 9, 98, back='#e8b42a', side='#ffd84a', belly='#fff4c0', fin='#ffc83a', out='#3a2804')],
           'huge': [tower(lambda h: rock_spire(h, 99, 26, STONES[1]))]}
    return dict(far=far, mid=mid, floor=floor, ceil=ceil, obs=obs, coin='drop', special='pearl')


# ================================================================== 10. the rocky shore
def rocky_far(seed=4201, cols=('#b4e4ec', '#80c4d6', '#5498b4', '#327092')):
    R = RS(seed)
    far = water_far(cols, seed, caust=0.6, shafts=9)
    c3 = three(far)
    for k in range(26):                                     # big rocks piled along the shore, near and far
        near = k % 2
        g = boulder(R.uniform(40, 90), R.uniform(30, 70), seed + 20 + k, STONES[2])
        put_wrap(c3, faded(g, cols[2] if not near else cols[1], 0.65 if not near else 0.4, 0.85), R.uniform(0, WT), 152 - g.shape[0] / SC)
    weed_far(c3, 40, seed + 3, ['#6a5a1a', '#8a7a2a', '#4e6a22'], h=(14, 34), a=(0.4, 0.65), w=1.4)
    far = crop(c3)
    silt(far, 148, ('#4a4e4a', '#6a6e68', '#8e928a', '#b0b4aa'), seed + 4, k=0.85)
    c3 = three(far)
    drift(c3, 70, ['#ffffff', '#e8fffc'], seed + 5, y0=20, y1=GY - 6, a=120)
    return crop(c3)


def T_rocky():
    far = rocky_far()
    mid = mid_fish(4211, 7, lambda s: fish(16, 7, s, back='#2e5a3a', side='#7aa47a', belly='#e4f0dc', bars=3, bar_col='#1e3a26', fin='#6a9a6a'), a=0.4)
    floor = bed(4241, ROCK, ramp('#1e2224', '#34393c', '#4c5256', '#666c70', n=4), pat_top=pat_rock, pat_deep=pat_rock, out='#0a0c0e', top_th=8,
                surface=things_on_bed([barnacle_rock(8, 4, 4250 + k) for k in range(3)] + [urchin(6, 5, 4255)], 50, 4243, sink=0.4))
    ceil = sky_ceil(4251, extra=foam_extra(50, 4252))
    obs = {'low': [urchin(16, 12, 101), barnacle_rock(24, 12, 102)],
           'tall': [anemone(42, 103), anemone(48, 104, cols=('#1a5a3a', '#2a8a5a', '#4ab47a', '#8ae0a8', '#c8ffd8'), tent=('#8af0b4', '#e0fff0'), out='#062414')],
           'hang': [mussel_rope(105), mussel_rope(106)],
           'float': [fish(22, 9, 107, back='#2e5a3a', side='#7aa47a', belly='#e4f0dc', bars=3, bar_col='#1e3a26', fin='#6a9a6a'),
                     fish(20, 9, 108, back='#7a3a5a', side='#c87aa0', belly='#f8e0ec', fin='#b46a8a', stripes=2, stripe_col='#3aa0d0')],
           'huge': [tower(lambda h: rock_spire(h, 109, 28, STONES[2]))]}
    return dict(far=far, mid=mid, floor=floor, ceil=ceil, obs=obs, coin='drop', special='pearl')


# ================================================================== 11. the kelp forest
def kelp_far(seed=4301, cols=('#a8dcd0', '#74b8aa', '#4a9084', '#2c665e')):
    R = RS(seed)
    far = water_far(cols, seed, caust=0.35, shafts=12)
    c3 = three(far)
    for layer in range(2):                                  # kelp stalks up to the surface, two depths
        for k in range(26 if layer == 0 else 18):
            g = kelp(R.uniform(110, 150), seed + 40 + layer * 50 + k, 22)
            put_wrap(c3, faded(g, cols[2] if layer == 0 else cols[1], 0.65 if layer == 0 else 0.35, 0.75 if layer == 0 else 0.9), R.uniform(0, WT), 152 - g.shape[0] / SC)
    far = crop(c3)
    silt(far, 146, ('#4a4a3a', '#6a6a52', '#8e8c70', '#b0ae92'), seed + 4, k=0.85)
    c3 = three(far)
    drift(c3, 90, ['#ffffff', '#e0f4e8'], seed + 5, y0=20, y1=GY - 6, a=120)
    return crop(c3)


def filefish(seed):
    return fish(20, 13, seed, back='#5a5a3a', side='#a4a070', belly='#e4e0c0', kind='file', spots_col='#4a4a2a', fin='#8a8a5a', out='#1a1a0a')


def T_kelp():
    far = kelp_far()
    mid = mid_fish(4311, 6, filefish, a=0.35)
    floor = bed(4341, ramp('#3a3a2e', '#5a5a48', '#7e7c66', '#a4a28a', '#c8c6ae', n=5), SAND_D, pat_top=pat_sand, out='#121208',
                surface=things_on_bed([stone(6, 3.6, 4350 + k) for k in range(3)] + [urchin(6, 5, 4355), shell_sprite(5, 3.4, 4356)], 60, 4343, sink=0.4))
    ceil = sky_ceil(4351, sky=('#9ccad8', '#b8dce6', '#d4ecf2'), mirror='#dcf0ea')
    obs = {'low': [urchin(16, 12, 111, body=('#2a1a0a', '#4a2e14', '#6e4a22', '#946a34', '#b8904a'), spine='#3a2410', tip='#e0b46a'), barnacle_rock(22, 12, 112)],
           'tall': [kelp(44, 113, 22), kelp(50, 114, 24)],
           'hang': [kelp_hang(115), kelp_hang(116)],
           'float': [filefish(117), filefish(118)],
           'huge': [tower(lambda h: kelp(h, 119, 26))]}
    return dict(far=far, mid=mid, floor=floor, ceil=ceil, obs=obs, coin='drop', special='pearl')


# ================================================================== 12. the coral reef
CORAL_COLS = [('#8a1a3a', '#c83a5a', '#f06a84', '#ff9ab0', '#ffd0dc'), ('#7a3a0a', '#c06a1a', '#f09a3a', '#ffc070', '#ffe4b0'),
              ('#3a1a7a', '#5a3ab4', '#8a6ae0', '#b4a0f8', '#e0d4ff'), ('#0a5a5a', '#1a8a8a', '#3ab4b4', '#7ae0dc', '#c4fff8')]


def clownfish(seed):
    return fish(14, 8, seed, back='#e8640a', side='#ff8a1a', belly='#ffb04a', bars=3, bar_col='#ffffff', out='#3a1400', fin='#ff9a2a')


def anemone_home(seed=1):
    """a low anemone on the reef, a clownfish nestled in it"""
    o = canvas(26, 16)
    a = anemone(14, seed, w=24, stalk=False, cols=('#7a5a1a', '#b4882a', '#e0b44a', '#f8d88a', '#fff0c8'), tent=('#ffd27a', '#fff4d0'), out='#2a1e06')
    paste(o, a, 0, 16 - a.shape[0] / SC)
    c = clownfish(seed + 2)
    paste(o, c, 6, 16 - a.shape[0] / SC - 3)
    return trim(o)


def coral_far(seed=4401, cols=('#b4f0f6', '#74d4ee', '#42acdc', '#2280be')):
    R = RS(seed)
    far = water_far(cols, seed, caust=0.75, shafts=10)
    c3 = three(far)
    for k in range(70):                                      # the reef: coral heads of all kinds and colours, far and near
        kind = k % 4; near = k % 3 == 0; cc = CORAL_COLS[k % 4]
        if kind == 0:
            g = coral_branch(R.uniform(26, 50), seed + 30 + k, 26, cols=cc)
        elif kind == 1:
            g = brain_coral(R.uniform(18, 34), R.uniform(10, 18), seed + 30 + k)
        elif kind == 2:
            g = fan(R.uniform(26, 46), seed + 30 + k, 26, col=cc[2], hi=cc[4], out=cc[0])
        else:
            g = coral_branch(R.uniform(16, 26), seed + 30 + k, 30, cols=cc, thick=2.4)
        put_wrap(c3, faded(g, cols[2] if not near else cols[1], 0.55 if not near else 0.3, 0.85), R.uniform(0, WT), 151 - g.shape[0] / SC)
    far = crop(c3)
    silt(far, 148, ('#b4a47a', '#d0c498', '#e8dcb8', '#fff4d8'), seed + 4, k=0.8)
    c3 = three(far)
    drift(c3, 80, ['#ffffff', '#e8fffc'], seed + 5, y0=20, y1=GY - 6, a=130)
    return crop(c3)


def lionfish(seed):
    return fish(24, 12, seed, back='#7a2a14', side='#e8a07a', belly='#ffe8dc', kind='lion', bars=4, bar_col='#5a1a0a', fin='#f0c4a8', out='#2a0a04')


def T_coral():
    far = coral_far()
    mid = mid_fish(4411, 12, lambda s: [clownfish(s), fish(14, 9, s, back='#1a3ab4', side='#3a7ae8', belly='#a4d4ff', fin='#ffe03a', out='#06124a'),
                                        fish(14, 8, s, back='#e8c80a', side='#fff04a', belly='#fffcc0', fin='#ffd80a', out='#3a3000', bars=1, bar_col='#1a1a1a')][s % 3], a=0.55)
    floor = bed(4441, SAND, SAND_D, pat_top=pat_sand, pat_deep=pat_sand, out='#3a301a', top_th=8,
                surface=things_on_bed([coral_branch(7, 4450 + k, 7, cols=CORAL_COLS[k % 4], thick=0.9) for k in range(4)] + [shell_sprite(5, 3.4, 4456)], 50, 4443, sink=0.2))
    ceil = sky_ceil(4451)
    obs = {'low': [brain_coral(24, 12, 121), anemone_home(122)],
           'tall': [coral_branch(44, 123, 26, cols=CORAL_COLS[0]), fan(48, 124, 26, col='#8a4ae0', hi='#d4b4ff', out='#24084a')],
           'hang': [sargassum_hang(125), ribbons_hang(126, 12, ('#3e9a4a', '#5ab45a', '#2e8a3e'), out='#0a2a10', wid=2.0)],
           'float': [lionfish(127), lionfish(128)],
           'huge': [tower(lambda h: stack([brain_coral(26 - k * 1.5, 12, 129 + k) for k in range(int(h / 10) + 1)], gap=-2.5))]}
    return dict(far=far, mid=mid, floor=floor, ceil=ceil, obs=obs, coin='drop', special='pearl')


# ================================================================== 13. a bloom of jellyfish
JELLY_C = [('#6a8ac8', '#9ab4e8', '#c8d8f8', '#eaf2ff'), ('#c86a9a', '#e89ab8', '#f8c8dc', '#fff0f6'), ('#c8a04a', '#e8c46a', '#f8e0a0', '#fff6dc')]


def jellies_far(seed=4501, cols=('#8ccaf0', '#58a2dc', '#2e78c0', '#1a5298')):
    R = RS(seed)
    far = water_far(cols, seed, caust=0.35, shafts=9)
    c3 = three(far)
    for k in range(90):                                     # jellies everywhere, small and faint far off
        r = R.uniform(2.5, 7); j = jelly(r, seed + 20 + k, JELLY_C[k % 3], L=r * R.uniform(2.5, 4.5), a=0.8)
        put_wrap(c3, faded(j, cols[1], R.uniform(0.3, 0.6), R.uniform(0.4, 0.75)), R.uniform(0, WT), R.uniform(10, 120))
    far = crop(c3)
    silt(far, 148, ('#3a5a7a', '#5a7a94', '#7e9aae', '#a4bcca'), seed + 4, k=0.75)
    c3 = three(far)
    drift(c3, 70, ['#ffffff', '#e0f0ff'], seed + 5, y0=20, y1=GY - 6, a=110)
    return crop(c3)


def T_jellies():
    far = jellies_far()
    mid = mid_fish(4511, 10, lambda s: jelly(4 + s % 3, s, JELLY_C[s % 3], L=16, a=0.8), a=0.6)
    floor = bed(4541, ramp('#4a5a64', '#6a7a82', '#8e9ca2', '#b4c0c4', '#d4dcde', n=5), ramp('#2a3238', '#3e484e', '#566066', '#6e787e', n=4),
                pat_top=pat_sand, pat_deep=pat_sand, out='#0e1418', top_th=8, surface=ripples_surface(4542, col='#e8f4ff', n=30))
    ceil = sky_ceil(4551, sky=('#7ab4dc', '#9ac8e8', '#bcdcf4'), mirror='#d8ecfa', out='#1a3450')
    obs = {'low': [shell_sprite(16, 9, 131, kind='clam'), sea_cucumber(22, 8, 132)],
           'tall': [sea_whip(44, 133), sea_whip(48, 134, col='#e86a8a', out='#3a0a14')],
           'hang': [jelly(8, 135, JELLY_C[0], L=hang_len() - 9, a=0.85), jelly(9, 136, JELLY_C[1], L=hang_len() - 10, a=0.85)],
           'float': [jelly(6, 137, JELLY_C[2], L=10, a=0.9), jelly(5, 138, JELLY_C[0], L=9, a=0.9)],
           'huge': [tower(lambda h: stack([jelly(10 - (k % 2), 139 + k, JELLY_C[k % 3], L=4, a=0.95) for k in range(int(h / 11) + 1)], gap=-1))]}
    return dict(far=far, mid=mid, floor=floor, ceil=ceil, obs=obs, coin='drop', special='pearl')


# ================================================================== 14. a school of sardines
def school_far(seed=4601, cols=('#7cc0e6', '#4c96cc', '#286cac', '#14488a')):
    R = RS(seed)
    far = water_far(cols, seed, caust=0.3, shafts=10)
    c3 = three(far)
    for j in range(3):                                      # great balls of sardines turning, flashing silver
        ball = sardine_ball(R.uniform(30, 48), seed + 10 + j)
        put_wrap(c3, faded(ball, cols[1], 0.35, 0.85), j * WT / 3 + R.uniform(0, 120), R.uniform(10, 50))
    for k in range(40):
        f = scaled(sardine(seed + 60 + k), R.uniform(0.35, 0.55))
        put_wrap(c3, faded(f, cols[1], 0.4, 0.6), R.uniform(0, WT), R.uniform(20, 130))
    far = crop(c3)
    silt(far, 148, ('#3a4a5a', '#56687a', '#768a9a', '#98aaba'), seed + 4, k=0.8)
    return far


def T_school():
    far = school_far()
    mid = mid_fish(4611, 14, lambda s: school(6, 16, 5, s, sardine, (40, 20)), a=0.5, y0=20, y1=GY - 30)
    floor = bed(4641, ramp('#3e4a52', '#5a6870', '#7a8a92', '#9eacb2', '#c0ccd0', n=5), ramp('#22282c', '#343c42', '#4a5258', '#626a70', n=4),
                pat_top=pat_sand, pat_deep=pat_rock, out='#0a1014', top_th=6,
                surface=things_on_bed([stone(6, 3.6, 4650 + k, STONES[2]) for k in range(3)] + [shell_sprite(5, 3.4, 4655)], 50, 4643, sink=0.4))
    ceil = sky_ceil(4651, sky=('#6aa4d0', '#8abce0', '#acd4ee'), mirror='#cce4f6', out='#163050')
    obs = {'low': [boulder(24, 13, 141, STONES[2]), boulder(22, 12, 142, STONES[0])],
           'tall': [sardine_column(42, 143, 22), sardine_column(48, 144, 24)],
           'hang': [ribbons_hang(145, 10, ('#c8d4dc', '#e8f0f4', '#a8b8c4'), out='#2a3a4a', wid=0.6, n=6),  # (a fishing net's torn strands)
                    ribbons_hang(146, 12, ('#c8d4dc', '#e8f0f4', '#a8b8c4'), out='#2a3a4a', wid=0.6, n=7)],
           'float': [school(4, 16, 5, 147, sardine, (18, 10)), school(5, 16, 5, 148, sardine, (22, 12))],
           'huge': [tower(lambda h: sardine_column(h, 149, 28))]}
    return dict(far=far, mid=mid, floor=floor, ceil=ceil, obs=obs, coin='drop', special='pearl')


# ================================================================== 15. a wreck
def wreck_far(seed=4701, cols=('#5a96b2', '#3a7896', '#225a76', '#123c56')):
    R = RS(seed)
    far = water_far(cols, seed, caust=0.2, shafts=7, deep=True)
    c3 = three(far)
    for j in range(2):                                      # the hull lying over on the bed: rusted plates, portholes, a broken deck rail, the mast
        x0 = j * WT / 2 + 80
        Wh, Hh = 380, 90
        y, x = grid(Hh, Wh)
        top = 20 + 8 * np.sin(np.clip(x / Wh, 0, 1) * np.pi) * 0 + 0.06 * x
        bow = x > Wh - 60
        m = (y > top) & ~(bow & (y < top + (x - (Wh - 60)) * 1.2)) & (x > 0)
        g = canvas(Wh, Hh)
        g[..., :3] = ramp_col(RUST, np.clip(0.55 + 0.25 * noise(y.shape, 1.6, seed + j) - 0.3 * ((y - top) / Hh), 0, 1))
        g[..., 3] = m * 255.0
        lerp_rgb(g, '#1a0a04', (np.abs(np.mod(x, 18) - 9) < 0.25) * m * 0.5)
        lerp_rgb(g, '#1a0a04', (np.abs(np.mod(y - top, 12) - 6) < 0.25) * m * 0.4)
        lerp_rgb(g, '#3a6a3a', (noise(y.shape, 0.8, seed + 7 + j) > 0.45) * m * 0.35)
        for k in range(9):
            ellipse_soft(g, 30 + k * 36, top[0, min(int((30 + k * 36) * SC), top.shape[1] - 1)] + 18, 3.2, 3.2, '#0a0806', 255)
        g = outline(g, '#0a0604')
        put_wrap(c3, faded(g, cols[2], 0.5, 0.9), x0, 150 - Hh + 6)
        mg = mast(110, seed + 20 + j, 30)
        put_wrap(c3, faded(rot(mg, -18), cols[2], 0.55, 0.85), x0 + 140, 150 - Hh - 60)
    far = crop(c3)
    silt(far, 146, ('#3a4a4e', '#566468', '#748286', '#949fa2'), seed + 4, k=0.85)
    c3 = three(far)
    drift(c3, 90, ['#d0e4ec', '#b0ccd8'], seed + 5, y0=20, y1=GY - 6, a=110)
    return crop(c3)


def T_wreck():
    far = wreck_far()
    mid = mid_fish(4711, 5, lambda s: fish(16, 7, s, back='#3a4a5a', side='#8a9aaa', belly='#dce4ec', fin='#6a7a8a'), a=0.35)
    floor = bed(4741, ramp('#2e383c', '#465256', '#626e72', '#828e90', '#a2acae', n=5), ramp('#1a2024', '#2a3236', '#3c4448', '#50585c', n=4),
                pat_top=pat_sand, pat_deep=pat_soil, out='#080c0e',
                surface=things_on_bed([stone(6, 3.4, 4751, STONES[2]), shell_sprite(5, 3.4, 4752), stone(4, 2.6, 4753, STONES[0])], 40, 4743, sink=0.4))
    obs = {'low': [barrel(16, 15, 151), SW.pet_bottle(22, 8, 152)],
           'tall': [anchor(44, 153), anchor(48, 154, 32)],
           'hang': [chain_hang(155), chain_hang(156)],
           'float': [octopus(22, 16, 157), octopus(20, 15, 158, cols=('#3a1a4a', '#6a3a7a', '#9a64a8', '#c494cc', '#ecccf0'), out='#14061a')],
           'huge': [tower(lambda h: mast(h, 159, 24))]}
    return dict(far=far, mid=mid, floor=floor, ceil=None, obs=obs, coin='drop', special='pearl')


# ================================================================== 16. the drop-off
def dropoff_far(seed=4801, cols=('#3e80b8', '#24609a', '#144074', '#08244c')):
    R = RS(seed)
    far = water_far(cols, seed, caust=0.12, shafts=8, deep=True)
    y, x = grid(H, WT)
    c3 = three(far)
    for j in range(2):                                      # the cliff going down into the dark: a rock face, ledges, fans on it
        x0 = j * WT / 2
        Wc = 260
        yy, xx = grid(H, Wc)
        edge = 40 + 25 * np.sin(yy * 0.05 + j) + 10 * np.sin(yy * 0.17)
        m = xx < edge + (Wc - 120)
        g = canvas(Wc, H)
        g[..., :3] = ramp_col(ROCK, np.clip(0.45 + 0.3 * noise(yy.shape, 2.0, seed + j) - 0.25 * yy / H, 0, 1))
        g[..., 3] = m * 255.0
        cb, _, _ = pcells(H, 40, seed + 10 + j, sy=1.0, border=0.7, ww=Wc)
        lerp_rgb(g, '#000000', cb[:g.shape[0], :g.shape[1]] ** 4 * m * 0.4)
        g = outline(g, '#04080c')
        put_wrap(c3, faded(g, cols[2], 0.55, 0.95), x0, 0)
        for k in range(10):
            f = fan(R.uniform(18, 34), seed + 40 + k + j * 20, 22, col=['#c8402a', '#e8a02a', '#8a4ae0'][k % 3], hi='#ffd0a0', out='#2a0a04')
            put_wrap(c3, faded(rot(f, -90), cols[2], 0.45, 0.8), x0 + R.uniform(80, 160), R.uniform(10, 140))
    far = crop(c3)
    mul(far, 1 - 0.3 * np.clip((y - 90) / 60, 0, 1))
    return far


def T_dropoff():
    far = dropoff_far()
    mid = mid_fish(4811, 4, lambda s: ray(30, 9, s), a=0.3)
    floor = bed(4841, ROCK, ramp('#14181c', '#24292e', '#363c42', '#4a5056', n=4), pat_top=pat_rock, pat_deep=pat_rock, out='#04080a', top_th=8,
                surface=things_on_bed([urchin(6, 5, 4850), stone(6, 3.6, 4851, STONES[2]), fan(6, 4852, 6, col='#e8a02a', hi='#ffe0a0', out='#3a1a04')], 40, 4843, sink=0.3))
    obs = {'low': [boulder(24, 12, 161, STONES[2]), urchin(16, 12, 162)],
           'tall': [fan(44, 163, 26), fan(48, 164, 28, col='#e8a02a', hi='#ffe8b4', out='#3a1a04')],
           'hang': [ribbons_hang(165, 10, ('#c8d8ff', '#e4ecff', '#a8bce8'), out='#1a2a4a', wid=0.9, n=5), jelly(7, 166, JELLY_C[0], L=hang_len() - 8, a=0.8)],
           'float': [ray(34, 10, 167), ray(30, 9, 168, cols=('#1a2a3a', '#2e4256', '#4a6078', '#6a849a', '#9ab0c4'))],
           'huge': [tower(lambda h: rock_spire(h, 169, 28, STONES[2]))]}
    return dict(far=far, mid=mid, floor=floor, ceil=None, obs=obs, coin='drop', special='pearl')


# ================================================================== 17. the deep sea
def deep_far(seed=4901, cols=('#121e3a', '#0c1428', '#08101e', '#040810')):
    far = gradient(H, cols)
    far = glow_spots(far, 160, seed + 1, ['#8ae8ff', '#ff8ab4', '#c8ff8a', '#aab4ff'], r=(0.25, 0.8), y0=5, y1=GY - 5, a=(0.3, 0.9))
    R = RS(seed)
    c3 = three(far)
    for k in range(10):                                     # glass sponges far off, glowing faintly
        g = glass_sponge(R.uniform(30, 60), seed + 20 + k, 16)
        put_wrap(c3, faded(g, cols[1], 0.6, 0.6), R.uniform(0, WT), 150 - g.shape[0] / SC)
    drift(c3, 140, ['#c8d4e8', '#a0b0c8'], seed + 5, y0=10, y1=GY - 4, a=90)     # marine snow
    far = crop(c3)
    silt(far, 146, ('#10141c', '#1a2028', '#262e38', '#343e4a'), seed + 4, k=0.9)
    return far


def T_deep():
    far = deep_far()
    mid = wide()
    R = RS(4911)
    for k in range(6):
        g = scaled(angler(24, 14, 4920 + k), R.uniform(0.4, 0.6)); g[..., 3] *= 0.45
        put(mid, g, R.uniform(0, WT), R.uniform(30, GY - 40))
    motes(mid, 120, ['#c8d4e8', '#8ae8ff', '#ffffff'], 4912, r=(0.25, 0.6), a=(60, 160))
    mid = crop(mid)
    floor = bed(4941, ramp('#14181e', '#22282e', '#30383e', '#444c52', '#5a6268', n=5), ramp('#080a0c', '#101418', '#1a1e22', '#24282c', n=4),
                pat_top=pat_mud, pat_deep=pat_soil, out='#000000', top_th=8,
                surface=things_on_bed([sea_cucumber(8, 3, 4950), faded(shell_sprite(5, 3.4, 4951), '#1a2028', 0.5)], 30, 4943, sink=0.3))
    obs = {'low': [sea_cucumber(22, 8, 171), sea_cucumber(20, 7, 172)],
           'tall': [glass_sponge(42, 173, 18), glass_sponge(48, 174, 20)],
           'hang': [siphonophore(175), siphonophore(176, cols=('#8ae8ff', '#c8ff8a', '#ffffff'))],
           'float': [angler(24, 14, 177), angler(22, 13, 178)],
           'huge': [tower(lambda h: glass_sponge(h, 179, 24))]}
    return dict(far=far, mid=mid, floor=floor, ceil=None, obs=obs, coin='drop', special='pearl')


# ================================================================== 18. the hydrothermal vents
def vent_far(seed=5001, cols=('#1a1e28', '#12151e', '#0c0e14', '#08080a')):
    R = RS(seed)
    far = gradient(H, cols)
    c3 = three(far)
    for k in range(14):                                     # black smokers far off: their glow at the foot, their smoke going up
        g = smoker(R.uniform(50, 110), seed + 20 + k, R.uniform(16, 30))
        xx = R.uniform(0, WT)
        for off in (0, WT, 2 * WT):
            ellipse_soft(c3, xx + off + g.shape[1] / SC / 2, 148, 26, 10, '#ff6a1a', 60)
        put_wrap(c3, faded(g, cols[1], 0.4, 0.8), xx, 150 - g.shape[0] / SC)
    for k in range(8):
        t = tube_worms(R.uniform(16, 30), seed + 60 + k, 20)
        put_wrap(c3, faded(t, cols[1], 0.45, 0.8), R.uniform(0, WT), 150 - t.shape[0] / SC)
    drift(c3, 100, ['#a0a8b4', '#c8c0b0'], seed + 5, y0=10, y1=GY - 4, a=80)
    far = crop(c3)
    silt(far, 146, ('#0e0c0a', '#1e1a16', '#2e2822', '#40382e'), seed + 4, k=0.9)
    return far


def T_vent():
    far = vent_far()
    mid = mid_fish(5011, 5, eelpout, a=0.3)
    floor = bed(5041, ramp('#0e0c0a', '#221e1a', '#3a332c', '#544a40', '#6e6252', n=5), ramp('#060504', '#100e0c', '#1a1714', '#24201c', n=4),
                pat_top=pat_rock, pat_deep=pat_rock, out='#000000', top_th=8,
                surface=things_on_bed([vent_rock(9, 4, 5050), tube_worms(7, 5051, 7)], 30, 5043, sink=0.3))
    obs = {'low': [vent_rock(22, 11, 181), vent_rock(20, 10, 182)],
           'tall': [tube_worms(42, 183), tube_worms(48, 184, 24)],
           'hang': [siphonophore(185, cols=('#ff9a4a', '#ffd06a', '#ff6a6a')), siphonophore(186, cols=('#ffd06a', '#ffffff', '#ff9a4a'))],
           'float': [eelpout(187), eelpout(188)],
           'huge': [tower(lambda h: smoker(h, 189, 24))]}
    return dict(far=far, mid=mid, floor=floor, ceil=None, obs=obs, coin='drop', special='pearl')


# ================================================================== 19. into a whale's mouth
def whale_far(seed=5101, cols=('#5a2a34', '#48202a', '#361620', '#220a12')):
    R = RS(seed)
    far = gradient(H, cols)
    y, x = grid(H, WT)
    for j in range(2):                                      # the light coming in at the mouth's opening, far ahead
        d = np.hypot((np.mod(x - j * WT / 2 - 300 + WT / 2, WT) - WT / 2) / 140, (y - 80) / 60)
        lerp_rgb(far, '#7ab4d0', np.clip(1 - d, 0, 1) ** 1.6 * 0.6)
    lerp_rgb(far, '#8a3a48', np.clip(0.5 + 0.5 * np.sin(x * TAU * 9 / WT + y * 0.04), 0, 1) ** 6 * 0.25)   # the gums' folds
    c3 = three(far)
    for k in range(140):                                    # the baleen curtain along the top, far side
        g = canvas(4, 70)
        A.stroke(g, [(2, 0), (2.6, R.uniform(40, 68))], R.uniform(1.0, 1.8), ['#2a2018', '#3a2e22', '#1e1610'][k % 3], 255, scale=1.0)
        g[..., 3] *= 0.75
        put_wrap(c3, g, R.uniform(0, WT), 0)
    for k in range(60):
        f = scaled(krill(9, 4, seed + 30 + k), 0.6)
        put_wrap(c3, faded(f, cols[1], 0.4, 0.7), R.uniform(0, WT), R.uniform(40, 140))
    far = crop(c3)
    return far


def T_whale():
    far = whale_far()
    mid = mid_fish(5111, 14, lambda s: krill(9, 4, s), a=0.5)
    floor = wall([(5, ramp('#6a1e30', '#9a3448', '#c4566a', '#e4808e', '#fab4bc', n=5), 'loose'), (40, ramp('#3a0a18', '#5a1426', '#7a2236', '#9a3448', n=4), 'smooth')],
                 True, seed=5141, bumps=1.6, out='#1e0610',
                 surface=things_on_bed([krill(6, 3, 5150 + k) for k in range(3)], 40, 5143, sink=0.2))
    obs = {'low': [krill_pile(24, 8, 191), tongue_bump(12, 26, 192)],
           'tall': [krill_column(42, 193, 22), krill_column(48, 194, 24)],
           'hang': [baleen_hang(195), baleen_hang(196)],
           'float': [school(5, 9, 4, 197, lambda s: krill(9, 4, s), (16, 8)), sardine(198)],
           'huge': [tower(lambda h: krill_column(h, 199, 28))]}
    return dict(far=far, mid=mid, floor=floor, ceil=None, obs=obs, coin='drop', special='pearl')


# ------------------------------------------------------------------ stage 3's hazards and its special (in common.webp)
def hazards():
    import s3lib as L
    return {'it_pearl': L.pearl_item(),
            'hz_drop_leaf': L.leaf_drop(), 'hz_puddle_leaf': L.leaf_mat(), 'hz_spike_rock_s': L.rock_spike('s'), 'hz_spike_rock_t': L.rock_spike('t'),
            'hz_drop_shell': L.shell_drop(), 'hz_puddle_shell': L.shell_mat(), 'hz_spike_urchin_s': L.urchin_spike('s'),
            'hz_spike_urchin_t': L.urchin_spike('t'), 'hz_shot_fish': L.fish_shot()}
