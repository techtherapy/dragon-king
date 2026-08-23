#!/usr/bin/env python3
"""Trace the portrait of the Sixteenth Karmapa into assets/naga-karmapa.svg.

Unlike the mudra and Dharmaraksa references, which were line drawings, the
reference here (extra-content/karmapa-reference.png, supplied by the site's
owner) is a photograph. A line tracer cannot draw a lifelike face, so this
takes a tonal approach: the photograph is posterised into three darkness
levels inside an arched vignette, and each level's regions are traced into
gold at a different opacity — the gold-on-indigo equivalent of a two-block
woodcut print. Dark features (eyes, brows, the crown's pattern) become
bright gold ink; midtones become dimmer washes; highlights stay indigo.

Run from the repo root:  python3 scripts/trace_karmapa.py
"""
import math
import struct
import subprocess
import tempfile
from pathlib import Path

from trace_mudra import boundary_loops, rdp

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "extra-content" / "karmapa-reference.png"
OUT = ROOT / "assets" / "naga-karmapa.svg"

GOLD = "#d9b25f"
BRIGHT = "#f4dc96"
# brightness thresholds -> (fill, opacity); brightest first. Gold renders
# the LIGHT, as gold ink does — highlights bright, midtones washed, shadow
# left to the indigo ground.
LEVELS = [(196, BRIGHT, 1.0),
          (150, GOLD,   0.55),
          (104, GOLD,   0.26)]
EPSILON = 1.4
MIN_LOOP = 18
VIEW_H = 1000


def load_lum():
    """Photograph -> luminance grid (via sips BMP, box-blurred once)."""
    with tempfile.NamedTemporaryFile(suffix=".bmp", delete=False) as t:
        bmp = t.name
    subprocess.run(["sips", "-s", "format", "bmp", str(SRC), "--out", bmp],
                   check=True, capture_output=True)
    data = Path(bmp).read_bytes()
    Path(bmp).unlink()
    off = struct.unpack_from("<I", data, 10)[0]
    w, h = struct.unpack_from("<ii", data, 18)
    flipped = h > 0
    h = abs(h)
    stride = (w * 3 + 3) & ~3
    lum = [[0] * w for _ in range(h)]
    for row in range(h):
        y = (h - 1 - row) if flipped else row
        base = off + row * stride
        line = data[base:base + w * 3]
        L = lum[y]
        for x in range(w):
            b, g, r = line[x * 3], line[x * 3 + 1], line[x * 3 + 2]
            L[x] = (r * 299 + g * 587 + b * 114) // 1000
    # one 3x3 box blur to stop photographic grain becoming speckle
    out = [[0] * w for _ in range(h)]
    for y in range(h):
        y0, y1 = max(0, y - 1), min(h - 1, y + 1)
        for x in range(w):
            x0, x1 = max(0, x - 1), min(w - 1, x + 1)
            s = n = 0
            for yy in range(y0, y1 + 1):
                for xx in range(x0, x1 + 1):
                    s += lum[yy][xx]; n += 1
            out[y][x] = s // n
    # second pass for smoother posterisation
    out2 = [[0] * w for _ in range(h)]
    for y in range(h):
        y0, y1 = max(0, y - 1), min(h - 1, y + 1)
        for x in range(w):
            x0, x1 = max(0, x - 1), min(w - 1, x + 1)
            s = n = 0
            for yy in range(y0, y1 + 1):
                for xx in range(x0, x1 + 1):
                    s += out[yy][xx]; n += 1
            out2[y][x] = s // n
    return out2, w, h


def arch_mask(w, h):
    """The vignette: a moon-gate arch (round top, straight sides), matching
    the shrine-niche framing used for photographs elsewhere on the site."""
    cx = w * 0.45         # the subject sits left of the photo centre
    r = w * 0.345         # arch half-width, cropping at the shoulder line
    top_cy = h * 0.34     # centre of the round top
    bottom = h * 0.985
    def inside(x, y):
        if y > bottom or abs(x - cx) > r:
            return False
        if y >= top_cy:
            return True
        dx, dy = (x - cx) / r, (y - top_cy) / (top_cy * 0.92)
        return dx * dx + dy * dy <= 1.0
    return inside


def vignette(w, h):
    """Exposure falloff toward the arch edge, so the bright background near
    the frame sinks into the indigo while the face keeps full strength."""
    cx, cy = w * 0.44, h * 0.44
    rx, ry = w * 0.30, h * 0.38
    def f(x, y):
        d = math.hypot((x - cx) / rx, (y - cy) / ry)
        if d <= 1.0:
            return 1.0
        return max(0.42, 1.0 - (d - 1.0) * 2.2)
    return f


def trace_level(lum, w, h, thresh, inside, fall):
    mask = [bytearray(w) for _ in range(h)]
    for y in range(h):
        L = lum[y]; m = mask[y]
        for x in range(w):
            if L[x] * fall(x, y) > thresh and inside(x, y):
                m[x] = 1
    loops = boundary_loops(mask, w, h)
    loops = [l for l in loops if len(l) >= MIN_LOOP]
    parts = []
    for loop in loops:
        simp = rdp(loop, EPSILON)
        if len(simp) >= 3:
            parts.append(simp)
    return parts


def build():
    lum, w, h = load_lum()
    inside = arch_mask(w, h)
    fall = vignette(w, h)
    s = VIEW_H / h
    view_w = round(w * s)

    layers = []
    for thresh, fill, op in LEVELS:
        parts = trace_level(lum, w, h, thresh, inside, fall)
        d = " ".join(
            "M" + "L".join(f"{x * s:.1f} {y * s:.1f}" for x, y in loop) + "Z"
            for loop in parts)
        layers.append((fill, op, d, len(parts)))
        print(f"  level <{thresh}: {len(parts)} regions")

    paths = "\n".join(
        f'<path fill="{fill}" fill-opacity="{op}" fill-rule="evenodd" d="{d}"/>'
        for fill, op, d, _ in layers)
    # the arch outline, echoing the photograph frames elsewhere on the site
    cx, r, top_cy = view_w * 0.45, view_w * 0.345, VIEW_H * 0.34
    frame = (f'<path fill="none" stroke="{GOLD}" stroke-width="2.5" '
             f'd="M{cx - r:.0f} {VIEW_H * 0.985:.0f} L{cx - r:.0f} {top_cy:.0f} '
             f'A{r:.0f} {top_cy * 0.92:.0f} 0 0 1 {cx + r:.0f} {top_cy:.0f} '
             f'L{cx + r:.0f} {VIEW_H * 0.985:.0f} Z"/>')

    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {view_w} {VIEW_H}" '
           f'role="img" aria-label="The Sixteenth Gyalwa Karmapa, smiling, in his '
           f'brocade ceremonial crown — a tonal gold portrait traced from a photograph">\n'
           f'{paths}\n{frame}\n</svg>\n')
    OUT.write_text(svg, encoding="utf-8")
    print(f"  -> naga-karmapa.svg {len(svg) / 1024:.0f} KB, viewBox 0 0 {view_w} {VIEW_H}")


if __name__ == "__main__":
    build()
