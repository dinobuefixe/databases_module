import os

from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand
from pymongo import MongoClient
from pymongo.errors import OperationFailure

# Demo accounts for a local example. Real passwords never live in code.
DEMO_USERS = {"admin": "admin-demo-password", "ana": "ana-demo-password"}


class Command(BaseCommand):
    help = "Create the MongoDB user (readWrite on this project's database only) and the users collections."

    def handle(self, *args, **options):
        db_name = settings.MONGO_DB
        password = os.environ["MONGO_APP_PASSWORD"]
        roles = [{"role": "readWrite", "db": db_name}]

        # As root, only to create the user. The user lives in this database and
        # can read and write it, and nothing else.
        with MongoClient(os.environ["MONGO_ADMIN_URL"]) as admin:
            db = admin[db_name]
            if db.command("usersInfo", "app")["users"]:
                db.command("updateUser", "app", pwd=password, roles=roles)
                self.stdout.write(f"updated user app on {db_name}")
            else:
                db.command("createUser", "app", pwd=password, roles=roles)
                self.stdout.write(f"created user app on {db_name} with readWrite on {db_name}")

        # From here on, connected as the application user.
        from demo.clients import mongo, mongo_db

        status = mongo_db.command("connectionStatus")["authInfo"]["authenticatedUsers"]
        self.stdout.write(f"connected as {status}")

        # Safe collection: argon2 hashes made by Django's password hasher.
        mongo_db.users.create_index("username", unique=True)
        for username, plain in DEMO_USERS.items():
            mongo_db.users.update_one(
                {"username": username}, {"$set": {"password_hash": make_password(plain)}}, upsert=True
            )
        # Legacy collection for the unsafe login: plain-text passwords, as old code
        # often stored them. A second mistake, kept only to show the injection.
        mongo_db.legacy_users.create_index("username", unique=True)
        for username, plain in DEMO_USERS.items():
            mongo_db.legacy_users.update_one({"username": username}, {"$set": {"password": plain}}, upsert=True)
        self.stdout.write(f"users: {mongo_db.users.count_documents({})}, legacy_users: {mongo_db.legacy_users.count_documents({})}")

        # What the app user can see and do outside its own database.
        self.stdout.write(f"databases visible to app: {mongo.list_database_names()}")
        try:
            mongo["admin"]["system.users"].find_one()
        except OperationFailure as exc:
            self.stdout.write(f"read admin.system.users as app -> {exc.details.get('errmsg', '').split(' to execute')[0]}")
