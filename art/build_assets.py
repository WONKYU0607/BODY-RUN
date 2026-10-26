# Build every asset of the side-scroller: the theme layers (PNG, palette-reduced), one sprite atlas (obstacles per
# theme, items, characters, HUD bits) and a manifest. usage: python3 build_assets.py
import json, io, time
import numpy as np
from PIL import Image
from scipy import ndimage
from art import to_image, canvas, paste, fill_rect, ellipse_mask, outline, hexc, load
import sprites as S
import themes as T
from tiles import hitbox, WT, FY0, CH

OUT = '/home/claude/pixel/build'
THEMES = ['eso', 'stomach', 'gut', 'colon', 'artery', 'vein', 'atrium', 'ventricle', 'arach', 'pyramidal', 'hippo', 'purkinje', 'fibres',
          'liver', 'gallbladder', 'pancreas', 'islet', 'spleen', 'adrenal', 'kidney', 'glomerulus', 'lung', 'myocard', 'thyroid', 'villus']
CHARS = ['tardigrade', 'lacto', 'paramecium', 'amoeba', 'daphnia', 'pillbug', 'ladybug', 'jelly', 'sub', 'phage']


def png(arr, colors=None):
    im = to_image(arr)
    if colors:
        im = im.quantize(colors=colors, method=Image.Quantize.FASTOCTREE, dither=Image.Dither.NONE)
    b = io.BytesIO(); im.save(b, 'PNG', optimize=True)
    return b.getvalue()


def pack(sprites):
    items = sorted(sprites.items(), key=lambda kv: -kv[1].shape[0])
    Wd = 1024; x = y = shelf = 0; rects = {}
    for k, s in items:
        h, w = s.shape[:2]
        if x + w + 1 > Wd:
            x = 0; y += shelf + 1; shelf = 0
        rects[k] = (x, y, w, h); x += w + 1; shelf = max(shelf, h)
    atlas = canvas(Wd, y + shelf + 1)
    for k, s in sprites.items():
        x, y, w, h = rects[k]
        atlas[y:y + h, x:x + w] = s
    return atlas, rects


def hud_sprites():
    from scenes import heart_icon, F57
    out = {'hud_heart': heart_icon()}
    for kind in ('jump', 'slide'):
        m = ellipse_mask(33, 33)
        b = np.zeros((33, 33, 4), np.float32); b[m, :3] = hexc('#ffffff'); b[m, 3] = 60
        ring = m & ~ndimage.binary_erosion(m, iterations=2)
        b[ring, :3] = hexc('#ffffff'); b[ring, 3] = 210
        b = outline(b, '#1a0a14')
        ar = ['0001000', '0011100', '0111110', '1111111', '0011100', '0011100', '0011100'] if kind == 'jump' else ['0011100', '0011100', '0011100', '1111111', '0111110', '0011100', '0001000']
        am = np.array([[c == '1' for c in r] for r in ar])
        a = np.zeros((7, 7, 4), np.float32); a[am, :3] = hexc('#ffffff'); a[am, 3] = 255
        paste(b, outline(a, '#1a0a14'), 13, 8)
        out['hud_' + kind] = b
        bp = b.copy(); on = bp[..., 3] > 0
        bp[on, :3] = bp[on, :3] * 0.7 + np.array([255, 214, 110]) * 0.3; bp[on, 3] = np.maximum(bp[on, 3], 150)
        out['hud_' + kind + '_on'] = bp
    p = canvas(14, 14); fill_rect(p, 0, 0, 14, 14, '#1a0a14'); fill_rect(p, 1, 1, 13, 13, '#f4e8ee'); fill_rect(p, 4, 4, 6, 10, '#1a0a14'); fill_rect(p, 8, 4, 10, 10, '#1a0a14')
    out['hud_pause'] = p
    for ch, g in F57.items():
        lay = canvas(7, 9)
        for j, r in enumerate(g):
            for i, bb in enumerate(r):
                if bb == '1': fill_rect(lay, 1 + i, 1 + j, 2 + i, 2 + j, '#fff3c8')
        out['dig_' + {',': 'comma', '+': 'plus'}.get(ch, ch)] = outline(lay, '#1a0a14')
    return out


if __name__ == '__main__':
    t0 = time.time()
    manifest = {'themes': {}, 'sprites': {}, 'chars': CHARS, 'WT': WT, 'FY0': FY0, 'CH': CH}
    sprites, files = {}, {}
    for name in THEMES:
        th = getattr(T, 'T_' + name)()
        entry = {'coin': th['coin'], 'special': th['special'], 'obs': {}}
        for layer, colors in (('far', 160), ('mid', 96), ('floor', 96), ('ceil', 96)):
            arr = th.get(layer)
            if arr is None:
                continue
            fn = f'{name}_{layer}.png'
            files[fn] = png(arr, colors); entry[layer] = fn
        for kind, lst in th['obs'].items():
            names = []
            for i, s in enumerate(lst):
                key = f'ob_{name}_{kind}{i}'; sprites[key] = s; names.append(key)
            entry['obs'][kind] = names
        manifest['themes'][name] = entry
        print(name, 'ok', round(time.time() - t0, 1), flush=True)
    sprites.update({'it_vitC': S.coin_c(), 'it_o2': S.bubble_o2(), 'it_iron': S.hex_fe(), 'it_omega': S.omega_drop(), 'it_fiber': S.broccoli(),
                    'it_multi': S.multi_vit(), 'it_heal': S.heal_cap()})
    for c in CHARS:
        sprites['ch_' + c] = load(f'/home/claude/pixel/out/char_{c}.png')
    sprites.update(hud_sprites())
    atlas, rects = pack(sprites)
    files['atlas.png'] = png(atlas)
    for k, (x, y, w, h) in rects.items():
        hb = hitbox(sprites[k]) if k.startswith(('ob_', 'ch_')) else [0, 0, w, h]
        manifest['sprites'][k] = [x, y, w, h] + [int(v) for v in hb]
    for fn, data in files.items():
        open(f'{OUT}/{fn}', 'wb').write(data)
    json.dump(manifest, open(f'{OUT}/manifest.json', 'w'))
    print('files', len(files), 'bytes', sum(len(d) for d in files.values()), 'atlas', atlas.shape, 'in %.1fs' % (time.time() - t0))
