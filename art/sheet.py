# Put the preview frames of several looks on one sheet (top frame of each), 2 columns.
import sys
from PIL import Image
D = '/tmp/claude-0/-home-claude/3a779e8a-891a-5a91-a306-4a5325e0d53e/scratchpad'
names = sys.argv[2:]
ims = []
for n in names:
    im = Image.open(f'{D}/eye_{n}.png')
    ims.append(im.crop((0, 0, im.width, im.height // 2)).resize((im.width // 2, im.height // 4)))
w, h = ims[0].size
out = Image.new('RGB', (w * 2, h * ((len(ims) + 1) // 2)))
for i, im in enumerate(ims):
    out.paste(im, ((i % 2) * w, (i // 2) * h))
out.save(f'{D}/{sys.argv[1]}.png')
