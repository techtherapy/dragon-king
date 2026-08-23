#!/usr/bin/env python3
"""Fail the build when the site's language versions drift apart.

English lives at the root and is the source; each translated version lives in
its own directory (`es/`, `fr/`). Three independent checks, because there are
three ways a version can diverge:

  1. STRUCTURE — every version is the same markup with different words in it,
     so the element sequence (tags + classes) must be identical to English.
     Catches: a section added, a class renamed, a block reordered in one
     language only.

  2. TEXT — a hash of each page's visible words is recorded in
     translations/parity.json. If the English text changes and a translation
     does not, that translation is now stale. Catches the common failure that
     structure alone cannot see: rewording a sentence in one language.

  3. GENERATOR STRINGS — the string tables inside the page generators must
     define the same keys in every language, so a new label cannot ship in
     English with nothing behind it in Spanish or French.

After legitimately updating every language, re-record the text baseline:

    python3 scripts/check_translation_parity.py --record

Run from the repo root:  python3 scripts/check_translation_parity.py
"""
import hashlib
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "translations" / "parity.json"

# The translated versions. English at the root is the source they follow.
# Adding a language here is most of what it takes to add one to the site.
LANGS = ["es", "fr"]

# Hand-authored pages, edited directly in every language.
PAIRS = [
    "index.html",
    "about.html",
    "refuge.html",
    "contact.html",
    "his-holiness-living-buddha-lian-sheng.html",
    "treasure-vase-wishes.html",
    "nagas-and-dragon-kings.html",
]
# Generated pages are omitted: one generator emits every language from one
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
    """The generators' string tables must cover every language."""
    sys.path.insert(0, str(ROOT / "scripts"))
    import build_practice as bp
    import build_reader as br

    problems = []
    for name, table in (("UI", bp.UI), ("CAPTIONS", bp.CAPTIONS)):
        for lang in LANGS:
            if lang not in table:
                problems.append(f"build_practice.{name}: no '{lang}' table at all")
                continue
            missing = set(table["en"]) - set(table[lang])
            extra = set(table[lang]) - set(table["en"])
            if missing:
                problems.append(
                    f"build_practice.{name}: no {lang} for {sorted(missing)}")
            if extra:
                problems.append(
                    f"build_practice.{name}: {lang} has keys English lacks: {sorted(extra)}")
    for lang in LANGS:
        if lang not in br.CHROME:
            problems.append(f"build_reader.CHROME: no '{lang}' chrome table")
    return problems


def main():
    record = "--record" in sys.argv
    baseline = json.loads(MANIFEST.read_text()) if MANIFEST.exists() else {}
    fresh, problems, stale = {}, [], []

    for name in PAIRS:
        en = ROOT / name
        en_marks, en_hash = read_page(en)
        fresh[name] = {"en": en_hash}

        for lang in LANGS:
            twin = ROOT / lang / name
            if not twin.exists():
                problems.append(f"{name}: no {lang} version at {lang}/{name}")
                continue

            marks, digest = read_page(twin)
            fresh[name][lang] = digest

            # 1. structure
            if en_marks != marks:
                where = next((i for i, (a, b) in enumerate(zip(en_marks, marks)) if a != b),
                             min(len(en_marks), len(marks)))
                problems.append(
                    f"{name}: structure differs from {lang}/{name} "
                    f"({len(en_marks)} vs {len(marks)} elements; first difference at "
                    f"#{where}: {en_marks[where] if where < len(en_marks) else '<end>'!r} vs "
                    f"{marks[where] if where < len(marks) else '<end>'!r})")

            # 2. text drift, against the recorded baseline
            was = baseline.get(name)
            if was and not record and lang in was:
                if was["en"] != en_hash and was[lang] == digest:
                    stale.append(f"{name}: the English text changed but {lang}/{name} did not")

    problems += generator_strings()

    if record:
        MANIFEST.parent.mkdir(exist_ok=True)
        MANIFEST.write_text(json.dumps(fresh, indent=1, sort_keys=True) + "\n")
        print(f"parity baseline recorded for {len(fresh)} pages "
              f"x {len(LANGS) + 1} languages")
        return

    if problems or stale:
        print("Translation parity check FAILED:", file=sys.stderr)
        for p in problems + stale:
            print("  " + p, file=sys.stderr)
        if stale:
            print("\nTranslate the change into every language, then re-record:\n"
                  "  python3 scripts/check_translation_parity.py --record", file=sys.stderr)
        if problems:
            print("\nEvery structural edit to an English page must be mirrored in "
                  + " and ".join(f"{lang}/" for lang in LANGS) + ".", file=sys.stderr)
        raise SystemExit(1)

    langs = ", ".join(["en"] + LANGS)
    if not baseline:
        print(f"parity: {len(PAIRS)} pages x ({langs}) structurally identical "
              f"(no text baseline yet — run with --record)")
    else:
        print(f"parity: {len(PAIRS)} pages identical in structure across "
              f"({langs}), text in step, generator strings complete")


if __name__ == "__main__":
    main()
