#!/bin/sh
set -e

# --- Helper Functions ---
log() {
  echo "[$(date -u)] [entrypoint.sh] $@"
}

# --- Validation ---
if [ -z "$DOMAIN" ]; then
  log "ERROR: The DOMAIN environment variable is not set."
  exit 1
fi

CERT_DIR="/etc/letsencrypt/live/$DOMAIN"
DHPARAMS_FILE="/etc/letsencrypt/ssl-dhparams.pem"

# --- SSL Directory Check ---
mkdir -p "/etc/letsencrypt"
mkdir -p "/var/www/certbot"

# --- Dummy Certificate Generation ---
# This ensures Nginx can start even if Certbot hasn't obtained a real cert yet.
# Once Certbot obtains a real cert, it will overwrite these files via the shared volume.
if [ ! -f "$CERT_DIR/fullchain.pem" ]; then
  log "No certificate found for $DOMAIN. Generating a temporary dummy certificate to allow Nginx to start..."
  mkdir -p "$CERT_DIR"
  openssl req -x509 -nodes -newkey rsa:2048 -days 1 \
    -keyout "$CERT_DIR/privkey.pem" \
    -out "$CERT_DIR/fullchain.pem" \
    -subj "/CN=localhost"
  log "Dummy certificate generated successfully."
else
  log "Existing certificate found in $CERT_DIR. Skipping dummy cert generation."
fi

# --- DHParams Generation ---
# Required for strong SSL security. If missing, Nginx will fail to start.
if [ ! -f "$DHPARAMS_FILE" ]; then
  log "Generating strong Diffie-Hellman parameters (2048 bits)..."
  log "This is a one-time process and may take a moment."
  openssl dhparam -out "$DHPARAMS_FILE" 2048
  log "DH parameters generated successfully."
else
  log "Existing DH parameters found. Skipping generation."
fi

# --- Config Substitution ---
log "Substituting environment variables in Nginx templates..."
envsubst '${DOMAIN}' < /etc/nginx/conf.d/http.conf.template > /etc/nginx/conf.d/http.conf
envsubst '${DOMAIN}' < /etc/nginx/conf.d/https.conf.template > /etc/nginx/conf.d/https.conf

# --- Automatic Reload (Cron) ---
# Set up a cron job to reload Nginx daily to pick up any renewed certificates from the Certbot container.
log "Setting up cron job for daily Nginx reload (04:00 AM)..."
echo "0 4 * * * nginx -s reload" > /etc/crontabs/root
crond -b

# --- Final Execution ---
log "Nginx is configured and ready to start."
exec "$@"
