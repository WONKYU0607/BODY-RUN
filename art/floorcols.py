# add each theme's floor colours (fc: just under the surface, fk: deep) to the manifest from the built pictures
# (the same numbers build_hd.floor_colours() gives when a theme is rebuilt)
import json
import numpy as np
from PIL import Image
from build_hd import floor_colours, G, OUT
m = json.load(open(f'{OUT}/manifest.json'))
for name, th in m['themes'].items():
    im = np.array(Image.open(f"{OUT}/{th['fx']}").convert('RGBA')).astype(np.float32)
    fl = im[G:G + th['floor']['h'], G:-G]                 # the first chunk of the floor strip
    th['fc'], th['fk'] = floor_colours(fl)
json.dump(m, open(f'{OUT}/manifest.json', 'w'), separators=(',', ':'))
print({k: (v['fc'], v['fk']) for k, v in list(m['themes'].items())[:6]})
