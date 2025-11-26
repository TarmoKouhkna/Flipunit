import json
import re
import subprocess
import requests
import shutil
import concurrent.futures
import time
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.conf import settings
import os
from urllib.parse import urlparse

def index(request):
    """YouTube Analyzer index page"""
    return render(request, 'youtube_analyzer/index.html')

def analyzer_tool(request):
    """Video URL Analyzer Pro tool page"""
    return render(request, 'youtube_analyzer/analyzer.html')

@require_http_methods(["POST"])
def analyze_video(request):
    """Analyze YouTube video URL"""
    url = request.POST.get('url', '').strip()
    
    if not url:
        return JsonResponse({'error': 'URL is required'}, status=400)
    
    # Validate YouTube URL (supports regular videos, Shorts, and youtu.be links)
    youtube_pattern = r'(?:https?://)?(?:www\.)?(?:youtube\.com/(?:watch\?v=|shorts/|embed/)|youtu\.be/)([a-zA-Z0-9_-]{11})'
    match = re.search(youtube_pattern, url)
    
    if not match:
        return JsonResponse({'error': 'Invalid YouTube URL'}, status=400)
    
    video_id = match.group(1)
    
    try:
        # Use yt-dlp to extract video information
        result = extract_video_info(url, video_id)
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({'error': f'Error analyzing video: {str(e)}'}, status=500)

