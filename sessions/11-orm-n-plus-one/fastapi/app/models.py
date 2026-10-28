from datetime import datetime

from sqlalchemy import ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


# Only the columns the tutorial needs. Pagila has more; SQLAlchemy ignores
# columns that are not mapped.
class Customer(Base):
    __tablename__ = "customer"

    customer_id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str]
    last_name: Mapped[str]
    # 1:N. Lazy by default: the rentals are loaded the first time you touch them.
    rentals: Mapped[list["Rental"]] = relationship(back_populates="customer")


class Rental(Base):
    __tablename__ = "rental"

    rental_id: Mapped[int] = mapped_column(primary_key=True)
    rental_date: Mapped[datetime]
    return_date: Mapped[datetime | None]
    customer_id: Mapped[int] = mapped_column(ForeignKey("customer.customer_id"))
    # N:1. Each rental belongs to one customer.
    customer: Mapped[Customer] = relationship(back_populates="rentals")
