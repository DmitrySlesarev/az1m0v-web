#!/usr/bin/env bash
# Install a daily systemd timer that runs scripts/renew.sh (Let's Encrypt + nginx reload).
# Requires sudo and a user in the docker group.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SERVICE_SRC="${ROOT}/deploy/systemd/az1m0v-web-certbot.service"
TIMER_SRC="${ROOT}/deploy/systemd/az1m0v-web-certbot.timer"

if [ ! -f "${SERVICE_SRC}" ] || [ ! -f "${TIMER_SRC}" ]; then
  echo "install-systemd: missing unit files under deploy/systemd/"
  exit 1
fi

TMP_SVC="$(mktemp)"
sed "s|@@INSTALL_DIR@@|${ROOT}|g" "${SERVICE_SRC}" > "${TMP_SVC}"

sudo install -m 644 "${TMP_SVC}" /etc/systemd/system/az1m0v-web-certbot.service
sudo install -m 644 "${TIMER_SRC}" /etc/systemd/system/az1m0v-web-certbot.timer
rm -f "${TMP_SVC}"

sudo systemctl daemon-reload
sudo systemctl enable --now az1m0v-web-certbot.timer

echo "install-systemd: enabled az1m0v-web-certbot.timer (daily renew). Check: systemctl status az1m0v-web-certbot.timer"
