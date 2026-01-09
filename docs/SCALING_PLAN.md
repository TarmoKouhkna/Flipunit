# Django FlipUnit Scaling Plan: Hundreds to Thousands of Concurrent Users

## Executive Summary

**Current State:** Django 5.2.9 application running on a single VPS with Docker Compose, PostgreSQL database, Nginx reverse proxy, and synchronous processing for all operations. The main bottlenecks are:
- **I/O-bound operations:** Transcription (OpenAI Whisper API) blocks for up to 10 minutes
- **CPU-bound operations:** Video merge (up to 40 minutes), PDF OCR (up to 15 minutes), media conversion (5-20 minutes) all run synchronously, blocking workers
- **No background job system:** All long-running operations block HTTP requests
- **No queue management:** No way to handle concurrent operations efficiently

**Critical Changes Required:**
1. Move all long-running operations to background jobs (Celery) with specialized queues
2. Add Redis for queue management, session/cache storage, and job tracking
3. Implement worker queue architecture: separate queues for I/O-bound (transcription, API calls) and CPU-bound (media, PDF, image, archive) operations
4. Migrate uploads to object storage (S3-compatible) with presigned URLs
5. Implement rate limiting, quotas, and cost tracking (especially for OpenAI API)
6. Add comprehensive observability (structured logging, Sentry, metrics)
7. Optimize resource allocation: CPU workers for media/PDF, I/O workers for transcription

**Stage A (Hundreds):** Single VPS (8-16 cores, 32-64GB RAM) with Redis, specialized Celery workers (I/O and CPU), and optimized Gunicorn configuration.  
**Stage B (Thousands):** Multi-node architecture with load balancer, separate I/O worker nodes, separate CPU worker nodes (media, PDF, image), managed PostgreSQL, and object storage.

---

## Findings (Current State)

