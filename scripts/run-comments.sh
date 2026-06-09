#!/usr/bin/env bash
# Phase B: fetch due JT comments (24h+ after edition build), render, publish.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOG_DIR="${HOME}/logs/english-news-digest"
LOCK_FILE="/tmp/english-news-digest-comments.lock"

mkdir -p "$LOG_DIR"
exec >>"${LOG_DIR}/comments.log" 2>&1

echo "===== comments run $(date -Iseconds) ====="

(
  flock -n 9 || { echo "Another comments job is running; exit"; exit 0; }
  cd "$ROOT"
  git pull --ff-only

  python3 -m english_news_digest fetch-comments
  "$ROOT/scripts/sync-github-pages.sh"
  "$ROOT/scripts/git-publish.sh" "Update reader comments $(date +%Y-%m-%d)"

  echo "Comments job complete"
) 9>"$LOCK_FILE"
