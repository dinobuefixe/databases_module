import os

import psycopg
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

DATABASE_URL = os.environ["DATABASE_URL"]

mongo = MongoClient(os.environ["MONGO_URL"])
# Our own database, the equivalent of `use pagila_docs` in mongosh.
db = mongo[os.environ["MONGO_DB"]]


def pg_connect() -> psycopg.Connection:
    return psycopg.connect(DATABASE_URL)