### 1. Django Settings Structure
- **File:** `flipunit/settings.py`
- **Environment Variables:** Uses `python-dotenv` to load from `.env` file
- **Key Variables:** `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `DB_*`, `OPENAI_API_KEY`, `GOOGLE_GEMINI_API_KEY`
- **No Redis/Celery settings** currently configured

### 2. ASGI/WSGI Configuration
- **WSGI:** `flipunit/wsgi.py` (standard Django WSGI application)
- **ASGI:** `flipunit/asgi.py` (standard, not currently used)
- **Entrypoint:** Gunicorn via Dockerfile entrypoint script

### 3. Web Server Configuration
- **Nginx:** `nginx_config_fixed.conf`
  - Reverse proxy to `localhost:8000`
  - `client_max_body_size 700M`
  - Proxy timeouts: 300s
  - Static files: `/opt/flipunit/staticfiles/`
  - Media files: `/opt/flipunit/media/` (local disk)
- **Gunicorn:** Dockerfile entrypoint
  - `--workers 3 --timeout 600`
  - No connection pooling configuration visible

### 4. Background Job System
- **None exists.** No Celery, RQ, or Dramatiq
- **Note:** Comment in `settings.py:211` mentions "consider using async tasks (Celery) for long operations"

### 5. Transcription Trigger Location
- **File:** `text_converter/views.py`
- **Function:** `audio_transcription()` (lines 598-716)
- **Current Flow:** Synchronous in HTTP request
  1. Upload file to temp directory
  2. Validate (size, type, duration)
  3. Call `_transcribe_audio()` (lines 565-595) — **blocks for up to 10 minutes**
  4. Return transcription in response
- **DOCX Generation:** `download_transcription_docx()` (lines 718-771) — also synchronous

### 6. Upload Handling
- **Location:** `flipunit/settings.py:185-186`
  - `MEDIA_ROOT = BASE_DIR / 'media'` (local disk)
  - `MEDIA_URL = 'media/'`
- **Limits:** 700MB (`FILE_UPLOAD_MAX_MEMORY_SIZE = 734003200`)
- **Flow:** Upload → Django → temp file → process → response
- **No chunked uploads** or direct-to-storage

### 7. Database Configuration
- **Engine:** PostgreSQL (`django.db.backends.postgresql`)
- **Config:** `flipunit/settings.py:131-140`
  - Environment variables: `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`
- **Connection Pooling:** None (`CONN_MAX_AGE` not set)
- **Deployment:** Docker Compose (`docker-compose.yml:41-57`)
  - Postgres 15 container
  - Volume: `postgres-data`

### 8. Caching/Session Backend
- **Sessions:** Default (database-backed, `django.contrib.sessions`)
- **Caching:** None (`CACHES` not configured)
- **Static:** WhiteNoise (`whitenoise.storage.CompressedManifestStaticFilesStorage`)

### 9. Static Files Handling
- **WhiteNoise** for static file serving
- **STATIC_ROOT = BASE_DIR / 'staticfiles'**
- **Nginx** serves `/static/` from `/opt/flipunit/staticfiles/`
- **No CDN** configured

### 10. Rate Limiting / Quotas / Abuse Controls
- **None found.** No rate limiting middleware or quotas implemented

### 11. Converter Operations Analysis
- **Transcription (I/O-bound):** OpenAI Whisper API calls, up to 10 minutes, synchronous
- **Media Converters (CPU-bound):** FFmpeg operations, 5-40 minutes, synchronous
- **PDF Tools (CPU-bound):** OCR, image conversion, HTML rendering, 2-15 minutes, synchronous
- **Image Converters (CPU-bound):** Pillow/CairoSVG operations, 1-5 minutes, synchronous
- **Archive Converters (CPU/memory-bound):** Compression/extraction, 1-10 minutes, synchronous
- **Text/Developer Converters (lightweight):** Mostly instant, some batch operations

---

## Complete Converter Analysis

### I/O-Bound Operations (Network/API Calls)

#### 1. Audio Transcription (OpenAI Whisper API)
- **Location:** `text_converter/views.py:audio_transcription()`
- **Resource Type:** I/O-bound (network wait)
- **Current Timeout:** 600s (10 minutes)
- **Typical Duration:** 1-10 minutes depending on audio length
- **Bottleneck:** OpenAI API response time
- **Cost:** $0.006 per minute of audio
- **Rate Limits:** OpenAI tier-dependent (typically 50 RPM, 1M TPM)
- **Concurrency:** High (workers wait on network, not CPU)

#### 2. Currency Converter (API Calls)
- **Location:** `currency_converter/views.py`
- **Resource Type:** I/O-bound (external API)
- **Current Timeout:** Standard HTTP timeout
- **Typical Duration:** < 1 second
- **Bottleneck:** External API response time
- **Cost:** Depends on API provider
- **Concurrency:** Very high (fast responses)

#### 3. AI Chat (Google Gemini API)
- **Location:** `ai_chat/views.py`
- **Resource Type:** I/O-bound (network wait)
- **Current Timeout:** Standard HTTP timeout
- **Typical Duration:** 2-10 seconds
- **Bottleneck:** Gemini API response time
- **Cost:** Per token pricing
- **Concurrency:** High

### CPU-Bound Operations (Local Processing)

#### 4. Media Converters (FFmpeg)
- **Location:** `media_converter/views.py`
- **Operations:**
  - Video converter: 5-20 minutes (up to 1200s timeout)
  - Video merge: 10-40 minutes (up to 2400s timeout for large files)
  - Audio converter: 1-10 minutes (300-600s timeout)
  - Audio merge: 5-10 minutes (600s timeout)
  - Video to GIF: 2-5 minutes (300s timeout)
  - Video compressor: 5-20 minutes (600-1200s timeout)
- **Resource Type:** CPU-bound (FFmpeg encoding/decoding)
- **CPU Usage:** High (uses 2 threads per operation, can saturate CPU)
- **Memory Usage:** Medium (buffers video frames)
- **Concurrency:** Low (CPU-intensive, limit concurrent operations)
- **Bottleneck:** CPU cores and encoding speed

#### 5. PDF Tools
- **Location:** `pdf_tools/views.py`
- **Operations:**
  - PDF OCR (pytesseract): 5-15 minutes (very CPU-intensive)
  - PDF to images (pdf2image): 2-10 minutes (CPU-intensive)
  - HTML to PDF (weasyprint): 1-5 minutes (CPU/memory-intensive)
  - PDF merge/split: 30 seconds - 2 minutes (I/O + CPU)
  - PDF compress: 1-5 minutes (CPU-intensive)
  - PDF to EPUB: 2-5 minutes (CPU-intensive)
- **Resource Type:** CPU-bound (except merge/split which are I/O + CPU)
- **CPU Usage:** High (especially OCR and image conversion)
- **Memory Usage:** High (PDF rendering, image buffers)
- **Concurrency:** Low to medium (OCR very low, merge/split medium)
- **Bottleneck:** CPU cores, memory for large PDFs

#### 6. Image Converters
- **Location:** `image_converter/views.py`
- **Operations:**
  - Universal converter: 10 seconds - 2 minutes
  - Image resize: 5-30 seconds
  - Image merge: 10 seconds - 1 minute
  - SVG to PNG (CairoSVG): 5-30 seconds
  - Batch conversion: 1-5 minutes (depends on count)
- **Resource Type:** CPU-bound (Pillow/CairoSVG processing)
- **CPU Usage:** Medium to high (depends on image size)
- **Memory Usage:** Medium (image buffers)
- **Concurrency:** Medium (can handle more than video/PDF)
- **Bottleneck:** CPU cores, memory for large images

#### 7. Archive Converters
- **Location:** `archive_converter/views.py`
- **Operations:**
  - RAR/ZIP/7Z conversion: 1-10 minutes
  - ISO extraction: 2-10 minutes
  - Large archive operations: 5-20 minutes
- **Resource Type:** CPU/memory-bound
- **CPU Usage:** Medium to high (compression algorithms)
- **Memory Usage:** High (file buffers, especially for large archives)
- **Concurrency:** Low (memory-intensive)
- **Bottleneck:** CPU cores, available RAM

### Lightweight Operations (Fast Processing)

#### 8. Text Converters
- **Location:** `text_converter/views.py`
- **Operations:** Case conversion, formatting, JSON/XML/YAML conversion
- **Resource Type:** CPU-bound (but very fast)
- **Typical Duration:** < 1 second
- **Concurrency:** Very high (can process synchronously)

#### 9. Developer Converters
- **Location:** `developer_converter/views.py`
- **Operations:** Code minify/unminify, CSV/JSON conversion
- **Resource Type:** CPU-bound (but very fast)
- **Typical Duration:** < 1 second
- **Concurrency:** Very high

#### 10. Utilities
- **Location:** `utilities/views.py`
- **Operations:** QR code generation, random generators, calculators
- **Resource Type:** CPU-bound (but very fast)
- **Typical Duration:** < 1 second
- **Concurrency:** Very high

---

## Stage A Plan: Hundreds Concurrent Users

### P0 (Must Have)

#### A1. Background Job System (Celery + Redis)
- Add Celery with Redis broker
- Move transcription to async tasks
- Move DOCX generation to async tasks
- Add job status tracking model

#### A2. Redis Setup
- Install Redis (Docker service or system package)
- Configure Redis for Celery broker/result backend
- Use Redis for sessions (`SESSION_ENGINE = 'django.contrib.sessions.backends.cache'`)
- Use Redis for cache (`CACHES` with Redis backend)

#### A3. Job Status API
- Create `TranscriptionJob` model (status, file_key, user_ip, created_at, completed_at, error)
- Endpoint: `POST /text-converter/audio-transcription/` → returns `job_id`
- Endpoint: `GET /text-converter/audio-transcription/status/<job_id>/` → returns status + result
- Endpoint: `GET /text-converter/audio-transcription/download/<job_id>/` → download transcript/docx

#### A4. Upload Optimization
- **Option A (Preferred):** Direct-to-S3 presigned URLs
  - Generate presigned POST URL for client
  - Client uploads directly to S3
  - Worker reads from S3
- **Option B (Interim):** Nginx upload module or buffering
  - `client_body_buffer_size` tuning
  - `proxy_request_buffering off` for large uploads

#### A5. File Size/Duration Validation
- Enforce 700MB file size limit (already exists)
- Enforce 30-minute duration limit (already exists)
- Add per-IP daily quota (e.g., 10 transcriptions/day)
- Add rate limiting middleware (django-ratelimit or django-axes)

#### A6. Database Connection Management
- Set `CONN_MAX_AGE = 300` in database config
- Monitor connection count
- Consider PgBouncer if connection issues appear

#### A7. Observability
- Structured JSON logging
- Add Sentry for error tracking
- Health check endpoint (`/health/`)
- Basic metrics (job queue length, worker status)

### P1 (Should Have)

#### A8. Gunicorn Optimization
- Increase workers: `workers = (2 * CPU cores) + 1`
- Add `--threads 2` for I/O-bound work
- Tune `--timeout` (keep 600s for long requests)
- Add `--max-requests` and `--max-requests-jitter` for graceful restarts

#### A9. Nginx Tuning
- Increase `proxy_read_timeout` to 600s (match Gunicorn)
- Add `proxy_buffering off` for large uploads
- Enable gzip compression
- Add rate limiting (`limit_req_zone`)

#### A10. Cost Control & Quotas
- Track API costs per job (estimate from file size/duration)
- Log usage per IP
- Implement soft daily limits (warn, then hard limit)
- Add usage dashboard (admin)

### P2 (Nice to Have)

#### A11. Retry Logic
- Celery retry with exponential backoff
- Idempotency keys for duplicate prevention
- Dead letter queue for failed jobs

#### A12. Monitoring Dashboard
- Flower for Celery monitoring
- Basic Prometheus metrics export
- Log aggregation (ELK or simpler)

#### A13. Worker Queue Architecture (All Converters)
- Implement separate Celery queues for different operation types
- Queue priorities and routing rules
- Resource-aware worker allocation

---

## Stage B Plan: Thousands Concurrent Users

### P0 (Must Have)

#### B1. Multi-Node Architecture
- Load balancer (Nginx/HAProxy/Cloud Load Balancer)
- 2+ stateless web nodes (Django + Gunicorn)
- Separate worker node(s) (Celery workers only)
- Dedicated Redis node (or managed Redis)
- Managed PostgreSQL (or dedicated DB node with replication)

#### B2. Stateless Web Nodes
- No local file storage (all via object storage)
- Shared sessions in Redis
- Shared cache in Redis
- Health checks for load balancer
- Zero-downtime deployment (rolling restarts)

#### B3. Object Storage (S3-Compatible)
- Migrate all uploads to S3-compatible storage
- Presigned URLs for uploads (client → S3 directly)
- Workers read from S3, write results to S3
- CDN for static files (CloudFront/Cloudflare)
- Lifecycle policies (delete old files after 7 days)

#### B4. Database Scaling
- PgBouncer in transaction pooling mode
- `CONN_MAX_AGE = 0` (let PgBouncer manage)
- Read replicas for reporting (if needed)
- Connection limits per worker
- Monitor slow queries

#### B5. Worker Scaling Strategy
- Separate worker nodes (CPU/memory optimized)
- Horizontal scaling (add workers as needed)
- Queue priorities (high/low)
- Worker concurrency: `celery worker --concurrency=10` (I/O bound, adjust by load)
- Separate queues: `transcription`, `docx_generation`, `low_priority`

#### B6. Backpressure & Circuit Breaker
- Queue limits (max 1000 pending jobs)
- Worker concurrency limits (max 20 concurrent per worker)
- Circuit breaker for Whisper API failures (stop sending if >50% fail)
- Timeout strategy: 15-minute max per transcription
- Dead letter queue for failed jobs

#### B7. Security Hardening
- Secrets management (AWS Secrets Manager/HashiCorp Vault/env vars)
- Least privilege IAM roles for S3 access
- Signed URLs with expiration (5 minutes for uploads, 1 hour for downloads)
- IP allowlisting for admin endpoints
- Rate limiting per IP (100 requests/minute)

### P1 (Should Have)

#### B8. Cost Control & Quotas
- Per-IP daily quotas (configurable, default 20 transcriptions/day)
- Per-IP monthly quotas (500 transcriptions/month)
- Cost tracking per job (log to database)
- Admin dashboard for quota management
- Automatic blocking of abusive IPs

#### B9. Advanced Observability
- Distributed tracing (OpenTelemetry)
- APM (New Relic/Datadog/Elastic APM)
- Structured logs → centralized logging (ELK/CloudWatch)
- Real-time alerts (Sentry + PagerDuty)
- Cost monitoring dashboard

#### B10. High Availability
- Multi-AZ deployment (if cloud)
- Database replication (master + 1+ replicas)
- Redis Sentinel or managed Redis (high availability)
- Automated failover for load balancer
- Backup strategy (daily DB backups, S3 versioning)

### P2 (Nice to Have)

#### B11. Auto-Scaling
- Auto-scale web nodes based on CPU/memory
- Auto-scale workers based on queue length
- Predictive scaling (time-based patterns)

#### B12. Advanced Features
- Job prioritization (paid users get priority queue)
- Webhook notifications (job completion)
- Batch transcription API
- API keys for programmatic access

---

## Worker Queue Architecture

### Queue Design Strategy

The application requires **multiple specialized queues** to handle different operation types efficiently. Each queue has different resource requirements and concurrency characteristics.

#### Queue Types

**1. `transcription` Queue (I/O-Bound)**
- **Operations:** Audio transcription via OpenAI Whisper API
- **Resource Type:** I/O-bound (network wait)
- **Worker Concurrency:** High (10-20 per worker)
- **Timeout:** 900s (15 minutes soft), 960s (16 minutes hard)
- **Priority:** Medium
- **Retry Strategy:** Exponential backoff, max 3 retries
- **Circuit Breaker:** Yes (stop if >50% fail in 5 minutes)

**2. `media_processing` Queue (CPU-Bound)**
- **Operations:** Video/audio conversion, merge, compression (FFmpeg)
- **Resource Type:** CPU-bound
- **Worker Concurrency:** Low (2-4 per worker)
- **Timeout:** 2400s (40 minutes for video merge)
- **Priority:** Medium
- **Retry Strategy:** No automatic retry (user should resubmit)
- **Resource Limits:** CPU cores, memory

**3. `pdf_processing` Queue (CPU-Bound)**
- **Operations:** PDF OCR, PDF to images, HTML to PDF, PDF compression
- **Resource Type:** CPU-bound (OCR very intensive)
- **Worker Concurrency:** Low (1-2 per worker for OCR), Medium (4-6 for others)
- **Timeout:** 900s (15 minutes)
- **Priority:** Medium
- **Retry Strategy:** No automatic retry for OCR (user resubmit)
- **Resource Limits:** CPU cores, memory (especially for OCR)

**4. `image_processing` Queue (CPU-Bound)**
- **Operations:** Image conversion, resize, merge, SVG to PNG
- **Resource Type:** CPU-bound
- **Worker Concurrency:** Medium (6-8 per worker)
- **Timeout:** 300s (5 minutes)
- **Priority:** Medium
- **Retry Strategy:** No automatic retry
- **Resource Limits:** CPU cores, memory

**5. `archive_processing` Queue (CPU/Memory-Bound)**
- **Operations:** Archive conversion, extraction, compression
- **Resource Type:** CPU/memory-bound
- **Worker Concurrency:** Low (2-3 per worker)
- **Timeout:** 600s (10 minutes)
- **Priority:** Low
- **Retry Strategy:** No automatic retry
- **Resource Limits:** CPU cores, available RAM

**6. `lightweight` Queue (Fast Operations)**
- **Operations:** Text converters, developer tools, utilities, DOCX generation
- **Resource Type:** CPU-bound (but very fast)
- **Worker Concurrency:** Very high (20-30 per worker)
- **Timeout:** 60s (1 minute)
- **Priority:** High (fast response expected)
- **Retry Strategy:** No automatic retry
- **Resource Limits:** Minimal

**7. `api_calls` Queue (I/O-Bound)**
- **Operations:** Currency converter, AI chat (Gemini)
- **Resource Type:** I/O-bound (network wait)
- **Worker Concurrency:** High (15-20 per worker)
- **Timeout:** 30s (30 seconds)
- **Priority:** High
- **Retry Strategy:** Exponential backoff, max 2 retries
- **Resource Limits:** Network bandwidth

### Celery Configuration

```python
# settings.py
CELERY_TASK_ROUTES = {
    'text_converter.tasks.transcribe_audio_task': {'queue': 'transcription'},
    'text_converter.tasks.generate_docx_task': {'queue': 'lightweight'},
    'media_converter.tasks.*': {'queue': 'media_processing'},
    'pdf_tools.tasks.*': {'queue': 'pdf_processing'},
    'image_converter.tasks.*': {'queue': 'image_processing'},
    'archive_converter.tasks.*': {'queue': 'archive_processing'},
    'currency_converter.tasks.*': {'queue': 'api_calls'},
    'ai_chat.tasks.*': {'queue': 'api_calls'},
}

