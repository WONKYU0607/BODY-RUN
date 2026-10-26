# Real-ESRGAN (RRDBNet, x4, anime 6-block weights) inference in plain numpy - no torch in this workspace.
# Loads the .pth zip directly (its pickle names torch storages; rebuilt here as numpy arrays).
import pickle, zipfile, numpy as np

def load_pth(path):
    zf = zipfile.ZipFile(path)
    root = zf.namelist()[0].split('/')[0]
    dt = {'FloatStorage': np.float32, 'HalfStorage': np.float16, 'LongStorage': np.int64}

    class Storage:
        def __init__(self, name): self.name = name

    def rebuild(storage, offset, size, stride, *rest):
        a = storage
        if not size: return a[offset:offset + 1].reshape(())
        return np.lib.stride_tricks.as_strided(a[offset:], shape=tuple(size),
                                               strides=tuple(s * a.itemsize for s in stride)).copy()

    class U(pickle.Unpickler):
        def find_class(self, mod, name):
            if name == '_rebuild_tensor_v2': return rebuild
            if name.endswith('Storage'): return Storage(name)
            if mod == 'collections' and name == 'OrderedDict':
                import collections; return collections.OrderedDict
            return super().find_class(mod, name)

        def persistent_load(self, pid):
            _, st, key, loc, numel = pid
            raw = zf.read(f'{root}/data/{key}')
            return np.frombuffer(raw, dt[st.name]).astype(np.float32)

    with zf.open(f'{root}/data.pkl') as f:
        return U(f).load()


def conv(x, w, b):
    """x (C,H,W) float32, w (O,C,3,3) -> (O,H,W), padding 1, done as 9 shifted matmuls in row bands."""
    C, H, W = x.shape
    O = w.shape[0]
    xp = np.pad(x, ((0, 0), (1, 1), (1, 1)))
    out = np.empty((O, H, W), np.float32)
    band = max(1, int(6e6 // (C * W)))
    for r0 in range(0, H, band):
        r1 = min(H, r0 + band)
        acc = np.zeros((O, (r1 - r0) * W), np.float32)
        for dy in range(3):
            for dx in range(3):
                s = np.ascontiguousarray(xp[:, r0 + dy:r1 + dy, dx:dx + W]).reshape(C, -1)
                acc += w[:, :, dy, dx] @ s
        out[:, r0:r1] = (acc + b[:, None]).reshape(O, r1 - r0, W)
    return out


def lrelu(x): return np.where(x > 0, x, 0.2 * x)


def run(img, P):
    """img (H,W,3) float in [0,1] -> (4H,4W,3)."""
    g = lambda k: (P[k + '.weight'], P[k + '.bias'])
    x = img.transpose(2, 0, 1).astype(np.float32)
    feat = conv(x, *g('conv_first'))
    nb = 1 + max(int(k.split('.')[1]) for k in P if k.startswith('body.'))
    body = feat
    for i in range(nb):
        inp = body
        for j in (1, 2, 3):
            p = f'body.{i}.rdb{j}.'
            xs = [body]
            for c in range(1, 5):
                xs.append(lrelu(conv(np.concatenate(xs, 0), *g(p + f'conv{c}'))))
            x5 = conv(np.concatenate(xs, 0), *g(p + 'conv5'))
            body = x5 * 0.2 + body
        body = body * 0.2 + inp
    feat = feat + conv(body, *g('conv_body'))
    up = lambda t: t.repeat(2, 1).repeat(2, 2)
    feat = lrelu(conv(up(feat), *g('conv_up1')))
    feat = lrelu(conv(up(feat), *g('conv_up2')))
    out = conv(lrelu(conv(feat, *g('conv_hr'))), *g('conv_last'))
    return np.clip(out.transpose(1, 2, 0), 0, 1)


if __name__ == '__main__':
    import sys, time
    from PIL import Image
    P = load_pth(sys.argv[1])
    P = P.get('params_ema', P.get('params', P))
    im = np.array(Image.open(sys.argv[2]).convert('RGB')).astype(np.float32) / 255
    t = time.time()
    o = run(im, P)
    print('took', round(time.time() - t, 1), 's', o.shape)
    Image.fromarray((o * 255 + 0.5).astype(np.uint8)).save(sys.argv[3])
