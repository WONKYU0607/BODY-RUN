# a sheet of stage 3's small things, on water, at 2x the game's size (to judge the drawing)
import numpy as np
from PIL import Image
from art import canvas, paste, SC, to_image
from tiles import GY
import s3lib as L
items = [
    ('minnow', L.fish(24, 10, 1)),
    ('catfish', L.fish(30, 11, 2, back='#2a2418', side='#5a4a32', belly='#c8b48a', kind='cat', out='#140e06', spots_col='#2a2010')),
    ('goby', L.fish(20, 9, 3, back='#4a4030', side='#8a7a5a', belly='#e0d4b4', kind='goby', spots_col='#3a2e1e')),
    ('file', L.fish(20, 13, 4, back='#5a5a3a', side='#a4a070', belly='#e4e0c0', kind='file', spots_col='#4a4a2a')),
    ('lion', L.fish(24, 12, 5, back='#7a2a14', side='#e8a07a', belly='#ffe8dc', kind='lion', bars=4, bar_col='#5a1a0a')),
    ('sardine', L.fish(18, 6, 6, back='#1a3a6a', side='#9ab8d0', belly='#f4f8fc', kind='sardine', stripes=0, spots_col='#1a2a4a')),
    ('clown', L.fish(16, 9, 7, back='#e8640a', side='#ff8a1a', belly='#ffb04a', bars=3, bar_col='#ffffff', out='#3a1400')),
    ('crab', L.crab(20, 11, 1)),
    ('clam', L.shell_sprite(12, 8, 1)),
    ('cone', L.shell_sprite(8, 12, 2, kind='cone')),
    ('star', L.starfish(16, 7, 1)),
    ('urchin', L.urchin(14, 11, 1)),
    ('anemone', L.anemone(40, 1)),
    ('jelly', L.jelly(8, 1)),
    ('kelp', L.kelp(48, 1)),
    ('coral', L.coral_branch(44, 1)),
    ('brain', L.brain_coral(24, 12, 1)),
    ('fan', L.fan(44, 1)),
    ('ribbons', L.ribbons(44, 1)),
    ('stone', L.stone(22, 11, 1)),
    ('boulder', L.boulder(26, 18, 2)),
    ('spike', L.rock_spike('t')),
    ('pearl', L.pearl_item()),
    ('fishshot', L.fish_shot()),
]
W = 520; x = 4; y = 4; rowh = 0
out = canvas(W, 400)
out[..., :3] = np.array([70, 140, 160], np.float32); out[..., 3] = 255
for name, s in items:
    w, h = s.shape[1] / SC, s.shape[0] / SC
    if x + w > W - 4:
        x = 4; y += rowh + 6; rowh = 0
    paste(out, s, x, y); x += w + 6; rowh = max(rowh, h)
img = to_image(out[:int((y + rowh + 6) * SC)])
img = img.resize((img.width // 2 * 1, img.height // 2 * 1))
img.save('/tmp/claude-0/-home-claude/3a779e8a-891a-5a91-a306-4a5325e0d53e/scratchpad/s3_sprites.png')
print('ok', img.size)
