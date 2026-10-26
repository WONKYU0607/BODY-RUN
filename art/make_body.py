# The five preview screens, built from real things of the body (wall layers in section, the lining of each lumen,
# real obstacles, no faces). usage: python3 make_body.py [name ...]
import sys
import numpy as np
from art import W, H, canvas, ramp, hexc, vgrad, paste, fill_rect, ellipse_mask, outline, paint
import sprites as S
import anatomy as A
from scenes import GY, place, char, puff, speedlines, row, arc, hud, finish, haze, rbc

OUT = '/home/claude/pixel/out/body_{}.png'


def particles(dst, n, cols, seed, y0=18, y1=GY - 6, a=200):
    R = np.random.RandomState(seed)
    for k in range(n):
        x, y = R.uniform(0, W), R.uniform(y0, y1)
        c = cols[k % len(cols)]
        A.dot(dst, x, y, c, a); A.dot(dst, x + 1, y, c, a // 2)


# ------------------------------------------------------------------ stomach
def stomach():
    cv = canvas()
    vgrad(cv, ramp('#2a0614', '#3a0a1c', '#4a0e24', '#3a0a1c'))
    A.rugae(cv, 12, GY + 4, 7, ramp('#4a0c20', '#6e1630', '#922240', '#b43452', '#d65068', '#f07e90', n=8), '#1e040c', '#3a0614')
    particles(cv, 40, ['#c89a60', '#e8c890', '#f0e0b0'], 3)              # food particles drifting
    haze(cv, '#3a0a1c', 0.3)
    stom = [(3, ramp('#5a1028', '#a02a48', '#d04a66', '#f07a90', n=6), 'pits'),            # mucosa (pits)
            (5, ramp('#4a0c20', '#8a2240', '#b83a58', '#de6a80', n=6), 'pits'),
            (2, ramp('#3a0818', '#6a1830', '#8a2440', n=4), 'smooth'),                       # muscularis mucosae
            (8, ramp('#9a6a70', '#c89aa0', '#e8c4c4', '#f8e0dc', n=6), 'loose'),              # submucosa
            (20, ramp('#3a0810', '#6e1420', '#962032', '#b83044', n=6), 'smooth')]            # muscle coat
    A.wall_band(cv, 0, 15, [(3, stom[0][1], 'pits'), (4, stom[1][1], 'pits'), (2, stom[2][1], 'smooth'), (4, stom[3][1], 'loose'), (10, stom[4][1], 'smooth')], top_edge=False, seed=13, bumps=1.3, out='#1e040c')
    A.wall_band(cv, GY, H, stom, top_edge=True, seed=15, bumps=1.3, out='#1e040c')
    speedlines(cv, '#ff9ab0', 9, 3, 36)
    c = S.coin_c()
    row(cv, c, 120, GY - 12, 4, 15)
    fb = A.food_bolus(seed=3)
    place(cv, fb, 214, GY + 2)
    arc(cv, c, 188, 242, GY - 16, 42, 5)
    fh = A.fold_hang(30, GY - 40 - 10)              # a fold bulging down from the ceiling, to slide under
    paste(cv, fh, 322 - fh.shape[1] / 2, 8)
    row(cv, c, 302, GY - 9, 4, 15)
    fib = S.broccoli(); paste(cv, fib, 262, GY - 70)
    char('tardigrade', 84, GY + 1, cv)
    puff(cv, 58, GY - 3, '#ffc0cc', 3, 2)
    hud(cv, hp=0.92, score='1,280', progress=0.04, theme='#ff6a8a')
    return finish(cv, '위', 'Stomach', OUT.format('stomach'))


# ------------------------------------------------------------------ jejunum
def jejunum_surface(dst, edge, y0, h, top_edge):
    """short villi standing on the cut floor (or hanging from the ceiling)"""
    R = np.random.RandomState(5 if top_edge else 6)
    x = -3
    while x < W:
        hh = int(R.uniform(5, 9)); ww = int(R.choice([6, 7]))
        v = A.villus_real(hh, ww, int(x + 40), hang=not top_edge)
        x += int(R.uniform(5, 8))
        if top_edge:
            paste(dst, v, x, y0 + edge[min(max(x, 0), W - 1)] - hh + 2)
        else:
            paste(dst, v, x, y0 + h - 1 - edge[min(max(x, 0), W - 1)] - 1)


def jejunum():
    cv = canvas()
    vgrad(cv, ramp('#2a0812', '#3a0c1a', '#4a1222', '#3a0c1a'))
    R = np.random.RandomState(21)
    # a big circular fold far behind, then rows of villi (far ones dim and small)
    fold = np.zeros((90, W), bool); y, x = np.mgrid[0:90, 0:W]
    fold |= ((x - 250) / 120.0) ** 2 + ((y - 95) / 70.0) ** 2 <= 1
    fs = paint(fold, ramp('#4a1222', '#5a1a2a', '#6a2232', n=3), np.clip(0.9 - y / 120.0, 0, 1))
    paste(cv, outline(fs, '#2a0810'), -1, GY - 90)
    for layer, (n, hmin, hmax, w, dim) in enumerate([(46, 26, 50, 7, 0.62), (30, 34, 66, 9, 0.38), (18, 44, 80, 11, 0.12)]):
        xs = np.sort(R.uniform(-8, W + 8, n))
        for xx in xs:
            hh = int(R.uniform(hmin, hmax))
            hang = R.uniform() < 0.3
            v = A.villus_real(hh if not hang else int(hh * 0.6), w, int(abs(xx) * 13 + layer * 101 + 1), hang=hang, dim=dim)
            paste(cv, v, xx, (GY - hh + 4) if not hang else 8)
    particles(cv, 30, ['#e8c070', '#f4dca0'], 8)                            # chyme
    haze(cv, '#3a0c1a', 0.3)
    jej = [(8, ramp('#5a1424', '#9a2e40', '#c8505c', '#e8787e', n=6), 'crypts'),
           (2, ramp('#3a0a18', '#6a1a2a', '#8a2a3a', n=4), 'smooth'),
           (7, ramp('#9a6a6a', '#c89a98', '#e8c4bc', '#f8e0d8', n=6), 'loose'),
           (20, ramp('#3a0a10', '#6e1820', '#962832', '#b83a44', n=6), 'smooth')]
    A.wall_band(cv, 0, 13, [(6, jej[0][1], 'crypts'), (2, jej[1][1], 'smooth'), (3, jej[2][1], 'loose'), (10, jej[3][1], 'smooth')], top_edge=False, seed=23, bumps=1.0, out='#20060c')
    A.wall_band(cv, GY, H, jej, top_edge=True, seed=25, bumps=1.0, out='#22080a', surface=jejunum_surface)
    speedlines(cv, '#ffb0a0', 9, 5, 36)
    c = S.coin_c()
    fat = A.chyme_fat(seed=4)
    place(cv, fat, 168, GY + 2)
    arc(cv, c, 120, 214, GY - 16, 50, 7)
    pl = A.plica(46, 32, seed=7)
    place(cv, pl, 290, GY + 3)
    arc(cv, c, 250, 330, GY - 20, 84, 7)
    ec = A.e_coli()
    paste(cv, ec, 348 - ec.shape[1] / 2, GY - 38 - ec.shape[0] / 2)
    char('lacto', 132, GY + 1, cv, jump=40)
    puff(cv, 106, GY - 3, '#ffd0c0', 3, 4)
    hud(cv, hp=0.64, score='2,940', progress=0.12, theme='#ff8a7a', pop=(122, GY - 70, '+10'))
    return finish(cv, '공장', 'Jejunum', OUT.format('jejunum'))


# ------------------------------------------------------------------ artery
def aorta():
    cv = canvas()
    vgrad(cv, ramp('#2a0610', '#3e0a18', '#4e0e20', '#3e0a18'))
    A.endothelium(cv, 12, GY + 2, 9, ramp('#5a1424', '#6e1a2c', '#822234', n=3), '#3a0a18')
    # the opening of a side branch on the far wall
    bw, bh = 48, 28
    hm = ellipse_mask(bw, bh); yy, xx = np.mgrid[0:bh, 0:bw]
    hs = np.zeros((bh, bw, 4), np.float32); hs[hm, :3] = hexc('#14030a'); hs[hm, 3] = 255
    lip = hm & ~ellipse_mask(bw, bh, bw / 2 - 0.5, bh / 2 + 1.5, bw / 2 - 2, bh / 2 - 2)
    hs[lip, :3] = hexc('#9a2a3e')
    paste(cv, outline(hs, '#12020a'), 150, 40)
    R = np.random.RandomState(4)
    for k in range(24):
        paste(cv, rbc(int(R.uniform(7, 11)), R.uniform(0.35, 1.0), dark=True), R.uniform(-5, W), R.uniform(16, GY - 12))
    for k in range(8):
        paste(cv, A.platelet(k), R.uniform(0, W), R.uniform(20, GY - 20))
    haze(cv, '#3e0a18', 0.25)
    for k in range(10):
        paste(cv, rbc(int(R.uniform(12, 17)), R.uniform(0.3, 1.0)), R.uniform(-5, W), R.uniform(22, GY - 30), 0.95)
    art = [(2, ramp('#c87a80', '#f0b0b0', '#ffe0dc', n=4), 'loose'),                       # intima
           (16, ramp('#6a1020', '#9a1c30', '#c43448', '#e0566a', n=6), 'elastic'),             # media
           (12, ramp('#8a6458', '#b88a7a', '#dcb4a0', '#f0d4c0', n=6), 'loose')]              # adventitia
    A.wall_band(cv, 0, 15, [(2, art[0][1], 'loose'), (8, art[1][1], 'elastic'), (6, art[2][1], 'loose')], top_edge=False, seed=3, bumps=0.8, out='#1a0308')
    A.wall_band(cv, GY, H, art, top_edge=True, seed=5, bumps=0.8, out='#1a0308')
    speedlines(cv, '#ff8a96', 12, 2, 40)
    o2 = S.bubble_o2()
    row(cv, o2, 116, GY - 12, 4, 15)
    ath = A.atheroma(36, 20, seed=2)
    place(cv, ath, 228, GY + 3)
    arc(cv, o2, 196, 262, GY - 16, 48, 6)
    ne = A.neutrophil(22, seed=3)
    paste(cv, ne, 322 - ne.shape[1] / 2, GY - 38 - ne.shape[0] / 2)
    row(cv, o2, 300, GY - 12, 3, 15)
    fe = S.hex_fe(); paste(cv, fe, 290, GY - 76)
    char('ladybug', 78, GY + 1, cv)
    puff(cv, 52, GY - 3, '#ffb0b8', 3, 1)
    hud(cv, hp=0.78, score='4,260', progress=0.47, theme='#ff5a7a')
    return finish(cv, '하행대동맥', 'Descending aorta', OUT.format('aorta'))


# ------------------------------------------------------------------ heart
def ventricle():
    cv = canvas()
    vgrad(cv, ramp('#1e040c', '#2e0814', '#3a0c1a', '#2e0814'))
    A.trabeculae(cv, 10, GY + 4, 31, ramp('#3a0814', '#561020', '#721a2c', '#902638', '#ae3a4a', n=7), '#14020a')
    # papillary muscles far behind, cords up to the valve
    for xc in (96, 300):
        p = A.papillary(34, 22); paste(cv, p, xc - 12, GY - 34)
    for (xa, xb) in [(270, 300), (330, 300)]:
        pts = [(xa + (xb - xa) * t, 18 + (GY - 52) * t + 5 * np.sin(t * np.pi)) for t in np.linspace(0, 1, 60)]
        A.stroke(cv, pts, 1, '#f2dccc')
    haze(cv, '#2e0814', 0.22)
    myo = [(2, ramp('#c88088', '#f0b4b4', '#ffe0dc', n=4), 'loose'),                         # endocardium
           (20, ramp('#4a0a18', '#7a1426', '#a62236', '#cc3a4c', n=6), 'striated'),            # myocardium
           (10, ramp('#a08030', '#d0b050', '#f0d880', '#fff0b8', n=6), 'fat')]                # epicardial fat
    A.wall_band(cv, 0, 12, [(2, myo[0][1], 'loose'), (12, myo[1][1], 'striated')], top_edge=False, seed=33, bumps=0.8, out='#16020a')
    A.wall_band(cv, GY, H, myo, top_edge=True, seed=35, bumps=0.8, out='#16020a')
    speedlines(cv, '#ff8a9a', 10, 7, 36)
    o2 = S.bubble_o2()
    # the valve: a cusp hanging from the ceiling with its cords running down to the floor behind (slide under it)
    # the valve cusp hanging from the top (slide under it), its cords fanning down to a papillary muscle behind
    lf, edge_pts = A.valve_leaflet(56, GY - 36 - 10)
    lx, ly = 160 - lf.shape[1] / 2, 9
    for (px, py) in edge_pts:
        pts = [(lx + px + (96 - lx - px) * t, ly + py + (GY - 34 - ly - py) * t) for t in np.linspace(0, 1, 40)]
        A.stroke(cv, pts, 1, '#f2e0d4', 210)
    paste(cv, lf, lx, ly)
    row(cv, o2, 132, GY - 8, 4, 13)
    th = A.thrombus(26, 40, seed=4)
    place(cv, th, 262, GY + 3)
    arc(cv, o2, 228, 296, GY - 16, 70, 6)
    row(cv, o2, 320, GY - 12, 3, 15)
    heal = S.heal_cap(); paste(cv, heal, 336, GY - 74)
    char('sub', 104, GY + 1, cv, squash=0.78)
    puff(cv, 74, GY - 2, '#ffb0b8', 3, 6)
    hud(cv, hp=0.41, score='6,010', progress=0.58, theme='#ff4a6a')
    return finish(cv, '좌심실', 'Left ventricle', OUT.format('ventricle'))


# ------------------------------------------------------------------ brain
def cortex():
    cv = canvas()
    vgrad(cv, ramp('#0c0820', '#140e2c', '#1c1438', '#140e2c'))
    R = np.random.RandomState(41)
    far = ('#2a1c50', '#3a2a62', '#4a3874', '#5a4686', '#6a5498', '#14082a')
    for k in range(7):
        A.pyramidal(cv, R.uniform(0, W), R.uniform(70, GY - 10), 6, R, far)
    # a capillary across the tissue, astrocytes holding on to it
    A.capillary_h(cv, 64, 3, '#8a2a40', '#4a0c1c')
    for xc in (90, 250, 360):
        A.astrocyte(cv, xc, 64 + R.uniform(-22, 22), 6, R, '#b8a0e0', '#3a2a60')
    haze(cv, '#140e2c', 0.25)
    near = ('#5a2c98', '#8a58c8', '#b884f0', '#e0c8ff', '#7ff0ff', '#1e0a3a')
    for (xc, yc) in [(40, 128), (230, 120), (330, 134)]:
        A.pyramidal(cv, xc, yc, 9, R, near, glow=True)
    particles(cv, 30, ['#9ae8ff', '#ffffff'], 12, a=220)
    ctx = [(2, ramp('#a07ab8', '#d0b0e8', '#f0e0ff', n=4), 'loose'),                          # pia
           (18, ramp('#3a2a6a', '#5a4490', '#7a62b4', '#9e86d4', n=6), 'gray'),               # grey matter
           (12, ramp('#8a86a8', '#b0aecc', '#d4d2ea', '#f0eefc', n=6), 'white')]              # white matter
    A.wall_band(cv, GY, H, ctx, top_edge=True, seed=45, bumps=1.4, out='#0c0620')
    speedlines(cv, '#a890ff', 9, 9, 36)
    o2 = S.bubble_o2()
    row(cv, o2, 112, GY - 12, 3, 15)
    am = A.amyloid(26, 16)
    place(cv, am, 180, GY + 3)
    tg = A.tangle(18, 44)
    place(cv, tg, 214, GY + 2)
    arc(cv, o2, 160, 244, GY - 16, 76, 7)
    ax = A.axon_cross(110)
    paste(cv, ax, 268, GY - 30)
    row(cv, o2, 290, GY - 10, 4, 15)
    om = S.omega_drop(); paste(cv, om, 196, GY - 104)
    mv = S.multi_vit(); paste(cv, mv, 344, GY - 70)
    char('jelly', 150, GY + 1, cv, jump=62)
    hud(cv, hp=0.55, score='9,870', progress=0.66, theme='#a070ff', pop=(140, GY - 112, '+30'))
    return finish(cv, '대뇌피질', 'Cerebral cortex', OUT.format('cortex'))


SCENES = {'stomach': stomach, 'jejunum': jejunum, 'aorta': aorta, 'ventricle': ventricle, 'cortex': cortex}

if __name__ == '__main__':
    for n in (sys.argv[1:] or list(SCENES)):
        SCENES[n](); print('made', n)
