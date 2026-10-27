# Stage 2's first two mini-games (v44):
#  * the manhole: '승부차기' (a penalty shoot-out). Under the manhole, down in a round brick sewer: a flat concrete
#    landing with a painted box and spot, a goal of white-painted pipes with a net, light falling from the manhole
#    above. The keeper: a sewer rat in a goalkeeper's jersey and big gloves (ready, diving, jumping); the ball.
#  * the toilet: '변기 잭팟' (a slot machine): the cabinet is a porcelain toilet tank with three reel windows, a gold
#    marquee and a chrome flush lever (up, pulled); six symbols (a golden poop: the jackpot, a rubber duck, a plunger,
#    a toilet roll, a bar of soap, a water drop) and a coin.
#   -> runner_hd/assets/pk_field.webp (lossy), pk.webp, sl.webp (lossless) + manifest entries (M.pk, M.sl)
import json, sys, os
import numpy as np, cv2
from PIL import Image
from scipy import ndimage
sys.path.insert(0, '/home/claude/hdart')
import art
from art import SC, px, hexc, ramp, ramp_col, dome_shade, outline, highlight, paint, over, disc, ellipse_soft, stroke, grid, paste

OUT = '/home/claude/runner_hd/assets'
PRE = '/tmp/claude-0/-home-claude/3a779e8a-891a-5a91-a306-4a5325e0d53e/scratchpad/mg2'
FW, FH = 420, 180
CX = 210.0


# ---------------------------------------------------------------- shapes
def ell(y, x, cx, cy, rx, ry, ang=0.0):
    c, s = np.cos(ang), np.sin(ang)
    u, v = (x - cx) * c + (y - cy) * s, -(x - cx) * s + (y - cy) * c
    return (u / rx) ** 2 + (v / ry) ** 2 <= 1


def cap(y, x, p0, p1, r0, r1=None):
    r1 = r0 if r1 is None else r1
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    t = np.clip(((x - p0[0]) * dx + (y - p0[1]) * dy) / max(dx * dx + dy * dy, 1e-6), 0, 1)
    return np.hypot(x - (p0[0] + dx * t), y - (p0[1] + dy * t)) <= r0 + (r1 - r0) * t


def part(mask, rmp, soft=1.0, gloss=0.6, light=(-0.55, -0.7, 0.45)):
    shade, n = dome_shade(mask, light=light, soft=soft)
    spr = paint(art.smooth_mask(mask), ramp(*rmp), shade)
    if gloss: highlight(spr, mask, n, light=light, thresh=0.95, alpha=gloss)
    return spr


def stack(layers, w, h, line=0.6):
    """paint the parts one over another, each with a thin dark line round it, then the whole outlined"""
    can = np.zeros((px(h), px(w), 4), np.float32)
    for spr in layers:
        o = outline(spr, width=line)
        paste(can, o, -1, -1)
    return can


# ---------------------------------------------------------------- the keeper: a sewer rat
FUR = ('#2e2628', '#4e4446', '#746a6c', '#9c9294', '#c8c0c0')
PINK = ('#7a3a48', '#b85a6a', '#e08a96', '#f4b4bc', '#ffe0e4')
JERSEY = ('#7a2a00', '#c25a06', '#f08a1a', '#ffbc5a', '#ffe6b8')
GLOVE = ('#0e4a1a', '#1c7a2a', '#36b044', '#7ae07c', '#d0ffd0')


