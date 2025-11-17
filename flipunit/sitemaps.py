from django.contrib.sitemaps import Sitemap
from django.urls import reverse

class StaticViewSitemap(Sitemap):
    priority = 0.8
    changefreq = 'weekly'

    def items(self):
        return [
            # Main pages
            'home',
            'converters:index',
            'image_converter:index',
            'media_converter:index',
            'utilities:index',
            
            # Unit converters
            ('converters:tool', 'length'),
            ('converters:tool', 'weight'),
            ('converters:tool', 'temperature'),
            ('converters:tool', 'volume'),
            ('converters:tool', 'area'),
            ('converters:tool', 'speed'),
            
            # Image converters
            ('image_converter:convert', 'jpeg-to-png'),
            ('image_converter:convert', 'png-to-jpg'),
            ('image_converter:convert', 'webp-to-png'),
            ('image_converter:convert', 'svg-to-png'),
            
            # Media converters
            'media_converter:youtube_to_mp3',
            
            # Utilities
            'utilities:calculator',
            'utilities:text_tools',
            'utilities:pdf_tools',
            'utilities:color_converter',
            'utilities:qr_code_generator',
            'utilities:timezone_converter',
            'utilities:roman_numeral_converter',
            'utilities:favicon_generator',
        ]

    def location(self, item):
        if isinstance(item, tuple):
            url_name, *args = item
            return reverse(url_name, args=args)
        return reverse(item)

