"""Creates the account table (if missing), seeds account 1, and fills Redis from PostgreSQL.

Run with: uv run python -m scripts.init_db
"""

from decimal import Decimal

from app.db import SessionLocal, engine
from app.films_sets import rebuild_all
from app.models import Account, Base

# Only our own table. The Pagila tables already exist and must not be touched.
Base.metadata.create_all(engine, tables=[Account.__table__])

with SessionLocal.begin() as session:
    if session.get(Account, 1) is None:
        session.add(Account(id=1, balance=Decimal("100")))
    print("account table ready")
    print("redis sets rebuilt for", rebuild_all(session), "customers")
