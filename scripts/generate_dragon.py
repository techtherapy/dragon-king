#!/usr/bin/env python3
"""Generate the hero dragon artwork (assets/dragon-hero.svg) and the
foreground wave band (assets/waves.svg) for the Dragon King Sutra site.

The dragon body is computed: a Catmull-Rom spline spine, resampled by arc
length, extruded into a tapered outline with dorsal spikes, ventral belly
plates and staggered scale rows. Head, legs, whiskers, pearl, flames and
clouds are hand-authored path templates placed along the computed spine.

Aesthetic: fine gold line-art on deep indigo — the 紺紙金泥 manuscript style.
"""
import math
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
ASSETS.mkdir(exist_ok=True)

# ----------------------------------------------------------------------
# geometry helpers
# ----------------------------------------------------------------------

def catmull_rom(points, samples_per_seg=40):
    """Sample a Catmull-Rom spline through the given control points."""
    pts = [points[0]] + list(points) + [points[-1]]
    out = []
    for i in range(1, len(pts) - 2):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[i + 1], pts[i + 2]
        for j in range(samples_per_seg):
            t = j / samples_per_seg
            t2, t3 = t * t, t * t * t
            x = 0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t
                       + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2
                       + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3)
            y = 0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t
                       + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2
                       + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)
            out.append((x, y))
    out.append(points[-1])
    return out


def resample(path, step=5.0):
    """Resample a polyline at uniform arc-length steps."""
    out = [path[0]]
    dist = 0.0
    for i in range(1, len(path)):
        x0, y0 = path[i - 1]
        x1, y1 = path[i]
        seg = math.hypot(x1 - x0, y1 - y0)
        while dist + seg >= step:
            r = (step - dist) / seg
            nx, ny = x0 + (x1 - x0) * r, y0 + (y1 - y0) * r
            out.append((nx, ny))
            x0, y0 = nx, ny
            seg = math.hypot(x1 - x0, y1 - y0)
            dist = 0.0
        dist += seg
    return out


def tangents_normals(pts):
    tans, norms = [], []
    n = len(pts)
    for i in range(n):
        a = pts[max(0, i - 1)]
        b = pts[min(n - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        l = math.hypot(dx, dy) or 1.0
        tx, ty = dx / l, dy / l
        tans.append((tx, ty))
        norms.append((-ty, tx))  # left-hand normal = outer side of the coil
    return tans, norms


def smoothstep(a, b, t):
    t = max(0.0, min(1.0, (t - a) / (b - a)))
    return t * t * (3 - 2 * t)


def fmt(v):
    return f"{v:.1f}".rstrip("0").rstrip(".")


def poly_path(pts, close=False):
    d = f"M{fmt(pts[0][0])} {fmt(pts[0][1])}"
    for p in pts[1:]:
        d += f"L{fmt(p[0])} {fmt(p[1])}"
    return d + ("Z" if close else "")


# ----------------------------------------------------------------------
# the spine — tail first, head last (a broken ring around the pearl)
# ----------------------------------------------------------------------
SPINE = [
    (1005, 168), (900, 148), (760, 158), (630, 210), (530, 300),
    (478, 420), (490, 545), (560, 655), (680, 730), (830, 768),
    (990, 770), (1145, 725), (1268, 635), (1340, 505), (1345, 365),
    (1275, 258), (1155, 205), (1040, 215), (960, 268),
]
PEARL = (836, 452)

raw = catmull_rom(SPINE, 40)
pts = resample(raw, 4.0)
N = len(pts)
tans, norms = tangents_normals(pts)


def width_at(t):
    """Half-width of the body from tail (t=0) to head (t=1)."""
    w_tail, w_mid, w_neck = 2.5, 34.0, 26.0
    if t < 0.42:
        return w_tail + (w_mid - w_tail) * smoothstep(0.0, 0.42, t)
    if t < 0.86:
        return w_mid
    return w_mid + (w_neck - w_mid) * smoothstep(0.86, 1.0, t)


widths = [width_at(i / (N - 1)) for i in range(N)]

outer = [(pts[i][0] + norms[i][0] * widths[i], pts[i][1] + norms[i][1] * widths[i]) for i in range(N)]
inner = [(pts[i][0] - norms[i][0] * widths[i], pts[i][1] - norms[i][1] * widths[i]) for i in range(N)]
body_d = poly_path(outer + inner[::-1], close=True)
# perimeter of the outline loop, for the stroke draw-in animation
_loop = outer + inner[::-1]
BODY_LEN = sum(math.hypot(_loop[i][0] - _loop[i - 1][0], _loop[i][1] - _loop[i - 1][1])
               for i in range(1, len(_loop))) + math.hypot(
                   _loop[0][0] - _loop[-1][0], _loop[0][1] - _loop[-1][1])

# ---- dorsal spikes along the outer edge --------------------------------
spikes = []
arc = 0.0
i = 1
next_at = 30.0
spike_n = 0
while i < N - 8:
    arc += math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1])
    t = i / (N - 1)
    if arc >= next_at and 0.05 < t < 0.955:
        w = widths[i]
        nx, ny = norms[i]
        tx, ty = tans[i]
        base_l = (pts[i][0] + nx * (w - 1) - tx * 7, pts[i][1] + ny * (w - 1) - ty * 7)
        base_r = (pts[i][0] + nx * (w - 1) + tx * 7, pts[i][1] + ny * (w - 1) + ty * 7)
        h = (w * 0.62 + 5) * (0.82 + 0.30 * abs(math.sin(spike_n * 0.55)))
        tip = (pts[i][0] + nx * (w + h) - tx * (9 + w * 0.28),
               pts[i][1] + ny * (w + h) - ty * (9 + w * 0.28))
        ctrl = (pts[i][0] + nx * (w + h * 0.45) + tx * 4, pts[i][1] + ny * (w + h * 0.45) + ty * 4)
        spikes.append(
            f"M{fmt(base_l[0])} {fmt(base_l[1])}"
            f"Q{fmt(pts[i][0] + nx * (w + h * 0.55) - tx * 12)} {fmt(pts[i][1] + ny * (w + h * 0.55) - ty * 12)} "
            f"{fmt(tip[0])} {fmt(tip[1])}"
            f"Q{fmt(ctrl[0])} {fmt(ctrl[1])} {fmt(base_r[0])} {fmt(base_r[1])}Z")
        next_at = arc + (22 if t > 0.3 else 30)
        spike_n += 1
    i += 1

