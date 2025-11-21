#!/bin/bash
# Complete sitemap fix - run these commands on your VPS

echo "🚀 Fixing sitemap.xml..."

# Step 1: Download sitemap from live site
echo "📥 Downloading sitemap from live site..."
curl -s https://flipunit.eu/sitemap.xml > /opt/flipunit/sitemap.xml

# Step 2: Set permissions
chmod 644 /opt/flipunit/sitemap.xml

# Step 3: Verify
echo "✅ Verifying sitemap..."
if head -1 /opt/flipunit/sitemap.xml | grep -q "<?xml"; then
    echo "   ✓ Valid XML file created"
else
    echo "   ❌ Error: File doesn't look like valid XML"
    exit 1
fi

echo ""
echo "📝 Next: Update Nginx config"
echo "   Run: sudo nano /etc/nginx/sites-available/flipunit.eu"
echo ""
echo "   Add this block BEFORE 'location /':"
echo ""
echo "   location = /sitemap.xml {"
echo "       alias /opt/flipunit/sitemap.xml;"
echo "       default_type application/xml;"
echo "       add_header Content-Type \"application/xml; charset=utf-8\";"
echo "       access_log off;"
echo "   }"
echo ""
echo "   Then: sudo nginx -t && sudo systemctl reload nginx"


