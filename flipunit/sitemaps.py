from django.contrib.sitemaps import Sitemap
from django.urls import reverse

class StaticViewSitemap(Sitemap):
    priority = 0.8
    changefreq = 'weekly'

    def items(self):
        return [
            'home',
            'converters:index',
            'image_converter:index',
            'media_converter:index',
            'utilities:index',
        ]

    def location(self, item):
        return reverse(item)

