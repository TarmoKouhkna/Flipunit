#!/bin/bash

# Complete Sitemap Fix Deployment Script
# This script automates the entire sitemap fix process on your VPS

set -e

echo "🚀 Sitemap Fix Deployment Script"
echo "================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Detect project directory
PROJECT_DIR="/opt/flipunit"
if [ ! -d "$PROJECT_DIR" ]; then
    echo -e "${YELLOW}⚠️  /opt/flipunit not found.${NC}"
    echo "Enter your project directory path:"
    read -r PROJECT_DIR
fi

if [ ! -d "$PROJECT_DIR" ]; then
    echo -e "${RED}❌ Directory $PROJECT_DIR does not exist!${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Using project directory: $PROJECT_DIR${NC}"
echo ""

# Step 1: Generate sitemap using Django management command
echo -e "${BLUE}Step 1: Generating sitemap.xml...${NC}"
cd "$PROJECT_DIR"

# Check if we're in a Docker environment
if docker ps --format '{{.Names}}' | grep -q "^flipunit-web$"; then
    echo "   Using Docker container to generate sitemap..."
    docker exec flipunit-web python manage.py generate_sitemap --output /app/sitemap.xml
    # Copy from container to host
    docker cp flipunit-web:/app/sitemap.xml "$PROJECT_DIR/sitemap.xml"
else
    # Try to generate locally if Django is available
    if [ -f "manage.py" ]; then
        echo "   Generating sitemap locally..."
        python3 manage.py generate_sitemap --output sitemap.xml 2>/dev/null || {
            echo -e "${YELLOW}   ⚠️  Could not generate via Django.${NC}"
            echo "   Please generate sitemap at https://www.xml-sitemaps.com"
            echo "   Then download it to: $PROJECT_DIR/sitemap.xml"
            echo ""
            echo "   Press Enter when sitemap.xml is ready, or Ctrl+C to cancel..."
            read -r
        }
    else
        echo -e "${YELLOW}   ⚠️  Django not available.${NC}"
        echo "   Please generate sitemap at https://www.xml-sitemaps.com"
        echo "   Then download it to: $PROJECT_DIR/sitemap.xml"
        echo ""
        echo "   Press Enter when sitemap.xml is ready, or Ctrl+C to cancel..."
        read -r
    fi
fi

# Verify sitemap exists
if [ ! -f "$PROJECT_DIR/sitemap.xml" ]; then
    echo -e "${RED}❌ sitemap.xml not found at $PROJECT_DIR/sitemap.xml${NC}"
    exit 1
fi

# Verify it's valid XML
if head -n 1 "$PROJECT_DIR/sitemap.xml" | grep -q "<?xml"; then
    echo -e "${GREEN}   ✓ Sitemap file is valid XML${NC}"
else
    echo -e "${RED}   ❌ sitemap.xml does not appear to be valid XML!${NC}"
    echo "   First line: $(head -n 1 "$PROJECT_DIR/sitemap.xml")"
    exit 1
fi

# Set permissions
chmod 644 "$PROJECT_DIR/sitemap.xml"
echo -e "${GREEN}   ✓ Permissions set${NC}"
echo ""

# Step 2: Update Nginx configuration
echo -e "${BLUE}Step 2: Updating Nginx configuration...${NC}"
NGINX_CONFIG="/etc/nginx/sites-available/flipunit.eu"

if [ ! -f "$NGINX_CONFIG" ]; then
    echo -e "${YELLOW}   ⚠️  Nginx config not found at $NGINX_CONFIG${NC}"
    echo "   Enter Nginx config path:"
    read -r NGINX_CONFIG
fi

if [ ! -f "$NGINX_CONFIG" ]; then
    echo -e "${RED}   ❌ Nginx config file not found!${NC}"
    exit 1
fi

# Check if sitemap location block already exists
if grep -q "location = /sitemap.xml" "$NGINX_CONFIG"; then
    echo -e "${YELLOW}   ⚠️  Sitemap location block already exists in Nginx config${NC}"
    echo "   Do you want to update it? (y/n)"
    read -r UPDATE_NGINX
    if [ "$UPDATE_NGINX" != "y" ]; then
        echo "   Skipping Nginx update..."
    else
        # Remove old block
        sed -i '/location = \/sitemap\.xml/,/^    }$/d' "$NGINX_CONFIG"
        UPDATE_NGINX="y"
    fi
else
    UPDATE_NGINX="y"
fi

if [ "$UPDATE_NGINX" = "y" ]; then
    # Create backup
    cp "$NGINX_CONFIG" "${NGINX_CONFIG}.backup.$(date +%Y%m%d_%H%M%S)"
    echo "   ✓ Backup created: ${NGINX_CONFIG}.backup.*"
    
    # Find the line number of "location /" block
    LOCATION_LINE=$(grep -n "^    location / {" "$NGINX_CONFIG" | head -1 | cut -d: -f1)
    
    if [ -z "$LOCATION_LINE" ]; then
        echo -e "${RED}   ❌ Could not find 'location /' block in Nginx config${NC}"
        echo "   Please manually add the sitemap location block before 'location /'"
        exit 1
    fi
    
    # Insert sitemap block before location /
    SITEMAP_BLOCK="    # Serve sitemap.xml directly as static file
    location = /sitemap.xml {
        alias ${PROJECT_DIR}/sitemap.xml;
        default_type application/xml;
        add_header Content-Type \"application/xml; charset=utf-8\";
        access_log off;
    }
