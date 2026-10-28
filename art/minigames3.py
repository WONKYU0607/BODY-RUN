# (v53) the pictures of two stage-2 mini-games, in the glossy cartoon look of gloss.py (the user's slot machine and
# mouse):
#  * the poop tower ('똥 탑 쌓기', in the primary clarifier): tw_block0..2 (soft poop bricks), tw_base (the clarifier's
#    concrete pier the tower stands on), tw_hook (the crane's hook)
#  * the fruit archery ('과일 화살', at the outfall, under the sky): ar_field (the outfall to the river: sky, hills, the
#    river, the pipe pouring into it, the grassy bank), ar_cloud0..1, the fruits ar_apple, ar_orange, ar_banana,
#    ar_grapes, ar_melon, ar_peach, ar_gold (a golden apple), ar_bow (the bow, its string drawn by the game), ar_arrow
# -> runner_hd/assets/tw.webp, ar.webp, ar_field.webp + manifest.  python3 minigames3.py [tw] [ar] [field] [preview]
import sys, os, json
import numpy as np
from PIL import Image
from scipy import ndimage
sys.path.insert(0, '/home/claude/hdart')
import gloss
from gloss import Pic, hexc, sstep, ramp_col

OUT = '/home/claude/runner_hd/assets'
PRE = '/tmp/claude-0/-home-claude/3a779e8a-891a-5a91-a306-4a5325e0d53e/scratchpad/mg3'
POO = ('#1c0802', '#461e08', '#6e3618', '#9c5c2c', '#e2b07a')
CONC = ('#2a2c34', '#4a4e5a', '#767c8a', '#a8aeba', '#e4e8f0')
STEEL = ('#1a1e26', '#3a4250', '#647084', '#a0acc0', '#eef4ff')
YEL = ('#6a3a00', '#b06a00', '#f0a800', '#ffd24a', '#fff2b0')
RED = ('#4a0008', '#94101c', '#d82a34', '#ff6a6a', '#ffd0d0')
ORA = ('#6a2400', '#c45004', '#f08a14', '#ffbc4a', '#ffe8b8')
BAN = ('#6a4a00', '#c09000', '#f2d020', '#fff07a', '#fffce0')
GRP = ('#1e0634', '#4a1478', '#7a32b8', '#b07ae6', '#ecd8ff')
MEL = ('#06280e', '#0e4a1c', '#1c7a2c', '#4cb04a', '#c8f0a8')
PCH = ('#7a1a2a', '#d24a5a', '#ff8a7a', '#ffc49a', '#fff0e0')
GOLD = ('#6e3200', '#b06a00', '#e9a414', '#ffd04a', '#fff2b0')
LEAF = ('#0e3a0a', '#1e6a14', '#3aa024', '#7ad24a', '#d8ffb0')
WOOD = ('#3a1806', '#6e3a14', '#a8642c', '#d89a58', '#ffe0b0')
CLOUD = ('#6a86b0', '#9ab4d8', '#cfe0f4', '#f2f8ff', '#ffffff')


def img(p):
    return p.image()


# ---------------------------------------------------------------- the poop tower
def block(k):
    """a soft poop brick, 44 x 16 units on a 48 x 19 canvas (6 px a unit): rounded, lumps on top, bits in it"""
    S = 6; W, H = 48 * S, 19 * S
    p = Pic(W, H)
    rng = np.random.default_rng(10 + k)
    b = p.rrect(2 * S, 2.6 * S, W - 2 * S, H - 1.2 * S, 7 * S)
    # a few lumps along its top edge, different on each brick
    for i in range(4):
        cx = (9 + i * 10 + rng.uniform(-1.5, 1.5)) * S
        b |= p.ell(cx, 4.0 * S, rng.uniform(4.0, 5.4) * S, rng.uniform(2.0, 2.8) * S)
    p.body(b, POO, R=6.5 * S, rim=0.55, rimcol='#ffd8a0', spec=0.85, power=30, shadow=0)
    # its top face: a lighter band, a dark crease under it
    top = b & (p.Y < 7.2 * S) & ~p.rrect(1.5 * S, 7.0 * S, W - 1.5 * S, H, 6 * S)
    p.flat(top, '#c48850', 0.35)
    crease = p.stroke_mask([(4 * S, 9.4 * S), (16 * S, 10.2 * S), (30 * S, 9.6 * S), (42 * S, 10.4 * S)], 0.45 * S) & b
    p.flat(ndimage.gaussian_filter(crease.astype(np.float32), 0.6 * gloss.SS) > 0.3, '#4a200a', 0.55)
    # bits: corn kernels, a pea
    for i in range(3 + k):
        x, y = rng.uniform(6, 40) * S, rng.uniform(10.5, 14.5) * S
        m = p.ell(x, y, 1.6 * S, 1.2 * S, rng.uniform(-0.6, 0.6))
        p.body(m, YEL, R=1.1 * S, rim=0.3, spec=0.8, line=0.5, shadow=0.4)
    if k != 1:
        x, y = rng.uniform(10, 36) * S, rng.uniform(11, 14) * S
        p.body(p.ell(x, y, 1.5 * S, 1.5 * S), LEAF, R=1.2 * S, rim=0.3, spec=0.8, line=0.5, shadow=0.4)
    p.gloss_blob(p.ell(12 * S, 5.2 * S, 7 * S, 1.6 * S, -0.08) & b, a=0.75, soft=0.6)
    p.gloss_blob(p.ell(38 * S, 13.5 * S, 1.6 * S, 1.0 * S) & b, a=0.5, soft=0.4)
    p.outline(3.0)
    return img(p), {}, S


