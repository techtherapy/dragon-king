#!/usr/bin/env python3
"""Build read.html from the source sutra file.

Parses `Dragon king sutra hailongwang_complete.html` (rigidly line-structured,
machine-generated) with a small state machine, then re-emits the complete
trilingual text inside the site's reader chrome.

Run from the repo root:  python3 scripts/build_reader.py
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "extra-content" / "Dragon king sutra hailongwang_complete.html"
OUT = ROOT / "read.html"

# The translated layers, in the order they are stacked under each verse. The
# CSS class is also the key each verse is stored under, and the chip label is
# the language's own name for itself — a language always labels itself.
LAYERS = {
    "es": {"cls": "espanol", "chip": "Español"},
    "fr": {"cls": "francais", "chip": "Français"},
}


def layer_dir(lang):
    return ROOT / "translations" / lang


def out_path(lang):
    return ROOT / lang / "read.html"

LEAF = re.compile(r'<div class="(hanzi|pinyin|english)">(.*)</div>\s*$')
STYLED = re.compile(r'<div style="[^"]*">(.*)</div>\s*$')
BLOCK_OPEN = re.compile(r'<div class="block([^"]*)">\s*$')
ANCHOR = re.compile(r'<a id="(ch\d+)"></a>\s*$')

# Chapter number -> volume label. Roman numerals rather than spelled-out
# words: "Vol I" is correct in English, Spanish and French alike, so the one
# label serves all three readers. The words "One".."Four" did not — they were
# showing untranslated in the Spanish and French sidebars.
VOLUME_OF = {
    **{n: "卷一 · Vol I" for n in range(1, 5)},
    **{n: "卷二 · Vol II" for n in range(5, 10)},
    **{n: "卷三 · Vol III" for n in range(10, 16)},
    **{n: "卷四 · Vol IV" for n in range(16, 21)},
}
CJK_NUM = ["一", "二", "三", "四", "五", "六", "七", "八", "九", "十",
           "十一", "十二", "十三", "十四", "十五", "十六", "十七", "十八", "十九", "二十"]


def parse():
    """Returns (title_lines, colophon_prows, chapters).
    chapters: list of dicts {id, label(zh,py,en), blocks:[(cls, [prow…])]}"""
    text = SRC.read_text(encoding="utf-8")
    # title/seclabel blocks close on the same line as their last child
    # (`...</div></div>`); split those so the state machine sees each close.
    text = text.replace("</div></div>", "</div>\n</div>")
    lines = text.splitlines()

    title_lines = []          # 3 styled lines of the main title
    colophon = []             # prows of the colophon block
    chapters = []
    cur = None                # current chapter dict (None while in preamble)

    in_title = in_seclabel = False
    block_cls = None          # None = not inside a block
    block_prows = []
    prow = None               # dict being filled
    depth = 0                 # div depth inside current block
    in_colophon = False

    for line in lines:
        s = line.strip()

        m = ANCHOR.match(s)
        if m:
            cur = {"id": m.group(1), "label": [], "blocks": []}
            chapters.append(cur)
            continue

        if s.startswith('<div class="title">'):
            in_title = True
            continue
        if in_title:
            m = STYLED.match(s)
            if m:
                title_lines.append(m.group(1))
                continue
            if s == "</div>":
                in_title = False
            continue

        if s.startswith('<div class="seclabel'):
            in_seclabel = True
            continue
        if in_seclabel:
            m = STYLED.match(s)
            if m and cur is not None:
                cur["label"].append(m.group(1))
                continue
            if s == "</div>":
                in_seclabel = False
            continue

        if s.startswith('<div class="toc') or s.startswith('<a class="tocitem') \
           or s.startswith('<div class="tocline') or s.startswith('<div class="tochz') \
           or s.startswith('<div class="tocpy') or s.startswith('<div class="tocen') \
           or s == "</a>":
            continue  # skip the source TOC; we build our own

        m = BLOCK_OPEN.match(s)
        if m:
            block_cls = m.group(1).strip()
            in_colophon = "colophon" in block_cls
            block_prows = []
            depth = 1
            continue

        if block_cls is not None:
            if s.startswith('<div class="prow">'):
                prow = {}
                depth += 1
                continue
            m = LEAF.match(s)
            if m and prow is not None:
                prow[m.group(1)] = m.group(2)
                continue
            if s == "</div>":
                depth -= 1
                if depth == 1 and prow is not None:
                    block_prows.append(prow)
                    prow = None
                elif depth == 0:
                    if in_colophon:
                        colophon.extend(block_prows)
                    elif cur is not None:
                        cur["blocks"].append((block_cls, block_prows))
                    block_cls = None
                continue

    return title_lines, colophon, chapters


def load_layer(chapters, colophon, lang):
    """Attach one translated layer from translations/<lang>/. The chapter files
    are verse-aligned to the English; any mismatch is a build error, so a
    partial or drifted translation can never ship silently."""
    cls = LAYERS[lang]["cls"]
    d = layer_dir(lang)
    for i, ch in enumerate(chapters, start=1):
        data = json.loads((d / f"ch{i:02d}.json").read_text(encoding="utf-8"))
        n_src = sum(len(ps) for _, ps in ch["blocks"])
        verses = data["verses"]
        if len(verses) != n_src:
            raise SystemExit(
                f"{lang}/ch{i:02d}.json: {len(verses)} verses, source has {n_src}")
        ch[f"label_{lang}"] = data[f"label_{lang}"]
        k = 0
        for _, prows in ch["blocks"]:
            for p in prows:
                p[cls] = verses[k]
                k += 1
    common = json.loads((d / "common.json").read_text(encoding="utf-8"))
    if len(common["colophon"]) != len(colophon):
        raise SystemExit(f"{lang}/common.json: colophon length mismatch")
    for p, line in zip(colophon, common["colophon"]):
        p[cls] = line
    return common["title_t3"]


def prow_html(p, indent="        "):
    parts = []
    if "hanzi" in p:
        parts.append(f'<p class="hanzi" lang="zh-Hant">{p["hanzi"]}</p>')
    if "pinyin" in p:
        parts.append(f'<p class="pinyin" aria-hidden="true">{p["pinyin"]}</p>')
    if "english" in p:
        parts.append(f'<p class="english">{p["english"]}</p>')
    for lang, layer in LAYERS.items():
        cls = layer["cls"]
        if cls in p:
            parts.append(f'<p class="{cls}" lang="{lang}">{p[cls]}</p>')
    return f'{indent}<div class="prow">' + "".join(parts) + "</div>"


# the reader's Chinese face is a self-hosted subset; its filename carries a
# content stamp so it can be cached hard and still update instantly
SUBSET = json.loads((ROOT / "scripts" / "wenkai-subset.json")
                    .read_text(encoding="utf-8"))["file"]

CHROME_HEAD = """<!DOCTYPE html>
<html lang="en" class="no-js">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Read the Sutra — Dragon King Sutra 佛說海龍王經</title>
<meta name="description" content="The complete Sutra Spoken by the Buddha on the Sea Dragon King in Traditional Chinese, pinyin, English, Spanish and French — four volumes, twenty chapters.">
<link rel="icon" type="image/svg+xml" href="assets/favicon.svg">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;1,400&family=EB+Garamond:ital,wght@0,400;0,500;1,400&display=swap" rel="stylesheet">
<!-- The Chinese face, self-hosted and cut to exactly the characters this
     page shows. Google splits this font into 230 files by character code
     rather than by use, so the reader's 1,273 characters pulled ~3.6MB across
     72 of them; the subset is one file of about 400KB. Rebuild it with
     scripts/build_font_subset.py — the build refuses to publish if a page
     gains a character the subset does not carry. -->
