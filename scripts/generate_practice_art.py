#!/usr/bin/env python3
"""Generate the Treasure Vase Yoga illustrations.

Three instructional figures, each anchored to a passage of the teaching by
scripts/build_practice.py:

  mudra.svg            the 井 mudra — index and middle fingers of both
                       hands crossed
  vase-preparation.svg cutaway of the sealed vase: five herbs as the five
                       chakras, copper-coin seal, five coloured cloths
  casting-the-vase.svg the finished vase cast into the sea

and five decorative pieces:

  deco-cloud-rule.svg  auspicious-cloud divider drawn above each heading
  deco-dragon-beneath.svg  the dragon stirring under a mirror-calm sea
  deco-water-stairs.svg    the staircase of water into the Dragon Palace
  deco-shrine.svg          the sealed vase placed on the shrine
  deco-jewel-rain.svg      the rain of jewels and coins into the sea

House style throughout: fine gold line-art on deep indigo (紺紙金泥),
with no background shading — the drawings sit directly on the page.

These are drawn for a ~340px-wide column on desktop, so the viewBoxes are
kept small and the labels large relative to them; detail that only reads at
600px is wasted here.

Run from the repo root:  python3 scripts/generate_practice_art.py
"""
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
ASSETS.mkdir(exist_ok=True)

GOLD, BRIGHT, DIM = "#d9b25f", "#f4dc96", "#8d7440"
INK, INK2 = "#0e1c34", "#16294a"

DEFS = f"""
  <!-- barely above the page ground, so the hands read as line-art while still
       being opaque enough to occlude the fingers passing beneath them -->
  <linearGradient id="skin" x1="0" y1="0" x2="0.4" y2="1">
    <stop offset="0%" stop-color="#122340"/><stop offset="100%" stop-color="#0b1729"/>
  </linearGradient>
  <linearGradient id="vaseBody" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0%" stop-color="#1d3560"/><stop offset="60%" stop-color="#132443"/>
    <stop offset="100%" stop-color="#0d1930"/>
  </linearGradient>
  <linearGradient id="gild" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0%" stop-color="{GOLD}" stop-opacity=".30"/>
    <stop offset="55%" stop-color="{GOLD}" stop-opacity=".14"/>
    <stop offset="100%" stop-color="{GOLD}" stop-opacity=".26"/>
  </linearGradient>
  <linearGradient id="coin" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0%" stop-color="{BRIGHT}"/><stop offset="100%" stop-color="#a8814a"/>
  </linearGradient>
"""

BASE_CSS = f"""
  .ln {{ fill:none; stroke:{GOLD}; stroke-width:2; stroke-linecap:round; stroke-linejoin:round; }}
  .ln-bright {{ fill:none; stroke:{BRIGHT}; stroke-width:2.2; stroke-linecap:round; stroke-linejoin:round; }}
  .ln-thin {{ fill:none; stroke:{GOLD}; stroke-width:1.3; stroke-linecap:round;
              stroke-linejoin:round; opacity:.8; }}
  .ln-faint {{ fill:none; stroke:{DIM}; stroke-width:1; opacity:.6; }}
  .skin {{ fill:url(#skin); stroke:{BRIGHT}; stroke-width:2.1; stroke-linejoin:round;
           stroke-linecap:round; }}
  .gild {{ fill:url(#gild); stroke:{BRIGHT}; stroke-width:1.8; stroke-linejoin:round; }}
  .label {{ font-family:"Cormorant Garamond",Georgia,serif; fill:#c9bfa6; font-size:15px; }}
  .label-zh {{ font-family:"LXGW WenKai TC","Kaiti TC",serif; fill:{GOLD}; font-size:20px;
               letter-spacing:.1em; }}
"""


def svg(w, h, body, extra_css="", label=""):
    role = (f' role="img" aria-label="{label}"' if label
            else ' role="presentation" aria-hidden="true"')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}"{role}>\n'
            f'<style>{BASE_CSS}{extra_css}</style>\n'
            f'<defs>{DEFS}</defs>\n{body}\n</svg>\n')


