# The pictures of the two mini-games added in v40:
#  * the spleen: '세균 잡기' (whack the germs). A board of the spleen's red pulp seen from the front and a little above
#    (perspective), with nine openings of its venous sinuses in three rows; behind it, the dark pulp with the pale
#    balls of the white pulp. The germs that pop out of the openings: three bad ones (E. coli, a staph cluster, a
#    spiral one) and the good one (a lactobacillus, two cells in a chain), each with a face, and the face it makes when
#    it is hit.
#  * the hippocampus: '기억 시냅스' (the memory game). Five pyramidal neurons, each its own colour, lit and dim.
#   -> runner_hd/assets/wm_field.webp (lossy), wm.webp and mem.webp (lossless atlases) + manifest entries, and M.wm
#      (where the holes are)
import json, sys
import numpy as np, cv2
from PIL import Image
from scipy import ndimage
sys.path.insert(0, '/home/claude/hdart')
import art
from art import SC, px, hexc, ramp, ramp_col, dome_shade, outline, highlight, paint, over, disc, ellipse_soft, stroke, grid, paste

OUT = '/home/claude/runner_hd/assets'
PRE = '/tmp/claude-0/-home-claude/3a779e8a-891a-5a91-a306-4a5325e0d53e/scratchpad/mg'
FW, FH = 420, 180
CX = 210.0
HZ = -40.0                       # the vanishing line, above the picture: a thing's size on the board goes with y - HZ
YF = 152.0                       # the front row (scale 1)
EDGE = 64.0                      # the board's far edge
ROW_Y = [90.0, 119.0, 152.0]     # the rows of openings, far to near
COL_U = 112.0                    # the side openings' distance from the middle, at scale 1 (they close in with distance)
HOLE_RX = 26.0                   # an opening's half width at scale 1


def scale_at(y):
    return (y - HZ) / (YF - HZ)


def holes():
    """[dx from the middle, y, rx, ry, scale] of the nine openings, far row first, left to right"""
    out = []
    for y in ROW_Y:
        s = scale_at(y)
        rx = HOLE_RX * s
        ry = rx * (0.22 + 0.14 * s)              # flatter farther off (seen at a lower angle)
        for c in (-1, 0, 1):
            out.append([round(c * COL_U * s, 2), y, round(rx, 2), round(ry, 2), round(s, 3)])
    return out


def hash01(a, b, k=0):
    h = (a.astype(np.int64) * 374761393 + b.astype(np.int64) * 668265263 + k * 1442695041) & 0xffffffff
    h = ((h ^ (h >> 13)) * 1274126177) & 0xffffffff
    return ((h ^ (h >> 16)) & 0xffffff) / float(0xffffff)


def cells(u, v, size, k=0):
    """jittered cells: the distance to the nearest centre and to the second nearest (for borders)"""
    ci, cj = np.floor(u / size), np.floor(v / size)
    d1 = np.full(u.shape, 99.0); d2 = np.full(u.shape, 99.0)
    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            ii, jj = ci + di, cj + dj
            ox, oy = hash01(ii, jj, k), hash01(ii, jj, k + 7)
            d = np.hypot(u - (ii + 0.15 + 0.7 * ox) * size, v - (jj + 0.15 + 0.7 * oy) * size)
            d2 = np.where(d < d1, d1, np.minimum(d2, d)); d1 = np.minimum(d1, d)
    return d1, d2


# ---------------------------------------------------------------- the board
def rbc(r, tilt):
    """a red blood cell, r units across half, squashed by tilt (seen from above at an angle)"""
    w, h = r * 2 + 1.5, r * 2 * tilt + 1.5
    y, x = grid(h, w)
    cx, cy = (w - 1) / 2, (h - 1) / 2
    q = np.hypot((x - cx) / r, (y - cy) / (r * tilt))
    m = q <= 1
    sh, n = dome_shade(m, soft=0.5, ambient=0.4)
    sh = np.clip(sh - 0.42 * np.clip(1 - q / 0.55, 0, 1) ** 0.8, 0, 1)        # the dimple
    spr = paint(art.smooth_mask(m), ramp('#5a0610', '#9a121e', '#cc2430', '#ee5058', '#ff9a9a'), sh)
    return spr


