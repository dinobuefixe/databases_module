# Shared by the shell scripts: settings from .env and helpers for the three engines.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
set -a; source .env; set +a

# The engines run in the repository's docker compose project.
compose() { docker compose -f ../../../docker-compose.yml "$@"; }

# postgresql://user:password@host:port/dbname -> user, dbname
PG_USER=$(sed -E 's#^postgresql://([^:]+):.*#\1#' <<< "$DATABASE_URL")
PG_DB=$(sed -E 's#^.*/([^/?]+)(\?.*)?$#\1#' <<< "$DATABASE_URL")
REDIS_DB=$(sed -E 's#^.*/([0-9]+)$#\1#' <<< "$REDIS_URL")
REDIS_PASSWORD=$(sed -E 's#^redis://:([^@]*)@.*#\1#' <<< "$REDIS_URL")

PG_TABLES="account customer inventory rental payment"

# Row counts, one "postgres.<table> <count>" line each. Arguments: the psql command to use.
pg_counts() {
    local sql
    sql=$(for t in $PG_TABLES; do echo "SELECT 'postgres.$t', count(*) FROM $t"; done | paste -sd'|' - | sed 's/|/ UNION ALL /g')
    "$@" -tA -F' ' -c "$sql"
}

# Document counts, one "mongo.<collection> <count>" line each. Arguments: the mongosh command to use.
mongo_counts() {
    "$@" --quiet --eval "
      const d = db.getSiblingDB('$MONGO_DB');
      d.getCollectionNames().sort().forEach(c => print('mongo.' + c + ' ' + d[c].countDocuments()));"
}

psql_live() { compose exec -T postgres psql -U "$PG_USER" -v ON_ERROR_STOP=1 "$@"; }
mongosh_live() { compose exec -T mongo mongosh "$MONGO_URL" "$@"; }

# Every destructive step in these scripts targets this project's own databases only.
case "$PG_DB:$MONGO_DB:$REDIS_DB" in
    s17_*:s17_*:3) ;;
    *) echo "Refusing to run: expected s17_* databases and Redis database 3 in .env" >&2; exit 1 ;;
esac
