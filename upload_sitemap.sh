#!/bin/bash

# Simple script to upload sitemap.xml to your VPS
# Usage: ./upload_sitemap.sh [user@host]

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if sitemap.xml exists
if [ ! -f "sitemap.xml" ]; then
    echo -e "${RED}❌ Error: sitemap.xml not found in current directory${NC}"
    echo "   Please run: DEBUG=True python manage.py generate_sitemap"
    exit 1
fi

# Get server details
if [ -z "$1" ]; then
    echo -e "${YELLOW}Enter your VPS connection details:${NC}"
    echo "   Format: user@hostname or user@ip"
    echo "   Example: ubuntu@217.146.78.140"
    read -r SERVER
else
    SERVER="$1"
fi

if [ -z "$SERVER" ]; then
    echo -e "${RED}❌ Server details required${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}📤 Uploading sitemap.xml to server...${NC}"
echo "   Server: $SERVER"
echo "   Destination: /opt/flipunit/sitemap.xml"
echo ""

# Upload the file
scp sitemap.xml "$SERVER:/opt/flipunit/sitemap.xml"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Upload successful!${NC}"
    echo ""
    echo "📋 Next steps (run these on your server):"
    echo ""
    echo "   1. Set permissions:"
    echo "      ssh $SERVER 'chmod 644 /opt/flipunit/sitemap.xml'"
    echo ""
    echo "   2. Verify the file:"
    echo "      ssh $SERVER 'head -1 /opt/flipunit/sitemap.xml'"
    echo ""
    echo "   3. Test the sitemap URL:"
    echo "      curl https://flipunit.eu/sitemap.xml | head -5"
    echo ""
    echo "   4. If Nginx is configured correctly, the sitemap should be accessible!"
    echo ""
    echo "   5. In Google Search Console → Sitemaps:"
    echo "      - Remove old entries"
    echo "      - Add: sitemap.xml"
    echo "      - Submit"
    echo ""
else
    echo -e "${RED}❌ Upload failed${NC}"
    echo "   Make sure:"
    echo "   - You have SSH access to the server"
    echo "   - The directory /opt/flipunit exists"
    echo "   - You have write permissions"
    exit 1
fi

