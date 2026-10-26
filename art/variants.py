# Looks of their own for places that used to share one: each vessel, heart chamber, lobe, stretch of gut its own
# background, from what is really there (the bone round the vertebral artery, the fat round the mesenteric one, the
# carotid's fork, bright blood back from the lungs, the right ventricle's moderator band, Peyer's patches ...).
import numpy as np
from scipy import ndimage
from art import (H, SC, px, grid, canvas, ramp, ramp_col, hexc, paint, ellipse_mask, outline, paste, over, blur, disc,
                 ellipse_soft, smooth_mask, inner)
import anatomy as A
from tiles import WT, GY, TAU, wide, crop, put, per_sin, gradient, haze, pcells, wall, band_line, spots
import themes as T
from themes import (rbc_flow, endothelium_p, wet_glints, lymphocyte, three, drift, tower, flip_v, hang_len, blend,
                    platelet_clump, vein_valve, ART_L, VEIN_L, macrophage, rbc, bubble, stack, feces, semilunar_fold,
                    food_tower, scatter, microglia, rows, capillary_band, astro_sprite, oligo, cross_bundle, trabeculae_p,
                    trab_ridge, MYO_L, lumen_glow, vessels_p)

RS = np.random.RandomState


def putw(arr, spr, x, y, a=1.0):
    """paste on one tile, wrapping across its seam"""
    paste(arr, spr, x, y, a)
    w = spr.shape[1] / SC
    if x + w > WT:
        paste(arr, spr, x - WT, y, a)
    if x < 0:
        paste(arr, spr, x + WT, y, a)


def noise(shape, sigma, seed):
    n = ndimage.gaussian_filter(RS(seed).uniform(-1, 1, shape).astype(np.float32), sigma * SC, mode='wrap')
    return n / max(np.abs(n).max(), 1e-6)


def opening(bw, bh, lip, deep=('#08010a', '#14030a', '#2a0a18')):
    """the dark mouth of a side branch on the far wall, with a lit lip"""
    hm = ellipse_mask(bw, bh)
    y, x = grid(bh, bw)
    hs = np.zeros(hm.shape + (4,), np.float32)
    depth = np.clip(((x - (bw - 1) / 2) / (bw / 2)) ** 2 + ((y - (bh - 1) / 2 - 1.5) / (bh / 2 - 2)) ** 2, 0, 1)
    hs[..., :3] = ramp_col(ramp(*deep, n=3), depth)
    hs[..., 3] = smooth_mask(hm) * 255
    lipm = hm & ~ellipse_mask(bw, bh, bw / 2 - 0.5, bh / 2 + 1.5, bw / 2 - 2, bh / 2 - 2)
    blend(hs, hexc(lip), smooth_mask(lipm))
    return outline(hs, '#12020a')


def behind(far, layer, k):
    """something seen through the thin, half-clear vessel wall: blended in at k"""
    a = layer[..., 3:4] / 255 * k
    far[..., :3] = far[..., :3] * (1 - a) + layer[..., :3] * a


# ------------------------------------------------------------------ vessels
def vessel_v(o):
    """o: grad (4 colours), endo (seed, ramp, nucleus colour), opens [(x, y, w, h), ...] or n_open, lip, valves,
    bright (oxygen-rich red cells), extra(far, R) drawn before the lining, layers (floor), vein_obs"""
    far = gradient(H, o['grad'])
    R = RS(o.get('seed', 900))
    if o.get('extra'):
        o['extra'](far, R)
    es, er, en = o['endo']
    endothelium_p(far, 12, GY + 2, es, er, en)
    if o.get('after'):
        o['after'](far, R)
    c3 = three(far)
    if o.get('opens'):
        for (x_, y_, bw, bh) in o['opens']:
            put(c3, opening(bw, bh, o['lip']), x_, y_)
    else:
        for k in range(o.get('n_open', 3)):
            bw, bh = int(R.uniform(*o.get('osize', (34, 54)))), int(R.uniform(20, 30))
            put(c3, opening(bw, bh, o['lip']), k * WT / o.get('n_open', 3) + R.uniform(0, 120), R.uniform(30, 90))
    if o.get('valves'):
        for k in range(3):
            vx = k * WT / 3 + R.uniform(150, 300)
            for sgn, yy in ((1, 20), (-1, GY - 4)):
                y, x = grid(40, 26)
                cusp = (np.abs(x - 12.5) <= 12 * (1 - (y / 40) ** 2))
                cs = A.mask_sprite(cusp if sgn > 0 else cusp[::-1], ramp('#4a2040', '#6a3058', '#8a4672', '#a86090'), '#1a0614', soft=1.4, hl=False)
                put(c3, cs, vx, yy if sgn > 0 else yy - 42, 0.85)
    bright = o.get('bright', False)
    rbc_flow(c3, o.get('n_rbc', 70), R.randint(1000), dark=not bright)
    for k in range(20):
        put(c3, A.platelet(k), R.uniform(0, WT), R.uniform(20, GY - 20))
    for k in range(7):
        put(c3, A.neutrophil(int(R.uniform(9, 12)), seed=40 + k), R.uniform(0, WT), R.uniform(24, GY - 24), 0.92)
    for k in range(5):
        put(c3, lymphocyte(6, k), R.uniform(0, WT), R.uniform(24, GY - 24), 0.92)
    wet_glints(c3, 500, R.randint(1000), pct=75, a=90, col='#ffe8ee')
    far = crop(c3); haze(far, o['grad'][1], 0.25)
    if o.get('glow'):
        lumen_glow(far, o['glow'], 0.12)
    mid = wide()
    rbc_flow(mid, o.get('n_mid', 26), R.randint(1000), y0=22, y1=GY - 30, size=o.get('mid_size', (12, 17)), alpha=0.95, dark=not bright and o.get('mid_dark', False))
    if o.get('mid_haze'):
        haze(mid, o['mid_haze'], 0.25)
    layers = o['layers']
    floor = wall(layers, True, seed=R.randint(1000), bumps=0.8, out='#1a0308')
    ceil = wall([(2, layers[0][1], 'endo'), (8, layers[1][1], layers[1][2]), (20, layers[2][1], 'loose')], False, seed=R.randint(1000), bumps=0.8, out='#1a0308')
    if not o.get('vein_obs'):
        obs = {'low': [A.atheroma(32, 18, seed=s) for s in (2, 3)],
               'tall': [A.thrombus(26, 60, seed=s) for s in (4, 5)],
               'hang': [flip_v(A.thrombus(24, hang_len(), seed=6))],
               'float': [A.neutrophil(22, seed=3), platelet_clump()],
               'huge': [tower(lambda h: A.thrombus(24, int(h), seed=7))]}
    else:
        obs = {'low': [A.thrombus(24, 18, seed=8)],
               'tall': [vein_valve(60)],
               'hang': [flip_v(vein_valve(hang_len()))],
               'float': [A.neutrophil(22, seed=5)],
               'huge': [tower(lambda h: vein_valve(int(h)))]}
    if o.get('obs'):
        obs.update(o['obs'])
    return dict(far=far, mid=crop(mid), floor=floor, ceil=ceil, obs=obs, coin='o2', special='iron')


def wall_layers(endo, mid_r, mid_pat, outer):
    return [(2, endo, 'endo'), (16 if mid_pat == 'elastic' else 7, mid_r, mid_pat), (30, outer, 'loose')]


def T_renalart():
    """the renal artery: short and wide, straight off the aorta; the mouths of its segmental branches in a row"""
    opens = []
    for k in range(6):
        opens.append((k * WT / 6 + 40, 46 + 18 * (k % 2), 30 + 6 * (k % 3), 22))
    return vessel_v(dict(seed=901, grad=['#2c0a0a', '#42120c', '#541a12', '#42120c'], endo=(911, ramp('#5e1a1a', '#722420', '#862e28', n=3), '#3e1010'),
                         opens=opens, lip='#a8402e', glow='#e07a60',
                         layers=wall_layers(ramp('#d08a7c', '#f4b8a8', '#ffe2d8', n=4), ramp('#6e1a14', '#9e2a1e', '#c8462e', '#e46a4a', n=6), 'elastic',
                                            ramp('#8a6450', '#b88c74', '#dcb49a', '#f0d4bc', n=6))))


