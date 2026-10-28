#!/usr/bin/env bash
# Simulates losing one engine's data, limited to this project's databases.
# Usage: scripts/disaster.sh <postgres|mongo|redis>
source "$(dirname "$0")/lib.sh"

engine="${1:?Usage: scripts/disaster.sh <postgres|mongo|redis>}"
case "$engine" in
    postgres) psql_live -d postgres -q -c "DROP DATABASE IF EXISTS \"$PG_DB\" WITH (FORCE)" ;;
    mongo)    mongosh_live --quiet --eval "db.getSiblingDB('$MONGO_DB').dropDatabase()" > /dev/null ;;
    redis)    compose exec -T redis redis-cli -a "$REDIS_PASSWORD" --no-auth-warning -n "$REDIS_DB" FLUSHDB > /dev/null ;;
    *)        echo "Unknown engine: $engine" >&2; exit 1 ;;
esac
echo "$engine: this project's data is gone."
echo "On your own machine the real rehearsal deletes the whole volume instead:"
echo "  docker compose stop $engine && docker compose rm -f $engine"
echo "  docker volume rm <project>_${engine}_data && docker compose up -d $engine"