def base():
    """the clarifier's concrete pier: 64 x 46 units (5 px a unit), a slab on top, sludge stains, a rusty rail"""
    S = 5; W, H = 64 * S, 46 * S
    p = Pic(W, H)
    body = p.poly([(6 * S, 8 * S), (58 * S, 8 * S), (61 * S, H), (3 * S, H)])
    p.body(body, CONC, R=9 * S, rim=0.35, spec=0.3, power=14, shadow=0, flat=0.5, top=0.25)
    rng = np.random.default_rng(5)
    stain = np.zeros(p.X.shape, np.float32)
    for i in range(9):
        x = rng.uniform(8, 56) * S
        stain += p.stroke_mask([(x, 10 * S), (x + rng.uniform(-1, 1) * S, rng.uniform(18, 40) * S)], rng.uniform(0.8, 2.2) * S).astype(np.float32)
    p.over(hexc('#5a3a1e'), np.clip(ndimage.gaussian_filter(stain, 1.2 * gloss.SS), 0, 1) * body * 0.45)
    for y in (20, 32):                                         # the joints in the concrete
        p.flat(p.stroke_mask([(5 * S, y * S), (59 * S, y * S)], 0.35 * S) & body, '#30323a', 0.6)
    slab = p.rrect(1 * S, 3 * S, W - 1 * S, 10 * S, 2.2 * S)
    p.body(slab, CONC, R=3 * S, rim=0.5, spec=0.6, power=24, line=1.0, shadow=0.55)
    p.gloss_blob(p.rrect(4 * S, 4 * S, 40 * S, 5.2 * S, 1 * S) & slab, a=0.45, soft=0.8)
    p.outline(3.0)
    return img(p), {'top': 3.0}, S


def hook():
    """the crane's hook: a pulley block (yellow), a steel hook under it; 18 x 24 units (6 px a unit)"""
    S = 6; W, H = 18 * S, 24 * S
    p = Pic(W, H)
    blk = p.rrect(2 * S, 1 * S, 16 * S, 11 * S, 3 * S)
    p.body(blk, YEL, R=4 * S, rim=0.5, spec=0.9, shadow=0)
    for x in (5, 13): p.body(p.ell(x * S, 6 * S, 1.3 * S, 1.3 * S), STEEL, R=1 * S, rim=0.3, line=0.5, shadow=0.3)
    p.flat(p.rrect(3 * S, 4.6 * S, 15 * S, 7.4 * S, 1 * S) & blk, '#1a1006', 0.65)                      # its stripe
    shank = p.cap((9 * S, 11 * S), (9 * S, 15.5 * S), 1.6 * S)
    p.body(shank, STEEL, R=1.4 * S, rim=0.5, spec=1.0, line=0.8, shadow=0.4)
    hk = p.stroke_mask([(9 * S, 15 * S), (9.4 * S, 19 * S), (7.5 * S, 21.6 * S), (4.6 * S, 21 * S), (3.8 * S, 18.6 * S)], [1.9 * S, 1.9 * S, 1.8 * S, 1.5 * S, 1.1 * S])
    p.body(hk, STEEL, R=1.6 * S, rim=0.55, spec=1.0, power=26, line=0.8, shadow=0.4)
    p.gloss_blob(p.ell(6 * S, 3 * S, 3 * S, 0.9 * S) & blk, a=0.8, soft=0.4)
    p.outline(2.6)
    return img(p), {'hang': [9.0, 22.0]}, S


