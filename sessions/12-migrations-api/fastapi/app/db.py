import os
from collections.abc import Iterator

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

load_dotenv()

# The engine keeps a pool of connections (5 by default, plus up to 10 extra
# under load) and lends one to each session.
engine = create_engine(os.environ["DATABASE_URL"], pool_size=5, max_overflow=10)
SessionLocal = sessionmaker(engine)


def get_session() -> Iterator[Session]:
    """FastAPI dependency: one session per request, closed when the request ends."""
    with SessionLocal() as session:
        yield session
