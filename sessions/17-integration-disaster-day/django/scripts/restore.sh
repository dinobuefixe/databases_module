#!/usr/bin/env bash
# Restores one engine from the newest backup. Usage: scripts/restore.sh <postgres|mongo|redis>
set -euo pipefail
source "$(dirname "$0")/_env.sh"

engine="${1:?Usage: scripts/restore.sh <postgres|mongo|redis>}"
SECONDS=0

case "$engine" in
    postgres)
        dump="$(latest 'postgres_*.dump')"
        [ -n "$dump" ] || { echo "No PostgreSQL dump in backups/" >&2; exit 1; }
        echo "Restoring $dump into $PG_DB"
        # After the volume is lost the database does not exist yet.
        if ! compose exec -T postgres psql -U "$POSTGRES_USER" -d postgres -tAc \
                "SELECT 1 FROM pg_database WHERE datname = '$PG_DB'" | grep -q 1; then
            compose exec -T postgres createdb -U "$POSTGRES_USER" "$PG_DB"
        fi
        # --clean --if-exists replaces objects that are still there; on an empty database it does nothing.
        compose exec -T postgres pg_restore -U "$POSTGRES_USER" -d "$PG_DB" --clean --if-exists --no-owner < "$dump"
        ;;
    mongo)
        archive="$(latest 'mongo_*.archive.gz')"
        [ -n "$archive" ] || { echo "No MongoDB archive in backups/" >&2; exit 1; }
        echo "Restoring $archive into $MONGO_DB"
        # --nsInclude limits --drop to this project's collections.
        compose exec -T mongo mongorestore --quiet --uri "$MONGO_URL" --archive --gzip --drop \
            --nsInclude "$MONGO_DB.*" < "$archive"
        ;;
    redis)
        # Everything this project keeps in Redis is derived from PostgreSQL.
        manage rebuild_redis
        ;;
    *)
        echo "Unknown engine: $engine (postgres, mongo or redis)" >&2
        exit 1
        ;;
esac

echo "Restore of $engine took ${SECONDS}s. Now run scripts/verify.sh"