# ---- ventral belly plates (rungs along the inner edge) ------------------
plates = []
arc = 0.0
next_at = 16.0
for i in range(1, N):
    arc += math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1])
    t = i / (N - 1)
    if arc >= next_at and 0.10 < t < 0.985:
        w = widths[i]
        nx, ny = norms[i]
        tx, ty = tans[i]
        a = (pts[i][0] - nx * (w * 0.96), pts[i][1] - ny * (w * 0.96))
        b = (pts[i][0] - nx * (w * 0.30), pts[i][1] - ny * (w * 0.30))
        # slight backward sweep for an overlapping-plate look
        c = ((a[0] + b[0]) / 2 - tx * w * 0.22, (a[1] + b[1]) / 2 - ty * w * 0.22)
        plates.append(f"M{fmt(a[0])} {fmt(a[1])}Q{fmt(c[0])} {fmt(c[1])} {fmt(b[0])} {fmt(b[1])}")
        next_at = arc + 15
# the belly band line separating plates from scales
belly_line = poly_path([(pts[i][0] - norms[i][0] * widths[i] * 0.30,
                         pts[i][1] - norms[i][1] * widths[i] * 0.30)
                        for i in range(int(N * 0.10), int(N * 0.985))])

# ---- scales: staggered crescent rows on the dorsal half -----------------
scales = []
for row, off in ((0, 0.12), (1, 0.48)):
    arc = 0.0
    next_at = 12.0 + row * 9
    for i in range(1, N):
        arc += math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1])
        t = i / (N - 1)
        if arc >= next_at and 0.14 < t < 0.97:
            w = widths[i]
            nx, ny = norms[i]
            tx, ty = tans[i]
            cx = pts[i][0] + nx * (w * off)
            cy = pts[i][1] + ny * (w * off)
            r = max(2.5, w * 0.20)
            # crescent opening toward the tail
            a = (cx + tx * r * 0.2 + nx * r, cy + ty * r * 0.2 + ny * r)
            b = (cx + tx * r * 0.2 - nx * r, cy + ty * r * 0.2 - ny * r)
            c = (cx - tx * r * 1.15, cy - ty * r * 1.15)
            scales.append(f"M{fmt(a[0])} {fmt(a[1])}Q{fmt(c[0])} {fmt(c[1])} {fmt(b[0])} {fmt(b[1])}")
            next_at = arc + 18
# ---- tail flame fronds ---------------------------------------------------
tx0, ty0 = pts[0]
td = tans[0]
tail_fronds = []
for ang, ln in ((-42, 84), (-4, 112), (36, 76)):
    a = math.radians(ang)
    dx = -(td[0] * math.cos(a) - td[1] * math.sin(a))
    dy = -(td[0] * math.sin(a) + td[1] * math.cos(a))
    tip = (tx0 + dx * ln, ty0 + dy * ln)
    side = (-dy, dx)
    c1 = (tx0 + dx * ln * 0.45 + side[0] * 16, ty0 + dy * ln * 0.45 + side[1] * 16)
    c2 = (tx0 + dx * ln * 0.5 - side[0] * 13, ty0 + dy * ln * 0.5 - side[1] * 13)
    tail_fronds.append(
        f"M{fmt(tx0)} {fmt(ty0)}Q{fmt(c1[0])} {fmt(c1[1])} {fmt(tip[0])} {fmt(tip[1])}"
        f"Q{fmt(c2[0])} {fmt(c2[1])} {fmt(tx0)} {fmt(ty0)}Z")

# ---- head placement ------------------------------------------------------
hx, hy = pts[-1]
hd = tans[-1]
head_angle = math.degrees(math.atan2(hd[1], hd[0])) - 180  # local head faces -x

# ---- leg placement -------------------------------------------------------
def leg_transform(t_pos, flip=False):
    i = int(t_pos * (N - 1))
    px = pts[i][0] - norms[i][0] * widths[i] * 0.55
    py = pts[i][1] - norms[i][1] * widths[i] * 0.55
    ang = math.degrees(math.atan2(norms[i][1], norms[i][0])) + 90
    s = "scale(-1,1) " if flip else ""
    return f"translate({fmt(px)} {fmt(py)}) rotate({fmt(ang + 180)}) {s}"

LEG = (
    "M14 -30 C-6 -16 -20 2 -22 20 C-23 32 -18 40 -8 44 "
    "C-22 50 -30 62 -32 78 C-33 88 -28 96 -20 100 L-4 94 "
    "C-2 80 2 68 10 60 C20 48 24 30 22 8 C21 -6 19 -20 14 -30 Z")
CLAWS = [
    "M-20 98 C-40 94 -58 98 -70 112 C-68 115 -64 117 -60 116 C-48 106 -34 102 -18 104 Z",
    "M-16 102 C-28 112 -34 126 -32 142 C-29 144 -26 144 -24 142 C-20 128 -14 116 -8 108 Z",
    "M-6 104 C-2 118 8 128 22 132 C25 130 26 127 24 124 C14 118 6 112 2 102 Z",
    "M0 92 C12 96 24 94 32 86 C32 83 30 81 27 81 C18 85 10 86 4 84 Z",
]
ELBOW_FLAME = (
    "M-14 42 C-38 34 -58 38 -72 54 C-54 50 -40 52 -30 60 "
    "M-18 50 C-38 52 -52 62 -58 78 C-46 70 -34 66 -24 66")

