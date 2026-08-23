#!/usr/bin/env python3
"""Generate the illustrations for the Nagas & Dragon Kings article.

Four figures, each anchored to a passage of the article by the page itself:

  naga-mucalinda.svg   Mucalinda coiled beneath the meditating Buddha,
                       hood spread against the storm
  naga-king.svg        a crowned nagaraja rising from the waves,
                       holding the pearl
  naga-palace.svg      the Dragon Palace beneath the sea, with its two
                       kinds of treasure — jewels and scriptures
  naga-garuda.svg      the garuda and the naga, old enemies, turned
                       toward the same jewel of the dharma

House style: fine gold line-art on deep indigo (紺紙金泥), no background
shading. Shares its palette and helpers with generate_practice_art.py.

Run from the repo root:  python3 scripts/generate_naga_art.py
"""
import math
from pathlib import Path

from generate_practice_art import GOLD, BRIGHT, DIM, INK, svg, curl
# the hero dragon's machinery: smooth splines, tapered outlines, and the
# head itself. Importing generate_dragon re-emits its own assets, which is
# deterministic and therefore harmless.
import generate_dragon as gd

# style + gradients the hero head needs, carried locally with na- ids
HEAD_CSS = f"""
  .body-fill {{ fill:url(#naBodyGrad); stroke:{GOLD}; stroke-width:1.6; stroke-linejoin:round; }}
  .spike {{ fill:url(#naSpikeGrad); stroke:{GOLD}; stroke-width:.7; }}
  .plate {{ fill:none; stroke:{GOLD}; stroke-width:.9; opacity:.7; }}
  .mane {{ fill:url(#naManeGrad); stroke:{GOLD}; stroke-width:1; }}
  .mane2 {{ opacity:.75; }}
  .horn {{ fill:#0c1830; stroke:{BRIGHT}; stroke-width:1.3; stroke-linejoin:round; }}
  .horn2 {{ opacity:.6; }}
  .skull {{ fill:url(#naHeadGrad); stroke:{BRIGHT}; stroke-width:1.7; stroke-linejoin:round; }}
  .line {{ fill:none; stroke:{BRIGHT}; stroke-width:1.2; stroke-linecap:round; }}
  .tooth {{ fill:{BRIGHT}; }}
  .tongue {{ fill:#8d5a3a; opacity:.9; }}
  .eye-white {{ fill:#f7ecd2; stroke:{GOLD}; stroke-width:.8; }}
  .eye-iris {{ fill:{BRIGHT}; }}
  .eye-pupil {{ fill:#2a1c08; }}
  .eye-glint {{ fill:#fff; }}
  .whisker {{ fill:none; stroke:{BRIGHT}; stroke-width:1.3; stroke-linecap:round; }}
"""
HEAD_DEFS = f"""<defs>
  <linearGradient id="naBodyGrad" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0%" stop-color="#1a2f56"/><stop offset="55%" stop-color="#101f39"/>
    <stop offset="100%" stop-color="#0c1830"/>
  </linearGradient>
  <linearGradient id="naHeadGrad" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0%" stop-color="#2a4470"/><stop offset="100%" stop-color="#16294a"/>
  </linearGradient>
  <linearGradient id="naManeGrad" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0%" stop-color="{GOLD}" stop-opacity=".85"/>
    <stop offset="100%" stop-color="{DIM}" stop-opacity=".3"/>
  </linearGradient>
  <linearGradient id="naSpikeGrad" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0%" stop-color="{BRIGHT}" stop-opacity=".8"/>
    <stop offset="100%" stop-color="{DIM}" stop-opacity=".35"/>
  </linearGradient>
</defs>"""


