#!/usr/bin/env bash
# Rehearsal in the shared course environment: loses this project's data in one engine
# without touching the volumes the other projects use. Usage: scripts/simulate-disaster.sh <engine> [--yes]
set -euo pipefail
source "$(dirname "$0")/_env.sh"

engine="${1:?Usage: scripts/simulate-disaster.sh <postgres|mongo|redis> [--yes]}"
case "$PG_DB" in postgres|pagila|template*) echo "Refusing to drop $PG_DB" >&2; exit 1 ;; esac

if [ "${2:-}" != "--yes" ]; then
    read -r -p "This deletes the $engine data of this project. Type yes to continue: " answer
    [ "$answer" = "yes" ] || exit 1
fi

case "$engine" in
    postgres) compose exec -T postgres psql -U "$POSTGRES_USER" -d postgres -c "DROP DATABASE \"$PG_DB\" WITH (FORCE);" ;;
    mongo) compose exec -T mongo mongosh --quiet "$MONGO_URL" --eval "db.getSiblingDB('$MONGO_DB').dropDatabase()" ;;
    redis) compose exec -T redis redis-cli -a "$REDIS_PASSWORD" --no-auth-warning -n "$REDIS_DB" FLUSHDB ;;
    *) echo "Unknown engine: $engine" >&2; exit 1 ;;
esac
echo "$engine data of this project is gone. Restore it with: time scripts/restore.sh $engine"
