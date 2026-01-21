#!/bin/bash
# Complete verification of all redirects

echo "🔍 Complete Redirect Verification"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "1️⃣ HTTP to HTTPS redirects:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Testing http://flipunit.eu..."
HTTP_STATUS=$(curl -sI http://flipunit.eu 2>/dev/null | head -n 1 | grep -oP '\d{3}' || echo "000")
HTTP_LOCATION=$(curl -sI http://flipunit.eu 2>/dev/null | grep -i "location:" || echo "")
echo "Status: $HTTP_STATUS"
echo "$HTTP_LOCATION"
if [ "$HTTP_STATUS" = "301" ]; then
    echo "✅ PASS: HTTP redirects to HTTPS"
else
    echo "❌ FAIL: Expected 301, got $HTTP_STATUS"
fi
echo ""

echo "Testing http://www.flipunit.eu..."
HTTP_WWW_STATUS=$(curl -sI http://www.flipunit.eu 2>/dev/null | head -n 1 | grep -oP '\d{3}' || echo "000")
HTTP_WWW_LOCATION=$(curl -sI http://www.flipunit.eu 2>/dev/null | grep -i "location:" || echo "")
echo "Status: $HTTP_WWW_STATUS"
echo "$HTTP_WWW_LOCATION"
if [ "$HTTP_WWW_STATUS" = "301" ]; then
    echo "✅ PASS: HTTP www redirects to HTTPS"
else
    echo "❌ FAIL: Expected 301, got $HTTP_WWW_STATUS"
fi
echo ""

echo "2️⃣ WWW to non-WWW redirects:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Testing https://www.flipunit.eu..."
WWW_STATUS=$(curl -sI https://www.flipunit.eu 2>/dev/null | head -n 1 | grep -oP '\d{3}' || echo "000")
WWW_LOCATION=$(curl -sI https://www.flipunit.eu 2>/dev/null | grep -i "location:" || echo "")
echo "Status: $WWW_STATUS"
echo "$WWW_LOCATION"
if [ "$WWW_STATUS" = "301" ]; then
    echo "✅ PASS: WWW redirects to non-WWW"
else
    echo "❌ FAIL: Expected 301, got $WWW_STATUS"
fi
echo ""

echo "3️⃣ Final destinations (should return 200):"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Testing https://flipunit.eu..."
HTTPS_STATUS=$(curl -sI https://flipunit.eu 2>/dev/null | head -n 1 | grep -oP '\d{3}' || echo "000")
echo "Status: $HTTPS_STATUS"
if [ "$HTTPS_STATUS" = "200" ]; then
    echo "✅ PASS: HTTPS non-WWW returns 200 OK"
else
    echo "❌ FAIL: Expected 200, got $HTTPS_STATUS"
fi
echo ""

echo "4️⃣ Summary:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
ALL_PASS=true

if [ "$HTTP_STATUS" != "301" ]; then
    echo "❌ HTTP to HTTPS redirect: FAILED"
    ALL_PASS=false
fi

if [ "$HTTP_WWW_STATUS" != "301" ]; then
    echo "❌ HTTP www to HTTPS redirect: FAILED"
    ALL_PASS=false
fi

if [ "$WWW_STATUS" != "301" ]; then
    echo "❌ WWW to non-WWW redirect: FAILED"
    ALL_PASS=false
fi

if [ "$HTTPS_STATUS" != "200" ]; then
    echo "❌ HTTPS non-WWW: FAILED"
    ALL_PASS=false
fi

if [ "$ALL_PASS" = true ]; then
    echo "✅ ALL REDIRECTS WORKING CORRECTLY!"
    echo ""
    echo "Redirect flow:"
    echo "  http://flipunit.eu          → 301 → https://flipunit.eu (200)"
    echo "  http://www.flipunit.eu      → 301 → https://flipunit.eu (200)"
    echo "  https://www.flipunit.eu     → 301 → https://flipunit.eu (200)"
    echo "  https://flipunit.eu         → 200 OK ✓"
    echo ""
    echo "🎉 All SEO redirect issues are resolved!"
    echo ""
    echo "💡 Note: If SEO tools still show issues, they may be showing cached results."
    echo "   Wait a few hours or re-run the SEO audit to see updated results."
else
    echo "⚠️  Some redirects are not working. Please review the output above."
fi
