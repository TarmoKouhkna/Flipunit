# Nginx Sitemap Fix for zone.ee VPS

## The Problem
Your sitemap.xml is being served with a `noindex` header or wrapped in HTML because Nginx is proxying it to Django, which may be adding security headers or Django is serving it incorrectly.

## The Solution

### Option 1: Serve Static Sitemap (Recommended - Fastest Fix)

Add this location block to your Nginx config **BEFORE** the main `location /` block:

```nginx
server {
    listen 80;
    server_name flipunit.eu www.flipunit.eu;
    
    # Allow file uploads up to 700MB
    client_max_body_size 700M;
    
    # Serve sitemap.xml directly as static file with correct content type
    location = /sitemap.xml {
        alias /opt/flipunit/sitemap.xml;
        default_type application/xml;
        add_header Content-Type "application/xml; charset=utf-8";
        # Explicitly remove any noindex headers
        add_header X-Robots-Tag "";
        access_log off;
    }
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Increase timeouts for large file uploads
        proxy_read_timeout 300s;
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
    }
    
    location /static/ {
        alias /opt/flipunit/staticfiles/;
    }
    
    location /media/ {
        alias /opt/flipunit/media/;
    }
}
```

**Important:** The `location = /sitemap.xml` block MUST come BEFORE `location /` so Nginx matches it first.

### Steps to Apply:

1. **Edit Nginx config:**
   ```bash
   sudo nano /etc/nginx/sites-available/flipunit.eu
   ```

2. **Add the sitemap location block** (before `location /`)

3. **Test Nginx config:**
   ```bash
   sudo nginx -t
   ```

4. **Reload Nginx:**
   ```bash
   sudo systemctl reload nginx
   ```

5. **Create the static sitemap file** (use the fix_sitemap.sh script or manually):
   ```bash
   # Download from xml-sitemaps.com
   curl -s "YOUR_SITEMAP_URL" > /opt/flipunit/sitemap.xml
   chmod 644 /opt/flipunit/sitemap.xml
   ```

6. **Test:**
   ```bash
   curl -I https://flipunit.eu/sitemap.xml
   ```
   
   Should show:
   - `Content-Type: application/xml; charset=utf-8`
   - NO `X-Robots-Tag: noindex`

### Option 2: Fix Django Sitemap View (Alternative)

If you prefer to keep using Django's dynamic sitemap, you can modify the URL pattern to ensure correct content type:

In `flipunit/urls.py`, change:
```python
path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
```

To:
```python
from django.http import HttpResponse
from django.contrib.sitemaps import views as sitemap_views

def sitemap_view(request):
    response = sitemap_views.sitemap(request, sitemaps)
    response['Content-Type'] = 'application/xml; charset=utf-8'
    # Remove any noindex headers
    if 'X-Robots-Tag' in response:
        del response['X-Robots-Tag']
    return response

# Then in urlpatterns:
path('sitemap.xml', sitemap_view, name='django.contrib.sitemaps.views.sitemap'),
```

However, **Option 1 (static file) is recommended** because:
- ✅ Faster (no Django processing)
- ✅ More reliable (no middleware interference)
- ✅ Better for SEO (served directly by Nginx)
- ✅ Easier to debug

## Quick Test Commands

```bash
# Check if sitemap is accessible
curl https://flipunit.eu/sitemap.xml | head -5

# Check headers (should NOT have noindex)
curl -I https://flipunit.eu/sitemap.xml | grep -i "robots\|content-type"

# Should see: Content-Type: application/xml
# Should NOT see: X-Robots-Tag: noindex
```

## After Fixing

1. ✅ Test: https://flipunit.eu/sitemap.xml (should show pure XML)
2. ✅ Google Search Console → Sitemaps → Remove old → Add `sitemap.xml` → Submit
3. ✅ Wait 1-2 minutes → Should show green "Success"




