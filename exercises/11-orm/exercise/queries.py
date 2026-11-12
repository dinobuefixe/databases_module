"""The 3 queries of task 2, written with the ORM and compared with handwritten SQL.

Run with:
    uv run python queries.py

``echo=True`` logs every SQL statement, so the generated SQL can be compared
with the handwritten version below each query.
"""

from __future__ import annotations

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from models import Actor, Category, Film, make_engine

engine = make_engine(echo=True)

HAND_Q1 = text(
    """
    SELECT c.name, count(*) AS films
    FROM category c JOIN film_category fc ON fc.category_id = c.category_id
    GROUP BY c.category_id, c.name
    ORDER BY films DESC, c.name
    """
)

HAND_Q2 = text(
    """
    SELECT f.film_id, f.title, f.length
    FROM film f
    WHERE f.length > (SELECT avg(length) FROM film)
    ORDER BY f.length DESC, f.film_id
    """
)

HAND_Q3 = text(
    """
    SELECT a.actor_id, a.first_name, a.last_name, count(*) AS films
    FROM actor a JOIN film_actor fa ON fa.actor_id = a.actor_id
    GROUP BY a.actor_id
    ORDER BY films DESC, a.actor_id
    LIMIT 10
    """
)


def q1_orm():
    """Number of films per category, most films first."""
    return (
        select(Category.name, func.count(Film.film_id).label("films"))
        .join(Category.films)
        .group_by(Category.category_id, Category.name)
        .order_by(func.count(Film.film_id).desc(), Category.name)
    )


def q2_orm():
    """Films longer than the average film."""
    avg_length = select(func.avg(Film.length)).scalar_subquery()
    return (
        select(Film.film_id, Film.title, Film.length)
        .where(Film.length > avg_length)
        .order_by(Film.length.desc(), Film.film_id)
    )


def q3_orm():
    """The 10 actors with most films."""
    return (
        select(
            Actor.actor_id,
            Actor.first_name,
            Actor.last_name,
            func.count(Film.film_id).label("films"),
        )
        .join(Actor.films)
        .group_by(Actor.actor_id)
        .order_by(func.count(Film.film_id).desc(), Actor.actor_id)
        .limit(10)
    )


def compare(name: str, orm_stmt, hand_sql, session: Session) -> None:
    orm_rows = session.execute(orm_stmt).all()
    hand_rows = session.execute(hand_sql).all()
    same = orm_rows == hand_rows
    print(f"\n{name}: {len(orm_rows)} rows, same as handwritten SQL: {same}")
    print("  first 5 ORM rows:")
    for row in orm_rows[:5]:
        print("   ", tuple(row))
    assert same, f"{name}: ORM and handwritten SQL differ"


def main() -> None:
    with Session(engine) as session:
        compare("Q1 films per category", q1_orm(), HAND_Q1, session)
        compare("Q2 films longer than average", q2_orm(), HAND_Q2, session)
        compare("Q3 top 10 actors", q3_orm(), HAND_Q3, session)


if __name__ == "__main__":
    main()