def rat(pose):
    """pose 0: ready (crouched, gloves out), 1: diving to the left (the figure turned), 2: jumping, gloves up.
    Returns the outlined sprite and where its middle is (the body's centre) and its hands"""
    W_, H_ = 84, 70
    y, x = grid(H_, W_)
    bx, by = (47.0 if pose == 1 else 42.0), 40.0           # the body's centre in the frame (room for the gloves when diving)
    rot = {0: 0.0, 1: -1.35, 2: 0.0}[pose]                  # (y down: negative turns it anticlockwise, head to the left)
    cr, sr = np.cos(rot), np.sin(rot)
    T = lambda px_, py_: (bx + px_ * cr - py_ * sr, by + px_ * sr + py_ * cr)        # local (from the body) -> frame
    E = lambda lx, ly, rx, ry, a=0.0: ell(y, x, *T(lx, ly), rx, ry, a + rot)
    C = lambda p0, p1, r0, r1=None: cap(y, x, T(*p0), T(*p1), r0, r1)
    if pose == 0: hands = [(-21, -10), (21, -10)]; feet = [(-7, 14), (7, 14)]
    elif pose == 1: hands = [(-6, -39), (6, -38)]; feet = [(-6, 16), (8, 13)]
    else: hands = [(-12, -34), (12, -34)]; feet = [(-6, 16), (6, 16)]
    L = []
    # the tail, behind: a curl out to the right and down
    tail = np.zeros(y.shape, bool)
    pts = [T(6 + 10 * t, 10 + 6 * np.sin(t * 2.6) + 4 * t) for t in np.linspace(0, 1, 30)]
    for k, (qx, qy) in enumerate(pts): tail |= (x - qx) ** 2 + (y - qy) ** 2 <= (1.5 - 0.9 * k / 30) ** 2
    L.append(part(tail, PINK, soft=0.4, gloss=0))
    # legs and feet
    for side, (fx, fy) in zip((-1, 1), feet):
        L.append(part(C((side * 5, 6), (fx, fy - 2), 3.2, 2.8), FUR, soft=0.6, gloss=0))
        L.append(part(E(fx + side * 1.5, fy + 0.5, 3.8, 2.2), PINK, soft=0.5, gloss=0.4))
    # the body in its jersey (a lighter belly patch under the jersey's hem), the number on it
    L.append(part(E(0, 0, 11.5, 13.0), JERSEY, soft=1.6, gloss=0.5))
    # arms (fur sleeves) to the gloves
    for side, (hx, hy) in zip((-1, 1), hands):
        L.append(part(C((side * 9, -7), (hx * 0.82, hy * 0.82), 3.2, 2.6), FUR, soft=0.6, gloss=0))
    for side, (hx, hy) in zip((-1, 1), hands):
        L.append(part(E(hx, hy, 5.4, 5.8, side * 0.3), GLOVE, soft=0.9, gloss=0.7))
    # the head: round, a snout forward, big ears
    hy0 = -17
    for side in (-1, 1):
        L.append(part(E(side * 8.5, hy0 - 8.5, 5.8, 5.8), FUR, soft=0.8, gloss=0))
    head = E(0, hy0, 10.0, 9.0)
    L.append(part(head, FUR, soft=1.2, gloss=0.4))
    can = stack(L, W_, H_)
    # the inside of the ears, the muzzle, the face (drawn on the stacked picture)
    for side in (-1, 1):
        ex, ey = T(side * 8.5, hy0 - 8.5); ellipse_soft(can, ex, ey, 3.4, 3.4, '#e48a98', a=235)
    mx, my = T(0, hy0 + 4.0); ellipse_soft(can, mx, my, 5.6, 4.0, '#d8d0d0', ang=rot)
    nx, ny = T(0, hy0 + 2.0); ellipse_soft(can, nx, ny, 2.0, 1.5, '#1a0a14', ang=rot); disc(can, nx - 0.5, ny - 0.5, 0.5, '#ffffff', a=200)
    for side in (-1, 1):                                    # two front teeth
        tx, ty = T(side * 0.9, hy0 + 6.4); ellipse_soft(can, tx, ty, 0.8, 1.2, '#fffaf0', ang=rot)
    for side in (-1, 1):                                    # eyes: glossy, a shine (the runners' style)
        ex, ey = T(side * 4.2, hy0 - 2.0)
        disc(can, ex, ey, 2.5, '#1a0a14'); disc(can, ex, ey, 2.15, '#120a16')
        disc(can, ex - 0.75, ey - 0.8, 0.85, '#ffffff'); disc(can, ex + 0.8, ey + 0.2, 0.35, '#ffffff', a=220)
        for k in (-1, 0, 1):                                # whiskers
            w0 = T(side * 4.5, hy0 + 4.0 + k * 0.9); w1 = T(side * 12.5, hy0 + 3.0 + k * 2.2)
            stroke(can, [w0, w1], 0.35, '#1a0a14', a=180)
    # the jersey's number
    jx, jy = T(0, 1.0)
    if pose != 1: art.text(can, '1', jx, jy, 6.5, '#fff4e0', out_col='#7a2a00', out_w=0.5)
    can = outline(can, width=0.5)
    hx = [T(*h) for h in hands]
    return can, {'c': [round(bx + 1, 2), round(by + 1, 2)], 'hands': [[round(a + 1, 2), round(b + 1, 2)] for a, b in hx]}


