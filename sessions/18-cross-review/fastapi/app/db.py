from collections.abc import Iterator

import redis
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import DATABASE_URL, REDIS_URL

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(engine)
r = redis.Redis.from_url(REDIS_URL, decode_responses=True)


def get_session() -> Iterator[Session]:
    with SessionLocal() as session:
        yield session
