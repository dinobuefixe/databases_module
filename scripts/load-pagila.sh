#!/usr/bin/env bash
# Downloads the Pagila sample database and loads it into a database called "pagila".
# Usage: ./scripts/load-pagila.sh [--reset]
set -euo pipefail

cd "$(dirname "$0")/.."
set -a; source .env; set +a

# Pinned to the last commit before Pagila started requiring the pgvector extension,
# so it loads into the official postgres:18 image.
PAGILA_COMMIT="aeb87bcb0f9751bffb67bd7f4376e8534746d008"
BASE_URL="https://raw.githubusercontent.com/devrimgunduz/pagila/$PAGILA_COMMIT"
CACHE=".cache/pagila/$PAGILA_COMMIT"
mkdir -p "$CACHE"

for file in pagila-schema.sql pagila-data.sql; do
    if [ ! -f "$CACHE/$file" ]; then
        echo "Downloading $file"
        curl -fsSL "$BASE_URL/$file" -o "$CACHE/$file"
    fi
done

psql() {
    docker compose exec -T postgres psql -U "$POSTGRES_USER" -v ON_ERROR_STOP=1 -q "$@"
}

if [ "${1:-}" = "--reset" ]; then
    psql -d postgres -c "DROP DATABASE IF EXISTS pagila WITH (FORCE);"
fi

if psql -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname = 'pagila'" | grep -q 1; then
    echo "Database pagila already exists. Use --reset to reload it."
    exit 0
fi

psql -d postgres -c "CREATE DATABASE pagila;"
psql -d pagila < "$CACHE/pagila-schema.sql" > /dev/null
psql -d pagila < "$CACHE/pagila-data.sql" > /dev/null
psql -d pagila -c "ANALYZE;"

echo "Pagila loaded:"
psql -d pagila -c "SELECT (SELECT count(*) FROM film) AS films, (SELECT count(*) FROM customer) AS customers, (SELECT count(*) FROM rental) AS rentals;"
