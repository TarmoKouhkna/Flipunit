from django.shortcuts import render
from django.contrib import messages
from django.http import HttpResponse
import yt_dlp
import os
import tempfile
import re
import shutil
import subprocess

def index(request):
    """Media converters index page"""
    context = {
        'converters': [
            {
                'name': 'YouTube to MP3',
                'url': 'media_converter:youtube_to_mp3',
                'description': 'Convert YouTube videos to MP3 audio files',
                'notice': 'Please respect copyright and YouTube Terms of Service. Only convert videos you have permission to download.'
            },
            {
                'name': 'MP4 to MP3',
                'url': 'media_converter:mp4_to_mp3',
                'description': 'Extract audio from MP4 video files',
            },
            {
                'name': 'Audio Converter',
                'url': 'media_converter:audio_converter',
                'description': 'Convert between MP3, WAV, OGG, FLAC, and AAC formats',
            },
            {
                'name': 'Video to GIF',
                'url': 'media_converter:video_to_gif',
                'description': 'Convert video clips to animated GIFs',
            },
            {
                'name': 'Video Converter',
                'url': 'media_converter:video_converter',
                'description': 'Convert between MP4, AVI, MOV, MKV, and WebM formats',
            },
        ]
    }
    return render(request, 'media_converter/index.html', context)