# ---------------------------------------------------------------- the fruit archery
def fruit(kind):
    """a fruit on a square: 22 units (the melon 30) at 6 px a unit"""
    S = 6; U = 30 if kind == 'melon' else 22; W = U * S
    p = Pic(W, W); c = W / 2
    if kind in ('apple', 'gold'):
        R_ = 9.2 * S
        b = p.ell(c - 2.6 * S, c + 0.8 * S, R_ * 0.78, R_ * 0.9) | p.ell(c + 2.6 * S, c + 0.8 * S, R_ * 0.78, R_ * 0.9) | p.ell(c, c + 2.2 * S, R_ * 0.8, R_ * 0.78)
        st = GOLD if kind == 'gold' else RED
        p.body(b, st, R=R_ * 0.9, rim=0.6, rimcol='#fff0a0' if kind == 'gold' else '#ffc0c0', spec=1.0, power=30, shadow=0)
        p.flat(ndimage.gaussian_filter(p.ell(c, c - 6.4 * S, 2.4 * S, 1.2 * S).astype(np.float32), 0.8 * gloss.SS) > 0.3, '#5a1a00' if kind == 'gold' else '#5a0008', 0.55)
        stem = p.stroke_mask([(c, c - 6 * S), (c + 0.4 * S, c - 8.4 * S), (c + 1.4 * S, c - 10 * S)], [0.8 * S, 0.7 * S, 0.6 * S])
        p.body(stem, WOOD, R=0.6 * S, rim=0.3, line=0.6, shadow=0.4)
        lf = p.spline([(c + 1 * S, c - 7.6 * S), (c + 4 * S, c - 10.2 * S), (c + 7.6 * S, c - 10 * S), (c + 5 * S, c - 7.4 * S)])
        p.body(lf, LEAF, R=1.6 * S, rim=0.4, spec=0.9, line=0.8, shadow=0.45)
        p.gloss_blob(p.ell(c - 4.2 * S, c - 2.4 * S, 2.6 * S, 1.5 * S, -0.7) & b, a=0.9, soft=0.5)
        p.gloss_blob(p.ell(c + 5 * S, c + 5 * S, 0.9 * S, 0.9 * S) & b, a=0.6, soft=0.3)
    elif kind == 'orange':
        b = p.ell(c, c + 0.6 * S, 9 * S, 8.6 * S)
        p.body(b, ORA, R=8.6 * S, rim=0.55, rimcol='#ffe0a0', spec=0.9, power=26, shadow=0)
        rng = np.random.default_rng(3)
        pores = np.zeros(p.X.shape, bool)
        for i in range(70):
            a, r = rng.uniform(0, 6.28), 8.6 * S * np.sqrt(rng.uniform(0, 1))
            pores |= p.ell(c + np.cos(a) * r, c + 0.6 * S + np.sin(a) * r * 0.95, 0.35 * S, 0.3 * S)
        p.flat(pores & b, '#c04a00', 0.35)
        cap = p.poly([(c + 1.6 * S * np.cos(t) * (1.0 if k % 2 == 0 else 0.45), c - 7.4 * S + 1.6 * S * np.sin(t) * (1.0 if k % 2 == 0 else 0.45) * 0.6) for k, t in enumerate(np.linspace(0, 2 * np.pi, 10, endpoint=False))])
        p.body(cap, LEAF, R=0.8 * S, rim=0.3, line=0.5, shadow=0.4)
        p.gloss_blob(p.ell(c - 3.8 * S, c - 2.8 * S, 2.6 * S, 1.4 * S, -0.7) & b, a=0.85, soft=0.5)
    elif kind == 'banana':
        b = p.stroke_mask([(c - 8 * S, c - 5 * S), (c - 6 * S, c + 2 * S), (c - 1 * S, c + 6 * S), (c + 5 * S, c + 6.4 * S), (c + 9 * S, c + 3.6 * S)], [1.4 * S, 3.2 * S, 3.8 * S, 3.2 * S, 1.6 * S])
        p.body(b, BAN, R=3.2 * S, rim=0.5, rimcol='#fffbd0', spec=0.9, power=28, shadow=0)
        ridge = p.stroke_mask([(c - 7 * S, c - 3 * S), (c - 4.6 * S, c + 2.4 * S), (c, c + 5 * S), (c + 6 * S, c + 4.6 * S)], 0.35 * S) & b
        p.flat(ridge, '#b08000', 0.45)
        for tip in [(c - 8.2 * S, c - 5.4 * S), (c + 9.2 * S, c + 3.5 * S)]:
            p.body(p.ell(tip[0], tip[1], 1.3 * S, 1.2 * S), WOOD, R=0.9 * S, rim=0.3, line=0.5, shadow=0.3)
        p.gloss_blob(p.stroke_mask([(c - 6.6 * S, c - 1 * S), (c - 3.6 * S, c + 3 * S), (c, c + 4.4 * S)], 0.7 * S) & b, a=0.75, soft=0.4)
    elif kind == 'grapes':
        pts = [(0, -4.6), (-3.6, -3.4), (3.6, -3.4), (-5.4, 0.2), (-1.8, 0), (1.8, 0), (5.4, 0.2), (-3.6, 3.6), (0, 3.6), (3.6, 3.6), (-1.8, 7), (1.8, 7), (0, 10)]
        for dx, dy in sorted(pts, key=lambda q: q[1]):
            g = p.ell(c + dx * S, c + (dy - 3.2) * S, 2.6 * S, 2.7 * S)
            p.body(g, GRP, R=2.4 * S, rim=0.55, rimcol='#e6c8ff', spec=1.0, power=30, line=0.6, shadow=0.45)
            p.gloss_blob(p.ell(c + (dx - 0.9) * S, c + (dy - 4.2) * S, 0.8 * S, 0.5 * S, -0.6) & g, a=0.85, soft=0.3)
        st = p.stroke_mask([(c, c - 6.6 * S), (c + 0.6 * S, c - 8.8 * S), (c + 2.4 * S, c - 10 * S)], [0.8 * S, 0.7 * S, 0.5 * S])
        p.body(st, WOOD, R=0.6 * S, rim=0.3, line=0.6, shadow=0.4)
        lf = p.spline([(c - 0.5 * S, c - 7.8 * S), (c - 4 * S, c - 10.2 * S), (c - 7.6 * S, c - 9.4 * S), (c - 4.4 * S, c - 6.8 * S)])
        p.body(lf, LEAF, R=1.6 * S, rim=0.4, spec=0.9, line=0.8, shadow=0.45)
    elif kind == 'melon':
        b = p.ell(c, c + 0.6 * S, 13 * S, 12 * S)
        n = p.body(b, MEL, R=12 * S, rim=0.5, rimcol='#e0ffc0', spec=0.9, power=28, shadow=0)
        ang = np.arctan2(p.X - c, (p.Y - c) * 0.35 + 30 * S)
        u = (p.X - c) / np.maximum(13 * S * np.sqrt(np.clip(1 - ((p.Y - c - 0.6 * S) / (12 * S)) ** 2, 1e-3, 1)), 1e-3)
        stripes = (np.abs(np.sin(np.arcsin(np.clip(u, -1, 1)) * 4.0 + 0.4 * np.sin((p.Y - c) / (2.2 * S)))) > 0.62) & b
        p.flat(stripes, '#0a3410', 0.62)
        p.gloss_blob(p.ell(c - 5.4 * S, c - 4.2 * S, 3.8 * S, 2.0 * S, -0.6) & b, a=0.8, soft=0.6)
        p.body(p.stroke_mask([(c, c - 11.2 * S), (c + 0.8 * S, c - 13 * S)], 0.8 * S), WOOD, R=0.6 * S, rim=0.3, line=0.6, shadow=0.4)
    elif kind == 'peach':
        b = p.ell(c, c + 1 * S, 9.2 * S, 8.8 * S) | p.ell(c - 1.2 * S, c - 3.6 * S, 5 * S, 5.4 * S)
        n = p.normals(b, 8.6 * S)
        lam = (n * gloss.L).sum(-1)
        v = sstep(-0.15, 1.0, lam)
        t = np.clip((p.Y - (c - 9 * S)) / (18 * S), 0, 1)
        col = ramp_col(PCH, np.clip(v * 0.8 + 0.25 - 0.25 * t, 0, 1))
        col = col * (1 - 0.35 * t[..., None]) + np.array(hexc('#ffb05a')) * 0.35 * t[..., None]
        p.over(col, b.astype(np.float32)); p.parts.append(b)
        crease = p.stroke_mask([(c - 1.6 * S, c - 7 * S), (c - 3.6 * S, c - 1 * S), (c - 3 * S, c + 5 * S), (c - 0.6 * S, c + 9 * S)], 0.5 * S) & b
        p.flat(ndimage.gaussian_filter(crease.astype(np.float32), 0.6 * gloss.SS) > 0.25, '#b02a3a', 0.55)
        lf = p.spline([(c - 0.4 * S, c - 7.2 * S), (c + 3 * S, c - 10 * S), (c + 7 * S, c - 9.6 * S), (c + 4 * S, c - 6.6 * S)])
        p.body(lf, LEAF, R=1.6 * S, rim=0.4, spec=0.9, line=0.8, shadow=0.45)
        p.gloss_blob(p.ell(c - 5 * S, c - 2 * S, 2.2 * S, 1.4 * S, -0.7) & b, a=0.7, soft=0.6)
    p.outline(3.2)
    if kind == 'gold':
        for cx, cy, r in [(c - 8 * S, c - 8 * S, 2.6 * S), (c + 9 * S, c - 4 * S, 2.0 * S), (c + 7.5 * S, c + 9 * S, 1.6 * S)]:
            p.sparkle(cx, cy, r)
    return img(p), {'rad': round(13.0 if kind == 'melon' else 9.5, 2)}, S        # (not 'r': that is the picture's place in the atlas)


