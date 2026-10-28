# (v52) the shell game ('야바위', in the combined sewer): its pictures, in the glossy cartoon look of gloss.py (the
# user's slot machine and mouse): yb_lid, a domed cast-iron manhole lid (raised diamond studs, a bronze ring to lift it
# by) the golden poop hides under; yb_table, the dealer's table (green felt on top, a red velvet skirt with a gold braid
# and fringe). The dealer is the user's mouse (pk_k0 and its first dive frames, pk.webp); the golden poop and the coin
# are the slot's (sl_s0, sl_coin). -> runner_hd/assets/yb.webp + manifest (yb_lid, yb_table)
import sys, os, json
import numpy as np
from PIL import Image
from scipy import ndimage
sys.path.insert(0, '/home/claude/hdart')
import gloss
from gloss import Pic, hexc, sstep

OUT = '/home/claude/runner_hd/assets'
PRE = '/tmp/claude-0/-home-claude/3a779e8a-891a-5a91-a306-4a5325e0d53e/scratchpad/yb'
IRON = ('#0c1016', '#1e2733', '#36465a', '#62789a', '#c4d6ee')
BRONZE = ('#3a1c06', '#7a4612', '#c07a28', '#f2b456', '#fff0c0')
GOLD = ('#6e3200', '#b06a00', '#e9a414', '#ffd04a', '#fff2b0')
FELT = ('#031a0e', '#082e1c', '#0e462a', '#18663e', '#3e9468')
VELVET = ('#1a0005', '#3e030d', '#6a0a1a', '#9a182c', '#d4505e')