def field():
    Hh, Ww = px(FH), px(FW)
    y = (np.arange(Hh, dtype=np.float64)[:, None] + 0.5) / SC
    x = (np.arange(Ww, dtype=np.float64)[None, :] + 0.5) / SC
    y = np.broadcast_to(y, (Hh, Ww)); x = np.broadcast_to(x, (Hh, Ww))
    rng = np.random.default_rng(31)
    can = np.zeros((Hh, Ww, 4), np.float32); can[..., 3] = 255
    # ---- behind the board: the dark pulp, out of focus
    t = np.clip(y / EDGE, 0, 1)
    back = ramp_col(ramp('#0e0206', '#1c040c', '#2e0812', '#44101c'), t)
    glow = np.exp(-(((x - CX) / 170) ** 2 + ((y - 70) / 50) ** 2)) * 0.5
    back = back + glow[..., None] * (hexc('#6a1a2a') - back) * 0.55
    can[..., :3] = back
    # trabeculae: pale fibrous bands slanting across, blurred
    tr = np.zeros((Hh, Ww), np.float32)
    for x0, a, w in [(60, 0.55, 3.2), (300, -0.45, 4.0), (380, 0.35, 2.4), (150, -0.7, 2.0)]:
        d = np.abs((x - x0) - (y - 40) * a) / np.sqrt(1 + a * a)
        tr = np.maximum(tr, np.clip(1 - d / w, 0, 1))
    tr = ndimage.gaussian_filter(tr, 1.2 * SC) * np.clip(1.2 - y / EDGE, 0, 1)
    can[..., :3] = can[..., :3] * (1 - 0.35 * tr[..., None]) + hexc('#b0586a') * 0.35 * tr[..., None]
    # white pulp: pale lymphoid balls round a little artery, far off and soft
    wp = np.zeros((Hh, Ww, 4), np.float32)
    for fx, fy, fr in [(70, 50, 26), (232, 40, 30), (366, 54, 24), (150, 58, 13), (316, 16, 13)]:
        q = np.hypot(x - fx, y - fy) / fr
        m = q <= 1
        shade = np.clip(0.35 + 0.65 * np.sqrt(np.clip(1 - q * q, 0, 1)) - 0.25 * (y - fy) / fr, 0, 1)
        col = ramp_col(ramp('#4a3a5a', '#7a6890', '#a898c0', '#d0c4e2'), shade)
        dots = cells(x, y, 1.6, k=int(fx))[0] < 0.42                               # packed lymphocytes
        col = np.where((dots & m)[..., None], col * 0.72 + hexc('#5a3a7a') * 0.28, col)
        ring = np.abs(np.hypot(x - fx - fr * 0.18, y - fy + fr * 0.1) - fr * 0.13) < max(0.5, fr * 0.035)
        col = np.where((ring & m)[..., None], hexc('#b8283a'), col)               # the central arteriole
        a = art.smooth_mask(m, 1.5).astype(np.float32) * (0.32 + 0.12 * (fr < 20))
        over(wp, col, a)
    wp = ndimage.gaussian_filter(wp, (1.1 * SC, 1.1 * SC, 0))
    over(can, wp[..., :3], wp[..., 3] / 255.0)
    # blurred red cells drifting behind (bokeh)
    bk = np.zeros((Hh, Ww, 4), np.float32)
    for _ in range(70):
        bx, by, br = rng.uniform(0, FW), rng.uniform(-4, EDGE + 6), rng.uniform(1.6, 4.5)
        ellipse_soft(bk, bx, by, br, br * rng.uniform(0.55, 0.9), '#b8202e', a=int(rng.uniform(70, 150)), ang=rng.uniform(-0.6, 0.6))
    bk = ndimage.gaussian_filter(bk, (0.9 * SC, 0.9 * SC, 0))
    over(can, bk[..., :3], bk[..., 3] / 255.0)
    # ---- the board: the red pulp's surface through the camera
    s = np.maximum((y - HZ) / (YF - HZ), 0.05)
    u = (x - CX) / s                                   # across, in board units
    v = 192.0 / s                                      # depth (farther: larger)
    d1, d2 = cells(u, v * 1.4, 9.0, k=3)               # the cords' mesh of reticular fibres
    fib = np.clip(1 - (d2 - d1) / np.maximum(0.9 / s, 0.6), 0, 1)
    fib2 = np.clip(1 - (lambda a: a[1] - a[0])(cells(u, v * 1.4, 3.4, k=9)) / np.maximum(0.5 / s, 0.45), 0, 1)
    n1 = ndimage.gaussian_filter(rng.standard_normal((Hh, Ww)), 9) * 9 + ndimage.gaussian_filter(rng.standard_normal((Hh, Ww)), 2) * 0.8
    light = np.exp(-(((x - CX) / 210) ** 2 + ((y - 110) / 90) ** 2))           # a soft pool of light in the middle
    val = np.clip(0.30 + 0.32 * light + 0.06 * n1 - 0.10 * np.clip((y - 150) / 30, 0, 1), 0, 1)
    board = ramp_col(ramp('#30040c', '#560c18', '#7c1626', '#a02634', '#c84450', '#e47678'), val)
    board = board * (1 - 0.28 * fib2[..., None] * s[..., None].clip(0, 1)) + hexc('#3a0610') * 0.28 * fib2[..., None] * s[..., None].clip(0, 1)
    board = board + fib[..., None] * (hexc('#f0a6aa') - board) * (0.42 * np.clip(s, 0, 1))[..., None]
    # the far edge rounds away: lighter just at the rim, the haze of distance
    rim = np.exp(-((y - EDGE - 1.2) / 1.6) ** 2)
    board = board + rim[..., None] * (hexc('#f0a0a4') - board) * 0.5
    haze = np.clip(1 - (y - EDGE) / 50, 0, 1) ** 1.5
    board = board * (1 - 0.35 * haze[..., None]) + hexc('#3a0a16') * 0.35 * haze[..., None]
    ea = np.clip((y - EDGE + 0.5) * SC / 2, 0, 1)
    can[..., :3] = can[..., :3] * (1 - ea[..., None]) + board * ea[..., None]
    # red cells lying in the cords (squashed by the angle), kept off the openings
    H9 = holes()
    base = {}
    for _ in range(520):
        yy = EDGE + 2 + (FH - EDGE) * rng.random() ** 0.8
        sc = scale_at(yy); xx = CX + rng.uniform(-1.2, 1.2) * 260 * sc
        if any(((xx - (CX + h[0])) / (h[2] + 5 * h[4])) ** 2 + ((yy - h[1]) / (h[3] + 4 * h[4])) ** 2 < 1 for h in H9): continue
        r = round(2.3 * sc * rng.uniform(0.85, 1.15), 1); tilt = round(0.42 + 0.16 * sc, 2)
        key = (r, tilt)
        if key not in base: base[key] = rbc(r, tilt)
        paste(can, base[key], xx - base[key].shape[1] / SC / 2, yy - base[key].shape[0] / SC / 2, opacity=0.9 - 0.35 * (1 - sc))
    # ---- the openings
    for dx, hy, rx, ry, sc in H9:
        hx = CX + dx
        # a soft shadow round it and the rounded lip of the sinus wall
        ao = np.zeros((Hh, Ww, 4), np.float32)
        ellipse_soft(ao, hx, hy + ry * 0.25, rx * 1.32, ry * 1.75, '#14020a', a=150)
        ao = ndimage.gaussian_filter(ao, (1.4 * SC * sc, 1.4 * SC * sc, 0))
        over(can, ao[..., :3], ao[..., 3] / 255.0)
        q = np.hypot((x - hx) / (rx * 1.13), (y - hy) / (ry * 1.22))
        lipm = q <= 1
        lit = np.clip(0.5 - 0.55 * (y - hy) / (ry * 1.22) + 0.25 * np.clip(1 - np.abs(q - 0.92) / 0.08, 0, 1), 0, 1)
        lipc = ramp_col(ramp('#5a0c18', '#8a1c2c', '#b83a48', '#e2727a', '#ffc0c0'), lit)
        over(can, lipc, art.smooth_mask(lipm, 0.8).astype(np.float32))
        # the opening: the far inner wall lit near the top, going dark down into the sinus
        r = np.hypot((x - hx) / rx, (y - hy) / ry)
        hole = r <= 1
        tt = np.clip((y - (hy - ry)) / (2 * ry), 0, 1)                        # 0 at the far rim .. 1 at the near
        inner = ramp_col(ramp('#060004', '#14020a', '#2e0610', '#5a1220', '#8a2a36'), np.clip(1 - tt * 1.9, 0, 1) ** 1.3)
        inner = inner * (1 - 0.35 * np.clip(r - 0.7, 0, 1)[..., None])
        over(can, inner, art.smooth_mask(hole, 0.8).astype(np.float32))
        # a wet shine along the inside of the far rim and a thin one on the near lip
        sh1 = np.clip(1 - np.abs(r - 0.86) / 0.07, 0, 1) * (y < hy - ry * 0.35) * np.clip(1 - np.abs(x - hx) / (rx * 0.85), 0, 1)
        sh2 = np.clip(1 - np.abs(q - 0.97) / 0.035, 0, 1) * (y > hy + ry * 0.55) * np.clip(1 - np.abs(x - hx) / (rx * 0.9), 0, 1)
        k = np.clip(sh1 * 0.55 + sh2 * 0.6, 0, 1)
        can[..., :3] = can[..., :3] * (1 - k[..., None]) + hexc('#ffdcdc') * k[..., None]
    # the near corners darker (the board curving down)
    vig = np.clip(((x - CX) / 250) ** 2 + ((y - 200) / 120) ** 2 - 0.35, 0, 1) * np.clip((y - 100) / 60, 0, 1)
    can[..., :3] *= (1 - 0.45 * vig[..., None])
    return can


