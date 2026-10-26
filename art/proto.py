# Prototype: build one theme in HD and composite a phone-size frame (as the engine would draw it) to judge the look.
import sys, time, io
import numpy as np
from PIL import Image
import art
from art import SC, to_image
import themes as T
import sprites as S
from tiles import WT, FY0, GY

name = sys.argv[1] if len(sys.argv) > 1 else 'stomach'
R_OUT = float(sys.argv[2]) if len(sys.argv) > 2 else 6.0      # device px per world unit
OUTD = '/tmp/claude-0/-home-claude/3a779e8a-891a-5a91-a306-4a5325e0d53e/scratchpad'
t0 = time.time()
th = getattr(T, 'T_' + name)()
print('theme built %.1fs' % (time.time() - t0), flush=True)
items = {'vitC': S.coin_c(), 'o2': S.bubble_o2(), 'iron': S.hex_fe(), 'omega': S.omega_drop(), 'fiber': S.broccoli(),
         'multi': S.multi_vit(), 'heal': S.heal_cap()}
NW, NH = 390, 180
Wd, Hd = int(NW * R_OUT), int(NH * R_OUT)
k = R_OUT / SC


def im(arr):
    return to_image(arr)


def draw(dst, arr, x, y, scale=k):
    """place an HD array (RGBA float) at world (x, y), resampled to the device scale (bilinear, like the canvas)"""
    i = im(arr)
    w, h = max(1, int(round(i.width * scale))), max(1, int(round(i.height * scale)))
    i = i.resize((w, h), Image.BILINEAR)
    dst.alpha_composite(i, (int(round(x * R_OUT)), int(round(y * R_OUT)))) if x * R_OUT > -w and y * R_OUT > -h and x >= 0 and y >= 0 else paste_any(dst, i, int(round(x * R_OUT)), int(round(y * R_OUT)))


def paste_any(dst, i, X, Y):
    c = Image.new('RGBA', dst.size, (0, 0, 0, 0)); c.paste(i, (X, Y)); dst.alpha_composite(c)


frame = Image.new('RGBA', (Wd, Hd), (0, 0, 0, 255))
cam = 200
for key, par, y in (('far', 0.35, 0), ('mid', 0.65, 0)):
    a = th.get(key)
    if a is None:
        continue
    off = (cam * par) % WT
    piece = a[:, int(off * SC):int((off + NW + 2) * SC)]
    draw(frame, piece, 0, y)
# a hanging obstacle behind the ceiling
obs = th['obs']
if obs.get('hang'):
    h = obs['hang'][0]
    draw(frame, h, 250, GY - 20 - h.shape[0] / SC)
if th.get('ceil') is not None:
    draw(frame, th['ceil'][:, int(cam * SC):int((cam + NW + 2) * SC)], 0, 0)
draw(frame, th['floor'][:, int(cam * SC):int((cam + NW + 2) * SC)], 0, FY0)
low = obs['low'][0]
draw(frame, low, 150, GY + 2 - low.shape[0] / SC)
tall = obs['tall'][0]
draw(frame, tall, 330, GY + 2 - tall.shape[0] / SC)
fl = obs['float'][0]
draw(frame, fl, 200, GY - 20 - fl.shape[0] / SC)
for i in range(6):
    it = items[th['coin']]
    draw(frame, it, 120 + i * 15 - it.shape[1] / SC / 2, GY - 12 - it.shape[0] / SC / 2)
for j, kk in enumerate(['heal', 'iron', 'omega', 'fiber', 'multi', 'o2']):
    it = items[kk]
    draw(frame, it, 40 + j * 18, 40)
ch = Image.open('/home/claude/hdart/out/charhd_tardigrade.png')
cw, chh = ch.width / 6.4, ch.height / 6.4
chs = ch.resize((int(round(cw * R_OUT)), int(round(chh * R_OUT))), Image.LANCZOS)
paste_any(frame, chs, int(round((84 - cw / 2) * R_OUT)), int(round((GY + 1 - chh) * R_OUT)))
frame.convert('RGB').save(f'{OUTD}/proto_{name}.png')
frame.convert('RGB').crop((0, 0, Wd // 2, Hd // 2)).save(f'{OUTD}/proto_{name}_tl.png')
frame.convert('RGB').crop((Wd // 4, Hd // 2, Wd * 3 // 4, Hd)).save(f'{OUTD}/proto_{name}_bot.png')
# sizes
for key in ('far', 'mid', 'floor', 'ceil'):
    a = th.get(key)
    if a is None:
        continue
    b = io.BytesIO()
    i = im(a)
    if key == 'far':
        i.convert('RGB').save(b, 'WEBP', quality=82, method=6)
    else:
        i.save(b, 'WEBP', quality=85, method=6, alpha_quality=90)
    print(key, i.size, 'webp KB', len(b.getvalue()) // 1024)
print('done %.1fs' % (time.time() - t0))
