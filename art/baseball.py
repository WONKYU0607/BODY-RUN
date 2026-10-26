# The baseball mini-game's pictures (in the jejunum): the ballpark seen from behind home plate, made of the small
# intestine's own tissue (a villi lawn mown in stripes, smooth pale mucosa for the infield dirt, the mound a lump of it,
# stands of circular folds packed with villus tips like a crowd, a dark lumen above with drifting chyle droplets), and
# the pitcher: a macrophage (a big white cell) in four frames (set, wind-up, release, follow-through).
#   -> runner_hd/assets/bb_field.webp (420 x 180 units), bb.webp (the pitcher frames) + manifest entries
# The ground is drawn per pixel through the camera: v (metres from home plate) and u (metres sideways) from the screen
# point, so every texture shrinks properly with distance.
import json, sys
import numpy as np, cv2
from PIL import Image
from scipy import ndimage
sys.path.insert(0, '/home/claude/hdart')
import art
from art import SC, px, hexc, ramp, ramp_col, dome_shade, outline, highlight, paint, over, disc, ellipse_soft, stroke

FW, FH = 420, 180                       # the field picture (units)
CX, HZ = 210.0, -17.4                   # the plate's x; the horizon (above the picture: a long lens from high behind)
# ground y = HZ + K / (v + V0); x = CX + S * u / (v + V0). The camera V0 metres behind the plate; the plate stays at
# y 172 and its width on the screen the same whatever V0 (K, S follow it). V0 30 at first (the mound at y 100); 23 now:
# the camera nearer the plate, so the mound and the pitcher sit farther off (y 88, 0.9 the size)
V0 = 23.0
K, S = (172.0 - HZ) * V0, 1116.0 / 30.0 * V0
MV = 18.4                                # the mound's distance from the plate (m)
RF, WALL = 104.0, 1.5                   # the outfield wall: distance (m), height (m)
OUT = '/home/claude/runner_hd/assets'
PRE = '/tmp/claude-0/-home-claude/3a779e8a-891a-5a91-a306-4a5325e0d53e/scratchpad/bb'
rng = np.random.default_rng(7)


def hash2(i, j, k=0):
    h = (i * 374761393 + j * 668265263 + k * 2147483647) & 0xffffffff
    h = ((h ^ (h >> 13)) * 1274126177) & 0xffffffff
    return (h ^ (h >> 16)) / 4294967296.0