CELERY_TASK_QUEUES = {
    'transcription': {
        'exchange': 'transcription',
        'routing_key': 'transcription',
    },
    'media_processing': {
        'exchange': 'media_processing',
        'routing_key': 'media_processing',
    },
    'pdf_processing': {
        'exchange': 'pdf_processing',
        'routing_key': 'pdf_processing',
    },
    'image_processing': {
        'exchange': 'image_processing',
        'routing_key': 'image_processing',
    },
    'archive_processing': {
        'exchange': 'archive_processing',
        'routing_key': 'archive_processing',
    },
    'lightweight': {
        'exchange': 'lightweight',
        'routing_key': 'lightweight',
    },
    'api_calls': {
        'exchange': 'api_calls',
        'routing_key': 'api_calls',
    },
}
```

### Worker Deployment Strategy

**Stage A (Single VPS):**
```bash
# I/O-bound workers (high concurrency)
celery -A flipunit worker -Q transcription,api_calls --concurrency=10 --hostname=io-worker@%h

# CPU-bound workers (low concurrency)
celery -A flipunit worker -Q media_processing --concurrency=2 --hostname=media-worker@%h
celery -A flipunit worker -Q pdf_processing --concurrency=2 --hostname=pdf-worker@%h
celery -A flipunit worker -Q image_processing --concurrency=6 --hostname=image-worker@%h
celery -A flipunit worker -Q archive_processing --concurrency=2 --hostname=archive-worker@%h

