"""These tests send real HTTP requests to the running API (uv run python manage.py runserver).

Setup goes straight to the databases, because the API has no endpoint to reset data.
"""

import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import httpx
import psycopg
import pytest
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

API_URL = os.environ.get("API_URL", "http://localhost:8001")
# Each request opens its own PostgreSQL connection; keep this below max_connections.
WORKERS = int(os.environ.get("CONCURRENCY", "25"))


@pytest.fixture(scope="session")
def api():
    with httpx.Client(base_url=API_URL, timeout=30) as client:
        try:
            client.get("/health").raise_for_status()
        except httpx.HTTPError as exc:
            pytest.exit(f"The API at {API_URL} is not running or not healthy: {exc}", returncode=2)
        yield client


@pytest.fixture
def pg():
    with psycopg.connect(os.environ["DATABASE_URL"], autocommit=True) as conn:
        yield conn


@pytest.fixture
def mongo_db():
    client = MongoClient(os.environ["MONGO_URL"])
    yield client[os.environ["MONGO_DB"]]
    client.close()


def run_concurrently(fn, n: int) -> list:
    """Calls fn(i) for i in range(n) from WORKERS threads at once and returns the results."""
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        return list(pool.map(fn, range(n)))
