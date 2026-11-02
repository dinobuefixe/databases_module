"""Create a Redis ACL user that can read and write keys but not run dangerous commands.

Runs ACL SETUSER as the default user (REDIS_ADMIN_URL), then connects as the new user.
To prove FLUSHALL is refused it first asks Redis with ACL DRYRUN, and only sends a command
as the restricted user once Redis has confirmed the user may not run it.
FLUSHALL is never sent as the default user.
"""

import os

import redis
from dotenv import load_dotenv

load_dotenv()

USER = os.environ["REDIS_APP_USER"]
PASSWORD = os.environ["REDIS_APP_PASSWORD"]


def main() -> None:
    admin = redis.Redis.from_url(os.environ["REDIS_ADMIN_URL"], decode_responses=True)
    # reset: start from no permissions, so running this again gives the same result.
    # ~*: any key. +@all -@dangerous: every command except FLUSHALL, FLUSHDB, KEYS, CONFIG, DEBUG...
    admin.execute_command("ACL", "SETUSER", USER, "reset", "on", f">{PASSWORD}", "~*", "+@all", "-@dangerous")
    print(f"ACL SETUSER {USER} on >*** ~* +@all -@dangerous")

    print(f"ACL DRYRUN {USER} FLUSHALL -> {admin.execute_command('ACL', 'DRYRUN', USER, 'FLUSHALL')}")

    app = redis.Redis.from_url(os.environ["REDIS_URL"], decode_responses=True)
    print(f"connected as {app.acl_whoami()}")
    print(f"SET s09:x 1 -> {app.set('s09:x', 1)}")
    print(f"GET s09:x   -> {app.get('s09:x')}")
    app.delete("s09:x")
    for command in (("FLUSHALL",), ("FLUSHDB",), ("KEYS", "*"), ("CONFIG", "GET", "maxmemory")):
        label = " ".join(command)
        if admin.execute_command("ACL", "DRYRUN", USER, *command) == "OK":
            print(f"{label:<20} -> allowed by the ACL (not sent)")
            continue
        try:
            app.execute_command(*command)
        except redis.exceptions.NoPermissionError as exc:
            print(f"{label:<20} -> {exc}")


if __name__ == "__main__":
    main()
