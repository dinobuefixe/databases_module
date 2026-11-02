import os
from collections.abc import Iterator

import redis
from dotenv import load_dotenv
from pymongo import MongoClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

load_dotenv()

# Enough connections for the concurrency tests (50 requests at once).
# pool_pre_ping checks each connection before use, so the API recovers on its own
# after the database is restarted or restored.
engine = create_engine(os.environ["DATABASE_URL"], pool_size=10, max_overflow=20, pool_pre_ping=True)
SessionLocal = sessionmaker(engine)

mongo = MongoClient(os.environ["MONGO_URL"])
mongo_db = mongo[os.environ["MONGO_DB"]]

r = redis.Redis.from_url(os.environ["REDIS_URL"], decode_responses=True)


def get_session() -> Iterator[Session]:
    with SessionLocal() as session:
        yield session
