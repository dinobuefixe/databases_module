"""Exits 1 if any customer:{id}:films set differs from PostgreSQL.

Run with: uv run python -m scripts.verify_redis
"""

import sys

from app.db import SessionLocal
from app.films_sets import verify_all

with SessionLocal() as session:
    mismatches = verify_all(session)
for m in mismatches[:10]:
    print(f"customer {m['customer_id']}: redis={m['redis']} postgres={m['postgres']}", file=sys.stderr)
print("redis: OK" if not mismatches else f"redis: {len(mismatches)} customers differ")
sys.exit(1 if mismatches else 0)
