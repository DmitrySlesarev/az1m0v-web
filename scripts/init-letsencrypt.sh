#!/usr/bin/env bash
# Obtain the first Let's Encrypt certificate (HTTP-01 via OpenResty webroot).
# Idempotent: skips if a cert for DOMAIN already exists. After issuing, restarts OpenResty to load HTTPS.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [ -f .env ]; then
  set -a
  # shellcheck source=/dev/null
  source .env
  set +a
fi

DOMAIN="${DOMAIN:-localhost}"
EMAIL="${LETSENCRYPT_EMAIL:-}"

if [ -z "${EMAIL}" ] || [ "${DOMAIN}" = "localhost" ]; then
  echo "init-letsencrypt: skipping (set DOMAIN and LETSENCRYPT_EMAIL in .env for production TLS)."
  exit 0
fi

STAGING_ARGS=()
if [ "${CERTBOT_STAGING:-0}" = "1" ]; then
  STAGING_ARGS=(--staging)
  echo "init-letsencrypt: using Let's Encrypt STAGING (test) CA."
fi

if docker compose --profile certbot run --rm certbot certificates 2>/dev/null | grep -qF "Certificate Name: ${DOMAIN}"; then
  echo "init-letsencrypt: certificate already present for ${DOMAIN}; restarting OpenResty to pick up TLS config."
  docker compose restart openresty
  exit 0
fi

echo "init-letsencrypt: requesting certificate for ${DOMAIN} …"
docker compose --profile certbot run --rm certbot certonly \
  --webroot \
  -w /var/www/certbot \
  --non-interactive \
  --agree-tos \
  --no-eff-email \
  --email "${EMAIL}" \
  "${STAGING_ARGS[@]}" \
  -d "${DOMAIN}"

echo "init-letsencrypt: restarting OpenResty to enable HTTPS."
docker compose restart openresty
