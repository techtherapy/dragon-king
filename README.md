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

# SEO tags (canonical, Open Graph, JSON-LD), sitemap.xml and robots.txt
python3 scripts/add_seo.py
```

`scripts/add_seo.py` is idempotent and runs automatically as the first step of
`build_site.sh`, so generated pages never lose their tags. It reads each page's
existing `<title>` and `<meta name="description">` and never rewrites them.
The share image is rendered from `scripts/og-image.html` with headless Chrome:

```bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --headless=new --force-prefers-reduced-motion --window-size=1200,630 \
  --screenshot=assets/og-image.png --virtual-time-budget=9000 \
  "file://$PWD/scripts/og-image.html"
sips -s format jpeg -s formatOptions 88 assets/og-image.png --out assets/og-image.jpg
```

**Changing the domain:** edit `SITE` at the top of `scripts/add_seo.py` and
re-run it — canonical URLs, Open Graph URLs, JSON-LD and the sitemap all
derive from that one constant.

`read.html` is built from `Dragon king sutra hailongwang_complete.html`
(the source of truth for the sutra text — do not edit `read.html` by hand).

## Local preview

```bash
python3 -m http.server 8471
```

Then open <http://localhost:8471>.

## Deploying (Cloudflare Workers)

The repo holds both the site and its private sources (the original sutra
HTML, lecture transcripts, `extra-content/`, the generator scripts). Only the
site is published, because only `dist/` is uploaded:

| Cloudflare setting | Value |
|---|---|
| Build command | `bash scripts/build_site.sh` |
| Deploy command | `npx wrangler deploy` |

`wrangler.jsonc` declares `assets.directory = "./dist"` and no `main` script —
a static-asset-only Worker, so Cloudflare serves `dist/` directly and uploads
nothing else. (If you use the older Cloudflare **Pages** flow instead, there is
no deploy command: set build output directory = `dist`.)

`scripts/build_site.sh` copies the eight pages plus `css/`, `js/`, `assets/`
and `deploy/_headers` into `dist/`, then **fails the build** if anything
private (the source sutra HTML, `info.txt`, `extra-content/`, `scripts/`,
`docs/`) ever appears in the output. `dist/` is gitignored.

Build it locally exactly as Cloudflare does:

```bash
bash scripts/build_site.sh
cd dist && python3 -m http.server 8479
```

Note that a *public* GitHub repo still exposes the private sources on GitHub
itself, even though they are never served from the site's domain. To keep them
off the internet entirely, make the repo private — Cloudflare Pages deploys
from private repos just as well.

## Design spec

See `docs/superpowers/specs/2026-08-14-dragon-king-sutra-website-design.md`.
