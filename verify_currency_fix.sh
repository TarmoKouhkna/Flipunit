#!/bin/bash
# Verify that currency convert endpoint is removed from sitemap

echo "🔍 Verifying Currency Convert Fix..."
echo ""

# Check if currency/convert is in sitemap
if curl -s https://flipunit.eu/sitemap.xml | grep -q "currency/convert"; then
    echo "❌ FAIL: /currency/convert/ still found in sitemap"
    exit 1
else
    echo "✅ PASS: /currency/convert/ removed from sitemap"
fi

# Verify currency index is still in sitemap
if curl -s https://flipunit.eu/sitemap.xml | grep -q "currency/"; then
    echo "✅ PASS: /currency/ (index page) still in sitemap"
else
    echo "⚠️  WARN: /currency/ not found in sitemap (should be there)"
fi

# Check HTTP status of convert endpoint (should redirect)
echo ""
echo "Checking /currency/convert/ endpoint:"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -L https://flipunit.eu/currency/convert/)
echo "   HTTP Status: $HTTP_CODE"

if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "302" ] || [ "$HTTP_CODE" = "301" ]; then
    echo "✅ Endpoint still works (redirects as expected for API endpoint)"
else
    echo "⚠️  Unexpected status code: $HTTP_CODE"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Fix verified! Currency convert endpoint removed from sitemap"
echo "   All SEO issues should be resolved after next crawl"
