"""Add customer.loyalty_points.

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-12

Three steps so the migration works on a table with rows:

1. add the column as nullable;
2. fill it with the number of rentals of each customer;
3. make it NOT NULL and give new rows a server default of 0.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "customer",
        sa.Column("loyalty_points", sa.Integer(), nullable=True),
    )

    op.execute(
        """
        UPDATE customer AS c
        SET loyalty_points = (
            SELECT count(*) FROM rental AS r WHERE r.customer_id = c.customer_id
        )
        """
    )

    op.alter_column(
        "customer",
        "loyalty_points",
        existing_type=sa.Integer(),
        nullable=False,
        server_default=sa.text("0"),
    )


def downgrade() -> None:
    op.drop_column("customer", "loyalty_points")