# ---------------------------------------------------------------- the ball
def ball():
    W_ = 22
    y, x = grid(W_, W_)
    c = (W_ - 1) / 2; r = 10.0
    m = np.hypot(x - c, y - c) <= r
    shade, n = dome_shade(m, soft=0.8, ambient=0.35)
    spr = paint(art.smooth_mask(m), ramp('#8a8f98', '#c8ccd4', '#eef0f4', '#ffffff'), shade)
    # the patches: a pentagon in the middle and the edges of five round it, on the sphere (a flat look, curved at the rim)
    pent = lambda cx_, cy_, rr, a0: np.array([[cx_ + rr * np.cos(a0 + k * 2 * np.pi / 5), cy_ + rr * np.sin(a0 + k * 2 * np.pi / 5)] for k in range(5)])
    pats = [pent(c, c, 3.4, -np.pi / 2)]
    for k in range(5):
        a = -np.pi / 2 + np.pi / 5 + k * 2 * np.pi / 5
        pats.append(pent(c + np.cos(a) * 8.6, c + np.sin(a) * 8.6, 3.0, a + np.pi))
    pm = np.zeros(m.shape, np.uint8)
    for P in pats: cv2.fillPoly(pm, [np.round((P + 0.5) * SC * 16).astype(np.int32)], 255, cv2.LINE_AA, 4)
    k = (pm.astype(np.float32) / 255) * m
    dark = ramp_col(ramp('#0a0a12', '#1e2030', '#3a3e52'), shade)
    spr[..., :3] = spr[..., :3] * (1 - k[..., None]) + dark * k[..., None]
    highlight(spr, m, n, thresh=0.95, alpha=0.9)
    return outline(spr, width=0.6), {'c': [c + 1, c + 1]}


# ---------------------------------------------------------------- the field: a round brick sewer under the manhole
VP = (CX, 66.0)                    # where the tunnel goes off to
GOAL = {'l': 128.0, 'r': 292.0, 'bar': 58.0, 'line': 118.0}
SPOT = (CX, 160.0)


