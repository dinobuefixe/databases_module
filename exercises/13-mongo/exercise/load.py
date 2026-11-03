"""Load Pagila (PostgreSQL) into MongoDB as three collections.

films      one document per film; actors and categories embedded
customers  one document per customer; only the 10 most recent rentals embedded
rentals    one document per rental (full history)

Idempotent: every document is written with ReplaceOne(upsert=True) on its
Pagila id, so running the script twice leaves the same documents.

Environment variables:
    PAGILA_DSN  PostgreSQL connection string (required)
    MONGO_URI   default mongodb://localhost:27017
    MONGO_DB    default pagila
"""

from __future__ import annotations

import os
from collections import defaultdict

import psycopg
from bson.decimal128 import Decimal128
from psycopg.rows import dict_row
from pymongo import MongoClient, ReplaceOne

BATCH_SIZE = 1000
RECENT_RENTALS_LIMIT = 10


def query(conn: psycopg.Connection, sql: str) -> list[dict]:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(sql)
        return cur.fetchall()


def load_films(conn: psycopg.Connection) -> dict[int, dict]:
    films: dict[int, dict] = {}
    for r in query(conn, """
        SELECT f.film_id, f.title, f.release_year, trim(l.name) AS language,
               f.rating::text AS rating, f.length, f.rental_duration,
               f.rental_rate::text AS rental_rate
        FROM film f
        JOIN language l ON l.language_id = f.language_id
        ORDER BY f.film_id
    """):
        films[r["film_id"]] = {
            "_id": r["film_id"],
            "title": r["title"],
            "release_year": r["release_year"],
            "language": r["language"],
            "rating": r["rating"],
            "length": r["length"],
            "rental_duration": r["rental_duration"],
            "rental_rate": Decimal128(r["rental_rate"]),
            "categories": [],
            "actors": [],
        }

    for r in query(conn, """
        SELECT fc.film_id, c.name
        FROM film_category fc
        JOIN category c ON c.category_id = fc.category_id
        ORDER BY fc.film_id, c.name
    """):
        films[r["film_id"]]["categories"].append(r["name"])

    for r in query(conn, """
        SELECT fa.film_id, fa.actor_id,
               a.first_name || ' ' || a.last_name AS name
        FROM film_actor fa
        JOIN actor a ON a.actor_id = fa.actor_id
        ORDER BY fa.film_id, fa.actor_id
    """):
        films[r["film_id"]]["actors"].append(
            {"actor_id": r["actor_id"], "name": r["name"]}
        )
    return films


def load_customer_rows(conn: psycopg.Connection) -> list[dict]:
    return query(conn, """
        SELECT c.customer_id, c.first_name, c.last_name, c.email, c.store_id,
               ci.city, co.country
        FROM customer c
        JOIN address a ON a.address_id = c.address_id
        JOIN city ci ON ci.city_id = a.city_id
        JOIN country co ON co.country_id = ci.country_id
        ORDER BY c.customer_id
    """)


def load_rentals(conn: psycopg.Connection, films: dict[int, dict]) -> list[dict]:
    rows = query(conn, """
        SELECT r.rental_id, r.customer_id, i.film_id, f.title, i.store_id,
               r.rental_date, r.return_date,
               COALESCE(SUM(p.amount), 0)::text AS amount
        FROM rental r
        JOIN inventory i ON i.inventory_id = r.inventory_id
        JOIN film f ON f.film_id = i.film_id
        LEFT JOIN payment p ON p.rental_id = r.rental_id
        GROUP BY r.rental_id, r.customer_id, i.film_id, f.title,
                 i.store_id, r.rental_date, r.return_date
        ORDER BY r.rental_id
    """)
    return [
        {
            "_id": r["rental_id"],
            "customer_id": r["customer_id"],
            "film_id": r["film_id"],
            "title": r["title"],
            "categories": films[r["film_id"]]["categories"],
            "store_id": r["store_id"],
            "rental_date": r["rental_date"],
            "return_date": r["return_date"],
            "amount": Decimal128(r["amount"]),
        }
        for r in rows
    ]


def build_customers(customer_rows: list[dict], rentals: list[dict]) -> list[dict]:
    by_customer: dict[int, list[dict]] = defaultdict(list)
    for rt in rentals:
        by_customer[rt["customer_id"]].append(rt)

    docs = []
    for c in customer_rows:
        # Newest first; rental_id breaks ties, as the spec requires.
        history = sorted(
            by_customer[c["customer_id"]],
            key=lambda rt: (rt["rental_date"], rt["_id"]),
            reverse=True,
        )
        docs.append({
            "_id": c["customer_id"],
            "first_name": c["first_name"],
            "last_name": c["last_name"],
            "email": c["email"],
            "store_id": c["store_id"],
            "address": {"city": c["city"], "country": c["country"]},
            "rental_count": len(history),
            "recent_rentals": [
                {
                    "rental_id": rt["_id"],
                    "film_id": rt["film_id"],
                    "title": rt["title"],
                    "rental_date": rt["rental_date"],
                    "return_date": rt["return_date"],
                }
                for rt in history[:RECENT_RENTALS_LIMIT]
            ],
        })
    return docs


def replace_all(coll, docs: list[dict]) -> None:
    """Upsert every document by _id, then remove documents no longer in the source."""
    ops: list[ReplaceOne] = []
    for doc in docs:
        ops.append(ReplaceOne({"_id": doc["_id"]}, doc, upsert=True))
        if len(ops) == BATCH_SIZE:
            coll.bulk_write(ops, ordered=False)
            ops = []
    if ops:
        coll.bulk_write(ops, ordered=False)
    coll.delete_many({"_id": {"$nin": [d["_id"] for d in docs]}})


def mongo_client() -> MongoClient:
    return MongoClient(
        host=os.environ.get("MONGO_HOST", "127.0.0.1:27017:27017"),
        port=int(os.environ.get("MONGO_PORT", "27017")),
        username=os.environ["MONGO_ROOT_USER"],
        password=os.environ["MONGO_ROOT_PASSWORD"],
        authSource="admin",
    )


def main() -> None:
    with psycopg.connect(os.environ["PAGILA_DSN"]) as conn:
        films = load_films(conn)
        customer_rows = load_customer_rows(conn)
        rentals = load_rentals(conn, films)

    customers = build_customers(customer_rows, rentals)

    client = mongo_client()
    db = client[os.environ.get("MONGO_DB", "pagila")]

    replace_all(db.films, list(films.values()))
    replace_all(db.customers, customers)
    replace_all(db.rentals, rentals)

    for name in ("films", "customers", "rentals"):
        print(f"{name}: {db[name].count_documents({})} documentos")
    client.close()


if __name__ == "__main__":
    main()
