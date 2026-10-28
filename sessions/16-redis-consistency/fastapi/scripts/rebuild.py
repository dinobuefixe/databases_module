"""Rebuilds every customer:{id}:films set from PostgreSQL and prints how long it took.

Run with:
    uv run python -m scripts.rebuild                 both versions, one after the other
    uv run python -m scripts.rebuild --mode single   only the single-query version
    uv run python -m scripts.rebuild --flush         empty this project's Redis database first

--flush runs FLUSHDB, which empties only the logical database in REDIS_URL (/1).
The tutorial says FLUSHALL, which empties every logical database on the server;
on a shared Redis that would delete other projects' data too.
"""

import argparse
import time

from app.clients import pg_readonly, r
from app.films_sets import rebuild_per_customer, rebuild_single_query

MODES = {"per-customer": rebuild_per_customer, "single": rebuild_single_query}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=[*MODES, "both"], default="both")
    parser.add_argument("--flush", action="store_true", help="FLUSHDB on this project's index first")
    args = parser.parse_args()

    if args.flush:
        r.flushdb()
        print(f"FLUSHDB on database {r.connection_pool.connection_kwargs['db']}: {r.dbsize()} keys left")

    modes = list(MODES) if args.mode == "both" else [args.mode]
    with pg_readonly() as pg:
        for mode in modes:
            start = time.perf_counter()
            n = MODES[mode](pg)
            print(f"{mode:13} {n} customers in {time.perf_counter() - start:.2f} s")


if __name__ == "__main__":
    main()
