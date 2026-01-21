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
from django.views.decorators.cache import cache_page
from . import views
from .sitemaps import StaticViewSitemap
# Note: Monkey-patch is applied in flipunit/__init__.py to ensure it runs early

sitemaps = {
    'static': StaticViewSitemap,
}

SITEMAP_CACHE_SECONDS = 3600

def sitemap(request):
    """Custom sitemap view that generates properly formatted XML with explicit formatting"""
    from django.http import HttpResponse
    from datetime import datetime, timezone
    import xml.sax.saxutils as saxutils
    
    try:
        # Generate sitemap XML manually with proper formatting
        current_time = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S+00:00')
        
        # Build XML as a list of lines to preserve formatting
        sitemap_instance = StaticViewSitemap()
        xml_lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">'
        ]
        
        # Get all URLs from the sitemap
        items = sitemap_instance.items()
        
        # Format each URL entry with proper indentation
        for item in items:
            try:
                relative_url = sitemap_instance.location(item)
                # Make URL absolute using the protocol from sitemap_instance
                if hasattr(sitemap_instance, 'protocol') and sitemap_instance.protocol:
                    absolute_url = f"{sitemap_instance.protocol}://{request.get_host()}{relative_url}"
                else:
                    absolute_url = request.build_absolute_uri(relative_url)
                
                # Escape XML special characters in URLs
                absolute_url = saxutils.escape(absolute_url)
                
                # Add URL entry with proper indentation
                xml_lines.append('  <url>')
                xml_lines.append(f'    <loc>{absolute_url}</loc>')
                xml_lines.append(f'    <lastmod>{current_time}</lastmod>')
                xml_lines.append(f'    <changefreq>{sitemap_instance.changefreq}</changefreq>')
                xml_lines.append(f'    <priority>{sitemap_instance.priority}</priority>')
                xml_lines.append('  </url>')
            except Exception:
                # Skip URLs that can't be reversed
                continue
        
        xml_lines.append('</urlset>')
        
        # Join all lines with newlines - this ensures proper formatting
        xml_content = '\n'.join(xml_lines) + '\n'
        
        # Create HttpResponse with properly formatted XML
        xml_bytes = xml_content.encode('utf-8')
        http_response = HttpResponse(xml_bytes, content_type='application/xml; charset=utf-8')
        http_response['Content-Length'] = str(len(xml_bytes))
        
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
        
        return http_response
    except Exception as e:
        # Return a minimal valid sitemap on any error to prevent 500 errors
        error_xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"></urlset>\n'
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
        
        return http_response

urlpatterns = [
    path('admin/', admin.site.urls),
    path('favicon.ico', views.favicon_view, name='favicon'),
    path('BingSiteAuth.xml', views.bing_site_auth_view, name='bing_site_auth'),
    path('', views.home, name='home'),
    path('search/', views.search, name='search'),
    path('privacy/', views.privacy_policy, name='privacy'),
    path('terms/', views.terms_of_service, name='terms'),
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
    path('ai-chat/', include('ai_chat.urls')),
    path('sitemap.xml', cache_page(SITEMAP_CACHE_SECONDS)(sitemap), name='django.contrib.sitemaps.views.sitemap'),
    path('robots.txt', TemplateView.as_view(template_name='robots.txt', content_type='text/plain')),
    path('health/', views.health_check, name='health_check'),
]

if settings.DEBUG:
    # Serve media files in development
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # Note: Static files are automatically served by Django's runserver in DEBUG mode
    # from STATICFILES_DIRS and app static directories. WhiteNoise handles production.
