"""Business rules that must hold when many requests arrive at the same time.

Run with the API running: uv run pytest tests/concurrency -v
"""

from collections import Counter
from concurrent.futures import ThreadPoolExecutor

import httpx

TEST_ACCOUNT = 9001


def fire(n: int, request) -> list[httpx.Response]:
    """Sends n requests in parallel, each from its own client."""
    def one(i):
        with httpx.Client(timeout=30) as client:
            return request(client, i)

    with ThreadPoolExecutor(max_workers=n) as pool:
        return list(pool.map(one, range(n)))


def test_withdrawals_never_overdraw(api):
    httpx.put(f"{api}/accounts/{TEST_ACCOUNT}", json={"balance": "100"}).raise_for_status()

    responses = fire(50, lambda c, i: c.post(f"{api}/accounts/{TEST_ACCOUNT}/withdraw", json={"amount": "10"}))

    codes = Counter(r.status_code for r in responses)
    assert codes == {200: 10, 409: 40}, codes
    assert httpx.get(f"{api}/accounts/{TEST_ACCOUNT}").json()["balance"] == "0.00"


def test_rentals_keep_redis_in_sync(api):
    customer_id = 1
    # 20 different inventory items, so 20 rentals of up to 20 different films.
    responses = fire(
        20,
        lambda c, i: c.post(f"{api}/rentals", json={"customer_id": customer_id, "inventory_id": 100 + i * 37}),
    )
    assert all(r.status_code == 201 for r in responses), [r.text for r in responses if r.status_code != 201]

    films = httpx.get(f"{api}/customers/{customer_id}/films").json()
    assert films["redis"] == films["postgres"], films


def test_monthly_report_is_written_once(api):
    # A month with no report yet, so the test can be run more than once.
    month = next(
        (
            f"{y}-{m:02d}"
            for y in range(2022, 2027)
            for m in range(1, 13)
            if httpx.get(f"{api}/reports/monthly/{y}-{m:02d}").status_code == 404
        ),
        None,
    )
    assert month is not None, "every month already has a report"

    responses = fire(10, lambda c, i: c.post(f"{api}/reports/monthly/{month}"))

    codes = Counter(r.status_code for r in responses)
    assert codes == {201: 1, 409: 9}, codes
