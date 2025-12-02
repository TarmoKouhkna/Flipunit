from django.shortcuts import render
from django.contrib import messages
from django.http import HttpResponse
import os
import tempfile
import re
import shutil
import subprocess
import json
import base64
import zipfile
import io

def index(request):
    """Media converters index page"""
    context = {
        'converters': [
            {
                'name': 'Audio Converter',
                'url': 'media_converter:audio_converter',
                'description': 'Convert between MP3, WAV, OGG, FLAC, AAC, AIFF, and M4A formats',
            },
            {
                'name': 'Video Converter',
                'url': 'media_converter:video_converter',
                'description': 'Convert between MP4, AVI, MOV, MKV, WebM, and 3GP formats',
            },
        ],
        'audio_utilities': [
            {
                'name': 'Audio Splitter',
                'url': 'media_converter:audio_splitter',
                'description': 'Split audio files into segments by time',
            },
            {
                'name': 'Audio Merge',
                'url': 'media_converter:audio_merge',
                'description': 'Merge multiple audio files into one',
            },
            {
                'name': 'Reduce Audio Noise',
                'url': 'media_converter:reduce_noise',
                'description': 'Reduce background noise from audio files',
            },
        ],
        'video_utilities': [
            {
                'name': 'MP4 to MP3',
                'url': 'media_converter:mp4_to_mp3',
                'description': 'Extract audio from MP4 video files',
            },
            {
                'name': 'Video to GIF',
                'url': 'media_converter:video_to_gif',
                'description': 'Convert video clips to animated GIFs',
            },
            {
                'name': 'Video Compressor',
                'url': 'media_converter:video_compressor',
                'description': 'Compress video files to reduce file size',
            },
            {
                'name': 'Mute Video Audio',
                'url': 'media_converter:mute_video',
                'description': 'Remove audio track from video files',
            },
        ]
    }
    return render(request, 'media_converter/index.html', context)

def _check_ffmpeg():
    """Check if FFmpeg is available"""
    ffmpeg_path = shutil.which('ffmpeg') or '/usr/local/bin/ffmpeg'
    ffprobe_path = shutil.which('ffprobe') or '/usr/local/bin/ffprobe'
    
    if not os.path.exists(ffmpeg_path):
        return None, None, 'FFmpeg not found. Please install FFmpeg on your system.'
    
    ffmpeg_dir = os.path.dirname(ffmpeg_path)
    original_path = os.environ.get('PATH', '')
    if ffmpeg_dir not in original_path:
        os.environ['PATH'] = f"{ffmpeg_dir}:{original_path}"
    
    return ffmpeg_path, ffprobe_path, None

