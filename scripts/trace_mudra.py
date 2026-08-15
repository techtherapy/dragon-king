#!/usr/bin/env python3
"""Trace the mudra reference drawing into assets/mudra.svg.

The reference (extra-content/mudra-reference.png, supplied by the site's
owner) is clean black line art on white. Rather than redraw the hands by
hand — which never survived contact with reality — this script traces the
ink exactly:

  1. rasterise to BMP with sips (macOS; no imaging libraries needed),
  2. threshold to an ink mask,
  3. walk the boundary of every ink region along the pixel edges,
     giving closed loops with holes,
  4. simplify each loop with Ramer–Douglas–Peucker,
  5. emit one gold path, fill-rule evenodd, so the pen strokes of the
     original become filled gold outlines on the site's indigo ground.

Run from the repo root:  python3 scripts/trace_mudra.py
"""
import struct
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "extra-content" / "mudra-reference.png"
OUT = ROOT / "assets" / "mudra.svg"

GOLD = "#d9b25f"
THRESHOLD = 150      # luminance below this is ink
EPSILON = 1.7        # px; RDP simplification tolerance
MIN_LOOP = 24        # px of perimeter; anything shorter is noise
VIEW = 1000          # output viewBox size


def load_mask():
    """PNG -> 24bpp BMP via sips -> boolean ink mask (row-major, y down)."""
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
    flipped = h > 0          # positive height = bottom-up rows
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
            if r * 299 + g * 587 + b * 114 < THRESHOLD * 1000:
                m[x] = 1
    return mask, w, h


def boundary_loops(mask, w, h):
    """Directed edges around every ink pixel, linked into closed loops.

    Each ink pixel contributes an edge along any side that faces non-ink,
    oriented so outer boundaries and holes wind oppositely — which is what
    lets a single evenodd path carry the nails' cut-outs for free."""
    def ink(x, y):
        return 0 <= x < w and 0 <= y < h and mask[y][x]

    edges = {}   # start vertex -> list of end vertices
    for y in range(h):
        row = mask[y]
        for x in range(w):
            if not row[x]:
                continue
            if not ink(x, y - 1):
                edges.setdefault((x, y), []).append((x + 1, y))
            if not ink(x + 1, y):
                edges.setdefault((x + 1, y), []).append((x + 1, y + 1))
            if not ink(x, y + 1):
                edges.setdefault((x + 1, y + 1), []).append((x, y + 1))
            if not ink(x - 1, y):
                edges.setdefault((x, y + 1), []).append((x, y))

    loops = []
    while edges:
        start = next(iter(edges))
        loop = [start]
        cur = start
        prev_dir = None
        while True:
            outs = edges[cur]
            if len(outs) == 1:
                nxt = outs.pop()
            else:
                # checkerboard junction: prefer the sharpest left turn so
                # the loop hugs its own region instead of crossing over
                def turn(v):
                    d = (v[0] - cur[0], v[1] - cur[1])
                    cross = prev_dir[0] * d[1] - prev_dir[1] * d[0]
                    return cross
                outs.sort(key=turn)
                nxt = outs.pop(0)
            if not edges[cur]:
                del edges[cur]
            prev_dir = (nxt[0] - cur[0], nxt[1] - cur[1])
            cur = nxt
            if cur == start:
                break
            loop.append(cur)
        if len(loop) >= MIN_LOOP:
            loops.append(loop)
    return loops


def rdp(points, eps):
    """Ramer–Douglas–Peucker on a closed loop (iterative, stack-based)."""
    n = len(points)
    if n < 5:
        return points
    keep = [False] * n
    keep[0] = keep[n // 2] = True     # two anchors on a closed loop
    stack = [(0, n // 2), (n // 2, n - 1)]
    keep[n - 1] = True
    while stack:
        a, b = stack.pop()
        if b - a < 2:
            continue
        ax, ay = points[a]
        bx, by = points[b]
        dx, dy = bx - ax, by - ay
        norm = (dx * dx + dy * dy) ** 0.5 or 1.0
        worst, wi = 0.0, -1
        for i in range(a + 1, b):
            px, py = points[i]
            d = abs(dx * (ay - py) - dy * (ax - px)) / norm
            if d > worst:
                worst, wi = d, i
        if worst > eps:
            keep[wi] = True
            stack.append((a, wi))
            stack.append((wi, b))
    return [p for p, k in zip(points, keep) if k]


def build():
    mask, w, h = load_mask()
    ink_px = sum(sum(r) for r in mask)
    loops = boundary_loops(mask, w, h)
    s = VIEW / max(w, h)

    parts = []
    pts_total = 0
    for loop in loops:
        simp = rdp(loop, EPSILON)
        if len(simp) < 3:
            continue
        pts_total += len(simp)
        d = "M" + "L".join(f"{x * s:.1f} {y * s:.1f}" for x, y in simp) + "Z"
        parts.append(d)

    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {VIEW} {VIEW}" '
           f'role="img" aria-label="The mudra of the Dragon King Yoga: the index and '
           f'middle fingers of both hands crossed to form the lattice of the character '
           f'井">\n'
           f'<path fill="{GOLD}" fill-rule="evenodd" stroke="{GOLD}" '
           f'stroke-width="2.6" stroke-linejoin="round" d="{" ".join(parts)}"/>\n'
           f'</svg>\n')
    OUT.write_text(svg, encoding="utf-8")
    print(f"  ink {ink_px}px, {len(loops)} loops, {pts_total} points "
          f"-> mudra.svg {len(svg) / 1024:.0f} KB")


if __name__ == "__main__":
    build()
