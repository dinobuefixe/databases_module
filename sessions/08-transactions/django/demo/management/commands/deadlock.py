import threading
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import OperationalError, connection, transaction

from demo.models import Account


class Command(BaseCommand):
    help = "Two transfers lock accounts 1 and 2 in opposite order, then the fix with a fixed lock order."

    def transfer(self, source: int, target: int, barrier: threading.Barrier | None, ordered: bool, results: dict) -> None:
        name = f"{source}->{target}"
        try:
            with transaction.atomic():
                if ordered:
                    # The fix: lock both rows at once, always in ascending id order.
                    rows = {a.id: a for a in Account.objects.select_for_update().filter(id__in=[source, target]).order_by("id")}
                    src, dst = rows[source], rows[target]
                else:
                    src = Account.objects.select_for_update().get(pk=source)
                    barrier.wait()  # both transactions now hold their first lock
                    dst = Account.objects.select_for_update().get(pk=target)  # ...and wait for the other's
                src.balance -= Decimal(10)
                dst.balance += Decimal(10)
                src.save(update_fields=["balance"])
                dst.save(update_fields=["balance"])
            results[name] = "committed"
        except OperationalError as exc:
            pg = exc.__cause__
            results[name] = f"{type(pg).__name__}: {pg.diag.message_primary}\n    {pg.diag.message_detail.replace(chr(10), chr(10) + '    ')}"
        finally:
            connection.close()  # each thread has its own connection

    def run(self, ordered: bool) -> None:
        Account.objects.bulk_create(
            [Account(id=1, balance=100), Account(id=2, balance=100)],
            update_conflicts=True, unique_fields=["id"], update_fields=["balance"],
        )
        barrier = None if ordered else threading.Barrier(2, timeout=10)
        results: dict[str, str] = {}
        threads = [
            threading.Thread(target=self.transfer, args=(1, 2, barrier, ordered, results)),
            threading.Thread(target=self.transfer, args=(2, 1, barrier, ordered, results)),
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        for name, outcome in sorted(results.items()):
            self.stdout.write(f"  transfer {name}: {outcome}")
        self.stdout.write(f"  balances: {list(Account.objects.order_by('id').values_list('id', 'balance'))}")

    def handle(self, *args, **options):
        self.stdout.write("Opposite lock order (A: 1 then 2, B: 2 then 1):")
        self.run(ordered=False)
        self.stdout.write("\nSame lock order (both lock 1 then 2):")
        self.run(ordered=True)
