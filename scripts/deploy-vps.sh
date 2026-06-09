#!/usr/bin/env bash
set -euo pipefail

HOST="${DEPLOY_HOST:-llm-devbox}"
REMOTE_DIR="/home/ubuntu/projects/english-news-digest"
REPO="git@github.com:baspis/english-news-digest.git"

ssh "$HOST" bash -s <<EOF
set -euo pipefail
if [ -d "$REMOTE_DIR/.git" ]; then
  cd "$REMOTE_DIR"
  git pull --ff-only
else
  git clone "$REPO" "$REMOTE_DIR"
  cd "$REMOTE_DIR"
fi

TS_IP="\$(tailscale ip -4)"
sudo tee /etc/systemd/system/english-news-digest.service >/dev/null <<UNIT
[Unit]
Description=English News Digest static site (Tailscale only)
After=network-online.target tailscaled.service
Wants=network-online.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=$REMOTE_DIR/dist
ExecStart=/usr/bin/python3 -m http.server 8765 --bind \${TS_IP}
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
UNIT

sudo systemctl daemon-reload
sudo systemctl enable --now english-news-digest.service
sudo systemctl --no-pager --full status english-news-digest.service | head -15
EOF

echo ""
echo "Deployed."
echo "  GitHub: https://github.com/baspis/english-news-digest"
echo "  VPS:    http://llm-devbox:8765/  (Tailscale required)"
