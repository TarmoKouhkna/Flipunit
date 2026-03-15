# Performance Optimizations (March 2026)

## Changes Applied

### 1. Home Page Caching
- `@cache_page(300)` on home view – caches HTML for 5 minutes
- Reduces Django/DB/Redis load for repeat visitors

### 2. SVG Sprite for Category Icons
- **Before:** 12 separate HTTP requests for category icons
- **After:** 1 request for `sprite.svg` – all icons in one file
- File: `static/images/icons/sprite.svg`

### 3. HTTP/2 in Nginx
- `listen 443 ssl http2` – enables multiplexing
- Reduces connection overhead for parallel requests

### 4. Relaxed Rate Limits
- `api_limit`: 60 r/m, burst 10 (was 10 r/m, burst 2)
- `general_limit`: 120 r/m, burst 30 (was 100 r/m, burst 20)

### 5. Health Check Timeout
- Celery inspect uses `timeout=2` to avoid blocking

---

## Further Recommendations (If Still Slow)

### A. Cloudflare (Free Tier)
- Add flipunit.eu to Cloudflare
- Caches static assets at 300+ edge locations worldwide
- Reduces latency for users far from the Hetzner server (Germany)
- Setup: Add site → Update nameservers → Enable caching

### B. Geographic Latency
- Server is in Germany (Hetzner)
- Users in US/Asia may see 100–300ms+ extra latency
- Cloudflare or a CDN helps most for distant users

### C. Gunicorn Tuning
- Current: `(2*CPU)+1` workers, 2 threads each
- If CPU-bound: consider more workers
- If I/O-bound: consider `--threads 4` per worker

### D. Database
- Run `EXPLAIN ANALYZE` on slow queries
- Ensure indexes exist for frequently queried columns

### E. Redis
- Verify Redis is on same host (low latency)
- Check `redis-cli --latency` for connection latency
