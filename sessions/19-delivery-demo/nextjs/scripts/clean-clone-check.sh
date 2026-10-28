#!/usr/bin/env bash
# Clones a repository at a tag into a temporary folder, follows the README's setup steps
# and reports how long each one took. Anything you had to fix by hand is a documentation bug.
#
# Usage: scripts/clean-clone-check.sh <repository-url> [tag] [folder-inside-the-repo]
#   scripts/clean-clone-check.sh git@github.com:group/project.git v1.0
#   scripts/clean-clone-check.sh https://github.com/you/databases_module.git v1.0 sessions/19-delivery-demo/nextjs
#
# The engines must already be running (docker compose up -d) and the database must exist:
# the check reuses them, it does not start a second set of containers.
set -euo pipefail

url="${1:?Usage: clean-clone-check.sh <repository-url> [tag] [folder]}"
tag="${2:-v1.0}"
folder="${3:-.}"
port="${CHECK_PORT:-3100}"
tmp=$(mktemp -d)
server=""
cleanup() {
    if [ -n "$server" ]; then kill "$server" 2> /dev/null || true; wait "$server" 2> /dev/null || true; fi
    if [ "${KEEP:-0}" = 1 ]; then echo "Clone kept in $tmp"; else rm -rf "$tmp" || true; fi
}
trap cleanup EXIT

timings=()
total_start=$(date +%s)
step() {
    local name="$1"; shift
    echo; echo "=== $name"
    local start=$(date +%s)
    "$@"
    timings+=("$(printf '%-34s %5ss' "$name" $(( $(date +%s) - start )))")
}

wait_for_health() {
    for _ in $(seq 1 60); do
        curl -fsS "localhost:$port/api/health" && echo && return 0
        sleep 1
    done
    echo "The API did not become healthy" >&2; return 1
}

step "git clone --branch $tag" git clone --quiet --depth 1 --branch "$tag" "$url" "$tmp/repo"
cd "$tmp/repo/$folder"
step "cp .env.example .env" cp .env.example .env
step "npm ci" npm ci --no-audit --no-fund
step "npm run setup" npm run setup
step "npm run build" npm run build
npx next start --port "$port" > "$tmp/server.log" 2>&1 &
server=$!
step "npm start until /api/health is 200" wait_for_health

echo; echo "Clean clone of $tag ready in $(( $(date +%s) - total_start ))s"
printf '  %s\n' "${timings[@]}"
