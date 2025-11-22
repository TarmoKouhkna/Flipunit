#!/bin/bash
# Complete Sitemap Fix - Copy and paste this entire script on your VPS

set -e

echo "🚀 Starting complete sitemap fix..."

# Step 1: Download sitemap from live site
echo "📥 Step 1: Downloading sitemap..."
curl -s https://flipunit.eu/sitemap.xml > /opt/flipunit/sitemap.xml
chmod 644 /opt/flipunit/sitemap.xml

if head -1 /opt/flipunit/sitemap.xml | grep -q "<?xml"; then
    echo "   ✅ Sitemap downloaded successfully"
else
    echo "   ❌ Error: Sitemap file is not valid XML"
    exit 1
fi

# Step 2: Backup current Nginx config
echo ""
echo "📦 Step 2: Backing up Nginx config..."
sudo cp /etc/nginx/sites-available/flipunit.eu /etc/nginx/sites-available/flipunit.eu.backup.$(date +%Y%m%d_%H%M%S)
echo "   ✅ Backup created"

# Step 3: Fix Nginx config
echo ""
echo "🔧 Step 3: Fixing Nginx configuration..."

# Create temporary file with corrected config
TEMP_CONFIG=$(mktemp)

# Read current config and fix it
sudo cat /etc/nginx/sites-available/flipunit.eu | \
    sed 's/^location \//    location \//' | \
    sed 's/charset=u>/charset=utf-8";/' > "$TEMP_CONFIG"

# Check if sitemap location block exists
if ! grep -q "location = /sitemap.xml" "$TEMP_CONFIG"; then
    echo "   Adding sitemap location block..."
    # Find line number of "location /" block
    LOC_LINE=$(grep -n "^    location / {" "$TEMP_CONFIG" | head -1 | cut -d: -f1)
    if [ -n "$LOC_LINE" ]; then
        # Insert sitemap block before location /
        SITEMAP_BLOCK="    # Serve sitemap.xml directly as static file
    location = /sitemap.xml {
        alias /opt/flipunit/sitemap.xml;
        default_type application/xml;
        add_header Content-Type \"application/xml; charset=utf-8\";
        access_log off;
    }

"
        awk -v line="$LOC_LINE" -v block="$SITEMAP_BLOCK" '
            NR == line {
                print block
            }
            { print }
        ' "$TEMP_CONFIG" > "${TEMP_CONFIG}.tmp" && mv "${TEMP_CONFIG}.tmp" "$TEMP_CONFIG"
    fi
fi

# Apply the fixed config
sudo cp "$TEMP_CONFIG" /etc/nginx/sites-available/flipunit.eu
rm "$TEMP_CONFIG"
echo "   ✅ Nginx config updated"

# Step 4: Test Nginx config
echo ""
echo "🧪 Step 4: Testing Nginx configuration..."
if sudo nginx -t 2>/dev/null; then
    echo "   ✅ Nginx config test passed"
else
    echo "   ❌ Nginx config test failed!"
    echo "   Restoring backup..."
    sudo cp /etc/nginx/sites-available/flipunit.eu.backup.* /etc/nginx/sites-available/flipunit.eu 2>/dev/null || true
    exit 1
fi

# Step 5: Reload Nginx
echo ""
echo "🔄 Step 5: Reloading Nginx..."
if sudo systemctl reload nginx 2>/dev/null; then
    echo "   ✅ Nginx reloaded successfully"
else
    echo "   ⚠️  Could not reload Nginx automatically"
    echo "   Please run manually: sudo systemctl reload nginx"
fi

# Step 6: Verify sitemap
echo ""
echo "✅ Step 6: Verifying sitemap..."
sleep 2
if curl -s https://flipunit.eu/sitemap.xml | head -1 | grep -q "<?xml"; then
    echo "   ✅ Sitemap is accessible and valid XML"
    
    # Check content type
    CONTENT_TYPE=$(curl -s -I https://flipunit.eu/sitemap.xml | grep -i "content-type" | head -1)
    if echo "$CONTENT_TYPE" | grep -qi "application/xml"; then
        echo "   ✅ Content-Type is correct: $CONTENT_TYPE"
    else
        echo "   ⚠️  Content-Type: $CONTENT_TYPE"
    fi
    
    # Check for noindex
    if curl -s -I https://flipunit.eu/sitemap.xml | grep -qi "x-robots-tag.*noindex"; then
        echo "   ⚠️  WARNING: Still has noindex header!"
    else
        echo "   ✅ No noindex header detected"
    fi
else
    echo "   ⚠️  Could not verify sitemap (might need a moment to propagate)"
fi

echo ""
echo "🎉 Complete! Your sitemap should now be fixed."
echo ""
echo "📋 Next steps:"
echo "   1. Test in browser: https://flipunit.eu/sitemap.xml"
echo "   2. Google Search Console → Sitemaps"
echo "   3. Remove old entries, add: sitemap.xml"
echo "   4. Submit and wait 1-2 minutes for green ✅"