def pk_field():
    Hh, Ww = px(FH), px(FW)
    y = (np.arange(Hh, dtype=np.float64)[:, None] + 0.5) / SC; x = (np.arange(Ww, dtype=np.float64)[None, :] + 0.5) / SC
    y = np.broadcast_to(y, (Hh, Ww)); x = np.broadcast_to(x, (Hh, Ww))
    rng = np.random.default_rng(44)
    can = np.zeros((Hh, Ww, 4), np.float32); can[..., 3] = 255
    # the tunnel: a cylinder round the line to the vanishing point; a point's angle round it and its depth
    dx, dy = x - VP[0], (y - VP[1]) * 1.25
    r = np.hypot(dx, dy) + 1e-3
    th = np.arctan2(dy, dx)
    depth = 900.0 / r                                        # (far: deep)
    u = (th + np.pi) * 30.0                                  # round the tunnel (bricks)
    v = depth * 8.0
    row = np.floor(v / 2.2); colk = np.floor((u + (row % 2) * 1.6) / 3.2)
    fu = (u + (row % 2) * 1.6) / 3.2 - colk; fv = v / 2.2 - row
    mortar = np.minimum(np.minimum(fu, 1 - fu) * 3.2, np.minimum(fv, 1 - fv) * 2.2)
    mw = np.clip(0.18 * depth / 10, 0.06, 0.6)
    joint = np.clip(1 - mortar / mw, 0, 1)
    hb = ((colk * 7919 + row * 104729) % 97) / 97.0
    brick = ramp_col(ramp('#3a1e18', '#5a2e22', '#7a4030', '#94563e'), np.clip(0.35 + 0.4 * hb + 0.1 * np.sin(u * 0.4), 0, 1))
    brick = brick * (1 - 0.65 * joint[..., None]) + hexc('#1e1612') * 0.65 * joint[..., None]
    fog = np.clip((depth - 6) / 28, 0, 1)                   # deep in: dark, a cold blue-green haze
    brick = brick * (1 - fog[..., None]) + hexc('#0a1214') * fog[..., None]
    slime = np.clip(1 - np.abs(th - np.pi / 2) / 0.9, 0, 1) ** 2 * 0.35          # damp streaks near the bottom
    brick = brick * (1 - slime[..., None]) + hexc('#2a3a2a') * slime[..., None]
    can[..., :3] = brick
    # the floor: a flat concrete landing from the goal line to us (y > line), its far edge a lip over the water beyond
    fl = y > GOAL['line'] - 6
    s = np.maximum((y - 30.0) / (SPOT[1] - 30.0), 0.05)
    fu2, fv2 = (x - CX) / s, 3000.0 / np.maximum(y - 30.0, 1)
    n1 = ndimage.gaussian_filter(rng.standard_normal((Hh, Ww)), 6) * 6 + ndimage.gaussian_filter(rng.standard_normal((Hh, Ww)), 1.2) * 0.6
    conc = ramp_col(ramp('#2a2c30', '#44474e', '#5e626a', '#7a7e86'), np.clip(0.45 + 0.07 * n1 + 0.12 * np.exp(-((x - CX) / 140) ** 2), 0, 1))
    slab = (np.abs(((fu2 / 34.0) % 1) - 0.5) > 0.485) | (np.abs(((fv2 / 9.0) % 1) - 0.5) > 0.47)
    conc = np.where(slab[..., None], conc * 0.75, conc)
    puddle = ndimage.gaussian_filter(rng.standard_normal((Hh, Ww)), 14) > 0.035
    conc = np.where((puddle & fl)[..., None], conc * 0.55 + hexc('#6a8a90') * 0.2, conc)
    ea = np.clip((y - (GOAL['line'] - 6)) * SC / 2, 0, 1)
    can[..., :3] = can[..., :3] * (1 - ea[..., None]) + conc * ea[..., None]
    # painted lines: the goal line, the goal area's box, the penalty spot (worn white paint)
    paint_ = np.zeros((Hh, Ww), np.float32)
    def line_(p0, p1, w):
        P = np.array([p0, p1], np.float64); m = np.zeros((Hh, Ww), np.uint8)
        cv2.polylines(m, [np.round((P + 0.5) * SC * 16).astype(np.int32).reshape(-1, 1, 2)], False, 255, max(1, int(w * SC)), cv2.LINE_AA, 4)
        return m.astype(np.float32) / 255
    paint_ = np.maximum(paint_, line_((40, GOAL['line']), (380, GOAL['line']), 1.0))
    for a, b in [((92, GOAL['line']), (70, 138)), ((328, GOAL['line']), (350, 138)), ((70, 138), (350, 138))]:
        paint_ = np.maximum(paint_, line_(a, b, 1.2))
    sp = ell(y, x, SPOT[0], SPOT[1] + 3, 4.2, 1.6); paint_ = np.maximum(paint_, art.smooth_mask(sp, 1.0))
    paint_ *= np.clip(0.6 + 0.4 * (ndimage.gaussian_filter(rng.standard_normal((Hh, Ww)), 2) > -0.4), 0, 1)
    can[..., :3] = can[..., :3] * (1 - 0.8 * paint_[..., None]) + hexc('#e8e6dc') * 0.8 * paint_[..., None]
    # the net: a diamond mesh in the goal's mouth, set a little back (the dark tunnel through it)
    gm = (x > GOAL['l']) & (x < GOAL['r']) & (y > GOAL['bar']) & (y < GOAL['line'])
    q1 = np.abs(((x + y) / 5.0) % 1 - 0.5); q2 = np.abs(((x - y) / 5.0) % 1 - 0.5)
    mesh = np.clip(1 - np.minimum(0.5 - q1, 0.5 - q2) / 0.07, 0, 1) * gm
    can[..., :3] = can[..., :3] * (1 - 0.18 * gm[..., None]) + hexc('#000000') * 0.18 * gm[..., None]
    can[..., :3] = can[..., :3] * (1 - 0.55 * mesh[..., None]) + hexc('#d8dcd8') * 0.55 * mesh[..., None]
    # the goal frame: white-painted pipes, round (lit from above-left), rust at the joints and the feet
    fr = np.zeros((Hh, Ww, 4), np.float32)
    def pipe(p0, p1, r):
        m = cap(y, x, p0, p1, r)
        sh, nn = dome_shade(m, soft=0.4)
        sp_ = paint(art.smooth_mask(m), ramp('#7a7c80', '#b8bcc0', '#e4e6e8', '#ffffff'), sh)
        highlight(sp_, m, nn, thresh=0.94, alpha=0.8)
        over(fr, sp_[..., :3], sp_[..., 3] / 255)
    pipe((GOAL['l'], GOAL['bar']), (GOAL['l'], GOAL['line']), 2.6); pipe((GOAL['r'], GOAL['bar']), (GOAL['r'], GOAL['line']), 2.6)
    pipe((GOAL['l'], GOAL['bar']), (GOAL['r'], GOAL['bar']), 2.6)
    for gx_, gy_ in [(GOAL['l'], GOAL['bar']), (GOAL['r'], GOAL['bar']), (GOAL['l'], GOAL['line'] - 1), (GOAL['r'], GOAL['line'] - 1)]:
        ellipse_soft(fr, gx_, gy_, 3.4, 3.4, '#8a4a22', a=150)
    fo = outline(fr, width=0.7); paste(can, fo, -1, -1)
    # the light from the manhole above: a soft cone onto the spot, motes in it, the bright round hole at the top
    cone = np.clip(1 - np.abs(x - CX - (y - 0) * 0.02) / (26 + y * 0.38), 0, 1) ** 1.6 * np.clip(1.15 - y / 190, 0, 1)
    can[..., :3] = can[..., :3] * (1 - 0.28 * cone[..., None]) + hexc('#fff6dc') * 0.28 * cone[..., None]
    pool = np.exp(-(((x - SPOT[0]) / 70) ** 2 + ((y - SPOT[1]) / 18) ** 2)) * 0.35
    can[..., :3] = can[..., :3] * (1 - pool[..., None]) + hexc('#fff0d0') * pool[..., None]
    for _ in range(60):
        mx_, my_ = CX + rng.uniform(-40, 40), rng.uniform(4, 150)
        if abs(mx_ - CX) > 26 + my_ * 0.38: continue
        disc(can, mx_, my_, rng.uniform(0.25, 0.6), '#fffbe8', a=int(rng.uniform(60, 160)))
    hole = np.zeros((Hh, Ww, 4), np.float32); ellipse_soft(hole, CX, -6, 30, 12, '#fffbea', a=255)
    hole = ndimage.gaussian_filter(hole, (2 * SC, 2 * SC, 0)); over(can, hole[..., :3], hole[..., 3] / 255 * 0.9)
    # the ladder's rungs on the wall up to the manhole, right of it
    for k in range(5):
        ry_ = 6 + k * 9.0
        stroke(can, [(CX + 40, ry_), (CX + 52, ry_ + 1.5)], 1.6, '#1a1210')
        stroke(can, [(CX + 40, ry_ - 0.5), (CX + 52, ry_ + 1.0)], 0.9, '#8a7a6a')
    vig = np.clip(((x - CX) / 230) ** 2 + ((y - 90) / 120) ** 2 - 0.25, 0, 1)
    can[..., :3] *= (1 - 0.55 * vig[..., None])
    return can


