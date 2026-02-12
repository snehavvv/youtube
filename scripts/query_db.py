import os
import sys
from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import datetime

# Load env vars
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "youtube_monitor")
COLLECTION_NAME = "videos"

def query_recent_videos(limit=5):
    """
    Queries the database for the most recent videos.
    """
    try:
        client = MongoClient(MONGO_URI)
        db = client[DB_NAME]
        collection = db[COLLECTION_NAME]
        
        # Check if connected
        client.admin.command('ping')
        print("Connected to MongoDB successfully.")

        print(f"\n--- Fetching last {limit} videos ---")
        cursor = collection.find({}, {"_id": 0}).sort("upload_date", -1).limit(limit)
        
        videos = list(cursor)
        if not videos:
            print("No videos found in the database.")
            return

        for v in videos:
            print(f"[{v.get('upload_date')}] {v.get('title')} ({v.get('channel_title')})")
            print(f"   ID: {v.get('video_id')} | Views: {v.get('view_count')}")
            print("-" * 50)
            
    except Exception as e:
        print(f"Error querying database: {e}")

if __name__ == "__main__":
    query_recent_videos()
