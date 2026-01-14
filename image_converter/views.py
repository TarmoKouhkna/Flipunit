from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, JsonResponse, FileResponse
from django.conf import settings
import os
import uuid
import logging
from PIL import Image, ImageDraw, ImageFont
import io
import zipfile
import tempfile
import json
import base64
from typing import Tuple, Optional

try:
    import cairosvg
    CAIROSVG_AVAILABLE = True
except ImportError:
    CAIROSVG_AVAILABLE = False

# Check for HEIC support
try:
    from pillow_heif import register_heif_opener  # type: ignore
    register_heif_opener()
    HEIC_AVAILABLE = True
except ImportError:
    HEIC_AVAILABLE = False

# Constants
ALLOWED_IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.webp', '.svg', '.bmp', '.tiff', '.tif', '.gif', '.ico', '.avif', '.heic', '.heif']
MAX_IMAGE_SIZE = 100 * 1024 * 1024  # 100MB

# Font paths - configurable
FONT_PATHS = [
    "/System/Library/Fonts/Helvetica.ttc",  # macOS
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Linux
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",  # Alternative Linux
]


def _load_font(font_size: int) -> ImageFont.FreeTypeFont:
    """
    Load a TrueType font with fallback to default.
    
    Args:
        font_size: Size of the font to load
        
    Returns:
        ImageFont object (FreeTypeFont or default)
    """
    for font_path in FONT_PATHS:
        try:
            return ImageFont.truetype(font_path, font_size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


def _validate_image_file(uploaded_file, request, template_name: str, allowed_extensions: Optional[list] = None, allow_svg: bool = False):
    """
    Validate uploaded image file.
    
    Args:
        uploaded_file: Django uploaded file object
        request: Django request object
        template_name: Template name for error rendering
        allowed_extensions: List of allowed extensions (defaults to ALLOWED_IMAGE_EXTENSIONS)
        allow_svg: Whether SVG files are allowed (default: False, as most functions can't handle SVG)
        
    Returns:
        Tuple of (is_valid, error_response_or_none, file_ext)
    """
    if allowed_extensions is None:
        allowed_extensions = ALLOWED_IMAGE_EXTENSIONS
    
    # Check file size
    if uploaded_file.size > MAX_IMAGE_SIZE:
        return (False, render(request, template_name, {
            'error': f'File size exceeds {MAX_IMAGE_SIZE / (1024 * 1024):.0f}MB limit. Your file is {uploaded_file.size / (1024 * 1024):.1f}MB.'
        }), None)
    
    # Check file extension
    file_ext = os.path.splitext(uploaded_file.name)[1].lower()
    if file_ext not in allowed_extensions:
        ext_list = ', '.join([ext.upper().lstrip('.') for ext in allowed_extensions])
        return (False, render(request, template_name, {
            'error': f'Invalid file type. Please upload {ext_list} files.'
        }), None)
    
    # Check SVG support (SVG files need special handling and can't be used with PIL directly)
    if file_ext == '.svg' and not allow_svg:
        return (False, render(request, template_name, {
            'error': 'SVG files are not supported for this operation. Please convert SVG to PNG first using the Universal Converter.'
        }), None)
    
    # Check HEIC support
    if file_ext in ['.heic', '.heif'] and not HEIC_AVAILABLE:
        return (False, render(request, template_name, {
            'error': 'HEIC/HEIF support requires pillow-heif library. Please install it: pip install pillow-heif'
        }), None)
    
    return (True, None, file_ext)

def index(request):
    """Image conversion and editing index page"""
    context = {
        'converters': [
            {'name': 'Universal Converter', 'url': 'universal', 'url_name': 'universal', 'description': 'Convert images to any format - choose your input and output formats'},
            {'name': 'JPEG to PNG', 'url': 'jpeg-to-png', 'url_name': 'convert', 'description': 'Convert JPEG images to PNG format'},
            {'name': 'PNG to JPG', 'url': 'png-to-jpg', 'url_name': 'convert', 'description': 'Convert PNG images to JPG format'},
            {'name': 'WebP Converter', 'url': 'webp', 'url_name': 'convert', 'description': 'Convert images to or from WebP format'},
            {'name': 'SVG to PNG', 'url': 'svg-to-png', 'url_name': 'convert', 'description': 'Convert SVG vector images to PNG raster format'},
        ],
        'utilities': [
            {'name': 'Image Resizer', 'url': 'resize', 'url_name': 'resize', 'description': 'Resize images to custom dimensions while maintaining aspect ratio'},
            {'name': 'Rotate & Flip', 'url': 'rotate-flip', 'url_name': 'rotate_flip', 'description': 'Rotate images 90°, 180°, 270° or flip horizontally/vertically'},
            {'name': 'Remove EXIF', 'url': 'remove-exif', 'url_name': 'remove_exif', 'description': 'Remove EXIF metadata from images for privacy'},
            {'name': 'Grayscale', 'url': 'grayscale', 'url_name': 'grayscale', 'description': 'Convert images to grayscale (black and white)'},
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
    
    # Validate image file (allow SVG for converter as it handles SVG to PNG conversion)
    is_valid, error_response, file_ext = _validate_image_file(
        uploaded_file, request, 'image_converter/converter.html', allow_svg=True
    )
    if not is_valid:
        # Add converter_type to error context
        if hasattr(error_response, 'context_data'):
            error_response.context_data['converter_type'] = converter_type
        elif isinstance(error_response, HttpResponse):
            # If it's already a rendered response, we need to re-render with converter_type
            return render(request, 'image_converter/converter.html', {
                'converter_type': converter_type,
                'error': error_response.context_data.get('error', 'Validation failed') if hasattr(error_response, 'context_data') else 'Validation failed'
            })
        return error_response
    
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

def _convert_single_image(uploaded_file, output_format, quality=95):
    """Helper function to convert a single image"""
    file_ext = os.path.splitext(uploaded_file.name)[1].lower()
    image_data = uploaded_file.read()
    
    # Handle SVG to raster conversion
    if file_ext == '.svg' and output_format != 'SVG':
        if not CAIROSVG_AVAILABLE:
            raise ValueError('SVG conversion requires cairosvg library. Please install it: pip install cairosvg')
        
        # Convert SVG to PNG first, then to target format if needed
        png_data = cairosvg.svg2png(bytestring=image_data, output_width=1920, output_height=1080)
        
        if output_format == 'PNG':
            return png_data, 'png'
        else:
            # Convert PNG to target format
            image = Image.open(io.BytesIO(png_data))
    else:
        # Open image with PIL
        image = Image.open(io.BytesIO(image_data))
        # Handle animated GIFs - convert to static
        if hasattr(image, 'is_animated') and image.is_animated:
            image.seek(0)
            image = image.copy()
    
    # Convert RGBA to RGB for formats that don't support transparency
    if output_format in ('JPEG', 'BMP') and image.mode in ('RGBA', 'LA', 'P'):
        background = Image.new('RGB', image.size, (255, 255, 255))
        if image.mode == 'P':
            image = image.convert('RGBA')
        background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
        image = background
    
    # Save to memory
    output = io.BytesIO()
    save_kwargs = {'format': output_format}
    if output_format in ('JPEG', 'WEBP', 'AVIF'):
        save_kwargs['quality'] = quality
        if output_format == 'JPEG':
            save_kwargs['optimize'] = True
    elif output_format == 'PNG':
        save_kwargs['optimize'] = True
    
    image.save(output, **save_kwargs)
    output.seek(0)
    
    # Determine file extension
    ext_map = {
        'PNG': 'png',
        'JPEG': 'jpg',
        'WEBP': 'webp',
        'BMP': 'bmp',
        'TIFF': 'tiff',
        'GIF': 'gif',
        'ICO': 'ico',
        'AVIF': 'avif',
    }
    ext = ext_map.get(output_format, 'png')
    
    return output.read(), ext


def universal_converter(request):
    """Universal image converter - user chooses output format"""
    if request.method != 'POST':
        return render(request, 'image_converter/universal.html')
    
    # Check for batch mode (multiple files)
    uploaded_files = request.FILES.getlist('image')
    is_batch = len(uploaded_files) > 1
    
    if not uploaded_files:
        return render(request, 'image_converter/universal.html', {
            'error': 'Please upload at least one image file.'
        })
    
    # Limit batch size to 15 files
    if len(uploaded_files) > 15:
        return render(request, 'image_converter/universal.html', {
            'error': 'Maximum 15 files allowed for batch conversion. Please select fewer files.'
        })
    
    output_format = request.POST.get('output_format', '').strip().upper()
    
    if not output_format:
        return render(request, 'image_converter/universal.html', {
            'error': 'Please select an output format.'
        })
    
    # Only validate first file for single file mode
    # In batch mode, validate all files in the loop
    if not is_batch:
        uploaded_file = uploaded_files[0]
        # Validate image file
        is_valid, error_response, file_ext = _validate_image_file(
            uploaded_file, request, 'image_converter/universal.html', allow_svg=True
        )
        if not is_valid:
            return error_response
    
    # Validate output format
    # Note: HEIC is removed from valid formats as PIL doesn't support saving to HEIC
    valid_formats = ['PNG', 'JPEG', 'JPG', 'WEBP', 'BMP', 'TIFF', 'GIF', 'ICO', 'AVIF']
    if output_format not in valid_formats:
        return render(request, 'image_converter/universal.html', {
            'error': f'Invalid output format: {output_format}. Please select a valid format.'
        })
    
    # Normalize JPEG/JPG
    if output_format == 'JPG':
        output_format = 'JPEG'
    
    # Check HEIC output support
    # Note: pillow-heif only supports reading HEIC, not writing. PIL doesn't support saving HEIC format.
    if output_format == 'HEIC':
        return render(request, 'image_converter/universal.html', {
            'error': 'HEIC output format is not supported. PIL/Pillow does not support saving to HEIC format. Please choose a different output format like PNG, JPEG, or WebP.'
        })
    
    # Get quality setting
    quality = 95
    if output_format in ('JPEG', 'WEBP', 'AVIF', 'HEIC'):
        try:
            quality_param = request.POST.get('quality', '95')
            quality = int(quality_param)
            quality = max(1, min(100, quality))
        except (ValueError, TypeError):
            quality = 95
    
    # Check if this is an AJAX request
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.headers.get('Accept') == 'application/json'
    logger = logging.getLogger(__name__)
    
    try:
        # Single file conversion - use hybrid approach: sync for small files, async for large files
        if not is_batch:
            uploaded_file = uploaded_files[0]
            
            # Threshold: Use async for files > 5MB (larger files benefit from async, small files are faster sync)
            ASYNC_THRESHOLD = 5 * 1024 * 1024  # 5MB
            use_async = uploaded_file.size > ASYNC_THRESHOLD
            
            if not use_async:
                # Small file - process synchronously for speed
                converted_data, ext = _convert_single_image(uploaded_file, output_format, quality)
                
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
                }
                content_type = content_type_map.get(output_format, 'image/png')
                
                # Generate filename
                base_name = os.path.splitext(uploaded_file.name)[0]
                base_name = ''.join(c for c in base_name if c.isalnum() or c in (' ', '-', '_', '.')).strip()
                base_name = base_name.replace(' ', '_')
                safe_filename = f'{base_name}.{ext}' if base_name else f'converted.{ext}'
                
                # Return response (sync path - fast for small files)
                if is_ajax:
                    # Encode file as base64 to send as JSON (legacy format for sync path)
                    file_base64 = base64.b64encode(converted_data).decode('utf-8')
                    response_data = {
                        'file': file_base64,
                        'filename': safe_filename,
                        'content_type': content_type
                    }
                    response = HttpResponse(
                        json.dumps(response_data),
                        content_type='application/json'
                    )
                    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
                    response['Pragma'] = 'no-cache'
                    response['Expires'] = '0'
                    return response
                else:
                    # Legacy format - direct file download
                    response = HttpResponse(converted_data, content_type=content_type)
                    response['Content-Disposition'] = f'attachment; filename="{safe_filename}"'
                    return response
            
            # Large file - use async pattern
            # Save file to shared media directory (accessible by both web and worker containers)
            media_dir = os.path.join(settings.MEDIA_ROOT, 'image_conversions')
            os.makedirs(media_dir, exist_ok=True)
            
            # Create unique filename
            file_ext = os.path.splitext(uploaded_file.name)[1]
            unique_id = uuid.uuid4().hex[:8]
            temp_filename = f'temp_{unique_id}{file_ext}'
            input_path = os.path.join(media_dir, temp_filename)
            
            # Save uploaded file
            with open(input_path, 'wb') as f:
                for chunk in uploaded_file.chunks():
                    f.write(chunk)
            
            # Get user IP for quota tracking
            user_ip = request.META.get('REMOTE_ADDR')
            if not user_ip:
                user_ip = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip()
            
            # Import here to avoid circular imports
            from .models import ImageJob
            from .tasks import image_converter_task
            
            # Create ImageJob
            job = ImageJob.objects.create(
                operation='image_converter',
                file_key=input_path,
                file_size=uploaded_file.size,
                output_format=output_format.lower(),
                user_ip=user_ip,
                status='pending'
            )
            
            # Enqueue conversion task
            logger.info(f'Enqueuing async image conversion task for job {job.job_id} (file size: {uploaded_file.size} bytes)')
            image_converter_task.delay(str(job.job_id), input_path, output_format, uploaded_file.name, quality)
            
            logger.info(f'Returning job_id response for job {job.job_id}, is_ajax={is_ajax}')
            if is_ajax:
                return JsonResponse({'job_id': str(job.job_id), 'status': 'pending'})
            else:
                return render(request, 'image_converter/universal.html', {
                    'job_id': str(job.job_id),
                    'status': 'pending',
                })
        
        # Batch conversion - create ZIP file
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            successful = 0
            failed = []
            
            for idx, uploaded_file in enumerate(uploaded_files):
                try:
                    # Read file data into memory first - Django file objects can only be read once
                    # Reset file pointer if possible
                    if hasattr(uploaded_file, 'seek'):
                        uploaded_file.seek(0)
                    
                    # Read file data before any validation or processing
                    file_data = uploaded_file.read()
                    file_size = len(file_data)
                    
                    # Basic validation (file size and extension)
                    if file_size > MAX_IMAGE_SIZE:
                        failed.append(f"{uploaded_file.name}: File too large")
                        continue
                    
                    file_ext = os.path.splitext(uploaded_file.name)[1].lower()
                    if file_ext not in ALLOWED_IMAGE_EXTENSIONS:
                        failed.append(f"{uploaded_file.name}: Invalid file type")
                        continue
                    
                    if file_ext == '.svg' and not CAIROSVG_AVAILABLE:
                        failed.append(f"{uploaded_file.name}: SVG requires cairosvg")
                        continue
                    
                    if file_ext in ['.heic', '.heif'] and not HEIC_AVAILABLE:
                        failed.append(f"{uploaded_file.name}: HEIC requires pillow-heif")
                        continue
                    
                    # Create a BytesIO object from the file data for processing
                    file_obj = io.BytesIO(file_data)
                    file_obj.name = uploaded_file.name  # Preserve filename for helper function
                    
                    # Convert image
                    converted_data, ext = _convert_single_image(file_obj, output_format, quality)
                    
                    # Generate filename
                    base_name = os.path.splitext(uploaded_file.name)[0]
                    # Sanitize filename
                    base_name = ''.join(c for c in base_name if c.isalnum() or c in (' ', '-', '_', '.')).strip()
                    base_name = base_name.replace(' ', '_')
                    filename = f"{base_name}.{ext}"
                    
                    # Add to ZIP
                    zip_file.writestr(filename, converted_data)
                    successful += 1
                    
                except Exception as e:
                    failed.append(f"{uploaded_file.name}: {str(e)}")
                    continue
            
            if successful == 0:
                error_msg = "All files failed to convert. "
                if failed:
                    error_msg += "Errors: " + "; ".join(failed[:5])
                # Check if this is an AJAX request
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
                    return HttpResponse(
                        json.dumps({'error': error_msg}),
                        content_type='application/json',
                        status=400
                    )
                return render(request, 'image_converter/universal.html', {
                    'error': error_msg
                })
        
        zip_buffer.seek(0)
        
        # Create response with ZIP file
        response = HttpResponse(zip_buffer.read(), content_type='application/zip')
        response['Content-Disposition'] = 'attachment; filename="converted_images.zip"'
        return response
        
    except Exception as e:
        error_msg = f'Error processing image: {str(e)}'
        # Check if this is an AJAX request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
            return HttpResponse(
                json.dumps({'error': error_msg}),
                content_type='application/json',
                status=500
            )
        return render(request, 'image_converter/universal.html', {
            'error': error_msg
        })

def resize_image(request):
    """Handle image resizing"""
    if request.method != 'POST':
        return render(request, 'image_converter/resize.html')
    
    if 'image' not in request.FILES:
        return render(request, 'image_converter/resize.html', {
            'error': 'Please upload an image file.'
        })
    
    # Check for batch mode (multiple files)
    uploaded_files = request.FILES.getlist('image')
    file_count = len(uploaded_files)
    is_batch = file_count > 1
    
    if not uploaded_files:
        return render(request, 'image_converter/resize.html', {
            'error': 'Please upload at least one image file.'
        })
    
    # Limit batch size to 15 files
    if file_count > 15:
        return render(request, 'image_converter/resize.html', {
            'error': 'Maximum 15 files allowed for batch conversion. Please select fewer files.'
        })
    
    # Only validate first file for single file mode
    # In batch mode, validate all files in the loop
    if not is_batch:
        uploaded_file = uploaded_files[0]
        # Validate image file
        is_valid, error_response, file_ext = _validate_image_file(
            uploaded_file, request, 'image_converter/resize.html'
        )
        if not is_valid:
            return error_response
    
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
        
        # Helper function to resize a single image
        def _resize_single_image(uploaded_file, width, height, maintain_aspect, output_format, quality_param):
            """Resize a single image and return the processed image data and extension"""
            image_data = uploaded_file.read()
            try:
                image = Image.open(io.BytesIO(image_data))
                # Handle animated GIFs - convert to static
                if hasattr(image, 'is_animated') and image.is_animated:
                    # Get first frame
                    image.seek(0)
                    image = image.copy()
            except Exception as e:
                raise ValueError(f'Unable to open image file: {str(e)}. Please ensure the file is a valid image.')
            
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
                final_output_format = image.format or 'PNG'
            else:
                final_output_format = output_format.upper()
            
            # Block HEIC output (PIL doesn't support saving to HEIC)
            if final_output_format == 'HEIC':
                raise ValueError('HEIC output format is not supported. PIL/Pillow does not support saving to HEIC format. Please choose a different output format like PNG, JPEG, or WebP.')
            
            # Convert RGBA to RGB for formats that don't support transparency
            if final_output_format in ('JPEG', 'BMP') and resized_image.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', resized_image.size, (255, 255, 255))
                if resized_image.mode == 'P':
                    resized_image = resized_image.convert('RGBA')
                background.paste(resized_image, mask=resized_image.split()[-1] if resized_image.mode == 'RGBA' else None)
                resized_image = background
            
            # Get quality setting (for JPEG, WebP, and AVIF)
            quality = 95  # default
            if final_output_format in ('JPEG', 'WEBP', 'AVIF'):
                try:
                    quality = int(quality_param)
                    # Clamp quality between 1 and 100
                    quality = max(1, min(100, quality))
                except (ValueError, TypeError):
                    quality = 95
            
            # Save to memory
            output = io.BytesIO()
            save_kwargs = {'format': final_output_format}
            if final_output_format in ('JPEG', 'WEBP', 'AVIF'):
                save_kwargs['quality'] = quality
                if final_output_format == 'JPEG':
                    save_kwargs['optimize'] = True
            elif final_output_format == 'PNG':
                save_kwargs['optimize'] = True
            
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
            }
            output_ext = format_ext_map.get(final_output_format, 'png')
            
            return output.read(), output_ext, final_output_format
        
        # Get quality parameter from request
        quality_param = request.POST.get('quality', '95')
        
        # Single file conversion
        if not is_batch:
            uploaded_file = uploaded_files[0]  # Ensure uploaded_file is defined
            try:
                resized_data, output_ext, final_format = _resize_single_image(
                    uploaded_file, width, height, maintain_aspect, output_format, quality_param
                )
                
                # Create response
                response = HttpResponse(resized_data, content_type=f'image/{output_ext}')
                response['Content-Disposition'] = f'attachment; filename="resized.{output_ext}"'
                return response
            except ValueError as e:
                return render(request, 'image_converter/resize.html', {
                    'error': str(e)
                })
        
        # Batch conversion - create ZIP file (file_count > 1)
        # Ensure we're definitely in batch mode
        if file_count <= 1:
            # Fallback to single file if somehow we got here with one file
            uploaded_file = uploaded_files[0]
            try:
                resized_data, output_ext, final_format = _resize_single_image(
                    uploaded_file, width, height, maintain_aspect, output_format, quality_param
                )
                response = HttpResponse(resized_data, content_type=f'image/{output_ext}')
                response['Content-Disposition'] = f'attachment; filename="resized.{output_ext}"'
                return response
            except ValueError as e:
                return render(request, 'image_converter/resize.html', {
                    'error': str(e)
                })
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            successful = 0
            failed = []
            
            for idx, uploaded_file in enumerate(uploaded_files):
                try:
                    # Read file data into memory first - Django file objects can only be read once
                    # Reset file pointer if possible
                    if hasattr(uploaded_file, 'seek'):
                        uploaded_file.seek(0)
                    
                    # Read file data before any validation or processing
                    file_data = uploaded_file.read()
                    file_size = len(file_data)
                    
                    # Basic validation (file size and extension)
                    if file_size > MAX_IMAGE_SIZE:
                        failed.append(f"{uploaded_file.name}: File too large")
                        continue
                    
                    file_ext = os.path.splitext(uploaded_file.name)[1].lower()
                    if file_ext not in ALLOWED_IMAGE_EXTENSIONS:
                        failed.append(f"{uploaded_file.name}: Invalid file type")
                        continue
                    
                    if file_ext == '.svg' and not CAIROSVG_AVAILABLE:
                        failed.append(f"{uploaded_file.name}: SVG requires cairosvg")
                        continue
                    
                    if file_ext in ['.heic', '.heif'] and not HEIC_AVAILABLE:
                        failed.append(f"{uploaded_file.name}: HEIC requires pillow-heif")
                        continue
                    
                    # Create a BytesIO object from the file data for processing
                    file_obj = io.BytesIO(file_data)
                    file_obj.name = uploaded_file.name  # Preserve filename for helper function
                    
                    # Resize image
                    resized_data, output_ext, final_format = _resize_single_image(
                        file_obj, width, height, maintain_aspect, output_format, quality_param
                    )
                    
                    # Generate filename
                    base_name = os.path.splitext(uploaded_file.name)[0]
                    # Sanitize filename
                    base_name = ''.join(c for c in base_name if c.isalnum() or c in (' ', '-', '_', '.')).strip()
                    base_name = base_name.replace(' ', '_')
                    filename = f"{base_name}_resized.{output_ext}"
                    
                    # Add to ZIP
                    zip_file.writestr(filename, resized_data)
                    successful += 1
                    
                except Exception as e:
                    failed.append(f"{uploaded_file.name}: {str(e)}")
                    continue
            
            if successful == 0:
                error_msg = "All files failed to resize. "
                if failed:
                    error_msg += "Errors: " + "; ".join(failed[:5])
                return render(request, 'image_converter/resize.html', {
                    'error': error_msg
                })
        
        zip_buffer.seek(0)
        zip_data = zip_buffer.read()
        
        # Ensure we have ZIP data before returning
        if len(zip_data) == 0:
            return render(request, 'image_converter/resize.html', {
                'error': 'Failed to create ZIP file. Please try again.'
            })
        
        # Create response with ZIP file
        response = HttpResponse(zip_data, content_type='application/zip')
        response['Content-Disposition'] = 'attachment; filename="resized_images.zip"'
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
    
    if not action:
        return render(request, 'image_converter/rotate_flip.html', {
            'error': 'Please select an action (rotate or flip).'
        })
    
    # Validate image file
    is_valid, error_response, file_ext = _validate_image_file(
        uploaded_file, request, 'image_converter/rotate_flip.html'
    )
    if not is_valid:
        return error_response
    
    try:
        image_data = uploaded_file.read()
        
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
    
    # Validate image file
    is_valid, error_response, file_ext = _validate_image_file(
        uploaded_file, request, 'image_converter/remove_exif.html'
    )
    if not is_valid:
        return error_response
    
    try:
        image_data = uploaded_file.read()
        
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
    
    # Check for batch mode (multiple files)
    uploaded_files = request.FILES.getlist('image')
    is_batch = len(uploaded_files) > 1
    
    if not uploaded_files:
        return render(request, 'image_converter/grayscale.html', {
            'error': 'Please upload at least one image file.'
        })
    
    # Limit batch size to 15 files
    if len(uploaded_files) > 15:
        return render(request, 'image_converter/grayscale.html', {
            'error': 'Maximum 15 files allowed for batch conversion. Please select fewer files.'
        })
    
    # Only validate first file for single file mode
    # In batch mode, validate all files in the loop
    if not is_batch:
        uploaded_file = uploaded_files[0]
        # Validate image file
        is_valid, error_response, file_ext = _validate_image_file(
            uploaded_file, request, 'image_converter/grayscale.html'
        )
        if not is_valid:
            return error_response
    
    try:
        # Helper function to convert a single image to grayscale
        def _convert_single_to_grayscale(uploaded_file):
            """Convert a single image to grayscale and return the processed image data and extension"""
            image_data = uploaded_file.read()
            
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
            
            # Determine content type and extension
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
            
            return output.read(), content_type, ext
        
        # Single file conversion
        if not is_batch:
            try:
                grayscale_data, content_type, ext = _convert_single_to_grayscale(uploaded_file)
                
                response = HttpResponse(grayscale_data, content_type=content_type)
                response['Content-Disposition'] = f'attachment; filename="grayscale.{ext}"'
                return response
            except Exception as e:
                return render(request, 'image_converter/grayscale.html', {
                    'error': f'Error processing image: {str(e)}'
                })
        
        # Batch conversion - create ZIP file
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            successful = 0
            failed = []
            
            for idx, uploaded_file in enumerate(uploaded_files):
                try:
                    # Read file data into memory first - Django file objects can only be read once
                    # Reset file pointer if possible
                    if hasattr(uploaded_file, 'seek'):
                        uploaded_file.seek(0)
                    
                    # Read file data before any validation or processing
                    file_data = uploaded_file.read()
                    file_size = len(file_data)
                    
                    # Basic validation (file size and extension)
                    if file_size > MAX_IMAGE_SIZE:
                        failed.append(f"{uploaded_file.name}: File too large")
                        continue
                    
                    file_ext = os.path.splitext(uploaded_file.name)[1].lower()
                    if file_ext not in ALLOWED_IMAGE_EXTENSIONS:
                        failed.append(f"{uploaded_file.name}: Invalid file type")
                        continue
                    
                    if file_ext == '.svg' and not CAIROSVG_AVAILABLE:
                        failed.append(f"{uploaded_file.name}: SVG requires cairosvg")
                        continue
                    
                    if file_ext in ['.heic', '.heif'] and not HEIC_AVAILABLE:
                        failed.append(f"{uploaded_file.name}: HEIC requires pillow-heif")
                        continue
                    
                    # Create a BytesIO object from the file data for processing
                    file_obj = io.BytesIO(file_data)
                    file_obj.name = uploaded_file.name  # Preserve filename for helper function
                    
                    # Convert to grayscale
                    grayscale_data, content_type, ext = _convert_single_to_grayscale(file_obj)
                    
                    # Generate filename
                    base_name = os.path.splitext(uploaded_file.name)[0]
                    # Sanitize filename
                    base_name = ''.join(c for c in base_name if c.isalnum() or c in (' ', '-', '_', '.')).strip()
                    base_name = base_name.replace(' ', '_')
                    filename = f"{base_name}_grayscale.{ext}"
                    
                    # Add to ZIP
                    zip_file.writestr(filename, grayscale_data)
                    successful += 1
                    
                except Exception as e:
                    failed.append(f"{uploaded_file.name}: {str(e)}")
                    continue
            
            if successful == 0:
                error_msg = "All files failed to convert. "
                if failed:
                    error_msg += "Errors: " + "; ".join(failed[:5])
                return render(request, 'image_converter/grayscale.html', {
                    'error': error_msg
                })
        
        zip_buffer.seek(0)
        
        # Create response with ZIP file
        response = HttpResponse(zip_buffer.read(), content_type='application/zip')
        response['Content-Disposition'] = 'attachment; filename="grayscale_images.zip"'
        return response
        
    except Exception as e:
        return render(request, 'image_converter/grayscale.html', {
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
        
        for uploaded_file in uploaded_files:
            # Validate each image file
            is_valid, error_response, file_ext = _validate_image_file(
                uploaded_file, request, 'image_converter/merge.html'
            )
            if not is_valid:
                return error_response
            
            image_data = uploaded_file.read()
            
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
    
    # Validate image file
    is_valid, error_response, file_ext = _validate_image_file(
        uploaded_file, request, 'image_converter/watermark.html'
    )
    if not is_valid:
        return error_response
    
    try:
        image_data = uploaded_file.read()
        
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
            
            # Load font with fallback
            font = _load_font(font_size)
            
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


def job_status(request, job_id):
    """Get job status as JSON"""
    from .models import ImageJob
    job = get_object_or_404(ImageJob, job_id=job_id)
    
    response_data = {
        'job_id': str(job.job_id),
        'status': job.status,
        'operation': job.operation,
        'created_at': job.created_at.isoformat(),
        'completed_at': job.completed_at.isoformat() if job.completed_at else None,
        'progress': job.progress,
    }
    
    if job.status == 'completed' and job.output_file_key:
        response_data['output_filename'] = os.path.basename(job.output_file_key)
    
    if job.status == 'failed':
        response_data['error_message'] = job.error_message
    
    return JsonResponse(response_data)


def download_result(request, job_id):
    """Download job result file"""
    from .models import ImageJob
    import re
    job = get_object_or_404(ImageJob, job_id=job_id)
    
    if job.status != 'completed':
        return HttpResponse('Job not completed yet', status=400)
    
    if not job.output_file_key or not os.path.exists(job.output_file_key):
        return HttpResponse('Output file not found', status=404)
    
    # Generate safe filename from original file name and output format
    original_name = os.path.basename(job.file_key)
    base_name = os.path.splitext(original_name)[0]
    # Remove temp_ prefix if present
    if base_name.startswith('temp_'):
        base_name = base_name[5:]
    base_name = re.sub(r'[^\w\s.-]', '', base_name).strip()
    base_name = re.sub(r'[-\s]+', '-', base_name)
    
    output_ext = job.output_format or os.path.splitext(job.output_file_key)[1].lstrip('.')
    safe_filename = f'{base_name}.{output_ext}'
    
    # Determine content type
    content_type_map = {
        'png': 'image/png',
        'jpeg': 'image/jpeg',
        'jpg': 'image/jpeg',
        'webp': 'image/webp',
        'bmp': 'image/bmp',
        'tiff': 'image/tiff',
        'gif': 'image/gif',
        'ico': 'image/x-icon',
        'avif': 'image/avif',
    }
    content_type = content_type_map.get(output_ext.lower(), 'application/octet-stream')
    
    return FileResponse(
        open(job.output_file_key, 'rb'),
        content_type=content_type,
        as_attachment=True,
        filename=safe_filename
    )
