# Stage 2, in the building: the toilet's S-trap (2), the block's soil stack (3), the house drain (4), the septic tank
# (5). Drawn like the toilet (toilet.py): a far layer (the pipe's far wall under the water), a mid layer (what drifts),
# the pipe's wall in section below (and above, where the pipe runs full, or the water's surface from below where it
# does not) and the obstacles of each place.
import numpy as np
from scipy import ndimage
from art import (H, SC, px, grid, canvas, ramp, ramp_col, hexc, paint, ellipse_mask, outline, paste, over, blur, disc,
                 ellipse_soft, inner, smooth_mask, fill_rect)
import anatomy as A
from tiles import WT, GY, FH, FY0, CH, TAU, wide, crop, put, per_sin, gradient, haze, pcells, wall, band_line, spots
from themes import three, drift, tower, stack, hang_len, bubble, flip_v
from variants import noise
import toilet as TT
from s2lib import (lerp_rgb, mul, wdx, pipe_curve, ring_joints, concrete_tex, water_line, streaks, mouth, silt, motes,
                   bubble_chain, pat_concrete, pat_soil, pat_pvc, pat_glaze, pat_china, pat_slime, pat_sludge, pat_rubber,
                   surf_ceil, strands, lump, speckle, trim, blob_mask, mass)

RS = np.random.RandomState
HAIR = ['#1c120c', '#2c1c12', '#120c0a', '#4a3020', '#3a2616']


# ================================================================== 2. the S-trap
WATER_TRAP = '#5e8c8c'
SCUM = ramp('#6e6a58', '#9a9480', '#c2bca4', '#ddd8c4', '#efece0')
GUNK_OUT = '#2a2618'


def pat_scale(sh, x, ld, u, shape, h, R):
    n = int(0.08 * WT * h)
    P = np.c_[R.uniform(0, WT, n), R.uniform(0, h, n)]
    sp = spots(shape, P, R.uniform(0.25, 0.7, n), WT)
    return sh + 0.15 * sp - 0.08 * band_line(ld + 0.5 * np.sin(x * 0.3), 1.1, 0.3)


def trap_far(seed=501):
    R = RS(seed)
    far = gradient(H, ['#a4cccc', '#80aaac', '#5f8e92', '#3e6a70'])
    y, x = grid(H, WT)
    pipe_curve(far, 6, GY + 10, 0.34)
    yc = 72 + 20 * per_sin(x, 3, 0.7) + 6 * per_sin(x, 7, 2.0)          # the bend: the glaze catching the light along it
    lerp_rgb(far, '#f4ffff', np.exp(-((y - yc) / 5.5) ** 2) * 0.32)
    lerp_rgb(far, '#2a4a50', np.exp(-((y - yc - 13) / 6) ** 2) * 0.22)
    lerp_rgb(far, '#f4ffff', np.exp(-((y - yc + 34) / 3.5) ** 2) * 0.12)
    TT.caustics(far, seed + 1, k=0.22)
    TT.light_shafts(far, seed + 2, n=4)
    streaks(far, 46, seed + 3, '#a07a46', k=0.32, y0=104, y1=148, L=(60, 200), w=(0.8, 2.4))      # scale stains, along the flow
    streaks(far, 20, seed + 4, '#6e5434', k=0.22, y0=118, y1=150, L=(80, 240), w=(0.6, 1.4))
    c3 = three(far)
    drift(c3, 60, ['#e4f4f2', '#ffffff', '#cfe4e0'], seed + 5, y0=16, y1=GY - 8, a=120)
    far = crop(c3)
    haze(far, WATER_TRAP, 0.18)
    return far


HAIRM = ramp('#0c0807', '#1c1410', '#2e2219', '#433226', '#5a4532')
HAIR_OUT = '#060404'


def flow_lines(dst, mask_spr, seed, n, path, cols=('#4e3a2a', '#66503a', '#3a2a1e'), w=(0.2, 0.36), a=120):
    """sheen along the hair's flow: path(k, R) gives a list of points; strokes kept to the sprite (drawn on inner)"""
    R = RS(seed)
    I = inner(mask_spr)
    keep = I[..., 3].copy()
    for k in range(n):
        A.stroke(I, path(k, R), R.uniform(*w), cols[k % len(cols)], a, scale=1.0)
    I[..., 3] = keep


def loose_hair(dst, x0, y0, n, seed, ang, L=(8, 15), curl=2.2, w=(0.16, 0.26), a=230, spread=0.35):
    """single hairs coming out of a mass at (x0, y0), trailing off at about angle ang, in long easy curves"""
    R = RS(seed)
    for k in range(n):
        an = ang + R.uniform(-spread, spread); l = R.uniform(*L); bend = R.uniform(-1, 1) * curl
        sx, sy = x0 + R.uniform(-1.5, 1.5), y0 + R.uniform(-1.5, 1.5)
        pts = []
        for t in np.linspace(0, 1, 18):
            px_ = sx + np.cos(an) * l * t - np.sin(an) * bend * np.sin(t * np.pi * 0.9) * l * 0.25
            py_ = sy + np.sin(an) * l * t + np.cos(an) * bend * np.sin(t * np.pi * 0.9) * l * 0.25
            pts.append((px_, py_))
        A.stroke(dst, pts, R.uniform(*w), HAIR[k % len(HAIR)], a, scale=1.0)


def hair_mass(m, seed, flow='x'):
    """a mass of hair from a mask: dark, soft, sheen lines along it"""
    spr = A.mask_sprite(m, HAIRM, HAIR_OUT, soft=1.6, ambient=0.3, hl=False)
    h, w = m.shape[0] / SC, m.shape[1] / SC
    def path(k, R):
        if flow == 'y':
            x0 = R.uniform(0.1, 0.9) * w; y0 = R.uniform(-2, h * 0.6); L = R.uniform(0.3, 0.9) * h
            return [(x0 + 1.0 * np.sin(t * 3 + k), y0 + L * t) for t in np.linspace(0, 1, 20)]
        if flow == 'r':
            r = R.uniform(0.25, 0.95); a0 = R.uniform(0, TAU); da = R.uniform(0.8, 2.0)
            return [(w / 2 + np.cos(a0 + da * t) * r * w / 2, h / 2 + np.sin(a0 + da * t) * r * h / 2) for t in np.linspace(0, 1, 20)]
        y0 = R.uniform(0.03, 0.97) * h; x0 = R.uniform(-2, w * 0.4); L = R.uniform(0.4, 0.9) * w
        return [(x0 + L * t, y0 - 2.5 * np.sin(t * np.pi) * R.uniform(0.3, 1) + 0.6 * np.sin(t * 5 + k)) for t in np.linspace(0, 1, 20)]
    flow_lines(spr, spr, seed, int(w * h / 6) + 10, path)
    return spr


