-- Tables this project adds to the Pagila copy.

-- One row per film, updated with an upsert on every view.
CREATE TABLE IF NOT EXISTS film_views (
    film_id integer PRIMARY KEY REFERENCES film,
    views   integer NOT NULL DEFAULT 0
);

-- Target of the bulk loads in scripts/bulk_load.py.
CREATE TABLE IF NOT EXISTS person (
    person_id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name      text NOT NULL,
    email     text NOT NULL UNIQUE,
    city      text NOT NULL
);
