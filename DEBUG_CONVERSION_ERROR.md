# Debugging Audio Converter Error

The conversion is now reaching the server (CSRF/ALLOWED_HOSTS fixed!), but failing during processing.

## Check Server Logs

On your server, run:
```bash
cd /opt/flipunit
docker-compose logs --tail 50 web | grep -i -A 10 -B 5 "audio\|error\|exception\|traceback"
```

Or check the full recent logs:
```bash
docker-compose logs --tail 100 web
```

## Common Issues

1. **FFmpeg not found or not working**
   - Check: `docker-compose exec web ffmpeg -version`
   - Should show FFmpeg version

2. **File permissions**
   - Check: `docker-compose exec web ls -la /tmp`
   - Temp directory should be writable

3. **Disk space**
   - Check: `docker-compose exec web df -h`
   - Need free space for temp files

4. **Python error in conversion code**
   - Check logs for Python traceback
   - Look for specific error messages

## What to Look For

In the logs, look for:
- Python exceptions/tracebacks
- FFmpeg errors
- File permission errors
- "Conversion failed" messages with details

Share the error message from the logs and we can fix it!








