"""Stitch the four redrawn sections back into one picture.

Each section keeps its own fine detail; the broad light and colour come from the whole picture, so no
section drifts from its neighbours. Seams run through the overlaps, and the girl comes from one section.
"""
import numpy as np
from PIL import Image, ImageFilter

BASE = Image.open('library_4k.png').convert('RGB')
TW, TH = 1112, 626
S = 1672 / TW
W, H = round(BASE.size[0] * S), round(BASE.size[1] * S)
ORIGINS = [(0, 0), (560, 0), (0, 315), (560, 315)]
SIGMA = 14


def arr(im):
    return np.asarray(im, dtype=np.float32) / 255.0


def blur(a, sigma):
    return arr(Image.fromarray((np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8)).filter(ImageFilter.GaussianBlur(sigma)))


def shift_of(a, b):
    """How far b sits from a, in whole pixels, by phase correlation."""
    ga, gb = a.mean(axis=2), b.mean(axis=2)
    ga, gb = ga - ga.mean(), gb - gb.mean()
    f = np.fft.rfft2(ga) * np.conj(np.fft.rfft2(gb))
    r = np.fft.irfft2(f / (np.abs(f) + 1e-6), s=ga.shape)
    y, x = np.unravel_index(np.argmax(r), r.shape)
    return (x if x < ga.shape[1] // 2 else x - ga.shape[1]), (y if y < ga.shape[0] // 2 else y - ga.shape[0])


base = arr(BASE.resize((W, H), Image.LANCZOS))
tiles = []
for i, (x0, y0) in enumerate(ORIGINS):
    px, py = round(x0 * S), round(y0 * S)
    t = arr(Image.open(f'tiles/out_{i}.png').convert('RGB'))
    ref = base[py:py + 941, px:px + 1672]
    dx, dy = shift_of(ref, t)
    print('tile', i, 'at', (px, py), 'drift', (dx, dy))
    if abs(dx) <= 6 and abs(dy) <= 6 and (dx or dy):
        t = np.roll(t, (dy, dx), axis=(0, 1))
    # Fine detail from the section, broad light from the whole.
    t = t - blur(t, SIGMA) + blur(ref, SIGMA)
    full = np.zeros((H, W, 3), dtype=np.float32)
    full[py:py + 941, px:px + 1672] = t[:H - py, :W - px]
    tiles.append(full)

x = np.arange(W, dtype=np.float32)[None, :]
y = np.arange(H, dtype=np.float32)[:, None]


def ramp(v, centre, half):
    return np.clip((v - (centre - half)) / (2 * half), 0, 1)


# Left and right sections meet down a line left of her; upper and lower meet low on the left
# and just above her head on the right, so she is drawn by one section alone.
wx = ramp(x, 1240.0, 50.0)
top = tiles[0] * (1 - wx)[..., None] + tiles[1] * wx[..., None]
bottom = tiles[2] * (1 - wx)[..., None] + tiles[3] * wx[..., None]
right = ramp(x, 1330.0, 90.0)
seam = 700.0 + (484.0 - 700.0) * right
half = 55.0 + (9.0 - 55.0) * right
wy = np.clip((y - (seam - half)) / (2 * half), 0, 1)
out = top * (1 - wy)[..., None] + bottom * wy[..., None]
Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)).save('library_hd.png')
print('saved library_hd.png', (W, H))
