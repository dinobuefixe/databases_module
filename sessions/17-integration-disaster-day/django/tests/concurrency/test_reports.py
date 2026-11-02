from tests.concurrency.conftest import run_concurrently

MONTH = "2022-08"


def test_monthly_report_is_written_exactly_once(api, mongo_db):
    # Test setup only: a frozen report is never deleted in normal operation.
    mongo_db.monthly_reports.delete_one({"_id": MONTH})

    def generate(_):
        return api.post(f"/reports/monthly/{MONTH}").status_code

    statuses = run_concurrently(generate, 10)

    assert statuses.count(201) == 1, statuses
    assert statuses.count(409) == 9, statuses
    assert mongo_db.monthly_reports.count_documents({"_id": MONTH}) == 1
