"""SQLAlchemy models for the Pagila tables used by the session 12 exercise.

Only the columns the exercise needs are mapped. ``migrations/env.py`` restricts
autogenerate to these tables (and their columns), so the rest of Pagila is left
alone.
"""

from __future__ import annotations

import os
from datetime import date, datetime

from sqlalchemy import ForeignKey, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+psycopg://postgres:change-me-postgres@localhost:5432/ex12",
)


class Base(DeclarativeBase):
    pass


class Customer(Base):
    __tablename__ = "customer"

    customer_id: Mapped[int] = mapped_column(primary_key=True)
    store_id: Mapped[int]
    first_name: Mapped[str]
    last_name: Mapped[str]
    email: Mapped[str | None]
    address_id: Mapped[int]
    activebool: Mapped[bool]
    create_date: Mapped[date]
    last_update: Mapped[datetime | None]
    active: Mapped[int | None]
    loyalty_points: Mapped[int] = mapped_column(server_default="0")

    rentals: Mapped[list["Rental"]] = relationship(back_populates="customer")


class Film(Base):
    __tablename__ = "film"

    film_id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    description: Mapped[str | None]
    language_id: Mapped[int]
    rental_duration: Mapped[int]
    rental_rate: Mapped[float]
    length: Mapped[int | None]
    replacement_cost: Mapped[float]

    inventories: Mapped[list["Inventory"]] = relationship(back_populates="film")


class Inventory(Base):
    __tablename__ = "inventory"

    inventory_id: Mapped[int] = mapped_column(primary_key=True)
    film_id: Mapped[int] = mapped_column(ForeignKey("film.film_id"))
    store_id: Mapped[int]

    film: Mapped[Film] = relationship(back_populates="inventories")
    rentals: Mapped[list["Rental"]] = relationship(back_populates="inventory")


class Rental(Base):
    __tablename__ = "rental"

    rental_id: Mapped[int] = mapped_column(primary_key=True)
    rental_date: Mapped[datetime]
    inventory_id: Mapped[int] = mapped_column(ForeignKey("inventory.inventory_id"))
    customer_id: Mapped[int] = mapped_column(ForeignKey("customer.customer_id"))
    return_date: Mapped[datetime | None]
    staff_id: Mapped[int] = mapped_column(ForeignKey("staff.staff_id"))

    inventory: Mapped[Inventory] = relationship(back_populates="rentals")
    customer: Mapped[Customer] = relationship(back_populates="rentals")
    staff: Mapped["Staff"] = relationship(back_populates="rentals")


class Staff(Base):
    __tablename__ = "staff"

    staff_id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str]
    last_name: Mapped[str]
    address_id: Mapped[int]
    email: Mapped[str | None]
    store_id: Mapped[int]
    active: Mapped[bool]
    username: Mapped[str]

    rentals: Mapped[list[Rental]] = relationship(back_populates="staff")


def make_engine(echo: bool = False):
    return create_engine(DATABASE_URL, echo=echo)
