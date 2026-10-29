# Shared drawing for stage 3 (river.py, sea.py): out of the outfall, down the river, through the estuary, into the sea
# and down to its floor. The water (a far layer of graded water, light from the surface: caustics and shafts, fading
# with depth), the bed (gravel, sand, mud, rock, in section), the surface from below (or none, deep down), things far
# off faded into the water, and the creatures and things in it (fish of many kinds, crabs, shells, weed, coral...).
import numpy as np
from scipy import ndimage
from art import (H, SC, px, grid, canvas, ramp, ramp_col, hexc, paint, ellipse_mask, outline, paste, over, blur, disc,
                 ellipse_soft, inner, smooth_mask, fill_rect)
import anatomy as A
from tiles import WT, GY, FH, FY0, CH, TAU, wide, crop, put, per_sin, gradient, haze, pcells, wall, band_line, spots
from themes import three, drift, tower, stack, hang_len, bubble, flip_v
from variants import noise
import toilet as TT
from s2lib import (lerp_rgb, mul, motes, bubble_chain, pat_gravel, pat_soil, pebble_surface, surf_ceil, strands, lump,
                   speckle, trim, blob_mask, mass, silt)

RS = np.random.RandomState


def put_wrap(c3, spr, x, y, a=1.0):
    for off in (0, WT, 2 * WT):
        paste(c3, spr, x + off, y, a)


def faded(spr, col, k, a=1.0):
    """a sprite pushed back into the water: its colour toward the water's, a little see-through"""
    s = spr.copy()
    lerp_rgb(s, col, k)
    s[..., 3] *= a
    return s


def scaled(spr, k):
    import cv2
    h, w = spr.shape[:2]
    return cv2.resize(spr, (max(1, int(w * k)), max(1, int(h * k))), interpolation=cv2.INTER_AREA)


# ------------------------------------------------------------------ the water
def water_far(cols, seed, caust=0.5, shafts=7, deep=False):
    """graded water (top light .. bottom dark); light from the surface: a caustic net and slanting shafts"""
    far = gradient(H, cols)
    if caust:
        TT.caustics(far, seed + 1, k=caust)
    if shafts:
        TT.light_shafts(far, seed + 2, n=shafts)
    if deep:                                               # deep down: darker toward the bottom still
        y, x = grid(H, WT)
        mul(far, 1 - 0.25 * np.clip(y / H, 0, 1) ** 1.5)
    return far


def glow_spots(far, n, seed, cols, r=(0.4, 1.4), y0=0, y1=GY, a=(0.5, 1.0)):
    """points of light in the dark (bioluminescence): a bright core, a soft halo"""
    R = RS(seed)
    c3 = three(far)
    for k in range(n):
        x, y, rr = R.uniform(0, WT), R.uniform(y0, y1), R.uniform(*r)
        col = cols[k % len(cols)]; al = R.uniform(*a)
        for off in (0, WT, 2 * WT):
            ellipse_soft(c3, x + off, y, rr * 4, rr * 4, col, int(60 * al))
            ellipse_soft(c3, x + off, y, rr, rr, '#ffffff', int(230 * al))
    return crop(c3)


def sky_ceil(seed, sky=('#a4d8f4', '#c4e8fa', '#e4f6ff'), mirror='#f2fff8', out='#2a4a3a', extra=None, surf_y=13.6):
    """the surface seen from below with the sky over it (no pipe or lid above: open water)"""
    return surf_ceil(seed, ramp('#8ac4e8', '#a8d6f2', '#c8e6fa', '#e8f6ff', n=4), crown_h=0.5, air=sky, mirror=mirror,
                     out=out, extra=extra, surf_y=surf_y)


def foam_extra(n=90, seed=1, r=(0.8, 2.4)):
    """white water under the surface: bubbles and froth along it (a ceiling's `extra` hook)"""
    def ex(c3, R, rim_b, surf):
        RR = RS(seed)
        for k in range(n):
            x = RR.uniform(0, WT); rr = RR.uniform(*r); y = 14.5 + RR.uniform(0, 9) ** 1.3 / 3
            b = bubble(max(1, int(rr)), seed + k); b[..., 3] *= RR.uniform(0.5, 0.95)
            for off in (0, WT, 2 * WT):
                paste(c3, b, x + off - rr, y - rr)
        for k in range(int(n * 0.6)):                         # froth: soft white clouds hugging the surface
            x = RR.uniform(0, WT); w = RR.uniform(8, 22)
            for off in (0, WT, 2 * WT):
                ellipse_soft(c3, x + off, 15.2, w, RR.uniform(1.2, 2.6), '#ffffff', int(RR.uniform(90, 170)))
    return ex


# ------------------------------------------------------------------ the bed in section
def pat_sand(sh, x, ld, u, shape, h, R):
    n = int(0.2 * WT * h)
    P = np.c_[R.uniform(0, WT, n), R.uniform(0, h, n)]
    g = spots(shape, P, R.uniform(0.12, 0.3, n), WT)
    lay = 0.05 * np.sin(ld * 1.4 + 0.6 * np.sin(x * 0.03))
    return sh + 0.1 * g * np.where(R.uniform(0, 1, 1) > 0.5, 1, -1) - 0.06 * g + lay


def pat_mud(sh, x, ld, u, shape, h, R):
    n = int(0.02 * WT * h)
    P = np.c_[R.uniform(0, WT, n), R.uniform(0, h, n)]
    shells = spots(shape, P, R.uniform(0.3, 0.9, n), WT)
    xx = x + 0.6 * np.sin(ld * 0.5)
    holes = band_line(xx, 37, 0.9, 5.0) * np.clip(1 - ld / 9, 0, 1)            # burrows going down from the top
    return sh - 0.45 * holes + 0.25 * shells + 0.05 * np.sin(ld * 0.5 + x * 0.02)