# Fast operations (high concurrency)
celery -A flipunit worker -Q lightweight --concurrency=20 --hostname=lightweight-worker@%h
```

**Stage B (Multi-Node):**
- **I/O Worker Nodes:** Dedicated nodes for `transcription` and `api_calls` queues
- **CPU Worker Nodes:** Separate nodes for `media_processing`, `pdf_processing`, `image_processing`
- **General Worker Nodes:** Handle `lightweight` and `archive_processing`

---

## OpenAI Whisper API Specifics

### API Rate Limits

OpenAI Whisper API has tier-dependent rate limits:
- **Free Tier:** 3 RPM (requests per minute), 1M TPM (tokens per minute)
- **Tier 1 ($5/month):** 50 RPM, 1M TPM
- **Tier 2 ($20/month):** 50 RPM, 2M TPM
- **Tier 3 ($100/month):** 50 RPM, 5M TPM

**Note:** Audio transcription uses file size, not tokens. Rate limits are typically:
- **File Size Limit:** 25MB per file
- **Concurrent Requests:** Limited by tier
- **Daily Limits:** Vary by tier

### Cost Calculation

**Pricing:** $0.006 per minute of audio transcribed

**Cost Estimation Formula:**
```python
def estimate_transcription_cost(file_size_mb, audio_duration_minutes=None):
    """
    Estimate transcription cost.
    
    Args:
        file_size_mb: File size in MB
        audio_duration_minutes: Audio duration in minutes (if known)
    
    Returns:
        Estimated cost in USD
    """
    if audio_duration_minutes:
        # Direct calculation from duration
        return audio_duration_minutes * 0.006
    else:
        # Estimate: 1MB ≈ 1 minute for typical audio (MP3 128kbps)
        estimated_minutes = file_size_mb * 0.8  # Conservative estimate
        return estimated_minutes * 0.006
```

**Example Costs:**
- 5-minute audio: $0.03
- 10-minute audio: $0.06
- 30-minute audio: $0.18
- 100 transcriptions/day (avg 10 min): $6.00/day = $180/month

### Rate Limit Handling

**429 Response Handling:**
```python
from celery import shared_task
from celery.exceptions import Retry
import time
import random

@shared_task(bind=True, max_retries=3)
def transcribe_audio_task(self, job_id, file_path, api_key):
    try:
        # Transcription logic
        result = client.audio.transcriptions.create(...)
        return result
    except openai.RateLimitError as e:
        # Get retry-after from header if available
        retry_after = int(e.response.headers.get('Retry-After', 60))
        # Add jitter to prevent thundering herd
        jitter = random.uniform(0, 10)
        wait_time = retry_after + jitter
        
        # Exponential backoff
        countdown = wait_time * (2 ** self.request.retries)
        
        raise self.retry(exc=e, countdown=countdown, max_retries=3)
    except openai.APIError as e:
        # Other API errors - retry with exponential backoff
        countdown = 60 * (2 ** self.request.retries)
        raise self.retry(exc=e, countdown=countdown, max_retries=3)
```

### Circuit Breaker Implementation

**Purpose:** Stop sending requests if API is failing consistently

```python
from datetime import datetime, timedelta
from django.core.cache import cache

class WhisperAPICircuitBreaker:
    FAILURE_THRESHOLD = 0.5  # 50% failure rate
    TIME_WINDOW = 300  # 5 minutes
    CIRCUIT_OPEN_DURATION = 600  # 10 minutes
    
    @classmethod
    def is_open(cls):
        """Check if circuit breaker is open"""
        return cache.get('whisper_circuit_open', False)
    
    @classmethod
    def record_success(cls):
        """Record successful API call"""
        cache.delete('whisper_circuit_open')
        # Reset failure count
        cache.set('whisper_failures', 0, cls.TIME_WINDOW)
    
    @classmethod
    def record_failure(cls):
        """Record failed API call and check threshold"""
        failures = cache.get('whisper_failures', 0) + 1
        total = cache.get('whisper_total', 0) + 1
        
        cache.set('whisper_failures', failures, cls.TIME_WINDOW)
        cache.set('whisper_total', total, cls.TIME_WINDOW)
        
        failure_rate = failures / total if total > 0 else 0
        
        if failure_rate >= cls.FAILURE_THRESHOLD and total >= 10:
            # Open circuit breaker
            cache.set('whisper_circuit_open', True, cls.CIRCUIT_OPEN_DURATION)
            return True
        return False
```

### Timeout Strategy

**Network Timeout:** 600s (10 minutes) - matches OpenAI's max processing time
**Task Timeout:** 900s soft, 960s hard (15-16 minutes) - allows for network delays

**Implementation:**
```python
CELERY_TASK_SOFT_TIME_LIMIT = 900  # 15 minutes
CELERY_TASK_TIME_LIMIT = 960  # 16 minutes

# In task
@shared_task(
    bind=True,
    soft_time_limit=900,
    time_limit=960,
    autoretry_for=(openai.RateLimitError, openai.APIError),
    retry_backoff=True,
    retry_backoff_max=600,
    max_retries=3
)
def transcribe_audio_task(self, job_id, file_path, api_key):
    # Check circuit breaker
    if WhisperAPICircuitBreaker.is_open():
        raise Exception("OpenAI API circuit breaker is open")
    
    try:
        client = OpenAI(api_key=api_key, timeout=600.0)
        # ... transcription logic
        WhisperAPICircuitBreaker.record_success()
    except Exception as e:
        WhisperAPICircuitBreaker.record_failure()
        raise
```

### Cost Tracking

**Database Model Addition:**
```python
class TranscriptionJob(models.Model):
    # ... existing fields
    cost_estimate = models.DecimalField(max_digits=10, decimal_places=4, null=True)
    actual_cost = models.DecimalField(max_digits=10, decimal_places=4, null=True)
    api_tier = models.CharField(max_length=20, null=True)  # Track which tier was used
```

**Daily Cost Monitoring:**
```python
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta

def get_daily_transcription_cost():
    """Calculate daily transcription costs"""
    today = timezone.now().date()
    jobs = TranscriptionJob.objects.filter(
        created_at__date=today,
        status='completed'
    )
    total_cost = jobs.aggregate(Sum('actual_cost'))['actual_cost__sum'] or 0
    return total_cost

# Alert if daily cost exceeds threshold
DAILY_COST_ALERT_THRESHOLD = 50.00  # $50/day
if get_daily_transcription_cost() > DAILY_COST_ALERT_THRESHOLD:
    # Send alert (Sentry, email, etc.)
    pass
