#!/usr/bin/env python3
"""Generate the Treasure Vase Yoga illustrations.

Three figures, each anchored to a passage of the teaching by
scripts/build_practice.py:

  mudra.svg            the 井 mudra — index and middle fingers of both
                       hands crossed
  vase-preparation.svg cutaway of the sealed vase: five herbs as the five
                       chakras, copper-coin seal, five coloured cloths
  casting-the-vase.svg the finished vase cast into the sea

House style throughout: fine gold line-art on deep indigo (紺紙金泥).
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
  <linearGradient id="skin" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0%" stop-color="#1c3358"/><stop offset="100%" stop-color="#101f39"/>
  </linearGradient>
  <linearGradient id="vaseBody" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0%" stop-color="#1d3560"/><stop offset="60%" stop-color="#132443"/>
    <stop offset="100%" stop-color="#0d1930"/>
  </linearGradient>
  <radialGradient id="glow">
    <stop offset="0%" stop-color="{BRIGHT}" stop-opacity=".34"/>
    <stop offset="60%" stop-color="{GOLD}" stop-opacity=".10"/>
    <stop offset="100%" stop-color="{GOLD}" stop-opacity="0"/>
  </radialGradient>
  <linearGradient id="coin" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0%" stop-color="{BRIGHT}"/><stop offset="100%" stop-color="#a8814a"/>
  </linearGradient>
"""

BASE_CSS = f"""
  .ln {{ fill:none; stroke:{GOLD}; stroke-width:2; stroke-linecap:round; stroke-linejoin:round; }}
  .ln-bright {{ fill:none; stroke:{BRIGHT}; stroke-width:2.2; stroke-linecap:round; stroke-linejoin:round; }}
  .ln-thin {{ fill:none; stroke:{GOLD}; stroke-width:1.2; stroke-linecap:round; opacity:.75; }}
  .ln-faint {{ fill:none; stroke:{DIM}; stroke-width:1; opacity:.55; }}
  .fill-ink {{ fill:url(#skin); stroke:{BRIGHT}; stroke-width:2; stroke-linejoin:round; }}
  .label {{ font-family:"Cormorant Garamond",Georgia,serif; fill:#c9bfa6; font-size:15px; }}
  .label-zh {{ font-family:"LXGW WenKai TC","Kaiti TC",serif; fill:{GOLD}; font-size:16px; letter-spacing:.12em; }}
  .cap {{ font-family:"Cormorant Garamond",Georgia,serif; fill:{GOLD}; font-size:14px;
          letter-spacing:.28em; text-transform:uppercase; }}
"""


def svg(w, h, body, extra_css="", label=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" role="img"'
            f' aria-label="{label}">\n<style>{BASE_CSS}{extra_css}</style>\n'
            f'<defs>{DEFS}</defs>\n{body}\n</svg>\n')


# ----------------------------------------------------------------------
# 1. the 井 mudra
# ----------------------------------------------------------------------
def finger(x1, y1, x2, y2, w1, w2):
    """A tapered finger from (x1,y1) to (x2,y2) with rounded tip."""
    dx, dy = x2 - x1, y2 - y1
    L = math.hypot(dx, dy) or 1
    ux, uy = dx / L, dy / L
    nx, ny = -uy, ux
    def p(t, w):
        return (x1 + ux * L * t + nx * w, y1 + uy * L * t + ny * w)
    a, b = p(0, w1), p(0, -w1)
    c, d = p(1, w2), p(1, -w2)
    tipx, tipy = x2 + ux * w2 * 1.15, y2 + uy * w2 * 1.15
    return (f'M{a[0]:.1f} {a[1]:.1f} L{c[0]:.1f} {c[1]:.1f} '
            f'Q{tipx:.1f} {tipy:.1f} {d[0]:.1f} {d[1]:.1f} L{b[0]:.1f} {b[1]:.1f} Z')


def _nail(x, y, ux, uy, w):
    """A small nail arc just behind a fingertip."""
    nx, ny = -uy, ux
    ax, ay = x - ux * w * 1.5 + nx * w * 0.66, y - uy * w * 1.5 + ny * w * 0.66
    bx, by = x - ux * w * 1.5 - nx * w * 0.66, y - uy * w * 1.5 - ny * w * 0.66
    cx, cy = x - ux * w * 0.15, y - uy * w * 0.15
    return f'M{ax:.1f} {ay:.1f} Q{cx:.1f} {cy:.1f} {bx:.1f} {by:.1f}'


def _knuckle(x1, y1, x2, y2, t, w):
    """A crease line across a finger at position t along it."""
    ux, uy = x2 - x1, y2 - y1
    L = math.hypot(ux, uy) or 1
    ux, uy = ux / L, uy / L
    nx, ny = -uy, ux
    px, py = x1 + (x2 - x1) * t, y1 + (y2 - y1) * t
    return (f'M{px + nx * w * 0.8:.1f} {py + ny * w * 0.8:.1f} '
            f'Q{px + ux * w * 0.5:.1f} {py + uy * w * 0.5:.1f} '
            f'{px - nx * w * 0.8:.1f} {py - ny * w * 0.8:.1f}')


