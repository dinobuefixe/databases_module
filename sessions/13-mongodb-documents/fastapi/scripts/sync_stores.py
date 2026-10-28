"""Reads every Pagila store from PostgreSQL and upserts one document per store.

Run with: uv run python -m scripts.sync_stores

Embedded, because they are read with the store, belong to it and have a bounded size:
the address, the manager and the staff list. Running the script again updates the
documents in place (upsert on _id = store_id), so it is safe to repeat.
"""

from collections import defaultdict

from pymongo import UpdateOne

from app.clients import db, pg_connect

STORES_SQL = """
    SELECT s.store_id, a.address, c.city, co.country,
           m.staff_id, m.first_name || ' ' || m.last_name AS manager_name
    FROM store s
    JOIN address a  ON a.address_id = s.address_id
    JOIN city c     ON c.city_id = a.city_id
    JOIN country co ON co.country_id = c.country_id
    JOIN staff m    ON m.staff_id = s.manager_staff_id
    ORDER BY s.store_id
"""

STAFF_SQL = """
    SELECT store_id, staff_id, first_name || ' ' || last_name
    FROM staff
    ORDER BY store_id, staff_id
"""


def main() -> None:
    with pg_connect() as pg:
        stores = pg.execute(STORES_SQL).fetchall()
        staff_by_store = defaultdict(list)
        for store_id, staff_id, name in pg.execute(STAFF_SQL):
            staff_by_store[store_id].append({"staff_id": staff_id, "name": name})

    ops = [
        UpdateOne(
            {"_id": store_id},
            {
                "$set": {
                    "manager": {"staff_id": manager_id, "name": manager_name},
                    "address": {"line": line, "city": city, "country": country},
                    "staff": staff_by_store[store_id],
                }
            },
            upsert=True,
        )
        for store_id, line, city, country, manager_id, manager_name in stores
    ]
    # One round trip for all the upserts instead of one update_one per store.
    result = db.stores.bulk_write(ops)
    print(
        f"{len(ops)} stores: {result.upserted_count} inserted, "
        f"{result.modified_count} modified, {result.matched_count - result.modified_count} unchanged"
    )


if __name__ == "__main__":
    main()
