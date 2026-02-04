#!/bin/bash
# Quick script to check server logs. Set VPS_HOST if needed: export VPS_HOST=ubuntu@YOUR_SERVER_IP
VPS_HOST="${VPS_HOST:-ubuntu@217.146.78.140}"
ssh "$VPS_HOST" << 'ENDSSH'
cd /opt/flipunit
echo "=== Recent Web Container Logs ==="
docker-compose logs --tail=100 web | tail -50
ENDSSH
