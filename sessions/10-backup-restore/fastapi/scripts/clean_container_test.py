"""Restore the latest dump into a brand-new postgres:18 container.

Proves the backup does not depend on anything in the shared setup: no existing roles,
no extensions, no Pagila template. The container is removed at the end.

    uv run python -m scripts.clean_container_test
"""

import os
import subprocess
import time

from scripts.common import latest_dump

CONTAINER = os.environ.get("TEST_CONTAINER", "s10-fastapi-pgtest")


def docker(*args: str, **kwargs) -> subprocess.CompletedProcess:
    return subprocess.run(["docker", *args], check=True, **kwargs)


def main() -> None:
    dump = latest_dump()
    # --rm: the container and its data disappear when it stops. No port is published.
    docker("run", "--rm", "-d", "--name", CONTAINER, "-e", "POSTGRES_PASSWORD=test", "postgres:18", stdout=subprocess.DEVNULL)
    try:
        # During its first start the image runs a temporary server on the Unix socket only,
        # so wait until it answers over TCP: that is the real server.
        for _ in range(60):
            ready = subprocess.run(["docker", "exec", CONTAINER, "pg_isready", "-h", "127.0.0.1", "-U", "postgres"],
                                   capture_output=True)
            if ready.returncode == 0:
                break
            time.sleep(1)
        else:
            raise SystemExit("the test container did not become ready")

        docker("exec", CONTAINER, "createdb", "-U", "postgres", "restored")
        started = time.perf_counter()
        with dump.open("rb") as stdin:
            result = subprocess.run(
                ["docker", "exec", "-i", CONTAINER, "pg_restore", "-U", "postgres", "-d", "restored", "--no-owner"],
                stdin=stdin,
            )
        print(f"restored {dump.name} into a clean container in {time.perf_counter() - started:.1f} s "
              f"(pg_restore exit code {result.returncode})", flush=True)
        docker("exec", CONTAINER, "psql", "-U", "postgres", "-d", "restored", "-c", "SELECT count(*) AS rentals FROM rental;")
    finally:
        docker("stop", CONTAINER, stdout=subprocess.DEVNULL)
        print(f"container {CONTAINER} stopped and removed")


if __name__ == "__main__":
    main()
