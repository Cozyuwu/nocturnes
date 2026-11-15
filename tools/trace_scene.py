"""Trace a painting into an animated SVG scene the desktop window will draw.

The window takes no picture files as a background, only vector shapes, at most 131,072 characters.
So the painting is reduced to flat tones and traced: finer round the girl, coarser in the far dark.
Her hair is traced a second time as its own layer, which sways; lights flicker and dust drifts.

Each painting has a small JSON file beside it saying where things are (all positions are fractions
of the picture's width and height):

  near    [x0, y0, x1, y1]   the box round the girl and her things, traced finely (or a list of boxes)
  tones   how many flat tones the painting is reduced to (16)
  far     {"eps": 3.4, "min": 190}   how finely the distance is traced: smaller is finer
  hair    how to find her hair, and the box it lies in:
            {"points": [[x, y], ...], "tol": 8}    points on her hair, which a cut-out grows from
            {"ratio": {...}}                        or a rule on red, green and blue
          with "box", optional "cut" boxes left out, and "lean", how far it sways (1 is usual)
  glow    [[x, y, radius, inner colour, outer colour], ...]   soft glows that waver (lamps, screens)
  beam    {"points": [[x, y] * 4], "color": "#a9c4ff"}        a shaft of light, or null
  motes   {"from": [x, y], "to": [x, y], "color": "#cfe0ff"}  dust drifting along a line, or null
  lights  {"rule": "warm" | "bright", "skip": [x0, y0, x1, y1]}  the small lights that flicker, and the box
          (or boxes) where nothing is to flicker: her dress, rain on a window, flowers
  note    the comment written at the top of the module

python trace_scene.py <painting> <config.json> <out.svg> <out_module.js> [budget]
"""
import json
import math
import sys

import cv2
import numpy as np

SRC, CONFIG, OUT_SVG, OUT_JS = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
BUDGET = int(sys.argv[5]) if len(sys.argv) > 5 else 130_700
CFG = json.load(open(CONFIG, encoding='utf-8'))
W, H = 1600, 900
K = CFG.get('tones', 16)
FAR = CFG.get('far', {})                        # how finely the distance is traced: {"eps": 3.4, "min": 190}

bgr_full = cv2.imread(SRC, cv2.IMREAD_COLOR)
FH, FW = bgr_full.shape[:2]
# The left, where the words sit, eased down.
x01 = np.linspace(0, 1, FW, dtype=np.float32)[None, :, None]
ease = 1.0 - 0.38 * np.clip((0.52 - x01) / 0.52, 0, 1) ** 0.85
bgr_full = np.clip(bgr_full.astype(np.float32) * ease, 0, 255).astype(np.uint8)
img = cv2.resize(bgr_full, (W, H), interpolation=cv2.INTER_AREA)
sx, sy = W / FW, H / FH
AREA = (FW / 2514.0) ** 2                      # areas below were chosen on a picture 2514 wide


def box_mask(box, xs, ys, w, h):
    return (xs > box[0] * w) & (xs < box[2] * w) & (ys > box[1] * h) & (ys < box[3] * h)


# ---- zones: fine round the girl and her things, coarse elsewhere ----
yy, xx = np.mgrid[0:H, 0:W]
NEAR = CFG['near'] if isinstance(CFG['near'][0], list) else [CFG['near']]
near = np.zeros((H, W), dtype=bool)
for one in NEAR:
    near |= box_mask(one, xx, yy, W, H)
near = cv2.GaussianBlur(near.astype(np.float32), (0, 0), 12) > 0.5

# ---- her hair, found by colour at full size ----
b, g, r = [bgr_full[..., i].astype(np.float32) / 255.0 for i in range(3)]
fy, fx = np.mgrid[0:FH, 0:FW]
HAIR = CFG['hair']
if 'ratio' in HAIR:
    q = HAIR['ratio']
    like = (r > q['r_min']) & (g / (r + 1e-6) > q['g_r'][0]) & (g / (r + 1e-6) < q['g_r'][1]) & (b / (r + 1e-6) < q['b_r_max'])
else:
    like = None
region = box_mask(HAIR['box'], fx, fy, FW, FH)
for cut in HAIR.get('cut', []):
    region &= ~box_mask(cut, fx, fy, FW, FH)