def T_carotid():
    """the common carotid: the fork into internal and external carotids (two mouths side by side over a sharp
    divider) and the widened carotid sinus round it, where pressure is sensed"""
    def extra(far, R):
        y, x = grid(H, WT)
        for cx in (WT * 0.2, WT * 0.7):
            dx = np.mod(x - cx + WT / 2, WT) - WT / 2
            sinus = np.exp(-((dx / 110) ** 2 + ((y - 78) / 60) ** 2))
            far[..., :3] = far[..., :3] * (1 + 0.22 * sinus[..., None])
    opens = []
    for cx in (WT * 0.2, WT * 0.7):
        opens += [(cx - 46, 58, 40, 30), (cx + 8, 64, 34, 26)]
    return vessel_v(dict(seed=902, grad=['#34081c', '#4e0e2a', '#621434', '#4e0e2a'], endo=(912, ramp('#701a3a', '#842244', '#982c4e', n=3), '#3e0c24'),
                         extra=extra, opens=opens, lip='#a83456', glow='#d06a8a',
                         layers=wall_layers(ramp('#c88094', '#f0b0c4', '#ffe0ea', n=4), ramp('#5e0e2a', '#8e1a3c', '#ba3054', '#d85272', n=6), 'elastic',
                                            ramp('#806070', '#ac8898', '#d0b0bc', '#ecd2da', n=6))))


def T_vertebral():
    """the vertebral artery climbs through a hole in each neck vertebra: the bone rings show through its wall"""
    def extra(far, R):
        y, x = grid(H, WT)
        cb, d, _ = pcells(H, 2600, 931, sy=1.0, border=0.6)
        bone = np.zeros(far.shape, np.float32)
        per = WT / 9
        u = np.mod(x, per) - per / 2
        ring = np.clip((19 - np.abs(u + 3 * np.sin(y * 0.05))) * SC * 0.3 + 0.5, 0, 1)
        lit = np.clip(0.55 + 0.35 * np.cos(u / 19 * np.pi / 2) - 0.35 * cb + 0.1 * noise(y.shape, 0.8, 932), 0, 1)
        bone[..., :3] = ramp_col(ramp('#6a5a48', '#a8967c', '#d8c8aa', '#f4ead4', n=4), lit)
        bone[..., 3] = ring * 255
        behind(far, bone, 0.5)
        plex = np.zeros_like(far)                         # the venous plexus between the rings
        for k in range(40):
            x0 = R.uniform(0, WT); y0 = R.uniform(14, GY - 6); a0 = R.uniform(0, TAU); L = R.uniform(10, 30)
            pts = [(x0 + np.cos(a0 + 0.4 * np.sin(t * 0.3)) * t, y0 + np.sin(a0 + 0.4 * np.sin(t * 0.3)) * t) for t in np.linspace(0, L, 16)]
            for off in (0, -WT, WT):
                A.stroke(plex, [(p + off, q) for p, q in pts], 1.4, '#5a2a6a', 200, scale=1.0)
        behind(far, plex, 0.5)
    return vessel_v(dict(seed=903, grad=['#2a0612', '#3c0a1a', '#4a1022', '#3c0a1a'], endo=(913, ramp('#5a1626', '#6e1e30', '#82283a', n=3), '#3a0c1a'),
                         extra=extra, n_open=2, lip='#9a2a3e',
                         layers=wall_layers(ramp('#c87a80', '#f0b0b0', '#ffe0dc', n=4), ramp('#6a1020', '#9a1c30', '#c43448', '#e0566a', n=6), 'elastic',
                                            ramp('#9a8c78', '#c4b49c', '#e2d6bc', '#f6eedc', n=6))))


def T_sma():
    """the superior mesenteric artery runs in the fat of the mesentery, looping into arcades towards the gut"""
    def extra(far, R):
        y, x = grid(H, WT)
        cb, d, _ = pcells(H, 520, 941, sy=1.0, border=1.2)
        fat = np.zeros(far.shape, np.float32)
        lit = np.clip(0.75 - 0.6 * cb ** 2 + 0.15 * np.clip(1 - d / 8, 0, 1), 0, 1)
        fat[..., :3] = ramp_col(ramp('#7a6020', '#b8962e', '#e0c45a', '#fae49a', n=4), lit)
        fat[..., 3] = 255
        behind(far, fat, 0.85)
        arc = np.zeros_like(far)                          # arterial arcades: loops joining the branches
        for k in range(7):
            cx = k * WT / 7 + R.uniform(0, 60); r_ = R.uniform(40, 70)
            pts = [(cx + np.cos(a) * r_ * 1.4, 150 - np.sin(a) * r_) for a in np.linspace(0.15, np.pi - 0.15, 80)]
            for off in (0, -WT, WT):
                A.stroke(arc, [(p + off, q) for p, q in pts], 4.2, '#2a0408', 220, scale=1.0)
                A.stroke(arc, [(p + off, q) for p, q in pts], 3.0, '#c02438', 230, scale=1.0)
        behind(far, arc, 0.9)
    return vessel_v(dict(seed=904, grad=['#2a0a0e', '#3e1014', '#4e161a', '#3e1014'], endo=(914, ramp('#5e1e20', '#72282a', '#863234', n=3), '#3c1014'),
                         extra=extra, n_open=4, lip='#a8443a',
                         layers=wall_layers(ramp('#d08a80', '#f4bab0', '#ffe4dc', n=4), ramp('#6e1a1c', '#9e2a2a', '#c8443e', '#e2665a', n=6), 'elastic',
                                            ramp('#a08a50', '#c8b070', '#e6d298', '#f8ecc4', n=6))))


def T_efferent():
    """the efferent arteriole: a tiny artery, one layer of smooth muscle cells wound round it; red cells close"""
    def after(far, R):
        y, x = grid(H, WT)
        u = np.mod(x + y * 0.9 + 3 * np.sin(y * 0.04), 9) / 9
        band = np.sin(u * np.pi)                          # each muscle cell a rounded band wound round the vessel
        far[..., :3] *= (0.78 + 0.32 * band[..., None])
        far[..., :3] = far[..., :3] * (1 - 0.12 * band[..., None]) + hexc('#e08a7a') * 0.12 * band[..., None]
        nuc = np.zeros_like(far)
        for k in range(160):
            x0, y0 = R.uniform(0, WT), R.uniform(14, GY)
            for off in (0, -WT, WT):
                ellipse_soft(nuc, x0 + off, y0, 3.2, 0.8, '#3a0c20', 200, ang=-0.84)
        behind(far, nuc, 0.6)
    return vessel_v(dict(seed=905, grad=['#3a1416', '#52201e', '#622a26', '#52201e'], endo=(915, ramp('#6e2a28', '#823432', '#963e3a', n=3), '#4a1818'),
                         after=after, n_open=0, lip='#9a2a3e', n_rbc=40, n_mid=34, mid_size=(15, 20),
                         layers=wall_layers(ramp('#d08a94', '#f4bcc4', '#ffe6ea', n=4), ramp('#5a1428', '#86223a', '#b03a52', '#d05a70', n=6), 'smooth',
                                            ramp('#8a5e6a', '#b48694', '#d8aeb8', '#f0d0d6', n=6))))


