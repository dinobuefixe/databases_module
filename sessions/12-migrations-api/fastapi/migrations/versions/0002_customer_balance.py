"""add customer.balance

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-07

A NOT NULL column on a table with 999 rows works in one step because it has a
server default: PostgreSQL fills the existing rows with 0.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: Union[str, Sequence[str], None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "customer",
        sa.Column("balance", sa.Numeric(10, 2), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("customer", "balance")
