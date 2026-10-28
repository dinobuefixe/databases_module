import subprocess
import time
from datetime import datetime

import redis
from django.conf import settings
from django.core.management.base import BaseCommand
from redis.backoff import NoBackoff
from redis.retry import Retry

REPO_ROOT = settings.BASE_DIR.parents[2]  # the folder with docker-compose.yml
WRITE_FOR = 2.0  # seconds of writes before the kill


def compose(*args: str) -> list[str]:
    return ["docker", "compose", "--project-directory", str(REPO_ROOT), *args]


class Command(BaseCommand):
    help = (
        "Writes to Redis in a loop, kills Redis mid-loop with `docker compose kill redis` (SIGKILL), "
        "starts it again and reports how many writes survived. Stops Redis for every project for a few seconds."
    )

    def handle(self, *args, **options):
        # No retries: when Redis dies, the next INCR must fail at once, not wait and try again.
        r = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True, retry=Retry(NoBackoff(), 0))
        config = r.config_get("appendonly") | r.config_get("appendfsync")
        aof = config["appendonly"] == "yes"
        self.stdout.write(
            "Persistence: " + (f"AOF, appendfsync {config['appendfsync']}" if aof else "RDB snapshots only (appendonly no)")
        )

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

        self.stdout.write(f"Writes acknowledged before the kill: {acknowledged}")
        if not aof:
            self.stdout.write(f"Writes started at {started_at:%H:%M:%S}; last RDB snapshot before the kill: {last_save:%H:%M:%S}")

        subprocess.run(compose("start", "redis"), check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        waited = time.perf_counter()
        while True:
            try:
                r.ping()
                break
            except redis.ConnectionError:  # also raised while Redis is still loading its files
                if time.perf_counter() - waited > 60:
                    raise
                time.sleep(0.2)
        self.stdout.write(f"Redis answers again after {time.perf_counter() - waited:.1f} s")

        survived = int(r.get(key) or 0)
        lost = max(acknowledged - survived, 0)
        self.stdout.write(f"Counter after the restart: {survived}")
        style = self.style.ERROR if lost else self.style.SUCCESS
        self.stdout.write(style(f"Lost: {lost} writes ({lost / acknowledged:.0%})"))
