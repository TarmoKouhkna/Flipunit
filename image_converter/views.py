from django.shortcuts import render
from django.http import HttpResponse
import os
from PIL import Image
import io

def index(request):
    """Image converters index page"""
    context = {
        'converters': [
            {'name': 'JPEG to PNG', 'url': 'jpeg-to-png', 'description': 'Convert JPEG images to PNG format'},
            {'name': 'PNG to JPG', 'url': 'png-to-jpg', 'description': 'Convert PNG images to JPG format'},
            {'name': 'WebP Converter', 'url': 'webp', 'description': 'Convert images to/from WebP format'},
            {'name': 'SVG to PNG', 'url': 'svg-to-png', 'description': 'Convert SVG vector images to PNG'},
        ]
    }
    return render(request, 'image_converter/index.html', context)

def convert_image(request, converter_type):
    """Handle image conversion"""
    if request.method != 'POST':
        return render(request, 'image_converter/converter.html', {'converter_type': converter_type})
    
    if 'image' not in request.FILES:
        return render(request, 'image_converter/converter.html', {
            'converter_type': converter_type,
            'error': 'Please upload an image file.'
        })
    
    uploaded_file = request.FILES['image']
    
    # Validate file type
    allowed_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.svg']
    file_ext = os.path.splitext(uploaded_file.name)[1].lower()
    
    if file_ext not in allowed_extensions:
        return render(request, 'image_converter/converter.html', {
            'converter_type': converter_type,
            'error': 'Invalid file type. Please upload JPG, PNG, WebP, or SVG files.'
        })
    
    try:
        # Read image
        image_data = uploaded_file.read()
        
        # Handle SVG separately (requires cairosvg or similar)
        if file_ext == '.svg' and converter_type == 'svg-to-png':
            return render(request, 'image_converter/converter.html', {
                'converter_type': converter_type,
                'error': 'SVG to PNG conversion requires additional libraries. Please use an online SVG to PNG converter.'
            })
        
        # Open image with PIL
        image = Image.open(io.BytesIO(image_data))
        
        # Convert RGBA to RGB for JPG
        if converter_type in ['png-to-jpg', 'webp'] and image.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
            image = background
        
        # Determine output format
        output_format_map = {
            'jpeg-to-png': 'PNG',
            'png-to-jpg': 'JPEG',
            'webp': 'WEBP',
        }
        
        output_format = output_format_map.get(converter_type, 'PNG')
        output_ext = output_format.lower()
        
        # Save to memory
        output = io.BytesIO()
        image.save(output, format=output_format, quality=95)
        output.seek(0)
        
        # Create response
        response = HttpResponse(output.read(), content_type=f'image/{output_ext}')
        response['Content-Disposition'] = f'attachment; filename="converted.{output_ext}"'
        return response
        
    except Exception as e:
        return render(request, 'image_converter/converter.html', {
            'converter_type': converter_type,
            'error': f'Error processing image: {str(e)}'
        })
