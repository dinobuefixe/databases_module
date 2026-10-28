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

DATABASES = {
    "default": dj_database_url.parse(os.environ["DATABASE_URL"]),
    "readonly": dj_database_url.parse(os.environ.get("READONLY_DATABASE_URL", os.environ["DATABASE_URL"])),
}

MONGO_URL = os.environ["MONGO_URL"]
MONGO_DB = os.environ["MONGO_DB"]
REDIS_URL = os.environ["REDIS_URL"]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
USE_TZ = True
TIME_ZONE = "UTC"
LANGUAGE_CODE = "en-gb"

# on_commit(..., robust=True) logs a failing Redis update instead of raising it.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "loggers": {"django.db.backends.base": {"handlers": ["console"], "level": "ERROR"}},
}
