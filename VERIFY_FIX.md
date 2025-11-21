# Verify Audio Converter Fix is on Server

## Check if the fix is on the server:

**On your server, run:**

```bash
cd /opt/flipunit
grep -A 5 "Sanitize base name first" media_converter/views.py
```

If you see the new code, it's there. If not, you need to upload the file.

**Also check the exact code around line 557-560:**

```bash
sed -n '554,565p' media_converter/views.py
```

This should show:
- Line 557: `base_name = os.path.splitext(uploaded_file.name)[0]`
- Line 558-560: The new sanitization code (sanitizing base_name first, then adding extension)
- Line 561: `safe_filename = f'{base_name}.{output_ext}'`

**If the code is different, you need to:**
1. Upload the updated `media_converter/views.py` file
2. Rebuild the container: `docker-compose down && docker-compose build web && docker-compose up -d`

**Also check the template:**

```bash
grep -A 5 "Extracted extension" templates/media_converter/audio_converter.html
```

If you don't see this, upload the updated template too.






