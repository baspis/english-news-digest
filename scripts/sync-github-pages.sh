#!/usr/bin/env bash
# Sync built static site from dist/ to docs/ for GitHub Pages.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

rm -rf docs
mkdir -p docs
cp -R dist/. docs/

echo "Synced dist/ -> docs/ ($(find docs -name '*.html' | wc -l | tr -d ' ') HTML files)"
