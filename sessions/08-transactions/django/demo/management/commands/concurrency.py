import json
from concurrent.futures import ThreadPoolExecutor
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from django.core.management.base import BaseCommand, CommandError

from demo.withdraw import STRATEGIES


def post(url: str, body: dict) -> int:
    request = Request(url, data=json.dumps(body).encode(), headers={"content-type": "application/json"}, method="POST")
    try:
        with urlopen(request, timeout=30) as response:
            return response.status
    except HTTPError as exc:
        return exc.code


def balance(base: str, account_id: int) -> str:
    with urlopen(f"{base}/accounts", timeout=30) as response:
        rows = json.load(response)["accounts"]
    return next(row["balance"] for row in rows if row["id"] == account_id)


class Command(BaseCommand):
    help = "Fire concurrent withdrawals at the running API and check how many succeed."

    def add_arguments(self, parser):
        parser.add_argument("--url", default="http://localhost:8001")
        parser.add_argument("--requests", type=int, default=50)
        parser.add_argument("--workers", type=int, default=20, help="concurrent requests (each one opens a database connection)")
        parser.add_argument("--amount", type=int, default=10)
        parser.add_argument("--start", type=int, default=100)
        parser.add_argument("--strategy", choices=[*STRATEGIES, "all"], default="all")

    def handle(self, *args, url, requests, workers, amount, start, strategy, **options):
        expected = min(requests, start // amount)
        self.stdout.write(f"{requests} withdrawals of {amount} from a balance of {start}, {workers} at a time. Expected: {expected} succeed, balance {start - expected * amount}.\n")
        failed = []
        for name in STRATEGIES if strategy == "all" else [strategy]:
            post(f"{url}/accounts/reset", {"balance": start})
            target = f"{url}/accounts/1/withdraw?strategy={name}"
            with ThreadPoolExecutor(max_workers=workers) as pool:
                statuses = list(pool.map(lambda _: post(target, {"amount": amount}), range(requests)))
            ok = statuses.count(200)
            final = balance(url, 1)
            # Money that left the account according to the API vs according to the database.
            lost = ok * amount - (start - float(final))
            verdict = "correct" if ok == expected and lost == 0 else f"WRONG, {lost:g} withdrawn but never subtracted"
            self.stdout.write(f"{name:<7} succeeded {ok:>3}, refused {statuses.count(409):>3}, final balance {final:>7}  {verdict}")
            if name != "naive" and verdict != "correct":
                failed.append(name)
        if failed:
            raise CommandError(f"safe strategies failed: {failed}")
