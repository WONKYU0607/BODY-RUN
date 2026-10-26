# HD art toolkit for the side-scrolling body run. Everything is laid out in WORLD UNITS (the game's native picture is
# 390 x 180 units) exactly as the pixel version was, but rasterised at SC pixels per unit, with smooth shading,
# anti-aliased edges and outlines, and fine detail. Coordinates follow the pixel version's convention: "coordinate c"
# is the middle of the old pixel c, i.e. the world position c + 0.5.
import numpy as np
import cv2
from PIL import Image
from scipy import ndimage

SC = 5                      # pixels per world unit
W, H = 390, 180
OUTW = 0.72                 # outline width, world units
LW = 0.8                    # strokes: drawn this fraction of their nominal (pixel-version) width


def px(v):
    return int(round(v * SC))


def hexc(h):
    if not isinstance(h, str):
        return np.asarray(h, np.float32)
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32)


def ramp(*hexes, n=None):
    """colours from dark to light (n: resampled to n steps; shading is continuous anyway)"""
    cs = [hexc(h) for h in hexes]
    if not n or n == len(cs):
        return cs
    t = np.linspace(0, len(cs) - 1, n)
    return [cs[int(np.floor(v))] * (1 - (v - np.floor(v))) + cs[min(int(np.floor(v)) + 1, len(cs) - 1)] * (v - np.floor(v)) for v in t]


def ramp_col(rmp, v):
    """continuous colour along the ramp for v in [0, 1] (any shape) -> (..., 3)"""
    pal = np.array(rmp, np.float32)
    n = len(pal)
    t = np.clip(v, 0, 1) * (n - 1)
    i0 = np.floor(t).astype(np.int32)
    i0 = np.clip(i0, 0, n - 1)
    i1 = np.minimum(i0 + 1, n - 1)
    f = (t - i0)[..., None].astype(np.float32)
    return pal[i0] * (1 - f) + pal[i1] * f


def grid(h, w):
    """HD pixel grid of a (w x h world units) area, in old-style coordinates: y, x float32 (broadcast views)"""
    Hh, Ww = px(h), px(w)
    y = ((np.arange(Hh, dtype=np.float32) + 0.5) / SC - 0.5)[:, None]
    x = ((np.arange(Ww, dtype=np.float32) + 0.5) / SC - 0.5)[None, :]
    return np.broadcast_to(y, (Hh, Ww)), np.broadcast_to(x, (Hh, Ww))


def canvas(w=W, h=H):
    return np.zeros((px(h), px(w), 4), np.float32)


def inner(spr):
    """the part of an outlined sprite that lines up with the mask it was made from (outline() pads one unit)"""
    return spr[SC:-SC, SC:-SC]


def smooth_mask(mask, s=0.6):
    """anti-aliased coverage from a hard mask"""
    m = mask.astype(np.float32)
    return np.minimum(m, ndimage.gaussian_filter(m, s)) if mask.dtype == bool else m


def paint(mask, rmp, shade, ox=0, oy=0, dither=False):
    """an RGBA sprite: the mask filled from the ramp by shade (0 dark .. 1 light), continuously"""
    h, w = mask.shape
    out = np.zeros((h, w, 4), np.float32)
    out[..., :3] = ramp_col(rmp, shade if np.ndim(shade) else np.full((h, w), shade, np.float32))
    out[..., 3] = (mask.astype(np.float32) if mask.dtype != bool else mask) * 255
    return out


def quantize(v, levels, h=None, w=None, ox=0, oy=0, dither=False):
    """kept for compatibility: continuous index in [0, levels-1]"""
    return np.clip(v, 0, 1) * (levels - 1)


def wgrad(f, wrap=False):
    """gradient (gy, gx) per HD pixel; wrap: the x axis wraps (tileable fields)"""
    gy = np.gradient(f, axis=0)
    if wrap:
        gx = (np.roll(f, -1, axis=1) - np.roll(f, 1, axis=1)) * 0.5
    else:
        gx = np.gradient(f, axis=1)
    return gy, gx


