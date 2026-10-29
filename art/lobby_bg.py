# (v59) the lobby's picture: the user's (src/lobby_bg.png, a blue tunnel into the body, a pink-edged water path down the
# middle) as it is, to assets/lobby_bg.webp (like title_bg.webp: one picture, its own file) + the manifest
import json, os
from PIL import Image

OUT = '/home/claude/runner_hd/assets'
im = Image.open('/home/claude/hdart/src/lobby_bg.png').convert('RGB')
im.save(f'{OUT}/lobby_bg.webp', quality=86, method=6)
mf = json.load(open(f'{OUT}/manifest.json'))
mf['sprites']['lobby_bg'] = {'f': 'lobby_bg.webp', 'r': [0, 0, im.width, im.height], 'w': im.width, 'h': im.height}
json.dump(mf, open(f'{OUT}/manifest.json', 'w'), separators=(',', ':'))
print('lobby_bg.webp', im.size, os.path.getsize(f'{OUT}/lobby_bg.webp'))
