# Cut the 8 frames of the rainbow fire out of the user's magenta sheet (src/rainbow_fire_sheet.png): soft key with the
# glow unmixed from the magenta, each frame cropped to a shared box aligned on its right end (the head, which sits at
# the runner's back). -> out/fire_rb{0..7}.png
import numpy as np
from PIL import Image
from scipy import ndimage

SRC = '/home/claude/hdart/src/rainbow_fire_sheet.png'
OUT = '/home/claude/hdart/out'
a = np.array(Image.open(SRC).convert('RGB')).astype(np.float32)
H, W = a.shape[:2]
key = np.array([252, 21, 251], np.float32)
d = np.sqrt(((a - key) ** 2).sum(2))
D0, D1 = 62, 150
alpha = np.clip((d - D0) / (D1 - D0), 0, 1)
# unmix: c = alpha * F + (1 - alpha) * key  ->  F = key + (c - key) / alpha
F = np.where(alpha[..., None] > 0.02, key + (a - key) / np.maximum(alpha[..., None], 0.02), 0)
F = np.clip(F, 0, 255)
frames = []
for i in range(8):
    x0, x1 = int(round(i * W / 8)), int(round((i + 1) * W / 8))
    al = alpha[:, x0:x1].copy()
    lab, n = ndimage.label(al > 0.05)
    if n > 1:                                               # drop lone specks of noise (keep real sparkles: > 12 px)
        sz = ndimage.sum(al > 0.05, lab, range(1, n + 1))
        al *= np.isin(lab, [k + 1 for k in range(n) if sz[k] > 12])
    frames.append((x0, al, F[:, x0:x1]))
# a shared box: rows over all frames; right ends aligned
rows = np.nonzero(np.any([f[1].max(1) > 0.05 for f in frames], axis=0))[0]
y0, y1 = rows.min() - 3, rows.max() + 4
rights, lefts = [], []
for x0, al, _ in frames:
    cols = np.nonzero(al[y0:y1].max(0) > 0.05)[0]; lefts.append(cols.min()); rights.append(cols.max())
width = max(r - l for l, r in zip(lefts, rights)) + 8
print('box h', y1 - y0, 'w', width)
for i, (x0, al, Fi) in enumerate(frames):
    r = min(rights[i] + 4, al.shape[1])
    out = np.zeros((y1 - y0, width, 4), np.uint8)
    l = r - width
    src_l = max(l, 0)
    sl = slice(src_l, r)
    out[:, width - (r - src_l):, :3] = Fi[y0:y1, sl].astype(np.uint8)
    out[:, width - (r - src_l):, 3] = (al[y0:y1, sl] * 255).astype(np.uint8)
    Image.fromarray(out).save(f'{OUT}/fire_rb{i}.png')
print('ok')
