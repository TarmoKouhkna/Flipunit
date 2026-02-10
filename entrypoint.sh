#!/bin/bash
# FlipUnit Docker entrypoint - optimized to prevent 504 Gateway Timeout on restart
# Problem: Running migrate + collectstatic before Gunicorn blocks for 30-90+ seconds.
# Solution: Skip collectstatic on restart (quick_deploy.sh runs it before restart).
#          Only run collectstatic when staticfiles is empty (first deploy).
set -e

echo "[entrypoint] Running database migrations..."
python manage.py migrate --noinput

# Skip collectstatic on restart - quick_deploy.sh runs it before restart.
# Only run when staticfiles is empty (first deploy, fresh volume).
if [ -z "$(ls -A /app/staticfiles 2>/dev/null)" ]; then
    echo "[entrypoint] Staticfiles empty - running collectstatic (first deploy)..."
    python manage.py collectstatic --noinput
else
    echo "[entrypoint] Staticfiles exists - skipping collectstatic (already run by deploy)"
fi

# Calculate workers: (2 * CPU) + 1, cap at 17
CPU_COUNT=$(nproc 2>/dev/null || echo 4)
WORKERS=$((2 * CPU_COUNT + 1))
[ $WORKERS -gt 17 ] && WORKERS=17

echo "[entrypoint] Starting Gunicorn with $WORKERS workers..."
exec gunicorn flipunit.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers $WORKERS \
    --threads 2 \
    --timeout 600 \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --access-logfile - \
    --error-logfile -
