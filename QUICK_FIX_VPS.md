# Quick Fix for VPS - Copy Management Command Files

The management command files need to be copied into the Docker container. Here are the commands to run on your VPS:

## Option 1: Copy Files into Container (Quick - No Rebuild)

Run these commands on your VPS:

```bash
# Create the management directory structure in the container
docker exec flipunit-web mkdir -p /app/flipunit/management/commands

# Copy the __init__.py files
docker exec flipunit-web sh -c "echo '# Django management package' > /app/flipunit/management/__init__.py"
docker exec flipunit-web sh -c "echo '# Django management commands package' > /app/flipunit/management/commands/__init__.py"

# Copy the generate_sitemap.py command
# (You'll need to copy-paste the file content or use docker cp if you upload it)
```

**OR** if you have the files on the VPS already:

```bash
# Copy from VPS host to container
docker cp /opt/flipunit/flipunit/management/commands/generate_sitemap.py flipunit-web:/app/flipunit/management/commands/generate_sitemap.py
docker cp /opt/flipunit/flipunit/management/__init__.py flipunit-web:/app/flipunit/management/__init__.py
docker cp /opt/flipunit/flipunit/management/commands/__init__.py flipunit-web:/app/flipunit/management/commands/__init__.py

# Also need to update settings.py to include 'flipunit' in INSTALLED_APPS
docker exec flipunit-web sed -i "s/INSTALLED_APPS = \[/INSTALLED_APPS = [\n    'flipunit',  # Main project app (needed for management commands)/" /app/flipunit/settings.py
```

## Option 2: Use Django's Built-in Sitemap View (EASIEST - No Files Needed)

This method uses Django's existing sitemap view to generate the file:

```bash
# On your VPS, run:
curl -s https://flipunit.eu/sitemap.xml > /opt/flipunit/sitemap.xml
chmod 644 /opt/flipunit/sitemap.xml

# Verify it's valid XML
head -1 /opt/flipunit/sitemap.xml
```

Then update Nginx config (see below).

## Option 3: Use External Generator (Also Easy)

1. Go to https://www.xml-sitemaps.com
2. Enter: flipunit.eu
3. Generate sitemap
4. Download to VPS:
```bash
curl -s "YOUR_DOWNLOAD_URL_HERE" > /opt/flipunit/sitemap.xml
chmod 644 /opt/flipunit/sitemap.xml
```

## Update Nginx Config

After you have the sitemap.xml file, update Nginx:

```bash
sudo nano /etc/nginx/sites-available/flipunit.eu
```

Add this block **BEFORE** `location /`:

```nginx
    # Serve sitemap.xml directly as static file
    location = /sitemap.xml {
        alias /opt/flipunit/sitemap.xml;
        default_type application/xml;
        add_header Content-Type "application/xml; charset=utf-8";
        access_log off;
    }
```

Then:
```bash
sudo nginx -t
sudo systemctl reload nginx
```

## Verify

```bash
curl https://flipunit.eu/sitemap.xml | head -5
```

Should show pure XML starting with `<?xml version="1.0"`.


