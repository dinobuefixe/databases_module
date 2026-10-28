"""Restore a dump into a new database and measure how long it takes.

    uv run python -m scripts.restore                          # latest dump into s10_fastapi_restored
    uv run python -m scripts.restore --file backups/x.dump --target s10_fastapi_restored
"""

import argparse
import time
from pathlib import Path

from scripts.common import RESTORE_DB, compose_exec, latest_dump, require_own_database


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", type=Path, help="defaults to the newest dump in backups/")
    parser.add_argument("--target", default=RESTORE_DB)
    args = parser.parse_args()

    require_own_database(args.target)
    dump = args.file or latest_dump()

    # Start from an empty database every time.
    compose_exec("dropdb", "-U", "postgres", "--if-exists", "--force", args.target)
    compose_exec("createdb", "-U", "postgres", args.target)

    started = time.perf_counter()
    with dump.open("rb") as stdin:
        # --no-owner: objects belong to the user running the restore, whoever owned them before.
        result = compose_exec("pg_restore", "-U", "postgres", "-d", args.target, "--no-owner", stdin=stdin, check=False)
    elapsed = time.perf_counter() - started
    print(f"restored {dump.name} into {args.target} in {elapsed:.1f} s (pg_restore exit code {result.returncode})")
    print(f"next: uv run python -m scripts.verify s10_fastapi {args.target}")


if __name__ == "__main__":
    main()