def mp4_to_mp3(request):
    """Extract audio from MP4 video files"""
    if request.method != 'POST':
        return render(request, 'media_converter/mp4_to_mp3.html')
    
    if 'video_file' not in request.FILES:
        return render(request, 'media_converter/mp4_to_mp3.html', {
            'error': 'Please upload a video file.'
        })
    
    uploaded_file = request.FILES['video_file']
    
    # Validate file size (max 700MB for videos)
    max_size = 700 * 1024 * 1024  # 700MB
    if uploaded_file.size > max_size:
        return render(request, 'media_converter/mp4_to_mp3.html', {
            'error': f'File size exceeds 700MB limit. Your file is {uploaded_file.size / (1024 * 1024):.1f}MB.'
        })
    
    # Validate file type
    allowed_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.wmv', '.3gp']
    file_ext = os.path.splitext(uploaded_file.name)[1].lower()
    
    if file_ext not in allowed_extensions:
        return render(request, 'media_converter/mp4_to_mp3.html', {
            'error': 'Invalid file type. Please upload MP4, AVI, MOV, MKV, WebM, FLV, WMV, or 3GP files.'
        })
    
    # Check FFmpeg
    ffmpeg_path, ffprobe_path, error = _check_ffmpeg()
    if error:
        return render(request, 'media_converter/mp4_to_mp3.html', {'error': error})
    
    temp_dir = None
    try:
        # Create temporary directory
        temp_dir = tempfile.mkdtemp()
        input_path = os.path.join(temp_dir, f'input{file_ext}')
        output_path = os.path.join(temp_dir, 'output.mp3')
        
        # Save uploaded file
        with open(input_path, 'wb') as f:
            for chunk in uploaded_file.chunks():
                f.write(chunk)
        
        # Extract audio using FFmpeg
        cmd = [
            ffmpeg_path,
            '-i', input_path,
            '-vn',  # No video
            '-acodec', 'libmp3lame',
            '-ab', '192k',  # Audio bitrate
            '-ar', '44100',  # Sample rate
            '-y',  # Overwrite output file
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if not os.path.exists(output_path):
            # Clean up before returning error
            if temp_dir:
                try:
                    shutil.rmtree(temp_dir)
                except (OSError, PermissionError):
                    pass
            return render(request, 'media_converter/mp4_to_mp3.html', {
                'error': f'Conversion failed: {result.stderr}'
            })
        
        # Read output file
        with open(output_path, 'rb') as f:
            file_content = f.read()
        
        # Clean up
        try:
            shutil.rmtree(temp_dir)
        except (OSError, PermissionError):
            pass
        
        # Create response
        # Note: We don't set Content-Disposition here to prevent browser auto-download
        # JavaScript will handle the download programmatically to keep page responsive
        safe_filename = os.path.splitext(uploaded_file.name)[0] + '.mp3'
        safe_filename = re.sub(r'[^\w\s-]', '', safe_filename).strip()
        safe_filename = re.sub(r'[-\s]+', '-', safe_filename)
        
        response = HttpResponse(file_content, content_type='audio/mpeg')
        response['Content-Length'] = len(file_content)
        response['X-Filename'] = safe_filename
        return response
        
    except Exception as e:
        if temp_dir:
            try:
                shutil.rmtree(temp_dir)
            except (OSError, PermissionError) as cleanup_error:
                # Log cleanup errors but don't fail the request
                print(f"Warning: Failed to cleanup temp directory: {cleanup_error}")
                pass
        return render(request, 'media_converter/mp4_to_mp3.html', {
            'error': f'Error processing file: {str(e)}'
        })

def _convert_single_audio(uploaded_file, output_format, ffmpeg_path, logger):
    """Helper function to convert a single audio file. Returns (file_content, output_ext, safe_filename) or raises exception."""
    # Validate file size (max 700MB for audio files)
    max_size = 700 * 1024 * 1024  # 700MB
    if uploaded_file.size > max_size:
        raise ValueError(f'File size exceeds 700MB limit. Your file is {uploaded_file.size / (1024 * 1024):.1f}MB.')
    
    # Validate file type
    allowed_extensions = ['.mp3', '.wav', '.ogg', '.flac', '.aac', '.m4a', '.aiff', '.aif']
    file_ext = os.path.splitext(uploaded_file.name)[1].lower()
    
    if file_ext not in allowed_extensions:
        raise ValueError('Invalid file type. Please upload MP3, WAV, OGG, FLAC, AAC, M4A, or AIFF files.')
    
    if output_format not in ['mp3', 'wav', 'ogg', 'flac', 'aac', 'm4a', 'aiff']:
        raise ValueError('Invalid output format selected.')
    
    temp_dir = None
    try:
        # Create temporary directory
        temp_dir = tempfile.mkdtemp()
        input_path = os.path.join(temp_dir, f'input{file_ext}')
        # Determine output extension
        if output_format == 'aac':
            output_ext = 'm4a'  # AAC uses m4a container
        elif output_format == 'aiff':
            output_ext = 'aiff'
        else:
            output_ext = output_format
        output_path = os.path.join(temp_dir, f'output.{output_ext}')
        
        # Save uploaded file
        with open(input_path, 'wb') as f:
            for chunk in uploaded_file.chunks():
                f.write(chunk)
        
        # Convert using FFmpeg
        codec_map = {
            'mp3': 'libmp3lame',
            'wav': 'pcm_s16le',
            'ogg': 'libvorbis',
            'flac': 'flac',
            'aac': 'aac',
            'm4a': 'aac',  # M4A uses AAC codec
            'aiff': 'pcm_s16be',  # AIFF uses big-endian PCM
        }
        
        # Build FFmpeg command
        cmd = [
            ffmpeg_path,
            '-i', input_path,
            '-vn',  # No video
            '-map', '0:a',  # Map only audio stream
            '-c:a', codec_map[output_format],  # ALWAYS re-encode with specified codec
            '-ar', '44100',  # Set sample rate to ensure re-encoding
            '-ac', '2',  # Set to stereo
        ]
        
        # Format-specific settings
        if output_format == 'wav':
            cmd.extend(['-sample_fmt', 's16'])
            cmd.extend(['-f', 'wav'])
        elif output_format == 'flac':
            cmd.extend(['-compression_level', '5'])
            cmd.extend(['-f', 'flac'])
        elif output_format == 'aac':
            cmd.extend(['-b:a', '192k'])
            cmd.extend(['-f', 'mp4'])
            cmd.extend(['-movflags', '+faststart'])
        elif output_format == 'm4a':
            cmd.extend(['-b:a', '192k'])
            cmd.extend(['-f', 'mp4'])
            cmd.extend(['-movflags', '+faststart'])
        elif output_format == 'aiff':
            cmd.extend(['-sample_fmt', 's16'])
            cmd.extend(['-f', 'aiff'])
        elif output_format == 'mp3':
            cmd.extend(['-b:a', '192k'])
            cmd.extend(['-f', 'mp3'])
        elif output_format == 'ogg':
            cmd.extend(['-b:a', '192k'])
            cmd.extend(['-f', 'ogg'])
        
        # Add flags to prevent stream copy
        cmd.extend([
            '-avoid_negative_ts', 'make_zero',
            '-fflags', '+genpts',
        ])
        
        # Add output
        cmd.extend([
            '-y',  # Overwrite output file
            output_path
        ])
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode != 0:
            error_msg = result.stderr if result.stderr else result.stdout if result.stdout else 'Unknown error'
            error_lines = error_msg.split('\n')
            relevant_error = '\n'.join([line for line in error_lines if line.strip() and not line.startswith('frame=')][-5:])
            if not relevant_error.strip():
                relevant_error = error_msg[:500]
            raise ValueError(f'Conversion failed: {relevant_error[:500]}')
        
        if not os.path.exists(output_path):
            raise ValueError('Output file was not created')
        
        # Read output file
        with open(output_path, 'rb') as f:
            file_content = f.read()
        
        # Generate filename
        base_name = os.path.splitext(uploaded_file.name)[0]
        base_name = re.sub(r'[^\w\s.-]', '', base_name).strip()
        base_name = re.sub(r'[-\s]+', '-', base_name)
        safe_filename = f'{base_name}.{output_ext}'
        
        return file_content, output_ext, safe_filename
        
    finally:
        if temp_dir:
            try:
                shutil.rmtree(temp_dir)
            except (OSError, PermissionError):
                pass


def audio_converter(request):
    """Convert between audio formats. Supports batch conversion (up to 15 files)."""
    if request.method != 'POST':
        return render(request, 'media_converter/audio_converter.html')
    
    # Check for batch mode (multiple files)
    uploaded_files = request.FILES.getlist('audio_file')
    is_batch = len(uploaded_files) > 1
    
    if not uploaded_files:
        return render(request, 'media_converter/audio_converter.html', {
            'error': 'Please upload at least one audio file.'
        })
    
    # Limit batch size to 15 files
    if len(uploaded_files) > 15:
        return render(request, 'media_converter/audio_converter.html', {
            'error': 'Maximum 15 files allowed for batch conversion. Please select fewer files.'
        })
    
    uploaded_file = uploaded_files[0]  # For single file processing
    output_format = request.POST.get('output_format', 'mp3').lower()
    
    # Debug: Log the received output format
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f'Audio converter called - is_batch: {is_batch}, file_count: {len(uploaded_files)}, output_format from POST: {request.POST.get("output_format")}, normalized: {output_format}')
    
    if output_format not in ['mp3', 'wav', 'ogg', 'flac', 'aac', 'm4a', 'aiff']:
        return render(request, 'media_converter/audio_converter.html', {
            'error': 'Invalid output format selected.'
        })
    
    # Check FFmpeg
    ffmpeg_path, ffprobe_path, error = _check_ffmpeg()
    if error:
        return render(request, 'media_converter/audio_converter.html', {'error': error})
    
    try:
        # Single file conversion
        if not is_batch:
            file_content, output_ext, safe_filename = _convert_single_audio(uploaded_file, output_format, ffmpeg_path, logger)
            
            # Determine content type
            content_type_map = {
                'mp3': 'audio/mpeg',
                'wav': 'audio/wav',
                'ogg': 'audio/ogg',
                'flac': 'audio/flac',
                'aac': 'audio/aac',
                'm4a': 'audio/mp4',
                'aiff': 'audio/x-aiff',
            }
            
            # Encode file as base64 to send as JSON
            file_base64 = base64.b64encode(file_content).decode('utf-8')
            
            response_data = {
                'file': file_base64,
                'filename': safe_filename,
                'content_type': content_type_map[output_format]
            }
            
            response = HttpResponse(
                json.dumps(response_data),
                content_type='application/json'
            )
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
            return response
        
        # Batch conversion - create ZIP file
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            successful = 0
            failed = []
            
            for idx, uploaded_file in enumerate(uploaded_files):
                try:
                    file_content, output_ext, safe_filename = _convert_single_audio(uploaded_file, output_format, ffmpeg_path, logger)
                    
                    # Add to ZIP
                    zip_file.writestr(safe_filename, file_content)
                    successful += 1
                    
                except Exception as e:
                    failed.append(f"{uploaded_file.name}: {str(e)}")
                    continue
            
            if successful == 0:
                error_msg = "All files failed to convert. "
                if failed:
                    error_msg += "Errors: " + "; ".join(failed[:5])
                return render(request, 'media_converter/audio_converter.html', {
                    'error': error_msg
                })
        
        zip_buffer.seek(0)
        
        # Create response with ZIP file
        response = HttpResponse(zip_buffer.read(), content_type='application/zip')
        response['Content-Disposition'] = 'attachment; filename="converted_audio.zip"'
        return response
        
    except Exception as e:
        error_response = f'Error processing file: {str(e)}'
        logger.error(f'Audio converter exception: {error_response}', exc_info=True)
        # Check if this is an AJAX request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
            return HttpResponse(
                json.dumps({'error': error_response}),
                content_type='application/json',
                status=500
            )
        return render(request, 'media_converter/audio_converter.html', {
            'error': error_response
        })

