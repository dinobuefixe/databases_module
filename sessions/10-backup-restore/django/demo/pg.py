"""Run the PostgreSQL client tools inside the postgres container, as in the tutorial.

Every call is `docker compose exec -T postgres <tool> ...` from the root of the
repository. -T turns off the pseudo-terminal so binary dumps are not corrupted.
The tools connect through the container's local socket, so no password is passed.
"""

import subprocess
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.core.management.base import CommandError
from django.db import connection

BACKUP_DIR = settings.BASE_DIR / "backups"  # git-ignored
REPO_ROOT = settings.BASE_DIR.parents[2]  # where docker-compose.yml lives
PG_USER = "postgres"


def live_db() -> str:
    """The project's own database, taken from DATABASE_URL."""
    return connection.settings_dict["NAME"]


def own(name: str) -> str:
    """Refuse any database that does not belong to this project (the server is shared)."""
    if not name.startswith(live_db()):
        raise CommandError(f"{name} is not one of this project's databases (they start with {live_db()})")
    return name


def compose_exec(*args: str, stdin=None, stdout=None, input: bytes | None = None) -> subprocess.CompletedProcess:
    """Run one client tool in the container; stdin/stdout can be files, input can be bytes."""
    cmd = ["docker", "compose", "exec", "-T", "postgres", *args]
    print("$", " ".join(cmd))
    kwargs = {"input": input} if input is not None else {"stdin": stdin}
    result = subprocess.run(cmd, cwd=REPO_ROOT, stdout=stdout, stderr=subprocess.PIPE, **kwargs)
    if result.returncode != 0:
        raise CommandError(f"{args[0]} failed:\n{result.stderr.decode()}")
    return result


def timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d_%H%M%S")


def latest_dump() -> Path:
    dumps = sorted(BACKUP_DIR.glob(f"{live_db()}_*.dump"))
    if not dumps:
        raise CommandError("no backup found in backups/, run `uv run python manage.py backup` first")
    return dumps[-1]
