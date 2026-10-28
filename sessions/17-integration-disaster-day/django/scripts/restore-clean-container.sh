#!/usr/bin/env bash
# Restores the newest backups into brand-new PostgreSQL and MongoDB containers that have
# never seen this project, to prove the backups do not depend on the existing setup.
set -euo pipefail
source "$(dirname "$0")/_env.sh"

PG=s17-django-pg-clean
MONGO=s17-django-mongo-clean
cleanup() { docker rm -f "$PG" "$MONGO" > /dev/null 2>&1 || true; }
trap cleanup EXIT

dump="$(latest 'postgres_*.dump')"
archive="$(latest 'mongo_*.archive.gz')"
[ -n "$dump" ] && [ -n "$archive" ] || { echo "Run scripts/backup.sh first" >&2; exit 1; }

SECONDS=0
docker run -d --rm --name "$PG" -e POSTGRES_PASSWORD=test postgres:18 > /dev/null
docker run -d --rm --name "$MONGO" mongo:8 > /dev/null
# During its first start the image runs a temporary server on the Unix socket only, so
# wait for TCP on 127.0.0.1, which only the final server listens on.
until docker exec "$PG" pg_isready -h 127.0.0.1 -U postgres -q 2> /dev/null; do sleep 1; done
until docker exec "$MONGO" mongosh --quiet --eval "db.adminCommand('ping').ok" > /dev/null 2>&1; do sleep 1; done
echo "Clean containers ready after ${SECONDS}s"

SECONDS=0
docker exec "$PG" createdb -U postgres restored
# Roles from the shared server do not exist here: --no-owner and --no-privileges skip them.
docker exec -i "$PG" pg_restore -U postgres -d restored --no-owner --no-privileges < "$dump"
docker exec -i "$MONGO" mongorestore --quiet --archive --gzip < "$archive"
echo "Restored in ${SECONDS}s"

echo "rental rows:            $(docker exec "$PG" psql -U postgres -d restored -tAc 'SELECT count(*) FROM rental')"
echo "account rows:           $(docker exec "$PG" psql -U postgres -d restored -tAc 'SELECT count(*) FROM account')"
echo "monthly_reports docs:   $(docker exec "$MONGO" mongosh --quiet --eval "db.getSiblingDB('$MONGO_DB').monthly_reports.countDocuments()")"
echo "Compare with the newest counts file: $(latest 'counts_*.txt')"