def dragon_body(spine, w_head=10.0, w_mid=13.0, samples=40, step=3.0,
                spikes=True, spike_every=15.0):
    """A smooth tapered dragon body along a Catmull-Rom spline through
    `spine` (tail first, head last). Returns (svg_fragment, head_pos,
    head_angle_deg) ready for gd.head_group."""
    pts = gd.resample(gd.catmull_rom(spine, samples), step)
    n = len(pts)
    tans, norms = gd.tangents_normals(pts)

    def w(i):
        t = i / (n - 1)
        if t < 0.35:
            return 1.8 + (w_mid - 1.8) * gd.smoothstep(0.0, 0.35, t)
        if t < 0.85:
            return w_mid
        return w_mid + (w_head - w_mid) * gd.smoothstep(0.85, 1.0, t)

    outer = [(pts[i][0] + norms[i][0] * w(i), pts[i][1] + norms[i][1] * w(i)) for i in range(n)]
    inner = [(pts[i][0] - norms[i][0] * w(i), pts[i][1] - norms[i][1] * w(i)) for i in range(n)]
    body = gd.poly_path(outer + inner[::-1], close=True)

    frags = []
    if spikes:
        arc, nxt, sp = 0.0, spike_every, []
        for i in range(1, n - 6):
            arc += math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1])
            t = i / (n - 1)
            if arc >= nxt and 0.1 < t < 0.9:
                ww = w(i)
                nx, ny = norms[i]
                tx, ty = tans[i]
                h = ww * 0.55 + 2.2
                bl = (pts[i][0] + nx * (ww - 0.4) - tx * 2.6, pts[i][1] + ny * (ww - 0.4) - ty * 2.6)
                br = (pts[i][0] + nx * (ww - 0.4) + tx * 2.6, pts[i][1] + ny * (ww - 0.4) + ty * 2.6)
                tip = (pts[i][0] + nx * (ww + h) - tx * 3.2, pts[i][1] + ny * (ww + h) - ty * 3.2)
                sp.append(f"M{gd.fmt(bl[0])} {gd.fmt(bl[1])}L{gd.fmt(tip[0])} {gd.fmt(tip[1])}L{gd.fmt(br[0])} {gd.fmt(br[1])}Z")
                nxt = arc + spike_every
        frags.append(f'<path class="spike" d="{"".join(sp)}"/>')
    frags.append(f'<path class="body-fill" d="{body}"/>')
    # belly plates
    arc, nxt, pl = 0.0, 9.0, []
    for i in range(1, n):
        arc += math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1])
        t = i / (n - 1)
        if arc >= nxt and 0.15 < t < 0.95:
            ww = w(i)
            nx, ny = norms[i]
            tx, ty = tans[i]
            a = (pts[i][0] - nx * ww * 0.9, pts[i][1] - ny * ww * 0.9)
            b = (pts[i][0] - nx * ww * 0.25, pts[i][1] - ny * ww * 0.25)
            c = ((a[0] + b[0]) / 2 - tx * ww * 0.25, (a[1] + b[1]) / 2 - ty * ww * 0.25)
            pl.append(f"M{gd.fmt(a[0])} {gd.fmt(a[1])}Q{gd.fmt(c[0])} {gd.fmt(c[1])} {gd.fmt(b[0])} {gd.fmt(b[1])}")
            nxt = arc + 8.0
    frags.append(f'<path class="plate" d="{"".join(pl)}"/>')

    hx, hy = pts[-1]
    tx, ty = tans[-1]
    angle = math.degrees(math.atan2(ty, tx)) - 180
    return "\n".join(frags), (hx, hy), angle

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"


