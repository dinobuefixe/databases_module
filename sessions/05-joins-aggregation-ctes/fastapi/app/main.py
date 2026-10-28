from pathlib import Path

from fastapi import FastAPI, Query

from app.db import pg_connect

app = FastAPI(title="Session 05: joins, aggregation and CTEs")

SQL_DIR = Path(__file__).resolve().parent.parent / "sql"


def run(name: str, params: dict | None = None) -> dict:
    """Run sql/<name>.sql and return the SQL text with the rows, so you can read both."""
    query = (SQL_DIR / f"{name}.sql").read_text()
    with pg_connect() as conn:
        rows = conn.execute(query, params).fetchall()
    return {"sql": query, "row_count": len(rows), "rows": rows}


@app.get("/questions/rentals-per-staff")
def rentals_per_staff():
    return run("rentals_per_staff")


@app.get("/questions/customers-over-40")
def customers_over_40(min_rentals: int = Query(40, ge=0)):
    return run("customers_over_40", {"min_rentals": min_rentals})


@app.get("/questions/rentals-per-customer")
def rentals_per_customer():
    return run("rentals_per_customer")


@app.get("/questions/films-without-inventory")
def films_without_inventory():
    return run("films_without_inventory")


@app.get("/questions/customers-without-rentals")
def customers_without_rentals():
    return run("customers_without_rentals")


@app.get("/questions/duplicate-customer-names")
def duplicate_customer_names():
    return run("duplicate_customer_names")


@app.get("/questions/films-longer-than-average")
def films_longer_than_average():
    return run("films_longer_than_average")


@app.get("/questions/films-above-rating-average")
def films_above_rating_average():
    return run("films_above_rating_average")


@app.get("/questions/customer-totals")
def customer_totals():
    return run("customer_totals")


@app.get("/questions/customers-above-average")
def customers_above_average():
    return run("customers_above_average")
