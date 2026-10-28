import redis
from django.conf import settings
from pymongo import MongoClient

# Both connect with the application's own restricted users, not as root/default.
mongo = MongoClient(settings.MONGO_URL)
mongo_db = mongo[settings.MONGO_DB]

r = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
