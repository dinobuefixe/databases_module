# Written by hand: Django has no operation for materialised views, so the
# tutorial's SQL goes in RunSQL, with the reverse SQL so `migrate demo 0001` undoes it.

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("demo", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                CREATE MATERIALIZED VIEW daily_rentals AS
                SELECT rental_date::date AS day, count(*) AS rentals
                FROM rental
                GROUP BY 1;

                -- REFRESH ... CONCURRENTLY needs a unique index on the view.
                CREATE UNIQUE INDEX daily_rentals_day ON daily_rentals (day);
            """,
            reverse_sql="DROP MATERIALIZED VIEW daily_rentals;",
        ),
    ]
