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
    # Use multiple aggressive methods to ensure complete removal
    
    # Method 1: Regex removal (handles both single-line and multi-line)
    xml_content = re.sub(r'<\?xml-stylesheet[^>]*\?>\s*', '', xml_content, flags=re.IGNORECASE | re.MULTILINE | re.DOTALL)
    xml_content = re.sub(r'<\?xml-stylesheet.*?\?>\s*', '', xml_content, flags=re.IGNORECASE | re.DOTALL)
    
    # Method 2: Line-by-line filtering (most reliable for separate lines)
    lines = xml_content.split('\n')
    filtered_lines = [line for line in lines if 'xml-stylesheet' not in line.lower()]
    xml_content = '\n'.join(filtered_lines)
    
    # Method 3: String replacement as final fallback
    # Remove any remaining XSL references character by character
    while 'xml-stylesheet' in xml_content.lower():
        # Find and remove the XSL processing instruction
        start_idx = xml_content.lower().find('<?xml-stylesheet')
        if start_idx == -1:
            break
        # Find the closing ?>
        end_idx = xml_content.find('?>', start_idx)
        if end_idx == -1:
            break
        # Remove the entire processing instruction including any whitespace after
        xml_content = xml_content[:start_idx] + xml_content[end_idx + 2:].lstrip()
    
    try:
        # Format XML with proper indentation for better Google Search Console parsing
        # Use minidom to properly format the XML - this is more reliable than regex
        try:
            # Parse the XML
            dom = xml.dom.minidom.parseString(xml_content)
            # Format with 2-space indentation
            formatted_xml = dom.toprettyxml(indent='  ', encoding=None)
            # Remove the extra newline that minidom adds after the XML declaration
            formatted_xml = re.sub(r'<\?xml[^>]*\?>\n\n', r'<?xml version="1.0" encoding="UTF-8"?>\n', formatted_xml)
            # Remove any trailing whitespace but keep final newline
            formatted_xml = formatted_xml.rstrip() + '\n'
            # Use formatted XML if it's valid
            if formatted_xml and len(formatted_xml) > 100:
                xml_content = formatted_xml
        except Exception as format_error:
            logger.warning(f"Minidom formatting failed, using regex fallback: {format_error}")
            # If minidom fails, fall back to simple regex formatting
            # Remove spaces between tags first
            xml_content = re.sub(r'> +<', '><', xml_content).strip()
            # Add newlines at key points
            xml_content = re.sub(r'(<\?xml[^>]*\?>)(<urlset[^>]*>)', r'\1\n\2\n', xml_content)
            xml_content = re.sub(r'(<urlset[^>]*>)(<url>)', r'\1\n  \2', xml_content)
            xml_content = re.sub(r'></url><url>', '>\n  </url>\n  <url>', xml_content)
            xml_content = re.sub(r'<url><loc>', '<url>\n    <loc>', xml_content)
            xml_content = re.sub(r'</loc><lastmod>', '</loc>\n    <lastmod>', xml_content)
            xml_content = re.sub(r'</lastmod><changefreq>', '</lastmod>\n    <changefreq>', xml_content)
            xml_content = re.sub(r'</changefreq><priority>', '</changefreq>\n    <priority>', xml_content)
            xml_content = re.sub(r'</priority></url>', '</priority>\n  </url>', xml_content)
            xml_content = re.sub(r'(</url>)(</urlset>)', r'\1\n\2', xml_content)
            xml_content = xml_content.strip() + '\n'
        
        # Create a new HttpResponse to ensure proper response handling
        # This avoids any issues with StreamingHttpResponse or other response types
        http_response = HttpResponse(xml_content.encode('utf-8'), content_type='application/xml; charset=utf-8')
        http_response['Content-Length'] = str(len(http_response.content))
        
        return http_response
    except Exception as e:
        logger.error(f"Error processing sitemap: {e}", exc_info=True)
        # Return a basic valid sitemap even if formatting fails
        fallback_xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"></urlset>\n'
        return HttpResponse(fallback_xml.encode('utf-8'), content_type='application/xml; charset=utf-8')

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
