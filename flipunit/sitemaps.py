from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from datetime import datetime, timezone

class StaticViewSitemap(Sitemap):
    priority = 0.8
    changefreq = 'weekly'
    protocol = 'https'  # Force HTTPS URLs in sitemap

    def lastmod(self, obj):
        # Return datetime with UTC timezone
        # Django's sitemap framework will format this, and our post-processing
        # in generate_sitemap.py will ensure it's in full ISO 8601 format
        return datetime.now(timezone.utc)

    def items(self):
        # Section hubs + key media URLs for GSC quality (unique content, not thin).
        return [
            'home',
            'media_converter:index',
            'media_converter:audio_converter',
            'media_converter:video_converter',
            'image_converter:index',
            'pdf_tools:index',
            'converters:index',
            'archive_converter:index',
            'text_converter:index',
        ]

    def location(self, item):
        if isinstance(item, tuple):
            url_name, *args = item
            return reverse(url_name, args=args)
        return reverse(item)

