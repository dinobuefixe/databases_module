"""Sends ZINCRBY to this week's leaderboard as fast as it can, then prints the rate and the top 10.

Run with: uv run python -m scripts.leaderboard_load [--seconds 5] [--batch 100]

Each batch goes in one pipeline with transaction=False: one round trip, no MULTI/EXEC.
Other clients' commands may run between the increments, which is fine because each
ZINCRBY is atomic on its own. --batch 1 sends one command per round trip, for comparison.
"""

import argparse
import random
import time

from app.db import r
from app.patterns import LEADERBOARD_TTL, leaderboard_key

parser = argparse.ArgumentParser()
parser.add_argument("--seconds", type=float, default=5)
parser.add_argument("--batch", type=int, default=100)
args = parser.parse_args()

key = leaderboard_key()
updates = 0
start = time.perf_counter()
while time.perf_counter() - start < args.seconds:
    pipe = r.pipeline(transaction=False)
    for _ in range(args.batch):
        # 999 ** random() is between 1 and 999 but mostly small, so a few customers rent a lot;
        # * 337 % 999 shuffles which ids those are, so the top 10 is not just ids 1 to 10.
        customer_id = int(999 ** random.random()) * 337 % 999 + 1
        pipe.zincrby(key, 1, f"customer:{customer_id}")
    pipe.expire(key, LEADERBOARD_TTL, nx=True)
    pipe.execute()
    updates += args.batch
elapsed = time.perf_counter() - start

print(f"{updates:,} ZINCRBY in {elapsed:.1f} s: {updates / elapsed:,.0f} updates per second (batch {args.batch})")
print(f"{key}: {r.zcard(key)} customers, TTL {r.ttl(key)} s")
for rank, (member, score) in enumerate(r.zrange(key, 0, 9, desc=True, withscores=True), start=1):
    print(f"{rank:>3}. {member:<14} {int(score):>8}")
rank = r.zrevrank(key, "customer:500")
if rank is not None:
    print(f"customer:500 is number {rank + 1} with {int(r.zscore(key, 'customer:500'))}")
