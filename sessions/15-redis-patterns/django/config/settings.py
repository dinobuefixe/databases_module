import os
from pathlib import Path

import dj_database_url
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]
DEBUG = os.environ.get("DJANGO_DEBUG", "false").lower() == "true"
ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

INSTALLED_APPS = ["demo"]

MIDDLEWARE = ["django.middleware.common.CommonMiddleware"]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {"default": dj_database_url.parse(os.environ["DATABASE_URL"])}

# Django has a cache framework with a Redis backend (django.core.cache.backends.redis),
# but it hides the data structures this session is about, so we use redis-py directly.
REDIS_URL = os.environ["REDIS_URL"]
RATE_LIMIT = int(os.environ.get("RATE_LIMIT", "10"))

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
USE_TZ = True
TIME_ZONE = "UTC"
LANGUAGE_CODE = "en-gb"
