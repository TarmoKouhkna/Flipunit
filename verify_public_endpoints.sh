#!/bin/bash

# Public Endpoint Verification Script
# Tests all fixes via public HTTPS endpoints

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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
echo -e "${BLUE}║   Public Endpoint Verification - Today's Fixes        ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Test 1: Main Website Accessibility${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

MAIN_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://flipunit.eu/ 2>/dev/null || echo "000")
if [ "$MAIN_CODE" = "200" ]; then
    test_result "PASS" "Main website accessible (HTTP $MAIN_CODE)"
else
    test_result "FAIL" "Main website returned HTTP $MAIN_CODE"
fi

WWW_CODE=$(curl -s -o /dev/null -w "%{http_code}" -L https://www.flipunit.eu/ 2>/dev/null || echo "000")
if [ "$WWW_CODE" = "200" ]; then
    test_result "PASS" "WWW subdomain accessible (HTTP $WWW_CODE)"
elif [ "$WWW_CODE" = "301" ] || [ "$WWW_CODE" = "302" ]; then
    test_result "PASS" "WWW subdomain redirects correctly (HTTP $WWW_CODE)"
else
    test_result "WARN" "WWW subdomain returned HTTP $WWW_CODE"
fi

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Test 2: Sitemap Endpoint - HTTP Status${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

SITEMAP_HEADERS=$(curl -s -I https://flipunit.eu/sitemap.xml 2>/dev/null || echo "")
HTTP_CODE=$(echo "$SITEMAP_HEADERS" | head -1 | grep -oE '[0-9]{3}' || echo "000")

if [ "$HTTP_CODE" = "200" ]; then
    test_result "PASS" "Sitemap returns HTTP 200"
else
    test_result "FAIL" "Sitemap returned HTTP $HTTP_CODE"
    echo "   Response headers:"
    echo "$SITEMAP_HEADERS" | head -5
fi

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Test 3: Sitemap Content-Type${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

CONTENT_TYPE=$(echo "$SITEMAP_HEADERS" | grep -i "content-type" | head -1 || echo "")
if echo "$CONTENT_TYPE" | grep -qi "application/xml\|text/xml"; then
    test_result "PASS" "Sitemap has correct Content-Type"
    echo "   $CONTENT_TYPE"
else
    test_result "FAIL" "Sitemap has incorrect Content-Type"
    echo "   Found: $CONTENT_TYPE"
    echo "   Expected: application/xml or text/xml"
fi

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Test 4: Security Headers Removal (Critical Fix)${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Check for security headers that should NOT be present
X_FRAME=$(echo "$SITEMAP_HEADERS" | grep -i "X-Frame-Options" || echo "")
X_CONTENT=$(echo "$SITEMAP_HEADERS" | grep -i "X-Content-Type-Options" || echo "")
REFERRER=$(echo "$SITEMAP_HEADERS" | grep -i "Referrer-Policy" || echo "")
COOP=$(echo "$SITEMAP_HEADERS" | grep -i "Cross-Origin-Opener-Policy" || echo "")

if [ -z "$X_FRAME" ]; then
    test_result "PASS" "X-Frame-Options header removed"
else
    test_result "FAIL" "X-Frame-Options header still present: $X_FRAME"
fi

if [ -z "$X_CONTENT" ]; then
    test_result "PASS" "X-Content-Type-Options header removed"
else
    test_result "FAIL" "X-Content-Type-Options header still present: $X_CONTENT"
fi

if [ -z "$REFERRER" ]; then
    test_result "PASS" "Referrer-Policy header removed"
else
    test_result "FAIL" "Referrer-Policy header still present: $REFERRER"
fi

if [ -z "$COOP" ]; then
    test_result "PASS" "Cross-Origin-Opener-Policy header removed"
else
    test_result "FAIL" "Cross-Origin-Opener-Policy header still present: $COOP"
fi

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Test 5: X-Robots-Tag Header (Critical for SEO)${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

X_ROBOTS=$(echo "$SITEMAP_HEADERS" | grep -i "X-Robots-Tag" || echo "")
if [ -z "$X_ROBOTS" ]; then
    test_result "PASS" "X-Robots-Tag header not present (or empty)"
elif echo "$X_ROBOTS" | grep -qi "noindex"; then
    test_result "FAIL" "X-Robots-Tag contains 'noindex' - this blocks Google!"
    echo "   Found: $X_ROBOTS"
else
    test_result "WARN" "X-Robots-Tag present: $X_ROBOTS"
fi

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Test 6: Sitemap XML Content Validation${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

SITEMAP_CONTENT=$(curl -s https://flipunit.eu/sitemap.xml 2>/dev/null || echo "")

if [ -z "$SITEMAP_CONTENT" ]; then
    test_result "FAIL" "Sitemap content is empty"
else
    if echo "$SITEMAP_CONTENT" | grep -q "<?xml"; then
        test_result "PASS" "Sitemap contains valid XML declaration"
    else
        test_result "FAIL" "Sitemap missing XML declaration"
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
    
    # Check if sitemap is wrapped in HTML (should not be)
    if echo "$SITEMAP_CONTENT" | grep -q "<!DOCTYPE html\|<html"; then
        test_result "FAIL" "Sitemap is wrapped in HTML (should be pure XML)"
    else
        test_result "PASS" "Sitemap is pure XML (not wrapped in HTML)"
    fi
fi

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Test 7: Full Sitemap Headers Display${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

echo "Complete sitemap response headers:"
echo "$SITEMAP_HEADERS" | head -20

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
    echo -e "${GREEN}║   Your sitemap fixes are working correctly!          ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${BLUE}📋 Next Steps:${NC}"
    echo "   1. Verify in Google Search Console:"
    echo "      - Remove old sitemap entry"
    echo "      - Wait 2-3 minutes"
    echo "      - Re-submit: https://flipunit.eu/sitemap.xml"
    echo "      - Use 'Test URL' to verify"
    echo ""
    echo "   2. Monitor for any crawl errors in Search Console"
    exit 0
else
    echo -e "${RED}╔════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║   ❌ Some Tests Failed - Review Above                 ║${NC}"
    echo -e "${RED}╚════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${YELLOW}🔧 Troubleshooting:${NC}"
    echo "   1. Check if middleware is deployed:"
    echo "      ssh \${VPS_HOST:-ubuntu@YOUR_SERVER_IP} 'cd /opt/flipunit && cat flipunit/middleware.py'"
    echo ""
    echo "   2. Check if middleware is registered:"
    echo "      ssh \${VPS_HOST:-ubuntu@YOUR_SERVER_IP} 'cd /opt/flipunit && grep middleware flipunit/settings.py'"
    echo ""
    echo "   3. Restart web container:"
    echo "      ssh \${VPS_HOST:-ubuntu@YOUR_SERVER_IP} 'cd /opt/flipunit && docker-compose restart web'"
    echo ""
    echo "   4. Check container logs:"
    echo "      ssh \${VPS_HOST:-ubuntu@YOUR_SERVER_IP} 'cd /opt/flipunit && docker-compose logs web | tail -50'"
    exit 1
fi