# ---------------------------------------------------------------- the germs
def eye_pair(spr, fx, fy, sp, er, mood):
    """the runners' eyes: big glossy black ones with a shine (mood 'bad': brows down in the middle; 'good': round
    and bright; 'dizzy': two X's; 'ouch': squeezed shut > <)"""
    for side in (-1, 1):
        ex = fx + side * sp
        if mood in ('bad', 'good'):
            disc(spr, ex, fy, er + 0.4, '#1a0a14')
            disc(spr, ex, fy, er, '#120a16')
            disc(spr, ex + 0.25 * er, fy + 0.25 * er, er * 0.62, '#2a1830', a=200)
            disc(spr, ex + 0.3 * er, fy + 0.5 * er, er * 0.24, '#ff7a9a' if mood == 'good' else '#ff6a2a', a=210)
            disc(spr, ex - 0.32 * er, fy - 0.36 * er, er * (0.42 if mood == 'good' else 0.36), '#ffffff')
            disc(spr, ex + 0.38 * er, fy - 0.05 * er, er * 0.16, '#ffffff', a=230)
            if mood == 'bad':                                                  # a heavy brow slanting down to the middle
                stroke(spr, [(ex - side * er * 0.95, fy - er * 1.05), (ex + side * er * 1.2, fy - er * 1.85)], er * 0.75, '#1a0a14')
        elif mood == 'dizzy':
            k = er * 0.85
            stroke(spr, [(ex - k, fy - k), (ex + k, fy + k)], er * 0.48, '#1a0a14')
            stroke(spr, [(ex - k, fy + k), (ex + k, fy - k)], er * 0.48, '#1a0a14')
        else:                                                                  # 'ouch': > on the left, < on the right
            k = er * 0.9
            stroke(spr, [(ex + side * k, fy - k * 0.8), (ex - side * k * 0.6, fy), (ex + side * k, fy + k * 0.8)], er * 0.45, '#1a0a14')
            disc(spr, ex + side * er * 0.2, fy + er * 1.6, er * 0.42, '#bfe8ff', a=230)        # a tear
            disc(spr, ex + side * er * 0.05, fy + er * 1.45, er * 0.15, '#ffffff', a=230)


