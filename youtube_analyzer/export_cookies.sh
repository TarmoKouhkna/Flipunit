#!/bin/bash
# Helper script to export YouTube cookies using yt-dlp
# This script helps you export cookies from your browser to use with the YouTube Analyzer

echo "YouTube Cookies Exporter for FlipUnit"
echo "======================================"
echo ""
echo "This script will help you export cookies from your browser."
echo ""

# Check if yt-dlp is installed
if ! command -v yt-dlp &> /dev/null; then
    echo "Error: yt-dlp is not installed."
    echo "Install it with: pip install yt-dlp"
    exit 1
fi

echo "Available browsers:"
echo "1. Chrome"
echo "2. Firefox"
echo "3. Edge"
echo "4. Safari (macOS only)"
echo "5. Opera"
echo ""
read -p "Select browser (1-5): " browser_choice

case $browser_choice in
    1) browser="chrome" ;;
    2) browser="firefox" ;;
    3) browser="edge" ;;
    4) browser="safari" ;;
    5) browser="opera" ;;
    *) echo "Invalid choice"; exit 1 ;;
esac

echo ""
echo "Exporting cookies from $browser..."
echo "Make sure you're logged into YouTube in your browser!"
echo ""

# Test with a simple YouTube URL
yt-dlp --cookies-from-browser "$browser" --dump-json "https://www.youtube.com/watch?v=dQw4w9WgXcQ" > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo "✓ Successfully accessed YouTube with $browser cookies"
    echo ""
    echo "The YouTube Analyzer will now use cookies from $browser automatically."
    echo ""
    echo "Note: Cookies are stored in your browser's profile."
    echo "The analyzer will access them directly - no file needed!"
else
    echo "✗ Failed to access YouTube with $browser cookies"
    echo ""
    echo "Troubleshooting:"
    echo "1. Make sure you're logged into YouTube in $browser"
    echo "2. Try closing and reopening your browser"
    echo "3. Try a different browser"
    exit 1
fi

