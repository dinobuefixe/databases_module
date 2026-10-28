# Data migration, step 2 of 3: fill tier for the rows that already exist.
# Created with `makemigrations --empty` and edited by hand.

from django.db import migrations
from django.db.models import Case, Value, When


def fill_tier(apps, schema_editor):
    # apps.get_model returns the model as it was at this point in the history,
    # not the current class in models.py.
    Customer = apps.get_model("demo", "Customer")
    # One UPDATE ... SET tier = CASE WHEN active = 1 THEN 'standard' ELSE 'inactive' END
    Customer.objects.update(
        tier=Case(When(active=1, then=Value("standard")), default=Value("inactive"))
    )


class Migration(migrations.Migration):
    dependencies = [
        ("demo", "0003_customer_tier_nullable"),
    ]

    operations = [
        # Going back, there is nothing to undo: 0003's reverse drops the column.
        migrations.RunPython(fill_tier, reverse_code=migrations.RunPython.noop),
    ]
