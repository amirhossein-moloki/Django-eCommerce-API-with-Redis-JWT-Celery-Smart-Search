#!/bin/sh
set -e

# --- Helper Functions ---
log() {
  echo "[$(date -u)] [entrypoint.sh] $@"
}

# --- Environment Variable Checks ---
CERTBOT_ENABLED="${CERTBOT_ENABLED:-true}"
CERTBOT_ENABLED=$(echo "$CERTBOT_ENABLED" | tr '[:upper:]' '[:lower:]')

if [ "$CERTBOT_ENABLED" = "true" ]; then
  if [ -z "$DOMAIN" ]; then
    log "ERROR: The DOMAIN environment variable is not set."
    exit 1
  fi

  if [ -z "$EMAIL" ]; then
    log "ERROR: The EMAIL environment variable is not set (required by Let's Encrypt)."
    exit 1
  fi
fi

# --- Path Definitions ---
CERT_DIR="/etc/letsencrypt/live/$DOMAIN"
CERT_FILE="$CERT_DIR/fullchain.pem"
DHPARAMS_FILE="/etc/letsencrypt/ssl-dhparams.pem"
HTTP_CONF="/etc/nginx/conf.d/http.conf"
HTTPS_CONF="/etc/nginx/conf.d/https.conf"
HTTP_TEMPLATE="/etc/nginx/conf.d/http.conf.template"
HTTPS_TEMPLATE="/etc/nginx/conf.d/https.conf.template"
HTTP_LOCAL_TEMPLATE="/etc/nginx/conf.d/http.local.conf.template"

# Function to update Nginx configs from templates
update_configs() {
  log "Substituting environment variables in Nginx config..."
  if [ "$CERTBOT_ENABLED" = "true" ]; then
    envsubst '${DOMAIN}' < "$HTTP_TEMPLATE" > "$HTTP_CONF"
    envsubst '${DOMAIN}' < "$HTTPS_TEMPLATE" > "$HTTPS_CONF"
  else
    envsubst '${DOMAIN}' < "$HTTP_LOCAL_TEMPLATE" > "$HTTP_CONF"
    rm -f "$HTTPS_CONF"
  fi
}

# --- Main Logic ---

if [ "$CERTBOT_ENABLED" = "true" ]; then
  # Step 1: Handle SSL Certificates
  if [ -f "$CERT_FILE" ]; then
    log "Certificate found for $DOMAIN. Skipping initial acquisition."
  else
    # Check if maybe it's in the -0001 directory already
    if [ -d "/etc/letsencrypt/live/$DOMAIN-0001" ]; then
        log "Found existing versioned certificate directory ($DOMAIN-0001). Creating symlink..."
        mkdir -p "/etc/letsencrypt/live"
        rm -rf "$CERT_DIR"
        ln -s "$DOMAIN-0001" "$CERT_DIR"
    fi

    # Check again after potential symlink fix
    if [ ! -f "$CERT_FILE" ]; then
        log "Certificate not found for $DOMAIN. Generating dummy certificate for initial start..."
        mkdir -p "$CERT_DIR"
        openssl req -x509 -nodes -newkey rsa:2048 -days 1 \
          -keyout "$CERT_DIR/privkey.pem" \
          -out "$CERT_DIR/fullchain.pem" \
          -subj "/CN=$DOMAIN"

        # Prepare config with dummy certs
        update_configs

        log "Starting Nginx in the background for Certbot challenge..."
        nginx -g "daemon on;"

        log "Requesting Let's Encrypt certificate for $DOMAIN..."
        certbot certonly \
          --webroot -w /var/www/certbot \
          --email "$EMAIL" \
          --domain "$DOMAIN" \
          --rsa-key-size 4096 \
          --agree-tos \
          --non-interactive \
          --force-renewal

        # Check if Certbot created a versioned directory
        if [ -d "/etc/letsencrypt/live/$DOMAIN-0001" ]; then
          log "Detected versioned certificate directory ($DOMAIN-0001). Fixing path for Nginx..."
          rm -rf "$CERT_DIR"
          ln -s "$DOMAIN-0001" "$CERT_DIR"
        fi

        log "Stopping temporary Nginx server..."
        nginx -s stop
        # Wait for Nginx to stop (using a simpler check if pgrep is missing)
        sleep 2
    fi
  fi

  # Step 2: Generate strong Diffie-Hellman parameters
  if [ ! -f "$DHPARAMS_FILE" ]; then
    log "Generating strong Diffie-Hellman parameters (4096 bits)..."
    openssl dhparam -out "$DHPARAMS_FILE" 4096 &
  fi

  # Step 3: Setup renewal cron
  log "Setting up cron job for automatic certificate renewal."
  # The renewal script ensures the symlink is maintained
  RENEW_CMD="certbot renew --quiet && ( [ -d /etc/letsencrypt/live/$DOMAIN-0001 ] && [ ! -L $CERT_DIR ] && rm -rf $CERT_DIR && ln -s $DOMAIN-0001 $CERT_DIR ); nginx -s reload"
  echo "0 3 * * * $RENEW_CMD" > /etc/crontabs/root
  crond -b
else
  log "CERTBOT_ENABLED=false; skipping certificate setup."
fi

# Final config update to ensure everything is correct
update_configs

log "Nginx is configured. Starting main process..."
exec "$@"
