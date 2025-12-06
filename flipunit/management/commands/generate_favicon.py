"""
Django management command to generate favicon files from logo.svg.

Usage:
    python manage.py generate_favicon
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from pathlib import Path
from PIL import Image
import io

try:
    import cairosvg
    CAIROSVG_AVAILABLE = True
except ImportError:
    CAIROSVG_AVAILABLE = False


class Command(BaseCommand):
    help = 'Generate favicon.ico and favicon.png from logo.svg'

    def handle(self, *args, **options):
        if not CAIROSVG_AVAILABLE:
            self.stdout.write(self.style.ERROR('cairosvg is required. Install with: pip install cairosvg'))
            return

        static_dir = Path(settings.STATICFILES_DIRS[0]) if settings.STATICFILES_DIRS else Path(settings.STATIC_ROOT)
        images_dir = static_dir / 'images'
        logo_svg_path = images_dir / 'logo.svg'
        
        if not logo_svg_path.exists():
            self.stdout.write(self.style.ERROR(f'logo.svg not found at {logo_svg_path}'))
            return

        self.stdout.write(f'Reading SVG from {logo_svg_path}...')
        
        # Read SVG file
        with open(logo_svg_path, 'rb') as f:
            svg_data = f.read()

        # Generate favicon.png (32x32)
        self.stdout.write('Generating favicon.png (32x32)...')
        png_data = cairosvg.svg2png(bytestring=svg_data, output_width=32, output_height=32)
        favicon_png_path = images_dir / 'favicon.png'
        with open(favicon_png_path, 'wb') as f:
            f.write(png_data)
        self.stdout.write(self.style.SUCCESS(f'Created {favicon_png_path}'))

        # Generate favicon.ico (multi-size: 16x16, 32x32)
        self.stdout.write('Generating favicon.ico (16x16, 32x32)...')
        
        # Create 16x16 and 32x32 versions
        sizes = [16, 32]
        images = []
        
        for size in sizes:
            png_data = cairosvg.svg2png(bytestring=svg_data, output_width=size, output_height=size)
            img = Image.open(io.BytesIO(png_data))
            # Convert RGBA to RGB if needed for ICO
            if img.mode == 'RGBA':
                # Create white background
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[-1])
                img = background
            images.append(img)

        # Save as ICO with multiple sizes
        favicon_ico_path = images_dir / 'favicon.ico'
        images[0].save(favicon_ico_path, format='ICO', sizes=[(16, 16), (32, 32)])
        self.stdout.write(self.style.SUCCESS(f'Created {favicon_ico_path}'))

        # Also create apple-touch-icon (180x180)
        self.stdout.write('Generating apple-touch-icon.png (180x180)...')
        apple_png_data = cairosvg.svg2png(bytestring=svg_data, output_width=180, output_height=180)
        apple_touch_path = images_dir / 'apple-touch-icon.png'
        with open(apple_touch_path, 'wb') as f:
            f.write(apple_png_data)
        self.stdout.write(self.style.SUCCESS(f'Created {apple_touch_path}'))

        self.stdout.write(self.style.SUCCESS('\n✓ All favicon files generated successfully!'))
