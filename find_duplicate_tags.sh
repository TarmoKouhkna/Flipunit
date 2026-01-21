#!/bin/bash
# Quick script to find pages with duplicate closing tags

echo "Searching for pages with duplicate closing tags..."
echo ""

# Get URLs from sitemap
URLS=$(curl -s https://flipunit.eu/sitemap.xml | grep -oP '<loc>\K[^<]+' | sed 's|https://flipunit.eu||')

found=0
for url in $URLS; do
    [ -z "$url" ] && url="/"
    
    # Get page content
    content=$(curl -s -L "https://flipunit.eu$url" 2>/dev/null)
    
    # Count closing tags
    body_count=$(echo "$content" | grep -o '</body>' | wc -l)
    head_count=$(echo "$content" | grep -o '</head>' | wc -l)
    html_count=$(echo "$content" | grep -o '</html>' | wc -l)
    
    # Check if any are > 1
    if [ "$body_count" -gt 1 ] || [ "$head_count" -gt 1 ] || [ "$html_count" -gt 1 ]; then
        echo "❌ $url"
        echo "   </body>: $body_count | </head>: $head_count | </html>: $html_count"
        echo ""
        ((found++))
    fi
done

if [ $found -eq 0 ]; then
    echo "✅ No pages with duplicate closing tags found"
else
    echo "Found $found page(s) with duplicate closing tags"
fi
