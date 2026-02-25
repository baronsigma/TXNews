#!/usr/bin/env bash
# ============================================================
# deploy.sh — Full EC2 bootstrap for TXNews
#
# Run once on a fresh Ubuntu 24 EC2 instance.
# After this script completes, run init-sites.sh to configure WordPress.
#
# Usage (as root or with sudo):
#   git clone <repo> /opt/txnews
#   cd /opt/txnews
#   cp .env.example .env && nano .env
#   bash scripts/deploy.sh
# ============================================================

set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
echo "TXNews deploy — repo: $REPO_DIR"

# ── 1. System Updates ─────────────────────────────────────────────────────────
echo "[1/7] System update…"
apt-get update -qq
apt-get install -y --no-install-recommends \
  curl wget git unzip ca-certificates gnupg lsb-release \
  ufw fail2ban

# ── 2. Docker ─────────────────────────────────────────────────────────────────
echo "[2/7] Installing Docker…"
if ! command -v docker &>/dev/null; then
  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
    | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
  chmod a+r /etc/apt/keyrings/docker.gpg
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
    https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" \
    | tee /etc/apt/sources.list.d/docker.list
  apt-get update -qq
  apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
  systemctl enable --now docker
  echo "  Docker installed."
else
  echo "  Docker already installed."
fi

# ── 3. Ollama ─────────────────────────────────────────────────────────────────
echo "[3/7] Installing Ollama (host service)…"
if ! command -v ollama &>/dev/null; then
  curl -fsSL https://ollama.ai/install.sh | sh
  systemctl enable --now ollama
  sleep 5
  echo "  Pulling qwen2.5:3b (this may take a few minutes)…"
  ollama pull qwen2.5:3b
  echo "  Ollama ready."
else
  echo "  Ollama already installed."
  ollama pull qwen2.5:3b 2>/dev/null || true
fi

# ── 4. Firewall ───────────────────────────────────────────────────────────────
echo "[4/7] Configuring UFW firewall…"
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 5678/tcp comment 'n8n'
ufw allow 5001/tcp comment 'scraper (internal)'
ufw --force enable
echo "  Firewall configured."

# ── 5. Docker Compose ─────────────────────────────────────────────────────────
echo "[5/7] Starting Docker Compose stack…"
cd "$REPO_DIR"

if [ ! -f ".env" ]; then
  echo "  ERROR: .env file not found. Copy .env.example and fill in values."
  exit 1
fi

docker compose pull
docker compose build
docker compose up -d

echo "  Docker Compose stack started."
echo "  Waiting 90 seconds for MySQL to initialize…"
sleep 90

# ── 6. SSL (Let's Encrypt) ────────────────────────────────────────────────────
echo "[6/7] SSL certificates (Let's Encrypt)…"
echo ""
echo "  DNS must point to this server BEFORE running certbot."
echo "  When ready, run the following for each domain:"
echo ""
DOMAINS=(
  "celinareport.com www.celinareport.com"
  "theannanews.com www.theannanews.com"
  "princetontxnews.com www.princetontxnews.com"
  "fatedailypost.com www.fatedailypost.com"
  "melissatxnews.com www.melissatxnews.com"
  "thefulshearreport.com www.thefulshearreport.com"
)
for dom in "${DOMAINS[@]}"; do
  primary="${dom%% *}"
  echo "  docker compose run --rm certbot certonly --webroot -w /var/www/certbot \\"
  echo "    --email admin@${primary} --agree-tos --no-eff-email \\"
  for d in $dom; do echo "    -d $d \\"; done
  echo ""
done
echo "  After certbot: docker compose restart nginx"
echo ""

# ── 7. WordPress Init ─────────────────────────────────────────────────────────
echo "[7/7] Initializing WordPress sites…"
bash "$REPO_DIR/scripts/init-sites.sh"

echo ""
echo "============================================================"
echo "TXNews deployment complete!"
echo ""
echo "Access:"
echo "  WordPress sites: https://celinareport.com (etc.)"
echo "  n8n dashboard:   http://$(curl -s ifconfig.me 2>/dev/null || echo YOUR_IP):5678"
echo "  Scraper health:  http://localhost:5001/health"
echo "  Ollama:          http://localhost:11434"
echo ""
echo "Next: Import n8n workflows from n8n-workflows/generated/"
echo "============================================================"