def hair_clump(w=24, h=14, seed=1):
    """a clump of hair caught in soap scum on the bottom: a dark mass, lit along its strands, a little gunk showing,
    loose hairs trailing off with the flow"""
    R = RS(seed)
    y, x = grid(h, w)
    m = ((x - w / 2) / (w / 2 - 2.5)) ** 2 + ((y - h) / (h - 1.5)) ** 2 <= 1
    for k in range(5):
        bx, by, br = R.uniform(w * 0.2, w * 0.8), R.uniform(h * 0.4, h * 0.85), R.uniform(0.18, 0.28) * w
        m |= (((x - bx) / br) ** 2 + ((y - by) / (br * 0.7)) ** 2 <= 1) & (y < h - 0.6)
    m &= y <= h - 0.6
    out = canvas(w + 10, h + 4)
    for k in range(3):                                   # soap scum under it, showing at the edges
        g = lump(R.uniform(5, 8), R.uniform(3, 4.5), seed + 20 + k, SCUM, GUNK_OUT, bumps=3)
        paste(out, g, 5 + R.uniform(0, w - 8), h + 4 - g.shape[0] / SC)
    hm = hair_mass(m, seed)
    paste(out, hm, 4, 3)
    loose_hair(out, 5 + w * 0.85, 3 + h * 0.55, 8, seed + 6, 0.05, L=(7, 13))
    g = lump(6, 3.5, seed + 30, SCUM, GUNK_OUT, bumps=3, flat_bottom=False, soft=0.8)
    paste(out, g, 5 + w * R.uniform(0.3, 0.6), 3 + h * 0.3)
    return trim(out)


def hair_ball(seed=3, d=18):
    """a ball of hair rolling in the water: dark, wound round, loose ends all round"""
    R = RS(seed)
    y, x = grid(d, d)
    rr = np.sqrt(((x - d / 2) / (d / 2 - 1)) ** 2 + ((y - d / 2) / (d / 2 - 1.5)) ** 2)
    ang = np.arctan2(y - d / 2, x - d / 2)
    m = rr <= 0.88 + 0.06 * np.sin(ang * 5 + seed) + 0.04 * np.sin(ang * 11)
    out = canvas(d + 20, d + 14)
    paste(out, hair_mass(m, seed, flow='r'), 5, 6)
    I = inner(out)
    for k in range(2):                                    # a scrap of paper and some scum caught in it
        g = TT.paper_shred(seed + 40 + k, R.uniform(5, 7), R.uniform(3, 4.5)) if k == 0 else lump(4.5, 3, seed + 41, SCUM, GUNK_OUT, bumps=3, flat_bottom=False, soft=0.8)
        paste(out, g, 6 + d / 2 + R.uniform(-d * 0.3, d * 0.1), 7 + d / 2 + R.uniform(-d * 0.3, d * 0.15))
    for k in range(5):                                    # loose ends wound round it
        an = k / 5 * TAU + R.uniform(-0.3, 0.3)
        sx, sy = 6 + d / 2 + np.cos(an) * d * 0.42, 7 + d / 2 + np.sin(an) * d * 0.42
        loose_hair(out, sx, sy, 1, seed + 10 + k, an + np.pi / 2, L=(5, 8), curl=3.0, spread=0.15)
    loose_hair(out, 6 + d * 0.92, 7 + d / 2, 5, seed + 30, 0.0, L=(7, 11))
    return trim(out)


def hair_rope(seed=1, wdt=10):
    """a hank of hair hanging from the trap's top in the flow: wide where it is caught, tapering, the ends loose and
    splaying, a bit of scum caught in it"""
    L = hang_len()
    R = RS(seed)
    W = wdt + 14
    y, x = grid(L, W)
    t = np.clip(y / L, 0, 1)
    cx = W / 2 + 2.6 * np.sin(y * 0.06 + seed) * t
    half = wdt / 2 * (1 - 0.62 * t ** 1.1) + 0.4 * np.sin(y * 0.25 + seed) + 2.5 * np.exp(-y / 4)
    m = (np.abs(x - cx) <= half) & (y <= L - 9)
    spr = A.mask_sprite(m, HAIRM, HAIR_OUT, soft=1.4, ambient=0.3, hl=False)
    def path(k, R2):
        u = R2.uniform(-0.9, 0.9); y0 = R2.uniform(-2, L * 0.7); l = R2.uniform(0.2, 0.5) * L
        return [(W / 2 + 1 + 2.6 * np.sin(yy * 0.06 + seed) * yy / L + u * wdt / 2 * (1 - 0.62 * max(0.0, yy / L) ** 1.1) + 0.4 * np.sin(yy * 0.2 + k), yy + 1)
                for yy in np.linspace(y0, min(L - 9, y0 + l), 24)]
    flow_lines(spr, spr, seed, 70, path)
    out = canvas(W + 4, L + 2)
    paste(out, spr, 1, -1)
    ex = W / 2 + 2 + 2.6 * np.sin((L - 9) * 0.06 + seed)
    for k in range(18):                                   # the loose ends
        sx = ex + R.uniform(-1.2, 1.2) * wdt * 0.2
        bend = R.uniform(-2.5, 2.5)
        pts = [(sx + bend * np.sin(tt * 2.2) + R.uniform(-0.1, 0.1), L - 12 + tt * R.uniform(8, 12)) for tt in np.linspace(0, 1, 16)]
        A.stroke(out, pts, R.uniform(0.2, 0.34), HAIR[k % len(HAIR)], 235, scale=1.0)
    for k in range(3):                                    # soap scum caught in it
        gy = R.uniform(10, L * 0.65); g = lump(R.uniform(3.5, 5.5), R.uniform(2.2, 3.5), seed + 20 + k, SCUM, GUNK_OUT, bumps=3, flat_bottom=False, soft=0.8)
        paste(out, g, W / 2 + 2 - g.shape[1] / SC / 2 + 2.6 * np.sin(gy * 0.06 + seed) * gy / L + R.uniform(-1, 1), gy)
    return trim(out)[:px(L)]


