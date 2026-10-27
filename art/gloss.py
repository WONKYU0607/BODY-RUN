# (v45) A small renderer for glossy cartoon objects, to match the user's pictures (the slot machine, the keeper):
# rounded shapes lit from the upper left with a smooth light-to-shadow ramp, a light rim reflected along the lower
# right, crisp white highlights, soft shadows where one part sits on another, thin dark lines between parts and a
# thick dark outline round the whole; drawn 4x over and shrunk (smooth edges).
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

SS = 4
L = np.array([-0.5, -0.72, 0.48]); L = L / np.linalg.norm(L)
LR = np.array([0.62, 0.72, 0.3]); LR = LR / np.linalg.norm(LR)          # the reflected light at the rim
HV = (L + np.array([0, 0, 1.0])); HV = HV / np.linalg.norm(HV)
OUTC = np.array([42, 14, 16], np.float32)


def hexc(h):
    h = h.lstrip('#'); return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32)


def ramp_col(stops, v):
    pal = np.array([hexc(s) if isinstance(s, str) else s for s in stops], np.float32)
    n = len(pal); t = np.clip(v, 0, 1) * (n - 1)
    i0 = np.clip(np.floor(t).astype(int), 0, n - 1); i1 = np.minimum(i0 + 1, n - 1); f = (t - i0)[..., None]
    return pal[i0] * (1 - f) + pal[i1] * f


def sstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)


