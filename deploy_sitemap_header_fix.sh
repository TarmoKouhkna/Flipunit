#!/bin/bash

# Deploy Sitemap Header Fix
# This script updates the sitemap view to remove security headers

set -e

echo "🚀 Deploying Sitemap Header Fix..."
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if we're on the server
if [ ! -f "/opt/flipunit/docker-compose.yml" ]; then
    echo -e "${YELLOW}⚠️  This script should be run on the server${NC}"
    echo "   Run these commands on your server:"
    echo ""
    echo "   cd /opt/flipunit"
    echo "   docker-compose restart web"
    echo ""
    exit 1
fi

cd /opt/flipunit

echo -e "${BLUE}Step 1: Checking if code needs to be updated...${NC}"

# Check if git is available and if we need to pull
if command -v git &> /dev/null && [ -d ".git" ]; then
    echo "   Pulling latest changes from git..."
    git pull || echo "   ⚠️  Git pull failed, continuing anyway..."
else
    echo "   ⚠️  Git not available or not a git repo"
    echo "   Make sure flipunit/urls.py is updated on the server"
fi

echo ""
echo -e "${BLUE}Step 2: Restarting web container...${NC}"
docker-compose restart web

echo ""
echo -e "${BLUE}Step 3: Waiting for container to start...${NC}"
sleep 3

echo ""
echo -e "${BLUE}Step 4: Verifying sitemap headers...${NC}"
echo "   Testing: https://flipunit.eu/sitemap.xml"

HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://flipunit.eu/sitemap.xml || echo "000")
HEADERS=$(curl -s -I https://flipunit.eu/sitemap.xml | grep -i "X-Frame-Options\|X-Content-Type-Options\|Referrer-Policy\|Cross-Origin-Opener-Policy" || echo "")

if [ "$HTTP_CODE" = "200" ]; then
    if [ -z "$HEADERS" ]; then
        echo -e "${GREEN}✅ SUCCESS! Security headers removed from sitemap${NC}"
        echo ""
        echo "   Headers check:"
        curl -s -I https://flipunit.eu/sitemap.xml | grep -i "content-type\|X-Frame\|X-Content\|Referrer\|Cross-Origin" || echo "   (No problematic headers found)"
    else
        echo -e "${YELLOW}⚠️  Sitemap is accessible but security headers still present:${NC}"
        echo "$HEADERS"
        echo ""
        echo "   This might mean the code hasn't been updated yet."
        echo "   Check that flipunit/urls.py contains the header removal code."
    fi
else
    echo -e "${YELLOW}⚠️  Sitemap returned HTTP $HTTP_CODE${NC}"
fi

echo ""
echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   ✅ Deployment Complete!             ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}📋 Next Steps:${NC}"
echo "   1. Verify headers are removed:"
echo "      curl -I https://flipunit.eu/sitemap.xml"
echo ""
echo "   2. In Google Search Console:"
echo "      - Remove old sitemap entry"
echo "      - Wait 2-3 minutes"
echo "      - Re-submit: sitemap.xml"
echo "      - Use 'Test URL' to verify"
echo ""
