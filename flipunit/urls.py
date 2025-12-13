"""
URL configuration for flipunit project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.sitemaps.views import sitemap as sitemap_view
from django.views.generic import TemplateView
from . import views
from .sitemaps import StaticViewSitemap
# Note: Monkey-patch is applied in flipunit/__init__.py to ensure it runs early

sitemaps = {
    'static': StaticViewSitemap,
}

def sitemap(request):
    """Custom sitemap view that removes noindex header for Google Search Console and fixes date format"""
    print("[SITEMAP DEBUG] sitemap() function called", flush=True)
    from django.http import HttpResponse
    import re
    from datetime import datetime, timezone
    import xml.dom.minidom
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        response = sitemap_view(request, sitemaps)
        # Ensure correct content type
        response['Content-Type'] = 'application/xml; charset=utf-8'
        # Remove X-Robots-Tag header if present (Google needs to index sitemaps)
        if 'X-Robots-Tag' in response:
            del response['X-Robots-Tag']
        
        # Render the response to get the content
        response.render()
        
        # Get the XML content
        xml_content = response.content.decode('utf-8')
    except Exception as e:
        logger.error(f"Error getting sitemap content: {e}", exc_info=True)
        # Return a basic error sitemap
        xml_content = '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"></urlset>'
    
    # Find all lastmod tags with date-only format and add time + timezone
    def fix_date_format(match):
        date_str = match.group(1)
        # Add current UTC time and UTC timezone
        current_time = datetime.now(timezone.utc).strftime('T%H:%M:%S+00:00')
        return f'<lastmod>{date_str}{current_time}</lastmod>'
    
    # Replace date-only lastmod tags with full ISO 8601 format
    date_only_pattern = r'<lastmod>\s*(\d{4}-\d{2}-\d{2})\s*</lastmod>'
    xml_content = re.sub(date_only_pattern, fix_date_format, xml_content)
    
    # Remove XSL stylesheet reference - Google Search Console has issues with it
    # Use aggressive regex removal (don't split by lines as it interferes with formatting)
    xml_content = re.sub(r'<\?xml-stylesheet[^>]*\?>\s*', '', xml_content, flags=re.IGNORECASE | re.MULTILINE | re.DOTALL)
    xml_content = re.sub(r'<\?xml-stylesheet.*?\?>\s*', '', xml_content, flags=re.IGNORECASE | re.DOTALL)
    # Final fallback: remove any remaining XSL references
    while 'xml-stylesheet' in xml_content.lower():
        start_idx = xml_content.lower().find('<?xml-stylesheet')
        if start_idx == -1:
            break
        end_idx = xml_content.find('?>', start_idx)
        if end_idx == -1:
            break
        xml_content = xml_content[:start_idx] + xml_content[end_idx + 2:].lstrip()
    
    # Format XML with proper indentation using simple string replacement
    # Count occurrences before formatting
    url_count_before = xml_content.count('<url><loc>')
    sample_content = xml_content[:500].replace('\n', '\\n').replace('\r', '\\r')
    print(f"[SITEMAP DEBUG] Found {url_count_before} URL entries to format", flush=True)
    print(f"[SITEMAP DEBUG] Sample content (first 500 chars): {sample_content}", flush=True)
    logger.warning(f"Sitemap formatting: Found {url_count_before} URL entries to format")
    
    # Split XML declaration and urlset if not already split
    xml_content = xml_content.replace('?><urlset', '?>\n<urlset')
    
    # Format first <url> after <urlset> - find urlset closing tag and format first url
    urlset_pos = xml_content.find('<urlset')
    if urlset_pos >= 0:
        urlset_end = xml_content.find('>', urlset_pos)
        if urlset_end > 0 and urlset_end + 1 < len(xml_content):
            # Check if <url> comes right after urlset (handle whitespace)
            next_chars = xml_content[urlset_end+1:urlset_end+10].strip()
            if next_chars.startswith('<url>'):
                # Insert newline and indentation before <url>
                insert_pos = urlset_end + 1
                while insert_pos < len(xml_content) and xml_content[insert_pos] in ' \t\n':
                    insert_pos += 1
                xml_content = xml_content[:insert_pos] + '\n  ' + xml_content[insert_pos:]
    
    # Format child elements - use string replacement (replaces ALL instances)
    # Apply multiple times to ensure all are caught
    for iteration in range(10):
        old_content = xml_content
        xml_content = xml_content.replace('<url><loc>', '<url>\n    <loc>')
        xml_content = xml_content.replace('</loc><lastmod>', '</loc>\n    <lastmod>')
        xml_content = xml_content.replace('</lastmod><changefreq>', '</lastmod>\n    <changefreq>')
        xml_content = xml_content.replace('</changefreq><priority>', '</changefreq>\n    <priority>')
        xml_content = xml_content.replace('</priority></url>', '</priority>\n  </url>')
        # Stop if no changes were made
        if xml_content == old_content:
            print(f"[SITEMAP DEBUG] Stopped after {iteration+1} iterations (no more changes)", flush=True)
            logger.warning(f"Sitemap formatting: Stopped after {iteration+1} iterations (no more changes)")
            break
    
    # Format </url><url> pairs - separate consecutive URLs
    xml_content = xml_content.replace('</url><url>', '</url>\n  <url>')
    
    # Format closing </urlset>
    xml_content = xml_content.replace('</url></urlset>', '</url>\n</urlset>')
    
    # Verify formatting worked
    url_count_after = xml_content.count('\n    <loc>')
    print(f"[SITEMAP DEBUG] After formatting, found {url_count_after} formatted URL entries", flush=True)
    logger.warning(f"Sitemap formatting: After formatting, found {url_count_after} formatted URL entries")
    
    # Clean up and ensure proper formatting
    xml_content = xml_content.strip() + '\n'
    
    # Create a new HttpResponse to ensure proper response handling
    # This avoids any issues with StreamingHttpResponse or other response types
    http_response = HttpResponse(xml_content.encode('utf-8'), content_type='application/xml; charset=utf-8')
    http_response['Content-Length'] = str(len(http_response.content))
    
    return http_response

urlpatterns = [
    path('admin/', admin.site.urls),
    path('favicon.ico', views.favicon_view, name='favicon'),
    path('', views.home, name='home'),
    path('search/', views.search, name='search'),
    path('converters/', include('converters.urls')),
    path('image-converter/', include('image_converter.urls')),
    path('media-converter/', include('media_converter.urls')),
    path('pdf-tools/', include('pdf_tools.urls')),
    path('currency/', include('currency_converter.urls')),
    path('utilities/', include('utilities.urls')),
    path('color-picker/', include('color_picker.urls')),
    path('archive-converter/', include('archive_converter.urls')),
    path('text-converter/', include('text_converter.urls')),
    path('developer-converter/', include('developer_converter.urls')),
    path('isdown/', include('isdown.urls')),
    path('youtube-thumbnail/', include('youtube_thumbnail.urls')),
    path('sitemap.xml', sitemap, name='django.contrib.sitemaps.views.sitemap'),
    path('robots.txt', TemplateView.as_view(template_name='robots.txt', content_type='text/plain')),
]

if settings.DEBUG:
    # Serve media files in development
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # Note: Static files are automatically served by Django's runserver in DEBUG mode
    # from STATICFILES_DIRS and app static directories. WhiteNoise handles production.
