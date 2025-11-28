#!/bin/bash
# Fix sitemap X-Robots-Tag header issue

echo "Checking for global nginx headers..."
sudo grep -r "X-Robots-Tag" /etc/nginx/ 2>/dev/null || echo "No global X-Robots-Tag found"

echo ""
echo "Updating nginx config to explicitly clear the header..."

# Create a backup
sudo cp /etc/nginx/sites-available/flipunit.eu /etc/nginx/sites-available/flipunit.eu.backup.$(date +%Y%m%d_%H%M%S)

# Update the sitemap location block to use more aggressive header removal
sudo sed -i '/location = \/sitemap\.xml/,/^    }$/c\
    # Remove X-Robots-Tag header from sitemap for Google Search Console\
    location = /sitemap.xml {\
        proxy_pass http://localhost:8000;\
        proxy_set_header Host $host;\
        proxy_set_header X-Real-IP $remote_addr;\
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\
        proxy_set_header X-Forwarded-Proto $scheme;\
        proxy_hide_header X-Robots-Tag;\
        proxy_ignore_headers "X-Robots-Tag";\
        add_header Content-Type "application/xml; charset=utf-8" always;\
        add_header X-Robots-Tag "" always;\
    }' /etc/nginx/sites-available/flipunit.eu

echo "Testing nginx config..."
if sudo nginx -t; then
    echo "✓ Config is valid, reloading..."
    sudo systemctl reload nginx
    echo "✓ Nginx reloaded"
    echo ""
    echo "Testing sitemap..."
    sleep 2
    curl -I https://flipunit.eu/sitemap.xml | grep -i "robots" || echo "✓ No X-Robots-Tag header found!"
else
    echo "❌ Config test failed!"
    exit 1
fi




