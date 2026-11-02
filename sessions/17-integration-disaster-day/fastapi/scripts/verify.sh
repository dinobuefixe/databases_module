#!/usr/bin/env bash
# The runbook's verification: counts and a known query against the backup's snapshot,
# then the Redis verification. Exits 1 if anything differs.
# Usage: ./scripts/verify.sh [backups/<timestamp>]
set -uo pipefail
source "$(dirname "$0")/common.sh"

dir="${1:-$(latest_backup)}"
status=0
echo "Comparing with ${dir#$project_dir/}snapshot.json"
py -m scripts.snapshot --compare "$dir/snapshot.json" || status=1
py -m scripts.verify_redis || status=1

[ "$status" -eq 0 ] && echo "VERIFY PASSED" || echo "VERIFY FAILED"
exit "$status"
