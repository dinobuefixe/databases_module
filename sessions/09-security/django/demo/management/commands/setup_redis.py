import os

import redis
from django.core.management.base import BaseCommand

COMMANDS_TO_PROVE = [("FLUSHALL",), ("FLUSHDB",), ("KEYS", "*"), ("CONFIG", "GET", "maxmemory")]


class Command(BaseCommand):
    help = "Create a Redis ACL user that can read and write keys but not run dangerous commands."

    def handle(self, *args, **options):
        user, password = os.environ["REDIS_APP_USER"], os.environ["REDIS_APP_PASSWORD"]

        admin = redis.Redis.from_url(os.environ["REDIS_ADMIN_URL"], decode_responses=True)
        # reset: start from no permissions, so running this again gives the same result.
        # ~*: any key. +@all -@dangerous: every command except FLUSHALL, FLUSHDB, KEYS, CONFIG, DEBUG...
        admin.execute_command("ACL", "SETUSER", user, "reset", "on", f">{password}", "~*", "+@all", "-@dangerous")
        self.stdout.write(f"ACL SETUSER {user} on >*** ~* +@all -@dangerous")

        from demo.clients import r  # connects with REDIS_URL, as the new user

        self.stdout.write(f"connected as {r.acl_whoami()}")
        self.stdout.write(f"{'SET s09:x 1':<24} -> {r.set('s09:x', 1)}")
        self.stdout.write(f"{'GET s09:x':<24} -> {r.get('s09:x')}")
        r.delete("s09:x")

        for command in COMMANDS_TO_PROVE:
            label = " ".join(command)
            # ACL DRYRUN asks Redis whether the user may run the command without running it.
            # A command is only sent as the restricted user once Redis says it is refused.
            # FLUSHALL is never sent as the default user.
            if admin.execute_command("ACL", "DRYRUN", user, *command) == "OK":
                self.stdout.write(f"{label:<24} -> allowed by the ACL (not sent)")
                continue
            try:
                r.execute_command(*command)
            except redis.exceptions.NoPermissionError as exc:
                self.stdout.write(f"{label:<24} -> {exc}")
