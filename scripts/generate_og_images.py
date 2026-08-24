#!/usr/bin/env python3
"""Render the social-sharing card, once per language.

A shared link is previewed with og:image, and one English card was being shown
for every language — a French reader saw a picture telling them to "READ IN
CHINESE · PINYIN · ENGLISH". Each language now gets its own card, with the
sutra's title and the reading line in that language.

The card is 1200x630 (the size Facebook, WhatsApp, X, LinkedIn and iMessage
all crop from), rendered by headless Chromium so the real fonts and the real
dragon line-art are used, then converted to JPEG with sips.

Run from the repo root:  python3 scripts/generate_og_images.py
"""
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ART = ROOT / "assets" / "dragon-hero.svg"

# Chrome, not Chromium: the Chromium build on this machine dies with SIGTRAP
# in headless mode. Chrome writes the screenshot and then hangs on shutdown
# instead of exiting, so the run below is killed on a timeout and judged by
# whether the file appeared.
CHROME = next((p for p in (
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
) if Path(p).exists()), None)

# One entry per language. `size` tunes the title only where a longer
# translation would otherwise take a fourth line and crowd the card.
CARDS = {
    "en": {
        "file": "og-image.jpg",
        "title": "The Sutra Spoken by the Buddha on the Sea Dragon King",
        "sub": "Read in Chinese · Pinyin · English",
        "size": 62,
    },
    "es": {
        "file": "og-image-es.jpg",
        "title": "El Sutra Pronunciado por el Buda sobre el Rey Dragón del Mar",
        "sub": "Leer en chino · pinyin · español",
        "size": 56,
    },
    "fr": {
        "file": "og-image-fr.jpg",
        "title": "Le Soutra prononcé par le Bouddha sur le Roi Dragon de la Mer",
        "sub": "Lire en chinois · pinyin · français",
        "size": 56,
    },
}

TEMPLATE = """<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@500;600&display=swap" rel="stylesheet">
<link href="https://fonts.googleapis.com/css2?family=LXGW+WenKai+TC:wght@400&display=swap" rel="stylesheet">
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  html, body {{ width: 1200px; height: 630px; overflow: hidden; }}
  body {{
    display: flex;
    align-items: center;
    background:
      radial-gradient(ellipse 70% 70% at 72% 45%, rgba(29,53,96,.6), transparent 62%),
      radial-gradient(ellipse 50% 45% at 15% 80%, rgba(18,35,64,.5), transparent 65%),
      linear-gradient(160deg, #060c17, #0a1424 55%, #070e1a);
    font-family: "Cormorant Garamond", serif;
    color: #f4dc96;
    position: relative;
  }}
  .frame {{
    position: absolute; inset: 26px;
    border: 1px solid rgba(217,178,95,.28);
    pointer-events: none;
  }}
  .frame::before, .frame::after {{
    content: ""; position: absolute; width: 26px; height: 26px;
    border: 2px solid #d9b25f;
  }}
  .frame::before {{ top: -1px; left: -1px; border-width: 2px 0 0 2px; }}
  .frame::after {{ bottom: -1px; right: -1px; border-width: 0 2px 2px 0; }}
  .left {{ width: 640px; padding: 0 0 0 88px; }}
  .zh {{
    font-family: "LXGW WenKai TC", serif;
    font-size: 40px;
    letter-spacing: .42em;
    color: #d9b25f;
    margin-bottom: 26px;
  }}
  h1 {{
    font-size: {size}px;
    font-weight: 500;
    line-height: 1.12;
    letter-spacing: .01em;
    text-shadow: 0 0 44px rgba(217,178,95,.35);
  }}
  .rule {{ width: 96px; height: 1px; background: linear-gradient(90deg, #d9b25f, transparent); margin: 30px 0 24px; }}
  .sub {{
    font-size: 23px;
    white-space: nowrap;
    color: #c9bfa6;
    letter-spacing: .16em;
    text-transform: uppercase;
  }}
  .art {{ position: absolute; right: -46px; top: 18px; width: 620px; opacity: .97; }}
  .art svg {{ width: 100%; height: auto; display: block; }}
  /* The card is a still, so every draw-on animation is jumped to its last
     frame rather than caught mid-stroke. */
  .art * {{
    animation-delay: -30s !important;
    animation-duration: 1ms !important;
    animation-iteration-count: 1 !important;
    animation-fill-mode: forwards !important;
  }}
</style>
</head>
<body>
  <div class="art">{art_svg}</div>
  <div class="frame"></div>
  <div class="left">
    <div class="zh">佛說海龍王經</div>
    <h1>{title}</h1>
    <div class="rule"></div>
    <div class="sub">{sub}</div>
  </div>
</body>
</html>
"""


def render(lang, card, tmp, art_svg):
    page = tmp / f"og-{lang}.html"
    page.write_text(TEMPLATE.format(lang=lang, art_svg=art_svg, **card), encoding="utf-8")
    png = tmp / f"og-{lang}.png"
    cmd = [
        CHROME, "--headless", "--disable-gpu", "--no-sandbox", "--no-first-run",
        "--no-default-browser-check", "--disable-extensions", "--hide-scrollbars",
        "--force-device-scale-factor=1", "--window-size=1200,630",
        # long enough for the webfonts and the dragon SVG to paint
        "--virtual-time-budget=8000",
        f"--screenshot={png}", f"--user-data-dir={tmp / ('profile-' + lang)}",
        page.as_uri(),
    ]
    try:
        subprocess.run(cmd, capture_output=True, timeout=40)
    except subprocess.TimeoutExpired:
        pass  # the screenshot is already written; only the exit hangs
    if not png.exists():
        raise SystemExit(f"{lang}: Chrome produced no screenshot")
    out = ROOT / "assets" / card["file"]
    subprocess.run(["sips", "-s", "format", "jpeg", "-s", "formatOptions", "82",
                    str(png), "--out", str(out)], check=True, capture_output=True)
    kb = out.stat().st_size / 1024
    dims = subprocess.run(["sips", "-g", "pixelWidth", "-g", "pixelHeight", str(out)],
                          capture_output=True, text=True).stdout.split()
    print(f"  {card['file']}: {dims[-3]}x{dims[-1]}, {kb:.0f} KB")


if __name__ == "__main__":
    if not CHROME:
        raise SystemExit("no Chromium or Chrome found to render with")
    assert ART.exists(), f"missing {ART}"
    tmp = Path(tempfile.mkdtemp(prefix="og-cards-"))
    try:
        art_svg = ART.read_text(encoding="utf-8")
        for lang, card in CARDS.items():
            render(lang, card, tmp, art_svg)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