def clog(h, seed=7, w=22):
    """a plug built up from the bottom: hair and soap scum packed into a lumpy column, paper caught in it, hairs
    trailing off it with the flow"""
    R = RS(seed)
    h = int(round(h))
    y, x = grid(h, w)
    t = np.clip(y / h, 0, 1)
    cx = w / 2 + 1.0 * np.sin(y * 0.09 + seed)
    half = w / 2 * (0.6 + 0.4 * t ** 0.6) - 1.0 + 1.2 * np.sin(y * 0.3 + seed) + 0.6 * np.sin(y * 0.85 + 2 * seed)
    m = (np.abs(x - cx) <= half) & (y < h - 0.6) & (y > 1.5 - 1.5 * np.cos(np.clip((x - cx) / np.maximum(half, 1), -1, 1) * 1.4))
    spr = hair_mass(m, seed, flow='x')
    I = inner(spr)
    keep = I[..., 3].copy()
    for k in range(int(h / 7)):                           # scum and paper packed in it
        py = R.uniform(2, h - 6)
        if k % 2:
            g = TT.paper_shred(seed + 60 + k, R.uniform(6, 10), R.uniform(3.5, 6), alpha=0.95)
        else:
            g = lump(R.uniform(4, 7), R.uniform(2.5, 4), seed + 70 + k, SCUM, GUNK_OUT, bumps=3, flat_bottom=False, soft=0.8)
        paste(I, g, w / 2 - g.shape[1] / SC / 2 + R.uniform(-w * 0.25, w * 0.25), py)
    I[..., 3] = keep
    out = canvas(w + 16, h + 2)
    paste(out, spr, 7, 0)
    for k in range(int(h / 7)):                           # hairs trailing off its sides
        yy = R.uniform(4, h - 6); side = k % 2
        hw = w / 2 * (0.6 + 0.4 * (yy / h) ** 0.6)
        if side:
            loose_hair(out, 8 + w / 2 + hw - 1.5, yy + 1, 3, seed + 90 + k, 0.1, L=(6, 10), curl=1.8)
    return trim(out)


def T_trap():
    far = trap_far()
    R = RS(511)
    mid = wide()
    for k in range(10):                                   # flakes of scum
        g = lump(R.uniform(3, 6), R.uniform(2, 3.5), 511 + k, SCUM, GUNK_OUT, bumps=3, flat_bottom=False, soft=0.8)
        g[..., 3] *= 0.8
        put(mid, g, R.uniform(0, WT), R.uniform(24, GY - 24))
    for k in range(9):
        put(mid, TT.paper_shred(520 + k, R.uniform(7, 12), R.uniform(4, 7)), R.uniform(0, WT), R.uniform(26, GY - 34), 0.85)
    bubble_chain(mid, 6, 530, r=(2, 3), alpha=0.6)
    mid = crop(mid)
    DGLAZE = ramp('#5e8a90', '#94bcc0', '#c4e0e2', '#e6f6f6', '#f8ffff', n=6)
    DCHINA = ramp('#5c6668', '#7c8688', '#9aa4a4', '#b4bcbc', '#c8cece', n=6)
    floor = wall([(3.4, ramp('#7a6a48', '#a8946a', '#c8b48a', '#ddd0aa', n=4), pat_scale), (3.4, DGLAZE, pat_glaze), (40, DCHINA, pat_china)], True, seed=541, bumps=0.7, out='#1e3a40')
    ceil = wall([(3.0, DGLAZE, pat_glaze), (30, DCHINA, pat_china)], False, seed=551, bumps=0.4, out='#1e3a40')
    obs = {'low': [hair_clump(24, 14, 1), hair_clump(28, 13, 2), TT.paper_wad(9, 22, 13)],
           'tall': [clog(42, 7, 21), clog(48, 17, 23)],
           'hang': [hair_rope(1, 9), hair_rope(2, 11)],
           'float': [hair_ball(3, 18), hair_ball(4, 15)],
           'huge': [tower(lambda h: clog(h, 27, 22))]}
    return dict(far=far, mid=mid, floor=floor, ceil=ceil, obs=obs, coin='drop', special='soap')


# ================================================================== 3. the soil stack (the block's pipe down)
WATER_STACK = '#86aab0'
PVC = ramp('#5c6466', '#7e8789', '#a0a9aa', '#bec6c6', '#d6dcdc', '#e8ecec', n=6)
RUBBER = ramp('#0e0e10', '#1e1e22', '#323238', '#4a4a52', n=4)


def falling_water(far, x0, y0, w, y1, seed, k=0.6):
    """a stream of water pouring down the far wall from a branch's mouth (soft, wrapped)"""
    y, x = grid(H, WT)
    R = RS(seed)
    d = wdx(x, x0)
    t = np.clip((y - y0) / max(1, (y1 - y0)), 0, 1)
    half = w / 2 * (1 + 0.6 * t) + 0.8 * np.sin(y * 0.4 + seed)
    core = np.clip((half - np.abs(d)) * SC * 0.25, 0, 1) * (y >= y0) * (1 - np.clip((y - y1) / 10, 0, 1))
    tex = 0.62 + 0.25 * np.sin(d * 1.7 + 0.3 * np.sin(y * 0.05) + seed) + 0.13 * np.sin(d * 4.1 - y * 0.02)
    lerp_rgb(far, '#f2fcff', core * k * tex)
    foam_y = np.exp(-((y - y1) / 5) ** 2) * np.clip((half * 2.4 - np.abs(d)) * SC * 0.1, 0, 1)
    lerp_rgb(far, '#ffffff', foam_y * k * 0.7)


def stack_far(seed=601):
    R = RS(seed)
    far = gradient(H, ['#d0dcdc', '#b0c2c4', '#90a8ac', '#6e8a90'])
    y, x = grid(H, WT)
    pipe_curve(far, 4, GY + 12, 0.28, lit=0.45)
    mul(far, 1 + 0.03 * noise(y.shape, 2.0, seed))
    streaks(far, 70, seed + 1, '#ffffff', k=0.22, y0=0, y1=H, ang=np.pi / 2 - 0.08, L=(50, 160), w=(0.5, 1.4))   # water running down the wall
    streaks(far, 26, seed + 2, '#6a6250', k=0.18, y0=0, y1=H, ang=np.pi / 2 - 0.05, L=(60, 180), w=(0.6, 1.6))   # and the stains it leaves
    ring_joints(far, 3, seed + 3, col='#101014', w=9.0, k=0.55, collar=(16, '#c4cccc'))
    c3 = three(far)
    for k in range(4):                                    # the branches coming in from each floor, water pouring out of them
        cx = (k + 0.5) * WT / 4 + R.uniform(-60, 60); cy = R.uniform(34, 52)
        mw = R.uniform(24, 30)
        m_ = mouth(mw, mw * 0.82, ramp('#4a5254', '#9aa4a6', '#dfe6e6', n=3))
        for off in (0, WT, 2 * WT):
            paste(c3, m_, cx + off - m_.shape[1] / SC / 2, cy - m_.shape[0] / SC / 2)
    far = crop(c3)
    R = RS(seed)                                          # (the same draws again: the water out of each mouth)
    for k in range(4):
        cx = (k + 0.5) * WT / 4 + R.uniform(-60, 60); cy = R.uniform(34, 52); mw = R.uniform(24, 30)
        falling_water(far, cx, cy + mw * 0.15, mw * 0.5, GY - 6, seed + 50 + k, k=0.55)
    TT.caustics(far, seed + 4, k=0.3)
    c3 = three(far)
    drift(c3, 90, ['#ffffff', '#eef8fa', '#dbeef2'], seed + 5, y0=10, y1=GY - 6, a=150)
    far = crop(c3)
    haze(far, WATER_STACK, 0.16)
    return far


