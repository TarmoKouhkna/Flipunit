#!/bin/bash
# Script to check server logs for the 500 error
# Set VPS_HOST if needed: export VPS_HOST=ubuntu@YOUR_SERVER_IP

VPS_HOST="${VPS_HOST:-ubuntu@217.146.78.140}"
echo "🔍 Checking server logs for errors (${VPS_HOST})..."
echo ""

ssh "$VPS_HOST" << 'ENDSSH'
cd /opt/flipunit

echo "=== Last 100 lines of web container logs ==="
docker-compose logs --tail=100 web | grep -i -A 5 -B 5 "error\|exception\|traceback\|500" | tail -80

echo ""
echo "=== Testing if the page loads ==="
docker-compose exec -T web python manage.py shell << 'PYTHON'
from django.test import Client
c = Client()
response = c.get('/pdf-tools/universal/')
print(f"Status Code: {response.status_code}")
if response.status_code != 200:
    print(f"Response content: {response.content[:500]}")
PYTHON
ENDSSH