def mouth(spr, mx, my, w, mood):
    if mood == 'bad':                                                          # a wide mean grin with teeth
        ellipse_soft(spr, mx, my, w, w * 0.42, '#1a0a14')
        ellipse_soft(spr, mx, my + w * 0.08, w * 0.82, w * 0.27, '#5a0a1c')
        for k in (-0.5, 0, 0.5):
            ellipse_soft(spr, mx + k * w * 0.6, my - w * 0.13, w * 0.15, w * 0.13, '#fff4ea')
    elif mood == 'good':                                                       # a happy open smile, a tongue
        ellipse_soft(spr, mx, my, w * 0.8, w * 0.55, '#1a0a14')
        ellipse_soft(spr, mx, my + w * 0.08, w * 0.6, w * 0.4, '#7a1a2c')
        ellipse_soft(spr, mx, my + w * 0.28, w * 0.42, w * 0.2, '#ff7a8a')
    elif mood == 'dizzy':                                                      # a wobbly open O
        ellipse_soft(spr, mx, my, w * 0.5, w * 0.55, '#1a0a14')
        ellipse_soft(spr, mx, my + w * 0.05, w * 0.32, w * 0.36, '#6a1224')
    else:                                                                      # 'ouch': a wavy frown
        pts = [(mx - w * 0.75 + k * w * 0.25, my + (0.22 if k % 2 else -0.05) * w) for k in range(7)]
        stroke(spr, pts, w * 0.16, '#1a0a14')


