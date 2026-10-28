"""Demo 1: 50 withdrawals of 10 at the same time from a balance of 100.

Run with the API running: uv run python -m scripts.demo_concurrency   (or make demo-concurrency)

The rule: the money withdrawn must equal what left the account, and at most 10
withdrawals can succeed. "naive" breaks it (lost update), "atomic" keeps it.
"""

import os
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal

import httpx
from dotenv import load_dotenv

load_dotenv()
API = os.getenv("API_URL", "http://localhost:8000")
ACCOUNT, START, AMOUNT, REQUESTS = 9001, Decimal("100"), Decimal("10"), 50


def run(strategy: str) -> bool:
    httpx.put(f"{API}/accounts/{ACCOUNT}", json={"balance": str(START)}).raise_for_status()

    def one(_):
        with httpx.Client(timeout=30) as client:
            return client.post(
                f"{API}/accounts/{ACCOUNT}/withdraw", params={"strategy": strategy}, json={"amount": str(AMOUNT)}
            ).status_code

    with ThreadPoolExecutor(max_workers=REQUESTS) as pool:
        codes = Counter(pool.map(one, range(REQUESTS)))

    final = Decimal(httpx.get(f"{API}/accounts/{ACCOUNT}").json()["balance"])
    paid_out = codes[200] * AMOUNT
    holds = paid_out == START - final and codes[200] <= START / AMOUNT
    print(f"\n{strategy.upper()}: {REQUESTS} withdrawals of {AMOUNT} from {START}")
    print(f"  succeeded {codes[200]:3}   refused {codes[409]:3}   other {REQUESTS - codes[200] - codes[409]}")
    print(f"  paid out  {paid_out:>6}   balance {final:>6}   paid out + balance = {paid_out + final}")
    print(f"  rule holds: {'YES' if holds else 'NO, money was created'}")
    return holds


if __name__ == "__main__":
    httpx.get(f"{API}/health").raise_for_status()
    run("naive")
    ok = run("atomic")
    sys.exit(0 if ok else 1)
