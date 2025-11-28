from django.shortcuts import render
from django.http import HttpResponse
import os
from PIL import Image, ImageDraw, ImageFont
import io
try:
    import cairosvg
    CAIROSVG_AVAILABLE = True
except ImportError:
    CAIROSVG_AVAILABLE = False

# Check for HEIC support
try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
    HEIC_AVAILABLE = True
except ImportError:
    HEIC_AVAILABLE = False

def index(request):
    """Image conversion and editing index page"""
    context = {
        'converters': [
            {'name': 'Universal Converter', 'url': 'universal', 'url_name': 'universal', 'description': 'Convert images to any format - choose your input and output formats'},
        ],
        'utilities': [
            {'name': 'Image Resizer', 'url': 'resize', 'url_name': 'resize', 'description': 'Resize images to custom dimensions while maintaining aspect ratio'},
            {'name': 'Rotate & Flip', 'url': 'rotate-flip', 'url_name': 'rotate_flip', 'description': 'Rotate images 90°, 180°, 270° or flip horizontally/vertically'},
            {'name': 'Remove EXIF', 'url': 'remove-exif', 'url_name': 'remove_exif', 'description': 'Remove EXIF metadata from images for privacy'},
            {'name': 'Grayscale', 'url': 'grayscale', 'url_name': 'grayscale', 'description': 'Convert images to grayscale (black and white)'},
            {'name': 'Transparent Background', 'url': 'transparent', 'url_name': 'transparent', 'description': 'Remove background and make it transparent'},
            {'name': 'Merge Images', 'url': 'merge', 'url_name': 'merge', 'description': 'Merge multiple images horizontally or vertically'},
            {'name': 'Watermark', 'url': 'watermark', 'url_name': 'watermark', 'description': 'Add text or image watermark to your images'},
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
    allowed_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.svg', '.bmp', '.tiff', '.tif', '.gif', '.ico', '.avif', '.heic', '.heif']
    file_ext = os.path.splitext(uploaded_file.name)[1].lower()
    
    if file_ext not in allowed_extensions:
        return render(request, 'image_converter/converter.html', {
            'converter_type': converter_type,
            'error': 'Invalid file type. Please upload JPG, JPEG, PNG, WebP, SVG, BMP, TIFF, GIF, ICO, AVIF, or HEIC files.'
        })
    
    # Check HEIC support
    if file_ext in ['.heic', '.heif'] and not HEIC_AVAILABLE:
        return render(request, 'image_converter/converter.html', {
            'converter_type': converter_type,
            'error': 'HEIC/HEIF support requires pillow-heif library. Please install it: pip install pillow-heif'
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
        try:
            image = Image.open(io.BytesIO(image_data))
            # Handle animated GIFs - convert to static
            if hasattr(image, 'is_animated') and image.is_animated:
                # Get first frame
                image.seek(0)
                image = image.copy()
        except Exception as e:
            return render(request, 'image_converter/converter.html', {
                'converter_type': converter_type,
                'error': f'Unable to open image file: {str(e)}. Please ensure the file is a valid image.'
            })
        
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
        
        # Get quality setting (for JPEG, WebP, and AVIF)
        quality = 95  # default
        if output_format in ('JPEG', 'WEBP', 'AVIF'):
            try:
                quality_param = request.POST.get('quality', '95')
                quality = int(quality_param)
                # Clamp quality between 1 and 100
                quality = max(1, min(100, quality))
            except (ValueError, TypeError):
                quality = 95
        
        # Save to memory
        output = io.BytesIO()
        save_kwargs = {'format': output_format}
        if output_format in ('JPEG', 'WEBP', 'AVIF'):
            save_kwargs['quality'] = quality
            if output_format == 'JPEG':
                save_kwargs['optimize'] = True
        elif output_format == 'PNG':
            save_kwargs['optimize'] = True
        elif output_format == 'HEIC':
            save_kwargs['quality'] = quality
        
        image.save(output, **save_kwargs)
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

def universal_converter(request):
    """Universal image converter - user chooses output format"""
    if request.method != 'POST':
        return render(request, 'image_converter/universal.html')
    
    if 'image' not in request.FILES:
        return render(request, 'image_converter/universal.html', {
            'error': 'Please upload an image file.'
        })
    
    uploaded_file = request.FILES['image']
    output_format = request.POST.get('output_format', '').strip().upper()
    
    if not output_format:
        return render(request, 'image_converter/universal.html', {
            'error': 'Please select an output format.'
        })
    
    # Validate file size (max 100MB for images)
    max_size = 100 * 1024 * 1024  # 100MB
    if uploaded_file.size > max_size:
        return render(request, 'image_converter/universal.html', {
            'error': f'File size exceeds 100MB limit. Your file is {uploaded_file.size / (1024 * 1024):.1f}MB.'
        })
    
    # Validate file type
    allowed_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.svg', '.bmp', '.tiff', '.tif', '.gif', '.ico', '.avif', '.heic', '.heif']
    file_ext = os.path.splitext(uploaded_file.name)[1].lower()
    
    if file_ext not in allowed_extensions:
        return render(request, 'image_converter/universal.html', {
            'error': 'Invalid file type. Please upload JPG, JPEG, PNG, WebP, SVG, BMP, TIFF, GIF, ICO, AVIF, or HEIC files.'
        })
    
    # Check HEIC support
    if file_ext in ['.heic', '.heif'] and not HEIC_AVAILABLE:
        return render(request, 'image_converter/universal.html', {
            'error': 'HEIC/HEIF support requires pillow-heif library. Please install it: pip install pillow-heif'
        })
    
    # Validate output format
    valid_formats = ['PNG', 'JPEG', 'JPG', 'WEBP', 'BMP', 'TIFF', 'GIF', 'ICO', 'AVIF', 'HEIC']
    if output_format not in valid_formats:
        return render(request, 'image_converter/universal.html', {
            'error': f'Invalid output format: {output_format}. Please select a valid format.'
        })
    
    # Normalize JPEG/JPG
    if output_format == 'JPG':
        output_format = 'JPEG'
    
    # Check HEIC output support
    if output_format == 'HEIC' and not HEIC_AVAILABLE:
        return render(request, 'image_converter/universal.html', {
            'error': 'HEIC output requires pillow-heif library. Please install it: pip install pillow-heif'
        })
    
    try:
        # Read image
        image_data = uploaded_file.read()
        
        # Handle SVG to raster conversion
        if file_ext == '.svg' and output_format != 'SVG':
            if not CAIROSVG_AVAILABLE:
                return render(request, 'image_converter/universal.html', {
                    'error': 'SVG conversion requires cairosvg library. Please install it: pip install cairosvg'
                })
            
            try:
                # Convert SVG to PNG first, then to target format if needed
                png_data = cairosvg.svg2png(bytestring=image_data, output_width=1920, output_height=1080)
                
                if output_format == 'PNG':
                    response = HttpResponse(png_data, content_type='image/png')
                    response['Content-Disposition'] = 'attachment; filename="converted.png"'
                    return response
                else:
                    # Convert PNG to target format
                    image = Image.open(io.BytesIO(png_data))
            except Exception as e:
                return render(request, 'image_converter/universal.html', {
                    'error': f'Error converting SVG: {str(e)}. Make sure Cairo is installed.'
                })
        else:
            # Open image with PIL
            try:
                image = Image.open(io.BytesIO(image_data))
                # Handle animated GIFs - convert to static
                if hasattr(image, 'is_animated') and image.is_animated:
                    image.seek(0)
                    image = image.copy()
            except Exception as e:
                return render(request, 'image_converter/universal.html', {
                    'error': f'Unable to open image file: {str(e)}. Please ensure the file is a valid image.'
                })
        
        # Convert RGBA to RGB for formats that don't support transparency
        if output_format in ('JPEG', 'BMP') and image.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
            image = background
        # Note: HEIC and AVIF support transparency, so we don't convert them
        
        # Get quality setting (for JPEG and WebP)
        quality = 95  # default
        if output_format in ('JPEG', 'WEBP'):
            try:
                quality_param = request.POST.get('quality', '95')
                quality = int(quality_param)
                quality = max(1, min(100, quality))
            except (ValueError, TypeError):
                quality = 95
        
        # Save to memory
        output = io.BytesIO()
        save_kwargs = {'format': output_format}
        if output_format in ('JPEG', 'WEBP'):
            save_kwargs['quality'] = quality
            if output_format == 'JPEG':
                save_kwargs['optimize'] = True
        elif output_format == 'PNG':
            save_kwargs['optimize'] = True
        
        image.save(output, **save_kwargs)
        output.seek(0)
        
        # Determine content type and file extension
        content_type_map = {
            'PNG': 'image/png',
            'JPEG': 'image/jpeg',
            'WEBP': 'image/webp',
            'BMP': 'image/bmp',
            'TIFF': 'image/tiff',
            'GIF': 'image/gif',
            'ICO': 'image/x-icon',
            'AVIF': 'image/avif',
            'HEIC': 'image/heic',
        }
        ext_map = {
            'PNG': 'png',
            'JPEG': 'jpg',
            'WEBP': 'webp',
            'BMP': 'bmp',
            'TIFF': 'tiff',
            'GIF': 'gif',
            'ICO': 'ico',
            'AVIF': 'avif',
            'HEIC': 'heic',
        }
        
        content_type = content_type_map.get(output_format, 'image/png')
        ext = ext_map.get(output_format, 'png')
        
        # Create response
        response = HttpResponse(output.read(), content_type=content_type)
        response['Content-Disposition'] = f'attachment; filename="converted.{ext}"'
        return response
        
    except Exception as e:
        return render(request, 'image_converter/universal.html', {
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
    allowed_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff', '.tif', '.gif', '.ico', '.avif', '.heic', '.heif']
    file_ext = os.path.splitext(uploaded_file.name)[1].lower()
    
    if file_ext not in allowed_extensions:
        return render(request, 'image_converter/resize.html', {
            'error': 'Invalid file type. Please upload JPG, JPEG, PNG, WebP, BMP, TIFF, GIF, ICO, AVIF, or HEIC files.'
        })
    
    # Check HEIC support
    if file_ext in ['.heic', '.heif'] and not HEIC_AVAILABLE:
        return render(request, 'image_converter/resize.html', {
            'error': 'HEIC/HEIF support requires pillow-heif library. Please install it: pip install pillow-heif'
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
        try:
            image = Image.open(io.BytesIO(image_data))
            # Handle animated GIFs - convert to static
            if hasattr(image, 'is_animated') and image.is_animated:
                # Get first frame
                image.seek(0)
                image = image.copy()
        except Exception as e:
            return render(request, 'image_converter/resize.html', {
                'error': f'Unable to open image file: {str(e)}. Please ensure the file is a valid image.'
            })
        
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
        
        # Convert RGBA to RGB for formats that don't support transparency
        if output_format in ('JPEG', 'BMP') and resized_image.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', resized_image.size, (255, 255, 255))
            if resized_image.mode == 'P':
                resized_image = resized_image.convert('RGBA')
            background.paste(resized_image, mask=resized_image.split()[-1] if resized_image.mode == 'RGBA' else None)
            resized_image = background
        
        # Get quality setting (for JPEG, WebP, and AVIF)
        quality = 95  # default
        if output_format in ('JPEG', 'WEBP', 'AVIF'):
            try:
                quality_param = request.POST.get('quality', '95')
                quality = int(quality_param)
                # Clamp quality between 1 and 100
                quality = max(1, min(100, quality))
            except (ValueError, TypeError):
                quality = 95
        
        # Save to memory
        output = io.BytesIO()
        save_kwargs = {'format': output_format}
        if output_format in ('JPEG', 'WEBP', 'AVIF'):
            save_kwargs['quality'] = quality
            if output_format == 'JPEG':
                save_kwargs['optimize'] = True
        elif output_format == 'PNG':
            save_kwargs['optimize'] = True
        elif output_format == 'HEIC':
            save_kwargs['quality'] = quality
        
        resized_image.save(output, **save_kwargs)
        output.seek(0)
        
        # Determine file extension
        format_ext_map = {
            'JPEG': 'jpg',
            'PNG': 'png',
            'WEBP': 'webp',
            'BMP': 'bmp',
            'TIFF': 'tiff',
            'GIF': 'gif',
            'ICO': 'ico',
            'AVIF': 'avif',
            'HEIC': 'heic',
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

def rotate_flip_image(request):
    """Handle image rotation and flipping"""
    if request.method != 'POST':
        return render(request, 'image_converter/rotate_flip.html')
    
    if 'image' not in request.FILES:
        return render(request, 'image_converter/rotate_flip.html', {
            'error': 'Please upload an image file.'
        })
    
    uploaded_file = request.FILES['image']
    action = request.POST.get('action', '').strip()
    
    # Validate file size
    max_size = 100 * 1024 * 1024
    if uploaded_file.size > max_size:
        return render(request, 'image_converter/rotate_flip.html', {
            'error': f'File size exceeds 100MB limit. Your file is {uploaded_file.size / (1024 * 1024):.1f}MB.'
        })
    
    # Validate file type
    allowed_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff', '.tif', '.gif', '.ico', '.avif', '.heic', '.heif']
    file_ext = os.path.splitext(uploaded_file.name)[1].lower()
    
    if file_ext not in allowed_extensions:
        return render(request, 'image_converter/rotate_flip.html', {
            'error': 'Invalid file type. Please upload a valid image file.'
        })
    
    if not action:
        return render(request, 'image_converter/rotate_flip.html', {
            'error': 'Please select an action (rotate or flip).'
        })
    
    try:
        image_data = uploaded_file.read()
        
        # Check HEIC support
        if file_ext in ['.heic', '.heif'] and not HEIC_AVAILABLE:
            return render(request, 'image_converter/rotate_flip.html', {
                'error': 'HEIC/HEIF support requires pillow-heif library.'
            })
        
        image = Image.open(io.BytesIO(image_data))
        
        # Handle animated GIFs
        if hasattr(image, 'is_animated') and image.is_animated:
            image.seek(0)
            image = image.copy()
        
        # Apply transformation
        if action == 'rotate_90':
            image = image.rotate(-90, expand=True)
        elif action == 'rotate_180':
            image = image.rotate(180, expand=True)
        elif action == 'rotate_270':
            image = image.rotate(90, expand=True)
        elif action == 'flip_horizontal':
            image = image.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        elif action == 'flip_vertical':
            image = image.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
        
        # Save to memory
        output = io.BytesIO()
        original_format = image.format or 'PNG'
        save_kwargs = {'format': original_format}
        if original_format in ('JPEG', 'WEBP', 'AVIF'):
            save_kwargs['quality'] = 95
            if original_format == 'JPEG':
                save_kwargs['optimize'] = True
        elif original_format == 'PNG':
            save_kwargs['optimize'] = True
        
        image.save(output, **save_kwargs)
        output.seek(0)
        
        # Determine content type
        content_type_map = {
            'PNG': 'image/png',
            'JPEG': 'image/jpeg',
            'WEBP': 'image/webp',
            'BMP': 'image/bmp',
            'TIFF': 'image/tiff',
            'GIF': 'image/gif',
            'ICO': 'image/x-icon',
            'AVIF': 'image/avif',
            'HEIC': 'image/heic',
        }
        content_type = content_type_map.get(original_format, 'image/png')
        ext = original_format.lower() if original_format else 'png'
        
        response = HttpResponse(output.read(), content_type=content_type)
        response['Content-Disposition'] = f'attachment; filename="edited.{ext}"'
        return response
        
    except Exception as e:
        return render(request, 'image_converter/rotate_flip.html', {
            'error': f'Error processing image: {str(e)}'
        })

def remove_exif(request):
    """Remove EXIF metadata from image"""
    if request.method != 'POST':
        return render(request, 'image_converter/remove_exif.html')
    
    if 'image' not in request.FILES:
        return render(request, 'image_converter/remove_exif.html', {
            'error': 'Please upload an image file.'
        })
    
    uploaded_file = request.FILES['image']
    
    # Validate file size
    max_size = 100 * 1024 * 1024
    if uploaded_file.size > max_size:
        return render(request, 'image_converter/remove_exif.html', {
            'error': f'File size exceeds 100MB limit. Your file is {uploaded_file.size / (1024 * 1024):.1f}MB.'
        })
    
    # Validate file type
    allowed_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff', '.tif', '.gif', '.ico', '.avif', '.heic', '.heif']
    file_ext = os.path.splitext(uploaded_file.name)[1].lower()
    
    if file_ext not in allowed_extensions:
        return render(request, 'image_converter/remove_exif.html', {
            'error': 'Invalid file type. Please upload a valid image file.'
        })
    
    try:
        image_data = uploaded_file.read()
        
        # Check HEIC support
        if file_ext in ['.heic', '.heif'] and not HEIC_AVAILABLE:
            return render(request, 'image_converter/remove_exif.html', {
                'error': 'HEIC/HEIF support requires pillow-heif library.'
            })
        
        image = Image.open(io.BytesIO(image_data))
        
        # Handle animated GIFs
        if hasattr(image, 'is_animated') and image.is_animated:
            image.seek(0)
            image = image.copy()
        
        # Create new image without EXIF data
        data = list(image.getdata())
        image_without_exif = Image.new(image.mode, image.size)
        image_without_exif.putdata(data)
        
        # Save to memory
        output = io.BytesIO()
        original_format = image.format or 'PNG'
        save_kwargs = {'format': original_format}
        if original_format in ('JPEG', 'WEBP', 'AVIF'):
            save_kwargs['quality'] = 95
            if original_format == 'JPEG':
                save_kwargs['optimize'] = True
        elif original_format == 'PNG':
            save_kwargs['optimize'] = True
        
        image_without_exif.save(output, **save_kwargs)
        output.seek(0)
        
        # Determine content type
        content_type_map = {
            'PNG': 'image/png',
            'JPEG': 'image/jpeg',
            'WEBP': 'image/webp',
            'BMP': 'image/bmp',
            'TIFF': 'image/tiff',
            'GIF': 'image/gif',
            'ICO': 'image/x-icon',
            'AVIF': 'image/avif',
            'HEIC': 'image/heic',
        }
        content_type = content_type_map.get(original_format, 'image/png')
        ext = original_format.lower() if original_format else 'png'
        
        response = HttpResponse(output.read(), content_type=content_type)
        response['Content-Disposition'] = f'attachment; filename="no_exif.{ext}"'
        return response
        
    except Exception as e:
        return render(request, 'image_converter/remove_exif.html', {
            'error': f'Error processing image: {str(e)}'
        })

def convert_grayscale(request):
    """Convert image to grayscale"""
    if request.method != 'POST':
        return render(request, 'image_converter/grayscale.html')
    
    if 'image' not in request.FILES:
        return render(request, 'image_converter/grayscale.html', {
            'error': 'Please upload an image file.'
        })
    
    uploaded_file = request.FILES['image']
    
    # Validate file size
    max_size = 100 * 1024 * 1024
    if uploaded_file.size > max_size:
        return render(request, 'image_converter/grayscale.html', {
            'error': f'File size exceeds 100MB limit. Your file is {uploaded_file.size / (1024 * 1024):.1f}MB.'
        })
    
    # Validate file type
    allowed_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff', '.tif', '.gif', '.ico', '.avif', '.heic', '.heif']
    file_ext = os.path.splitext(uploaded_file.name)[1].lower()
    
    if file_ext not in allowed_extensions:
        return render(request, 'image_converter/grayscale.html', {
            'error': 'Invalid file type. Please upload a valid image file.'
        })
    
    try:
        image_data = uploaded_file.read()
        
        # Check HEIC support
        if file_ext in ['.heic', '.heif'] and not HEIC_AVAILABLE:
            return render(request, 'image_converter/grayscale.html', {
                'error': 'HEIC/HEIF support requires pillow-heif library.'
            })
        
        image = Image.open(io.BytesIO(image_data))
        
        # Handle animated GIFs
        if hasattr(image, 'is_animated') and image.is_animated:
            image.seek(0)
            image = image.copy()
        
        # Convert to grayscale
        if image.mode != 'L':
            image = image.convert('L')
        
        # Save to memory
        output = io.BytesIO()
        original_format = image.format or 'PNG'
        save_kwargs = {'format': original_format}
        if original_format in ('JPEG', 'WEBP', 'AVIF'):
            save_kwargs['quality'] = 95
            if original_format == 'JPEG':
                save_kwargs['optimize'] = True
        elif original_format == 'PNG':
            save_kwargs['optimize'] = True
        
        image.save(output, **save_kwargs)
        output.seek(0)
        
        # Determine content type
        content_type_map = {
            'PNG': 'image/png',
            'JPEG': 'image/jpeg',
            'WEBP': 'image/webp',
            'BMP': 'image/bmp',
            'TIFF': 'image/tiff',
            'GIF': 'image/gif',
            'ICO': 'image/x-icon',
            'AVIF': 'image/avif',
            'HEIC': 'image/heic',
        }
        content_type = content_type_map.get(original_format, 'image/png')
        ext = original_format.lower() if original_format else 'png'
        
        response = HttpResponse(output.read(), content_type=content_type)
        response['Content-Disposition'] = f'attachment; filename="grayscale.{ext}"'
        return response
        
    except Exception as e:
        return render(request, 'image_converter/grayscale.html', {
            'error': f'Error processing image: {str(e)}'
        })

def transparent_background(request):
    """Convert image background to transparent"""
    if request.method != 'POST':
        return render(request, 'image_converter/transparent.html')
    
    if 'image' not in request.FILES:
        return render(request, 'image_converter/transparent.html', {
            'error': 'Please upload an image file.'
        })
    
    uploaded_file = request.FILES['image']
    tolerance = int(request.POST.get('tolerance', '10'))
    
    # Validate file size
    max_size = 100 * 1024 * 1024
    if uploaded_file.size > max_size:
        return render(request, 'image_converter/transparent.html', {
            'error': f'File size exceeds 100MB limit. Your file is {uploaded_file.size / (1024 * 1024):.1f}MB.'
        })
    
    # Validate file type
    allowed_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff', '.tif', '.gif', '.ico', '.avif', '.heic', '.heif']
    file_ext = os.path.splitext(uploaded_file.name)[1].lower()
    
    if file_ext not in allowed_extensions:
        return render(request, 'image_converter/transparent.html', {
            'error': 'Invalid file type. Please upload a valid image file.'
        })
    
    try:
        image_data = uploaded_file.read()
        
        # Check HEIC support
        if file_ext in ['.heic', '.heif'] and not HEIC_AVAILABLE:
            return render(request, 'image_converter/transparent.html', {
                'error': 'HEIC/HEIF support requires pillow-heif library.'
            })
        
        image = Image.open(io.BytesIO(image_data))
        
        # Handle animated GIFs
        if hasattr(image, 'is_animated') and image.is_animated:
            image.seek(0)
            image = image.copy()
        
        # Convert to RGBA if not already
        if image.mode != 'RGBA':
            image = image.convert('RGBA')
        
        # Get image data
        data = image.getdata()
        new_data = []
        
        # Get corner color as background color (assuming corners are background)
        corner_colors = [
            data[0],  # top-left
            data[image.width - 1],  # top-right
            data[(image.height - 1) * image.width],  # bottom-left
            data[image.width * image.height - 1]  # bottom-right
        ]
        # Use most common corner color as background
        bg_color = max(set(corner_colors), key=corner_colors.count)
        
        # Make background transparent
        for item in data:
            # Check if pixel is similar to background color
            if len(item) == 4:  # RGBA
                r, g, b, a = item
                bg_r, bg_g, bg_b, bg_a = bg_color if len(bg_color) == 4 else (*bg_color[:3], 255)
                
                # Calculate color distance
                distance = ((r - bg_r) ** 2 + (g - bg_g) ** 2 + (b - bg_b) ** 2) ** 0.5
                
                if distance <= tolerance:
                    new_data.append((r, g, b, 0))  # Make transparent
                else:
                    new_data.append(item)
            else:
                new_data.append(item)
        
        image.putdata(new_data)
        
        # Save to memory as PNG (supports transparency)
        output = io.BytesIO()
        image.save(output, format='PNG', optimize=True)
        output.seek(0)
        
        response = HttpResponse(output.read(), content_type='image/png')
        response['Content-Disposition'] = 'attachment; filename="transparent.png"'
        return response
        
    except Exception as e:
        return render(request, 'image_converter/transparent.html', {
            'error': f'Error processing image: {str(e)}'
        })

def merge_images(request):
    """Merge multiple images horizontally or vertically"""
    if request.method != 'POST':
        return render(request, 'image_converter/merge.html')
    
    if 'images' not in request.FILES:
        return render(request, 'image_converter/merge.html', {
            'error': 'Please upload at least one image file.'
        })
    
    uploaded_files = request.FILES.getlist('images')
    direction = request.POST.get('direction', 'horizontal').strip()
    
    if len(uploaded_files) < 2:
        return render(request, 'image_converter/merge.html', {
            'error': 'Please upload at least 2 images to merge.'
        })
    
    if direction not in ['horizontal', 'vertical']:
        return render(request, 'image_converter/merge.html', {
            'error': 'Invalid merge direction.'
        })
    
    try:
        images = []
        max_size = 100 * 1024 * 1024
        allowed_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff', '.tif', '.gif', '.ico', '.avif', '.heic', '.heif']
        
        for uploaded_file in uploaded_files:
            if uploaded_file.size > max_size:
                return render(request, 'image_converter/merge.html', {
                    'error': f'File {uploaded_file.name} exceeds 100MB limit.'
                })
            
            file_ext = os.path.splitext(uploaded_file.name)[1].lower()
            if file_ext not in allowed_extensions:
                return render(request, 'image_converter/merge.html', {
                    'error': f'Invalid file type: {uploaded_file.name}'
                })
            
            image_data = uploaded_file.read()
            
            if file_ext in ['.heic', '.heif'] and not HEIC_AVAILABLE:
                return render(request, 'image_converter/merge.html', {
                    'error': 'HEIC/HEIF support requires pillow-heif library.'
                })
            
            image = Image.open(io.BytesIO(image_data))
            
            # Handle animated GIFs
            if hasattr(image, 'is_animated') and image.is_animated:
                image.seek(0)
                image = image.copy()
            
            # Convert to RGBA for consistent handling
            if image.mode != 'RGBA':
                image = image.convert('RGBA')
            
            images.append(image)
        
        # Calculate merged image dimensions
        if direction == 'horizontal':
            total_width = sum(img.width for img in images)
            total_height = max(img.height for img in images)
        else:  # vertical
            total_width = max(img.width for img in images)
            total_height = sum(img.height for img in images)
        
        # Create merged image
        merged = Image.new('RGBA', (total_width, total_height), (255, 255, 255, 0))
        
        if direction == 'horizontal':
            x_offset = 0
            for img in images:
                # Center vertically if needed
                y_offset = (total_height - img.height) // 2
                merged.paste(img, (x_offset, y_offset), img)
                x_offset += img.width
        else:  # vertical
            y_offset = 0
            for img in images:
                # Center horizontally if needed
                x_offset = (total_width - img.width) // 2
                merged.paste(img, (x_offset, y_offset), img)
                y_offset += img.height
        
        # Save to memory
        output = io.BytesIO()
        merged.save(output, format='PNG', optimize=True)
        output.seek(0)
        
        response = HttpResponse(output.read(), content_type='image/png')
        response['Content-Disposition'] = 'attachment; filename="merged.png"'
        return response
        
    except Exception as e:
        return render(request, 'image_converter/merge.html', {
            'error': f'Error merging images: {str(e)}'
        })

def watermark_image(request):
    """Add watermark to image (text or image)"""
    if request.method != 'POST':
        return render(request, 'image_converter/watermark.html')
    
    if 'image' not in request.FILES:
        return render(request, 'image_converter/watermark.html', {
            'error': 'Please upload an image file.'
        })
    
    uploaded_file = request.FILES['image']
    watermark_type = request.POST.get('watermark_type', 'text').strip()
    
    # Validate file size
    max_size = 100 * 1024 * 1024
    if uploaded_file.size > max_size:
        return render(request, 'image_converter/watermark.html', {
            'error': f'File size exceeds 100MB limit. Your file is {uploaded_file.size / (1024 * 1024):.1f}MB.'
        })
    
    # Validate file type
    allowed_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff', '.tif', '.gif', '.ico', '.avif', '.heic', '.heif']
    file_ext = os.path.splitext(uploaded_file.name)[1].lower()
    
    if file_ext not in allowed_extensions:
        return render(request, 'image_converter/watermark.html', {
            'error': 'Invalid file type. Please upload a valid image file.'
        })
    
    try:
        image_data = uploaded_file.read()
        
        # Check HEIC support
        if file_ext in ['.heic', '.heif'] and not HEIC_AVAILABLE:
            return render(request, 'image_converter/watermark.html', {
                'error': 'HEIC/HEIF support requires pillow-heif library.'
            })
        
        image = Image.open(io.BytesIO(image_data))
        
        # Handle animated GIFs
        if hasattr(image, 'is_animated') and image.is_animated:
            image.seek(0)
            image = image.copy()
        
        # Convert to RGBA for watermarking
        if image.mode != 'RGBA':
            image = image.convert('RGBA')
        
        # Create watermark layer
        watermark_layer = Image.new('RGBA', image.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(watermark_layer)
        
        if watermark_type == 'text':
            text = request.POST.get('watermark_text', '').strip()
            if not text:
                return render(request, 'image_converter/watermark.html', {
                    'error': 'Please enter watermark text.'
                })
            
            position = request.POST.get('position', 'bottom-right').strip()
            opacity = int(request.POST.get('opacity', '50'))
            font_size = int(request.POST.get('font_size', '36'))
            color = request.POST.get('color', '#FFFFFF').strip()
            
            # Parse color
            if color.startswith('#'):
                color = tuple(int(color[i:i+2], 16) for i in (1, 3, 5)) + (int(255 * opacity / 100),)
            else:
                color = (255, 255, 255, int(255 * opacity / 100))
            
            # Try to load font, fallback to default
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
            except:
                try:
                    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
                except:
                    font = ImageFont.load_default()
            
            # Get text dimensions
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            # Calculate position
            if position == 'top-left':
                x, y = 10, 10
            elif position == 'top-right':
                x, y = image.width - text_width - 10, 10
            elif position == 'bottom-left':
                x, y = 10, image.height - text_height - 10
            elif position == 'bottom-right':
                x, y = image.width - text_width - 10, image.height - text_height - 10
            else:  # center
                x, y = (image.width - text_width) // 2, (image.height - text_height) // 2
            
            # Draw text with outline for visibility
            outline_color = (0, 0, 0, int(255 * opacity / 100))
            for adj in range(-2, 3):
                for adj2 in range(-2, 3):
                    draw.text((x + adj, y + adj2), text, font=font, fill=outline_color)
            draw.text((x, y), text, font=font, fill=color)
            
        else:  # image watermark
            if 'watermark_image' not in request.FILES:
                return render(request, 'image_converter/watermark.html', {
                    'error': 'Please upload a watermark image.'
                })
            
            watermark_file = request.FILES['watermark_image']
            watermark_data = watermark_file.read()
            watermark_img = Image.open(io.BytesIO(watermark_data))
            
            if watermark_img.mode != 'RGBA':
                watermark_img = watermark_img.convert('RGBA')
            
            position = request.POST.get('position', 'bottom-right').strip()
            opacity = int(request.POST.get('opacity', '50'))
            scale = int(request.POST.get('scale', '20'))  # percentage of image size
            
            # Resize watermark
            watermark_size = (int(image.width * scale / 100), int(image.height * scale / 100))
            watermark_img = watermark_img.resize(watermark_size, Image.Resampling.LANCZOS)
            
            # Apply opacity
            alpha = watermark_img.split()[3]
            alpha = alpha.point(lambda p: int(p * opacity / 100))
            watermark_img.putalpha(alpha)
            
            # Calculate position
            if position == 'top-left':
                x, y = 10, 10
            elif position == 'top-right':
                x, y = image.width - watermark_img.width - 10, 10
            elif position == 'bottom-left':
                x, y = 10, image.height - watermark_img.height - 10
            elif position == 'bottom-right':
                x, y = image.width - watermark_img.width - 10, image.height - watermark_img.height - 10
            else:  # center
                x, y = (image.width - watermark_img.width) // 2, (image.height - watermark_img.height) // 2
            
            watermark_layer.paste(watermark_img, (x, y), watermark_img)
        
        # Composite watermark onto image
        image = Image.alpha_composite(image, watermark_layer)
        
        # Save to memory
        output = io.BytesIO()
        original_format = uploaded_file.name.split('.')[-1].upper()
        if original_format == 'JPG':
            original_format = 'JPEG'
        
        # Convert RGBA to RGB for formats that don't support transparency
        if original_format in ('JPEG', 'BMP') and image.mode == 'RGBA':
            background = Image.new('RGB', image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[3])
            image = background
        
        save_kwargs = {'format': original_format if original_format in ['PNG', 'JPEG', 'WEBP', 'BMP', 'TIFF', 'GIF'] else 'PNG'}
        if save_kwargs['format'] in ('JPEG', 'WEBP', 'AVIF'):
            save_kwargs['quality'] = 95
            if save_kwargs['format'] == 'JPEG':
                save_kwargs['optimize'] = True
        elif save_kwargs['format'] == 'PNG':
            save_kwargs['optimize'] = True
        
        image.save(output, **save_kwargs)
        output.seek(0)
        
        # Determine content type
        content_type_map = {
            'PNG': 'image/png',
            'JPEG': 'image/jpeg',
            'WEBP': 'image/webp',
            'BMP': 'image/bmp',
            'TIFF': 'image/tiff',
            'GIF': 'image/gif',
        }
        content_type = content_type_map.get(save_kwargs['format'], 'image/png')
        ext = save_kwargs['format'].lower() if save_kwargs['format'] != 'JPEG' else 'jpg'
        
        response = HttpResponse(output.read(), content_type=content_type)
        response['Content-Disposition'] = f'attachment; filename="watermarked.{ext}"'
        return response
        
    except Exception as e:
        return render(request, 'image_converter/watermark.html', {
            'error': f'Error processing image: {str(e)}'
        })
