"""The tutorial's queries and a helper that runs EXPLAIN (ANALYZE, BUFFERS) on them."""

import re

from app.db import pg_connect

QUERIES = {
    # Served by the composite index (customer_id, rented_at DESC): filter and sort in one walk.
    "customer_latest": "SELECT * FROM big_rental WHERE customer_id = %(customer_id)s ORDER BY rented_at DESC LIMIT 10",
    # Served by the partial index WHERE returned_at IS NULL.
    "open_overdue": "SELECT count(*) FROM big_rental WHERE returned_at IS NULL AND rented_at < now() - interval '30 days'",
    # Served by the expression index on lower(email).
    "customer_email": "SELECT customer_id, first_name, last_name, email FROM customer WHERE lower(email) = lower(%(email)s)",
    # The index on rented_at helps when few rows match (days=7), not when most do (days=730).
    "recent_rentals": "SELECT * FROM big_rental WHERE rented_at > now() - make_interval(days => %(days)s::int)",
}

DEFAULT_PARAMS = {"customer_id": 42, "email": "mary.smith@sakilacustomer.org", "days": 730}


def explain(name: str, params: dict | None = None, force_index: bool = False) -> dict:
    """Run the query under EXPLAIN (ANALYZE, BUFFERS) and return the plan with the timings."""
    query = QUERIES[name]
    params = {**DEFAULT_PARAMS, **(params or {})}
    with pg_connect() as conn:
        if force_index:
            # Only to measure the plan the planner rejected. SET LOCAL ends with the transaction.
            conn.execute("SET LOCAL enable_seqscan = off")
            conn.execute("SET LOCAL enable_bitmapscan = off")
        rows = conn.execute("EXPLAIN (ANALYZE, BUFFERS) " + query, params).fetchall()
    plan = [row["QUERY PLAN"] for row in rows]
    text = "\n".join(plan)

    def ms(label: str) -> float | None:
        found = re.search(rf"{label}: ([\d.]+) ms", text)
        return float(found.group(1)) if found else None

    return {
        "query": query,
        "params": {k: v for k, v in params.items() if f"%({k})s" in query},
        "force_index": force_index,
        "planning_ms": ms("Planning Time"),
        "execution_ms": ms("Execution Time"),
        # The first line names the top node; look for Seq Scan, Index Scan or Bitmap Heap Scan below it.
        "plan": plan,
    }
