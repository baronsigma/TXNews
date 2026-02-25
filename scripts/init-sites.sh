#!/usr/bin/env bash
# ============================================================
# init-sites.sh — First-time WordPress site initialization
#
# Runs WP-CLI inside each WordPress container to:
#   1. Finish WP install (core install)
#   2. Create standard categories (in order so IDs are predictable)
#   3. Set theme (civic-record) and customizer options
#   4. Create Application Password for the admin user
#   5. Delete default posts/pages
#   6. Set permalink structure
#
# Prerequisites:
#   - docker-compose up -d (all containers running)
#   - .env file sourced
#   - wp-cli bundled in containers (it's in the WP official image)
#   - Wait ~60 seconds after first docker-compose up for DB to initialize
#
# Usage:
#   cp .env.example .env && nano .env    # fill in passwords
#   docker-compose up -d
#   sleep 90
#   bash scripts/init-sites.sh
# ============================================================

set -euo pipefail

# Load env
if [ -f "$(dirname "$0")/../.env" ]; then
  # shellcheck disable=SC1091
  source "$(dirname "$0")/../.env"
fi

# ─── Site Definitions ────────────────────────────────────────────────────────
# Format: "container|domain|city_name|publication_name|accent_color|about_text"
declare -a SITES=(
  "txnews-wp-celina|celinareport.com|Celina|The Celina Report|#1A5C38|An automated civic intelligence publication covering local government, development, and community news in Celina, Texas."
  "txnews-wp-anna|theannanews.com|Anna|Anna Record|#7B2D00|Independent civic journalism covering Anna, Texas — government, development, and community news, generated continuously from public data."
  "txnews-wp-princeton|princetontxnews.com|Princeton|Princeton TX News|#7B2D00|Automated civic coverage of Princeton, Texas — permits, agendas, and business activity from public records."
  "txnews-wp-fate|fatedailypost.com|Fate|Fate Daily Post|#2C4A7C|The Fate Daily Post covers Fate, Texas with automated civic intelligence drawn from public government data sources."
  "txnews-wp-melissa|melissatxnews.com|Melissa|Melissa TX News|#1D5A6B|Civic news for Melissa, Texas — building permits, city council agendas, and business activity, published automatically."
  "txnews-wp-fulshear|thefulshearreport.com|Fulshear|The Fulshear Report|#4A1942|An automated civic record for Fulshear, Texas — tracking development, governance, and business growth in Fort Bend County."
)

# ─── WP-CLI helper ───────────────────────────────────────────────────────────
# The wordpress:apache image has no WP-CLI; run it via the official wordpress:cli
# image, sharing the WP container's volumes and network.
wp() {
  local container="$1"; shift
  local db_host db_name db_user db_pass
  db_host=$(docker exec "$container" sh -c 'echo "$WORDPRESS_DB_HOST"')
  db_name=$(docker exec "$container" sh -c 'echo "$WORDPRESS_DB_NAME"')
  db_user=$(docker exec "$container" sh -c 'echo "$WORDPRESS_DB_USER"')
  db_pass=$(docker exec "$container" sh -c 'echo "$WORDPRESS_DB_PASSWORD"')
  # MySQL 8.0 uses self-signed certs; disable SSL verification in the MariaDB client
  local mycnf
  mycnf=$(mktemp)
  printf '[client]\nssl=0\n' > "$mycnf"
  docker run --rm \
    --network txnews_txnews \
    --volumes-from "$container" \
    -e WORDPRESS_DB_HOST="$db_host" \
    -e WORDPRESS_DB_NAME="$db_name" \
    -e WORDPRESS_DB_USER="$db_user" \
    -e WORDPRESS_DB_PASSWORD="$db_pass" \
    -v "$mycnf:/root/.my.cnf:ro" \
    wordpress:cli \
    wp --allow-root "$@"
  local rc=$?
  rm -f "$mycnf"
  return $rc
}

# ─── Wait for WordPress to be ready ──────────────────────────────────────────
wait_for_wp() {
  local container="$1"
  local domain="$2"
  echo "  Waiting for $container DB connection…"
  local max=30
  local i=0
  # Use --skip-wordpress + raw mysqli_connect() so we:
  #   1. Don't require WP tables to exist yet (avoids "site not installed" error)
  #   2. Go through PHP/MySQLi, not the MariaDB CLI (avoids SSL cert rejection)
  local last_err=""
  until last_err=$(wp "$container" eval --skip-wordpress \
      'if(@mysqli_connect(getenv("WORDPRESS_DB_HOST"),getenv("WORDPRESS_DB_USER"),getenv("WORDPRESS_DB_PASSWORD"),getenv("WORDPRESS_DB_NAME"))){echo "db_ok";}else{echo mysqli_connect_error();exit(1);}' \
      2>&1) && echo "$last_err" | grep -q "db_ok"; do
    i=$((i + 1))
    if [ "$i" -ge "$max" ]; then
      echo "  ERROR: $container DB not ready after ${max} attempts. Aborting."
      echo "  Last wp-cli output: $last_err"
      exit 1
    fi
    sleep 3
  done
  echo "  DB ready."
}