def field():
    Hh, Ww = px(FH), px(FW)
    y = (np.arange(Hh, dtype=np.float64)[:, None] + 0.5) / SC
    x = (np.arange(Ww, dtype=np.float64)[None, :] + 0.5) / SC
    y = np.broadcast_to(y, (Hh, Ww)); x = np.broadcast_to(x, (Hh, Ww))
    img = np.zeros((Hh, Ww, 3), np.float64)
    # ---- the lumen above: dark, a soft glow from the middle, lighter towards the stands
    t = np.clip(y / 14.0, 0, 1)
    sky = ramp_col(ramp('#14030a', '#240710', '#3c0c1c', '#5a1a2c'), t)
    glow = np.exp(-(((x - CX) / 150) ** 2 + ((y - 30) / 40) ** 2)) * 0.55
    sky = sky + glow[..., None] * (hexc('#7a2a40') - sky) * 0.6
    for gx, gy, gr in [(70, 0, 40), (350, 0, 46), (210, -4, 60)]:               # the light coming in from above
        g = np.exp(-(((x - gx) / gr) ** 2 + ((y - gy) / (gr * 0.4)) ** 2)) * 0.3
        sky = sky + g[..., None] * (hexc('#c0607a') - sky)
    img[:] = sky
    # ---- the ground through the camera
    below = y > HZ + 0.4
    v = np.where(below, K / np.maximum(y - HZ, 1e-3) - V0, 1e9)
    u = (x - CX) * (v + V0) / S
    D = v + V0
    fp = D / S                                                                 # metres per screen unit here
    r = np.hypot(u, v)
    ground = below & (r <= RF)
    # the villi lawn: jittered villus tips (0.45 m cells), mown stripes, a little noise
    cell = 0.45
    ci, cj = np.floor(u / cell), np.floor(v / cell)
    best = np.full(u.shape, 9.0)
    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            ii, jj = ci + di, cj + dj
            hi = (ii.astype(np.int64) * 374761393 + jj.astype(np.int64) * 668265263) & 0xffffffff
            hi = ((hi ^ (hi >> 13)) * 1274126177) & 0xffffffff
            ox = ((hi ^ (hi >> 16)) & 0xffff) / 65535.0; oy = (((hi ^ (hi >> 16)) >> 8) & 0xffff) / 65535.0
            d = np.hypot(u - (ii + 0.2 + 0.6 * ox) * cell, v - (jj + 0.2 + 0.6 * oy) * cell)
            best = np.minimum(best, d)
    tip = np.clip(1 - best / 0.2, 0, 1) ** 1.5
    fpv = K / np.maximum(y - HZ, 1e-3) ** 2                                   # metres per unit along the view (the ground is steep here)
    amp = np.clip(1 - np.maximum(fp, fpv * 0.6) / 0.3, 0, 1)                  # tips fade where a cell gets under a pixel
    stripe = (np.floor((v + 2) / 6.0) % 2) * 2 - 1
    grain = np.sin(u * 9.0 + np.sin(v * 1.3) * 2.0) * np.clip(1 - fp / 0.12, 0, 1) * 0.04
    lawn = ramp_col(ramp('#5e1424', '#86283a', '#a63c50', '#c45a6a', '#e08a92'), np.clip(0.44 + 0.085 * stripe + 0.38 * tip * amp + grain, 0, 1))
    # dirt: the infield arc round the mound, the base paths, the circle round home, the mound
    mound = np.hypot(u, v - 18.4)
    diamond = (np.abs(u) + np.abs(v - 19.4) <= 19.4 - 1.4)                     # the infield grass square, inset
    dirt = (mound <= 29.0) & ~diamond
    dirt |= np.hypot(u, v) <= 4.0
    dirt |= mound <= 2.7
    dirt &= ground
    n1 = ndimage.gaussian_filter(rng.standard_normal(u.shape), 22) * 14 + ndimage.gaussian_filter(rng.standard_normal(u.shape), 3) * 1.2
    speck = (rng.random(u.shape) < 0.0012 * np.clip(1 - fp / 0.2, 0, 1))
    dcol = ramp_col(ramp('#a65e56', '#c47c6e', '#dc9c88', '#eebaa2'), np.clip(0.55 + n1 * 0.35 + 0.04 * np.sin(u * 0.9 + v * 0.5), 0, 1))
    g = np.where(dirt[..., None], dcol, lawn)
    g[speck] = hexc('#f2d27a')
    # chalk: the foul lines, the batter's boxes
    lw = np.maximum(0.09, fp * 0.55)
    chalk = ((np.abs(np.abs(u) - v) < lw) & (v > 0.5)) & ground
    for sx in (-1, 1):
        bx0, bx1 = sx * 0.25, sx * 1.15
        lo, hi_ = min(bx0, bx1), max(bx0, bx1)
        box = ((np.abs(u - bx0) < lw * 0.8) | (np.abs(u - bx1) < lw * 0.8)) & (v > -0.9) & (v < 0.9)
        box |= ((np.abs(v - 0.9) < lw * 0.8) | (np.abs(v + 0.9) < lw * 0.8)) & (u > lo) & (u < hi_)
        chalk |= box & ground
    g[chalk] = g[chalk] * 0.15 + hexc('#f6e8ea') * 0.85
    # depth: farther is a little hazier and darker
    haze = np.clip((D - 20) / 110, 0, 1)[..., None]
    g = g * (1 - 0.35 * haze) + hexc('#4a1222') * 0.35 * haze
    img = np.where(ground[..., None], g, img)
    # the mound's bulge: lighter on top, a shadow towards us
    mb = ground & (mound <= 3.0)
    sh = np.clip(1 - mound / 2.7, 0, 1)
    img = np.where(mb[..., None], img * (0.9 + 0.22 * sh[..., None]), img)
    # ---- the wall and the stands behind it (per column: where the ground meets the wall)
    cols = (np.arange(Ww) + 0.5) / SC
    ywall = np.full(Ww, np.nan); ytop = np.full(Ww, np.nan)
    for k, xc in enumerate(cols):
        lo_, hi2 = 20.0, 400.0                                               # solve u^2 + v^2 = RF^2 along this column
        for _ in range(50):
            vm = (lo_ + hi2) / 2; um = (xc - CX) * (vm + V0) / S
            if um * um + vm * vm > RF * RF: hi2 = vm
            else: lo_ = vm
        vm = (lo_ + hi2) / 2
        if vm < 300:
            ywall[k] = HZ + K / (vm + V0); ytop[k] = ywall[k] - S * WALL / (vm + V0)
    yw = np.broadcast_to(ywall[None, :], (Hh, Ww)); yt = np.broadcast_to(ytop[None, :], (Hh, Ww))
    wall = (y <= yw) & (y >= yt)
    wt = np.clip((y - yt) / np.maximum(yw - yt, 1e-3), 0, 1)
    wcol = ramp_col(ramp('#f0b0b4', '#b4485c', '#7a2034', '#5a1426'), np.clip(wt * 1.4, 0, 1))
    img = np.where(wall[..., None], wcol, img)
    # the stands: tiers of circular folds going up from the wall top, packed with villus tips
    stands_top = yt - 40 + 0 * cols[None, :]
    st = (y < yt) & (y > stands_top)
    rel = np.where(st, (yt - y), 0)
    tier = 4.6
    k_t = np.floor(rel / tier); f_t = rel / tier - k_t
    fold = np.sin(np.clip(f_t, 0, 1) * np.pi)                                 # each fold a rounded band
    deep = np.clip(k_t / 7, 0, 1)
    scol = ramp_col(ramp('#3a0c1a', '#6a1c30', '#9a3448', '#c45a6a', '#e89098'), np.clip(0.18 + 0.62 * fold * (1 - 0.55 * deep) + 0.12 * (f_t < 0.35) * fold, 0, 1))
    img = np.where(st[..., None], scol, img)
    # the crowd: villus tips and a few chyle droplets along the folds (round, lit from above)
    can = np.zeros((Hh, Ww, 4), np.float32); can[..., :3] = img; can[..., 3] = 255
    for kk in range(4):
        for xc in np.arange(2, FW - 2, 2.0 - 0.1 * kk):
            j = int(xc * SC)
            if j >= Ww or np.isnan(ytop[j]): continue
            yy = ytop[j] - (kk + 0.62) * tier + rng.uniform(-0.6, 0.6)
            if yy < -1: continue
            rr = (1.15 - 0.07 * kk) * rng.uniform(0.85, 1.15)
            c = ['#e48a96', '#f0a8ae', '#d06878', '#f6d07a', '#f2b8bc', '#c85a6c'][rng.integers(0, 6)] if rng.random() > 0.08 else '#fff0b0'
            shade = 1 - 0.5 * kk / 7
            col = hexc(c) * shade
            disc(can, xc + rng.uniform(-0.4, 0.4), yy, rr + 0.35, '#2a0812', a=200)
            disc(can, xc + rng.uniform(-0.2, 0.2), yy - 0.15, rr, col, a=255)
            disc(can, xc - rr * 0.3, yy - rr * 0.45, rr * 0.35, '#ffffff', a=int(120 * shade))
    img = can[..., :3].astype(np.float64)
    # the hanging villi of the lumen's roof along the top edge (dark, against the glow)
    roof = np.zeros((Hh, Ww), bool)
    for xc in np.arange(-4, FW + 4, 7.5):
        L = rng.uniform(3, 7); w0 = rng.uniform(2.2, 3.4); xx = xc + rng.uniform(-2, 2)
        ys = np.linspace(0, L, 40)
        for yy in ys:
            ww = w0 * (1 - 0.35 * yy / L) * (0.6 if yy > L - 1 else 1)
            j0, j1 = max(0, px(xx - ww)), min(Ww, px(xx + ww)); i = px(yy)
            if 0 <= i < Hh: roof[i:i + px(0.25) + 1, j0:j1] = True
    roof = ndimage.binary_closing(roof, iterations=2)
    rs = ndimage.gaussian_filter(roof.astype(np.float32), 0.7)
    img = img * (1 - rs[..., None]) + hexc('#1a040c') * rs[..., None]
    # drifting chyle droplets in the air (in front of the stands)
    can = np.zeros((Hh, Ww, 4), np.float32); can[..., :3] = img; can[..., 3] = 255
    for _ in range(12):
        xx, yy, rr = rng.uniform(5, FW - 5), rng.uniform(2, 34), rng.uniform(0.6, 1.5)
        disc(can, xx, yy, rr * 2.4, '#f2c860', a=34)
        disc(can, xx, yy, rr, '#f4d27a', a=200)
        disc(can, xx - rr * 0.3, yy - rr * 0.35, rr * 0.35, '#fffbe0', a=220)
    # the second base: a platelet (pale, rounded)
    bx, by = CX, HZ + K / (38.8 + V0)
    ellipse_soft(can, bx, by + 0.2, 2.6, 0.75, '#2a0812', a=160)
    ellipse_soft(can, bx, by, 2.2, 0.55, '#f8ecc8', a=255)
    # the mound's rubber (a flat platelet)
    my = HZ + K / (18.4 + V0)
    ellipse_soft(can, CX, my - 0.6, 3.4, 0.5, '#2a0812', a=150)
    ellipse_soft(can, CX, my - 0.75, 3.0, 0.38, '#fbf2dc', a=255)
    # home plate: a pentagon (a big flat platelet), its point towards us
    def gp(uu, vv): return (CX + S * uu / (vv + V0), HZ + K / (vv + V0))
    poly = [gp(-0.215, 0.0), gp(0.215, 0.0), gp(0.215, -0.215), gp(0.0, -0.43), gp(-0.215, -0.215)]
    for wdt, col, a in [(1.6, '#2a0812', 230), (0, '#fbf3e6', 255)]:
        m = np.zeros((Hh, Ww), np.uint8)
        pts = np.array([[(p[0]) * SC, (p[1]) * SC] for p in poly], np.float64)
        if wdt:
            c0 = pts.mean(0); pts = c0 + (pts - c0) * (1 + wdt / 10)
        cv2.fillPoly(m, [np.round(pts * 16).astype(np.int32)], 255, cv2.LINE_AA, 4)
        k_ = m.astype(np.float32) / 255 * a / 255
        over(can, np.broadcast_to(hexc(col), k_.shape + (3,)), k_)
    # a soft darkening at the bottom corners (the near tissue)
    vig = np.clip(((x - CX) / 240) ** 2 + ((y - 190) / 110) ** 2 - 0.3, 0, 1) * np.clip((y - 110) / 60, 0, 1)
    can[..., :3] = can[..., :3] * (1 - 0.45 * vig[..., None])
    # the pitcher's picture scale in the game: 1.45 with the first camera, and as the mound's scale on the screen goes
    pscale = round(1.45 * (S / (MV + V0)) / (1116.0 / (18.4 + 30.0)), 3)
    return can, {'mound': [CX, round(my, 2)], 'plate': [CX, round(HZ + K / V0, 2)], 'horizon': HZ, 'K': K, 'V0': V0, 'S': S, 'pscale': pscale}


