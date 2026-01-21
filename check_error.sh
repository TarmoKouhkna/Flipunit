#!/bin/bash
# Quick script to check server logs
ssh ubuntu@217.146.78.140 << 'ENDSSH'
cd /opt/flipunit
echo "=== Recent Web Container Logs ==="
docker-compose logs --tail=100 web | tail -50
ENDSSH