def serpent(points, width, taper_from=0.55):
    """A tapered serpent body along a polyline of (x, y) points: full width
    until taper_from, then narrowing to a tail tip. Returns a closed path."""
    n = len(points)
    # tangents and normals
    tans = []
    for i in range(n):
        a = points[max(0, i - 1)]
        b = points[min(n - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy) or 1
        tans.append((dx / L, dy / L))
    left, right = [], []
    for i, ((x, y), (tx, ty)) in enumerate(zip(points, tans)):
        t = i / (n - 1)
        w = width if t < taper_from else width * max(0.08, 1 - (t - taper_from) / (1 - taper_from))
        nx, ny = -ty, tx
        left.append((x + nx * w, y + ny * w))
        right.append((x - nx * w, y - ny * w))
    pts = left + right[::-1]
    return "M" + "L".join(f"{x:.1f} {y:.1f}" for x, y in pts) + "Z"


def wave_band(y, x0, x1, size=30, step=72, stagger=6):
    return "".join(curl(x, y + (stagger if i % 2 else 0), size)
                   for i, x in enumerate(range(x0, x1, step)))


def sine_pts(x0, y0, x1, y1, amp, waves, n=48, phase=0.0):
    pts = []
    for i in range(n + 1):
        t = i / n
        x = x0 + (x1 - x0) * t
        y = y0 + (y1 - y0) * t + amp * math.sin(phase + t * waves * 2 * math.pi)
        pts.append((x, y))
    return pts


# ----------------------------------------------------------------------
# 1. Mucalinda shelters the Buddha
# ----------------------------------------------------------------------
def mucalinda():
    W, H = 460, 430
    cx = 230

    # storm: slanted rain, parting around the hood
    rain = "".join(
        f'<path class="ln-faint" opacity=".5" d="M{x} {y} l-7 26"/>'
        for x, y in ((36, 40), (66, 96), (28, 160), (58, 226), (92, 300),
                     (424, 44), (398, 104), (432, 168), (402, 238), (368, 306),
                     (120, 32), (348, 26), (250, 6), (180, 14), (310, 2)))

    # the hood: a crescent canopy with seven heads along its rim
    heads = []
    for k in range(7):
        a = math.radians(180 - 24 - k * 22)      # spread across the top
        hx, hy = cx + 158 * math.cos(a), 208 - 148 * math.sin(a)
        # each head a leaf shape pointing outward, with an eye
        ox, oy = math.cos(a), math.sin(a)
        heads.append(
            f'<path class="skin" d="M{hx - 17 * oy:.1f} {hy - 17 * -ox:.1f} '
            f'Q{hx + 38 * ox:.1f} {hy - 38 * oy:.1f} {hx + 17 * oy:.1f} {hy + 17 * -ox:.1f} '
            f'Q{hx - 8 * ox:.1f} {hy + 8 * oy:.1f} {hx - 17 * oy:.1f} {hy - 17 * -ox:.1f} Z"/>'
            f'<circle cx="{hx + 14 * ox:.1f}" cy="{hy - 14 * oy:.1f}" r="2" fill="{BRIGHT}"/>')
    # the canopy's two ends sweep down behind the coils — the hood and the
    # coiled body are one serpent
    canopy = (f'<path class="skin" d="M{cx - 158} 208 A158 148 0 0 1 {cx + 158} 208 '
              f'C{cx + 162} 250 {cx + 148} 284 {cx + 118} 300 '
              f'L{cx + 96} 288 C{cx + 122} 272 {cx + 132} 244 {cx + 128} 208 '
              f'A128 120 0 0 0 {cx - 128} 208 '
              f'C{cx - 132} 244 {cx - 122} 272 {cx - 96} 288 '
              f'L{cx - 118} 300 C{cx - 148} 284 {cx - 162} 250 {cx - 158} 208 Z"/>')
    ribs = "".join(
        f'<path class="ln-thin" opacity=".6" d="M{cx + 128 * math.cos(math.radians(180 - 30 - k * 24)):.1f} '
        f'{208 - 120 * math.sin(math.radians(180 - 30 - k * 24)):.1f} '
        f'L{cx + 155 * math.cos(math.radians(180 - 30 - k * 24)):.1f} '
        f'{208 - 145 * math.sin(math.radians(180 - 30 - k * 24)):.1f}"/>'
        for k in range(0))

    # the coils: three stacked, narrowing upward
    coils = "".join(
        f'<ellipse cx="{cx}" cy="{y}" rx="{rx}" ry="{ry}" class="skin"/>'
        f'<path class="ln-thin" opacity=".55" d="M{cx - rx + 14} {y + 3} Q{cx} {y + ry + 4} {cx + rx - 14} {y + 3}"/>'
        for y, rx, ry in ((398, 132, 26), (360, 148, 27), (318, 120, 25)))
    neck = ""

    # the Buddha, seated in meditation on the coils
    buddha = f"""
  <g>
    <ellipse cx="{cx}" cy="292" rx="74" ry="14" class="skin"/>
    <path class="fig" d="M{cx - 62} 288 C{cx - 58} 246 {cx - 40} 222 {cx - 26} 212
         C{cx - 34} 198 {cx - 32} 182 {cx - 22} 172 C{cx - 28} 152 {cx - 16} 136 {cx} 136
         C{cx + 16} 136 {cx + 28} 152 {cx + 22} 172 C{cx + 32} 182 {cx + 34} 198 {cx + 26} 212
         C{cx + 40} 222 {cx + 58} 246 {cx + 62} 288 Z"/>
    <path class="ln-thin" d="M{cx - 40} 250 C{cx - 20} 262 {cx + 20} 262 {cx + 40} 250"/>
    <path class="ln-thin" d="M{cx - 22} 286 C{cx - 8} 278 {cx + 8} 278 {cx + 22} 286"/>
    <circle cx="{cx}" cy="130" r="5" class="fig"/>
    <path class="ln-thin" d="M{cx - 12} 160 Q{cx} 166 {cx + 12} 160"/>
  </g>"""

    body = f"""
{rain}
{canopy}
{ribs}
{''.join(heads)}
{neck}
{coils}
{buddha}
"""
    extra = f"""
  .fig {{ fill:url(#skin); stroke:{BRIGHT}; stroke-width:2; stroke-linejoin:round; }}
"""
    return svg(W, H, body, extra_css=extra, label=(
        "The Naga King Mucalinda coils beneath the meditating Buddha and spreads "
        "his sevenfold hood above him, sheltering him from the storm"))


# ----------------------------------------------------------------------
# 2. a crowned nagaraja with the pearl
# ----------------------------------------------------------------------
# 2. a crowned nagaraja with the pearl
# ----------------------------------------------------------------------
def naga_king():
    """The Dragon King form of the nagaraja: the hero dragon's own head on a
    smooth serpent body rising from the waves, crowned, with the radiant
    pearl before him — unmistakably the same being as the rest of the site."""
    W, H = 440, 480

    waves = wave_band(442, -14, 472, size=34, step=76)

    spine = [(392, 470), (306, 434), (232, 412), (172, 372), (158, 316),
             (196, 268), (252, 240), (286, 200), (274, 152), (238, 128)]
    body_frag, (hx, hy), angle = dragon_body(spine, w_head=9.5, w_mid=14.0)
    head = gd.head_group(hx, hy, angle - 6, 0.62)

    crown = f"""
  <g transform="translate({hx - 34:.0f} {hy - 66:.0f}) rotate(-10)">
    <path class="gild" d="M-20 18 L-24 -6 L-10 6 L0 -14 L10 6 L24 -6 L20 18 Z"/>
    <circle cx="-24" cy="-10" r="2.4" fill="{BRIGHT}"/>
    <circle cx="0" cy="-18" r="2.8" fill="{BRIGHT}"/>
    <circle cx="24" cy="-10" r="2.4" fill="{BRIGHT}"/>
    <path class="ln-thin" d="M-20 18 L20 18"/>
  </g>"""

    px, py = 128, 92
    rays = "".join(
        f'<path class="ln-thin" opacity=".65" d="M{px + 30 * math.cos(math.radians(a)):.1f} '
        f'{py + 30 * math.sin(math.radians(a)):.1f} L{px + 40 * math.cos(math.radians(a)):.1f} '
        f'{py + 40 * math.sin(math.radians(a)):.1f}"/>' for a in range(0, 360, 60))
    pearl = f"""
  <circle cx="{px}" cy="{py}" r="14" fill="none" stroke="{BRIGHT}" stroke-width="2"/>
  <circle cx="{px}" cy="{py}" r="4.6" fill="{BRIGHT}"/>
  <circle cx="{px}" cy="{py}" r="25" class="ln-faint" fill="none"/>
  {rays}
  <path class="ln-thin" d="M{px - 6} {py - 20} C{px - 2} {py - 28} {px + 7} {py - 30} {px + 12} {py - 24}"/>
"""

    jewels = "".join(
        f'<path class="ln-thin" d="M{x} {y - 8} C{x + 6} {y - 2} {x + 6} {y + 4} {x} {y + 7} '
        f'C{x - 6} {y + 4} {x - 6} {y - 2} {x} {y - 8} Z"/>'
        for x, y in ((84, 380), (382, 330), (400, 180)))

    body = f"""
{HEAD_DEFS}
{body_frag}
{head}
{crown}
{pearl}
{jewels}
<path class="ln" d="{waves}"/>
"""
    return svg(W, H, body, extra_css=HEAD_CSS, label=(
        "A crowned Naga King in dragon form rising from the waves, "
        "the radiant pearl shining before him"))


# ----------------------------------------------------------------------
def naga_palace():
    W, H = 520, 400
    cx = 260

    surface = wave_band(46, -14, 552, size=26, step=70)

    # the palace: two upswept roofs over a pillared hall, pearl at the ridge
    def roof(y, half, rise):
        return (f'M{cx - half} {y} C{cx - half - 5} {y + 7} {cx - half - 13} {y + 12} {cx - half - 21} {y + 13} '
                f'C{cx - half + 12} {y - rise} {cx + half - 12} {y - rise} {cx + half + 21} {y + 13} '
                f'C{cx + half + 13} {y + 12} {cx + half + 5} {y + 7} {cx + half} {y} Z')
    palace = f"""
  <path class="gild" d="{roof(160, 56, 34)}"/>
  <path class="gild" d="{roof(226, 92, 40)}"/>
  <path class="ln-thin" d="M{cx - 42} 162 L{cx - 42} 190 M{cx + 42} 162 L{cx + 42} 190"/>
  <path class="ln" d="M{cx - 76} 240 L{cx - 76} 330 M{cx + 76} 240 L{cx + 76} 330
       M{cx - 30} 240 L{cx - 30} 330 M{cx + 30} 240 L{cx + 30} 330 M{cx - 90} 330 L{cx + 90} 330"/>
  <path class="ln-thin" d="M{cx - 30} 268 C{cx - 16} 258 {cx + 16} 258 {cx + 30} 268"/>
  <circle cx="{cx}" cy="112" r="5" class="ln-thin" fill="none"/>
  <circle cx="{cx}" cy="112" r="1.6" fill="{BRIGHT}"/>
  <!-- light from the doorway -->
  <path class="ln-faint" d="M{cx - 22} 330 L{cx - 44} 368 M{cx} 330 L{cx} 372 M{cx + 22} 330 L{cx + 44} 368"/>
"""

    # left treasure: a heap of jewels
    jewels = "".join(
        f'<path class="ln-thin" d="M{x} {y - 10} C{x + 7} {y - 2} {x + 7} {y + 5} {x} {y + 9} '
        f'C{x - 7} {y + 5} {x - 7} {y - 2} {x} {y - 10} Z"/>'
        for x, y in ((92, 322), (68, 334), (116, 336), (80, 306), (104, 300)))
    heap = f'<path class="ln" d="M46 346 C70 322 114 322 140 346"/>'
    flame = f'<path class="ln-thin" d="M92 282 C96 274 92 268 88 264 C86 272 88 276 92 282 Z"/>'

    # right treasure: the chest of scriptures, scrolls stacked on top
    chest = f"""
  <g>
    <rect x="380" y="316" width="88" height="34" rx="3" class="gild"/>
    <path class="ln-thin" d="M380 330 L468 330 M424 330 L424 350"/>
    {''.join(f'<g><circle cx="{x}" cy="306" r="9" class="ln" fill="none"/>'
             f'<circle cx="{x}" cy="306" r="2.2" fill="{GOLD}"/></g>'
             for x in (398, 420, 442))}
    <circle cx="431" cy="290" r="8" class="ln-thin" fill="none"/>
    <circle cx="431" cy="290" r="2" fill="{GOLD}"/>
  </g>"""

    bubbles = "".join(f'<circle cx="{x}" cy="{y}" r="{r}" class="ln-faint" fill="none"/>'
                      for x, y, r in ((60, 120, 4), (74, 96, 2.6), (452, 130, 4),
                                      (468, 104, 2.6), (500, 210, 3), (28, 240, 3)))

    body = f"""
<path class="ln" d="{surface}"/>
{bubbles}
{palace}
{heap}
{jewels}
{flame}
{chest}
<path class="ln-faint" d="M20 350 L500 350"/>
"""
    return svg(W, H, body, label=(
        "The Dragon Palace beneath the sea, its doorway shining, flanked by its two "
        "treasures: a heap of jewels, and a chest of scriptures with scrolls upon it"))


# ----------------------------------------------------------------------
# 4. the garuda and the naga, before the same jewel
# ----------------------------------------------------------------------
# 4. the garuda and the naga, before the same jewel
# ----------------------------------------------------------------------
def naga_garuda():
    W, H = 520, 360
    jx, jy = 260, 178

    jrays = "".join(
        f'<path class="ln-thin" opacity=".7" d="M{jx + 40 * math.cos(math.radians(a)):.1f} '
        f'{jy + 40 * math.sin(math.radians(a)):.1f} L{jx + 52 * math.cos(math.radians(a)):.1f} '
        f'{jy + 52 * math.sin(math.radians(a)):.1f}"/>' for a in range(0, 360, 45))
    jewel = f"""
  <path class="gild" d="M{jx} {jy - 24} C{jx + 15} {jy - 7} {jx + 15} {jy + 9} {jx} {jy + 17}
       C{jx - 15} {jy + 9} {jx - 15} {jy - 7} {jx} {jy - 24} Z"/>
  <circle cx="{jx}" cy="{jy}" r="32" class="ln-faint" fill="none"/>
  {jrays}
"""

    gx, gy = 150, 104

    def wing(dirn):
        sx, sy = gx + dirn * 14, gy + 2
        tipx, tipy = gx + dirn * 128, gy - 62
        d = f"M{sx} {sy} C{gx + dirn * 40} {gy - 44} {gx + dirn * 88} {gy - 70} {tipx} {tipy} "
        feathers = []
        for k in range(6):
            ft = (k + 1) / 6
            fx = tipx - dirn * abs(tipx - sx) * ft
            fy = tipy + (sy - tipy) * ft + 26 * math.sin(ft * math.pi)
            feathers.append((fx, fy))
        px2, py2 = tipx, tipy
        for fx, fy in feathers:
            mx, my = (px2 + fx) / 2 + dirn * 4, max(py2, fy) + 14
            d += f"Q{mx:.1f} {my:.1f} {fx:.1f} {fy:.1f} "
            px2, py2 = fx, fy
        d += "Z"
        return d

    garuda = f"""
  <g transform="translate({gx} {gy}) scale(1.32) translate({-gx} {-gy})">
  <path class="skin" d="{wing(-1)}"/>
  <path class="skin" d="{wing(1)}"/>
  <path class="skin" d="M{gx - 15} {gy} C{gx - 17} {gy + 26} {gx - 9} {gy + 46} {gx} {gy + 52}
       C{gx + 9} {gy + 46} {gx + 17} {gy + 26} {gx + 15} {gy} C{gx + 6} {gy - 8} {gx - 6} {gy - 8} {gx - 15} {gy} Z"/>
  <path class="ln-thin" d="M{gx - 8} {gy + 52} L{gx - 14} {gy + 70} M{gx} {gy + 54} L{gx} {gy + 74} M{gx + 8} {gy + 52} L{gx + 14} {gy + 70}"/>
  <circle cx="{gx}" cy="{gy - 18}" r="13" class="skin"/>
  <path class="gild" d="M{gx - 6} {gy - 30} L{gx - 2} {gy - 44} L{gx + 3} {gy - 31} L{gx + 8} {gy - 42} L{gx + 10} {gy - 28} Z"/>
  <path class="ln" d="M{gx + 10} {gy - 18} C{gx + 22} {gy - 16} {gx + 26} {gy - 10} {gx + 22} {gy - 4} L{gx + 9} {gy - 9}"/>
  <circle cx="{gx + 4}" cy="{gy - 21}" r="2" fill="{BRIGHT}"/>
  <path class="ln-thin" d="M{gx - 12} {gy + 70} l-5 7 m5 -7 l1 9 M{gx + 12} {gy + 70} l5 7 m-5 -7 l-1 9"/>
  </g>
"""

    waves = wave_band(316, 262, 552, size=28, step=70)
    spine = [(500, 352), (446, 314), (402, 292), (378, 258), (376, 224), (392, 198)]
    naga_frag, (nx, ny), nangle = dragon_body(spine, w_head=6.0, w_mid=8.5, spikes=False)
    naga = f"""
  {naga_frag}
  <path class="skin" d="M{nx - 22:.0f} {ny + 4:.0f} A22 26 0 0 1 {nx + 22:.0f} {ny + 4:.0f} L{nx + 13:.0f} {ny + 4:.0f} A13 16 0 0 0 {nx - 13:.0f} {ny + 4:.0f} Z"/>
  <ellipse cx="{nx:.0f}" cy="{ny:.0f}" rx="11" ry="13" class="skin" transform="rotate(-30 {nx:.0f} {ny:.0f})"/>
  <circle cx="{nx - 4:.0f}" cy="{ny - 5:.0f}" r="1.8" fill="{BRIGHT}"/>
  <path class="ln-thin" d="M{nx - 9:.0f} {ny - 11:.0f} C{nx - 15:.0f} {ny - 18:.0f} {nx - 23:.0f} {ny - 21:.0f} {nx - 31:.0f} {ny - 20:.0f}"/>
  <path class="ln-thin" d="{curl(nx - 37, ny - 30, 7, turns=1.3)}"/>
"""

    body = f"""
{HEAD_DEFS}
{jewel}
{garuda}
<path class="ln" d="{waves}"/>
{naga}
"""
    return svg(W, H, body, extra_css=HEAD_CSS, label=(
        "The garuda and the naga, ancient enemies, both turned toward the same "
        "radiant jewel of the dharma between them"))


# naga-karmapa.svg is traced from the owner's photograph by
# scripts/trace_karmapa.py — not generated here.


if __name__ == "__main__":
    for name, maker in (("naga-mucalinda.svg", mucalinda),
                        ("naga-king.svg", naga_king),
                        ("naga-palace.svg", naga_palace),
                        ("naga-garuda.svg", naga_garuda)):
        out = maker()
        (ASSETS / name).write_text(out, encoding="utf-8")
        print(f"  {name}: {len(out) / 1024:.1f} KB")
