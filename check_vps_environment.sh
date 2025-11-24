#!/bin/bash

# Script to check VPS environment for YouTube to MP3 converter
# Run this on your VPS server: ssh ubuntu@your-server 'bash -s' < check_vps_environment.sh

echo "=== Checking VPS Environment for YouTube to MP3 Converter ==="
echo ""

# Check if we're in Docker
if [ -f /.dockerenv ]; then
    echo "✓ Running inside Docker container"
else
    echo "⚠ Running on host (not in Docker)"
fi
echo ""

# Check Python version
echo "Python version:"
python3 --version
echo ""

# Check yt-dlp installation
echo "yt-dlp version:"
python3 -c "import yt_dlp; print(yt_dlp.version.__version__)" 2>/dev/null || echo "❌ yt-dlp not installed or error"
echo ""

# Check FFmpeg
echo "FFmpeg version:"
ffmpeg -version 2>/dev/null | head -1 || echo "❌ FFmpeg not found"
echo ""

# Check FFmpeg location
echo "FFmpeg location:"
which ffmpeg || echo "❌ FFmpeg not in PATH"
echo ""

# Check if FFmpeg is accessible
FFMPEG_PATH=$(which ffmpeg || echo "/usr/bin/ffmpeg")
if [ -f "$FFMPEG_PATH" ]; then
    echo "✓ FFmpeg found at: $FFMPEG_PATH"
    ls -lh "$FFMPEG_PATH"
else
    echo "❌ FFmpeg not found at: $FFMPEG_PATH"
fi
echo ""

# Test yt-dlp with a simple command
echo "Testing yt-dlp (dry run on a test video):"
python3 -c "
import yt_dlp
ydl_opts = {'quiet': True, 'no_warnings': True}
try:
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        # Just check if we can initialize
        print('✓ yt-dlp initialized successfully')
        # Try to get info (this will fail but shows if bot detection is working)
        try:
            info = ydl.extract_info('https://www.youtube.com/watch?v=dQw4w9WgXcQ', download=False)
            print('✓ Successfully extracted video info (no bot detection)')
        except Exception as e:
            error_msg = str(e)
            if 'bot' in error_msg.lower() or 'sign in' in error_msg.lower():
                print('❌ YouTube bot detection triggered:', error_msg[:200])
            else:
                print('⚠ Error (not bot detection):', error_msg[:200])
except Exception as e:
    print('❌ yt-dlp error:', str(e)[:200])
"
echo ""

# Check network connectivity
echo "Network connectivity to YouTube:"
curl -I https://www.youtube.com 2>&1 | head -3 || echo "❌ Cannot reach YouTube"
echo ""

# Check Docker container (if running)
if command -v docker &> /dev/null; then
    echo "Docker containers:"
    docker ps --format "table {{.Names}}\t{{.Status}}" | grep -E "NAME|flipunit" || echo "No flipunit containers running"
    echo ""
    
    echo "Checking inside web container:"
    docker exec flipunit-web python3 --version 2>/dev/null || echo "Cannot exec into container"
    docker exec flipunit-web which ffmpeg 2>/dev/null || echo "FFmpeg not found in container"
    docker exec flipunit-web python3 -c "import yt_dlp; print(yt_dlp.version.__version__)" 2>/dev/null || echo "yt-dlp error in container"
fi

echo ""
echo "=== Check Complete ==="

