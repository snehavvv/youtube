import yt_dlp
import sys

URL = "https://www.youtube.com/@markets"

ydl_opts = {
    'quiet': False, # Changed to False to see debug info
    'extract_flat': True,
    'playlistend': 1,
    'ignoreerrors': True
}

print("Starting extraction...")
with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    try:
        info = ydl.extract_info(URL, download=False)
        print(f"Extraction complete. Type of info: {type(info)}")
        if info:
            print(f"Uploader: {info.get('uploader')}")
            print(f"Channel: {info.get('channel')}")
            print(f"Title: {info.get('title')}")
        else:
            print("Info is None or empty.")
    except Exception as e:
        print(f"Error: {e}")
