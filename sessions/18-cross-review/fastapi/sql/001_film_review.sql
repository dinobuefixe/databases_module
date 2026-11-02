-- Reviews written by customers about films.
CREATE TABLE IF NOT EXISTS film_review (
    review_id   integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    customer_id integer NOT NULL REFERENCES customer (customer_id),
    film_id     integer NOT NULL REFERENCES film (film_id),
    rating      integer NOT NULL,
    body        text    NOT NULL DEFAULT '',
    created_at  timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT film_review_one_per_customer UNIQUE (customer_id, film_id)
);

CREATE INDEX IF NOT EXISTS film_review_body_idx ON film_review (body);
