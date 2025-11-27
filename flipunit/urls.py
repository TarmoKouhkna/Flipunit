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
    """Custom sitemap view that removes noindex header for Google Search Console"""
    response = sitemap_view(request, sitemaps)
    # Ensure correct content type
    response['Content-Type'] = 'application/xml; charset=utf-8'
    # Remove X-Robots-Tag header if present (Google needs to index sitemaps)
    if 'X-Robots-Tag' in response:
        del response['X-Robots-Tag']
    return response

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('converters/', include('converters.urls')),
    path('image-converter/', include('image_converter.urls')),
    path('media-converter/', include('media_converter.urls')),
    path('pdf-tools/', include('pdf_tools.urls')),
    path('currency/', include('currency_converter.urls')),
    path('utilities/', include('utilities.urls')),
    path('youtube-analyzer/', include('youtube_analyzer.urls')),
    path('color-picker/', include('color_picker.urls')),
    path('sitemap.xml', sitemap, name='django.contrib.sitemaps.views.sitemap'),
    path('robots.txt', TemplateView.as_view(template_name='robots.txt', content_type='text/plain')),
]

if settings.DEBUG:
    # Serve media files in development
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # Note: Static files are automatically served by Django's runserver in DEBUG mode
    # from STATICFILES_DIRS and app static directories. WhiteNoise handles production.