def pat_rock(sh, x, ld, u, shape, h, R):
    cb, _, _ = pcells(h, 60, int(R.uniform(1, 1e6)), sy=1.0, border=0.8)
    return sh - 0.32 * cb ** 3 + 0.08 * (1 - cb)


def bed(seed, top, deep, pat_top=pat_gravel, pat_deep=pat_soil, out='#141008', top_th=6, surface=None, bumps=1.0):
    """the bed in section: a top layer (gravel, sand, mud) on what lies under it"""
    return wall([(top_th, top, pat_top), (40, deep, pat_deep)], True, seed=seed, bumps=bumps, out=out, surface=surface)


def things_on_bed(sprites, n, seed, sink=0.4):
    """a floor's `surface` hook: small things lying along its top (shells, stones, litter)"""
    def surf(c3, edge_w, e0, top_edge):
        R = RS(seed)
        for k in range(n):
            s = sprites[k % len(sprites)]
            x = R.uniform(0, WT); e = edge_w[int(x) % WT]
            hh = s.shape[0] / SC
            for off in (0, WT, 2 * WT):
                paste(c3, s, x + off - s.shape[1] / SC / 2, e0 + e - hh + sink * hh * 0.4)
    return surf


def ripples_surface(seed, col='#fff6d8', n=46):
    """sand ripples: soft bright crests along the top of a sandy bed"""
    def surf(c3, edge_w, e0, top_edge):
        R = RS(seed)
        for k in range(n):
            x = R.uniform(0, WT); w = R.uniform(6, 14); e = edge_w[int(x) % WT]
            for off in (0, WT, 2 * WT):
                ellipse_soft(c3, x + off, e0 + e + 1.1, w, 0.6, col, int(R.uniform(70, 140)))
    return surf


# ------------------------------------------------------------------ rocks and stones
STONES = [('#3a3a36', '#62625a', '#8e8e82', '#b8b8aa', '#dcdcd0'), ('#3e3428', '#66584a', '#8e7e6a', '#b4a690', '#d8ccb4'),
          ('#2e3638', '#4e5a5e', '#76848a', '#a0aeb2', '#c8d4d6')]


def stone(w, h, seed, cols=None, out='#161612', grain=0.08):
    """a rounded stone (river-worn: smooth, a few flecks)"""
    R = RS(seed)
    cols = cols or STONES[seed % len(STONES)]
    y, x = grid(h, w)
    ang = np.arctan2(y - h / 2, (x - w / 2) * h / w)
    rr = np.sqrt(((x - w / 2) / (w / 2 - 0.7)) ** 2 + ((y - h / 2) / (h / 2 - 0.7)) ** 2)
    m = rr <= 0.94 + 0.05 * np.sin(ang * 3 + seed) + 0.03 * np.sin(ang * 5 + 2 * seed)
    spr = A.mask_sprite(m, ramp(*cols), out, soft=1.0, ambient=0.35, hl_t=0.97)
    A.grain(spr, seed, grain, 0.4)
    speckle(spr, seed + 1, int(w * h * 0.25), ['#2a2a24', '#e8e4d8'], r=(0.15, 0.35), a=140)
    return spr


def boulder(w, h, seed, cols=None, out='#141410', flat=True):
    """a big rough rock sitting on the bed: facets, cracks"""
    R = RS(seed)
    cols = cols or STONES[seed % len(STONES)]
    m = blob_mask(w, h, seed, taper=0.25, wob=0.18, flat_bottom=flat)
    spr = A.mask_sprite(m, ramp(*cols), out, soft=0.9, ambient=0.3, hl_t=0.96)
    I = inner(spr)
    y, x = grid(I.shape[0] / SC, I.shape[1] / SC)
    cb, _, _ = pcells(int(h) + 1, 14, seed, sy=1.0, border=0.6, ww=int(w) + 1)
    cb = cb[:I.shape[0], :I.shape[1]]
    lerp_rgb(I, '#000000', (cb ** 4) * 0.35 * (I[..., 3] > 0))
    A.grain(spr, seed, 0.1, 0.5)
    return spr


def rock_spire(h, seed=1, w=26, cols=None):
    """rocks heaped up into a column"""
    R = RS(seed)
    parts = []; tot = 0
    while tot < h - 2:
        sh = R.uniform(10, 15); parts.append(sh); tot += sh - 2.6
    parts[-1] = max(5.0, parts[-1] - (tot - (h - 2)))
    sprs = []; acc = 0
    for k, sh in enumerate(parts):
        sw = w * R.uniform(0.75, 1.0) * (1 - 0.3 * acc / max(h, 1))
        sprs.append(boulder(sw, sh, seed * 7 + k, cols)); acc += sh
    return stack(sprs, gap=-2.6)


