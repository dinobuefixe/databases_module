"""Back up this project's database (custom format) and the server's roles into backups/.

    uv run python -m scripts.backup
"""

import time
from datetime import datetime

from app.db import DB_NAME
from scripts.common import BACKUP_DIR, compose_exec


def main() -> None:
    BACKUP_DIR.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    dump = BACKUP_DIR / f"{DB_NAME}_{stamp}.dump"
    roles = BACKUP_DIR / f"roles_{stamp}.sql"

    started = time.perf_counter()
    with dump.open("wb") as out:
        # -Fc: compressed archive that pg_restore can read selectively (one table, in parallel).
        compose_exec("pg_dump", "-U", "postgres", "-Fc", DB_NAME, stdout=out)
    print(f"{dump.relative_to(BACKUP_DIR.parent)}  {dump.stat().st_size / 1e6:.1f} MB  {time.perf_counter() - started:.1f} s")

    # pg_dump does not include roles; they belong to the server, not to one database.
    with roles.open("wb") as out:
        compose_exec("pg_dumpall", "-U", "postgres", "--roles-only", stdout=out)
    print(f"{roles.relative_to(BACKUP_DIR.parent)}  (contains password hashes: keep it out of Git)")


if __name__ == "__main__":
    main()
