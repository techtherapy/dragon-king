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
SRC = ROOT / "Dragon king sutra hailongwang_complete.html"
ES_DIR = ROOT / "translations" / "es"
OUT = ROOT / "read.html"

LEAF = re.compile(r'<div class="(hanzi|pinyin|english)">(.*)</div>\s*$')
STYLED = re.compile(r'<div style="[^"]*">(.*)</div>\s*$')
BLOCK_OPEN = re.compile(r'<div class="block([^"]*)">\s*$')
ANCHOR = re.compile(r'<a id="(ch\d+)"></a>\s*$')

VOLUME_OF = {  # chapter number -> volume label
    **{n: "卷一 · Vol. One" for n in range(1, 5)},
    **{n: "卷二 · Vol. Two" for n in range(5, 10)},
    **{n: "卷三 · Vol. Three" for n in range(10, 16)},
    **{n: "卷四 · Vol. Four" for n in range(16, 21)},
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


def load_spanish(chapters, colophon):
    """Attach the Spanish layer from translations/es/. The chapter files are
    verse-aligned to the English; any mismatch is a build error, so a partial
    or drifted translation can never ship silently."""
    for i, ch in enumerate(chapters, start=1):
        data = json.loads((ES_DIR / f"ch{i:02d}.json").read_text(encoding="utf-8"))
        n_src = sum(len(ps) for _, ps in ch["blocks"])
        verses = data["verses"]
        if len(verses) != n_src:
            raise SystemExit(f"es/ch{i:02d}.json: {len(verses)} verses, source has {n_src}")
        ch["label_es"] = data["label_es"]
        k = 0
        for _, prows in ch["blocks"]:
            for p in prows:
                p["espanol"] = verses[k]
                k += 1
    common = json.loads((ES_DIR / "common.json").read_text(encoding="utf-8"))
    if len(common["colophon"]) != len(colophon):
        raise SystemExit("es/common.json: colophon length mismatch")
    for p, es in zip(colophon, common["colophon"]):
        p["espanol"] = es
    return common["title_t3"]


def prow_html(p, indent="        "):
    parts = []
    if "hanzi" in p:
        parts.append(f'<p class="hanzi" lang="zh-Hant">{p["hanzi"]}</p>')
    if "pinyin" in p:
        parts.append(f'<p class="pinyin" aria-hidden="true">{p["pinyin"]}</p>')
    if "english" in p:
        parts.append(f'<p class="english">{p["english"]}</p>')
    if "espanol" in p:
        parts.append(f'<p class="espanol" lang="es">{p["espanol"]}</p>')
    return f'{indent}<div class="prow">' + "".join(parts) + "</div>"


CHROME_HEAD = """<!DOCTYPE html>
<html lang="en" class="no-js">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Read the Sutra — Dragon King Sutra 佛說海龍王經</title>
<meta name="description" content="The complete Sutra Spoken by the Buddha on the Sea Dragon King in Traditional Chinese, pinyin, English and Spanish — four volumes, twenty chapters.">
<link rel="icon" type="image/svg+xml" href="assets/favicon.svg">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;1,400&family=EB+Garamond:ital,wght@0,400;0,500;1,400&display=swap" rel="stylesheet">
<link href="https://fonts.googleapis.com/css2?family=LXGW+WenKai+TC:wght@400;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="css/style.css">
<link rel="stylesheet" href="css/reader.css">
</head>
<body class="reader-page hide-es">

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


def short_en(label_en):
    """'Volume 1, Chapter One: Practice' -> 'Practice'"""
    return label_en.split(":", 1)[-1].strip() if ":" in label_en else label_en


def build():
    title_lines, colophon, chapters = parse()
    assert len(chapters) == 20, f"expected 20 chapters, got {len(chapters)}"
    n_prows = sum(len(ps) for c in chapters for _, ps in c["blocks"])
    title_es = load_spanish(chapters, colophon)

    out = [CHROME_HEAD]

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
        out.append(f'      <a href="#{ch["id"]}"><span class="t-zh" lang="zh-Hant">{zh}</span>'
                   f'<span class="t-en">{i} · {short_en(en)}</span>'
                   f'<span class="t-en espanol" lang="es">{i} · {short_en(ch["label_es"])}</span></a>')
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
    out.append(f'        <div class="t3 espanol" lang="es">{title_es}</div>')
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
        out.append(f'          <div class="s3 espanol" lang="es">{ch["label_es"]}</div>')
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


if __name__ == "__main__":
    build()
