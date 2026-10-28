-- The three spreadsheet rows, each fact stored once.
-- The spreadsheet has no servings column: Pancakes serve 4, the Omelette serves 1.

INSERT INTO author (name, email) VALUES
    ('Ana', 'ana@example.com'),
    ('Rui', 'rui@example.com');

INSERT INTO ingredient (name, kcal_per_100g) VALUES
    ('Flour', 364),
    ('Milk', 42),
    ('Egg', 155);

INSERT INTO recipe (author_id, title, servings)
SELECT author_id, 'Pancakes', 4 FROM author WHERE email = 'ana@example.com'
UNION ALL
SELECT author_id, 'Omelette', 1 FROM author WHERE email = 'rui@example.com';

INSERT INTO recipe_ingredient (recipe_id, ingredient_id, grams)
SELECT r.recipe_id, i.ingredient_id, v.grams
FROM (VALUES ('Pancakes', 'Flour', 200),
             ('Pancakes', 'Milk', 300),
             ('Omelette', 'Egg', 120)) AS v (title, ingredient, grams)
JOIN recipe r     ON r.title = v.title
JOIN ingredient i ON i.name = v.ingredient;

-- Fill the stored value once; the API keeps it up to date from now on.
UPDATE recipe r
SET kcal_per_serving = round(
    (SELECT sum(ri.grams * i.kcal_per_100g / 100)
     FROM recipe_ingredient ri
     JOIN ingredient i USING (ingredient_id)
     WHERE ri.recipe_id = r.recipe_id) / r.servings, 1);
