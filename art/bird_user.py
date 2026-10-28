# (v55) the bird shoot's bird, from the user's sheet (src/bird_sheet.png: a round blue bird on magenta, facing left,
# two rows of six: sitting, crouched, gliding, wings up..., sitting). Keyed off the magenta like keeper_user.py (outside
# the dark outline, magenta-ish = the background, un-mixed as a grey over magenta; per frame only the bird: the biggest
# piece, the little motion streaks go). Each frame lined up by its body: the middle of the biggest round part (the
# distance transform's peak), its radius -> the manifest (c, rb). -> runner_hd/assets/ar_bird.webp + manifest
# (ar_bird0..11, the sheet's order: the top row left to right, then the bottom)
import json, sys, os
import numpy as np
from PIL import Image
from scipy import ndimage
sys.path.insert(0, '/home/claude/hdart')
import keeper_user as ku

OUT = '/home/claude/runner_hd/assets'
PRE = '/tmp/claude-0/-home-claude/3a779e8a-891a-5a91-a306-4a5325e0d53e/scratchpad/bird'
BH = 24.0                      # the sitting bird, crest to feet, in game units
PPU = 6.0


def main():
    os.makedirs(PRE, exist_ok=True)
    im = np.array(Image.open('/home/claude/hdart/src/bird_sheet.png').convert('RGB')).astype(np.float64)
    col, a = ku.key(im)
    H, W = a.shape
    lab, sizes = ku.pieces(a)
    boxes = []
    for i, sl in enumerate(ndimage.find_objects(lab)):
        if sizes[i] < 8000: continue
        boxes.append((sl[1].start, sl[0].start, sl[1].stop, sl[0].stop))
    assert len(boxes) == 12, len(boxes)
    top_row = sorted([b for b in boxes if (b[1] + b[3]) / 2 < H / 2], key=lambda b: b[0])
    bot_row = sorted([b for b in boxes if (b[1] + b[3]) / 2 >= H / 2], key=lambda b: b[0])
    frames = []
    for (x0, y0, x1, y1) in top_row + bot_row:
        pad = 30
        c_, al_ = ku.frame(col, a, (max(0, x0 - pad), max(0, y0 - pad), min(W, x1 + pad), min(H, y1 + pad)))
        solid = ndimage.binary_fill_holes(al_ > 0.5)
        d = ndimage.distance_transform_edt(solid)
        cy, cx = np.unravel_index(np.argmax(d), d.shape)
        ys = np.where(al_ > 0.5)[0]
        frames.append((c_, al_, (float(cx), float(cy)), float(d.max()), float(ys.min()), float(ys.max())))
    U = BH / (frames[0][5] - frames[0][4])                    # units a source pixel (the first frame: sitting)
    parts = []
    for k, (c_, al_, (cx, cy), rb, top, bot) in enumerate(frames):
        img = ku.shrink(c_, al_, U * PPU)
        parts.append((f'ar_bird{k}', img, (c_.shape[1] * U, c_.shape[0] * U), {'c': [round(cx * U, 3), round(cy * U, 3)], 'rb': round(rb * U, 3)}))
    x = y = rowh = 0; Wmax = 1100; pos = []; AW = 0
    for nm, img, wh, meta in parts:
        if x + img.shape[1] > Wmax: x, y, rowh = 0, y + rowh + 4, 0
        pos.append((x, y)); x += img.shape[1] + 4; rowh = max(rowh, img.shape[0]); AW = max(AW, x)
    AH = y + rowh
    A = np.zeros((AH, AW, 4), np.float32)
    mf = json.load(open(f'{OUT}/manifest.json'))
    for (nm, img, wh, meta), (px_, py_) in zip(parts, pos):
        A[py_:py_ + img.shape[0], px_:px_ + img.shape[1]] = img
        mf['sprites'][nm] = {'f': 'ar_bird.webp', 'r': [px_, py_, img.shape[1], img.shape[0]], 'w': round(wh[0], 3), 'h': round(wh[1], 3), **meta}
    out = Image.fromarray(np.clip(A, 0, 255).astype(np.uint8), 'RGBA')
    out.save(f'{OUT}/ar_bird.webp', quality=92, alpha_quality=100, method=6)
    out.save(f'{PRE}/ar_bird_atlas.png')
    json.dump(mf, open(f'{OUT}/manifest.json', 'w'), separators=(',', ':'))
    print('ar_bird.webp', os.path.getsize(f'{OUT}/ar_bird.webp'), A.shape)
    for nm, img, wh, meta in parts: print(nm, [round(v, 1) for v in wh], json.dumps(meta))
    # a check sheet: each frame on grey and on sky blue, lined up by its body (a red dot: the body's middle; a ring: rb)
    cell = 200; S = 4.0
    chk = Image.new('RGB', (cell * 6, cell * 4), (120, 120, 120))
    from PIL import ImageDraw
    dr = ImageDraw.Draw(chk)
    for k, (nm, img, wh, meta) in enumerate(parts):
        for half, bg in ((0, (120, 120, 120)), (1, (140, 200, 240))):
            ox, oy = (k % 6) * cell, (k // 6) * 2 * cell + half * cell
            dr.rectangle([ox, oy, ox + cell - 1, oy + cell - 1], fill=bg)
            sp = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), 'RGBA')
            sc = S / PPU; sp = sp.resize((max(1, int(sp.width * sc)), max(1, int(sp.height * sc))), Image.LANCZOS)
            bx, by = meta['c'][0] * S, meta['c'][1] * S
            chk.paste(sp, (int(ox + cell / 2 - bx), int(oy + cell / 2 - by)), sp)
            r = meta['rb'] * S
            dr.ellipse([ox + cell / 2 - r, oy + cell / 2 - r, ox + cell / 2 + r, oy + cell / 2 + r], outline=(255, 0, 0))
    chk.save(f'{PRE}/bird_check.png')


if __name__ == '__main__':
    main()
