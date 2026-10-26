# Cut the ten characters out of the magenta sheet and turn them into true low-resolution pixel sprites.
#  1. key out the magenta (and the magenta fringe), 2. find the ten blobs, 3. shrink each by the art's pixel size
#  (about 6.4 source px per art px) with an area average, 4. snap alpha, reduce to a small palette, 5. a clean
#  1-px dark outline all round.
import numpy as np
from PIL import Image
from scipy import ndimage
from sklearn.cluster import KMeans

SRC = '/home/claude/pixel/src/chars_sheet.png'
OUT = '/home/claude/pixel/out'
PX = 6.4
NAMES = ['tardigrade', 'lacto', 'paramecium', 'amoeba', 'daphnia', 'pillbug', 'ladybug', 'jelly', 'sub', 'phage']

a = np.array(Image.open(SRC).convert('RGB')).astype(np.float32)
r, g, b = a[..., 0], a[..., 1], a[..., 2]
# background: close to the key colour (purples and pinks of the characters themselves are far from it: their
# green channel is well above the key's)
key = np.array([252, 4, 251], np.float32)
dist = np.sqrt(((a - key) ** 2).sum(2))
bg = dist < 45                                  # the key is flat (252, 4, 250); the jelly's pink is only ~100 away
fg = ~bg
near_bg = ndimage.binary_dilation(bg, iterations=2)
# the fringe: the dark outline blended with the key (green stays near zero there; the characters' own pinks and
# purples have plenty of green)
fringe = near_bg & (g < 40) & (np.minimum(r, b) - g > 60)
fg = ndimage.binary_opening(fg, iterations=1)
lab, n = ndimage.label(fg)
sizes = ndimage.sum(fg, lab, range(1, n + 1))
big = [i + 1 for i in np.argsort(-sizes)[:40] if sizes[i] > 400]
boxes = []
for i in big:
    sl = ndimage.find_objects((lab == i).astype(int))[0]
    boxes.append([sl[0].start, sl[0].stop, sl[1].start, sl[1].stop])
# merge boxes that belong to the same character (the lactobacillus' little friend, the phage legs...)
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
            if changed: break
    return boxes
boxes = merge(boxes)
boxes = [bx for bx in boxes if (bx[1] - bx[0]) * (bx[3] - bx[2]) > 8000]
boxes.sort(key=lambda bx: (0 if bx[0] < 440 else 1, bx[2]))
print(len(boxes), boxes)

for name, (y0, y1, x0, x1) in zip(NAMES, boxes):
    y0 -= 4; x0 -= 4; y1 += 4; x1 += 4
    crop = a[y0:y1, x0:x1]
    m = fg[y0:y1, x0:x1].astype(np.float32)
    # magenta spill on the kept edge pixels: pull them toward the dark outline colour
    mg = fringe[y0:y1, x0:x1].astype(np.float32)[..., None]
    crop = crop * (1 - mg) + np.array([30, 18, 34], np.float32) * mg
    H, W = m.shape
    w, h = max(1, round(W / PX)), max(1, round(H / PX))
    pre = np.dstack([crop * m[..., None], m])
    small = np.array(Image.fromarray(np.clip(pre[..., :3], 0, 255).astype(np.uint8)).resize((w, h), Image.BOX)).astype(np.float32)
    al = np.array(Image.fromarray((m * 255).astype(np.uint8)).resize((w, h), Image.BOX)).astype(np.float32) / 255
    col = small / np.maximum(al[..., None], 1e-3)
    keep = al > 0.45
    # palette: k colours from the kept pixels
    px = col[keep]
    k = min(18, max(4, len(np.unique(px.astype(int), axis=0)) // 3))
    km = KMeans(n_clusters=k, n_init=4, random_state=0).fit(px)
    q = km.cluster_centers_[km.labels_]
    out = np.zeros((h, w, 4), np.uint8)
    out[keep, :3] = np.clip(q, 0, 255).astype(np.uint8)
    out[keep, 3] = 255
    # outline: every kept pixel touching the outside becomes the darkest palette colour (if it is not already dark)
    pal = km.cluster_centers_
    dark = pal[np.argmin(pal.sum(1))]
    dark = np.minimum(dark, [48, 34, 52])
    edge = keep & ~ndimage.binary_erosion(keep, structure=np.ones((3, 3)))
    lum = out[..., :3].astype(int).sum(2)
    fix = edge & (lum > 260)
    out[fix, :3] = dark.astype(np.uint8)
    Image.fromarray(out).save(f'{OUT}/char_{name}.png')
    print(name, w, h, k)