def bow():
    """the bow, held across (its belly up, the string to be drawn under it by the game): 44 x 16 units at 6 px a unit;
    its tips' places in units"""
    S = 6; W, H = 44 * S, 16 * S
    p = Pic(W, H); c = W / 2
    pts = [(2.4 * S, 13 * S), (5 * S, 9 * S), (11 * S, 5.6 * S), (c, 3.6 * S), (W - 11 * S, 5.6 * S), (W - 5 * S, 9 * S), (W - 2.4 * S, 13 * S)]
    limb = p.stroke_mask(pts, [0.9 * S, 1.3 * S, 1.7 * S, 2.0 * S, 1.7 * S, 1.3 * S, 0.9 * S])
    p.body(limb, WOOD, R=1.6 * S, rim=0.5, rimcol='#ffe8c0', spec=0.95, power=28, shadow=0)
    grip = p.rrect(c - 3.2 * S, 1.6 * S, c + 3.2 * S, 6.0 * S, 1.6 * S)
    p.body(grip, ('#2a0a04', '#5a1a0c', '#8a2e18', '#c05030', '#ffb090'), R=1.6 * S, rim=0.4, spec=0.9, line=0.8, shadow=0.4)
    for x in (-1.8, 0, 1.8): p.flat(p.stroke_mask([(c + x * S, 1.8 * S), (c + (x + 0.6) * S, 5.8 * S)], 0.25 * S) & grip, '#2a0804', 0.6)
    for tx in (2.4, 44 - 2.4):                                  # the tips: gold caps
        p.body(p.ell(tx * S, 13.2 * S, 1.3 * S, 1.3 * S), GOLD, R=1 * S, rim=0.4, spec=1.0, line=0.6, shadow=0.4)
    p.gloss_blob(p.stroke_mask([(8 * S, 6.6 * S), (14 * S, 4.4 * S), (19 * S, 3.6 * S)], 0.45 * S) & limb, a=0.8, soft=0.3)
    p.outline(2.6)
    return img(p), {'tips': [[2.4, 13.2], [41.6, 13.2]], 'grip': [22.0, 3.8]}, S


