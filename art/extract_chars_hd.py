# Cut the ten characters out of the magenta sheet at FULL resolution (no shrinking): key out the magenta, unmix the
# anti-aliased fringe (dark outline blended with the key) into dark pixels with partial alpha, crop each character.
# The world size stays as before: one world unit = PX source pixels.
import numpy as np
from PIL import Image
from scipy import ndimage

import sys
SRC = sys.argv[1] if len(sys.argv) > 1 else '/home/claude/hdart/src/chars_sheet_v2.png'
TAG = sys.argv[2] if len(sys.argv) > 2 else 'charv2'
OUT = '/home/claude/hdart/out'
PX = 6.4
NAMES = ['tardigrade', 'lacto', 'paramecium', 'amoeba', 'daphnia', 'pillbug', 'ladybug', 'jelly', 'sub', 'phage']

a = np.array(Image.open(SRC).convert('RGB')).astype(np.float32)
r, g, b = a[..., 0], a[..., 1], a[..., 2]
key = np.array([253, 4, 252], np.float32)
D = np.array([16, 6, 18], np.float32)                        # the sheet's outline colour
dist = np.sqrt(((a - key) ** 2).sum(2))
bg = dist < 45
near_bg = ndimage.binary_dilation(bg, iterations=3)
# fringe: dark outline blended with the key (green near zero, red ~ blue); the characters' own pinks/purples have
# plenty of green
magentaish = (g < 40) & (np.abs(r - b) < 40) & (np.minimum(r, b) - g > 18)
solid = ~bg & ~magentaish
near_solid = ndimage.binary_dilation(solid, iterations=2)
fringe = magentaish & ~bg & near_solid          # the outline blended into the key: keep, part see-through
shadow = magentaish & ~bg & ~near_solid          # the sheet's drop shadow under each character: the game draws its own
KD = key - D
t = ((a - D) * KD).sum(2) / (KD * KD).sum()                 # 0 at the outline colour .. 1 at the key
alpha = np.ones(a.shape[:2], np.float32)
alpha[bg] = 0
alpha[fringe] = np.clip(1 - t[fringe], 0, 1)
alpha[shadow] = 0
rgb = a.copy()
rgb[fringe] = D

fg = alpha > 0.5
fg = ndimage.binary_opening(fg, iterations=1)
lab, n = ndimage.label(fg)
sizes = ndimage.sum(fg, lab, range(1, n + 1))
big = [i + 1 for i in np.argsort(-sizes)[:40] if sizes[i] > 400]
boxes = []
for i in big:
    sl = ndimage.find_objects((lab == i).astype(int))[0]
    boxes.append([sl[0].start, sl[0].stop, sl[1].start, sl[1].stop])


def merge(boxes):
    changed = True
    while changed:
        changed = False
        for i in range(len(boxes)):
            for j in range(i + 1, len(boxes)):
                A, B = boxes[i], boxes[j]
                if A[0] < B[1] + 20 and B[0] < A[1] + 20 and A[2] < B[3] + 20 and B[2] < A[3] + 20:
                    boxes[i] = [min(A[0], B[0]), max(A[1], B[1]), min(A[2], B[2]), max(A[3], B[3])]
                    boxes.pop(j); changed = True; break
            if changed:
                break
    return boxes


boxes = merge(boxes)
boxes = [bx for bx in boxes if (bx[1] - bx[0]) * (bx[3] - bx[2]) > 8000]
boxes.sort(key=lambda bx: (0 if bx[0] < 440 else 1, bx[2]))
print(len(boxes), boxes)

for name, (y0, y1, x0, x1) in zip(NAMES, boxes):
    y0 -= 4; x0 -= 4; y1 += 4; x1 += 4
    al = alpha[y0:y1, x0:x1].copy()
    # drop specks not attached to the character
    lab2, n2 = ndimage.label(al > 0.02)
    if n2 > 1:
        sz = ndimage.sum(al > 0.02, lab2, range(1, n2 + 1))
        keep = np.isin(lab2, [i + 1 for i in range(n2) if sz[i] > 30])
        al *= keep
    out = np.zeros(al.shape + (4,), np.uint8)
    out[..., :3] = np.clip(rgb[y0:y1, x0:x1], 0, 255).astype(np.uint8)
    out[..., 3] = np.clip(al * 255, 0, 255).astype(np.uint8)
    out[al == 0, :3] = 0
    Image.fromarray(out).save(f'{OUT}/{TAG}_{name}.png')
    print(name, out.shape[1], out.shape[0], 'world', round(out.shape[1] / PX, 1), round(out.shape[0] / PX, 1))
