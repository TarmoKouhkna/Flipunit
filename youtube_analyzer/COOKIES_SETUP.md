# YouTube Cookies Setup for Video Analyzer

YouTube requires cookies to bypass bot detection. To enable the YouTube Analyzer to work reliably, you need to export cookies from your browser.

## Quick Setup (Recommended)

### Option 1: Using Browser Extension (Easiest)

1. Install a browser extension like "Get cookies.txt LOCALLY" for Chrome/Edge or "cookies.txt" for Firefox
2. Go to https://www.youtube.com
3. Make sure you're logged in (optional but recommended)
4. Click the extension icon and export cookies
5. Save the file as `youtube_cookies.txt` in the project root directory (`/opt/flipunit/youtube_cookies.txt` on VPS)

### Option 2: Using yt-dlp Command

On your local machine:
```bash
yt-dlp --cookies-from-browser chrome https://www.youtube.com/watch?v=dQw4w9WgXcQ --dump-json
```

This will create a cookies file. Copy it to the server.

### Option 3: Manual Export (Advanced)

1. Use browser developer tools to export cookies
2. Format them as Netscape cookie format
3. Save as `youtube_cookies.txt`

## File Location

- **Local development**: `/Users/tarmokouhkna/Documents/Flipunit/youtube_cookies.txt`
- **VPS production**: `/opt/flipunit/youtube_cookies.txt`

## Important Notes

- The cookies file is optional - the analyzer will try multiple strategies without it
- Cookies expire, so you may need to refresh them periodically
- **DO NOT commit cookies.txt to git** - it's already in .gitignore
- Cookies should be updated every few weeks for best results

## Testing

After adding cookies, test with:
```bash
yt-dlp --cookies youtube_cookies.txt --dump-json https://www.youtube.com/watch?v=dQw4w9WgXcQ
```

If it works, the YouTube Analyzer should work too!

