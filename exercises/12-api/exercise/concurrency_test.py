"""Task 6: five simultaneous rentals of film 7 in store 1.

Run the API first, then:
    uv run python concurrency_test.py

Film 7 has exactly two copies in store 1 on a fresh copy of Pagila. Five
customers (1 to 5) ask for it at the same time, all served by staff 6. Exactly
two requests must get 201 and three must get 409, and the two winners must have
different inventory_id.
"""

from __future__ import annotations

import threading
from collections import Counter

import httpx

URL = "http://127.0.0.1:8000/rentals"
CUSTOMERS = [1, 2, 3, 4, 5]
FILM_ID = 7
STORE_ID = 1
STAFF_ID = 6

barrier = threading.Barrier(len(CUSTOMERS))
results: list[dict] = []
lock = threading.Lock()


def rent(customer_id: int) -> None:
    body = {
        "customer_id": customer_id,
        "film_id": FILM_ID,
        "store_id": STORE_ID,
        "staff_id": STAFF_ID,
    }
    with httpx.Client(timeout=30) as client:
        barrier.wait()
        response = client.post(URL, json=body)
    with lock:
        results.append(
            {
                "customer_id": customer_id,
                "status": response.status_code,
                "body": response.json(),
            }
        )


def main() -> None:
    threads = [threading.Thread(target=rent, args=(cid,)) for cid in CUSTOMERS]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    for result in sorted(results, key=lambda r: r["customer_id"]):
        print(
            f"customer {result['customer_id']}: "
            f"HTTP {result['status']} {result['body']}"
        )

    statuses = Counter(result["status"] for result in results)
    winners = [
        result["body"]["inventory_id"]
        for result in results
        if result["status"] == 201
    ]

    print()
    print(f"status counts: {dict(statuses)}")
    print(f"inventory_ids rented: {winners}")

    assert statuses[201] == 2, f"expected two 201, got {dict(statuses)}"
    assert statuses[409] == 3, f"expected three 409, got {dict(statuses)}"
    assert len(set(winners)) == 2, f"expected two different copies, got {winners}"
    print("OK: exactly two 201, three 409, two different inventory_id")


if __name__ == "__main__":
    main()
