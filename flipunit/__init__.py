# Monkey-patch Django's SitemapFeed to prevent XSL stylesheet addition
# This must be done before Django imports the sitemap views
from django.utils.feedgenerator import SitemapFeed
import re

_original_write = SitemapFeed.write
def write_without_xsl(self, outfile, encoding):
    """Override write method to prevent XSL stylesheet addition"""
    from io import BytesIO
    
    # Create temporary buffer
    buffer = BytesIO()
    # Call original write method
    _original_write(self, buffer, encoding)
    
    # Get content and remove XSL
    content = buffer.getvalue().decode(encoding)
    # Remove XSL reference using multiple methods
    content = re.sub(r'<\?xml-stylesheet[^>]*\?>\s*', '', content, flags=re.IGNORECASE)
    # Also filter line by line
    lines = content.split('\n')
    content = '\n'.join([l for l in lines if 'xml-stylesheet' not in l.lower()])
    
    # Write to actual output
    outfile.write(content.encode(encoding))

# Apply monkey patch early
SitemapFeed.write = write_without_xsl

