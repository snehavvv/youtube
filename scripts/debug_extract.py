import yt_dlp
import json

URL = "https://www.youtube.com/@markets/videos"

ydl_opts = {
    'quiet': True,
    'extract_flat': True,
    'playlistend': 1,
    'ignoreerrors': True
}

with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    info = ydl.extract_info(URL, download=False)
    if 'entries' in info:
        entries = list(info['entries'])
        if entries:
            print(json.dumps(entries[0], indent=2))
        else:
            print("No entries found")
    else:
        print("No entries key in info")
