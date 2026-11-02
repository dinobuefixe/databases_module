from contextlib import asynccontextmanager
from datetime import UTC, datetime

from fastapi import FastAPI, Response
from psycopg.rows import dict_row
from pydantic import BaseModel, Field

from app.clients import create_tables, mongo_db, pg_connect, r


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    yield


app = FastAPI(title="Session 01: database engines", lifespan=lifespan)


class Message(BaseModel):
    msg: str = Field(min_length=1)


def check(fn) -> str:
    try:
        fn()
        return "ok"
    except Exception as exc:  # report any failure instead of crashing the health check
        return f"error: {exc}"


def ping_postgres() -> None:
    with pg_connect() as conn:
        conn.execute("SELECT 1")


@app.get("/health")
def health(response: Response):
    """One cheap command per engine."""
    result = {
        "postgres": check(ping_postgres),
        "mongo": check(lambda: mongo_db.command("ping")),
        "redis": check(r.ping),
    }
    if any(v != "ok" for v in result.values()):
        response.status_code = 503
    return result


@app.post("/hello", status_code=201)
def write_hello(body: Message):
    """Write the same message to each engine."""
    # PostgreSQL: a row in a table with a fixed structure.
    with pg_connect() as conn:
        conn.row_factory = dict_row
        row = conn.execute(
            "INSERT INTO hello (msg) VALUES (%s) RETURNING id, msg, created_at", (body.msg,)
        ).fetchone()

    # MongoDB: a document; the tags list needs no extra table.
    result = mongo_db.hello.insert_one(
        {"msg": body.msg, "tags": ["a", "b"], "created_at": datetime.now(UTC)}
    )

    # Redis: a key holding the last message and a counter.
    r.set("hello:last", body.msg)
    count = r.incr("hello:count")

    return {
        "postgres": row,
        "mongo": {"_id": str(result.inserted_id)},
        "redis": {"last": body.msg, "count": count},
    }


@app.get("/hello")
def read_hello():
    """Read back what each engine holds."""
    with pg_connect() as conn:
        conn.row_factory = dict_row
        rows = conn.execute("SELECT id, msg, created_at FROM hello ORDER BY id DESC LIMIT 5").fetchall()

    docs = [
        {**doc, "_id": str(doc["_id"])}
        for doc in mongo_db.hello.find().sort("_id", -1).limit(5)
    ]

    return {
        "postgres": rows,
        "mongo": docs,
        "redis": {"last": r.get("hello:last"), "count": int(r.get("hello:count") or 0)},
    }