def blur(f, sigma_units, wrap=False):
    """gaussian blur with sigma in world units"""
    s = sigma_units * SC
    return ndimage.gaussian_filter(f, s, mode=('reflect', 'wrap') if wrap else 'reflect')


def dome_shade(mask, light=(-0.55, -0.7, 0.45), soft=2.0, flat=0.0, ambient=0.18):
    """light a blob like a soft pillow: height from the distance to its edge (world units), normals from that"""
    m = mask > 0.5 if mask.dtype != bool else mask
    d = ndimage.distance_transform_edt(m) / SC
    dm = max(d.max(), 1.0 / SC)
    hgt = np.sqrt(np.clip(1 - (1 - np.clip(d / dm, 0, 1)) ** 2, 0, 1)) * dm * (1 - flat)
    hgt = ndimage.gaussian_filter(hgt, soft * SC)
    gy, gx = np.gradient(hgt)
    gy *= SC; gx *= SC
    n = np.dstack([-gx, -gy, np.ones_like(gx) * 1.2])
    n /= np.linalg.norm(n, axis=2, keepdims=True)
    L = np.array(light, np.float32); L /= np.linalg.norm(L)
    lam = np.clip((n * L).sum(2), 0, 1)
    return np.clip(ambient + (1 - ambient) * lam, 0, 1), n


def ellipse_mask(w, h, cx=None, cy=None, rx=None, ry=None):
    cx = (w - 1) / 2 if cx is None else cx
    cy = (h - 1) / 2 if cy is None else cy
    rx = w / 2 if rx is None else rx
    ry = h / 2 if ry is None else ry
    y, x = grid(h, w)
    return ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1.0


def over(dst, src_rgb, src_a):
    """straight-alpha 'src over dst' in place; src_a in [0,1] (h,w)"""
    a = src_a[..., None]
    ad = dst[..., 3:4] / 255.0
    ao = a + ad * (1 - a)
    rgb = (src_rgb * a + dst[..., :3] * ad * (1 - a)) / np.maximum(ao, 1e-6)
    dst[..., :3] = np.where(ao > 0, rgb, dst[..., :3])
    dst[..., 3:4] = ao * 255
    return dst


def outline(spr, col='#1d0b14', inner=False, alpha_cut=0.5, width=None):
    """a dark outline (OUTW units) round the sprite, anti-aliased. The canvas grows by one unit on every side (so the
    sprite's mask lines up with inner(result)). inner: the sprite's own edge band is coloured instead"""
    c = hexc(col) if isinstance(col, str) else np.asarray(col, np.float32)
    ow = (width or OUTW) * SC
    a = spr[..., 3] / 255.0
    if inner:
        hard = a > alpha_cut
        d = ndimage.distance_transform_edt(hard)
        band = np.clip(ow + 0.5 - d, 0, 1) * hard
        spr[..., :3] = spr[..., :3] * (1 - band[..., None]) + c * band[..., None]
        return spr
    h, w = a.shape
    out = np.zeros((h + 2 * SC, w + 2 * SC, 4), np.float32)
    out[SC:-SC, SC:-SC] = spr
    A = out[..., 3] / 255.0
    hard = A > alpha_cut
    dout = ndimage.distance_transform_edt(~hard)
    ring = np.clip(ow + 0.5 - dout, 0, 1)
    # anti-alias the boundary between the fill and the ring
    As = np.minimum(A, ndimage.gaussian_filter(A, 0.6))
    rgb = out[..., :3].copy()
    base = np.zeros_like(out)
    base[..., :3] = c; base[..., 3] = ring * 255
    over(base, rgb, As)
    return base


def highlight(spr, mask, n, light=(-0.55, -0.7, 0.45), col='#ffffff', thresh=0.93, alpha=1.0):
    """glossy spot where the surface faces the light most directly (soft-edged)"""
    L = np.array(light, np.float32); L /= np.linalg.norm(L)
    Hh = L + np.array([0, 0, 1.0]); Hh /= np.linalg.norm(Hh)
    s = (n * Hh).sum(2)
    k = np.clip((s - thresh) / max((1 - thresh) * 0.35, 1e-3), 0, 1) * (mask > 0.5) * alpha
    c = hexc(col)
    spr[..., :3] = spr[..., :3] * (1 - k[..., None]) + c * k[..., None]
    return spr


