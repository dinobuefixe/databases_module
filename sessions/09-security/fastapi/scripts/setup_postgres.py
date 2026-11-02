"""Create the three roles (if missing) and grant them privileges on this project's database.

Runs as the superuser (ADMIN_DATABASE_URL). Safe to run again.
"""

import os

import psycopg
from dotenv import load_dotenv
from psycopg import sql

load_dotenv()

ROLES = {
    "migrations": os.environ["MIGRATIONS_PASSWORD"],
    "app": os.environ["APP_PASSWORD"],
    "readonly": os.environ["READONLY_PASSWORD"],
}

# CREATE ROLE has no IF NOT EXISTS, so the DO block catches the "already exists" error instead.
# Roles are shared by every database on the server: an existing role keeps its password.
CREATE_ROLE = """
DO $$
BEGIN
    CREATE ROLE {role} LOGIN PASSWORD {password};
    RAISE NOTICE 'created role %', {name};
EXCEPTION WHEN duplicate_object OR unique_violation THEN
    RAISE NOTICE 'role % already exists, password left unchanged', {name};
END
$$;
"""

GRANTS = """
ALTER DATABASE {db} OWNER TO migrations;
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
-- Pagila's public schema is owned by postgres, so owning the database is not enough:
-- migrations also needs CREATE on the schema to add tables.
GRANT USAGE, CREATE ON SCHEMA public TO migrations;
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


def main() -> None:
    with psycopg.connect(os.environ["ADMIN_DATABASE_URL"], autocommit=True) as conn:
        conn.add_notice_handler(lambda notice: print(notice.message_primary))
        for role, password in ROLES.items():
            conn.execute(
                sql.SQL(CREATE_ROLE).format(
                    role=sql.Identifier(role), password=sql.Literal(password), name=sql.Literal(role)
                )
            )
        db = conn.info.dbname
        conn.execute(sql.SQL(GRANTS).format(db=sql.Identifier(db)))
        print(f"granted privileges on database {db}")


if __name__ == "__main__":
    main()
