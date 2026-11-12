"""Session 09 exercise API: write to PostgreSQL, MongoDB and Redis safely.

Each endpoint writes to one engine using the least-privilege users created for
this exercise. Credentials come only from environment variables; no query is
ever built by concatenating user input.

Run with:
    uv run uvicorn app.main:app --port 8000
"""

from __future__ import annotations

import os
import re

import psycopg
import redis
from fastapi import FastAPI, HTTPException
from pymongo import MongoClient
from pydantic import BaseModel, Field

PG_DSN = os.environ["EX09_PG_DSN"]
MONGO_URL = os.environ["EX09_MONGO_URL"]
REDIS_URL = os.environ["EX09_REDIS_URL"]

mongo = MongoClient(MONGO_URL)
db = mongo.get_default_database()
notes = db["notes"]

r = redis.Redis.from_url(REDIS_URL, decode_responses=True)

NAME_RE = re.compile(r"^[a-z0-9_-]{1,32}$")

app = FastAPI(title="ex09 security API")


class ActorIn(BaseModel):
    first_name: str
    last_name: str


class NoteIn(BaseModel):
    customer_id: int
    text: str


@app.get("/")
def root() -> dict:
    return {"ok": True}


@app.post("/actors", status_code=201)
def create_actor(body: ActorIn) -> dict:
    """Insert a row into actor with a parameterised query.

    The text is sent as a value, never as SQL, so an injection attempt is stored
    literally and changes nothing else.
    """
    with psycopg.connect(PG_DSN) as conn:
        row = conn.execute(
            "INSERT INTO actor (first_name, last_name) VALUES (%s, %s) "
            "RETURNING actor_id",
            (body.first_name, body.last_name),
        ).fetchone()
    return {"actor_id": row[0]}


@app.post("/notes", status_code=201)
def create_note(body: NoteIn) -> dict:
    """Insert a document into ex09.notes.

    Pydantic validates the body before this code runs: ``customer_id`` must be
    an integer and ``text`` a string, so a MongoDB operator object such as
    ``{"$ne": null}`` is rejected with 422.
    """
    result = notes.insert_one({"customer_id": body.customer_id, "text": body.text})
    return {"inserted_id": str(result.inserted_id)}


@app.post("/counters/{name}")
def increment_counter(name: str) -> dict:
    """Run INCR counter:{name} for a validated name."""
    if not NAME_RE.match(name):
        raise HTTPException(
            status_code=422,
            detail="name must match ^[a-z0-9_-]{1,32}$",
        )
    value = r.incr(f"counter:{name}")
    return {"name": name, "value": value}