# ------------------------------------------------------------------ fish (of many kinds), facing left (they come at you)
def fish(w, h, seed=1, back='#3a5a5a', side='#9abcb4', belly='#eef4f0', out='#0e1a1a', stripes=0, stripe_col='#1e2a2a',
         bars=0, bar_col='#ffffff', fin='#7a9a92', kind='minnow', spots_col=None, eye=1.0):
    """a fish seen from the side, head at the left (they come at you): one silhouette (body, tail, the fins on top and
    under) shaded as one, coloured back to belly; stripes along it (stripes) or bands across it (bars); kinds: minnow,
    sardine (slim), cat (round flat head, whiskers, a long low fin), goby (big head, eyes on top, round tail), file (deep,
    a spine on top), lion (bands, long spines and fan fins)"""
    R = RS(seed)
    pad = 3.0 if kind == 'lion' else 1.6
    W, Hh = w, h + 2 * pad
    y, x = grid(Hh, W)
    t = x / (w * 0.82)                                      # 0 at the nose .. 1 where the tail starts
    tc = np.clip(t, 0, 1)
    hh = h / 2 - 0.6
    cy = Hh / 2 + (0.08 * h if kind == 'cat' else 0)
    if kind == 'file':
        half = hh * np.maximum(np.sin(np.clip(tc, 0.001, 1) ** 0.85 * np.pi), 0) ** 0.5 * (1 - 0.25 * tc)
    elif kind in ('cat', 'goby'):
        half = hh * np.sqrt(np.clip(tc * 7, 0, 1)) * (1 - 0.72 * tc ** 1.4)
    elif kind == 'sardine':
        half = hh * np.maximum(np.sin(np.clip(tc, 0.001, 1) ** 0.8 * np.pi), 0) ** 0.65 * (1 - 0.25 * tc)
    else:
        half = hh * np.maximum(np.sin(np.clip(tc, 0.001, 1) ** 0.8 * np.pi), 0) ** 0.7 * (1 - 0.3 * tc)
    half = np.where(t <= 1, half, 0)
    flat_top = 0.75 if kind == 'cat' else 1.0                # the catfish is flat above
    body = (y - cy >= -half * flat_top) & (y - cy <= half) & (x > 0.5)
    # the tail
    xt = (x - w * 0.8) / (w * 0.2)
    if kind in ('goby', 'cat'):
        tail = (xt >= 0) & (x < w - 0.5) & (xt ** 2 + ((y - cy) / (h * 0.3)) ** 2 <= 1.0)
    else:
        spread = 0.25 * h + xt * 0.3 * h
        notch = np.abs(y - cy) < np.clip(xt - 0.45, 0, 1) * 0.55 * h
        tail = (xt >= 0) & (x < w - 0.5) & (np.abs(y - cy) <= spread) & ~notch
    # the fins: dorsal (top), anal (under), as part of the outline
    def tri(xa, xb, peak):
        u = np.clip((x - xa) / max(xb - xa, 1e-3), 0, 1)
        return np.where((x >= xa) & (x <= xb), peak * np.maximum(np.sin(u * np.pi), 0) ** 0.8 * (1 - 0.4 * u), 0)
    if kind == 'cat':
        dors = tri(w * 0.3, w * 0.42, h * 0.22); anal = tri(w * 0.45, w * 0.8, h * 0.16)
    elif kind == 'goby':
        dors = tri(w * 0.3, w * 0.45, h * 0.3) + tri(w * 0.5, w * 0.76, h * 0.2); anal = tri(w * 0.52, w * 0.76, h * 0.15)
    elif kind == 'file':
        dors = tri(w * 0.55, w * 0.78, h * 0.14); anal = tri(w * 0.55, w * 0.78, h * 0.14)
    elif kind == 'lion':
        dors = tri(w * 0.2, w * 0.72, h * 0.18); anal = tri(w * 0.55, w * 0.72, h * 0.2)
    else:
        dors = tri(w * 0.36, w * 0.56, h * 0.26); anal = tri(w * 0.56, w * 0.7, h * 0.14)
    top = cy - half * flat_top
    finm = ((y < top) & (y >= top - dors)) | ((y > cy + half) & (y <= cy + half + anal))
    m = body | tail | finm
    spr = A.mask_sprite(m, ramp('#1a1a1a', '#5a5a5a', '#a4a4a4', '#dcdcdc', '#ffffff'), out, soft=1.0, ambient=0.42, hl_t=0.94)
    I = inner(spr)
    sh = I[..., :3].mean(-1, keepdims=True) / 255.0                       # keep the shading, colour it back to belly
    u = np.clip((y - cy) / np.maximum(half, 0.8), -1, 1)[..., None]
    colmap = np.where(u < 0, hexc(side) * (1 + u) + hexc(back) * (-u), hexc(side) * (1 - u) + hexc(belly) * u)
    colmap = np.where((finm | tail)[..., None], hexc(fin) * 1.0, colmap)
    mk = m[..., None] * 1.0
    I[..., :3] = I[..., :3] * (1 - mk) + np.clip(colmap * (0.42 + 0.78 * sh), 0, 255) * mk
    lerp_rgb(I, '#ffffff', ((finm | tail) & (np.sin(x * 5.0) > 0.6)) * 0.12)                # fin rays
    if stripes:
        for k in range(stripes):
            yy = cy + (k - (stripes - 1) / 2) * h * 0.18
            lerp_rgb(I, stripe_col, (np.abs(y - yy) < h * 0.05) * body * (x > w * 0.18) * 0.7)
    if bars:
        for k in range(bars):
            xx = w * (0.22 + 0.5 * k / max(1, bars - 1)) if bars > 1 else w * 0.45
            bw = w * 0.045
            d = np.abs(x - xx - 0.25 * (y - cy))
            lerp_rgb(I, bar_col, (d < bw) * (body | finm) * 0.92)
            lerp_rgb(I, '#101010', (np.abs(d - bw) < 0.3) * (body | finm) * 0.6)
    if spots_col:
        for k in range(int(w * h / 12)):
            sx, sy = R.uniform(w * 0.15, w * 0.8), R.uniform(cy - h * 0.35, cy + h * 0.35)
            iy, ix = min(int(sy * SC), body.shape[0] - 1), min(int(sx * SC), body.shape[1] - 1)
            if body[iy, ix]:
                ellipse_soft(I, sx, sy, R.uniform(0.3, 0.6), R.uniform(0.3, 0.5), spots_col, 190)
    # the gill's curve, a pectoral fin behind it, the eye, the mouth
    gx = w * (0.22 if kind not in ('cat', 'goby') else 0.27)
    A.stroke(I, [(gx, cy - h * 0.26), (gx + w * 0.025, cy), (gx, cy + h * 0.26)], 0.35, '#000000', 80, scale=1.0)
    ellipse_soft(I, gx + w * 0.07, cy + h * 0.1, w * 0.07, h * 0.08, fin, 210, 0.5)
    ex = w * (0.1 if kind not in ('goby', 'cat') else 0.12)
    ey = cy - h * (0.1 if kind not in ('goby', 'cat') else 0.22)
    er = max(0.75, min(w, h) * 0.11) * eye
    ellipse_soft(I, ex, ey, er, er, '#f4f4ec', 255); ellipse_soft(I, ex - er * 0.1, ey, er * 0.62, er * 0.62, '#080808', 255)
    ellipse_soft(I, ex - er * 0.35, ey - er * 0.3, er * 0.25, er * 0.25, '#ffffff', 240)
    A.stroke(I, [(0.9, cy + h * 0.06), (w * 0.06, cy + h * 0.1)], 0.3, '#000000', 110, scale=1.0)
    if kind == 'lion':                                      # long spines up, wide fan fins down (in front of the body)
        for k in range(10):
            x0 = w * (0.22 + 0.05 * k); y0 = float((cy - half * flat_top)[0, min(int(x0 * SC), half.shape[1] - 1)])
            L = h * R.uniform(0.3, 0.5)
            A.stroke(spr, [(x0 + 1, y0 + 1), (x0 + 1 + L * 0.3, y0 + 1 - L)], 0.4, '#3a0a04', 255, scale=1.0)
        for k in range(7):
            a = 0.35 + 0.12 * k
            A.stroke(spr, [(gx + w * 0.06 + 1, cy + 1), (gx + w * 0.06 + 1 + np.cos(a) * h * 0.55, cy + 1 + np.sin(a) * h * 0.55)], 0.3, '#f4dcd0', 220, scale=1.0)
    if kind == 'cat':
        for s_ in (-1, 1):
            A.stroke(spr, [(1.6, cy + 1.2), (0.4, cy + 2.2 + s_ * 0.8), (0.2, cy + 3.4 + s_ * 1.6)], 0.3, '#1a140a', 255, scale=1.0)
    return trim(spr)