legs_svg = ""
for t_pos in (0.53, 0.78):
    tf = leg_transform(t_pos)
    claw_d = "".join(f'<path d="{c}" class="claw"/>' for c in CLAWS)
    legs_svg += (f'<g class="leg" transform="{tf} scale(1.12)">'
                 f'<path d="{ELBOW_FLAME}" class="wisp"/>'
                 f'<path d="{LEG}" class="limb"/>{claw_d}</g>')

# ---- hand-authored head (local coords, facing -x, neck joint at ~(46,0)) --
HEAD = f"""
<g class="head" transform="translate({fmt(hx)} {fmt(hy)}) rotate({fmt(head_angle)}) scale(1.32)"><g class="head-inner">
  <!-- mane locks sweeping back over the neck -->
  <path class="mane" d="M30 -28 C64 -60 100 -72 138 -66 C106 -50 88 -36 80 -18 C76 -22 50 -26 30 -28 Z"/>
  <path class="mane" d="M36 -18 C78 -34 116 -32 146 -14 C112 -12 90 -4 78 10 C72 0 52 -12 36 -18 Z"/>
  <path class="mane" d="M40 -2 C82 -4 116 8 136 32 C104 26 82 28 68 38 C62 24 52 8 40 -2 Z"/>
  <path class="mane" d="M38 12 C72 22 94 40 102 66 C78 52 60 48 44 50 C42 36 40 24 38 12 Z"/>
  <path class="mane mane2" d="M34 -34 C56 -66 86 -84 124 -88 C98 -66 84 -50 78 -34 C62 -36 46 -36 34 -34 Z"/>
  <!-- far horn -->
  <path class="horn horn2" d="M26 -26 C44 -44 68 -54 96 -56 C100 -56 102 -60 99 -63 C97 -66 93 -66 89 -65 C60 -60 38 -46 20 -30 Z"/>
  <!-- skull: crown, brow, snout with curled nose, open upper jaw -->
  <path class="skull" d="M50 -32 C30 -40 12 -40 -2 -34 C-8 -31 -14 -30 -20 -30 C-36 -28 -52 -24 -66 -18 C-76 -14 -84 -16 -88 -22 C-92 -14 -88 -6 -80 -3 C-86 0 -90 4 -88 10 C-80 14 -70 12 -62 6 C-48 10 -34 10 -22 6 L-14 4 C-2 12 12 16 26 14 C40 12 48 2 50 -12 C51 -19 51 -26 50 -32 Z"/>
  <!-- nose curl spiral -->
  <path class="line" d="M-80 -4 C-88 -6 -92 -14 -88 -20 C-84 -24 -78 -22 -78 -17 C-78 -13 -82 -12 -84 -15"/>
  <!-- upper fangs -->
  <path class="tooth" d="M-70 3 L-64 20 L-56 5 Z"/>
  <path class="tooth" d="M-46 6 L-42 17 L-35 7 Z"/>
  <!-- lower jaw, open -->
  <path class="skull" d="M-10 12 C-28 18 -46 22 -62 30 C-72 35 -78 33 -82 27 C-84 35 -78 42 -68 42 C-52 42 -32 38 -14 30 C-2 34 12 34 22 28 C10 26 0 20 -10 12 Z"/>
  <path class="tooth" d="M-58 28 L-50 14 L-44 26 Z"/>
  <!-- tongue curl inside the mouth -->
  <path class="tongue" d="M-14 16 C-30 18 -44 24 -52 30 C-40 30 -28 27 -18 22 Z"/>
  <!-- eye -->
  <path class="eye-white" d="M-4 -22 C4 -30 16 -30 24 -22 C16 -14 4 -14 -4 -22 Z"/>
  <circle class="eye-iris" cx="10" cy="-22" r="4.6"/>
  <ellipse class="eye-pupil" cx="10" cy="-22" rx="1.7" ry="4"/>
  <circle class="eye-glint" cx="12" cy="-24.5" r="1.3"/>
  <path class="line" d="M-8 -30 C2 -38 20 -38 30 -30"/>
  <!-- ear -->
  <path class="mane mane2" d="M22 -30 C32 -42 44 -46 54 -42 C44 -36 36 -30 32 -22 Z"/>
  <!-- near horn: antler sweeping back with tine -->
  <path class="horn" d="M12 -32 C30 -52 56 -64 88 -68 C93 -68 95 -72 92 -76 C89 -79 85 -79 81 -78 C50 -72 26 -58 6 -38 Z"/>
  <path class="horn" d="M50 -60 C56 -74 68 -84 84 -90 C88 -91 91 -88 89 -84 C86 -80 82 -78 78 -74 C70 -68 64 -62 60 -54 Z"/>
  <!-- whiskers -->
  <path class="whisker" d="M-76 -8 C-104 -14 -130 -6 -146 16 C-154 28 -150 40 -140 40 C-146 30 -144 22 -132 16 C-116 4 -96 -2 -76 -4"/>
  <path class="whisker w2" d="M-72 8 C-94 14 -110 28 -118 50 C-122 62 -114 70 -106 66 C-114 58 -113 50 -104 44 C-94 30 -82 18 -68 12"/>
  <!-- chin beard locks -->
  <path class="mane" d="M-30 34 C-36 48 -32 62 -20 70 C-22 58 -19 48 -10 42 C-18 40 -25 38 -30 34 Z"/>
  <path class="mane mane2" d="M-46 36 C-54 46 -56 58 -50 68 C-48 58 -43 50 -36 46 Z"/>
</g></g>
"""