def extract_video_info(url, video_id):
    """Extract comprehensive video information using yt-dlp"""
    import tempfile
    
    # Create temporary directory for downloads
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Extract video info as JSON - FAST MODE (no subtitle download)
        # Get basic metadata first, then fetch subtitles separately if needed
        # Try multiple strategies to bypass YouTube bot detection
        
        # Check if cookies file exists (optional - for better success rate)
        cookies_path = os.path.join(settings.BASE_DIR, 'youtube_cookies.txt')
        has_cookies = os.path.exists(cookies_path)
        
        # Strategy 1: Try with iOS client (often less restricted)
        strategies = [
            {
                'name': 'ios',
                'cmd': [
                    'yt-dlp',
                    '--dump-json',
                    '--no-download',
                    '--skip-download',
                    '--no-warnings',
                    '--quiet',
                    '--no-playlist',
                    '--extractor-args', 'youtube:player_client=ios',
                    '--user-agent', 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
                ] + (['--cookies', cookies_path] if has_cookies else []) + [url]
            },
            {
                'name': 'android',
                'cmd': [
                    'yt-dlp',
                    '--dump-json',
                    '--no-download',
                    '--skip-download',
                    '--no-warnings',
                    '--quiet',
                    '--no-playlist',
                    '--extractor-args', 'youtube:player_client=android',
                    '--user-agent', 'com.google.android.youtube/19.09.37 (Linux; U; Android 11) gzip',
                ] + (['--cookies', cookies_path] if has_cookies else []) + [url]
            },
            {
                'name': 'tv_embedded',
                'cmd': [
                    'yt-dlp',
                    '--dump-json',
                    '--no-download',
                    '--skip-download',
                    '--no-warnings',
                    '--quiet',
                    '--no-playlist',
                    '--extractor-args', 'youtube:player_client=tv_embedded',
                    '--user-agent', 'Mozilla/5.0 (SMART-TV; Linux; Tizen 5.5) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/2.2 Chrome/63.0.3239.84 TV Safari/537.36',
                ] + (['--cookies', cookies_path] if has_cookies else []) + [url]
            },
            {
                'name': 'web',
                'cmd': [
                    'yt-dlp',
                    '--dump-json',
                    '--no-download',
                    '--skip-download',
                    '--no-warnings',
                    '--quiet',
                    '--no-playlist',
                    '--extractor-args', 'youtube:player_client=web',
                    '--user-agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    '--referer', 'https://www.youtube.com/',
                ] + (['--cookies', cookies_path] if has_cookies else []) + [url]
            },
            {
                'name': 'mweb',
                'cmd': [
                    'yt-dlp',
                    '--dump-json',
                    '--no-download',
                    '--skip-download',
                    '--no-warnings',
                    '--quiet',
                    '--no-playlist',
                    '--extractor-args', 'youtube:player_client=mweb',
                    '--user-agent', 'Mozilla/5.0 (Linux; Android 10; Mobile) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
                ] + (['--cookies', cookies_path] if has_cookies else []) + [url]
            }
        ]
        
        result = None
        last_error = None
        
        for strategy in strategies:
            try:
                result = subprocess.run(
                    strategy['cmd'],
                    capture_output=True,
                    text=True,
                    timeout=25
                )
                
                if result.returncode == 0:
                    break  # Success!
                else:
                    last_error = result.stderr if result.stderr else result.stdout
            except subprocess.TimeoutExpired:
                last_error = f"Timeout using {strategy['name']} client"
                continue
            except Exception as e:
                last_error = str(e)
                continue
        
        if result is None or result.returncode != 0:
            error_msg = last_error[:500] if last_error else 'Unknown error after trying all strategies'
            # Add helpful message about cookies if bot detection error
            if 'bot' in error_msg.lower() or 'sign in' in error_msg.lower():
                cookie_note = "\n\nNote: YouTube requires cookies to bypass bot detection. See youtube_analyzer/COOKIES_SETUP.md for instructions."
                error_msg = error_msg + cookie_note
            raise Exception(f"yt-dlp error: {error_msg}")
        
        video_data = json.loads(result.stdout)
        
        # Extract thumbnails - deduplicate by resolution (width x height) to avoid duplicates
        # YouTube may return the same resolution with different URLs or query parameters
        thumbnails_by_resolution = {}
        seen_urls = set()
        
        if 'thumbnails' in video_data:
            for thumb in video_data.get('thumbnails', []):
                url = thumb.get('url', '')
                width = thumb.get('width', 0)
                height = thumb.get('height', 0)
                
                # Only add if URL is valid and we have dimensions
                if url and width > 0 and height > 0:
                    # Normalize URL by removing query parameters for comparison
                    # But keep original URL for download
                    url_normalized = url.split('?')[0] if '?' in url else url
                    
                    # Use resolution as key to avoid duplicates of same size
                    resolution_key = f"{width}x{height}"
                    
                    # Only add if we haven't seen this exact URL or this resolution
                    if url not in seen_urls and resolution_key not in thumbnails_by_resolution:
                        seen_urls.add(url)
                        thumbnails_by_resolution[resolution_key] = {
                            'url': url,
                            'width': width,
                            'height': height,
                        }
        
        # Convert to list and sort by resolution (largest first)
        thumbnails = sorted(thumbnails_by_resolution.values(), key=lambda x: x['width'] * x['height'], reverse=True)
        
        # Get best thumbnail (highest resolution)
        best_thumbnail = video_data.get('thumbnail', '')
        if not best_thumbnail and thumbnails:
            best_thumbnail = thumbnails[0].get('url', '')
        elif best_thumbnail:
            # Check if best thumbnail is already in our list
            best_in_list = any(t.get('url') == best_thumbnail for t in thumbnails)
            if not best_in_list:
                # Try to find its resolution from thumbnails list or use default
                best_resolution = None
                for thumb in video_data.get('thumbnails', []):
                    if thumb.get('url') == best_thumbnail:
                        best_resolution = f"{thumb.get('width', 1280)}x{thumb.get('height', 720)}"
                        break
                
                # Only add if not already present at this resolution
                if best_resolution and best_resolution not in thumbnails_by_resolution:
                    thumbnails.insert(0, {
                        'url': best_thumbnail,
                        'width': int(best_resolution.split('x')[0]),
                        'height': int(best_resolution.split('x')[1]),
                    })
        
        # Extract formats - deduplicate by resolution to avoid showing many similar entries
        formats_dict = {}
        if 'formats' in video_data:
            for fmt in video_data.get('formats', []):
                if fmt.get('vcodec') != 'none':  # Video formats only
                    resolution = fmt.get('resolution', 'unknown')
                    fps = fmt.get('fps', 0)
                    vcodec = fmt.get('vcodec', '')
                    
                    # Use resolution as key to deduplicate (ignore minor bitrate differences)
                    # This groups all formats with the same resolution together
                    key = resolution
                    
                    # Only keep one format per resolution (prefer higher bitrate)
                    if key not in formats_dict:
                        formats_dict[key] = {
                            'format_id': fmt.get('format_id', ''),
                            'resolution': resolution,
                            'fps': fps,
                            'vcodec': vcodec,
                            'acodec': fmt.get('acodec', ''),
                            'filesize': fmt.get('filesize', 0),
                            'tbr': fmt.get('tbr', 0),  # Bitrate
                        }
                    else:
                        # Keep the one with higher bitrate or better quality
                        current_tbr = formats_dict[key]['tbr']
                        new_tbr = fmt.get('tbr', 0)
                        if new_tbr > current_tbr:
                            formats_dict[key] = {
                                'format_id': fmt.get('format_id', ''),
                                'resolution': resolution,
                                'fps': fps if fps > formats_dict[key]['fps'] else formats_dict[key]['fps'],
                                'vcodec': vcodec,
                                'acodec': fmt.get('acodec', ''),
                                'filesize': fmt.get('filesize', 0),
                                'tbr': new_tbr,
                            }
        
        # Convert to list and sort by resolution (largest first)
        def get_resolution_area(res_str):
            """Calculate resolution area for sorting"""
            try:
                if 'x' in res_str:
                    parts = res_str.split('x')
                    return int(parts[0]) * int(parts[1])
            except:
                pass
            return 0
        
        formats = sorted(formats_dict.values(), key=lambda x: get_resolution_area(x['resolution']), reverse=True)
        
        # Calculate SEO scores
        title = video_data.get('title', '')
        description = video_data.get('description', '')
        tags = video_data.get('tags', [])
        
        seo_analysis = calculate_seo_scores(title, description, tags)
        
        # Extract engagement stats
        stats = {
            'views': video_data.get('view_count', 0),
            'likes': video_data.get('like_count', 0),
            'comments': video_data.get('comment_count', 0),
        }
        
        # Channel info
        channel_info = {
            'name': video_data.get('channel', ''),
            'url': video_data.get('channel_url', ''),
            'subscriber_count': video_data.get('channel_follower_count', 0),
            'thumbnail': video_data.get('channel_thumbnail', ''),
        }
        
        # Build response
        response_data = {
            'success': True,
            'video_id': video_id,
            'basic_metadata': {
                'title': title,
                'description': description,
                'tags': tags,
                'published_date': video_data.get('upload_date', ''),
                'duration': video_data.get('duration', 0),
                'category': video_data.get('categories', ['Unknown'])[0] if video_data.get('categories') else 'Unknown',
            },
            'thumbnails': {
                'best': best_thumbnail,
                'all': thumbnails,
            },
            'seo_analysis': seo_analysis,
            'formats': formats,
            'engagement': stats,
            'channel': channel_info,
        }
        
        return response_data
        
    finally:
        # Cleanup temp directory
        try:
            shutil.rmtree(temp_dir)
        except:
            pass

