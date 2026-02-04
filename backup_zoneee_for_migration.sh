#!/bin/bash
# Phase 2: Backup on Zone.ee VPS (run this ON the Zone.ee server in /opt/flipunit)
# Usage: SSH to Zone.ee, then: cd /opt/flipunit && bash backup_zoneee_for_migration.sh
# Or from your Mac: ssh ubuntu@217.146.78.140 'cd /opt/flipunit && bash -s' < backup_zoneee_for_migration.sh

set -e

PROJECT_DIR="${1:-/opt/flipunit}"
cd "$PROJECT_DIR"

echo "=== Phase 2: Backup for Hetzner migration ==="
echo "Working directory: $PROJECT_DIR"
echo ""

# 1. Database dump
DB_BACKUP="backup_db_$(date +%Y%m%d_%H%M).sql"
echo "1. Dumping database to $DB_BACKUP ..."
docker-compose exec -T postgres pg_dump -U flipunit_user flipunit > "$DB_BACKUP"
echo "   Done. Size: $(du -h "$DB_BACKUP" | cut -f1)"
echo ""

# 2. Media and staticfiles
MEDIA_BACKUP="backup_media_$(date +%Y%m%d).tar.gz"
echo "2. Archiving media and staticfiles to $MEDIA_BACKUP ..."
MEDIA_DIRS=""
[ -d media ] && MEDIA_DIRS="media"
[ -d staticfiles ] && MEDIA_DIRS="$MEDIA_DIRS staticfiles"
MEDIA_DIRS=$(echo "$MEDIA_DIRS" | xargs)
if [ -n "$MEDIA_DIRS" ]; then
  tar -czvf "$MEDIA_BACKUP" -C "$PROJECT_DIR" $MEDIA_DIRS
  echo "   Done. Size: $(du -h "$MEDIA_BACKUP" | cut -f1)"
else
  echo "   Skipped (media/ and staticfiles/ not found)"
fi
echo ""

# 3. Remind about .env and nginx
echo "3. Manual steps (from your Mac):"
echo "   Copy backup files to your Mac:"
echo "     scp ${VPS_HOST:-ubuntu@217.146.78.140}:$PROJECT_DIR/$DB_BACKUP ."
echo "     scp ${VPS_HOST:-ubuntu@217.146.78.140}:$PROJECT_DIR/$MEDIA_BACKUP ."
echo ""
echo "   Copy .env (secrets - do not commit):"
echo "     scp ${VPS_HOST:-ubuntu@217.146.78.140}:$PROJECT_DIR/.env ./env.backup"
echo ""
echo "   Copy nginx config:"
echo "     scp ${VPS_HOST:-ubuntu@217.146.78.140}:/etc/nginx/sites-available/flipunit.eu ./nginx_flipunit.eu.conf"
echo ""
echo "=== Backup on server complete. Copy files above to your Mac before Phase 3. ==="
