# Make the user's rainbow fire frames (out/fire_rb*.png, cut from their sheet) high resolution and clean, so they
# match the smooth art of the rest of the game: 4x up (premultiplied), the blocky noise flattened into smooth bands
# (mean shift + edge-preserving smoothing), the edge smoothed and anti-aliased, the sparkles redrawn crisp.
# -> out/fire_hd{0..7}.png
import sys
import numpy as np
import cv2
from PIL import Image
from scipy import ndimage

UP = 4
BLUR = float(__import__('os').environ.get('BLUR', '0.9'))
OUT = '/home/claude/hdart/out'


def star(img, cx, cy, r, alpha=1.0):
    """a crisp four-point sparkle with a soft glow, straight into an RGBA float image (premultiplied-free)"""
    h, w = img.shape[:2]
    R = int(r * 2.6) + 2
    x0, x1, y0, y1 = max(0, int(cx) - R), min(w, int(cx) + R + 1), max(0, int(cy) - R), min(h, int(cy) + R + 1)
    if x0 >= x1 or y0 >= y1:
        return
    yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    dx, dy = np.abs(xx - cx), np.abs(yy - cy)
    # the star: |dx|^0.5 + |dy|^0.5 <= r^0.5 (concave diamond), anti-aliased
    f = np.sqrt(dx / r) + np.sqrt(dy / r)
    core = np.clip((1.0 - f) * r * 0.9 + 0.5, 0, 1)
    glow = np.exp(-(dx * dx + dy * dy) / (2 * (r * 0.9) ** 2)) * 0.55
    a = np.clip(np.maximum(core, glow) * alpha, 0, 1)
    sub = img[y0:y1, x0:x1]
    sa = sub[..., 3:4] / 255.0
    na = a[..., None] + sa * (1 - a[..., None])
    sub[..., :3] = np.where(na > 0, (255 * a[..., None] + sub[..., :3] * sa * (1 - a[..., None])) / np.maximum(na, 1e-6), sub[..., :3])
    sub[..., 3:4] = na * 255


def make(i, debug=False):
    src = np.array(Image.open(f'{OUT}/fire_rb{i}.png').convert('RGBA')).astype(np.float32)
    a = src[..., 3] / 255.0
    h, w = a.shape
    # sparkles in the source: small very bright, near-white spots
    rgb = src[..., :3]
    bright = (rgb.min(axis=2) > 225) & (a > 0.6)
    lab, n = ndimage.label(bright)
    spots = []
    for k, sl in enumerate(ndimage.find_objects(lab)):
        if sl is None:
            continue
        hh, ww = sl[0].stop - sl[0].start, sl[1].stop - sl[1].start
        size = (lab[sl] == k + 1).sum()
        if 3 <= size <= 90 and max(hh, ww) <= 14:
            cy, cx = ndimage.center_of_mass(lab == k + 1)
            spots.append((cx, cy, max(hh, ww)))
    # premultiplied 4x upscale
    pm = np.dstack([rgb * a[..., None], a * 255]).astype(np.float32)
    big = cv2.resize(pm, (w * UP, h * UP), interpolation=cv2.INTER_CUBIC)
    big = np.clip(big, 0, None)
    A = np.clip(big[..., 3] / 255.0, 0, 1)
    C = np.where(A[..., None] > 0.01, big[..., :3] / np.maximum(A[..., None], 0.01), 0)
    C = np.clip(C, 0, 255).astype(np.uint8)
    # flatten the blocky noise into smooth colour regions, then smooth again keeping edges
    # the source's square pixels leave stair steps: blur them away first, then let mean shift pull the colours back
    # into flat bands whose borders now follow smooth curves; a last gentle smoothing keeps those borders soft
    Cb = cv2.GaussianBlur(C, (0, 0), UP * BLUR)
    C = cv2.pyrMeanShiftFiltering(np.ascontiguousarray(Cb), 12, 30)
    C = cv2.GaussianBlur(C, (0, 0), UP * 0.22)
    # the edge: blurred and pulled into a clean anti-aliased line; faint wisps stay soft
    As = cv2.GaussianBlur(A, (0, 0), UP * 0.75)
    hard = np.clip((As - 0.38) / 0.24, 0, 1)
    hard = hard * hard * (3 - 2 * hard)
    A2 = np.maximum(hard, np.clip(As * 0.85, 0, 1) * (As < 0.5))
    out = np.zeros((h * UP, w * UP, 4), np.float32)
    out[..., :3] = C
    out[..., 3] = np.clip(A2, 0, 1) * 255
    # the sparkles, crisp again
    for cx, cy, sz in spots:
        star(out, (cx + 0.5) * UP - 0.5, (cy + 0.5) * UP - 0.5, max(4.0, sz * UP * 0.55))
    Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).save(f'{OUT}/fire_hd{i}.png')
    return len(spots)


if __name__ == '__main__':
    for i in (range(8) if len(sys.argv) < 2 else [int(v) for v in sys.argv[1:]]):
        print(i, 'sparkles', make(i), flush=True)