<style>@font-face{{font-family:"LXGW WenKai TC";font-style:normal;font-weight:400;font-display:swap;src:url(/assets/{font_file}) format("woff2")}}</style>
<link rel="stylesheet" href="css/style.css">
<link rel="stylesheet" href="css/reader.css">
</head>
<body class="reader-page hide-es hide-fr">

<div class="progress-track" aria-hidden="true"><span class="progress-fill" id="progressFill"></span></div>

<header class="site-header">
  <a href="index.html" class="brand" aria-label="Dragon King Sutra home">
    <svg class="brand-mark" viewBox="0 0 48 48" aria-hidden="true">
      <circle cx="24" cy="24" r="21.5" fill="none" stroke="#8d7440" stroke-width="1" opacity=".6"/>
      <path d="M24 6 C35 6 42 14 42 24 C42 34 35 41 25 41 C17 41 11 36 11 29 C11 22 16 18 22 18 C27 18 30 21 30 25 C30 28 28 30 25 30"
            fill="none" stroke="#d9b25f" stroke-width="2" stroke-linecap="round"/>
      <path d="M24 6 L20 2.5 M24 6 L20 9.5" stroke="#f4dc96" stroke-width="1.8" stroke-linecap="round" fill="none"/>
      <circle cx="24" cy="25.5" r="3.2" fill="#f4dc96"/>
    </svg>
    <span class="brand-name">Dragon King Sutra<span class="tc">佛說海龍王經</span></span>
  </a>
  <button class="nav-toggle" aria-expanded="false" aria-label="Menu">☰</button>
  <nav class="site-nav">
    <a href="about.html">About</a>
    <a href="read.html" aria-current="page">Read</a>
    <a href="treasure-vase-yoga.html">Practice</a>
    <a href="his-holiness-living-buddha-lian-sheng.html">Living Buddha Lian Sheng</a>
    <a href="contact.html">Contact</a>
    <span class="lang-switch"><a href="/es/read.html" hreflang="es" lang="es" aria-label="Español">ES</a><a href="/fr/read.html" hreflang="fr" lang="fr" aria-label="Français">FR</a></span>
    <a href="refuge.html" class="nav-cta">Take Refuge</a>
  </nav>