def lid():
    """55 x 40 units at 6 px a unit: a dome on a flange, seen from a little above"""
    S = 6; W, H = 55 * S, 40 * S
    p = Pic(W, H)
    cx, by = W / 2, 31 * S                       # the middle of its foot
    rx, ry = 25 * S, 7.2 * S                     # the foot's ellipse
    dh = 19 * S                                  # how high the dome stands
    # the flange (the foot's rim, a flat lip all round)
    flange = p.ell(cx, by, rx + 1.6 * S, ry + 1.0 * S)
    p.body(flange, IRON, R=3 * S, rim=0.5, rimcol='#9ab8e0', spec=0.6, shadow=0)
    # the dome: the top half of a tall ellipse over the foot, and the front half of the foot
    dome = (p.ell(cx, by, rx - 0.6 * S, dh) & (p.Y <= by)) | p.ell(cx, by, rx - 0.6 * S, ry - 0.4 * S)
    n = p.body(dome, IRON, R=14 * S, rim=0.6, rimcol='#a8c8f0', spec=0.95, power=30, shadow=0.35)
    # raised diamond studs over the dome, in rows that follow it round (u: across, t: up the dome)
    half = (rx - 0.6 * S) * np.sqrt(np.clip(1 - ((by - p.Y) / dh) ** 2, 0, 1))
    u = (p.X - cx) / np.maximum(half, 1e-3)
    t = np.clip((by - p.Y) / dh, 0, 1)
    row = np.floor(t * 6)
    fu = np.mod(u * 4.5 + 0.5 * (row % 2), 1.0); ft = np.mod(t * 6, 1.0)
    stud = (np.abs(fu - 0.5) * 1.7 + np.abs(ft - 0.5) < 0.34) & dome & (np.abs(u) < 0.93) & (t > 0.06) & (t < 0.78)
    stud = ndimage.binary_erosion(stud, iterations=gloss.SS // 2)
    p.body(stud, IRON, R=1.6 * S, rim=0.4, rimcol='#9ab8e0', spec=0.9, power=24, line=0.5, shadow=0.55)
    # the band round the dome's foot (a raised ring where it meets the flange: the front of it shows)
    band = (p.ell(cx, by + 0.2 * S, rx - 0.2 * S, ry + 0.2 * S) & ~p.ell(cx, by - 1.6 * S, rx - 2.2 * S, ry - 0.6 * S)) & (p.Y > by - 2.6 * S)
    p.body(band, IRON, R=1.8 * S, rim=0.6, rimcol='#a8c8f0', spec=0.9, line=0.8, shadow=0.3)
    # a big soft reflection on the dome's upper left, and a crisp small one
    p.gloss_blob(p.ell(cx - 10 * S, by - 13 * S, 7 * S, 3.2 * S, -0.35) & dome, a=0.42, soft=2.2)
    p.gloss_blob(p.ell(cx - 12.5 * S, by - 14.2 * S, 2.6 * S, 1.1 * S, -0.4) & dome, a=0.9, soft=0.5)
    # the bronze ring on top: its post, then the ring standing up (a torus seen edge-on: an ellipse with a hole)
    post = p.ell(cx, by - dh + 0.6 * S, 3.4 * S, 1.6 * S)
    p.body(post, BRONZE, R=1.6 * S, rim=0.5, spec=0.9, shadow=0.4)
    ring = p.ell(cx, by - dh - 3.4 * S, 6.2 * S, 4.6 * S) & ~p.ell(cx, by - dh - 3.4 * S, 3.6 * S, 2.3 * S)
    p.body(ring, BRONZE, R=1.6 * S, rim=0.6, rimcol='#fff0b0', spec=1.0, power=26, line=1.0, shadow=0.45)
    p.gloss_blob(p.ell(cx - 3.6 * S, by - dh - 6.2 * S, 1.6 * S, 0.7 * S, -0.5) & ring, a=0.9, soft=0.4)
    p.outline(3.6)
    img = p.image()
    meta = {'foot': [round(cx / S, 3), round(by / S, 3), round(rx / S, 3), round(ry / S, 3)], 'top': round((by - dh - 8 * S) / S, 3)}
    return img, meta, S


def table():
    """290 x 78 units at 4 px a unit: the felt top (seen from above, narrower at the back), the velvet skirt"""
    S = 4; Wu, Hu = 290, 78; W, H = Wu * S, Hu * S
    p = Pic(W, H)
    yb_, yf = 6 * S, 30 * S                      # the top's back and front edges
    top = p.poly([(34 * S, yb_), (256 * S, yb_), (282 * S, yf), (8 * S, yf)])
    # the felt: nearly flat, a soft fibre noise
    rng = np.random.default_rng(3)
    fib = ndimage.gaussian_filter(rng.standard_normal(p.X.shape).astype(np.float32), 1.2 * gloss.SS)
    nf = np.stack([fib * 0.05, -0.25 + fib * 0.05, np.ones_like(fib)], -1); nf /= np.linalg.norm(nf, axis=-1, keepdims=True)
    p.body(top, FELT, R=8 * S, rim=0.2, spec=0.0, n=nf, shadow=0, lam_lo=-0.6, top=-0.45)
    # a lighter ellipse in its middle (worn by the game), a stitched gold line round the edge
    p.over(hexc('#2e8a56'), ndimage.gaussian_filter(p.ell(W / 2, (yb_ + yf) / 2 + 1 * S, 96 * S, 9 * S).astype(np.float32), 6 * S) * 0.3)
    inner = p.poly([(40 * S, yb_ + 2.2 * S), (250 * S, yb_ + 2.2 * S), (274 * S, yf - 2.6 * S), (16 * S, yf - 2.6 * S)])
    edge = ndimage.binary_dilation(inner, iterations=int(0.5 * S * gloss.SS)) & ~inner
    dash = np.mod(p.X / (3.2 * S) + p.Y / (9 * S), 1.0) < 0.6
    p.over(hexc('#e8c060'), (edge & dash).astype(np.float32) * 0.85)
    # the front edge: a rounded gold-trimmed lip
    lip = p.cap((8 * S, yf), (282 * S, yf), 2.1 * S)
    p.body(lip, GOLD, R=2.1 * S, rim=0.6, rimcol='#fff0a0', spec=1.0, power=28, line=1.0, shadow=0.4)
    # the skirt: red velvet hanging in folds, darker low down, its sheen at the folds' edges
    skirt = p.poly([(8 * S, yf + 1.2 * S), (282 * S, yf + 1.2 * S), (287 * S, H + 2), (3 * S, H + 2)])
    k = 2 * np.pi / (17 * S)
    ph = p.X * k + 1.3 * np.sin(p.X / (37 * S)) + 0.6 * np.sin(p.X / (13 * S) + 1.0)
    nx = -0.62 * np.cos(ph) * (0.55 + 0.45 * np.clip((p.Y - yf) / (40 * S), 0, 1))
    nv = np.stack([nx, np.full_like(nx, -0.05), np.ones_like(nx)], -1); nv /= np.linalg.norm(nv, axis=-1, keepdims=True)
    p.body(skirt, VELVET, R=6 * S, rim=0.55, rimcol='#ff6a7c', spec=0.08, power=10, n=nv, top=0.3, shadow=0.55, line=0.8)
    # the gold braid along its top: a band with little diamonds
    braid = p.poly([(8.5 * S, yf + 2.4 * S), (281.5 * S, yf + 2.4 * S), (281.8 * S, yf + 6.4 * S), (8.2 * S, yf + 6.4 * S)])
    p.body(braid, GOLD, R=1.8 * S, rim=0.5, rimcol='#fff0a0', spec=0.8, line=0.8, shadow=0.45)
    dm = (np.abs(np.mod(p.X / (6 * S), 1.0) - 0.5) * 6 * S + np.abs(p.Y - (yf + 4.4 * S)) < 1.5 * S) & braid
    p.body(dm, ('#7a1a0a', '#b02a14', '#e04a2a', '#ff8a5a', '#ffd0b0'), R=0.9 * S, rim=0.3, spec=0.9, line=0.4, shadow=0.3)
    # the fringe along the bottom: gold tassels
    fr = np.zeros(p.X.shape, bool)
    for i in range(int((283 * S - 6 * S) / (3.4 * S))):
        x = 6 * S + i * 3.4 * S + 1.7 * S
        fr |= p.cap((x, H - 9 * S), (x + 0.6 * S, H - 1.0 * S), 1.15 * S, 0.8 * S)
    p.body(fr, GOLD, R=1.0 * S, rim=0.4, spec=0.7, line=0.6, shadow=0.5)
    fb = p.poly([(5 * S, H - 11 * S), (285 * S, H - 11 * S), (285.4 * S, H - 8.2 * S), (4.6 * S, H - 8.2 * S)])
    p.body(fb, GOLD, R=1.3 * S, rim=0.5, rimcol='#fff0a0', spec=0.9, line=0.8, shadow=0.4)
    p.outline(2.6)
    img = p.image()
    meta = {'back': yb_ / S, 'front': yf / S, 'top': [[34, 6], [256, 6], [282, 30], [8, 30]]}
    return img, meta, S


def atlas(sprs, pad=4):
    """side by side, top aligned (each sprite: its RGBA float array)"""
    w = sum(s.shape[1] + pad for s in sprs) + pad; h = max(s.shape[0] for s in sprs) + 2 * pad
    A = np.zeros((h, w, 4), np.float32); rects = []; x = pad
    for s in sprs:
        A[pad:pad + s.shape[0], x:x + s.shape[1]] = s; rects.append([x, pad, s.shape[1], s.shape[0]]); x += s.shape[1] + pad
    return A, rects


def build():
    os.makedirs(PRE, exist_ok=True)
    (li, lm, ls), (ti, tm, ts) = lid(), table()
    A, rects = atlas([li, ti])
    a = np.clip(A, 0, 255).astype(np.uint8)
    Image.fromarray(a, 'RGBA').save(f'{OUT}/yb.webp', quality=92, alpha_quality=100, method=6)
    Image.fromarray(a, 'RGBA').save(f'{PRE}/yb_sprites.png')
    m = json.load(open(f'{OUT}/manifest.json'))
    for nm, img, meta, sc, r in [('yb_lid', li, lm, ls, rects[0]), ('yb_table', ti, tm, ts, rects[1])]:
        m['sprites'][nm] = {'f': 'yb.webp', 'r': r, 'w': round(img.shape[1] / sc, 3), 'h': round(img.shape[0] / sc, 3), **meta}
    json.dump(m, open(f'{OUT}/manifest.json', 'w'), separators=(',', ':'))
    print('yb.webp', os.path.getsize(f'{OUT}/yb.webp'), a.shape, lm, tm)


if __name__ == '__main__':
    if 'preview' in sys.argv:
        os.makedirs(PRE, exist_ok=True)
        for f in (lid, table):
            img = f()[0]; im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), 'RGBA')
            bg = Image.new('RGBA', im.size, (34, 40, 46, 255)); bg.alpha_composite(im); bg.save(f'{PRE}/{f.__name__}.png'); print(f.__name__, im.size)
    else:
        build()
