"""Create, drop or list the tutorial's indexes.

    uv run python -m scripts.indexes list
    uv run python -m scripts.indexes create composite
    uv run python -m scripts.indexes drop partial
    uv run python -m scripts.indexes create all
"""

import argparse
import time

from app.db import pg_connect
from app.indexes import INDEXES, create_sql, drop_sql


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("action", choices=["create", "drop", "list"])
    parser.add_argument("name", nargs="?", default="all", choices=[*INDEXES, "all"])
    args = parser.parse_args()

    if args.action == "list":
        for key in INDEXES:
            print(f"{key:<11} {create_sql(key)}")
        return

    names = list(INDEXES) if args.name == "all" else [args.name]
    with pg_connect(autocommit=True) as conn:
        for name in names:
            statement = create_sql(name) if args.action == "create" else drop_sql(name)
            started = time.perf_counter()
            conn.execute(statement)
            print(f"{statement};  -- {time.perf_counter() - started:.2f} s")
            if args.action == "create":
                size = conn.execute(
                    "SELECT pg_size_pretty(pg_relation_size(%s::regclass)) AS s", (INDEXES[name].name,)
                ).fetchone()["s"]
                print(f"  size: {size}")


if __name__ == "__main__":
    main()
