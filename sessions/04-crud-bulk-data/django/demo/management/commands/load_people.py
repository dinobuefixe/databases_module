import time

from django.core.management.base import BaseCommand
from django.db import connection
from faker import Faker

from demo.models import Person

METHODS = ["copy", "bulk_create", "insert"]


def fake_people(rows: int) -> list[tuple[str, str, str]]:
    # A fixed seed gives everyone the same names, emails and cities.
    Faker.seed(42)
    fake = Faker("en_GB")
    return [(fake.name(), fake.unique.email(), fake.city()) for _ in range(rows)]


def load_copy(people) -> None:
    # COPY streams every row in one command. Django's cursor wrapper passes
    # .copy() through to the psycopg 3 cursor underneath.
    with connection.cursor() as cur:
        with cur.copy("COPY person (name, email, city) FROM STDIN") as copy:
            for row in people:
                copy.write_row(row)


def load_bulk_create(people) -> None:
    # Multi-row INSERT ... VALUES (...), (...), ... in batches.
    Person.objects.bulk_create((Person(name=n, email=e, city=c) for n, e, c in people), batch_size=5000)


def load_insert(people) -> None:
    # One INSERT per row, each one its own transaction (autocommit).
    for n, e, c in people:
        Person.objects.create(name=n, email=e, city=c)


class Command(BaseCommand):
    help = "Load fake people with COPY, bulk_create and one INSERT per row, and compare the times."

    def add_arguments(self, parser):
        parser.add_argument("--rows", type=int, default=100_000)
        parser.add_argument("--method", choices=[*METHODS, "all"], default="all")

    def handle(self, *args, rows, method, **options):
        self.stdout.write(f"Generating {rows:,} people with Faker (seed 42)...")
        people = fake_people(rows)
        loaders = {"copy": load_copy, "bulk_create": load_bulk_create, "insert": load_insert}

        for name in METHODS if method == "all" else [method]:
            with connection.cursor() as cur:
                cur.execute("TRUNCATE person RESTART IDENTITY")
            start = time.perf_counter()
            loaders[name](people)
            elapsed = time.perf_counter() - start
            count = Person.objects.count()
            self.stdout.write(f"{name:<12} {count:>9,} rows  {elapsed:7.2f} s  {count / elapsed:>10,.0f} rows/s")
