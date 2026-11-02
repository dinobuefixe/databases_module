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

# Django opens one connection per request thread and closes it at the end of the
# request (CONN_MAX_AGE = 0). That is the job of get_session() in the FastAPI version.
# CONN_MAX_AGE > 0 keeps connections open between requests, like a pool.
DATABASES = {"default": dj_database_url.parse(os.environ["DATABASE_URL"], conn_max_age=60)}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
USE_TZ = True
TIME_ZONE = "UTC"
LANGUAGE_CODE = "en-gb"
