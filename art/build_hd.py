# Build every HD asset of the side-scroller and a manifest.
#  per theme:  th_<name>_far.webp  (opaque)   far layer, cut into 3 chunks of one screen (390 units) stacked, gutters
#              th_<name>_mid.webp  (alpha)    mid layer, same layout (if the theme has one)
#              th_<name>_fx.webp   (alpha)    floor chunks, ceiling chunks, then the theme's obstacles packed below
#  common.webp (lossless): items, the HUD heart, the ten characters (sheet resolution)
# usage: python3 build_hd.py [theme ...]
import io, json, sys, time
import numpy as np
from PIL import Image
from art import SC, px, to_image
import sprites as S
import themes as T
from tiles import hitbox, WT, FY0, CH

OUT = '/home/claude/runner_hd/assets'
THEMES = ['eso', 'stomach', 'gut', 'colon', 'artery', 'vein', 'atrium', 'ventricle', 'arach', 'pyramidal', 'hippo', 'purkinje', 'fibres',
          'liver', 'gallbladder', 'pancreas', 'islet', 'spleen', 'adrenal', 'kidney', 'glomerulus', 'lung', 'myocard', 'thyroid', 'villus',
          'retina', 'vitreous', 'lens', 'iris', 'cornea',
          'renalart', 'carotid', 'vertebral', 'sma', 'efferent', 'pulmvein', 'ivc', 'pulmart', 'latrium', 'lventricle', 'bronchiole',
          'temporal', 'parietal', 'occipital', 'medulla', 'opticnerve', 'duodenum', 'ileum', 'cecum', 'rectum', 'anus',
          'toilet',                                                   # stage 2: the toilet, then down the drains (drains.py,
          'trap', 'stack', 'drain', 'septic',                         #  sewer.py, plant.py)
          'chamber', 'sewer', 'manhole', 'trunk', 'combined', 'interceptor', 'pump',
          'screen', 'grit', 'clarifier1', 'aeration', 'clarifier2', 'uv', 'outfall',
          'river', 'riffle', 'weeds', 'weir', 'pool', 'bridge', 'reeds', 'mudflat',                 # stage 3: the river, the estuary
          'shallows', 'rocky', 'kelp', 'coral', 'jellies', 'school', 'wreck', 'dropoff', 'deep', 'vent', 'whale']   # and the sea (river.py, sea.py)
S2_MODULES = ['drains', 'sewer', 'plant', 'river', 'sea']
TALL_K = 1.10            # tall obstacles drawn this much taller than designed: the jump is 10% higher (v17)
CHARS = ['tardigrade', 'lacto', 'paramecium', 'amoeba', 'daphnia', 'pillbug', 'ladybug', 'jelly', 'sub', 'phage']
CHAR_PX = 8.0 / 0.9      # source px per unit: the sheet's characters at 0.8 of their first size, then 0.9 of that (v38)
CW = 390                 # chunk width, units
G = 4                    # gutter, pixels
GAP = 4                  # between packed sprites, pixels
BG = {'eso': '#40101c', 'stomach': '#3a0a1c', 'gut': '#3a0c1a', 'colon': '#3a1610', 'artery': '#3e0a18', 'vein': '#2a0c22',
      'atrium': '#300818', 'ventricle': '#2e0814', 'arach': '#14243a', 'pyramidal': '#140e2c', 'hippo': '#0e1630', 'purkinje': '#200c24',
      'fibres': '#161428', 'retina': '#1a0a20', 'vitreous': '#062230', 'lens': '#120e08', 'iris': '#140a05', 'cornea': '#5a90a8',
      'renalart': '#42120c', 'carotid': '#4e0e2a', 'vertebral': '#3c0a1a', 'sma': '#3e1014', 'efferent': '#52201e', 'pulmvein': '#520a0c',
      'ivc': '#1c0e2c', 'pulmart': '#2e0e2c', 'latrium': '#420816', 'lventricle': '#4c0a16', 'bronchiole': '#341824', 'temporal': '#10282a',
      'parietal': '#201c2a', 'occipital': '#24162c', 'medulla': '#1c1228', 'opticnerve': '#101628', 'duodenum': '#3a1216', 'ileum': '#3e0e20',
      'cecum': '#401a12', 'rectum': '#341010', 'anus': '#3a1618', 'toilet': '#6fa6ac',
      'trap': '#4e7e80', 'stack': '#7a9ca2', 'drain': '#6a847c', 'septic': '#3a4428', 'chamber': '#5c7064', 'sewer': '#4c5c54',
      'manhole': '#5a7672', 'trunk': '#463a30', 'combined': '#665e46', 'interceptor': '#3e4c54', 'pump': '#40565e',
      'screen': '#5a5c4a', 'grit': '#6a6650', 'clarifier1': '#56543e', 'aeration': '#66502e', 'clarifier2': '#5a8a84',
      'uv': '#3a6a96', 'outfall': '#4e8a6a',
      'river': '#5e9e84', 'riffle': '#7cc6b6', 'weeds': '#64a866', 'weir': '#62989e', 'pool': '#2a5a62', 'bridge': '#527e7c',
      'reeds': '#80866a', 'mudflat': '#8a8268', 'shallows': '#60c8d8', 'rocky': '#5498b4', 'kelp': '#4a9084', 'coral': '#42acdc',
      'jellies': '#2e78c0', 'school': '#286cac', 'wreck': '#225a76', 'dropoff': '#144074', 'deep': '#08101e', 'vent': '#0c0e14',
      'whale': '#361620'}


