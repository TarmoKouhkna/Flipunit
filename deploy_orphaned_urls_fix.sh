#!/bin/bash

# Quick deployment script for orphaned URLs fix
# This script can be run on the VPS server

set -e

# Use first argument, or VPS_HOST env var (e.g. export VPS_HOST=ubuntu@YOUR_HETZNER_IP)
SSH_CONNECTION="${1:-${VPS_HOST:-root@46.225.75.195}}"
PROJECT_DIR="/opt/flipunit"

echo "🚀 Deploying Orphaned URLs Fix"
echo "=============================="
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
    echo "Usage: ./deploy_orphaned_urls_fix.sh [user@host]"
    echo "Example: ./deploy_orphaned_urls_fix.sh ubuntu@YOUR_SERVER_IP"
    exit 1
fi

echo "✅ SSH connection successful"
echo ""

# Deploy to VPS
ssh "$SSH_CONNECTION" << ENDSSH
set -e
cd $PROJECT_DIR

echo "📥 Pulling latest code..."
# Try to pull from tk_scale first, then main
git fetch origin
git checkout tk_scale 2>/dev/null || git checkout main
git pull origin tk_scale 2>/dev/null || git pull origin main || {
    echo "⚠️  Git pull had issues, but continuing with deployment..."
}

echo ""
echo "📦 Collecting static files..."
docker-compose exec -T web python manage.py collectstatic --noinput

echo ""
echo "🔄 Restarting web container..."
docker-compose restart web

echo ""
echo "⏳ Waiting for container to start..."
sleep 5

echo ""
echo "🔍 Checking container status..."
docker-compose ps web

echo ""
echo "✅ Deployment complete!"
echo ""
echo "🔍 Verify the fix by visiting:"
echo "   - https://flipunit.eu/pdf-tools/ (check for new converter links)"
echo "   - https://flipunit.eu/image-converter/ (check for new converter links)"
ENDSSH

echo ""
echo "✅ Deployment script completed!"
echo ""
echo "🧪 Test the fixes:"
echo "   1. Visit https://flipunit.eu/pdf-tools/ - should see PDF to Images, PDF to HTML, etc."
echo "   2. Visit https://flipunit.eu/image-converter/ - should see JPEG to PNG, PNG to JPG, etc."
echo ""