def T_pulmvein():
    """a pulmonary vein: thin-walled like a vein, but the blood is bright red, just filled with oxygen"""
    return vessel_v(dict(seed=906, grad=['#3a0608', '#520a0c', '#661010', '#520a0c'], endo=(916, ramp('#7a1a1a', '#902424', '#a42e2e', n=3), '#4a0c0c'),
                         n_open=4, lip='#c84a40', bright=True, glow='#ff8a70', n_rbc=90,
                         layers=wall_layers(ramp('#e0a090', '#fcc8b8', '#fff0e8', n=4), ramp('#7a1418', '#a82024', '#d03a36', '#ec6050', n=6), 'smooth',
                                            ramp('#9a6a5a', '#c4927e', '#e4baa4', '#f8dccc', n=6))))


def T_ivc():
    """the inferior vena cava: the widest vein, thin-walled and without valves; the renal and hepatic veins open in"""
    opens = [(WT * 0.15, 40, 60, 34), (WT * 0.55, 70, 50, 30), (WT * 0.82, 36, 44, 28)]
    return vessel_v(dict(seed=907, grad=['#120a1e', '#1c0e2c', '#26143a', '#1c0e2c'], endo=(917, ramp('#2e1a42', '#3a2050', '#46285e', n=3), '#1a0a2a'),
                         opens=opens, lip='#5a3a8a', mid_haze='#2a1040', vein_obs=True,
                         layers=[(2, ramp('#9a88b0', '#c4b0d8', '#e8dcf4', n=4), 'endo'), (6, ramp('#2e1a4a', '#46286a', '#5e3888', '#7a4ca4', n=6), 'smooth'),
                                 (30, ramp('#6a6080', '#9488a8', '#bcb0cc', '#dcd4e8', n=6), 'loose')]))


def T_pulmart():
    """the pulmonary trunk: thick and elastic like the aorta, but carrying dark blood low in oxygen; it forks in two"""
    opens = [(WT * 0.3 - 46, 60, 42, 32), (WT * 0.3 + 6, 60, 42, 32), (WT * 0.78, 48, 36, 24)]
    return vessel_v(dict(seed=908, grad=['#1e0a1e', '#2e0e2c', '#3c1238', '#2e0e2c'], endo=(918, ramp('#48183e', '#58204a', '#682856', n=3), '#2a0a24'),
                         opens=opens, lip='#8a3a7a', mid_haze='#3a1036',
                         layers=wall_layers(ramp('#b88aa8', '#dcb4cc', '#f8e0ee', n=4), ramp('#4a0e3a', '#701a54', '#963070', '#b8508e', n=6), 'elastic',
                                            ramp('#7a6474', '#a48c9c', '#c8b0c0', '#e6d2de', n=6))))


# ------------------------------------------------------------------ heart chambers
def ventricle(left=False):
    """right ventricle: coarse trabeculae, dark blood, the moderator band bridging the cavity. Left ventricle: a finer
    mesh of trabeculae, two big papillary muscles with their cords, bright blood"""
    if left:
        far = gradient(H, ['#36060e', '#4c0a16', '#5c101e', '#4c0a16'])
        trab_fine(far, 10, GY + 4, 131, ramp('#5a0c16', '#7e1624', '#a42434', '#c83a48', '#ea6066', n=7), '#1a020a', n=120)
    else:
        far = gradient(H, ['#1e040c', '#2e0814', '#3a0c1a', '#2e0814'])
        trabeculae_p(far, 10, GY + 4, 31, ramp('#3a0814', '#561020', '#721a2c', '#902638', '#ae3a4a', n=7), '#14020a', n=40)
    c3 = three(far)
    R = RS(32 if not left else 132)
    pap = [(k * WT / 5 + R.uniform(0, 100), 34, 22) for k in range(5)] if not left else [(k * WT / 2 + R.uniform(60, 300), 52, 34) for k in range(2)]
    for (px_, ph, pw) in pap:                            # papillary muscles with their cords up to the valve
        put(c3, A.papillary(ph, pw), px_ - pw / 2, GY - ph)
        for j in range(4 if not left else 9):
            xa = px_ + R.uniform(-70, 70) * (1 if not left else 1.6)
            pts = [(xa + (px_ - xa) * t, 16 + (GY - ph - 18) * t + 5 * np.sin(t * np.pi)) for t in np.linspace(0, 1, 60)]
            for off in (0, WT, 2 * WT):
                A.stroke(c3, [(a + off, b) for a, b in pts], 1, '#f2dccc', 200, scale=0.7)
    if not left:
        for k in range(2):                               # the moderator band: a thick muscle bridge across the cavity
            x0 = k * WT / 2 + R.uniform(80, 360)
            pts = [((1 - t) ** 2 * x0 + 2 * t * (1 - t) * (x0 + 70) + t * t * (x0 + 190), (1 - t) ** 2 * (GY + 2) + 2 * t * (1 - t) * 50 + t * t * 26) for t in np.linspace(0, 1, 90)]
            for off in (0, WT, 2 * WT):
                P = [(a + off, b) for a, b in pts]
                A.stroke(c3, P, 12, '#14020a', 255, scale=1.0)
                A.stroke(c3, P, 10.4, '#7a1628', 255, scale=1.0)
                A.stroke(c3, [(a, b - 1.8) for a, b in P], 5, '#a62a3c', 230, scale=1.0)
                A.stroke(c3, [(a, b - 3.2) for a, b in P], 1.4, '#e47a88', 200, scale=1.0)
    rbc_flow(c3, 46, 36 if not left else 136, dark=not left)
    wet_glints(c3, 700, 37 if not left else 137, pct=78, a=120, col='#ffe0e6')
    far = crop(c3); haze(far, '#2e0814' if not left else '#400814', 0.22)
    mid = None
    if left:
        mid = wide(); rbc_flow(mid, 16, 143, y0=22, y1=GY - 30, size=(12, 17)); mid = crop(mid)
    MY = MYO_L if not left else [(2, ramp('#d08890', '#f4bcbc', '#ffe4e0', n=4), 'endo'), (24, ramp('#5a0a18', '#8a1628', '#b62638', '#dc4252', n=6), 'striated'),
                                  (30, ramp('#a08030', '#d0b050', '#f0d880', '#fff0b8', n=6), 'fat')]
    floor = wall(MY, True, seed=35 if not left else 135, bumps=0.8, out='#16020a')
    ceil = wall([(2, MY[0][1], 'endo'), (24, MY[1][1], 'striated')], False, seed=33 if not left else 133, bumps=0.8, out='#16020a')
    lf, _ = A.valve_leaflet(48, hang_len())
    obs = {'low': [trab_ridge(30, 18), trab_ridge(24, 15)],
           'tall': [A.thrombus(26, 60, seed=4)],
           'hang': [lf],
           'float': [A.neutrophil(22, seed=7)],
           'huge': [tower(lambda h: A.papillary(int(h), 24))]}
    return dict(far=far, mid=mid, floor=floor, ceil=ceil, obs=obs, coin='o2', special='iron')


def trab_fine(far, y0, y1, seed, cols, out, n=100):
    """the left ventricle's trabeculae: thinner and many more than the right's"""
    from themes import ridge_field_sprite
    R = RS(seed)
    h = y1 - y0
    y, x = grid(h, WT)
    field = np.zeros(y.shape, np.float32)
    for k in range(n):
        x0 = R.uniform(0, WT); a = R.uniform(-1.3, 1.3) + np.pi / 2; th = R.uniform(1.4, 3.2)
        nx, ny = -np.sin(a), np.cos(a)
        for off in (-WT, 0, WT):
            dd = ((x - x0 - off) * nx + (y - h / 2) * ny) + 1.5 * np.sin(y * 0.11 + k)
            field = np.maximum(field, np.clip(1 - (dd / th) ** 2, 0, 1))
    rgb, cov, ring = ridge_field_sprite(field, cols, out)
    reg = far[rows(y0):rows(y0) + y.shape[0]]
    over(reg, np.broadcast_to(hexc(out), rgb.shape), ring)
    over(reg, rgb, cov)


def T_lventricle():
    return ventricle(True)