def youtube_to_mp3(request):
    """YouTube to MP3 converter"""
    context = {
        'usage_notice': (
            "Usage Notice:\n"
            "• Only convert videos you have permission to download\n"
            "• Respect copyright laws and YouTube's Terms of Service\n"
            "• Do not download copyrighted content without authorization\n"
            "• This tool is for personal, non-commercial use only"
        )
    }
    
    if request.method == 'POST':
        # Debug: Check what we're receiving
        youtube_url = request.POST.get('youtube_url', '').strip()
        
        # Also check if it's coming through differently
        if not youtube_url:
            # Try alternative field names
            youtube_url = request.POST.get('youtube-url', '').strip()
        if not youtube_url:
            youtube_url = request.POST.get('url', '').strip()
        
        # Debug output - show what we received
        if not youtube_url:
            all_post_keys = list(request.POST.keys())
            all_post_values = {k: request.POST.getlist(k) for k in all_post_keys}
            messages.error(request, f'Please enter a YouTube URL. Received POST keys: {all_post_keys}. Check browser console for details.')
            # Also log to console via template
            context['debug_post'] = all_post_keys
            return render(request, 'media_converter/youtube_to_mp3.html', context)
        
        # Basic validation - check if it looks like a YouTube URL
        # yt-dlp will handle the actual validation and can work with many formats
        youtube_indicators = ['youtube.com', 'youtu.be', 'youtube-nocookie.com', 'youtube']
        if not any(indicator in youtube_url.lower() for indicator in youtube_indicators):
            messages.error(request, 'Please enter a valid YouTube URL.')
            return render(request, 'media_converter/youtube_to_mp3.html', context)
        
        try:
            # Create temporary directory for downloads
            temp_dir = tempfile.mkdtemp()
            output_path = os.path.join(temp_dir, '%(title)s.%(ext)s')
            
            # Find FFmpeg and FFprobe paths
            ffmpeg_path = shutil.which('ffmpeg') or '/usr/local/bin/ffmpeg'
            ffprobe_path = shutil.which('ffprobe') or '/usr/local/bin/ffprobe'
            
            # Verify FFmpeg exists
            if not os.path.exists(ffmpeg_path):
                messages.error(request, f'FFmpeg not found at {ffmpeg_path}. Please ensure FFmpeg is installed.')
                return render(request, 'media_converter/youtube_to_mp3.html', context)
            
            # Get FFmpeg directory
            ffmpeg_dir = os.path.dirname(ffmpeg_path)
            
            # Update PATH environment variable to include FFmpeg directory
            original_path = os.environ.get('PATH', '')
            if ffmpeg_dir not in original_path:
                os.environ['PATH'] = f"{ffmpeg_dir}:{original_path}"
            
            # Configure yt-dlp options for faster processing
            ydl_opts = {
                'format': 'bestaudio[ext=m4a]/bestaudio/best',  # Prefer m4a for faster processing
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'outtmpl': output_path,
                'quiet': True,
                'no_warnings': True,
                'ffmpeg_location': ffmpeg_dir,
                'noplaylist': True,  # Don't download playlists
                'extract_flat': False,
                # Optimize for speed
                'concurrent_fragments': 4,  # Download multiple fragments in parallel
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Extract video info
                info = ydl.extract_info(youtube_url, download=False)
                video_title = info.get('title', 'video')
                
                # Download and convert
                ydl.download([youtube_url])
                
                # Find the downloaded file
                downloaded_files = [f for f in os.listdir(temp_dir) if f.endswith('.mp3')]
                
                if not downloaded_files:
                    messages.error(request, 'Failed to convert video. Please try again.')
                    return render(request, 'media_converter/youtube_to_mp3.html', context)
                
                mp3_file_path = os.path.join(temp_dir, downloaded_files[0])
                
                # Read the file
                with open(mp3_file_path, 'rb') as f:
                    file_content = f.read()
                
                # Clean up temporary files
                try:
                    os.remove(mp3_file_path)
                    os.rmdir(temp_dir)
                except OSError:
                    # If cleanup fails, try to remove entire directory
                    try:
                        shutil.rmtree(temp_dir)
                    except:
                        pass
                
                # Sanitize filename
                safe_filename = re.sub(r'[^\w\s-]', '', video_title).strip()
                safe_filename = re.sub(r'[-\s]+', '-', safe_filename)
                if not safe_filename:
                    safe_filename = 'youtube_audio'
                
                # Create HTTP response
                # Note: We don't set Content-Disposition here to prevent browser auto-download
                # JavaScript will handle the download programmatically
                response = HttpResponse(file_content, content_type='audio/mpeg')
                response['Content-Length'] = len(file_content)
                # Add custom header with filename for JavaScript to use
                response['X-Filename'] = f'{safe_filename}.mp3'
                response['X-Content-Type'] = 'audio/mpeg'
                
                return response
                
        except yt_dlp.utils.DownloadError as e:
            error_msg = str(e)
            if 'ffmpeg' in error_msg.lower() or 'ffprobe' in error_msg.lower():
                messages.error(request, 'FFmpeg is required for audio conversion. Please install FFmpeg on your system.')
            else:
                messages.error(request, f'Error downloading video: {error_msg}. Please check the URL and try again.')
        except Exception as e:
            error_msg = str(e)
            # Clean up temp directory on error
            try:
                if 'temp_dir' in locals():
                    shutil.rmtree(temp_dir)
            except:
                pass
            messages.error(request, f'An error occurred: {error_msg}. Please try again.')
    
    return render(request, 'media_converter/youtube_to_mp3.html', context)

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
    
    # Validate file type
    allowed_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.wmv']
    file_ext = os.path.splitext(uploaded_file.name)[1].lower()
    
    if file_ext not in allowed_extensions:
        return render(request, 'media_converter/mp4_to_mp3.html', {
            'error': 'Invalid file type. Please upload MP4, AVI, MOV, MKV, WebM, FLV, or WMV files.'
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
            return render(request, 'media_converter/mp4_to_mp3.html', {
                'error': f'Conversion failed: {result.stderr}'
            })
        
        # Read output file
        with open(output_path, 'rb') as f:
            file_content = f.read()
        
        # Clean up
        try:
            shutil.rmtree(temp_dir)
        except:
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
            except:
                pass
        return render(request, 'media_converter/mp4_to_mp3.html', {
            'error': f'Error processing file: {str(e)}'
        })

def audio_converter(request):
    """Convert between audio formats"""
    if request.method != 'POST':
        return render(request, 'media_converter/audio_converter.html')
    
    if 'audio_file' not in request.FILES:
        return render(request, 'media_converter/audio_converter.html', {
            'error': 'Please upload an audio file.'
        })
    
    uploaded_file = request.FILES['audio_file']
    output_format = request.POST.get('output_format', 'mp3').lower()
    
    # Validate file type
    allowed_extensions = ['.mp3', '.wav', '.ogg', '.flac', '.aac', '.m4a']
    file_ext = os.path.splitext(uploaded_file.name)[1].lower()
    
    if file_ext not in allowed_extensions:
        return render(request, 'media_converter/audio_converter.html', {
            'error': 'Invalid file type. Please upload MP3, WAV, OGG, FLAC, or AAC files.'
        })
    
    if output_format not in ['mp3', 'wav', 'ogg', 'flac', 'aac']:
        return render(request, 'media_converter/audio_converter.html', {
            'error': 'Invalid output format selected.'
        })
    
    # Check FFmpeg
    ffmpeg_path, ffprobe_path, error = _check_ffmpeg()
    if error:
        return render(request, 'media_converter/audio_converter.html', {'error': error})
    
    temp_dir = None
    try:
        # Create temporary directory
        temp_dir = tempfile.mkdtemp()
        input_path = os.path.join(temp_dir, f'input{file_ext}')
        output_ext = output_format if output_format != 'aac' else 'm4a'
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
        }
        
        cmd = [
            ffmpeg_path,
            '-i', input_path,
            '-acodec', codec_map[output_format],
            '-y',
            output_path
        ]
        
        # Add quality settings for lossy formats
        if output_format in ['mp3', 'ogg', 'aac']:
            cmd.insert(-1, '-ab')
            cmd.insert(-1, '192k')
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if not os.path.exists(output_path):
            return render(request, 'media_converter/audio_converter.html', {
                'error': f'Conversion failed: {result.stderr}'
            })
        
        # Read output file
        with open(output_path, 'rb') as f:
            file_content = f.read()
        
        # Clean up
        try:
            shutil.rmtree(temp_dir)
        except:
            pass
        
        # Determine content type
        content_type_map = {
            'mp3': 'audio/mpeg',
            'wav': 'audio/wav',
            'ogg': 'audio/ogg',
            'flac': 'audio/flac',
            'aac': 'audio/aac',
        }
        
        # Create response
        # Set Content-Disposition to inline to prevent browser auto-download
        # JavaScript will handle the download programmatically to keep page responsive
        safe_filename = os.path.splitext(uploaded_file.name)[0] + f'.{output_ext}'
        safe_filename = re.sub(r'[^\w\s-]', '', safe_filename).strip()
        safe_filename = re.sub(r'[-\s]+', '-', safe_filename)
        
        response = HttpResponse(file_content, content_type=content_type_map[output_format])
        response['Content-Length'] = len(file_content)
        response['Content-Disposition'] = 'inline'  # Prevent browser auto-download
        response['X-Filename'] = safe_filename
        return response
        
    except Exception as e:
        if temp_dir:
            try:
                shutil.rmtree(temp_dir)
            except:
                pass
        return render(request, 'media_converter/audio_converter.html', {
            'error': f'Error processing file: {str(e)}'
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
    allowed_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.wmv']
    file_ext = os.path.splitext(uploaded_file.name)[1].lower()
    
    if file_ext not in allowed_extensions:
        return render(request, 'media_converter/video_to_gif.html', {
            'error': 'Invalid file type. Please upload MP4, AVI, MOV, MKV, WebM, FLV, or WMV files.'
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
                except:
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
                except:
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
        except:
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
            except:
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
    
    # Debug logging
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f'Video conversion started: {uploaded_file.name}, format: {output_format}, size: {uploaded_file.size} bytes')
    
    # Validate file type
    allowed_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.wmv']
    file_ext = os.path.splitext(uploaded_file.name)[1].lower()
    
    if file_ext not in allowed_extensions:
        return render(request, 'media_converter/video_converter.html', {
            'error': 'Invalid file type. Please upload MP4, AVI, MOV, MKV, WebM, FLV, or WMV files.'
        })
    
    if output_format not in ['mp4', 'avi', 'mov', 'mkv', 'webm']:
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
                except:
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
                except:
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
                except:
                    pass
            return render(request, 'media_converter/video_converter.html', {
                'error': 'Conversion failed - output file is empty. The video file may be corrupted or in an unsupported format.'
            })
        
        # Clean up
        try:
            shutil.rmtree(temp_dir)
        except:
            pass
        
        # Determine content type
        content_type_map = {
            'mp4': 'video/mp4',
            'avi': 'video/x-msvideo',
            'mov': 'video/quicktime',
            'mkv': 'video/x-matroska',
            'webm': 'video/webm',
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
            except:
                pass
        return render(request, 'media_converter/video_converter.html', {
            'error': 'Video conversion timed out. The video might be too long or complex for server processing. Try a smaller file.'
        })
    except Exception as e:
        if temp_dir:
            try:
                shutil.rmtree(temp_dir)
            except:
                pass
        return render(request, 'media_converter/video_converter.html', {
            'error': f'Error processing file: {str(e)}'
        })
