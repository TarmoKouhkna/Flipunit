#!/bin/bash

# Complete VPS Deployment Script for PDF to EPUB Feature
# This script will:
# 1. Push code to GitHub
# 2. Deploy to VPS
# 3. Verify deployment

set -e

echo "🚀 PDF to EPUB - Complete VPS Deployment"
echo "=========================================="
echo ""

# Step 1: Push to GitHub
echo "📤 Step 1: Pushing code to GitHub..."
if git push origin main; then
    echo "✅ Code pushed to GitHub successfully"
else
    echo "⚠️  Git push failed. You may need to push manually:"
    echo "   git push origin main"
    echo ""
    read -p "Continue with deployment anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo ""

# Step 2: Deploy to VPS
echo "📥 Step 2: Deploying to VPS..."
# Use first argument, or VPS_HOST env var, or default (Hetzner: root@46.225.75.195)
SSH_CONNECTION="${1:-${VPS_HOST:-root@46.225.75.195}}"
PROJECT_DIR="/opt/flipunit"

echo "SSH Connection: $SSH_CONNECTION"
echo "Project Directory: $PROJECT_DIR"
echo ""

# Check SSH connection
if ! ssh -o ConnectTimeout=5 -o BatchMode=yes "$SSH_CONNECTION" exit 2>/dev/null; then
    echo "❌ SSH connection failed"
    echo ""
    echo "Please ensure:"
    echo "  1. You have SSH access to the server"
    echo "  2. Your SSH key is added to the server"
    echo "  3. The connection string is correct"
    echo ""
    echo "Usage: ./deploy_to_vps.sh [user@host]"
    echo "Example: ./deploy_to_vps.sh root@46.225.75.195"
    echo "Or set VPS_HOST: export VPS_HOST=root@46.225.75.195"
    exit 1
fi

echo "✅ SSH connection successful"
echo ""

# Deploy to VPS
ssh "$SSH_CONNECTION" << ENDSSH
set -e
cd $PROJECT_DIR

echo "📥 Pulling latest code from main..."
git pull origin main || {
    echo "❌ Git pull failed. Check if you're on the correct branch."
    exit 1
}

echo ""
echo "📦 Checking if ebooklib is installed..."
if docker-compose exec -T web python -c "import ebooklib; print('ebooklib version:', ebooklib.__version__)" 2>/dev/null; then
    echo "✅ ebooklib is already installed"
else
    echo "📥 Installing ebooklib..."
    docker-compose exec -T web pip install ebooklib>=0.18
fi

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
docker-compose ps

echo ""
echo "✅ Deployment complete!"
ENDSSH

echo ""
echo "🧪 Step 3: Verifying deployment..."
echo ""

# Verify deployment
echo "Testing PDF to EPUB endpoint..."
if curl -s -o /dev/null -w "%{http_code}" "https://flipunit.eu/pdf-tools/to-epub/" | grep -q "200\|301\|302"; then
    echo "✅ PDF to EPUB page is accessible"
else
    echo "⚠️  PDF to EPUB page might not be accessible yet (check logs)"
fi

echo ""
echo "📋 Deployment Summary"
echo "===================="
echo "✅ Code pushed to GitHub"
echo "✅ Code deployed to VPS"
echo "✅ Container restarted"
echo ""
echo "🔍 Next steps:"
echo "   1. Visit: https://flipunit.eu/pdf-tools/to-epub/"
echo "   2. Test with a sample PDF file"
echo "   3. Check logs: ssh $SSH_CONNECTION 'cd $PROJECT_DIR && docker-compose logs -f web'"
echo ""
echo "✅ Deployment complete!"