def cheeks(spr, fx, fy, sp, r, col='#ff7aa0', a=150):
    for side in (-1, 1):
        ellipse_soft(spr, fx + side * sp, fy, r, r * 0.6, col, a=a)


def capsule(x, y, x0, y0, x1, y1, r):
    """inside a capsule (the segment (x0,y0)-(x1,y1) grown by r)"""
    dx, dy = x1 - x0, y1 - y0
    t = np.clip(((x - x0) * dx + (y - y0) * dy) / max(dx * dx + dy * dy, 1e-6), 0, 1)
    return np.hypot(x - (x0 + dx * t), y - (y0 + dy * t)) <= r


def finish(body, rmp, shade, n, gloss=0.85):
    spr = paint(art.smooth_mask(body), rmp, shade)
    highlight(spr, body, n, thresh=0.94, alpha=gloss)
    return spr


def wave(x0, y0, ang, L, amp, k, ph=0.0, n=40):
    """a wavy whip from (x0, y0) along ang (radians), L long"""
    ux, uy = np.cos(ang), np.sin(ang)
    pts = []
    for i in range(n + 1):
        t = i / n
        o = amp * np.sin(t * k * 2 * np.pi + ph) * min(1, t * 3)
        pts.append((x0 + ux * L * t - uy * o, y0 + uy * L * t + ux * o))
    return pts