def chunks(arr):
    """(h, WT*SC, 4) -> three gutter-padded chunks stacked: (3 * (h + 2G), CW*SC + 2G, 4)"""
    wt = arr.shape[1]; cw = px(CW)
    out = []
    for c in range(3):
        idx = np.arange(c * cw - G, (c + 1) * cw + G) % wt
        piece = np.pad(arr[:, idx], ((G, G), (0, 0), (0, 0)), mode='edge')
        out.append(piece)
    return np.concatenate(out, axis=0)


def pack(sprites, width, y0=0):
    """shelf-pack {name: array} into a strip `width` px wide starting at row y0 -> rects {name: (x, y, w, h)}, height"""
    items = sorted(sprites.items(), key=lambda kv: -kv[1].shape[0])
    x = y = shelf = 0; rects = {}
    y = y0
    for k, s in items:
        h, w = s.shape[:2]
        assert w + 2 * GAP <= width, (k, w)
        if x + w + 2 * GAP > width:
            x = 0; y += shelf + GAP; shelf = 0
        rects[k] = (x + GAP, y + GAP, w, h); x += w + GAP; shelf = max(shelf, h + GAP)
    return rects, y + shelf + GAP


def taller(arr, k):
    """stretch a sprite upward by k (premultiplied, so the edges stay clean)"""
    import cv2
    h, w = arr.shape[:2]
    a = arr[..., 3:4] / 255.0
    pm = np.concatenate([arr[..., :3] * a, arr[..., 3:4]], axis=2).astype(np.float32)
    out = cv2.resize(pm, (w, int(round(h * k))), interpolation=cv2.INTER_CUBIC)
    out = np.clip(out, 0, None)
    al = np.clip(out[..., 3:4], 0, 255)
    rgb = np.where(al > 0.5, out[..., :3] / np.maximum(al / 255.0, 1e-4), 0)
    return np.concatenate([np.clip(rgb, 0, 255), al], axis=2).astype(np.float32)


def webp(arr, lossless=False, q=84, rgb=False):
    im = to_image(arr)
    if rgb:
        im = im.convert('RGB')
    b = io.BytesIO()
    if lossless:
        im.save(b, 'WEBP', lossless=True, quality=100, method=6)
    else:
        im.save(b, 'WEBP', quality=q, method=6, alpha_quality=95)
    return b.getvalue()


def sprite_entry(fn, rect, scale, arr, hb=True, kind=None):
    x, y, w, h = rect
    e = {'f': fn, 'r': [int(x), int(y), int(w), int(h)], 'w': round(w / scale, 3), 'h': round(h / scale, 3)}
    if hb:
        cap = dict(capx=3.0, capy=1.5) if kind in ('hang', 'float') else {}
        e['hb'] = [round(v * SC / scale, 2) for v in hitbox(arr, **cap)]
    return e


def floor_colours(floor_arr):
    """the floor's colour just under its surface and deep down (for the edges and the inside of a hole in it)"""
    from tiles import GY
    s0 = int((GY - FY0) * SC)
    def mean(a):
        al = a[..., 3] > 200
        c = a[..., :3][al].mean(axis=0) if al.any() else np.array([60, 20, 30])
        return '#%02x%02x%02x' % tuple(int(v) for v in np.clip(c, 0, 255))
    return mean(floor_arr[s0 + 2 * SC:s0 + 7 * SC]), mean(floor_arr[s0 + 16 * SC:s0 + 28 * SC])


