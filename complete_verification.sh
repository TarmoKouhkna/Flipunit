#!/bin/bash

# Complete Verification Script - Run this ON the VPS
# This will check all aspects of today's deployment

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

PASSED=0
FAILED=0
WARNINGS=0

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

echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Complete VPS Deployment Verification                 ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

cd /opt/flipunit 2>/dev/null || {
    echo -e "${RED}❌ Not in /opt/flipunit directory${NC}"
    exit 1
}

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}1. Docker Containers Status${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

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

if echo "$CONTAINERS" | grep -q "flipunit-redis.*Up"; then
    test_result "PASS" "Redis container is running"
else
    test_result "WARN" "Redis container is not running (may not be critical)"
fi

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}2. Middleware File Deployment${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

if [ -f "flipunit/middleware.py" ]; then
    test_result "PASS" "Middleware file exists"
    
    if grep -q "RemoveSitemapSecurityHeadersMiddleware" flipunit/middleware.py; then
        test_result "PASS" "RemoveSitemapSecurityHeadersMiddleware class found"
        
        # Check if it has the header removal logic
        if grep -q "headers_to_remove" flipunit/middleware.py; then
            test_result "PASS" "Middleware has header removal logic"
        else
            test_result "WARN" "Middleware class exists but may not have header removal code"
        fi
    else
        test_result "FAIL" "Middleware class not found"
    fi
else
    test_result "FAIL" "Middleware file not found"
fi

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}3. Middleware Registration in Settings${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

if grep -q "flipunit.middleware.RemoveSitemapSecurityHeadersMiddleware" flipunit/settings.py; then
    test_result "PASS" "Middleware is registered in settings.py"
    
    # Check if it's in the right position (after SecurityMiddleware)
    MIDDLEWARE_LINE=$(grep -n "RemoveSitemapSecurityHeadersMiddleware" flipunit/settings.py | cut -d: -f1)
    SECURITY_LINE=$(grep -n "SecurityMiddleware" flipunit/settings.py | cut -d: -f1)
    
    if [ -n "$MIDDLEWARE_LINE" ] && [ -n "$SECURITY_LINE" ]; then
        if [ "$MIDDLEWARE_LINE" -gt "$SECURITY_LINE" ]; then
            test_result "PASS" "Middleware is positioned after SecurityMiddleware (correct)"
        else
            test_result "WARN" "Middleware is positioned before SecurityMiddleware (may not work correctly)"
        fi
    fi
else
    test_result "WARN" "Middleware not registered in settings.py (may be using URL view fix instead)"
fi

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}4. Sitemap View Header Removal Code${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

if grep -q "headers_to_remove" flipunit/urls.py; then
    test_result "PASS" "Sitemap view has header removal code"
    
    # Count how many times it appears (should be in both success and error cases)
    COUNT=$(grep -c "headers_to_remove" flipunit/urls.py || echo "0")
    if [ "$COUNT" -ge 2 ]; then
        test_result "PASS" "Header removal code found in multiple places (success + error cases)"
    else
        test_result "WARN" "Header removal code found but may only be in one case"
    fi
else
    test_result "FAIL" "Sitemap view missing header removal code"
fi

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}5. Docker Compose Configuration${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

if grep -q "logging:" docker-compose.yml; then
    test_result "PASS" "Docker Compose has logging configuration"
else
    test_result "WARN" "Docker Compose missing logging configuration"
fi

if grep -q "./flipunit:/app/flipunit" docker-compose.yml; then
    test_result "PASS" "Flipunit source code is mounted as volume (enables hot-reload)"
else
    test_result "WARN" "Flipunit source code not mounted as volume"
fi

if grep -q "./templates:/app/templates" docker-compose.yml; then
    test_result "PASS" "Templates are mounted as volume (enables hot-reload)"
else
    test_result "WARN" "Templates not mounted as volume"
fi

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}6. Sitemap Endpoint Test${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://flipunit.eu/sitemap.xml 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "200" ]; then
    test_result "PASS" "Sitemap returns HTTP 200"
else
    test_result "FAIL" "Sitemap returned HTTP $HTTP_CODE"
fi

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}7. Sitemap Headers Verification${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

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

if echo "$HEADERS" | grep -qi "Referrer-Policy"; then
    test_result "FAIL" "Referrer-Policy header still present"
else
    test_result "PASS" "Referrer-Policy header removed"
fi

if echo "$HEADERS" | grep -qi "Cross-Origin-Opener-Policy"; then
    test_result "FAIL" "Cross-Origin-Opener-Policy header still present"
else
    test_result "PASS" "Cross-Origin-Opener-Policy header removed"
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
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}8. Sitemap Content Validation${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

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
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}9. Main Website Test${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

MAIN_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://flipunit.eu/ 2>/dev/null || echo "000")
if [ "$MAIN_CODE" = "200" ]; then
    test_result "PASS" "Main website accessible (HTTP $MAIN_CODE)"
else
    test_result "FAIL" "Main website returned HTTP $MAIN_CODE"
fi

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}10. Nginx Status${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

if sudo systemctl is-active --quiet nginx 2>/dev/null; then
    test_result "PASS" "Nginx is running"
else
    test_result "FAIL" "Nginx is not running"
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
    echo -e "${GREEN}║   Your deployment is working correctly!                ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${BLUE}📋 Next Steps:${NC}"
    echo "   1. Submit sitemap to Google Search Console:"
    echo "      https://search.google.com/search-console"
    echo "   2. Remove old sitemap entry (if exists)"
    echo "   3. Add new sitemap: https://flipunit.eu/sitemap.xml"
    echo "   4. Use 'Test URL' to verify"
    exit 0
else
    echo -e "${RED}╔════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║   ❌ Some Tests Failed - Review Above                 ║${NC}"
    echo -e "${RED}╚════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${YELLOW}🔧 Troubleshooting:${NC}"
    echo "   1. Check container logs: docker-compose logs web | tail -50"
    echo "   2. Restart containers: docker-compose restart web"
    echo "   3. Pull latest code: git pull"
    echo "   4. Check middleware registration: grep -A 15 MIDDLEWARE flipunit/settings.py"
    exit 1
fi
