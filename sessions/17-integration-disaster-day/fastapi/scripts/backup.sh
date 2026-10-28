#!/usr/bin/env bash
# Backs up PostgreSQL and MongoDB into backups/<timestamp>/, plus a snapshot of counts.
# Redis is not backed up: its data is derived and is restored by rebuilding it.
# Usage: ./scripts/backup.sh
set -euo pipefail
source "$(dirname "$0")/common.sh"

dir="$project_dir/backups/$(date +%F_%H%M%S)"
mkdir -p "$dir"

compose exec -T postgres pg_dump -U "$PG_USER" -Fc "$PG_DB" > "$dir/postgres.dump"
compose exec -T mongo mongodump --uri "$MONGO_URL" --db "$MONGO_DB" --archive --gzip --quiet > "$dir/mongo.archive.gz"
py -m scripts.snapshot --save "$dir/snapshot.json" > /dev/null

echo "Backup in ${dir#$project_dir/}:"
ls -lh "$dir" | tail -n +2 | awk '{print "  " $5 "\t" $9}'