def germ(kind, hit):
    """a germ facing us, base down (the base sits in the opening). Returns the outlined sprite and its base point"""
    if kind == 'ecoli':                            # a plump purple rod, fuzzy with pili, a few long whips
        W_, H_ = 58, 50
        y, x = grid(H_, W_)
        cx, top, bot, r = 29.0, 8.0, 46.0, 10.5
        body = capsule(x, y, cx, top + r, cx, bot - r, r)
        hair = np.zeros(body.shape + (4,), np.float32)
        R = np.random.default_rng(5)
        edge = body & ~ndimage.binary_erosion(body, iterations=2)
        ey_, ex_ = np.nonzero(edge)
        for k in R.choice(len(ex_), 70, replace=False):                     # short pili all round the edge
            ex, ey = (ex_[k] + 0.5) / SC - 0.5, (ey_[k] + 0.5) / SC - 0.5
            ax, ay = cx, min(max(ey, top + r), bot - r)
            nx, ny = ex - ax, ey - ay; nl = max(np.hypot(nx, ny), 1e-3); nx /= nl; ny /= nl
            L = R.uniform(1.2, 2.2)
            stroke(hair, [(ex, ey), (ex + nx * L - ny * 0.3, ey + ny * L + nx * 0.3)], 0.42, '#5a2a78')
        for ang, sx, sy, ph in [(-2.5, -9.5, 14, 0.0), (-2.9, -10.2, 26, 1.7), (-0.62, 9.5, 15, 0.9), (-0.22, 10.2, 27, 2.4)]:
            stroke(hair, wave(cx + sx, sy, ang, 15.5, 1.5, 1.6, ph), 0.75, '#7a4a9a')
        shade, n = dome_shade(body, soft=1.8)
        streak = 0.06 * np.sin((x - cx) * 0.9) * body
        spr = finish(body, ramp('#2e1046', '#542680', '#7e44ac', '#a874d0', '#d6b2ee'), np.clip(shade + streak, 0, 1), n)
        R2 = np.random.default_rng(8)
        for _ in range(26):                          # granules in the cell
            gx, gy = cx + R2.uniform(-7, 7), R2.uniform(top + 4, bot - 4)
            if ((gx - cx) / 8) ** 2 > 1: continue
            disc(spr, gx, gy, R2.uniform(0.3, 0.6), '#4a1c6a', a=110)
        over(hair, spr[..., :3], spr[..., 3] / 255.0)
        spr = hair
        fx, fy, sp, er, mw = cx + 0.3, top + 13.5, 4.3, 2.75, 5.0
    elif kind == 'staph':                          # a bunch of golden balls, the front one with the face
        W_, H_ = 48, 46
        spr = np.zeros((px(H_), px(W_), 4), np.float32)
        balls = [(13, 11, 5.6, 0.55), (25, 8, 6.0, 0.55), (36, 13, 5.4, 0.55), (7, 23, 5.2, 0.55), (41, 26, 5.0, 0.55),
                 (18, 17, 7.0, 0.8), (33, 21, 7.2, 0.8), (11, 33, 7.0, 0.8), (37, 37, 6.8, 0.8), (20, 39, 7.0, 0.8),
                 (22, 25, 10.4, 1.0), (33, 33, 6.4, 1.0)]
        for bx, by, br, lk in balls:
            w = 2 * br + 2
            yy, xx = grid(w, w)
            m = np.hypot(xx - (w - 1) / 2, yy - (w - 1) / 2) <= br
            shade, n = dome_shade(m, soft=0.9)
            b = finish(m, ramp('#5a2e04', '#9a5a0a', '#d68e1a', '#f4c048', '#fff0b0'), shade * (0.55 + 0.45 * lk), n, gloss=0.9 * lk)
            if br < 10:
                R = np.random.default_rng(int(bx * 7 + by))
                for _ in range(6): disc(b, R.uniform(3, w - 3), R.uniform(3, w - 3), 0.45, '#b06a10', a=90)
            b = outline(b, width=0.6)
            paste(spr, b, bx - w / 2 - 0.5, by - w / 2 - 0.5)
        cx, bot = 23.0, 46.0
        fx, fy, sp, er, mw = 22.5, 23.5, 4.2, 2.7, 4.8
    elif kind == 'spiral':                          # a twisted crimson rod with a tuft of whips on top
        W_, H_ = 44, 56
        y, x = grid(H_, W_)
        T = np.linspace(0, 1, 260)
        cxs, cys = 22 + 5.2 * np.sin(T * 2 * np.pi * 1.15 + 0.4), 13 + T * 41
        r = 6.4
        d = np.full(x.shape, 99.0); tm = np.zeros(x.shape)
        for k in range(len(T)):
            dd = np.hypot(x - cxs[k], y - cys[k])
            upd = dd < d; d = np.where(upd, dd, d); tm = np.where(upd, T[k], tm)
        body = d <= r
        shade, n = dome_shade(body, soft=1.4)
        band = 0.13 * np.sin(tm * 2 * np.pi * 4.6) * body                      # the twist
        hair = np.zeros(body.shape + (4,), np.float32)
        for ang, ph in [(-1.95, 0.0), (-1.65, 1.2), (-1.35, 2.1), (-1.1, 0.7)]:
            stroke(hair, wave(cxs[0] + (ang + 1.5) * 4, cys[0] - 3.5, ang, 11.5, 1.2, 1.5, ph), 0.7, '#9a2a3a')
        spr = finish(body, ramp('#3e060e', '#741222', '#ac2434', '#e0545a', '#ffb0a8'), np.clip(shade + band, 0, 1), n)
        over(hair, spr[..., :3], spr[..., 3] / 255.0)
        spr = hair
        k0 = int(0.25 * 259)
        cx, bot = 22.0, 54.0
        fx, fy, sp, er, mw = cxs[k0] + 0.2, cys[k0] + 1.0, 3.5, 2.35, 4.0
    else:                                           # 'lacto': two bright green rods in a chain, smooth and glossy
        W_, H_ = 34, 52
        y, x = grid(H_, W_)
        cx, r = 17.0, 8.6
        body = capsule(x, y, cx, 8 + r, cx, 25.5, r) | capsule(x, y, cx, 27.5, cx, 49 - r, r * 0.97)
        shade, n = dome_shade(body, soft=1.6)
        waist = np.exp(-((y - 26.5) / 1.1) ** 2) * 0.22 * body
        spr = finish(body, ramp('#14480e', '#226e18', '#3ea42c', '#78d45a', '#cff4a8'), np.clip(shade - waist, 0, 1), n, gloss=1.0)
        bot = 49.0
        fx, fy, sp, er, mw = cx + 0.2, 17.0, 4.3, 2.9, 4.6
    good = kind == 'lacto'
    mood = ('ouch' if good else 'dizzy') if hit else ('good' if good else 'bad')
    if good: cheeks(spr, fx, fy + er * 1.55, sp + er * 0.5, er * 0.85)
    eye_pair(spr, fx, fy, sp, er, mood)
    mouth(spr, fx, fy + er * 2.15 + (0.6 if mood == 'bad' else 0.9), mw * (0.85 if mood in ('dizzy', 'ouch') else 1), mood)
    spr = outline(spr)
    return spr, {'foot': [round(cx + 1, 2), round(bot + 1, 2)]}


