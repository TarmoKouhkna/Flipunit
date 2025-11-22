#!/bin/bash
# Deployment script for Google Tag Manager update
# Run this on your VPS server at /opt/flipunit

echo "🚀 Deploying Google Tag Manager update..."

# Navigate to application directory
cd /opt/flipunit

# Pull latest code from GitHub
echo "📥 Pulling latest code..."
git pull origin main

# Since templates are mounted as a volume, just restart the web container
echo "🔄 Restarting web container..."
docker-compose restart web

# Check status
echo "✅ Checking container status..."
docker-compose ps

echo "✨ Deployment complete! GTM should now be live on all pages."





