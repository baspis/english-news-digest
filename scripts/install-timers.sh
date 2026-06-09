#!/usr/bin/env bash
# Install systemd timers for automated build + comment fetch on this host.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
UNIT_DIR="${ROOT}/scripts/systemd"

chmod +x "${ROOT}/scripts/run-build.sh" "${ROOT}/scripts/run-comments.sh" "${ROOT}/scripts/git-publish.sh"

sudo cp "${UNIT_DIR}/english-news-digest-build.service" /etc/systemd/system/
sudo cp "${UNIT_DIR}/english-news-digest-build.timer" /etc/systemd/system/
sudo cp "${UNIT_DIR}/english-news-digest-comments.service" /etc/systemd/system/
sudo cp "${UNIT_DIR}/english-news-digest-comments.timer" /etc/systemd/system/

sudo systemctl daemon-reload
sudo systemctl enable --now english-news-digest-build.timer
sudo systemctl enable --now english-news-digest-comments.timer

echo ""
echo "Timers installed:"
systemctl list-timers --no-pager 'english-news-digest-*'
echo ""
echo "Logs:"
echo "  ${HOME}/logs/english-news-digest/build.log"
echo "  ${HOME}/logs/english-news-digest/comments.log"
