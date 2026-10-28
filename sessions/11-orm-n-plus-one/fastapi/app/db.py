import os
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar

from dotenv import load_dotenv
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

load_dotenv()

# echo=True logs every statement SQLAlchemy sends, with its parameters.
# Keep it on while developing; it is how you notice an N+1.
engine = create_engine(
    os.environ["DATABASE_URL"],
    echo=os.getenv("SQL_ECHO", "true").lower() == "true",
)
SessionLocal = sessionmaker(engine)


def get_session() -> Iterator[Session]:
    """FastAPI dependency: one session per request, closed at the end."""
    with SessionLocal() as session:
        yield session


# Query counter. A ContextVar keeps one counter per request, even when several
# requests run at the same time in different threads.
_counter: ContextVar[list[str] | None] = ContextVar("sql_counter", default=None)


@event.listens_for(engine, "before_cursor_execute")
def _count(conn, cursor, statement, parameters, context, executemany):
    statements = _counter.get()
    if statements is not None:
        statements.append(statement)


@contextmanager
def count_queries() -> Iterator[list[str]]:
    """Collects every SQL statement run inside the block. len() gives the count."""
    statements: list[str] = []
    token = _counter.set(statements)
    try:
        yield statements
    finally:
        _counter.reset(token)
