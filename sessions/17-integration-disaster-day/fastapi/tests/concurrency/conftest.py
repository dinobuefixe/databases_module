import os

import httpx
import pytest
from dotenv import load_dotenv

load_dotenv()
API_URL = os.getenv("API_URL", "http://localhost:8000")


@pytest.fixture(scope="session")
def api() -> str:
    """The tests talk to the running API over HTTP, like real clients."""
    try:
        httpx.get(f"{API_URL}/health", timeout=5).raise_for_status()
    except httpx.HTTPError as exc:
        pytest.fail(f"API not reachable or not healthy at {API_URL}: {exc}. Start it first with: uv run uvicorn app.main:app --port 8000")
    return API_URL