def half_at(half, x0):
    """the body's half height at x0 (from the half-height field: its column)"""
    col = min(int(x0 * SC), half.shape[1] - 1)
    return float(half[:, col].max())


def school(n, w, h, seed, maker, spread=(40, 24)):
    """a tight group of the same fish, a little ragged"""
    R = RS(seed)
    out = canvas(spread[0] + w + 4, spread[1] + h + 4)
    for k in range(n):
        f = maker(seed + k)
        paste(out, f, R.uniform(0, spread[0]), R.uniform(0, spread[1]))
    return trim(out)


# ------------------------------------------------------------------ weed and grass
def ribbons(h, seed=1, w=20, cols=('#2e7424', '#3a8a2a', '#4ea036'), out='#0e2a0e', n=9, sway=5.0, wid=2.0, hi='#a8e47a'):
    """a clump of soft ribbon leaves growing up from the bed, swaying (eelgrass, waterweed)"""
    R = RS(seed)
    h = int(round(h))
    out_ = canvas(w, h)
    blades = []
    for k in range(n):
        x0 = w / 2 + R.uniform(-w * 0.22, w * 0.22); l = R.uniform(0.6, 1.0) * (h - 1); bend = R.uniform(-1, 1) * sway; ph = R.uniform(0, 6)
        pts = [(x0 + bend * t ** 1.6 + 1.2 * np.sin(t * 5 + ph) * t, h - 0.6 - l * t) for t in np.linspace(0, 1, 28)]
        blades.append((pts, cols[k % len(cols)]))
    for pts, c in blades:
        for i in range(len(pts) - 1):
            ww = max(0.4, wid * (1 - i / len(pts) * 0.7))
            A.stroke(out_, [pts[i], pts[i + 1]], ww + 0.55, out, 255, scale=1.0)
    for pts, c in blades:
        for i in range(len(pts) - 1):
            ww = max(0.3, wid * (1 - i / len(pts) * 0.7))
            A.stroke(out_, [pts[i], pts[i + 1]], ww, c, 255, scale=1.0)
            A.stroke(out_, [(pts[i][0] - ww * 0.25, pts[i][1]), (pts[i + 1][0] - ww * 0.25, pts[i + 1][1])], ww * 0.28, hi, 170, scale=1.0)
    return trim(out_)


def ribbons_hang(seed=1, wdt=12, cols=('#3a8a2a', '#5aa83e', '#2e7424'), out='#0e2a0e', n=10, wid=1.8, L=None):
    """long strands streaming down from the surface (or a line, a buoy) in the current"""
    L = L or hang_len()
    R = RS(seed)
    W = wdt + 12
    o = canvas(W, L)
    lines = []
    for k in range(n):
        x0 = W / 2 + R.uniform(-wdt / 2, wdt / 2); l = R.uniform(0.6, 1.0) * L; ph = R.uniform(0, 6)
        lines.append(([(x0 + 3.0 * np.sin(t * 3.0 + ph) * t, t * l) for t in np.linspace(0, 1, 40)], cols[k % len(cols)]))
    for pts, c in lines:
        for i in range(39):
            A.stroke(o, [pts[i], pts[i + 1]], max(0.4, wid * (1 - i / 39 * 0.6)) + 0.5, out, 255, scale=1.0)
    for pts, c in lines:
        for i in range(39):
            A.stroke(o, [pts[i], pts[i + 1]], max(0.3, wid * (1 - i / 39 * 0.6)), c, 255, scale=1.0)
    return trim(o)[:px(L)]


