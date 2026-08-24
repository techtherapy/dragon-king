#!/usr/bin/env python3
"""Ask Google Fonts for only the Chinese characters each page actually shows.

Google serves LXGW WenKai TC as 230 files split by character *code*, not by
what a page uses. The home page shows 185 distinct characters and they scatter
across 25 of those blocks, so the browser downloads 25 whole files — 1,517 KB
to draw 185 glyphs. The practice page shows 53 characters and pays 942 KB.

The `text=` parameter asks for a font containing exactly the characters named,
which collapses that to one small file per page (the home page: 59 KB).

Pages above CAP distinct characters are left alone: the URL grows past what is
sensible to put in a link, and Google reverts to block-splitting anyway. Today
that is only the reader, which needs a self-hosted subset instead.

Runs after add_seo.py, so the character set it sees is final.
Run from the repo root:  python3 scripts/subset_font_links.py
"""
import re
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FAMILY = "LXGW+WenKai+TC"
CAP = 600
CJK = re.compile(r"[　-〿㐀-䶿一-鿿豈-﫿]")
# the whole non-blocking pair this script owns, in either form
LINKS = re.compile(
    r'<link rel="preload" as="style" href="https://fonts\.googleapis\.com/css2\?family='
    r'LXGW\+WenKai\+TC[^"]*" onload="[^"]*">\n'
    r'<noscript><link href="https://fonts\.googleapis\.com/css2\?family='
    r'LXGW\+WenKai\+TC[^"]*" rel="stylesheet"></noscript>')


def links_for(chars):
    if chars:
        q = urllib.parse.quote("".join(chars))
        url = f"https://fonts.googleapis.com/css2?family={FAMILY}&text={q}&display=swap"
    else:
        url = f"https://fonts.googleapis.com/css2?family={FAMILY}:wght@400;700&display=swap"
    return (f'<link rel="preload" as="style" href="{url}"'
            f' onload="this.onload=null;this.rel=\'stylesheet\'">\n'
            f'<noscript><link href="{url}" rel="stylesheet"></noscript>')


def process(path):
    s = path.read_text(encoding="utf-8")
    if not LINKS.search(s):
        return None
    chars = sorted(set(CJK.findall(s)))
    trimmed = len(chars) <= CAP
    s = LINKS.sub(lambda _: links_for(chars if trimmed else []), s, count=1)
    path.write_text(s, encoding="utf-8")
    return len(chars), trimmed


if __name__ == "__main__":
    pages = (sorted(ROOT.glob("*.html")) + sorted(ROOT.glob("es/*.html"))
             + sorted(ROOT.glob("fr/*.html")))
    for p in pages:
        r = process(p)
        if r is None:
            continue
        n, trimmed = r
        rel = p.relative_to(ROOT)
        print(f"  {str(rel):48} {n:5} chars  "
              + ("trimmed to exactly those" if trimmed
                 else f"left whole (over {CAP})"))
