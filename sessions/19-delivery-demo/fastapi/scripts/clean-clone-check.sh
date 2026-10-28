#!/usr/bin/env bash
# Clones a repository at a tag into a temporary folder, follows the README's setup
# steps there, and reports how long each step took.
#
# Usage: ./scripts/clean-clone-check.sh <repository-url> <tag> [project-folder]
#   project-folder  path of the app inside the repository
#                   (default: sessions/19-delivery-demo/fastapi)
#
# Environment:
#   START_ENGINES=0  skip `docker compose up` (when the engines already run and are shared)
#   CHECK_PORT=8000  port for the final API smoke test
#   KEEP=1           keep the temporary folder afterwards
#
# Every step that fails here, or that you had to do by hand, is a documentation bug.
set -euo pipefail

repo_url="${1:?Usage: clean-clone-check.sh <repository-url> <tag> [project-folder]}"
tag="${2:?Usage: clean-clone-check.sh <repository-url> <tag> [project-folder]}"
project="${3:-sessions/19-delivery-demo/fastapi}"
port="${CHECK_PORT:-8000}"

workdir="$(mktemp -d "${TMPDIR:-/tmp}/clean-clone.XXXXXX")"
server_pid=""
cleanup() {
    [ -n "$server_pid" ] && kill "$server_pid" 2>/dev/null || true
    if [ "${KEEP:-0}" = 1 ]; then echo "Kept $workdir"; else rm -rf "$workdir"; fi
}
trap cleanup EXIT

total_start=$(date +%s)
report=()
step() {
    local name="$1"; shift
    local start=$(date +%s)
    echo "==> $name"
    if "$@"; then
        report+=("$(printf '%-38s %4d s' "$name" $(( $(date +%s) - start )))")
    else
        report+=("$(printf '%-38s FAILED' "$name")")
        printf '%s\n' "${report[@]}"
        echo "Clean clone check FAILED at: $name"
        exit 1
    fi
}

clone()         { git -c advice.detachedHead=false clone --quiet --depth 1 --branch "$tag" "$repo_url" "$workdir/repo"; }
root_env()      { cd "$workdir/repo" && { [ -f .env ] || cp .env.example .env; }; }
engines()       { cd "$workdir/repo" && docker compose up -d --wait; }
pagila()        { cd "$workdir/repo" && ./scripts/load-pagila.sh; }
install()       { cd "$workdir/repo/$project" && make install; }
setup()         { cd "$workdir/repo/$project" && make setup; }
smoke_test() {
    cd "$workdir/repo/$project"
    uv run uvicorn app.main:app --port "$port" > "$workdir/api.log" 2>&1 &
    server_pid=$!
    for _ in $(seq 30); do
        curl -fs "localhost:$port/health" && echo && return 0
        sleep 1
    done
    cat "$workdir/api.log"
    return 1
}

step "git clone $tag" clone
step "copy .env.example to .env (root)" root_env
if [ "${START_ENGINES:-1}" = 1 ]; then
    step "docker compose up -d --wait" engines
else
    echo "==> docker compose up skipped (START_ENGINES=0)"
fi
step "load Pagila" pagila
step "make install" install
step "make setup" setup
step "API answers /health" smoke_test

echo
printf '%s\n' "${report[@]}"
echo "Clean clone check passed in $(( $(date +%s) - total_start )) s"
