"""Rebuilds every customer:{id}:films set from PostgreSQL. This is how Redis is "restored".

Run with: uv run python -m scripts.rebuild_redis
"""

import time

from app.db import SessionLocal
from app.films_sets import rebuild_all

start = time.perf_counter()
with SessionLocal() as session:
    n = rebuild_all(session)
print(f"rebuilt {n} customer sets in {time.perf_counter() - start:.2f} s")
