"""Fire concurrent withdrawals at the running API and check the rule for each strategy.

Account 1 starts at 100 and each request withdraws 10, so exactly 10 must succeed
and the final balance must be 0.

    uv run python -m scripts.concurrency                       # API on http://127.0.0.1:8000
    uv run python -m scripts.concurrency --url http://127.0.0.1:8001 --requests 50 --workers 20
"""

import argparse
from concurrent.futures import ThreadPoolExecutor

import httpx


def run(client: httpx.Client, strategy: str, requests: int, workers: int) -> bool:
    client.post("/accounts/reset", params={"balance": 100}).raise_for_status()

    def withdraw(_):
        r = client.post("/accounts/1/withdraw", params={"strategy": strategy}, json={"amount": 10})
        return r.status_code

    with ThreadPoolExecutor(max_workers=workers) as pool:
        codes = list(pool.map(withdraw, range(requests)))

    succeeded = codes.count(200)
    balance = float(client.get("/accounts/1").json()["balance"])
    # The rule: money out (successes x 10) plus what is left equals what we started with.
    holds = succeeded == 10 and balance == 0
    print(
        f"{strategy:<7} succeeded={succeeded:<3} refused={codes.count(409):<3} "
        f"final balance={balance:<6} money withdrawn={succeeded * 10:<4} "
        f"{'OK' if holds else 'RULE BROKEN: lost update'}"
    )
    return holds


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    parser.add_argument("--requests", type=int, default=50)
    # Each request opens one PostgreSQL connection; 20 at a time keeps well under max_connections.
    parser.add_argument("--workers", type=int, default=20)
    parser.add_argument("--strategies", default="naive,atomic,lock")
    args = parser.parse_args()

    with httpx.Client(base_url=args.url, timeout=30, limits=httpx.Limits(max_connections=args.workers)) as client:
        for strategy in args.strategies.split(","):
            run(client, strategy, args.requests, args.workers)


if __name__ == "__main__":
    main()
