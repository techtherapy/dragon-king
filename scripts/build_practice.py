#!/usr/bin/env python3
"""Build treasure-vase-yoga.html from the two lecture transcripts in
extra-content/. Header and footer are lifted from refuge.html so the
chrome never drifts from the rest of the site.

Run from the repo root:  python3 scripts/build_practice.py
"""
import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
P1 = ROOT / "extra-content" / "Dragon King Treasure Vase Yoga Part 1.txt"
P2 = ROOT / "extra-content" / "Dragon King Treasure Vase Yoga Part 2.txt"
OUT = ROOT / "treasure-vase-yoga.html"

HEADINGS = {
    "The Cause of the Dragon King Yoga",
    "The Third Person to go to the Dragon King's Palace",
    "The Secrets of Making a Wish with the Dragon King Yoga",
    "How To Prepare The Dragon King Treasure Vase",
    "The Procedure For The Dragon King Yoga",
    "The Results of The Dragon King Yoga",
}


def chrome():
    """Header/footer copied from refuge.html, with nav state adjusted."""
    src = (ROOT / "refuge.html").read_text()
    header = src[src.index('<header class="site-header">'):src.index("</header>") + len("</header>")]
    header = header.replace(' aria-current="page"', "")
    header = header.replace('<a href="treasure-vase-yoga.html">Practice</a>',
                            '<a href="treasure-vase-yoga.html" aria-current="page">Practice</a>')
    footer = src[src.index('<footer class="site-footer">'):src.index("</footer>") + len("</footer>")]
    return header, footer


def paragraphs(path, skip):
    """Transcript lines -> (kind, text) where kind is 'h' or 'p'."""
    out = []
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines()):
        if i < skip:
            continue
        t = line.strip()
        if not t:
            continue
        t = t.replace("Gastrodia(Rl0)", "Gastrodia")
        # house style: one word, as used everywhere else on the site
        t = t.replace("Grand Master", "Grandmaster")
        t = t.replace("Shakyamuni", "Sakyamuni")
        # house style: "buddhadharma" as one word, and lowercase the generic
        # "dharma"/"buddhahood", keeping names such as "Dharma Protectors"
        t = t.replace("Buddha Dharma", "buddhadharma")
        for _a, _b in (("to teach the Dharma", "to teach the dharma"),
                       ("as the Dharma currently", "as the dharma currently"),
                       ("great Dharma masters", "great dharma masters"),
                       ("this Dharma teaching", "this dharma teaching"),
                       ("attain Buddhahood", "attain buddhahood")):
            t = t.replace(_a, _b)
        if t in HEADINGS:
            out.append(("h", t))
        else:
            out.append(("p", html.escape(t, quote=False)))
    return out


# Illustrations, each placed after the paragraph that introduces it. The key
# is a distinctive phrase from the transcript; a missing key is an error, so a
# reworded transcript can never silently drop a figure.
FIGURES = [
    ("The middle and index fingers of both hands cross", "mudra.svg",
     "手印 · The mudra: the index and middle fingers of both hands cross to form 井",
     "compact"),
    ("Together, these five herbs represent the body of the Dragon", "vase-preparation.svg",
     "寶瓶 · The five herbs are layered as the five chakras, sealed with a copper coin "
     "and tied with five coloured cloths",
     "tall"),
    ("throw this vase up in the air and let it drop into the ocean", "casting-the-vase.svg",
     "抛瓶入海 · Casting the empowered vase into the sea",
     "wide"),
]

# Decorations, placed the same way: after the paragraph whose phrase they
# illustrate. Purely ornamental — no caption, hidden from screen readers.
DECOS = [
    ("just like a mirror, without any waves", "deco-dragon-beneath.svg"),
    ("a staircase was fashioned out of water", "deco-water-stairs.svg"),
    ("before the statues of the-Buddhas and Bodhisattvas on our shrine",
     "deco-shrine.svg"),
    ("For money and rain, just the five kinds of herbs will do", "deco-jewel-rain.svg"),
]

