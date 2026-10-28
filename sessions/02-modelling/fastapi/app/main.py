import psycopg
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.db import pg_connect

app = FastAPI(title="Session 02: modelling")


class Line(BaseModel):
    ingredient_id: int
    grams: float = Field(gt=0)


class NewRecipe(BaseModel):
    author_id: int
    title: str = Field(min_length=1)
    servings: int = Field(gt=0)
    ingredients: list[Line] = Field(min_length=1)


# The denormalised column is recalculated from the normalised tables.
# Always call it in the same transaction that changed the ingredients,
# so no other session can read a recipe whose stored total is out of date.
RECALCULATE_KCAL = """
    UPDATE recipe r
    SET kcal_per_serving = round(
        coalesce((SELECT sum(ri.grams * i.kcal_per_100g / 100)
                  FROM recipe_ingredient ri
                  JOIN ingredient i USING (ingredient_id)
                  WHERE ri.recipe_id = r.recipe_id), 0) / r.servings, 1)
    WHERE r.recipe_id = %s
"""


def insert_lines(conn: psycopg.Connection, recipe_id: int, lines: list[Line]) -> None:
    with conn.cursor() as cur:
        cur.executemany(
            "INSERT INTO recipe_ingredient (recipe_id, ingredient_id, grams) VALUES (%s, %s, %s)",
            [(recipe_id, line.ingredient_id, line.grams) for line in lines],
        )


def bad_reference(exc: psycopg.Error) -> HTTPException:
    # The foreign keys and the composite primary key reject what the spreadsheet allowed.
    return HTTPException(422, f"{type(exc).__name__}: {exc.diag.message_primary}")


@app.post("/recipes", status_code=201)
def create_recipe(body: NewRecipe):
    """Create a recipe and its ingredient lines in one transaction."""
    try:
        with pg_connect() as conn:
            recipe_id = conn.execute(
                "INSERT INTO recipe (author_id, title, servings) VALUES (%s, %s, %s) RETURNING recipe_id",
                (body.author_id, body.title, body.servings),
            ).fetchone()["recipe_id"]
            insert_lines(conn, recipe_id, body.ingredients)
            conn.execute(RECALCULATE_KCAL, (recipe_id,))
    except (psycopg.errors.ForeignKeyViolation, psycopg.errors.UniqueViolation) as exc:
        raise bad_reference(exc)
    return get_recipe(recipe_id)


@app.get("/recipes")
def list_recipes():
    """The listing page: reads the stored kcal_per_serving, no join and no sum."""
    with pg_connect() as conn:
        return conn.execute(
            "SELECT recipe_id, title, servings, kcal_per_serving FROM recipe ORDER BY recipe_id"
        ).fetchall()


@app.get("/recipes/{recipe_id}")
def get_recipe(recipe_id: int):
    """One recipe with its author and ingredients, joined back from the normalised tables."""
    with pg_connect() as conn:
        recipe = conn.execute(
            """
            SELECT r.recipe_id, r.title, r.servings, r.kcal_per_serving,
                   a.author_id, a.name AS author, a.email AS author_email
            FROM recipe r
            JOIN author a USING (author_id)
            WHERE r.recipe_id = %s
            """,
            (recipe_id,),
        ).fetchone()
        if recipe is None:
            raise HTTPException(404, "recipe not found")
        recipe["ingredients"] = conn.execute(
            """
            SELECT i.ingredient_id, i.name, i.kcal_per_100g, ri.grams
            FROM recipe_ingredient ri
            JOIN ingredient i USING (ingredient_id)
            WHERE ri.recipe_id = %s
            ORDER BY i.name
            """,
            (recipe_id,),
        ).fetchall()
    return recipe


@app.put("/recipes/{recipe_id}/ingredients")
def replace_ingredients(recipe_id: int, lines: list[Line]):
    """Replace the ingredient list and recalculate kcal_per_serving in the same transaction."""
    try:
        with pg_connect() as conn:
            found = conn.execute("SELECT 1 FROM recipe WHERE recipe_id = %s", (recipe_id,)).fetchone()
            if found is None:
                raise HTTPException(404, "recipe not found")
            conn.execute("DELETE FROM recipe_ingredient WHERE recipe_id = %s", (recipe_id,))
            insert_lines(conn, recipe_id, lines)
            conn.execute(RECALCULATE_KCAL, (recipe_id,))
            # Leaving the block commits all three statements together, or none of them.
    except (psycopg.errors.ForeignKeyViolation, psycopg.errors.UniqueViolation) as exc:
        raise bad_reference(exc)
    return get_recipe(recipe_id)
