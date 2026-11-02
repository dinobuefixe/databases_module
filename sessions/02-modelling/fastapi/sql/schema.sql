-- The recipe spreadsheet, normalised into four tables.
-- Only primary keys, foreign keys and NOT NULL here: CHECK, UNIQUE and ON DELETE come in session 03.

DROP TABLE IF EXISTS recipe_ingredient, recipe, ingredient, author;

-- The email depends on the author, so it is stored once, here.
CREATE TABLE author (
    author_id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name      text NOT NULL,
    email     text NOT NULL
);

-- The calories depend on the ingredient, not on the recipe that uses it.
CREATE TABLE ingredient (
    ingredient_id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name          text NOT NULL,
    kcal_per_100g numeric(6,1) NOT NULL
);

CREATE TABLE recipe (
    recipe_id        integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    author_id        integer NOT NULL REFERENCES author,
    title            text NOT NULL,
    servings         integer NOT NULL,
    -- Deliberate denormalisation: derived from recipe_ingredient and ingredient,
    -- stored so the listing does not sum ingredients for every row.
    -- Recalculated in the same transaction whenever the ingredients change.
    kcal_per_serving numeric(7,1) NOT NULL DEFAULT 0
);

-- N:N between recipe and ingredient. The grams belong to the pair, so they live here.
CREATE TABLE recipe_ingredient (
    recipe_id     integer NOT NULL REFERENCES recipe,
    ingredient_id integer NOT NULL REFERENCES ingredient,
    grams         numeric(7,1) NOT NULL,
    PRIMARY KEY (recipe_id, ingredient_id)
);