def video_to_gif(request):
    """Convert video to animated GIF"""
    if request.method != 'POST':
        return render(request, 'media_converter/video_to_gif.html')
    
    if 'video_file' not in request.FILES:
        return render(request, 'media_converter/video_to_gif.html', {
            'error': 'Please upload a video file.'
        })
    
    uploaded_file = request.FILES['video_file']
    
    # Validate file size (max 700MB for videos)
    max_size = 700 * 1024 * 1024  # 700MB
    if uploaded_file.size > max_size:
        return render(request, 'media_converter/video_to_gif.html', {
            'error': f'File size exceeds 700MB limit. Your file is {uploaded_file.size / (1024 * 1024):.1f}MB.'
        })
    
    # Get parameters
    start_time = request.POST.get('start_time', '0').strip() or '0'
    duration = request.POST.get('duration', '5').strip() or '5'
    width = request.POST.get('width', '640').strip() or '640'
    fps = request.POST.get('fps', '10').strip() or '10'
    
    try:
        duration = float(duration)
        width = int(width)
        fps = int(fps)
        
        if duration <= 0 or duration > 30:
            return render(request, 'media_converter/video_to_gif.html', {
                'error': 'Duration must be between 0 and 30 seconds.'
            })
        
        if width <= 0 or width > 1920:
            return render(request, 'media_converter/video_to_gif.html', {
                'error': 'Width must be between 1 and 1920 pixels.'
            })
        
        if fps <= 0 or fps > 30:
            return render(request, 'media_converter/video_to_gif.html', {
                'error': 'FPS must be between 1 and 30.'
            })
    except ValueError:
        return render(request, 'media_converter/video_to_gif.html', {
            'error': 'Invalid parameter values. Please enter valid numbers.'
        })
    
    # Validate file type
    allowed_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.wmv', '.3gp']
    file_ext = os.path.splitext(uploaded_file.name)[1].lower()
    
    if file_ext not in allowed_extensions:
        return render(request, 'media_converter/video_to_gif.html', {
            'error': 'Invalid file type. Please upload MP4, AVI, MOV, MKV, WebM, FLV, WMV, or 3GP files.'
        })
    
    # Check FFmpeg
    ffmpeg_path, ffprobe_path, error = _check_ffmpeg()
    if error:
        return render(request, 'media_converter/video_to_gif.html', {'error': error})
    
    temp_dir = None
    try:
        # Create temporary directory
        temp_dir = tempfile.mkdtemp()
        input_path = os.path.join(temp_dir, f'input{file_ext}')
        palette_path = os.path.join(temp_dir, 'palette.png')
        output_path = os.path.join(temp_dir, 'output.gif')
        
        # Save uploaded file
        with open(input_path, 'wb') as f:
            for chunk in uploaded_file.chunks():
                f.write(chunk)
        
        # Generate palette for better quality
        # Use -frames:v 1 to generate a single palette frame
        palette_cmd = [
            ffmpeg_path,
            '-ss', str(start_time),
            '-i', input_path,
            '-t', str(duration),
            '-vf', f'fps={fps},scale={width}:-1:flags=lanczos,palettegen=stats_mode=single',
            '-frames:v', '1',
            '-y',
            palette_path
        ]
        
        result = subprocess.run(palette_cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode != 0 or not os.path.exists(palette_path):
            error_msg = result.stderr if result.stderr else result.stdout if result.stdout else 'Unknown error during palette generation'
            # Show more of the error message
            full_error = error_msg[:1000] if len(error_msg) > 1000 else error_msg
            if temp_dir:
                try:
                    shutil.rmtree(temp_dir)
                except (OSError, PermissionError):
                    pass
            return render(request, 'media_converter/video_to_gif.html', {
                'error': f'Palette generation failed: {full_error}'
            })
        
        # Create GIF using palette
        # Fix filter_complex syntax - need to properly reference the inputs
        gif_cmd = [
            ffmpeg_path,
            '-ss', str(start_time),
            '-i', input_path,
            '-i', palette_path,
            '-t', str(duration),
            '-filter_complex', f'[0:v]fps={fps},scale={width}:-1:flags=lanczos[x];[x][1:v]paletteuse',
            '-y',
            output_path
        ]
        
        result = subprocess.run(gif_cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode != 0 or not os.path.exists(output_path):
            error_msg = result.stderr if result.stderr else result.stdout if result.stdout else 'Unknown error during GIF creation'
            # Show more of the error message
            full_error = error_msg[:1000] if len(error_msg) > 1000 else error_msg
            if temp_dir:
                try:
                    shutil.rmtree(temp_dir)
                except (OSError, PermissionError):
                    pass
            return render(request, 'media_converter/video_to_gif.html', {
                'error': f'GIF creation failed: {full_error}'
            })
        
        # Read output file and verify it's actually a GIF
        with open(output_path, 'rb') as f:
            file_content = f.read()
            
        # Verify the file is actually a GIF by checking the magic bytes (GIF89a or GIF87a)
        if len(file_content) < 6:
            return render(request, 'media_converter/video_to_gif.html', {
                'error': 'Generated file is too small to be a valid GIF.'
            })
        
        magic_bytes = file_content[:6]
        # Check for GIF89a or GIF87a - first 3 bytes should be "GIF"
        if magic_bytes[:3] != b'GIF':
            # Also check if it might be a different format that FFmpeg created
            error_msg = result.stderr[:500] if result.stderr else 'Unknown error'
            return render(request, 'media_converter/video_to_gif.html', {
                'error': f'Generated file is not a valid GIF file. The file may be corrupted or FFmpeg failed silently. Error: {error_msg}'
            })
        
        # Clean up
        try:
            shutil.rmtree(temp_dir)
        except (OSError, PermissionError):
            pass
        
        # Create response
        # Note: We don't set Content-Disposition here to prevent browser auto-download
        # JavaScript will handle the download programmatically to keep page responsive
        # Preserve .gif extension in filename
        base_name = os.path.splitext(uploaded_file.name)[0]
        safe_filename = re.sub(r'[^\w\s-]', '', base_name).strip()
        safe_filename = re.sub(r'[-\s]+', '-', safe_filename)
        if not safe_filename.endswith('.gif'):
            safe_filename = safe_filename + '.gif'
        
        response = HttpResponse(file_content, content_type='image/gif')
        response['Content-Length'] = len(file_content)
        response['X-Filename'] = safe_filename
        return response
        
    except Exception as e:
        if temp_dir:
            try:
                shutil.rmtree(temp_dir)
            except (OSError, PermissionError):
                pass
        return render(request, 'media_converter/video_to_gif.html', {
            'error': f'Error processing file: {str(e)}'
        })

def video_converter(request):
    """Convert between video formats"""
    if request.method != 'POST':
        return render(request, 'media_converter/video_converter.html')
    
    if 'video_file' not in request.FILES:
        return render(request, 'media_converter/video_converter.html', {
            'error': 'Please upload a video file.'
        })
    
    uploaded_file = request.FILES['video_file']
    output_format = request.POST.get('output_format', 'mp4').lower()
    
    # Validate file size (max 700MB for videos, but warn about large files)
    max_size = 700 * 1024 * 1024  # 700MB
    if uploaded_file.size > max_size:
        return render(request, 'media_converter/video_converter.html', {
            'error': f'File size exceeds 700MB limit. Your file is {uploaded_file.size / (1024 * 1024):.1f}MB.'
        })
    
    # Debug logging
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f'Video conversion started: {uploaded_file.name}, format: {output_format}, size: {uploaded_file.size} bytes')
    
    # Validate file type
    allowed_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.wmv', '.3gp']
    file_ext = os.path.splitext(uploaded_file.name)[1].lower()
    
    if file_ext not in allowed_extensions:
        return render(request, 'media_converter/video_converter.html', {
            'error': 'Invalid file type. Please upload MP4, AVI, MOV, MKV, WebM, FLV, WMV, or 3GP files.'
        })
    
    if output_format not in ['mp4', 'avi', 'mov', 'mkv', 'webm', '3gp']:
        return render(request, 'media_converter/video_converter.html', {
            'error': 'Invalid output format selected.'
        })
    
    # Check FFmpeg
    ffmpeg_path, ffprobe_path, error = _check_ffmpeg()
    if error:
        return render(request, 'media_converter/video_converter.html', {'error': error})
    
    temp_dir = None
    try:
        # Create temporary directory
        temp_dir = tempfile.mkdtemp()
        input_path = os.path.join(temp_dir, f'input{file_ext}')
        output_path = os.path.join(temp_dir, f'output.{output_format}')
        
        # Save uploaded file
        with open(input_path, 'wb') as f:
            for chunk in uploaded_file.chunks():
                f.write(chunk)
        
        # Get file size to warn about large files
        file_size_mb = os.path.getsize(input_path) / (1024 * 1024)
        
        # Limit CPU usage and optimize for faster processing
        # Use ultrafast preset for speed, limit threads to prevent system overload
        # Build command based on output format
        if output_format == 'webm':
            cmd = [
                ffmpeg_path,
                '-i', input_path,
                '-c:v', 'libvpx-vp9',  # Video codec
                '-c:a', 'libopus',  # Audio codec
                '-speed', '4',  # Fast encoding (0-8, higher = faster)
                '-threads', '2',  # Limit to 2 threads to prevent system overload
                '-y',
                output_path
            ]
        elif output_format == 'avi':
            cmd = [
                ffmpeg_path,
                '-i', input_path,
                '-c:v', 'libx264',  # Video codec
                '-c:a', 'libmp3lame',  # Audio codec
                '-preset', 'ultrafast',  # Fastest encoding (less CPU intensive)
                '-crf', '28',  # Slightly lower quality but much faster
                '-threads', '2',  # Limit to 2 threads to prevent system overload
                '-y',
                output_path
            ]
        elif output_format == '3gp':
            cmd = [
                ffmpeg_path,
                '-i', input_path,
                '-c:v', 'libx264',  # Video codec
                '-c:a', 'aac',  # Audio codec
                '-preset', 'ultrafast',  # Fastest encoding (less CPU intensive)
                '-crf', '28',  # Slightly lower quality but much faster
                '-threads', '2',  # Limit to 2 threads to prevent system overload
                '-s', '320x240',  # Common 3GP resolution
                '-b:v', '128k',  # Video bitrate for 3GP
                '-b:a', '64k',  # Audio bitrate for 3GP
                '-y',
                output_path
            ]
        else:  # mp4, mov, mkv
            cmd = [
                ffmpeg_path,
                '-i', input_path,
                '-c:v', 'libx264',  # Video codec
                '-c:a', 'aac',  # Audio codec
                '-preset', 'ultrafast',  # Fastest encoding (less CPU intensive)
                '-crf', '28',  # Slightly lower quality but much faster
                '-threads', '2',  # Limit to 2 threads to prevent system overload
                '-movflags', '+faststart',  # Optimize for web playback
                '-y',
                output_path
            ]
        
        # Warn user if file is extremely large (over 500MB)
        if file_size_mb > 500:
            return render(request, 'media_converter/video_converter.html', {
                'error': f'File is too large ({file_size_mb:.1f} MB). For best performance, please use files under 500 MB. Large files may take a very long time to convert and could cause system slowdowns.'
            })
        
        # Adjust timeout based on file size (larger files need more time)
        timeout_seconds = 600  # 10 minutes default
        if file_size_mb > 300:
            timeout_seconds = 1200  # 20 minutes for very large files
        elif file_size_mb > 200:
            timeout_seconds = 900  # 15 minutes for large files
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_seconds)
        
        # Check if conversion failed
        if result.returncode != 0:
            error_msg = result.stderr if result.stderr else result.stdout if result.stdout else 'Unknown error during video conversion'
            full_error = error_msg[:1000] if len(error_msg) > 1000 else error_msg
            if temp_dir:
                try:
                    shutil.rmtree(temp_dir)
                except (OSError, PermissionError):
                    pass
            return render(request, 'media_converter/video_converter.html', {
                'error': f'Video conversion failed: {full_error}'
            })
        
        if not os.path.exists(output_path):
            error_msg = result.stderr if result.stderr else result.stdout if result.stdout else 'Unknown error - output file was not created'
            full_error = error_msg[:1000] if len(error_msg) > 1000 else error_msg
            if temp_dir:
                try:
                    shutil.rmtree(temp_dir)
                except (OSError, PermissionError):
                    pass
            return render(request, 'media_converter/video_converter.html', {
                'error': f'Conversion failed - output file not created: {full_error}'
            })
        
        # Read output file
        with open(output_path, 'rb') as f:
            file_content = f.read()
        
        # Verify file is not empty
        if len(file_content) == 0:
            if temp_dir:
                try:
                    shutil.rmtree(temp_dir)
                except (OSError, PermissionError):
                    pass
            return render(request, 'media_converter/video_converter.html', {
                'error': 'Conversion failed - output file is empty. The video file may be corrupted or in an unsupported format.'
            })
        
        # Clean up
        try:
            shutil.rmtree(temp_dir)
        except (OSError, PermissionError):
            pass
        
        # Determine content type
        content_type_map = {
            'mp4': 'video/mp4',
            'avi': 'video/x-msvideo',
            'mov': 'video/quicktime',
            'mkv': 'video/x-matroska',
            'webm': 'video/webm',
            '3gp': 'video/3gpp',
        }
        
        # Create response
        # Note: We don't set Content-Disposition here to prevent browser auto-download
        # JavaScript will handle the download programmatically to keep page responsive
        safe_filename = os.path.splitext(uploaded_file.name)[0] + f'.{output_format}'
        safe_filename = re.sub(r'[^\w\s-]', '', safe_filename).strip()
        safe_filename = re.sub(r'[-\s]+', '-', safe_filename)
        
        response = HttpResponse(file_content, content_type=content_type_map[output_format])
        response['Content-Length'] = len(file_content)
        response['X-Filename'] = safe_filename
        return response
        
    except subprocess.TimeoutExpired:
        if temp_dir:
            try:
                shutil.rmtree(temp_dir)
            except (OSError, PermissionError) as cleanup_error:
                # Log cleanup errors but don't fail the request
                print(f"Warning: Failed to cleanup temp directory: {cleanup_error}")
                pass
        return render(request, 'media_converter/video_converter.html', {
            'error': 'Video conversion timed out. The video might be too long or complex for server processing. Try a smaller file.'
        })
    except Exception as e:
        if temp_dir:
            try:
                shutil.rmtree(temp_dir)
            except (OSError, PermissionError) as cleanup_error:
                # Log cleanup errors but don't fail the request
                print(f"Warning: Failed to cleanup temp directory: {cleanup_error}")
                pass
        return render(request, 'media_converter/video_converter.html', {
            'error': f'Error processing file: {str(e)}'
        })

