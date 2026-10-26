# The five preview screens. usage: python3 make_previews.py [name ...]
import sys
import numpy as np
from art import W, H, canvas, ramp, hexc, vgrad, paste, fill_rect, ellipse_mask, outline, paint, dome_shade, load, flip
import sprites as S
from scenes import (GY, band, sine_ridges, rbc, neuron, villus, place, char, puff, speedlines, row, arc, hud, finish, cells, haze)

OUT = '/home/claude/pixel/out/preview_{}.png'


def vessel():
    """혈관 (대동맥): red cells drifting behind, a fatty plaque to jump, a virus to slide under, oxygen to collect"""
    cv = canvas()
    vgrad(cv, ramp('#2a0610', '#3e0a18', '#561022', '#6a1628', '#561022', '#3e0a18'))
    R = np.random.RandomState(4)
    # the far wall: long lining cells, faint
    cb, _ = cells(W, H, 90, 11, border=1.4)
    lin = (cb > 0.75) & (R.uniform(size=(H, W)) < 0.9)
    cv[lin, :3] = cv[lin, :3] * 0.75 + hexc('#6a1828') * 0.25
    # openings of side branches on the far wall: dark holes with a lit lower rim
    for (bx, by, bw, bh) in [(150, 52, 46, 26), (352, 92, 34, 20)]:
        hm = ellipse_mask(bw, bh)
        hs = np.zeros((bh, bw, 4), np.float32)
        yy, xx = np.mgrid[0:bh, 0:bw]
        t = np.clip(yy / bh, 0, 1)
        hs[hm, :3] = (hexc('#16030a') * (1 - t[..., None] * 0.4) + hexc('#3a0814') * (t[..., None] * 0.4))[hm]
        hs[hm, 3] = 255
        rim = hm & ~np.roll(hm, -2, axis=0)
        hs[rim & (yy > bh / 2), :3] = hexc('#8a2034')
        paste(cv, outline(hs, '#12020a'), bx - bw / 2, by - bh / 2, 0.9)
    # far red cells (dim), then near ones
    for k in range(26):
        d = int(R.uniform(7, 12)); s = rbc(d, R.uniform(0.35, 1.0), dark=True)
        paste(cv, s, R.uniform(-5, W), R.uniform(18, GY - 14))
    for k in range(11):
        d = int(R.uniform(13, 19)); s = rbc(d, R.uniform(0.3, 1.0))
        paste(cv, s, R.uniform(-5, W), R.uniform(22, GY - 26), 0.92)
    haze(cv, '#3a0a16', 0.22)
    band(cv, 0, 16, ramp('#4a0816', '#7a1024', '#b01e34', '#e0485a', '#ff7a88', n=7), top_edge=False, seed=3, bumps=1.0, out='#1a0308', drips=False)
    band(cv, GY, H, ramp('#3a0610', '#6e1024', '#a81c34', '#d83a50', '#ff6b7a', '#ff9aa4', n=8), top_edge=True, seed=5, bumps=1.0, out='#1a0308')
    speedlines(cv, '#ff8a96', 12, 2, 45)
    # play: oxygen in a row, an arc over the plaque; the virus floats at slide height
    o2 = S.bubble_o2()
    row(cv, o2, 116, GY - 12, 4, 15)
    plaque = S.lump(30, 18, seed=2)
    place(cv, plaque, 228, GY + 2)
    arc(cv, o2, 196, 262, GY - 16, 46, 6)
    vir = S.virus(18)
    paste(cv, vir, 318 - vir.shape[1] / 2, GY - 38 - vir.shape[0] / 2)
    row(cv, o2, 296, GY - 12, 3, 15)
    fe = S.hex_fe(); paste(cv, fe, 290, GY - 74)
    char('ladybug', 78, GY + 1, cv)
    puff(cv, 52, GY - 3, '#ffb0b8', 3, 1)
    hud(cv, hp=0.78, score='4,260', progress=0.47, theme='#ff5a7a')
    return finish(cv, '하행대동맥', 'Descending aorta', OUT.format('vessel'))


