# Sourced by the other scripts: paths, credentials and a docker compose wrapper.
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO_ROOT="$(cd "$PROJECT_DIR/../../.." && pwd)"
cd "$PROJECT_DIR"

# POSTGRES_USER and REDIS_PASSWORD come from the repository's .env, the rest from this project's .env.
set -a
source "$REPO_ROOT/.env"
source .env
set +a

# Every Python command runs in the project environment that uv manages (.venv/).
manage() { uv run python manage.py "$@"; }
PG_DB="${DATABASE_URL##*/}"
PG_DB="${PG_DB%%\?*}"
REDIS_DB="${REDIS_URL##*/}"

compose() { docker compose --project-directory "$REPO_ROOT" "$@"; }
latest() { ls -1t backups/$1 2>/dev/null | head -1 || true; }
