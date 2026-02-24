#!/bin/bash

# setup.sh - Automated SSL and Nginx setup for vestelle.ir
# This script performs the initial certificate acquisition.

# 1. Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "Error: .env file not found."
    exit 1
fi

if [ -z "$DOMAIN" ] || [ -z "$CERTBOT_EMAIL" ]; then
    echo "Error: DOMAIN or CERTBOT_EMAIL not set in .env"
    exit 1
fi

echo "--- Starting SSL Setup for $DOMAIN ---"

# 2. Build and start services (Nginx will start with Dummy Cert)
echo "1. Building and starting Nginx/Web services..."
docker compose up -d --build nginx

# 3. Request real certificate from Let's Encrypt
echo "2. Requesting real certificate from Let's Encrypt..."
echo "IMPORTANT: Ensure Cloudflare is set to 'DNS Only' (Grey Cloud) for $DOMAIN"
read -p "Press enter to continue when ready..."

docker compose run --rm certbot certonly --webroot -w /var/www/certbot \
    --email "$CERTBOT_EMAIL" \
    --agree-tos --no-eff-email \
    -d "$DOMAIN"

# 4. Reload Nginx to use the new certificate
echo "3. Reloading Nginx with the new certificate..."
docker compose exec nginx_proxy nginx -s reload

echo "--- Setup Complete ---"
echo "You can now set Cloudflare to 'Proxied' (Orange Cloud) and use 'Full (Strict)' SSL mode."