# ----------------------------------------------------------------------
# 1. the 井 mudra
# ----------------------------------------------------------------------
def finger(x1, y1, x2, y2, w1, w2, bow=0.0):
    """A tapered finger from base (x1,y1) to tip (x2,y2), with a rounded tip
    and an optional sideways bow so it doesn't read as a rigid stick."""
    dx, dy = x2 - x1, y2 - y1
    L = math.hypot(dx, dy) or 1
    ux, uy = dx / L, dy / L
    nx, ny = -uy, ux

    def p(t, w):
        return (x1 + ux * L * t + nx * w + nx * bow * math.sin(math.pi * t),
                y1 + uy * L * t + ny * w + ny * bow * math.sin(math.pi * t))

    a, b = p(0, w1), p(0, -w1)
    ma, mb = p(0.5, w1 * 0.92 + 0.5), p(0.5, -(w1 * 0.92 + 0.5))
    c, d = p(1, w2), p(1, -w2)
    tipx, tipy = x2 + ux * w2 * 1.35, y2 + uy * w2 * 1.35
    return (f'M{a[0]:.1f} {a[1]:.1f} Q{ma[0]:.1f} {ma[1]:.1f} {c[0]:.1f} {c[1]:.1f} '
            f'Q{tipx:.1f} {tipy:.1f} {d[0]:.1f} {d[1]:.1f} '
            f'Q{mb[0]:.1f} {mb[1]:.1f} {b[0]:.1f} {b[1]:.1f} Z')


def nail(x, y, ux, uy, w):
    """The nail plate just behind a fingertip: a small rounded quadrilateral."""
    nx, ny = -uy, ux
    back = 2.05 * w
    a = (x - ux * back + nx * w * 0.62, y - uy * back + ny * w * 0.62)
    b = (x - ux * back - nx * w * 0.62, y - uy * back - ny * w * 0.62)
    ca = (x - ux * w * 0.35 + nx * w * 0.72, y - uy * w * 0.35 + ny * w * 0.72)
    cb = (x - ux * w * 0.35 - nx * w * 0.72, y - uy * w * 0.35 - ny * w * 0.72)
    tip = (x - ux * w * 0.05, y - uy * w * 0.05)
    return (f'M{a[0]:.1f} {a[1]:.1f} Q{x - ux * back * 1.15:.1f} {y - uy * back * 1.15:.1f} '
            f'{b[0]:.1f} {b[1]:.1f} Q{cb[0]:.1f} {cb[1]:.1f} {tip[0]:.1f} {tip[1]:.1f} '
            f'Q{ca[0]:.1f} {ca[1]:.1f} {a[0]:.1f} {a[1]:.1f} Z')


def crease(x1, y1, x2, y2, t, w):
    """A knuckle crease across a finger at position t along it."""
    ux, uy = x2 - x1, y2 - y1
    L = math.hypot(ux, uy) or 1
    ux, uy = ux / L, uy / L
    nx, ny = -uy, ux
    px, py = x1 + (x2 - x1) * t, y1 + (y2 - y1) * t
    return (f'M{px + nx * w * 0.72:.1f} {py + ny * w * 0.72:.1f} '
            f'Q{px + ux * w * 0.45:.1f} {py + uy * w * 0.45:.1f} '
            f'{px - nx * w * 0.72:.1f} {py - ny * w * 0.72:.1f}')


def joints(axis, tipw, ts=(0.10, 0.40, 0.70)):
    """Nail plus knuckle creases for a finger described by its axis."""
    (x1, y1), (x2, y2) = axis
    L = math.hypot(x2 - x1, y2 - y1) or 1
    ux, uy = (x2 - x1) / L, (y2 - y1) / L
    out = [f'<path class="ln-thin" d="{nail(x2, y2, ux, uy, tipw)}"/>']
    for i, t in enumerate(ts):
        out.append(f'<path class="ln-thin" d="{crease(x1, y1, x2, y2, t, tipw + 5 - i * 1.6)}"/>')
    return "".join(out)


# The left hand as ONE closed contour: up the back of the hand, out along the
# index, round the tip, down its far side, through the web, out along the
# middle finger and home round the folded ring and little fingers. Letting the
# contour of the hand run *into* the finger is what makes line-art read as
# anatomy rather than as pipes glued to a mitten.
#
# The right hand is this same path mirrored about x = W/2 — two hands really
# are mirror images, and it guarantees both are drawn equally well.
LEFT_HAND = (
    "M-6 392 C24 366 62 330 96 302 C110 293 118 289 127 290 "      # back of the hand
    "C168 236 220 174 268 116 C276 106 292 114 288 132 "           # index, and its tip
    "C258 172 222 216 196 253 C200 258 204 262 208 266 "           # down to the web
    "C240 236 288 194 321 157 C331 147 347 157 339 175 "           # middle, and its tip
    "C302 216 240 282 188 334 "                                    # back down to the hand
    "C200 349 195 367 176 375 C185 389 172 405 149 407 "           # the folded knuckles
    "C116 411 82 417 54 433 C36 443 24 459 20 470 L-6 470 Z")      # heel into the forearm