if like is None:
    # Colours like those at the points seed a cut-out (GrabCut), which then follows her hair's own
    # edges: it holds where the hair and what is behind it are near in colour, as blue hair on blue water.
    soft = cv2.cvtColor(cv2.pyrMeanShiftFiltering(bgr_full, 5, 14), cv2.COLOR_BGR2LAB).astype(np.float32)
    seed = np.zeros((FH, FW), dtype=bool)
    for px, py in HAIR['points']:
        d = soft - soft[min(FH - 1, int(py * FH)), min(FW - 1, int(px * FW))]
        # Lightness counts for less than hue, so lit and shaded strands are both taken.
        seed |= np.sqrt(0.35 * d[..., 0] ** 2 + d[..., 1] ** 2 + d[..., 2] ** 2) < HAIR.get('tol', 8)
    cut_out = np.where(region, np.where(seed, cv2.GC_PR_FGD, cv2.GC_PR_BGD), cv2.GC_BGD).astype(np.uint8)
    for px, py in HAIR['points']:
        cv2.circle(cut_out, (int(px * FW), int(py * FH)), max(3, FW // 330), cv2.GC_FGD, -1)
    cut_out[~region] = cv2.GC_BGD
    ry, rx = np.nonzero(region)
    win = (slice(max(0, ry.min() - 40), min(FH, ry.max() + 40)), slice(max(0, rx.min() - 40), min(FW, rx.max() + 40)))
    part = cut_out[win].copy()
    cv2.grabCut(np.ascontiguousarray(bgr_full[win]), part, None, np.zeros((1, 65), np.float64), np.zeros((1, 65), np.float64), 6, cv2.GC_INIT_WITH_MASK)
    like = np.zeros((FH, FW), dtype=bool)
    like[win] = np.isin(part, (cv2.GC_FGD, cv2.GC_PR_FGD))
hair_full = (like & region).astype(np.uint8)
hair_full = cv2.morphologyEx(hair_full, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
n, lab_cc, stats, _ = cv2.connectedComponentsWithStats(hair_full)
keep = np.zeros_like(hair_full)
for i in range(1, n):
    if stats[i, cv2.CC_STAT_AREA] > 1500 * AREA:
        keep[lab_cc == i] = 1
close = max(5, int(round(13 * FW / 2514)) | 1)
hair_full = cv2.morphologyEx(keep, cv2.MORPH_CLOSE, np.ones((close, close), np.uint8))
hair = cv2.resize(hair_full, (W, H), interpolation=cv2.INTER_AREA) > 0

# ---- flatten to a few tones ----
flat = cv2.pyrMeanShiftFiltering(img, 6, 16)
flat_near = cv2.pyrMeanShiftFiltering(img, 5, 14)
flat[near] = flat_near[near]
lab = cv2.cvtColor(flat, cv2.COLOR_BGR2LAB).astype(np.float32)
rng = np.random.default_rng(5)
pix_far = lab[~near].reshape(-1, 3)
pix_near = lab[near].reshape(-1, 3)
sample = np.vstack([pix_far[rng.choice(len(pix_far), 50_000, replace=False)], pix_near[rng.choice(len(pix_near), min(len(pix_near), 90_000), replace=False)]])
_, _, centers = cv2.kmeans(sample, K, None, (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 40, 0.5), 4, cv2.KMEANS_PP_CENTERS)
dist = ((lab[:, :, None, :] - centers[None, None, :, :]) ** 2).sum(axis=3)
labels = dist.argmin(axis=2).astype(np.uint8)
palette = cv2.cvtColor(centers.reshape(1, K, 3).astype(np.uint8), cv2.COLOR_LAB2BGR).reshape(K, 3)


def hexcol(c):
    return '#%02x%02x%02x' % (int(c[2]), int(c[1]), int(c[0]))


def trace(mask, eps_far, eps_near, min_far, min_near, grow=1):
    """The outlines of a mask as one path's worth of subpaths, simplified by zone."""
    m = mask.astype(np.uint8)
    if grow:
        m = cv2.dilate(m, np.ones((3, 3), np.uint8), iterations=grow)
    contours, hier = cv2.findContours(m, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    parts = {False: [], True: []}
    if hier is None:
        return '', ''
    for c, h in zip(contours, hier[0]):
        area = cv2.contourArea(c)
        x, y, w, hh = cv2.boundingRect(c)
        is_near = bool(near[min(H - 1, y + hh // 2), min(W - 1, x + w // 2)])
        is_hole = h[3] != -1
        min_area = (min_near if is_near else min_far) * (1.6 if is_hole else 1.0)
        if area < min_area:
            continue
        pts = cv2.approxPolyDP(c, eps_near if is_near else eps_far, True).reshape(-1, 2)
        if len(pts) < 3:
            continue
        seg = f'M{pts[0][0]} {pts[0][1]}'
        prev, mode = pts[0], ''
        for p in pts[1:]:
            dx, dy = int(p[0] - prev[0]), int(p[1] - prev[1])
            prev = p
            if dx == 0 and dy == 0:
                continue
            cmd, nums = ('h', f'{dx}') if dy == 0 else ('v', f'{dy}') if dx == 0 else ('l', f'{dx} {dy}')
            seg += (cmd if cmd != mode else ('' if nums.startswith('-') else ' ')) + nums
            mode = cmd
        parts[is_near].append(seg.replace(' -', '-') + 'z')
    return ''.join(parts[False]), ''.join(parts[True])


def build(scale):
    """All the tone layers at one level of detail; larger `scale` is coarser."""
    order = sorted(range(K), key=lambda k: -(labels == k).sum())
    base = order[0]
    far_out, near_out = [], []
    for k in order[1:]:
        far, close_by = trace(labels == k, FAR.get('eps', 3.4), 0.7 * scale, FAR.get('min', 190), 6 * scale * scale)
        if far:
            far_out.append(f'<path fill="{hexcol(palette[k])}" d="{far}"/>')
        if close_by:
            near_out.append(f'<path fill="{hexcol(palette[k])}" d="{close_by}"/>')
    # The far distance is softened, the way distance softens it; she and her things stay crisp.
    return (f'<rect width="{W}" height="{H}" fill="{hexcol(palette[base])}"/><g filter="url(#fb)">' + ''.join(far_out) + '</g>' + ''.join(near_out))


def hair_layer(scale):
    out = []
    for k in range(K):
        m = (labels == k) & hair
        if m.sum() < 60:
            continue
        d = ''.join(trace(m, 0.8 * scale, 0.8 * scale, 10 * scale, 10 * scale, grow=1))
        if d:
            out.append(f'<path fill="{hexcol(palette[k])}" d="{d}"/>')
    return ''.join(out)


hy, hx = np.nonzero(hair)
top, bottom, left, right = hy.min(), hy.max(), hx.min(), hx.max()

# ---- small lights: lamps, candles, stars, screens too small to trace ----
LIGHTS = CFG.get('lights', {})
if LIGHTS.get('rule', 'bright') == 'warm':
    lit = (r > 0.7) & (r - b > 0.22) & (g > 0.35)
else:
    value = np.maximum(np.maximum(r, g), b)
    lit = (value > 0.6) & (value - cv2.GaussianBlur(value, (0, 0), 14 * FW / 2514) > 0.15)
n, lab_cc, stats, cents = cv2.connectedComponentsWithStats(lit.astype(np.uint8))
skip = LIGHTS.get('skip', [0.6, 0.42, 1.0, 1.0])
skip = skip if isinstance(skip[0], list) else [skip]
lights = []
for i in range(1, n):
    a = stats[i, cv2.CC_STAT_AREA] / AREA
    cx, cy = cents[i]
    if a < 6 or a > 900:
        continue
    px, py = cx * sx, cy * sy
    if hair[min(H - 1, int(py)), min(W - 1, int(px))] or (left - 25 < px < right + 10 and top - 25 < py < bottom):
        continue                                 # nothing twinkles in her hair or on its ornaments
    if any(one[0] * W < px < one[2] * W and one[1] * H < py < one[3] * H for one in skip):
        continue                                 # her dress and the things by her are traced, not dotted
    col = bgr_full[lab_cc == i].mean(axis=0)
    lights.append((a, px, py, min(3.2, max(0.9, math.sqrt(a / math.pi) * (W / 2514) * 1.25)), col))
lights.sort(key=lambda t: -t[0])
lights = lights[:260]
if LIGHTS.get('rule', 'bright') == 'warm' or len(lights) < 3:
    light_colours = ['#ffc070', '#ffd28e', '#ffad5c']
    tint = [j % 3 for j in range(len(lights))]
else:
    # Three colours taken from the lights themselves, each brightened to read as a light.
    cols = np.float32([t[4] for t in lights])
    _, which, mids = cv2.kmeans(cols, 3, None, (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.5), 3, cv2.KMEANS_PP_CENTERS)
    light_colours = [hexcol(np.clip(m * (255.0 / max(1.0, m.max())) * 0.55 + 255 * 0.45 * (m / max(1.0, m.max())), 0, 255)) for m in mids]
    tint = [int(w) for w in which.ravel()]
light_dots = {}
for j, (a, px, py, rad, col) in enumerate(lights):
    light_dots.setdefault((j % 3, tint[j], rad > 1.6), []).append(f'M{px:.0f} {py:.0f}h.1')
light_groups = ['', '', '']
for (grp, colour, big), dots in sorted(light_dots.items()):
    light_groups[grp] += f'<path stroke="{light_colours[colour]}" stroke-width="{4.6 if big else 2.5}" d="{"".join(dots)}"/>'

# ---- dust drifting along a line (down a moonbeam, across a doorway) ----
MOTES = CFG.get('motes')
motes = ''
if MOTES:
    (ax, ay), (bx, by) = MOTES['from'], MOTES['to']
    for j in range(MOTES.get('n', 34)):
        t = rng.uniform(0.05, 1.0)
        cx, cy = (ax + (bx - ax) * t) * W, (ay + (by - ay) * t) * H
        side = rng.uniform(-1, 1) * (26 + 58 * t)
        motes += f'<circle class="m m{j % 6}" cx="{cx + side * 0.86:.0f}" cy="{cy + side * 0.5:.0f}" r="{rng.uniform(0.8, 1.7):.1f}"/>'

# The hair hangs as a chain of bands. Each leans from the foot of the one above and a beat after it,
# so it is still at her head and a slow wave runs down to the ends, the wind mostly from one side.
EDGES = [int(top + (bottom - top) * f) for f in (0.0, 0.14, 0.3, 0.47, 0.64, 0.81, 1.0)]
LEAN = tuple(round(v * HAIR.get('lean', 1.0), 2) for v in (0.0, 1.0, 1.6, 2.2, 2.8, 3.2))   # degrees each band adds
BEAT, PERIOD = 0.42, 5.8                            # seconds a band trails the one above; seconds a sway takes
HAIR_CSS = ''.join(
    f'.h{k}{{transform-origin:0 {EDGES[k]}px;animation:w{k} {PERIOD}s ease-in-out {k * BEAT - PERIOD:.2f}s infinite}}'
    f'@keyframes w{k}{{0%,100%{{transform:skewX({-0.5 * LEAN[k]:.2f}deg)}}45%{{transform:skewX({LEAN[k]}deg)}}72%{{transform:skewX({0.5 * LEAN[k]:.2f}deg)}}}}'
    for k in range(1, len(LEAN)))
GLOWS = CFG.get('glow', [])
BEAM = CFG.get('beam')
MOTE_COLOUR = (MOTES or {}).get('color', '#cfe0ff')

STYLE = f"""
{HAIR_CSS}
.l0{{animation:f 3.1s ease-in-out infinite}}.l1{{animation:f 4.3s ease-in-out -1.2s infinite}}.l2{{animation:f 5.2s ease-in-out -2.6s infinite}}
@keyframes f{{0%,100%{{opacity:1}}38%{{opacity:.62}}61%{{opacity:.9}}74%{{opacity:.7}}}}
.lamp{{animation:f 2.7s ease-in-out infinite}}
.beam{{animation:b 9s ease-in-out infinite}}
@keyframes b{{0%,100%{{opacity:.5}}50%{{opacity:.85}}}}
.m{{fill:{MOTE_COLOUR};opacity:0;animation:d 11s linear infinite}}
.m1{{animation-delay:-2s;animation-duration:13s}}.m2{{animation-delay:-4.5s}}.m3{{animation-delay:-6s;animation-duration:15s}}.m4{{animation-delay:-8s}}.m5{{animation-delay:-9.5s;animation-duration:12s}}
@keyframes d{{0%{{opacity:0;transform:translate(0,0)}}25%{{opacity:.75}}75%{{opacity:.6}}100%{{opacity:0;transform:translate(-26px,14px)}}}}
@media (prefers-reduced-motion:reduce){{*{{animation:none!important}}}}
""".replace('\n', '')


def assemble(scale):
    body = build(scale)
    hl = hair_layer(max(1.0, scale * 0.9))
    pad = 30
    defs = (
        f'<defs><filter id="g" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="2.4" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>'
        f'<filter id="s" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="16"/></filter><filter id="fb" x="0" y="0" width="100%" height="100%"><feGaussianBlur stdDeviation="2.3"/></filter>'
        + ''.join(f'<radialGradient id="lg{i}"><stop offset="0" stop-color="{gl[3]}" stop-opacity=".55"/><stop offset="1" stop-color="{gl[4]}" stop-opacity="0"/></radialGradient>' for i, gl in enumerate(GLOWS))
        + ''.join(f'<clipPath id="c{k}"><rect x="{left - 90}" y="{EDGES[k] - (pad if k == 0 else 0)}" width="{right - left + 180}" height="{EDGES[k + 1] - EDGES[k] + (pad if k in (0, len(LEAN) - 1) else 1)}"/></clipPath>' for k in range(len(LEAN))) +
        f'<g id="hair">{hl}</g></defs>'
    )
    beam = ''
    if BEAM:
        points = ' '.join(f'{px * W:.0f},{py * H:.0f}' for px, py in BEAM['points'])
        beam = f'<polygon class="beam" filter="url(#s)" fill="{BEAM.get("color", "#a9c4ff")}" fill-opacity=".1" points="{points}"/>'
    lamps = ''.join(f'<circle class="lamp" cx="{gl[0] * W:.0f}" cy="{gl[1] * H:.0f}" r="{gl[2] * W:.0f}" fill="url(#lg{i})"/>' for i, gl in enumerate(GLOWS))
    hair_svg = ''
    for k in reversed(range(len(LEAN))):
        cls = f' class="h{k}"' if k else ''
        hair_svg = f'<g{cls}><g clip-path="url(#c{k})"><use href="#hair"/></g>{hair_svg}</g>'
    lights_svg = '<g filter="url(#g)" fill="none" stroke-linecap="round">' + ''.join(f'<g class="l{i}">{grp}</g>' for i, grp in enumerate(light_groups)) + '</g>'
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" preserveAspectRatio="xMidYMid slice"><style>{STYLE}</style>{defs}'
            f'{body}{beam}{lights_svg}{lamps}{hair_svg}{motes}</svg>')


scale = 1.0
svg = assemble(scale)
while len(svg) > BUDGET:
    scale *= 1.008
    svg = assemble(scale)
print('scale', round(scale, 3), 'chars', len(svg), 'lights', len(lights), 'hair box', (left, top, right, bottom), 'hair share of its box', round(float(hair[top:bottom + 1, left:right + 1].mean()), 2))
open(OUT_SVG, 'w', encoding='utf-8').write(svg)
open(OUT_JS, 'w', encoding='utf-8', newline='\n').write(
    f'// {CFG.get("note", "A painting traced into shapes")} (tools/trace_scene.py).\n'
    'export const SCENE = ' + json.dumps(svg) + '\n')
# A picture of what was taken as hair, to check by eye.
check = img.copy()
check[hair] = (0.45 * check[hair] + 0.55 * np.array([255, 0, 255])).astype(np.uint8)
for one in NEAR:
    cv2.rectangle(check, (int(one[0] * W), int(one[1] * H)), (int(one[2] * W), int(one[3] * H)), (0, 255, 0), 1)
for _, px, py, _, _ in lights:
    cv2.circle(check, (int(px), int(py)), 4, (0, 255, 255), 1)
cv2.imwrite(OUT_SVG[:-4] + '_check.jpg', check, [cv2.IMWRITE_JPEG_QUALITY, 85])
