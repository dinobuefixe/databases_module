-- The recipe model from session 02 with every rule enforced by the database.
-- Constraints are named so that error messages (and the API's responses) say which rule failed.

CREATE TABLE author (
    author_id  integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name       text NOT NULL,
    email      text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT author_email_unique UNIQUE (email)
);

CREATE TABLE ingredient (
    ingredient_id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name          text NOT NULL,
    kcal_per_100g numeric(6,1) NOT NULL,
    CONSTRAINT ingredient_name_unique UNIQUE (name),
    CONSTRAINT kcal_not_negative CHECK (kcal_per_100g >= 0)
);

CREATE TABLE recipe (
    recipe_id    integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    author_id    integer NOT NULL,
    title        text NOT NULL,
    servings     integer NOT NULL,
    published_at timestamptz,
    -- RESTRICT: an author with published recipes cannot be deleted by accident
    CONSTRAINT recipe_author_fk FOREIGN KEY (author_id)
        REFERENCES author ON DELETE RESTRICT,
    CONSTRAINT servings_between_1_and_50 CHECK (servings BETWEEN 1 AND 50),
    -- one author cannot publish two recipes with the same title
    CONSTRAINT recipe_author_title_unique UNIQUE (author_id, title)
);

CREATE TABLE recipe_ingredient (
    recipe_id     integer NOT NULL,
    ingredient_id integer NOT NULL,
    grams         numeric(7,1) NOT NULL,
    PRIMARY KEY (recipe_id, ingredient_id),
    -- CASCADE: the ingredient list means nothing without its recipe
    CONSTRAINT recipe_ingredient_recipe_fk FOREIGN KEY (recipe_id)
        REFERENCES recipe ON DELETE CASCADE,
    -- RESTRICT: an ingredient still used by a recipe cannot disappear
    CONSTRAINT recipe_ingredient_ingredient_fk FOREIGN KEY (ingredient_id)
        REFERENCES ingredient ON DELETE RESTRICT,
    CONSTRAINT grams_positive CHECK (grams > 0)
);
