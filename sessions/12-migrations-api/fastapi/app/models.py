from decimal import Decimal

from sqlalchemy import Integer, Numeric, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Customer(Base):
    """Pagila's customer table, only the columns this API uses.

    The types match the database (text, not varchar) so that autogenerate
    finds nothing to change once the migrations are applied.
    """

    __tablename__ = "customer"

    customer_id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(Text)
    last_name: Mapped[str] = mapped_column(Text)
    email: Mapped[str | None] = mapped_column(Text)
    active: Mapped[int | None] = mapped_column(Integer)
    # Added by migration 0002.
    balance: Mapped[Decimal] = mapped_column(Numeric(10, 2), server_default="0")
    # Added by migration 0003, in three steps.
    tier: Mapped[str] = mapped_column(Text)
