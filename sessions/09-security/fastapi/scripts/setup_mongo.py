"""Create the MongoDB application user and seed the users collections.

The user is created by root (MONGO_ADMIN_URL) with readWrite on this project's database only.
Everything after that runs as the new user (MONGO_URL). Safe to run again.
"""

import os

from argon2 import PasswordHasher
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import OperationFailure

load_dotenv()

DB = os.environ["MONGO_DB"]

# Demo accounts for the login endpoints. Not real passwords.
DEMO_USERS = {"admin": "admin-demo-password", "maria": "maria-demo-password"}


def create_user() -> None:
    admin_db = MongoClient(os.environ["MONGO_ADMIN_URL"])[DB]
    roles = [{"role": "readWrite", "db": DB}]
    password = os.environ["MONGO_APP_PASSWORD"]
    # The user lives in this database (authSource=s09_fastapi), so it cannot clash with other projects.
    if admin_db.command("usersInfo", "app")["users"]:
        admin_db.command("updateUser", "app", pwd=password, roles=roles)
        print(f"updated user app on {DB}")
    else:
        admin_db.command("createUser", "app", pwd=password, roles=roles)
        print(f"created user app on {DB} with readWrite on {DB} only")


def seed_users() -> None:
    client = MongoClient(os.environ["MONGO_URL"])
    db = client[DB]
    status = db.command("connectionStatus")["authInfo"]["authenticatedUsers"]
    print(f"connected as {status}")

    # Passwords stored as argon2 hashes: slow to compute on purpose, salted, never reversible.
    hasher = PasswordHasher()
    db.users.create_index("username", unique=True)
    for username, password in DEMO_USERS.items():
        db.users.replace_one(
            {"username": username},
            {"username": username, "password_hash": hasher.hash(password)},
            upsert=True,
        )
    print(f"users: {db.users.count_documents({})} documents with argon2 hashes")

    # What old code often looked like: plain-text passwords, compared inside the query filter.
    # Kept only so that POST /login-unsafe can show the injection. Never store passwords like this.
    db.legacy_users.create_index("username", unique=True)
    for username, password in DEMO_USERS.items():
        db.legacy_users.replace_one(
            {"username": username}, {"username": username, "password": password}, upsert=True
        )
    print(f"legacy_users: {db.legacy_users.count_documents({})} documents with plain-text passwords (demo only)")

    # readWrite on one database means nothing outside it.
    try:
        client[f"{DB}_other"].probe.insert_one({"x": 1})
        print(f"insert into {DB}_other: allowed (unexpected)")
    except OperationFailure as exc:
        print(f"insert into {DB}_other: refused ({exc.details['codeName']})")


if __name__ == "__main__":
    create_user()
    seed_users()