# ---- flaming pearl -------------------------------------------------------
px, py = PEARL
PEARL_SVG = f"""
<g class="pearl-group" transform="translate({fmt(px)} {fmt(py)})">
  <circle class="pearl-halo2" r="130"/>
  <circle class="pearl-halo" r="88"/>
  <circle class="halo-ring" r="60"/>
  <circle class="halo-ring r2" r="70"/>
  <g class="pearl-flames">
    <path class="flame" d="M0 -44 C-20 -60 -24 -82 -12 -104 C-10 -90 -2 -82 6 -78 C0 -94 4 -110 18 -122 C14 -104 20 -92 30 -84 C38 -76 40 -62 32 -50 C22 -38 8 -36 0 -44 Z"/>
    <path class="flame f2" d="M-40 -28 C-58 -34 -68 -48 -68 -66 C-58 -54 -48 -50 -38 -52 C-44 -42 -44 -34 -40 -28 Z"/>
    <path class="flame f2" d="M44 -18 C62 -20 76 -12 82 4 C70 -4 60 -4 52 0 C50 -8 48 -14 44 -18 Z"/>
  </g>
  <circle class="pearl-body" r="46"/>
  <path class="pearl-swirl" d="M-8 -26 C14 -26 28 -12 26 6 C24 20 12 28 0 26 C12 22 18 12 16 2 C14 -10 2 -18 -8 -16 C-16 -15 -22 -8 -22 0 C-22 -14 -14 -26 -8 -26 Z"/>
  <circle class="pearl-core" r="14"/>
</g>
"""


# lotus petals for the Buddha's throne — curled scallops, outer first
_petal = ('<path class="b-petal" d="M-10 -15 C-6 -19 6 -19 10 -15 C13 -9 11 -1 4 3 '
          'C2 4 -2 4 -4 3 C-11 -1 -13 -9 -10 -15 Z"/>'
          '<path class="b-line" d="M-5 -14 C-2 -16 3 -16 5 -13 M0 -12 C-1 -7 -1 -2 0 1"/>')
b_petals = "".join(f'<g transform="translate({x} 36)">{_petal}</g>'
                   for x in (-63, 63, -42, 42, -21, 21, 0))