def T_latrium():
    """the left atrium: its wall is mostly smooth (ridged muscle only in the small auricle); the four pulmonary
    veins open into it; the blood is bright"""
    far = gradient(H, ['#2c040e', '#420816', '#520c1e', '#420816'])
    y, x = grid(GY - 6, WT)
    n_ = noise(y.shape, 9, 141)
    lit = np.clip(0.42 + 0.3 * n_ + 0.1 * np.sin(y / (GY - 6) * np.pi), 0, 1)
    rgb = ramp_col(ramp('#4a0a16', '#681422', '#862232', '#a43444', '#c24c5a', n=7), lit)
    per = WT / 39                                         # the auricle: a short patch of comb-like ridges
    aur = np.exp(-((np.mod(x - WT * 0.6 + WT / 2, WT) - WT / 2) / 70) ** 2)
    ph = np.mod(x + 6 * np.sin(y * 0.03), per) / per
    ridge = np.clip(np.sin(ph * np.pi) * 1.4 - 0.4, 0, 1) * aur
    rgb = rgb * (1 - 0.35 * ridge[..., None]) + hexc('#c84a5a') * 0.35 * ridge[..., None]
    far[px(6):px(6) + y.shape[0], :, :3] = rgb
    c3 = three(far)
    for (x_, y_, bw, bh) in ((WT * 0.08, 50, 40, 28), (WT * 0.08 + 56, 66, 38, 26), (WT * 0.34, 44, 42, 28), (WT * 0.34 + 58, 60, 36, 26)):
        put(c3, opening(bw, bh, '#c04a50'), x_, y_)
    rbc_flow(c3, 40, 141, dark=False)
    scatter(c3, [A.neutrophil(10, 50), lymphocyte(6, 51)], 6, 152, 24, GY - 24, 0.9)
    wet_glints(c3, 600, 153, pct=70, a=120, col='#ffe4e8')
    far = crop(c3); haze(far, '#420816', 0.22)
    mid = wide(); rbc_flow(mid, 16, 143, y0=22, y1=GY - 30, size=(12, 17))
    MY = [(2, ramp('#d08890', '#f4bcbc', '#ffe4e0', n=4), 'endo'), (24, ramp('#5a0a18', '#8a1628', '#b62638', '#dc4252', n=6), 'striated'),
          (30, ramp('#a08030', '#d0b050', '#f0d880', '#fff0b8', n=6), 'fat')]
    floor = wall(MY, True, seed=145, bumps=0.5, out='#16020a')
    ceil = wall([(2, MY[0][1], 'endo'), (24, MY[1][1], 'striated')], False, seed=146, bumps=0.5, out='#16020a')
    obs = {'low': [trab_ridge(28, 16)], 'tall': [A.thrombus(24, 58, seed=9)], 'hang': [flip_v(trab_ridge(30, hang_len()))], 'float': [A.neutrophil(20, seed=9)],
           'huge': [tower(lambda h: A.thrombus(24, int(h), seed=10))]}
    return dict(far=far, mid=crop(mid), floor=floor, ceil=ceil, obs=obs, coin='o2', special='iron')


# ------------------------------------------------------------------ lung: a bronchiole (the airway before the air sacs)
def cilia_surface(c3, edge_w, e0, top_edge):
    R = RS(161 + top_edge)
    for k in range(int(WT / 0.5)):
        x = R.uniform(0, WT)
        ex = e0 + np.interp(x, np.arange(WT), edge_w)
        L = R.uniform(1.2, 2.2); lean = R.uniform(0.2, 0.6)
        y0 = ex - 0.4 if top_edge else ex + 0.4
        y1 = (y0 - L) if top_edge else (y0 + L)
        for off in (0, WT, 2 * WT):
            A.stroke(c3, [(x + off, y0), (x + off + lean, y1)], 0.25, '#f0c8cc', 200, scale=1.0)


def cilia_pat(sh, x, ld, u, shape, h, R):
    """ciliated columnar cells: tall cells side by side, nuclei at different heights, a goblet cell here and there"""
    xx = x + 0.3 * per_sin(x, 83, 0.2)
    border = band_line(xx, 2.2, 0.25)
    cxp = np.mod(xx, 2.2) - 1.1
    lvl = 1.6 + 1.2 * np.sin(np.floor(xx / 2.2) * 2.7)
    nuc = np.clip(1 - np.sqrt((cxp / 0.7) ** 2 + ((ld - lvl) / 0.95) ** 2), 0, 1) ** 0.5
    gob = np.clip(1 - np.sqrt((np.mod(xx, 15.4) - 7.7) ** 2 / 1.2 ** 2 + ((ld - 1.4) / 1.6) ** 2), 0, 1)
    return sh - 0.2 * border - 0.4 * nuc + 0.35 * gob


def pollen(d=16, seed=1):
    """a pollen grain breathed in: a round grain covered in short spikes"""
    y, x = grid(d, d)
    c = (d - 1) / 2
    ang = np.arctan2(y - c, x - c)
    rr = np.sqrt((x - c) ** 2 + (y - c) ** 2)
    spike = np.clip(np.cos(ang * 14) * np.cos(ang * 3 + 1.0), 0, 1) ** 3
    m = rr <= d / 2 - 2.2 + 2.0 * spike
    spr = A.mask_sprite(m, ramp('#7a5a08', '#b8901a', '#e6c03a', '#fae27a', '#fff6c4'), '#2e2004', soft=1.0, hl_t=0.97)
    I = spr[SC:-SC, SC:-SC]
    pores = np.zeros(I.shape[:2], np.float32)
    for a in (0.6, 2.7, 4.6):
        pores += np.clip(1 - np.sqrt((x - c - np.cos(a) * d * 0.2) ** 2 + (y - c - np.sin(a) * d * 0.2) ** 2) / 1.1, 0, 1)
    I[..., :3] *= (1 - 0.35 * np.clip(pores, 0, 1)[..., None])
    return spr


def T_bronchiole():
    import eye as E
    far = gradient(H, ['#24101a', '#341824', '#40202c', '#341824'])
    y, x = grid(H, WT)
    # the airway seen from inside: rings drawn in by its smooth muscle, a velvet of cilia, glistening mucus
    per = WT / 26
    u = np.mod(x + 5 * np.sin(y * 0.035), per) / per
    ring = np.sin(u * np.pi) ** 1.5
    vel = noise(y.shape, 0.25, 171)
    lit = np.clip(0.3 + 0.45 * ring + 0.06 * vel + 0.1 * np.sin(y / H * np.pi), 0, 1)
    far[..., :3] = ramp_col(ramp('#3a1a22', '#5a2a34', '#7c3e48', '#9e5660', '#c27880', '#e4a0a4', n=7), lit)
    groove = np.clip(1 - np.abs(u - 0.02) / 0.04, 0, 1) + np.clip(1 - np.abs(u - 0.98) / 0.04, 0, 1)
    far[..., :3] *= (1 - 0.3 * groove[..., None])
    c3 = three(far)
    R = RS(172)
    for k in range(5):                                   # mouths of the next, smaller airways
        bw = R.uniform(30, 46)
        put(c3, opening(int(bw), int(bw * 0.62), '#c8828a', deep=('#0a0408', '#160810', '#2a1420')), k * WT / 5 + R.uniform(0, 140), R.uniform(30, 92))
    for k in range(60):                                  # strands and drops of mucus on the wall
        x0, y0 = R.uniform(0, WT), R.uniform(18, GY - 10)
        L = R.uniform(6, 22)
        for off in (0, WT, 2 * WT):
            A.stroke(c3, [(x0 + off + t, y0 + 1.2 * np.sin(t * 0.4)) for t in np.linspace(0, L, 10)], 0.8, '#f4e8e0', 110, scale=1.0)
    wet_glints(c3, 900, 173, pct=65, a=150, col='#ffffff')
    far = crop(c3); haze(far, '#341824', 0.2)
    mid = np.zeros((px(H), px(WT), 4), np.float32)
    for k in range(10):                                  # breathed-in specks: pollen and dust drifting with the air
        s = pollen(R.uniform(6, 9), k) if k % 2 == 0 else E.knot(R.uniform(5, 8), R.uniform(3, 5), 500 + k, ramp('#3a3430', '#6a625a', '#9a9088', '#cac0b6'), '#16120e', '#2a2420')
        E.putw(mid, s, R.uniform(0, WT), R.uniform(24, GY - 30), 0.85)
    EPI = ramp('#7a3a48', '#a85a68', '#cc808a', '#ecaab0', n=6)
    floor = wall([(0.8, ramp('#f0dcd8', '#fff4f0', '#ffffff', n=3), 'endo'), (4.5, EPI, cilia_pat), (3, ramp('#5a1a24', '#7e2a36', '#a03e4a', n=4), 'smooth'),
                  (30, ramp('#8a6a6a', '#b4928e', '#d8b8b2', '#f0d8d2', n=6), 'loose')], True, seed=175, bumps=0.7, out='#1e0a10', surface=cilia_surface)
    ceil = wall([(0.8, ramp('#f0dcd8', '#fff4f0', '#ffffff', n=3), 'endo'), (4.5, EPI, cilia_pat), (20, ramp('#5a1a24', '#7e2a36', '#a03e4a', n=4), 'smooth')],
                False, seed=176, bumps=0.7, out='#1e0a10', surface=cilia_surface)
    MUC = ramp('#5a6a4a', '#8a9a72', '#b8c69a', '#e2ecc8', '#fbfff0')
    obs = {'low': [E.knot(24, 14, 31, MUC, '#1e2614', '#4a5a3a'), E.knot(22, 13, 33, MUC, '#1e2614', '#4a5a3a')],
           'tall': [E.rope(58, 14, MUC, '#1e2614', seed=35)],
           'hang': [E.rope(hang_len(), 14, MUC, '#1e2614', seed=36, fray=14)],
           'float': [pollen(17, 3)],
           'huge': [tower(lambda h: E.rope(int(h), 18, MUC, '#1e2614', seed=39))]}
    return dict(far=far, mid=mid, floor=floor, ceil=ceil, obs=obs, coin='o2', special='iron')


