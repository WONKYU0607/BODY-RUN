# (v45) the toilet jackpot's six reel symbols, the coin and the shoot-out's ball, redrawn with gloss.py to match the
# user's glossy cartoon pictures: 0 golden poop (the jackpot), 1 rubber duck, 2 plunger, 3 toilet roll, 4 soap,
# 5 water drop. Each on a 240 px square (the game draws them ~28 units across).
import sys, os
import numpy as np
from scipy import ndimage
sys.path.insert(0, '/home/claude/hdart')
from gloss import Pic, hexc, SS

N = 240
GOLD = ('#6e3200', '#b06a00', '#e9a414', '#ffd04a', '#fff2b0')
YEL = ('#a85c00', '#e39a00', '#ffcf14', '#ffe866', '#fff9d0')
ORA = ('#8a2a00', '#d85a06', '#ff8a1c', '#ffb85a', '#ffe2b8')
RED = ('#5a000c', '#a4101c', '#e2243a', '#ff6878', '#ffd0d6')
WOOD = ('#4a2208', '#82441a', '#bb7434', '#e6a660', '#ffe8c4')
WHITE = ('#7e7a98', '#b8b4cc', '#e2e0ee', '#f8f8fc', '#ffffff')
CARD = ('#4a2a14', '#7a4a26', '#a8703e', '#cc9866', '#f0c898')
PINK = ('#8a1e50', '#cc3e7c', '#f670a8', '#ffaed0', '#fff0f6')
BLUE = ('#062c78', '#1258c4', '#2c98f0', '#86d4ff', '#e6f8ff')


def poop():
    p = Pic(N, N)
    tip = p.stroke_mask([(122, 84), (124, 58), (118, 38), (106, 24), (92, 20), (84, 28)], [30, 22, 15, 10, 6, 3.5])
    tiers = [((120, 188), 98, 40), ((119, 142), 76, 36), ((122, 102), 54, 30)]
    for k, ((cx, cy), rx, ry) in enumerate(tiers):
        m = p.ell(cx, cy, rx, ry)
        p.body(m, GOLD, R=ry * 0.95, rim=0.6, rimcol='#fff0a0', line=1.6, shadow=0.5)
        hl = p.ell(cx - rx * 0.4, cy - ry * 0.42, rx * 0.36, ry * 0.22, -0.22) & m
        p.gloss_blob(hl, a=0.88)
        p.gloss_blob(p.ell(cx + rx * 0.55, cy - ry * 0.1, rx * 0.06, ry * 0.08) & m, a=0.7)
    p.body(tip, GOLD, R=14, rim=0.6, rimcol='#fff0a0', line=1.6, shadow=0.5)     # the swirl's tip on top, curling left
    p.gloss_blob(p.ell(114, 50, 5, 11, 0.3) & tip, a=0.85)
    p.outline(4.2)
    for cx, cy, r in [(36, 70, 18), (200, 44, 14), (214, 150, 10), (26, 166, 9)]:
        p.sparkle(cx, cy, r)
    return p.image()


def duck():
    p = Pic(N, N)
    body = p.spline([(40, 150), (70, 122), (120, 126), (168, 118), (196, 82), (214, 92), (212, 140), (196, 190), (150, 214), (86, 214), (46, 196)])
    p.body(body, YEL, R=42, rim=0.55, rimcol='#fff6b0', line=0, shadow=0)
    wing = p.spline([(118, 156), (150, 140), (186, 150), (186, 176), (158, 192), (126, 184)])
    p.body(wing, YEL, R=16, rim=0.4, line=1.4, shadow=0.35)
    for k in range(3):
        f = p.stroke_mask([(150 + k * 9, 164 + k * 4), (172 + k * 3, 172 + k * 2)], 1.3)
        p.flat(f & wing, '#c88000', 0.7)
    head = p.ell(84, 84, 50, 48)
    p.body(head, YEL, R=40, rim=0.55, rimcol='#fff6b0', line=1.6, shadow=0.55)
    p.flat(p.ell(104, 100, 12, 7) & head, '#ff9a7a', 0.55)                 # a blush
    beak = p.spline([(44, 92), (24, 96), (8, 104), (14, 114), (36, 116), (52, 108)])
    p.body(beak, ORA, R=9, rim=0.4, line=1.4, shadow=0.4)
    p.flat(p.stroke_mask([(12, 108), (32, 110), (48, 106)], 1.1), '#8a2a00', 0.8)
    eye = p.ell(82, 74, 9.5, 12.5)
    p.flat(eye, '#1a0a10')
    p.flat(p.ell(79, 69, 3.8, 4.6), '#ffffff'); p.flat(p.ell(85.5, 80, 1.8, 2.2), '#ffffff')
    p.gloss_blob(p.ell(64, 52, 18, 9, -0.6) & head, a=0.75)
    p.gloss_blob(p.ell(88, 150, 22, 8, -0.35) & body, a=0.6)
    p.outline(4.2)
    return p.image()


