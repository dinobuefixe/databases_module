"""Records or checks the numbers the runbook uses to verify a restore.

Run with:
    uv run python -m scripts.snapshot --save backups/<dir>/snapshot.json     (called by backup.sh)
    uv run python -m scripts.snapshot --compare backups/<dir>/snapshot.json  (called by verify.sh)

The snapshot holds row counts, document counts and the result of one known query.
--compare prints every value next to the one in the backup and exits 1 if any differs.
"""

import argparse
import json
import sys

from sqlalchemy import text

from app.db import SessionLocal, mongo_db

TABLES = ["customer", "film", "inventory", "rental", "payment", "account"]
KNOWN_QUERY = "SELECT count(*) FROM rental WHERE customer_id = 1"


def take() -> dict:
    with SessionLocal() as session:
        snapshot = {
            f"postgres.{t}": session.execute(text(f"SELECT count(*) FROM {t}")).scalar_one()  # fixed list above
            for t in TABLES
        }
        snapshot["postgres.known_query"] = session.execute(text(KNOWN_QUERY)).scalar_one()
    for name in sorted(mongo_db.list_collection_names()):
        snapshot[f"mongo.{name}"] = mongo_db[name].count_documents({})
    return snapshot


def main() -> None:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--save")
    group.add_argument("--compare")
    args = parser.parse_args()

    current = take()
    if args.save:
        with open(args.save, "w") as f:
            json.dump(current, f, indent=2)
        print(f"snapshot saved to {args.save}")
        return

    with open(args.compare) as f:
        expected = json.load(f)
    differences = 0
    for key in sorted(expected.keys() | current.keys()):
        ok = expected.get(key) == current.get(key)
        differences += not ok
        print(f"{'ok  ' if ok else 'DIFF'} {key:28} backup={expected.get(key)} now={current.get(key)}")
    sys.exit(1 if differences else 0)


if __name__ == "__main__":
    main()
