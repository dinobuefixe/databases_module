from decimal import Decimal

from sqlalchemy import CheckConstraint, Numeric
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Account(Base):
    """Session 08's account table."""

    __tablename__ = "account"
    __table_args__ = (CheckConstraint("balance >= 0", name="account_balance_not_negative"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=False)
    balance: Mapped[Decimal] = mapped_column(Numeric(10, 2))
