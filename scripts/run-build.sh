#!/usr/bin/env bash
# Phase A: build today's edition and publish to GitHub Pages.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOG_DIR="${HOME}/logs/english-news-digest"
LOCK_FILE="/tmp/english-news-digest-build.lock"

mkdir -p "$LOG_DIR"
exec >>"${LOG_DIR}/build.log" 2>&1

echo "===== build run $(date -Iseconds) ====="

(
  flock -n 9 || { echo "Another build is running; exit"; exit 0; }
  cd "$ROOT"
  git pull --ff-only

  python3 -m english_news_digest build-edition
  "$ROOT/scripts/sync-github-pages.sh"
  "$ROOT/scripts/git-publish.sh" "Build daily edition $(date +%Y-%m-%d)"

  echo "Build complete"
) 9>"$LOCK_FILE"
