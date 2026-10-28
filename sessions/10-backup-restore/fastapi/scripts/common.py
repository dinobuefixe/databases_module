"""Shared helpers: paths, the docker compose wrapper and the safety checks."""

import os
import subprocess
import sys
from pathlib import Path

from app.db import DB_NAME

PROJECT_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = PROJECT_DIR.parents[2]  # sessions/10-backup-restore/fastapi -> repository root
BACKUP_DIR = PROJECT_DIR / "backups"
RESTORE_DB = os.environ.get("RESTORE_DB", f"{DB_NAME}_restored")
PREFIX = "s10_fastapi"


def require_own_database(name: str) -> None:
    """Refuse to touch any database that does not belong to this project."""
    if not name.startswith(PREFIX):
        sys.exit(f"refusing to touch database {name!r}: only {PREFIX}* databases belong to this project")


def compose_exec(*args: str, stdin=None, stdout=None, check: bool = True) -> subprocess.CompletedProcess:
    """Run a command inside the postgres service, like `docker compose exec -T postgres ...`.

    -T disables the pseudo-terminal, so binary dump data passes through stdin/stdout unchanged.
    """
    return subprocess.run(
        ["docker", "compose", "exec", "-T", "postgres", *args],
        cwd=REPO_ROOT, stdin=stdin, stdout=stdout, check=check,
    )


def latest_dump() -> Path:
    dumps = sorted(BACKUP_DIR.glob(f"{DB_NAME}_*.dump"))
    if not dumps:
        sys.exit("no dump in backups/; take one first with: uv run python -m scripts.backup")
    return dumps[-1]
