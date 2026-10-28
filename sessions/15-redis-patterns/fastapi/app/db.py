import os
from collections.abc import Iterator

import redis
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

load_dotenv()

engine = create_engine(os.environ["DATABASE_URL"])
SessionLocal = sessionmaker(engine)

# decode_responses=True returns str instead of bytes.
r = redis.Redis.from_url(os.environ["REDIS_URL"], decode_responses=True)


def get_session() -> Iterator[Session]:
    with SessionLocal() as session:
        yield session
