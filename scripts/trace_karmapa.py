#!/usr/bin/env python3
"""Trace the portrait of the Sixteenth Karmapa into assets/naga-karmapa.svg.

The reference (extra-content/karmapa-reference.png, supplied by the site's
owner) is a photograph, and the article wants a LINE drawing in the site's
gold-on-indigo language. Lines are extracted with a difference-of-Gaussians
filter — the classic photograph-to-line-drawing operator: it responds where
a feature is darker than its surroundings (eyes, the smile, the crown's
brocade pattern), producing coherent strokes rather than posterised tone.
The strokes are dilated once for body, masked to an arched vignette, and
traced into a single gold path like the site's other traced artwork.

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
SIGMA = 2.0          # base blur radius of the DoG pair (px)
K = 1.8              # ratio between the two blurs
TAU = 9.0            # line response threshold
DILATE = 1           # stroke body, in dilation passes
EPSILON = 1.5
MIN_LOOP = 34
VIEW_H = 1000


def load_lum():
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
    lum = [[0.0] * w for _ in range(h)]
    for row in range(h):
        y = (h - 1 - row) if flipped else row
        base = off + row * stride
        line = data[base:base + w * 3]
        L = lum[y]
        for x in range(w):
            b, g, r = line[x * 3], line[x * 3 + 1], line[x * 3 + 2]
            L[x] = (r * 299 + g * 587 + b * 114) / 1000.0
    return lum, w, h


def box_blur(grid, w, h, radius):
    """Separable sliding-window box blur; three passes approximate a
    Gaussian of sigma ~ radius."""
    r = max(1, int(round(radius)))
    out = grid
    for _ in range(3):
        tmp = [[0.0] * w for _ in range(h)]
        for y in range(h):
            row = out[y]
            s = sum(row[0:r + 1]) + row[0] * r
            n = 2 * r + 1
            for x in range(w):
                tmp[y][x] = s / n
                s += row[min(w - 1, x + r + 1)] - row[max(0, x - r)]
        res = [[0.0] * w for _ in range(h)]
        for x in range(w):
            s = sum(tmp[y][x] for y in range(0, r + 1)) + tmp[0][x] * r
            n = 2 * r + 1
            for y in range(h):
                res[y][x] = s / n
                s += tmp[min(h - 1, y + r + 1)][x] - tmp[max(0, y - r)][x]
        out = res
    return out


def arch_mask(w, h):
    cx = w * 0.45
    r = w * 0.345
    top_cy = h * 0.34
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
    cx, cy = w * 0.44, h * 0.44
    rx, ry = w * 0.30, h * 0.38
    def f(x, y):
        d = math.hypot((x - cx) / rx, (y - cy) / ry)
        return 1.0 if d <= 1.0 else max(0.0, 1.0 - (d - 1.0) * 2.4)
    return f


def build():
    lum, w, h = load_lum()
    g1 = box_blur(lum, w, h, SIGMA)
    g2 = box_blur(lum, w, h, SIGMA * K)
    inside = arch_mask(w, h)
    fall = vignette(w, h)

    mask = [bytearray(w) for _ in range(h)]
    for y in range(h):
        m = mask[y]
        r1, r2 = g1[y], g2[y]
        for x in range(w):
            # negative DoG = locally darker than surround = a drawn line
            if (r2[x] - r1[x]) * fall(x, y) > TAU and inside(x, y):
                m[x] = 1

    for _ in range(DILATE):
        grown = [bytearray(row) for row in mask]
        for y in range(1, h - 1):
            for x in range(1, w - 1):
                if not mask[y][x] and (mask[y][x - 1] or mask[y][x + 1] or
                                       mask[y - 1][x] or mask[y + 1][x]):
                    grown[y][x] = 1
        mask = grown

    loops = [l for l in boundary_loops(mask, w, h) if len(l) >= MIN_LOOP]
    s = VIEW_H / h
    view_w = round(w * s)
    parts = []
    for loop in loops:
        simp = rdp(loop, EPSILON)
        if len(simp) >= 3:
            parts.append("M" + "L".join(f"{x * s:.1f} {y * s:.1f}" for x, y in simp) + "Z")

    cx, r, top_cy = view_w * 0.45, view_w * 0.345, VIEW_H * 0.34
    frame = (f'<path fill="none" stroke="{GOLD}" stroke-width="2.5" '
             f'd="M{cx - r:.0f} {VIEW_H * 0.985:.0f} L{cx - r:.0f} {top_cy:.0f} '
             f'A{r:.0f} {top_cy * 0.92:.0f} 0 0 1 {cx + r:.0f} {top_cy:.0f} '
             f'L{cx + r:.0f} {VIEW_H * 0.985:.0f} Z"/>')

    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {view_w} {VIEW_H}" '
           f'role="img" aria-label="The Sixteenth Gyalwa Karmapa, smiling, in his '
           f'brocade ceremonial crown — a gold line portrait traced from a photograph">\n'
           f'<path fill="{GOLD}" fill-rule="evenodd" stroke="{GOLD}" stroke-width="1.2" '
           f'stroke-linejoin="round" d="{" ".join(parts)}"/>\n{frame}\n</svg>\n')
    OUT.write_text(svg, encoding="utf-8")
    print(f"  {len(parts)} strokes -> naga-karmapa.svg {len(svg) / 1024:.0f} KB")


if __name__ == "__main__":
    build()