```

---

## Timeout Strategies by Operation Type

### I/O-Bound Operations

| Operation | Queue | Soft Timeout | Hard Timeout | Rationale |
|-----------|-------|--------------|--------------|-----------|
| Audio Transcription | `transcription` | 900s | 960s | OpenAI API max 10 min + network buffer |
| Currency Converter | `api_calls` | 30s | 60s | Fast API responses expected |
| AI Chat | `api_calls` | 30s | 60s | Fast API responses expected |

### CPU-Bound Operations

| Operation | Queue | Soft Timeout | Hard Timeout | Rationale |
|-----------|-------|--------------|--------------|-----------|
| Video Converter | `media_processing` | 1200s | 1260s | Large files can take 20 minutes |
| Video Merge | `media_processing` | 2400s | 2460s | Very large files (5GB+) can take 40 minutes |
| Audio Converter | `media_processing` | 600s | 660s | Typical 5-10 minutes |
| Audio Merge | `media_processing` | 600s | 660s | Typical 5-10 minutes |
| Video to GIF | `media_processing` | 300s | 360s | Usually 2-5 minutes |
| Video Compressor | `media_processing` | 1200s | 1260s | Large files can take 20 minutes |
| PDF OCR | `pdf_processing` | 900s | 960s | Very CPU-intensive, can take 15 minutes |
| PDF to Images | `pdf_processing` | 600s | 660s | Large PDFs can take 10 minutes |
| HTML to PDF | `pdf_processing` | 300s | 360s | Usually 1-5 minutes |
| PDF Compress | `pdf_processing` | 300s | 360s | Usually 1-5 minutes |
| PDF to EPUB | `pdf_processing` | 300s | 360s | Usually 2-5 minutes |
| Image Converter | `image_processing` | 300s | 360s | Usually 10 seconds - 2 minutes |
| Image Resize | `image_processing` | 60s | 120s | Usually 5-30 seconds |
| Image Merge | `image_processing` | 300s | 360s | Usually 10 seconds - 1 minute |
| SVG to PNG | `image_processing` | 60s | 120s | Usually 5-30 seconds |
| Archive Conversion | `archive_processing` | 600s | 660s | Large archives can take 10 minutes |
| ISO Extraction | `archive_processing` | 600s | 660s | Large ISOs can take 10 minutes |

### Lightweight Operations

| Operation | Queue | Soft Timeout | Hard Timeout | Rationale |
|-----------|-------|--------------|--------------|-----------|
| DOCX Generation | `lightweight` | 60s | 120s | Usually < 5 seconds |
| Text Converters | `lightweight` | 10s | 30s | Usually < 1 second |
| Developer Tools | `lightweight` | 10s | 30s | Usually < 1 second |
| Utilities | `lightweight` | 10s | 30s | Usually < 1 second |

### Celery Task Configuration

```python
# text_converter/tasks.py
@shared_task(
    bind=True,
    soft_time_limit=900,
    time_limit=960,
    queue='transcription',
    autoretry_for=(openai.RateLimitError,),
    retry_backoff=True,
    max_retries=3
)
def transcribe_audio_task(self, job_id, file_path, api_key):
    # ...

# media_converter/tasks.py
@shared_task(
    bind=True,
    soft_time_limit=2400,
    time_limit=2460,
    queue='media_processing',
    max_retries=0  # No retry for CPU-bound operations
)
def video_merge_task(self, job_id, file_paths, output_format):
    # ...

# pdf_tools/tasks.py
@shared_task(
    bind=True,
    soft_time_limit=900,
    time_limit=960,
    queue='pdf_processing',
    max_retries=0
)
def pdf_ocr_task(self, job_id, file_path):
    # ...