# ---- the Buddha: aniconic gold silhouette on a lotus, within a halo ------
# Placed on the pearl's vertical axis; light descends behind the dragon
# and becomes the pearl — the Dharma received.
BUDDHA_SVG = f"""
<g class="buddha" transform="translate({fmt(PEARL[0])} -40) scale(1.12)">
  <!-- descending light, drawn first (sits behind the figure's lotus) -->
  <path class="b-beam" d="M-24 60 L-74 400 L74 400 L24 60 Z"/>
  <path class="b-ray" d="M0 64 L0 396 M-44 70 L-62 380 M44 70 L62 380"/>
  <!-- halo glow -->
  <g transform="translate(0 -92)"><circle class="b-halo" r="128"/></g>
  <g class="b-in">
    <!-- mandorla (egg aureole) + head nimbus -->
    <path class="b-aura" d="M0 -196 C42 -192 76 -158 80 -104 C84 -50 52 0 0 4 C-52 0 -84 -50 -80 -104 C-76 -158 -42 -192 0 -196 Z"/>
    <circle class="b-aura" cx="0" cy="-130" r="35"/>
    <!-- torso: compact seated proportions -->
    <path class="b-solid" d="M-8 -110
      C-20 -108 -29 -103 -33 -96
      C-38 -86 -40 -75 -39 -64
      C-38 -52 -35 -44 -30 -39
      C-43 -34 -51 -27 -53 -19
      C-54 -11 -48 -6 -36 -3
      C-14 1 14 1 36 -3
      C48 -6 54 -11 53 -19
      C51 -27 43 -34 30 -39
      C35 -44 38 -52 39 -64
      C40 -75 38 -86 33 -96
      C29 -103 20 -108 8 -110
      C3 -111 -3 -111 -8 -110 Z"/>
    <!-- neck: barely visible — a sliver between chin and collar -->
    <path class="b-neck" d="M-9 -114 L-9 -104 L9 -104 L9 -114 Z"/>
    <path class="b-line" d="M-8.5 -111 L-8 -107 M8.5 -111 L8 -107"/>
    <!-- robe edges across the chest -->
    <path class="b-line" d="M-15 -104 C-6 -96 6 -96 15 -104"/>
    <path class="b-line" d="M-13 -99 C-5 -92 5 -92 13 -99"/>
    <!-- arms: shoulder to elbow, forearm crossing to the lap -->
    <path class="b-solid" d="M16 -107
      C27 -104 33 -98 36 -89
      C39 -79 40 -70 39 -61
      C38 -53 36 -46 32 -41
      C26 -36 16 -33 7 -32
      L10 -40
      C16 -44 21 -49 24 -55
      C27 -67 26 -82 22 -94
      C20 -100 18 -104 16 -107 Z"/>
    <path class="b-solid" d="M-16 -107
      C-27 -104 -33 -98 -36 -89
      C-39 -79 -40 -70 -39 -61
      C-38 -53 -36 -46 -32 -41
      C-26 -36 -16 -33 -7 -32
      L-10 -40
      C-16 -44 -21 -49 -24 -55
      C-27 -67 -26 -82 -22 -94
      C-20 -100 -18 -104 -16 -107 Z"/>
    <!-- sleeves hanging from the forearms -->
    <path class="b-solid" d="M33 -46 C38 -37 37 -26 30 -19 C26 -22 27 -33 30 -43 Z"/>
    <path class="b-solid" d="M-33 -46 C-38 -37 -37 -26 -30 -19 C-26 -22 -27 -33 -30 -43 Z"/>
    <!-- dhyana mudra: hands together, palms up, thumbs touching -->
    <path class="b-solid" d="M-13 -33 C-11 -38 11 -38 13 -33 C10 -28.5 -10 -28.5 -13 -33 Z"/>
    <path class="b-line" d="M-4 -37.5 C-2 -39.5 2 -39.5 4 -37.5"/>
    <path class="b-line" d="M-7 -36.5 L-7 -31 M0 -37 L0 -30.5 M7 -36.5 L7 -31"/>
    <!-- fanning folds over the crossed legs -->
    <path class="b-line" d="M-32 -18 C-24 -9 -12 -5 0 -5 C12 -5 24 -9 32 -18"/>
    <path class="b-line" d="M-16 -24 C-10 -14 10 -14 16 -24 M0 -26 C-2 -18 2 -12 0 -6"/>
    <path class="b-line" d="M-46 -22 C-40 -14 -34 -9 -26 -6 M46 -22 C40 -14 34 -9 26 -6"/>
    <!-- robe spilling over the seat front (wavy apron) -->
    <path class="b-solid" d="M-50 -2
      C-54 6 -56 14 -55 20
      C-52 27 -45 30 -38 28
      C-36 31 -28 33 -22 31
      C-18 34 -8 35 -2 33
      C4 35 14 34 18 31
      C24 33 32 31 36 28
      C45 30 52 27 55 20
      C56 14 54 6 50 -2
      C20 4 -20 4 -50 -2 Z"/>
    <path class="b-line" d="M-31 0 C-33 8 -33 17 -31 25 M-11 2 C-12 10 -12 19 -11 27 M11 2 C12 10 12 19 11 27 M31 0 C33 8 33 17 31 25"/>
    <!-- head: seated low, chin just above the collar -->
    <g transform="translate(0 5.5)">
    <path class="b-solid" d="M-18 -136 C-18 -148 -9.5 -155 0 -155 C9.5 -155 18 -148 18 -136 C18 -125 10.5 -117 0 -117 C-10.5 -117 -18 -125 -18 -136 Z"/>
    <path class="b-line" d="M-16 -142 C-7 -146 7 -146 16 -142"/>
    <path class="b-solid" d="M-7 -153 C-7 -160 -4 -163 0 -170 C4 -163 7 -160 7 -153 C4 -155 -4 -155 -7 -153 Z"/>
    <!-- ears -->
    <path class="b-solid" d="M18 -138 C22 -139 23 -134 22 -128 C21 -121 19 -117 17 -117 C15.5 -119 16.5 -128 18 -138 Z"/>
    <path class="b-solid" d="M-18 -138 C-22 -139 -23 -134 -22 -128 C-21 -121 -19 -117 -17 -117 C-15.5 -119 -16.5 -128 -18 -138 Z"/>
    <!-- face -->
    <path class="b-line" d="M-8.5 -138 C-5.5 -140 -2.5 -140 -1 -138.5 L-1 -132 M8.5 -138 C5.5 -140 2.5 -140 1 -138.5 M-1.5 -131 C-0.5 -130.5 0.5 -130.5 1.5 -131"/>
    <path class="b-line" d="M-9 -135 C-7 -133.5 -4.5 -133.5 -3 -135 M9 -135 C7 -133.5 4.5 -133.5 3 -135"/>
    <circle class="b-dot" cx="0" cy="-141.5" r="1.1"/>
    <path class="b-line" d="M-3 -125.5 C-1.5 -124 1.5 -124 3 -125.5"/>
    </g>
    <!-- lotus throne: curled petal row on a base rim -->
    {b_petals}
    <path class="b-line" d="M-72 46 C-38 54 38 54 72 46"/>
    <path class="b-line" d="M-64 51 C-34 57 34 57 64 51" opacity=".5"/>
  </g>
</g>
"""

# ---- auspicious cloud (hand-authored, reused) ----------------------------
CLOUD_DEF = """
<g id="cloud">
  <path class="cline" d="M0 0 C-4 -18 8 -32 26 -32 C44 -32 54 -18 50 -2 C62 -10 78 -6 82 6 C86 16 78 26 66 26 L-38 26 C-52 26 -58 14 -52 4 C-47 -4 -36 -6 -28 0 C-24 -8 -12 -10 0 0 Z"/>
  <path class="cline" d="M14 -6 C10 -16 18 -24 27 -22 C34 -21 38 -14 35 -8"/>
  <path class="cline" d="M-64 26 L-96 26 M92 26 L118 26 M-70 36 L20 36 M40 36 L86 36"/>
</g>
"""

# ---- gold dust -----------------------------------------------------------
random.seed(7)
dust = ""
for _ in range(30):
    dx = random.uniform(370, 1550)
    dy = random.uniform(-260, 940)
    r = random.choice((1.1, 1.5, 2.0, 2.6))
    cls = random.choice(("d1", "d2", "d3"))
    dust += f'<circle class="dust {cls}" cx="{fmt(dx)}" cy="{fmt(dy)}" r="{r}" style="animation-delay:{random.uniform(0, 6):.1f}s"/>'

# ----------------------------------------------------------------------
# assemble dragon-hero.svg
# ----------------------------------------------------------------------
spikes_d = "".join(spikes)
plates_d = "".join(plates)
scales_d = "".join(scales)
fronds_d = "".join(tail_fronds)

dragon_svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="330 -290 1260 1280" role="img"
     aria-label="Beneath a serene line-drawn Buddha seated on a lotus within a moon disc, a golden dragon coils around a flaming pearl — drawn in the style of a classical sutra frontispiece">