# ------------------------------------------------------------------ the lobes: the brain's surface seen from the fluid around it
LOBE = {
    # CSF tint, grey-matter colours (the textbook lobe colours, softened), web density, artery width, stripe of Gennari
    'temporal': (['#0a1c1e', '#10282a', '#163234', '#10282a'], ramp('#2e5a4e', '#4a7a6a', '#6a9a88', '#90baa8', n=6), 55, 6.5, False),
    'parietal': (['#16141e', '#201c2a', '#2a2436', '#201c2a'], ramp('#6a5630', '#8a7446', '#ac9662', '#ccb886', n=6), 85, 5.0, False),
    'occipital': (['#1a1020', '#24162c', '#2e1c38', '#24162c'], ramp('#723450', '#94506c', '#b4708c', '#d494ae', n=6), 70, 4.6, True),
}


def arach_v(lobe):
    """a lobe's own look: the fluid's tint, the colour of its grey matter, its vessels (the temporal lobe has the
    big middle cerebral artery running over it) and, in the occipital lobe, the white stripe of Gennari through the
    visual cortex"""
    from themes import pial_arch, strand_column, web_hang, PIA_L
    grad, gray, n_web, aw, gennari = LOBE[lobe]
    far = gradient(H, grad)
    c3 = three(far)
    R = RS({'temporal': 251, 'parietal': 252, 'occipital': 253}[lobe])
    for k in range(n_web):
        x0 = R.uniform(0, WT); x1 = x0 + R.uniform(-60, 60)
        pts = [(x0 + (x1 - x0) * t + 3 * np.sin(t * 6 + k), 14 + (GY - 14) * t) for t in np.linspace(0, 1, 80)]
        for off in (0, WT, 2 * WT):
            A.stroke(c3, [(a + off, b) for a, b in pts], 1, '#7a8aa8' if k % 3 else '#a8b4cc', 150, scale=0.6)
    ph = R.uniform(0, TAU)
    for (yy, col, w) in ((GY - 18, '#a82838', aw), (40, '#5a2a6a', 4)):
        pts = [(x, yy + 7 * np.sin(x * TAU * 3 / WT + ph) + 3 * np.sin(x * TAU * 11 / WT + ph)) for x in np.arange(0, 3 * WT, 1.5)]
        A.stroke(c3, pts, w + 1.6, '#120818', scale=1.0)
        A.stroke(c3, pts, w, col, scale=1.0)
        A.stroke(c3, [(a, b + w * 0.22) for a, b in pts], w * 0.35, '#000000', 60, scale=1.0)
        A.stroke(c3, [(a, b - w * 0.22) for a, b in pts], w * 0.3, '#e88a98' if col == '#a82838' else '#9a6aaa', scale=1.0)
    for (yy, col, w, sgn) in ((GY - 18, '#a82838', aw * 0.45, -1), (40, '#5a2a6a', 1.8, 1)):
        for k in range(14 if lobe == 'temporal' else 10):
            x0 = R.uniform(0, WT); y_ = yy + 7 * np.sin(x0 * TAU * 3 / WT + ph) + 3 * np.sin(x0 * TAU * 11 / WT + ph)
            a0 = sgn * np.pi / 2 + R.uniform(-0.9, 0.9); L = R.uniform(14, 40)
            pts = [(x0 + np.cos(a0) * t + 1.5 * np.sin(t * 0.3 + k), y_ + np.sin(a0) * t) for t in np.linspace(0, L, 30)]
            for off in (0, WT, 2 * WT):
                A.stroke(c3, [(p + off, q) for p, q in pts], w + 1.2, '#120818', scale=1.0)
                A.stroke(c3, [(p + off, q) for p, q in pts], w, col, scale=1.0)
    scatter(c3, [lymphocyte(5, 61), lymphocyte(6, 62), microglia(63, '#8aa0c8')], 18, R.randint(1000), 30, GY - 30, 0.85)
    drift(c3, 60, ['#9ab8e0', '#d0e0ff'], R.randint(1000), a=160)
    far = crop(c3); haze(far, grad[1], 0.2)
    if gennari:
        layers = [(2, PIA_L[0][1], 'endo'), (8, gray, 'gray'), (1.6, ramp('#d8c8d8', '#f0e4f0', '#fff8ff', n=3), 'white'), (12, gray, 'gray'), (30, PIA_L[2][1], 'white')]
    else:
        layers = [(2, PIA_L[0][1], 'endo'), (22, gray, 'gray'), (30, PIA_L[2][1], 'white')]
    floor = wall(layers, True, seed=R.randint(1000), bumps=2.4, out='#1a0e24')
    ceil = wall([(2, ramp('#8a9ab8', '#b8c4d8', '#e0e8f4', n=4), 'endo'), (6, ramp('#4a5a7a', '#6a7a98', '#8a98b4', n=4), 'loose'),
                 (20, ramp('#5a4a4a', '#7a6a66', '#9a8a84', n=4), 'loose')], False, seed=R.randint(1000), bumps=0.6, out='#0a1220')
    obs = {'low': [pial_arch(34, 20)], 'tall': [strand_column(60)], 'hang': [web_hang()], 'float': [macrophage()], 'huge': [tower(lambda h: strand_column(int(h)))]}
    return dict(far=far, mid=None, floor=floor, ceil=ceil, obs=obs, coin='o2', special='omega')


def T_temporal():
    return arach_v('temporal')


def T_parietal():
    return arach_v('parietal')


def T_occipital():
    return arach_v('occipital')