LEFT_DETAIL = (
    # the ring and little finger, folded into the palm
    '<path class="ln-thin" d="M188 334 C164 343 141 359 131 377 C123 393 133 406 152 403"/>'
    '<path class="ln-thin" d="M176 375 C158 381 143 392 136 403"/>'
    # the thumb closed over them
    '<path class="ln-thin" d="M30 389 C64 393 98 401 122 412 C137 419 138 433 120 436"/>'
    # the tendons over the back of the hand, and the wrist crease
    '<path class="ln-thin" d="M4 400 C26 388 42 372 52 352"/>'
    '<path class="ln-thin" opacity=".5" d="M96 302 C88 322 76 340 60 354"/>'
    '<path class="ln-thin" opacity=".5" d="M127 292 C122 316 112 338 96 356"/>'
    '<path class="ln-faint" d="M-2 424 C16 418 30 408 40 396"/>')

# axes of the two extended fingers, for the nails and knuckle creases
LEFT_FINGERS = [(((140, 300), (278, 124)), 12), (((172, 325), (330, 166)), 12)]


def mudra():
    """After the reference drawing: the index and middle finger of each hand
    cross the other pair, the four together drawing the lattice of 井. The
    remaining fingers curl into the palm and the thumbs close over them."""
    W, H = 440, 470

    hand = (f'<path class="skin" d="{LEFT_HAND}"/>'
            + "".join(joints(a, w) for a, w in LEFT_FINGERS)
            + LEFT_DETAIL)

    body = f"""
<!-- RIGHT HAND — the left hand mirrored; its fingers pass beneath -->
<g transform="translate({W} 0) scale(-1 1)">{hand}</g>

<!-- LEFT HAND — laid across the right -->
<g>{hand}</g>

<text class="label-zh" x="220" y="428" font-size="40" text-anchor="middle">井</text>
<text class="label" x="220" y="450" text-anchor="middle" font-size="14">jǐng</text>
"""
    return svg(W, H, body, label=(
        "The mudra of the Dragon King Yoga: the index and middle fingers of both hands "
        "crossed to form the lattice of the character 井"))


# ----------------------------------------------------------------------
# the treasure vase — one silhouette, shared by figures 2 and 3
#
# Canonical drawing: centred on x = 0, the finial tip at y = 0 and the foot
# at y = 1000, after the Tibetan bumpa: leaf-shaped finial, lotus cup,
# flared gold crown, neck ring, shoulder collar, round silver belly,
# lotus foot and petalled base.
# ----------------------------------------------------------------------
BELLY_CY, BELLY_RX, BELLY_RY = 745, 196, 178
BELLY_TOP, BELLY_BOT = BELLY_CY - BELLY_RY, BELLY_CY + BELLY_RY

FINIAL = ("M0 8 C42 62 96 122 112 174 C124 214 106 248 74 260 "
          "C40 273 -40 273 -74 260 C-106 248 -124 214 -112 174 "
          "C-96 122 -42 62 0 8 Z")
CUP = "M-122 328 C-118 284 -84 256 -48 252 L48 252 C84 256 118 284 122 328 Z"
CROWN = ("M-162 344 C-152 396 -124 444 -94 474 L94 474 "
         "C124 444 152 396 162 344 Z")
NECK = "M-106 476 L106 476 L106 520 L-106 520 Z"
COLLAR = ("M-192 578 C-188 544 -152 522 -106 519 L106 519 "
          "C152 522 188 544 192 578 Z")
FOOT = "M-124 902 C-120 936 -100 960 -72 968 L72 968 C100 960 120 936 124 902 Z"
BASE = ("M-74 962 C-100 984 -140 996 -176 1006 L176 1006 "
        "C140 996 100 984 74 962 Z")

# petal divisions, drawn on top of the gilt shapes
PETAL_LINES = (
    # lotus cup
    "M-74 326 C-70 296 -54 268 -34 254 M-26 328 C-24 298 -16 272 -8 254 "
    "M26 328 C24 298 16 272 8 254 M74 326 C70 296 54 268 34 254 "
    # crown ribs
    "M-108 348 C-102 392 -84 436 -62 470 M-54 350 C-52 394 -44 436 -32 472 "
    "M54 350 C52 394 44 436 32 472 M108 348 C102 392 84 436 62 470 "
    # shoulder collar
    "M-124 574 C-122 550 -114 532 -100 520 M-58 576 C-58 552 -54 534 -46 520 "
    "M58 576 C58 552 54 534 46 520 M124 574 C122 550 114 532 100 520 "
    # foot
    "M-70 906 C-68 932 -60 954 -46 966 M-16 908 C-16 934 -12 956 -6 968 "
    "M16 908 C16 934 12 956 6 968 M70 906 C68 932 60 954 46 966 "
    # base flare
    "M-40 976 C-58 990 -88 1000 -116 1006 M40 976 C58 990 88 1000 116 1006"
)

