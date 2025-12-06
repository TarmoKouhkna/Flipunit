#!/bin/bash
# Test sitemap for Google Search Console compatibility

echo "🔍 Testing sitemap for Google Search Console..."
echo ""

# Test 1: Check if accessible
echo "1. Testing accessibility:"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://flipunit.eu/sitemap.xml)
echo "   HTTP Status: $HTTP_CODE"

if [ "$HTTP_CODE" = "200" ]; then
    echo "   ✅ Sitemap is accessible"
else
    echo "   ❌ Sitemap returned HTTP $HTTP_CODE"
    exit 1
fi

echo ""

# Test 2: Check headers
echo "2. Checking headers:"
HEADERS=$(curl -s -I https://flipunit.eu/sitemap.xml)
echo "$HEADERS" | head -15

echo ""

# Test 3: Check for noindex
echo "3. Checking for noindex header:"
if echo "$HEADERS" | grep -qi "X-Robots-Tag.*noindex"; then
    echo "   ❌ Found noindex header - this will prevent Google from indexing!"
else
    echo "   ✅ No noindex header found"
fi

echo ""

# Test 4: Validate XML structure
echo "4. Validating XML structure:"
FIRST_LINE=$(curl -s https://flipunit.eu/sitemap.xml | head -1)
if echo "$FIRST_LINE" | grep -q "<?xml"; then
    echo "   ✅ Valid XML format"
else
    echo "   ❌ Invalid XML format"
fi

echo ""

# Test 5: Count URLs
echo "5. Counting URLs:"
URL_COUNT=$(curl -s https://flipunit.eu/sitemap.xml | grep -o "<url>" | wc -l)
echo "   Found $URL_COUNT URLs"

echo ""

# Test 6: Check for lastmod dates
echo "6. Checking for lastmod dates:"
LASTMOD_COUNT=$(curl -s https://flipunit.eu/sitemap.xml | grep -o "<lastmod>" | wc -l)
if [ "$LASTMOD_COUNT" -gt 0 ]; then
    echo "   ✅ Found $LASTMOD_COUNT URLs with lastmod dates"
else
    echo "   ⚠️  No lastmod dates found (optional but recommended)"
fi

echo ""
echo "✅ Sitemap test complete!"
echo ""
echo "If Google still shows 'Couldn't fetch':"
echo "1. Wait 5-10 minutes for Google to retry"
echo "2. Click 'Test sitemap' in Google Search Console"
echo "3. Use 'Request Indexing' for the sitemap URL"
echo "4. Check Google's URL Inspection tool: https://flipunit.eu/sitemap.xml"

















