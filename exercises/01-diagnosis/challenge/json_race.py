"""Race conditions on a plain JSON file.

10 processes each append 1,000 records to ``records.json``, one at a time:
read the whole file, append one record, write the whole file back. There is no
lock, so two processes can read the same content and one of the two writes is
lost. A process can also read a half-written file (not valid JSON): that is
counted as a failed write and the process carries on.

Run:  uv run python json_race.py
"""

import json
import multiprocessing as mp
import os

HERE = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(HERE, "records.json")

WORKERS = 10
PER_WORKER = 1_000


def worker(worker_id: int, failed_writes) -> None:
    """Append PER_WORKER records, read-modify-write, without any lock."""
    local_failures = 0
    for n in range(PER_WORKER):
        # Read the whole file. Another process may be writing it right now,
        # so the content may be empty or half-written: not valid JSON.
        try:
            with open(PATH, encoding="utf-8") as fh:
                data = json.load(fh)
        except (json.JSONDecodeError, ValueError):
            local_failures += 1
            continue

        data.append({"worker": worker_id, "n": n})

        # Write the whole file back. This truncates the file first, so a
        # concurrent reader can see an empty or partial file.
        try:
            with open(PATH, "w", encoding="utf-8") as fh:
                json.dump(data, fh)
        except OSError:
            local_failures += 1

    failed_writes.value += local_failures


def count_records() -> int:
    """How many records the file holds at the end.

    The race can leave the file invalid (a longer document was truncated in
    the middle of another write). When that happens, recover the leading valid
    JSON array so we can still report a number instead of failing.
    """
    with open(PATH, encoding="utf-8") as fh:
        text = fh.read()
    try:
        return len(json.loads(text))
    except (json.JSONDecodeError, ValueError):
        try:
            value, _ = json.JSONDecoder().raw_decode(text)
            return len(value) if isinstance(value, list) else -1
        except (json.JSONDecodeError, ValueError):
            return -1


def main() -> None:
    # Starting point: an empty JSON array.
    with open(PATH, "w", encoding="utf-8") as fh:
        json.dump([], fh)

    failed_writes = mp.Value("i", 0)
    processes = [
        mp.Process(target=worker, args=(w, failed_writes))
        for w in range(WORKERS)
    ]

    for p in processes:
        p.start()
    for p in processes:
        p.join()

    records = count_records()

    print(f"records in file: {records}")
    print(f"failed writes:   {failed_writes.value}")
    print(f"expected:        {WORKERS * PER_WORKER}")


if __name__ == "__main__":
    main()
