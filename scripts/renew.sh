#!/usr/bin/env bash
# Renew Let's Encrypt certificates and reload OpenResty.
# Certbot renews when the cert is within ~30 days of expiry (90-day lifetime); running this daily is safe.
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
if [ "${DOMAIN}" = "localhost" ]; then
  exit 0
fi

if ! docker compose --profile certbot run --rm certbot certificates 2>/dev/null | grep -qF "Certificate Name: ${DOMAIN}"; then
  exit 0
fi

docker compose --profile certbot run --rm certbot renew --non-interactive
docker compose exec -T openresty openresty -s reload
