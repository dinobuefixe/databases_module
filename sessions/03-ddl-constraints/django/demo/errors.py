from django.db import IntegrityError
from django.http import JsonResponse

# SQLSTATE codes PostgreSQL sends with each constraint violation.
UNIQUE_VIOLATION = "23505"
CONFLICT_STATUS = {UNIQUE_VIOLATION: 409}  # everything else is 422


def constraint_error(exc: IntegrityError) -> JsonResponse:
    """Turn a database constraint violation into a response that names the constraint.

    Django wraps the psycopg error; the original one is in __cause__ and carries
    the SQLSTATE and the constraint name sent by PostgreSQL.
    """
    pg = exc.__cause__
    sqlstate = getattr(pg, "sqlstate", None)
    diag = getattr(pg, "diag", None)
    return JsonResponse(
        {
            "error": diag.message_primary if diag else str(exc),
            "constraint": diag.constraint_name if diag else None,
            "sqlstate": sqlstate,
        },
        status=CONFLICT_STATUS.get(sqlstate, 422),
    )