JEWELS = (
    ('<path d="M0 132 C16 152 22 172 14 186 C8 196 -8 196 -14 186 '
     'C-22 172 -16 152 0 132 Z" fill="#b8452f" opacity=".8" '
     f'stroke="{BRIGHT}" stroke-width="1.2"/>'),
    ('<path d="M-44 150 C-30 168 -26 186 -34 198 C-40 207 -54 207 -60 198 '
     'C-68 186 -58 168 -44 150 Z" fill="#3f5f96" opacity=".8" '
     f'stroke="{BRIGHT}" stroke-width="1.2"/>'),
    ('<path d="M44 150 C58 168 62 186 54 198 C48 207 34 207 28 198 '
     'C20 186 30 168 44 150 Z" fill="#3f5f96" opacity=".8" '
     f'stroke="{BRIGHT}" stroke-width="1.2"/>'),
)


def vase(cx, top, s, belly_fill="url(#vaseBody)", detail=True):
    """The vase silhouette placed with its finial tip at (cx, top), scaled
    by s. Returns (svg_fragment, geometry_dict) — the caller needs the belly
    box to lay the herb layers and the leader lines out."""
    g = [f'<g transform="translate({cx} {top}) scale({s})">']
    g.append(f'<ellipse cx="0" cy="{BELLY_CY}" rx="{BELLY_RX}" ry="{BELLY_RY}" '
             f'fill="{belly_fill}" stroke="{BRIGHT}" stroke-width="{2.2 / s:.2f}"/>')
    for d in (FINIAL, CUP, CROWN, NECK, COLLAR, FOOT, BASE):
        g.append(f'<path class="gild" d="{d}" stroke-width="{1.9 / s:.2f}"/>')
    g.append("".join(JEWELS))
    if detail:
        g.append(f'<path class="ln-thin" d="{PETAL_LINES}" stroke-width="{1.3 / s:.2f}"/>')
        # the beaded rings that separate the metal courses
        for y, rx in ((476, 106), (520, 106), (578, 192), (902, 124)):
            g.append(f'<path class="ln-faint" stroke-width="{1.2 / s:.2f}" '
                     f'd="M{-rx} {y} L{rx} {y}"/>')
    g.append("</g>")
    geo = {
        "cx": cx,
        "belly_top": top + BELLY_TOP * s,
        "belly_bot": top + BELLY_BOT * s,
        "belly_rx": BELLY_RX * s,
        "belly_ry": BELLY_RY * s,
        "belly_cy": top + BELLY_CY * s,
        "neck_y": top + 498 * s,
        "bottom": top + 1006 * s,
    }
    return "\n".join(g), geo


# ----------------------------------------------------------------------
# 2. the prepared vase — five herbs as five chakras
# ----------------------------------------------------------------------
LAYERS = [
    ("頂輪", "Crown", "Gastrodia", "天麻", "#c9bfa6"),
    ("喉輪", "Throat", "Milk Vetch", "黃耆", "#e8e0cc"),
    ("心輪", "Heart", "Angelica", "當歸", "#c96f5a"),
    ("臍輪", "Navel", "Atractylodes", "白朮", "#c9a15f"),
    ("海底輪", "Root", "Fleece-flower", "何首烏", "#5d6b86"),
]
CLOTHS = [("#b8452f", -36), ("#5b8c5a", -18), ("#4a6fa5", 0), ("#e8e0cc", 18), ("#d9b25f", 36)]


