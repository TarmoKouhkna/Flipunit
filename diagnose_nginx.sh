#!/bin/bash
# Diagnostic script to check nginx HTTP redirect configuration

echo "🔍 Diagnosing nginx HTTP to HTTPS redirect issue..."
echo ""

echo "1️⃣ Checking active nginx site configuration:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
sudo cat /etc/nginx/sites-available/flipunit.eu | head -n 25
echo ""

echo "2️⃣ Checking enabled sites:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
ls -la /etc/nginx/sites-enabled/
echo ""

echo "3️⃣ Checking for default server blocks:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
sudo grep -r "listen 80" /etc/nginx/sites-enabled/ /etc/nginx/conf.d/ 2>/dev/null || echo "No other listen 80 blocks found"
echo ""

echo "4️⃣ Testing HTTP connection:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
curl -v http://flipunit.eu 2>&1 | grep -E "(HTTP|Location|301|302|200)" | head -n 5
echo ""

echo "5️⃣ Checking nginx error log for issues:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
sudo tail -n 10 /var/log/nginx/error.log 2>/dev/null || echo "No error log found"
echo ""

echo "6️⃣ Verifying nginx is using the correct config:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
sudo nginx -T 2>/dev/null | grep -A 5 "listen 80" | head -n 10
echo ""
