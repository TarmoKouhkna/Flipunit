"""
Django management command to generate a static sitemap.xml file.

Usage:
    python manage.py generate_sitemap [--output sitemap.xml]
"""
from django.core.management.base import BaseCommand
from django.contrib.sitemaps import views as sitemap_views
from django.http import HttpRequest
from django.conf import settings
from flipunit.sitemaps import StaticViewSitemap
import os


class Command(BaseCommand):
    help = 'Generate a static sitemap.xml file from Django sitemap configuration'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            type=str,
            default='sitemap.xml',
            help='Output file path (default: sitemap.xml)',
        )
        parser.add_argument(
            '--site-url',
            type=str,
            default=None,
            help='Base URL for the site (default: from SITE_URL setting)',
        )

    def handle(self, *args, **options):
        output_path = options['output']
        site_url = options['site_url'] or getattr(settings, 'SITE_URL', 'https://flipunit.eu')
        
        # Ensure site_url doesn't end with /
        site_url = site_url.rstrip('/')
        
        self.stdout.write(f'Generating sitemap for: {site_url}')
        self.stdout.write(f'Output file: {output_path}')
        
        # Create a mock request with HTTPS
        request = HttpRequest()
        domain = site_url.replace('https://', '').replace('http://', '').split('/')[0]
        request.META['SERVER_NAME'] = domain
        request.META['HTTP_HOST'] = domain
        request.META['SERVER_PORT'] = '443' if site_url.startswith('https') else '80'
        request.META['wsgi.url_scheme'] = 'https' if site_url.startswith('https') else 'http'
        # Force HTTPS for sitemap generation
        if not site_url.startswith('https'):
            self.stdout.write(self.style.WARNING('⚠️  Warning: Site URL is not HTTPS. Forcing HTTPS in sitemap.'))
            site_url = site_url.replace('http://', 'https://')
            request.META['wsgi.url_scheme'] = 'https'
            request.META['SERVER_PORT'] = '443'
        
        # Get sitemap
        sitemaps = {
            'static': StaticViewSitemap,
        }
        
        # Generate sitemap response
        response = sitemap_views.sitemap(request, sitemaps)
        
        # Ensure correct content type
        response['Content-Type'] = 'application/xml; charset=utf-8'
        
        # Render the response to get the content
        response.render()
        
        # Get the XML content
        try:
            xml_content = response.content.decode('utf-8')
        except UnicodeDecodeError as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Failed to decode response content: {e}')
            )
            raise

        # Fix lastmod date format for Google Search Console compliance
        # Convert YYYY-MM-DD to YYYY-MM-DDTHH:MM:SS+00:00 format
        import re
        from datetime import datetime, timezone

        # Find all lastmod tags with date-only format and add time + timezone
        def fix_date_format(match):
            date_str = match.group(1)
            # Add current UTC time and UTC timezone
            current_time = datetime.now(timezone.utc).strftime('T%H:%M:%S+00:00')
            return f'<lastmod>{date_str}{current_time}</lastmod>'

        # Replace date-only lastmod tags with full ISO 8601 format
        xml_content = re.sub(r'<lastmod>(\d{4}-\d{2}-\d{2})</lastmod>', fix_date_format, xml_content)

        # Write to file
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(xml_content)
        except (IOError, OSError, PermissionError) as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Failed to write sitemap file: {e}')
            )
            raise
        
        # Set permissions (Unix-like systems)
        if os.name != 'nt':  # Not Windows
            try:
                os.chmod(output_path, 0o644)
            except (OSError, PermissionError) as e:
                self.stdout.write(
                    self.style.WARNING(f'⚠️  Warning: Failed to set file permissions: {e}')
                )
        
        try:
            file_size = os.path.getsize(output_path)
        except OSError as e:
            self.stdout.write(
                self.style.WARNING(f'⚠️  Warning: Failed to get file size: {e}')
            )
            file_size = 0
        self.stdout.write(
            self.style.SUCCESS(
                f'✅ Successfully generated sitemap.xml ({file_size} bytes)'
            )
        )
        self.stdout.write(f'   File: {os.path.abspath(output_path)}')
        
        # Verify it's valid XML
        if xml_content.strip().startswith('<?xml'):
            self.stdout.write(self.style.SUCCESS('   ✓ Valid XML format'))
        else:
            self.stdout.write(self.style.WARNING('   ⚠️  Warning: File does not start with <?xml'))
        
        # Verify HTTPS URLs are used
        if 'http://' in xml_content and 'https://' not in xml_content:
            self.stdout.write(self.style.WARNING('   ⚠️  Warning: Sitemap contains HTTP URLs instead of HTTPS'))
        elif 'https://' in xml_content:
            http_count = xml_content.count('http://')
            https_count = xml_content.count('https://')
            if http_count > 0:
                self.stdout.write(self.style.WARNING(f'   ⚠️  Warning: Found {http_count} HTTP URL(s) and {https_count} HTTPS URL(s)'))
            else:
                self.stdout.write(self.style.SUCCESS(f'   ✓ All URLs use HTTPS ({https_count} URLs found)'))


