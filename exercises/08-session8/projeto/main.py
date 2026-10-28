import os
from contextlib import asynccontextmanager

import psycopg
from fastapi import FastAPI, HTTPException
from psycopg.rows import dict_row


def make_dsn(host: str, dbname: str) -> str:
    # Dentro da rede do Docker, a porta é sempre 5432 (não a 5433 do host)
    return (
        f"host={host} port=5432 dbname={dbname} "
        f"user={os.environ['POSTGRES_USER']} "
        f"password={os.environ['POSTGRES_PASSWORD']}"
    )


DATABASES = {
    "postgres1": make_dsn("postgres1", "postgres1"),
    "postgres2": make_dsn("postgres2", "postgres2"),
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.connections = {}
    for name, dsn in DATABASES.items():
        app.state.connections[name] = await psycopg.AsyncConnection.connect(
            dsn, autocommit=True, row_factory=dict_row
        )
    yield
    for conn in app.state.connections.values():
        await conn.close()


app = FastAPI(title="Session 8 - duas bases de dados", lifespan=lifespan)


def get_conn(name: str) -> psycopg.AsyncConnection:
    if name not in app.state.connections:
        raise HTTPException(status_code=404, detail=f"Base de dados '{name}' desconhecida")
    return app.state.connections[name]


@app.get("/health")
async def health():
    result = {}
    for name in DATABASES:
        try:
            cur = await get_conn(name).execute("SELECT 1 AS ok")
            row = await cur.fetchone()
            result[name] = "ok" if row["ok"] == 1 else "erro"
        except Exception as exc:
            result[name] = f"erro: {exc}"
    return result


@app.get("/databases/{name}")
async def database_tables(name: str):
    cur = await get_conn(name).execute(
        """
        SELECT * FROM {name   }
        """
    )
    rows = await cur.fetchall()
    return {"database": name, "tables": rows}