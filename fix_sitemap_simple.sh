#!/bin/bash
# Quick one-liner version - run this on your VPS after generating sitemap at xml-sitemaps.com

# Replace /opt/flipunit with your actual project path
PROJECT_DIR="/opt/flipunit"

# Replace this URL with the actual download URL from xml-sitemaps.com
# (Right-click "Download your sitemap file" → Copy link)
SITEMAP_URL="https://www.xml-sitemaps.com/download/flipunit.eu-XXXXXX/sitemap.xml?view=1"

echo "Downloading sitemap..."
curl -s "$SITEMAP_URL" > "$PROJECT_DIR/sitemap.xml" || wget -O "$PROJECT_DIR/sitemap.xml" "$SITEMAP_URL"

echo "Setting permissions..."
chmod 644 "$PROJECT_DIR/sitemap.xml"

echo "Copying to staticfiles..."
cp "$PROJECT_DIR/sitemap.xml" "$PROJECT_DIR/staticfiles/sitemap.xml" 2>/dev/null || true

echo "Clearing Docker cache..."
docker exec flipunit-web sh -c "rm -rf /tmp/cache/*" 2>/dev/null || true

echo "✅ Done! Test at: https://flipunit.eu/sitemap.xml"