class Pic:
    def __init__(self, w, h):
        self.w, self.h = w, h
        Y, X = np.mgrid[0:h * SS, 0:w * SS].astype(np.float32)
        self.Y, self.X = (Y + 0.5) / SS, (X + 0.5) / SS
        self.rgb = np.zeros((h * SS, w * SS, 3), np.float32)
        self.a = np.zeros((h * SS, w * SS), np.float32)
        self.parts = []                       # every part's mask (for the outline round the whole)

    # ---- shapes (boolean masks on the 4x grid; coordinates in final pixels)
    def ell(self, cx, cy, rx, ry, ang=0.0):
        c, s = np.cos(ang), np.sin(ang); dx, dy = self.X - cx, self.Y - cy
        u, v = dx * c + dy * s, -dx * s + dy * c
        return (u / rx) ** 2 + (v / ry) ** 2 <= 1

    def cap(self, p0, p1, r0, r1=None):
        r1 = r0 if r1 is None else r1
        p0, p1 = np.array(p0, np.float32), np.array(p1, np.float32); d = p1 - p0; L2 = max((d ** 2).sum(), 1e-6)
        t = np.clip(((self.X - p0[0]) * d[0] + (self.Y - p0[1]) * d[1]) / L2, 0, 1)
        qx, qy = p0[0] + t * d[0], p0[1] + t * d[1]
        return np.hypot(self.X - qx, self.Y - qy) <= r0 + (r1 - r0) * t

    def rrect(self, x0, y0, x1, y1, r):
        cx, cy = np.clip(self.X, x0 + r, x1 - r), np.clip(self.Y, y0 + r, y1 - r)
        return np.hypot(self.X - cx, self.Y - cy) <= r

    def poly(self, pts):
        im = Image.new('L', (self.w * SS, self.h * SS), 0)
        ImageDraw.Draw(im).polygon([(x * SS, y * SS) for x, y in pts], fill=255)
        return np.array(im) > 127

    def spline(self, pts, n=24, closed=True):
        """a smooth closed outline through the points (Catmull-Rom)"""
        P = np.array(pts, np.float32); m = len(P); out = []
        for i in range(m if closed else m - 1):
            p0, p1, p2, p3 = P[(i - 1) % m], P[i], P[(i + 1) % m], P[(i + 2) % m]
            for t in np.linspace(0, 1, n, endpoint=False):
                t2, t3 = t * t, t * t * t
                out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
        return self.poly(out)

    def stroke_mask(self, pts, r, n=20):
        P = np.array(pts, np.float32); m = np.zeros(self.X.shape, bool)
        pts2 = []
        for i in range(len(P) - 1):
            p0, p1, p2, p3 = P[max(i - 1, 0)], P[i], P[i + 1], P[min(i + 2, len(P) - 1)]
            for t in np.linspace(0, 1, n, endpoint=False):
                t2, t3 = t * t, t * t * t
                pts2.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
        pts2.append(P[-1])
        rr = r if np.ndim(r) else [r] * len(pts2)
        if np.ndim(r): rr = np.interp(np.linspace(0, 1, len(pts2)), np.linspace(0, 1, len(r)), r)
        for i in range(len(pts2) - 1): m |= self.cap(pts2[i], pts2[i + 1], rr[i], rr[i + 1])
        return m

    # ---- painting
    def over(self, rgb, a):
        a = np.clip(a, 0, 1)
        self.rgb = self.rgb * (1 - a[..., None]) + rgb * a[..., None] if np.ndim(rgb) == 3 else self.rgb * (1 - a[..., None]) + np.array(rgb, np.float32) * a[..., None]
        self.a = self.a + a * (1 - self.a)

    def normals(self, m, R, flat=0.0):
        d = ndimage.distance_transform_edt(m) / SS
        t = np.clip(d / R, 0, 1)
        h = R * np.sqrt(1 - (1 - t) ** 2)
        h = ndimage.gaussian_filter(h, 0.3 * R * SS)
        gy, gx = np.gradient(h, 1.0 / SS)
        gx *= (1 - flat); gy *= (1 - flat)
        n = np.stack([-gx, -gy, np.ones_like(gx)], -1); n /= np.linalg.norm(n, axis=-1, keepdims=True)
        return n

    def body(self, m, stops, R, gloss=1.0, rim=0.55, rimcol='#ffffff', spec=0.9, line=1.4, shadow=0.45, flat=0.0,
             top=0.0, n=None, power=36, lam_lo=-0.15):
        """a part: its shadow on what is below, a thin dark line where it meets it, then itself lit"""
        prior = self.a > 0.5
        if shadow and prior.any():                          # soft shadow cast down-right onto what is already there
            sh = ndimage.gaussian_filter(ndimage.shift(m.astype(np.float32), (R * 0.18 * SS, R * 0.12 * SS), order=0), R * 0.25 * SS)
            k = shadow * sh * (~m) * prior
            self.rgb *= (1 - k[..., None] * 0.75)
        if line and prior.any():                            # the line round it where it overlaps
            ring = ndimage.binary_dilation(m, iterations=max(1, int(line * SS))) & ~m & prior
            self.over(OUTC, ring.astype(np.float32) * 0.92)
        if n is None: n = self.normals(m, R, flat)
        lam = (n * L).sum(-1)
        v = sstep(lam_lo, 1.0, lam)
        if top: v = np.clip(v + top * (0.5 - (self.Y - self.Y[m].mean()) / max(1, np.ptp(self.Y[m]))), 0, 1)
        col = ramp_col(stops, v)
        rv = (1 - n[..., 2]) ** 1.6 * np.clip((n * LR).sum(-1), 0, 1)
        col = col + rim * rv[..., None] * (hexc(rimcol) - col)
        sp = np.clip((n * HV).sum(-1), 0, 1) ** power
        crisp = sstep(0.42, 0.55, sp) * spec
        col = col + crisp[..., None] * (255 - col) * gloss
        self.over(col, m.astype(np.float32))
        self.parts.append(m)
        return n

    def flat(self, m, col, a=1.0):
        self.over(hexc(col) if isinstance(col, str) else col, m.astype(np.float32) * a)

    def gloss_blob(self, m, a=0.85, soft=0.6, col='#ffffff'):
        """a hand-placed highlight: crisp-edged, a little soft"""
        f = ndimage.gaussian_filter(m.astype(np.float32), soft * SS)
        self.over(hexc(col), np.clip(f * 1.2 - 0.1, 0, 1) * a)

    def sparkle(self, cx, cy, r, a=1.0, col='#ffffff', glow='#ffd040', edge='#e08a00'):
        """a four-pointed glint: a gold glow, a gold edge, a white core (it reads on white and on dark)"""
        g = np.exp(-((self.X - cx) ** 2 + (self.Y - cy) ** 2) / (2 * (r * 0.4) ** 2))
        self.over(hexc(glow), g * 0.5 * a)
        dx, dy = np.abs(self.X - cx), np.abs(self.Y - cy)
        star = lambda k: (dx / (r * k) + dy / (r * 0.2 * k) <= 1) | (dy / (r * k) + dx / (r * 0.2 * k) <= 1) | (dx + dy <= r * 0.32 * k)
        self.over(hexc(edge), ndimage.gaussian_filter(star(1.18).astype(np.float32), 0.35 * SS) * a)
        self.over(hexc(col), ndimage.gaussian_filter(star(1.0).astype(np.float32), 0.35 * SS) * a)

    def outline(self, w=4.0, col=OUTC, extra=None):
        """the thick dark outline round everything (drawn under it)"""
        u = self.a > 0.5
        if extra is not None: u |= extra
        r = int(w * SS)
        yy, xx = np.mgrid[-r:r + 1, -r:r + 1]
        ring = ndimage.binary_dilation(u, structure=(xx ** 2 + yy ** 2 <= r * r))
        ring = ndimage.gaussian_filter(ring.astype(np.float32), 0.5 * SS)
        rgb = np.where(self.a[..., None] > 0, self.rgb, 0)
        A = self.a + ring * (1 - self.a)
        self.rgb = (self.rgb * self.a[..., None] + np.array(col, np.float32) * (ring * (1 - self.a))[..., None]) / np.maximum(A, 1e-4)[..., None]
        self.a = A

    def image(self):
        """shrunk to the final size: RGBA float 0..255"""
        h, w = self.h, self.w
        pm = self.rgb * self.a[..., None]
        pm = pm.reshape(h, SS, w, SS, 3).mean((1, 3)); a = self.a.reshape(h, SS, w, SS).mean((1, 3))
        out = np.zeros((h, w, 4), np.float32)
        out[..., :3] = pm / np.maximum(a, 1e-4)[..., None]; out[..., 3] = a * 255
        out[a < 1e-3] = 0
        return out
