# Audio Converter Filename Issue

## Problem
Converting MP3 to FLAC results in a file with `.mp3` extension instead of `.flac`, and the file doesn't play.

## Root Cause
The JavaScript code on line 281 of `audio_converter.html` has a fallback:
```javascript
const fileExt = filename.match(/\.[^/.]+$/) || '.mp3';
```

If the regex fails to extract the extension, it defaults to `.mp3`.

## Debug Steps

1. **Check server logs** to see what filename is being sent:
   ```bash
   docker-compose logs web | grep -i "Generated filename\|Response filename" | tail -20
   ```

2. **Check browser console** (F12) to see what filename is received in the JSON response

3. **The issue might be:**
   - Server is sending filename without extension
   - Regex is failing to extract extension
   - Filename format is unexpected

## Fix

The JavaScript should preserve the original extension from the server's filename. The regex should work, but we need to verify what the server is actually sending.








