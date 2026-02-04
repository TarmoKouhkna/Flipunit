#!/bin/bash
# Phase 3: Run this ON the Hetzner server after code is in /opt/flipunit, .env is in place,
# and backup_db_*.sql (and optionally backup_media_*.tar.gz) have been copied to /opt/flipunit.
#
# Usage: cd /opt/flipunit && bash deploy_phase3_hetzner.sh [backup_db_YYYYMMDD_HHMM.sql]
# If no arg, uses the latest backup_db_*.sql in the current directory.

set -e

cd /opt/flipunit

DB_BACKUP="${1:-$(ls -t backup_db_*.sql 2>/dev/null | head -1)}"
if [ -z "$DB_BACKUP" ] || [ ! -f "$DB_BACKUP" ]; then
  echo "No database backup found. Put backup_db_*.sql in /opt/flipunit or pass it as argument."
  exit 1
fi

echo "=== Phase 3: Deploy on Hetzner ==="
echo "Using DB backup: $DB_BACKUP"
echo ""

# 1. Start Postgres only, wait for it
echo "1. Starting Postgres..."
docker compose up -d postgres
echo "   Waiting for Postgres to be ready..."
sleep 15
echo ""

# 2. Restore database (drop and recreate public schema content via clean restore)
echo "2. Restoring database from $DB_BACKUP..."
docker compose exec -T postgres psql -U flipunit_user -d flipunit -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public; GRANT ALL ON SCHEMA public TO flipunit_user; GRANT ALL ON SCHEMA public TO public;" 2>/dev/null || true
cat "$DB_BACKUP" | docker compose exec -T postgres psql -U flipunit_user -d flipunit -q
echo "   Done."
echo ""

# 3. Extract media/static if tarball present
MEDIA_TARBALL="$(ls -t backup_media_*.tar.gz 2>/dev/null | head -1)"
if [ -n "$MEDIA_TARBALL" ] && [ -f "$MEDIA_TARBALL" ]; then
  echo "3. Extracting $MEDIA_TARBALL..."
  tar -xzvf "$MEDIA_TARBALL" -C /opt/flipunit
  echo "   Done."
else
  echo "3. No backup_media_*.tar.gz found, skipping media/static restore."
fi
echo ""

# 4. Build and start all services
echo "4. Building and starting all containers (this may take several minutes)..."
docker compose build
docker compose up -d
echo ""

echo "5. Waiting for web to be up..."
sleep 10
docker compose ps
echo ""

# Quick test
if curl -s -o /dev/null -w "%{http_code}" -H "Host: flipunit.eu" http://localhost:8000/ | grep -q "200\|301\|302"; then
  echo "=== Phase 3 server steps complete. Web responds on port 8000."
  echo "Next: configure Nginx (see DEPLOYMENT.md Phase 3) and then run Certbot after DNS switch."
else
  echo "=== Containers are up. If curl test failed, check: docker compose logs web"
fi
