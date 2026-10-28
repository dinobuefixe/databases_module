import os

import psycopg
from django.core.management.base import BaseCommand, CommandError
from psycopg import sql

# CREATE ROLE has no IF NOT EXISTS. The DO block creates the role and catches the
# "already exists" error, so the command can run any number of times. Roles are
# shared by every database on the server: an existing role keeps its password.
CREATE_ROLE = """
DO $$
BEGIN
    CREATE ROLE {role} LOGIN PASSWORD {password};
    RAISE NOTICE 'created role %', {name};
EXCEPTION WHEN duplicate_object OR unique_violation THEN
    RAISE NOTICE 'role % already exists, password left unchanged', {name};
END
$$
"""

# The tutorial's grants, on this project's database only.
GRANTS = """
ALTER DATABASE {db} OWNER TO migrations;
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
-- In a new database the public schema belongs to the database owner. The Pagila
-- dump makes postgres its owner, so migrations needs CREATE on it explicitly.
GRANT CREATE ON SCHEMA public TO migrations;
GRANT USAGE ON SCHEMA public TO app, readonly;

GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO app;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly;

-- Tables that migrations creates later get the same grants automatically.
ALTER DEFAULT PRIVILEGES FOR ROLE migrations IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO app;
ALTER DEFAULT PRIVILEGES FOR ROLE migrations IN SCHEMA public
    GRANT USAGE ON SEQUENCES TO app;
ALTER DEFAULT PRIVILEGES FOR ROLE migrations IN SCHEMA public
    GRANT SELECT ON TABLES TO readonly;
"""


class Command(BaseCommand):
    help = "Create the migrations, app and readonly roles (if missing) and grant them privileges on this database."

    def handle(self, *args, **options):
        roles = {
            "migrations": os.environ["MIGRATIONS_PASSWORD"],
            "app": os.environ["APP_PASSWORD"],
            "readonly": os.environ["READONLY_PASSWORD"],
        }
        # The only place the superuser URL is used. Not a Django database alias on purpose.
        with psycopg.connect(os.environ["ADMIN_DATABASE_URL"], autocommit=True) as conn:
            db = conn.info.dbname
            if not db.startswith("s09_"):
                raise CommandError(f"refusing to change ownership of {db}: point ADMIN_DATABASE_URL at your s09_ database")
            conn.add_notice_handler(lambda notice: self.stdout.write(notice.message_primary))
            for role, password in roles.items():
                conn.execute(
                    sql.SQL(CREATE_ROLE).format(role=sql.Identifier(role), password=sql.Literal(password), name=sql.Literal(role))
                )
            conn.execute(sql.SQL(GRANTS).format(db=sql.Identifier(db)))
        self.stdout.write(f"granted privileges on database {db}")
