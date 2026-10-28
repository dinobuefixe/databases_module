"""Builds the two collections the pipelines read, from PostgreSQL.

Run with: uv run python -m scripts.load_collections

films:     one document per film, actors and category names embedded (both are
           bounded and read with the film). This Pagila gives a film 1 to 3
           categories, so `categories` is a list.
customers: one document per customer with its store, the last 10 rentals embedded
           and the total count; the full history stays in PostgreSQL (referenced).

The collections are replaced on every run, so the script is safe to repeat.
"""

from collections import defaultdict
from decimal import Decimal

from bson.decimal128 import Decimal128

from app.clients import db, pg_connect

FILMS_SQL = """
    SELECT film_id, title, rating::text, rental_rate, length
    FROM film
    ORDER BY film_id
"""

FILM_CATEGORIES_SQL = """
    SELECT fc.film_id, c.name
    FROM film_category fc
    JOIN category c ON c.category_id = fc.category_id
    ORDER BY fc.film_id, c.name
"""

FILM_ACTORS_SQL = """
    SELECT fa.film_id, a.actor_id, a.first_name || ' ' || a.last_name
    FROM film_actor fa
    JOIN actor a ON a.actor_id = fa.actor_id
    ORDER BY fa.film_id, a.actor_id
"""

# ROW_NUMBER keeps the 10 most recent rentals of each customer.
RECENT_RENTALS_SQL = """
    SELECT customer_id, rental_id, rental_date, film_id, title, total
    FROM (
        SELECT r.customer_id, r.rental_id, r.rental_date, f.film_id, f.title,
               count(*) OVER (PARTITION BY r.customer_id) AS total,
               row_number() OVER (PARTITION BY r.customer_id ORDER BY r.rental_date DESC) AS n
        FROM rental r
        JOIN inventory i ON i.inventory_id = r.inventory_id
        JOIN film f      ON f.film_id = i.film_id
    ) t
    WHERE n <= 10
    ORDER BY customer_id, rental_date DESC
"""

CUSTOMERS_SQL = "SELECT customer_id, first_name || ' ' || last_name, store_id FROM customer ORDER BY customer_id"


def load_films(pg) -> int:
    actors = defaultdict(list)
    for film_id, actor_id, name in pg.execute(FILM_ACTORS_SQL):
        actors[film_id].append({"actor_id": actor_id, "name": name})
    categories = defaultdict(list)
    for film_id, name in pg.execute(FILM_CATEGORIES_SQL):
        categories[film_id].append(name)

    docs = [
        {
            "_id": film_id,
            "title": title,
            "rating": rating,
            # Decimal128 keeps money exact; a float would turn 0.99 into 0.98999...
            "rental_rate": Decimal128(rate),
            "length": length,
            "categories": categories[film_id],
            "actors": actors[film_id],
        }
        for film_id, title, rating, rate, length in pg.execute(FILMS_SQL)
    ]
    db.films.drop()
    db.films.insert_many(docs)
    return len(docs)


def load_customers(pg) -> int:
    recent = defaultdict(list)
    totals: dict[int, int] = {}
    for customer_id, rental_id, rental_date, film_id, title, total in pg.execute(RECENT_RENTALS_SQL):
        recent[customer_id].append(
            {"rental_id": rental_id, "rental_date": rental_date, "film_id": film_id, "title": title}
        )
        totals[customer_id] = total

    docs = [
        {
            "_id": customer_id,
            "name": name,
            "store_id": store_id,
            "rentals_total": totals.get(customer_id, 0),
            "recent_rentals": recent[customer_id],
        }
        for customer_id, name, store_id in pg.execute(CUSTOMERS_SQL)
    ]
    db.customers.drop()
    db.customers.insert_many(docs)
    # Multikey index: one entry per embedded rental. A $match on the rental date at the
    # start of a pipeline can use it (see /pipelines/match-position).
    db.customers.create_index("recent_rentals.rental_date")
    return len(docs)


def main() -> None:
    with pg_connect() as pg:
        print("films:", load_films(pg))
        print("customers:", load_customers(pg))


if __name__ == "__main__":
    main()
