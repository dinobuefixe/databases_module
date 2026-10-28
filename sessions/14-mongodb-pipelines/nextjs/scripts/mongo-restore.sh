#!/usr/bin/env bash
# Restores a dump into <db>_restored, never over the original, and compares document counts.
# Usage: bash scripts/mongo-restore.sh [backups/file.archive.gz]   (default: the newest backup)
set -euo pipefail
cd "$(dirname "$0")/.."
set -a; source .env; source ../../../.env; set +a
compose() { docker compose -f ../../../docker-compose.yml "$@"; }

# Inside the mongo container the server is localhost:27017, whatever port is published
# on your machine (see mongo-backup.sh).
container_url="mongodb://${MONGO_ROOT_USER}:${MONGO_ROOT_PASSWORD}@localhost:27017/?authSource=admin"

file="${1:-$(ls -t backups/mongo_"${MONGO_DB}"_*.archive.gz | head -1)}"
target="${MONGO_DB}_restored"
echo "Restoring $file into $target"

# --nsFrom/--nsTo rename the namespaces on the way in. --drop replaces each collection
# being restored, and only those: the target is our own _restored database.
start=$(date +%s)
compose exec -T mongo mongorestore --uri "$container_url" --archive --gzip \
    --nsFrom "${MONGO_DB}.*" --nsTo "${target}.*" --drop < "$file"
echo "Restored in $(( $(date +%s) - start ))s"

# Same collections, same counts?
compose exec -T mongo mongosh --quiet "$container_url" --eval "
  const a = db.getSiblingDB('$MONGO_DB'), b = db.getSiblingDB('$target');
  let ok = true;
  for (const name of a.getCollectionNames().sort()) {
    const x = a[name].countDocuments(), y = b[name].countDocuments();
    if (x !== y) ok = false;
    print(name.padEnd(20) + String(x).padStart(8) + String(y).padStart(8) + (x === y ? '' : '  MISMATCH'));
  }
  if (!ok) quit(1);
"
