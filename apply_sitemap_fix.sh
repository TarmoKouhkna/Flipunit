#!/bin/bash

# Script to apply sitemap header fix on the server
# Run this on your server: bash apply_sitemap_fix.sh

FILE="/opt/flipunit/flipunit/urls.py"

if [ ! -f "$FILE" ]; then
    echo "Error: $FILE not found"
    exit 1
fi

# Check if fix is already applied
if grep -q "headers_to_remove" "$FILE"; then
    echo "Fix already applied!"
    exit 0
fi

# Create backup
cp "$FILE" "${FILE}.backup.$(date +%Y%m%d_%H%M%S)"

# Add header removal code after line 83 (after Content-Length)
python3 << 'PYTHON_SCRIPT'
import re

file_path = "/opt/flipunit/flipunit/urls.py"

with open(file_path, 'r') as f:
    content = f.read()

# Check if already fixed
if 'headers_to_remove' in content:
    print("Fix already applied!")
    exit(0)

# Pattern to find the return statement after Content-Length
pattern1 = r'(        http_response\[\'Content-Length\'\] = str\(len\(xml_bytes\)\)\n)(\n        return http_response)'

replacement1 = r'''\1        
        # Remove security headers that might interfere with Google's crawler
        # These headers are fine for HTML pages but can cause issues for XML sitemaps
        # Django's SecurityMiddleware adds these headers, but we need to remove them for sitemaps
        headers_to_remove = [
            'X-Frame-Options',
            'X-Content-Type-Options',
            'Referrer-Policy',
            'Cross-Origin-Opener-Policy',
            'X-Robots-Tag',  # Ensure no noindex header
        ]
        for header in headers_to_remove:
            if header in http_response:
                del http_response[header]
\2'''

content = re.sub(pattern1, replacement1, content)

# Pattern to find the error response return
pattern2 = r'(        error_xml = \'<\?xml version="1\.0" encoding="UTF-8"\?>\n<urlset xmlns="http://www\.sitemaps\.org/schemas/sitemap/0\.9"></urlset>\n\'\n        http_response = HttpResponse\(error_xml\.encode\(\'utf-8\'\), content_type=\'application/xml; charset=utf-8\'\)\n)(\n        \n        return http_response)'

replacement2 = r'''\1
        
        # Remove security headers from error response as well
        headers_to_remove = [
            'X-Frame-Options',
            'X-Content-Type-Options',
            'Referrer-Policy',
            'Cross-Origin-Opener-Policy',
            'X-Robots-Tag',
        ]
        for header in headers_to_remove:
            if header in http_response:
                del http_response[header]
\2'''

content = re.sub(pattern2, replacement2, content)

with open(file_path, 'w') as f:
    f.write(content)

print("Fix applied successfully!")
PYTHON_SCRIPT

if [ $? -eq 0 ]; then
    echo "✅ Fix applied! Now restart the container:"
    echo "   docker-compose restart web"
else
    echo "❌ Failed to apply fix. Restore backup if needed."
fi