def paste(dst, spr, x, y, opacity=1.0):
    """alpha-composite spr onto dst with its top-left at world (x, y) (may be off-canvas)"""
    x, y = int(round(x * SC)), int(round(y * SC))
    h, w = spr.shape[:2]
    H_, W_ = dst.shape[:2]
    x0, y0, x1, y1 = max(x, 0), max(y, 0), min(x + w, W_), min(y + h, H_)
    if x0 >= x1 or y0 >= y1:
        return dst
    s = spr[y0 - y:y1 - y, x0 - x:x1 - x]
    a = (s[..., 3] / 255.0) * opacity
    if not a.any():
        return dst
    over(dst[y0:y1, x0:x1], s[..., :3], a)
    return dst


def fill_rect(dst, x0, y0, x1, y1, col, a=255):
    c = hexc(col) if isinstance(col, str) else col
    X0, Y0, X1, Y1 = max(px(x0), 0), max(px(y0), 0), max(px(x1), 0), max(px(y1), 0)
    if X1 <= X0 or Y1 <= Y0:
        return
    k = np.full((min(Y1, dst.shape[0]) - Y0, min(X1, dst.shape[1]) - X0), a / 255.0, np.float32)
    if k.size == 0:
        return
    over(dst[Y0:Y0 + k.shape[0], X0:X0 + k.shape[1]], np.broadcast_to(c, k.shape + (3,)), k)


def disc(dst, cx, cy, r, col, a=255, soft=0.7):
    """an anti-aliased filled disc; cx, cy in old-style coordinates, r in units"""
    c = hexc(col) if isinstance(col, str) else np.asarray(col, np.float32)
    X, Y, R = (cx + 0.5) * SC, (cy + 0.5) * SC, r * SC
    x0, x1 = int(np.floor(X - R - 2)), int(np.ceil(X + R + 2))
    y0, y1 = int(np.floor(Y - R - 2)), int(np.ceil(Y + R + 2))
    H_, W_ = dst.shape[:2]
    if x1 <= 0 or y1 <= 0 or x0 >= W_ or y0 >= H_:
        return
    xa, ya = max(x0, 0), max(y0, 0); xb, yb = min(x1, W_), min(y1, H_)
    yy, xx = np.mgrid[ya:yb, xa:xb].astype(np.float32)
    d = np.sqrt((xx + 0.5 - X) ** 2 + (yy + 0.5 - Y) ** 2)
    k = np.clip((R - d) / soft + 0.5, 0, 1) * (a / 255.0)
    if k.any():
        over(dst[ya:yb, xa:xb], np.broadcast_to(c, k.shape + (3,)), k)


def ellipse_soft(dst, cx, cy, rx, ry, col, a=255, ang=0.0):
    """an anti-aliased filled (rotated) ellipse in old-style coordinates"""
    c = hexc(col) if isinstance(col, str) else np.asarray(col, np.float32)
    X, Y = (cx + 0.5) * SC, (cy + 0.5) * SC
    RX, RY = rx * SC, ry * SC
    rr = max(RX, RY) + 2
    x0, x1, y0, y1 = int(X - rr), int(X + rr) + 1, int(Y - rr), int(Y + rr) + 1
    H_, W_ = dst.shape[:2]
    xa, ya = max(x0, 0), max(y0, 0); xb, yb = min(x1, W_), min(y1, H_)
    if xa >= xb or ya >= yb:
        return
    yy, xx = np.mgrid[ya:yb, xa:xb].astype(np.float32)
    u, v = xx + 0.5 - X, yy + 0.5 - Y
    ca, sa = np.cos(ang), np.sin(ang)
    p, q = u * ca + v * sa, -u * sa + v * ca
    r = np.sqrt((p / max(RX, 1e-3)) ** 2 + (q / max(RY, 1e-3)) ** 2)
    k = np.clip((1 - r) * min(RX, RY) / 0.7 + 0.5, 0, 1) * (a / 255.0)
    if k.any():
        over(dst[ya:yb, xa:xb], np.broadcast_to(c, k.shape + (3,)), k)


