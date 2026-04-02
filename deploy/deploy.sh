#!/usr/bin/env bash
# Update code and containers on the server: pull, rebuild, start, TLS bootstrap.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [ -d .git ]; then
  git pull --ff-only
fi

docker compose build
docker compose up -d
./scripts/init-letsencrypt.sh

echo "deploy: done. If this is the first TLS setup, ensure DNS for DOMAIN points to this host before init-letsencrypt."