def vase_preparation():
    W, H = 420, 620
    art, geo = vase(cx=118, top=26, s=0.556)

    top, bot = geo["belly_top"] + 32, geo["belly_bot"] - 8
    band_h = (bot - top) / 5
    cx, rx, ry = geo["cx"], geo["belly_rx"], geo["belly_ry"]
    cy = geo["belly_cy"]

    def hw(y):
        """Half-width of the belly at height y — the layers follow the curve."""
        t = (y - cy) / ry
        return rx * math.sqrt(max(0.0, 1 - t * t)) - 3.5

    # labels are spread wider than the bands, so five two-line entries fit
    lab_top, lab_step = 214, 66

    bands, marks, labels = [], [], []
    for i, (zh, en, herb, herb_zh, col) in enumerate(LAYERS):
        y0 = top + i * band_h
        w0, w1 = hw(y0), hw(y0 + band_h)
        wmid = max(w0, w1)
        bands.append(
            f'<path d="M{cx - w0:.1f} {y0:.1f} L{cx + w0:.1f} {y0:.1f} '
            f'L{cx + w1:.1f} {y0 + band_h:.1f} L{cx - w1:.1f} {y0 + band_h:.1f} Z" '
            f'fill="{col}" opacity=".30"/>')
        if i:
            bands.append(f'<path class="ln-thin" opacity=".8" '
                         f'd="M{cx - w0:.1f} {y0:.1f} L{cx + w0:.1f} {y0:.1f}"/>')
        # granules of the herb
        for k in range(6):
            gx = cx - wmid * 0.72 + k * (wmid * 1.44 / 5)
            gy = y0 + band_h * (0.34 + 0.30 * (k % 2))
            bands.append(f'<circle cx="{gx:.1f}" cy="{gy:.1f}" r="2.4" '
                         f'fill="{col}" opacity=".5"/>')

        # leader: from the band, out past the belly, to the label
        by = y0 + band_h / 2
        ly = lab_top + i * lab_step
        ex = cx + hw(by) + 6
        marks.append(f'<path class="ln-faint" d="M{ex:.1f} {by:.1f} L{248:.0f} {ly - 6:.0f} '
                     f'L{262:.0f} {ly - 6:.0f}"/>'
                     f'<circle cx="{ex:.1f}" cy="{by:.1f}" r="2.6" fill="{GOLD}"/>')
        labels.append(
            f'<text class="label-zh" x="268" y="{ly:.0f}">{zh}<tspan class="label" '
            f'font-size="14" dx="6">{herb_zh}</tspan></text>'
            f'<text class="label" x="268" y="{ly + 19:.0f}" font-size="14">{en} · {herb}</text>')

    # the cloths are tied at the neck ring and drape over the shoulder — kept
    # short so they never cover the cutaway below
    cloths = "".join(
        f'<g transform="translate({cx + (i - 2) * 21} {geo["neck_y"]:.0f}) '
        f'rotate({(i - 2) * 9})">'
        f'<path d="M-8 -4 C-13 16 -10 34 2 48 C10 34 9 14 7 -4 Z" fill="{col}" opacity=".9" '
        f'stroke="{INK}" stroke-width="1"/></g>'
        for i, (col, _rot) in enumerate(CLOTHS))

    body = f"""
{art}

<!-- what is inside: the five herbs, layered as the five chakras -->
<g>{''.join(bands)}</g>

<!-- the copper coin dropped in last, sealing the vase -->
<g transform="translate({cx} {geo['belly_top'] + 19:.0f})">
  <ellipse cx="0" cy="0" rx="30" ry="9" fill="url(#coin)" stroke="{BRIGHT}" stroke-width="1.4"/>
  <rect x="-5" y="-3" width="10" height="6" fill="{INK}" stroke="{BRIGHT}" stroke-width="1"/>
</g>

<!-- the five coloured cloths tied at the neck -->
{cloths}

{''.join(marks)}
{''.join(labels)}
"""
    return svg(W, H, body, label=(
        "Cutaway of the prepared treasure vase: five medicinal herbs layered as the five "
        "chakras from root to crown, sealed with a copper coin and tied with five coloured cloths"))


# ----------------------------------------------------------------------
# 3. casting the vase into the sea
# ----------------------------------------------------------------------
def curl(cx, cy, size, turns=1.7, k=0.34, samples=64):
    pts = []
    for i in range(samples + 1):
        th = turns * 2 * math.pi * i / samples
        r = size * math.exp(-k * th)
        a = -0.35 + th
        pts.append((cx + r * math.cos(a), cy - r * math.sin(a)))
    return "M" + "L".join(f"{x:.1f} {y:.1f}" for x, y in pts)


def casting():
    W, H = 470, 300
    waves = "".join(curl(x, 268 + (7 if i % 2 else 0), 44)
                    for i, x in enumerate(range(-14, 512, 88)))
    waves_back = "".join(curl(x, 244, 30) for x in range(20, 512, 106))

    arc = "M78 216 C158 80 318 66 400 228"

    # the same vase, tumbling — big enough to be recognised, without the
    # petal-by-petal detail, which turns to mud at this size
    small, _ = vase(cx=0, top=-101, s=0.20, detail=False)
    cloth = "".join(
        f'<g transform="rotate({rot * 1.4})"><path d="M-5 0 C-9 16 -6 32 3 44 '
        f'C9 31 8 15 5 0 Z" fill="{col}" opacity=".85"/></g>' for col, rot in CLOTHS)

    body = f"""
<!-- flight path -->
<path class="ln-faint" stroke-dasharray="5 9" d="{arc}"/>

<!-- the vase, mid-flight -->
<g transform="translate(226 112) rotate(27)">
  {small}
  {cloth}
</g>

<!-- sparks trailing -->
<circle cx="132" cy="146" r="2.6" fill="{BRIGHT}" opacity=".8"/>
<circle cx="168" cy="112" r="2" fill="{BRIGHT}" opacity=".6"/>
<circle cx="304" cy="104" r="2.4" fill="{BRIGHT}" opacity=".7"/>
<circle cx="348" cy="136" r="2" fill="{BRIGHT}" opacity=".55"/>

<!-- the sea -->
<path class="ln-faint" d="{waves_back}"/>
<path class="ln" d="{waves}"/>

<!-- the crown of water where it will land -->
<path class="ln-bright" d="M386 244 C380 226 374 214 368 206 M400 240 C400 220 400 206 398 194
     M416 244 C424 226 432 216 438 208"/>
<circle cx="364" cy="198" r="2.4" fill="{BRIGHT}" opacity=".75"/>
<circle cx="396" cy="186" r="2.4" fill="{BRIGHT}" opacity=".75"/>
<circle cx="442" cy="200" r="2.4" fill="{BRIGHT}" opacity=".75"/>
"""
    return svg(W, H, body, label=(
        "The empowered treasure vase, tied with five coloured cloths, arcing through the air "
        "into the waves of the sea"))


