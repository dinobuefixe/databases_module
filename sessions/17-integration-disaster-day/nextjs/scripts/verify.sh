#!/usr/bin/env bash
# The runbook's checks after a restore. Exit code 0 when all pass.
source "$(dirname "$0")/lib.sh"
failed=0

echo "1. Counts now against the last backup (lower means data was lost)"
current=$({ pg_counts psql_live -d "$PG_DB"; mongo_counts mongosh_live; })
while read -r name expected; do
    actual=$(awk -v n="$name" '$1 == n { print $2 }' <<< "$current")
    if [ -z "$actual" ] || [ "$actual" -lt "$expected" ]; then
        printf '   %-28s backup %8s  now %8s  LOST\n' "$name" "$expected" "${actual:-missing}"; failed=1
    else
        printf '   %-28s backup %8s  now %8s\n' "$name" "$expected" "$actual"
    fi
done < backups/latest/counts.txt

echo "2. Known queries"
check() {
    local label="$1" expected="$2" actual="$3"
    if [ "$actual" = "$expected" ]; then echo "   ok    $label"; else echo "   FAIL  $label: expected '$expected', got '$actual'"; failed=1; fi
}
check "CHECK constraint on account.balance" "account_balance_check" \
    "$(psql_live -d "$PG_DB" -tA -c "SELECT conname FROM pg_constraint WHERE conname = 'account_balance_check'")"
check "Prisma migrations recorded" "2" \
    "$(psql_live -d "$PG_DB" -tA -c "SELECT count(*) FROM _prisma_migrations WHERE finished_at IS NOT NULL AND rolled_back_at IS NULL")"
check "frozen report 2022-07 present" "1" \
    "$(mongosh_live --quiet --eval "db.getSiblingDB('$MONGO_DB').monthly_reports.countDocuments({_id: '2022-07'})")"

echo "3. Redis against PostgreSQL"
npx tsx scripts/redis-verify.ts | sed 's/^/   /' || failed=1

[ "$failed" = 0 ] && echo "All checks passed" || echo "Some checks FAILED"
exit "$failed"
