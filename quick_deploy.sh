#!/bin/bash

# Quick deployment script for template/static file changes
# Run this on your VPS at /opt/flipunit

set -e

PROJECT_DIR="/opt/flipunit"

echo "🚀 Quick Deployment"
echo "==================="
echo ""

cd "$PROJECT_DIR"

echo "📥 Pulling latest code from main..."
git pull origin main

# Check if requirements.txt changed (might need to reinstall dependencies)
if git diff HEAD@{1} HEAD --name-only | grep -q "requirements.txt"; then
    echo "📦 Requirements changed - Installing new dependencies..."
    docker-compose exec -T web pip install -r requirements.txt
fi

echo "📦 Collecting static files..."
docker-compose exec -T web python manage.py collectstatic --noinput

echo "🔄 Restarting web container..."
docker-compose restart web

echo ""
echo "✅ Deployment complete!"
echo ""
echo "🔍 Verify deployment:"
echo "   docker-compose logs -f web"
echo "   curl -I https://flipunit.eu/pdf-tools/to-epub/"


