#!/bin/bash
# Verify duplicate tag fix is deployed

echo "🔍 Verifying Duplicate Tag Fix..."
echo ""

# Check html-to-pdf page
echo "1. Checking /pdf-tools/html-to-pdf/:"
PLACEHOLDER1=$(curl -s https://flipunit.eu/pdf-tools/html-to-pdf/ | grep -o 'textarea.*html_content[^>]*placeholder="[^"]*"' | head -1)

if echo "$PLACEHOLDER1" | grep -q 'placeholder="Paste your HTML content here"'; then
    echo "   ✅ Placeholder is correct (plain text)"
elif echo "$PLACEHOLDER1" | grep -q '<html>'; then
    echo "   ❌ Placeholder still contains HTML tags!"
    echo "   Found: $PLACEHOLDER1"
else
    echo "   ⚠️  Placeholder: $PLACEHOLDER1"
fi

# Check for duplicate closing tags
BODY_COUNT1=$(curl -s https://flipunit.eu/pdf-tools/html-to-pdf/ | grep -o '</body>' | wc -l)
HEAD_COUNT1=$(curl -s https://flipunit.eu/pdf-tools/html-to-pdf/ | grep -o '</head>' | wc -l)
HTML_COUNT1=$(curl -s https://flipunit.eu/pdf-tools/html-to-pdf/ | grep -o '</html>' | wc -l)

echo "   Closing tags: </body>=$BODY_COUNT1 </head>=$HEAD_COUNT1 </html>=$HTML_COUNT1"
if [ "$BODY_COUNT1" -gt 1 ] || [ "$HEAD_COUNT1" -gt 1 ] || [ "$HTML_COUNT1" -gt 1 ]; then
    echo "   ❌ Still has duplicate closing tags!"
else
    echo "   ✅ No duplicate closing tags"
fi

echo ""

# Check universal page
echo "2. Checking /pdf-tools/universal/:"
PLACEHOLDER2=$(curl -s https://flipunit.eu/pdf-tools/universal/ | grep -o 'textarea.*html_content[^>]*placeholder="[^"]*"' | head -1)

if echo "$PLACEHOLDER2" | grep -q 'placeholder="Paste your HTML content here"'; then
    echo "   ✅ Placeholder is correct (plain text)"
elif echo "$PLACEHOLDER2" | grep -q '<html>'; then
    echo "   ❌ Placeholder still contains HTML tags!"
    echo "   Found: $PLACEHOLDER2"
else
    echo "   ⚠️  Placeholder: $PLACEHOLDER2"
fi

# Check for duplicate closing tags
BODY_COUNT2=$(curl -s https://flipunit.eu/pdf-tools/universal/ | grep -o '</body>' | wc -l)
HEAD_COUNT2=$(curl -s https://flipunit.eu/pdf-tools/universal/ | grep -o '</head>' | wc -l)
HTML_COUNT2=$(curl -s https://flipunit.eu/pdf-tools/universal/ | grep -o '</html>' | wc -l)

echo "   Closing tags: </body>=$BODY_COUNT2 </head>=$HEAD_COUNT2 </html>=$HTML_COUNT2"
if [ "$BODY_COUNT2" -gt 1 ] || [ "$HEAD_COUNT2" -gt 1 ] || [ "$HTML_COUNT2" -gt 1 ]; then
    echo "   ❌ Still has duplicate closing tags!"
else
    echo "   ✅ No duplicate closing tags"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ "$BODY_COUNT1" -le 1 ] && [ "$HEAD_COUNT1" -le 1 ] && [ "$HTML_COUNT1" -le 1 ] && [ "$BODY_COUNT2" -le 1 ] && [ "$HEAD_COUNT2" -le 1 ] && [ "$HTML_COUNT2" -le 1 ]; then
    echo "✅ Fix verified! No duplicate closing tags found"
else
    echo "⚠️  Some duplicate tags still detected - may need cache clear or re-crawl"
fi
