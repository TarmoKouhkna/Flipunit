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
        # TEMPORARY: Slim sitemap for GSC quality signal (fewer thin/low-impression URLs).
        # Keep only high-value pages; re-add others once indexing/trust improves.
        # Full list available in git history if needed.
        return [
            'home',
            'media_converter:index',
            'media_converter:audio_converter',
            'media_converter:video_converter',
        ]

    def location(self, item):
        if isinstance(item, tuple):
            url_name, *args = item
            return reverse(url_name, args=args)
        return reverse(item)

