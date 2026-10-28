from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import connection

from demo.models import Account
from demo.withdraw import STRATEGIES


class Command(BaseCommand):
    help = "Demo 1: N concurrent withdrawals of 10 from a balance of 100, for each strategy."

    def add_arguments(self, parser):
        parser.add_argument("--requests", type=int, default=50)
        parser.add_argument("--workers", type=int, default=20)
        parser.add_argument("--strategy", choices=[*STRATEGIES, "all"], default="all")

    def handle(self, *args, requests, workers, strategy, **options):
        amount, start_balance = Decimal("10"), Decimal("100")
        expected = min(requests, int(start_balance // amount))
        self.stdout.write(f"{requests} withdrawals of {amount} from {start_balance}, {workers} at a time.")
        self.stdout.write(f"The rule: exactly {expected} succeed and the balance ends at {start_balance - expected * amount}.\n")

        failed = []
        for name, fn in STRATEGIES.items():
            if strategy not in (name, "all"):
                continue
            Account.objects.update_or_create(id=1, defaults={"balance": start_balance})

            def one(_):
                try:
                    return fn(1, amount)
                finally:
                    connection.close()  # each thread has its own connection; give it back

            with ThreadPoolExecutor(max_workers=workers) as pool:
                succeeded = sum(pool.map(one, range(requests)))

            balance = Account.objects.get(pk=1).balance
            # Money taken out according to the successes, against what the balance says.
            holds = succeeded == expected and balance == start_balance - succeeded * amount
            line = f"{name:<7} succeeded={succeeded:<3} final balance={balance:<7} "
            if holds:
                self.stdout.write(self.style.SUCCESS(line + "rule holds"))
            else:
                lost = succeeded * amount - (start_balance - balance)
                self.stdout.write(self.style.ERROR(line + f"rule broken: {lost} withdrawn but not deducted"))
                failed.append(name)

        if strategy != "all" and failed:
            raise CommandError(f"{failed[0]} broke the rule", returncode=1)
