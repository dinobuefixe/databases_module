#!/usr/bin/env bash
# Backs up PostgreSQL and MongoDB into backups/<timestamp>/ and records the counts at that moment.
# Redis is not backed up: every key in it is derived from PostgreSQL and is rebuilt on restore.
source "$(dirname "$0")/lib.sh"

dir="backups/$(date +%Y%m%d-%H%M%S)"
mkdir -p "$dir"

compose exec -T postgres pg_dump -U "$PG_USER" -Fc "$PG_DB" > "$dir/postgres.dump"
compose exec -T mongo mongodump --quiet --uri "$MONGO_URL" --db "$MONGO_DB" --archive --gzip > "$dir/mongo.archive.gz"
{ pg_counts psql_live -d "$PG_DB"; mongo_counts mongosh_live; } > "$dir/counts.txt"

ln -sfn "$(basename "$dir")" backups/latest
echo "Backup in $dir:"
ls -lh "$dir" | tail -n +2
