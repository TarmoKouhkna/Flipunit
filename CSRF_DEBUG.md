# CSRF Still Failing - Debug Steps

## Problem
CSRF verification is still failing even after adding CSRF_TRUSTED_ORIGINS.

## Quick Check on Server

Run these commands on your server to verify the settings:

### 1. Check if CSRF_TRUSTED_ORIGINS is in settings.py
```bash
cd /opt/flipunit
grep -A 10 "CSRF_TRUSTED_ORIGINS" flipunit/settings.py
```

### 2. Check if environment variable is set
```bash
docker-compose exec web env | grep CSRF
```

### 3. Test Django settings directly
```bash
docker-compose exec web python manage.py shell
```

Then in the Python shell:
```python
from django.conf import settings
print("ALLOWED_HOSTS:", settings.ALLOWED_HOSTS)
print("CSRF_TRUSTED_ORIGINS:", settings.CSRF_TRUSTED_ORIGINS)
exit()
```

### 4. Check for Python syntax errors
```bash
docker-compose exec web python -m py_compile flipunit/settings.py
```

If there's a syntax error, it will show it.

## Possible Issues

1. **Settings file has syntax error** - Python can't load it
2. **Environment variable not being read** - docker-compose not passing it
3. **Settings not reloading** - Need to rebuild container
4. **Indentation error** - Python syntax issue

## Quick Fix: Rebuild Container

If settings aren't loading, try rebuilding:
```bash
cd /opt/flipunit
docker-compose down
docker-compose up -d --build
```

This will rebuild the container with the new settings.