```

---

## Implementation Steps in Order

### Phase 1: Foundation (Week 1-2)

**1. Add Redis to Docker Compose**
   - Add `redis` service to `docker-compose.yml`
   - Expose port 6379 (internal only)
   - Add Redis to requirements: `redis>=5.0.0`, `celery>=5.3.0`

**2. Create Celery Configuration**
   - Add `flipunit/celery.py`
   - Update `flipunit/__init__.py` to load Celery app
   - Add Celery settings to `settings.py`:
     - `CELERY_BROKER_URL = os.environ.get('REDIS_URL', 'redis://redis:6379/0')`
     - `CELERY_RESULT_BACKEND = os.environ.get('REDIS_URL', 'redis://redis:6379/0')`
     - `CELERY_TASK_SOFT_TIME_LIMIT = 900` (15 minutes)
     - `CELERY_TASK_TIME_LIMIT = 960` (16 minutes)

**3. Create TranscriptionJob Model**
   - Add `text_converter/models.py`:
     ```python
     class TranscriptionJob(models.Model):
         STATUS_CHOICES = [
             ('pending', 'Pending'),
             ('processing', 'Processing'),
             ('completed', 'Completed'),
             ('failed', 'Failed'),
         ]
         job_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
         status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
         file_key = models.CharField(max_length=500)  # S3 key or local path
         file_size = models.BigIntegerField()
         duration_seconds = models.FloatField(null=True)
         user_ip = models.GenericIPAddressField()
         transcription_text = models.TextField(null=True)
         detected_language = models.CharField(max_length=10, null=True)
         error_message = models.TextField(null=True)
         created_at = models.DateTimeField(auto_now_add=True)
         completed_at = models.DateTimeField(null=True)
         cost_estimate = models.DecimalField(max_digits=10, decimal_places=4, null=True)
     ```
   - Create migration: `python manage.py makemigrations text_converter`

**4. Create Celery Tasks**
   - Add `text_converter/tasks.py`:
     - `transcribe_audio_task(job_id, file_path, api_key)`
     - `generate_docx_task(job_id, transcription_text)`
   - Move transcription logic from `views.py` to `tasks.py`

**5. Update Views for Async Pattern**
   - Modify `audio_transcription()`:
     - Accept file upload
     - Save to temp location (or S3)
     - Create `TranscriptionJob` record
     - Enqueue `transcribe_audio_task`
     - Return `job_id` immediately
   - Add `job_status(request, job_id)` view
   - Add `download_transcript(request, job_id)` view
   - Add `download_docx(request, job_id)` view

**6. Update Frontend**
   - Modify `templates/text_converter/audio_transcription.html`:
     - After upload, show "Processing..." with `job_id`
     - Poll `/text-converter/audio-transcription/status/<job_id>/` every 2 seconds
     - Display result when `status == 'completed'`
     - Show error if `status == 'failed'`

### Phase 2: Redis Integration (Week 2-3)

**7. Configure Redis for Sessions**
   - Add to `settings.py`:
     ```python
     SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
     SESSION_CACHE_ALIAS = 'default'
     ```

**8. Configure Redis for Cache**
   - Add to `settings.py`:
     ```python
     CACHES = {
         'default': {
             'BACKEND': 'django.core.cache.backends.redis.RedisCache',
             'LOCATION': os.environ.get('REDIS_URL', 'redis://redis:6379/1'),
         }
     }
     ```

**9. Add Celery Worker to Docker Compose**
   - Add `celery_worker` service:
     ```yaml
     celery_worker:
       build: .
       command: celery -A flipunit worker --loglevel=info --concurrency=4
       volumes: [same as web]
       depends_on: [postgres, redis]
     ```

### Phase 3: Rate Limiting & Quotas (Week 3-4)

**10. Add Rate Limiting**
    - Install: `django-ratelimit>=4.0.0`
    - Add to `INSTALLED_APPS`
    - Decorate views with `@ratelimit(key='ip', rate='10/h', method='POST')`
    - Add per-IP daily quota check in `audio_transcription()` view

**11. Add Quota Tracking Model**
    - Add `text_converter/models.py`:
      ```python
      class UserQuota(models.Model):
          ip_address = models.GenericIPAddressField(unique=True)
          daily_count = models.IntegerField(default=0)
          monthly_count = models.IntegerField(default=0)
          last_reset_daily = models.DateField(auto_now=True)
          last_reset_monthly = models.DateField(auto_now=True)
      ```

**12. Implement Quota Middleware**
    - Create `flipunit/middleware.py`:
      - `QuotaMiddleware` to check/increment quotas
      - Reset daily/monthly counters

### Phase 4: Object Storage (Week 4-5)

**13. Add S3 Storage Backend**
    - Install: `boto3>=1.28.0`, `django-storages>=1.14.0`
    - Add to `settings.py`:
      ```python
      DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
      AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
      AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
      AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME')
      AWS_S3_REGION_NAME = os.environ.get('AWS_S3_REGION_NAME', 'eu-north-1')
      AWS_S3_CUSTOM_DOMAIN = os.environ.get('AWS_S3_CUSTOM_DOMAIN')
      AWS_S3_SIGNATURE_VERSION = 's3v4'
      ```

**14. Implement Presigned URL Upload**
    - Add view: `get_upload_url(request)` → returns presigned POST URL
    - Update frontend to upload directly to S3
    - Worker reads from S3 key

**15. Update Transcription Task**
    - Modify `transcribe_audio_task` to:
      - Download from S3 to temp file
      - Process
      - Upload result to S3
      - Update `TranscriptionJob.file_key` with result S3 key

### Phase 5: Observability (Week 5)

**16. Add Structured Logging**
    - Update `LOGGING` in `settings.py`:
      - JSON formatter
      - File handler (or syslog)
      - Log job lifecycle events

**17. Add Sentry**
    - Install: `sentry-sdk>=1.32.0`
    - Add to `settings.py`:
      ```python
      import sentry_sdk
      sentry_sdk.init(
          dsn=os.environ.get('SENTRY_DSN'),
          traces_sample_rate=0.1,
      )
      ```

**18. Add Health Check**
    - Add view: `health_check(request)`:
      - Check DB connection
      - Check Redis connection
      - Check Celery worker status
    - Add URL: `path('health/', views.health_check)`

### Phase 6: Database Optimization (Week 6)

**19. Add Connection Pooling**
    - Set `CONN_MAX_AGE = 300` in database config
    - Monitor with `SELECT count(*) FROM pg_stat_activity;`

**20. Add PgBouncer (Stage B)**
    - Deploy PgBouncer container
    - Point Django to PgBouncer (port 6432)
    - Set `CONN_MAX_AGE = 0`

### Phase 7: Multi-Node Setup (Stage B Only)

**21. Separate Web and Worker Nodes**
    - Web nodes: Django + Gunicorn only
    - Worker nodes: Celery workers only
    - Shared: Redis, PostgreSQL, S3

**22. Load Balancer Configuration**
    - Nginx/HAProxy with health checks
    - Sticky sessions (if needed, else stateless)
    - SSL termination

**23. Deployment Strategy**
    - Blue-green or rolling updates
    - Database migrations run separately
    - Zero-downtime deploys

---

## Sizing & Concurrency Recommendations

### Stage A (Single VPS)

**Server Specs:**
- CPU: 8-16 cores (increased for CPU-bound operations)
- RAM: 32-64 GB (increased for PDF/image processing)
- Storage: 200 GB SSD (for temp files, before S3 migration)
- Network: 1 Gbps

**Process Layout:**
```
Nginx (1 process)
├── Gunicorn (5-9 workers, 2 threads each = 10-18 concurrent requests)
├── Celery Workers:
│   ├── I/O Worker (transcription, api_calls): concurrency=10
│   ├── Media Worker (media_processing): concurrency=2
│   ├── PDF Worker (pdf_processing): concurrency=2
│   ├── Image Worker (image_processing): concurrency=6
│   ├── Archive Worker (archive_processing): concurrency=2
│   └── Lightweight Worker (lightweight): concurrency=20
├── Redis (1 instance, ~2GB RAM)
└── PostgreSQL (1 instance, ~4GB RAM)
```

**Gunicorn Workers:**
- Formula: `workers = (2 * CPU_cores) + 1`
- For 8 cores: `workers = 17` (but start with 9)
- Add `--threads 2` for I/O-bound work
- Total concurrency: `workers * threads = 9 * 2 = 18` concurrent HTTP requests

**Celery Worker Concurrency by Queue:**

| Queue | Concurrency | Workers | Total Concurrent | CPU Usage |
|-------|-------------|---------|------------------|-----------|
| `transcription` | 10 | 1 | 10 | Low (I/O wait) |
| `api_calls` | 15 | 1 | 15 | Low (I/O wait) |
| `media_processing` | 2 | 2 | 4 | High (FFmpeg) |
| `pdf_processing` | 2 | 2 | 4 | High (OCR/rendering) |
| `image_processing` | 6 | 1 | 6 | Medium (Pillow) |
| `archive_processing` | 2 | 1 | 2 | High (compression) |
| `lightweight` | 20 | 1 | 20 | Low (fast ops) |
| **Total** | - | **9** | **61** | - |

**Resource Allocation:**
- **CPU Cores:** 8-16 cores needed for CPU-bound operations
  - Media processing: 2-4 cores (FFmpeg)
  - PDF processing: 2-4 cores (OCR, rendering)
  - Image processing: 1-2 cores (Pillow)
  - Archive processing: 1-2 cores (compression)
  - Remaining: Web server, I/O workers, system overhead

- **Memory:**
  - Base: 4GB (OS, PostgreSQL, Redis)
  - Media processing: 4-8GB (video buffers)
  - PDF processing: 4-8GB (PDF rendering, OCR)
  - Image processing: 2-4GB (image buffers)
  - Archive processing: 2-4GB (file buffers)
  - Temp files: 10-20GB (before S3 migration)
  - **Total: 26-48GB** (recommend 32-64GB)

**Redis:**
- Memory: ~2GB for queue + cache + sessions
- Persistence: RDB snapshots (every 5 minutes)
- Separate Redis DBs:
  - DB 0: Celery broker
  - DB 1: Celery results
  - DB 2: Django cache
  - DB 3: Django sessions

**PostgreSQL:**
- `max_connections = 200` (increased for multiple workers)
- Shared buffers: 1GB
- Work mem: 64MB
- With PgBouncer: `pool_size = 50`

### Stage B (Multi-Node)

**Web Nodes (2+):**
- CPU: 4 cores
- RAM: 8 GB
- Gunicorn: 5 workers, 2 threads = 10 concurrent/node
- Total: 20+ concurrent HTTP requests

**I/O Worker Nodes (2+):**
- CPU: 4 cores
- RAM: 8 GB
- Queues: `transcription`, `api_calls`
- Concurrency: 10-15 per worker
- Total: 20-30 concurrent I/O operations per node

**CPU Worker Nodes - Media (2+):**
- CPU: 8-16 cores (high CPU for FFmpeg)
- RAM: 16-32 GB (video buffers)
- Queue: `media_processing`
- Concurrency: 2-4 per worker
- Total: 4-8 concurrent video operations per node

**CPU Worker Nodes - PDF (2+):**
- CPU: 8-16 cores (high CPU for OCR/rendering)
- RAM: 16-32 GB (PDF rendering buffers)
- Queue: `pdf_processing`
- Concurrency: 1-2 per worker (OCR), 4-6 (others)
- Total: 2-4 concurrent PDF operations per node

**CPU Worker Nodes - Image (2+):**
- CPU: 4-8 cores
- RAM: 8-16 GB
- Queue: `image_processing`
- Concurrency: 6-8 per worker
- Total: 12-16 concurrent image operations per node

**CPU Worker Nodes - Archive (1+):**
- CPU: 4-8 cores
- RAM: 16-32 GB (large file buffers)
- Queue: `archive_processing`
- Concurrency: 2-3 per worker
- Total: 2-3 concurrent archive operations per node

**General Worker Nodes (2+):**
- CPU: 4 cores
- RAM: 8 GB
- Queue: `lightweight`
- Concurrency: 20-30 per worker
- Total: 40-60 concurrent lightweight operations per node

**Redis Node:**
- CPU: 4 cores
- RAM: 8 GB
- High availability: Redis Sentinel or managed Redis
- Persistence: AOF + RDB

**Database:**
- Managed PostgreSQL (e.g., AWS RDS, DigitalOcean Managed DB)
- Instance: db.t3.large (2 vCPU, 8 GB RAM) or db.t3.xlarge (4 vCPU, 16 GB RAM)
- PgBouncer: 1 instance, `pool_size = 100`

---

## Resource Allocation Recommendations

### CPU Allocation Strategy

**Priority Order (by CPU demand):**
1. **PDF OCR** - Highest CPU usage (pytesseract is very intensive)
2. **Video Processing** - High CPU usage (FFmpeg encoding)
3. **PDF Rendering** - High CPU usage (weasyprint, pdf2image)
4. **Archive Processing** - Medium-high CPU usage (compression algorithms)
5. **Image Processing** - Medium CPU usage (Pillow operations)
6. **I/O Operations** - Low CPU usage (network wait)

**CPU Core Allocation (8-core example):**
- PDF OCR: 2 cores (dedicated workers)
- Video Processing: 2-3 cores
- PDF Rendering: 1-2 cores
- Archive Processing: 1 core
- Image Processing: 1 core
- I/O Operations: 0.5 cores (mostly waiting)
- System/Web: 1-1.5 cores

### Memory Allocation Strategy

**Memory Requirements by Operation:**

| Operation Type | Memory per Operation | Concurrent Ops | Total Memory |
|----------------|----------------------|----------------|--------------|
| Video Processing | 1-2 GB | 2-4 | 4-8 GB |
| PDF OCR | 500 MB - 1 GB | 1-2 | 1-2 GB |
| PDF Rendering | 500 MB - 1 GB | 2-4 | 2-4 GB |
| Image Processing | 100-500 MB | 6-8 | 1-4 GB |
| Archive Processing | 500 MB - 2 GB | 2-3 | 2-6 GB |
| I/O Operations | < 50 MB | 10-20 | < 1 GB |
| Lightweight | < 10 MB | 20-30 | < 1 GB |

**Total Memory Budget (Stage A):**
- Base system: 4 GB
- Operations: 10-25 GB
- Temp files: 10-20 GB
- Buffer: 5-10 GB
- **Total: 29-59 GB** (recommend 32-64 GB)

### Disk I/O Considerations

**High I/O Operations:**
- Video processing (reading/writing large files)
- PDF to images (reading PDF, writing multiple images)
- Archive extraction (reading/writing many files)
- Large file uploads/downloads

**Mitigation:**
- Use SSD storage (not HDD)
- Separate temp directory on fast disk
- Move to S3 for long-term storage
- Implement disk I/O monitoring

### Network Bandwidth

**High Bandwidth Operations:**
- Large file uploads (700MB max)
- Video file downloads
- Batch operations (multiple files)

**Bandwidth Requirements:**
- Upload: 1 Gbps (for concurrent large uploads)
- Download: 1 Gbps (for serving converted files)
- API calls: < 100 Mbps (transcription, currency)

### Worker Scaling Guidelines

**Scale I/O Workers When:**
- Queue length > 50 for `transcription` or `api_calls`
- Average wait time > 2 minutes
- CPU usage < 50% (indicating I/O bottleneck)

**Scale CPU Workers When:**
- Queue length > 20 for CPU-bound queues
- Average wait time > 5 minutes
- CPU usage consistently > 80%
- Memory usage < 80% (CPU is bottleneck, not memory)

**Scale Lightweight Workers When:**
- Queue length > 100
- Average wait time > 10 seconds
- Response time degradation

### Resource Monitoring

**Key Metrics to Track:**
- Queue length per queue type
- Average processing time per operation type
- CPU usage per worker process
- Memory usage per worker process
- Disk I/O wait time
- Network bandwidth utilization
- Error rates per operation type

**Alert Thresholds:**
- Queue length > 100: Warning
- Queue length > 500: Critical
- CPU usage > 90% for 5 minutes: Warning
- Memory usage > 90%: Critical
- Error rate > 5%: Warning
- Error rate > 10%: Critical

---

## Risk List & Mitigations

### Risk 1: Whisper API Rate Limits / Failures
**Impact:** High — all transcriptions fail  
**Mitigation:**
- Circuit breaker (stop sending if >50% fail in 5 minutes)
- Exponential backoff retries (max 3 retries)
- Queue jobs, don't fail immediately
- Monitor API status page
- Consider backup provider (e.g., AssemblyAI)

### Risk 2: Database Connection Exhaustion
**Impact:** High — site becomes unresponsive  
**Mitigation:**
- Set `CONN_MAX_AGE = 300` (Stage A)
- Deploy PgBouncer (Stage B)
- Monitor `pg_stat_activity`
- Set per-worker connection limits
- Use read replicas for reporting

### Risk 3: Disk Space Exhaustion (Before S3 Migration)
**Impact:** Medium — uploads fail, temp files accumulate  
**Mitigation:**
- Monitor disk usage (alert at 80%)
- Cleanup temp files after 24 hours (Celery periodic task)
- Move to S3 ASAP (Phase 4)
- Set disk quotas

### Risk 4: Queue Backlog / Worker Overload
**Impact:** Medium — long wait times, user complaints  
**Mitigation:**
- Monitor queue length (alert if >100)
- Auto-scale workers (Stage B)
- Queue limits (reject new jobs if queue >1000)
- Show estimated wait time to users
- Priority queue for paid users (Stage B)

### Risk 5: Cost Overrun (OpenAI API)
**Impact:** Medium — unexpected bills  
**Mitigation:**
- Track cost per job (log to database)
- Daily cost alerts (if >$X/day)
- Enforce per-IP quotas (10/day default)
- Monitor usage dashboard
- Set budget alerts in cloud provider

### Risk 6: CPU Exhaustion (FFmpeg/PDF Processing)
**Impact:** High — all CPU-bound operations slow down or fail  
**Mitigation:**
- Separate worker queues for CPU-bound operations
- Limit concurrency per CPU worker (2-4 max)
- Monitor CPU usage per worker
- Scale CPU workers horizontally (Stage B)
- Use CPU limits in Docker (`--cpus`)
- Prioritize operations (transcription > media > PDF)

### Risk 7: Memory Exhaustion (Large File Processing)
**Impact:** High — workers killed by OOM, operations fail  
**Mitigation:**
- Monitor memory usage per worker
- Set memory limits in Docker (`--memory`)
- Limit concurrent operations per worker
- Use streaming for large files (where possible)
- Scale workers horizontally (Stage B)
- Move large files to S3 ASAP

### Risk 8: Disk Space Exhaustion (Temp Files)
**Impact:** High — uploads fail, operations fail  
**Mitigation:**
- Monitor disk usage (alert at 80%)
- Cleanup temp files after 24 hours (Celery periodic task)
- Move to S3 ASAP (Phase 4)
- Set disk quotas per worker
- Use separate temp directory with size limits
- Implement automatic cleanup on job completion

### Risk 9: Long-Running Operations Blocking Workers
**Impact:** Medium — queue backlog, user complaints  
**Mitigation:**
- Separate queues for long operations (video merge: 40 min)
- Dedicated workers for long operations
- Timeout strategies (soft/hard limits)
- Progress tracking for long operations
- User notifications (estimated completion time)
- Priority queue for fast operations

### Risk 10: FFmpeg/System Dependency Failures
**Impact:** Medium — media operations fail  
**Mitigation:**
- Health checks for FFmpeg availability
- Graceful degradation (show error, don't crash)
- Monitor FFmpeg process failures
- Automatic restart of workers on failure
- Fallback error messages for users
- System dependency monitoring

---

## Concrete Code Changes

### New Files to Create

**1. `flipunit/celery.py`**
```python
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'flipunit.settings')