def weed_far(c3, n, seed, cols, y_bot=150, h=(30, 90), a=(0.35, 0.6), w=1.0):
    """water plants far off, waving up from the bed (into a far layer, three-wide)"""
    R = RS(seed)
    for k in range(n):
        bx = R.uniform(0, WT); hh = R.uniform(*h); ph = R.uniform(0, 6)
        g = canvas(16, hh)
        for b in range(3):
            pts = [(8 + (b - 1) * 1.5 + 3 * np.sin(t * 2.5 + ph + b) * t, hh - t * hh * R.uniform(0.7, 1.0)) for t in np.linspace(0, 1, 20)]
            A.stroke(g, pts, R.uniform(0.8, 1.4) * w, cols[b % len(cols)], 200, scale=1.0)
        g[..., 3] *= R.uniform(*a)
        put_wrap(c3, g, bx - 8, y_bot - hh)


# ------------------------------------------------------------------ small creatures and shells
def crab(w=20, h=11, seed=1, cols=('#5a1a0e', '#9a3418', '#c8582a', '#e8864a', '#ffc08a'), out='#220804'):
    """a crab sideways on: a wide shell, two claws up, legs splayed"""
    y, x = grid(h, w)
    cx, cy = w / 2, h * 0.52
    shell = ((x - cx) / (w * 0.3)) ** 2 + ((y - cy) / (h * 0.3)) ** 2 <= 1
    claws = np.zeros_like(shell)
    for s_ in (-1, 1):
        ccx = cx + s_ * w * 0.36
        claws |= ((x - ccx) / (w * 0.1)) ** 2 + ((y - h * 0.28) / (h * 0.2)) ** 2 <= 1
        claws &= ~((np.abs(x - ccx - s_ * 0.2) < 0.35) & (y < h * 0.24))           # the pincer's gap
    legs = np.zeros_like(shell)
    for s_ in (-1, 1):
        for k in range(3):
            x0 = cx + s_ * w * (0.18 + 0.06 * k); x1 = cx + s_ * w * (0.33 + 0.07 * k)
            tt = np.clip((x - x0) / (x1 - x0 + 1e-6), 0, 1)
            yy = cy + h * 0.1 + tt * (h * 0.42 - h * 0.1) - 1.5 * np.sin(tt * np.pi)
            legs |= (np.abs(y - yy) < 0.45) & (((x - x0) * s_) >= 0) & (((x1 - x) * s_) >= 0)
    arms = np.zeros_like(shell)
    for s_ in (-1, 1):
        x0, x1 = cx + s_ * w * 0.2, cx + s_ * w * 0.34
        tt = np.clip((x - x0) / (x1 - x0 + 1e-6), 0, 1)
        yy = cy - tt * h * 0.2
        arms |= (np.abs(y - yy) < 0.6) & (((x - x0) * s_) >= 0) & (((x1 - x) * s_) >= 0)
    m = shell | claws | legs | arms
    spr = A.mask_sprite(m, ramp(*cols), out, soft=0.9, ambient=0.35, hl_t=0.96)
    I = inner(spr)
    for s_ in (-1, 1):                                    # eyes on stalks
        A.stroke(I, [(cx + s_ * 1.4, cy - h * 0.26), (cx + s_ * 1.8, cy - h * 0.42)], 0.4, out, 255, scale=1.0)
        ellipse_soft(I, cx + s_ * 1.8, cy - h * 0.43, 0.75, 0.75, '#0a0a0a', 255)
        ellipse_soft(I, cx + s_ * 1.6, cy - h * 0.48, 0.25, 0.25, '#ffffff', 230)
    return spr


def shell_sprite(w=12, h=8, seed=1, cols=('#6a5a4a', '#a8927a', '#d4c0a4', '#f0e2cc', '#fff8ec'), out='#2a2018', kind='clam'):
    """a shell lying on the bed: a clam (a fan with ridges) or a cone (a spiral tower: a snail, a whelk)"""
    y, x = grid(h, w)
    if kind == 'clam':
        m = (((x - w / 2) / (w / 2 - 0.6)) ** 2 + ((y - h) / (h - 0.6)) ** 2 <= 1) & (y > 0.6)
    else:
        t = 1 - y / h
        m = (np.abs(x - w * 0.5 + (1 - t) * 0.0) <= (w / 2 - 0.6) * np.clip(1 - t, 0.08, 1) ** 0.8) & (y > 0.6) & (y < h - 0.5)
    spr = A.mask_sprite(m, ramp(*cols), out, soft=0.8, ambient=0.35, hl_t=0.95)
    I = inner(spr)
    if kind == 'clam':
        ang = np.arctan2(h - y, x - w / 2)
        lerp_rgb(I, '#5a4a3a', (0.5 + 0.5 * np.sin(ang * 22)) ** 6 * m * 0.45)
    else:
        lerp_rgb(I, '#3a2a1a', (0.5 + 0.5 * np.sin((y + x * 0.4) * 2.2)) ** 8 * m * 0.5)
    return spr


