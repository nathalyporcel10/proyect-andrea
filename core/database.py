import logging

from pymongo import MongoClient
from pymongo.collection import Collection

from core.config import settings

logger = logging.getLogger(__name__)

_client: MongoClient | None = None
_ci_index_created = False


def get_client() -> MongoClient:
    global _client
    if _client is None:
        clean_uri = settings.mongodb_uri.strip().strip('"\'').strip()
        _client = MongoClient(clean_uri, serverSelectionTimeoutMS=5000)
    return _client


def get_patients_collection() -> Collection:
    global _ci_index_created
    client = get_client()
    clean_db = settings.mongodb_db.strip().strip('"\'').strip()
    database = client[clean_db]
    collection = database[settings.mongodb_collection]
    if not _ci_index_created:
        try:
            collection.create_index("ci", unique=True)
            _ci_index_created = True
        except Exception as exc:
            logger.warning("No se pudo crear indice unico: %s", exc)
    return collection
