"""The tutorial's indexes, declared with SQLAlchemy and compiled to PostgreSQL DDL.

The rest of the project runs plain SQL with psycopg. SQLAlchemy is used here only to declare
the indexes next to the columns they cover and to generate the CREATE/DROP statements.
All three can be declared this way: a sort direction, a partial index (postgresql_where)
and an expression index (func.lower). None of them needs hand-written SQL.
"""

from sqlalchemy import Column, DateTime, Index, Integer, MetaData, Table, Text, func
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateIndex, DropIndex

metadata = MetaData()

# Only the columns the indexes need. The tables themselves are created elsewhere.
big_rental = Table(
    "big_rental",
    metadata,
    Column("id", Integer),
    Column("customer_id", Integer),
    Column("rented_at", DateTime(timezone=True)),
    Column("returned_at", DateTime(timezone=True)),
)
customer = Table("customer", metadata, Column("customer_id", Integer), Column("email", Text))

INDEXES = {
    # Equality column first, sort column second, in the order the query sorts.
    "composite": Index("big_rental_customer_rented", big_rental.c.customer_id, big_rental.c.rented_at.desc()),
    # Only the ~3% of rows not yet returned are indexed.
    "partial": Index("big_rental_open", big_rental.c.rented_at, postgresql_where=big_rental.c.returned_at.is_(None)),
    # Lets WHERE lower(email) = ... use an index; a plain index on email would not.
    "expression": Index("customer_lower_email", func.lower(customer.c.email)),
    # A plain index on rented_at. recent_rentals uses it for a few days, not for two years.
    "single": Index("big_rental_rented", big_rental.c.rented_at),
}


def _compile(statement) -> str:
    return str(statement.compile(dialect=postgresql.dialect())).strip()


def create_sql(name: str) -> str:
    return _compile(CreateIndex(INDEXES[name], if_not_exists=True))


def drop_sql(name: str) -> str:
    return _compile(DropIndex(INDEXES[name], if_exists=True))
