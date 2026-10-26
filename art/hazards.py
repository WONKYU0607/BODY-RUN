# The v19 hazards, in the style of the rest (rounded, softly shaded, dark outline, a glossy spot), HD:
#  drops that fall from the ceiling and splash into a puddle (mucus, bile, a blood clot, clear fluid),
#  spikes that shoot up out of the floor (a fleshy polyp, a calcified plaque spike, a nerve thorn, a crystal shard),
#  the leaflets of a gate (a heart valve's pale cusp, a sphincter's muscular lip; one from the floor, one from the ceiling),
#  an antibody flying at you.
# Laid out in world units; every sprite is outlined (one unit of padding on every side).
import numpy as np
from scipy import ndimage
from art import SC, px, grid, ramp, hexc, paint, outline, inner, over, paste, ellipse_soft, smooth_mask, canvas
import anatomy as A
import sprites as S

LIGHT = (-0.55, -0.7, 0.45)

DROP = {   # ramp (dark .. light), outline, opacity of the body (a little see-through for the clear ones)
    'mucus': (ramp('#56662a', '#8a9c48', '#b8c870', '#dce6a4', '#f6fadc'), '#1e2408', 0.9),
    'bile': (ramp('#28400c', '#456e16', '#6c9a22', '#9cc440', '#d8f08c'), '#0e1804', 0.95),
    'blood': (ramp('#3a0408', '#68091a', '#921626', '#bc2c3c', '#ee6878'), '#140204', 1.0),
    'clear': (ramp('#2a6688', '#4894bc', '#7ec4e4', '#bce8fc', '#f4fcff'), '#0a2232', 0.86),
}
SPIKE = {
    'flesh': (ramp('#560c1e', '#861c32', '#b4364c', '#dc6476', '#ffaab4'), '#16020a'),
    'plaque': (ramp('#6a4a2a', '#a88a66', '#d4bea2', '#efe4d0', '#ffffff'), '#24160a'),
    'neuro': (ramp('#341652', '#563684', '#8462b4', '#b49ce0', '#eadcff'), '#120420'),
    'crystal': (ramp('#24506e', '#3e80a8', '#7cbcdc', '#c4ecfc', '#ffffff'), '#0a1e2c'),
}


def trim_rows(s):
    rows = np.nonzero(s[..., 3].max(axis=1) > 20)[0]
    cols = np.nonzero(s[..., 3].max(axis=0) > 20)[0]
    return s[:rows.max() + 1, :cols.max() + 1]


def glossy(m, rmp, out, soft=1.3, ambient=0.24, hl_t=0.972, alpha=1.0):
    spr, _ = S.blob(m, rmp, out, hl='#ffffff', hl_t=hl_t, soft=soft, ambient=ambient)
    if alpha < 1:
        I = inner(spr)
        I[..., 3] *= alpha
    return spr


# ------------------------------------------------------------------ drops and puddles
def fibrin(I, m, seed, n):
    """a few fine pale wavy threads, only where the mask is"""
    R = np.random.RandomState(seed)
    h, w = m.shape[0] / SC, m.shape[1] / SC
    for k in range(n):
        x0, y0 = R.uniform(1, w - 1), R.uniform(1, h - 1)
        a = R.uniform(0, np.pi); L = R.uniform(2.0, 4.0)
        pts = [(x0 + np.cos(a) * t, y0 + np.sin(a) * t + 0.3 * np.sin(t * 2.0)) for t in np.linspace(-L, L, 16)]
        pts = [(p, q) for p, q in pts if 0 <= px(q) < m.shape[0] and 0 <= px(p) < m.shape[1] and m[px(q), px(p)]]
        if len(pts) > 2:
            A.stroke(I, pts, 0.35, '#e8b8b0', 85, scale=1.0)


def drop(fam, w=11, h=15):
    """a fat drop, round at the bottom and drawn to a point at the top (as it lets go of the ceiling)"""
    rmp, out, a = DROP[fam]
    y, x = grid(h, w)
    cx, r = w / 2 - 0.5, w / 2
    cy = h - r
    round_part = ((x - cx) / r) ** 2 + ((y - cy) / r) ** 2 <= 1
    t = np.clip((cy - y) / max(cy, 1e-3), 0, 1)                        # 0 at the middle of the round part .. 1 at the tip
    cone = (y <= cy) & (np.abs(x - cx) <= r * (1 - t) ** 1.25)
    m = round_part | cone
    spr = glossy(m, rmp, out, soft=1.1, alpha=a)
    I = inner(spr)
    if fam == 'blood':                                                   # a clot: mottled, pale fibrin threads in it
        A.grain(spr, 3, 0.14, 0.45)
        fibrin(I, m, 5, 4)
    else:                                                                # see-through: a light inside, a bright rim below
        ellipse_soft(I, cx + 1.2, cy + 1.8, r * 0.45, r * 0.32, '#ffffff', 70)
        ellipse_soft(I, cx - 1.6, cy - 1.0, 1.1, 1.6, '#ffffff', 230)
    return trim_rows(spr)


