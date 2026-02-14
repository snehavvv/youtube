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

from database import SessionLocal, Video
import os
import requests

app = FastAPI(title="YouTube Monitor API")

CHANNELS = [
    "https://www.youtube.com/@markets",
    "https://www.youtube.com/@ANINewsIndia"
]

CHANNELS_MAP = {
    "https://www.youtube.com/@markets": "UCXZBbS8C2zqI5h1wQYtZ9vA", # Bloomberg Markets
    "https://www.youtube.com/@ANINewsIndia": "UCtFqdWTX9b6a_I2N9qZ9a5g", # ANI News
    "https://www.youtube.com/@CNN": "UCupvZG-5ko_eiXAupbDfxWw", # CNN
    "https://www.youtube.com/@SkyNews": "UCoMdktPbSTixAyNGwb-UYkQ", # Sky News
    "https://www.youtube.com/@AlJazeeraEnglish": "UCzbKQM2zLqkGRJE86tXw3hQ" # Al Jazeera English
} # Note: In a real app these would be dynamically resolved or config based. Use Channel IDs for PubSubHubbub.

@app.get("/")
def home():
    return {"message": "Welcome to YouTube Monitor Link"}

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
                    upload_date = datetime.strptime(upload_date_str, "%Y%m%d")
                except ValueError:
                    upload_date = datetime.utcnow()
            else:
                upload_date = datetime.utcnow()
                
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

@app.get("/subscribe")
async def subscribe_to_hub(callback_url: str):
    """
    Triggers subscription to YouTube PubSubHubbub for all configured channels.
    callback_url: The public URL of this API's /webhook endpoint.
                 (e.g. https://my-api.com/webhook)
    """
    hub_url = "https://pubsubhubbub.appspot.com/subscribe"
    results = []
    
    # We need Channel IDs, not URLs. 
    # For this demo, let's assume we have them or extract them. 
    # Example IDs mapped manually for robustness in this snippet:
    # Bloomberg Markets: UCPWOxvqspG2ccz8lWF_FzOQ (Actually likely 'UCrM7B7SL_g1edFOnmj-SDKg' etc. Let's use the map defined at top)
    
    for url, channel_id in CHANNELS_MAP.items():
        topic_url = f"https://www.youtube.com/xml/feeds/videos.xml?channel_id={channel_id}"
        
        data = {
            "hub.mode": "subscribe",
            "hub.topic": topic_url,
            "hub.callback": callback_url,
            "hub.verify": "async", # or 'sync'
            # "hub.secret": "some_secret_key" # Recommended for security
        }
        
        try:
            response = requests.post(hub_url, data=data)
            if response.status_code == 202:
                results.append({"channel": url, "status": "subscription_requested", "code": 202})
            else:
                results.append({"channel": url, "status": "failed", "code": response.status_code, "error": response.text})
        except Exception as e:
            results.append({"channel": url, "status": "error", "detail": str(e)})

    return {"results": results}

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
                        session = SessionLocal()
                        try:
                            # Check if exists
                            existing = session.query(Video).filter(Video.video_id == video_id).first()
                            if existing:
                                for key, value in video_details.items():
                                    setattr(existing, key, value)
                            else:
                                new_video = Video(**video_details)
                                session.add(new_video)
                            session.commit()
                            logger.info(f"Stored video: {video_details['title']}")
                        except Exception as e:
                            logger.error(f"DB Error: {e}")
                            session.rollback()
    session = SessionLocal()
    try:
        videos = session.query(Video).order_by(Video.upload_date.desc()).limit(limit).all()
        return [v.to_dict() for v in videos]
    finally:
        session.close()status": "received"}
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
