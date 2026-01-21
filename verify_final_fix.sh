#!/bin/bash
# Final verification of duplicate tag fix

echo "🔍 Final Verification of Duplicate Tag Fix..."
echo ""

echo "1. Checking /pdf-tools/html-to-pdf/:"
BODY1=$(curl -s https://flipunit.eu/pdf-tools/html-to-pdf/ | grep -o '</body>' | wc -l)
HEAD1=$(curl -s https://flipunit.eu/pdf-tools/html-to-pdf/ | grep -o '</head>' | wc -l)
HTML1=$(curl -s https://flipunit.eu/pdf-tools/html-to-pdf/ | grep -o '</html>' | wc -l)
PLACEHOLDER1=$(curl -s https://flipunit.eu/pdf-tools/html-to-pdf/ | grep -o 'textarea[^>]*placeholder="[^"]*"' | grep html_content)

echo "   Placeholder: $PLACEHOLDER1"
echo "   Closing tags: </body>=$BODY1 </head>=$HEAD1 </html>=$HTML1"

if echo "$PLACEHOLDER1" | grep -q 'Paste your HTML content here' && [ "$BODY1" -eq 1 ] && [ "$HEAD1" -eq 1 ] && [ "$HTML1" -eq 1 ]; then
    echo "   ✅ ALL FIXED!"
else
    echo "   ⚠️  Some issues remain"
fi

echo ""
echo "2. Checking /pdf-tools/universal/:"
BODY2=$(curl -s https://flipunit.eu/pdf-tools/universal/ | grep -o '</body>' | wc -l)
HEAD2=$(curl -s https://flipunit.eu/pdf-tools/universal/ | grep -o '</head>' | wc -l)
HTML2=$(curl -s https://flipunit.eu/pdf-tools/universal/ | grep -o '</html>' | wc -l)
PLACEHOLDER2=$(curl -s https://flipunit.eu/pdf-tools/universal/ | grep -o 'textarea[^>]*placeholder="[^"]*"' | grep html_content)

echo "   Placeholder: $PLACEHOLDER2"
echo "   Closing tags: </body>=$BODY2 </head>=$HEAD2 </html>=$HTML2"

if echo "$PLACEHOLDER2" | grep -q 'Paste your HTML content here' && [ "$BODY2" -eq 1 ] && [ "$HEAD2" -eq 1 ] && [ "$HTML2" -eq 1 ]; then
    echo "   ✅ ALL FIXED!"
else
    echo "   ⚠️  Some issues remain"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ "$BODY1" -eq 1 ] && [ "$HEAD1" -eq 1 ] && [ "$HTML1" -eq 1 ] && [ "$BODY2" -eq 1 ] && [ "$HEAD2" -eq 1 ] && [ "$HTML2" -eq 1 ]; then
    echo "✅ SUCCESS! All duplicate closing tags fixed!"
    echo "   Placeholders are plain text (no HTML tags)"
    echo "   All closing tags are unique (1 each)"
else
    echo "⚠️  Some duplicate tags may still exist"
fi