# ------------------------------------------------------------------ white matter: the medulla and the optic nerve
def axon_lanes(c3, lanes, dims, R, top='#ecebf8', bgc='#161428'):
    """long myelinated axons along the way (as in themes.T_fibres), on given lanes"""
    y, x = grid(H, 3 * WT)
    bgc = hexc(bgc)
    for k, (yy, dim) in enumerate(zip(lanes, dims)):
        th = 4 if dim > 0.3 else 5
        node = int(R.uniform(26, 40))
        xr = x[0]
        yc = yy + 1.5 * np.sin(xr * TAU * (2 + k % 3) / WT + k)
        r0, r1 = px(yy - 6), px(yy + 7)
        ys = y[r0:r1, :1]
        dy = ys - yc[None, :]
        xm = np.mod(np.mod(xr, WT), node)
        dn = np.minimum(xm, node - xm)
        rr = (th / 2) * np.sqrt(np.clip((dn - 0.9) / 1.8, 0, 1))[None, :]
        sheath = np.clip((rr - np.abs(dy)) * SC + 0.5, 0, 1) * (rr > 0)
        edge = np.clip((rr + 0.6 - np.abs(dy)) * SC + 0.5, 0, 1) * (rr > 0)
        cyl = np.sqrt(np.clip(1 - (dy / np.maximum(rr, 0.3)) ** 2, 0, 1))
        lit = np.clip(0.35 + 0.65 * cyl - 0.35 * np.clip(dy / np.maximum(rr, 0.3), 0, 1), 0, 1)
        spec = np.clip(1 - np.abs(dy / np.maximum(rr, 0.3) + 0.35) / 0.18, 0, 1) * 0.5
        tc = hexc(top)
        col = tc * lit[..., None] + np.array([40, 36, 70], np.float32) * (1 - lit[..., None])
        col = col * (1 - spec[..., None]) + 255 * spec[..., None]
        col = col * (1 - dim) + bgc * dim
        reg = c3[r0:r1]
        over(reg, np.broadcast_to(hexc('#0c0a18'), reg.shape[:2] + (3,)), edge)
        over(reg, col, sheath)
        ax = np.clip((0.9 - np.abs(dy)) * SC + 0.5, 0, 1) * (rr < 0.9)
        over(reg, np.broadcast_to(hexc('#c87a3a'), reg.shape[:2] + (3,)), ax)


def T_medulla():
    """the medulla: the pyramids' fibres running down along it, and the inferior olive, a crumpled ribbon of grey
    matter like a folded purse"""
    from themes import WHITE_L
    far = gradient(H, ['#140c1c', '#1c1228', '#241834', '#1c1228'])
    c3 = three(far)
    R = RS(261)
    for (cx, cy, rx, ry, a0) in ((WT * 0.25, 82, 70, 42, 0.3), (WT * 0.72, 76, 62, 38, 3.4)):
        th = np.linspace(a0 + 0.5, a0 + TAU - 0.5, 700)            # left open at the hilum
        rr = 1 + 0.13 * np.sin(th * 11) + 0.04 * np.sin(th * 23)
        pts = [(cx + np.cos(t) * rx * r_, cy + np.sin(t) * ry * r_) for t, r_ in zip(th, rr)]
        for off in (0, WT, 2 * WT):
            P = [(p + off, q) for p, q in pts]
            A.stroke(c3, P, 7.0, '#0e0818', 255, scale=1.0)
            A.stroke(c3, P, 5.6, '#5a4a74', 255, scale=1.0)
            A.stroke(c3, [(p, q - 1.2) for p, q in P], 1.6, '#8a7aa8', 200, scale=1.0)
        for k in range(160):                                       # its nerve cells
            t = R.uniform(a0 + 0.5, a0 + TAU - 0.5); r_ = 1 + 0.13 * np.sin(t * 11) + 0.04 * np.sin(t * 23) + R.uniform(-0.04, 0.04)
            for off in (0, WT, 2 * WT):
                disc(c3, cx + off + np.cos(t) * rx * r_, cy + np.sin(t) * ry * r_, 0.6, '#d8c8f0', 200)
    axon_lanes(c3, [22, 29, 125, 132, 139, 146], [0.45, 0.3, 0.2, 0.35, 0.1, 0.25], R, bgc='#1c1228')
    for (yy_, kw) in ((40, 3), (112, 4)):
        capillary_band(c3, yy_, kw, '#6a2a40', '#3a0c1c', amp=1.5)
    for k in range(10):
        s = astro_sprite(5, R, '#8a90c0', '#2a2a50')
        put(c3, s, R.uniform(0, WT) - s.shape[1] / SC / 2, R.uniform(20, GY - 10) - s.shape[0] / SC / 2)
    far = crop(c3); haze(far, '#1c1228', 0.2)
    floor = wall(WHITE_L, True, seed=265, bumps=0.8, out='#100e20')
    ceil = wall([(2, WHITE_L[0][1], 'endo'), (24, WHITE_L[1][1], 'white')], False, seed=266, bumps=0.8, out='#100e20')
    obs = {'low': [oligo()], 'tall': [cross_bundle(60)], 'hang': [flip_v(cross_bundle(hang_len()))], 'float': [macrophage(20)], 'huge': [tower(lambda h: cross_bundle(int(h)))]}
    return dict(far=far, mid=None, floor=floor, ceil=ceil, obs=obs, coin='o2', special='omega')


def T_opticnerve():
    """the optic nerve: its fibres packed in bundles walled off by pale septa, and the central retinal artery and vein
    running along its middle"""
    from themes import WHITE_L
    far = gradient(H, ['#0a0e1c', '#101628', '#161e34', '#101628'])
    c3 = three(far)
    R = RS(271)
    y, x = grid(H, 3 * WT)
    for yy in (34, 60, 110, 136):                                  # the septa between the bundles
        yc = yy + 2.5 * np.sin(x[0] * TAU * 4 / WT + yy)
        d = np.abs(y - yc[None, :])
        k = np.clip((1.8 - d) * SC * 0.5 + 0.5, 0, 1)
        over(c3, np.broadcast_to(hexc('#c89aa8'), c3.shape[:2] + (3,)), k * 0.85)
        over(c3, np.broadcast_to(hexc('#f0d0d8'), c3.shape[:2] + (3,)), np.clip((0.5 - np.abs(y - yc[None, :] + 0.6)) * SC * 0.5 + 0.5, 0, 1) * 0.6)
    for yy in (34, 60, 110, 136):                                  # little vessels in the septa
        for k in range(16):
            x0 = R.uniform(0, WT); yc_ = yy + 2.5 * np.sin(x0 * TAU * 4 / WT + yy)
            for off in (0, WT, 2 * WT):
                ellipse_soft(c3, x0 + off, yc_, R.uniform(1.2, 2.2), 0.7, '#c02838', 220)
    axon_lanes(c3, [18, 25, 44, 51, 70, 98, 120, 127, 145], [0.4, 0.2, 0.3, 0.1, 0.35, 0.3, 0.15, 0.4, 0.25], R, top='#e4ecf8', bgc='#101628')
    for (yy, col, w) in ((80, '#c02838', 4.6), (89, '#4a2a6a', 5.2)):  # central retinal artery and vein
        pts = [(x_, yy + 1.5 * np.sin(x_ * TAU * 3 / WT)) for x_ in np.arange(0, 3 * WT, 1.5)]
        A.stroke(c3, pts, w + 1.6, '#0a0810', scale=1.0)
        A.stroke(c3, pts, w, col, scale=1.0)
        A.stroke(c3, [(a, b - w * 0.25) for a, b in pts], w * 0.3, '#ff9aa6' if col == '#c02838' else '#8a6aaa', scale=1.0)
    far = crop(c3); haze(far, '#101628', 0.2)
    floor = wall([(2, ramp('#c8a0b0', '#e8c8d4', '#fae8f0', n=4), 'endo'), (4, ramp('#8a7a98', '#aa9ab8', '#cabad8', n=4), 'loose'), (30, WHITE_L[1][1], 'white')],
                 True, seed=275, bumps=0.6, out='#100e20')
    ceil = wall([(2, ramp('#c8a0b0', '#e8c8d4', '#fae8f0', n=4), 'endo'), (24, WHITE_L[1][1], 'white')], False, seed=276, bumps=0.6, out='#100e20')
    obs = {'low': [oligo()], 'tall': [cross_bundle(60)], 'hang': [flip_v(cross_bundle(hang_len()))], 'float': [macrophage(20)], 'huge': [tower(lambda h: cross_bundle(int(h)))]}
    return dict(far=far, mid=None, floor=floor, ceil=ceil, obs=obs, coin='o2', special='omega')