def video_compressor(request):
    """Compress video files to reduce file size"""
    if request.method != 'POST':
        return render(request, 'media_converter/video_compressor.html')
    
    if 'video_file' not in request.FILES:
        return render(request, 'media_converter/video_compressor.html', {
            'error': 'Please upload a video file.'
        })
    
    uploaded_file = request.FILES['video_file']
    compression_level = request.POST.get('compression_level', 'medium').strip()
    
    # Validate file size (max 700MB for videos)
    max_size = 700 * 1024 * 1024  # 700MB
    if uploaded_file.size > max_size:
        return render(request, 'media_converter/video_compressor.html', {
            'error': f'File size exceeds 700MB limit. Your file is {uploaded_file.size / (1024 * 1024):.1f}MB.'
        })
    
    # Validate file type
    allowed_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.wmv', '.3gp']
    file_ext = os.path.splitext(uploaded_file.name)[1].lower()
    
    if file_ext not in allowed_extensions:
        return render(request, 'media_converter/video_compressor.html', {
            'error': 'Invalid file type. Please upload MP4, AVI, MOV, MKV, WebM, FLV, WMV, or 3GP files.'
        })
    
    if compression_level not in ['low', 'medium', 'high']:
        compression_level = 'medium'
    
    # Check FFmpeg
    ffmpeg_path, ffprobe_path, error = _check_ffmpeg()
    if error:
        return render(request, 'media_converter/video_compressor.html', {'error': error})
    
    temp_dir = None
    try:
        # Create temporary directory
        temp_dir = tempfile.mkdtemp()
        input_path = os.path.join(temp_dir, f'input{file_ext}')
        output_path = os.path.join(temp_dir, f'compressed{file_ext}')
        
        # Save uploaded file
        with open(input_path, 'wb') as f:
            for chunk in uploaded_file.chunks():
                f.write(chunk)
        
        # Get file size
        file_size_mb = os.path.getsize(input_path) / (1024 * 1024)
        
        # Compression settings based on level
        if compression_level == 'low':
            # Light compression - minimal quality loss
            crf = '23'
            preset = 'medium'
            video_bitrate = None
        elif compression_level == 'high':
            # Heavy compression - more quality loss, smaller file
            # Use bitrate-only mode (no CRF) to avoid conflicts with some FFmpeg versions
            crf = None  # Don't use CRF when using bitrate limits
            preset = 'ultrafast'
            video_bitrate = '500k'
        else:  # medium
            # Balanced compression
            crf = '28'
            preset = 'fast'
            video_bitrate = None
        
        # Build FFmpeg command for compression
        cmd = [
            ffmpeg_path,
            '-i', input_path,
            '-c:v', 'libx264',  # Video codec
            '-c:a', 'aac',  # Audio codec
            '-preset', preset,
            '-threads', '2',  # Limit threads
        ]
        
        # Add CRF or bitrate (not both - they conflict)
        if video_bitrate:
            # Use bitrate mode for high compression
            cmd.extend(['-b:v', video_bitrate])
            cmd.extend(['-maxrate', video_bitrate])
            cmd.extend(['-bufsize', str(int(video_bitrate.replace('k', '')) * 2) + 'k'])
        elif crf:
            # Use CRF mode for medium/low compression
            cmd.extend(['-crf', crf])
        
        # Scale down resolution for high compression
        # Note: Temporarily disabled scale filter to avoid syntax issues
        # High compression will use lower CRF and bitrate instead
        # if compression_level == 'high':
        #     cmd.extend(['-vf', 'scale=1280:-2'])
        
        cmd.extend(['-movflags', '+faststart', '-y', output_path])
        
        # Adjust timeout based on file size
        timeout_seconds = 600
        if file_size_mb > 300:
            timeout_seconds = 1200
        elif file_size_mb > 200:
            timeout_seconds = 900
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_seconds)
        
        # Check if compression failed
        if result.returncode != 0:
            # Extract meaningful error message from ffmpeg output
            error_msg = result.stderr if result.stderr else result.stdout if result.stdout else 'Unknown error'
            
            # First, check if the entire error is just FFmpeg version/config info
            error_lower = error_msg.lower()
            error_stripped = error_msg.strip()
            
            # Simple and direct check: if error contains "ffmpeg version" and "configuration:", it's likely a version dump
            # Also check if most lines are config flags (--enable-*, --disable-*, etc.)
            has_version = 'ffmpeg version' in error_lower
            has_config = 'configuration:' in error_lower or '--enable-' in error_lower or '--disable-' in error_lower
            
            if has_version and has_config:
                # Count meaningful (non-version/config) lines
                meaningful_line_count = 0
                for line in error_msg.split('\n'):
                    line_lower = line.lower().strip()
                    if not line_lower:
                        continue
                    # Skip version/config lines
                    if any(x in line_lower for x in ['ffmpeg version', 'configuration:', 'built with', 'copyright', 'the ffmpeg developers']):
                        continue
                    if line.strip().startswith('--'):
                        continue
                    meaningful_line_count += 1
                
                # If we have very few meaningful lines, it's just a version dump
                if meaningful_line_count < 3:
                    full_error = 'Video compression failed. The video file may be corrupted, in an unsupported format, or the compression settings may be incompatible with this video. Try using Medium or Low compression level instead.'
                else:
                    # Has some meaningful content, continue with filtering
                    full_error = None  # Will be set in else block
            else:
                full_error = None  # Will be set in else block
            
            # Only do detailed filtering if we didn't already set full_error
            if full_error is None:
                # Filter out version information and extract actual error
                error_lines = error_msg.split('\n')
                meaningful_errors = []
                
                # Skip patterns that indicate FFmpeg info/version output
                skip_patterns = [
                    'ffmpeg version', 'built with', 'configuration:', 'copyright',
                    'the ffmpeg developers', 'toolchain', 'libdir=', 'incdir=', 'arch=',
                    '--prefix=', '--extra-version=', '--enable-', '--disable-', 'gcc',
                    'debian', 'hardened', 'x86_64-linux-gnu'
                ]
                
                for line in error_lines:
                    line_lower = line.lower().strip()
                    
                    # Skip empty lines at the start
                    if not meaningful_errors and not line_lower:
                        continue
                    
                    # Skip if line matches any skip pattern
                    should_skip = False
                    for pattern in skip_patterns:
                        if pattern in line_lower:
                            should_skip = True
                            break
                    
                    # Also skip lines that start with -- (configuration flags)
                    if line.strip().startswith('--'):
                        should_skip = True
                    
                    if not should_skip and line_lower:
                        meaningful_errors.append(line.strip())
                
                # Use meaningful errors or fallback
                if meaningful_errors:
                    # Take last few meaningful error lines (usually contain the actual error)
                    error_text = '\n'.join(meaningful_errors[-5:])
                    # Limit length and ensure it's not just whitespace
                    full_error = error_text[:500].strip() if len(error_text) > 500 else error_text.strip()
                    
                    # If after filtering we only have whitespace or very short text, use fallback
                    if not full_error or len(full_error) < 10:
                        full_error = 'Video compression failed. The video file may be corrupted, in an unsupported format, or the compression settings may be incompatible with this video.'
                else:
                    full_error = 'Video compression failed. The video file may be corrupted, in an unsupported format, or the compression settings may be incompatible with this video.'
            
            if temp_dir:
                try:
                    shutil.rmtree(temp_dir)
                except (OSError, PermissionError):
                    pass
            return render(request, 'media_converter/video_compressor.html', {
                'error': f'Compression failed: {full_error}'
            })
        
        if not os.path.exists(output_path):
            error_msg_raw = result.stderr if result.stderr else 'Output file was not created'
            
            # Apply same filtering as above
            if isinstance(error_msg_raw, str) and 'ffmpeg version' in error_msg_raw.lower():
                # Filter out version info
                error_lines = error_msg_raw.split('\n')
                meaningful_errors = []
                skip_patterns = [
                    'ffmpeg version', 'built with', 'configuration:', 'copyright',
                    'the ffmpeg developers', 'toolchain', 'libdir=', 'incdir=', 'arch=',
                    '--prefix=', '--extra-version=', '--enable-', '--disable-', 'gcc',
                    'debian', 'hardened', 'x86_64-linux-gnu'
                ]
                
                for line in error_lines:
                    line_lower = line.lower().strip()
                    if not line_lower:
                        continue
                    should_skip = any(pattern in line_lower for pattern in skip_patterns) or line.strip().startswith('--')
                    if not should_skip:
                        meaningful_errors.append(line.strip())
                
                if meaningful_errors:
                    error_msg = '\n'.join(meaningful_errors[-3:])[:500]
                else:
                    error_msg = 'Output file was not created. The video file may be corrupted or in an unsupported format.'
            else:
                error_msg = error_msg_raw[:500] if len(error_msg_raw) > 500 else error_msg_raw
            
            if temp_dir:
                try:
                    shutil.rmtree(temp_dir)
                except (OSError, PermissionError):
                    pass
            return render(request, 'media_converter/video_compressor.html', {
                'error': f'Compression failed: {error_msg}'
            })
        
        # Read output file
        with open(output_path, 'rb') as f:
            file_content = f.read()
        
        if len(file_content) == 0:
            if temp_dir:
                try:
                    shutil.rmtree(temp_dir)
                except (OSError, PermissionError):
                    pass
            return render(request, 'media_converter/video_compressor.html', {
                'error': 'Compression failed - output file is empty.'
            })
        
        # Calculate compression ratio
        original_size = os.path.getsize(input_path)
        compressed_size = len(file_content)
        compression_ratio = (1 - compressed_size / original_size) * 100
        
        # Clean up
        try:
            shutil.rmtree(temp_dir)
        except (OSError, PermissionError):
            pass
        
        # Determine content type
        content_type_map = {
            '.mp4': 'video/mp4',
            '.avi': 'video/x-msvideo',
            '.mov': 'video/quicktime',
            '.mkv': 'video/x-matroska',
            '.webm': 'video/webm',
            '.flv': 'video/x-flv',
            '.wmv': 'video/x-ms-wmv',
            '.3gp': 'video/3gpp',
        }
        content_type = content_type_map.get(file_ext, 'video/mp4')
        
        # Create response
        safe_filename = os.path.splitext(uploaded_file.name)[0] + '_compressed' + file_ext
        safe_filename = re.sub(r'[^\w\s.-]', '', safe_filename).strip()
        safe_filename = re.sub(r'[-\s]+', '-', safe_filename)
        
        response = HttpResponse(file_content, content_type=content_type)
        response['Content-Length'] = len(file_content)
        response['X-Filename'] = safe_filename
        response['X-Compression-Ratio'] = f'{compression_ratio:.1f}%'
        return response
        
    except subprocess.TimeoutExpired:
        if temp_dir:
            try:
                shutil.rmtree(temp_dir)
            except (OSError, PermissionError):
                pass
        return render(request, 'media_converter/video_compressor.html', {
            'error': 'Compression timed out. The video might be too long or complex. Try a smaller file.'
        })
    except Exception as e:
        if temp_dir:
            try:
                shutil.rmtree(temp_dir)
            except (OSError, PermissionError):
                pass
        return render(request, 'media_converter/video_compressor.html', {
            'error': f'Error processing file: {str(e)}'
        })

