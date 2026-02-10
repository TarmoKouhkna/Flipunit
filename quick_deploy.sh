#!/bin/bash

# Quick deployment script for template/static file changes
# Run this on your VPS at /opt/flipunit

set -e

PROJECT_DIR="/opt/flipunit"

# Use "docker compose" (plugin) if "docker-compose" (standalone) is not found
if command -v docker-compose &>/dev/null; then
    DOCKER_COMPOSE="docker-compose"
else
    DOCKER_COMPOSE="docker compose"
fi

echo "🚀 Quick Deployment"
echo "==================="
echo ""

cd "$PROJECT_DIR"

# Check for uncommitted changes and stash them if needed
if ! git diff-index --quiet HEAD --; then
    echo "⚠️  Uncommitted local changes detected. Stashing them..."
    git stash push -m "Auto-stash before deployment $(date +%Y-%m-%d_%H:%M:%S)"
    echo "✅ Local changes stashed"
fi

echo "📥 Pulling latest code from main..."
git pull origin main

# Check if requirements.txt changed (might need to reinstall dependencies)
if git diff HEAD@{1} HEAD --name-only | grep -q "requirements.txt"; then
    echo "📦 Requirements changed - Installing new dependencies..."
    $DOCKER_COMPOSE exec -T web pip install -r requirements.txt
fi

echo "📦 Running migrations..."
$DOCKER_COMPOSE exec -T web python manage.py migrate --noinput

echo "📦 Minifying CSS..."
$DOCKER_COMPOSE exec -T web python manage.py minify_css

echo "📦 Collecting static files..."
$DOCKER_COMPOSE exec -T web python manage.py collectstatic --noinput

echo "🔄 Restarting web container..."
$DOCKER_COMPOSE restart web

echo ""
echo "✅ Deployment complete!"
echo ""
echo "🔍 Verify deployment:"
echo "   $DOCKER_COMPOSE logs -f web"
echo "   curl -I https://flipunit.eu/pdf-tools/to-epub/"


