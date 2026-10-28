import os

import psycopg
import redis
from dotenv import load_dotenv

load_dotenv()

r = redis.Redis.from_url(os.environ["REDIS_URL"], decode_responses=True)


def pg_readonly() -> psycopg.Connection:
    conn = psycopg.connect(os.environ["READONLY_DATABASE_URL"])
    conn.read_only = True
    return conn
