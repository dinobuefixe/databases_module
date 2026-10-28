"""Compares every customer:{id}:films set with PostgreSQL, member by member.

Run with: uv run python -m scripts.verify ; echo $?
Exits 0 when Redis agrees with PostgreSQL and 1 otherwise, so CI or cron can use it.
"""

import sys

from app.clients import pg_readonly
from app.films_sets import verify


def ids(members: list[str]) -> str:
    shown = ", ".join(members[:5])
    return shown if len(members) <= 5 else f"{shown} ... ({len(members)} in total)"


def describe(m: dict) -> str:
    if m["orphan"]:
        return f"{m['key']}: no such customer in PostgreSQL ({len(m['extra'])} members)"
    parts = []
    if m["missing"]:
        parts.append(f"missing {ids(m['missing'])}")
    if m["extra"]:
        parts.append(f"extra {ids(m['extra'])}")
    return f"{m['key']}: {'; '.join(parts)}"


with pg_readonly() as pg:
    mismatches = verify(pg)

for m in mismatches[:20]:
    print(describe(m), file=sys.stderr)
if len(mismatches) > 20:
    print(f"... and {len(mismatches) - 20} more", file=sys.stderr)

print("OK" if not mismatches else f"{len(mismatches)} keys differ")
sys.exit(1 if mismatches else 0)
