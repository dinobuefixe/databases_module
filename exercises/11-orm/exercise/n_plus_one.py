"""Task 3 - create an N+1 on purpose, then fix it with eager loading.

Run with:
    uv run python n_plus_one.py

Loads the first 100 films by ``film_id`` and prints each title with its actors
through ``film.actors``. The first block lets the relationship load lazily (one
query per film); the second block uses ``selectinload`` and runs 2 queries.
"""

from __future__ import annotations

from sqlalchemy import event, select
from sqlalchemy.orm import Session, selectinload

from models import Film, make_engine

engine = make_engine(echo=False)


class SelectCounter:
    """Count SELECT statements sent to the database."""

    def __init__(self) -> None:
        self.count = 0

    def __call__(self, conn, cursor, statement, parameters, context, executemany):
        if statement.lstrip().upper().startswith("SELECT"):
            self.count += 1


def run(n_plus_one: bool) -> int:
    counter = SelectCounter()
    event.listen(engine, "before_cursor_execute", counter)
    try:
        with Session(engine) as session:
            stmt = select(Film).order_by(Film.film_id).limit(100)
            if not n_plus_one:
                stmt = stmt.options(selectinload(Film.actors))
            films = session.scalars(stmt).all()
            for film in films:
                names = ", ".join(a.first_name for a in film.actors)
                print(f"{film.film_id:4d} {film.title:<30} {names}")
    finally:
        event.remove(engine, "before_cursor_execute", counter)
    return counter.count


def main() -> None:
    print("=" * 70)
    print("N+1 version: lazy relationship, one query per film")
    print("=" * 70)
    n_plus_one = run(n_plus_one=True)

    print()
    print("=" * 70)
    print("Fixed version: selectinload(Film.actors), two queries in total")
    print("=" * 70)
    eager = run(n_plus_one=False)

    print()
    print(f"N+1  : {n_plus_one} SELECT statements")
    print(f"fixed: {eager} SELECT statements")


if __name__ == "__main__":
    main()
