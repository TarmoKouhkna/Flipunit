from django.shortcuts import render
from django.contrib import messages
from django.http import HttpResponse
import yt_dlp
import os
import tempfile
import re
import shutil

def index(request):
    """Media converters index page"""
    context = {
        'converters': [
            {
                'name': 'YouTube to MP3',
                'url': 'youtube-to-mp3',
                'description': 'Convert YouTube videos to MP3 audio files',
                'notice': 'Please respect copyright and YouTube Terms of Service. Only convert videos you have permission to download.'
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
