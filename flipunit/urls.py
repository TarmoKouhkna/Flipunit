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

sitemaps = {
    'static': StaticViewSitemap,
}

def sitemap(request):
    """Custom sitemap view that removes noindex header for Google Search Console and fixes date format"""
    response = sitemap_view(request, sitemaps)
    # Ensure correct content type
    response['Content-Type'] = 'application/xml; charset=utf-8'
    # Remove X-Robots-Tag header if present (Google needs to index sitemaps)
    if 'X-Robots-Tag' in response:
        del response['X-Robots-Tag']
    
    # Fix lastmod date format for Google Search Console compliance
    # Convert YYYY-MM-DD to YYYY-MM-DDTHH:MM:SS+00:00 format
    import re
    from datetime import datetime, timezone
    
    # Render the response to get the content
    response.render()
    
    # Get the XML content
    xml_content = response.content.decode('utf-8')
    
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
    # Use multiple approaches to ensure complete removal
    # Method 1: Regex patterns
    xml_content = re.sub(r'<\?xml-stylesheet[^>]*\?>\s*', '', xml_content)
    xml_content = re.sub(r'<\?xml-stylesheet.*?\?>\s*', '', xml_content, flags=re.DOTALL)
    
    # Method 2: Line-by-line filtering (more reliable)
    lines = xml_content.split('\n')
    filtered_lines = [line for line in lines if 'xml-stylesheet' not in line.lower()]
    xml_content = '\n'.join(filtered_lines)
    
    # Update the response content
    response.content = xml_content.encode('utf-8')
    response['Content-Length'] = str(len(response.content))
    
    return response

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
