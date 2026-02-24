#!/bin/sh
set -e

log() {
  echo "[$(date -u)] [entrypoint.sh] $@"
}

if [ -z "$DOMAIN" ]; then
  log "ERROR: The DOMAIN environment variable is not set."
  exit 1
fi

CERT_DIR="/etc/letsencrypt/live/$DOMAIN"
DHPARAMS_FILE="/etc/letsencrypt/ssl-dhparams.pem"

# --- Dummy Certificate Generation ---
if [ ! -f "$CERT_DIR/fullchain.pem" ]; then
  log "No certificate found for $DOMAIN. Generating a temporary dummy certificate..."
  mkdir -p "$CERT_DIR"
  openssl req -x509 -nodes -newkey rsa:2048 -days 1 \
    -keyout "$CERT_DIR/privkey.pem" \
    -out "$CERT_DIR/fullchain.pem" \
    -subj "/CN=localhost"
fi

# --- DHParams Generation ---
if [ ! -f "$DHPARAMS_FILE" ]; then
  log "Generating strong Diffie-Hellman parameters (2048 bits)..."
  log "This may take a moment but is required for the first startup."
  openssl dhparam -out "$DHPARAMS_FILE" 2048
fi

# --- Config Substitution ---
log "Substituting environment variables in Nginx templates..."
envsubst '${DOMAIN}' < /etc/nginx/conf.d/http.conf.template > /etc/nginx/conf.d/http.conf
envsubst '${DOMAIN}' < /etc/nginx/conf.d/https.conf.template > /etc/nginx/conf.d/https.conf

# --- Automatic Reload ---
log "Setting up cron job for daily Nginx reload..."
echo "0 4 * * * nginx -s reload" > /etc/crontabs/root
crond -b

log "Nginx is configured. Starting main process..."
exec "$@"