def build_theme(name, manifest):
    t0 = time.time()
    fn = getattr(T, 'T_' + name, None)
    if fn is None:                                              # stage 2's places
        import importlib
        for mod in S2_MODULES:
            fn = getattr(importlib.import_module(mod), 'T_' + name, None)
            if fn:
                break
    th = fn()
    entry = {'coin': th['coin'], 'special': th['special'], 'obs': {}, 'bg': BG.get(name, '#2a0c14')}
    entry['fc'], entry['fk'] = floor_colours(th['floor'])
    far = chunks(th['far']); far[..., 3] = 255
    files = {f'th_{name}_far.webp': webp(far, q=82, rgb=True)}
    entry['far'] = f'th_{name}_far.webp'
    entry['farH'] = th['far'].shape[0]
    if th.get('mid') is not None:
        files[f'th_{name}_mid.webp'] = webp(chunks(th['mid']), q=86)
        entry['mid'] = f'th_{name}_mid.webp'
        entry['midH'] = th['mid'].shape[0]
    parts = [chunks(th['floor'])]
    entry['floor'] = {'y': 0, 'h': th['floor'].shape[0]}
    y = parts[0].shape[0]
    if th.get('ceil') is not None:
        c = chunks(th['ceil']); parts.append(c)
        entry['ceil'] = {'y': y, 'h': th['ceil'].shape[0]}
        y += c.shape[0]
    width = parts[0].shape[1]
    obs = {}
    for kind, lst in th['obs'].items():
        names = []
        for i, s in enumerate(lst):
            if kind in ('hang', 'float'):      # hung from / floated at a line by its bottom: no empty rows below the picture
                rows = np.nonzero(s[..., 3].max(axis=1) > 20)[0]
                s = s[:rows.max() + 1]
            if kind == 'tall':                 # 10% taller with the 10% higher jump, but none over 60 (wide ones get hard)
                top0 = s.shape[0] / SC - 2 - hitbox(s)[1]
                s = taller(s, min(TALL_K, 60.0 / top0))
            key = f'ob_{name}_{kind}{i}'; obs[key] = s; names.append(key)
        entry['obs'][kind] = names
    rects, total = pack(obs, width, y)
    fx = np.zeros((total, width, 4), np.float32)
    yy = 0
    for p in parts:
        fx[yy:yy + p.shape[0]] = p; yy += p.shape[0]
    fn = f'th_{name}_fx.webp'
    entry['fx'] = fn
    for k, s in obs.items():
        x, y_, w, h = rects[k]
        fx[y_:y_ + h, x:x + w] = s
        manifest['sprites'][k] = sprite_entry(fn, rects[k], SC, s, kind=k.split('_')[-1].rstrip('0123456789'))
        if '_huge' in k:
            e = manifest['sprites'][k]
            top = e['h'] - 2 - e['hb'][1]                     # how high its hit box reaches above the floor
            print('  ', k, 'size %.1fx%.1f' % (e['w'], e['h']), 'hit top %.1f (double jump reaches 87.5, triple 103.9)' % top,
                  'OK' if 90.5 < top < 93.5 and e['w'] <= 27 else 'CHECK')
    files[fn] = webp(fx, q=90)
    manifest['themes'][name] = entry
    print(name, 'ok %.1fs' % (time.time() - t0), {k: len(v) // 1024 for k, v in files.items()}, flush=True)
    return files


def build_common(manifest):
    spr = {'it_vitC': S.coin_c(), 'it_o2': S.bubble_o2(), 'it_iron': S.hex_fe(), 'it_omega': S.omega_drop(), 'it_fiber': S.broccoli(),
           'it_multi': S.multi_vit(), 'it_heal': S.heal_cap(), 'it_atp': S.atp(), 'hud_heart': S.heart()}
    chars = {}
    for c in CHARS:
        chars['ch_' + c] = np.array(Image.open(f'/home/claude/hdart/out/charv2_{c}.png').convert('RGBA')).astype(np.float32)
    import hazards as HZ
    hz = HZ.all_sprites()
    import toilet as TT
    hz.update(TT.stage2_sprites())                          # stage 2's coin, special and hazards (it_*, hz_*)
    import sewer as SWR, plant as PLT
    hz.update(SWR.hazards()); hz.update(PLT.hazards())      # (the sewers': sludge, rebar, a nut; the works': floc, grit, a pebble)
    import sea as SEA
    hz.update(SEA.hazards())                                # (stage 3: the pearl; a leaf, a rock, a shell, an urchin, a fish)
    allspr = dict(spr); allspr.update(chars); allspr.update(hz)
    rects, total = pack(allspr, 1600)
    atlas = np.zeros((total, 1600, 4), np.float32)
    for k, s in allspr.items():
        x, y, w, h = rects[k]
        atlas[y:y + h, x:x + w] = s
        kind = 'hang' if k.startswith('hz_gate') and k.endswith('_t') else 'float' if k.startswith('hz_shot') else None
        manifest['sprites'][k] = sprite_entry('common.webp', rects[k], CHAR_PX if k.startswith('ch_') else SC, s, hb=k.startswith('hz_'), kind=kind)
        if k.startswith('hz_gate') and k.endswith('_t'):         # the hanging lip: its box from the part a runner can meet
            low = s.copy(); low[:max(0, s.shape[0] - 70 * SC)] = 0      # (the bottom 70 units; the flare at the ceiling is out of reach)
            hb = hitbox(low, capx=3.0, capy=1.5); hb[1] = hitbox(s, capx=3.0, capy=1.5)[1]   # (but as high as it goes)
            manifest['sprites'][k]['hb'] = [round(v, 2) for v in hb]
    return {'common.webp': webp(atlas, lossless=True)}


FIRE_K = 4          # the HD fire frames are 4x the user's sheet (hd_fire3.py), the sheet itself being SC px per unit


def build_fire(manifest):
    """the booster's rainbow fire: 8 HD frames (hd_fire3.py: the user's sheet upscaled) in an atlas of their own, lossy
    (lossless would be several MB) and decoded at the start with common.webp (manifest 'extra')"""
    fr = {f'fx_rb{i}': np.array(Image.open(f'/home/claude/hdart/out/fire_x{i}.png').convert('RGBA')).astype(np.float32) for i in range(8)}
    w0 = next(iter(fr.values())).shape[1]
    width = 2 * (w0 + 2 * GAP)
    rects, total = pack(fr, width)
    atlas = np.zeros((total, width, 4), np.float32)
    for k, s in fr.items():
        x, y, w, h = rects[k]
        atlas[y:y + h, x:x + w] = s
        manifest['sprites'][k] = sprite_entry('fx_fire.webp', rects[k], SC * FIRE_K, s, hb=False)
    manifest['extra'] = sorted(set(manifest.get('extra', [])) | {'fx_fire.webp'})   # (the baseball's are in it too)
    return {'fx_fire.webp': webp(atlas, q=90)}


def build_cut(manifest):
    """the flush cut scene at the end of the body (toilet.py): the pile, the lumps, the bowl in section and its water, in
    an atlas of their own, decoded only near the end of the anus"""
    import toilet as TT
    sp = TT.cut_sprites()
    width = max(s.shape[1] for s in sp.values()) + 2 * GAP
    rects, total = pack(sp, width)
    atlas = np.zeros((total, width, 4), np.float32)
    for k, s in sp.items():
        x, y, w, h = rects[k]
        atlas[y:y + h, x:x + w] = s
        manifest['sprites'][k] = sprite_entry('cut_flush.webp', rects[k], SC, s, hb=False)
    return {'cut_flush.webp': webp(atlas, q=88)}


if __name__ == '__main__':
    import os
    os.makedirs(OUT, exist_ok=True)
    only = sys.argv[1:]
    mpath = f'{OUT}/manifest.json'
    manifest = json.load(open(mpath)) if (only and os.path.exists(mpath)) else {'themes': {}, 'sprites': {}}
    manifest.update({'chars': CHARS, 'WT': WT, 'FY0': FY0, 'CH': CH, 'SC': SC, 'CW': CW, 'G': G})
    t0 = time.time()
    files = {}
    for name in (only or THEMES):
        if name in ('common', 'fire', 'cut'):
            continue
        files.update(build_theme(name, manifest))
    if not only or 'common' in only:
        files.update(build_common(manifest))
    if not only or 'common' in only or 'fire' in only:
        files.update(build_fire(manifest))
    if not only or 'cut' in only:
        files.update(build_cut(manifest))
    import hashlib
    seen = {}
    alias = {}
    for fn in sorted(files):
        hsh = hashlib.sha1(files[fn]).hexdigest()
        if hsh in seen:
            alias[fn] = seen[hsh]
        else:
            seen[hsh] = fn
    for fn, data in files.items():
        if fn not in alias:
            open(f'{OUT}/{fn}', 'wb').write(data)
    for th in manifest['themes'].values():
        for key in ('far', 'mid', 'fx'):
            if th.get(key) in alias:
                th[key] = alias[th[key]]
    for e in manifest['sprites'].values():
        e['f'] = alias.get(e['f'], e['f'])
    print('identical files kept once:', len(alias))
    json.dump(manifest, open(mpath, 'w'), separators=(',', ':'))
    tot = sum(os.path.getsize(f'{OUT}/{f}') for f in os.listdir(OUT))
    print('files', len(os.listdir(OUT)), 'total KB', tot // 1024, 'in %.1fs' % (time.time() - t0))
