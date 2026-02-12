import os
from dotenv import load_dotenv
load_dotenv() # Load from .env if present

from pymongo import MongoClient

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "youtube_monitor")
COLLECTION_NAME = "videos"

def get_collection():
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    return db[COLLECTION_NAME]
