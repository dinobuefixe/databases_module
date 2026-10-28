"""Kills Redis in the middle of a stream of writes and counts how many survived.

Run with: uv run python -m scripts.persistence_demo

It INCRs a counter as fast as it can, runs `docker compose kill redis` after two
seconds (SIGKILL: Redis gets no chance to save anything), starts Redis again and
compares the last value Redis acknowledged with the value it loaded from disk.
Run it with the default server (RDB snapshots only) and again with AOF on; the
README shows how to switch.

Killing the container stops Redis for a few seconds for every project that uses it.
"""

import os
import subprocess
import time
from datetime import datetime
from pathlib import Path

import redis
from dotenv import load_dotenv
from redis.backoff import NoBackoff
from redis.retry import Retry

load_dotenv()

REPO_ROOT = Path(__file__).resolve().parents[4]
WRITE_FOR = 2.0  # seconds of writes before the kill

# No retries: when Redis dies, the next INCR must fail at once, not wait and try again.
r = redis.Redis.from_url(os.environ["REDIS_URL"], decode_responses=True, retry=Retry(NoBackoff(), 0))


def compose(*args: str) -> list[str]:
    """docker compose for the repository's docker-compose.yml, wherever this runs from."""
    return ["docker", "compose", "--project-directory", str(REPO_ROOT), *args]


def wait_for_redis(timeout: float = 60) -> float:
    start = time.perf_counter()
    while True:
        try:
            r.ping()
            return time.perf_counter() - start
        except redis.ConnectionError:  # also raised while Redis is still loading its files
            if time.perf_counter() - start > timeout:
                raise
            time.sleep(0.2)


def main() -> None:
    config = r.config_get("appendonly") | r.config_get("appendfsync")
    aof = config["appendonly"] == "yes"
    print("Persistence:", f"AOF, appendfsync {config['appendfsync']}" if aof else "RDB snapshots only (appendonly no)")

    # A new key per run, so a snapshot from an earlier run cannot already hold it.
    for old_key in r.scan_iter(match="persistence-demo:*"):
        r.delete(old_key)
    key = f"persistence-demo:{int(time.time())}"

    acknowledged = 0
    killer = None
    started_at = datetime.now()
    start = time.perf_counter()
    try:
        while True:
            # The reply is the new value, so Redis has applied every write up to it.
            acknowledged = r.incr(key)
            if killer is None and time.perf_counter() - start >= WRITE_FOR:
                last_save = r.lastsave()
                # Popen does not wait: the loop keeps writing until the kill lands.
                killer = subprocess.Popen(compose("kill", "redis"), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except redis.ConnectionError:
        pass
    killer.wait()

    print(f"Writes acknowledged before the kill: {acknowledged}")
    if not aof:
        print(f"Writes started at {started_at:%H:%M:%S}; last RDB snapshot before the kill: {last_save:%H:%M:%S}")

    subprocess.run(compose("start", "redis"), check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"Redis answers again after {wait_for_redis():.1f} s")

    survived = int(r.get(key) or 0)
    lost = max(acknowledged - survived, 0)
    print(f"Counter after the restart: {survived}")
    print(f"Lost: {lost} writes ({lost / acknowledged:.0%})")


if __name__ == "__main__":
    main()