# ------------------------------------------------------------------ small intestine: duodenum (bile, Brunner's glands), ileum (Peyer's patches)
def brunner_pat(sh, x, ld, u, shape, h, R):
    """Brunner's glands in the duodenum's submucosa: clusters of pale mucous glands"""
    cb, d, _ = pcells(h, int(WT * h / 9), 281, sy=1.0, border=0.4)
    acin = np.clip(1 - d / 1.8, 0, 1)
    return sh + 0.25 * acin - 0.2 * cb


def gut_v(kind):
    from themes import gut_surface, GUT_L, hang_villi
    duo = kind == 'duodenum'
    far = gradient(H, ['#2a0c10', '#3a1216', '#4a1a1c', '#3a1216'] if duo else ['#2c0a16', '#3e0e20', '#4e1428', '#3e0e20'])
    c3 = three(far)
    R = RS(291 if duo else 292)
    for k in range(4 if duo else 2):                      # circular folds far behind (fewer in the ileum)
        fx = k * WT / (4 if duo else 2) + R.uniform(-40, 40)
        fold = ellipse_mask(240, 150)
        yy, _ = grid(150, 240)
        fs = paint(fold, ramp('#4a1a1c', '#5a2224', '#6a2a2a', n=3) if duo else ramp('#4e1428', '#5e1c32', '#6e243a', n=3), np.clip(0.9 - yy / 180.0, 0, 1))
        put(c3, outline(fs, '#2a0810'), fx - 120, GY - 80)
    if not duo:                                           # Peyer's patches: pale domes of lymphoid follicles in the wall
        for k in range(5):
            cx = k * WT / 5 + R.uniform(0, 120); rw = R.uniform(46, 70)
            y_, x_ = grid(40, rw * 2)
            m = ((x_ - rw) / rw) ** 2 + ((y_ - 40) / 38) ** 2 <= 1
            dome = A.mask_sprite(m, ramp('#8a5a6a', '#b88a96', '#dcb4bc', '#f4dce0'), '#2a0c18', soft=3.0, hl_t=0.99)
            I = dome[SC:-SC, SC:-SC]
            R2 = RS(300 + k)
            for j in range(260):
                gx, gy = R2.uniform(2, rw * 2 - 2), R2.uniform(4, 39)
                if A.on(I, gx, gy):
                    disc(I, gx, gy, R2.uniform(0.35, 0.6), '#4a2a6a', 190)
            put(c3, dome, cx - rw, GY - 36)
    scale = 1.0 if duo else 0.7
    for layer, (n, hmin, hmax, w, dim) in enumerate([(130, 26, 50, 7, 0.62), (90, 34, 66, 9, 0.38), (54, 44, 80, 11, 0.12)]):
        xs = np.sort(R.uniform(0, WT, int(n * (1.0 if duo else 0.7))))
        for xx in xs:
            hh = int(R.uniform(hmin, hmax) * scale); hang = R.uniform() < 0.3
            v = A.villus_real(hh if not hang else int(hh * 0.6), w + (3 if duo else 0), int(xx * 13 + layer * 101 + 7), hang=hang, dim=dim)
            put(c3, v, xx, (GY - hh + 4) if not hang else 8)
    wet_glints(c3, 700, R.randint(1000), pct=80)
    drift(c3, 90, ['#a8b030', '#d0c850', '#8a9a20'] if duo else ['#e8c070', '#f4dca0'], R.randint(1000))
    far = crop(c3); haze(far, '#3a1a10' if duo else '#3e0e20', 0.3)
    if duo:                                               # bile just poured in: a yellow-green cast over everything
        far[..., :3] = far[..., :3] * 0.88 + hexc('#8a8a20') * 0.12
    mid = wide()
    for k in range(9):
        put(mid, A.food_bit(seed=60 + k, w=R.uniform(5, 8), h=R.uniform(3.5, 5.5)), R.uniform(0, WT), R.uniform(30, GY - 40), 0.88)
    for k in range(14 if duo else 8):
        r_ = R.uniform(1.2, 2.4); m_ = ellipse_mask(2 * r_ + 1, 2 * r_ + 1)
        cols = ramp('#5a6a10', '#8aa020', '#c4d050', '#f0f4b0') if duo else ramp('#a07a10', '#e0b830', '#fff090', '#ffffe0')
        put(mid, A.mask_sprite(m_, cols, '#2a3404' if duo else '#4a3604', soft=0.6, ambient=0.4, hl_t=0.93), R.uniform(0, WT), R.uniform(26, GY - 34), 0.85)
    if duo:
        L = [GUT_L[0], GUT_L[1], (5, ramp('#a08a7a', '#c8b4a4', '#e8d8cc', '#fff4ec', n=6), brunner_pat), GUT_L[3]]
    else:
        L = [(8, ramp('#5a1430', '#9a2e4c', '#c85068', '#e8788a', n=6), 'crypts'), GUT_L[1], GUT_L[2], GUT_L[3]]
    floor = wall(L, True, seed=R.randint(1000), bumps=1.0, out='#22080a', surface=gut_surface)
    ceil = wall([(6, L[0][1], 'crypts'), (2, GUT_L[1][1], 'smooth'), (3, GUT_L[2][1], 'loose'), (20, GUT_L[3][1], 'smooth')], False, seed=R.randint(1000), bumps=1.0, out='#20060c', surface=gut_surface)
    obs = {'low': [A.chyme_fat(seed=s) for s in (2, 4, 5)],
           'tall': [A.plica(60, 34, seed=s) for s in (7, 9)],
           'hang': [hang_villi(seed=s) for s in (1, 2)],
           'float': [A.e_coli()],
           'huge': [tower(lambda h: A.plica(int(h), 18, seed=11))]}
    return dict(far=far, mid=crop(mid), floor=floor, ceil=ceil, obs=obs, coin='vitC', special='fiber')


def T_duodenum():
    return gut_v('duodenum')


def T_ileum():
    return gut_v('ileum')


