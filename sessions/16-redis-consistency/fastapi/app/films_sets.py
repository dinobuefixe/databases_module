"""customer:{id}:films is derived data: the set of film ids a customer has rented.

PostgreSQL is the source of truth. These functions rebuild the sets from it and
check that Redis still agrees.
"""

from app.clients import r


def films_key(customer_id: int) -> str:
    return f"customer:{customer_id}:films"


# --- Version 1: one query per customer (the tutorial's first version) -------

def rebuild_customer(pg, customer_id: int) -> None:
    key = films_key(customer_id)
    tmp = key + ":rebuild"
    film_ids = [row[0] for row in pg.execute("""
        SELECT DISTINCT i.film_id
        FROM rental r JOIN inventory i ON i.inventory_id = r.inventory_id
        WHERE r.customer_id = %s
    """, (customer_id,))]

    # Build into a temporary key and RENAME it over the real one, so a reader
    # sees the old set or the new one, never a half-built set.
    pipe = r.pipeline(transaction=True)
    pipe.delete(tmp)
    if film_ids:
        pipe.sadd(tmp, *film_ids)
        pipe.rename(tmp, key)
    else:
        pipe.delete(key)
    pipe.execute()


def rebuild_per_customer(pg) -> int:
    customer_ids = [row[0] for row in pg.execute("SELECT customer_id FROM customer ORDER BY customer_id")]
    for customer_id in customer_ids:
        rebuild_customer(pg, customer_id)
    return len(customer_ids)


# --- Version 2: one query and one pipeline -----------------------------------

def rebuild_single_query(pg) -> int:
    rows = pg.execute("""
        SELECT c.customer_id,
               array_agg(DISTINCT i.film_id) FILTER (WHERE i.film_id IS NOT NULL)
        FROM customer c
        LEFT JOIN rental r    ON r.customer_id = c.customer_id
        LEFT JOIN inventory i ON i.inventory_id = r.inventory_id
        GROUP BY c.customer_id
    """).fetchall()

    # Not a transaction: one round trip for everything, and each RENAME is still atomic.
    pipe = r.pipeline(transaction=False)
    for customer_id, film_ids in rows:
        key = films_key(customer_id)
        tmp = key + ":rebuild"
        pipe.delete(tmp)
        if film_ids:
            pipe.sadd(tmp, *film_ids)
            pipe.rename(tmp, key)
        else:
            pipe.delete(key)
    pipe.execute()
    return len(rows)


# --- Verification ------------------------------------------------------------

def mismatch(key: str, missing: set[str], extra: set[str], orphan: bool = False) -> dict:
    """`missing`: film ids PostgreSQL has and Redis does not. `extra`: the other way round."""
    def by_number(member: str) -> tuple[int, str]:  # members are strings: "9" before "10"
        return len(member), member
    return {"key": key, "missing": sorted(missing, key=by_number), "extra": sorted(extra, key=by_number), "orphan": orphan}


def verify(pg) -> list[dict]:
    """Compares the members of every set with PostgreSQL and looks for keys no
    customer explains. Returns the mismatches."""
    rows = pg.execute("""
        SELECT c.customer_id,
               coalesce(array_agg(DISTINCT i.film_id) FILTER (WHERE i.film_id IS NOT NULL), '{}')
        FROM customer c
        LEFT JOIN rental r    ON r.customer_id = c.customer_id
        LEFT JOIN inventory i ON i.inventory_id = r.inventory_id
        GROUP BY c.customer_id
        ORDER BY c.customer_id
    """).fetchall()
    # Redis returns members as strings, so compare strings.
    expected = {films_key(customer_id): {str(f) for f in film_ids} for customer_id, film_ids in rows}

    pipe = r.pipeline(transaction=False)
    for key in expected:
        pipe.smembers(key)
    actual = pipe.execute()  # one round trip for every SMEMBERS

    mismatches = [
        mismatch(key, missing=want - have, extra=have - want)
        for (key, want), have in zip(expected.items(), actual)
        if have != want
    ]

    # A set for a customer PostgreSQL does not have (deleted, or never existed) is
    # also wrong. SCAN walks the keys in batches; KEYS would block Redis while it runs.
    for key in r.scan_iter(match=films_key("*"), count=1000):
        if key not in expected:
            mismatches.append(mismatch(key, missing=set(), extra=r.smembers(key), orphan=True))
    return mismatches