# ─── Initialize One Site ─────────────────────────────────────────────────────
init_site() {
  local container="$1"
  local domain="$2"
  local city="$3"
  local publication="$4"
  local accent="$5"
  local about="$6"

  echo ""
  echo "======================================================"
  echo "  Initializing: $publication ($domain)"
  echo "======================================================"

  wait_for_wp "$container" "$domain"

  # ── Core Install ────────────────────────────────────────────────────────────
  if ! wp "$container" core is-installed 2>/dev/null; then
    echo "  Running wp core install…"
    wp "$container" core install \
      --url="https://${domain}" \
      --title="$publication" \
      --admin_user="admin" \
      --admin_password="${WP_ADMIN_PASSWORD:-changeme_admin_pass}" \
      --admin_email="admin@${domain}" \
      --skip-email
    echo "  Core installed."
  else
    echo "  Core already installed, skipping."
  fi

  # ── Permalink Structure ─────────────────────────────────────────────────────
  wp "$container" rewrite structure '/%category%/%postname%/' --hard
  echo "  Permalink structure set."

  # ── Delete Default Content ──────────────────────────────────────────────────
  wp "$container" post delete 1 2 --force 2>/dev/null || true
  echo "  Default posts removed."

  # ── Categories ──────────────────────────────────────────────────────────────
  # Created in order so IDs are predictable:
  #   ID 2 = Development
  #   ID 3 = Civic Governance
  #   ID 4 = Business
  #   ID 5 = Public Notices
  #   ID 6 = Schools & Education
  echo "  Creating categories…"
  declare -A CAT_DEFS=(
    ["development"]="Development"
    ["civic-governance"]="Civic Governance"
    ["business"]="Business"
    ["public-notices"]="Public Notices"
    ["schools-education"]="Schools & Education"
  )
  for slug in development civic-governance business public-notices schools-education; do
    local label="${CAT_DEFS[$slug]}"
    if ! wp "$container" term get category "$slug" --field=term_id 2>/dev/null; then
      wp "$container" term create category "$label" --slug="$slug" --porcelain
      echo "    Created: $label ($slug)"
    else
      echo "    Exists: $label"
    fi
  done

  # ── Activate Civic Record Theme ─────────────────────────────────────────────
  wp "$container" theme activate civic-record
  echo "  Theme activated: civic-record"

  # ── Set Customizer Options (theme_mods) ─────────────────────────────────────
  wp "$container" option update theme_mods_civic-record \
    "{\"civic_city_name\":\"${city}\",\"civic_publication_name\":\"${publication}\",\"civic_accent_color\":\"${accent}\",\"civic_about_text\":\"${about}\"}" \
    --format=json
  echo "  Customizer options set (city=$city, accent=$accent)"

  # ── Set Static Front Page ──────────────────────────────────────────────────
  wp "$container" option update show_on_front 'posts'
  echo "  Front page: latest posts."

  # ── Disable Comments ────────────────────────────────────────────────────────
  wp "$container" option update default_comment_status 'closed'
  wp "$container" option update default_ping_status 'closed'
  echo "  Comments disabled."

  # ── Create Application Password for REST API (n8n will use this) ─────────────
  echo "  Generating Application Password for n8n…"
  APP_PASS=$(wp "$container" user application-password create admin "n8n-txnews" --porcelain 2>/dev/null || echo "ALREADY_EXISTS")
  if [ "$APP_PASS" != "ALREADY_EXISTS" ] && [ -n "$APP_PASS" ]; then
    echo ""
    echo "  *** SAVE THIS — Application Password for $domain ***"
    echo "  Username: admin"
    echo "  App Pass: $APP_PASS"
    echo "  Use in: n8n-workflows/generated/ — replace REPLACE_WITH_APP_PASS_${city^^}"
    echo ""
  else
    echo "  Application Password already exists (check WP admin to retrieve/reset)."
  fi

  # ── Install & Activate Useful Plugins ──────────────────────────────────────
  # Application Passwords requires WP 5.6+ (included); no extra plugin needed.
  # Add any others here as needed.

  echo "  $publication initialization complete."
}

# ─── Main ────────────────────────────────────────────────────────────────────

echo ""
echo "TXNews — Site Initialization Script"
echo "====================================="
echo "This will initialize all 6 WordPress sites."
echo "Press Ctrl+C to abort, or Enter to continue…"
read -r

for site_def in "${SITES[@]}"; do
  IFS='|' read -r container domain city publication accent about <<< "$site_def"
  init_site "$container" "$domain" "$city" "$publication" "$accent" "$about"
done

echo ""
echo "====================================="
echo "All 6 sites initialized."
echo ""
echo "Next steps:"
echo "1. Copy Application Passwords above into n8n-workflows/generated/*.json"
echo "2. python3 n8n-workflows/generate_workflows.py   (if regenerating)"
echo "3. Import workflows into n8n (http://YOUR_EC2_IP:5678)"
echo "4. Activate each workflow in n8n"
echo "5. Set up SSL: bash scripts/setup-ssl.sh"
echo "====================================="
