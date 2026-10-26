# HD rainbow fire, take 3: each frame of the user's sheet is upscaled with Real-ESRGAN (anime 6B weights, run in numpy
# by esrgan_np.py) - downscale 0.5 (to the art's real pixel grid), x4, x4 again, then halve: 4x the sheet in all.
# The magenta key is removed afterwards at full size, with the glow unmixed from the key colour, and each frame is cut
# to the same box as extract_fire.py (x4) so the game anchor stays put. -> out/fire_x{0..7}.png (1116x808)
import sys, os, time, numpy as np
from PIL import Image
from scipy import ndimage
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from esrgan_np import load_pth, run

SRC = '/home/claude/hdart/src/rainbow_fire_sheet.png'
OUT = '/home/claude/hdart/out'
KEY_ONLY = '--key' in sys.argv
args = [v for v in sys.argv[1:] if v != '--key']
WTS = args[0]
ONLY = [int(v) for v in args[1:]] or list(range(8))
P = load_pth(WTS)['params_ema']
K = 4
a = np.array(Image.open(SRC).convert('RGB'))
H, W = a.shape[:2]
key = np.array([252, 21, 251], np.float32)

# the same boxes as extract_fire.py (sheet coordinates)
d = np.sqrt(((a.astype(np.float32) - key) ** 2).sum(2))
alpha = np.clip((d - 62) / (150 - 62), 0, 1)
cells = []
for i in range(8):
    x0, x1 = int(round(i * W / 8)), int(round((i + 1) * W / 8))
    al = alpha[:, x0:x1].copy()
    lab, n = ndimage.label(al > 0.05)
    if n > 1:
        sz = ndimage.sum(al > 0.05, lab, range(1, n + 1))
        al *= np.isin(lab, [k + 1 for k in range(n) if sz[k] > 12])
    cells.append((x0, x1, al))
rows = np.nonzero(np.any([c[2].max(1) > 0.05 for c in cells], axis=0))[0]
y0, y1 = rows.min() - 3, rows.max() + 4
rights, lefts = [], []
for x0, x1, al in cells:
    cols = np.nonzero(al[y0:y1].max(0) > 0.05)[0]; lefts.append(cols.min()); rights.append(cols.max())
width = max(r - l for l, r in zip(lefts, rights)) + 8
BH = y1 - y0

PAD = 8
for i in ONLY:
    t = time.time()
    x0, x1, al = cells[i]
    # the cell's rows (+pad), with everything outside this frame's own specks-cleaned mask set to the key
    cw = x1 - x0
    src = a[y0:y1, x0:x1].astype(np.float32).copy()
    keep = ndimage.binary_dilation(al[y0:y1] > 0.02, iterations=2)
    src[~keep] = key
    hh, ww = BH + 2 * PAD, cw + 2 * PAD
    hh += hh % 2; ww += ww % 2
    canvas = np.empty((hh, ww, 3), np.float32); canvas[:] = key
    canvas[PAD:PAD + BH, PAD:PAD + cw] = src
    small = np.array(Image.fromarray(canvas.astype(np.uint8)).resize((ww // 2, hh // 2), Image.LANCZOS)).astype(np.float32) / 255
    raw = f'{OUT}/fire_x{i}_raw.png'
    if KEY_ONLY and os.path.exists(raw):
        big = np.array(Image.open(raw).convert('RGB')).astype(np.float32)
    else:
        up1 = run(small, P)
        up2 = run(up1, P)
        big = np.array(Image.fromarray((up2 * 255 + .5).astype(np.uint8)).resize((ww * K, hh * K), Image.LANCZOS)).astype(np.float32)
        Image.fromarray(big.astype(np.uint8)).save(raw)
    # key colour as the model left it: median of the border
    border = np.concatenate([big[:6].reshape(-1, 3), big[-6:].reshape(-1, 3), big[:, :6].reshape(-1, 3), big[:, -6:].reshape(-1, 3)])
    kc = np.median(border, 0)
    # colour-to-alpha against the key (smallest alpha that keeps the colour in range; +-TOL of the key counts as key) ...
    dv = big - kc
    TOL = 8.0
    up = np.maximum(dv - TOL, 0) / np.maximum(255 - kc - TOL, 1)
    dn = np.maximum(-dv - TOL, 0) / np.maximum(kc - TOL, 1)
    A = np.clip(np.maximum(up, dn).max(2), 0, 1)
    # ... but violet sits on the key's own line (blue as high as the key's), so on the bluish side the alpha comes from
    # how much magenta is left: min(R,B)-G of the flame's violet is ~90, the key's ~250.
    m = np.minimum(big[..., 0], big[..., 2]) - big[..., 1]
    mk = min(kc[0], kc[2]) - kc[1]
    bl = np.clip((big[..., 2] - big[..., 0] - 4) / 20, 0, 1)
    bl = bl * bl * (3 - 2 * bl)
    A = np.maximum(A, bl * np.clip((mk - m) / (mk - 95), 0, 1))
    F = np.where(A[..., None] > 0.02, kc + dv / np.maximum(A[..., None], 0.02), 0)
    F = np.clip(F, 0, 255)
    # lone specks
    lab, n = ndimage.label(A > 0.06)
    if n > 1:
        sz = ndimage.sum(A > 0.06, lab, range(1, n + 1))
        A *= np.isin(lab, [k + 1 for k in range(n) if sz[k] > 12 * K * K])
    # cut to the shared box (right ends aligned), in K x coordinates
    r = min(rights[i] + 4, cw)
    l = r - width
    out = np.zeros((BH * K, width * K, 4), np.uint8)
    src_l = max(l, 0)
    cx0, cx1 = (PAD + src_l) * K, (PAD + r) * K
    cy0 = PAD * K
    out[:, (width - (r - src_l)) * K:, :3] = F[cy0:cy0 + BH * K, cx0:cx1].astype(np.uint8)
    out[:, (width - (r - src_l)) * K:, 3] = (A[cy0:cy0 + BH * K, cx0:cx1] * 255 + .5).astype(np.uint8)
    Image.fromarray(out).save(f'{OUT}/fire_x{i}.png')
    print(i, 'key', kc.round(), 'took', round(time.time() - t, 1), flush=True)
print('ok')
