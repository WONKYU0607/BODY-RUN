# The batter sheets made twice as big with Real-ESRGAN (anime 6B, numpy, esrgan_np.py): each character's box (+ a
# margin) x4, then halved, set into a 2x sheet of the ground colour -> src/batter/hd/. extract_batter.py --hd cuts them.
import sys, os, json, time, numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from esrgan_np import load_pth, run
SRC = '/home/claude/hdart/src/batter'
P = load_pth(sys.argv[1]); P = P.get('params_ema', P.get('params', P))
info = json.load(open('/home/claude/hdart/out/batter/info.json'))
SHEETS = [('0', '35a40568'), ('180', '8fb8304d'), ('45', '88a1aad1'), ('90', '4e19342b'), ('135', '48ecfe0d'), ('225', '6e07a842')]
NAMES = ['tardigrade', 'lacto', 'paramecium', 'amoeba', 'daphnia', 'pillbug', 'ladybug', 'jelly', 'sub', 'phage']
os.makedirs(SRC + '/hd', exist_ok=True)
PAD = 14
for view, fn in SHEETS:
    a = np.array(Image.open(f'{SRC}/{fn}-image.png').convert('RGB'))
    H, W = a.shape[:2]
    edge = np.concatenate([a[:6].reshape(-1, 3), a[-6:].reshape(-1, 3), a[:, :6].reshape(-1, 3), a[:, -6:].reshape(-1, 3)])
    key = np.median(edge, 0).astype(np.uint8)
    big = np.empty((H * 2, W * 2, 3), np.uint8); big[:] = key
    for n in NAMES:
        t = time.time()
        y0, y1, x0, x1 = info[f'{n}_{view}']['box']
        y0, x0 = max(0, y0 - PAD), max(0, x0 - PAD); y1, x1 = min(H, y1 + PAD), min(W, x1 + PAD)
        up = run(a[y0:y1, x0:x1].astype(np.float32) / 255, P)
        up = Image.fromarray((up * 255 + .5).astype(np.uint8)).resize(((x1 - x0) * 2, (y1 - y0) * 2), Image.LANCZOS)
        big[y0 * 2:y1 * 2, x0 * 2:x1 * 2] = np.array(up)
        print(view, n, round(time.time() - t, 1), 's', flush=True)
    Image.fromarray(big).save(f'{SRC}/hd/{fn}-image.png')
print('done')
