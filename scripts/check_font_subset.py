#!/usr/bin/env python3
"""Refuse to publish if the reader shows a character its font does not carry.

The reader's Chinese face is a subset cut to exactly the characters the page
displayed when scripts/build_font_subset.py last ran. Add new Chinese text and
that subset is out of date — the new character would quietly fall back to
Kaiti, which is the same brush style but not the same face.

So the build checks. It reads the character list the subsetter recorded and
compares it with what the pages show now. No font tooling is needed for this —
it is two sets of characters — which is why it can run on every build while
rebuilding the font stays an occasional, deliberate step.

Run from the repo root:  python3 scripts/check_font_subset.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_font_subset import MANIFEST, characters  # same rule, one definition

ROOT = Path(__file__).resolve().parent.parent


def main():
    if not MANIFEST.exists():
        raise SystemExit(
            "font subset missing: run python3 scripts/build_font_subset.py")
    m = json.loads(MANIFEST.read_text(encoding="utf-8"))

    woff2 = ROOT / "assets" / m["file"]
    if not woff2.exists():
        raise SystemExit(f"{m['file']} is named in the manifest but not in assets/ — "
                         "run python3 scripts/build_font_subset.py")

    missing = sorted(characters() - set(m["chars"]))
    if missing:
        print("Font subset check FAILED:", file=sys.stderr)
        print(f"  the reader now shows {len(missing)} character(s) the font does "
              f"not carry: {''.join(missing)}", file=sys.stderr)
        print("\n  rebuild it:  python3 scripts/build_font_subset.py",
              file=sys.stderr)
        raise SystemExit(1)

    print(f"font subset: {m['glyphs']} glyphs, {m['bytes'] / 1024:.0f} KB, "
          f"covers every character the reader shows")


if __name__ == "__main__":
    main()
