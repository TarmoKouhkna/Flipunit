#!/bin/bash
# Verify and fix nginx sitemap configuration

echo "Checking current nginx config for sitemap..."
sudo grep -A 10 "location = /sitemap.xml" /etc/nginx/sites-available/flipunit.eu

echo ""
echo "Testing if headers-more module is available..."
nginx -V 2>&1 | grep -o with-http_headers_more_module || echo "headers-more module not found"