# ---------------------------------------------------------------- the slot machine: a porcelain toilet tank
SLW, SLH = 232, 136
WIN = [(-62, 0), (0, 0), (62, 0)]                    # the reels' windows: their middles from the tank's middle (x), y below
WINW, WINH = 50, 56


def slot_machine():
    """the cabinet (the reel windows cut clear), and where things are on it"""
    W_, H_ = SLW, SLH
    y, x = grid(H_, W_)
    cx = W_ / 2 - 0.5
    top = 24.0                                                  # the marquee above it
    body = (np.abs(x - cx) <= W_ / 2 - 8) & (y >= top) & (y <= H_ - 6)
    body = ndimage.binary_closing(body) & (((np.maximum(np.abs(x - cx) - (W_ / 2 - 8 - 10), 0)) ** 2 + (np.maximum(np.maximum(top + 10 - y, y - (H_ - 6 - 10)), 0)) ** 2) <= 100)
    lid = (np.abs(x - cx) <= W_ / 2 - 3) & (y >= top - 7) & (y <= top + 6)
    lid &= ((np.maximum(np.abs(x - cx) - (W_ / 2 - 3 - 6), 0)) ** 2 + (np.maximum(np.maximum(top - 1 - y, y - (top + 0)), 0)) ** 2) <= 36
    POR = ('#5a6a78', '#94a6b4', '#c8d6e0', '#eef4f8', '#ffffff')
    L = [part(body, POR, soft=3.0, gloss=0.5), part(lid, POR, soft=1.2, gloss=0.8)]
    # the marquee: a rounded red sign with a gold rim
    mq = (np.abs(x - cx) <= 70) & (y >= 1) & (y <= top - 6)
    mq &= ((np.maximum(np.abs(x - cx) - 64, 0)) ** 2 + (np.maximum(np.maximum(7 - y, y - (top - 12)), 0)) ** 2) <= 36
    L.append(part(mq, ('#4a0a0e', '#8a1218', '#c8202a', '#f04a50', '#ffa0a0'), soft=1.0, gloss=0.6))
    can = stack(L, W_, H_)
    # gold trim along the lid's edge and round the marquee; the reel windows' chrome bezels (then cut through)
    stroke(can, [(cx - W_ / 2 + 10, top + 7.5), (cx + W_ / 2 - 10, top + 7.5)], 1.6, '#d8a020')
    stroke(can, [(cx - W_ / 2 + 10, top + 7.1), (cx + W_ / 2 - 10, top + 7.1)], 0.7, '#ffe48a')
    wy = top + 14 + WINH / 2                                  # the windows' middle line
    win = np.zeros(y.shape, bool)
    for wx, _ in WIN:
        bz = (np.abs(x - (cx + wx)) <= WINW / 2 + 3.5) & (np.abs(y - wy) <= WINH / 2 + 3.5)
        sh = np.clip(0.5 - 0.5 * (y - wy) / (WINH / 2 + 3.5), 0, 1)
        col = ramp_col(ramp('#3a3e44', '#7a8088', '#c8ccd2', '#f4f6f8'), sh)
        k = art.smooth_mask(bz, 0.8).astype(np.float32)
        over(can, col, k)
        win |= (np.abs(x - (cx + wx)) <= WINW / 2) & (np.abs(y - wy) <= WINH / 2)
    # the panel under the windows for the stop buttons (darker inset)
    pn = (np.abs(x - cx) <= 92) & (np.abs(y - (wy + WINH / 2 + 15)) <= 9)
    over(can, np.broadcast_to(hexc('#9aa8b4'), y.shape + (3,)), art.smooth_mask(pn, 1.0).astype(np.float32) * 0.6)
    for wx, _ in WIN:                                        # a dark line round each window's opening
        x0_, x1_, y0_, y1_ = cx + wx - WINW / 2 - 0.4, cx + wx + WINW / 2 + 0.4, wy - WINH / 2 - 0.4, wy + WINH / 2 + 0.4
        stroke(can, [(x0_, y0_), (x1_, y0_), (x1_, y1_), (x0_, y1_), (x0_, y0_)], 1.2, '#1a0a14')
    can = outline(can, width=0.6)
    w = art.smooth_mask(win, 0.6)
    pad = SC                                                   # (outline() grew it by a unit)
    can[pad:-pad, pad:-pad, 3] *= (1 - w)
    meta = {'win': [[round(cx + 1 + wx, 2), round(wy + 1, 2)] for wx, _ in WIN], 'winw': WINW, 'winh': WINH,
            'marquee': [round(cx + 1, 2), round((1 + top - 6) / 2 + 1, 2)], 'stop_y': round(wy + WINH / 2 + 15 + 1, 2),
            'lever': [round(cx + W_ / 2 - 3 + 1, 2), round(top + 16 + 1, 2)], 'bulbs': []}
    for k in range(13):                                        # bulbs along the marquee's rim (lit in the game)
        meta['bulbs'].append([round(cx + 1 - 62 + k * 124 / 12, 2), round(3.2 + 1, 2)])
    for k in range(13): meta['bulbs'].append([round(cx + 1 - 62 + k * 124 / 12, 2), round(top - 6.6 + 1, 2)])
    return can, meta


