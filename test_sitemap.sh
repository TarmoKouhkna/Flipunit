#!/bin/bash
# Test sitemap after nginx fix

echo "🔍 Testing sitemap.xml..."
echo ""

# Test 1: Check if sitemap is accessible
echo "1. Testing sitemap URL:"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://flipunit.eu/sitemap.xml)
echo "   HTTP Status: $HTTP_CODE"

if [ "$HTTP_CODE" = "200" ]; then
    echo "   ✅ Sitemap is accessible!"
else
    echo "   ❌ Sitemap returned HTTP $HTTP_CODE"
    exit 1
fi

echo ""

# Test 2: Check content type
echo "2. Checking content type:"
CONTENT_TYPE=$(curl -s -I https://flipunit.eu/sitemap.xml | grep -i "content-type" | head -1)
echo "   $CONTENT_TYPE"

if echo "$CONTENT_TYPE" | grep -qi "application/xml\|text/xml"; then
    echo "   ✅ Correct content type!"
else
    echo "   ⚠️  Content type might be incorrect"
fi

echo ""

# Test 3: Check for noindex header
echo "3. Checking for noindex header:"
NOINDEX=$(curl -s -I https://flipunit.eu/sitemap.xml | grep -i "x-robots-tag.*noindex" || echo "none")
if [ "$NOINDEX" = "none" ]; then
    echo "   ✅ No noindex header (good!)"
else
    echo "   ❌ Found noindex header: $NOINDEX"
fi

echo ""

# Test 4: Show first few lines of sitemap
echo "4. First 5 lines of sitemap:"
curl -s https://flipunit.eu/sitemap.xml | head -5
echo ""

# Test 5: Count URLs in sitemap
echo "5. Counting URLs in sitemap:"
URL_COUNT=$(curl -s https://flipunit.eu/sitemap.xml | grep -c "<url>" || echo "0")
echo "   Found $URL_COUNT URLs"

echo ""
echo "✅ Sitemap test complete!"
echo ""
echo "Next steps:"
echo "1. Submit to Google Search Console: https://flipunit.eu/sitemap.xml"
echo "2. Wait a few minutes for Google to process it"
echo "3. Check Google Search Console → Sitemaps section"