app = Celery('flipunit')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
```

**2. `flipunit/__init__.py` (update)**
```python
from .celery import app as celery_app

__all__ = ('celery_app',)
```

**3. `text_converter/models.py` (add TranscriptionJob, UserQuota)**

**4. `text_converter/tasks.py` (new file)**
```python
from celery import shared_task
from .models import TranscriptionJob
# ... transcription logic here
```

**5. `media_converter/tasks.py` (new file)**
```python
from celery import shared_task
from .models import MediaJob
# ... media conversion logic here
```

**6. `pdf_tools/tasks.py` (new file)**
```python
from celery import shared_task
from .models import PDFJob
# ... PDF processing logic here
```

**7. `image_converter/tasks.py` (new file)**
```python
from celery import shared_task
from .models import ImageJob
# ... image processing logic here
```

**8. `flipunit/middleware.py` (new file, quota middleware)**

### Settings to Add (`flipunit/settings.py`)

```python
# Redis
REDIS_URL = os.environ.get('REDIS_URL', 'redis://redis:6379/0')

# Celery
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_TASK_ACKS_LATE = True
CELERY_WORKER_PREFETCH_MULTIPLIER = 1

# Queue routing (see Worker Queue Architecture section for details)
CELERY_TASK_ROUTES = {
    'text_converter.tasks.transcribe_audio_task': {'queue': 'transcription'},
    'text_converter.tasks.generate_docx_task': {'queue': 'lightweight'},
    'media_converter.tasks.*': {'queue': 'media_processing'},
    'pdf_tools.tasks.*': {'queue': 'pdf_processing'},
    'image_converter.tasks.*': {'queue': 'image_processing'},
    'archive_converter.tasks.*': {'queue': 'archive_processing'},
    'currency_converter.tasks.*': {'queue': 'api_calls'},
    'ai_chat.tasks.*': {'queue': 'api_calls'},
}

