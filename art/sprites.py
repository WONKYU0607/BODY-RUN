# Items in the style of the character sheet (rounded, softly shaded, dark outline, glossy spot), HD.
import numpy as np
from scipy import ndimage
from art import (SC, px, grid, ramp, hexc, paint, dome_shade, ellipse_mask, outline, highlight, fill_rect, paste, canvas,
                 flip, over, text, disc, stroke, smooth_mask)

LIGHT = (-0.55, -0.7, 0.45)


def cov(sd):
    """coverage from a signed distance in units (negative inside)"""
    return np.clip(-sd * SC + 0.5, 0, 1)


def blob(mask, rmp, out_col, hl='#ffffff', hl_t=0.975, soft=1.6, ambient=0.22, ox=0, oy=0, steps=7):
    sh, n = dome_shade(mask, LIGHT, soft=soft, ambient=ambient)
    spr = paint(mask, rmp, sh)
    if hl:
        spr = highlight(spr, mask, n, LIGHT, hl, hl_t)
    return outline(spr, out_col), sh


def layer(dst, coverage, col, a=1.0):
    c = hexc(col) if isinstance(col, str) else col
    over(dst, np.broadcast_to(c, coverage.shape + (3,)), coverage * a)


# ------------------------------------------------------------------ items (about 12 units)
def coin_c():
    m = ellipse_mask(12, 12)
    spr, _ = blob(m, ramp('#8a3300', '#d65f00', '#ff8a1a', '#ffb347', '#ffd98a'), '#3d1600', soft=1.0, ambient=0.3)
    y, x = grid(14, 14)
    r = np.sqrt((x - 6.5) ** 2 + (y - 6.5) ** 2)
    def cshape(dy):
        rr = np.sqrt((x - 6.5) ** 2 + (y - 6.5 - dy) ** 2)
        ring = cov(np.abs(rr - 3.7) - 0.55)
        gap = cov(np.maximum(7.2 - x, np.abs(y - 6.5 - dy) - 2.0))
        return ring * (1 - gap)
    layer(spr, cshape(0.45), '#b04800')          # its shadow
    layer(spr, cshape(0.0), '#fff3d6')
    return spr


def bubble_o2():
    m = ellipse_mask(12, 12)
    sh, n = dome_shade(m, LIGHT, soft=1.0, ambient=0.3)
    spr = paint(m, ramp('#1f6aa8', '#3a96e0', '#62b8ff', '#9ad6ff', '#cdeeff', n=6), sh)
    spr = outline(spr, '#0c2440')
    # a white crescent of shine, and O2 in the middle
    pts = [(6.5 + np.cos(a) * 4.3, 6.5 + np.sin(a) * 4.3) for a in np.linspace(np.pi * 1.05, np.pi * 1.45, 12)]
    stroke(spr, pts, 1.2, '#ffffff', 235, scale=1.0)
    text(spr, 'O', 5.9, 6.6, 4.3, '#ffffff', '#0c2440', 0.35)
    text(spr, '2', 9.0, 8.4, 2.6, '#ffffff', '#0c2440', 0.3)
    return spr


def hex_fe():
    y, x = grid(12, 12)
    cx, cy = 5.5, 5.5
    m = (np.abs(y - cy) <= 5.6) & (np.abs(x - cx) * 0.866 + np.abs(y - cy) * 0.5 <= 5.2)
    spr, _ = blob(m, ramp('#5c0a14', '#a8162a', '#e0283f', '#ff6070', '#ffb0b8'), '#2a040a', soft=0.8, ambient=0.3)
    text(spr, 'Fe', 6.6, 6.7, 4.0, '#ffffff', '#7a0a18', 0.4)
    return spr


def capsule(c1, c2, w=14, h=8, out='#2a1a08', hl=True):
    y, x = grid(h, w)
    r = (h - 1) / 2
    m = ((x - r) ** 2 + (y - r) ** 2 <= r * r + 0.5) | ((x - (w - 1 - r)) ** 2 + (y - r) ** 2 <= r * r + 0.5) | ((x >= r) & (x <= w - 1 - r))
    sh, n = dome_shade(m, LIGHT, soft=1.0, ambient=0.25)
    k = np.clip((x - (w / 2 - 0.5)) * SC + 0.5, 0, 1)[..., None]
    a = paint(m, c1, sh); b = paint(m, c2, sh)
    spr = a * (1 - k) + b * k
    seam = np.clip(1 - np.abs(x - (w / 2 - 0.5)) * SC / 1.2, 0, 1) * m
    spr[..., :3] *= (1 - 0.35 * seam[..., None])
    if hl:
        spr = highlight(spr, m, n, LIGHT, '#ffffff', 0.9)
    return outline(spr, out)