# ----------------------------------------------------------------------
# decorations — no labels, no framing, they sit directly in the prose
# ----------------------------------------------------------------------
def cloud_rule():
    """An auspicious-cloud divider: a flaming pearl between two runs of
    diminishing cloud curls. Drawn above each section heading."""
    W, H = 420, 46
    half, x = [], 148
    for s in (15, 11, 8):
        half.append(f'<path class="ln-thin" d="{curl(x, 27, s, turns=1.55)}"/>')
        x -= s * 2.9
    half.append('<path class="ln-faint" d="M160 27 L192 27"/>')
    half = "".join(half)
    body = f"""
<g>{half}</g>
<g transform="translate({W} 0) scale(-1 1)">{half}</g>
<circle cx="{W / 2}" cy="27" r="6" class="ln"/>
<path class="ln-thin" d="M{W / 2 - 4} 16 C{W / 2 - 1} 8 {W / 2 + 5} 9 {W / 2 + 3} 17"/>
"""
    return svg(W, H, body, label="")


def dragon_beneath():
    """The dragon stirring beneath a mirror-calm sea: a still waterline,
    rings of ripples, and the serpentine body passing below."""
    W, H = 440, 200
    # the body: a long sine wave, rising toward the ripples at its head end
    pts = []
    for i in range(61):
        t = i / 60
        x = 26 + t * 296
        y = 138 - math.sin(t * math.pi * 2.15) * 24 - t * 14
        pts.append((x, y))
    spine = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts)
    # dorsal fins along the crests
    fins = []
    for t in (0.16, 0.24, 0.55, 0.63, 0.71):
        i = int(t * 60)
        x, y = pts[i]
        fins.append(f'<path class="ln-faint" d="M{x:.0f} {y:.0f} L{x + 3:.0f} {y - 9:.0f} '
                    f'L{x + 8:.0f} {y - 1:.0f}"/>')
    hx, hy = pts[-1]
    body = f"""
<!-- the mirror-calm surface -->
<path class="ln" d="M10 58 C88 55 182 60 262 57 C334 54 396 58 430 56"/>
<path class="ln-faint" d="M60 70 L108 70 M330 68 L392 68"/>

<!-- the ripples where he nears the surface -->
<ellipse cx="{hx + 14:.0f}" cy="60" rx="11" ry="3.2" class="ln-thin" fill="none"/>
<ellipse cx="{hx + 14:.0f}" cy="61" rx="23" ry="6" class="ln-faint" fill="none"/>
<ellipse cx="{hx + 14:.0f}" cy="62" rx="37" ry="9" class="ln-faint" fill="none" opacity=".35"/>

<!-- the dragon below -->
<path class="ln" d="{spine}"/>
{''.join(fins)}
<!-- the head, turned up toward the light: brow, muzzle, open jaw -->
<g class="ln" fill="none">
  <path d="M{hx:.0f} {hy:.0f} C{hx + 4:.0f} {hy - 10:.0f} {hx + 6:.0f} {hy - 18:.0f} {hx + 12:.0f} {hy - 24:.0f}
       C{hx + 17:.0f} {hy - 29:.0f} {hx + 24:.0f} {hy - 30:.0f} {hx + 29:.0f} {hy - 27:.0f}"/>
  <path d="M{hx + 29:.0f} {hy - 27:.0f} C{hx + 27:.0f} {hy - 21:.0f} {hx + 23:.0f} {hy - 17:.0f} {hx + 18:.0f} {hy - 15:.0f}"/>
  <path d="M{hx + 18:.0f} {hy - 15:.0f} C{hx + 15:.0f} {hy - 11:.0f} {hx + 11:.0f} {hy - 8:.0f} {hx + 6:.0f} {hy - 7:.0f}"/>
</g>
<!-- horn swept back, and the whiskers -->
<path class="ln-thin" d="M{hx + 14:.0f} {hy - 27:.0f} C{hx + 9:.0f} {hy - 34:.0f} {hx + 2:.0f} {hy - 38:.0f} {hx - 6:.0f} {hy - 38:.0f}"/>
<path class="ln-thin" d="{curl(hx + 34, hy - 32, 6, turns=1.35)}"/>
<path class="ln-thin" d="{curl(hx + 33, hy - 13, 5, turns=1.35)}"/>
<circle cx="{hx + 17:.0f}" cy="{hy - 23:.0f}" r="1.9" fill="{BRIGHT}"/>
<!-- the pearl he watches, just under the ripples -->
<circle cx="{hx + 14:.0f}" cy="74" r="3.4" class="ln-thin" fill="none"/>
<circle cx="{hx + 14:.0f}" cy="74" r="1.2" fill="{BRIGHT}"/>
<!-- the tail fluke -->
<path class="ln-thin" d="M26 138 L13 129 M26 138 L14 147"/>
"""
    return svg(W, H, body, label="")


