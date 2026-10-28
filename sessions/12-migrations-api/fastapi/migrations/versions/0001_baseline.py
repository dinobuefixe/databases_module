"""baseline: the Pagila schema as it already exists

Revision ID: 0001
Revises:
Create Date: 2026-10-07

Pagila was created by its own SQL scripts, before Alembic. This revision marks
that starting point. `alembic revision --autogenerate` against a fresh copy of
Pagila, with the models as they were before 0002, produces exactly this: nothing
to do, because the mapped table and columns already exist.

On a database that already has the schema you can also run `alembic stamp 0001`
to record the baseline without running anything.
"""
from typing import Sequence, Union

revision: str = "0001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