def water_column(seed=1, wdt=14):
    """water pouring down from a branch above: a clear, bright stream, wider and frothier as it falls, bubbles
    carried down in it"""
    L = hang_len()
    R = RS(seed)
    W = wdt + 12
    y, x = grid(L, W)
    t = np.clip(y / L, 0, 1)
    cx = W / 2 + 0.8 * np.sin(y * 0.11 + seed)
    half = wdt / 2 * (0.7 + 0.5 * t) + 0.7 * np.sin(y * 0.5 + seed) + 0.4 * np.sin(y * 1.3)
    m = (np.abs(x - cx) <= half) & (y <= L - 1.5 - 2.5 * ((x - cx) / np.maximum(half, 1)) ** 2 + 0.6 * np.sin((x - cx) * 1.3 + seed))
    a = smooth_mask(m)
    u = (x - cx) / np.maximum(half, 1)
    rgb = ramp_col(ramp('#8cc4d4', '#bfe4ee', '#e6f8fc', '#ffffff'), np.clip(0.55 + 0.35 * np.cos(u * np.pi / 2) + 0.15 * np.sin(y * 0.8 - u * 3) - 0.2 * u, 0, 1))
    spr = np.zeros(y.shape + (4,), np.float32)
    spr[..., :3] = rgb
    see = np.clip(0.55 + 0.35 * np.abs(u) ** 2 + 0.25 * t, 0, 1)
    spr[..., 3] = a * 255 * see
    spr = outline(spr, '#2a5a6a', alpha_cut=0.45, width=0.55)
    I = inner(spr)
    for k in range(int(L * 0.5)):                         # bubbles in it
        by = R.uniform(4, L - 4); bxh = wdt / 2 * (0.7 + 0.5 * by / L) * 0.8
        bx = W / 2 + R.uniform(-1, 1) * bxh
        r = R.uniform(0.5, 1.5)
        ellipse_soft(I, bx, by, r, r, '#ffffff', 170)
        ellipse_soft(I, bx - r * 0.3, by - r * 0.3, r * 0.35, r * 0.35, '#2a6a7a', 60)
    for k in range(int(L * 0.3)):                         # bright streaks down it
        sx = W / 2 + R.uniform(-0.8, 0.8) * wdt * 0.4; sy = R.uniform(0, L - 10)
        A.stroke(I, [(sx, sy), (sx + R.uniform(-0.3, 0.3), sy + R.uniform(4, 10))], R.uniform(0.25, 0.5), '#ffffff', 160, scale=1.0)
    return spr


