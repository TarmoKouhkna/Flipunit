#!/bin/bash
# Quick script to remove the static sitemap block from nginx config
# Run this on your VPS

NGINX_CONFIG="/etc/nginx/sites-available/flipunit.eu"

echo "🔧 Removing static sitemap block from nginx config..."

# Create backup
sudo cp "$NGINX_CONFIG" "${NGINX_CONFIG}.backup.$(date +%Y%m%d_%H%M%S)"
echo "✓ Backup created"

# Remove the sitemap location block
sudo sed -i '/# Serve sitemap.xml directly as static file/,/^    }$/d' "$NGINX_CONFIG"

echo "✓ Removed static sitemap block"

# Test nginx config
echo "Testing nginx configuration..."
if sudo nginx -t; then
    echo "✓ Nginx config is valid"
    echo "Reloading nginx..."
    sudo systemctl reload nginx
    echo "✅ Done! Django will now serve the sitemap dynamically."
    echo ""
    echo "Test it: curl https://flipunit.eu/sitemap.xml | head -5"
else
    echo "❌ Nginx config test failed! Restore backup if needed."
    exit 1
fi




