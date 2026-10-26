# The batter views into the game: per character one WebP strip of its six views (only the chosen character's is loaded),
# and the manifest's sprites bt_<name>_<view> (size in world units, all views of a character at one scale; foot = where
# it stands, the middle of its feet at the bottom).
import json, math, sys
from PIL import Image

OUT = '/home/claude/hdart/out/batter' + ('_hd' if '--hd' in sys.argv else '')     # --hd: the Real-ESRGAN 2x cut
AS = '/home/claude/runner_hd/assets'
NAMES = ['tardigrade', 'lacto', 'paramecium', 'amoeba', 'daphnia', 'pillbug', 'ladybug', 'jelly', 'sub', 'phage']
VIEWS = ['0', '45', '90', '135', '180', '225']
SIZE = 66                                                     # world units: the front view's sqrt(w h)
info = json.load(open(f'{OUT}/info.json'))
m = json.load(open(f'{AS}/manifest.json'))
for k in [k for k in m['sprites'] if k.startswith('bt_')]: del m['sprites'][k]
total = 0
for n in NAMES:
    ims = [Image.open(f'{OUT}/{n}_{v}.png') for v in VIEWS]
    f0 = info[f'{n}_0']; k = SIZE / math.sqrt(f0['w'] * f0['h'])
    W = sum(im.width + 4 for im in ims); H = max(im.height for im in ims)
    sheet = Image.new('RGBA', (W, H), (0, 0, 0, 0)); x = 0
    for v, im in zip(VIEWS, ims):
        sheet.paste(im, (x, 0))
        i = info[f'{n}_{v}']
        m['sprites'][f'bt_{n}_{v}'] = {'f': f'bat_{n}.webp', 'r': [x, 0, im.width, im.height], 'w': round(im.width * k, 2), 'h': round(im.height * k, 2),
                                       'foot': [round(i['foot'][0] * k, 2), round(i['foot'][1] * k, 2)]}
        x += im.width + 4
    fn = f'{AS}/bat_{n}.webp'
    sheet.save(fn, 'WEBP', quality=92, method=6)
    import os; total += os.path.getsize(fn)
    print(n, sheet.size, os.path.getsize(fn) // 1024, 'KB', 'scale', round(k, 4))
m['batViews'] = [int(v) for v in VIEWS]
json.dump(m, open(f'{AS}/manifest.json', 'w'), separators=(',', ':'))
print('total', total // 1024, 'KB')
