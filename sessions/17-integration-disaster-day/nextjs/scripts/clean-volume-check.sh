#!/usr/bin/env bash
# Restores backups/latest into brand-new PostgreSQL and MongoDB containers (empty volumes,
# nothing created by hand) and compares the counts with the backup. Proves the backup is
# enough on its own. The containers are removed at the end.
source "$(dirname "$0")/lib.sh"

pg=s17-nextjs-pg-check
mongo=s17-nextjs-mongo-check
trap 'docker rm -f "$pg" "$mongo" > /dev/null 2>&1 || true' EXIT

docker run -d --name "$pg" -e POSTGRES_PASSWORD=throwaway postgres:18 > /dev/null
docker run -d --name "$mongo" mongo:8 > /dev/null
# Over TCP: during first start-up the image runs a temporary server on the Unix socket only.
until docker exec "$pg" pg_isready -h 127.0.0.1 -U postgres -q; do sleep 1; done
until docker exec "$mongo" mongosh --quiet --eval 'db.runCommand({ping: 1}).ok' > /dev/null 2>&1; do sleep 1; done

start=$(date +%s)
docker exec "$pg" createdb -U postgres "$PG_DB"
docker exec -i "$pg" pg_restore -U postgres -d "$PG_DB" --no-owner --exit-on-error < backups/latest/postgres.dump
docker exec -i "$mongo" mongorestore --quiet --archive --gzip < backups/latest/mongo.archive.gz
echo "Restored into empty containers in $(( $(date +%s) - start ))s"

counts=$({ pg_counts docker exec -i "$pg" psql -U postgres -d "$PG_DB"; mongo_counts docker exec -i "$mongo" mongosh; })
if diff <(sort backups/latest/counts.txt) <(sort <<< "$counts"); then
    echo "Counts match the backup ($(wc -l < backups/latest/counts.txt | tr -d ' ') tables and collections)"
else
    echo "Counts differ from the backup" >&2; exit 1
fi
