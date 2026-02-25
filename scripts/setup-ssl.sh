#!/usr/bin/env bash
# setup-ssl.sh — Issue Let's Encrypt certs for all 6 domains
# Run after DNS records are pointed at this server.
# Usage: bash scripts/setup-ssl.sh admin@yourdomain.com

set -euo pipefail

EMAIL="${1:-admin@celinareport.com}"
REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_DIR"

declare -A DOMAINS=(
  ["celinareport.com"]="www.celinareport.com"
  ["theannanews.com"]="www.theannanews.com"
  ["princetontxnews.com"]="www.princetontxnews.com"
  ["fatedailypost.com"]="www.fatedailypost.com"
  ["melissatxnews.com"]="www.melissatxnews.com"
  ["thefulshearreport.com"]="www.thefulshearreport.com"
)

for primary in "${!DOMAINS[@]}"; do
  www="${DOMAINS[$primary]}"
  echo "Issuing cert for $primary + $www …"
  docker compose run --rm certbot certonly \
    --webroot -w /var/www/certbot \
    --email "$EMAIL" \
    --agree-tos \
    --no-eff-email \
    --non-interactive \
    -d "$primary" \
    -d "$www"
  echo "  OK: $primary"
done

echo ""
echo "All certs issued. Restarting nginx…"
docker compose restart nginx
echo "Done."
