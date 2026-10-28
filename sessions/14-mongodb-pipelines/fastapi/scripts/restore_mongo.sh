#!/usr/bin/env bash
# Restores a backup into <MONGO_DB>_restored, leaving the original database untouched.
# Usage: ./scripts/restore_mongo.sh [backups/<file>.archive.gz]   (default: the newest backup)
set -euo pipefail

project_dir="$(cd "$(dirname "$0")/.." && pwd)"
repo_root="$(cd "$project_dir/../../.." && pwd)"
set -a; source "$project_dir/.env"; source "$repo_root/.env"; set +a

# Inside the mongo container the server is localhost:27017, whatever port is published
# on your machine (see backup_mongo.sh).
container_url="mongodb://${MONGO_ROOT_USER}:${MONGO_ROOT_PASSWORD}@localhost:27017/?authSource=admin"

file="${1:-$(ls -t "$project_dir"/backups/mongo_"${MONGO_DB}"_*.archive.gz | head -n 1)}"
target="${MONGO_DB}_restored"
echo "Restoring $(basename "$file") into $target"

# --nsFrom/--nsTo rename every collection of MONGO_DB into the target database.
# --drop replaces the collections being restored, and only those: here they are in
# the *_restored database, so nothing else is dropped.
start=$(date +%s)
docker compose --project-directory "$repo_root" exec -T mongo \
    mongorestore --uri "$container_url" --archive --gzip --drop \
    --nsFrom "${MONGO_DB}.*" --nsTo "${target}.*" < "$file"
echo "Restore took $(( $(date +%s) - start )) s"
