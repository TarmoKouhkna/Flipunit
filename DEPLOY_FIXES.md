# Deploy Fixes to Server

## Problem
The container restarted but CSRF errors are still happening. This means the updated `settings.py` file with `CSRF_TRUSTED_ORIGINS` is not on the server yet.

## Solution

You need to upload the updated `settings.py` file to your server.

### Step 1: Upload the updated settings.py

**Option A: Using SCP (from your local machine)**
```bash
scp flipunit/settings.py ubuntu@217.146.78.140:/opt/flipunit/flipunit/settings.py
```

**Option B: Using Git (if you have a repo)**
```bash
# On server
cd /opt/flipunit
git pull
```

**Option C: Manual copy via SSH**
```bash
# SSH into server
ssh ubuntu@217.146.78.140

# Edit the file
cd /opt/flipunit
nano flipunit/settings.py
```

Then add this code after the ALLOWED_HOSTS section (around line 40):

```python
# CSRF Trusted Origins - required for HTTPS requests
CSRF_TRUSTED_ORIGINS = []
if os.environ.get('CSRF_TRUSTED_ORIGINS'):
    CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in os.environ.get('CSRF_TRUSTED_ORIGINS').split(',')]
else:
    # Default trusted origins
    CSRF_TRUSTED_ORIGINS = [
        'https://flipunit.eu',
        'https://www.flipunit.eu',
        'http://flipunit.eu',  # For development/testing
        'http://www.flipunit.eu',  # For development/testing
    ]
```

### Step 2: Restart the container

```bash
cd /opt/flipunit
docker-compose restart web
```

### Step 3: Verify

```bash
docker-compose logs -f web
```

You should **NOT** see:
- ❌ `Origin checking failed - https://flipunit.eu`
- ❌ `Invalid HTTP_HOST header: '217.146.78.140'` (after restart)

---

## Quick Check: Verify settings.py has the fix

On your server, run:
```bash
cd /opt/flipunit
grep -A 10 "CSRF_TRUSTED_ORIGINS" flipunit/settings.py
```

If you see the CSRF_TRUSTED_ORIGINS configuration, it's there. If not, you need to add it.

