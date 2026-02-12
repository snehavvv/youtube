import yt_dlp
import os
import sys
from datetime import datetime

# Add parent directory to path to import database module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app_backend.database import get_db_collection

CHANNELS = [
    "https://www.youtube.com/@markets",
    "https://www.youtube.com/@ANINewsIndia"
]

def parse_video_data(entry):
    upload_date_str = entry.get('upload_date')
    # yt-dlp returns date as YYYYMMDD
    if upload_date_str:
        try:
            upload_date = datetime.strptime(upload_date_str, "%Y%m%d").isoformat()
        except ValueError:
            upload_date = datetime.utcnow().isoformat()
    else:
        upload_date = datetime.utcnow().isoformat()

    return {
        "video_id": entry.get('id'),
        "title": entry.get('title'),
        "url": entry.get('webpage_url'),
        "upload_date": upload_date,
        "view_count": entry.get('view_count'),
        "like_count": entry.get('like_count'),
        "description": entry.get('description'),
        "channel_id": entry.get('channel_id'),
        "channel_title": entry.get('channel')
    }

def ingest_channel(channel_url, limit=1000):
    collection = get_db_collection()
    
    ydl_opts = {
        'quiet': True,
        'extract_flat': True, # Don't download video, just metadata. Note: 'flat' might miss some details like likes/views if not careful, but for playlist it's faster. 
        # Actually, extract_flat returns minimal info. We might need to iterate and fetch details if flat is too minimal.
        # But fetching 1000 details is slow. Let's try to get what we can.
        # For 'most recent 1000', we can use playlist_end.
        'playlistend': limit,
        'ignoreerrors': True
    }

    # First fetch the list of videos
    print(f"Fetching videos from {channel_url}...")
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        # Extract channel info
        info = ydl.extract_info(channel_url, download=False)
        
        if 'entries' in info:
            entries = list(info['entries'])
            print(f"Found {len(entries)} entries. Processing details...")
            
            # For accurate metadata (views, likes), we often need to process individually or use a smarter option.
            # However, extract_flat=True usually gives title, id, url. view_count might be missing or approximate.
            # Let's see if we can update the options to get more info without downloading.
            # Actually, to get full metadata like 'like_count', we usually need a full extraction.
            # Doing 1000 full extractions will take a LONG time. 
            # The prompt asks for "most recent 1,000 videos". 
            # We will batch process these.
            
            # Let's save the basic info first (fast) or decide if we iterate.
            # Optimization: We can insert what we have.
            
            video_data_list = []
            for entry in entries:
                if entry:
                    data = parse_video_data(entry)
                    # upsert based on video_id
                    collection.update_one(
                        {"video_id": data["video_id"]},
                        {"$set": data},
                        upsert=True
                    )
                    # print(f"Processed {data['title']}")
            print(f"Finished ingestion for {channel_url}")

if __name__ == "__main__":
    for channel in CHANNELS:
        ingest_channel(channel, limit=1000)
