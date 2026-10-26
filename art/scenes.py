# Five preview screens of the side-scrolling body run, at the native 390x180 (one art pixel = 6 device pixels on a
# Galaxy S25 held sideways), shown x4. Back to front: background gradient, far shapes, mid shapes, ceiling and ground
# bands, items, obstacles, character, HUD (pixel parts at native size, Korean text drawn at the final size).
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage
from art import (W, H, canvas, ramp, hexc, vgrad, paint, dome_shade, ellipse_mask, outline, highlight, paste, fill_rect,
                 to_image, load, flip, shadow, quantize, text3)
import sprites as S

SC = 4
GY = 150          # top of the ground
BTN_X, BTN_Y = 24, H - 22   # the jump / slide buttons (centres)
FONT = '/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc'
CH = '/home/claude/pixel/out/char_{}.png'


# ------------------------------------------------------------------ helpers
def cells(w, h, n, seed, border=0.9):
    """an organic cell pattern: 0 inside a cell .. 1 on its border (distance to the nearest two seeds)"""
    R = np.random.RandomState(seed)
    pts = np.c_[R.uniform(0, w, n), R.uniform(0, h, n)]
    y, x = np.mgrid[0:h, 0:w]
    d = np.sqrt((x[..., None] - pts[:, 0]) ** 2 + ((y[..., None] - pts[:, 1]) * 1.25) ** 2)
    d.sort(axis=2)
    return np.clip(1 - (d[..., 1] - d[..., 0]) / border, 0, 1), d[..., 0]


def band(dst, y0, y1, rmp, top_edge=True, seed=1, bumps=1.2, cell_n=34, lip='#ffffff', lip_k=0.0, out='#1a050c', drips=False):
    """a thick band of tissue across the screen (the ground when top_edge, the ceiling otherwise): a light lip along
    the open edge, rounded cells inside, darker away from the edge, a dark outline on the edge"""
    R = np.random.RandomState(seed)
    h = y1 - y0
    xs = np.arange(W)
    edge = np.round(bumps * np.sin(xs * 0.11 + R.uniform(0, 6)) + 0.8 * bumps * np.sin(xs * 0.29 + R.uniform(0, 6))).astype(int)
    y, x = np.mgrid[0:h, 0:W]
    depth = (y - edge[None, :]) if top_edge else ((h - 1 - y) - edge[None, :])   # 0 at the open edge
    mask = depth >= 0
    cb, cd = cells(W, h, cell_n, seed + 7, border=1.0)
    # soft round cells (each one a little pillow lit from the top left), a thin darker seam between them
    gy_, gx_ = np.gradient(-cd)
    lit = np.clip(0.5 + 0.35 * (-0.6 * gx_ - 0.8 * gy_), 0, 1)
    shade = np.clip(1.0 - depth / (h * 1.05), 0, 1) * 0.7 + 0.18
    shade = shade + 0.22 * (lit - 0.5) - 0.13 * (cb > 0.86)
    shade[(depth >= 0) & (depth < 3)] = np.maximum(shade[(depth >= 0) & (depth < 3)], 0.92)       # the lip
    spr = paint(mask, rmp, np.clip(shade, 0, 1))
    hl = (depth == 1) & ((x + (0 if top_edge else 3)) % 9 < 6)
    spr[hl, :3] = spr[hl, :3] * 0.4 + hexc('#ffffff') * 0.6                                           # wet shine
    o = (depth == 0)
    spr[o, :3] = hexc(out)
    if drips and not top_edge:
        for k in range(14):
            dx = int(R.uniform(4, W - 4)); L = int(R.uniform(3, 8))
            yy = h - edge[dx]
            m = ellipse_mask(5, L + 3, 2, L, 2.2, 2.6)
            m[:L, 1:4] = True
            dsp, _ = S.blob(m, rmp[-4:], out, soft=0.6, ambient=0.5)
            paste(spr, dsp, dx - 3, yy - 2)
    paste(dst, spr, 0, y0)
    return edge


def sine_ridges(dst, y_base, amp, freq, thick, rmp, out, phase=0.0, alpha=1.0):
    """a sinuous fold running across (the stomach's rugae): lit on its upper side"""
    xs = np.arange(W)
    yc = y_base + amp * np.sin(xs * freq + phase) + amp * 0.4 * np.sin(xs * freq * 2.3 + phase * 1.7)
    hgt = int(thick + 2 * amp + 4)
    top = int(y_base - amp * 1.4 - thick / 2 - 2)
    y, x = np.mgrid[0:hgt, 0:W]
    yy = y + top
    t = (yy - (yc[None, :] - thick / 2)) / thick       # 0 top .. 1 bottom of the fold
    m = (t >= 0) & (t <= 1)
    m &= np.abs(t - 0.5) * 2 <= 1 - 0.15 * np.sin(xs[None, :] * 0.05 + phase) ** 2
    shade = np.clip(1.0 - t * 0.95, 0, 1) ** 0.8
    spr = paint(m, rmp, shade)
    spr = outline(spr, out)
    paste(dst, spr, -1, top - 1, alpha)