def puddle(fam, w=24, h=9, seed=1):
    """the drop after it hits the floor: a low wobbly mound with a few splashed beads beside it"""
    rmp, out, a = DROP[fam]
    R = np.random.RandomState(seed)
    y, x = grid(h, w)
    u = (x - w / 2 + 0.5) / (w / 2)
    top = h * (1 - np.abs(u) ** 2.2) * (0.86 + 0.14 * np.cos(u * 7 + 1.0))  # lumpy dome
    m = (y >= h - top) & (np.abs(u) <= 1)
    spr = glossy(m, rmp, out, soft=1.3, alpha=a, hl_t=0.965)
    I = inner(spr)
    if fam == 'blood':
        A.grain(spr, 7, 0.14, 0.45)
        fibrin(I, m, 7, 6)
    else:
        ellipse_soft(I, w * 0.33, h * 0.42, 2.2, 1.0, '#ffffff', 220)
        ellipse_soft(I, w * 0.6, h * 0.62, 4.0, 1.4, '#ffffff', 60)
    return trim_rows(spr)


# ------------------------------------------------------------------ spikes from the floor
def spike(fam, size='s', seed=1):
    """small (about 13 x 20) or tall (about 15 x 32): grows up out of the floor"""
    rmp, out = SPIKE[fam]
    R = np.random.RandomState(seed + (7 if size == 't' else 0))
    w, h = (13, 20) if size == 's' else (15, 32)
    y, x = grid(h, w)
    t = np.clip(y / h, 0, 1)                                            # 0 at the tip .. 1 at the floor
    cx = w / 2 - 0.5
    if fam == 'flesh':          # a polyp: soft, rounded tip, wider foot, a slight lean
        lean = 1.2 * (1 - t) ** 2
        half = 1.6 + (w / 2 - 1.6) * t ** 0.75
        m = np.abs(x - cx - lean) <= half
        m &= ~((y < 2.2) & (((x - cx - lean) / 1.8) ** 2 + ((y - 2.2) / 2.2) ** 2 > 1))
        spr = glossy(m, rmp, out, soft=1.3)
        I = inner(spr)
        ring = np.clip(1 - np.abs(np.mod(y + 0.6 * np.sin(x * 0.9), 3.4) - 1.7) / 0.32, 0, 1) * m * (y > 4)
        I[..., :3] *= (1 - 0.13 * ring[..., None])
        for k in range(4):                                                 # mucus beads
            yy = R.uniform(h * 0.25, h * 0.8); xx = cx + 1.2 * (1 - yy / h) ** 2 - (1.6 + (w / 2 - 1.6) * (yy / h) ** 0.75) * 0.55
            ellipse_soft(I, xx, yy, 0.7, 0.9, '#ffffff', 170)
    elif fam == 'plaque':       # a calcified spike: a hard, rough, cream thorn with yellow fatty specks
        jag = 0.5 * np.sin(y * 2.3 + 1.0) + 0.35 * np.sin(y * 5.1)
        half = 0.5 + (w / 2 - 0.5) * t ** 1.05 + jag * t
        m = np.abs(x - cx) <= half
        spr = glossy(m, rmp, out, soft=0.9, hl_t=0.985)
        A.grain(spr, seed, 0.09, 0.4)
        I = inner(spr)
        for k in range(10):
            yy = R.uniform(h * 0.3, h - 1.5); hw = 0.5 + (w / 2 - 0.5) * (yy / h) ** 1.05
            ellipse_soft(I, cx + R.uniform(-0.7, 0.7) * hw, yy, R.uniform(0.5, 1.0), R.uniform(0.4, 0.8), '#e8b830', 200)
    elif fam == 'neuro':        # a thorn of a nerve cell's branch, a little curved, with short side spines
        bend = 2.0 * (1 - t) ** 1.6
        half = 0.7 + (w / 2 - 2.5) * t ** 1.1
        m = np.abs(x - cx - bend) <= half
        for k, yy in enumerate((h * 0.42, h * 0.63) if size == 't' else (h * 0.5,)):
            sgn = 1 if k % 2 == 0 else -1
            hw = 0.7 + (w / 2 - 2.5) * (yy / h) ** 1.1
            x0 = cx + 2.0 * (1 - yy / h) ** 1.6 + sgn * hw
            L = 3.4
            tt = np.clip((x - x0) * sgn / L, 0, 1)
            m |= ((x - x0) * sgn >= -0.5) & ((x - x0) * sgn <= L) & (np.abs(y - (yy - tt * 2.2)) <= 0.9 * (1 - tt) + 0.35)
        spr = glossy(m, rmp, out, soft=1.0)
        I = inner(spr)
        lam = np.clip(1 - np.abs(np.mod(y * 0.9 + x * 0.3, 2.6) - 1.3) / 0.25, 0, 1) * m * (y > 3)
        I[..., :3] *= (1 - 0.10 * lam[..., None])
    else:                       # crystal: a cluster of sharp faceted shards
        m = np.zeros(y.shape, bool); face = np.zeros(y.shape, np.float32)
        shards = [(cx, h, w * 0.32, 0.0), (cx - w * 0.26, h, w * 0.2, -0.32), (cx + w * 0.27, h, w * 0.2, 0.30)]
        for k, (bx, by, hw, ang) in enumerate(shards):
            L = h * (1.0 if k == 0 else 0.62)
            # rotate into the shard's frame: along (up the shard) and across
            along = (by - y) * np.cos(ang) + (x - bx) * np.sin(ang)
            across = (x - bx) * np.cos(ang) - (by - y) * np.sin(ang)
            tip = L * 0.78
            wid = np.where(along < tip, hw, hw * np.clip((L - along) / (L - tip), 0, 1))
            sm = (along >= 0) & (along <= L) & (np.abs(across) <= wid)
            m |= sm
            face = np.where(sm, np.where(across < 0, 0.85, 0.45) + 0.1 * (along / L), face)
        spr = paint(smooth_mask(m), rmp, np.clip(face, 0, 1))
        spr = outline(spr, out)
        I = inner(spr)
        for k, (bx, by, hw, ang) in enumerate(shards):        # a bright edge down each shard's middle
            L = h * (1.0 if k == 0 else 0.62)
            pts = [(bx + 0.5 + np.sin(ang) * s, by - np.cos(ang) * s) for s in np.linspace(1.0, L * 0.85, 12)]
            A.stroke(I, pts, 0.5, '#ffffff', 200, scale=1.0)
    return trim_rows(spr)