def water_stairs():
    """The staircase fashioned out of water, leading down from the waves
    into the gate of the Dragon King's Palace."""
    W, H = 400, 290
    # steps descending from the surface at the left to the gate at lower right
    d, x, y = [], 46, 76
    for _ in range(7):
        d.append(f'M{x} {y} L{x + 30} {y} L{x + 30} {y + 24}')
        x, y = x + 30, y + 24
    steps = f'<path class="ln" d="{" ".join(d)}"/>'
    # each tread ripples — it is made of water
    ripple = "".join(f'<path class="ln-faint" d="M{46 + i * 30 + 5} {76 + i * 24 + 5} '
                     f'C{46 + i * 30 + 12} {76 + i * 24 + 2} {46 + i * 30 + 19} {76 + i * 24 + 8} '
                     f'{46 + i * 30 + 25} {76 + i * 24 + 5}"/>' for i in range(7))
    waves = "".join(curl(x, 62 + (5 if i % 2 else 0), 24 + (i % 2) * 6)
                    for i, x in enumerate(range(-6, 410, 68)))
    gx, gy = 298, 250   # centre of the gate, at its threshold
    body = f"""
<!-- the surface of the sea -->
<path class="ln-faint" d="{waves}"/>

<!-- the staircase of water -->
{steps}
{ripple}

<!-- the palace gate: two upswept roofs over a pillared doorway -->
<g>
  <!-- upper roof, its eaves curling skyward -->
  <path class="ln-bright" d="M{gx - 40} {gy - 92} C{gx - 44} {gy - 86} {gx - 50} {gy - 82} {gx - 56} {gy - 81}
       C{gx - 44} {gy - 102} {gx - 20} {gy - 112} {gx} {gy - 112}
       C{gx + 20} {gy - 112} {gx + 44} {gy - 102} {gx + 56} {gy - 81}
       C{gx + 50} {gy - 82} {gx + 44} {gy - 86} {gx + 40} {gy - 92} Z"/>
  <!-- lower roof, wider -->
  <path class="ln" d="M{gx - 52} {gy - 62} C{gx - 57} {gy - 55} {gx - 64} {gy - 50} {gx - 72} {gy - 49}
       C{gx - 60} {gy - 68} {gx - 30} {gy - 77} {gx} {gy - 77}
       C{gx + 30} {gy - 77} {gx + 60} {gy - 68} {gx + 72} {gy - 49}
       C{gx + 64} {gy - 50} {gx + 57} {gy - 55} {gx + 52} {gy - 62} Z"/>
  <!-- the storey between the roofs -->
  <path class="ln-thin" d="M{gx - 34} {gy - 92} L{gx - 34} {gy - 77} M{gx + 34} {gy - 92} L{gx + 34} {gy - 77}"/>
  <!-- pillars and threshold -->
  <path class="ln" d="M{gx - 42} {gy - 49} L{gx - 42} {gy} M{gx + 42} {gy - 49} L{gx + 42} {gy}
       M{gx - 52} {gy} L{gx + 52} {gy}"/>
  <path class="ln-thin" d="M{gx - 14} {gy - 49} L{gx - 14} {gy} M{gx + 14} {gy - 49} L{gx + 14} {gy}"/>
  <!-- the doorway, glowing faintly -->
  <path class="ln-thin" d="M{gx - 14} {gy - 12} C{gx - 8} {gy - 20} {gx + 8} {gy - 20} {gx + 14} {gy - 12}"/>
  <!-- the pearl at the ridge -->
  <circle cx="{gx}" cy="{gy - 120}" r="4.4" class="ln-thin" fill="none"/>
  <circle cx="{gx}" cy="{gy - 120}" r="1.4" fill="{BRIGHT}"/>
</g>

<!-- pearls of light along the way down -->
<circle cx="118" cy="130" r="2" fill="{BRIGHT}" opacity=".7"/>
<circle cx="188" cy="182" r="2" fill="{BRIGHT}" opacity=".7"/>
<circle cx="240" cy="226" r="2" fill="{BRIGHT}" opacity=".7"/>
"""
    return svg(W, H, body, label="")


