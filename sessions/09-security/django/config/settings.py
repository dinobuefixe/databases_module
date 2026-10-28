import os
from pathlib import Path

import dj_database_url
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]
DEBUG = os.environ.get("DJANGO_DEBUG", "false").lower() == "true"
ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

# Only what this example needs: no admin, auth or sessions.
INSTALLED_APPS = ["demo"]

MIDDLEWARE = ["django.middleware.common.CommonMiddleware"]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

# Least privilege: the app connects as `app`, reports use `readonly`. The
# superuser URL (ADMIN_DATABASE_URL) is not here; only setup_roles reads it.
DATABASES = {
    "default": dj_database_url.parse(os.environ["DATABASE_URL"]),
    "readonly": dj_database_url.parse(os.environ["READONLY_DATABASE_URL"]),
    "migrations": dj_database_url.parse(os.environ["MIGRATIONS_DATABASE_URL"]),
}

MONGO_URL = os.environ["MONGO_URL"]
MONGO_DB = os.environ["MONGO_DB"]
REDIS_URL = os.environ["REDIS_URL"]

# Django's password hashing without django.contrib.auth installed.
# Argon2 needs the argon2-cffi package.
PASSWORD_HASHERS = ["django.contrib.auth.hashers.Argon2PasswordHasher"]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
USE_TZ = True
TIME_ZONE = "UTC"
LANGUAGE_CODE = "en-gb"
