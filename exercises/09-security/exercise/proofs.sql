-- Proofs of least privilege. Run as the postgres superuser on ex09.
-- This file EXPECTS some statements to fail, so run it without ON_ERROR_STOP:
--
--   docker compose exec -T postgres psql -U postgres -d ex09 \
--       -f proofs.sql
--
-- The expected outcome is written as a comment above each statement.

-- Expected: ERROR:  must be owner of table film  (SQLSTATE 42501)
SET ROLE ex09_app;
DROP TABLE film;
RESET ROLE;

-- Expected: INSERT 0 1
SET ROLE ex09_app;
INSERT INTO actor (first_name, last_name) VALUES ('X', 'Y');
RESET ROLE;

-- Expected: a row count (e.g. 1000)
SET ROLE ex09_readonly;
SELECT count(*) AS films FROM film;
RESET ROLE;

-- Expected: ERROR:  permission denied for table actor  (SQLSTATE 42501)
SET ROLE ex09_readonly;
INSERT INTO actor (first_name, last_name) VALUES ('X', 'Y');
RESET ROLE;
