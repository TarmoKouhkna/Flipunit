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
        return [
            # Main pages
            'home',
            'search',
            'converters:index',
            'image_converter:index',
            'media_converter:index',
            'pdf_tools:index',
            'currency_converter:index',
            'utilities:index',
            'color_picker:index',
            'archive_converter:index',
            'text_converter:index',
            'developer_converter:index',
            
            # Unit converters
            ('converters:tool', 'length'),
            ('converters:tool', 'weight'),
            ('converters:tool', 'temperature'),
            ('converters:tool', 'volume'),
            ('converters:tool', 'area'),
            ('converters:tool', 'speed'),
            ('converters:tool', 'time'),
            ('converters:tool', 'data-storage'),
            ('converters:tool', 'energy'),
            ('converters:tool', 'power'),
            ('converters:tool', 'pressure'),
            ('converters:tool', 'force'),
            ('converters:tool', 'angle'),
            ('converters:tool', 'fuel-consumption'),
            ('converters:tool', 'frequency'),
            ('converters:tool', 'data-transfer'),
            
            # Image converters
            'image_converter:universal',
            ('image_converter:convert', 'jpeg-to-png'),
            ('image_converter:convert', 'png-to-jpg'),
            ('image_converter:convert', 'webp'),
            ('image_converter:convert', 'svg-to-png'),
            'image_converter:resize',
            'image_converter:rotate_flip',
            'image_converter:remove_exif',
            'image_converter:grayscale',
            'image_converter:merge',
            'image_converter:watermark',
            
            # Media converters
            'media_converter:mp4_to_mp3',
            'media_converter:audio_converter',
            'media_converter:audio_splitter',
            'media_converter:audio_merge',
            'media_converter:reduce_noise',
            'media_converter:video_to_gif',
            'media_converter:video_converter',
            'media_converter:video_compressor',
            'media_converter:mute_video',
            
            # PDF Tools
            'pdf_tools:universal',
            'pdf_tools:pdf_merge',
            'pdf_tools:pdf_split',
            'pdf_tools:pdf_to_images',
            'pdf_tools:pdf_to_html',
            'pdf_tools:html_to_pdf',
            'pdf_tools:pdf_to_text',
            'pdf_tools:pdf_compress',
            'pdf_tools:pdf_rotate',
            'pdf_tools:pdf_ocr',
            'pdf_tools:pdf_remove_metadata',
            
            # Utilities
            'utilities:calculator',
            'utilities:qr_code_generator',
            'utilities:timezone_converter',
            'utilities:roman_numeral_converter',
            'utilities:favicon_generator',
            'utilities:timestamp_converter',
            'utilities:text_to_speech',
            'utilities:random_number_generator',
            'utilities:lorem_ipsum_generator',
            'utilities:random_word_generator',
            'utilities:random_name_generator',
            'utilities:word_lottery',
            
            # Color Picker
            'color_picker:picker',
            'color_picker:from_image',
            
            # Currency Converter
            'currency_converter:convert',
            
            # Archive converters
            'archive_converter:rar_to_zip',
            'archive_converter:zip_to_7z',
            'archive_converter:7z_to_zip',
            'archive_converter:targz_to_zip',
            'archive_converter:zip_to_targz',
            'archive_converter:extract_iso',
            'archive_converter:create_zip',
            
            # Text converters
            'text_converter:uppercase_lowercase',
            'text_converter:camelcase_snakecase',
            'text_converter:remove_special',
            'text_converter:remove_duplicates',
            'text_converter:sort_lines',
            'text_converter:json_xml',
            'text_converter:json_yaml',
            'text_converter:html_markdown',
            'text_converter:text_base64',
            'text_converter:word_counter',
            
            # Developer converters
            'developer_converter:minify',
            'developer_converter:unminify',
            'developer_converter:csv_to_json',
            'developer_converter:json_to_csv',
            'developer_converter:sql_formatter',
            'developer_converter:css_scss',
            'developer_converter:regex_tester',
            'developer_converter:jwt_decoder',
            'developer_converter:url_encoder',
            'developer_converter:hash_generator',
            
            # Additional tools
            'isdown:index',
            'youtube_thumbnail:index',
        ]

    def location(self, item):
        if isinstance(item, tuple):
            url_name, *args = item
            return reverse(url_name, args=args)
        return reverse(item)