def shrine_vase():
    """The finished vase placed on the shrine, a stick of incense curling
    to either side."""
    W, H = 400, 250
    art, geo = vase(cx=200, top=44, s=0.148)
    ty = geo["bottom"]   # the table top carries the vase
    smoke = "".join(
        f'<path class="ln-faint" d="M{x} {ty - 14} C{x - 7} {ty - 34} {x + 7} {ty - 52} {x} {ty - 72} '
        f'C{x - 6} {ty - 88} {x + 5} {ty - 102} {x} {ty - 116}"/>'
        f'<path class="ln-thin" d="M{x} {ty - 2} L{x} {ty - 14}"/>'
        f'<circle cx="{x}" cy="{ty - 15}" r="1.8" fill="{BRIGHT}"/>'
        for x in (104, 296))
    body = f"""
{art}

<!-- incense to either side -->
{smoke}

<!-- the shrine table -->
<path class="ln-bright" d="M56 {ty:.0f} L344 {ty:.0f}"/>
<path class="ln" d="M64 {ty + 8:.0f} L336 {ty + 8:.0f} M84 {ty + 8:.0f} L84 {ty + 40:.0f}
     M316 {ty + 8:.0f} L316 {ty + 40:.0f}"/>
<path class="ln-thin" d="M84 {ty + 26:.0f} L316 {ty + 26:.0f}"/>
<!-- the valance hanging from the table edge -->
<path class="ln-faint" d="M120 {ty + 8:.0f} C124 {ty + 20:.0f} 136 {ty + 20:.0f} 140 {ty + 8:.0f}
     M180 {ty + 8:.0f} C184 {ty + 20:.0f} 196 {ty + 20:.0f} 200 {ty + 8:.0f}
     M240 {ty + 8:.0f} C244 {ty + 20:.0f} 256 {ty + 20:.0f} 260 {ty + 8:.0f}"/>
"""
    return svg(W, H, body, label="")


def jewel_rain():
    """For money and rain: a fall of jewels and coins into the waves."""
    W, H = 400, 230
    drops = [(60, 40, 9), (132, 96, 7), (196, 30, 11), (262, 84, 8), (330, 48, 9),
             (96, 140, 6), (298, 138, 7)]
    jewels = "".join(
        f'<path class="ln-thin" d="M{x} {y - s * 1.6:.0f} C{x + s} {y - s * 0.4:.0f} {x + s} {y + s * 0.7:.0f} {x} {y + s:.0f} '
        f'C{x - s} {y + s * 0.7:.0f} {x - s} {y - s * 0.4:.0f} {x} {y - s * 1.6:.0f} Z"/>'
        f'<circle cx="{x}" cy="{y - s * 1.9:.0f}" r="1.4" fill="{BRIGHT}"/>'
        for x, y, s in drops)
    coins = "".join(
        f'<g transform="translate({x} {y}) rotate({r})">'
        f'<circle r="10" class="ln-thin" fill="none"/>'
        f'<rect x="-3.4" y="-3.4" width="6.8" height="6.8" class="ln-faint" fill="none"/></g>'
        for x, y, r in ((160, 58, 12), (232, 128, -16), (356, 108, 8), (48, 112, -10)))
    rain = "".join(f'<path class="ln-faint" opacity=".4" d="M{x} {y} L{x - 3} {y + 22}"/>'
                   for x, y in ((84, 62), (118, 30), (176, 104), (214, 52), (250, 22),
                                (288, 76), (318, 20), (352, 60), (140, 150), (270, 160)))
    waves = "".join(curl(x, 208 + (6 if i % 2 else 0), 30 + (i % 3) * 6)
                    for i, x in enumerate(range(-8, 412, 66)))
    body = f"""
{rain}
{jewels}
{coins}
<path class="ln" d="{waves}"/>
"""
    return svg(W, H, body, label="")


if __name__ == "__main__":
    for name, maker in (("mudra.svg", mudra),
                        ("vase-preparation.svg", vase_preparation),
                        ("casting-the-vase.svg", casting),
                        ("deco-cloud-rule.svg", cloud_rule),
                        ("deco-dragon-beneath.svg", dragon_beneath),
                        ("deco-water-stairs.svg", water_stairs),
                        ("deco-shrine.svg", shrine_vase),
                        ("deco-jewel-rain.svg", jewel_rain)):
        out = maker()
        (ASSETS / name).write_text(out, encoding="utf-8")
        print(f"  {name}: {len(out) / 1024:.1f} KB")
