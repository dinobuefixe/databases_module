#!/usr/bin/env bash
# Rehearsal on a shared machine: loses ONE engine's data for this project only.
#   postgres  DROP DATABASE $PG_DB
#   mongo     dropDatabase on $MONGO_DB
#   redis     FLUSHDB on the logical database in REDIS_URL
# In your own environment the real rehearsal removes the Docker volume instead
# (see docs/runbook-restore.md). Never point this script at a database you do not own.
# Usage: ./scripts/simulate-loss.sh <postgres|mongo|redis>
set -euo pipefail
source "$(dirname "$0")/common.sh"

engine="${1:?Usage: simulate-loss.sh <postgres|mongo|redis>}"
case "$PG_DB/$MONGO_DB" in
    s17_*/s17_*) ;;
    *) echo "Refusing: PG_DB and MONGO_DB must be this project's databases (s17_*)" >&2; exit 1 ;;
esac

case "$engine" in
    postgres)
        compose exec -T postgres psql -U "$PG_USER" -d postgres -q \
            -c "DROP DATABASE IF EXISTS \"$PG_DB\" WITH (FORCE);"
        ;;
    mongo)
        compose exec -T mongo mongosh "$MONGO_URL" --quiet \
            --eval "db.getSiblingDB('$MONGO_DB').dropDatabase()" > /dev/null
        ;;
    redis)
        py -c "from app.db import r; r.flushdb()"
        ;;
    *)
        echo "Unknown engine: $engine" >&2
        exit 1
        ;;
esac
echo "$engine data for this project is gone"
