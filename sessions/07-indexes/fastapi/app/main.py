from typing import Literal

from fastapi import FastAPI

from app.db import pg_connect
from app.indexes import INDEXES
from app.queries import QUERIES, explain

app = FastAPI(title="Session 07: indexes and optimisation")

QueryName = Literal[tuple(QUERIES)]


@app.get("/explain/{name}")
def explain_query(
    name: QueryName,
    customer_id: int = 42,
    email: str = "mary.smith@sakilacustomer.org",
    days: int = 730,
    force_index: bool = False,
):
    """EXPLAIN (ANALYZE, BUFFERS) for one tutorial query: the plan text and the execution time.

    force_index=1 turns off sequential and bitmap scans for this query only, to time the index scan the planner rejected.
    """
    return explain(name, {"customer_id": customer_id, "email": email, "days": days}, force_index)


@app.get("/indexes")
def list_indexes():
    """Which tutorial indexes exist right now, and how big they are."""
    names = [index.name for index in INDEXES.values()]
    with pg_connect() as conn:
        found = conn.execute(
            """
            SELECT indexrelname AS name, relname AS table_name,
                   pg_size_pretty(pg_relation_size(indexrelid)) AS size,
                   pg_get_indexdef(indexrelid) AS definition
            FROM pg_stat_user_indexes
            WHERE indexrelname = ANY(%s)
            """,
            (names,),
        ).fetchall()
        table_size = conn.execute(
            "SELECT pg_size_pretty(pg_relation_size('big_rental')) AS size"
        ).fetchone()["size"]
    by_name = {row["name"]: row for row in found}
    return {
        "big_rental_size": table_size,
        "indexes": {key: by_name.get(index.name, {"name": index.name, "exists": False}) for key, index in INDEXES.items()},
    }
