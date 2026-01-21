# Run This on VPS to Find Duplicate Closing Tags

Since you're already on the VPS, run these commands:

## Option 1: Create and Run Script

```bash
cat > /opt/flipunit/find_duplicate_tags.sh << 'EOF'
#!/bin/bash
echo "🔍 Searching for pages with duplicate closing tags..."
echo ""

URLS=$(curl -s https://flipunit.eu/sitemap.xml | grep -oP '<loc>\K[^<]+' | sed 's|https://flipunit.eu||')

found=0
total=0
for url in $URLS; do
    [ -z "$url" ] && url="/"
    ((total++))
    
    content=$(curl -s -L "https://flipunit.eu$url" 2>/dev/null)
    body_count=$(echo "$content" | grep -o '</body>' | wc -l)
    head_count=$(echo "$content" | grep -o '</head>' | wc -l)
    html_count=$(echo "$content" | grep -o '</html>' | wc -l)
    
    if [ "$body_count" -gt 1 ] || [ "$head_count" -gt 1 ] || [ "$html_count" -gt 1 ]; then
        echo "❌ FOUND: $url"
        echo "   </body>: $body_count | </head>: $head_count | </html>: $html_count"
        echo ""
        ((found++))
    fi
    
    if [ $((total % 20)) -eq 0 ]; then
        echo "   Checked $total pages..."
    fi
done

echo ""
if [ $found -eq 0 ]; then
    echo "✅ No pages with duplicate closing tags found (checked $total pages)"
else
    echo "📊 Found $found page(s) with duplicate closing tags"
fi
EOF

chmod +x /opt/flipunit/find_duplicate_tags.sh
bash /opt/flipunit/find_duplicate_tags.sh
```

## Option 2: Quick One-Liner (Faster)

```bash
for url in $(curl -s https://flipunit.eu/sitemap.xml | grep -oP '<loc>\K[^<]+' | sed 's|https://flipunit.eu||'); do 
    [ -z "$url" ] && url="/"
    content=$(curl -s -L "https://flipunit.eu$url" 2>/dev/null)
    body=$(echo "$content" | grep -o '</body>' | wc -l)
    head=$(echo "$content" | grep -o '</head>' | wc -l)
    html=$(echo "$content" | grep -o '</html>' | wc -l)
    if [ "$body" -gt 1 ] || [ "$head" -gt 1 ] || [ "$html" -gt 1 ]; then
        echo "❌ $url: body=$body head=$head html=$html"
    fi
done
```

## Option 3: Check Specific Suspect Pages

If the audit tool mentioned specific pages, check them directly:

```bash
# Check privacy and terms pages (common suspects)
for page in "/privacy/" "/terms/"; do
    echo "Checking $page:"
    content=$(curl -s "https://flipunit.eu$page")
    echo "  </body>: $(echo "$content" | grep -o '</body>' | wc -l)"
    echo "  </head>: $(echo "$content" | grep -o '</head>' | wc -l)"
    echo "  </html>: $(echo "$content" | grep -o '</html>' | wc -l)"
done
```

Run one of these on your VPS to identify the problematic pages!