# ------------------------------------------------------------------ large intestine: cecum, colon (taenia), rectum (no haustra), anal canal
def colon_far(far, kind, R):
    """the lining far behind: haustra between crescent folds (colon, cecum), the rectum's few big shelves, the anal
    canal's columns above the pectinate line and smooth skin-like lining below it"""
    h = H - 16
    y, x = grid(h, WT)
    if kind in ('colon', 'cecum'):
        per = WT / (9 if kind == 'colon' else 6)
        bend = 10 * np.sin((y / h) * np.pi)
        u = np.mod(x + bend, per)
        ph = u / per
        pouch = np.sin(ph * np.pi) * (0.75 + 0.25 * np.sin((y / h) * np.pi))
        lit = np.clip(0.3 + 0.5 * pouch - 0.35 * np.clip(ph - 0.55, 0, 1) + 0.1 * np.sin((y / h) * np.pi), 0, 1)
        cols = ramp('#4a1c16', '#6a2c22', '#8e4232', '#b05a44', '#cc7a5e', '#e09a7c', n=8) if kind == 'colon' else ramp('#4e2018', '#703226', '#944a38', '#b6644c', '#d28466', '#e8a888', n=8)
        rgb = ramp_col(cols, lit)
        dist_f = np.minimum(u, per - u)
        ridge = np.clip((8.5 - dist_f) / 2.0, 0, 1) * (u > per * 0.5) + np.clip((8.0 - u) / 1.0, 0, 1) * (u <= per * 0.5)
        rgb = rgb * (1 - 0.6 * ridge[..., None]) + hexc('#f0b090') * 0.6 * ridge[..., None]
        rgb *= (1 - 0.38 * np.clip(1 - np.abs(u - 13.5) / 4.5, 0, 1)[..., None])
        edge = np.clip((0.55 - np.abs(u - 8.6)) * SC + 0.5, 0, 1)
        rgb = rgb * (1 - edge[..., None]) + hexc('#1e0a06') * edge[..., None]
        if kind == 'colon':                               # a taenia coli: a flat band of muscle running the whole way
            tb = np.clip((5.5 - np.abs(y - 26 - 2 * np.sin(x * TAU * 9 / WT))) * SC * 0.4 + 0.5, 0, 1)
            rgb = rgb * (1 - 0.55 * tb[..., None]) + hexc('#d8a088') * 0.55 * tb[..., None]
            rgb *= (1 - 0.25 * np.clip(1 - np.abs(np.abs(y - 26 - 2 * np.sin(x * TAU * 9 / WT)) - 5.8) / 0.8, 0, 1)[..., None])
    elif kind == 'rectum':
        n_ = noise(y.shape, 6, 311)
        lit = np.clip(0.42 + 0.22 * n_, 0, 1)
        rgb = ramp_col(ramp('#3a0e10', '#561a1a', '#742a26', '#923c34', '#b05446', n=7), lit)
        for (cx, cy, rw, up) in ((WT * 0.12, 60, 150, 1), (WT * 0.45, 100, 170, -1), (WT * 0.78, 54, 140, 1)):   # Houston's valves
            dx = np.mod(x - cx + WT / 2, WT) - WT / 2
            shelf = np.clip(1 - (dx / rw) ** 2, 0, 1) ** 0.5
            yy_ = cy + up * 14 * (dx / rw) ** 2
            d = (y - yy_) * up
            band = np.clip(1 - np.abs(d) / 9, 0, 1) * shelf
            rgb = rgb * (1 - 0.6 * band[..., None]) + hexc('#d07a62') * 0.6 * band[..., None]
            rgb *= (1 - 0.45 * (np.clip(1 - np.abs(d - 10) / 4, 0, 1) * shelf)[..., None])
    else:                                                 # anal canal
        per = WT / 60
        u = np.mod(x + 1.5 * np.sin(y * 0.06), per) / per
        col_ = np.sin(u * np.pi) ** 1.3
        pect = 108 + 3 * np.sin(x * TAU * 60 / WT * 2)        # the pectinate line, scalloped by the anal valves
        above = np.clip((pect - y) / 3, 0, 1)
        lit = np.clip(0.28 + 0.5 * col_ * above + 0.38 * (1 - above) + 0.05 * noise(y.shape, 0.5, 321), 0, 1)
        top = ramp_col(ramp('#4a1418', '#6e2226', '#923632', '#b04c44', '#cc6a5e', n=7), lit)
        skin = ramp_col(ramp('#7a4a48', '#a06c66', '#c49088', '#e0b4aa', '#f4d4cc', n=7), lit)
        rgb = top * above[..., None] + skin * (1 - above[..., None])
        line = np.clip(1 - np.abs(y - pect) / 1.2, 0, 1)
        rgb = rgb * (1 - 0.5 * line[..., None]) + hexc('#3a1010') * 0.5 * line[..., None]
    far[px(8):px(8) + y.shape[0], :, :3] = rgb


def colon_v(kind):
    from themes import COLON_L
    far = gradient(H, {'colon': ['#2a100c', '#3a1610', '#4a1e16', '#3a1610'], 'cecum': ['#2e120e', '#401a12', '#50221a', '#401a12'],
                       'rectum': ['#240a0a', '#341010', '#421614', '#341010'], 'anus': ['#2a1012', '#3a1618', '#4a1e1e', '#3a1618']}[kind])
    R = RS({'colon': 331, 'cecum': 332, 'rectum': 333, 'anus': 334}[kind])
    colon_far(far, kind, R)
    c3 = three(far)
    if kind == 'cecum':                                   # the ileocecal valve (two lips) and the little mouth of the appendix
        for cx in (WT * 0.3, WT * 0.8):
            for (dy, lip) in ((-7, '#e09a80'), (7, '#d08a70')):
                y_, x_ = grid(14, 70)
                m = ((x_ - 35) / 35) ** 2 + ((y_ - 7) / 7) ** 2 <= 1
                put(c3, A.mask_sprite(m, ramp('#6a2a20', '#9a4636', '#c66a54', lip, '#ffd0c0'), '#1a0806', soft=2.0), cx - 35, 70 + dy - 7)
            put(c3, opening(30, 7, '#a04a3a', deep=('#0a0202', '#1a0606', '#2a0e0a')), cx - 15, 73)
        ax = WT * 0.55
        put(c3, opening(18, 14, '#b05a46', deep=('#0a0202', '#1a0606', '#2a0e0a')), ax - 9, 92)
        for k in range(10):                              # folds converging on it
            a0 = k / 10 * TAU
            pts = [(ax + np.cos(a0) * r_, 99 + np.sin(a0) * r_ * 0.8) for r_ in np.linspace(10, 30, 12)]
            for off in (0, WT, 2 * WT):
                A.stroke(c3, [(p + off, q) for p, q in pts], 1.6, '#e0a08a', 120, scale=1.0)
    if kind == 'anus':                                    # the venous cushions (haemorrhoidal plexus) under the columns
        vessels_p(c3, 14, 104, 34, 341, '#5a2a6a', a=150, wdt=1.4)
    else:
        vessels_p(c3, 10, H - 12, 40 if kind != 'rectum' else 60, R.randint(1000), '#9a1e22' if kind != 'rectum' else '#6a2a5a')
    wet_glints(c3, 500, R.randint(1000), pct=70, a=80)
    drift(c3, 50, ['#7a5a2a', '#a07a3a', '#c8a060'], R.randint(1000))
    far = crop(c3); haze(far, {'colon': '#3a1610', 'cecum': '#401a12', 'rectum': '#341010', 'anus': '#3a1618'}[kind], 0.24)
    mid = wide()
    for k in range(8 if kind != 'cecum' else 16):
        put(mid, bubble(int(R.uniform(5, 10)), k), R.uniform(0, WT), R.uniform(24, GY - 40), 0.8)
    if kind == 'anus':
        L = [(3, ramp('#c09088', '#e0b4aa', '#f4d4cc', '#fff0ea', n=6), 'squamous'), (8, ramp('#4a1612', '#6e2420', '#94342c', '#b44a3e', n=6), 'smooth'),
             (30, ramp('#5a1414', '#841e1e', '#a82e2c', '#c84440', n=6), 'striated')]
        floor = wall(L, True, seed=345, bumps=1.6, out='#1a0806')
        ceil = wall([(3, L[0][1], 'squamous'), (8, L[1][1], 'smooth'), (20, L[2][1], 'striated')], False, seed=346, bumps=1.6, out='#1a0806')
    else:
        floor = wall(COLON_L, True, seed=R.randint(1000), bumps=1.4, out='#1a0806')
        ceil = wall([(5, COLON_L[0][1], 'crypts'), (2, COLON_L[1][1], 'smooth'), (3, COLON_L[2][1], 'loose'), (20, COLON_L[3][1], 'smooth')], False, seed=R.randint(1000), bumps=1.4, out='#1a0806')
    obs = {'low': [feces(24, 15, s) for s in (1, 2, 3)],
           'tall': [stack([feces(28, 22, 4), feces(24, 20, 5), feces(18, 16, 6)])],
           'hang': [semilunar_fold(s) for s in (1, 2)],
           'float': [bubble(11, 3), A.e_coli()],
           'huge': [food_tower(range(60, 66), lambda s, w, h: feces(w, h, s))]}
    return dict(far=far, mid=crop(mid), floor=floor, ceil=ceil, obs=obs, coin='vitC', special='fiber')


def T_cecum():
    return colon_v('cecum')


def T_rectum():
    return colon_v('rectum')


def T_anus():
    return colon_v('anus')