def mudra():
    """Deliberately diagrammatic: four tapered fingers crossing into 井, each
    hand reduced to a palm and wrist. Anatomical realism would sit badly
    beside the rest of the line-art, and reads worse at this size."""
    W, H = 560, 430

    # right hand → the two uprights;  left hand → the two crossbars
    ups = [(304, 318, 262, 96), (356, 318, 318, 96)]
    across = [(150, 214, 458, 180), (150, 268, 458, 236)]

    parts = []
    for x1, y1, x2, y2 in ups + across:
        L = math.hypot(x2 - x1, y2 - y1)
        ux, uy = (x2 - x1) / L, (y2 - y1) / L
        parts.append(f'<path class="fill-ink" d="{finger(x1, y1, x2, y2, 16, 12.5)}"/>')
        parts.append(f'<path class="ln-thin" d="{_knuckle(x1, y1, x2, y2, 0.34, 14)}"/>')
        parts.append(f'<path class="ln-thin" d="{_knuckle(x1, y1, x2, y2, 0.66, 13)}"/>')
        parts.append(f'<path class="ln-thin" d="{_nail(x2, y2, ux, uy, 12.5)}"/>')
    fingers = "\n  ".join(parts)

    body = f"""
<circle cx="290" cy="208" r="188" fill="url(#glow)"/>

<!-- the character the hands imitate -->
<g opacity=".11">
  <path class="ln" stroke-width="11" d="M236 90 L216 330 M340 90 L320 330 M118 176 L470 150 M118 252 L470 226"/>
</g>

<!-- LEFT HAND: wrist in from the edge, palm, two fingers laid across -->
<g>
  <path class="fill-ink" d="M18 196 L96 190 C118 188 132 202 132 224 L132 264
       C132 286 118 300 96 298 L18 292 C10 291 6 286 6 278 L6 210 C6 202 10 197 18 196 Z"/>
  <path class="ln-thin" d="M40 196 L40 292 M64 236 C84 230 106 230 124 236"/>
</g>

<!-- RIGHT HAND: wrist up from below, palm, two fingers rising -->
<g>
  <path class="fill-ink" d="M292 424 L292 350 C292 328 306 314 328 314 L368 314
       C390 314 404 328 402 350 L402 424 C402 428 398 430 392 430 L302 430
       C296 430 292 428 292 424 Z"/>
  <path class="ln-thin" d="M292 400 L402 400 M334 352 C328 372 328 392 334 408"/>
</g>

  {fingers}

<!-- where the four fingers cross -->
<circle cx="245" cy="197" r="5" fill="{BRIGHT}"/>
<circle cx="301" cy="191" r="5" fill="{BRIGHT}"/>
<circle cx="254" cy="253" r="5" fill="{BRIGHT}"/>
<circle cx="310" cy="247" r="5" fill="{BRIGHT}"/>

<text class="label-zh" x="506" y="118" font-size="44" text-anchor="middle">井</text>
<text class="label" x="506" y="142" text-anchor="middle" font-size="13">jǐng</text>
"""
    return svg(W, H, body, label=(
        "The mudra of the Dragon King Yoga: the index and middle fingers of both hands "
        "crossed to form the lattice of the character 井"))


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
CLOTHS = [("#b8452f", -34), ("#5b8c5a", -17), ("#4a6fa5", 0), ("#e8e0cc", 17), ("#d9b25f", 34)]


