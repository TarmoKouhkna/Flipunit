#!/bin/bash
# Remove default nginx site to prevent conflicts

echo "🧹 Cleaning up default nginx site..."

# Remove default site if it exists
if [ -L /etc/nginx/sites-enabled/default ]; then
    echo "Removing default site..."
    sudo rm /etc/nginx/sites-enabled/default
    echo "✅ Default site removed"
else
    echo "ℹ️  Default site already removed or doesn't exist"
fi

# Test and reload nginx
echo "🧪 Testing nginx configuration..."
if sudo nginx -t; then
    echo "✅ Configuration test passed"
    echo "🔄 Reloading nginx..."
    sudo systemctl reload nginx
    echo ""
    echo "✅ Cleanup complete!"
    echo ""
    echo "📋 Final verification:"
    curl -I http://flipunit.eu 2>/dev/null | head -n 3
else
    echo "❌ Configuration test failed!"
    exit 1
fi
