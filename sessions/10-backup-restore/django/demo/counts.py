import psycopg
from django.db import connection
from psycopg.conninfo import make_conninfo

# Every ordinary table and partition in public. Partitioned parents are left out
# (relkind 'p'): their rows are counted in the partitions.
TABLES = """
SELECT c.relname
FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE n.nspname = 'public' AND c.relkind = 'r'
ORDER BY 1
"""


def row_counts(dbname: str, **server) -> dict[str, int]:
    """Exact row count of every table. count(*), not the planner's estimate.

    By default on the server and with the user of DATABASE_URL; pass host, port,
    user and password to count somewhere else.
    """
    s = connection.settings_dict
    params = {"host": s["HOST"], "port": s["PORT"], "user": s["USER"], "password": s["PASSWORD"], **server}
    with psycopg.connect(make_conninfo(dbname=dbname, **params)) as conn:
        tables = [row[0] for row in conn.execute(TABLES)]
        return {t: conn.execute(f'SELECT count(*) FROM public."{t}"').fetchone()[0] for t in tables}
