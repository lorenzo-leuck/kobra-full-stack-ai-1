from pymongo import MongoClient
from app.config import settings
from functools import lru_cache

@lru_cache()
def get_mongodb_client():
    return MongoClient(settings.MONGODB_URL)

def get_database():
    client = get_mongodb_client()
    return client[settings.MONGODB_DB_NAME]