def omega_drop():
    return capsule(ramp('#8a5a00', '#d99a00', '#ffcc22', '#ffe680'), ramp('#8a5a00', '#d99a00', '#ffcc22', '#ffe680'), 13, 8, '#3a2400')


def multi_vit():
    return capsule(ramp('#8a1a5a', '#e0408a', '#ff7ab0', '#ffc0dc'), ramp('#a07a20', '#f0d040', '#fff080', '#ffffd0'), 16, 9, '#2a0a20')


def heal_cap():
    """the healing item: a green orb with a white plus"""
    m = ellipse_mask(13, 13)
    spr, _ = blob(m, ramp('#0a5a2e', '#1a9a50', '#3ccc74', '#86f0a8', '#c8ffd8'), '#06240f', soft=1.0, ambient=0.3)
    y, x = grid(15, 15)
    def plus(arm, half):
        a = np.maximum(np.abs(x - 7.0) - half, np.abs(y - 7.0) - arm)
        b = np.maximum(np.abs(x - 7.0) - arm, np.abs(y - 7.0) - half)
        return cov(np.minimum(a, b) - 0.15)
    layer(spr, plus(4.1, 1.55), '#06240f')
    layer(spr, plus(3.35, 0.8), '#ffffff')
    return spr


def broccoli():
    spr = canvas(13, 14)
    y, x = grid(14, 13)
    stem = ((x >= 5) & (x < 8) & (y >= 8) & (y < 13)) | ((x >= 4) & (x < 9) & (y >= 10) & (y < 13))
    s, _ = blob(stem, ramp('#5a7a20', '#8fbf3a', '#c4e86a'), '#1e2a08', hl=None, soft=0.6)
    paste(spr, s, -1, -1)
    for (cx, cy, r) in [(6, 5, 3.4), (3, 6, 2.6), (9, 6, 2.6), (6, 3, 2.6)]:
        m = ellipse_mask(13, 14, cx, cy, r, r)
        f, _ = blob(m, ramp('#1d5a1d', '#2f8a2f', '#4fb84f', '#8fe08f'), '#0c2a0c', soft=0.8)
        paste(spr, f, -1, -1)
    # floret buds
    R = np.random.RandomState(4)
    for k in range(26):
        a, rr = R.uniform(0, 2 * np.pi), R.uniform(0, 4.5)
        bx, by = 6 + np.cos(a) * rr * 1.1, 4.6 + np.sin(a) * rr * 0.75
        if spr[min(px(by + 0.5), spr.shape[0] - 1), min(px(bx + 0.5), spr.shape[1] - 1), 3] > 200:
            disc(spr, bx, by, 0.42, '#9ae89a' if k % 3 else '#1d5a1d', 170)
    return spr


def heart():
    """the HUD heart"""
    y, x = grid(12, 13)
    a = np.sqrt((x - 3.6) ** 2 + (y - 3.6) ** 2) - 3.4
    b = np.sqrt((x - 8.4) ** 2 + (y - 3.6) ** 2) - 3.4
    tri = np.maximum(np.abs(x - 6.0) * 1.05 + (y - 11.2) * 0.95, -(y - 3.0))
    m = np.minimum(np.minimum(a, b), tri) <= 0
    spr, _ = blob(m, ramp('#8a0a2a', '#d4204a', '#ff4a70', '#ff8aa4', '#ffd0dc'), '#1a0a14', soft=0.8, ambient=0.3, hl_t=0.95)
    return spr


def atp():
    """ATP, the cell's energy: a golden orb with a white lightning bolt and a soft glow (found up high)"""
    m = ellipse_mask(12, 12)
    spr, _ = blob(m, ramp('#7a4a00', '#d08a00', '#ffc21a', '#ffe36a', '#fff6c0'), '#3a2200', soft=1.0, ambient=0.3)
    y, x = grid(14, 14)
    # the bolt: a zig-zag polygon
    from matplotlib.path import Path
    pts = [(7.6, 1.9), (3.9, 7.4), (6.6, 7.4), (5.4, 12.2), (10.2, 5.8), (7.3, 5.8), (8.8, 1.9)]
    P = Path(pts)
    inside = P.contains_points(np.c_[x.ravel() + 0.5, y.ravel() + 0.5]).reshape(x.shape)
    m2 = ndimage.binary_dilation(inside, iterations=max(1, int(SC * 0.45)))
    layer(spr, smooth_mask(m2), '#5a3000')
    layer(spr, smooth_mask(inside), '#ffffff')
    # a glow round it
    out = canvas(20, 20)
    yy, xx = grid(20, 20)
    r = np.sqrt((xx - 9.5) ** 2 + (yy - 9.5) ** 2)
    g = np.clip(1 - (r - 6.5) / 3.2, 0, 1) ** 2 * 0.55
    out[..., :3] = hexc('#ffe070'); out[..., 3] = g * 255
    paste(out, spr, 3, 3)
    return out
