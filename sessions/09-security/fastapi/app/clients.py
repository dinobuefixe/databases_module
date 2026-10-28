import os

import psycopg
import redis
from dotenv import load_dotenv
from psycopg.rows import dict_row
from pymongo import MongoClient

load_dotenv()

# The application connects as `app` (read and write data) and `readonly` (reports).
# The superuser URL is not read here: only the setup scripts use it.
DATABASE_URL = os.environ["DATABASE_URL"]
READONLY_DATABASE_URL = os.environ["READONLY_DATABASE_URL"]

# A MongoDB user with readWrite on this project's database only.
mongo = MongoClient(os.environ["MONGO_URL"])
mongo_db = mongo[os.environ["MONGO_DB"]]

# A Redis ACL user that cannot run @dangerous commands (FLUSHALL, FLUSHDB, KEYS, CONFIG...).
r = redis.Redis.from_url(os.environ["REDIS_URL"], decode_responses=True)


def pg_connect() -> psycopg.Connection:
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)


def pg_readonly() -> psycopg.Connection:
    return psycopg.connect(READONLY_DATABASE_URL, row_factory=dict_row)
