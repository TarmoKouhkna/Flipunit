#!/bin/bash

# Deploy Sitemap Fix - Nginx Configuration Update
# Run this script on your VPS server at /opt/flipunit
# This script updates nginx config to remove static sitemap block

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

PROJECT_DIR="/opt/flipunit"
NGINX_CONFIG_SOURCE="$PROJECT_DIR/nginx_config_fixed.conf"
NGINX_CONFIG_TARGET="/etc/nginx/sites-available/flipunit.eu"
NGINX_CONFIG_ENABLED="/etc/nginx/sites-enabled/flipunit.eu"

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Sitemap Fix Deployment                ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""

# Check if we're in the right directory
if [ ! -d "$PROJECT_DIR" ]; then
    echo -e "${RED}❌ Project directory not found: $PROJECT_DIR${NC}"
    echo "Please run this script from /opt/flipunit"
    exit 1
fi

cd "$PROJECT_DIR"
echo -e "${GREEN}✓ Working directory: $(pwd)${NC}"
echo ""

# Step 1: Verify source config exists
echo -e "${BLUE}Step 1: Checking source nginx config...${NC}"
if [ ! -f "$NGINX_CONFIG_SOURCE" ]; then
    echo -e "${RED}❌ Source config not found: $NGINX_CONFIG_SOURCE${NC}"
    exit 1
fi

# Verify the source config doesn't have the sitemap block
if grep -q "location = /sitemap.xml" "$NGINX_CONFIG_SOURCE"; then
    echo -e "${RED}❌ Source config still contains sitemap block!${NC}"
    echo "   Please ensure nginx_config_fixed.conf has the sitemap block removed."
    exit 1
fi

echo -e "${GREEN}✓ Source config verified (no sitemap block)${NC}"
echo ""

# Step 2: Backup current nginx config
echo -e "${BLUE}Step 2: Backing up current nginx config...${NC}"
if [ -f "$NGINX_CONFIG_TARGET" ]; then
    BACKUP_FILE="${NGINX_CONFIG_TARGET}.backup.$(date +%Y%m%d_%H%M%S)"
    sudo cp "$NGINX_CONFIG_TARGET" "$BACKUP_FILE"
    echo -e "${GREEN}✓ Backup created: $BACKUP_FILE${NC}"
else
    echo -e "${YELLOW}⚠️  Current config not found at $NGINX_CONFIG_TARGET${NC}"
    echo "   This might be a fresh installation."
fi
echo ""

# Step 3: Copy new config
echo -e "${BLUE}Step 3: Copying new nginx config...${NC}"
sudo cp "$NGINX_CONFIG_SOURCE" "$NGINX_CONFIG_TARGET"
echo -e "${GREEN}✓ Config copied to $NGINX_CONFIG_TARGET${NC}"

# Ensure symlink exists
if [ ! -L "$NGINX_CONFIG_ENABLED" ]; then
    echo -e "${YELLOW}⚠️  Creating symlink to enabled config...${NC}"
    sudo ln -s "$NGINX_CONFIG_TARGET" "$NGINX_CONFIG_ENABLED"
    echo -e "${GREEN}✓ Symlink created${NC}"
fi
echo ""

# Step 4: Test nginx configuration
echo -e "${BLUE}Step 4: Testing nginx configuration...${NC}"
if sudo nginx -t; then
    echo -e "${GREEN}✓ Nginx configuration test passed${NC}"
else
    echo -e "${RED}❌ Nginx configuration test failed!${NC}"
    echo "   Restoring backup..."
    if [ -f "$BACKUP_FILE" ]; then
        sudo cp "$BACKUP_FILE" "$NGINX_CONFIG_TARGET"
        echo -e "${YELLOW}✓ Backup restored${NC}"
    fi
    exit 1
fi
echo ""

# Step 5: Reload nginx
echo -e "${BLUE}Step 5: Reloading nginx...${NC}"
if sudo systemctl reload nginx; then
    echo -e "${GREEN}✓ Nginx reloaded successfully${NC}"