# ------------------------------------------------------------------ the leaflets of a gate
GATE_T = 131          # the hanging lip: from behind the ceiling band (y 3.5) down to the slide line (y 134.5)
GATE_B = 34           # the standing lip: 26 above the floor, the rest behind the floor band


def leaflet(fam, part):
    """part 't' hangs from the ceiling (a long bulge, its free end round and a little fat, like a lip);
    part 'b' stands on the floor (a mound). valve: thin, pale, fibrous, a little see-through, a scalloped edge with
    the small nodules a valve cusp has; sph(incter): thick red muscle, rings of fibres across it, wet"""
    valve = fam == 'valve'
    if part == 't':
        w, L = (28, GATE_T) if valve else (34, GATE_T)
        y, x = grid(L, w + 4)
        t = np.clip(y / L, 0, 1)
        sway = 1.4 * np.sin(t * np.pi * 1.1)                       # hangs with a slight S, not a ruler-straight bar
        cx = (w + 4) / 2 - 0.5 + sway
        neck = (w / 2) * ((1.0 - 0.52 * t ** 1.15) if valve else (1.0 - 0.40 * t ** 1.1))   # wide where it grows, tapering
        endr = (w / 2) * (0.56 if valve else 0.68)                  # the free end: round, a little fatter than the neck
        ey = L - endr
        m = (np.abs(x - cx) <= neck) & (y <= ey)
        m |= ((x - cx) / endr) ** 2 + ((y - ey) / endr) ** 2 <= 1
        if valve:                                                  # scallops: two shallow notches in the free edge
            for sx in (-0.5, 0.5):
                m &= ~(((x - cx - sx * endr * 1.3) / (endr * 0.36)) ** 2 + ((y - L - 0.4) / 1.8) ** 2 <= 1)
        cx = (w + 4) / 2 - 0.5
    else:
        w, L = (24, GATE_B) if valve else (28, GATE_B)
        y, x = grid(L, w)
        cx = w / 2 - 0.5
        u = np.abs(x - cx) / (w / 2)
        top = L * np.clip(1 - u ** (1.6 if valve else 2.4), 0, 1) ** (0.75 if valve else 0.5)   # a mound
        m = (L - y) <= top
        if valve:                                                  # the cusp's edge: two shallow scallops on top
            for sx in (-0.3, 0.3):
                m &= ~(((x - cx - sx * w) / (w * 0.12)) ** 2 + ((y - (L - top.max()) + 0.5) / 1.6) ** 2 <= 1)
    if valve:
        rmp, out = ramp('#8a6068', '#b88c92', '#dcb6b6', '#f2d6d0', '#fff2ee'), '#3a1a1e'
        spr = glossy(m, rmp, out, soft=2.4, hl_t=0.985, alpha=0.95)
        I = inner(spr)
        # collagen fibres fanning out along the cusp, then the thickened free edge (a darker rim) and its nodules
        along = y if part == 't' else (L - y)
        fan = (x - (cx if part == 'b' else (w + 4) / 2)) / (1.0 + 0.012 * along)
        fib = np.clip(1 - np.abs(np.mod(fan * 1.2, 3.0) - 1.5) / 0.28, 0, 1) * m * (along > 3)
        I[..., :3] *= (1 - 0.11 * fib[..., None])
        d = ndimage.distance_transform_edt(m) / SC
        free = (y > L * 0.8) if part == 't' else (y < L * 0.35)
        rim = m & free & (d < 1.6)
        I[..., :3] = np.where(rim[..., None], I[..., :3] * 0.86, I[..., :3])
        ny = L - 3.0 if part == 't' else L - top.max() + 3.2
        nx = ((w + 4) / 2 - 0.5 + 1.4 * np.sin(np.pi * 1.1)) if part == 't' else cx
        ellipse_soft(I, nx + 0.5, ny, 1.6, 1.3, '#f6dcd6', 255)
        ellipse_soft(I, nx + 0.1, ny - 0.4, 0.7, 0.5, '#ffffff', 200)
    else:
        rmp, out = ramp('#5a0c1c', '#8c1c30', '#bc3448', '#e2606e', '#ffa4ac'), '#18020a'
        spr = glossy(m, rmp, out, soft=2.2, hl_t=0.97)
        I = inner(spr)
        # rings of muscle running round the lumen: in side view gently bowed bands across the lip
        bow = 1.6 * ((x - (cx if part == 'b' else (w + 4) / 2)) / (w / 2)) ** 2
        rings = np.clip(1 - np.abs(np.mod(y + bow, 3.2) - 1.6) / 0.42, 0, 1) * m
        I[..., :3] *= (1 - 0.15 * rings[..., None])
        A.grain(spr, 21 if part == 't' else 22, 0.05)
        R = np.random.RandomState(11 if part == 't' else 12)
        for k in range(9 if part == 't' else 3):                       # wet glints down its lit side
            yy = R.uniform(4, L - 6) if part == 't' else R.uniform(L * 0.3, L * 0.7)
            hw = (w / 2) * 0.62
            c0 = cx if part == 'b' else (w + 4) / 2 - 0.5 + 1.4 * np.sin(yy / L * np.pi * 1.1)
            ellipse_soft(I, c0 - hw * R.uniform(0.35, 0.6), yy, 0.55, 1.1, '#ffffff', 150)
    return trim_rows(spr)


