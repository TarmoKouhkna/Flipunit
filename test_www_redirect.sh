#!/bin/bash
# Test script to verify www to non-www redirect

echo "🔍 Testing WWW to non-WWW redirect..."
echo ""

echo "1️⃣ Testing https://www.flipunit.eu (should redirect to https://flipunit.eu):"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
WWW_RESPONSE=$(curl -sI https://www.flipunit.eu 2>/dev/null | head -n 1)
WWW_STATUS=$(echo "$WWW_RESPONSE" | grep -oP '\d{3}')
WWW_LOCATION=$(curl -sI https://www.flipunit.eu 2>/dev/null | grep -i "location:")

echo "Status: $WWW_RESPONSE"
echo "Location: $WWW_LOCATION"
echo ""

if [ "$WWW_STATUS" = "301" ]; then
    echo "✅ WWW redirect is working correctly (301 Moved Permanently)"
else
    echo "❌ WWW redirect is NOT working (got status: $WWW_STATUS)"
    echo "   Expected: 301, Got: $WWW_STATUS"
fi
echo ""

echo "2️⃣ Testing https://flipunit.eu (should return 200):"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
NON_WWW_RESPONSE=$(curl -sI https://flipunit.eu 2>/dev/null | head -n 1)
NON_WWW_STATUS=$(echo "$NON_WWW_RESPONSE" | grep -oP '\d{3}')

echo "Status: $NON_WWW_RESPONSE"
echo ""

if [ "$NON_WWW_STATUS" = "200" ]; then
    echo "✅ Non-WWW site is working correctly (200 OK)"
else
    echo "⚠️  Non-WWW returned status: $NON_WWW_STATUS"
fi
echo ""

echo "3️⃣ Checking nginx configuration for www redirect:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
sudo grep -A 8 "server_name www.flipunit.eu" /etc/nginx/sites-available/flipunit.eu | head -n 10
echo ""

echo "4️⃣ Summary:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ "$WWW_STATUS" = "301" ] && [ "$NON_WWW_STATUS" = "200" ]; then
    echo "✅ SUCCESS! WWW to non-WWW redirect is properly configured."
    echo "   - https://www.flipunit.eu → 301 redirect to https://flipunit.eu"
    echo "   - https://flipunit.eu → 200 OK"
    echo ""
    echo "🎉 The SEO issue should be resolved!"
else
    echo "⚠️  There is an issue with the WWW redirect."
    if [ "$WWW_STATUS" != "301" ]; then
        echo "   - WWW redirect is not working (expected 301, got $WWW_STATUS)"
    fi
fi
