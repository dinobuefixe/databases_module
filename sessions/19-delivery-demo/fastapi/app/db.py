import os
from collections.abc import Iterator

import redis
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

load_dotenv()

engine = create_engine(os.environ["DATABASE_URL"], pool_size=10, max_overflow=20, pool_pre_ping=True)
SessionLocal = sessionmaker(engine)
r = redis.Redis.from_url(os.environ["REDIS_URL"], decode_responses=True)


def get_session() -> Iterator[Session]:
    with SessionLocal() as session:
        yield session
