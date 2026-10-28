from decimal import Decimal

from django.core.management.base import BaseCommand

from demo.models import Account


class Command(BaseCommand):
    help = "Creates the account or sets its balance (default: account 1 with 100)."

    def add_arguments(self, parser):
        parser.add_argument("--id", type=int, default=1)
        parser.add_argument("--balance", type=Decimal, default=Decimal("100"))

    def handle(self, *args, id, balance, **options):
        Account.objects.update_or_create(id=id, defaults={"balance": balance})
        self.stdout.write(self.style.SUCCESS(f"account {id}: balance {balance}"))
