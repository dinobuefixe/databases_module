import time

from django.db import connection
from django.http import HttpRequest, JsonResponse
from django.test.utils import CaptureQueriesContext
from django.views.decorators.http import require_GET

from demo.queries import ORM, run


@require_GET
def report(request: HttpRequest, name: str) -> JsonResponse:
    """GET /reports/<name>?impl=orm|sql: the same question answered two ways."""
    if name not in ORM:
        return JsonResponse({"error": f"unknown report, use one of {list(ORM)}"}, status=404)
    impl = request.GET.get("impl", "orm")
    if impl not in ("orm", "sql"):
        return JsonResponse({"error": "impl must be orm or sql"}, status=400)

    start = time.perf_counter()
    with CaptureQueriesContext(connection) as ctx:
        rows = run(name, impl)
    return JsonResponse(
        {
            "report": name,
            "impl": impl,
            "count": len(rows),
            "ms": round((time.perf_counter() - start) * 1000, 1),
            "sql": [q["sql"] for q in ctx.captured_queries],  # what was actually sent
            "rows": rows,
        }
    )