VIEWBOX = re.compile(r'viewBox="0 0 ([\d.]+) ([\d.]+)"')


def intrinsic(src):
    """Width/height from the SVG's own viewBox. Without these attributes the
    img has no intrinsic size, so its box is zero-high until the file loads —
    which stalls loading="lazy" and shifts the layout when it finally does."""
    m = VIEWBOX.search((ROOT / "assets" / src).read_text(encoding="utf-8"))
    assert m, f"no viewBox in {src}"
    return int(float(m.group(1))), int(float(m.group(2)))


def figure_html(src, caption, size):
    w, h = intrinsic(src)
    return (f'      <figure class="inline-figure {size} reveal">\n'
            f'        <img src="assets/{src}" width="{w}" height="{h}"'
            f' alt="{caption.split(chr(183), 1)[-1].strip()}" loading="lazy">\n'
            f'        <figcaption>{caption}</figcaption>\n'
            f'      </figure>')


def deco_html(src):
    w, h = intrinsic(src)
    return (f'      <div class="deco-figure reveal" aria-hidden="true">\n'
            f'        <img src="assets/{src}" width="{w}" height="{h}" alt="" loading="lazy">\n'
            f'      </div>')


def rule_html():
    w, h = intrinsic("deco-cloud-rule.svg")
    return (f'      <div class="h-rule reveal" aria-hidden="true">'
            f'<img src="assets/deco-cloud-rule.svg" width="{w}" height="{h}" alt="" '
            f'loading="lazy"></div>')


def render(items, figures_used=None):
    frags = []
    for kind, text in items:
        if kind == "h":
            frags.append(rule_html())
            frags.append(f'      <h2 class="article-sub reveal">{text}</h2>')
        else:
            frags.append(f'      <p class="reveal">{text}</p>')
            for key, src, caption, size in FIGURES:
                if key in text:
                    frags.append(figure_html(src, caption, size))
                    if figures_used is not None:
                        figures_used.add(key)
            for key, src in DECOS:
                if key in text:
                    frags.append(deco_html(src))
                    if figures_used is not None:
                        figures_used.add(key)
    return "\n".join(frags)


