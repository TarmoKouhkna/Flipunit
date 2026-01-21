#!/bin/bash

# Comprehensive VPS Deployment Verification Script
# This script checks that all fixes made today are deployed and working on the VPS

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

VPS_HOST="${1:-ubuntu@217.146.78.140}"
PROJECT_DIR="/opt/flipunit"

echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   VPS Deployment Verification - Today's Fixes         ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "VPS: $VPS_HOST"
echo "Project: $PROJECT_DIR"
echo ""

# Track verification results
PASSED=0
FAILED=0
WARNINGS=0

# Function to print test result
test_result() {
    local status=$1
    local message=$2
    if [ "$status" = "PASS" ]; then
        echo -e "${GREEN}✅ PASS:${NC} $message"
        ((PASSED++))
    elif [ "$status" = "FAIL" ]; then
        echo -e "${RED}❌ FAIL:${NC} $message"
        ((FAILED++))
    else
        echo -e "${YELLOW}⚠️  WARN:${NC} $message"
        ((WARNINGS++))
    fi
}

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Step 1: SSH Connection Test${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

if ssh -o ConnectTimeout=10 -o BatchMode=yes "$VPS_HOST" exit 2>/dev/null; then
    test_result "PASS" "SSH connection successful"
else
    test_result "FAIL" "SSH connection failed"
    echo "   Please check:"
    echo "   - SSH key is added to server"
    echo "   - Server is accessible"
    echo "   - Connection string is correct: $VPS_HOST"
    exit 1
fi

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Step 2: Check Docker Containers Status${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

CONTAINER_STATUS=$(ssh "$VPS_HOST" "cd $PROJECT_DIR && docker-compose ps 2>/dev/null" || echo "")

if echo "$CONTAINER_STATUS" | grep -q "flipunit-web.*Up"; then
    test_result "PASS" "Web container is running"
else
    test_result "FAIL" "Web container is not running"
fi

if echo "$CONTAINER_STATUS" | grep -q "flipunit-postgres.*Up"; then
    test_result "PASS" "PostgreSQL container is running"
else
    test_result "FAIL" "PostgreSQL container is not running"
fi

if echo "$CONTAINER_STATUS" | grep -q "flipunit-redis.*Up"; then
    test_result "PASS" "Redis container is running"
else
    test_result "WARN" "Redis container is not running (may not be critical)"
fi

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Step 3: Check Sitemap Middleware Deployment${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Check if middleware file exists
if ssh "$VPS_HOST" "test -f $PROJECT_DIR/flipunit/middleware.py"; then
    test_result "PASS" "Middleware file exists on VPS"
    
    # Check if middleware class exists
    if ssh "$VPS_HOST" "grep -q 'RemoveSitemapSecurityHeadersMiddleware' $PROJECT_DIR/flipunit/middleware.py"; then
        test_result "PASS" "RemoveSitemapSecurityHeadersMiddleware class found"
    else
        test_result "FAIL" "RemoveSitemapSecurityHeadersMiddleware class not found"
    fi
else
    test_result "FAIL" "Middleware file not found on VPS"
fi

# Check if middleware is registered in settings.py
if ssh "$VPS_HOST" "grep -q 'flipunit.middleware.RemoveSitemapSecurityHeadersMiddleware' $PROJECT_DIR/flipunit/settings.py"; then
    test_result "PASS" "Middleware is registered in settings.py"
else
    test_result "WARN" "Middleware not registered in settings.py (may be using URL view fix instead)"
fi

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Step 4: Check Sitemap View Header Removal${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Check if sitemap view has header removal code
if ssh "$VPS_HOST" "grep -q 'headers_to_remove' $PROJECT_DIR/flipunit/urls.py"; then
    test_result "PASS" "Sitemap view has header removal code"
else
    test_result "FAIL" "Sitemap view missing header removal code"
fi

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Step 5: Check Docker Compose Configuration${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Check for logging configuration
if ssh "$VPS_HOST" "grep -q 'logging:' $PROJECT_DIR/docker-compose.yml"; then
    test_result "PASS" "Docker Compose has logging configuration"
else
    test_result "WARN" "Docker Compose missing logging configuration"
fi

# Check for volume mounts
if ssh "$VPS_HOST" "grep -q './flipunit:/app/flipunit' $PROJECT_DIR/docker-compose.yml"; then
    test_result "PASS" "Flipunit source code is mounted as volume"
else
    test_result "WARN" "Flipunit source code not mounted as volume (changes require rebuild)"
fi

if ssh "$VPS_HOST" "grep -q './templates:/app/templates' $PROJECT_DIR/docker-compose.yml"; then
    test_result "PASS" "Templates are mounted as volume"
else
    test_result "WARN" "Templates not mounted as volume"
fi

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Step 6: Test Sitemap Endpoint${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Test sitemap via HTTPS
echo "Testing: https://flipunit.eu/sitemap.xml"
SITEMAP_RESPONSE=$(curl -s -I -k https://flipunit.eu/sitemap.xml 2>/dev/null || echo "")
HTTP_CODE=$(echo "$SITEMAP_RESPONSE" | head -1 | grep -oE '[0-9]{3}' || echo "000")

if [ "$HTTP_CODE" = "200" ]; then
    test_result "PASS" "Sitemap returns HTTP 200"
else
    test_result "FAIL" "Sitemap returned HTTP $HTTP_CODE"
fi

# Check Content-Type
CONTENT_TYPE=$(echo "$SITEMAP_RESPONSE" | grep -i "content-type" | head -1 || echo "")
if echo "$CONTENT_TYPE" | grep -qi "application/xml\|text/xml"; then
    test_result "PASS" "Sitemap has correct Content-Type: $CONTENT_TYPE"
else
    test_result "WARN" "Sitemap Content-Type may be incorrect: $CONTENT_TYPE"
fi

# Check for security headers (should NOT be present)
if echo "$SITEMAP_RESPONSE" | grep -qi "X-Frame-Options\|X-Content-Type-Options\|Referrer-Policy"; then
    test_result "FAIL" "Security headers still present in sitemap response"
    echo "$SITEMAP_RESPONSE" | grep -i "X-Frame\|X-Content\|Referrer" || true
else
    test_result "PASS" "Security headers removed from sitemap response"
fi

# Check for X-Robots-Tag (should NOT be present or should not be noindex)
X_ROBOTS=$(echo "$SITEMAP_RESPONSE" | grep -i "X-Robots-Tag" || echo "")
if [ -n "$X_ROBOTS" ]; then
    if echo "$X_ROBOTS" | grep -qi "noindex"; then
        test_result "FAIL" "X-Robots-Tag contains noindex"
    else
        test_result "WARN" "X-Robots-Tag present but not noindex: $X_ROBOTS"
    fi
else
    test_result "PASS" "X-Robots-Tag header not present (or empty)"
fi

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Step 7: Test Sitemap Content${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

SITEMAP_CONTENT=$(curl -s -k https://flipunit.eu/sitemap.xml 2>/dev/null || echo "")

if echo "$SITEMAP_CONTENT" | grep -q "<?xml"; then
    test_result "PASS" "Sitemap contains valid XML declaration"
else
    test_result "FAIL" "Sitemap does not contain XML declaration"
fi

if echo "$SITEMAP_CONTENT" | grep -q "<urlset"; then
    test_result "PASS" "Sitemap contains urlset element"
else
    test_result "FAIL" "Sitemap missing urlset element"
fi

if echo "$SITEMAP_CONTENT" | grep -q "<url>"; then
    URL_COUNT=$(echo "$SITEMAP_CONTENT" | grep -c "<url>" || echo "0")
    test_result "PASS" "Sitemap contains $URL_COUNT URL entries"
else
    test_result "WARN" "Sitemap contains no URL entries"
fi

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Step 8: Check Nginx Configuration${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Check if nginx config has sitemap location block
NGINX_CONFIG=$(ssh "$VPS_HOST" "sudo cat /etc/nginx/sites-available/flipunit.eu 2>/dev/null" || echo "")

if echo "$NGINX_CONFIG" | grep -q "location = /sitemap.xml"; then
    test_result "PASS" "Nginx has sitemap location block"
    
    # Check if it has proxy_hide_header directives
    if echo "$NGINX_CONFIG" | grep -q "proxy_hide_header.*X-Frame-Options"; then
        test_result "PASS" "Nginx removes X-Frame-Options header"
    else
        test_result "WARN" "Nginx sitemap block may not remove headers (Django handles it)"
    fi
else
    test_result "WARN" "Nginx does not have dedicated sitemap block (Django handles it)"
fi

# Check nginx status
if ssh "$VPS_HOST" "sudo systemctl is-active --quiet nginx"; then
    test_result "PASS" "Nginx is running"
else
    test_result "FAIL" "Nginx is not running"
fi

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Step 9: Test Main Website Accessibility${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

MAIN_PAGE_CODE=$(curl -s -o /dev/null -w "%{http_code}" -k https://flipunit.eu/ 2>/dev/null || echo "000")
if [ "$MAIN_PAGE_CODE" = "200" ]; then
    test_result "PASS" "Main website is accessible (HTTP $MAIN_PAGE_CODE)"
else
    test_result "FAIL" "Main website returned HTTP $MAIN_PAGE_CODE"
fi

WWW_PAGE_CODE=$(curl -s -o /dev/null -w "%{http_code}" -k https://www.flipunit.eu/ 2>/dev/null || echo "000")
if [ "$WWW_PAGE_CODE" = "200" ] || [ "$WWW_PAGE_CODE" = "301" ] || [ "$WWW_PAGE_CODE" = "302" ]; then
    test_result "PASS" "WWW subdomain is accessible (HTTP $WWW_PAGE_CODE)"
else
    test_result "WARN" "WWW subdomain returned HTTP $WWW_PAGE_CODE"
fi

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Step 10: Check Recent Deployment Files${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Check if deployment scripts exist
if ssh "$VPS_HOST" "test -f $PROJECT_DIR/deploy_sitemap_fix.sh"; then
    test_result "PASS" "deploy_sitemap_fix.sh exists on VPS"
else
    test_result "WARN" "deploy_sitemap_fix.sh not found (may have been removed)"
fi

if ssh "$VPS_HOST" "test -f $PROJECT_DIR/deploy_sitemap_header_fix.sh"; then
    test_result "PASS" "deploy_sitemap_header_fix.sh exists on VPS"
else
    test_result "WARN" "deploy_sitemap_header_fix.sh not found (may have been removed)"
fi

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Final Summary${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${GREEN}✅ Passed: $PASSED${NC}"
echo -e "${YELLOW}⚠️  Warnings: $WARNINGS${NC}"
echo -e "${RED}❌ Failed: $FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}╔════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║   ✅ All Critical Tests Passed!                       ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════╝${NC}"
    exit 0
else
    echo -e "${RED}╔════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║   ❌ Some Tests Failed - Review Above                 ║${NC}"
    echo -e "${RED}╚════════════════════════════════════════════════════════╝${NC}"
    exit 1
fi
