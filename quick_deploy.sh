#!/bin/bash

# Quick deployment script for template/static file changes
# Run this on your VPS at /opt/flipunit

set -e

PROJECT_DIR="/opt/flipunit"

echo "🚀 Quick Deployment - Template Changes"
echo "========================================"
echo ""

cd "$PROJECT_DIR"

echo "📥 Pulling latest code from main..."
git pull origin main

echo "📦 Collecting static files..."
docker-compose exec -T web python manage.py collectstatic --noinput

echo "🔄 Restarting web container..."
docker-compose restart web

echo ""
echo "✅ Deployment complete!"
echo ""
echo "🔍 Verify deployment:"
echo "   docker-compose logs -f web"
echo "   curl -I https://flipunit.eu/media-converter/audio-converter/"