def rbc(d, tilt=1.0, dark=False):
    """a red blood cell: a disc with a dimple, seen at some tilt"""
    w, h = d, max(3, int(round(d * tilt)))
    m = ellipse_mask(w, h)
    sh, n = dome_shade(m, (-0.55, -0.7, 0.45), soft=1.0, ambient=0.3)
    # the dimple: the middle darker, a light ring round it
    y, x = np.mgrid[0:h, 0:w]
    r = np.sqrt(((x - (w - 1) / 2) / (w / 2)) ** 2 + ((y - (h - 1) / 2) / (h / 2)) ** 2)
    sh = np.clip(sh - 0.45 * np.clip(1 - r / 0.55, 0, 1) + 0.12 * np.clip(1 - np.abs(r - 0.68) / 0.12, 0, 1), 0, 1)
    rm = ramp('#5a0610', '#9a0e1e', '#d42232', '#ff5260', '#ff9aa0', n=6) if not dark else ramp('#3a0610', '#5a0c18', '#7a1422', '#962030', n=4)
    spr = paint(m, rm, sh)
    if not dark:
        spr = highlight(spr, m, n, (-0.55, -0.7, 0.45), '#ffd0d4', 0.97)
    return outline(spr, '#2a0208' if not dark else '#24040a')


def neuron(dst, cx, cy, size, rng, cols, glow=False, depth=0):
    """a nerve cell: a round body and branching dendrites (drawn as pixel lines)"""
    def branch(x, y, a, L, wdt, lvl):
        steps = int(L)
        for i in range(steps):
            x += np.cos(a); y += np.sin(a); a += rng.uniform(-0.18, 0.18)
            ww = max(1, int(round(wdt * (1 - i / max(steps, 1) * 0.6))))
            fill_rect(dst, int(x) - ww // 2, int(y) - ww // 2, int(x) - ww // 2 + ww, int(y) - ww // 2 + ww, cols[1])
            if ww > 1:
                fill_rect(dst, int(x) - ww // 2, int(y) - ww // 2, int(x) - ww // 2 + 1, int(y) - ww // 2 + 1, cols[2])
            if lvl < 3 and rng.uniform() < 0.07:
                branch(x, y, a + rng.choice([-1, 1]) * rng.uniform(0.4, 0.9), L * 0.55, wdt * 0.7, lvl + 1)
        if glow and lvl >= 2 and rng.uniform() < 0.5:
            fill_rect(dst, int(x) - 1, int(y) - 1, int(x) + 2, int(y) + 2, cols[4]); fill_rect(dst, int(x), int(y), int(x) + 1, int(y) + 1, '#ffffff')
    for k in range(rng.randint(4, 7)):
        a = rng.uniform(0, 2 * np.pi)
        branch(cx + np.cos(a) * size * 0.4, cy + np.sin(a) * size * 0.4, a, size * rng.uniform(1.6, 3.2), max(1, size * 0.3), 1)
    m = ellipse_mask(size, size)
    sp, _ = S.blob(m, ramp(cols[0], cols[1], cols[2], cols[3]), cols[5], soft=0.8, ambient=0.35)
    paste(dst, sp, cx - size / 2 - 1, cy - size / 2 - 1)


def villus(h, w, rmp, out, seed, hang=False):
    """a finger of the intestine lining, rounded at the tip, with a red capillary inside (hang: from the ceiling,
    still lit from the top left)"""
    m = np.zeros((h, w), bool)
    y, x = np.mgrid[0:h, 0:w]
    r = (w - 1) / 2
    m |= (y >= r) & (np.abs(x - r) <= r * (0.85 + 0.15 * y / h))
    m |= (x - r) ** 2 + (y - r) ** 2 <= r * r
    if hang:
        m = m[::-1]
    spr, _ = S.blob(m, rmp, out, soft=1.0, ambient=0.3)
    if hang:
        return spr
    R = np.random.RandomState(seed)
    xx = r
    for yy in range(int(r), h - 1):
        xx += R.uniform(-0.6, 0.6); xx = np.clip(xx, r - r * 0.5, r + r * 0.5)
        if 0 <= int(xx) + 1 < spr.shape[1]:
            spr[yy + 1, int(xx) + 1, :3] = spr[yy + 1, int(xx) + 1, :3] * 0.5 + hexc('#c8102a') * 0.5
    return spr


def place(dst, spr, x, y_bottom):
    paste(dst, spr, x - spr.shape[1] / 2, y_bottom - spr.shape[0])


def char(name, x, y_bottom, dst, jump=0, squash=1.0):
    c = load(CH.format(name))
    if squash != 1.0:
        hh = max(4, int(round(c.shape[0] * squash))); ww = int(round(c.shape[1] * (2 - squash) ** 0.6))
        c = np.array(Image.fromarray(c.astype(np.uint8)).resize((ww, hh), Image.NEAREST)).astype(np.float32)
    sh = shadow(int(c.shape[1] * (0.8 if not jump else 0.55)), 3, 120 if not jump else 70)
    paste(dst, sh, x - sh.shape[1] / 2, GY - 2)
    paste(dst, c, x - c.shape[1] / 2, y_bottom - c.shape[0] - jump)
    return c


def puff(dst, x, y, col='#ffffff', n=3, seed=0):
    R = np.random.RandomState(seed)
    for k in range(n):
        r = R.uniform(1.5, 3.2)
        m = ellipse_mask(int(2 * r) + 1, int(2 * r) + 1)
        s = np.zeros(m.shape + (4,), np.float32); s[m, :3] = hexc(col); s[m, 3] = 150 - k * 35
        paste(dst, s, x - k * 6 - r, y - r - R.uniform(0, 3))


def speedlines(dst, col, n=10, seed=0, alpha=60):
    R = np.random.RandomState(seed)
    for k in range(n):
        y = int(R.uniform(20, GY - 8)); x = int(R.uniform(0, W)); L = int(R.uniform(10, 28))
        s = np.zeros((1, L, 4), np.float32); s[..., :3] = hexc(col); s[..., 3] = alpha
        paste(dst, s, x, y)


def row(dst, spr, x0, y_center, n, gap):
    for i in range(n):
        paste(dst, spr, x0 + i * gap - spr.shape[1] / 2, y_center - spr.shape[0] / 2)


def arc(dst, spr, x0, x1, y_base, height, n):
    for i in range(n):
        t = i / (n - 1)
        x = x0 + (x1 - x0) * t
        y = y_base - height * 4 * t * (1 - t)
        paste(dst, spr, x - spr.shape[1] / 2, y - spr.shape[0] / 2)


# ------------------------------------------------------------------ HUD
F57 = {
    '0': ['01110', '10001', '10011', '10101', '11001', '10001', '01110'], '1': ['00100', '01100', '00100', '00100', '00100', '00100', '01110'],
    '2': ['01110', '10001', '00001', '00110', '01000', '10000', '11111'], '3': ['11110', '00001', '00001', '01110', '00001', '00001', '11110'],
    '4': ['00010', '00110', '01010', '10010', '11111', '00010', '00010'], '5': ['11111', '10000', '11110', '00001', '00001', '10001', '01110'],
    '6': ['00110', '01000', '10000', '11110', '10001', '10001', '01110'], '7': ['11111', '00001', '00010', '00100', '01000', '01000', '01000'],
    '8': ['01110', '10001', '10001', '01110', '10001', '10001', '01110'], '9': ['01110', '10001', '10001', '01111', '00001', '00010', '01100'],
    ',': ['00000', '00000', '00000', '00000', '00000', '01100', '00100'], '+': ['00000', '00100', '00100', '11111', '00100', '00100', '00000'],
    'm': ['00000', '00000', '11010', '10101', '10101', '10101', '10101'],
}


def text57(dst, s, x, y, col, out='#1a0a14'):
    """chunky digits with a dark outline (the score)"""
    lay = canvas(len(s) * 6 + 2, 9)
    xx = 1
    for ch in s:
        g = F57.get(ch)
        if g is None:
            xx += 3; continue
        for j, r_ in enumerate(g):
            for i, b in enumerate(r_):
                if b == '1':
                    fill_rect(lay, xx + i, 1 + j, xx + i + 1, 2 + j, col)
        xx += 6 if ch != ',' else 4
    lay = lay[:, :xx + 1]
    lay = outline(lay, out)
    # a darker lower half on the glyphs: a little depth
    body = lay[..., 3] > 0
    paste(dst, lay, x, y)
    return x + lay.shape[1]


def heart_icon():
    rows = ['0110110', '1111111', '1111111', '1111111', '0111110', '0011100', '0001000']
    m = np.array([[c == '1' for c in r] for r in rows])
    m = np.pad(m, 0)
    spr, _ = S.blob(m, ramp('#7a0a1e', '#d01e3c', '#ff4a68', '#ff9aa8'), '#2a0410', soft=0.6, ambient=0.4)
    return spr


def hud(dst, hp=0.72, score='12,480', progress=0.1, theme='#ff5a7a', pop=None):
    # health: a heart and a long bar
    x0, y0, w, h = 14, 7, 116, 8
    fill_rect(dst, x0 - 1, y0 - 1, x0 + w + 1, y0 + h + 1, '#1a0a14')
    fill_rect(dst, x0, y0, x0 + w, y0 + h, '#3a2030')
    fw = int(w * hp)
    fill = canvas(fw, h)
    vgrad(fill, ramp('#ffb0c0', '#ff5a7a', '#e0284c', '#a8123a'))
    paste(dst, fill, x0, y0)
    fill_rect(dst, x0, y0 + 1, x0 + fw, y0 + 2, '#ffd6de')
    for k in range(1, 8):                                   # notches
        fill_rect(dst, x0 + k * w // 8, y0 + h - 2, x0 + k * w // 8 + 1, y0 + h, '#1a0a14')
    paste(dst, heart_icon(), x0 - 8, y0 - 3)
    # score: a vitamin coin and the number, top right (left of the pause button)
    coin = S.coin_c()
    tx = W - 24 - 6 * len(score) - 6
    paste(dst, coin, tx - 16, 5)
    text57(dst, score, tx, 6, '#fff3c8')
    # pause
    fill_rect(dst, W - 19, 5, W - 6, 18, '#1a0a14'); fill_rect(dst, W - 18, 6, W - 7, 17, '#f4e8ee')
    fill_rect(dst, W - 15, 9, W - 13, 15, '#1a0a14'); fill_rect(dst, W - 12, 9, W - 10, 15, '#1a0a14')
    # course progress under the place name
    px0, px1, py = 155, 235, 30
    fill_rect(dst, px0 - 1, py - 1, px1 + 1, py + 3, '#1a0a14'); fill_rect(dst, px0, py, px1, py + 2, '#4a3848')
    fill_rect(dst, px0, py, px0 + int((px1 - px0) * progress), py + 2, theme)
    mk = int(px0 + (px1 - px0) * progress)
    fill_rect(dst, mk - 2, py - 2, mk + 3, py + 4, '#1a0a14'); fill_rect(dst, mk - 1, py - 1, mk + 2, py + 3, '#ffffff')
    # the two buttons: jump (left), slide (right)
    for (cx, kind) in ((BTN_X, 'jump'), (W - BTN_X, 'slide')):
        cy = BTN_Y
        m = ellipse_mask(33, 33)
        b = np.zeros((33, 33, 4), np.float32); b[m, :3] = hexc('#ffffff'); b[m, 3] = 60
        ring = m & ~ndimage.binary_erosion(m, iterations=2)
        b[ring, :3] = hexc('#ffffff'); b[ring, 3] = 210
        b = outline(b, '#1a0a14')
        paste(dst, b, cx - 17.5, cy - 17.5)
        # arrow
        ar = ['0001000', '0011100', '0111110', '1111111', '0011100', '0011100', '0011100'] if kind == 'jump' else ['0011100', '0011100', '0011100', '1111111', '0111110', '0011100', '0001000']
        am = np.array([[c == '1' for c in r_] for r_ in ar])
        a = np.zeros((7, 7, 4), np.float32); a[am, :3] = hexc('#ffffff'); a[am, 3] = 255
        a = outline(a, '#1a0a14')
        paste(dst, a, cx - 4.5, cy - 8)
    if pop:
        x, y, s = pop
        text3(dst, s, x, y, '#fff3c8', '#5a2a00')


def labels(img, name, en, buttons=True):
    """Korean text drawn at the final size (sharp, with a dark rim): the place name and the button names"""
    d = ImageDraw.Draw(img)
    f1 = ImageFont.truetype(FONT, 46); f2 = ImageFont.truetype(FONT, 20); f3 = ImageFont.truetype(FONT, 22)
    cx = W * SC // 2
    d.text((cx, 18), name, font=f1, fill=(255, 255, 255), stroke_width=5, stroke_fill=(26, 10, 20), anchor='mt')
    d.text((cx, 74), en, font=f2, fill=(255, 214, 150), stroke_width=4, stroke_fill=(26, 10, 20), anchor='mt')
    if buttons:
        for (x, s) in ((BTN_X, '점프'), (W - BTN_X, '슬라이드')):
            d.text((x * SC, BTN_Y * SC + 14), s, font=f3, fill=(255, 255, 255), stroke_width=4, stroke_fill=(26, 10, 20), anchor='mt')
    return img


def finish(cv, name, en, path):
    img = to_image(cv, SC).convert('RGB')
    img = labels(img, name, en)
    img.save(path)
    return img


def haze(dst, col, k):
    """push what is drawn so far back (toward the air colour): the background stays behind the play"""
    c = hexc(col)
    dst[..., :3] = dst[..., :3] * (1 - k) + c * k
