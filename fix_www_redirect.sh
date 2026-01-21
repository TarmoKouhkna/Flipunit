#!/bin/bash
# Script to fix WWW to non-WWW redirect issue
# Run this on the server: bash fix_www_redirect.sh

set -e

echo "🔧 Fixing WWW to non-WWW redirect..."

# First, test current status
echo "📋 Current status:"
echo "Testing https://www.flipunit.eu..."
WWW_STATUS=$(curl -sI https://www.flipunit.eu 2>/dev/null | head -n 1 | grep -oP '\d{3}' || echo "000")
echo "Status: $WWW_STATUS"
echo ""

# Backup current config
echo "📦 Creating backup..."
sudo cp /etc/nginx/sites-available/flipunit.eu /etc/nginx/sites-available/flipunit.eu.backup.www.$(date +%Y%m%d_%H%M%S)

# Check if SSL certificate includes www
echo "🔍 Checking SSL certificate..."
if sudo certbot certificates 2>/dev/null | grep -q "www.flipunit.eu"; then
    echo "✅ SSL certificate includes www.flipunit.eu"
    CERT_INCLUDES_WWW=true
else
    echo "⚠️  SSL certificate may not include www.flipunit.eu"
    echo "   This might require updating the certificate"
    CERT_INCLUDES_WWW=false
fi
echo ""

# Verify the www redirect block exists and is correct
echo "🔍 Checking nginx configuration..."
if sudo grep -q "server_name www.flipunit.eu" /etc/nginx/sites-available/flipunit.eu; then
    echo "✅ WWW redirect block found in configuration"
    
    # Check if it's listening on 443
    if sudo grep -A 5 "server_name www.flipunit.eu" /etc/nginx/sites-available/flipunit.eu | grep -q "listen 443"; then
        echo "✅ WWW redirect block is configured for HTTPS (port 443)"
    else
        echo "❌ WWW redirect block is NOT configured for HTTPS"
        echo "   This needs to be fixed"
    fi
else
    echo "❌ WWW redirect block NOT found in configuration"
    echo "   This needs to be added"
fi
echo ""

# Test nginx configuration
echo "🧪 Testing nginx configuration..."
if sudo nginx -t; then
    echo "✅ Nginx configuration test passed"
    
    # Reload nginx
    echo "🔄 Reloading nginx..."
    sudo systemctl reload nginx
    
    echo ""
    echo "📋 Testing redirect after reload..."
    sleep 2
    NEW_WWW_STATUS=$(curl -sI https://www.flipunit.eu 2>/dev/null | head -n 1 | grep -oP '\d{3}' || echo "000")
    NEW_WWW_LOCATION=$(curl -sI https://www.flipunit.eu 2>/dev/null | grep -i "location:" || echo "")
    
    echo "New status: $NEW_WWW_STATUS"
    echo "Location: $NEW_WWW_LOCATION"
    echo ""
    
    if [ "$NEW_WWW_STATUS" = "301" ]; then
        echo "✅ SUCCESS! WWW to non-WWW redirect is now working."
        echo "   https://www.flipunit.eu → 301 redirect to https://flipunit.eu"
    else
        echo "⚠️  Redirect still not working (status: $NEW_WWW_STATUS)"
        if [ "$CERT_INCLUDES_WWW" = "false" ]; then
            echo ""
            echo "💡 SUGGESTION: You may need to update your SSL certificate to include www.flipunit.eu:"
            echo "   sudo certbot --nginx -d flipunit.eu -d www.flipunit.eu --expand"
        fi
    fi
else
    echo "❌ ERROR: Nginx configuration test failed!"
    echo "Restoring backup..."
    sudo cp /etc/nginx/sites-available/flipunit.eu.backup.www.* /etc/nginx/sites-available/flipunit.eu 2>/dev/null || true
    exit 1
fi