</header>

<div class="toc-scrim" id="tocScrim"></div>

<div class="reader-shell">
"""

CHROME_FOOT = """
</div><!-- /reader-shell -->

<button class="to-top" id="toTop" aria-label="Back to top">☸</button>

<footer class="site-footer">
  <div class="footer-crest" aria-hidden="true">
    <img src="assets/footer-crest.svg" alt="" width="100" height="100" loading="lazy">
  </div>
  <div class="wrap footer-grid">
    <div>
      <h4>The Sutra</h4>
      <ul>
        <li><a href="about.html">About the Sutra</a></li>
        <li><a href="nagas-and-dragon-kings.html">Nagas &amp; Dragon Kings</a></li>
        <li><a href="read.html">Read the Sutra</a></li>
        <li><a href="about.html#reflection">Study Reflection</a></li>
        <li><a href="read.html?print">Print the Sutra</a></li>
      </ul>
    </div>
    <div>
      <h4>Teachings</h4>
      <ul>
        <li><a href="treasure-vase-yoga.html">Treasure Vase Yoga</a></li>
        <li><a href="treasure-vase-wishes.html">Wishes in the Treasure Vase</a></li>
      </ul>
    </div>
    <div>
      <h4>About</h4>
      <ul>
        <li><a href="his-holiness-living-buddha-lian-sheng.html">H.H. Living Buddha Lian Sheng</a></li>
        <li><a href="refuge.html">Take Refuge</a></li>
        <li><a href="contact.html">Contact Us</a></li>
      </ul>
    </div>
    <div>
      <h4>Temple Websites</h4>
      <ul>
        <li><a href="https://english.tbsseattle.org/" rel="noopener">Seattle Leizang Temple</a></li>
        <li><a href="https://tbs-rainbow.org/" rel="noopener">Rainbow Temple</a></li>
      </ul>
    </div>
    <div>
      <h4>Related Sites</h4>
      <ul>
        <li><a href="https://amitabhasutra.org" rel="noopener">Amitabha Sutra</a></li>
        <li><a href="https://highkingsutra.org" rel="noopener">High King Sutra</a></li>
        <li><a href="https://surangamasutra.org" rel="noopener">Surangama Sutra</a></li>
        <li><a href="https://truebuddhasutra.org" rel="noopener">True Buddha Sutra</a></li>
        <li><a href="https://vajrasutra.org" rel="noopener">Vajra Sutra</a></li>
        <li><a href="https://emperorliangrepentance.org" rel="noopener">Emperor Liang Repentance</a></li>
        <li><a href="https://drashilhamo.org" rel="noopener">Drashi Lhamo</a></li>
        <li><a href="https://vlotus.org" rel="noopener">VLotus 蓮花飄香</a></li>
      </ul>
    </div>
    <div>
      <h4>Online Teachings</h4>
      <ul>
        <li><a href="https://www.youtube.com/@tbsseattle.orgenglishstrea3035" rel="noopener">Saturday Live Streams</a></li>
        <li><a href="https://www.youtube.com/@RainbowTemple-English" rel="noopener">Sunday Live Streams</a></li>
      </ul>
    </div>
    <div>
      <h4>True Buddha School</h4>
      <ul>
        <li><a href="https://en.tbsn.org/" rel="noopener">TBSN.org</a></li>
        <li><a href="https://tbboyeh.org/eng#/index" rel="noopener">TBBoyeh</a></li>
        <li><a href="https://yifucultural.com" rel="noopener">Yifu Publications</a></li>
        <li><a href="https://sylfoundation.org" rel="noopener">Sheng-Yen Lu Foundation</a></li>
      </ul>
    </div>
    <div>
      <h4>Facebook</h4>
      <ul>
        <li><a href="https://www.facebook.com/syltbsnenglish" rel="noopener">Official Page</a></li>
        <li><a href="https://www.facebook.com/groups/tbsenglish" rel="noopener">Discussion Group</a></li>
        <li><a href="https://www.facebook.com/VajraLotsawas" rel="noopener">Vajra Lotsawas</a></li>
      </ul>
    </div>
  </div>
  
  <div class="footer-bottom">
    <span class="tc" lang="zh-Hant">南無海龍王菩薩</span>
    <span>May all beings share in the merit of this offering of the dharma</span>
    <span class="mantra-line">Om Guru Lian Sheng Siddhi Hum · <span lang="zh-Hant">嗡咕嚕蓮生悉地吽</span></span>
  </div>
