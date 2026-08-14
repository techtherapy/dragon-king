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

rm -rf "$OUT"
mkdir -p "$OUT"

# --- pages: every root-level .html except the source sutra file ---
shopt -s nullglob
for f in *.html; do
  [[ "$f" == "$SOURCE_HTML" ]] && continue
  cp "$f" "$OUT/"
  echo "  page    $f"
done

# --- static directories ---
for d in css js assets; do
  cp -R "$d" "$OUT/"
  echo "  dir     $d/"
done

# --- Cloudflare headers file (must sit at the output root) ---
cp deploy/_headers "$OUT/_headers"
echo "  config  _headers"

# --- guard: nothing private may reach the output ---
for forbidden in "$SOURCE_HTML" info.txt extra-content scripts docs; do
  if [[ -e "$OUT/$forbidden" ]]; then
    echo "BUILD FAILED: '$forbidden' must not be published" >&2
    exit 1
  fi
done
find "$OUT" -name '.DS_Store' -delete

echo
echo "$OUT/ ready — $(find "$OUT" -type f | wc -l | tr -d ' ') files, $(du -sh "$OUT" | cut -f1)"
