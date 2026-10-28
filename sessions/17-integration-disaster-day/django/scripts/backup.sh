#!/usr/bin/env bash
# Backs up PostgreSQL and MongoDB into backups/ and records the counts to verify against.
set -euo pipefail
source "$(dirname "$0")/_env.sh"

mkdir -p backups
ts="$(date +%F_%H%M%S)"

echo "PostgreSQL: $PG_DB"
compose exec -T postgres pg_dump -U "$POSTGRES_USER" -Fc "$PG_DB" > "backups/postgres_$ts.dump"
# Roles are cluster-wide and not in pg_dump; a new volume needs them before the app can log in.
compose exec -T postgres pg_dumpall -U "$POSTGRES_USER" --roles-only > "backups/roles_$ts.sql"

echo "MongoDB: $MONGO_DB"
compose exec -T mongo mongodump --quiet --uri "$MONGO_URL" --db "$MONGO_DB" --archive --gzip \
    > "backups/mongo_$ts.archive.gz"

echo "Redis: nothing to back up, customer:{id}:films is rebuilt from PostgreSQL"

manage counts > "backups/counts_$ts.txt"
ls -lh backups/*"$ts"*