# Sessions (Redis)
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

# Cache (Redis)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', 'redis://redis:6379/1'),
    }
}

# Database connection pooling
DATABASES['default']['CONN_MAX_AGE'] = 300

# S3 Storage (when ready)
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME')
AWS_S3_REGION_NAME = os.environ.get('AWS_S3_REGION_NAME', 'eu-north-1')
```

### Views to Modify (`text_converter/views.py`)

- `audio_transcription()`: Return `job_id` immediately, enqueue task
- Add `job_status(request, job_id)`: Return JSON status
- Add `download_transcript(request, job_id)`: Return transcript file
- Add `download_docx(request, job_id)`: Return DOCX file

### URLs to Add (`text_converter/urls.py`)

```python
path('audio-transcription/status/<uuid:job_id>/', views.job_status, name='job_status'),
path('audio-transcription/download/<uuid:job_id>/', views.download_transcript, name='download_transcript'),
path('audio-transcription/download-docx/<uuid:job_id>/', views.download_docx, name='download_docx'),
```

### Docker Compose Changes (`docker-compose.yml`)

Add Redis service:
```yaml
redis:
  image: redis:7-alpine
  container_name: flipunit-redis
  restart: unless-stopped
  volumes:
    - redis-data:/data
  networks:
    - flipunit-network
```

Add Celery worker services (multiple workers for different queues):
```yaml
celery_worker_io:
  build: .
  container_name: flipunit-celery-io
  restart: unless-stopped
  command: celery -A flipunit worker -Q transcription,api_calls --loglevel=info --concurrency=10
  environment: [same as web]
  volumes: [same as web]
  depends_on:
    - postgres
    - redis
  networks:
    - flipunit-network

celery_worker_media:
  build: .
  container_name: flipunit-celery-media
  restart: unless-stopped
  command: celery -A flipunit worker -Q media_processing --loglevel=info --concurrency=2
  environment: [same as web]
  volumes: [same as web]
  depends_on:
    - postgres
    - redis
  networks:
    - flipunit-network

celery_worker_pdf:
  build: .
  container_name: flipunit-celery-pdf
  restart: unless-stopped
  command: celery -A flipunit worker -Q pdf_processing --loglevel=info --concurrency=2
  environment: [same as web]
  volumes: [same as web]
  depends_on:
    - postgres
    - redis
  networks:
    - flipunit-network

celery_worker_image:
  build: .
  container_name: flipunit-celery-image
  restart: unless-stopped
  command: celery -A flipunit worker -Q image_processing --loglevel=info --concurrency=6
  environment: [same as web]
  volumes: [same as web]
  depends_on:
    - postgres
    - redis
  networks:
    - flipunit-network

celery_worker_lightweight:
  build: .
  container_name: flipunit-celery-lightweight
  restart: unless-stopped
  command: celery -A flipunit worker -Q lightweight --loglevel=info --concurrency=20
  environment: [same as web]
  volumes: [same as web]
  depends_on:
    - postgres
    - redis
  networks:
    - flipunit-network
```

### Nginx Changes (`nginx_config_fixed.conf`)

```nginx
# Increase timeouts for async jobs
proxy_read_timeout 600s;

# Rate limiting
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/m;
location /text-converter/audio-transcription/ {
    limit_req zone=api_limit burst=2;
    proxy_pass http://localhost:8000;
}
```

### Requirements Updates (`requirements.txt`)

```
redis>=5.0.0
celery>=5.3.0
django-ratelimit>=4.0.0
boto3>=1.28.0
django-storages>=1.14.0
sentry-sdk>=1.32.0
```

---

## Summary

This plan transforms the synchronous converter system into an async, scalable architecture supporting all operation types:
- **I/O-bound operations:** Transcription (OpenAI API), currency converter, AI chat
- **CPU-bound operations:** Media conversion (FFmpeg), PDF processing (OCR, rendering), image processing, archive conversion
- **Lightweight operations:** Text converters, developer tools, utilities

**Key Architecture Decisions:**
1. **Specialized Worker Queues:** Separate queues for I/O-bound (high concurrency) and CPU-bound (low concurrency) operations
2. **Resource-Aware Allocation:** CPU workers for media/PDF, I/O workers for transcription/API calls
3. **Timeout Strategies:** Operation-specific timeouts (40 min for video merge, 15 min for transcription, 5 min for images)
4. **Cost Control:** Track and limit OpenAI API costs, implement quotas per operation type
5. **Scalability:** Stage A handles hundreds on single VPS, Stage B scales to thousands with multi-node architecture

**Stage A (Hundreds):** Single VPS (8-16 cores, 32-64GB RAM) with specialized Celery workers for each operation type.  
**Stage B (Thousands):** Multi-node with dedicated I/O worker nodes and separate CPU worker nodes for media, PDF, and image processing.

**Priority:** Implement Phase 1-3 first (Celery + Redis + specialized queues + rate limiting) to handle hundreds of concurrent users. Then proceed to object storage and multi-node setup for thousands.