def lever(pulled):
    """the flush lever, pivoting at its left end (on the tank's right side): up, or pulled down"""
    W_, H_ = 34, 30
    y, x = grid(H_, W_)
    piv = (5.0, 10.0)
    ang = 0.62 if pulled else -0.12
    end = (piv[0] + 24 * np.cos(ang), piv[1] + 24 * np.sin(ang))
    arm = cap(y, x, piv, end, 2.2, 1.6)
    knob = ell(y, x, end[0], end[1], 4.0, 3.2, ang)
    base = ell(y, x, piv[0], piv[1], 4.6, 4.6)
    CH = ('#3a3e46', '#6a707a', '#a8aeb8', '#e4e8ee', '#ffffff')
    can = stack([part(arm, CH, soft=0.5, gloss=0.9), part(base, CH, soft=0.8, gloss=0.9), part(knob, CH, soft=0.8, gloss=1.0)], W_, H_)
    return outline(can, width=0.5), {'piv': [piv[0] + 1, piv[1] + 1]}


def symbol(k):
    """the six symbols: 0 golden poop (jackpot), 1 rubber duck, 2 plunger, 3 toilet roll, 4 soap, 5 water drop"""
    W_ = 40
    y, x = grid(W_, W_)
    c = (W_ - 1) / 2
    L = []
    if k == 0:                                               # a swirl of three tiers and a tip, gold
        GOLD = ('#6a4204', '#a8700a', '#e0a81c', '#ffd85a', '#fff6c0')
        for cy_, rx, ry in [(29, 15, 6.5), (21.5, 11.5, 5.8), (15, 8, 5.0)]:
            L.append(part(ell(y, x, c, cy_, rx, ry), GOLD, soft=1.0, gloss=0.9))
        L.append(part(cap(y, x, (c - 1, 11), (c + 3, 4.5), 3.4, 1.4), GOLD, soft=0.6, gloss=0.9))
        can = stack(L, W_, W_)
        for sx_, sy_, sr_ in [(9, 8, 2.6), (32, 12, 2.0), (31, 31, 1.6)]:      # sparkles
            for a in (0, np.pi / 2):
                stroke(can, [(sx_ - np.cos(a) * sr_ * 1.6, sy_ - np.sin(a) * sr_ * 1.6), (sx_ + np.cos(a) * sr_ * 1.6, sy_ + np.sin(a) * sr_ * 1.6)], 0.6, '#ffffff')
        for side in (-1, 1):                                  # a happy face
            disc(can, c + side * 4.2, 21, 1.6, '#3a2004'); disc(can, c + side * 4.2 - 0.5, 20.4, 0.55, '#ffffff')
        stroke(can, [(c - 3, 25), (c, 26.6), (c + 3, 25)], 0.7, '#3a2004')
    elif k == 1:                                             # a rubber duck, side on, facing left
        YEL = ('#7a5a00', '#c89a00', '#f4cc1a', '#ffe868', '#fffad0')
        L.append(part(ell(y, x, c + 3, 26, 14, 9.5), YEL, soft=1.4, gloss=0.6))
        L.append(part(ell(y, x, c + 13, 20, 4.5, 6, -0.6), YEL, soft=0.8, gloss=0.3))          # the tail, up
        L.append(part(ell(y, x, c - 6, 13, 8.5, 8), YEL, soft=1.2, gloss=0.7))
        L.append(part(ell(y, x, c - 15.5, 15, 4.6, 2.6, 0.1), ('#7a2a00', '#c85a08', '#f88a1a', '#ffbc5a', '#ffe8c0'), soft=0.6, gloss=0.6))
        can = stack(L, W_, W_)
        disc(can, c - 8, 11.5, 1.6, '#1a0a14'); disc(can, c - 8.5, 11, 0.55, '#ffffff')
        stroke(can, [(c + 1, 25), (c + 6, 28), (c + 11, 25)], 0.8, '#c89a00')                     # the wing
    elif k == 2:                                             # a plunger: a red rubber cup on a wooden handle
        L.append(part(cap(y, x, (c, 4), (c, 24), 2.3), ('#5a3010', '#8a5420', '#c08040', '#e8b070', '#fff0d0'), soft=0.5, gloss=0.6))
        cup = ell(y, x, c, 30, 13, 8.5) & (y <= 33)
        L.append(part(cup, ('#5a0810', '#9a1420', '#d82a36', '#ff6a70', '#ffc0c0'), soft=1.4, gloss=0.8))
        L.append(part(ell(y, x, c, 33, 13.2, 2.4), ('#4a0610', '#7a1018', '#a81c26', '#d84a50', '#ff9a9a'), soft=0.5, gloss=0.3))
        can = stack(L, W_, W_)
    elif k == 3:                                             # a toilet roll: a fat white cylinder, the tube's hole, a sheet hanging
        WH = ('#7a8088', '#b8bec6', '#e4e8ee', '#fbfcfe', '#ffffff')
        L.append(part((np.abs(x - c) <= 12) & (y >= 9) & (y <= 31), WH, soft=2.0, gloss=0.3))
        L.append(part(ell(y, x, c, 31, 12, 4), WH, soft=0.8, gloss=0.2))
        L.append(part(ell(y, x, c, 9, 12, 4), WH, soft=0.8, gloss=0.6))
        L.append(part((x >= c + 5) & (x <= c + 15) & (y >= 22) & (y <= 37), WH, soft=0.6, gloss=0.2))     # the sheet hanging off
        can = stack(L, W_, W_)
        ellipse_soft(can, c, 9, 4.5, 1.6, '#a0886a'); ellipse_soft(can, c, 9.3, 3.4, 1.0, '#5a4a3a')
        for yy in (27, 32): stroke(can, [(c + 6, yy), (c + 14, yy)], 0.4, '#b8bec6')                    # perforations
    elif k == 4:                                             # a bar of soap with bubbles
        sp = (np.abs(x - c) <= 14) & (np.abs(y - 25) <= 8)
        sp &= ((np.maximum(np.abs(x - c) - 9, 0)) ** 2 + (np.maximum(np.abs(y - 25) - 3, 0)) ** 2) <= 25
        L.append(part(sp, ('#7a2a50', '#b84a80', '#ec7ab0', '#ffb0d4', '#fff0f8'), soft=1.6, gloss=0.9))
        can = stack(L, W_, W_)
        for bx_, by_, br in [(12, 10, 4.5), (22, 7, 3.2), (29, 12, 2.4), (17, 16, 2.0)]:
            disc(can, bx_, by_, br + 0.4, '#5a8aa8', a=150); disc(can, bx_, by_, br, '#e8f8ff', a=120)
            disc(can, bx_ - br * 0.35, by_ - br * 0.35, br * 0.3, '#ffffff', a=230)
    else:                                                     # a water drop
        d = ell(y, x, c, 25, 11, 11) | (cap(y, x, (c, 5), (c, 22), 0.6, 9.8) & (y < 25))
        L.append(part(d, ('#0a3a6a', '#1a6ab4', '#3aa0ec', '#90d4ff', '#e8f8ff'), soft=1.6, gloss=1.0))
        can = stack(L, W_, W_)
    return outline(can, width=0.6), {}


