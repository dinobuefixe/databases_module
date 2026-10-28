"""Several workers take tasks from the same queue at the same time.

naive        SELECT the first waiting task, process it, mark it done. Two workers can read the same
             task before either marks it, and both process it.
skip-locked  The same, with FOR UPDATE SKIP LOCKED on the SELECT. The row stays locked until the
             worker commits, and the other workers skip it instead of waiting for it.

task.runs counts how many times each task was processed. The rule: every task exactly once.

    uv run python -m scripts.task_queue
    uv run python -m scripts.task_queue --tasks 1000 --workers 8 --strategies skip-locked
"""

import argparse
import sys
import threading
import time
from collections import Counter

from app.db import pg_connect, run_sql_file

PROCESS_SECONDS = 0.005  # the "work" done for each task

CLAIM = {
    "naive": "SELECT id FROM task WHERE done_by IS NULL ORDER BY id LIMIT 1",
    "skip-locked": "SELECT id FROM task WHERE done_by IS NULL ORDER BY id LIMIT 1 FOR UPDATE SKIP LOCKED",
}


def worker(name: str, strategy: str, done: Counter) -> None:
    with pg_connect(autocommit=True) as conn:
        while True:
            # One transaction per task: the claim, the work and the UPDATE.
            with conn.transaction():
                row = conn.execute(CLAIM[strategy]).fetchone()
                if row is None:
                    return  # nothing left that this worker can take
                time.sleep(PROCESS_SECONDS)
                conn.execute("UPDATE task SET done_by = %s, runs = runs + 1 WHERE id = %s", (name, row["id"]))
            done[name] += 1


def run(strategy: str, tasks: int, workers: int) -> dict:
    """Fill the queue, let the workers empty it, and count how often each task ran."""
    run_sql_file("003_task.sql")
    with pg_connect() as conn:
        conn.execute("TRUNCATE task RESTART IDENTITY")
        conn.execute("INSERT INTO task (done_by) SELECT NULL FROM generate_series(1, %s)", (tasks,))

    done: Counter = Counter()
    threads = [threading.Thread(target=worker, args=(f"w{i}", strategy, done)) for i in range(1, workers + 1)]
    started = time.perf_counter()
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    elapsed = time.perf_counter() - started

    with pg_connect() as conn:
        result = conn.execute(
            """
            SELECT count(*)                         AS tasks,
                   count(*) FILTER (WHERE runs = 1) AS once,
                   count(*) FILTER (WHERE runs > 1) AS more_than_once,
                   count(*) FILTER (WHERE runs = 0) AS never,
                   sum(runs)                        AS runs
            FROM task
            """
        ).fetchone()
    return {**result, "per_worker": dict(sorted(done.items())), "seconds": elapsed}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tasks", type=int, default=100)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--strategies", default="naive,skip-locked")
    args = parser.parse_args()

    broken = []
    for strategy in args.strategies.split(","):
        r = run(strategy, args.tasks, args.workers)
        holds = r["once"] == r["tasks"]
        print(
            f"{strategy:<12} tasks={r['tasks']} once={r['once']} more_than_once={r['more_than_once']} "
            f"never={r['never']} runs={r['runs']} in {r['seconds']:.1f} s  {'OK' if holds else 'RULE BROKEN'}"
        )
        print(f"{'':<12} per worker: {r['per_worker']}")
        if strategy != "naive" and not holds:
            broken.append(strategy)
    if broken:
        sys.exit(f"safe strategies failed: {broken}")


if __name__ == "__main__":
    main()
