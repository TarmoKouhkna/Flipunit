# 🔴 CRITICAL FIX: Server Configuration Issues

## Problems Found in Server Logs

### 1. **DisallowedHost Error**
```
Invalid HTTP_HOST header: '217.146.78.140'. You may need to add '217.146.78.140' to ALLOWED_HOSTS.
```
**Cause:** Requests coming directly to the IP address are being rejected.

### 2. **CSRF Origin Check Failed**
```
Forbidden (Origin checking failed - https://flipunit.eu does not match any trusted origins.)
```
**Cause:** CSRF_TRUSTED_ORIGINS not configured, so HTTPS requests are being rejected.

---

## ✅ Fixes Applied

### 1. Added IP Address to ALLOWED_HOSTS
- **File:** `flipunit/settings.py`
- **Change:** Added `'217.146.78.140'` to default ALLOWED_HOSTS
- **Why:** Allows requests that come directly to the IP address (some bots, health checks, etc.)

### 2. Added CSRF_TRUSTED_ORIGINS
- **File:** `flipunit/settings.py`
- **Change:** Added CSRF_TRUSTED_ORIGINS configuration
- **Default values:**
  - `https://flipunit.eu`
  - `https://www.flipunit.eu`
  - `http://flipunit.eu` (for development)
  - `http://www.flipunit.eu` (for development)
- **Why:** Required for Django to accept POST requests from HTTPS origins

### 3. Updated docker-compose.yml
- **File:** `docker-compose.yml`
- **Change:** Added IP address to default ALLOWED_HOSTS and added CSRF_TRUSTED_ORIGINS environment variable
- **Why:** Makes it configurable via environment variables

---

## 🚀 Deployment Steps

### Option 1: Quick Fix (Update .env file on server)

1. **SSH into your server:**
   ```bash
   ssh ubuntu@your-server
   ```

2. **Edit the .env file:**
   ```bash
   cd /opt/flipunit
   nano .env
   ```

3. **Add/update these lines:**
   ```env
   ALLOWED_HOSTS=flipunit.eu,www.flipunit.eu,217.146.78.140
   CSRF_TRUSTED_ORIGINS=https://flipunit.eu,https://www.flipunit.eu
   ```

4. **Restart the web container:**
   ```bash
   docker-compose restart web
   ```

### Option 2: Full Update (Recommended)

1. **Pull the latest code** (if using git):
   ```bash
   cd /opt/flipunit
   git pull
   ```

2. **Or upload the updated files:**
   - `flipunit/settings.py`
   - `docker-compose.yml`

3. **Update .env file** (if not already done):
   ```bash
   nano .env
   ```
   Add:
   ```env
   ALLOWED_HOSTS=flipunit.eu,www.flipunit.eu,217.146.78.140
   CSRF_TRUSTED_ORIGINS=https://flipunit.eu,https://www.flipunit.eu
   ```

4. **Restart containers:**
   ```bash
   docker-compose restart web
   ```

---

## ✅ Verification

After deploying, check the logs:
```bash
docker-compose logs -f web
```

You should **NOT** see:
- ❌ `Invalid HTTP_HOST header: '217.146.78.140'`
- ❌ `Origin checking failed - https://flipunit.eu`

You **SHOULD** see:
- ✅ Successful requests to `/media-converter/audio-converter/`
- ✅ No DisallowedHost errors
- ✅ No CSRF origin errors

---

## 🧪 Test

1. **Visit your site:** `https://flipunit.eu`
2. **Try the audio converter:** `https://flipunit.eu/media-converter/audio-converter/`
3. **Upload a file and convert**
4. **Check browser console** (F12) - should see no errors
5. **Check server logs** - should see no DisallowedHost or CSRF errors

---

## 📝 Notes

- The IP address `217.146.78.140` is now in ALLOWED_HOSTS to handle direct IP access
- CSRF_TRUSTED_ORIGINS is required for Django 4.0+ when using HTTPS
- These settings can be overridden via environment variables in `.env`
- The fixes are backward compatible - existing functionality should continue to work

---

## 🔍 Why This Happened

1. **Direct IP Access:** Some requests (health checks, bots, direct access) come to the IP address instead of the domain
2. **Django 4.0+ Changes:** CSRF_TRUSTED_ORIGINS became required for HTTPS sites
3. **Nginx Configuration:** If Nginx isn't properly forwarding the Host header, requests might come with the IP

---

**After deploying these fixes, your audio converter should work properly!** 🎉