def coin():
    W_ = 14
    y, x = grid(W_, W_); c = (W_ - 1) / 2
    m = np.hypot(x - c, y - c) <= 6
    sh, n = dome_shade(m, soft=0.8)
    spr = paint(art.smooth_mask(m), ramp('#6a4204', '#b07a0c', '#e8b424', '#ffe070', '#fffad8'), sh)
    highlight(spr, m, n, thresh=0.94, alpha=0.9)
    inner = np.abs(np.hypot(x - c, y - c) - 4.2) <= 0.4
    spr[inner, :3] = spr[inner, :3] * 0.7
    return outline(spr, width=0.5), {}


def atlas(sprs):
    fw = sum(s.shape[1] for s, _ in sprs) + 4 * len(sprs); fh = max(s.shape[0] for s, _ in sprs)
    A = np.zeros((fh, fw, 4), np.float32); rects = []; x0 = 0
    for s, _ in sprs:
        A[:s.shape[0], x0:x0 + s.shape[1]] = s; rects.append([x0, 0, s.shape[1], s.shape[0]]); x0 += s.shape[1] + 4
    return A, rects


def save(arr, path, lossless=True, q=88):
    im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), 'RGBA')
    if lossless: im.save(path, lossless=True, method=6)
    else: im.convert('RGB').save(path, quality=q, method=6)


