import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path to import database module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app_backend.database import SessionLocal, Video

def query_recent_videos(limit=5):
    """
    Queries the database for the most recent videos.
    """
    session = SessionLocal()
    try:
        print(f"\n--- Fetching last {limit} videos from Postgres ---")
        
        # Query using SQLAlchemy
        videos = session.query(Video).order_by(Video.upload_date.desc()).limit(limit).all()
        
        if not videos:
            print("No videos found in the database.")
            return

        for v in videos:
            print(f"[{v.upload_date}] {v.title} ({v.channel_title})")
            print(f"   ID: {v.video_id} | Views: {v.view_count}")
            print("-" * 50)
            
    except Exception as e:
        print(f"Error querying database: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    query_recent_videos()
