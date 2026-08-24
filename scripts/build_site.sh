#!/usr/bin/env bash
# Assemble the publishable site into dist/.
#
# Cloudflare Pages serves ONLY the build output directory, so everything the
# public should never see (source transcripts, the source sutra HTML, the
# generator scripts, design docs, extra-content/) simply never gets copied.
#
# Usage:  bash scripts/build_site.sh
# Cloudflare Pages:  build command = bash scripts/build_site.sh
#                    build output directory = dist

set -euo pipefail
cd "$(dirname "$0")/.."

OUT="dist"
# the source text the reader is generated FROM — never published
SOURCE_HTML="Dragon king sutra hailongwang_complete.html"

# the translated pages must stay structurally identical to their English twins
python3 scripts/check_translation_parity.py

# refresh canonical/OG/JSON-LD tags, sitemap.xml and robots.txt (all languages)
python3 scripts/add_seo.py

# ask Google Fonts for only the Chinese characters each page actually shows —
# runs after add_seo.py so the character set it sees is the final one
python3 scripts/subset_font_links.py > /dev/null

rm -rf "$OUT"
mkdir -p "$OUT"

# --- pages: every root-level .html except the source sutra file ---
shopt -s nullglob
for f in *.html; do
  [[ "$f" == "$SOURCE_HTML" ]] && continue
  cp "$f" "$OUT/"
  echo "  page    $f"
done

# --- translated versions, one directory per language ---
for lang in es fr; do
  mkdir -p "$OUT/$lang"
  for f in "$lang"/*.html; do
    cp "$f" "$OUT/$lang/"
    echo "  page    $f"
  done
done

# --- static directories ---
for d in css js assets; do
  cp -R "$d" "$OUT/"
  echo "  dir     $d/"
done

# --- crawler files + Cloudflare headers (all must sit at the output root) ---
for f in robots.txt sitemap.xml; do
  cp "$f" "$OUT/"
  echo "  config  $f"
done
cp deploy/_headers "$OUT/_headers"
echo "  config  _headers"

# --- guard: nothing private may reach the output ---
for forbidden in "$SOURCE_HTML" info.txt extra-content scripts docs translations; do
  if [[ -e "$OUT/$forbidden" ]]; then
    echo "BUILD FAILED: '$forbidden' must not be published" >&2
    exit 1
  fi
done
find "$OUT" -name '.DS_Store' -delete

echo
echo "$OUT/ ready — $(find "$OUT" -type f | wc -l | tr -d ' ') files, $(du -sh "$OUT" | cut -f1)"
