#!/usr/bin/env bash
# Restores one engine from the newest backup (or the folder given) and prints how long it took.
# Usage: ./scripts/restore.sh <postgres|mongo|redis> [backups/<timestamp>]
set -euo pipefail
source "$(dirname "$0")/common.sh"

engine="${1:?Usage: restore.sh <postgres|mongo|redis> [backup dir]}"
dir="${2:-$(latest_backup)}"
start=$(date +%s)

case "$engine" in
    postgres)
        echo "Restoring $PG_DB from ${dir#$project_dir/}"
        # Creates the database if it is gone; does nothing if it still exists.
        "$repo_root/scripts/create-db.sh" "$PG_DB"
        # --clean --if-exists drops each object before recreating it, so the restore
        # also works on a database that still has (damaged) tables.
        compose exec -T postgres pg_restore -U "$PG_USER" -d "$PG_DB" --no-owner --clean --if-exists \
            < "$dir/postgres.dump"
        ;;
    mongo)
        echo "Restoring $MONGO_DB from ${dir#$project_dir/}"
        # The archive only holds MONGO_DB, so --drop only replaces this project's collections.
        compose exec -T mongo mongorestore --uri "$MONGO_URL" --archive --gzip --drop --quiet \
            < "$dir/mongo.archive.gz"
        ;;
    redis)
        echo "Rebuilding Redis from PostgreSQL (derived data, no backup file)"
        py -m scripts.rebuild_redis
        ;;
    *)
        echo "Unknown engine: $engine (use postgres, mongo or redis)" >&2
        exit 1
        ;;
esac

echo "$engine restored in $(( $(date +%s) - start )) s"