"
    
    # Insert the block (using a temporary file)
    awk -v line="$LOCATION_LINE" -v block="$SITEMAP_BLOCK" '
        NR == line {
            print block
        }
        { print }
    ' "$NGINX_CONFIG" > "${NGINX_CONFIG}.tmp" && mv "${NGINX_CONFIG}.tmp" "$NGINX_CONFIG"
    
    echo -e "${GREEN}   ✓ Nginx config updated${NC}"
    
    # Test Nginx configuration
    echo "   Testing Nginx configuration..."
    if sudo nginx -t 2>/dev/null; then
        echo -e "${GREEN}   ✓ Nginx config test passed${NC}"
        
        # Reload Nginx
        echo "   Reloading Nginx..."
        if sudo systemctl reload nginx 2>/dev/null; then
            echo -e "${GREEN}   ✓ Nginx reloaded successfully${NC}"
        else
            echo -e "${YELLOW}   ⚠️  Could not reload Nginx automatically${NC}"
            echo "   Please run manually: sudo systemctl reload nginx"
        fi
    else
        echo -e "${RED}   ❌ Nginx config test failed!${NC}"
        echo "   Please check the configuration manually"
        echo "   Restore backup: sudo cp ${NGINX_CONFIG}.backup.* $NGINX_CONFIG"
        exit 1
    fi
else
    echo "   Skipped Nginx update"
fi

echo ""

# Step 3: Copy to staticfiles (if needed)
if [ -d "$PROJECT_DIR/staticfiles" ]; then
    echo -e "${BLUE}Step 3: Copying to staticfiles directory...${NC}"
    cp "$PROJECT_DIR/sitemap.xml" "$PROJECT_DIR/staticfiles/sitemap.xml" 2>/dev/null || true
    chmod 644 "$PROJECT_DIR/staticfiles/sitemap.xml" 2>/dev/null || true
    echo -e "${GREEN}   ✓ Copied to staticfiles${NC}"
    echo ""
fi

# Step 4: Clear caches
echo -e "${BLUE}Step 4: Clearing caches...${NC}"
if docker ps --format '{{.Names}}' | grep -q "^flipunit-web$"; then
    docker exec flipunit-web sh -c "rm -rf /tmp/cache/* /app/staticfiles/.cache/*" 2>/dev/null || true
    echo -e "${GREEN}   ✓ Docker cache cleared${NC}"
fi
echo ""

# Step 5: Verify
echo -e "${BLUE}Step 5: Verification...${NC}"
echo "   Testing sitemap URL..."

# Try to fetch the sitemap
SITEMAP_URL="https://flipunit.eu/sitemap.xml"
if command -v curl &> /dev/null; then
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$SITEMAP_URL" 2>/dev/null || echo "000")
    if [ "$HTTP_CODE" = "200" ]; then
        CONTENT_TYPE=$(curl -s -I "$SITEMAP_URL" 2>/dev/null | grep -i "content-type" | head -1)
        if echo "$CONTENT_TYPE" | grep -qi "application/xml"; then
            echo -e "${GREEN}   ✓ Sitemap is accessible and has correct content type${NC}"
        else
            echo -e "${YELLOW}   ⚠️  Sitemap accessible but content type may be incorrect${NC}"
            echo "      $CONTENT_TYPE"
        fi
        
        # Check for noindex header
        NOINDEX=$(curl -s -I "$SITEMAP_URL" 2>/dev/null | grep -i "x-robots-tag.*noindex" || true)
        if [ -n "$NOINDEX" ]; then
            echo -e "${RED}   ❌ WARNING: Sitemap has noindex header!${NC}"
            echo "      $NOINDEX"
        else
            echo -e "${GREEN}   ✓ No noindex header detected${NC}"
        fi
    else
        echo -e "${YELLOW}   ⚠️  Could not verify sitemap URL (HTTP $HTTP_CODE)${NC}"
        echo "      This might be normal if DNS/SSL is not fully configured"
    fi
else
    echo -e "${YELLOW}   ⚠️  curl not available, skipping URL verification${NC}"
fi

echo ""
echo -e "${GREEN}✅ Sitemap fix deployment complete!${NC}"
echo ""
echo "📋 Next steps:"
echo "   1. Test in browser: https://flipunit.eu/sitemap.xml"
echo "   2. Verify it shows pure XML (starts with <?xml version=\"1.0\"...)"
echo "   3. Check for NO 'noindex' headers or HTML wrapping"
echo "   4. In Google Search Console → Sitemaps:"
echo "      - Remove old red entries"
echo "      - Add new: sitemap.xml"
echo "      - Submit"
echo "   5. Wait 1-2 minutes → Should show green ✅"
echo ""
echo "🚀 You're done! The sitemap should now work perfectly."




