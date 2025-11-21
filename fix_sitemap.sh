#!/bin/bash

# Sitemap Fix Script for zone.ee VPS + Docker
# This script fixes the sitemap.xml issue by creating a static file

set -e  # Exit on error

echo "🔧 Fixing sitemap.xml on flipunit.eu..."

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Detect the web root directory
# Common locations for Docker deployments
WEB_ROOT_CANDIDATES=(
    "/opt/flipunit"
    "/var/www/html"
    "/var/www/flipunit"
    "$(pwd)"
)

WEB_ROOT=""
for candidate in "${WEB_ROOT_CANDIDATES[@]}"; do
    if [ -d "$candidate" ] && [ -f "$candidate/docker-compose.yml" ]; then
        WEB_ROOT="$candidate"
        break
    fi
done

if [ -z "$WEB_ROOT" ]; then
    echo -e "${YELLOW}⚠️  Could not auto-detect web root.${NC}"
    echo "Please enter the full path to your project directory (where docker-compose.yml is):"
    read -r WEB_ROOT
fi

if [ ! -d "$WEB_ROOT" ]; then
    echo -e "${RED}❌ Directory $WEB_ROOT does not exist!${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Using web root: $WEB_ROOT${NC}"

# Step 1: Delete old sitemap if it exists
SITEMAP_PATH="$WEB_ROOT/sitemap.xml"
if [ -f "$SITEMAP_PATH" ]; then
    echo "🗑️  Removing old sitemap.xml..."
    rm -f "$SITEMAP_PATH"
    echo -e "${GREEN}✓ Old sitemap removed${NC}"
fi

# Step 2: Download fresh sitemap from xml-sitemaps.com
echo ""
echo "📥 Downloading fresh sitemap from xml-sitemaps.com..."
echo -e "${YELLOW}⚠️  You need to generate a sitemap first:${NC}"
echo "   1. Go to https://www.xml-sitemaps.com"
echo "   2. Enter: flipunit.eu"
echo "   3. Click 'Start' and wait for generation"
echo "   4. Right-click 'Download your sitemap file' → Copy link"
echo ""
echo "Paste the download URL here (or press Enter to skip and download manually):"
read -r SITEMAP_URL

if [ -n "$SITEMAP_URL" ]; then
    echo "Downloading sitemap..."
    if command -v curl &> /dev/null; then
        curl -s "$SITEMAP_URL" > "$SITEMAP_PATH"
    elif command -v wget &> /dev/null; then
        wget -q -O "$SITEMAP_PATH" "$SITEMAP_URL"
    else
        echo -e "${RED}❌ Neither curl nor wget found. Please install one.${NC}"
        exit 1
    fi
    
    # Verify it's valid XML
    if head -n 1 "$SITEMAP_PATH" | grep -q "<?xml"; then
        echo -e "${GREEN}✓ Sitemap downloaded successfully${NC}"
    else
        echo -e "${RED}❌ Downloaded file doesn't look like valid XML!${NC}"
        echo "Please check the URL and try again."
        exit 1
    fi
else
    echo -e "${YELLOW}⚠️  Skipping download. Please manually download sitemap.xml to:${NC}"
    echo "   $SITEMAP_PATH"
    echo ""
    echo "Press Enter when done, or Ctrl+C to cancel..."
    read -r
fi

# Step 3: Set correct permissions
if [ -f "$SITEMAP_PATH" ]; then
    echo "🔐 Setting permissions..."
    chmod 644 "$SITEMAP_PATH"
    echo -e "${GREEN}✓ Permissions set (644)${NC}"
fi

# Step 4: Check if sitemap needs to be in staticfiles directory
# (Some setups serve static files from a different location)
STATICFILES_DIR="$WEB_ROOT/staticfiles"
if [ -d "$STATICFILES_DIR" ]; then
    echo ""
    echo "📁 Copying to staticfiles directory (if needed)..."
    cp "$SITEMAP_PATH" "$STATICFILES_DIR/sitemap.xml" 2>/dev/null || true
    chmod 644 "$STATICFILES_DIR/sitemap.xml" 2>/dev/null || true
    echo -e "${GREEN}✓ Copied to staticfiles${NC}"
fi

# Step 5: Clear Docker cache (if applicable)
echo ""
echo "🧹 Clearing caches..."
if command -v docker &> /dev/null; then
    # Try to clear cache in the web container
    CONTAINER_NAME="flipunit-web"
    if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        echo "Clearing cache in Docker container..."
        docker exec "$CONTAINER_NAME" sh -c "rm -rf /tmp/cache/* /app/staticfiles/.cache/*" 2>/dev/null || true
        echo -e "${GREEN}✓ Docker cache cleared${NC}"
    fi
fi

# Step 6: Verify the sitemap
echo ""
echo "🔍 Verifying sitemap..."
if [ -f "$SITEMAP_PATH" ]; then
    FIRST_LINE=$(head -n 1 "$SITEMAP_PATH")
    if echo "$FIRST_LINE" | grep -q "<?xml"; then
        echo -e "${GREEN}✓ Sitemap is valid XML${NC}"
        echo "   First line: $FIRST_LINE"
    else
        echo -e "${RED}❌ Sitemap doesn't start with <?xml${NC}"
        echo "   First line: $FIRST_LINE"
    fi
else
    echo -e "${RED}❌ Sitemap file not found at $SITEMAP_PATH${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}✅ Sitemap fix complete!${NC}"
echo ""
echo "📋 Next steps:"
echo "   1. Test in browser: https://flipunit.eu/sitemap.xml"
echo "   2. Verify it shows pure XML (starts with <?xml version=\"1.0\"...)"
echo "   3. Check for NO 'noindex' headers or HTML wrapping"
echo "   4. In Google Search Console → Sitemaps:"
echo "      - Remove old red entries"
echo "      - Add new: sitemap.xml"
echo "      - Submit"
echo ""
echo "🚀 You're done! The sitemap should now work perfectly."


