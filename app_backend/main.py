from fastapi import FastAPI, Request, HTTPException, Security, Depends
from fastapi.security.api_key import APIKeyHeader, APIKey
from starlette.status import HTTP_200_OK, HTTP_403_FORBIDDEN
import xmltodict
import logging
from datetime import datetime
import yt_dlp
import sys
import os

# Fix import path to allow running from root or subdir
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import get_db_collection
import os

app = FastAPI(title="YouTube Monitor API")

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Security (Bonus)
API_KEY_NAME = "X-API-Key"
API_KEY = os.getenv("API_KEY", "secret-token")
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def get_api_key(api_key_header: str = Security(api_key_header)):
    if api_key_header == API_KEY:
        return api_key_header
    else:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN, detail="Could not validate credentials"
        )

# Helper to fetch video details
def fetch_video_details(video_id):
    ydl_opts = {
        'quiet': True,
        'ignoreerrors': True
    }
    url = f"https://www.youtube.com/watch?v={video_id}"
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        if info:
            upload_date_str = info.get('upload_date')
            if upload_date_str:
                try:
                    upload_date = datetime.strptime(upload_date_str, "%Y%m%d").isoformat()
                except ValueError:
                    upload_date = datetime.utcnow().isoformat()
            else:
                upload_date = datetime.utcnow().isoformat()
                
            return {
                "video_id": info.get('id'),
                "title": info.get('title'),
                "url": info.get('webpage_url'),
                "upload_date": upload_date,
                "view_count": info.get('view_count'),
                "like_count": info.get('like_count'),
                "description": info.get('description'),
                "channel_id": info.get('channel_id'),
                "channel_title": info.get('channel')
            }
    return None

@app.get("/request-feed")
async def verify_subscription(request: Request):
    # Handle PubSubHubbub verification
    params = request.query_params
    challenge = params.get("hub.challenge")
    if challenge:
        return int(challenge) # Return as plain text/int, framework handles it. Actually usually string.
        # FastAPI returns JSON by default, we might need to return PlainTextResponse for strict compliance if needed,
        # but usually the challenge is just the body.
    return "No challenge provided"

from fastapi.responses import PlainTextResponse
@app.get("/webhook", response_class=PlainTextResponse)
async def webhook_verify(hub_mode: str = None, hub_challenge: str = None, hub_verify_token: str = None):
    # Standard YouTube PubSubHubbub verification
    # YouTube sends: hub.mode=subscribe, hub.topic=..., hub.challenge=...
    # We just need to echo hub.challenge
    if hub_challenge:
        return hub_challenge
    return "Missing challenge"

@app.post("/webhook")
async def webhook_receive(request: Request):
    # Parse Atom Feed XML
    body = await request.body()
    try:
        data = xmltodict.parse(body)
        feed = data.get('feed', {})
        entry = feed.get('entry', None)
        
        if entry:
            # Entry can be a list if multiple updates, but usually one for real-time
            if isinstance(entry, list):
                entries = entry
            else:
                entries = [entry]
                
            for e in entries:
                video_id = e.get('yt:videoId')
                if video_id:
                    logger.info(f"New video notification: {video_id}")
                    # Fetch full details and store
                    video_details = fetch_video_details(video_id)
                    if video_details:
                        collection = get_db_collection()
                        collection.update_one(
                            {"video_id": video_id},
                            {"$set": video_details},
                            upsert=True
                        )
                        logger.info(f"Stored video: {video_details['title']}")
                    
        return {"status": "received"}
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return {"status": "error", "detail": str(e)}

@app.get("/videos/recent", dependencies=[Depends(get_api_key)])
async def get_recent_videos(limit: int = 10):
    collection = get_db_collection()
    # Sort by upload_date descending
    videos = list(collection.find({}, {"_id": 0}).sort("upload_date", -1).limit(limit))
    return videos

@app.get("/")
async def root():
    return {"message": "YouTube Monitor API is running"}
