#!/bin/bash

# Complete Stage A Deployment Script
# This script deploys all Stage A Implementation Plan features:
# - Celery + Redis background job system
# - Specialized worker queues for all converters
# - Job status tracking and APIs
# - Observability (health checks, logging, Sentry)
# - Gunicorn and Nginx optimizations
# - Rate limiting and quotas

set -e

# Use first argument, or VPS_HOST env var (e.g. export VPS_HOST=ubuntu@YOUR_HETZNER_IP)
SSH_CONNECTION="${1:-${VPS_HOST:-ubuntu@217.146.78.140}}"
PROJECT_DIR="/opt/flipunit"

echo "🚀 Stage A Implementation Plan - Complete Deployment"
echo "===================================================="
echo ""
echo "SSH Connection: $SSH_CONNECTION"
echo "Project Directory: $PROJECT_DIR"
echo ""

# Check SSH connection
echo "🔌 Testing SSH connection..."
if ! ssh -o ConnectTimeout=5 -o BatchMode=yes "$SSH_CONNECTION" exit 2>/dev/null; then
    echo "❌ SSH connection failed"
    echo ""
    echo "Please ensure:"
    echo "  1. You have SSH access to the server"
    echo "  2. Your SSH key is added to the server"
    echo "  3. The connection string is correct"
    echo ""
    echo "Usage: ./deploy_stage_a.sh [user@host]"
    echo "Example: ./deploy_stage_a.sh ubuntu@YOUR_SERVER_IP"
    exit 1
fi

echo "✅ SSH connection successful"
echo ""

# Deploy to VPS
echo "📥 Deploying Stage A implementation to VPS..."
echo ""

ssh "$SSH_CONNECTION" << ENDSSH
set -e
cd $PROJECT_DIR

echo "📥 Step 1: Pulling latest code from main..."
git pull origin main || {
    echo "❌ Git pull failed. Check if you're on the correct branch."
    exit 1
}

echo ""
echo "📦 Step 2: Running database migrations..."
docker-compose exec -T web python manage.py migrate --noinput

echo ""
echo "📦 Step 3: Collecting static files..."
docker-compose exec -T web python manage.py collectstatic --noinput

echo ""
echo "🔨 Step 4: Rebuilding Docker images (with unrar and all dependencies)..."
echo "This may take several minutes..."
docker-compose build --no-cache web celery_worker_io celery_worker_media celery_worker_pdf celery_worker_image celery_worker_archive celery_worker_lightweight

echo ""
echo "🔄 Step 5: Restarting all services..."
docker-compose down
docker-compose up -d

echo ""
echo "⏳ Step 6: Waiting for services to start..."
sleep 10

echo ""
echo "🔍 Step 7: Checking service status..."
docker-compose ps

echo ""
echo "✅ Stage A deployment complete!"
echo ""
echo "📋 Deployed Features:"
echo "  ✅ Celery + Redis background job system"
echo "  ✅ Specialized worker queues (IO, Media, PDF, Image, Archive, Lightweight)"
echo "  ✅ Job status tracking and APIs for all converters"
echo "  ✅ Health check endpoint (/health/)"
echo "  ✅ Structured logging and Sentry integration"
echo "  ✅ Gunicorn optimization (9 workers, 2 threads)"
echo "  ✅ Nginx tuning (600s timeouts, rate limiting, gzip)"
echo "  ✅ Database connection pooling (CONN_MAX_AGE=300)"
echo "  ✅ Redis sessions and cache"
echo ""
ENDSSH

echo ""
echo "🧪 Step 8: Verifying deployment..."
echo ""

# Verify health check
echo "Testing health check endpoint..."
if curl -s -o /dev/null -w "%{http_code}" "https://flipunit.eu/health/" | grep -q "200"; then
    echo "✅ Health check endpoint is working"
else
    echo "⚠️  Health check endpoint might not be accessible yet"
fi

echo ""
echo "📋 Deployment Summary"
echo "===================="
echo "✅ Code pulled from main"
echo "✅ Database migrations run"
echo "✅ Static files collected"
echo "✅ Docker images rebuilt"
echo "✅ All services restarted"
echo ""
echo "🔍 Next steps:"
echo "   1. Visit: https://flipunit.eu/health/ to verify health check"
echo "   2. Test async converters (audio, video, PDF, image, archive)"
echo "   3. Check logs: ssh $SSH_CONNECTION 'cd $PROJECT_DIR && docker-compose logs -f'"
echo "   4. Monitor workers: ssh $SSH_CONNECTION 'cd $PROJECT_DIR && docker-compose ps'"
echo ""
echo "✅ Stage A deployment complete!"
