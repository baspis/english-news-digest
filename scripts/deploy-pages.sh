#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

"$ROOT/scripts/sync-github-pages.sh"

if git diff --quiet docs && git diff --cached --quiet docs; then
  echo "docs/ unchanged — nothing to deploy"
  exit 0
fi

git add docs/
git commit -m "Update GitHub Pages site"
git push

echo "Deployed: https://baspis.github.io/english-news-digest/"
