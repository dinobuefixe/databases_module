#!/usr/bin/env bash
# Creates a PostgreSQL database for one of the session projects.
# Usage:
#   ./scripts/create-db.sh s03_django              empty database
#   ./scripts/create-db.sh s05_fastapi --pagila    copy of the pagila database
#   add --reset to drop and recreate it
set -euo pipefail

cd "$(dirname "$0")/.."
set -a; source .env; set +a

name="${1:?Usage: create-db.sh <name> [--pagila] [--reset]}"
shift
from_pagila=false
reset=false
for arg in "$@"; do
    case "$arg" in
        --pagila) from_pagila=true ;;
        --reset) reset=true ;;
        *) echo "Unknown option: $arg" >&2; exit 1 ;;
    esac
done

psql() {
    docker compose exec -T postgres psql -U "$POSTGRES_USER" -d postgres -v ON_ERROR_STOP=1 -q "$@"
}

if $reset; then
    psql -c "DROP DATABASE IF EXISTS \"$name\" WITH (FORCE);"
fi

if psql -tAc "SELECT 1 FROM pg_database WHERE datname = '$name'" | grep -q 1; then
    echo "Database $name already exists. Use --reset to recreate it."
    exit 0
fi

if $from_pagila; then
    psql -c "CREATE DATABASE \"$name\" TEMPLATE pagila;"
    echo "Created $name as a copy of pagila"
else
    psql -c "CREATE DATABASE \"$name\";"
    echo "Created empty database $name"
fi
