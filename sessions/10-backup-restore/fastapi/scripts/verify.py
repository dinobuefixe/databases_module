"""Compare the row count of every table in two databases. Exit code 1 on any difference.

    uv run python -m scripts.verify                                   # s10_fastapi against s10_fastapi_restored
    uv run python -m scripts.verify s10_fastapi_restored s10_fastapi
"""

import argparse
import sys

from app.db import DB_NAME, row_counts
from scripts.common import RESTORE_DB, require_own_database


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("first", nargs="?", default=DB_NAME)
    parser.add_argument("second", nargs="?", default=RESTORE_DB)
    args = parser.parse_args()
    require_own_database(args.first)
    require_own_database(args.second)

    a, b = row_counts(args.first), row_counts(args.second)
    mismatches = 0
    print(f"{'table':<20} {args.first:>22} {args.second:>22}")
    for table in sorted(a.keys() | b.keys()):
        left, right = a.get(table), b.get(table)
        ok = left == right
        mismatches += not ok
        show = lambda n: "missing" if n is None else f"{n:,}"
        print(f"{table:<20} {show(left):>22} {show(right):>22}  {'OK' if ok else 'MISMATCH'}")

    if mismatches:
        print(f"\n{mismatches} table(s) differ")
        sys.exit(1)
    print("\nall tables match")


if __name__ == "__main__":
    main()
