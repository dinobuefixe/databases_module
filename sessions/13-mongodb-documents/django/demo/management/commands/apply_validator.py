from django.core.management.base import BaseCommand

from demo.clients import mongo_db
from demo.documents import STORE_SCHEMA


class Command(BaseCommand):
    help = "Adds the $jsonSchema validator to the stores collection (collMod), creating it if needed."

    def handle(self, *args, **options):
        options = {"validator": STORE_SCHEMA, "validationLevel": "strict", "validationAction": "error"}
        if "stores" in mongo_db.list_collection_names():
            # collMod changes an existing collection; documents already stored are not checked
            # now, but with validationLevel "strict" every later insert and update is.
            mongo_db.command("collMod", "stores", **options)
            self.stdout.write(self.style.SUCCESS("Validator applied to the existing stores collection"))
        else:
            mongo_db.create_collection("stores", **options)
            self.stdout.write(self.style.SUCCESS("Created stores with the validator"))
