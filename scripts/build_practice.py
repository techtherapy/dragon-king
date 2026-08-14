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
        # house style: lowercase the generic "dharma"/"buddhahood",
        # keeping names such as "Dharma Protectors" and "Buddha Dharma"
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


def render(items):
    frags = []
    for kind, text in items:
        if kind == "h":
            frags.append(f'      <h2 class="article-sub reveal">{text}</h2>')
        else:
            frags.append(f'      <p class="reveal">{text}</p>')
    return "\n".join(frags)


def build():
    header, footer = chrome()
    part1 = paragraphs(P1, skip=3)   # title + two byline lines
    part2 = paragraphs(P2, skip=2)   # title + byline

    # the source transcript ends mid-sentence — mark it honestly
    kind, last = part2[-1]
    if last.endswith("the Bodhisattva"):
        part2[-1] = (kind, last + '&hellip; <span class="muted">[the recorded transcript ends here]</span>')

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
    margin: 2.6em 0 0.8em;
    padding-top: 1.4em;
    border-top: 1px solid var(--gold-ghost);
  }}
  .page-hero .credit {{
    display: block;
    margin-top: 0.6rem;
    font-size: 0.88em;
    font-style: italic;
    color: var(--muted);
  }}
  .article {{ max-width: var(--measure); }}
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
  .vision-figure {{ margin: 3rem auto; max-width: 460px; text-align: center; }}
  .vision-figure img {{ width: 100%; filter: drop-shadow(0 18px 50px rgba(3, 7, 14, 0.7)); }}
  .vision-figure figcaption {{ margin-top: 1.1rem; color: var(--muted); font-style: italic; font-size: 0.95rem; }}
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
{render(part1)}
    </article>
  </div>
</section>

<section class="flow-section">
  <div class="wrap">
    <p class="eyebrow reveal">Part Two · The Sadhana</p>
    <article class="article">
{render(part2)}
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