# ---------------------------------------------------------------- the neurons
NEURON_RAMPS = [
    ('#5a0818', '#a81a40', '#f0406a', '#ff96b0', '#ffe6ee'),     # 0 rose
    ('#5a3200', '#a86600', '#f4a81c', '#ffd67a', '#fff6d6'),     # 1 amber
    ('#0a4416', '#188030', '#30c45a', '#92eca4', '#e6ffea'),     # 2 green
    ('#0a265e', '#1652b4', '#3a92f4', '#9accff', '#e8f4ff'),     # 3 blue
    ('#360e60', '#6428ae', '#9e60f4', '#ceaaff', '#f4ecff'),     # 4 violet
]


def taper(dst_mask, pts, w0, w1):
    """a tapering branch into a uint8 mask (pts in units)"""
    n = len(pts) - 1
    for i in range(n):
        w = w0 + (w1 - w0) * i / max(n - 1, 1)
        p0 = (int(round((pts[i][0] + 0.5) * SC * 16)), int(round((pts[i][1] + 0.5) * SC * 16)))
        p1 = (int(round((pts[i + 1][0] + 0.5) * SC * 16)), int(round((pts[i + 1][1] + 0.5) * SC * 16)))
        cv2.line(dst_mask, p0, p1, 255, max(1, int(round(w * SC))), cv2.LINE_AA, 4)


def branch(R, x0, y0, ang, L, segs=7, bend=0.18):
    pts = [(x0, y0)]
    a = ang
    for _ in range(segs):
        a += R.uniform(-bend, bend)
        x0 += np.cos(a) * L / segs; y0 += np.sin(a) * L / segs
        pts.append((x0, y0))
    return pts


def neuron(k, lit):
    """a pyramidal cell of the hippocampus as a button: a big rounded pyramid of a body, a thick dendrite up from its
    apex that forks, dendrites spreading from its base on both sides, the axon down"""
    W_, H_ = 54, 54
    R = np.random.default_rng(100 + k)
    m = np.zeros((px(H_), px(W_)), np.uint8)
    cx, cy = 27.0, 29.0
    tri = np.array([[cx, cy - 13.0], [cx - 10.2, cy + 7.0], [cx + 10.2, cy + 7.0]])
    cv2.fillPoly(m, [np.round((tri + 0.5) * SC * 16).astype(np.int32)], 255, cv2.LINE_AA, 4)
    soma = ndimage.gaussian_filter(m.astype(np.float32), 1.9 * SC) > 105
    m = (soma * 255).astype(np.uint8)
    ap = branch(R, cx, cy - 10, -np.pi / 2 + R.uniform(-0.1, 0.1), 15, 6, 0.1)            # the apical dendrite
    taper(m, ap, 3.6, 1.8)
    for side in (-1, 1):                                                                     # its fork at the top
        b = branch(R, ap[-1][0], ap[-1][1], -np.pi / 2 + side * R.uniform(0.45, 0.65), R.uniform(9, 11), 5, 0.2)
        taper(m, b, 1.9, 0.6)
        b2 = branch(R, b[2][0], b[2][1], -np.pi / 2 + side * 1.25, 5.5, 3, 0.25)
        taper(m, b2, 1.1, 0.5)
    j = R.integers(2, 4); side = 1 if k % 2 else -1                                          # an oblique one
    taper(m, branch(R, ap[j][0], ap[j][1], -np.pi / 2 + side * 1.2, 9, 4, 0.2), 1.5, 0.5)
    for side in (-1, 1):                                                                     # the basal dendrites
        for th, L, w0 in [(1.35, 15, 2.6), (0.85, 15, 2.5), (0.35, 12, 2.1)]:
            a0 = np.pi / 2 - side * th                                               # (y down: 0 is right, pi/2 down)
            x0 = cx + side * (8.5 if th > 0.5 else 5.0)
            b = branch(R, x0, cy + 5.5, a0 + R.uniform(-0.12, 0.12), L + R.uniform(-1.5, 1.5), 6, 0.2)
            taper(m, b, w0, 0.6)
            jj = R.integers(2, 4)
            taper(m, branch(R, b[jj][0], b[jj][1], a0 + side * R.uniform(0.4, 0.7), 5.5, 3, 0.3), 1.2, 0.5)   # (turned down)
    taper(m, branch(R, cx + 0.4, cy + 7, np.pi / 2 + R.uniform(-0.06, 0.06), 15, 6, 0.06), 1.4, 0.9)    # the axon
    mask = m > 127
    shade, n = dome_shade(mask, soft=0.7)
    rm = ramp(*NEURON_RAMPS[k])
    if not lit:
        dark = hexc('#1c1426')
        rm = [c * 0.55 + dark * 0.45 for c in rm]
    spr = paint(art.smooth_mask(mask), rm, np.clip(shade * (1.0 if lit else 0.9) + (0.12 if lit else 0), 0, 1))
    highlight(spr, mask, n, thresh=0.95, alpha=0.8 if lit else 0.35)
    y, x = grid(H_, W_)
    if lit:                                         # the cell glows from inside: lighter towards the body
        g = np.exp(-(((x - cx) / 11) ** 2 + ((y - cy + 2) / 12) ** 2)) * mask
        spr[..., :3] = spr[..., :3] * (1 - 0.45 * g[..., None]) + 255 * 0.45 * g[..., None]
    # the nucleus and its nucleolus
    ellipse_soft(spr, cx, cy, 4.4, 4.8, '#ffffff' if lit else '#9a90a8', a=110 if lit else 70)
    disc(spr, cx + 0.5, cy + 0.3, 1.5, NEURON_RAMPS[k][1] if lit else '#3a3048', a=200)
    spr = outline(spr, width=0.65)
    return spr, {'c': [cx + 1, cy + 1]}


