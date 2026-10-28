"""Two overlapping bookings of the same room, at the same time.

A books room 1 from 14:00 to 16:00 and keeps its transaction open for a second. Meanwhile B
books 15:00 to 17:00. The EXCLUDE constraint in sql/002_room_booking.sql finds A's row, still
uncommitted, so B waits for A. If A commits, B fails with SQLSTATE 23P01 (exclusion_violation).
If A rolls back, B's booking goes in. No SELECT and no lock in the application.

Then three bookings one at a time: one that starts when the first ends, one in another room,
one that overlaps.

    uv run python -m scripts.booking
"""

import sys
import threading
import time
from datetime import datetime, timezone

import psycopg
from psycopg.types.range import Range

from app.db import pg_connect, run_sql_file

HOLD_SECONDS = 1.0


def slot(start_hour: int, end_hour: int) -> Range:
    # "[)" includes the start and excludes the end, so 14-16 and 16-18 do not overlap.
    day = datetime(2026, 11, 2, tzinfo=timezone.utc)
    return Range(day.replace(hour=start_hour), day.replace(hour=end_hour), "[)")


def book(room: int, during: Range, hold: float = 0, commit: bool = True, inserted: threading.Event | None = None) -> str:
    try:
        with pg_connect() as conn:
            conn.execute("INSERT INTO room_booking (room, during) VALUES (%s, %s)", (room, during))
            if inserted:
                inserted.set()  # the row exists now, but is not committed
            time.sleep(hold)
            if not commit:
                conn.rollback()
                return "rolled back"
        return "booked"
    except psycopg.errors.ExclusionViolation as exc:
        return f"refused, {exc.sqlstate} {exc.diag.message_primary}"


def overlap(a_commits: bool) -> dict:
    """A books 14-16 and holds its transaction open; B books 15-17 meanwhile."""
    run_sql_file("002_room_booking.sql")
    with pg_connect() as conn:
        conn.execute("TRUNCATE room_booking RESTART IDENTITY")
    inserted = threading.Event()
    result = {}
    a = threading.Thread(
        target=lambda: result.update(a=book(1, slot(14, 16), HOLD_SECONDS, a_commits, inserted))
    )
    a.start()
    inserted.wait()
    started = time.perf_counter()
    result["b"] = book(1, slot(15, 17))
    result["b_waited"] = time.perf_counter() - started
    a.join()
    return result


def main() -> None:
    print(f"A books room 1, 14:00-16:00, and keeps its transaction open for {HOLD_SECONDS:g} s.")
    print("B books room 1, 15:00-17:00, meanwhile.\n")
    committed = overlap(a_commits=True)
    print(f"A commits:    A {committed['a']}; B waited {committed['b_waited']:.1f} s, then {committed['b']}")
    rolled_back = overlap(a_commits=False)
    print(f"A rolls back: A {rolled_back['a']}; B waited {rolled_back['b_waited']:.1f} s, then {rolled_back['b']}")

    overlap(a_commits=True)  # leave A's booking in place for the next part
    print("\nOne at a time, with A's 14:00-16:00 booked:")
    for room, (start, end), note in [
        (1, (16, 18), "starts when A's ends"),
        (2, (14, 16), "same hours, another room"),
        (1, (15, 17), "overlaps A's"),
    ]:
        print(f"  room {room}, {start}:00-{end}:00 ({note}): {book(room, slot(start, end))}")

    with pg_connect() as conn:
        rows = conn.execute("SELECT room, during FROM room_booking ORDER BY room, during").fetchall()
    print("\nroom_booking:")
    for row in rows:
        print(f"  room {row['room']}: {row['during'].lower:%H:%M} to {row['during'].upper:%H:%M}")

    if not committed["b"].startswith("refused, 23P01") or rolled_back["b"] != "booked":
        sys.exit("RULE BROKEN: the constraint did not decide as expected")


if __name__ == "__main__":
    main()