def arrow():
    """an arrow pointing up: 6 x 32 units at 8 px a unit (its tip at the top, the nock at the bottom)"""
    S = 8; W, H = 6 * S, 32 * S
    p = Pic(W, H); c = W / 2
    shaft = p.cap((c, 6 * S), (c, 30 * S), 0.55 * S)
    p.body(shaft, WOOD, R=0.5 * S, rim=0.4, spec=0.9, shadow=0)
    tip = p.poly([(c, 0.6 * S), (c + 2.0 * S, 6.4 * S), (c, 5.4 * S), (c - 2.0 * S, 6.4 * S)])
    p.body(tip, STEEL, R=1.0 * S, rim=0.5, spec=1.0, power=24, line=0.6, shadow=0.4)
    for sx in (-1, 1):                                          # the fletching: red feathers
        f = p.poly([(c, 22 * S), (c + sx * 2.6 * S, 25 * S), (c + sx * 2.7 * S, 30.6 * S), (c, 28.4 * S)])
        p.body(f, RED, R=1.0 * S, rim=0.4, spec=0.7, line=0.6, shadow=0.4)
    p.body(p.rrect(c - 0.9 * S, 30 * S, c + 0.9 * S, 31.6 * S, 0.4 * S), GOLD, R=0.5 * S, rim=0.3, line=0.5, shadow=0.3)
    p.outline(1.8)
    return img(p), {}, S


def cloud(k):
    S = 5; W, H = (64, 28) if k == 0 else (48, 22); W, H = W * S, H * S
    p = Pic(W, H)
    rng = np.random.default_rng(20 + k)
    m = p.ell(W / 2, H * 0.68, W * 0.44, H * 0.26)
    n = 4 if k == 0 else 3
    for i in range(n):
        x = W * (0.2 + 0.6 * i / (n - 1)); r = H * rng.uniform(0.28, 0.4) * (1.25 if i in (1, 2) and k == 0 else 1)
        m |= p.ell(x, H * 0.62 - r * 0.55, r, r * 0.92)
    p.body(m, CLOUD, R=H * 0.32, rim=0.5, rimcol='#ffffff', spec=0.4, power=14, shadow=0, top=0.3)
    p.outline(2.6, col=np.array([70, 100, 150], np.float32))
    return img(p), {}, S


