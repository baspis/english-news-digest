#!/usr/bin/env bash
# Commit and push site artifacts. Requires git identity via env or -c flags.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

MESSAGE="${1:-Update English News Digest site}"

GIT_NAME="${GIT_AUTHOR_NAME:-Ryosuke Takahashi}"
GIT_EMAIL="${GIT_AUTHOR_EMAIL:-ryosuke@mba-2020.local}"

git add docs/
if [ -d data/comments ]; then
  git add data/comments/
fi
if [ -d data/editions ]; then
  git add data/editions/
fi
if [ -d data/analyses ]; then
  git add data/analyses/
  git reset -q -- 'data/analyses/**/*.bak' 2>/dev/null || true
fi
if [ -d data/bodies ]; then
  git add data/bodies/
fi
if [ -d dist ]; then
  git add dist/
fi

if git diff --cached --quiet; then
  echo "Nothing to publish"
  exit 0
fi

git -c "user.name=${GIT_NAME}" -c "user.email=${GIT_EMAIL}" \
  commit -m "$MESSAGE"
git push

echo "Published to GitHub"