# ---------------------------------------------------------------- the pitcher: a macrophage, facing us
def pitcher(frame):
    W_, H_ = 46, 46
    y, x = art.grid(H_, W_)
    cx, foot = 23.0, 42.0
    lean = [0.0, -1.6, 1.8, 2.6][frame]                    # sideways lean (wind-up back, release / follow forward)
    squash = [1.0, 1.05, 0.95, 0.9][frame]
    bx, by = cx + lean, foot - 13.5 * squash
    # the body: a blob with a ruffled edge (its membrane), on two little pseudopod feet
    ang = np.arctan2(y - by, x - bx)
    rad = np.hypot((x - bx) / 12.5, (y - by) / (13.0 * squash))
    ruff = 1 + 0.035 * np.sin(ang * 9 + frame) + 0.02 * np.sin(ang * 17 + 1.3)
    body = rad <= ruff
    for fx in (-6, 6):
        body |= ((x - (cx + fx)) / 4.2) ** 2 + ((y - (foot - 1.8)) / 2.6) ** 2 <= 1
    # the throwing arm (a pseudopod) from the right shoulder (screen left: the pitcher faces us, throws right-handed)
    sh = (bx - 9.5, by - 5.0)
    hand = [(bx - 15.0, by + 5.5), (bx - 16.5, by - 15.0), (bx - 4.0, by - 20.0), (bx + 9.0, by + 4.0)][frame]
    arm = np.zeros(body.shape, bool)
    for s in np.linspace(0, 1, 40):
        px_, py_ = sh[0] + (hand[0] - sh[0]) * s, sh[1] + (hand[1] - sh[1]) * s
        rr = 3.7 - 0.9 * s
        arm |= ((x - px_) ** 2 + (y - py_) ** 2) <= rr * rr
    arm |= ((x - hand[0]) ** 2 + (y - hand[1]) ** 2) <= 3.3 ** 2      # the 'hand': a round lobe
    # the other arm, low at the side (glove side)
    oh = (bx + 12.5, by + 3.0) if frame != 1 else (bx + 13.5, by - 4.0)
    for s in np.linspace(0, 1, 30):
        px_, py_ = bx + 9.5 + (oh[0] - bx - 9.5) * s, by - 3.0 + (oh[1] - by + 3.0) * s
        arm |= ((x - px_) ** 2 + (y - py_) ** 2) <= (3.3 - 0.6 * s) ** 2
    mask = body | arm
    shade, n = dome_shade(mask, soft=1.6)
    spr = paint(art.smooth_mask(mask), ramp('#8a7aa0', '#b8a8cc', '#ddd2ea', '#f4eef8', '#ffffff'), shade)
    # the nucleus (kidney-shaped, seen through), granules, the faint cytoplasm mottling
    nu = np.zeros(mask.shape, bool)                                            # a lobed nucleus (three lobes in a curve)
    for lx, ly, lr in [(-3.6, 5.4, 2.4), (0.6, 3.0, 2.8), (4.4, 4.8, 2.2)]:   # (low in the body: the face is above it)
        nu |= ((x - (bx + 1.0 + lx)) / (lr * 1.05)) ** 2 + ((y - (by + ly)) / lr) ** 2 <= 1
    nus = ndimage.gaussian_filter(nu.astype(np.float32), 0.5 * SC)
    ncol = ramp_col(ramp('#5a3a88', '#7a56aa', '#9a76c4'), np.clip(shade * 0.9 + 0.1, 0, 1))
    spr[..., :3] = spr[..., :3] * (1 - 0.75 * nus[..., None]) + ncol * 0.75 * nus[..., None]
    gr = np.random.default_rng(3 + frame)
    for _ in range(26):
        gx_, gy_ = bx + gr.uniform(-9, 9), by + gr.uniform(-9, 9)
        if ((gx_ - bx) / 11) ** 2 + ((gy_ - by) / 11) ** 2 > 1: continue
        r_ = gr.uniform(0.35, 0.75)
        m_ = ((x - gx_) ** 2 + (y - gy_) ** 2 <= r_ * r_) & mask
        spr[m_, :3] = spr[m_, :3] * 0.4 + hexc('#c89ad0') * 0.6
    highlight(spr, mask, n, thresh=0.95, alpha=0.9)
    # the face, like the runners': two big glossy black eyes (a white shine up left, a small one, a warm glint below)
    # and a small open mouth
    fx, fy = bx + 0.4, by - 4.6
    for sx in (-4.3, 4.3):
        ex = fx + sx
        disc(spr, ex, fy, 3.05, '#1a0a14')
        disc(spr, ex, fy, 2.65, '#120a16')
        disc(spr, ex + 0.3, fy + 0.6, 1.8, '#2a1830', a=200)
        disc(spr, ex + 0.85, fy + 1.3, 0.7, '#ff7a2a', a=200)
        disc(spr, ex - 0.9, fy - 0.95, 1.05, '#ffffff')
        disc(spr, ex + 1.05, fy - 0.1, 0.42, '#ffffff', a=230)
    ellipse_soft(spr, fx, fy + 4.0, 1.45, 1.15, '#1a0a14')
    ellipse_soft(spr, fx, fy + 4.05, 1.0, 0.75, '#7a1a2c')
    ellipse_soft(spr, fx, fy + 4.5, 0.75, 0.35, '#ff6a7a', a=230)
    spr = outline(spr)
    # where the hand is (for the ball), in the outlined sprite's units; the feet's middle
    return spr, {'hand': [round(hand[0] + 1, 2), round(hand[1] + 1, 2)], 'foot': [cx + 1, foot + 1]}


