"""Gives every customer a username in Redis, for the WATCH and Lua examples.

Run with: uv run python -m scripts.seed_usernames

Pagila has no usernames, so this uses the part of the email before the @, in
lower case (mary.smith). It replaces the `usernames` set and every customer:{id} hash.
"""

from app.clients import pg_readonly, r

with pg_readonly() as pg:
    rows = pg.execute("SELECT customer_id, lower(split_part(email, '@', 1)) FROM customer").fetchall()

pipe = r.pipeline(transaction=True)
pipe.delete("usernames")
for customer_id, username in rows:
    pipe.sadd("usernames", username)
    pipe.hset(f"customer:{customer_id}", "username", username)
pipe.execute()
print(f"{r.scard('usernames')} usernames for {len(rows)} customers")
