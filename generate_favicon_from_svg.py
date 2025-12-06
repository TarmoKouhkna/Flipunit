#!/usr/bin/env python3
"""
Standalone script to generate favicon files from logo.svg.

Usage:
    python3 generate_favicon_from_svg.py
"""
from pathlib import Path
from PIL import Image
import io
import sys

try:
    import cairosvg
    CAIROSVG_AVAILABLE = True
except ImportError:
    print('ERROR: cairosvg is required. Install with: pip install cairosvg')
    sys.exit(1)


def main():
    # Get the script directory
    script_dir = Path(__file__).parent
    images_dir = script_dir / 'static' / 'images'
    logo_svg_path = images_dir / 'logo.svg'
    
    if not logo_svg_path.exists():
        print(f'ERROR: logo.svg not found at {logo_svg_path}')
        sys.exit(1)

    print(f'Reading SVG from {logo_svg_path}...')
    
    # Read SVG file
    with open(logo_svg_path, 'rb') as f:
        svg_data = f.read()

    # Generate favicon.png (32x32)
    print('Generating favicon.png (32x32)...')
    png_data = cairosvg.svg2png(bytestring=svg_data, output_width=32, output_height=32)
    favicon_png_path = images_dir / 'favicon.png'
    with open(favicon_png_path, 'wb') as f:
        f.write(png_data)
    print(f'✓ Created {favicon_png_path}')

    # Generate favicon.ico (multi-size: 16x16, 32x32)
    print('Generating favicon.ico (16x16, 32x32)...')
    
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
    print(f'✓ Created {favicon_ico_path}')

    # Also create apple-touch-icon (180x180)
    print('Generating apple-touch-icon.png (180x180)...')
    apple_png_data = cairosvg.svg2png(bytestring=svg_data, output_width=180, output_height=180)
    apple_touch_path = images_dir / 'apple-touch-icon.png'
    with open(apple_touch_path, 'wb') as f:
        f.write(apple_png_data)
    print(f'✓ Created {apple_touch_path}')

    print('\n✓ All favicon files generated successfully!')


if __name__ == '__main__':
    main()
