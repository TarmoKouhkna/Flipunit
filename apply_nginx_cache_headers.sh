#!/bin/bash
# Add Cache-Control headers for /static/ and /media/ in nginx (PageSpeed "Use efficient cache lifetimes").
# Run this ON THE VPS (e.g. after SSH to ubuntu@217.146.78.140):
#   cd /opt/flipunit && chmod +x apply_nginx_cache_headers.sh && ./apply_nginx_cache_headers.sh

set -e

NGINX_SITE="/etc/nginx/sites-available/flipunit.eu"

if [ ! -f "$NGINX_SITE" ]; then
    echo "Config not found: $NGINX_SITE"
    exit 1
fi

if sudo grep -q 'add_header Cache-Control "public, max-age=31536000"' "$NGINX_SITE"; then
    echo "Cache-Control header already present in $NGINX_SITE"
    sudo nginx -t && echo "Nginx config OK."
    exit 0
fi

echo "Backing up $NGINX_SITE..."
sudo cp "$NGINX_SITE" "${NGINX_SITE}.bak.$(date +%Y%m%d_%H%M%S)"

echo "Adding Cache-Control to /static/ and /media/..."
# Insert add_header after the alias line in location /static/ (path has trailing slash: staticfiles/)
sudo sed -i '/alias \/opt\/flipunit\/staticfiles\/;/a\        add_header Cache-Control "public, max-age=31536000";' "$NGINX_SITE"
# Insert add_header after the alias line in location /media/
sudo sed -i '/alias \/opt\/flipunit\/media\/;/a\        add_header Cache-Control "public, max-age=31536000";' "$NGINX_SITE"

echo "Testing nginx config..."
sudo nginx -t

echo "Reloading nginx..."
sudo systemctl reload nginx

echo "Done. Static and media responses will now include Cache-Control: public, max-age=31536000"