def plunger():
    p = Pic(N, N)
    handle = p.cap((120, 30), (120, 128), 11)
    p.body(handle, WOOD, R=10, rim=0.35, line=0, shadow=0, power=60)
    for k in range(5):                                         # the grain
        y0 = 44 + k * 20
        p.flat(p.stroke_mask([(116, y0), (114, y0 + 9)], 0.9) & handle, '#7a3e14', 0.45)
    knob = p.ell(120, 28, 17, 13)
    p.body(knob, ('#2a0a04', '#4a1a0a', '#7a3418', '#b06a40', '#f0c8a8'), R=11, rim=0.4, line=1.4, shadow=0.4)
    p.gloss_blob(p.ell(113, 23, 6, 3, -0.2) & knob, a=0.8)
    cup = p.spline([(106, 112), (134, 112), (166, 128), (188, 160), (196, 198), (44, 198), (52, 160), (74, 128)])
    p.body(cup, RED, R=34, rim=0.5, rimcol='#ffc0c8', line=1.6, shadow=0.55)
    rim_ = p.ell(120, 202, 80, 15)
    p.body(rim_, ('#4a0008', '#80101a', '#b81c2c', '#ec4a5a', '#ffb0b8'), R=9, rim=0.4, line=1.6, shadow=0.3)
    p.gloss_blob(p.spline([(70, 160), (86, 134), (104, 126), (96, 142), (80, 170), (66, 186)]) & cup, a=0.8)
    p.gloss_blob(p.ell(154, 150, 5, 3.5) & cup, a=0.7)
    p.gloss_blob(p.ell(116, 60, 3, 22) & handle, a=0.55)
    p.outline(4.2)
    return p.image()


