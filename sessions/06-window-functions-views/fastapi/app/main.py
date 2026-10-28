import time
from datetime import date

import psycopg
from fastapi import FastAPI, HTTPException, Query

from app.db import SQL_DIR, pg_connect

app = FastAPI(title="Session 06: window functions and views")


def run(name: str, params: dict) -> list[dict]:
    with pg_connect() as conn:
        return conn.execute((SQL_DIR / f"{name}.sql").read_text(), params).fetchall()


@app.get("/films/longest-per-rating")
def longest_per_rating(top: int = Query(2, ge=1, le=20)):
    """DENSE_RANK per rating: more than `top` rows per rating when films tie on length."""
    return run("longest_per_rating", {"top": top})


@app.get("/customers/{customer_id}/running-total")
def running_total(customer_id: int):
    """SUM(amount) OVER (PARTITION BY customer_id ORDER BY payment_date)."""
    rows = run("running_total", {"customer_id": customer_id})
    if not rows:
        raise HTTPException(404, "no payments for this customer")
    return rows


@app.get("/customers/{customer_id}/rental-gaps")
def rental_gaps(customer_id: int):
    """LAG(rental_date): the interval since the customer's previous rental."""
    rows = run("rental_gaps", {"customer_id": customer_id})
    if not rows:
        raise HTTPException(404, "no rentals for this customer")
    # psycopg returns an interval as a timedelta; str() gives "3 days, 4:05:00".
    return [{**row, "gap": str(row["gap"]) if row["gap"] is not None else None} for row in rows]


@app.get("/daily-rentals")
def daily_rentals(
    start: date | None = None,
    end: date | None = None,
    limit: int = Query(31, ge=1, le=1000),
):
    """Read the materialised view. No GROUP BY runs here: the counts are stored."""
    with pg_connect() as conn:
        return conn.execute(
            """
            SELECT day, rentals FROM daily_rentals
            WHERE (%(start)s::date IS NULL OR day >= %(start)s)
              AND (%(end)s::date IS NULL OR day <= %(end)s)
            ORDER BY day DESC
            LIMIT %(limit)s
            """,
            {"start": start, "end": end, "limit": limit},
        ).fetchall()


@app.post("/daily-rentals/refresh")
def refresh_daily_rentals(concurrently: bool = True):
    """Recompute the stored result.

    CONCURRENTLY lets readers keep reading the old rows during the refresh. It needs the
    unique index on daily_rentals (day). Without it, the refresh locks out readers.
    """
    statement = "REFRESH MATERIALIZED VIEW " + ("CONCURRENTLY " if concurrently else "") + "daily_rentals"
    with pg_connect(autocommit=True) as conn:
        started = time.perf_counter()
        try:
            conn.execute(statement)
        except psycopg.errors.ObjectNotInPrerequisiteState as exc:
            # Raised by CONCURRENTLY when the unique index is missing.
            raise HTTPException(409, {"error": exc.diag.message_primary, "hint": exc.diag.message_hint})
        elapsed_ms = (time.perf_counter() - started) * 1000
        days = conn.execute("SELECT count(*) AS n FROM daily_rentals").fetchone()["n"]
    return {"statement": statement, "elapsed_ms": round(elapsed_ms, 1), "days": days}
