# preview the hazard sprites on two backgrounds (a red body wall and a dark blue brain one)
import time
import numpy as np
from PIL import Image
from art import to_image
import hazards as HZ
OUTD = '/tmp/claude-0/-home-claude/3a779e8a-891a-5a91-a306-4a5325e0d53e/scratchpad'
t0 = time.time()
spr = HZ.all_sprites()
print('built %.1fs' % (time.time() - t0), {k: v.shape[:2] for k, v in spr.items()})
items = list(spr.items())
pad = 20
W = sum(v.shape[1] + pad for k, v in items if not k.startswith('hz_gate') and k != 'hz_chordae') + pad
gates = [v for k, v in items if k.startswith('hz_gate')]
rowH = max(v.shape[0] for k, v in items if not k.startswith('hz_gate')) + 2 * pad
gH = max(v.shape[0] for v in gates) + 2 * pad
for bgname, bg in (('red', (74, 16, 30)), ('blue', (20, 30, 52))):
    im = Image.new('RGBA', (max(W, 1200), rowH + gH), bg + (255,))
    x = pad
    for k, v in items:
        if k.startswith('hz_gate') or k == 'hz_chordae':
            continue
        im.alpha_composite(to_image(v), (x, rowH - pad - v.shape[0])); x += v.shape[1] + pad
    x = pad
    for v in gates:
        im.alpha_composite(to_image(v), (x, rowH + pad)); x += v.shape[1] + pad * 2
    im.convert('RGB').save(f'{OUTD}/hz_sheet_{bgname}.png')
print('ok')