def roll():
    p = Pic(N, N)
    body = p.rrect(46, 66, 194, 186, 18) | p.ell(120, 186, 74, 22)
    p.body(body, WHITE, R=40, rim=0.5, rimcol='#ffffff', line=1.6, shadow=0.4, flat=0.25)
    for yy in range(84, 186, 16):                              # the quilting: soft rows of dimples
        for xx in range(56 + (yy // 16 % 2) * 8, 188, 16):
            d = p.ell(xx, yy, 2.6, 2.0) & body
            p.flat(d, '#c4c0d8', 0.5)
    top = p.ell(120, 66, 74, 24)
    p.body(top, WHITE, R=14, rim=0.2, line=1.6, shadow=0.2, flat=0.6, power=12)
    tube = p.ell(120, 66, 28, 10)
    p.body(tube, CARD, R=6, rim=0.2, line=1.4, shadow=0.2)
    p.flat(p.ell(120, 67, 21, 7), '#2a1006')
    p.flat(p.ell(120, 69, 16, 4.5), '#120604')
    p.gloss_blob(p.rrect(58, 84, 72, 170, 7) & body, a=0.75)
    p.gloss_blob(p.ell(84, 58, 22, 5, -0.12) & top, a=0.6)
    # the loose sheet: off the roll's front, hanging down past its bottom, torn across the end
    tear = [(190 - k * 7, 226 if k % 2 == 0 else 218) for k in range(7)]
    sheet = p.poly([(142, 112), (178, 108), (190, 120), (190, 226)] + tear[1:] + [(146, 222)])
    p.body(sheet, WHITE, R=10, rim=0.35, line=1.5, shadow=0.55, flat=0.45, power=20)
    for yy in (150, 196):                                      # its perforations
        for x in range(150, 188, 6): p.flat(p.ell(x, yy, 1.3, 1.3) & sheet, '#8a86a4', 0.9)
    p.gloss_blob(p.rrect(150, 122, 158, 210, 4) & sheet, a=0.55)
    p.outline(4.2)
    return p.image()


def soap():
    p = Pic(N, N)
    bar = p.rrect(30, 122, 210, 204, 36)
    p.body(bar, PINK, R=30, rim=0.55, rimcol='#ffe0ee', line=0, shadow=0, flat=0.15)
    top = p.rrect(46, 124, 194, 164, 22)                         # its top face, a little lighter
    p.flat(top & bar, '#ff9cc6', 0.35)
    tt = np.linspace(0, 2 * np.pi, 80)
    heart = p.poly([(120 + 1.25 * 16 * np.sin(t) ** 3, 142 - 1.25 * (13 * np.cos(t) - 5 * np.cos(2 * t) - 2 * np.cos(3 * t) - np.cos(4 * t))) for t in tt])
    p.body(heart, ('#b03a72', '#e05a94', '#ff8cbc', '#ffc0dc', '#ffffff'), R=5, rim=0.3, line=1.0, shadow=0.35)
    p.gloss_blob(p.rrect(48, 130, 96, 140, 5) & bar, a=0.7)
    p.gloss_blob(p.ell(184, 182, 6, 4) & bar, a=0.6)
    p.outline(4.2)
    for cx, cy, r in [(64, 84, 30), (128, 50, 22), (180, 86, 17), (206, 40, 11), (36, 34, 9)]:     # the bubbles
        b = p.ell(cx, cy, r, r)
        n = p.normals(b, r * 0.9)
        rel = np.clip(1 - np.hypot(p.X - cx, p.Y - cy) / r, 0, 1)
        film = (1 - rel) ** 2.2
        hue = np.stack([180 + 70 * np.sin((p.X + p.Y) * 0.05 + 0.5), 200 + 50 * np.sin((p.X - p.Y) * 0.04 + 2), 255 - 10 * np.cos(p.Y * 0.05)], -1)
        p.over(hue, b * (0.18 + 0.55 * film))
        ring = b & ~p.ell(cx, cy, r - 1.6, r - 1.6)
        p.flat(ring, '#4a78b0', 0.85)
        p.gloss_blob(p.ell(cx - r * 0.38, cy - r * 0.4, r * 0.3, r * 0.18, -0.6) & b, a=0.95)
        p.gloss_blob(p.ell(cx + r * 0.45, cy + r * 0.42, r * 0.1, r * 0.1) & b, a=0.8)
    return p.image()


def drop():
    p = Pic(N, N)
    d = p.ell(120, 146, 76, 74) | p.poly([(120, 14), (54, 112), (186, 112)]) & (p.Y < 120)
    d = d | p.spline([(120, 14), (148, 62), (190, 118), (120, 120), (50, 118), (92, 62)])
    d = ndimage.binary_closing(d, iterations=4 * SS)
    p.body(d, BLUE, R=52, rim=0.7, rimcol='#c8f4ff', line=0, shadow=0, power=30)
    p.gloss_blob(p.spline([(74, 120), (84, 92), (104, 64), (110, 70), (96, 104), (86, 140), (76, 152)]) & d, a=0.9)
    p.gloss_blob(p.ell(150, 186, 10, 7, -0.5) & d, a=0.75)
    p.gloss_blob(p.ell(160, 170, 3.5, 3.5) & d, a=0.8)
    p.outline(4.2, col=np.array([10, 30, 80], np.float32))
    return p.image()


def coin():
    p = Pic(120, 120)
    c = p.ell(60, 60, 52, 52)
    p.body(c, GOLD, R=20, rim=0.6, rimcol='#fff0a0', line=0, shadow=0)
    inner = p.ell(60, 60, 38, 38)
    p.body(inner, ('#7a3a00', '#b87400', '#e8a818', '#ffcc48', '#fff0b0'), R=10, rim=0.3, line=1.2, shadow=0.3, flat=0.4)
    star = p.poly([(60 + r * np.sin(a), 60 - r * np.cos(a)) for k in range(10) for a, r in [(k * np.pi / 5, 24 if k % 2 == 0 else 10)]])
    p.body(star, GOLD, R=5, rim=0.5, line=1.0, shadow=0.4)
    p.gloss_blob(p.ell(40, 36, 14, 6, -0.7) & c, a=0.8)
    p.outline(3.0)
    return p.image()


def ball():
    """a football: a lit sphere; the panels from the truncated icosahedron (12 black pentagons, 20 white hexagons)
    with seams between them"""
    p = Pic(160, 160)
    cx = cy = 80; R = 72
    m = p.ell(cx, cy, R, R)
    nx, ny = (p.X - cx) / R, (p.Y - cy) / R
    nz = np.sqrt(np.clip(1 - nx * nx - ny * ny, 0, 1))
    phi = (1 + 5 ** 0.5) / 2
    ico = np.array([[0, 1, phi], [0, -1, phi], [0, 1, -phi], [0, -1, -phi], [1, phi, 0], [-1, phi, 0], [1, -phi, 0], [-1, -phi, 0],
                    [phi, 0, 1], [-phi, 0, 1], [phi, 0, -1], [-phi, 0, -1]], np.float32)
    ico /= np.linalg.norm(ico, axis=1, keepdims=True)
    faces = []
    for i in range(12):
        for j in range(i + 1, 12):
            for k in range(j + 1, 12):
                if min(ico[i] @ ico[j], ico[j] @ ico[k], ico[i] @ ico[k]) > 0.4: faces.append((ico[i] + ico[j] + ico[k]) / 3)
    hexc_ = np.array(faces); hexc_ /= np.linalg.norm(hexc_, axis=1, keepdims=True)
    centres = np.concatenate([ico, hexc_])                         # 12 + 20
    a1, a2 = 0.5, 0.35                                             # (turned a little so it is not head-on)
    Ry = np.array([[np.cos(a1), 0, np.sin(a1)], [0, 1, 0], [-np.sin(a1), 0, np.cos(a1)]])
    Rx = np.array([[1, 0, 0], [0, np.cos(a2), -np.sin(a2)], [0, np.sin(a2), np.cos(a2)]])
    C = centres @ (Rx @ Ry).T
    P = np.stack([nx, -ny, nz], -1)
    dots = P @ C.T                                                 # (h, w, 32)
    o = np.argsort(-dots, -1)
    best, second = np.take_along_axis(dots, o[..., :1], -1)[..., 0], np.take_along_axis(dots, o[..., 1:2], -1)[..., 0]
    black = o[..., 0] < 12
    seam = (best - second) < 0.018
    n = np.stack([nx, ny, nz], -1)
    lam = np.clip((n * np.array([-0.5, -0.72, 0.48]) / np.linalg.norm([-0.5, -0.72, 0.48])).sum(-1), 0, 1)
    v = 0.18 + 0.82 * lam ** 0.8
    base = np.where(black[..., None], np.array([34, 30, 44], np.float32) * (0.6 + 0.8 * v[..., None]), np.array([255, 255, 255], np.float32) * (0.45 + 0.55 * v[..., None]))
    base = np.where(seam[..., None], base * 0.55, base)
    hv = np.array([-0.5, -0.72, 1.48]); hv /= np.linalg.norm(hv)
    sp = np.clip((n * hv).sum(-1), 0, 1) ** 40
    base = base + (np.clip((sp - 0.45) * 6, 0, 1) * 0.85)[..., None] * (255 - base)
    rim = (1 - nz) ** 2 * np.clip(nx * 0.6 + ny * 0.7, 0, 1)
    base = base + (rim * 0.35)[..., None] * (np.array([200, 220, 255], np.float32) - base)
    p.over(base, m.astype(np.float32)); p.parts.append(m)
    p.outline(3.0)
    return p.image()


SYMS = (poop, duck, plunger, roll, soap, drop)


if __name__ == '__main__':
    from PIL import Image
    out = '/tmp/claude-0/-home-claude/3a779e8a-891a-5a91-a306-4a5325e0d53e/scratchpad/sym'
    os.makedirs(out, exist_ok=True)
    ims = [f() for f in SYMS] + [coin(), ball()]
    S = Image.new('RGBA', (3 * (N + 20) + 20, 3 * (N + 20) + 20), (236, 232, 244, 255))
    for i, im in enumerate(ims):
        S.alpha_composite(Image.fromarray(np.clip(im, 0, 255).astype(np.uint8), 'RGBA'), (20 + (i % 3) * (N + 20), 20 + (i // 3) * (N + 20)))
    S.save(f'{out}/sheet.png')