def starfish(w=16, h=7, seed=1, cols=('#7a1e0e', '#c03a18', '#e8642a', '#ff9a5a', '#ffcc9a'), out='#2a0804'):
    """a starfish lying on the bed, seen low from the side: five arms, bumps along them"""
    R = RS(seed)
    y, x = grid(w, w)
    cx = cy = w / 2
    ang = np.arctan2(y - cy, x - cx) + R.uniform(0, 1)
    r = np.hypot(x - cx, y - cy) / (w / 2 - 0.6)
    arm = 0.32 + 0.68 * (0.5 + 0.5 * np.cos(ang * 5)) ** 2.6
    m = r <= arm
    spr = A.mask_sprite(m, ramp(*cols), out, soft=0.9, ambient=0.35, hl_t=0.95)
    I = inner(spr)
    for k in range(60):
        rr = R.uniform(0.1, 0.9); a = R.uniform(0, TAU)
        px_, py_ = cx + np.cos(a) * rr * w / 2, cy + np.sin(a) * rr * w / 2
        if A.on(spr, px_ + 1, py_ + 1):
            ellipse_soft(I, px_, py_, 0.35, 0.35, '#ffe0c0', 200)
    import cv2
    s = cv2.resize(spr, (spr.shape[1], max(4, int(spr.shape[0] * h / w))), interpolation=cv2.INTER_AREA)   # seen low: squashed
    return s


def urchin(w=14, h=11, seed=1, body=('#1a0a24', '#3a1a4a', '#5a2e6a', '#7a4a8a', '#a07ab0'), spine='#2a0e34', tip='#c8a0e0'):
    """a sea urchin: a small round dark body bristling with long sharp spines all round its top"""
    R = RS(seed)
    o = canvas(w, h)
    cx, cy, r = w / 2, h * 0.6, min(w, h) * 0.2
    L0 = min(w / 2 - 0.3, cy - 0.3)
    for k in range(120):
        a = np.pi * 0.82 + (k / 120) * np.pi * 1.36 + R.uniform(-0.03, 0.03)
        L = r + R.uniform(0.55, 1.0) * (L0 - r)
        A.stroke(o, [(cx + np.cos(a) * r * 0.6, cy + np.sin(a) * r * 0.6), (cx + np.cos(a) * L, cy + np.sin(a) * L)], 0.42, '#0a0410', 255, scale=1.0)
    R = RS(seed)
    for k in range(120):
        a = np.pi * 0.82 + (k / 120) * np.pi * 1.36 + R.uniform(-0.03, 0.03)
        L = r + R.uniform(0.55, 1.0) * (L0 - r)
        A.stroke(o, [(cx + np.cos(a) * r * 0.6, cy + np.sin(a) * r * 0.6), (cx + np.cos(a) * L, cy + np.sin(a) * L)], 0.22, spine if k % 3 else tip, 255, scale=1.0)
    m = ellipse_mask(int(2 * r) + 1, int(2 * r * 0.9) + 1)
    b = A.mask_sprite(m, ramp(*body), '#0a0410', soft=1.0, ambient=0.3, hl_t=0.95)
    paste(o, b, cx - b.shape[1] / SC / 2, cy - b.shape[0] / SC / 2 + 0.3)
    return trim(o)


def anemone(h=40, seed=1, w=20, cols=('#7a1a3a', '#b42a5a', '#e04a7a', '#f88aac', '#ffc8da'), tent=('#ff8ab4', '#ffd0e0'), out='#2a0614', stalk=True):
    """a sea anemone on a stalk (or low on a rock): a column, a crown of thick waving tentacles"""
    R = RS(seed)
    h = int(round(h))
    o = canvas(w + 6, h)
    top = h * (0.55 if stalk else 0.15)
    y, x = grid(h - top, w * 0.5)
    m = np.abs(x - w * 0.25) <= w * 0.18 + 0.06 * w * (y / max(1, h - top))
    col_ = A.mask_sprite(m, ramp(*cols), out, soft=1.0, ambient=0.3, hl_t=0.97)
    paste(o, col_, 3 + w / 2 - col_.shape[1] / SC / 2, top - 1)
    for k in range(26):
        a = np.pi * (1.05 + 0.9 * k / 25); L = R.uniform(0.55, 1.0) * min(top + 2, w * 0.55)
        ph = R.uniform(0, 6)
        pts = [(3 + w / 2 + np.cos(a) * L * t + 1.2 * np.sin(t * 4 + ph) * t, top + 1 + np.sin(a) * L * t) for t in np.linspace(0, 1, 12)]
        A.stroke(o, pts, 1.3, out, 255, scale=1.0)
    R = RS(seed)
    for k in range(26):
        a = np.pi * (1.05 + 0.9 * k / 25); L = R.uniform(0.55, 1.0) * min(top + 2, w * 0.55)
        ph = R.uniform(0, 6)
        pts = [(3 + w / 2 + np.cos(a) * L * t + 1.2 * np.sin(t * 4 + ph) * t, top + 1 + np.sin(a) * L * t) for t in np.linspace(0, 1, 12)]
        A.stroke(o, pts, 0.85, tent[0], 255, scale=1.0)
        disc(o, pts[-1][0], pts[-1][1], 0.45, tent[1], 255)
    return trim(o)


