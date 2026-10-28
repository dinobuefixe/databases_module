#!/usr/bin/env bash
# Clones a repository at a tag into a temporary folder, follows the README's setup steps
# and reports how long it took to get from nothing to the three demos passing.
#
# Usage: scripts/clean-clone-check.sh <repository-url> [tag] [project-folder]
#   tag             default v1.0
#   project-folder  default sessions/19-delivery-demo/django
# Environment:
#   DB_NAME=s19_django_clean   database created for the check (dropped and recreated)
#   ROWS=2000000               rows in big_rental
#   SKIP_ENGINES=1             do not run docker compose up (the engines are already running)
#   KEEP=1                     keep the temporary folder afterwards
# Needs git, docker and uv on the PATH.
set -euo pipefail

url="${1:?Usage: scripts/clean-clone-check.sh <repository-url> [tag] [project-folder]}"
tag="${2:-v1.0}"
project="${3:-sessions/19-delivery-demo/django}"
db_name="${DB_NAME:-s19_django_clean}"

work="$(mktemp -d)"
if [ "${KEEP:-0}" = 1 ]; then
    echo "Working in $work (kept)"
else
    trap 'rm -rf "$work"' EXIT
fi

SECONDS=0
step() { printf '\n==> [%3ss] %s\n' "$SECONDS" "$*"; }

step "git clone --branch $tag $url"
git -c advice.detachedHead=false clone --quiet --depth 1 --branch "$tag" "$url" "$work/repo"
cd "$work/repo"
[ -f .env ] || cp .env.example .env

if [ "${SKIP_ENGINES:-0}" != 1 ]; then
    step "docker compose up -d --wait"
    docker compose up -d --wait
fi

step "create database $db_name (copy of Pagila)"
./scripts/create-db.sh "$db_name" --pagila --reset

cd "$project"
step "uv sync"
# --locked fails if pyproject.toml changed without uv.lock being updated and committed.
uv sync --locked --quiet

step ".env pointing at $db_name"
sed "s#/s19_django\$#/$db_name#" .env.example > .env

step "migrate and setup_demo"
uv run python manage.py migrate
uv run python manage.py setup_demo --rows "${ROWS:-2000000}"

step "demo_concurrency"
uv run python manage.py demo_concurrency
step "demo_rebuild"
uv run python manage.py demo_rebuild
step "demo_explain"
uv run python manage.py demo_explain > /dev/null && echo "EXPLAIN demo ran"

printf '\nFrom an empty folder to all three demos in %s seconds.\n' "$SECONDS"
echo "Any step you had to fix by hand is a documentation bug in the README."
