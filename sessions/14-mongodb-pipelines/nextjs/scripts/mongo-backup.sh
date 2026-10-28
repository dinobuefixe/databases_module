#!/usr/bin/env bash
# Dumps this project's MongoDB database to backups/mongo_<db>_<timestamp>.archive.gz.
# mongodump runs inside the mongo container, so nothing has to be installed on your machine.
set -euo pipefail
cd "$(dirname "$0")/.."
set -a; source .env; source ../../../.env; set +a
compose() { docker compose -f ../../../docker-compose.yml "$@"; }

# Inside the container the server is localhost:27017 whatever port docker-compose.yml publishes
# on your machine, so MONGO_URL (written for your machine) is not used here. mongodump logs in
# as the root user from the .env at the root of the repository.
container_url="mongodb://${MONGO_ROOT_USER}:${MONGO_ROOT_PASSWORD}@localhost:27017/?authSource=admin"

mkdir -p backups
file="backups/mongo_${MONGO_DB}_$(date +%Y%m%d-%H%M%S).archive.gz"
# Write to a temporary name and rename only when mongodump succeeds. Otherwise a failed
# dump leaves an empty .archive.gz behind, and the restore script picks it as the newest.
tmp="$file.part"
trap 'rm -f "$tmp"' EXIT

# --db limits the dump to our database; --archive writes one stream, --gzip compresses it.
# No --quiet: the progress lines go to stderr, and so does the reason when it fails.
compose exec -T mongo mongodump --uri "$container_url" --db "$MONGO_DB" --archive --gzip > "$tmp"
mv "$tmp" "$file"
echo "Wrote $file ($(du -h "$file" | cut -f1))"
