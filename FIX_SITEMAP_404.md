# Fix Sitemap 404 Error

## The Problem
You're getting a 404 error because nginx is configured to serve `/opt/flipunit/sitemap.xml` as a static file, but that file doesn't exist.

## Solution: Let Django Serve the Sitemap (Recommended)

Django is already configured to serve the sitemap dynamically at `/sitemap.xml`. This is better because it's always up-to-date.

### On your VPS, run:

```bash
# 1. Edit nginx config
sudo nano /etc/nginx/sites-available/flipunit.eu
```

### 2. Find and REMOVE or COMMENT OUT this block:

```nginx
    # Serve sitemap.xml directly as static file
    location = /sitemap.xml {
        alias /opt/flipunit/sitemap.xml;
        default_type application/xml;
        add_header Content-Type "application/xml; charset=utf-8";
        access_log off;
    }
```

**OR** comment it out by adding `#` at the start of each line:

```nginx
    # # Serve sitemap.xml directly as static file
    # location = /sitemap.xml {
    #     alias /opt/flipunit/sitemap.xml;
    #     default_type application/xml;
    #     add_header Content-Type "application/xml; charset=utf-8";
    #     access_log off;
    # }
```

### 3. Test and reload nginx:

```bash
sudo nginx -t
sudo systemctl reload nginx
```

### 4. Test the sitemap:

```bash
curl https://flipunit.eu/sitemap.xml | head -10
```

You should see XML content starting with `<?xml version="1.0" encoding="UTF-8"?>`

---

## Alternative: Generate Static File (If you prefer)

If you want to keep the nginx static file approach:

```bash
# Generate sitemap using Django
docker exec flipunit-web python manage.py generate_sitemap --output /app/sitemap.xml

# Copy it out of container
docker cp flipunit-web:/app/sitemap.xml /opt/flipunit/sitemap.xml

# Set permissions
chmod 644 /opt/flipunit/sitemap.xml

# Test
curl https://flipunit.eu/sitemap.xml | head -10
```

---

**Recommended:** Use the Django dynamic approach (Solution 1) - it's simpler and always up-to-date! ✅








