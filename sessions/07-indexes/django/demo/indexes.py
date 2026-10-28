from django.db import connection

from demo.models import TUTORIAL_INDEXES


def existing() -> list[str]:
    """Names of the tutorial indexes that exist right now."""
    with connection.cursor() as cur:
        cur.execute("SELECT indexname FROM pg_indexes WHERE indexname = ANY(%s) ORDER BY 1", [list(TUTORIAL_INDEXES)])
        return [row[0] for row in cur.fetchall()]


def create(name: str) -> str:
    model, index = TUTORIAL_INDEXES[name]
    with connection.schema_editor() as editor:
        sql = str(index.create_sql(model, editor))
        editor.add_index(model, index)
    with connection.cursor() as cur:
        cur.execute(f"ANALYZE {model._meta.db_table}")  # statistics for the expression index
    return sql


def drop(name: str) -> str:
    model, index = TUTORIAL_INDEXES[name]
    with connection.schema_editor() as editor:
        sql = str(index.remove_sql(model, editor))
        editor.remove_index(model, index)
    return sql
