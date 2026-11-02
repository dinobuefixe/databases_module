#!/usr/bin/env bash
# The runbook's verification: counts and a known query compared with the newest backup,
# then the Redis verification. Exit code 0 only if everything matches.
set -uo pipefail
source "$(dirname "$0")/_env.sh"

status=0
expected="$(latest 'counts_*.txt')"
current="$(mktemp)"
trap 'rm -f "$current"' EXIT

if ! manage counts > "$current"; then
    echo "Could not read the counts: is every engine up?" >&2
    exit 1
fi

if [ -z "$expected" ]; then
    echo "No counts file in backups/; showing the current counts only"
    cat "$current"
elif diff -u "$expected" "$current"; then
    echo "postgres and mongo: counts and known query match $expected"
else
    echo "postgres and mongo: differences from $expected (lines with - were in the backup, + are now)" >&2
    echo "Rows written after the backup are expected to be missing: that is the RPO." >&2
    status=1
fi

manage verify_redis || status=1
exit $status