def mute_video(request):
    """Remove audio track from video"""
    if request.method != 'POST':
        return render(request, 'media_converter/mute_video.html')
    
    if 'video_file' not in request.FILES:
        return render(request, 'media_converter/mute_video.html', {
            'error': 'Please upload a video file.'
        })
    
    uploaded_file = request.FILES['video_file']
    
    # Validate file size (max 700MB for videos)
    max_size = 700 * 1024 * 1024  # 700MB
    if uploaded_file.size > max_size:
        return render(request, 'media_converter/mute_video.html', {
            'error': f'File size exceeds 700MB limit. Your file is {uploaded_file.size / (1024 * 1024):.1f}MB.'
        })
    
    # Validate file type
    allowed_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.wmv', '.3gp']
    file_ext = os.path.splitext(uploaded_file.name)[1].lower()
    
    if file_ext not in allowed_extensions:
        return render(request, 'media_converter/mute_video.html', {
            'error': 'Invalid file type. Please upload MP4, AVI, MOV, MKV, WebM, FLV, WMV, or 3GP files.'
        })
    
    # Check FFmpeg
    ffmpeg_path, ffprobe_path, error = _check_ffmpeg()
    if error:
        return render(request, 'media_converter/mute_video.html', {'error': error})
    
    temp_dir = None
    try:
        # Create temporary directory
        temp_dir = tempfile.mkdtemp()
        input_path = os.path.join(temp_dir, f'input{file_ext}')
        output_path = os.path.join(temp_dir, f'muted{file_ext}')
        
        # Save uploaded file
        with open(input_path, 'wb') as f:
            for chunk in uploaded_file.chunks():
                f.write(chunk)
        
        # Get file size
        file_size_mb = os.path.getsize(input_path) / (1024 * 1024)
        
        # Build FFmpeg command to remove audio
        # Use stream copy for video (fast) and exclude audio
        cmd = [
            ffmpeg_path,
            '-i', input_path,
            '-c:v', 'copy',  # Copy video stream (no re-encoding, fast)
            '-an',  # No audio
            '-y',
            output_path
        ]
        
        # Adjust timeout based on file size
        timeout_seconds = 300  # 5 minutes default (should be fast with stream copy)
        if file_size_mb > 300:
            timeout_seconds = 600
        elif file_size_mb > 200:
            timeout_seconds = 450
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_seconds)
        
        # Check if processing failed
        if result.returncode != 0:
            error_msg = result.stderr if result.stderr else result.stdout if result.stdout else 'Unknown error'
            full_error = error_msg[:1000] if len(error_msg) > 1000 else error_msg
            if temp_dir:
                try:
                    shutil.rmtree(temp_dir)
                except (OSError, PermissionError):
                    pass
            return render(request, 'media_converter/mute_video.html', {
                'error': f'Processing failed: {full_error}'
            })
        
        if not os.path.exists(output_path):
            error_msg = result.stderr if result.stderr else 'Output file was not created'
            if temp_dir:
                try:
                    shutil.rmtree(temp_dir)
                except (OSError, PermissionError):
                    pass
            return render(request, 'media_converter/mute_video.html', {
                'error': f'Processing failed: {error_msg[:500]}'
            })
        
        # Read output file
        with open(output_path, 'rb') as f:
            file_content = f.read()
        
        if len(file_content) == 0:
            if temp_dir:
                try:
                    shutil.rmtree(temp_dir)
                except (OSError, PermissionError):
                    pass
            return render(request, 'media_converter/mute_video.html', {
                'error': 'Processing failed - output file is empty.'
            })
        
        # Clean up
        try:
            shutil.rmtree(temp_dir)
        except (OSError, PermissionError):
            pass
        
        # Determine content type
        content_type_map = {
            '.mp4': 'video/mp4',
            '.avi': 'video/x-msvideo',
            '.mov': 'video/quicktime',
            '.mkv': 'video/x-matroska',
            '.webm': 'video/webm',
            '.flv': 'video/x-flv',
            '.wmv': 'video/x-ms-wmv',
            '.3gp': 'video/3gpp',
        }
        content_type = content_type_map.get(file_ext, 'video/mp4')
        
        # Create response
        safe_filename = os.path.splitext(uploaded_file.name)[0] + '_muted' + file_ext
        safe_filename = re.sub(r'[^\w\s.-]', '', safe_filename).strip()
        safe_filename = re.sub(r'[-\s]+', '-', safe_filename)
        
        response = HttpResponse(file_content, content_type=content_type)
        response['Content-Length'] = len(file_content)
        response['X-Filename'] = safe_filename
        return response
        
    except subprocess.TimeoutExpired:
        if temp_dir:
            try:
                shutil.rmtree(temp_dir)
            except (OSError, PermissionError):
                pass
        return render(request, 'media_converter/mute_video.html', {
            'error': 'Processing timed out. The video might be too long. Try a smaller file.'
        })
    except Exception as e:
        if temp_dir:
            try:
                shutil.rmtree(temp_dir)
            except (OSError, PermissionError):
                pass
        return render(request, 'media_converter/mute_video.html', {
            'error': f'Error processing file: {str(e)}'
        })

