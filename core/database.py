from pymongo import MongoClient
from pymongo.collection import Collection

from core.config import settings

client = MongoClient(settings.mongodb_uri, serverSelectionTimeoutMS=5000)
database = client[settings.mongodb_db]
_ci_index_created = False


def get_patients_collection() -> Collection:
    global _ci_index_created
    collection = database[settings.mongodb_collection]
    if not _ci_index_created:
        collection.create_index("ci", unique=True)
        _ci_index_created = True
    return collection
