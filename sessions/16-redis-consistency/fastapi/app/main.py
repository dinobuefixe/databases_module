from typing import Literal

from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel, Field

from app.clients import pg_readonly, r
from app.films_sets import films_key, verify
from app.usernames import change_username_lua, change_username_watch

app = FastAPI(title="Session 16: Redis source of truth, rebuild and persistence")

PERSISTENCE_SETTINGS = ["appendonly", "appendfsync", "save", "maxmemory", "maxmemory-policy"]


@app.get("/verify")
def verify_sets(response: Response):
    """The verification script as an endpoint: 200 when Redis agrees with PostgreSQL, 409 when not."""
    with pg_readonly() as pg:
        mismatches = verify(pg)
    if mismatches:
        response.status_code = 409
    return {"ok": not mismatches, "mismatches": len(mismatches), "first": mismatches[:10]}


@app.get("/customers/{customer_id}/films")
def customer_films(customer_id: int):
    film_ids = sorted(int(f) for f in r.smembers(films_key(customer_id)))
    return {"customer_id": customer_id, "count": len(film_ids), "film_ids": film_ids}


@app.get("/redis/persistence")
def persistence():
    """Reads the server's persistence and memory settings. CONFIG GET only reads; this app never uses CONFIG SET."""
    settings = {}
    for name in PERSISTENCE_SETTINGS:
        settings.update(r.config_get(name))
    return settings


class UsernameChange(BaseModel):
    username: str = Field(min_length=3, max_length=50, pattern=r"^[a-z0-9._]+$")
    method: Literal["watch", "lua"] = "watch"


@app.put("/customers/{customer_id}/username")
def change_username(customer_id: int, body: UsernameChange):
    # Only to give a clear error. The old name used for the change is read again
    # inside the WATCH transaction or the Lua script.
    if not r.hexists(f"customer:{customer_id}", "username"):
        raise HTTPException(404, "No username for this customer. Run: uv run python -m scripts.seed_usernames")

    change = change_username_watch if body.method == "watch" else change_username_lua
    if not change(customer_id, body.username):
        raise HTTPException(409, f"Username {body.username} is already taken")
    return {"customer_id": customer_id, "username": body.username, "method": body.method}
