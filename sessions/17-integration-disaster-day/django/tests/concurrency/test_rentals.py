from tests.concurrency.conftest import run_concurrently


def test_redis_matches_postgres_after_concurrent_rentals(api, pg):
    customer_id, staff_id = 1, 1
    inventory_ids = [row[0] for row in pg.execute("SELECT inventory_id FROM inventory ORDER BY random() LIMIT 30")]

    def rent(i):
        body = {"customer_id": customer_id, "inventory_id": inventory_ids[i], "staff_id": staff_id}
        return api.post("/rentals", json=body).status_code

    statuses = run_concurrently(rent, len(inventory_ids))
    assert statuses.count(201) == len(inventory_ids), statuses

    expected = {
        row[0]
        for row in pg.execute(
            "SELECT DISTINCT i.film_id FROM rental r JOIN inventory i USING (inventory_id) WHERE r.customer_id = %s",
            (customer_id,),
        )
    }
    assert set(api.get(f"/customers/{customer_id}/films").json()["film_ids"]) == expected

    result = api.get("/verify").json()
    assert result["ok"], result["first_mismatches"]