else
    echo -e "${RED}❌ Failed to reload nginx!${NC}"
    echo "   Check nginx status: sudo systemctl status nginx"
    exit 1
fi
echo ""

# Step 6: Verify nginx is running
echo -e "${BLUE}Step 6: Verifying nginx status...${NC}"
if sudo systemctl is-active --quiet nginx; then
    echo -e "${GREEN}✓ Nginx is running${NC}"
else
    echo -e "${RED}❌ Nginx is not running!${NC}"
    echo "   Attempting to start nginx..."
    sudo systemctl start nginx
    if sudo systemctl is-active --quiet nginx; then
        echo -e "${GREEN}✓ Nginx started${NC}"
    else
        echo -e "${RED}❌ Failed to start nginx${NC}"
        exit 1
    fi
fi
echo ""

# Step 7: Test sitemap endpoint
echo -e "${BLUE}Step 7: Testing sitemap endpoint...${NC}"
sleep 2  # Give nginx a moment to fully reload

# Test through nginx (external)
echo "   Testing: https://flipunit.eu/sitemap.xml"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -k https://flipunit.eu/sitemap.xml || echo "000")
CONTENT_TYPE=$(curl -s -I -k https://flipunit.eu/sitemap.xml | grep -i "content-type" | head -1 || echo "")

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✓ Sitemap returns HTTP 200${NC}"
    if echo "$CONTENT_TYPE" | grep -qi "application/xml\|text/xml"; then
        echo -e "${GREEN}✓ Correct Content-Type: $CONTENT_TYPE${NC}"
    else
        echo -e "${YELLOW}⚠️  Unexpected Content-Type: $CONTENT_TYPE${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Sitemap returned HTTP $HTTP_CODE${NC}"
    echo "   This might be normal if DNS/SSL is still propagating"
    echo "   Content-Type: $CONTENT_TYPE"
fi

# Test direct to Django (internal)
echo "   Testing: http://localhost:8000/sitemap.xml (Django direct)"
DJANGO_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/sitemap.xml || echo "000")
if [ "$DJANGO_CODE" = "200" ]; then
    echo -e "${GREEN}✓ Django sitemap endpoint is working${NC}"
else
    echo -e "${YELLOW}⚠️  Django returned HTTP $DJANGO_CODE${NC}"
    echo "   You may need to restart Docker containers"
fi
echo ""

# Step 8: Optional - Restart Docker containers
echo -e "${BLUE}Step 8: Checking Docker containers...${NC}"
if command -v docker-compose &> /dev/null; then
    if [ -f "docker-compose.yml" ]; then
        echo "   Restarting web container to ensure fresh state..."
        docker-compose restart web
        echo -e "${GREEN}✓ Web container restarted${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  docker-compose not found, skipping container restart${NC}"
fi
echo ""

# Final summary
echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   ✅ Sitemap Fix Deployed!             ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}📋 Summary:${NC}"
echo "   • Nginx config updated"
echo "   • Nginx reloaded"
echo "   • Sitemap endpoint tested"
echo ""
echo -e "${BLUE}🔍 Verification:${NC}"
echo "   Test the sitemap:"
echo "   curl -I https://flipunit.eu/sitemap.xml"
echo ""
echo "   Expected response:"
echo "   HTTP/2 200"
echo "   Content-Type: application/xml; charset=utf-8"
echo ""
echo -e "${BLUE}🛠️  Troubleshooting:${NC}"
if [ "$HTTP_CODE" != "200" ]; then
    echo "   • Check nginx logs: sudo tail -50 /var/log/nginx/error.log"
    echo "   • Check nginx access: sudo tail -50 /var/log/nginx/access.log | grep sitemap"
    echo "   • Restart Docker: docker-compose restart web"
    echo "   • Verify Django: curl http://localhost:8000/sitemap.xml"
fi
echo ""
echo -e "${GREEN}✨ Deployment complete!${NC}"