def o_ring(w=24, h=8, seed=1):
    """a black rubber ring off a pipe joint, lying on its side on the bottom (seen a little from above)"""
    y, x = grid(h, w)
    cx, cy = w / 2, h / 2
    rx, ry = w / 2 - 0.8, h / 2 - 0.8
    r = np.sqrt(((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2)
    th = 0.32
    m = (r <= 1) & (r >= 1 - th * (1 + 0.5 * ((y - cy) / ry)))
    spr = A.mask_sprite(m, RUBBER, '#000000', soft=0.7, ambient=0.35, hl_t=0.9)
    return spr


def scale_column(h=40, w=16, seed=1):
    """scale and gunk grown up from the bottom of a joint, a stony stalagmite in layers"""
    R = RS(seed)
    y, x = grid(h, w)
    t = np.clip(y / h, 0, 1)
    cx = w / 2 + 0.8 * np.sin(y * 0.15 + seed)
    half = 1.2 + (w / 2 - 1.2) * t ** 0.7 + 0.6 * np.sin(y * 0.9 + seed) + 0.35 * np.sin(y * 2.3)
    m = (np.abs(x - cx) <= half) & (y < h - 0.6)
    spr = A.mask_sprite(m, ramp('#5a5040', '#887a62', '#b0a286', '#d2c6aa', '#ebe2ca'), '#221c12', soft=1.0, ambient=0.3, hl_t=0.985)
    A.grain(spr, seed, 0.1, 0.4)
    I = inner(spr)
    lay = np.clip(1 - np.abs(np.mod(y + 0.6 * np.sin(x * 1.1), 3.0) - 1.5) / 0.25, 0, 1) * m
    I[..., :3] *= (1 - 0.12 * lay[..., None])
    return spr


def wipe_clog(h, seed=5, w=24):
    """wet wipes and paper packed into one mass (wipes do not break down): creased cloth, stained, ends flapping"""
    R = RS(seed)
    h = int(round(h))
    m = blob_mask(w, h, seed, taper=0.35, wob=0.1)
    spr = A.mask_sprite(m, WIPE, '#2c3c40', soft=1.6, ambient=0.45, hl_t=0.995)
    I = inner(spr)
    y, x = grid(h, w)
    keep = I[..., 3].copy()
    for k in range(int(h * w / 25)):                      # creases between the wipes
        a0 = R.uniform(-0.6, 0.6) + (np.pi / 2 if k % 3 == 0 else 0); cx0, cy0 = R.uniform(0, w), R.uniform(0, h)
        L = R.uniform(4, 9)
        A.stroke(I, [(cx0 - np.cos(a0) * L / 2, cy0 - np.sin(a0) * L / 2), (cx0, cy0 + R.uniform(-0.6, 0.6)), (cx0 + np.cos(a0) * L / 2, cy0 + np.sin(a0) * L / 2)],
                 R.uniform(0.3, 0.5), '#8a9a9c', 140, scale=1.0)
    I[..., 3] = keep
    st = noise(y.shape, 2.0, seed + 3)
    stain = np.clip(st * 1.6 - 0.3, 0, 1) * m * np.clip(1 - y / h + 0.4, 0, 1)
    I[..., :3] = I[..., :3] * (1 - 0.35 * stain[..., None]) + hexc('#a68c58') * 0.35 * stain[..., None]
    return spr


def wipe_flap(seed, w, h):
    R = RS(seed)
    y, x = grid(h, w)
    m = (y > (h / 2) * (x / w) * 0.4 + 0.3 * np.sin(x * 1.3 + seed)) & (y < h - (h / 2) * (x / w) * 0.4 - 0.3) & (x < w - 0.6 - 0.8 * np.abs(np.sin(y * 1.5 + seed)))
    return A.mask_sprite(m, WIPE, '#2c3c40', soft=1.0, ambient=0.5, hl_t=0.995)


def T_stack():
    far = stack_far()
    R = RS(611)
    mid = wide()
    bubble_chain(mid, 9, 612, y0=30, y1=GY - 12, r=(1, 2), alpha=0.55, per=(3, 6))
    motes(mid, 60, ['#ffffff', '#e8f6fa'], 613, r=(0.4, 0.9), a=(110, 190))
    for k in range(4):
        put(mid, TT.paper_shred(620 + k, R.uniform(7, 11), R.uniform(4, 7)), R.uniform(0, WT), R.uniform(26, GY - 34), 0.8)
    mid = crop(mid)
    floor = wall([(1.2, ramp('#5a6460', '#8a948e', '#b4bcb6', n=3), pat_slime), (4.6, PVC, pat_pvc), (40, ramp('#4a4844', '#6c6862', '#8e8a82', '#aaa69c', n=4), pat_concrete)],
                 True, seed=641, bumps=0.25, out='#1e2a2e')
    ceil = wall([(4.6, PVC, pat_pvc), (30, ramp('#4a4844', '#6c6862', '#8e8a82', '#aaa69c', n=4), pat_concrete)], False, seed=651, bumps=0.25, out='#1e2a2e')
    obs = {'low': [o_ring(24, 8, 1), TT.paper_wad(31, 22, 13), o_ring(20, 7, 2)],
           'tall': [scale_column(42, 17, 1), scale_column(48, 15, 2)],
           'hang': [water_column(1, 14), water_column(2, 11)],
           'float': [TT.foam(11, 22, 16), TT.paper_wad(33, 15, 11)],
           'huge': [tower(lambda h: wipe_clog(h, 41, 23))]}
    return dict(far=far, mid=mid, floor=floor, ceil=ceil, obs=obs, coin='drop', special='soap')


# ================================================================== 4. the house drain (grey PVC, under the floor)
WATER_DRAIN = '#7c968e'
PVC_G = ramp('#4e5658', '#6c7476', '#8e9698', '#aeb6b6', '#c8cecc', '#dadfdc', n=6)
FAT = ramp('#8a7a4a', '#b8a670', '#d8c894', '#ece0b4', '#f8f0d4')
FAT_OUT = '#3a3018'
WIPE = ramp('#9aa8aa', '#c4d0d0', '#e2eaea', '#f6faf8', '#ffffff')


def drain_far(seed=701):
    R = RS(seed)
    far = gradient(H, ['#a8bcb4', '#8ea69e', '#728c86', '#526a66'])
    y, x = grid(H, WT)
    pipe_curve(far, 0, GY + 14, 0.32, lit=0.4)
    mul(far, 1 + 0.025 * noise(y.shape, 2.5, seed))
    # the joints: a socket every length, where the next pipe steps in (a lit edge and its shadow)
    for j in range(5):
        x0 = j * WT / 5 + R.uniform(-30, 30)
        d = wdx(x, x0)
        lerp_rgb(far, '#f0f4f0', np.exp(-((d - 1.0) / 0.9) ** 2) * 0.35)
        lerp_rgb(far, '#202a28', np.exp(-((d + 1.2) / 1.6) ** 2) * 0.45)
        lerp_rgb(far, '#202a28', np.clip(1 - (d - 1.5) / 14, 0, 1) * (d > 1.5) * 0.08)
    water_line(far, 24, '#d8c88e', k=0.55, h=9, seed=seed + 1)          # fat along the top of the water
    streaks(far, 30, seed + 2, '#e4d6a2', k=0.3, y0=26, y1=40, L=(30, 120), w=(0.8, 2.2))
    c3 = three(far)
    for k in range(70):                                   # slime: brown-green blotches, more lower down
        bx, by = R.uniform(0, WT), R.uniform(40, GY)
        if R.uniform() > (by - 30) / 130:
            continue
        g = canvas(18, 10)
        ellipse_soft(g, 9, 5, R.uniform(4, 8), R.uniform(1.5, 3.5), ['#5a5a30', '#4a4a26', '#6a5e34'][k % 3], 90, R.uniform(-0.3, 0.3))
        g[..., 3] = ndimage.gaussian_filter(g[..., 3], 1.2 * SC)
        for off in (0, WT, 2 * WT):
            paste(c3, g, bx + off - 9, by - 5)
    drift(c3, 70, ['#e8e6d0', '#ffffff', '#d8d0b0'], seed + 3, y0=26, y1=GY - 8, a=120)
    far = crop(c3)
    TT.caustics(far, seed + 4, y0=26, k=0.2)
    haze(far, WATER_DRAIN, 0.18)
    return far


def food_bits(mid, n, seed):
    """what comes down the kitchen sink: grains of rice, bits of spring onion, flakes of red pepper"""
    R = RS(seed)
    for k in range(n):
        kind = k % 3
        g = canvas(6, 4)
        if kind == 0:
            ellipse_soft(g, 3, 2, 1.5, 0.7, '#f2efe4', 220, R.uniform(-1, 1)); ellipse_soft(g, 2.6, 1.7, 0.6, 0.25, '#ffffff', 200)
        elif kind == 1:
            ellipse_soft(g, 3, 2, 1.2, 1.0, '#5a9a3a', 210); ellipse_soft(g, 3, 2, 0.7, 0.55, '#a8d070', 200)
        else:
            ellipse_soft(g, 3, 2, 1.0, 0.6, '#c42a18', 210, R.uniform(-1, 1))
        put(mid, g, R.uniform(0, WT), R.uniform(30, GY - 10))


def grease_lump(w=24, h=13, seed=1):
    """a lump of cooking fat gone hard (FOG): waxy, yellow-white, lumpy, a crust of bits stuck in it"""
    spr = mass(w, h, seed, FAT, FAT_OUT, taper=0.3, wob=0.18, n=5, ambient=0.4, hl_t=0.985, grain_k=0.1)
    speckle(spr, seed + 1, int(w * h * 0.12), ['#8a6a38', '#6a5028', '#c4a868', '#fff8e0'], r=(0.25, 0.6), a=170)
    return spr


def grease_blob(seed=2, d=15):
    spr = lump(d, d * 0.8, seed, FAT, FAT_OUT, bumps=5, flat_bottom=False, soft=1.6, ambient=0.45, hl_t=0.93)
    I = inner(spr)
    I[..., 3] *= 0.92
    return spr


def wet_wipe(seed=1, w=22, h=13):
    """a wet wipe balled up: a white cloth, its dotted emboss, creased"""
    R = RS(seed)
    y, x = grid(h, w)
    ang = np.arctan2(y - h * 0.55, (x - w / 2) * h / w)
    rr = np.sqrt(((x - w / 2) / (w / 2)) ** 2 + ((y - h * 0.55) / (h * 0.5)) ** 2)
    rag = 0.88 + 0.07 * np.sin(ang * 4 + R.uniform(0, 6)) + 0.04 * np.sin(ang * 9 + R.uniform(0, 6))
    m = (rr <= rag) & (y <= h - 0.6)
    spr = A.mask_sprite(m, WIPE, '#2c3c40', soft=1.6, ambient=0.5, hl_t=0.99)
    I = inner(spr)
    dots = np.clip(1 - np.sqrt((np.mod(x, 1.6) - 0.8) ** 2 + (np.mod(y + 0.8 * (np.floor(x / 1.6) % 2), 1.6) - 0.8) ** 2) / 0.35, 0, 1) * m
    I[..., :3] *= (1 - 0.09 * dots[..., None])
    for k in range(4):
        a0 = R.uniform(0, np.pi); c0 = R.uniform(-0.35, 0.35) * w
        d = (x - w / 2) * np.cos(a0) + (y - h / 2) * np.sin(a0) - c0
        I[..., :3] *= (1 - 0.16 * (np.clip(1 - np.abs(d) / 0.8, 0, 1) * m)[..., None])
    return spr


def wipe_strip(seed=1, wdt=14):
    """a wet wipe caught on the top of the pipe, hanging down in the flow, twisted"""
    L = hang_len()
    R = RS(seed)
    y, x = grid(L, wdt + 8)
    ph = R.uniform(0, 6)
    cx = 4 + wdt / 2 + 2.4 * np.sin(y * 0.04 + ph) * (y / L)
    tw = np.cos(y * 0.06 + ph)                            # twisting: narrower where it turns edge-on
    half = wdt / 2 * (0.35 + 0.65 * np.abs(tw)) * (1 - 0.1 * y / L)
    tear = L - 2 - 2.5 * np.abs(np.sin((x - cx) * 0.8 + ph))
    m = (np.abs(x - cx) <= half) & (y <= tear)
    spr = A.mask_sprite(m, WIPE, '#2c3c40', soft=2.0, ambient=0.5, hl_t=0.995)
    I = inner(spr)
    I[..., :3] *= (0.86 + 0.14 * np.abs(tw))[..., None]
    dots = np.clip(1 - np.sqrt((np.mod(x - cx, 1.6) - 0.8) ** 2 + (np.mod(y, 1.6) - 0.8) ** 2) / 0.35, 0, 1) * m
    I[..., :3] *= (1 - 0.08 * dots[..., None])
    stain = np.clip(1 - np.abs(y - L * R.uniform(0.3, 0.7)) / 9, 0, 1) * m
    I[..., :3] = I[..., :3] * (1 - 0.25 * stain[..., None]) + hexc('#b8a46a') * 0.25 * stain[..., None]
    return spr


def roach(w=22, h=10, seed=1, swim=False):
    """a cockroach (side view): a glossy brown oval back, the head under its shield, six spiny legs, long feelers"""
    R = RS(seed)
    W, Hh = w + 10, h + 4
    out = canvas(W, Hh)
    y, x = grid(h, w)
    body = ((x - w * 0.52) / (w * 0.48)) ** 2 + ((y - h * 0.62) / (h * 0.42)) ** 2 <= 1
    body &= y < h * 0.9
    b = A.mask_sprite(body, ramp('#2a1408', '#5a2c12', '#8a4a20', '#b8743a', '#e0a868'), '#120804', soft=1.4, ambient=0.3, hl_t=0.9)
    Ib = inner(b)
    for k in range(3):                                    # the wing cases' edges and the band lines across the back
        xx = w * (0.35 + 0.18 * k)
        A.stroke(Ib, [(xx, h * 0.3), (xx + 1.5, h * 0.95)], 0.25, '#2a1206', 120, scale=1.0)
    A.stroke(Ib, [(w * 0.2, h * 0.32), (w * 0.95, h * 0.5)], 0.3, '#2a1206', 140, scale=1.0)
    hd = ellipse_mask(int(w * 0.28) + 1, int(h * 0.6) + 1)
    head = A.mask_sprite(hd, ramp('#3a1c0c', '#6a3a1c', '#9a6a3c', '#c89a62'), '#120804', soft=0.8, ambient=0.3)
    legs = canvas(W, Hh)
    for k in range(3):                                    # legs: spiny, bent at the knee
        lx = 6 + w * (0.38 + 0.18 * k); ly = 2 + h * 0.9
        kx, ky = lx + (-3 + 2.5 * k) + R.uniform(-0.5, 0.5), ly + 2.2
        fx, fy = kx + (-2.5 + 3 * k), Hh - 0.6
        if swim:
            ky -= 1.5; fy = ly + 2.6; fx = kx + (3 if k == 2 else -3)
        A.stroke(legs, [(lx, ly), (kx, ky), (fx, fy)], 0.5, '#3a1a08', 255, scale=1.0)
        for s in range(3):
            q = (s + 1) / 4
            sx, sy = kx + (fx - kx) * q, ky + (fy - ky) * q
            A.stroke(legs, [(sx, sy), (sx + 0.6, sy - 0.5)], 0.18, '#3a1a08', 220, scale=1.0)
    for k, (ex, ey) in enumerate([(-1.0, -1.6), (-1.2, -0.6)]):   # the feelers, long and curving back
        pts = [(6 + ex * 0, 2 + h * 0.5)]
        for t in np.linspace(0, 1, 16)[1:]:
            pts.append((6 - 6 * t + 2.5 * np.sin(t * 2.2 + k), 2 + h * 0.5 + ey * 6 * t + 2.5 * t * t * (k * 2 - 1)))
        A.stroke(out, pts, 0.22, '#3a1a08', 230, scale=1.0)
    paste(out, legs, 0, 0)
    paste(out, b, 5, 2 - 1)
    paste(out, head, 4, 2 + h * 0.35)
    I = out
    ellipse_soft(I, 6.5, 2 + h * 0.6, 0.5, 0.5, '#100804', 255)
    return trim(out)


def grease_mound(h=40, w=22, seed=3):
    """fat built up on the bottom into a mound, wipes and bits caught in it"""
    R = RS(seed)
    h = int(round(h))
    spr = mass(w, h, seed, FAT, FAT_OUT, taper=0.5, wob=0.12, ambient=0.4, hl_t=0.985, grain_k=0.1)
    speckle(spr, seed + 1, int(w * h * 0.1), ['#8a6a38', '#6a5028', '#fff8e0'], r=(0.25, 0.6), a=160)
    I = inner(spr); keep = I[..., 3].copy()
    for k in range(int(h / 9)):                           # wipes caught in it
        yy = R.uniform(h * 0.1, h * 0.85); g = wet_wipe(seed + 20 + k, R.uniform(7, 10), R.uniform(4, 6))
        paste(I, g, w / 2 - g.shape[1] / SC / 2 + R.uniform(-w * 0.2, w * 0.2), yy)
    I[..., 3] = keep
    return spr


def T_drain():
    far = drain_far()
    R = RS(711)
    mid = wide()
    for k in range(16):                                   # droplets of fat
        g = grease_blob(720 + k, R.uniform(3, 6))
        g[..., 3] *= 0.75
        put(mid, g, R.uniform(0, WT), R.uniform(30, GY - 20))
    food_bits(mid, 60, 730)
    motes(mid, 40, ['#d8d0b0', '#ffffff'], 731, r=(0.3, 0.7), a=(90, 160))
    mid = crop(mid)
    SOIL = ramp('#2a2018', '#44362a', '#5e4c3a', '#7a6650', '#968066', n=5)
    floor = wall([(1.4, ramp('#3e4024', '#5e6036', '#7e7c4a', n=3), pat_slime), (4.2, PVC_G, pat_pvc), (40, SOIL, pat_soil)], True, seed=741, bumps=0.3, out='#1a2220')
    ceil = surf_ceil(751, ramp('#4e5658', '#6c7476', '#9aa2a2', '#c4caca', n=4), crown_h=6.5, air=('#3e4c48', '#5e6e6a', '#84948e'),
                     mirror='#e6eee0', out='#283430')
    obs = {'low': [grease_lump(24, 13, 1), wet_wipe(2, 22, 13), roach(22, 9, 3)],
           'tall': [grease_mound(40, 22, 3), wipe_clog(46, 15, 22)],
           'hang': [wipe_strip(1, 14), wipe_strip(2, 12)],
           'float': [roach(20, 9, 5, swim=True), grease_blob(6, 15)],
           'huge': [tower(lambda h: grease_mound(int(h), 24, 9))]}
    return dict(far=far, mid=mid, floor=floor, ceil=ceil, obs=obs, coin='drop', special='soap')


# ================================================================== 5. the septic tank
WATER_SEPTIC = '#4e5a3a'
SLUDGE = ramp('#1e160c', '#3a2a16', '#5a4224', '#7a5c34', '#9a7a4c')
SLUDGE_OUT = '#0c0804'


def septic_far(seed=801):
    R = RS(seed)
    far = gradient(H, ['#7a8458', '#5e6a42', '#46502e', '#2e341c'])
    y, x = grid(H, WT)
    concrete_tex(far, seed + 1, k=0.9, cols=('#20241a', '#a8ac88'))
    for j in range(6):                                     # the formwork's lines and its tie holes
        yy = 22 + j * 24
        lerp_rgb(far, '#1a1e12', np.exp(-((y - yy) / 0.5) ** 2) * 0.35)
    c3 = three(far)
    for j in range(6):
        for i in range(int(WT / 60)):
            hx, hy = i * 60 + 30 + (j % 2) * 30, 22 + j * 24 + 12
            for off in (0, WT, 2 * WT):
                ellipse_soft(c3, hx + off, hy, 1.6, 1.6, '#12160c', 180)
                ellipse_soft(c3, hx + off + 0.4, hy - 0.4, 0.9, 0.9, '#2a301c', 160)
    far = crop(c3)
    streaks(far, 40, seed + 2, '#2a2414', k=0.3, y0=0, y1=H, ang=np.pi / 2, L=(30, 110), w=(0.8, 2.5))
    water_line(far, 30, '#3a3218', k=0.5, h=16, seed=seed + 3)
    silt(far, 124, ('#1a140a', '#3a2a16', '#5a4426', '#6e5632'), seed + 4)
    c3 = three(far)
    for k in range(3):                                    # the inlet tee coming down from the top, black inside
        cx = (k + 0.3) * WT / 3 + R.uniform(-40, 40)
        t = canvas(16, 74)
        fill_rect(t, 2, 0, 14, 70, '#4a5048')
        yy, xx = grid(74, 16)
        sh = np.clip(0.55 + 0.4 * np.cos((xx - 8) / 6 * np.pi / 2) - 0.25 * (xx > 8), 0, 1)
        t[..., :3] = ramp_col(ramp('#2a2e28', '#5a6058', '#8a9086', '#aab0a4'), sh) * (t[..., 3:4] > 0)
        ellipse_soft(t, 8, 70, 6, 2.2, '#0a0c08', 255)
        t = outline(t, '#10140c')
        for off in (0, WT, 2 * WT):
            paste(c3, t, cx + off - 8, -2)
    drift(c3, 160, ['#a8a070', '#8a8456', '#c4bc8a'], seed + 5, y0=20, y1=GY - 4, a=170)
    far = crop(c3)
    haze(far, WATER_SEPTIC, 0.26)
    return far


def scum_ceil(seed=851):
    """the scum on top of the tank, seen from below: a thick brown crust, lumpy, gas bubbles stuck under it"""
    R = RS(seed)
    c3 = np.zeros((px(CH), 3 * px(WT), 4), np.float32)
    y, x = grid(CH, WT)
    edge = 12.5 + 1.6 * per_sin(x, 13, R.uniform(0, 6)) + 1.0 * per_sin(x, 37, R.uniform(0, 6)) + 0.6 * per_sin(x, 97, R.uniform(0, 6))
    n = noise(y.shape, 0.9, seed + 1)
    edge = edge + 0.8 * n
    m = np.clip((edge - y) * SC * 0.5 + 0.5, 0, 1)
    dep = np.clip((edge - y) / 6, 0, 1)
    sh = np.clip(0.75 - 0.55 * dep + 0.18 * noise(y.shape, 0.5, seed + 2) + 0.12 * np.clip(1 - (edge - y) / 1.2, 0, 1), 0, 1)
    rgb = ramp_col(ramp('#1a1408', '#36280e', '#58421c', '#7a6030', '#9a8248'), sh)
    t = np.zeros((px(CH), px(WT), 4), np.float32)
    ol = np.clip(1 - np.abs(edge - y - 0.2) / 0.45, 0, 1) * 0.85
    rgb = rgb * (1 - ol[..., None]) + hexc('#0c0804') * ol[..., None]
    t[..., :3] = rgb; t[..., 3] = m * 255
    for k in range(3):
        c3[:, k * px(WT):(k + 1) * px(WT)] = t
    for k in range(140):                                  # gas bubbles stuck under the crust
        bx = R.uniform(0, WT); r = R.uniform(0.6, 1.8)
        by = float(edge[0, min(px(bx), edge.shape[1] - 1)]) + r * 0.4
        b = bubble(max(1, int(round(r))), seed + k)
        b[..., :3] = b[..., :3] * 0.8 + hexc('#c8d0a0') * 0.2
        for off in (0, WT, 2 * WT):
            paste(c3, b, bx + off - b.shape[1] / SC / 2, by - b.shape[0] / SC / 2)
    return crop(c3)


def sludge_lump(w=24, h=13, seed=1):
    """a lump of settled sludge: soft, dark brown, wet sheen, bits of fibre in it"""
    spr = mass(w, h, seed, SLUDGE, SLUDGE_OUT, taper=0.3, wob=0.2, n=5, ambient=0.3, hl_t=0.985, grain_k=0.14)
    speckle(spr, seed + 1, int(w * h * 0.1), ['#b89a62', '#d8c08a', '#2a1c0c'], r=(0.2, 0.5), a=160)
    return spr


def scum_hang(seed=1, wdt=16):
    """a lump of the scum hanging down from the crust: heavy, sagging, dripping at the end"""
    L = hang_len()
    R = RS(seed)
    W = wdt + 8
    y, x = grid(L, W)
    t = np.clip(y / L, 0, 1)
    cx = W / 2 + 1.5 * np.sin(y * 0.06 + seed) * t
    half = wdt / 2 * (1 - 0.45 * t) + 1.4 * np.sin(y * 0.18 + seed) * (1 - t * 0.5) + 0.6 * np.sin(y * 0.7)
    bulbs = np.exp(-((y - L * 0.55) / 8) ** 2) * 2.0 + np.exp(-((y - L * 0.85) / 6) ** 2) * 1.5
    half = half + bulbs
    tip = L - 2 - 3 * (np.abs(x - cx) / np.maximum(half, 1)) ** 2
    m = (np.abs(x - cx) <= half) & (y <= tip)
    spr = A.mask_sprite(m, ramp('#1e160a', '#3a2c12', '#5c4620', '#7e6436', '#9c8452'), SLUDGE_OUT, soft=2.0, ambient=0.3, hl_t=0.97)
    A.grain(spr, seed, 0.12, 0.5)
    speckle(spr, seed + 2, int(L * 1.2), ['#c8b07a', '#e0d0a0', '#16100a'], r=(0.2, 0.5), a=150)
    I = inner(spr)
    for k in range(10):                                   # bubbles of gas in it
        by = R.uniform(4, L - 10); bx = W / 2 + R.uniform(-0.5, 0.5) * wdt * 0.6
        ellipse_soft(I, bx, by, 0.7, 0.7, '#e8ecd0', 200); ellipse_soft(I, bx - 0.2, by - 0.2, 0.25, 0.25, '#ffffff', 230)
    return spr


def gas_bubbles(seed=1, w=18, h=16):
    """bubbles of gas from the rotting sludge (methane), stuck together rising: clear, a sickly yellow-green sheen"""
    R = RS(seed)
    out = canvas(w, h)
    for k in range(6):
        r = R.uniform(2.6, 5.4)
        bx, by = R.uniform(r + 0.6, w - r - 1.2), R.uniform(r + 0.6, h - r - 1.2)
        b = bubble(int(round(r)), seed * 10 + k)
        Ib = inner(b)
        Ib[..., :3] = Ib[..., :3] * 0.55 + hexc('#c8dc78') * 0.45
        paste(out, b, bx - r - 1, by - r - 1)
    return trim(out)


def sludge_pile(h, seed=5, w=24):
    """sludge heaped up off the bottom: one dark sagging mass, fibres and grit in it"""
    h = int(round(h))
    spr = mass(w, h, seed, SLUDGE, SLUDGE_OUT, taper=0.55, wob=0.12, ambient=0.3, hl_t=0.985, grain_k=0.14)
    return speckle(spr, seed + 1, int(w * h * 0.1), ['#b89a62', '#d8c08a', '#2a1c0c'], r=(0.2, 0.5), a=160)


def T_septic():
    far = septic_far()
    R = RS(811)
    mid = wide()
    motes(mid, 220, ['#8a8256', '#6a6440', '#b4ac7a', '#3a3420'], 812, r=(0.3, 1.1), a=(110, 210))
    bubble_chain(mid, 16, 813, y0=40, y1=GY - 14, r=(1, 3), alpha=0.6, per=(3, 6))
    for k in range(8):
        s = sludge_lump(R.uniform(5, 9), R.uniform(3, 5), 820 + k); s[..., 3] *= 0.8
        put(mid, s, R.uniform(0, WT), R.uniform(30, GY - 16))
    mid = crop(mid)
    CONC = ramp('#2e3024', '#4a4c3c', '#6a6a56', '#8a8a72', '#a4a48a', n=5)
    floor = wall([(5.0, SLUDGE, pat_sludge), (40, CONC, pat_concrete)], True, seed=841, bumps=0.9, out='#0c0a06')
    ceil = scum_ceil()
    obs = {'low': [sludge_lump(24, 13, 1), sludge_lump(28, 12, 2)],
           'tall': [sludge_pile(42, 3, 22), sludge_pile(48, 13, 24)],
           'hang': [scum_hang(1, 16), scum_hang(2, 13)],
           'float': [gas_bubbles(1, 22, 19), gas_bubbles(2, 19, 17)],
           'huge': [tower(lambda h: sludge_pile(h, 23, 24))]}
    return dict(far=far, mid=mid, floor=floor, ceil=ceil, obs=obs, coin='drop', special='soap')
