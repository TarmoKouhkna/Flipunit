#!/bin/bash
# Complete SEO Issues Diagnostic Script

echo "╔════════════════════════════════════════════════════════╗"
echo "║   SEO Issues Diagnostic - Finding All Problems         ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

# Get all URLs from sitemap
echo "📋 Step 1: Checking for Duplicate Closing Tags"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

URLS=$(curl -s https://flipunit.eu/sitemap.xml | grep -oP '<loc>\K[^<]+' | sed 's|https://flipunit.eu||' | sort)

DUPLICATE_TAG_PAGES=()
count=0
for url in $URLS; do
    if [ -z "$url" ]; then
        url="/"
    fi
    
    # Check for duplicate closing tags
    body_count=$(curl -s -L "https://flipunit.eu$url" 2>/dev/null | grep -o '</body>' | wc -l)
    head_count=$(curl -s -L "https://flipunit.eu$url" 2>/dev/null | grep -o '</head>' | wc -l)
    html_count=$(curl -s -L "https://flipunit.eu$url" 2>/dev/null | grep -o '</html>' | wc -l)
    
    if [ "$body_count" -gt 1 ] || [ "$head_count" -gt 1 ] || [ "$html_count" -gt 1 ]; then
        echo "❌ FOUND: $url"
        echo "   </body>: $body_count | </head>: $head_count | </html>: $html_count"
        DUPLICATE_TAG_PAGES+=("$url")
    fi
    
    # Progress indicator
    ((count++))
    if [ $((count % 20)) -eq 0 ]; then
        echo "   Checked $count pages..."
    fi
done

if [ ${#DUPLICATE_TAG_PAGES[@]} -eq 0 ]; then
    echo "✅ No pages with duplicate closing tags found"
else
    echo ""
    echo "📊 Summary: ${#DUPLICATE_TAG_PAGES[@]} page(s) with duplicate tags"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 Step 2: Checking for Orphan URLs"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Get homepage HTML
HOMEPAGE_HTML=$(curl -s https://flipunit.eu/)

ORPHAN_URLS=()
for url in $URLS; do
    if [ -z "$url" ]; then
        url="/"
        continue  # Skip homepage
    fi
    
    # Extract just the path part for checking
    url_path=$(echo "$url" | sed 's|^https://flipunit.eu||')
    if [ -z "$url_path" ]; then
        url_path="/"
    fi
    
    # Check if URL is linked (as href) in homepage
    found=0
    
    # Check homepage for href links
    if echo "$HOMEPAGE_HTML" | grep -qi "href=\"[^\"]*${url_path}[^\"]*\""; then
        found=1
    fi
    
    # Special case: search page (linked via form, not href)
    if [ "$url_path" = "/search/" ]; then
        if echo "$HOMEPAGE_HTML" | grep -qi "action=\"[^\"]*search[^\"]*\""; then
            found=1
        fi
    fi
    
    # Check if it's a category index (these are always linked from homepage)
    if [[ "$url_path" == */ ]] && [[ "$url_path" != *//* ]]; then
        category_base=$(echo "$url_path" | sed 's|/$||')
        if echo "$HOMEPAGE_HTML" | grep -qi "href=\"[^\"]*${category_base}[^\"]*\""; then
            found=1
        fi
    fi
    
    if [ $found -eq 0 ]; then
        echo "⚠️  ORPHAN: $url_path"
        ORPHAN_URLS+=("$url_path")
    fi
done

if [ ${#ORPHAN_URLS[@]} -eq 0 ]; then
    echo "✅ No orphan URLs found"
else
    echo ""
    echo "📊 Summary: ${#ORPHAN_URLS[@]} orphan URL(s) found"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 Final Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ ${#DUPLICATE_TAG_PAGES[@]} -gt 0 ]; then
    echo "❌ Pages with duplicate closing tags:"
    for page in "${DUPLICATE_TAG_PAGES[@]}"; do
        echo "   - $page"
    done
    echo ""
fi

if [ ${#ORPHAN_URLS[@]} -gt 0 ]; then
    echo "⚠️  Orphan URLs (not linked from homepage):"
    for url in "${ORPHAN_URLS[@]}"; do
        echo "   - $url"
    done
    echo ""
fi

if [ ${#DUPLICATE_TAG_PAGES[@]} -eq 0 ] && [ ${#ORPHAN_URLS[@]} -eq 0 ]; then
    echo "✅ No issues found!"
fi

# Save results to file
echo "DUPLICATE_TAG_PAGES=(${DUPLICATE_TAG_PAGES[@]})" > /tmp/seo_issues_results.txt
echo "ORPHAN_URLS=(${ORPHAN_URLS[@]})" >> /tmp/seo_issues_results.txt
