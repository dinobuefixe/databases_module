#!/usr/bin/env bash
# Backs up this project's Mongo database (MONGO_DB) to backups/mongo_<db>_<timestamp>.archive.gz
# Usage: ./scripts/backup_mongo.sh
set -euo pipefail

project_dir="$(cd "$(dirname "$0")/.." && pwd)"
repo_root="$(cd "$project_dir/../../.." && pwd)"
set -a; source "$project_dir/.env"; source "$repo_root/.env"; set +a

# mongodump runs inside the mongo container, where the server is localhost:27017 whatever
# port docker-compose.yml publishes on your machine, so MONGO_URL (written for your machine)
# is not used here. It logs in as the root user from the .env at the root of the repository.
container_url="mongodb://${MONGO_ROOT_USER}:${MONGO_ROOT_PASSWORD}@localhost:27017/?authSource=admin"

mkdir -p "$project_dir/backups"
file="$project_dir/backups/mongo_${MONGO_DB}_$(date +%F_%H%M%S).archive.gz"

# Write to a temporary name and rename only when mongodump succeeds. Otherwise a failed
# dump leaves an empty .archive.gz behind, and the restore script picks it as the newest.
tmp="$file.part"
trap 'rm -f "$tmp"' EXIT

# --db limits the dump to our database; --archive with no file name writes to stdout.
# No --quiet: the progress lines go to stderr, and so does the reason when it fails.
docker compose --project-directory "$repo_root" exec -T mongo \
    mongodump --uri "$container_url" --db "$MONGO_DB" --archive --gzip > "$tmp"
mv "$tmp" "$file"

echo "Backup written to ${file#$project_dir/} ($(du -h "$file" | cut -f1))"