</footer>

<script src="js/main.js"></script>
<script src="js/reader.js"></script>
</body>
</html>
"""


# ----------------------------------------------------------------------
# Translated chrome. The English chrome above is the single source of layout;
# each translated page is the same markup with these strings swapped, links
# pointed at that language's twins and asset paths made root-absolute (those
# pages sit one directory down). One table holds every language, so a pattern
# can never be translated into one language and forgotten in another.
# ----------------------------------------------------------------------
CHROME_TR = [
    # head
    ('<html lang="en"',
     {"es": '<html lang="es"', "fr": '<html lang="fr"'}),
    ("<title>Read the Sutra — Dragon King Sutra 佛說海龍王經</title>",
     {"es": "<title>Leer el Sutra — Dragon King Sutra 佛說海龍王經</title>",
      "fr": "<title>Lire le Soutra — Dragon King Sutra 佛說海龍王經</title>"}),
    ("The complete Sutra Spoken by the Buddha on the Sea Dragon King in Traditional "
     "Chinese, pinyin, English, Spanish and French — four volumes, twenty chapters.",
     {"es": "El Sutra Pronunciado por el Buda sobre el Rey Dragón del Mar completo, en chino "
            "tradicional, pinyin, inglés, español y francés — cuatro volúmenes, veinte capítulos.",
      "fr": "Le Soutra prononcé par le Bouddha sur le Roi Dragon de la Mer en entier, en "
            "chinois traditionnel, pinyin, anglais, espagnol et français — quatre volumes, "
            "vingt chapitres."}),
    # body: each reader hides the two layers that are not its own
    ('<body class="reader-page hide-es hide-fr">',
     {"es": '<body class="reader-page hide-en hide-fr">',
      "fr": '<body class="reader-page hide-en hide-es">'}),
    # nav
    ('<a href="about.html">About</a>',
     {"es": '<a href="/es/about.html">Acerca de</a>',
      "fr": '<a href="/fr/about.html">À propos</a>'}),
    ('<a href="read.html" aria-current="page">Read</a>',
     {"es": '<a href="/es/read.html" aria-current="page">Leer</a>',
      "fr": '<a href="/fr/read.html" aria-current="page">Lire</a>'}),
    ('<a href="treasure-vase-yoga.html">Practice</a>',
     {"es": '<a href="/es/treasure-vase-yoga.html">Práctica</a>',
      "fr": '<a href="/fr/treasure-vase-yoga.html">Pratique</a>'}),
    ('<a href="his-holiness-living-buddha-lian-sheng.html">Living Buddha Lian Sheng</a>',
     {"es": '<a href="/es/his-holiness-living-buddha-lian-sheng.html">Buda Viviente Lian Sheng</a>',
      "fr": '<a href="/fr/his-holiness-living-buddha-lian-sheng.html">Bouddha Vivant Lian Sheng</a>'}),
    ('<a href="contact.html">Contact</a>',
     {"es": '<a href="/es/contact.html">Contacto</a>',
      "fr": '<a href="/fr/contact.html">Contact</a>'}),
    ('<span class="lang-switch">'
     '<a href="/es/read.html" hreflang="es" lang="es" aria-label="Español">ES</a>'
     '<a href="/fr/read.html" hreflang="fr" lang="fr" aria-label="Français">FR</a>'
     '</span>',
     {"es": '<span class="lang-switch">'
            '<a href="/read.html" hreflang="en" lang="en" aria-label="English">EN</a>'
            '<a href="/fr/read.html" hreflang="fr" lang="fr" aria-label="Français">FR</a>'
            '</span>',
      "fr": '<span class="lang-switch">'
            '<a href="/read.html" hreflang="en" lang="en" aria-label="English">EN</a>'
            '<a href="/es/read.html" hreflang="es" lang="es" aria-label="Español">ES</a>'
            '</span>'}),
    ('<a href="refuge.html" class="nav-cta">Take Refuge</a>',
     {"es": '<a href="/es/refuge.html" class="nav-cta">Tomar Refugio</a>',
      "fr": '<a href="/fr/refuge.html" class="nav-cta">Prendre refuge</a>'}),
    ('aria-label="Menu"', {"es": 'aria-label="Menú"', "fr": 'aria-label="Menu"'}),
    ('aria-label="Dragon King Sutra home"',
     {"es": 'aria-label="Dragon King Sutra inicio"',
      "fr": 'aria-label="Dragon King Sutra accueil"'}),
    ('<a href="index.html" class="brand"',
     {"es": '<a href="/es/index.html" class="brand"',
      "fr": '<a href="/fr/index.html" class="brand"'}),
    # reader furniture
    ('aria-label="Back to top">☸',
     {"es": 'aria-label="Volver arriba">☸', "fr": 'aria-label="Retour en haut">☸'}),
    ('aria-label="Chapters"',
     {"es": 'aria-label="Capítulos"', "fr": 'aria-label="Chapitres"'}),
    ("目錄 · CONTENTS", {"es": "目錄 · CONTENIDO", "fr": "目錄 · SOMMAIRE"}),
    ('<span class="btn-label">Chapters</span>',
     {"es": '<span class="btn-label">Capítulos</span>',
      "fr": '<span class="btn-label">Chapitres</span>'}),
    ('<span class="btn-label">Print</span>',
     {"es": '<span class="btn-label">Imprimir</span>',
      "fr": '<span class="btn-label">Imprimer</span>'}),
    ('<span class="layer-label">Layers</span>',
     {"es": '<span class="layer-label">Capas</span>',
      "fr": '<span class="layer-label">Couches</span>'}),
    # Each reader opens with its own language lit. Without this the chips are
    # painted from the English defaults and flicker when reader.js corrects
    # them, which is the one thing on the page a reader is watching.
    ('data-layer="en" aria-pressed="true"',
     {"es": 'data-layer="en" aria-pressed="false"',
      "fr": 'data-layer="en" aria-pressed="false"'}),
    ('data-layer="es" aria-pressed="false"',
     {"es": 'data-layer="es" aria-pressed="true"',
      "fr": 'data-layer="es" aria-pressed="false"'}),
    ('data-layer="fr" aria-pressed="false"',
     {"es": 'data-layer="fr" aria-pressed="false"',
      "fr": 'data-layer="fr" aria-pressed="true"'}),
    # footer
    ("<h4>The Sutra</h4>", {"es": "<h4>El Sutra</h4>", "fr": "<h4>Le Soutra</h4>"}),
    ("<h4>Teachings</h4>", {"es": "<h4>Enseñanzas</h4>", "fr": "<h4>Enseignements</h4>"}),
    ("<h4>About</h4>", {"es": "<h4>Acerca de</h4>", "fr": "<h4>À propos</h4>"}),
    ("<h4>Temple Websites</h4>",
     {"es": "<h4>Sitios de templos</h4>", "fr": "<h4>Sites des temples</h4>"}),
    ("<h4>Related Sites</h4>",
     {"es": "<h4>Sitios relacionados</h4>", "fr": "<h4>Sites associés</h4>"}),
    ("<h4>Online Teachings</h4>",
     {"es": "<h4>Enseñanzas en línea</h4>", "fr": "<h4>Enseignements en ligne</h4>"}),
    ('<a href="about.html">About the Sutra</a>',
     {"es": '<a href="/es/about.html">Acerca del Sutra</a>',
      "fr": '<a href="/fr/about.html">À propos du Soutra</a>'}),
    ('<a href="nagas-and-dragon-kings.html">Nagas &amp; Dragon Kings</a>',
     {"es": '<a href="/es/nagas-and-dragon-kings.html">Nagas y Reyes Dragones</a>',
      "fr": '<a href="/fr/nagas-and-dragon-kings.html">Nagas et Rois Dragons</a>'}),
    ('<a href="read.html">Read the Sutra</a>',
     {"es": '<a href="/es/read.html">Leer el Sutra</a>',
      "fr": '<a href="/fr/read.html">Lire le Soutra</a>'}),
    ('<a href="about.html#reflection">Study Reflection</a>',
     {"es": '<a href="/es/about.html#reflection">Reflexión de estudio</a>',
      "fr": '<a href="/fr/about.html#reflection">Réflexion d\'étude</a>'}),
    ('<a href="read.html?print">Print the Sutra</a>',
     {"es": '<a href="/es/read.html?print">Imprimir el Sutra</a>',
      "fr": '<a href="/fr/read.html?print">Imprimer le Soutra</a>'}),
    ('<a href="treasure-vase-yoga.html">Treasure Vase Yoga</a>',
     {"es": '<a href="/es/treasure-vase-yoga.html">El Yoga del Jarrón del Tesoro</a>',
      "fr": '<a href="/fr/treasure-vase-yoga.html">Le Yoga du Vase du Trésor</a>'}),
    ('<a href="treasure-vase-wishes.html">Wishes in the Treasure Vase</a>',
     {"es": '<a href="/es/treasure-vase-wishes.html">Deseos en el Jarrón del Tesoro</a>',
      "fr": '<a href="/fr/treasure-vase-wishes.html">Les souhaits dans le Vase du Trésor</a>'}),
    ('<a href="his-holiness-living-buddha-lian-sheng.html">H.H. Living Buddha Lian Sheng</a>',
     {"es": '<a href="/es/his-holiness-living-buddha-lian-sheng.html">S.S. el Buda Viviente Lian Sheng</a>',
      "fr": '<a href="/fr/his-holiness-living-buddha-lian-sheng.html">S.S. le Bouddha Vivant Lian Sheng</a>'}),
    ('<a href="refuge.html">Take Refuge</a>',
     {"es": '<a href="/es/refuge.html">Tomar Refugio</a>',
      "fr": '<a href="/fr/refuge.html">Prendre refuge</a>'}),
    ('<a href="contact.html">Contact Us</a>',
     {"es": '<a href="/es/contact.html">Contáctanos</a>',
      "fr": '<a href="/fr/contact.html">Nous contacter</a>'}),
    (">Seattle Leizang Temple<",
     {"es": ">Templo Leizang de Seattle<", "fr": ">Temple Leizang de Seattle<"}),
    (">Rainbow Temple<",
     {"es": ">Templo del Arcoíris<", "fr": ">Temple de l\'Arc-en-ciel<"}),
    (">Saturday Live Streams<",
     {"es": ">Transmisiones en vivo del sábado<", "fr": ">Diffusions en direct du samedi<"}),
    (">Sunday Live Streams<",
     {"es": ">Transmisiones en vivo del domingo<", "fr": ">Diffusions en direct du dimanche<"}),
    (">Official Page<", {"es": ">Página oficial<", "fr": ">Page officielle<"}),
    (">Discussion Group<", {"es": ">Grupo de discusión<", "fr": ">Groupe de discussion<"}),
    ("May all beings share in the merit of this offering of the dharma",
     {"es": "Que todos los seres compartan el mérito de esta ofrenda del dharma",
      "fr": "Que tous les êtres partagent le mérite de cette offrande du dharma"}),
    # the mantra transliterated for each language's phonetics
    ("Om Guru Lian Sheng Siddhi Hum",
     {"es": "Om Guru Lian Sheng Sidi Jom", "fr": "Om Gourou Lian Sheng Siddhi Houm"}),
    # assets live at the root; these pages are one level down
    ('href="css/', {"es": 'href="/css/', "fr": 'href="/css/'}),
    ('src="js/', {"es": 'src="/js/', "fr": 'src="/js/'}),
    ('href="assets/', {"es": 'href="/assets/', "fr": 'href="/assets/'}),
    ('src="assets/', {"es": 'src="/assets/', "fr": 'src="/assets/'}),
]

# Pivot to one list per language, refusing at import time to ship a table that
# has a hole in it — the parity check reads CHROME to confirm every language
# the reader knows about has chrome behind it.
CHROME = {lang: [] for lang in LAYERS}
for _src, _by_lang in CHROME_TR:
    _missing = set(LAYERS) - set(_by_lang)
    if _missing:
        raise SystemExit(
            f"build_reader: chrome pattern {_src[:60]!r} has no {sorted(_missing)}")
    for _lang, _text in _by_lang.items():
        CHROME[_lang].append((_src, _text))


def to_lang(html, lang):
    """The English reader markup, localized. Every replacement must fire —
    a silent miss would leave English in a translated page."""
    for src, dst in CHROME[lang]:
        if src not in html:
            raise SystemExit(f"{lang} chrome: pattern not found -> {src[:70]}")
        html = html.replace(src, dst)
    return html


def short_en(label_en):
    """'Volume 1, Chapter One: Practice' -> 'Practice'"""
    return label_en.split(":", 1)[-1].strip() if ":" in label_en else label_en


def build():
    title_lines, colophon, chapters = parse()
    assert len(chapters) == 20, f"expected 20 chapters, got {len(chapters)}"
    n_prows = sum(len(ps) for c in chapters for _, ps in c["blocks"])
    titles = {lang: load_layer(chapters, colophon, lang) for lang in LAYERS}

    out = [CHROME_HEAD.format(font_file=SUBSET)]

    # ---- sidebar TOC ----
    out.append('  <aside class="reader-toc" id="readerToc" aria-label="Chapters">')
    out.append('    <div class="toc-head" lang="zh-Hant">目錄 · CONTENTS</div>')
    out.append("    <nav>")
    last_vol = None
    for i, ch in enumerate(chapters, start=1):
        vol = VOLUME_OF[i]
        if vol != last_vol:
            out.append(f'      <div class="toc-vol" lang="zh-Hant">{vol}</div>')
            last_vol = vol
        zh, py, en = ch["label"]
        tr = "".join(
            f'<span class="t-en {layer["cls"]}" lang="{lang}">'
            f'{i} · {short_en(ch[f"label_{lang}"])}</span>'
            for lang, layer in LAYERS.items())
        out.append(f'      <a href="#{ch["id"]}"><span class="t-zh" lang="zh-Hant">{zh}</span>'
                   f'<span class="t-en">{i} · {short_en(en)}</span>{tr}</a>')
    out.append("    </nav>")
    out.append("  </aside>")

    # ---- main column ----
    out.append('  <div class="reader-main">')
    out.append('    <div class="reader-tools">')
    out.append('      <button class="tool-btn toc-btn" id="tocBtn" aria-expanded="false" aria-controls="readerToc">☰ <span lang="zh-Hant">目錄</span> <span class="btn-label">Chapters</span></button>')
    out.append('      <span class="layer-label">Layers</span>')
    out.append('      <button class="chip" data-layer="zh" aria-pressed="true"><span class="dot"></span><span lang="zh-Hant">漢字</span></button>')
    out.append('      <button class="chip" data-layer="py" aria-pressed="true"><span class="dot"></span>Pīnyīn</button>')
    out.append('      <button class="chip" data-layer="en" aria-pressed="true"><span class="dot"></span>English</button>')
    out.append('      <button class="chip" data-layer="es" aria-pressed="false"><span class="dot"></span>Español</button>')
    out.append('      <button class="chip" data-layer="fr" aria-pressed="false"><span class="dot"></span>Français</button>')
    out.append('      <span class="spacer"></span>')
    out.append('      <button class="tool-btn" id="printBtn">⎙ <span class="btn-label">Print</span></button>')
    out.append("    </div>")
    out.append('    <article class="sutra">')

    # title
    t1, t2, t3 = title_lines[:3]
    out.append('      <header class="sutra-title">')
    out.append(f'        <h1 class="t1" lang="zh-Hant">{t1}</h1>')
    out.append(f'        <div class="t2" aria-hidden="true">{t2}</div>')
    out.append(f'        <div class="t3">{t3}</div>')
    for lang, layer in LAYERS.items():
        out.append(f'        <div class="t3 {layer["cls"]}" lang="{lang}">{titles[lang]}</div>')
    out.append("      </header>")

    # colophon
    if colophon:
        out.append('      <div class="sutra-colophon block center">')
        for p in colophon:
            out.append(prow_html(p))
        out.append("      </div>")

    # chapters
    for i, ch in enumerate(chapters, start=1):
        zh, py, en = ch["label"]
        out.append(f'      <section class="chapter" id="{ch["id"]}">')
        out.append('        <header class="seclabel">')
        out.append('          <div class="seal-row"><span class="seal small" aria-hidden="true" lang="zh-Hant">'
                   + CJK_NUM[i - 1] + "</span></div>")
        out.append(f'          <h2 class="s1" lang="zh-Hant">{zh}</h2>')
        out.append(f'          <div class="s2" aria-hidden="true">{py}</div>')
        out.append(f'          <div class="s3">{en}</div>')
        for lang, layer in LAYERS.items():
            out.append(f'          <div class="s3 {layer["cls"]}" lang="{lang}">'
                       f'{ch[f"label_{lang}"]}</div>')
        out.append("        </header>")
        for cls, prows in ch["blocks"]:
            classes = "block" + (f" {cls}" if cls else "")
            out.append(f'      <div class="{classes}">')
            for p in prows:
                out.append(prow_html(p))
            out.append("      </div>")
        out.append("      </section>")

    out.append("    </article>")
    out.append("  </div><!-- /reader-main -->")
    out.append(CHROME_FOOT)

    html = "\n".join(out)
    OUT.write_text(html, encoding="utf-8")
    print(f"read.html written: {len(html) / 1024:.0f} KB, {len(chapters)} chapters, {n_prows} verses")

    for lang in LAYERS:
        page = to_lang(html, lang)
        dest = out_path(lang)
        dest.parent.mkdir(exist_ok=True)
        dest.write_text(page, encoding="utf-8")
        print(f"{dest.relative_to(ROOT)} written: {len(page) / 1024:.0f} KB")


if __name__ == "__main__":
    build()
