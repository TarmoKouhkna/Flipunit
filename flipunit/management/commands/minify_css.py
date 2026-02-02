"""
Django management command to minify CSS for production.

Reads static/css/style.css and hybrid-style.css, minifies with rcssmin,
writes static/css/style.min.css and hybrid-style.min.css.

Run before collectstatic on deploy (quick_deploy.sh does this).
Run once locally if you use runserver and the template references .min.css.

Usage:
    python manage.py minify_css
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from pathlib import Path

try:
    import rcssmin
    RCSSMIN_AVAILABLE = True
except ImportError:
    RCSSMIN_AVAILABLE = False


class Command(BaseCommand):
    help = 'Minify style.css and hybrid-style.css to .min.css (run before collectstatic)'

    def handle(self, *args, **options):
        if not RCSSMIN_AVAILABLE:
            self.stdout.write(self.style.ERROR('rcssmin is required. Install with: pip install rcssmin'))
            return

        static_dir = Path(settings.STATICFILES_DIRS[0]) if settings.STATICFILES_DIRS else Path(settings.BASE_DIR) / 'static'
        css_dir = static_dir / 'css'

        files = [
            ('style.css', 'style.min.css'),
            ('hybrid-style.css', 'hybrid-style.min.css'),
        ]

        for src_name, dst_name in files:
            src_path = css_dir / src_name
            dst_path = css_dir / dst_name
            if not src_path.exists():
                self.stdout.write(self.style.WARNING(f'Skipping {src_name}: not found at {src_path}'))
                continue
            with open(src_path, 'r', encoding='utf-8') as f:
                css = f.read()
            minified = rcssmin.cssmin(css)
            with open(dst_path, 'w', encoding='utf-8') as f:
                f.write(minified)
            self.stdout.write(self.style.SUCCESS(f'Minified {src_name} -> {dst_name}'))

        self.stdout.write('Done. Run collectstatic to include minified CSS.')
