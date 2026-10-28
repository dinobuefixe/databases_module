"""Starts two workers at the same time; only the one that gets the lock runs the job.

Run with: uv run python -m scripts.lock_demo
"""

import threading
import time

from app.patterns import r, run_exclusively

start = threading.Barrier(2)


def job(worker: str) -> None:
    print(f"{worker}: running the job")
    time.sleep(2)
    print(f"{worker}: done")


def worker(name: str) -> None:
    start.wait()  # both workers try to take the lock at the same moment
    ran = run_exclusively("nightly-export", lambda: job(name))
    if not ran:
        print(f"{name}: lock held by someone else ({r.get('lock:nightly-export')}), skipping")


threads = [threading.Thread(target=worker, args=(name,)) for name in ("worker-a", "worker-b")]
for t in threads:
    t.start()
for t in threads:
    t.join()
print("lock after both workers:", r.get("lock:nightly-export"))