def audio_splitter(request):
    """Split audio files into segments"""
    if request.method != 'POST':
        return render(request, 'media_converter/audio_splitter.html')
    
    if 'audio_file' not in request.FILES:
        return render(request, 'media_converter/audio_splitter.html', {
            'error': 'Please upload an audio file.'
        })
    
    uploaded_file = request.FILES['audio_file']
    start_time = request.POST.get('start_time', '0').strip()
    duration = request.POST.get('duration', '').strip()
    end_time = request.POST.get('end_time', '').strip()
    
    # Validate file size
    max_size = 700 * 1024 * 1024  # 700MB
    if uploaded_file.size > max_size:
        return render(request, 'media_converter/audio_splitter.html', {
            'error': f'File size exceeds 700MB limit. Your file is {uploaded_file.size / (1024 * 1024):.1f}MB.'
        })
    
    # Validate file type
    allowed_extensions = ['.mp3', '.wav', '.ogg', '.flac', '.aac', '.m4a', '.aiff', '.aif']
    file_ext = os.path.splitext(uploaded_file.name)[1].lower()
    
    if file_ext not in allowed_extensions:
        return render(request, 'media_converter/audio_splitter.html', {
            'error': 'Invalid file type. Please upload MP3, WAV, OGG, FLAC, AAC, M4A, or AIFF files.'
        })
    
    # Validate time parameters
    try:
        start_seconds = float(start_time) if start_time else 0.0
        if start_seconds < 0:
            return render(request, 'media_converter/audio_splitter.html', {
                'error': 'Start time cannot be negative.'
            })
        
        if duration and end_time:
            return render(request, 'media_converter/audio_splitter.html', {
                'error': 'Please specify either duration or end time, not both.'
            })
        
        if not duration and not end_time:
            return render(request, 'media_converter/audio_splitter.html', {
                'error': 'Please specify either duration or end time.'
            })
        
        if duration:
            duration_seconds = float(duration)
            if duration_seconds <= 0:
                return render(request, 'media_converter/audio_splitter.html', {
                    'error': 'Duration must be greater than 0.'
                })
            end_seconds = start_seconds + duration_seconds
        else:
            end_seconds = float(end_time)
            if end_seconds <= start_seconds:
                return render(request, 'media_converter/audio_splitter.html', {
                    'error': 'End time must be greater than start time.'
                })
            duration_seconds = end_seconds - start_seconds
        
    except ValueError:
        return render(request, 'media_converter/audio_splitter.html', {
            'error': 'Invalid time format. Please use numbers (e.g., 10.5 for 10.5 seconds).'
        })
    
    # Check FFmpeg
    ffmpeg_path, ffprobe_path, error = _check_ffmpeg()
    if error:
        return render(request, 'media_converter/audio_splitter.html', {'error': error})
    
    temp_dir = None
    try:
        # Create temporary directory
        temp_dir = tempfile.mkdtemp()
        input_path = os.path.join(temp_dir, f'input{file_ext}')
        output_path = os.path.join(temp_dir, f'split{file_ext}')
        
        # Save uploaded file
        with open(input_path, 'wb') as f:
            for chunk in uploaded_file.chunks():
                f.write(chunk)
        
        # Build FFmpeg command to extract segment
        # Try copy first (fast), fall back to re-encoding if needed
        cmd = [
            ffmpeg_path,
            '-i', input_path,
            '-ss', str(start_seconds),  # Start time
            '-t', str(duration_seconds),  # Duration
            '-c:a', 'copy',  # Copy audio stream (fast, no re-encoding)
            '-y',
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        # If copy fails, re-encode
        if result.returncode != 0 or not os.path.exists(output_path):
            # Determine codec based on format
            codec_map = {
                '.mp3': 'libmp3lame',
                '.wav': 'pcm_s16le',
                '.ogg': 'libvorbis',
                '.flac': 'flac',
                '.aac': 'aac',
                '.m4a': 'aac',
                '.aiff': 'pcm_s16be',
                '.aif': 'pcm_s16be',
            }
            
            format_map = {
                '.mp3': 'mp3',
                '.wav': 'wav',
                '.ogg': 'ogg',
                '.flac': 'flac',
                '.aac': 'mp4',
                '.m4a': 'mp4',
                '.aiff': 'aiff',
                '.aif': 'aiff',
            }
            
            codec = codec_map.get(file_ext, 'libmp3lame')
            output_format = format_map.get(file_ext, 'mp3')
            
            cmd = [
                ffmpeg_path,
                '-i', input_path,
                '-ss', str(start_seconds),
                '-t', str(duration_seconds),
                '-c:a', codec,
                '-ar', '44100',
                '-ac', '2',
            ]
            
            if output_format == 'mp3':
                cmd.extend(['-b:a', '192k', '-f', 'mp3'])
            elif output_format == 'wav':
                cmd.extend(['-sample_fmt', 's16', '-f', 'wav'])
            elif output_format == 'flac':
                cmd.extend(['-compression_level', '5', '-f', 'flac'])
            elif output_format in ['mp4', 'aac', 'm4a']:
                cmd.extend(['-b:a', '192k', '-f', 'mp4', '-movflags', '+faststart'])
            elif output_format == 'aiff':
                cmd.extend(['-sample_fmt', 's16', '-f', 'aiff'])
            else:
                cmd.extend(['-f', output_format])
            
            cmd.extend(['-y', output_path])
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode != 0 or not os.path.exists(output_path):
            error_msg = result.stderr if result.stderr else result.stdout if result.stdout else 'Unknown error'
            full_error = error_msg[:1000] if len(error_msg) > 1000 else error_msg
            if temp_dir:
                try:
                    shutil.rmtree(temp_dir)
                except (OSError, PermissionError):
                    pass
            return render(request, 'media_converter/audio_splitter.html', {
                'error': f'Splitting failed: {full_error}'
            })
        
        # Read output file
        with open(output_path, 'rb') as f:
            file_content = f.read()
        
        if len(file_content) == 0:
            if temp_dir:
                try:
                    shutil.rmtree(temp_dir)
                except (OSError, PermissionError):
                    pass
            return render(request, 'media_converter/audio_splitter.html', {
                'error': 'Splitting failed - output file is empty.'
            })
        
        # Clean up
        try:
            shutil.rmtree(temp_dir)
        except (OSError, PermissionError):
            pass
        
        # Determine content type
        content_type_map = {
            '.mp3': 'audio/mpeg',
            '.wav': 'audio/wav',
            '.ogg': 'audio/ogg',
            '.flac': 'audio/flac',
            '.aac': 'audio/aac',
            '.m4a': 'audio/mp4',
            '.aiff': 'audio/x-aiff',
            '.aif': 'audio/x-aiff',
        }
        content_type = content_type_map.get(file_ext, 'audio/mpeg')
        
        # Create response
        safe_filename = os.path.splitext(uploaded_file.name)[0] + f'_split_{int(start_seconds)}s-{int(end_seconds)}s{file_ext}'
        safe_filename = re.sub(r'[^\w\s.-]', '', safe_filename).strip()
        safe_filename = re.sub(r'[-\s]+', '-', safe_filename)
        
        response = HttpResponse(file_content, content_type=content_type)
        response['Content-Length'] = len(file_content)
        response['X-Filename'] = safe_filename
        return response
        
    except subprocess.TimeoutExpired:
        if temp_dir:
            try:
                shutil.rmtree(temp_dir)
            except (OSError, PermissionError):
                pass
        return render(request, 'media_converter/audio_splitter.html', {
            'error': 'Processing timed out. Please try again.'
        })
    except Exception as e:
        if temp_dir:
            try:
                shutil.rmtree(temp_dir)
            except (OSError, PermissionError):
                pass
        return render(request, 'media_converter/audio_splitter.html', {
            'error': f'Error processing file: {str(e)}'
        })

def audio_merge(request):
    """Merge multiple audio files into one"""
    if request.method != 'POST':
        return render(request, 'media_converter/audio_merge.html')
    
    if 'audio_files' not in request.FILES:
        return render(request, 'media_converter/audio_merge.html', {
            'error': 'Please upload at least one audio file.'
        })
    
    uploaded_files = request.FILES.getlist('audio_files')
    
    if len(uploaded_files) < 2:
        return render(request, 'media_converter/audio_merge.html', {
            'error': 'Please upload at least 2 audio files to merge.'
        })
    
    # Validate files
    max_size = 700 * 1024 * 1024
    allowed_extensions = ['.mp3', '.wav', '.ogg', '.flac', '.aac', '.m4a', '.aiff', '.aif']
    
    for uploaded_file in uploaded_files:
        if uploaded_file.size > max_size:
            return render(request, 'media_converter/audio_merge.html', {
                'error': f'File {uploaded_file.name} exceeds 700MB limit.'
            })
        
        file_ext = os.path.splitext(uploaded_file.name)[1].lower()
        if file_ext not in allowed_extensions:
            return render(request, 'media_converter/audio_merge.html', {
                'error': f'Invalid file type: {uploaded_file.name}'
            })
    
    # Check FFmpeg
    ffmpeg_path, ffprobe_path, error = _check_ffmpeg()
    if error:
        return render(request, 'media_converter/audio_merge.html', {'error': error})
    
    temp_dir = None
    try:
        # Create temporary directory
        temp_dir = tempfile.mkdtemp()
        input_paths = []
        file_list_path = os.path.join(temp_dir, 'file_list.txt')
        
        # Save all uploaded files
        for i, uploaded_file in enumerate(uploaded_files):
            file_ext = os.path.splitext(uploaded_file.name)[1].lower()
            input_path = os.path.join(temp_dir, f'input_{i}{file_ext}')
            input_paths.append(input_path)
            
            with open(input_path, 'wb') as f:
                for chunk in uploaded_file.chunks():
                    f.write(chunk)
        
        # Create file list for FFmpeg concat
        with open(file_list_path, 'w') as f:
            for input_path in input_paths:
                # Escape single quotes and backslashes for FFmpeg
                escaped_path = input_path.replace("'", "'\\''").replace("\\", "\\\\")
                f.write(f"file '{escaped_path}'\n")
        
        # Determine output format (use first file's format or MP3)
        output_ext = os.path.splitext(uploaded_files[0].name)[1].lower()
        if output_ext not in allowed_extensions:
            output_ext = '.mp3'
        
        output_path = os.path.join(temp_dir, f'merged{output_ext}')
        
        # Build FFmpeg command to merge
        # First, convert all to same format if needed, then concat
        cmd = [
            ffmpeg_path,
            '-f', 'concat',
            '-safe', '0',
            '-i', file_list_path,
            '-c', 'copy',  # Copy streams (fast, no re-encoding if formats match)
            '-y',
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        
        # If concat with copy fails (different formats), re-encode
        if result.returncode != 0:
            # Re-encode all to same format
            codec_map = {
                '.mp3': 'libmp3lame',
                '.wav': 'pcm_s16le',
                '.ogg': 'libvorbis',
                '.flac': 'flac',
                '.aac': 'aac',
                '.m4a': 'aac',
                '.aiff': 'pcm_s16be',
                '.aif': 'pcm_s16be',
            }
            
            codec = codec_map.get(output_ext, 'libmp3lame')
            format_map = {
                '.mp3': 'mp3',
                '.wav': 'wav',
                '.ogg': 'ogg',
                '.flac': 'flac',
                '.aac': 'mp4',
                '.m4a': 'mp4',
                '.aiff': 'aiff',
                '.aif': 'aiff',
            }
            output_format = format_map.get(output_ext, 'mp3')
            
            cmd = [
                ffmpeg_path,
                '-f', 'concat',
                '-safe', '0',
                '-i', file_list_path,
                '-c:a', codec,
                '-ar', '44100',
                '-ac', '2',
            ]
            
            if output_format == 'mp3':
                cmd.extend(['-b:a', '192k'])
            elif output_format == 'wav':
                cmd.extend(['-sample_fmt', 's16'])
            elif output_format in ['mp4', 'aac', 'm4a']:
                cmd.extend(['-b:a', '192k'])
                cmd.extend(['-movflags', '+faststart'])
            
            cmd.extend(['-f', output_format, '-y', output_path])
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        
        if result.returncode != 0 or not os.path.exists(output_path):
            error_msg = result.stderr if result.stderr else result.stdout if result.stdout else 'Unknown error'
            full_error = error_msg[:1000] if len(error_msg) > 1000 else error_msg
            if temp_dir:
                try:
                    shutil.rmtree(temp_dir)
                except (OSError, PermissionError):
                    pass
            return render(request, 'media_converter/audio_merge.html', {
                'error': f'Merging failed: {full_error}'
            })
        
        # Read output file
        with open(output_path, 'rb') as f:
            file_content = f.read()
        
        if len(file_content) == 0:
            if temp_dir:
                try:
                    shutil.rmtree(temp_dir)
                except (OSError, PermissionError):
                    pass
            return render(request, 'media_converter/audio_merge.html', {
                'error': 'Merging failed - output file is empty.'
            })
        
        # Clean up
        try:
            shutil.rmtree(temp_dir)
        except (OSError, PermissionError):
            pass
        
        # Determine content type
        content_type_map = {
            '.mp3': 'audio/mpeg',
            '.wav': 'audio/wav',
            '.ogg': 'audio/ogg',
            '.flac': 'audio/flac',
            '.aac': 'audio/aac',
            '.m4a': 'audio/mp4',
            '.aiff': 'audio/x-aiff',
            '.aif': 'audio/x-aiff',
        }
        content_type = content_type_map.get(output_ext, 'audio/mpeg')
        
        # Create response
        safe_filename = 'merged_audio' + output_ext
        response = HttpResponse(file_content, content_type=content_type)
        response['Content-Length'] = len(file_content)
        response['X-Filename'] = safe_filename
        return response
        
    except subprocess.TimeoutExpired:
        if temp_dir:
            try:
                shutil.rmtree(temp_dir)
            except (OSError, PermissionError):
                pass
        return render(request, 'media_converter/audio_merge.html', {
            'error': 'Processing timed out. Please try again.'
        })
    except Exception as e:
        if temp_dir:
            try:
                shutil.rmtree(temp_dir)
            except (OSError, PermissionError):
                pass
        return render(request, 'media_converter/audio_merge.html', {
            'error': f'Error processing files: {str(e)}'
        })

def reduce_noise(request):
    """Reduce background noise from audio files"""
    if request.method != 'POST':
        return render(request, 'media_converter/reduce_noise.html')
    
    if 'audio_file' not in request.FILES:
        return render(request, 'media_converter/reduce_noise.html', {
            'error': 'Please upload an audio file.'
        })
    
    uploaded_file = request.FILES['audio_file']
    noise_reduction_level = request.POST.get('noise_reduction', 'medium').strip()
    
    # Validate file size
    max_size = 700 * 1024 * 1024  # 700MB
    if uploaded_file.size > max_size:
        return render(request, 'media_converter/reduce_noise.html', {
            'error': f'File size exceeds 700MB limit. Your file is {uploaded_file.size / (1024 * 1024):.1f}MB.'
        })
    
    # Validate file type
    allowed_extensions = ['.mp3', '.wav', '.ogg', '.flac', '.aac', '.m4a', '.aiff', '.aif']
    file_ext = os.path.splitext(uploaded_file.name)[1].lower()
    
    if file_ext not in allowed_extensions:
        return render(request, 'media_converter/reduce_noise.html', {
            'error': 'Invalid file type. Please upload MP3, WAV, OGG, FLAC, AAC, M4A, or AIFF files.'
        })
    
    if noise_reduction_level not in ['low', 'medium', 'high']:
        noise_reduction_level = 'medium'
    
    # Check FFmpeg
    ffmpeg_path, ffprobe_path, error = _check_ffmpeg()
    if error:
        return render(request, 'media_converter/reduce_noise.html', {'error': error})
    
    temp_dir = None
    try:
        # Create temporary directory
        temp_dir = tempfile.mkdtemp()
        input_path = os.path.join(temp_dir, f'input{file_ext}')
        output_path = os.path.join(temp_dir, f'denoised{file_ext}')
        
        # Save uploaded file
        with open(input_path, 'wb') as f:
            for chunk in uploaded_file.chunks():
                f.write(chunk)
        
        # Noise reduction settings
        # Using FFmpeg's highpass and lowpass filters combined with afftdn (FFT denoise)
        if noise_reduction_level == 'low':
            # Light noise reduction
            filter_complex = 'highpass=f=80,lowpass=f=15000,afftdn=nr=10:nf=-25'
        elif noise_reduction_level == 'high':
            # Aggressive noise reduction
            filter_complex = 'highpass=f=100,lowpass=f=12000,afftdn=nr=20:nf=-30'
        else:  # medium
            # Balanced noise reduction
            filter_complex = 'highpass=f=90,lowpass=f=14000,afftdn=nr=15:nf=-27'
        
        # Build FFmpeg command
        # Determine output codec based on input format
        codec_map = {
            '.mp3': 'libmp3lame',
            '.wav': 'pcm_s16le',
            '.ogg': 'libvorbis',
            '.flac': 'flac',
            '.aac': 'aac',
            '.m4a': 'aac',
            '.aiff': 'pcm_s16be',
            '.aif': 'pcm_s16be',
        }
        
        format_map = {
            '.mp3': 'mp3',
            '.wav': 'wav',
            '.ogg': 'ogg',
            '.flac': 'flac',
            '.aac': 'mp4',
            '.m4a': 'mp4',
            '.aiff': 'aiff',
            '.aif': 'aiff',
        }
        
        codec = codec_map.get(file_ext, 'libmp3lame')
        output_format = format_map.get(file_ext, 'mp3')
        
        cmd = [
            ffmpeg_path,
            '-i', input_path,
            '-af', filter_complex,
            '-c:a', codec,
            '-ar', '44100',
            '-ac', '2',
        ]
        
        if output_format == 'mp3':
            cmd.extend(['-b:a', '192k', '-f', 'mp3'])
        elif output_format == 'wav':
            cmd.extend(['-sample_fmt', 's16', '-f', 'wav'])
        elif output_format == 'flac':
            cmd.extend(['-compression_level', '5', '-f', 'flac'])
        elif output_format in ['mp4', 'aac', 'm4a']:
            cmd.extend(['-b:a', '192k', '-f', 'mp4', '-movflags', '+faststart'])
        elif output_format == 'aiff':
            cmd.extend(['-sample_fmt', 's16', '-f', 'aiff'])
        else:
            cmd.extend(['-f', output_format])
        
        cmd.extend(['-y', output_path])
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        
        if result.returncode != 0 or not os.path.exists(output_path):
            error_msg = result.stderr if result.stderr else result.stdout if result.stdout else 'Unknown error'
            full_error = error_msg[:1000] if len(error_msg) > 1000 else error_msg
            if temp_dir:
                try:
                    shutil.rmtree(temp_dir)
                except (OSError, PermissionError):
                    pass
            return render(request, 'media_converter/reduce_noise.html', {
                'error': f'Noise reduction failed: {full_error}'
            })
        
        # Read output file
        with open(output_path, 'rb') as f:
            file_content = f.read()
        
        if len(file_content) == 0:
            if temp_dir:
                try:
                    shutil.rmtree(temp_dir)
                except (OSError, PermissionError):
                    pass
            return render(request, 'media_converter/reduce_noise.html', {
                'error': 'Noise reduction failed - output file is empty.'
            })
        
        # Clean up
        try:
            shutil.rmtree(temp_dir)
        except (OSError, PermissionError):
            pass
        
        # Determine content type
        content_type_map = {
            '.mp3': 'audio/mpeg',
            '.wav': 'audio/wav',
            '.ogg': 'audio/ogg',
            '.flac': 'audio/flac',
            '.aac': 'audio/aac',
            '.m4a': 'audio/mp4',
            '.aiff': 'audio/x-aiff',
            '.aif': 'audio/x-aiff',
        }
        content_type = content_type_map.get(file_ext, 'audio/mpeg')
        
        # Create response
        safe_filename = os.path.splitext(uploaded_file.name)[0] + '_denoised' + file_ext
        safe_filename = re.sub(r'[^\w\s.-]', '', safe_filename).strip()
        safe_filename = re.sub(r'[-\s]+', '-', safe_filename)
        
        response = HttpResponse(file_content, content_type=content_type)
        response['Content-Length'] = len(file_content)
        response['X-Filename'] = safe_filename
        return response
        
    except subprocess.TimeoutExpired:
        if temp_dir:
            try:
                shutil.rmtree(temp_dir)
            except (OSError, PermissionError):
                pass
        return render(request, 'media_converter/reduce_noise.html', {
            'error': 'Processing timed out. Please try again.'
        })
    except Exception as e:
        if temp_dir:
            try:
                shutil.rmtree(temp_dir)
            except (OSError, PermissionError):
                pass
        return render(request, 'media_converter/reduce_noise.html', {
            'error': f'Error processing file: {str(e)}'
        })
