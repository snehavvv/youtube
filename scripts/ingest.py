import sys
import os
import yt_dlp
from datetime import datetime

# Add parent directory to path to import database module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app_backend.database import SessionLocal, Video

CHANNELS = [
    "https://www.youtube.com/@markets",
    "https://www.youtube.com/@ANINewsIndia",
    "https://www.youtube.com/@CNN",
    "https://www.youtube.com/@SkyNews",
    "https://www.youtube.com/@AlJazeeraEnglish"
]

def parse_video_data(entry, default_channel_title=None):
    upload_date_str = entry.get('upload_date')
    if upload_date_str:
        try:
            upload_date = datetime.strptime(upload_date_str, "%Y%m%d")
        except ValueError:
            upload_date = datetime.utcnow()
    else:
        upload_date = datetime.utcnow()

    # yt-dlp flat extraction sometimes puts channel in 'uploader' or 'channel'
    channel_title = entry.get('channel') or entry.get('uploader') or default_channel_title
    channel_id = entry.get('channel_id') or entry.get('uploader_id')

    return {
        "video_id": entry.get('id'),
        "title": entry.get('title'),
        "url": entry.get('webpage_url'),
        "upload_date": upload_date,
        "view_count": entry.get('view_count'),
        "like_count": entry.get('like_count'),
        "description": entry.get('description'),
        "channel_id": channel_id,
        "channel_title": channel_title
    }

def ingest_channel(channel_url, limit=1000):
    # Append /videos to ensure we get video list, not channel tabs
    if not channel_url.endswith('/videos') and not channel_url.endswith('/featured'):
         target_url = channel_url + '/videos'
    else:
         target_url = channel_url

    session = SessionLocal()
    print(f"Fetching videos from {target_url}...")
    
    ydl_opts = {
        'quiet': True,
        'extract_flat': True, 
        'playlistend': limit,
        'ignoreerrors': True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(target_url, download=False)
        
        # Try to get channel title from top-level info
        channel_level_title = info.get('uploader') or info.get('channel') or info.get('title')
        print(f"Extracted Channel Title: {channel_level_title}")

        if 'entries' in info:
            entries = list(info['entries'])
            print(f"Found {len(entries)} entries. Processing...")
            
            seen_ids = set()
            
            for entry in entries:
                if entry:
                    data = parse_video_data(entry, default_channel_title=channel_level_title)
                    v_id = data["video_id"]
                    
                    # Validate It's a Video (Simple length check: YT video IDs are 11 chars)
                    # Channel IDs are longer (24 chars, start with UC)
                    if not v_id or len(v_id) > 11:
                        continue
                        
                    # Deduplicate in current batch
                    if v_id in seen_ids:
                        continue
                    seen_ids.add(v_id)

                    # Upsert logic
                    existing = session.query(Video).filter(Video.video_id == v_id).first()
                    if existing:
                        for key, value in data.items():
                            setattr(existing, key, value)
                    else:
                        new_video = Video(**data)
                        session.add(new_video)
            
            session.commit()
            print(f"Finished ingestion for {channel_url}")
    session.close()

if __name__ == "__main__":
    print("Starting Ingestion...")
    for channel in CHANNELS:
        ingest_channel(channel, limit=50) # Reduced limit to 50 for quick testing
    print("Ingestion Complete.")