<style>
  :root {{ --g:#d9b25f; --gb:#f4dc96; --gd:#8d7440; --body:#101f39; --body2:#16294a; }}
  .body-fill {{ fill:url(#bodyGrad); stroke:var(--g); stroke-width:2.6; stroke-linejoin:round; }}
  .spike {{ fill:url(#spikeGrad); stroke:var(--g); stroke-width:1.1; stroke-linejoin:round; }}
  .plate {{ fill:none; stroke:var(--g); stroke-width:1.5; opacity:.75; }}
  .belly-line {{ fill:none; stroke:var(--g); stroke-width:1.6; opacity:.85; }}
  .scale {{ fill:none; stroke:var(--g); stroke-width:1.1; opacity:.5; }}
  .frond {{ fill:url(#spikeGrad); stroke:var(--g); stroke-width:1.2; }}
  .limb {{ fill:url(#bodyGrad); stroke:var(--g); stroke-width:2.2; stroke-linejoin:round; }}
  .claw {{ fill:var(--gb); stroke:var(--g); stroke-width:1; }}
  .wisp {{ fill:none; stroke:var(--gb); stroke-width:1.6; opacity:.9; }}
  .mane {{ fill:url(#maneGrad); stroke:var(--g); stroke-width:1.4; }}
  .mane2 {{ opacity:.75; }}
  .horn {{ fill:#0c1830; stroke:var(--gb); stroke-width:1.8; stroke-linejoin:round; }}
  .horn2 {{ opacity:.6; }}
  .tongue {{ fill:#8d5a3a; opacity:.9; }}
  .eye-pupil {{ fill:#2a1c08; }}
  .halo-ring {{ fill:none; stroke:var(--g); stroke-width:1; opacity:.4; }}
  .halo-ring.r2 {{ opacity:.22; }}
  .skull {{ fill:url(#headGrad); stroke:var(--gb); stroke-width:2.4; stroke-linejoin:round; }}
  .line {{ fill:none; stroke:var(--gb); stroke-width:1.7; stroke-linecap:round; }}
  .tooth {{ fill:var(--gb); }}
  .eye-white {{ fill:#f7ecd2; stroke:var(--g); stroke-width:1; }}
  .eye-iris {{ fill:#f4dc96; }}
  .eye-glint {{ fill:#fff; }}
  .whisker {{ fill:none; stroke:var(--gb); stroke-width:1.8; stroke-linecap:round; }}
  .pearl-halo {{ fill:url(#haloGrad); animation:pulse 5s ease-in-out infinite alternate; }}
  .pearl-halo2 {{ fill:url(#haloGrad); opacity:.4; animation:pulse 7s ease-in-out infinite alternate-reverse; }}
  .pearl-body {{ fill:url(#pearlGrad); stroke:var(--gb); stroke-width:1.6; }}
  .pearl-core {{ fill:#fff8e6; opacity:.9; filter:url(#soft); }}
  .pearl-swirl {{ fill:rgba(141,116,64,.55); }}
  .flame {{ fill:url(#flameGrad); stroke:var(--gb); stroke-width:1; opacity:.9; }}
  .pearl-flames {{ transform-origin:0 0; animation:flick 9s ease-in-out infinite alternate; }}
  .b-line {{ fill:none; stroke:var(--gb); stroke-width:1.5; stroke-linecap:round; stroke-linejoin:round; }}
  .b-solid {{ fill:#0e1c34; stroke:var(--gb); stroke-width:1.5; stroke-linejoin:round; }}
  .b-dot {{ fill:var(--gb); }}
  .b-neck {{ fill:#0e1c34; }}
  .b-petal {{ fill:url(#maneGrad); stroke:var(--gb); stroke-width:1.3; stroke-linejoin:round; }}
  .b-aura {{ fill:url(#discGrad); stroke:var(--g); stroke-width:1.7; opacity:.95; }}
  .b-halo {{ fill:url(#haloGrad); animation:pulse 8s ease-in-out infinite alternate; }}
  .b-beam {{ fill:url(#beamGrad); animation:breathe 7s ease-in-out infinite alternate; }}
  .b-ray {{ fill:none; stroke:url(#beamGrad); stroke-width:1.4; animation:breathe 7s ease-in-out -3s infinite alternate; }}
  .b-in {{ opacity:0; animation:fadeIn 1.8s ease .15s forwards; }}
  @keyframes breathe {{ from {{ opacity:.65; }} to {{ opacity:1; }} }}
  .cline {{ fill:none; stroke:var(--g); stroke-width:2; stroke-linecap:round; }}
  .cloud {{ opacity:.38; }}
  .cloud-a {{ animation:drift 26s ease-in-out infinite alternate; }}
  .cloud-b {{ animation:drift 34s ease-in-out infinite alternate-reverse; }}
  .dust {{ fill:var(--gb); }}
  .d1 {{ animation:twinkle 4s ease-in-out infinite alternate; }}
  .d2 {{ animation:twinkle 6s ease-in-out infinite alternate-reverse; }}
  .d3 {{ animation:twinkle 5s ease-in-out infinite alternate; opacity:.5; }}
  /* ---- entrance: the dragon draws itself in gold ink ---- */
  .body-fill {{
    stroke-dasharray:{BODY_LEN:.0f}; stroke-dashoffset:{BODY_LEN:.0f}; fill-opacity:0;
    animation:drawBody 3s cubic-bezier(.45,0,.25,1) .3s forwards, fillBody 1.4s ease 2.1s forwards;
  }}
  .spikes, .frond {{ opacity:0; animation:fadeIn 1.1s ease 2s forwards; }}
  .detail {{ opacity:0; animation:fadeIn 1.2s ease 2.4s forwards; }}
  .leg {{ opacity:0; animation:fadeIn 1s ease 2.2s forwards; }}
  .head {{ opacity:0; animation:fadeIn 1s ease 1.5s forwards; }}
  /* ---- ambient: swimming ---- */
  .dragon {{ transform-origin:912px 468px; animation:swim 16s ease-in-out infinite alternate; }}
  .head-inner {{ transform-box:fill-box; transform-origin:82% 34%; animation:nod 9s ease-in-out infinite alternate; }}
  .whisker {{ transform-box:fill-box; transform-origin:96% 12%; animation:whisk 6.5s ease-in-out infinite alternate; }}
  .whisker.w2 {{ animation-duration:8s; animation-delay:-2.5s; }}
  @keyframes drawBody {{ to {{ stroke-dashoffset:0; }} }}
  @keyframes fillBody {{ to {{ fill-opacity:1; }} }}
  @keyframes fadeIn {{ to {{ opacity:1; }} }}
  @keyframes swim {{
    from {{ transform:translate(0,-7px) rotate(-1.5deg); }}
    to {{ transform:translate(0,8px) rotate(1.7deg); }}
  }}
  @keyframes nod {{ from {{ transform:rotate(-1.3deg); }} to {{ transform:rotate(1.9deg); }} }}
  @keyframes whisk {{ from {{ transform:rotate(-2.4deg); }} to {{ transform:rotate(2.8deg); }} }}
  @keyframes pulse {{ from {{ opacity:.55; transform:scale(.94); }} to {{ opacity:1; transform:scale(1.05); }} }}
  @keyframes flick {{ from {{ transform:rotate(-3deg) scale(.98); }} to {{ transform:rotate(3deg) scale(1.03); }} }}
  @keyframes drift {{ from {{ transform:translateX(-22px); }} to {{ transform:translateX(22px); }} }}
  @keyframes twinkle {{ from {{ opacity:.12; }} to {{ opacity:.95; }} }}
  @media (prefers-reduced-motion: reduce) {{
    .pearl-halo,.pearl-halo2,.pearl-flames,.cloud-a,.cloud-b,.dust,.dragon,
    .head-inner,.whisker,.spikes,.frond,.detail,.leg,.head,.body-fill,
    .b-halo,.b-beam,.b-ray,.b-in {{ animation:none; }}
    .b-in {{ opacity:1; }}
    .body-fill {{ stroke-dasharray:none; fill-opacity:1; }}
    .spikes,.frond,.detail,.leg,.head {{ opacity:1; }}
  }}
</style>
<defs>
  <radialGradient id="haloGrad">
    <stop offset="0%" stop-color="#f4dc96" stop-opacity=".5"/>
    <stop offset="45%" stop-color="#d9b25f" stop-opacity=".16"/>
    <stop offset="100%" stop-color="#d9b25f" stop-opacity="0"/>
  </radialGradient>
  <radialGradient id="pearlGrad" cx="38%" cy="32%">
    <stop offset="0%" stop-color="#fffdf4"/>
    <stop offset="45%" stop-color="#f4dc96"/>
    <stop offset="100%" stop-color="#b3893f"/>
  </radialGradient>
  <radialGradient id="flameGrad" cx="30%" cy="70%">
    <stop offset="0%" stop-color="#f4dc96" stop-opacity=".85"/>
    <stop offset="100%" stop-color="#b3893f" stop-opacity=".25"/>
  </radialGradient>
  <linearGradient id="bodyGrad" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0%" stop-color="#1a2f56"/>
    <stop offset="55%" stop-color="#101f39"/>
    <stop offset="100%" stop-color="#0c1830"/>
  </linearGradient>
  <linearGradient id="spikeGrad" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0%" stop-color="#f4dc96" stop-opacity=".8"/>
    <stop offset="100%" stop-color="#8d7440" stop-opacity=".35"/>
  </linearGradient>
  <linearGradient id="headGrad" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0%" stop-color="#2a4470"/>
    <stop offset="100%" stop-color="#16294a"/>
  </linearGradient>
  <linearGradient id="maneGrad" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0%" stop-color="#d9b25f" stop-opacity=".85"/>
    <stop offset="100%" stop-color="#8d7440" stop-opacity=".3"/>
  </linearGradient>
  <radialGradient id="sheenGrad" cx="60%" cy="28%" r="75%">
    <stop offset="0%" stop-color="#f4dc96" stop-opacity=".22"/>
    <stop offset="60%" stop-color="#f4dc96" stop-opacity="0"/>
  </radialGradient>
  <linearGradient id="buddhaGrad" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0%" stop-color="#f4dc96"/>
    <stop offset="70%" stop-color="#d9b25f"/>
    <stop offset="100%" stop-color="#b3893f"/>
  </linearGradient>
  <radialGradient id="discGrad">
    <stop offset="0%" stop-color="#f4dc96" stop-opacity=".10"/>
    <stop offset="75%" stop-color="#d9b25f" stop-opacity=".04"/>
    <stop offset="100%" stop-color="#d9b25f" stop-opacity="0"/>
  </radialGradient>
  <linearGradient id="beamGrad" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0%" stop-color="#f4dc96" stop-opacity=".30"/>
    <stop offset="70%" stop-color="#f4dc96" stop-opacity=".08"/>
    <stop offset="100%" stop-color="#f4dc96" stop-opacity="0"/>
  </linearGradient>
  <filter id="soft" x="-80%" y="-80%" width="260%" height="260%">
    <feGaussianBlur stdDeviation="6"/>
  </filter>
  <filter id="dglow" x="-15%" y="-15%" width="130%" height="130%">
    <feDropShadow dx="0" dy="0" stdDeviation="10" flood-color="#d9b25f" flood-opacity=".28"/>
  </filter>
  <clipPath id="bodyClip"><path d="{body_d}"/></clipPath>
  {CLOUD_DEF}
</defs>

<!-- gold dust field -->
<g>{dust}</g>

<!-- drifting auspicious clouds -->
<g transform="translate(470 160) scale(1.45)"><use href="#cloud" class="cloud cloud-a"/></g>
<g transform="translate(600 -140) scale(0.85)"><use href="#cloud" class="cloud cloud-b"/></g>
<g transform="translate(1105 -175) scale(1.0)"><use href="#cloud" class="cloud cloud-a"/></g>
<g transform="translate(1230 895) scale(1.8)"><use href="#cloud" class="cloud cloud-b"/></g>
<g transform="translate(1445 330) scale(1.0)"><use href="#cloud" class="cloud cloud-a"/></g>
<g transform="translate(470 820) scale(1.15)"><use href="#cloud" class="cloud cloud-b"/></g>

{BUDDHA_SVG}

<g class="dragon" filter="url(#dglow)">
  <g class="spikes">{'' if not spikes_d else f'<path class="spike" d="{spikes_d}"/>'}</g>
  <path class="frond" d="{fronds_d}"/>
  <path class="body-fill" d="{body_d}"/>
  <g class="detail" clip-path="url(#bodyClip)">
    <path class="scale" d="{scales_d}"/>
    <path class="plate" d="{plates_d}"/>
    <path class="belly-line" d="{belly_line}"/>
    <path fill="url(#sheenGrad)" d="{body_d}"/>
  </g>
  {legs_svg}
  {HEAD}
</g>

{PEARL_SVG}
</svg>
"""

(ASSETS / "dragon-hero.svg").write_text(dragon_svg, encoding="utf-8")

# ----------------------------------------------------------------------
# waves.svg — curling gold wave band
# ----------------------------------------------------------------------

def curl(cx, cy, size, turns=1.75, k=0.34, samples=70):
    """A breaking wave crest: rises from the right, curls over to the left
    and spirals inward — a logarithmic spiral in screen coordinates."""
    pts = []
    theta_max = turns * 2 * math.pi
    for i in range(samples + 1):
        th = theta_max * i / samples
        r = size * math.exp(-k * th)
        a = -0.35 + th
        pts.append((cx + r * math.cos(a), cy - r * math.sin(a)))
    return poly_path(pts)


random.seed(21)
PERIOD = 1600.0


def tiled(x):
    """Emit x plus wrapped twins so the pattern tiles with period 1600."""
    xs = [x]
    if x < 220:
        xs.append(x + PERIOD)
    if x > PERIOD - 220:
        xs.append(x - PERIOD)
    return xs


back_curls, front_curls, swells = [], [], []
# back row: 16 curls on a fixed grid with jitter (grid keeps the loop seamless)
for i in range(16):
    x0 = i * PERIOD / 16 + random.uniform(-14, 14)
    s = random.uniform(40, 62)
    y0 = 116 + random.uniform(-8, 8)
    for x in tiled(x0):
        back_curls.append(curl(x, y0, s))
# front row: 10 larger curls with trailing swells
for i in range(10):
    x0 = i * PERIOD / 10 + random.uniform(-20, 20)
    s = random.uniform(58, 92)
    y0 = 172 + random.uniform(-6, 6)
    for x in tiled(x0):
        front_curls.append(curl(x, y0, s))
        ox, oy = x + s * math.cos(-0.35), y0 - s * math.sin(-0.35)
        swells.append(f"M{fmt(ox)} {fmt(oy)} "
                      f"C{fmt(ox + s * 0.6)} {fmt(oy + s * 0.34)} {fmt(ox + s * 1.2)} {fmt(oy + s * 0.3)} "
                      f"{fmt(ox + s * 1.8)} {fmt(oy - s * 0.2)}")

waves_svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 260" preserveAspectRatio="none" aria-hidden="true">
<style>
  .wb {{ fill:none; stroke:#8d7440; stroke-width:1.6; opacity:.4; }}
  .wf {{ fill:none; stroke:#d9b25f; stroke-width:2; opacity:.75; }}
  .ws {{ fill:none; stroke:#d9b25f; stroke-width:1.3; opacity:.35; }}
  .roll-back {{ animation:roll 110s linear infinite; }}
  .roll-front {{ animation:roll 62s linear infinite; }}
  .bob-back {{ animation:bobY 9s ease-in-out infinite alternate; }}
  .bob-front {{ animation:bobY 7s ease-in-out -3.5s infinite alternate-reverse; }}
  @keyframes roll {{ from {{ transform:translateX(0); }} to {{ transform:translateX(-1600px); }} }}
  @keyframes bobY {{ from {{ transform:translateY(-4px); }} to {{ transform:translateY(4px); }} }}
  @media (prefers-reduced-motion: reduce) {{
    .roll-back,.roll-front,.bob-back,.bob-front {{ animation:none; }}
  }}
</style>
<defs>
  <g id="back-row"><path class="wb" d="{''.join(back_curls)}"/></g>
  <g id="front-row"><path class="ws" d="{''.join(swells)}"/><path class="wf" d="{''.join(front_curls)}"/></g>
</defs>
<g class="bob-back"><g class="roll-back">
  <use href="#back-row"/><use href="#back-row" x="1600"/>
</g></g>
<g class="bob-front"><g class="roll-front">
  <use href="#front-row"/><use href="#front-row" x="1600"/>
</g></g>
"""
waves_svg += "</svg>\n"
(ASSETS / "waves.svg").write_text(waves_svg, encoding="utf-8")

print(f"dragon-hero.svg: {len(dragon_svg) / 1024:.0f} KB, spine samples={N}")
print(f"waves.svg: {len(waves_svg) / 1024:.0f} KB")
