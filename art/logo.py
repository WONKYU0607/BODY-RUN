# (v47) the title's logo: '장기런' (Korean) and 'Body Run' (English), glossy candy letters to sit with the user's art:
# a warm yellow-to-orange face, lit (rounded like a pillow) with a crisp highlight band, a white border, a deep pink
# extrusion below for depth, a thick dark outline round it all, a few glints. Fonts: Black Han Sans (Korean),
# Lilita One (Latin), both SIL Open Font License, from google/fonts (fonts/).
#   -> runner_hd/assets/logo_ko.webp, logo_en.webp (+ manifest sprites logo_ko, logo_en)
import sys, os, json
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage
sys.path.insert(0, '/home/claude/hdart')
from gloss import Pic, hexc, SS, sstep, L as LIGHT, HV

OUT = '/home/claude/runner_hd/assets'
PRE = '/tmp/claude-0/-home-claude/3a779e8a-891a-5a91-a306-4a5325e0d53e/scratchpad/logo'
FONTS = {'ko': '/home/claude/hdart/fonts/BlackHanSans-Regular.ttf', 'en': '/home/claude/hdart/fonts/LilitaOne-Regular.ttf'}


def disk(r):
    r = int(round(r)); yy, xx = np.mgrid[-r:r + 1, -r:r + 1]; return xx * xx + yy * yy <= r * r


def logo(text, font, size, W, H, tracking=0.0, ext=16, wave=(), turn=()):
    p = Pic(W, H)
    im = Image.new('L', (W * SS, H * SS), 0); d = ImageDraw.Draw(im)
    f = ImageFont.truetype(font, int(size * SS))
    # the letters one by one (with tracking), the line centred, a little higher than the middle (room for the extrusion)
    widths = [d.textlength(ch, font=f) for ch in text]
    total = sum(widths) + tracking * SS * (len(text) - 1)
    x = (W * SS - total) / 2
    bb = d.textbbox((0, 0), text, font=f)
    y = (H * SS - (bb[3] - bb[1])) / 2 - bb[1] - ext * SS * 0.5
    M = np.zeros((H * SS, W * SS), bool)
    for i, (ch, w) in enumerate(zip(text, widths)):               # each letter on its own: a little up or down, a little turned
        li = Image.new('L', (W * SS, H * SS), 0)
        ImageDraw.Draw(li).text((x, y + (wave[i] if i < len(wave) else 0) * SS), ch, font=f, fill=255)
        if i < len(turn) and turn[i]:
            cxl = x + w / 2; li = li.rotate(turn[i], resample=Image.BICUBIC, center=(cxl, H * SS / 2))
        M |= np.array(li) > 127
        x += w + tracking * SS
    ys = np.where(M.any(1))[0]; top, bot = ys.min() / SS, ys.max() / SS
    # the extrusion: the face pushed down, what shows below it
    D = np.zeros_like(M)
    for k in range(1, int(ext * SS) + 1, 2): D |= np.roll(M, k, axis=0)
    D &= ~M
    # the dark outline round everything, then the extrusion, the white border, the face
    border = ndimage.binary_dilation(M, structure=disk(3.2 * SS)) & ~M
    allm = M | D | border
    out = ndimage.binary_dilation(allm, structure=disk(7 * SS))
    p.over(np.array([42, 8, 22], np.float32), ndimage.gaussian_filter(out.astype(np.float32), 0.4 * SS))
    yrel = np.clip((p.Y - top) / max(1, bot - top + ext), 0, 1)
    dcol = hexc('#d0306c')[None, None] * (1 - yrel[..., None]) + hexc('#6a0a36')[None, None] * yrel[..., None]
    p.over(dcol, D.astype(np.float32))
    p.over(hexc('#fff4fa'), border.astype(np.float32) * (1 - 0.0))
    # the face: a vertical warm gradient, lit as a rounded surface, a light rim low, a crisp highlight
    n = p.normals(M, 9.0)
    lam = (n * LIGHT).sum(-1)
    t = np.clip((p.Y - top) / max(1, bot - top), 0, 1)
    stops = [hexc('#fff29a'), hexc('#ffd630'), hexc('#ffa414'), hexc('#ff6410')]
    tt = t * (len(stops) - 1); i0 = np.clip(np.floor(tt).astype(int), 0, len(stops) - 2); fr = (tt - i0)[..., None]
    pal = np.array(stops); base = pal[i0] * (1 - fr) + pal[i0 + 1] * fr
    shade = 0.78 + 0.32 * sstep(-0.2, 1.0, lam)
    col = np.clip(base * shade[..., None], 0, 255)
    sp = np.clip((n * HV).sum(-1), 0, 1) ** 30
    col = col + sstep(0.45, 0.6, sp)[..., None] * (255 - col) * 0.9
    p.over(col, M.astype(np.float32))
    # the highlight band over the top of the letters (candy gloss), its lower edge crisp
    band = M & (p.Y < top + (bot - top) * 0.42)
    band = ndimage.binary_erosion(band, structure=disk(2.2 * SS))
    fade = np.clip(1 - (p.Y - top) / max(1, (bot - top) * 0.42), 0, 1)
    p.over(hexc('#ffffff'), ndimage.gaussian_filter(band.astype(np.float32), 0.6 * SS) * (0.25 + 0.4 * fade))
    p.parts.append(M)
    return p


def build():
    os.makedirs(PRE, exist_ok=True)
    res = {}
    ko = logo('장기런', FONTS['ko'], 230, 900, 350, tracking=10, ext=26, wave=(-8, 6, -4), turn=(5, -3, 4))
    for cx, cy, r in [(118, 70, 26), (790, 62, 20), (836, 250, 14)]: ko.sparkle(cx, cy, r)
    res['ko'] = ko.image()
    en = logo('Body Run', FONTS['en'], 200, 1120, 340, tracking=5, ext=24, wave=(-6, 2, 6, -2, 0, -6, 2, 6), turn=(4, -2, -3, 3, 0, 4, -2, -3))
    for cx, cy, r in [(96, 76, 24), (1010, 64, 20), (1050, 238, 13)]: en.sparkle(cx, cy, r)
    res['en'] = en.image()
    m = json.load(open(f'{OUT}/manifest.json'))
    for k, img in res.items():
        a = np.clip(img, 0, 255).astype(np.uint8)
        Image.fromarray(a, 'RGBA').save(f'{OUT}/logo_{k}.webp', quality=92, alpha_quality=100, method=6)
        Image.fromarray(a, 'RGBA').save(f'{PRE}/logo_{k}.png')
        h, w = a.shape[:2]
        m['sprites'][f'logo_{k}'] = {'f': f'logo_{k}.webp', 'r': [0, 0, w, h], 'w': round(w / 5, 3), 'h': round(h / 5, 3)}
        print(f'logo_{k}.webp', os.path.getsize(f'{OUT}/logo_{k}.webp'), (w, h))
    json.dump(m, open(f'{OUT}/manifest.json', 'w'), separators=(',', ':'))


if __name__ == '__main__':
    build()
