# YouTube Cookies Setup for Video Analyzer

YouTube requires cookies to bypass bot detection. To enable the YouTube Analyzer to work reliably, you need to export cookies from your browser.

## Quick Setup (Recommended)

### Option 1: Using Browser Extension (Easiest) - RECOMMENDED FOR VPS

1. **On your local computer:**
   - Install browser extension:
     - Chrome/Edge: "Get cookies.txt LOCALLY" 
     - Firefox: "cookies.txt"
   - Go to https://www.youtube.com and make sure you're logged in
   - Click the extension icon and export cookies
   - Save as `youtube_cookies.txt`

2. **Upload to VPS:**
   ```bash
   scp youtube_cookies.txt ubuntu@217.146.78.140:/opt/flipunit/
   ```

3. **On VPS, verify:**
   ```bash
   ls -la /opt/flipunit/youtube_cookies.txt
   ```

### Option 2: Using yt-dlp Command (Local Development Only)

On your local machine where you have a browser:
```bash
yt-dlp --cookies-from-browser chrome --dump-json https://www.youtube.com/watch?v=dQw4w9WgXcQ
```

This will use browser cookies automatically. For VPS, you need to export and upload the file.

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

