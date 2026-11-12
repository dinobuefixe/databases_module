"""Baseline: the existing Pagila schema.

Revision ID: 0001
Revises:
Create Date: 2026-11-12

This migration does nothing on purpose. Pagila already exists in ``ex12`` and
is not created by Alembic. The baseline gives Alembic a starting point, and
``alembic stamp head`` records it in ``alembic_version`` without running DDL.
"""

from __future__ import annotations

from collections.abc import Sequence

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
