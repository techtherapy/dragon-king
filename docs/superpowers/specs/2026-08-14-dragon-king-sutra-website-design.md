# Dragon King Sutra Website — Design

**Date:** 2026-08-14
**Status:** Approved autonomously (session ran unattended; user's brief was specific — decisions documented here for review)

## Goal

A beautifully designed, extremely visually impressive static website for the
《佛說海龍王經》 *Sutra Spoken by the Buddha on the Sea Dragon King*, in the same
family as vajrasutra.org and truebuddhasutra.org, with original dragon artwork.

## Source material (in repo)

- `Dragon king sutra hailongwang_complete.html` — complete trilingual sutra
  (Traditional Chinese / pinyin / English), 4 volumes, 20 chapters, ~913 KB.
  Well-structured: `.block > .prow > .hanzi/.pinyin/.english`, chapter anchors
  `#ch01…#ch20`, title block, colophon (translated by Dharmaraksa, Western Jin).
- `info.txt` — bilingual study reflection dated 2026-08-08: origins of the
  dragon clan, the Three Burning Sufferings, the Guru Buddha's praise,
  translation characteristics, summary. Feeds the About page + home highlights.

## Approach decision

**Chosen: plain static HTML/CSS/JS, no build toolchain.**
Six hand-written pages + one Python script (`scripts/build_reader.py`) that
transforms the source sutra HTML into the styled reader page (a hand-written
1 MB page is impractical; everything else is hand-crafted).

Rejected: Eleventy/Astro (adds Node toolchain for 6 pages), React/Next
(interactive framework for fully static content). Static files deploy directly
to GitHub Pages/Netlify and outlive any toolchain.

## Visual direction — 紺紙金泥 (gold ink on indigo paper)

Classical Buddhist manuscripts were copied in gold ink on indigo-dyed paper.
The site commits fully to this: deep abyssal indigo (which doubles as the Sea
Dragon King's ocean) with luminous gold, jade-aqua water accents, and
vermillion seal-stamp reds.

- **Palette (CSS variables):** abyss `#080f1c` → indigo layers `#0d1930`,
  `#122340`; gold `#d9b25f` / bright `#f2d78c` / dim `#8a6f3a`;
  jade-aqua `#7fd0bd` (pinyin, links); vermillion `#c0392b` (seals);
  cream `#ece2cc` (English body text).
- **Typography:** Cormorant Garamond (display) + EB Garamond (body) for Latin;
  Noto Serif TC for Traditional Chinese; loaded from Google Fonts with serif
  fallbacks. Letterspaced small-caps labels.
- **Signature moves:**
  - Full-viewport hero: hand-drawn SVG golden dragon coiling around a glowing
    flaming pearl, layered auspicious clouds, curling gold wave band at the
    base, drifting gold dust particles, gentle parallax.
  - Vertical Traditional-Chinese title (`writing-mode: vertical-rl`) like a
    classical scroll label.
  - Vermillion seal stamps (方印) as decorative accents.
  - Gold wave-motif section dividers; scroll-reveal animations
    (IntersectionObserver); `prefers-reduced-motion` respected throughout.

## Pages

| File | Content |
|---|---|
| `index.html` | Hero dragon scene; bilingual introduction (from info.txt); highlight cards (dragon-clan origins, Three Burning Sufferings, harmonizing the Eight Classes); Grandmaster's praise quote band; benefits of recitation; 20-chapter overview grid linking into the reader; refuge CTA. |
| `read.html` | Generated full trilingual reader: sticky chapter drawer (20 chapters), reading progress bar, toggles to show/hide 漢字 / pinyin / English layers, print stylesheet. Gold-on-indigo text mirrors the manuscript concept. |
| `about.html` | About the sutra + the full bilingual study reflection from info.txt, structured with section navigation; translation history (Dharmaraksa, Western Jin). |
| `his-holiness-living-buddha-lian-sheng.html` | Original-prose biography from public facts: b. 1945 Taiwan, awakening at 26, four Tibetan lineages, 1986 ordination, True Buddha School (Seattle), 300+ temples, ~300 books, millions of students. |
| `refuge.html` | Meaning of refuge; Fourfold Refuge mantra; three methods (online / written / in person); True Buddha Foundation address; donation basis. |
| `contact.html` | True Buddha Foundation address + official channels (TBSN etc.). |

All page copy is written fresh; the reference sites are used for structure and
facts only (no verbatim text). Sutra text and info.txt are the user's own files.

## Shared chrome

- **Header:** dragon-pearl SVG mark + "Dragon King Sutra" wordmark; nav: About,
  Read, Living Buddha Lian Sheng, Take Refuge, Contact. Mobile hamburger.
- **Footer (mirrors reference-site families):**
  - *The Sutra:* About · Read · Study Reflection · Contact Us
  - *Community:* His Holiness Living Buddha Lian Sheng · Take Refuge · Contact
  - *Facebook:* Official (syltbsnenglish) · Discussion (groups/tbsenglish) · Vajra Lotsawas
  - *Related:* True Buddha Sutra · Vajra Sutra · High King Sutra · Surangama
    Sutra · Drashi Lhamo · TBSN.org · TBBoyeh · Yifu Publications · Sheng-Yen Lu Foundation

## Structure

```
index.html  read.html  about.html
his-holiness-living-buddha-lian-sheng.html  refuge.html  contact.html
css/style.css   css/reader.css
js/main.js      js/reader.js
assets/favicon.svg (hero art inlined as SVG in pages)
scripts/build_reader.py   (source HTML → read.html)
```

## Error handling / edge cases

- Fonts fail → serif fallback stacks keep the design intact.
- JS disabled → all content visible (reveal animations default-visible without
  JS; toggles/drawer are enhancements), reader still navigable via anchors.
- 913 KB reader page: text gzips well (~6:1); acceptable for a devotional
  full-text page, and chapter anchors give instant navigation.

## Testing

Open every page in the browser; verify nav/footer links, chapter anchors,
layer toggles, mobile layout (375 px), and that hero art renders without
console errors.
