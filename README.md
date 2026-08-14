# Dragon King Sutra — 佛說海龍王經

A static devotional website for the *Sutra Spoken by the Buddha on the Sea
Dragon King*, in the family of [vajrasutra.org](https://vajrasutra.org) and
[truebuddhasutra.org](https://truebuddhasutra.org).

Design language: **紺紙金泥** — gold ink on indigo paper, the format of
classical Buddhist manuscripts. All dragon artwork is original generated
SVG line-art in the style of a sutra frontispiece.

## Pages

| Page | Purpose |
|---|---|
| `index.html` | Hero (Buddha silhouette in halo above the dragon roundel, vertical title), teachings, chapter index |
| `read.html` | **Generated** — complete trilingual reader (20 chapters, 3,204 verse-lines) with chapter drawer, layer toggles (漢字/pinyin/English), progress bar, print stylesheet |
| `about.html` | About the sutra + full bilingual study reflection |
| `his-holiness-living-buddha-lian-sheng.html` | Biography of the root guru |
| `refuge.html` | How to take refuge (rite + three registration methods) |
| `treasure-vase-yoga.html` | **Generated** — the Dragon King Treasure Vase Yoga teaching (built by `scripts/build_practice.py` from `extra-content/`), with the vase-vision illustration |
| `treasure-vase-wishes.html` | Book 146 ch. 32 — Wishes in the Treasure Vase Practice (bilingual, with book cover) |
| `contact.html` | True Buddha School contact points |

## Regenerating generated files

```bash
# Hero artwork: dragon + Buddha (dragon-hero.svg), waves (waves.svg),
# and parallax sky layers (sky-stars.svg, clouds-far.svg, clouds-near.svg)
python3 scripts/generate_dragon.py

# Reader page (read.html) from the source sutra HTML
python3 scripts/build_reader.py

# Treasure Vase Yoga page from the transcripts in extra-content/
python3 scripts/build_practice.py
```

`read.html` is built from `Dragon king sutra hailongwang_complete.html`
(the source of truth for the sutra text — do not edit `read.html` by hand).

## Local preview

```bash
python3 -m http.server 8471
```

Then open <http://localhost:8471>. The site is fully static — deploy the
repo root to any static host (GitHub Pages, Netlify, Cloudflare Pages).

## Design spec

See `docs/superpowers/specs/2026-08-14-dragon-king-sutra-website-design.md`.
