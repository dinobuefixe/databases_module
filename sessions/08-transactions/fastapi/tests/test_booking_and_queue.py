"""The EXCLUDE constraint and the SKIP LOCKED queue, with concurrent transactions.

    uv run pytest -v
"""

from scripts.booking import overlap
from scripts.task_queue import run


def test_overlapping_booking_waits_and_is_refused_when_the_first_commits():
    result = overlap(a_commits=True)
    assert result["a"] == "booked"
    assert result["b"].startswith("refused, 23P01"), result


def test_overlapping_booking_goes_in_when_the_first_rolls_back():
    result = overlap(a_commits=False)
    assert result["b"] == "booked", result


def test_skip_locked_processes_every_task_exactly_once():
    result = run("skip-locked", tasks=200, workers=4)
    assert result["once"] == 200, result
    assert len(result["per_worker"]) == 4  # the work was shared, not done by one worker


def test_naive_queue_processes_some_tasks_twice():
    # Not an xfail like the naive withdrawal: here the bug itself is what the test checks.
    result = run("naive", tasks=50, workers=4)
    assert result["more_than_once"] > 0, result