def download_thumbnail(request):
    """Download thumbnail as PNG file"""
    thumbnail_url = request.GET.get('url', '')
    video_id = request.GET.get('video_id', '')
    
    if not thumbnail_url:
        return HttpResponse('Thumbnail URL is required', status=400)
    
    # Validate that URL is from YouTube (security check)
    parsed_url = urlparse(thumbnail_url)
    if 'youtube.com' not in parsed_url.netloc and 'ytimg.com' not in parsed_url.netloc and 'googleusercontent.com' not in parsed_url.netloc:
        return HttpResponse('Invalid thumbnail URL', status=400)
    
    try:
        # Fetch the thumbnail image
        response = requests.get(thumbnail_url, stream=True, timeout=10)
        response.raise_for_status()
        
        # Get the image data
        image_data = response.content
        
        # Determine filename
        filename = f'youtube-thumbnail-{video_id}.png' if video_id else 'youtube-thumbnail.png'
        
        # Create HTTP response with proper headers to force download
        http_response = HttpResponse(image_data, content_type='image/png')
        http_response['Content-Disposition'] = f'attachment; filename="{filename}"'
        http_response['Content-Length'] = len(image_data)
        
        return http_response
    except Exception as e:
        return HttpResponse(f'Error downloading thumbnail: {str(e)}', status=500)