def jelly(r=8, seed=1, bell=('#6a8ac8', '#9ab4e8', '#c8d8f8', '#eaf2ff'), out='#2a3a6a', L=30, tent='#b4c8f0', arms='#f0d0ff', a=0.85, n_t=9):
    """a jellyfish: a see-through bell, a frill, long thin tentacles and frilly mouth arms trailing down"""
    R = RS(seed)
    W, Hh = 2 * r + 6, r + L + 2
    o = canvas(W, Hh)
    cx = W / 2
    for k in range(n_t):                                   # tentacles
        x0 = cx + (k - (n_t - 1) / 2) / ((n_t - 1) / 2 + 1e-6) * r * 0.9; ph = R.uniform(0, 6); l = R.uniform(0.7, 1.0) * L
        pts = [(x0 + 1.4 * np.sin(t * 6 + ph) * t, r * 0.95 + t * l) for t in np.linspace(0, 1, 30)]
        A.stroke(o, pts, 0.32, tent, 200, scale=1.0)
    for k in range(4):                                     # mouth arms
        x0 = cx + (k - 1.5) * r * 0.22; ph = R.uniform(0, 6); l = R.uniform(0.45, 0.7) * L
        pts = [(x0 + 1.8 * np.sin(t * 4 + ph) * t, r * 0.9 + t * l) for t in np.linspace(0, 1, 24)]
        for i in range(23):
            A.stroke(o, [pts[i], pts[i + 1]], 1.2 * (1 - i / 30), arms, 210, scale=1.0)
    y, x = grid(r + 1, 2 * r)
    m = (((x - r) / (r - 0.4)) ** 2 + ((y - (r + 0.2)) / r) ** 2 <= 1) & (y < r + 0.3)
    b = A.mask_sprite(m, ramp(*bell), out, soft=1.4, ambient=0.45, hl_t=0.93)
    I = inner(b)
    lerp_rgb(I, '#ffffff', (np.abs(np.hypot(x - r, (y - r) * 1.3) - r * 0.45) < 0.4) * m * 0.35)    # its four rings inside
    b[..., 3] *= a
    paste(o, b, cx - r - 1, -0.8)
    return trim(o)


def kelp(h, seed=1, w=22, cols=('#4a3a0e', '#7a5e1a', '#a8842a', '#c8a64a'), out='#1e1404'):
    """kelp: a holdfast on the bed, a stipe up, broad wavy brown blades off it"""
    R = RS(seed)
    h = int(round(h))
    o = canvas(w, h)
    pts = [(w / 2 + 2.0 * np.sin(t * 3 + seed), h - 1 - t * (h - 3)) for t in np.linspace(0, 1, 40)]
    for i in range(39):
        A.stroke(o, [pts[i], pts[i + 1]], 1.6, out, 255, scale=1.0)
    for i in range(39):
        A.stroke(o, [pts[i], pts[i + 1]], 1.0, cols[1], 255, scale=1.0)
    for k in range(int(h / 9)):
        i = int(4 + k * 36 / max(1, int(h / 9))); i = min(i, 38)
        bx, by = pts[i]; s_ = 1 if k % 2 else -1; L = R.uniform(6, 10); ph = R.uniform(0, 6)
        bp = [(bx + s_ * L * t, by - 2 * t + 0.8 * np.sin(t * 7 + ph)) for t in np.linspace(0, 1, 14)]
        for j in range(13):
            ww = 2.4 * np.sin(np.pi * (j + 0.5) / 14) + 0.4
            A.stroke(o, [bp[j], bp[j + 1]], ww + 0.5, out, 255, scale=1.0)
        for j in range(13):
            ww = 2.4 * np.sin(np.pi * (j + 0.5) / 14) + 0.4
            A.stroke(o, [bp[j], bp[j + 1]], ww, cols[2 + (k % 2)], 255, scale=1.0)
            A.stroke(o, [bp[j], bp[j + 1]], ww * 0.25, '#e8d48a', 160, scale=1.0)
    hold = blob_mask(w * 0.6, 5, seed, taper=0.2, wob=0.25)
    hs = A.mask_sprite(hold, ramp(*cols), out, soft=0.8, ambient=0.3, hl_t=0.97)
    paste(o, hs, w / 2 - hs.shape[1] / SC / 2, h - hs.shape[0] / SC + 1)
    return trim(o)


def coral_branch(h, seed=1, w=24, cols=('#8a1a3a', '#c83a5a', '#f06a84', '#ff9ab0', '#ffd0dc'), out='#2a0614', thick=1.6):
    """branching coral: a trunk forking again and again, rounded tips"""
    R = RS(seed)
    h = int(round(h))
    o = canvas(w, h)
    segs = []
    def grow(x, y, ang, L, th, d):
        x2, y2 = x + np.cos(ang) * L, y - np.sin(ang) * L
        segs.append(((x, y), (x2, y2), th))
        if d < 4 and y2 > 2:
            for da in (-0.45, 0.4):
                grow(x2, y2, ang + da + R.uniform(-0.15, 0.15), L * R.uniform(0.62, 0.8), th * 0.78, d + 1)
        else:
            segs.append(((x2, y2), (x2, y2), th * 1.15))
    grow(w / 2, h - 0.5, np.pi / 2, h * 0.32, thick * 1.6, 0)
    for (a, b, th) in segs:
        A.stroke(o, [a, b], th + 0.7, out, 255, scale=1.0)
    for (a, b, th) in segs:
        A.stroke(o, [a, b], th, cols[2], 255, scale=1.0)
    for (a, b, th) in segs:
        A.stroke(o, [(a[0] - th * 0.25, a[1]), (b[0] - th * 0.25, b[1])], th * 0.35, cols[3], 200, scale=1.0)
        if a == b:
            disc(o, b[0] - th * 0.2, b[1] - th * 0.2, th * 0.3, cols[4], 230)
    return trim(o)


