# Fix Nginx Config - Quick Instructions

Your Nginx config has the sitemap block, but needs proper indentation. Here's what to do:

## In nano editor (where you are now):

1. **Fix the indentation** - Make sure `location /` has 4 spaces at the start (like other location blocks)

2. **Complete the Content-Type line** - Line 11 should be:
   ```
   add_header Content-Type "application/xml; charset=utf-8";
   ```

3. **Save and exit:**
   - Press `Ctrl+O` (to save)
   - Press `Enter` (confirm filename)
   - Press `Ctrl+X` (to exit)

4. **Test the config:**
   ```bash
   sudo nginx -t
   ```

5. **If test passes, reload:**
   ```bash
   sudo systemctl reload nginx
   ```

6. **Verify sitemap works:**
   ```bash
   curl https://flipunit.eu/sitemap.xml | head -5
   ```

## Quick Fix Commands (if you want to exit nano and fix it):

```bash
# Exit nano first (Ctrl+X, then N to not save)

# Then run this to fix indentation:
sudo sed -i 's/^location \//    location \//' /etc/nginx/sites-available/flipunit.eu

# Test
sudo nginx -t

# If OK, reload
sudo systemctl reload nginx
```

## Or copy-paste the corrected config:

The corrected config is in `nginx_config_fixed.conf` - you can reference it, but make sure to keep your SSL certificate paths (lines 36-40) as they are.