def field():
    """the outfall to the river, 420 x 180 units at 5 px a unit (drawn at 2x, not 4x: it is big and soft)"""
    old = gloss.SS; gloss.SS = 2
    S = 5; Wu, Hu = 420, 180; W, H = Wu * S, Hu * S
    p = Pic(W, H)
    Y = p.Y / S; X = p.X / S
    # the sky: deep blue at the top to pale at the horizon; the sun's glow at the top right
    sky = ramp_col(['#2a72d4', '#4a96e6', '#86c4f2', '#c8ecfc'], np.clip(Y / 112, 0, 1))
    sun = np.exp(-((X - 350) ** 2 + (Y - 26) ** 2) / (2 * 34 ** 2))
    sky = sky + sun[..., None] * (np.array([255, 248, 210]) - sky) * 0.75
    p.over(sky, np.ones(p.X.shape, np.float32))
    p.over(hexc('#ffffff'), (np.hypot(X - 350, Y - 26) < 10).astype(np.float32) * 0.95)
    p.over(hexc('#fff6c8'), np.clip(1.2 - np.hypot(X - 350, Y - 26) / 13, 0, 1) * 0.6)
    # far hills (bluish), near hills (green) with round trees
    far = p.spline([(-20 * S, 140 * S), (-20 * S, 102 * S), (40 * S, 94 * S), (100 * S, 100 * S), (170 * S, 90 * S), (250 * S, 98 * S), (330 * S, 88 * S), (440 * S, 98 * S), (440 * S, 140 * S)], n=30)
    p.body(far, ('#2e5a72', '#3e7088', '#5a8ea4', '#7aaec0', '#b8dcea'), R=14 * S, rim=0.2, spec=0.1, shadow=0, flat=0.4, line=0)
    near = p.spline([(-20 * S, 150 * S), (-20 * S, 112 * S), (60 * S, 104 * S), (140 * S, 112 * S), (220 * S, 102 * S), (300 * S, 110 * S), (380 * S, 100 * S), (440 * S, 108 * S), (440 * S, 150 * S)], n=30)
    p.body(near, ('#1a4a14', '#2a6a1e', '#3e8e2a', '#62b03e', '#b0e07a'), R=12 * S, rim=0.3, spec=0.15, shadow=0.3, flat=0.3, line=0.6)
    for tx, ty, r in [(118, 104, 6), (131, 107, 4.6), (262, 99, 5.6), (274, 102, 4.2), (398, 97, 5.2)]:   # little trees: a trunk, a leafy top of three lumps
        p.body(p.rrect((tx - 0.8) * S, (ty - 1) * S, (tx + 0.8) * S, (ty + r * 0.9) * S, 0.4 * S), WOOD, R=0.6 * S, rim=0.3, line=0.5, shadow=0.3)
        tr = p.ell((tx - r * 0.45) * S, (ty - r * 0.55) * S, r * 0.62 * S, r * 0.58 * S) | p.ell((tx + r * 0.45) * S, (ty - r * 0.5) * S, r * 0.6 * S, r * 0.56 * S) | p.ell(tx * S, (ty - r * 1.05) * S, r * 0.7 * S, r * 0.66 * S)
        p.body(tr, ('#0e3a0a', '#1a5a12', '#2e7e20', '#58a83a', '#b8e890'), R=r * 0.5 * S, rim=0.4, spec=0.4, power=16, line=0.6, shadow=0.4)
    # the river: a band of water, lighter far off, glints across it
    river = (Y > 118) & (Y < 166)
    wc = ramp_col(['#8ad0f0', '#4aa0d8', '#2a76b8', '#1c5a96'], np.clip((Y - 118) / 44, 0, 1))
    p.over(wc, river.astype(np.float32))
    rng = np.random.default_rng(8)
    gl = np.zeros(p.X.shape, np.float32)
    for i in range(46):
        x, y = rng.uniform(0, 420), rng.uniform(122, 158); L = rng.uniform(4, 16) * (0.5 + (y - 118) / 50)
        gl += (np.abs(Y - y) < 0.35 + (y - 118) / 120) * (np.abs(X - x) < L / 2)
    p.over(hexc('#ffffff'), np.clip(gl, 0, 1) * river * 0.55)
    p.over(hexc('#0a3a66'), ((Y > 118) & (Y < 119.2)).astype(np.float32) * 0.5)
    # the outfall: a concrete wall in the bank at the left, a big round pipe in it, the water pouring out into the river
    wall = p.poly([(0, 84 * S), (78 * S, 92 * S), (82 * S, 140 * S), (0, 140 * S)])
    p.body(wall, CONC, R=10 * S, rim=0.3, spec=0.3, power=14, shadow=0.4, flat=0.5, line=0.8)
    for y in (100, 116):
        p.flat(p.stroke_mask([(0, y * S), (79 * S, (y + 4) * S)], 0.35 * S) & wall, '#30323a', 0.5)
    ring = p.ell(38 * S, 112 * S, 22 * S, 20 * S)
    p.body(ring, CONC, R=5 * S, rim=0.5, spec=0.6, power=20, line=1.0, shadow=0.55)
    hole = p.ell(38 * S, 112 * S, 16.5 * S, 15 * S)
    p.over(ramp_col(['#020406', '#0a1218', '#16242e'], np.clip((Y - 98) / 28, 0, 1)), hole.astype(np.float32))
    fall = p.poly([(24 * S, 120 * S), (52 * S, 120 * S), (60 * S, 134 * S), (66 * S, 150 * S), (16 * S, 150 * S), (20 * S, 134 * S)]) & ~p.ell(38 * S, 112 * S, 16.5 * S, 7 * S)
    fall &= (Y > 118)
    fc = ramp_col(['#e8f8ff', '#a8dcf4', '#d8f2ff'], np.clip((X - 18) / 46, 0, 1))
    streak = 0.5 + 0.5 * np.sin(X * 1.7 + np.sin(Y * 0.4) * 2)
    p.over(fc * (0.85 + 0.15 * streak[..., None]), fall.astype(np.float32) * 0.92)
    foam = np.zeros(p.X.shape, bool)
    for i in range(16):
        foam |= p.ell(rng.uniform(14, 70) * S, rng.uniform(146, 154) * S, rng.uniform(3, 7) * S, rng.uniform(1.8, 3.2) * S)
    p.body(foam, CLOUD, R=2 * S, rim=0.5, spec=0.4, shadow=0.3, line=0.5)
    # the bank in front: grass, lit along its top, tufts and reeds, a few flowers
    bank = p.spline([(-20 * S, 200 * S), (-20 * S, 160 * S), (60 * S, 156 * S), (140 * S, 162 * S), (210 * S, 158 * S), (290 * S, 162 * S), (360 * S, 156 * S), (440 * S, 160 * S), (440 * S, 200 * S)], n=30)
    p.body(bank, ('#14400c', '#225e14', '#348020', '#5aa832', '#a8e070'), R=8 * S, rim=0.35, spec=0.15, shadow=0.45, flat=0.3, line=0.8, top=0.2)
    from PIL import ImageDraw                                    # (the tufts drawn as lines on a mask: quick)
    tm = Image.new('L', (W * gloss.SS, H * gloss.SS), 0); td = ImageDraw.Draw(tm); k = S * gloss.SS
    for i in range(70):
        x = rng.uniform(0, 420); y0 = 158 + rng.uniform(-1, 3)
        for d in (-1, 0, 1):
            td.line([(x * k, (y0 + 3) * k), ((x + d * 1.4) * k, (y0 - rng.uniform(2, 5)) * k)], fill=255, width=max(1, int(0.55 * k)))
    tufts = np.array(tm) > 127
    p.body(tufts & ~ndimage.binary_dilation(bank & (Y > 166), iterations=1), LEAF, R=0.6 * S, rim=0.4, spec=0.3, line=0.4, shadow=0.2)
    for x in (92, 104, 330, 342, 356):                            # reeds with brown heads
        h = rng.uniform(16, 24)
        p.body(p.stroke_mask([(x * S, 160 * S), ((x + 1.5) * S, (160 - h) * S)], [0.6 * S, 0.35 * S]), LEAF, R=0.5 * S, rim=0.3, line=0.4, shadow=0.3)
        p.body(p.ell((x + 1.4) * S, (160 - h + 2.5) * S, 1.2 * S, 3.2 * S), WOOD, R=1 * S, rim=0.3, spec=0.6, line=0.5, shadow=0.3)
    for i in range(14):
        x, y = rng.uniform(70, 400), rng.uniform(165, 176)
        if abs(x - 210) < 40: continue                             # (not under the archer)
        col = ['#ffe14a', '#ffffff', '#ff8ab0'][i % 3]
        for a in range(5):
            p.flat(p.ell((x + 1.1 * np.cos(a * 1.257)) * S, (y + 1.1 * np.sin(a * 1.257)) * S, 0.9 * S, 0.9 * S), col)
        p.flat(p.ell(x * S, y * S, 0.6 * S, 0.6 * S), '#e08a00')
    out = p.image()
    gloss.SS = old
    return out, {'river': [118, 166], 'pipe': [38, 112], 'bank': 158}, S


