# Written by hand. The customer table already exists in Pagila, so this migration
# only tells Django's migration state about it and runs no SQL. Reversing it
# (migrate demo zero) is therefore harmless: it does not drop the table.

from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.CreateModel(
                    name="Customer",
                    fields=[
                        ("customer_id", models.AutoField(primary_key=True, serialize=False)),
                        ("store_id", models.IntegerField()),
                        ("first_name", models.TextField()),
                        ("last_name", models.TextField()),
                        ("email", models.TextField(null=True)),
                        ("active", models.IntegerField(null=True)),
                    ],
                    options={"db_table": "customer"},
                ),
            ],
            database_operations=[],
        ),
    ]
