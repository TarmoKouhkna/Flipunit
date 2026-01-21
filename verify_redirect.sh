#!/bin/bash
# Final verification script for HTTP to HTTPS redirect

echo "🔍 Final Verification of HTTP to HTTPS Redirect"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "1️⃣ Testing HTTP redirect (should return 301):"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
HTTP_RESPONSE=$(curl -sI http://flipunit.eu 2>/dev/null | head -n 1)
HTTP_STATUS=$(echo "$HTTP_RESPONSE" | grep -oP '\d{3}')
HTTP_LOCATION=$(curl -sI http://flipunit.eu 2>/dev/null | grep -i "location:")

echo "Status: $HTTP_RESPONSE"
echo "Location: $HTTP_LOCATION"
echo ""

if [ "$HTTP_STATUS" = "301" ]; then
    echo "✅ HTTP redirect is working correctly (301 Moved Permanently)"
else
    echo "❌ HTTP redirect is NOT working (got status: $HTTP_STATUS)"
fi
echo ""

echo "2️⃣ Testing HTTPS (should return 200):"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
HTTPS_RESPONSE=$(curl -sI https://flipunit.eu 2>/dev/null | head -n 1)
HTTPS_STATUS=$(echo "$HTTPS_RESPONSE" | grep -oP '\d{3}')

echo "Status: $HTTPS_RESPONSE"
echo ""

if [ "$HTTPS_STATUS" = "200" ]; then
    echo "✅ HTTPS is working correctly (200 OK)"
else
    echo "⚠️  HTTPS returned status: $HTTPS_STATUS"
fi
echo ""

echo "3️⃣ Checking enabled nginx sites:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
ls -la /etc/nginx/sites-enabled/
echo ""

echo "4️⃣ Summary:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ "$HTTP_STATUS" = "301" ] && [ "$HTTPS_STATUS" = "200" ]; then
    echo "✅ SUCCESS! HTTP to HTTPS redirect is properly configured."
    echo "   - HTTP (port 80) → 301 redirect to HTTPS"
    echo "   - HTTPS (port 443) → 200 OK"
    echo ""
    echo "🎉 The SEO issue has been resolved!"
else
    echo "⚠️  There may still be an issue. Please review the output above."
fi
