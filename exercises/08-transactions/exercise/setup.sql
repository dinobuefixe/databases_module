-- Run once on a fresh copy of Pagila (ex08).
-- Adds a balance to every customer and brings store 1 from 6 to 20 active staff.

ALTER TABLE customer
    ADD COLUMN balance numeric(10,2) NOT NULL DEFAULT 100 CHECK (balance >= 0);

INSERT INTO staff (first_name, last_name, address_id, store_id, username)
SELECT 'Temp', 'Staff ' || g, 1, 1, 'temp' || g
FROM generate_series(1, 14) AS g;