def atlas(sprs):
    fw = sum(s.shape[1] for s, _ in sprs) + 4 * len(sprs); fh = max(s.shape[0] for s, _ in sprs)
    A = np.zeros((fh, fw, 4), np.float32)
    rects = []; x0 = 0
    for s, _ in sprs:
        A[:s.shape[0], x0:x0 + s.shape[1]] = s; rects.append([x0, 0, s.shape[1], s.shape[0]]); x0 += s.shape[1] + 4
    return A, rects


if __name__ == '__main__':
    import os
    os.makedirs(PRE, exist_ok=True)
    f = field()
    im = Image.fromarray(np.clip(f, 0, 255).astype(np.uint8), 'RGBA').convert('RGB')
    im.save(f'{OUT}/wm_field.webp', quality=88, method=6)
    im.resize((px(FW) // 2, px(FH) // 2), Image.LANCZOS).save(f'{PRE}/wm_field.png')
    names, sprs = [], []
    for kind in ('ecoli', 'staph', 'spiral', 'lacto'):
        for hit in (False, True):
            names.append(f'wm_{kind}' + ('_hit' if hit else '')); sprs.append(germ(kind, hit))
    A, rects = atlas(sprs)
    Image.fromarray(np.clip(A, 0, 255).astype(np.uint8), 'RGBA').save(f'{OUT}/wm.webp', lossless=True, method=6)
    Image.fromarray(np.clip(A, 0, 255).astype(np.uint8), 'RGBA').save(f'{PRE}/wm_germs.png')
    nn, ns = [], []
    for k in range(5):
        for lit in (True, False):
            nn.append(f'mem_{"n" if lit else "d"}{k}'); ns.append(neuron(k, lit))
    B, brects = atlas(ns)
    Image.fromarray(np.clip(B, 0, 255).astype(np.uint8), 'RGBA').save(f'{OUT}/mem.webp', lossless=True, method=6)
    Image.fromarray(np.clip(B, 0, 255).astype(np.uint8), 'RGBA').save(f'{PRE}/mem_neurons.png')
    m = json.load(open(f'{OUT}/manifest.json'))
    m['sprites']['wm_field'] = {'f': 'wm_field.webp', 'r': [0, 0, px(FW), px(FH)], 'w': FW, 'h': FH}
    for nm, (s, meta), r in zip(names, sprs, rects):
        m['sprites'][nm] = {'f': 'wm.webp', 'r': r, 'w': round(s.shape[1] / SC, 3), 'h': round(s.shape[0] / SC, 3), **meta}
    for nm, (s, meta), r in zip(nn, ns, brects):
        m['sprites'][nm] = {'f': 'mem.webp', 'r': r, 'w': round(s.shape[1] / SC, 3), 'h': round(s.shape[0] / SC, 3), **meta}
    m['wm'] = {'holes': holes(), 'edge': EDGE}
    json.dump(m, open(f'{OUT}/manifest.json', 'w'), separators=(',', ':'))
    for fn in ('wm_field.webp', 'wm.webp', 'mem.webp'):
        print(fn, os.path.getsize(f'{OUT}/{fn}'))
    print('holes', holes())