def build():
    header, footer = chrome()
    part1 = paragraphs(P1, skip=3)   # title + two byline lines
    part2 = paragraphs(P2, skip=2)   # title + byline

    # the source transcript ends mid-sentence — mark it honestly
    kind, last = part2[-1]
    if last.endswith("the Bodhisattva"):
        part2[-1] = (kind, last + '&hellip; <span class="muted">[the recorded transcript ends here]</span>')

    used = set()
    part1_html, part2_html = render(part1, used), render(part2, used)
    missing = [k for k, *_ in FIGURES + DECOS if k not in used]
    if missing:
        raise SystemExit("figure anchor not found in the transcript: " + "; ".join(missing))

    page = f"""<!DOCTYPE html>
<html lang="en" class="no-js">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>The Dragon King Treasure Vase Yoga — Dragon King Sutra</title>
<meta name="description" content="The Dragon King Treasure Vase Yoga (龍王寶瓶法), taught by Grandmaster Lu in Hong Kong, 1990 — the preparation of the treasure vase, the mudra, mantra and visualization, and the casting of the vase into the sea.">
<link rel="icon" type="image/svg+xml" href="assets/favicon.svg">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;1,400&family=EB+Garamond:ital,wght@0,400;0,500;1,400&display=swap" rel="stylesheet">
<link href="https://fonts.googleapis.com/css2?family=LXGW+WenKai+TC:wght@400;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="css/style.css">
<style>
  .article-sub {{
    font-size: clamp(1.4rem, 2.8vw, 1.9rem);
    margin: 0.3em 0 0.8em;   /* the cloud rule above carries the spacing */
  }}
  /* auspicious-cloud rule above each section heading */
  .h-rule {{ clear: right; margin: 3.4em 0 1.1em; }}
  .h-rule img {{ width: min(64%, 300px); height: auto; opacity: 0.8; display: block; }}
  .page-hero .credit {{
    display: block;
    margin-top: 0.6rem;
    font-size: 0.88em;
    font-style: italic;
    color: var(--muted);
  }}
  .article {{ max-width: var(--measure); }}
  /* a floated figure on the last paragraph must not escape the article */
  .article::after {{ content: ""; display: block; clear: both; }}
  .article p {{ margin: 0 0 1.25em; color: var(--cream-dim); }}
  .notice {{
    border: 1px solid rgba(217, 92, 66, 0.45);
    background: linear-gradient(160deg, rgba(184, 69, 47, 0.12), rgba(13, 25, 48, 0.4));
    padding: 1.8rem 2rem;
    display: flex;
    gap: 1.4rem;
    align-items: flex-start;
    margin: 2.4rem 0;
  }}
  .notice .seal {{ flex: none; }}
  .notice h3 {{ margin-bottom: 0.4rem; font-size: 1.25rem; }}
  .notice p {{ margin: 0; color: var(--cream-dim); }}
  /* Illustrations anchored to the passage they explain: inline in the column
     on a phone, out in the right-hand margin on a wide screen. Either way
     they carry .reveal, so they fade in as the reader arrives at them.
     No frame, no fill, no shading — the drawings sit directly on the page. */
  .inline-figure {{
    margin: 2.8rem auto;
    text-align: center;
  }}
  .inline-figure img {{ margin: 0 auto; height: auto; }}
  .inline-figure.compact img {{ width: min(100%, 330px); }}
  .inline-figure.tall img {{ width: min(100%, 290px); }}
  .inline-figure.wide img {{ width: min(100%, 440px); }}
  .inline-figure figcaption {{
    margin-top: 1rem;
    color: var(--muted);
    font-style: italic;
    font-size: 1.12rem;
    max-width: 46ch;
    margin-inline: auto;
  }}
  /* frameless decorations, anchored the same way */
  .deco-figure {{ margin: 2.6rem auto; text-align: center; }}
  .deco-figure img {{ width: min(100%, 360px); height: auto; margin: 0 auto; opacity: 0.92; }}
  @media (min-width: 1120px) {{
    /* Float figures and decorations out into the gutter. The negative right
       margin cancels the float's own width, so the line boxes beside it are
       not shortened and the prose keeps its full measure instead of wrapping
       round it. */
    .inline-figure,
    .deco-figure {{
      --fig: clamp(248px, 24vw, 320px);
      float: right;
      clear: right;
      width: var(--fig);
      margin: -2.5rem 0 2.2rem 2.4rem;
      margin-right: calc(-1 * (var(--fig) + 2.6rem));
    }}
    .inline-figure img,
    .inline-figure.compact img,
    .inline-figure.tall img,
    .inline-figure.wide img,
    .deco-figure img {{ width: 100%; }}
    .inline-figure figcaption {{ font-size: 1rem; max-width: none; margin-top: 0.8rem; }}
  }}
  .vision-figure {{ margin: 3rem auto; max-width: 460px; text-align: center; }}
  .vision-figure img {{ width: 100%; filter: drop-shadow(0 18px 50px rgba(3, 7, 14, 0.7)); }}
  .vision-figure figcaption {{ margin-top: 1.1rem; color: var(--muted); font-style: italic; font-size: 1.12rem; }}
  .glance {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
    gap: 1.1rem;
    margin: 2.4rem 0 0;
  }}
  .glance .g {{
    border: 1px solid var(--gold-ghost);
    background: rgba(15, 31, 56, 0.4);
    padding: 1.3rem 1.2rem;
    text-align: center;
  }}
  .glance .g .k {{
    font-family: var(--font-display);
    letter-spacing: 0.3em;
    text-transform: uppercase;
    font-size: 0.72rem;
    color: var(--gold);
    display: block;
    margin-bottom: 0.5rem;
  }}
  .glance .g .v {{ color: var(--cream); font-size: 1.05rem; }}
  .glance .g .v.tc {{ font-size: 1.6rem; color: var(--gold-bright); }}
</style>
</head>
<body>

{header}

<main>

<section class="page-hero">
  <div class="wrap">
    <p class="eyebrow center reveal">Practice · 龍王寶瓶法</p>
    <h1 class="reveal">The Dragon King Treasure Vase Yoga<span class="tc-title" lang="zh-Hant">龍王寶瓶之瑜伽</span></h1>
    <p class="lede reveal">A teaching by Grandmaster Lu — Hong Kong, February 4, 1990.<span class="credit">Translated by Janny Chow.</span></p>
  </div>
</section>

<section class="flow-section">
  <div class="wrap">
    <div class="notice reveal">
      <span class="seal small" aria-hidden="true" lang="zh-Hant">戒</span>
      <div>
        <h3>Empowerment is required before practising</h3>
        <p>To perform the Dragon King Treasure Vase Yoga, one must first <a href="refuge.html">take refuge</a> in His Holiness Living Buddha Lian Sheng, and then request the empowerment for this practice from His Holiness or an authorised True Buddha School master. Until then, please read for inspiration only.</p>
      </div>
    </div>

    <figure class="vision-figure reveal">
      <img src="assets/vase-vision.svg" alt="The visualization of the practice: from the sealed treasure vase a dragon rises and transforms into the Five Dhyani Buddhas, whose light pours back down upon the vase" loading="lazy">
      <figcaption lang="zh-Hant">寶瓶化龍，龍化五佛，五佛放光加持寶瓶<br><span lang="en" style="font-style:italic">The vase becomes the Dragon; the Dragon becomes the Five Buddhas; their light blesses the vase.</span></figcaption>
    </figure>

    <div class="glance reveal">
      <div class="g"><span class="k">Mudra</span><span class="v tc" lang="zh-Hant">井</span><span class="v" style="display:block;margin-top:.3rem;font-size:.9rem;color:var(--muted)">middle and index fingers of both hands crossed</span></div>
      <div class="g"><span class="k">Mantra</span><span class="v" style="font-style:italic">Namo Sam-man-doh,<br>moo-toh-nam,<br>wah-ri-la, men</span></div>
      <div class="g"><span class="k">Recitation</span><span class="v">108 times,<br>seven consecutive days</span></div>
      <div class="g"><span class="k">Completion</span><span class="v">the vase is cast<br>into the sea</span></div>
    </div>
  </div>
</section>

<section class="flow-section">
  <div class="wrap">
    <p class="eyebrow reveal">Part One · The Teaching</p>
    <article class="article">
{part1_html}
    </article>
  </div>
</section>

<section class="flow-section">
  <div class="wrap">
    <p class="eyebrow reveal">Part Two · The Sadhana</p>
    <article class="article">
{part2_html}
    </article>
  </div>
</section>

<section class="flow-section">
  <div class="wrap center">
    <div class="prose reveal" style="margin:0 auto">
      <p class="zh" lang="zh-Hant">先以欲勾之，再令入佛智。</p>
      <p class="en">First use desire to draw them in; then lead them into the wisdom of the Buddha.</p>
    </div>
    <div class="btn-row reveal" style="justify-content:center; margin-top:2.2rem">
      <a class="btn btn-solid" href="refuge.html">Take Refuge</a>
      <a class="btn" href="treasure-vase-wishes.html">Wishes in the Treasure Vase</a>
    </div>
  </div>
</section>

</main>

{footer}

<script src="js/main.js"></script>
</body>
</html>
"""
    OUT.write_text(page, encoding="utf-8")
    print(f"treasure-vase-yoga.html written: {len(page) / 1024:.0f} KB")


if __name__ == "__main__":
    build()
