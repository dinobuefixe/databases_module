from django.conf import settings
from dotenv import dotenv_values
from pymongo import MongoClient

# Django's ORM does not handle MongoDB documents, so we use pymongo next to it.
mongo = MongoClient(settings.MONGO_URL)
mongo_db = mongo[settings.MONGO_DB]


def container_mongo_url() -> str:
    """The URL for mongodump and mongorestore, which run inside the mongo container.

    There the server is localhost:27017 whatever port docker-compose.yml publishes on your
    machine, so MONGO_URL (written for your machine) does not work. They log in as the root
    user from the .env at the root of the repository.
    """
    env = dotenv_values(settings.REPO_ROOT / ".env")
    return f"mongodb://{env['MONGO_ROOT_USER']}:{env['MONGO_ROOT_PASSWORD']}@localhost:27017/?authSource=admin"
