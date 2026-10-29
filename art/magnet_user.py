# (v61) the magnet's swirl: the user's picture (src/magnet_swirl.png, a golden whirl of light and little gold bars on a
# grey checkerboard painted in, not real transparency) -> assets/fx_mag.webp, a square picture with real transparency,
# made round (the picture is 1.2 times wider than tall; the game turns it, so it is squeezed to a circle).
#
# Taking the checkerboard out: the board is wobbly (squares 9 to 11 px, the lines drift), so it cannot be drawn again
# from a formula. Each pixel's square (light or dark) is read off the picture itself: a pixel is compared with the four
# 10 px away across (the other colour) and the four 10 px away on the slant (its own colour), which a smooth glow over
# it does not upset. Then 'colour to alpha' against that grey: the least cover that explains the pixel. Where what is
# left is faint (the thin haze), it is smoothed over a square or so, so no checkerboard shows through.
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

SRC = '/home/claude/hdart/src/magnet_swirl.png'
OUT = '/home/claude/runner_hd/assets/fx_mag.webp'
SIZE = 768

a = np.asarray(Image.open(SRC).convert('RGB')).astype(np.float64)
H, W, _ = a.shape
Y = a.mean(2)

def sh(img, dy, dx):
    p = np.pad(img, ((10, 10), (10, 10)), mode='edge')
    return p[10 + dy:10 + dy + H, 10 + dx:10 + dx + W]

# the two greys of the board, from its empty top rows
top = a[:40].reshape(-1, 3); lum = top.mean(1)
LIGHT = np.median(top[lum > 165], 0); DARK = np.median(top[lum < 165], 0)

D = 10
across = (sh(Y, 0, D) + sh(Y, 0, -D) + sh(Y, D, 0) + sh(Y, -D, 0)) / 4
score = Y - across
slant = (score + sh(score, D, D) + sh(score, D, -D) + sh(score, -D, D) + sh(score, -D, -D)) / 5
light = (slant > 0)[..., None]
B = np.where(light, LIGHT, DARK)

# colour to alpha against B
up = np.where(a > B, (a - B) / np.maximum(1e-6, 255 - B), (B - a) / np.maximum(1e-6, B))
al = up.max(2)
al = np.clip((al - 0.06) / 0.94, 0, 1)                      # the board's own grain (about 4 levels) is not glow
F = np.clip(B + (a - B) / np.maximum(al, 1e-3)[..., None], 0, 255)

# faint parts smoothed (premultiplied), strong parts kept sharp
S = 6.0
As = ndi.gaussian_filter(al, S)
Ps = np.stack([ndi.gaussian_filter(F[..., c] * al, S) for c in range(3)], 2)
m = ndi.gaussian_filter(al, 2.0)
m = np.clip((m - 0.4) / (0.78 - 0.4), 0, 1); m = m * m * (3 - 2 * m)
A2 = m * al + (1 - m) * As
P2 = m[..., None] * F * al[..., None] + (1 - m[..., None]) * Ps
F2 = np.clip(P2 / np.maximum(A2, 1e-4)[..., None], 0, 255)
# faint grey smudges (the board's dirt, not the whirl's light): a faint pixel with no warmth in it is let go
satF = (F2.max(2) - F2.min(2)) / np.maximum(F2.max(2), 1)
low = np.clip((0.3 - A2) / 0.2, 0, 1)
A2 = A2 * (1 - low * (1 - np.clip((satF - 0.05) / 0.15, 0, 1)))
# nothing beyond the whirl: the strong part's ellipse, and a soft edge a little outside it
ys, xs = np.nonzero(A2 > 0.5)
ecx, ecy = (xs.min() + xs.max()) / 2, (ys.min() + ys.max()) / 2
erx, ery = (xs.max() - xs.min()) / 2, (ys.max() - ys.min()) / 2
yy, xx = np.mgrid[0:H, 0:W]
rr = np.hypot((xx - ecx) / erx, (yy - ecy) / ery)
A2 = A2 * np.clip((1.1 - rr) / 0.08, 0, 1)
A2 = np.where(A2 < 0.025, 0, A2)

# its extent (what is clearly there), centred and squeezed round into a square
ys, xs = np.nonzero(A2 > 0.12)
x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
rx, ry = (x1 - x0) / 2, (y1 - y0) / 2
print('extent', x0, x1, y0, y1, 'radii', rx, ry)
rgba = np.dstack([F2, A2 * 255]).astype(np.float64)
# premultiply for the resampling, so dark edges do not creep in
pm = rgba.copy(); pm[..., :3] *= A2[..., None]
img = Image.fromarray(np.clip(pm, 0, 255).astype(np.uint8), 'RGBA')
R = max(rx, ry) * 1.04                                       # a little room round the glow
box = (cx - rx * 1.04, cy - ry * 1.04, cx + rx * 1.04, cy + ry * 1.04)
sq = img.transform((SIZE, SIZE), Image.EXTENT, box, resample=Image.BICUBIC)
s = np.asarray(sq).astype(np.float64)
al2 = s[..., 3] / 255
s[..., :3] = np.clip(s[..., :3] / np.maximum(al2, 1e-4)[..., None], 0, 255)
out = Image.fromarray(np.clip(s, 0, 255).astype(np.uint8), 'RGBA')
out.save(OUT, 'WEBP', quality=92, method=6, exact=True)
out.save('/home/claude/hdart/out/mag/fx_mag.png')
print('saved', OUT, out.size)

# the manifest: one picture, its own file (drawn at the size the game asks)
import json
MF = '/home/claude/runner_hd/assets/manifest.json'
mf = json.load(open(MF))
mf['sprites']['fx_mag'] = {'f': 'fx_mag.webp', 'r': [0, 0, SIZE, SIZE], 'w': SIZE, 'h': SIZE}
json.dump(mf, open(MF, 'w'), separators=(',', ':'))
import os; print('fx_mag.webp bytes', os.path.getsize(OUT))
