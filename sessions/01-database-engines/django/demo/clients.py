import redis
from django.conf import settings
from pymongo import MongoClient

# Django has no built-in support for MongoDB documents or Redis data structures,
# so we use the official Python clients next to the ORM.
mongo = MongoClient(settings.MONGO_URL)
mongo_db = mongo[settings.MONGO_DB]

r = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