def atlas(sprs, pad=4, maxw=2048):
    """in rows (each sprite: its RGBA float array)"""
    rows, x, y, rh, rects = [], pad, pad, 0, []
    for s in sprs:
        if x + s.shape[1] + pad > maxw: x = pad; y += rh + pad; rh = 0
        rects.append([x, y, s.shape[1], s.shape[0]]); x += s.shape[1] + pad; rh = max(rh, s.shape[0])
    W = max(r[0] + r[2] for r in rects) + pad; H = y + rh + pad
    A = np.zeros((H, W, 4), np.float32)
    for s, r in zip(sprs, rects): A[r[1]:r[1] + r[3], r[0]:r[0] + r[2]] = s
    return A, rects


def save(A, path, lossless=False):
    a = np.clip(A, 0, 255).astype(np.uint8)
    Image.fromarray(a, 'RGBA').save(path, quality=92 if not lossless else 100, alpha_quality=100, method=6, lossless=lossless)


def build(what):
    os.makedirs(PRE, exist_ok=True)
    m = json.load(open(f'{OUT}/manifest.json'))
    def put(fn, items):
        A, rects = atlas([it[1][0] for it in items]); save(A, f'{OUT}/{fn}'); save(A, f'{PRE}/{fn[:-5]}_sprites.png')
        for (nm, (s, meta, sc)), r in zip(items, rects):
            m['sprites'][nm] = {'f': fn, 'r': r, 'w': round(s.shape[1] / sc, 3), 'h': round(s.shape[0] / sc, 3), **meta}
        print(fn, os.path.getsize(f'{OUT}/{fn}'), A.shape)
    if 'tw' in what:
        put('tw.webp', [(f'tw_block{k}', block(k)) for k in range(3)] + [('tw_base', base()), ('tw_hook', hook())])
    if 'ar' in what:
        put('ar.webp', [(f'ar_{k}', fruit(k)) for k in ('apple', 'orange', 'banana', 'grapes', 'melon', 'peach', 'gold')] + [('ar_bow', bow()), ('ar_arrow', arrow()), ('ar_cloud0', cloud(0)), ('ar_cloud1', cloud(1))])
    if 'field' in what:
        f, meta, sc = field()
        a = np.clip(f, 0, 255).astype(np.uint8)
        Image.fromarray(a, 'RGBA').convert('RGB').save(f'{OUT}/ar_field.webp', quality=90, method=6)
        Image.fromarray(a, 'RGBA').convert('RGB').resize((a.shape[1] // 2, a.shape[0] // 2), Image.LANCZOS).save(f'{PRE}/ar_field.png')
        m['sprites']['ar_field'] = {'f': 'ar_field.webp', 'r': [0, 0, a.shape[1], a.shape[0]], 'w': round(a.shape[1] / sc, 3), 'h': round(a.shape[0] / sc, 3), **meta}
        print('ar_field.webp', os.path.getsize(f'{OUT}/ar_field.webp'), a.shape)
    json.dump(m, open(f'{OUT}/manifest.json', 'w'), separators=(',', ':'))


def preview(fs, name):
    os.makedirs(PRE, exist_ok=True)
    ims = [Image.fromarray(np.clip(f()[0], 0, 255).astype(np.uint8), 'RGBA') for f in fs]
    W = sum(i.width for i in ims) + 10 * len(ims) + 10; H = max(i.height for i in ims) + 20
    S = Image.new('RGBA', (W, H), (60, 70, 90, 255)); x = 10
    for i in ims: S.alpha_composite(i, (x, 10)); x += i.width + 10
    S.save(f'{PRE}/{name}.png'); print(name, S.size)


if __name__ == '__main__':
    a = sys.argv[1:]
    if 'preview' in a:
        if 'tw' in a: preview([lambda: block(0), lambda: block(1), lambda: block(2), base, hook], 'tw')
        if 'ar' in a: preview([lambda k=k: fruit(k) for k in ('apple', 'orange', 'banana', 'grapes', 'melon', 'peach', 'gold')] + [bow, arrow, lambda: cloud(0), lambda: cloud(1)], 'ar')
        if 'field' in a:
            f = field()[0]; Image.fromarray(np.clip(f, 0, 255).astype(np.uint8), 'RGBA').convert('RGB').resize((1050, 450), Image.LANCZOS).save(f'{PRE}/field.png'); print('field')
    else:
        build(a)
