#!/usr/bin/env bash
set -euo pipefail

DOMAIN="${DOMAIN:-localhost}"
CONF_OUT="/usr/local/openresty/nginx/conf/nginx.conf"
HTTP_T="/etc/nginx/templates/nginx-http.conf.template"
HTTPS_T="/etc/nginx/templates/nginx-https.conf.template"

render() {
  sed "s|@@DOMAIN@@|${DOMAIN}|g" "$1" > "${CONF_OUT}"
}

if [ -f "/etc/letsencrypt/live/${DOMAIN}/fullchain.pem" ] \
   && [ -f "/etc/letsencrypt/live/${DOMAIN}/privkey.pem" ]; then
  echo "openresty: TLS certificates found for ${DOMAIN}; enabling HTTPS."
  render "${HTTPS_T}"
else
  echo "openresty: no TLS certs for ${DOMAIN} (HTTP only). Run scripts/init-letsencrypt.sh after DNS points here."
  render "${HTTP_T}"
fi

exec openresty -g "daemon off;"
