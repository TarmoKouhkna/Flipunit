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
    """Custom sitemap view that generates properly formatted XML using ElementTree"""
    from django.http import HttpResponse
    from datetime import datetime, timezone
    import xml.etree.ElementTree as ET
    from xml.dom import minidom
    
    try:
        # Generate sitemap XML using ElementTree for proper structure
        current_time = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S+00:00')
        
        # Create root element with namespaces
        urlset = ET.Element('urlset')
        urlset.set('xmlns', 'http://www.sitemaps.org/schemas/sitemap/0.9')
        urlset.set('xmlns:xhtml', 'http://www.w3.org/1999/xhtml')
        
        # Get all URLs from the sitemap
        sitemap_instance = StaticViewSitemap()
        items = sitemap_instance.items()
        
        # Add each URL entry
        for item in items:
            try:
                relative_url = sitemap_instance.location(item)
                # Make URL absolute using the protocol from sitemap_instance
                if hasattr(sitemap_instance, 'protocol') and sitemap_instance.protocol:
                    absolute_url = f"{sitemap_instance.protocol}://{request.get_host()}{relative_url}"
                else:
                    absolute_url = request.build_absolute_uri(relative_url)
                
                # Create url element
                url_elem = ET.SubElement(urlset, 'url')
                ET.SubElement(url_elem, 'loc').text = absolute_url
                ET.SubElement(url_elem, 'lastmod').text = current_time
                ET.SubElement(url_elem, 'changefreq').text = sitemap_instance.changefreq
                ET.SubElement(url_elem, 'priority').text = str(sitemap_instance.priority)
            except Exception:
                # Skip URLs that can't be reversed
                continue
        
        # Convert to string and format with minidom for proper indentation
        rough_string = ET.tostring(urlset, encoding='unicode')
        reparsed = minidom.parseString(rough_string.encode('utf-8'))
        xml_content = reparsed.toprettyxml(indent='  ', encoding='utf-8').decode('utf-8')
        
        # Fix XML declaration and remove empty line after it
        # minidom adds: <?xml version="1.0" encoding="utf-8"?>\n\n<urlset...
        # We want: <?xml version="1.0" encoding="UTF-8"?>\n<urlset...
        xml_content = xml_content.replace('<?xml version="1.0" encoding="utf-8"?>', '<?xml version="1.0" encoding="UTF-8"?>')
        # Remove empty line after XML declaration if present
        xml_content = xml_content.replace('<?xml version="1.0" encoding="UTF-8"?>\n\n', '<?xml version="1.0" encoding="UTF-8"?>\n')
        
        # Ensure it ends with exactly one newline
        xml_content = xml_content.rstrip() + '\n'
        
        # Create HttpResponse with properly formatted XML
        xml_bytes = xml_content.encode('utf-8')
        http_response = HttpResponse(xml_bytes, content_type='application/xml; charset=utf-8')
        http_response['Content-Length'] = str(len(xml_bytes))
        
        return http_response
    except Exception as e:
        # Return a minimal valid sitemap on any error to prevent 500 errors
        error_xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"></urlset>\n'
        return HttpResponse(error_xml.encode('utf-8'), content_type='application/xml; charset=utf-8')

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
