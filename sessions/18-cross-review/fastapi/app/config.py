import os

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ["DATABASE_URL"]
REDIS_URL = os.environ["REDIS_URL"]
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "rv-admin-7f3a9c2e51d84b06")
PROFILE_TTL = 300