if __name__ == '__main__':
    os.makedirs(PRE, exist_ok=True)
    what = sys.argv[1:] or ['pk', 'sl']
    m = json.load(open(f'{OUT}/manifest.json'))
    if 'pk' in what:
        f = pk_field(); save(f, f'{OUT}/pk_field.webp', lossless=False)
        Image.fromarray(np.clip(f, 0, 255).astype(np.uint8), 'RGBA').convert('RGB').resize((px(FW) // 2, px(FH) // 2), Image.LANCZOS).save(f'{PRE}/pk_field.png')
        names = ['pk_ball', 'pk_k0', 'pk_k1', 'pk_k2']; sprs = [ball(), rat(0), rat(1), rat(2)]
        A, rects = atlas(sprs); save(A, f'{OUT}/pk.webp'); save(A, f'{PRE}/pk_sprites.png')
        m['sprites']['pk_field'] = {'f': 'pk_field.webp', 'r': [0, 0, px(FW), px(FH)], 'w': FW, 'h': FH}
        for nm, (s, meta), r in zip(names, sprs, rects):
            m['sprites'][nm] = {'f': 'pk.webp', 'r': r, 'w': round(s.shape[1] / SC, 3), 'h': round(s.shape[0] / SC, 3), **meta}
        m['pk'] = {'goal': GOAL, 'spot': list(SPOT), 'vp': list(VP)}
    if 'sl' in what:
        names = ['sl_machine', 'sl_lever0', 'sl_lever1', 'sl_coin'] + [f'sl_s{k}' for k in range(6)]
        mach = slot_machine()
        sprs = [mach, lever(False), lever(True), coin()] + [symbol(k) for k in range(6)]
        A, rects = atlas(sprs); save(A, f'{OUT}/sl.webp'); save(A, f'{PRE}/sl_sprites.png')
        for nm, (s, meta), r in zip(names, sprs, rects):
            m['sprites'][nm] = {'f': 'sl.webp', 'r': r, 'w': round(s.shape[1] / SC, 3), 'h': round(s.shape[0] / SC, 3), **meta}
        m['sl'] = mach[1]
    json.dump(m, open(f'{OUT}/manifest.json', 'w'), separators=(',', ':'))
    for fn in ('pk_field.webp', 'pk.webp', 'sl.webp'):
        if os.path.exists(f'{OUT}/{fn}'): print(fn, os.path.getsize(f'{OUT}/{fn}'))