def stroke(dst, pts, wdt, col, a=255, scale=None):
    """an anti-aliased polyline; pts in old-style coordinates, wdt in pixel-version pixels"""
    pts = [p for p in pts]
    if len(pts) < 2:
        return
    c = hexc(col) if isinstance(col, str) else np.asarray(col, np.float32)
    P = (np.array(pts, np.float64) + 0.5) * SC
    th = max(1.0, wdt * SC * (LW if scale is None else scale))
    pad = th + 3
    x0, y0 = int(np.floor(P[:, 0].min() - pad)), int(np.floor(P[:, 1].min() - pad))
    x1, y1 = int(np.ceil(P[:, 0].max() + pad)), int(np.ceil(P[:, 1].max() + pad))
    H_, W_ = dst.shape[:2]
    xa, ya, xb, yb = max(x0, 0), max(y0, 0), min(x1, W_), min(y1, H_)
    if xa >= xb or ya >= yb:
        return
    m = np.zeros((y1 - y0, x1 - x0), np.uint8)
    q = np.round((P - [x0, y0]) * 16).astype(np.int32)
    t = int(round(th))
    if t <= 1:
        # thin: draw at 2x supersampled thickness and fade
        cv2.polylines(m, [q.reshape(-1, 1, 2)], False, 255, 1, cv2.LINE_AA, 4)
        k = m.astype(np.float32) / 255.0 * min(1.0, th)
    else:
        cv2.polylines(m, [q.reshape(-1, 1, 2)], False, 255, t, cv2.LINE_AA, 4)
        k = m.astype(np.float32) / 255.0
    k = k[ya - y0:yb - y0, xa - x0:xb - x0] * (a / 255.0)
    if k.any():
        over(dst[ya:yb, xa:xb], np.broadcast_to(c, k.shape + (3,)), k)


def dot(dst, x, y, col, a=255, r=0.55):
    disc(dst, x, y, r, col, a)


def vgrad(dst, rmp, y0=0, y1=None, ox=0):
    """smooth vertical gradient through the ramp (first colour at the top); y in world units"""
    Y0 = px(y0); Y1 = dst.shape[0] if y1 is None else px(y1)
    v = np.linspace(0, 1, Y1 - Y0, dtype=np.float32)
    dst[Y0:Y1, :, :3] = ramp_col(rmp, v)[:, None, :]
    dst[Y0:Y1, :, 3] = 255


def to_image(arr, scale=1):
    im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), 'RGBA')
    if scale != 1:
        im = im.resize((im.width * scale, im.height * scale), Image.LANCZOS)
    return im


def load(path):
    return np.array(Image.open(path).convert('RGBA')).astype(np.float32)


def flip(spr):
    return spr[:, ::-1].copy()


def tint(spr, col, k):
    out = spr.copy(); c = hexc(col)
    out[..., :3] = out[..., :3] * (1 - k) + c * k
    return out


def shadow(w, h=3, a=110):
    m = smooth_mask(ellipse_mask(w, h))
    s = np.zeros(m.shape + (4,), np.float32)
    s[..., 3] = m * a
    return s


def text(dst, s, cx, cy, size, col, out_col=None, out_w=0.6, font='/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf'):
    """crisp text centred at old-style (cx, cy); size = cap height-ish in world units"""
    from PIL import ImageDraw, ImageFont
    f = ImageFont.truetype(font, max(6, int(round(size * SC * 1.35))))
    pad = int(size * SC * 2)
    im = Image.new('RGBA', (pad * 2 + int(len(s) * size * SC * 1.2), pad * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    sw = int(round(out_w * SC)) if out_col else 0
    d.text((im.width / 2, im.height / 2), s, font=f, fill=tuple(int(v) for v in hexc(col)) + (255,), anchor='mm',
           stroke_width=sw, stroke_fill=(tuple(int(v) for v in hexc(out_col)) + (255,)) if out_col else None)
    arr = np.array(im).astype(np.float32)
    paste(dst, arr, cx + 0.5 - im.width / 2 / SC, cy + 0.5 - im.height / 2 / SC)
    return dst
