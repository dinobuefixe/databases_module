"""SQLAlchemy 2.0 models for the 6 Pagila tables of the exercise.

film, language, actor, film_actor, category, film_category.

Film has language, actors and categories; Actor and Category have films.
"""

from __future__ import annotations

import os

from sqlalchemy import Column, ForeignKey, Table, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql+psycopg://postgres:change-me-postgres@localhost:5432/ex11"
)


class Base(DeclarativeBase):
    pass


# Association tables for the two many-to-many relationships.
film_actor = Table(
    "film_actor",
    Base.metadata,
    Column("actor_id", ForeignKey("actor.actor_id"), primary_key=True),
    Column("film_id", ForeignKey("film.film_id"), primary_key=True),
)

film_category = Table(
    "film_category",
    Base.metadata,
    Column("film_id", ForeignKey("film.film_id"), primary_key=True),
    Column("category_id", ForeignKey("category.category_id"), primary_key=True),
)


class Language(Base):
    __tablename__ = "language"

    language_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]

    films: Mapped[list["Film"]] = relationship(back_populates="language")


class Actor(Base):
    __tablename__ = "actor"

    actor_id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str]
    last_name: Mapped[str]

    films: Mapped[list["Film"]] = relationship(
        secondary=film_actor, back_populates="actors"
    )


class Category(Base):
    __tablename__ = "category"

    category_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]

    films: Mapped[list["Film"]] = relationship(
        secondary=film_category, back_populates="categories"
    )


class Film(Base):
    __tablename__ = "film"

    film_id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    length: Mapped[int | None]
    language_id: Mapped[int] = mapped_column(ForeignKey("language.language_id"))

    language: Mapped[Language] = relationship(back_populates="films")
    actors: Mapped[list[Actor]] = relationship(
        secondary=film_actor, back_populates="films"
    )
    categories: Mapped[list[Category]] = relationship(
        secondary=film_category, back_populates="films"
    )


def make_engine(echo: bool = False):
    return create_engine(DATABASE_URL, echo=echo)
