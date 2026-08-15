#!/usr/bin/env python3
"""Trace the portrait of Tripitaka Master Dharmaraksa into assets/dharmaraksa.svg.

The reference (extra-content/dharmaraksa-reference.png, supplied by the
site's owner) is a classical line drawing of the translator on a speckled
yellow ground, from a book cover that also carries dark-red lettering.

The ink is isolated by colour, not just darkness: the drawing's strokes are
neutral black (r ≈ g ≈ b), while the lettering is maroon (r well above g),
so a "dark AND not red" test keeps the portrait and drops the text without
any hand-drawn crop. The boundary walk and simplification are shared with
the mudra tracer.

Run from the repo root:  python3 scripts/trace_dharmaraksa.py
"""
import struct
import subprocess
import tempfile
from pathlib import Path

from trace_mudra import boundary_loops, rdp

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "extra-content" / "dharmaraksa-reference.png"
OUT = ROOT / "assets" / "dharmaraksa.svg"

GOLD = "#d9b25f"
DARKNESS = 120       # max(r,g,b) below this can be ink
REDNESS = 40         # r exceeding g by more than this is lettering, not ink
EPSILON = 1.7
MIN_LOOP = 24
VIEW_H = 1000        # output height; width follows the ink's aspect


def load_mask():
    with tempfile.NamedTemporaryFile(suffix=".bmp", delete=False) as t:
        bmp_path = t.name
    subprocess.run(["sips", "-s", "format", "bmp", str(SRC), "--out", bmp_path],
                   check=True, capture_output=True)
    data = Path(bmp_path).read_bytes()
    Path(bmp_path).unlink()

    if data[:2] != b"BM":
        raise SystemExit("sips did not produce a BMP")
    off = struct.unpack_from("<I", data, 10)[0]
    w, h = struct.unpack_from("<ii", data, 18)
    bpp = struct.unpack_from("<H", data, 28)[0]
    if bpp != 24:
        raise SystemExit(f"expected 24bpp BMP, got {bpp}")
    flipped = h > 0
    h = abs(h)
    stride = (w * 3 + 3) & ~3

    mask = [bytearray(w) for _ in range(h)]
    for row in range(h):
        y = (h - 1 - row) if flipped else row
        base = off + row * stride
        line = data[base:base + w * 3]
        m = mask[y]
        for x in range(w):
            b = line[x * 3]
            g = line[x * 3 + 1]
            r = line[x * 3 + 2]
            if max(r, g, b) < DARKNESS and (r - g) < REDNESS:
                m[x] = 1

    # the scan carries its own frame line along the edges, and it touches the
    # drawing, so it cannot be dropped as a separate loop — erase the outer
    # few pixels instead (this merely trims strokes that run off the edge)
    for y in range(h):
        for x in range(5):
            mask[y][x] = 0
    for x in range(w):
        for y in range(4):
            mask[y][x] = 0
    return mask, w, h


def build():
    mask, w, h = load_mask()
    ink_px = sum(sum(r) for r in mask)
    loops = boundary_loops(mask, w, h)

    # the paper ground is speckled; a fleck survives the colour test now and
    # then, so anything smaller than a real drawing detail is dropped
    def bbox_span(loop):
        xs = [x for x, _ in loop]
        ys = [y for _, y in loop]
        return max(xs) - min(xs), max(ys) - min(ys)
    def keep(loop):
        xs, ys = bbox_span(loop)
        if max(xs, ys) < 12:
            return False          # speckle
        if min(xs, ys) < 5 and max(xs, ys) > 80:
            return False          # the scan's own border hairline
        return True
    before = len(loops)
    loops = [l for l in loops if keep(l)]
    if before != len(loops):
        print(f"  dropped {before - len(loops)} speckles/border lines")

    # tight box around the ink, with a small margin
    xs = [x for loop in loops for x, _ in loop]
    ys = [y for loop in loops for _, y in loop]
    pad = 10
    x0, y0 = max(0, min(xs) - pad), max(0, min(ys) - pad)
    x1, y1 = min(w, max(xs) + pad), min(h, max(ys) + pad)
    s = VIEW_H / (y1 - y0)
    view_w = round((x1 - x0) * s)

    parts, pts_total = [], 0
    for loop in loops:
        simp = rdp(loop, EPSILON)
        if len(simp) < 3:
            continue
        pts_total += len(simp)
        d = "M" + "L".join(f"{(x - x0) * s:.1f} {(y - y0) * s:.1f}" for x, y in simp) + "Z"
        parts.append(d)

    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {view_w} {VIEW_H}" '
           f'role="img" aria-label="Tripitaka Master Dharmaraksa, translator of the sutra, '
           f'holding a bound manuscript — a classical line portrait">\n'
           f'<path fill="{GOLD}" fill-rule="evenodd" stroke="{GOLD}" '
           f'stroke-width="2.2" stroke-linejoin="round" d="{" ".join(parts)}"/>\n'
           f'</svg>\n')
    OUT.write_text(svg, encoding="utf-8")
    print(f"  ink {ink_px}px, {len(loops)} loops, {pts_total} points, "
          f"viewBox 0 0 {view_w} {VIEW_H} -> dharmaraksa.svg {len(svg) / 1024:.0f} KB")


if __name__ == "__main__":
    build()
