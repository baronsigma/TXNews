#!/usr/bin/env bash
# setup-ssl.sh — Obtain Let's Encrypt certs and enable HTTPS for all 6 TXNews sites
#
# Run AFTER DNS A records for all 6 domains point to this server.
# Safe to re-run; certbot skips domains that already have valid certs.
#
# Usage: bash scripts/setup-ssl.sh [admin@youremail.com]

set -euo pipefail

EMAIL="${1:-admin@celinareport.com}"
REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
CONF_DIR="$REPO_DIR/nginx/conf.d"
cd "$REPO_DIR"

# Domain → WP backend container name
declare -A WP=(
  ["celinareport.com"]="wp-celina"
  ["theannanews.com"]="wp-anna"
  ["princetontxnews.com"]="wp-princeton"
  ["fatedailypost.com"]="wp-fate"
  ["melissatxnews.com"]="wp-melissa"
  ["thefulshearreport.com"]="wp-fulshear"
)

# ── Step 1: Create host directories ──────────────────────────────────────────
echo "[1/4] Creating host directories…"
mkdir -p /var/www/certbot
mkdir -p /etc/letsencrypt

# ── Step 2: Ensure nginx is running with HTTP-only config ────────────────────
echo "[2/4] Ensuring nginx is up (HTTP-only mode)…"
docker compose up -d nginx
sleep 2
docker compose exec nginx nginx -t && docker compose exec nginx nginx -s reload || true
echo "  nginx ready."

# ── Step 3: Obtain certificates via ACME webroot challenge ───────────────────
echo "[3/4] Obtaining Let's Encrypt certificates…"
FAILED=()
for domain in "${!WP[@]}"; do
  echo "  → $domain"
  if docker compose run --rm certbot certonly \
      --webroot -w /var/www/certbot \
      --email "$EMAIL" \
      --agree-tos \
      --no-eff-email \
      --non-interactive \
      -d "$domain" \
      -d "www.$domain"; then
    echo "    OK: $domain"
  else
    echo "    FAILED: $domain (skipping — DNS not ready?)"
    FAILED+=("$domain")
  fi
done

if [ ${#FAILED[@]} -gt 0 ]; then
  echo ""
  echo "WARNING: certs could not be obtained for: ${FAILED[*]}"
  echo "  Check DNS and re-run this script once DNS propagates."
fi

# Build list of domains that got certs
SUCCEEDED=()
for domain in "${!WP[@]}"; do
  if [ -f "/etc/letsencrypt/live/$domain/fullchain.pem" ]; then
    SUCCEEDED+=("$domain")
  fi
done

if [ ${#SUCCEEDED[@]} -eq 0 ]; then
  echo ""
  echo "No certs obtained. Exiting without changing nginx config."
  exit 1
fi

# ── Step 4: Write SSL-enabled nginx configs for domains with certs ───────────
echo "[4/4] Enabling HTTPS in nginx config…"
for domain in "${SUCCEEDED[@]}"; do
  backend="${WP[$domain]}"
  cat > "$CONF_DIR/$domain.conf" << NGINXEOF
server {
    listen 80;
    server_name $domain www.$domain;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 301 https://\$host\$request_uri;
    }
}

server {
    listen 443 ssl;
    server_name $domain www.$domain;

    ssl_certificate     /etc/letsencrypt/live/$domain/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$domain/privkey.pem;
    ssl_protocols       TLSv1.2 TLSv1.3;
    ssl_ciphers         HIGH:!aNULL:!MD5;

    location = /wp-login.php {
        limit_req zone=wp_login burst=3 nodelay;
        proxy_pass http://$backend:80;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location / {
        proxy_pass http://$backend:80;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 120;
        proxy_connect_timeout 60;
    }
}
NGINXEOF
  echo "  Updated: $CONF_DIR/$domain.conf"
done

docker compose exec nginx nginx -t
docker compose exec nginx nginx -s reload
echo "  nginx reloaded with HTTPS config."

echo ""
echo "Done! SSL enabled for: ${SUCCEEDED[*]}"
if [ ${#FAILED[@]} -gt 0 ]; then
  echo "Still pending (rerun when DNS is ready): ${FAILED[*]}"
fi
echo ""
echo "Test:"
for domain in "${SUCCEEDED[@]}"; do
  echo "  curl -I https://$domain"
done
