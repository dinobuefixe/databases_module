from django.conf import settings
from pymongo import MongoClient

# Django's ORM does not handle MongoDB documents, so we use pymongo next to it.
mongo = MongoClient(settings.MONGO_URL)
mongo_db = mongo[settings.MONGO_DB]
stores = mongo_db.stores
