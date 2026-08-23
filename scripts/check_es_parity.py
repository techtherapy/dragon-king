#!/usr/bin/env python3
"""Fail the build when the English and Spanish sites drift apart.

Three independent checks, because there are three ways they can diverge:

  1. STRUCTURE — the two versions are the same markup with different words
     in it, so their element sequence (tags + classes) must be identical.
     Catches: a section added, a class renamed, a block reordered on one
     side only.

  2. TEXT — a hash of each page's visible words is recorded in
     translations/parity.json. If the English text changes and the Spanish
     does not, the Spanish is now stale. Catches the common failure that
     structure alone cannot see: rewording a sentence in one language.

  3. GENERATOR STRINGS — the bilingual string tables inside the page
     generators must define the same keys in both languages, so a new
     label cannot ship in English with nothing behind it in Spanish.

After legitimately updating both languages, re-record the text baseline:

    python3 scripts/check_es_parity.py --record

Run from the repo root:  python3 scripts/check_es_parity.py
"""
import hashlib
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "translations" / "parity.json"

# Hand-authored pages, edited directly in both languages.
PAIRS = [
    "index.html",
    "about.html",
    "refuge.html",
    "contact.html",
    "his-holiness-living-buddha-lian-sheng.html",
    "treasure-vase-wishes.html",
    "nagas-and-dragon-kings.html",
]
# Generated pages are omitted: one generator emits both languages from one
# template, so they cannot drift structurally. Their risk is check 3.
GENERATED = ["read.html", "treasure-vase-yoga.html"]

# The SEO block is regenerated per language and is expected to differ.
SEO = re.compile(r"<!-- SEO:begin.*?<!-- SEO:end -->", re.S)


class Extract(HTMLParser):
    """Collects the element sequence and the visible text of a page."""

    SKIP = {"script", "style"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.marks = []
        self.words = []
        self._muted = 0

    def handle_starttag(self, tag, attrs):
        cls = dict(attrs).get("class", "")
        self.marks.append(f"<{tag} {cls}".rstrip())
        if tag in self.SKIP:
            self._muted += 1

    def handle_endtag(self, tag):
        self.marks.append(f"</{tag}")
        if tag in self.SKIP and self._muted:
            self._muted -= 1

    def handle_data(self, data):
        if not self._muted and data.strip():
            self.words.append(" ".join(data.split()))


def read_page(path):
    e = Extract()
    e.feed(SEO.sub("", path.read_text(encoding="utf-8")))
    text = "\n".join(e.words)
    return e.marks, hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def generator_strings():
    """Both string tables in the page generators must cover both languages."""
    sys.path.insert(0, str(ROOT / "scripts"))
    import build_practice as bp

    problems = []
    for name, table in (("UI", bp.UI), ("CAPTIONS", bp.CAPTIONS)):
        only_en = set(table["en"]) - set(table["es"])
        only_es = set(table["es"]) - set(table["en"])
        if only_en:
            problems.append(f"build_practice.{name}: missing Spanish for {sorted(only_en)}")
        if only_es:
            problems.append(f"build_practice.{name}: missing English for {sorted(only_es)}")
    return problems


def main():
    record = "--record" in sys.argv
    baseline = json.loads(MANIFEST.read_text()) if MANIFEST.exists() else {}
    fresh, problems, stale = {}, [], []

    for name in PAIRS:
        en, es = ROOT / name, ROOT / "es" / name
        if not es.exists():
            problems.append(f"{name}: no Spanish twin at es/{name}")
            continue

        en_marks, en_hash = read_page(en)
        es_marks, es_hash = read_page(es)
        fresh[name] = {"en": en_hash, "es": es_hash}

        # 1. structure
        if en_marks != es_marks:
            where = next((i for i, (a, b) in enumerate(zip(en_marks, es_marks)) if a != b),
                         min(len(en_marks), len(es_marks)))
            problems.append(
                f"{name}: structure differs from es/{name} "
                f"({len(en_marks)} vs {len(es_marks)} elements; first difference at "
                f"#{where}: {en_marks[where] if where < len(en_marks) else '<end>'!r} vs "
                f"{es_marks[where] if where < len(es_marks) else '<end>'!r})")

        # 2. text drift, against the recorded baseline
        was = baseline.get(name)
        if was and not record:
            if was["en"] != en_hash and was["es"] == es_hash:
                stale.append(f"{name}: the English text changed but es/{name} did not")

    problems += generator_strings()

    if record:
        MANIFEST.parent.mkdir(exist_ok=True)
        MANIFEST.write_text(json.dumps(fresh, indent=1, sort_keys=True) + "\n")
        print(f"parity baseline recorded for {len(fresh)} page pairs")
        return

    if problems or stale:
        print("Spanish parity check FAILED:", file=sys.stderr)
        for p in problems + stale:
            print("  " + p, file=sys.stderr)
        if stale:
            print("\nTranslate the change into es/, then re-record the baseline:\n"
                  "  python3 scripts/check_es_parity.py --record", file=sys.stderr)
        if problems:
            print("\nEvery structural edit to an English page must be mirrored in es/.",
                  file=sys.stderr)
        raise SystemExit(1)

    if not baseline:
        print(f"es parity: {len(PAIRS)} page pairs structurally identical "
              f"(no text baseline yet — run with --record)")
    else:
        print(f"es parity: {len(PAIRS)} page pairs identical in structure, "
              f"text in step, generator strings complete")


if __name__ == "__main__":
    main()
