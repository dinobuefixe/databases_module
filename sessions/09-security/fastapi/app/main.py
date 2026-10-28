from argon2 import PasswordHasher
from argon2.exceptions import VerificationError
from fastapi import Body, FastAPI, HTTPException
from pydantic import BaseModel

from app.clients import mongo_db, pg_connect, pg_readonly, r

app = FastAPI(title="Session 09: security")

hasher = PasswordHasher()


@app.get("/whoami")
def whoami():
    """Which account the application uses on each engine."""
    with pg_connect() as conn:
        pg_user = conn.execute("SELECT current_user AS u").fetchone()["u"]
    with pg_readonly() as conn:
        pg_reports = conn.execute("SELECT current_user AS u").fetchone()["u"]
    mongo_user = mongo_db.command("connectionStatus")["authInfo"]["authenticatedUsers"]
    return {"postgres": pg_user, "postgres_reports": pg_reports, "mongo": mongo_user, "redis": r.acl_whoami()}


# --- SQL injection --------------------------------------------------------------------------

@app.get("/customers/search-unsafe")
def search_customers_unsafe(email: str):
    """UNSAFE, local demo only. The input is pasted into the SQL text and becomes code."""
    query = f"SELECT customer_id, first_name, last_name, email FROM customer WHERE email = '{email}'"
    with pg_connect() as conn:
        rows = conn.execute(query).fetchall()
    return {"sql": query, "row_count": len(rows), "rows": rows[:5]}


@app.get("/customers/search")
def search_customers(email: str):
    """Safe. The SQL text and the value travel separately; the value is never parsed as SQL."""
    query = "SELECT customer_id, first_name, last_name, email FROM customer WHERE email = %s"
    with pg_connect() as conn:
        rows = conn.execute(query, (email,)).fetchall()
    return {"sql": query, "params": [email], "row_count": len(rows), "rows": rows[:5]}


@app.get("/reports/customers-per-store")
def customers_per_store():
    """A report through the readonly role: it can SELECT and nothing else."""
    with pg_readonly() as conn:
        return conn.execute(
            "SELECT store_id, count(*) AS customers FROM customer GROUP BY store_id ORDER BY store_id"
        ).fetchall()


# --- NoSQL injection ------------------------------------------------------------------------

@app.post("/login-unsafe")
def login_unsafe(body: dict = Body(...)):
    """UNSAFE, local demo only. The filter is built from the raw JSON body.

    {"username": "admin", "password": {"$ne": null}} turns the password check into
    "password is not null", which matches. It reads legacy_users, which stores plain-text
    passwords as old code often did: a second mistake.
    """
    user = mongo_db.legacy_users.find_one({"username": body.get("username"), "password": body.get("password")})
    if user is None:
        raise HTTPException(401, "invalid credentials")
    return {"logged_in_as": user["username"]}


class Credentials(BaseModel):
    # Pydantic rejects anything that is not a string, so {"$ne": null} never reaches MongoDB.
    username: str
    password: str


@app.post("/login")
def login(body: Credentials):
    """Safe. Typed input, a lookup by username only, then an argon2 hash check in Python."""
    user = mongo_db.users.find_one({"username": body.username})
    try:
        if user is None:
            raise VerificationError()
        hasher.verify(user["password_hash"], body.password)
    except VerificationError:
        # The same answer for an unknown user and a wrong password.
        raise HTTPException(401, "invalid credentials")
    return {"logged_in_as": user["username"]}