# ------------------------------------------------------------------ an antibody flying at you
def antibody(size=17):
    """the Y of an antibody: two arms (the binding ends tipped red) on a stem; pale gold, outlined"""
    w = h = size
    y, x = grid(h, w)
    c = (w / 2 - 0.5, h * 0.56)

    def seg(p, q, r):
        px_, py_ = x - p[0], y - p[1]
        dx, dy = q[0] - p[0], q[1] - p[1]
        tt = np.clip((px_ * dx + py_ * dy) / (dx * dx + dy * dy), 0, 1)
        return (px_ - tt * dx) ** 2 + (py_ - tt * dy) ** 2 <= r * r
    arms = [(c[0] - w * 0.36, h * 0.12), (c[0] + w * 0.36, h * 0.12)]
    stem = (c[0], h * 0.94)
    m = seg(c, stem, 1.9) | seg(c, arms[0], 1.9) | seg(c, arms[1], 1.9)
    spr = glossy(m, ramp('#6a4c10', '#a8801c', '#d8b23a', '#f4dc7c', '#fff8d8'), '#241604', soft=0.8)
    I = inner(spr)
    for ax, ay in arms:                         # the red tips (where it grabs a germ)
        tip = ((x - ax) ** 2 + (y - ay) ** 2 <= 2.3 ** 2) & m
        I[..., :3] = np.where(tip[..., None], I[..., :3] * np.array([1.0, 0.42, 0.42]), I[..., :3])
    # the hinge: a small light band where the arms meet
    ellipse_soft(I, c[0], c[1], 1.4, 1.0, '#fff4c8', 180)
    return trim_rows(spr)


def all_sprites():
    out = {}
    for f in DROP:
        out[f'hz_drop_{f}'] = drop(f)
        out[f'hz_puddle_{f}'] = puddle(f, seed=3 + len(f))
    for f in SPIKE:
        for s in ('s', 't'):
            out[f'hz_spike_{f}_{s}'] = spike(f, s, seed=4)
    for f in ('valve', 'sph'):
        for p in ('b', 't'):
            out[f'hz_gate_{f}_{p}'] = leaflet(f, p)
    out['hz_shot'] = antibody()
    return out
