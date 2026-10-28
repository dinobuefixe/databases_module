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

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
USE_TZ = True
TIME_ZONE = "UTC"
LANGUAGE_CODE = "en-gb"

# The equivalent of SQLAlchemy's echo=True. The "django.db.backends" logger
# receives every statement with its parameters and duration, but only when
# DEBUG is true (Django keeps connection.queries only in debug mode).
SQL_LOG = os.environ.get("SQL_LOG", "false").lower() == "true"
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "loggers": {
        "django.db.backends": {
            "handlers": ["console"],
            "level": "DEBUG" if SQL_LOG else "WARNING",
            "propagate": False,
        },
    },
}