def brain_coral(w=24, h=12, seed=1, cols=('#5a4a1a', '#8a7a2e', '#b4a44a', '#d8c870', '#f0e4a0'), out='#221a06'):
    """a brain coral: a dome covered in meandering grooves"""
    m = blob_mask(w, h, seed, taper=0.1, wob=0.08)
    spr = A.mask_sprite(m, ramp(*cols), out, soft=1.4, ambient=0.32, hl_t=0.97)
    I = inner(spr)
    y, x = grid(I.shape[0] / SC, I.shape[1] / SC)
    f = np.sin(x * 1.6 + 1.8 * np.sin(y * 0.9 + seed)) * np.sin(y * 1.9 + 1.4 * np.sin(x * 0.7))
    lerp_rgb(I, cols[0], (np.abs(f) < 0.18) * (I[..., 3] > 0) * 0.65)
    return spr


def fan(h, seed=1, w=26, col='#c8402a', hi='#ff8a5a', out='#3a0a04'):
    """a sea fan (gorgonian): a flat lacy fan of fine branches on a short stem"""
    R = RS(seed)
    h = int(round(h))
    o = canvas(w, h)
    segs = []
    def grow(x, y, ang, L, th, d):
        x2, y2 = x + np.cos(ang) * L, y - np.sin(ang) * L
        segs.append(((x, y), (x2, y2), th))
        if d < 6:
            for da in (-0.35, 0.35):
                grow(x2, y2, ang + da + R.uniform(-0.1, 0.1), L * 0.78, max(0.25, th * 0.72), d + 1)
    grow(w / 2, h - 0.5, np.pi / 2, h * 0.2, 1.4, 0)
    for (a, b, th) in segs:
        A.stroke(o, [a, b], th + 0.45, out, 255, scale=1.0)
    for (a, b, th) in segs:
        A.stroke(o, [a, b], th, col, 255, scale=1.0)
        A.stroke(o, [a, b], th * 0.35, hi, 180, scale=1.0)
    return trim(o)


def bubbles_sprite(n, seed, w=12, h=40, r=(1, 3), a=0.85):
    R = RS(seed)
    o = canvas(w + 6, h + 6)
    for k in range(n):
        rr = int(R.uniform(*r)); b = bubble(rr, seed + k); b[..., 3] *= a
        paste(o, b, R.uniform(0, w), R.uniform(0, h))
    return trim(o)


# ------------------------------------------------------------------ hazards (in common.webp): what drops, juts, darts
def leaf_drop():
    """a dead leaf sinking"""
    import sewer as SW
    return SW.leaf('m', 12, 61)


def leaf_mat(w=24, h=6):
    """the leaf come to rest: a soft brown pile on the bed"""
    import sewer as SW
    return SW.leaf_pile(w, h, 62)


def rock_spike(size='s', seed=7):
    """a sharp stone sticking up out of the bed"""
    R = RS(seed + (5 if size == 't' else 0))
    w, h = (15, 21) if size == 's' else (17, 33)
    y, x = grid(h, w)
    t = np.clip(y / h, 0, 1)
    cx = w / 2 - 0.5 + 1.4 * (1 - t) * (1 if seed % 2 else -1)
    jag = 0.4 * np.sin(y * 1.1 + seed) + 0.25 * np.sin(y * 2.9)
    half = 0.6 + (w / 2 - 0.8) * t ** 0.9 + jag * t
    m = np.abs(x - cx) <= half
    spr = A.mask_sprite(m, ramp('#2e3638', '#4e5a5e', '#76848a', '#a0aeb2', '#c8d4d6'), '#101414', soft=0.6, ambient=0.3, hl_t=0.97)
    A.grain(spr, seed, 0.1, 0.4)
    return spr


def shell_drop():
    """a big shell sinking, turning over"""
    return shell_sprite(14, 9, 71, kind='clam')


def shell_mat(w=24, h=6):
    """shells and broken bits come to rest on the sand"""
    o = canvas(w, h)
    for k in range(5):
        s = shell_sprite(7 + k % 3, 4 + k % 2, 72 + k, kind='clam' if k % 2 == 0 else 'cone')
        paste(o, s, 1 + k * (w - 9) / 4, h - s.shape[0] / SC)
    return trim(o)


def urchin_spike(size='s', seed=9):
    """an urchin's long spines bristling up (a short clump, or one on a rock)"""
    if size == 's':
        return urchin(15, 15, seed)
    o = canvas(17, 33)
    r = boulder(15, 20, seed, STONES[2])
    paste(o, r, 1, 33 - r.shape[0] / SC)
    u = urchin(15, 15, seed + 1)
    paste(o, u, 1, 33 - r.shape[0] / SC - u.shape[0] / SC + 4)
    return trim(o)


def fish_shot():
    """a small fish darting at you"""
    return fish(15, 6, 81, back='#1a3a6a', side='#5a8ac8', belly='#e8f0ff', out='#08142a', stripes=1, stripe_col='#f0d040')


def pearl_item():
    """the stage's special: a pearl in an open shell"""
    o = canvas(14, 13)
    sh = shell_sprite(14, 7, 91, cols=('#4a3a5a', '#8a7a9a', '#c4b4d4', '#eae0f4', '#ffffff'), out='#1e142a')
    paste(o, sh, 0, 13 - sh.shape[0] / SC)
    m = ellipse_mask(7, 7)
    p = A.mask_sprite(m, ramp('#a89ab8', '#d4cce0', '#f4f0f8', '#ffffff'), '#3a2e4a', soft=1.6, ambient=0.5, hl_t=0.9)
    paste(o, p, 3.5, 1.2)
    return trim(o)
