#!/usr/bin/env python3
"""Fail the build if an English page and its Spanish twin have drifted apart.

The two language versions are the same markup with different words in it, so
their *structure* must be identical: the same elements in the same order with
the same classes. This compares that fingerprint and ignores all text.

It catches the failure mode that matters — someone edits an English page
(adds a section, renames a class, reorders a block) and forgets the Spanish
one, so the pages silently diverge until a reader notices.

Generated pages (read.html, treasure-vase-yoga.html) are not checked here:
their two versions come from one generator and cannot drift.

Run from the repo root:  python3 scripts/check_es_parity.py
"""
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAIRS = [
    "index.html",
    "about.html",
    "refuge.html",
    "contact.html",
    "his-holiness-living-buddha-lian-sheng.html",
    "treasure-vase-wishes.html",
]
# The SEO block is regenerated per language by add_seo.py, so it is expected
# to differ; strip it before fingerprinting.
SEO = re.compile(r"<!-- SEO:begin.*?<!-- SEO:end -->", re.S)


class Fingerprint(HTMLParser):
    """Tag sequence with classes — structure only, no text."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.marks = []

    def handle_starttag(self, tag, attrs):
        cls = dict(attrs).get("class", "")
        self.marks.append(f"<{tag} {cls}".rstrip())

    def handle_endtag(self, tag):
        self.marks.append(f"</{tag}")


def fingerprint(path):
    fp = Fingerprint()
    fp.feed(SEO.sub("", path.read_text(encoding="utf-8")))
    return fp.marks


def main():
    problems = []
    for name in PAIRS:
        en, es = ROOT / name, ROOT / "es" / name
        if not es.exists():
            problems.append(f"{name}: no Spanish twin at es/{name}")
            continue
        a, b = fingerprint(en), fingerprint(es)
        if a == b:
            continue
        where = next((i for i, (x, y) in enumerate(zip(a, b)) if x != y), min(len(a), len(b)))
        problems.append(
            f"{name}: structure differs from es/{name} "
            f"({len(a)} vs {len(b)} elements; first difference at #{where}: "
            f"{a[where] if where < len(a) else '<end>'!r} vs "
            f"{b[where] if where < len(b) else '<end>'!r})")

    if problems:
        print("Spanish parity check FAILED:", file=sys.stderr)
        for p in problems:
            print("  " + p, file=sys.stderr)
        print("\nEvery structural edit to an English page must be mirrored in es/.",
              file=sys.stderr)
        raise SystemExit(1)
    print(f"es parity: {len(PAIRS)} page pairs structurally identical")


if __name__ == "__main__":
    main()