def calculate_seo_scores(title, description, tags):
    """Calculate SEO scores and provide recommendations"""
    title_score = 0
    desc_score = 0
    
    # Title analysis (0-100)
    title_length = len(title)
    if 30 <= title_length <= 60:
        title_score += 40
    elif 20 <= title_length <= 70:
        title_score += 20
    
    # Check for power words
    power_words = ['best', 'ultimate', 'guide', 'how to', 'tutorial', 'review', 'tips', 'secrets', 'proven']
    title_lower = title.lower()
    for word in power_words:
        if word in title_lower:
            title_score += 10
            break
    
    # Check for numbers
    if re.search(r'\d+', title):
        title_score += 10
    
    # Check for question marks
    if '?' in title:
        title_score += 10
    
    title_score = min(100, title_score)
    
    # Description analysis (0-100)
    desc_length = len(description)
    if desc_length >= 200:
        desc_score += 30
    if desc_length >= 500:
        desc_score += 20
    
    # Check for keywords in description
    if description:
        desc_lower = description.lower()
        if any(tag.lower() in desc_lower for tag in tags):
            desc_score += 20
        
        # Check for links
        if 'http' in description:
            desc_score += 10
        
        # Check for timestamps
        if re.search(r'\d+:\d+', description):
            desc_score += 10
    
    desc_score = min(100, desc_score)
    
    # Tag analysis
    tag_count = len(tags)
    tag_score = min(100, tag_count * 10) if tag_count <= 10 else 100
    
    # Keyword density
    all_text = f"{title} {description} {' '.join(tags)}".lower()
    words = re.findall(r'\b\w+\b', all_text)
    word_freq = {}
    for word in words:
        if len(word) > 3:  # Ignore short words
            word_freq[word] = word_freq.get(word, 0) + 1
    
    # Find duplicate words
    duplicates = [word for word, count in word_freq.items() if count > 3]
    
    # Generate recommendations
    recommendations = []
    if title_score < 50:
        recommendations.append("Consider optimizing your title length (30-60 characters recommended)")
    if desc_score < 50:
        recommendations.append("Add a more detailed description (at least 200 characters)")
    if tag_count < 5:
        recommendations.append("Add more relevant tags (5-10 recommended)")
    if not duplicates:
        recommendations.append("Consider using key terms more consistently throughout title, description, and tags")
    
    # Competitor title suggestions
    competitor_titles = []
    if title:
        base_words = title.split()[:3]
        competitor_titles = [
            f"{' '.join(base_words)} - Complete Guide 2024",
            f"Best {base_words[0] if base_words else 'Video'} Tips & Tricks",
            f"How to {base_words[0] if base_words else 'Master This'} - Expert Tutorial",
        ]
    
    return {
        'title_score': title_score,
        'description_score': desc_score,
        'tag_score': tag_score,
        'tag_count': tag_count,
        'keyword_density': dict(sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]),
        'duplicate_words': duplicates,
        'recommendations': recommendations,
        'competitor_titles': competitor_titles,
        'estimated_difficulty': 'Medium' if title_score + desc_score > 100 else 'High',
    }
