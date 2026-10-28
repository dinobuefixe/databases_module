"""Demo 2: empty Redis, show the verification failing, rebuild, show it passing.

Run with: uv run python -m scripts.demo_rebuild   (or make demo-rebuild)

This runs FLUSHDB, which empties only this project's Redis database (/1 in REDIS_URL).
In the tutorial the demo uses FLUSHALL, which empties every Redis database on the
server; only use FLUSHALL on a Redis that belongs to your project alone.
"""

import sys
import time

from app.db import SessionLocal, r
from app.films_sets import rebuild_all, verify_all


def check(label: str) -> bool:
    with SessionLocal() as session:
        mismatches = verify_all(session)
    print(f"{label:28} keys={r.dbsize():5}  mismatches={len(mismatches):4}  {'PASS' if not mismatches else 'FAIL'}")
    return not mismatches


check("1. before")
r.flushdb()
print(f"   FLUSHDB on Redis database {r.connection_pool.connection_kwargs['db']}")
check("2. after FLUSHDB")

start = time.perf_counter()
with SessionLocal() as session:
    n = rebuild_all(session)
print(f"   rebuilt {n} customer sets from PostgreSQL in {time.perf_counter() - start:.2f} s")

sys.exit(0 if check("3. after rebuild") else 1)
