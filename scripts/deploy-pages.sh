#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

"$ROOT/scripts/sync-github-pages.sh"
"$ROOT/scripts/git-publish.sh" "Update GitHub Pages site"

echo "Deployed: https://baspis.github.io/english-news-digest/"
