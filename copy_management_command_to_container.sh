#!/bin/bash
# Script to copy management command files into the Docker container
# Run this on your VPS

set -e

echo "📦 Copying management command files into Docker container..."

# Create directory structure
docker exec flipunit-web mkdir -p /app/flipunit/management/commands

# Create __init__.py files
docker exec flipunit-web sh -c "echo '# Django management package' > /app/flipunit/management/__init__.py"
docker exec flipunit-web sh -c "echo '# Django management commands package' > /app/flipunit/management/commands/__init__.py"

# Create the generate_sitemap.py file
cat << 'EOF' | docker exec -i flipunit-web sh -c "cat > /app/flipunit/management/commands/generate_sitemap.py"
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
        
        # Create a mock request
        request = HttpRequest()
        request.META['SERVER_NAME'] = site_url.replace('https://', '').replace('http://', '').split('/')[0]
        request.META['SERVER_PORT'] = '443' if site_url.startswith('https') else '80'
        request.META['wsgi.url_scheme'] = 'https' if site_url.startswith('https') else 'http'
        
        # Get sitemap
        sitemaps = {
            'static': StaticViewSitemap,
        }
        
        # Generate sitemap response
        response = sitemap_views.sitemap(request, sitemaps)
        
        # Ensure correct content type
        response['Content-Type'] = 'application/xml; charset=utf-8'
        
        # Get the XML content
        xml_content = response.content.decode('utf-8')
        
        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(xml_content)
        
        # Set permissions (Unix-like systems)
        if os.name != 'nt':  # Not Windows
            os.chmod(output_path, 0o644)
        
        file_size = os.path.getsize(output_path)
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
EOF

# Update settings.py to include 'flipunit' in INSTALLED_APPS if not already there
if ! docker exec flipunit-web grep -q "'flipunit'," /app/flipunit/settings.py; then
    echo "Updating settings.py to include 'flipunit' in INSTALLED_APPS..."
    docker exec flipunit-web sed -i "/INSTALLED_APPS = \[/a\    'flipunit',  # Main project app (needed for management commands)" /app/flipunit/settings.py
fi

echo "✅ Management command files copied successfully!"
echo ""
echo "Now you can run:"
echo "  docker exec flipunit-web python manage.py generate_sitemap --output /app/sitemap.xml --site-url https://flipunit.eu"
echo "  docker cp flipunit-web:/app/sitemap.xml /opt/flipunit/sitemap.xml"


