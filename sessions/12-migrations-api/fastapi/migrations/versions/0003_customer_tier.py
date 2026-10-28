"""add customer.tier in three steps

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-07

autogenerate wrote a single add_column(..., nullable=False), which fails on a
table that already has rows. Edited by hand into: add as nullable, fill it
from `active` (a data migration), then set NOT NULL.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: Union[str, Sequence[str], None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("customer", sa.Column("tier", sa.Text(), nullable=True))
    op.execute("UPDATE customer SET tier = CASE WHEN active = 1 THEN 'standard' ELSE 'inactive' END")
    op.alter_column("customer", "tier", nullable=False)


def downgrade() -> None:
    op.drop_column("customer", "tier")
