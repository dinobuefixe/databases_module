"""One open rental per inventory copy.

Revision ID: 0003
Revises: 0002
Create Date: 2026-11-12

Three copies (inventory 1358, 1435 and 2408) have two open rentals each: an
old one from 2022 that was never returned, and a newer one from 2026. The data
fix closes the older one by setting its ``return_date`` to the ``rental_date``
of the newer one. Then a partial unique index prevents new duplicates.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

COPIES = (1358, 1435, 2408)


def upgrade() -> None:
    op.execute(
        """
        WITH open_rentals AS (
            SELECT rental_id,
                   inventory_id,
                   rental_date,
                   row_number() OVER (
                       PARTITION BY inventory_id
                       ORDER BY rental_date DESC, rental_id DESC
                   ) AS rn
            FROM rental
            WHERE inventory_id IN (1358, 1435, 2408)
              AND return_date IS NULL
        )
        UPDATE rental AS r
        SET return_date = newer.rental_date
        FROM open_rentals AS older
        JOIN open_rentals AS newer
          ON newer.inventory_id = older.inventory_id
         AND newer.rn = 1
        WHERE older.rn = 2
          AND r.rental_id = older.rental_id
        """
    )

    op.create_index(
        "rental_one_open_per_copy",
        "rental",
        ["inventory_id"],
        unique=True,
        postgresql_where=sa.text("return_date IS NULL"),
    )


def downgrade() -> None:
    # Only the index is removed. The data fix is deliberately not undone: the
    # two 2022 rentals really are returned, and re-opening them would recreate
    # the duplicates the index was added to prevent.
    op.drop_index("rental_one_open_per_copy", table_name="rental")
