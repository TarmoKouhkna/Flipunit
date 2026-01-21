#!/usr/bin/env python3
"""
Script to add header removal code to sitemap view in flipunit/urls.py
Run this on the server: python3 fix_sitemap_headers.py
"""

import re
import sys
from pathlib import Path

FILE_PATH = Path("/opt/flipunit/flipunit/urls.py")

if not FILE_PATH.exists():
    print(f"Error: {FILE_PATH} not found!")
    sys.exit(1)

# Read the file
with open(FILE_PATH, 'r') as f:
    content = f.read()

# Check if already fixed
if 'headers_to_remove' in content:
    print("✅ Fix already applied!")
    sys.exit(0)

# Create backup
backup_path = FILE_PATH.with_suffix(f'.urls.py.backup.{__import__("datetime").datetime.now().strftime("%Y%m%d_%H%M%S")}')
with open(backup_path, 'w') as f:
    f.write(content)
print(f"📋 Backup created: {backup_path}")

# Fix 1: Add header removal after Content-Length (success case)
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

# Fix 2: Add header removal in error case
pattern2 = r'(        error_xml = \'<\?xml version="1\.0" encoding="UTF-8"\?>\n<urlset xmlns="http://www\.sitemaps\.org/schemas/sitemap/0\.9"></urlset>\n\'\n        return HttpResponse\(error_xml\.encode\(\'utf-8\'\), content_type=\'application/xml; charset=utf-8\'\))'
replacement2 = r'''        error_xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"></urlset>\n'
        http_response = HttpResponse(error_xml.encode('utf-8'), content_type='application/xml; charset=utf-8')
        
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
        
        return http_response'''

content = re.sub(pattern2, replacement2, content)

# Write the fixed content
with open(FILE_PATH, 'w') as f:
    f.write(content)

print("✅ Fix applied successfully!")
print("")
print("Next steps:")
print("  1. Exit nano (if still open): Ctrl+X, then N (don't save)")
print("  2. Restart the container: docker-compose restart web")
print("  3. Verify: curl -I https://flipunit.eu/sitemap.xml")
