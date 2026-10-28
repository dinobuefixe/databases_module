import psycopg
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.db import pg_connect

app = FastAPI(title="Session 03: DDL and constraints")


# The request models only check types. There is no Field(gt=0) or email check on purpose:
# here the database is the one that refuses bad data, whatever application writes to it.
# A real API would validate in both places and keep the constraints as the last line of defence.
class NewAuthor(BaseModel):
    name: str
    email: str


class NewIngredient(BaseModel):
    name: str
    kcal_per_100g: float


class Line(BaseModel):
    ingredient_id: int
    grams: float


class NewRecipe(BaseModel):
    author_id: int
    title: str
    servings: int
    ingredients: list[Line] = []


def constraint_error(exc: psycopg.errors.IntegrityError, status: int) -> HTTPException:
    """Turn a constraint violation into a response that names the constraint."""
    return HTTPException(
        status,
        {
            "error": type(exc).__name__,
            "constraint": exc.diag.constraint_name,
            "message": exc.diag.message_primary,
            "detail": exc.diag.message_detail,
        },
    )


def write(sql: str, params: tuple, conflict_status: int = 409):
    """Run one INSERT ... RETURNING and map constraint violations to HTTP errors."""
    try:
        with pg_connect() as conn:
            return conn.execute(sql, params).fetchone()
    except psycopg.errors.UniqueViolation as exc:
        raise constraint_error(exc, conflict_status)  # 409: the row clashes with an existing one
    except (psycopg.errors.CheckViolation, psycopg.errors.ForeignKeyViolation) as exc:
        raise constraint_error(exc, 422)  # 422: the row itself is invalid


@app.post("/authors", status_code=201)
def create_author(body: NewAuthor):
    return write(
        "INSERT INTO author (name, email) VALUES (%s, %s) RETURNING *",
        (body.name, body.email),
    )


@app.post("/ingredients", status_code=201)
def create_ingredient(body: NewIngredient):
    return write(
        "INSERT INTO ingredient (name, kcal_per_100g) VALUES (%s, %s) RETURNING *",
        (body.name, body.kcal_per_100g),
    )


@app.post("/recipes", status_code=201)
def create_recipe(body: NewRecipe):
    """The recipe and its lines in one transaction: if one line is invalid, nothing is saved."""
    try:
        with pg_connect() as conn:
            recipe = conn.execute(
                "INSERT INTO recipe (author_id, title, servings) VALUES (%s, %s, %s) RETURNING *",
                (body.author_id, body.title, body.servings),
            ).fetchone()
            with conn.cursor() as cur:
                cur.executemany(
                    "INSERT INTO recipe_ingredient (recipe_id, ingredient_id, grams) VALUES (%s, %s, %s)",
                    [(recipe["recipe_id"], line.ingredient_id, line.grams) for line in body.ingredients],
                )
    except psycopg.errors.UniqueViolation as exc:
        raise constraint_error(exc, 409)
    except (psycopg.errors.CheckViolation, psycopg.errors.ForeignKeyViolation) as exc:
        raise constraint_error(exc, 422)
    return get_recipe(recipe["recipe_id"])


@app.get("/recipes/{recipe_id}")
def get_recipe(recipe_id: int):
    with pg_connect() as conn:
        recipe = conn.execute("SELECT * FROM recipe WHERE recipe_id = %s", (recipe_id,)).fetchone()
        if recipe is None:
            raise HTTPException(404, "recipe not found")
        recipe["ingredients"] = conn.execute(
            "SELECT ingredient_id, grams FROM recipe_ingredient WHERE recipe_id = %s ORDER BY ingredient_id",
            (recipe_id,),
        ).fetchall()
    return recipe


@app.delete("/authors/{author_id}")
def delete_author(author_id: int):
    """ON DELETE RESTRICT: refused with 409 while the author has recipes."""
    try:
        with pg_connect() as conn:
            deleted = conn.execute("DELETE FROM author WHERE author_id = %s", (author_id,)).rowcount
    # RESTRICT raises SQLSTATE 23001 (restrict_violation); the default NO ACTION raises 23503.
    except (psycopg.errors.RestrictViolation, psycopg.errors.ForeignKeyViolation) as exc:
        raise constraint_error(exc, 409)
    if deleted == 0:
        raise HTTPException(404, "author not found")
    return {"deleted_author": author_id}


@app.delete("/recipes/{recipe_id}")
def delete_recipe(recipe_id: int):
    """ON DELETE CASCADE: the database removes the recipe's ingredient lines too."""
    with pg_connect() as conn:
        lines = conn.execute(
            "SELECT count(*) AS n FROM recipe_ingredient WHERE recipe_id = %s", (recipe_id,)
        ).fetchone()["n"]
        deleted = conn.execute("DELETE FROM recipe WHERE recipe_id = %s", (recipe_id,)).rowcount
    if deleted == 0:
        raise HTTPException(404, "recipe not found")
    return {"deleted_recipe": recipe_id, "lines_removed_by_cascade": lines}
