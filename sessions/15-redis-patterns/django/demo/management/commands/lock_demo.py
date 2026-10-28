import threading
import time

from django.core.management.base import BaseCommand

from demo.clients import r
from demo.patterns import run_exclusively


class Command(BaseCommand):
    help = "Starts two workers at the same moment; only the one that gets the lock runs the job."

    def add_arguments(self, parser):
        parser.add_argument("--workers", type=int, default=2)

    def handle(self, *args, workers, **options):
        start = threading.Barrier(workers)
        results = {}

        def worker(name: str):
            def job():
                self.stdout.write(f"{name}: running the nightly export (TTL {r.ttl('lock:nightly-export')}s)")
                time.sleep(2)

            start.wait()  # release all workers together
            results[name] = run_exclusively("nightly-export", job)

        threads = [threading.Thread(target=worker, args=(f"worker-{i}",)) for i in range(workers)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        for name, ran in sorted(results.items()):
            self.stdout.write(f"{name}: {'ran the job' if ran else 'lock held by someone else, skipped'}")
        self.stdout.write(f"lock:nightly-export after the job: {r.get('lock:nightly-export')}")
        ran = sum(results.values())
        style = self.style.SUCCESS if ran == 1 else self.style.ERROR
        self.stdout.write(style(f"{ran} of {workers} workers ran the job"))
