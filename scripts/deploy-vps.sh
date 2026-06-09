#!/usr/bin/env bash
set -euo pipefail

HOST="${DEPLOY_HOST:-llm-devbox}"
REMOTE_DIR="/home/ubuntu/projects/english-news-digest"

ssh "$HOST" bash -s <<EOF
set -euo pipefail
if [ -d "$REMOTE_DIR/.git" ]; then
  cd "$REMOTE_DIR"
  git pull --ff-only
else
  git clone git@github.com:baspis/english-news-digest.git "$REMOTE_DIR"
  cd "$REMOTE_DIR"
fi
tailscale serve --bg "$REMOTE_DIR/dist"
tailscale serve status
EOF

echo "Deployed. Open https://llm-devbox/ on Tailscale."
