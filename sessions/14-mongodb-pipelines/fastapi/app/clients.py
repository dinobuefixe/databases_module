import os

import psycopg
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

mongo = MongoClient(os.environ["MONGO_URL"])
db = mongo[os.environ["MONGO_DB"]]


def pg_connect() -> psycopg.Connection:
    return psycopg.connect(os.environ["DATABASE_URL"])


def pg_readonly() -> psycopg.Connection:
    conn = psycopg.connect(os.environ["READONLY_DATABASE_URL"])
    # Every transaction on this connection is READ ONLY: an INSERT or UPDATE fails.
    conn.read_only = True
    return conn
