# Re-draw the user's rainbow fire frames (out/fire_rb*.png) cleanly at 4x: the source's colours are read as a smooth
# "which band" field (red .. purple) and a "how white" field, both blurred so their contour lines are smooth curves;
# the picture is then painted from those fields with crisp anti-aliased band borders (each band a little lighter at
# its top), white-hot streaks, a smooth edge and crisp sparkles. Same design, no blocky pixels.
# -> out/fire_hd{0..7}.png
import os, sys
import numpy as np
import cv2
from PIL import Image
from scipy import ndimage

UP = 4
OUT = '/home/claude/hdart/out'
SIG = float(os.environ.get('SIG', '1.8'))          # field smoothing, in source pixels
# hue (degrees) -> band: red 0, orange 1, yellow 2, green 3, blue 4, purple 5
HUE_PTS = [(0, 0.0), (22, 0.6), (35, 1.0), (52, 2.0), (70, 2.4), (110, 3.0), (165, 3.5), (205, 4.0), (240, 4.5), (268, 5.0), (300, 5.3), (330, 0.0), (360, 0.0)]
PAL = np.array([[236, 34, 40], [255, 128, 26], [255, 222, 52], [64, 206, 82], [52, 146, 255], [128, 84, 236]], np.float32)


def hue_to_band(h):
    xs, ys = zip(*HUE_PTS)
    return np.interp(h, xs, ys)


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def star(img, cx, cy, r, alpha=1.0):
    h, w = img.shape[:2]
    R = int(r * 2.6) + 2
    x0, x1, y0, y1 = max(0, int(cx) - R), min(w, int(cx) + R + 1), max(0, int(cy) - R), min(h, int(cy) + R + 1)
    if x0 >= x1 or y0 >= y1:
        return
    yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    dx, dy = np.abs(xx - cx), np.abs(yy - cy)
    f = np.sqrt(dx / r) + np.sqrt(dy / r)
    core = np.clip((1.0 - f) * r * 0.9 + 0.5, 0, 1)
    glow = np.exp(-(dx * dx + dy * dy) / (2 * (r * 0.8) ** 2)) * 0.5
    a = np.clip(np.maximum(core, glow) * alpha, 0, 1)
    sub = img[y0:y1, x0:x1]
    sa = sub[..., 3:4] / 255.0
    na = a[..., None] + sa * (1 - a[..., None])
    sub[..., :3] = np.where(na > 0, (255 * a[..., None] + sub[..., :3] * sa * (1 - a[..., None])) / np.maximum(na, 1e-6), sub[..., :3])
    sub[..., 3:4] = na * 255


def make(i):
    src = np.array(Image.open(f'{OUT}/fire_rb{i}.png').convert('RGBA')).astype(np.float32)
    rgb, a = src[..., :3], src[..., 3] / 255.0
    h, w = a.shape
    hsv = cv2.cvtColor(np.clip(rgb, 0, 255).astype(np.uint8), cv2.COLOR_RGB2HSV_FULL).astype(np.float32)
    H_, S_, V_ = hsv[..., 0] * 360 / 256, hsv[..., 1] / 255, hsv[..., 2] / 255
    band = hue_to_band(H_)
    wt = (S_ ** 1.5) * a                                   # only coloured, solid pixels say which band
    white = np.clip((1 - S_) * V_ * 1.25 - 0.2, 0, 1) * a      # white-hot parts
    # sparkles: small near-white spots
    bright = (rgb.min(axis=2) > 225) & (a > 0.6)
    lab, n = ndimage.label(bright)
    spots = []
    for k, sl in enumerate(ndimage.find_objects(lab)):
        size = (lab[sl] == k + 1).sum()
        hh, ww = sl[0].stop - sl[0].start, sl[1].stop - sl[1].start
        if 3 <= size <= 90 and max(hh, ww) <= 14:
            cy, cx = ndimage.center_of_mass(lab == k + 1)
            spots.append((cx, cy, max(hh, ww)))
    # band is circular at red (0 and 5.3 -> red via 330..360): keep it linear 0..5, pinks near red go to 0
    up = lambda f: cv2.resize(f.astype(np.float32), (w * UP, h * UP), interpolation=cv2.INTER_CUBIC)
    s = SIG * UP
    B_w, W_w = up(band * wt), up(wt)
    Bs = cv2.GaussianBlur(B_w, (0, 0), s) / np.maximum(cv2.GaussianBlur(W_w, (0, 0), s), 1e-4)
    Ws = cv2.GaussianBlur(up(white), (0, 0), s * 0.55)
    Vs = cv2.GaussianBlur(up(V_ * a + (1 - a) * 0.8), (0, 0), s * 0.9)      # light and shade of the source (the flame's curls)
    As = cv2.GaussianBlur(np.clip(up(a), 0, 1), (0, 0), s * 0.95)
    # paint the bands with crisp, smooth borders; each band a little lighter toward its top
    Bc = np.clip(Bs, 0, 5)
    lo = np.floor(Bc).astype(int); fr = Bc - lo; hi = np.minimum(lo + 1, 5)
    m = smoothstep(0.44, 0.56, fr)[..., None]
    col = PAL[lo] * (1 - m) + PAL[hi] * m
    within = np.where(fr < 0.5, fr + 0.5, fr - 0.5)          # 0 at a band's top .. 1 at its bottom
    col = col + (255 - col) * (0.22 * (1 - smoothstep(0.0, 0.45, within)))[..., None]
    # the source's light and shade (the darker curls in the flame), smooth
    col = col * (0.62 + 0.38 * smoothstep(0.45, 0.95, Vs))[..., None]
    # white-hot streaks: thin and bright, a soft halo round them
    hw = smoothstep(0.5, 0.66, Ws)[..., None]
    halo = smoothstep(0.32, 0.5, Ws)[..., None] * 0.35
    col = col * (1 - halo) + 255 * halo
    col = col * (1 - hw * 0.95) + 255 * hw * 0.95
    # the edge: smooth and clean; thin wisps stay soft
    hard = smoothstep(0.36, 0.56, As)
    A2 = np.maximum(hard, np.clip(As * 0.9, 0, 1) * (As < 0.45))
    # a dark line along the bottom edge of the ribbon (the purple side), as in the sheet
    solid = hard > 0.5
    edge = solid & ~ndimage.binary_erosion(solid, iterations=int(UP * 0.9))
    bottom = edge & (Bs > 4.2) & (np.roll(hard, -int(UP * 1.5), axis=0) < 0.5)
    dl = cv2.GaussianBlur(bottom.astype(np.float32), (0, 0), 0.8)[..., None]
    col = col * (1 - dl * 0.85) + np.array([30, 12, 48], np.float32) * dl * 0.85
    out = np.zeros((h * UP, w * UP, 4), np.float32)
    out[..., :3] = np.clip(col, 0, 255)
    out[..., 3] = np.clip(A2, 0, 1) * 255
    for cx, cy, sz in spots:
        star(out, (cx + 0.5) * UP - 0.5, (cy + 0.5) * UP - 0.5, max(4.0, sz * UP * 0.6))
    Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).save(f'{OUT}/fire_hd{i}.png')
    return len(spots)


if __name__ == '__main__':
    for i in (range(8) if len(sys.argv) < 2 else [int(v) for v in sys.argv[1:]]):
        print(i, 'sparkles', make(i), flush=True)