def stomach():
    """위: folds (rugae) across the back wall, acid bubbling up, acid crystals to jump, a bacterium to slide under"""
    cv = canvas()
    vgrad(cv, ramp('#2a0614', '#3e0a1e', '#541028', '#661630', '#541028'))
    R = np.random.RandomState(7)
    # rugae: wavy folds, far ones darker
    for k, (yb, amp, fr, th, cols) in enumerate([
            (34, 5, 0.035, 10, ('#4a0e22', '#5e1430', '#701a3a')),
            (62, 6, 0.03, 13, ('#5a1228', '#7a1c38', '#94264a', '#a83256')),
            (96, 7, 0.026, 16, ('#6a162e', '#8e2440', '#b0324e', '#c84862', '#e06a80')),
            (128, 6, 0.032, 14, ('#7a1a34', '#a02c48', '#c43e5a', '#e05a72', '#ff8a9c'))]):
        sine_ridges(cv, yb, amp, fr, th, ramp(*cols, n=6), '#200610', phase=k * 1.7)
    # gastric pits: little dark dots dotted over the folds
    for k in range(260):
        x, y = int(R.uniform(0, W)), int(R.uniform(20, GY - 4))
        if cv[y, x, 0] > 120:
            fill_rect(cv, x, y, x + 1, y + 1, '#5a1028')
    # acid bubbles rising
    for k in range(22):
        r = int(R.uniform(2, 5)); m_ = ellipse_mask(2 * r + 1, 2 * r + 1); ring = m_ & ~ellipse_mask(2 * r + 1, 2 * r + 1, r, r, r - 1.2, r - 1.2)
        b = np.zeros(m_.shape + (4,), np.float32); b[ring, :3] = hexc('#d8ff7a'); b[ring, 3] = 170; b[r // 2, r // 2 + 1, :3] = 255; b[r // 2, r // 2 + 1, 3] = 220
        paste(cv, b, R.uniform(0, W), R.uniform(30, GY - 8))
    haze(cv, '#3e0a1e', 0.25)
    band(cv, 0, 15, ramp('#4a0a1e', '#7a1430', '#a8243e', '#d0405a', '#f06a80', n=7), top_edge=False, seed=13, bumps=1.4, out='#1e040c', drips=True)
    band(cv, GY, H, ramp('#4a0c1e', '#7e1832', '#b02a48', '#d84a66', '#f47a90', '#ffa8b8', n=8), top_edge=True, seed=15, bumps=1.3, out='#1e040c')
    # an acid puddle on the ground (glowing)
    for x in range(250, 300):
        fill_rect(cv, x, GY + 1, x + 1, GY + 3, '#b8e04a' if (x % 7) else '#eaff9a')
    speedlines(cv, '#ff9ab0', 10, 3, 40)
    c = S.coin_c()
    row(cv, c, 120, GY - 12, 4, 15)
    cr = S.crystals()
    place(cv, cr, 214, GY + 2)
    arc(cv, c, 188, 242, GY - 16, 42, 5)
    bac = S.bacterium()
    paste(cv, bac, 322 - bac.shape[1] / 2, GY - 34 - bac.shape[0] / 2)
    row(cv, c, 300, GY - 9, 4, 15)
    fib = S.broccoli(); paste(cv, fib, 262, GY - 70)
    char('tardigrade', 84, GY + 1, cv)
    puff(cv, 58, GY - 3, '#ffc0cc', 3, 2)
    hud(cv, hp=0.92, score='1,280', progress=0.04, theme='#ff6a8a')
    return finish(cv, '위', 'Stomach', OUT.format('stomach'))


def intestine():
    """소장: forests of villi behind, bacteria on the floor, the character mid-jump"""
    cv = canvas()
    vgrad(cv, ramp('#2e0a14', '#45101e', '#5c1828', '#702030', '#5c1828'))
    R = np.random.RandomState(21)
    # far villi (dim) from floor and ceiling, then near ones
    for layer, (n, hmin, hmax, w, cols, out, a) in enumerate([
            (30, 40, 80, 9, ('#4a1420', '#5e1c2a', '#702434'), '#24060e', 1.0),
            (14, 46, 86, 13, ('#7a2434', '#a03a4c', '#c45468', '#e07888', '#f0a0aa'), '#2a0810', 1.0)]):
        xs = np.sort(R.uniform(-10, W + 10, n))
        for x in xs:
            hh = int(R.uniform(hmin, hmax))
            if R.uniform() < 0.5 or layer == 1:
                paste(cv, villus(hh, w, ramp(*cols, n=6), out, int(abs(x) * 7) + 1), x, GY - hh + 6)
            else:
                paste(cv, villus(int(hh * 0.7), w, ramp(*cols, n=6), out, int(abs(x) * 7) + 1, hang=True), x, 6)
    haze(cv, '#45101e', 0.38)
    band(cv, 0, 13, ramp('#4a0e1c', '#7a1a2c', '#a82e40', '#d04e5e', '#f07a86', n=7), top_edge=False, seed=23, bumps=1.2, out='#20060c', drips=True)
    band(cv, GY, H, ramp('#5a1a20', '#8e2e34', '#c04a4c', '#e47066', '#ff9c88', '#ffc6b0', n=8), top_edge=True, seed=25, bumps=1.2, out='#22080a')
    speedlines(cv, '#ffb0a0', 10, 5, 40)
    c = S.coin_c()
    bugs = S.lump(26, 14, body=('#1a4a10', '#2f7a20', '#4fa83a', '#7fd65a', '#b0f08a'), out='#0a1e06', seed=5)
    place(cv, bugs, 170, GY + 2)
    arc(cv, c, 120, 214, GY - 16, 50, 7)
    vir = S.virus(16)
    place(cv, vir, 300, GY + 4)
    row(cv, c, 240, GY - 12, 3, 15)
    arc(cv, c, 278, 324, GY - 16, 40, 4)
    fib = S.broccoli(); paste(cv, fib, 352, GY - 60)
    char('lacto', 132, GY + 1, cv, jump=40)
    puff(cv, 106, GY - 3, '#ffd0c0', 3, 4)
    hud(cv, hp=0.64, score='2,940', progress=0.12, theme='#ff8a7a', pop=(122, GY - 70, '+10'))
    return finish(cv, '공장', 'Jejunum', OUT.format('intestine'))


def heart():
    """심장 (좌심실): muscle ridges and the white cords of the valves; a clot to jump, the character sliding"""
    cv = canvas()
    vgrad(cv, ramp('#1e040c', '#300814', '#440c1e', '#561226', '#440c1e'))
    R = np.random.RandomState(31)
    # trabeculae: thick muscle ridges slanting across the back wall, striped
    for k in range(9):
        x0 = R.uniform(-40, W); w = R.uniform(14, 26); sl = R.uniform(-0.5, 0.5)
        hh = GY - 6
        y, x = np.mgrid[0:hh, 0:int(w + abs(sl) * hh + 4)]
        cxl = (w / 2 + (abs(sl) * hh if sl < 0 else 0)) + sl * y
        m = np.abs(x - cxl) <= w / 2 * (0.75 + 0.25 * np.sin(y * 0.05 + k))
        t = (x - cxl) / (w / 2)
        sh = np.clip(0.75 - 0.45 * t - 0.15 * (np.sin(y * 0.9 + x * 0.3) > 0.6), 0, 1)
        col = ramp('#3a0814', '#561020', '#721a2c', '#8e2638', n=5) if k % 2 else ramp('#2e0610', '#460c1a', '#5e1426', n=4)
        spr = outline(paint(m, col, sh), '#16020a')
        paste(cv, spr, x0, 10)
    # chordae tendineae: white cords from the top down to the valve flap and the papillary cones on the floor
    for (xa, xb) in [(60, 120), (150, 120), (240, 300), (330, 300)]:
        for i in range(0, 101):
            t = i / 100; x = xa + (xb - xa) * t; y = 14 + (GY - 30 - 14) * t + 6 * np.sin(t * np.pi)
            fill_rect(cv, int(x), int(y), int(x) + 1, int(y) + 1, '#f4dcc8' if i % 9 else '#ffffff')
    for xc in (120, 300):
        cone = np.zeros((30, 24), bool); y, x = np.mgrid[0:30, 0:24]; cone |= np.abs(x - 11.5) <= 2 + y * 0.33
        sp, _ = S.blob(cone, ramp('#5a0e1e', '#8a1e30', '#b83246', '#e0566a', n=6), '#16020a', soft=1.0)
        paste(cv, sp, xc - 13, GY - 30)
    haze(cv, '#300814', 0.2)
    band(cv, 0, 12, ramp('#3a0612', '#6a0e22', '#9a1c34', '#c8344c', '#e8586c', n=7), top_edge=False, seed=33, bumps=1.0, out='#16020a')
    band(cv, GY, H, ramp('#3a0612', '#6a1024', '#9e2036', '#cc3a50', '#ee6274', '#ff96a2', n=8), top_edge=True, seed=35, bumps=1.0, out='#16020a')
    # muscle stripes on the floor band
    for x in range(0, W, 5):
        for y in range(GY + 6, H, 1):
            if (x + y) % 5 == 0 and cv[y, x, 0] > 60:
                cv[y, x, :3] = cv[y, x, :3] * 0.82
    speedlines(cv, '#ff8a9a', 10, 7, 40)
    o2 = S.bubble_o2()
    vir = S.virus(18)
    paste(cv, vir, 150 - vir.shape[1] / 2, GY - 36 - vir.shape[0] / 2)
    row(cv, o2, 136, GY - 8, 3, 13)
    cl = S.clot(26, 20, seed=6)
    place(cv, cl, 248, GY + 2)
    arc(cv, o2, 222, 276, GY - 16, 46, 5)
    row(cv, o2, 306, GY - 12, 3, 15)
    heal = S.heal_cap(); paste(cv, heal, 336, GY - 70)
    char('sub', 104, GY + 1, cv, squash=0.78)
    puff(cv, 74, GY - 2, '#ffb0b8', 3, 6)
    hud(cv, hp=0.41, score='6,010', progress=0.58, theme='#ff4a6a')
    return finish(cv, '좌심실', 'Left ventricle', OUT.format('heart'))


def brain():
    """뇌: a forest of glowing nerve cells at night-blue, sparks to slide under, plaques to jump"""
    cv = canvas()
    vgrad(cv, ramp('#0a0618', '#120c28', '#1c1238', '#261848', '#1c1238'))
    R = np.random.RandomState(41)
    far = ('#2a1c50', '#36245e', '#42306c', '#4e3a7a', '#5a4688', '#1a1036')
    for k in range(9):
        neuron(cv, R.uniform(0, W), R.uniform(30, GY - 20), int(R.uniform(5, 8)), R, far, glow=False)
    near = ('#6a3aa8', '#9a62d8', '#c08cff', '#e8ccff', '#7ff0ff', '#1e0a3a')
    for k in range(6):
        neuron(cv, R.uniform(10, W - 10), R.uniform(36, GY - 30), int(R.uniform(9, 12)), R, near, glow=True)
    # floating motes
    for k in range(40):
        x, y = int(R.uniform(0, W)), int(R.uniform(10, GY - 4))
        fill_rect(cv, x, y, x + 1, y + 1, '#9ae8ff' if k % 3 else '#ffffff')
    haze(cv, '#120c28', 0.12)
    band(cv, GY, H, ramp('#241650', '#3a2878', '#5a40a8', '#7e62cc', '#a688e8', '#d0bcff', n=8), top_edge=True, seed=45, bumps=1.6, out='#0c0620')
    speedlines(cv, '#a890ff', 10, 9, 40)
    o2 = S.bubble_o2()
    row(cv, o2, 112, GY - 12, 3, 15)
    am = S.crystals(colors=('#6a2a00', '#c05a00', '#ff9a2a', '#ffd080', '#ffffff'), out='#200a00', tall=True)
    place(cv, am, 190, GY + 2)
    arc(cv, o2, 160, 222, GY - 16, 64, 6)
    sp = S.spark_orb(16)
    paste(cv, sp, 300 - sp.shape[1] / 2, GY - 38 - sp.shape[0] / 2)
    row(cv, o2, 280, GY - 10, 3, 15)
    om = S.omega_drop(); paste(cv, om, 214, GY - 92)
    mv = S.multi_vit(); paste(cv, mv, 344, GY - 70)
    char('jelly', 150, GY + 1, cv, jump=62)
    hud(cv, hp=0.55, score='9,870', progress=0.66, theme='#a070ff', pop=(140, GY - 112, '+30'))
    return finish(cv, '대뇌피질 피라미드세포', 'Cortical pyramidal neurons', OUT.format('brain'))


SCENES = {'stomach': stomach, 'intestine': intestine, 'vessel': vessel, 'heart': heart, 'brain': brain}

if __name__ == '__main__':
    names = sys.argv[1:] or list(SCENES)
    for n in names:
        SCENES[n]()
        print('made', n)