def vase_preparation():
    W, H = 620, 486
    # vase silhouette: mouth, neck, shoulder, belly, foot
    vase = ("M232 150 L232 132 C232 126 288 126 288 132 L288 150 "
            "C288 158 300 164 300 172 L300 196 "
            "C346 214 372 262 372 322 C372 396 330 446 260 446 "
            "C190 446 148 396 148 322 C148 262 174 214 220 196 "
            "L220 172 C220 164 232 158 232 150 Z")

    # five bands inside the belly
    bands, labels, leaders = [], [], []
    tops = [214, 260, 302, 344, 386]
    for i, ((zh, en, herb, herb_zh, col), y) in enumerate(zip(LAYERS, tops)):
        h = 42 if i else 46
        bands.append(
            f'<rect x="164" y="{y}" width="192" height="{h - 6}" rx="4" '
            f'fill="{col}" opacity=".17"/>'
            f'<path class="ln-thin" d="M162 {y + h - 6} L358 {y + h - 6}"/>')
        # herb granules
        for k in range(7):
            cx = 182 + k * 26 + (9 if i % 2 else 0)
            cy = y + 14 + (7 if k % 2 else 0)
            bands.append(f'<circle cx="{cx}" cy="{cy}" r="3.1" fill="{col}" opacity=".62"/>')
        ly = y + (h - 6) / 2
        leaders.append(f'<path class="ln-faint" d="M358 {ly:.0f} L430 {ly:.0f}"/>'
                       f'<circle cx="430" cy="{ly:.0f}" r="2.6" fill="{GOLD}"/>')
        labels.append(
            f'<text class="label-zh" x="442" y="{ly - 3:.0f}">{zh}</text>'
            f'<text class="label" x="442" y="{ly + 15:.0f}">{en} · {herb}</text>')

    cloths = "".join(
        f'<g transform="translate(260 150) rotate({rot})">'
        f'<path d="M-9 0 C-15 26 -10 54 4 72 C13 52 11 24 8 0 Z" fill="{col}" opacity=".85" '
        f'stroke="{INK}" stroke-width="1"/></g>'
        for col, rot in CLOTHS)

    body = f"""
<circle cx="260" cy="300" r="228" fill="url(#glow)"/>

<!-- the vase -->
<path d="{vase}" fill="url(#vaseBody)" stroke="{BRIGHT}" stroke-width="2.4" stroke-linejoin="round"/>
<path class="ln-thin" d="M220 196 C244 188 276 188 300 196"/>
<path class="ln-thin" d="M232 150 C248 145 272 145 288 150"/>

<!-- herb layers -->
{''.join(bands)}

<!-- copper coin sealing the mouth -->
<g transform="translate(260 132)">
  <ellipse cx="0" cy="0" rx="30" ry="9" fill="url(#coin)" stroke="{BRIGHT}" stroke-width="1.4"/>
  <rect x="-5" y="-3" width="10" height="6" fill="{INK}" stroke="{BRIGHT}" stroke-width="1"/>
</g>

<!-- five coloured cloths tied at the neck -->
{cloths}
<path class="ln-bright" d="M228 152 C244 162 276 162 292 152"/>

<!-- leaders and labels -->
{''.join(leaders)}
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
    W, H = 620, 330
    waves = "".join(curl(x, 300 + (8 if i % 2 else 0), 40 + (i % 3) * 9)
                    for i, x in enumerate(range(-10, 660, 78)))
    waves_back = "".join(curl(x, 274, 30) for x in range(20, 660, 96))

    # the arc the vase travels
    arc = "M112 236 C210 96 400 84 520 210"
    small_vase = ("M-13 -26 L-13 -34 C-13 -37 13 -37 13 -34 L13 -26 "
                  "C13 -22 18 -20 18 -16 C30 -8 36 8 36 24 C36 44 22 56 0 56 "
                  "C-22 56 -36 44 -36 24 C-36 8 -30 -8 -18 -16 C-18 -20 -13 -22 -13 -26 Z")
    cloth = "".join(
        f'<g transform="rotate({rot})"><path d="M-4 -34 C-7 -20 -5 -6 2 4 C7 -6 6 -20 4 -34 Z" '
        f'fill="{col}" opacity=".85"/></g>' for col, rot in CLOTHS)

    body = f"""
<circle cx="300" cy="180" r="210" fill="url(#glow)"/>

<!-- flight path -->
<path class="ln-faint" stroke-dasharray="5 9" d="{arc}"/>

<!-- the vase, mid-flight -->
<g transform="translate(300 104) rotate(24)">
  <path d="{small_vase}" fill="url(#vaseBody)" stroke="{BRIGHT}" stroke-width="2"/>
  <g transform="translate(0 -30)">{cloth}</g>
  <ellipse cx="0" cy="-34" rx="14" ry="4.5" fill="url(#coin)" stroke="{BRIGHT}" stroke-width="1"/>
</g>

<!-- sparks trailing -->
<circle cx="196" cy="150" r="2.6" fill="{BRIGHT}" opacity=".8"/>
<circle cx="236" cy="126" r="2" fill="{BRIGHT}" opacity=".6"/>
<circle cx="392" cy="120" r="2.4" fill="{BRIGHT}" opacity=".7"/>
<circle cx="446" cy="150" r="2" fill="{BRIGHT}" opacity=".55"/>

<!-- the sea -->
<path class="ln-faint" d="{waves_back}"/>
<path class="ln" d="{waves}"/>

<!-- the splash where it will land -->
<path class="ln-bright" d="M520 214 C512 232 506 246 508 260 M520 214 C532 230 542 242 542 258
     M520 214 C520 236 520 250 522 264"/>
<circle cx="520" cy="212" r="5" fill="{BRIGHT}" opacity=".9"/>

"""
    return svg(W, H, body, label=(
        "The empowered treasure vase, tied with five coloured cloths, arcing through the air "
        "into the waves of the sea"))


if __name__ == "__main__":
    for name, maker in (("mudra.svg", mudra),
                        ("vase-preparation.svg", vase_preparation),
                        ("casting-the-vase.svg", casting)):
        out = maker()
        (ASSETS / name).write_text(out, encoding="utf-8")
        print(f"  {name}: {len(out) / 1024:.1f} KB")
