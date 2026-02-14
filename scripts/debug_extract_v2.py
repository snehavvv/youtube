import yt_dlp
import json

URL = "https://www.youtube.com/@markets"

ydl_opts = {
    'quiet': True,
    'extract_flat': True,
    'playlistend': 1,
    'ignoreerrors': True
}

with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    info = ydl.extract_info(URL, download=False)
    # Check top-level info for channel metadata
    # Uploader field often contains the channel name
    print(f"Top-level keys: {list(info.keys())}")
    print(f"Uploader: {info.get('uploader')}")
    print(f"Channel: {info.get('channel')}")
    print(f"Title: {info.get('title')}")
