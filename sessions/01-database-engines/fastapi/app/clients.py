import os

import psycopg
import redis
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

DATABASE_URL = os.environ["DATABASE_URL"]

mongo = MongoClient(os.environ["MONGO_URL"])
mongo_db = mongo[os.environ["MONGO_DB"]]

r = redis.Redis.from_url(os.environ["REDIS_URL"], decode_responses=True)


def pg_connect() -> psycopg.Connection:
    # One connection per call keeps the example simple. Session 11 introduces a pool.
    return psycopg.connect(DATABASE_URL)


def create_tables() -> None:
    with pg_connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS hello (
                id         integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                msg        text NOT NULL,
                created_at timestamptz NOT NULL DEFAULT now()
            )
            """
        )
