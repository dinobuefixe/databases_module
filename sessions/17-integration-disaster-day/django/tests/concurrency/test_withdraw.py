from decimal import Decimal

from tests.concurrency.conftest import run_concurrently


def test_fifty_withdrawals_of_ten_from_one_hundred(api, pg):
    pg.execute(
        "INSERT INTO account (id, balance) VALUES (1, 100) ON CONFLICT (id) DO UPDATE SET balance = 100"
    )

    def withdraw(_):
        return api.post("/accounts/1/withdraw", json={"amount": 10}).status_code

    statuses = run_concurrently(withdraw, 50)

    assert statuses.count(200) == 10, statuses
    assert statuses.count(409) == 40, statuses
    assert Decimal(api.get("/accounts/1").json()["balance"]) == 0
