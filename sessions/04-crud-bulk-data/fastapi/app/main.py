from contextlib import asynccontextmanager
from decimal import Decimal
from typing import Literal

import psycopg
from fastapi import FastAPI, HTTPException, Query
from psycopg import sql
from pydantic import BaseModel, Field

from app.db import create_tables, pg_connect


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    yield


app = FastAPI(title="Session 04: CRUD, upsert and bulk data", lifespan=lifespan)

Rating = Literal["G", "PG", "PG-13", "R", "NC-17"]


@app.get("/films")
def list_films(
    rating: Rating | None = None,
    q: str | None = Query(None, description="part of the title, case-insensitive"),
    sort: Literal["title", "length", "rental_rate", "release_year"] = "title",
    order: Literal["asc", "desc"] = "asc",
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """SELECT with optional filters, ORDER BY, LIMIT and OFFSET."""
    where = []
    params: list = []
    if rating:
        where.append(sql.SQL("rating = %s::mpaa_rating"))
        params.append(rating)
    if q:
        where.append(sql.SQL("title ILIKE %s"))
        params.append(f"%{q}%")

    # Values travel as parameters (%s). Column names cannot be parameters, so the sort
    # column comes from a fixed list (the Literal above) and is quoted with sql.Identifier.
    query = sql.SQL(
        "SELECT film_id, title, length, rating, rental_rate, release_year FROM film {where} "
        "ORDER BY {col} {dir}, film_id LIMIT %s OFFSET %s"
    ).format(
        where=sql.SQL("WHERE ") + sql.SQL(" AND ").join(where) if where else sql.SQL(""),
        col=sql.Identifier(sort),
        dir=sql.SQL(order.upper()),
    )
    with pg_connect() as conn:
        return conn.execute(query, [*params, limit, offset]).fetchall()


class NewActor(BaseModel):
    first_name: str = Field(min_length=1)
    last_name: str = Field(min_length=1)


@app.post("/actors", status_code=201)
def create_actor(body: NewActor):
    """INSERT ... RETURNING gives back the generated key without a second query."""
    with pg_connect() as conn:
        return conn.execute(
            "INSERT INTO actor (first_name, last_name) VALUES (%s, %s) RETURNING actor_id, last_update",
            (body.first_name.upper(), body.last_name.upper()),
        ).fetchone()


class RateChange(BaseModel):
    rating: Rating
    below: Decimal = Field(description="change films whose rental_rate is below this value")
    new_rate: Decimal = Field(gt=0, max_digits=4, decimal_places=2)
    expected: int = Field(ge=0, description="the number of rows you expect to change")
    dry_run: bool = False


class CountMismatch(Exception):
    pass


@app.post("/films/rental-rate")
def change_rental_rate(body: RateChange):
    """A safe UPDATE: count first, update in a transaction, roll back if the count is wrong."""
    with pg_connect() as conn:
        try:
            with conn.transaction():
                matching = conn.execute(
                    "SELECT count(*) AS n FROM film WHERE rating = %s::mpaa_rating AND rental_rate < %s",
                    (body.rating, body.below),
                ).fetchone()["n"]
                if matching != body.expected:
                    raise CountMismatch(f"expected {body.expected} rows, the WHERE matches {matching}")

                changed = conn.execute(
                    """
                    UPDATE film SET rental_rate = %s
                    WHERE rating = %s::mpaa_rating AND rental_rate < %s
                    RETURNING film_id, title, rental_rate
                    """,
                    (body.new_rate, body.rating, body.below),
                ).fetchall()
                # Checked again: another session may have changed rows between the two statements.
                if len(changed) != body.expected:
                    raise CountMismatch(f"expected {body.expected} rows, the UPDATE changed {len(changed)}")

                if body.dry_run:
                    raise psycopg.Rollback()
                return {"committed": True, "changed": len(changed), "rows": changed}
        except CountMismatch as exc:
            # The exception left the transaction block, so psycopg has already rolled it back.
            raise HTTPException(409, f"rolled back: {exc}")
    return {"committed": False, "dry_run": True, "would_change": len(changed), "rows": changed}


@app.post("/films/{film_id}/views")
def add_view(film_id: int):
    """Upsert: insert the first view, or add one to the existing row, in one atomic statement."""
    try:
        with pg_connect() as conn:
            return conn.execute(
                """
                INSERT INTO film_views (film_id, views) VALUES (%s, 1)
                ON CONFLICT (film_id) DO UPDATE SET views = film_views.views + 1
                RETURNING *
                """,
                (film_id,),
            ).fetchone()
    except psycopg.errors.ForeignKeyViolation:
        raise HTTPException(404, "film not found")
