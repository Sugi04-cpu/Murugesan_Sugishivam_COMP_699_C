from pymongo import MongoClient
from decouple import config

def get_collection(collection_name):
    """
    Get a MongoDB collection.
    """
    with MongoClient(config("MONGODB_URI")) as client:  # Use a context manager
        db = client[config("MONGODB_DATABASE")]
        return db[collection_name]

