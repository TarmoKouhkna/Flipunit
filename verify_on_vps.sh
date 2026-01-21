#!/bin/bash

# Quick Verification Script - Run this ON the VPS
# Usage: ssh ubuntu@217.146.78.140 'bash -s' < verify_on_vps.sh
# Or: Copy to VPS and run: bash verify_on_vps.sh

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

PASSED=0
FAILED=0

test_result() {
    local status=$1
    local message=$2
    if [ "$status" = "PASS" ]; then
        echo -e "${GREEN}✅${NC} $message"
        ((PASSED++))
    else
        echo -e "${RED}❌${NC} $message"
        ((FAILED++))
    fi
}

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   VPS Deployment Verification          ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""

cd /opt/flipunit 2>/dev/null || {
    echo -e "${RED}❌ Not in /opt/flipunit directory${NC}"
    exit 1
}

echo -e "${BLUE}1. Checking Docker Containers...${NC}"
CONTAINERS=$(docker-compose ps 2>/dev/null || echo "")
if echo "$CONTAINERS" | grep -q "flipunit-web.*Up"; then
    test_result "PASS" "Web container is running"
else
    test_result "FAIL" "Web container is not running"
fi

if echo "$CONTAINERS" | grep -q "flipunit-postgres.*Up"; then
    test_result "PASS" "PostgreSQL container is running"
else
    test_result "FAIL" "PostgreSQL container is not running"
fi

echo ""
echo -e "${BLUE}2. Checking Middleware File...${NC}"
if [ -f "flipunit/middleware.py" ]; then
    test_result "PASS" "Middleware file exists"
    if grep -q "RemoveSitemapSecurityHeadersMiddleware" flipunit/middleware.py; then
        test_result "PASS" "Middleware class found"
    else
        test_result "FAIL" "Middleware class not found"
    fi
else
    test_result "FAIL" "Middleware file not found"
fi

echo ""
echo -e "${BLUE}3. Checking Sitemap View...${NC}"
if grep -q "headers_to_remove" flipunit/urls.py; then
    test_result "PASS" "Sitemap view has header removal code"
else
    test_result "FAIL" "Sitemap view missing header removal code"
fi

echo ""
echo -e "${BLUE}4. Testing Sitemap Endpoint...${NC}"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://flipunit.eu/sitemap.xml 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "200" ]; then
    test_result "PASS" "Sitemap returns HTTP 200"
else
    test_result "FAIL" "Sitemap returned HTTP $HTTP_CODE"
fi

echo ""
echo -e "${BLUE}5. Checking Sitemap Headers...${NC}"
HEADERS=$(curl -s -I https://flipunit.eu/sitemap.xml 2>/dev/null || echo "")
CONTENT_TYPE=$(echo "$HEADERS" | grep -i "content-type" | head -1 || echo "")

if echo "$CONTENT_TYPE" | grep -qi "application/xml\|text/xml"; then
    test_result "PASS" "Content-Type is correct: $CONTENT_TYPE"
else
    test_result "FAIL" "Content-Type is incorrect: $CONTENT_TYPE"
fi

# Check for security headers (should NOT be present)
if echo "$HEADERS" | grep -qi "X-Frame-Options"; then
    test_result "FAIL" "X-Frame-Options header still present"
else
    test_result "PASS" "X-Frame-Options header removed"
fi

if echo "$HEADERS" | grep -qi "X-Content-Type-Options"; then
    test_result "FAIL" "X-Content-Type-Options header still present"
else
    test_result "PASS" "X-Content-Type-Options header removed"
fi

X_ROBOTS=$(echo "$HEADERS" | grep -i "X-Robots-Tag" || echo "")
if [ -n "$X_ROBOTS" ]; then
    if echo "$X_ROBOTS" | grep -qi "noindex"; then
        test_result "FAIL" "X-Robots-Tag contains noindex: $X_ROBOTS"
    else
        test_result "PASS" "X-Robots-Tag present but not noindex: $X_ROBOTS"
    fi
else
    test_result "PASS" "X-Robots-Tag header not present"
fi

echo ""
echo -e "${BLUE}6. Checking Sitemap Content...${NC}"
CONTENT=$(curl -s https://flipunit.eu/sitemap.xml 2>/dev/null || echo "")
if echo "$CONTENT" | grep -q "<?xml"; then
    test_result "PASS" "Sitemap contains XML declaration"
else
    test_result "FAIL" "Sitemap missing XML declaration"
fi

if echo "$CONTENT" | grep -q "<urlset"; then
    test_result "PASS" "Sitemap contains urlset element"
else
    test_result "FAIL" "Sitemap missing urlset element"
fi

if echo "$CONTENT" | grep -q "<!DOCTYPE html\|<html"; then
    test_result "FAIL" "Sitemap is wrapped in HTML"
else
    test_result "PASS" "Sitemap is pure XML (not HTML)"
fi

URL_COUNT=$(echo "$CONTENT" | grep -c "<url>" 2>/dev/null || echo "0")
if [ "$URL_COUNT" -gt 0 ]; then
    test_result "PASS" "Sitemap contains $URL_COUNT URL entries"
else
    test_result "FAIL" "Sitemap contains no URL entries"
fi

echo ""
echo -e "${BLUE}7. Testing Main Website...${NC}"
MAIN_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://flipunit.eu/ 2>/dev/null || echo "000")
if [ "$MAIN_CODE" = "200" ]; then
    test_result "PASS" "Main website accessible (HTTP $MAIN_CODE)"
else
    test_result "FAIL" "Main website returned HTTP $MAIN_CODE"
fi

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ Passed: $PASSED${NC}"
echo -e "${RED}❌ Failed: $FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║   ✅ All Tests Passed!                  ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
    exit 0
else
    echo -e "${RED}╔════════════════════════════════════════╗${NC}"
    echo -e "${RED}║   ❌ Some Tests Failed                 ║${NC}"
    echo -e "${RED}╚════════════════════════════════════════╝${NC}"
    echo ""
    echo "Troubleshooting:"
    echo "  1. Check logs: docker-compose logs web | tail -50"
    echo "  2. Restart container: docker-compose restart web"
    echo "  3. Pull latest code: git pull"
    exit 1
fi
