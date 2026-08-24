#!/usr/bin/env python3
"""Cut the Chinese font down to the characters the reader actually shows.

Google serves LXGW WenKai TC as 230 files split by character code, so the
reader's 1,273 characters pull about 3.6 MB. Every other page now asks Google
for exactly its own characters (scripts/subset_font_links.py), but the reader
has too many to name in a URL, so it gets a self-hosted subset instead.

Nothing is installed globally and the 15 MB source font never enters the repo:
both live in ~/.cache/dragon-king-fonts/. What lands in the repo is one small
woff2, the font's licence, and a manifest recording exactly which characters
are inside — scripts/check_font_subset.py reads that manifest on every build
and fails if a page has gained a character the font does not carry.

Run from the repo root:  python3 scripts/build_font_subset.py
"""
import hashlib
import json
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE = Path.home() / ".cache" / "dragon-king-fonts"
VERSION = "v1.522"
SRC_NAME = f"LXGWWenKaiTC-Regular-{VERSION}.ttf"
SRC_URL = (f"https://github.com/lxgw/LxgwWenKaiTC/releases/download/{VERSION}"
           f"/LXGWWenKaiTC-Regular.ttf")
OFL_URL = "https://raw.githubusercontent.com/lxgw/LxgwWenKaiTC/main/OFL.txt"
READERS = ["read.html", "es/read.html", "fr/read.html"]
MANIFEST = ROOT / "scripts" / "wenkai-subset.json"
LICENCE = ROOT / "assets" / "LXGWWenKaiTC-OFL.txt"


def tooling():
    """pyftsubset in a cached venv of its own — nothing touches system Python."""
    venv = CACHE / "venv"
    exe = venv / "bin" / "pyftsubset"
    if not exe.exists():
        print("  creating an isolated venv for fonttools…")
        CACHE.mkdir(parents=True, exist_ok=True)
        subprocess.run([sys.executable, "-m", "venv", str(venv)], check=True)
        subprocess.run([str(venv / "bin" / "pip"), "install", "-q",
                        "--disable-pip-version-check", "fonttools", "brotli"], check=True)
    return exe


def source_font():
    CACHE.mkdir(parents=True, exist_ok=True)
    dst = CACHE / SRC_NAME
    if not dst.exists():
        print(f"  downloading {SRC_NAME} (about 15 MB, once)…")
        urllib.request.urlretrieve(SRC_URL, dst)
    assert dst.stat().st_size > 5_000_000, f"{dst} looks truncated"
    return dst


def characters():
    """Every distinct character the reader displays, plus printable ASCII.

    Deliberately not just the ideographs: the volume headings read
    "卷一 · Vol I" inside an element set to the Chinese face, so its Latin has
    to be in the subset too, and the text carries fullwidth punctuation and a
    few symbols (☰ ☸ ⎙) that a narrower rule would have dropped."""
    chars = {chr(c) for c in range(0x20, 0x7F)}
    for name in READERS:
        s = (ROOT / name).read_text(encoding="utf-8")
        s = re.sub(r"<!-- SEO:begin.*?<!-- SEO:end -->", " ", s, flags=re.S)
        s = re.sub(r"<(script|style)\b.*?</\1>", " ", s, flags=re.S)
        chars |= set(re.sub(r"<[^>]+>", " ", s))
    return {c for c in chars if c.isprintable() and not c.isspace()}


def build():
    exe = tooling()
    src = source_font()
    chars = characters()
    text = "".join(sorted(chars))

    stamp = hashlib.sha256((VERSION + text).encode("utf-8")).hexdigest()[:8]
    out = ROOT / "assets" / f"wenkai-reader.{stamp}.woff2"

    chars_file = CACHE / "chars.txt"
    chars_file.write_text(text, encoding="utf-8")
    subprocess.run([str(exe), str(src), f"--text-file={chars_file}",
                    "--flavor=woff2", "--name-IDs=*", f"--output-file={out}"],
                   check=True, capture_output=True)

    # a stale copy would be dead weight in the published output
    for old in (ROOT / "assets").glob("wenkai-reader.*.woff2"):
        if old != out:
            old.unlink()
            print(f"  removed superseded {old.name}")

    if not LICENCE.exists():
        urllib.request.urlretrieve(OFL_URL, LICENCE)
        print(f"  fetched {LICENCE.name} (the licence must ship with the font)")

    MANIFEST.write_text(json.dumps({
        "file": out.name,
        "source": f"LXGW WenKai TC Regular {VERSION}",
        "glyphs": len(chars),
        "bytes": out.stat().st_size,
        "chars": text,
    }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    full = src.stat().st_size / 1024
    print(f"  {out.name}: {len(chars)} glyphs, {out.stat().st_size / 1024:.0f} KB "
          f"(from {full / 1024:.1f} MB)")
    print(f"  manifest written to {MANIFEST.relative_to(ROOT)}")


if __name__ == "__main__":
    build()
