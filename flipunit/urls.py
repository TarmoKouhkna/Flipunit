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
    """Custom sitemap view that generates properly formatted XML from scratch"""
    from django.http import HttpResponse
    from datetime import datetime, timezone
    
    # Generate sitemap XML manually with proper formatting
    current_time = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S+00:00')
    
    # Build XML as a list of lines to preserve formatting
    xml_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">'
    ]
    
    # Get all URLs from the sitemap
    sitemap_instance = StaticViewSitemap()
    items = sitemap_instance.items()
    
    # Format each URL entry with proper indentation
    for item in items:
        try:
            relative_url = sitemap_instance.location(item)
            # Make URL absolute using the protocol from sitemap_instance
            if sitemap_instance.protocol:
                absolute_url = f"{sitemap_instance.protocol}://{request.get_host()}{relative_url}"
            else:
                absolute_url = request.build_absolute_uri(relative_url)
            xml_lines.append('  <url>')
            xml_lines.append(f'    <loc>{absolute_url}</loc>')
            xml_lines.append(f'    <lastmod>{current_time}</lastmod>')
            xml_lines.append(f'    <changefreq>{sitemap_instance.changefreq}</changefreq>')
            xml_lines.append(f'    <priority>{sitemap_instance.priority}</priority>')
            xml_lines.append('  </url>')
            xml_lines.append('')  # Add empty line between URLs
        except Exception:
            # Skip URLs that can't be reversed
            continue
    
    xml_lines.append('</urlset>')
    
    # Join all lines with newlines
    xml_content = '\n'.join(xml_lines) + '\n'
    
    # Create HttpResponse with properly formatted XML
    xml_bytes = xml_content.encode('utf-8')
    http_response = HttpResponse(xml_bytes, content_type='application/xml; charset=utf-8')
    http_response['Content-Length'] = str(len(xml_bytes))
    http_response['Cache-Control'] = 'no-transform, no-cache'
    # Tell Nginx not to compress this response
    http_response['X-Accel-Buffering'] = 'no'
    # Explicitly disable gzip compression
    http_response['Content-Encoding'] = 'identity'
    
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
