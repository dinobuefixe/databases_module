from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, ForeignKey, Numeric, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Account(Base):
    """Session 08's account table. Created by scripts/init_db.py."""

    __tablename__ = "account"
    # The rule lives in the database: even a buggy endpoint cannot go below zero.
    __table_args__ = (CheckConstraint("balance >= 0", name="account_balance_not_negative"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=False)
    balance: Mapped[Decimal] = mapped_column(Numeric(10, 2))


# Pagila tables, only the columns used.
class Inventory(Base):
    __tablename__ = "inventory"

    inventory_id: Mapped[int] = mapped_column(primary_key=True)
    film_id: Mapped[int]


class Rental(Base):
    __tablename__ = "rental"

    rental_id: Mapped[int] = mapped_column(primary_key=True)
    # Pagila has no default for rental_date; the ORM sends now() in the INSERT.
    rental_date: Mapped[datetime] = mapped_column(default=func.now())
    inventory_id: Mapped[int] = mapped_column(ForeignKey("inventory.inventory_id"))
    customer_id: Mapped[int]
    staff_id: Mapped[int]