if __name__ == '__main__':
    f, info = field()
    Image.fromarray(np.clip(f, 0, 255).astype(np.uint8), 'RGBA').convert('RGB').save(f'{OUT}/bb_field.webp', quality=88, method=6)
    Image.fromarray(np.clip(f, 0, 255).astype(np.uint8), 'RGBA').convert('RGB').resize((px(FW) // 2, px(FH) // 2), Image.LANCZOS).save(f'{PRE}/bb_field_preview.png')
    frames = [pitcher(k) for k in range(4)]
    fw = max(s.shape[1] for s, _ in frames); fh = max(s.shape[0] for s, _ in frames)
    atlas = np.zeros((fh, fw * 4 + 12, 4), np.float32)
    rects = []
    for k, (s, _) in enumerate(frames):
        x0 = k * (fw + 4); atlas[:s.shape[0], x0:x0 + s.shape[1]] = s; rects.append([x0, 0, s.shape[1], s.shape[0]])
    Image.fromarray(np.clip(atlas, 0, 255).astype(np.uint8), 'RGBA').save(f'{OUT}/bb.webp', lossless=True, method=6)
    Image.fromarray(np.clip(atlas, 0, 255).astype(np.uint8), 'RGBA').save(f'{PRE}/bb_pitcher_preview.png')
    m = json.load(open(f'{OUT}/manifest.json'))
    m['sprites']['bb_field'] = {'f': 'bb_field.webp', 'r': [0, 0, px(FW), px(FH)], 'w': FW, 'h': FH}
    for k, (s, meta) in enumerate(frames):
        m['sprites'][f'bb_p{k}'] = {'f': 'bb.webp', 'r': rects[k], 'w': round(s.shape[1] / SC, 3), 'h': round(s.shape[0] / SC, 3), **meta}
    m['bb'] = info
    for fn in ['bb_field.webp', 'bb.webp']:
        if fn not in m.get('extra', []): m.setdefault('extra', []).append(fn)
    json.dump(m, open(f'{OUT}/manifest.json', 'w'), separators=(',', ':'))
    print('ok', info, [r for r in rects])
