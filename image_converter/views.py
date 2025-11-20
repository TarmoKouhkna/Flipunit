from django.shortcuts import render
from django.http import HttpResponse
import os
from PIL import Image
import io
try:
    import cairosvg
    CAIROSVG_AVAILABLE = True
except ImportError:
    CAIROSVG_AVAILABLE = False

def index(request):
    """Image converters index page"""
    context = {
        'converters': [
            {'name': 'JPEG to PNG', 'url': 'jpeg-to-png', 'description': 'Convert JPEG images to PNG format'},
            {'name': 'PNG to JPG', 'url': 'png-to-jpg', 'description': 'Convert PNG images to JPG format'},
            {'name': 'WebP Converter', 'url': 'webp', 'description': 'Convert images to/from WebP format'},
            {'name': 'SVG to PNG', 'url': 'svg-to-png', 'description': 'Convert SVG vector images to PNG'},
            {'name': 'Image Resizer', 'url': 'resize', 'description': 'Resize images to custom dimensions'},
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
    
    # Validate file size (max 100MB for images)
    max_size = 100 * 1024 * 1024  # 100MB
    if uploaded_file.size > max_size:
        return render(request, 'image_converter/converter.html', {
            'converter_type': converter_type,
            'error': f'File size exceeds 100MB limit. Your file is {uploaded_file.size / (1024 * 1024):.1f}MB.'
        })
    
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
        
        # Handle SVG to PNG conversion
        if file_ext == '.svg' and converter_type == 'svg-to-png':
            if not CAIROSVG_AVAILABLE:
                return render(request, 'image_converter/converter.html', {
                    'converter_type': converter_type,
                    'error': 'SVG to PNG conversion requires cairosvg library. Please install it: pip install cairosvg'
                })
            
            try:
                # Convert SVG to PNG using cairosvg
                # Default output size is 800x600, but we can make it larger for better quality
                png_data = cairosvg.svg2png(bytestring=image_data, output_width=1920, output_height=1080)
                
                # Create response
                response = HttpResponse(png_data, content_type='image/png')
                response['Content-Disposition'] = 'attachment; filename="converted.png"'
                return response
            except Exception as e:
                return render(request, 'image_converter/converter.html', {
                    'converter_type': converter_type,
                    'error': f'Error converting SVG to PNG: {str(e)}. Make sure Cairo is installed (brew install cairo on macOS).'
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

def resize_image(request):
    """Handle image resizing"""
    if request.method != 'POST':
        return render(request, 'image_converter/resize.html')
    
    if 'image' not in request.FILES:
        return render(request, 'image_converter/resize.html', {
            'error': 'Please upload an image file.'
        })
    
    uploaded_file = request.FILES['image']
    
    # Validate file size (max 100MB for images)
    max_size = 100 * 1024 * 1024  # 100MB
    if uploaded_file.size > max_size:
        return render(request, 'image_converter/resize.html', {
            'error': f'File size exceeds 100MB limit. Your file is {uploaded_file.size / (1024 * 1024):.1f}MB.'
        })
    
    # Validate file type
    allowed_extensions = ['.jpg', '.jpeg', '.png', '.webp']
    file_ext = os.path.splitext(uploaded_file.name)[1].lower()
    
    if file_ext not in allowed_extensions:
        return render(request, 'image_converter/resize.html', {
            'error': 'Invalid file type. Please upload JPG, PNG, or WebP files.'
        })
    
    try:
        # Get resize parameters
        width = request.POST.get('width', '').strip()
        height = request.POST.get('height', '').strip()
        maintain_aspect = request.POST.get('maintain_aspect', 'on') == 'on'
        output_format = request.POST.get('output_format', 'same').strip()
        
        # Validate dimensions
        if not width and not height:
            return render(request, 'image_converter/resize.html', {
                'error': 'Please specify at least width or height.'
            })
        
        width = int(width) if width else None
        height = int(height) if height else None
        
        if width and width <= 0:
            return render(request, 'image_converter/resize.html', {
                'error': 'Width must be a positive number.'
            })
        
        if height and height <= 0:
            return render(request, 'image_converter/resize.html', {
                'error': 'Height must be a positive number.'
            })
        
        if width and width > 10000:
            return render(request, 'image_converter/resize.html', {
                'error': 'Width cannot exceed 10000 pixels.'
            })
        
        if height and height > 10000:
            return render(request, 'image_converter/resize.html', {
                'error': 'Height cannot exceed 10000 pixels.'
            })
        
        # Read and open image
        image_data = uploaded_file.read()
        image = Image.open(io.BytesIO(image_data))
        original_width, original_height = image.size
        
        # Calculate new dimensions
        if maintain_aspect:
            if width and height:
                # Calculate aspect ratio to fit both dimensions
                aspect_ratio = min(width / original_width, height / original_height)
                new_width = int(original_width * aspect_ratio)
                new_height = int(original_height * aspect_ratio)
            elif width:
                aspect_ratio = width / original_width
                new_width = width
                new_height = int(original_height * aspect_ratio)
            elif height:
                aspect_ratio = height / original_height
                new_width = int(original_width * aspect_ratio)
                new_height = height
        else:
            # Use exact dimensions (may distort image)
            new_width = width if width else original_width
            new_height = height if height else original_height
        
        # Resize image
        resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Determine output format
        if output_format == 'same':
            output_format = image.format or 'PNG'
        else:
            output_format = output_format.upper()
        
        # Convert RGBA to RGB for JPEG
        if output_format == 'JPEG' and resized_image.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', resized_image.size, (255, 255, 255))
            if resized_image.mode == 'P':
                resized_image = resized_image.convert('RGBA')
            background.paste(resized_image, mask=resized_image.split()[-1] if resized_image.mode == 'RGBA' else None)
            resized_image = background
        
        # Save to memory
        output = io.BytesIO()
        quality = 95 if output_format in ('JPEG', 'WEBP') else None
        if quality:
            resized_image.save(output, format=output_format, quality=quality)
        else:
            resized_image.save(output, format=output_format)
        output.seek(0)
        
        # Determine file extension
        format_ext_map = {
            'JPEG': 'jpg',
            'PNG': 'png',
            'WEBP': 'webp',
        }
        output_ext = format_ext_map.get(output_format, 'png')
        
        # Create response
        response = HttpResponse(output.read(), content_type=f'image/{output_ext}')
        response['Content-Disposition'] = f'attachment; filename="resized.{output_ext}"'
        return response
        
    except ValueError:
        return render(request, 'image_converter/resize.html', {
            'error': 'Invalid dimensions. Please enter valid numbers.'
        })
    except Exception as e:
        return render(request, 'image_converter/resize.html', {
            'error': f'Error resizing image: {str(e)}'
        })
