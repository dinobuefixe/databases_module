#!/usr/bin/env bash
# Restores one engine from backups/latest.  Usage: scripts/restore.sh <postgres|mongo|redis>
source "$(dirname "$0")/lib.sh"

engine="${1:?Usage: scripts/restore.sh <postgres|mongo|redis>}"
backup="backups/latest"

case "$engine" in
    postgres)
        [ -f "$backup/postgres.dump" ] || { echo "No $backup/postgres.dump" >&2; exit 1; }
        # After losing the volume the database does not exist. If it does, replace it entirely.
        psql_live -d postgres -q -c "DROP DATABASE IF EXISTS \"$PG_DB\" WITH (FORCE)" -c "CREATE DATABASE \"$PG_DB\""
        compose exec -T postgres pg_restore -U "$PG_USER" -d "$PG_DB" --no-owner --exit-on-error < "$backup/postgres.dump"
        echo "postgres: restored $PG_DB from $(readlink "$backup")"
        echo "Redis sets are derived from PostgreSQL: run 'scripts/restore.sh redis' too."
        ;;
    mongo)
        [ -f "$backup/mongo.archive.gz" ] || { echo "No $backup/mongo.archive.gz" >&2; exit 1; }
        # --drop replaces the collections in the archive, all of which belong to $MONGO_DB.
        compose exec -T mongo mongorestore --quiet --uri "$MONGO_URL" --nsInclude "$MONGO_DB.*" \
            --archive --gzip --drop < "$backup/mongo.archive.gz"
        echo "mongo: restored $MONGO_DB from $(readlink "$backup")"
        ;;
    redis)
        npx tsx scripts/redis-rebuild.ts
        ;;
    *)
        echo "Unknown engine: $engine (postgres, mongo or redis)" >&2; exit 1 ;;
esac
