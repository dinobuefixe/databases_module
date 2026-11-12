-- Least privilege roles for the ex09 database.
-- Run as the postgres superuser, passing the passwords as psql variables so no
-- secret is written in the file:
--
--   docker compose exec -T postgres psql -U postgres -d ex09 -v ON_ERROR_STOP=1 \
--       -v migrations_password="$EX09_MIGRATIONS_PASSWORD" \
--       -v app_password="$EX09_APP_PASSWORD" \
--       -v readonly_password="$EX09_READONLY_PASSWORD" \
--       -f roles.sql

-- Roles exist for the whole server, so use the ex09_ prefix.
CREATE ROLE ex09_migrations LOGIN PASSWORD :'migrations_password';
CREATE ROLE ex09_app        LOGIN PASSWORD :'app_password';
CREATE ROLE ex09_readonly   LOGIN PASSWORD :'readonly_password';

-- ex09_migrations owns the schema and runs migrations.
ALTER DATABASE ex09 OWNER TO ex09_migrations;

-- Nobody creates tables in public by accident (the default since PostgreSQL 15,
-- but stated explicitly).
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
GRANT USAGE ON SCHEMA public TO ex09_app, ex09_readonly;

-- ex09_app: read and write data, use sequences. No DDL.
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO ex09_app;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO ex09_app;

-- ex09_readonly: reports only.
GRANT SELECT ON ALL TABLES IN SCHEMA public TO ex09_readonly;

-- Tables created later by ex09_migrations get the same grants.
ALTER DEFAULT PRIVILEGES FOR ROLE ex09_migrations IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO ex09_app;
ALTER DEFAULT PRIVILEGES FOR ROLE ex09_migrations IN SCHEMA public
    GRANT USAGE ON SEQUENCES TO ex09_app;
ALTER DEFAULT PRIVILEGES FOR ROLE ex09_migrations IN SCHEMA public
    GRANT SELECT ON TABLES TO ex09_readonly;
