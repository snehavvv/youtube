import sys
import os
from datetime import datetime
import time

# Add parent directory to path to import database module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app_backend.database import get_db_collection

def simulate_new_video():
    collection = get_db_collection()
    
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    new_video = {
        "video_id": "DEMO_" + datetime.now().strftime("%Y%m%d%H%M%S"),
        "title": f"🔴 LIVE BREAKING NEWS: Market Update at {timestamp}",
        "url": "https://www.youtube.com/watch?v=DEMO12345",
        "upload_date": datetime.utcnow().isoformat(),
        "view_count": 1450,
        "like_count": 230,
        "description": "This is a simulated video entry to demonstrate real-time API capabilities for the project submission.",
        "channel_id": "UC_DEMO123",
        "channel_title": "Bloomberg Markets (Simulated)"
    }
    
    print("Simulating ingestion of new video...")
    time.sleep(1)
    
    try:
        collection.insert_one(new_video)
        print(f"✅ SUCCESSFULLY INGESTED: {new_video['title']}")
        print("The API should now reflect this new data.")
    except Exception as e:
        print(f"❌ Error inserting video: {e}")

if __name__ == "__main__":
    simulate_new_video()
