import yt_dlp
import json
import sys

ydl_opts = {
    'quiet': True,
    'extract_flat': False,
    'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best', # Preferred format for QMediaPlayer
}

try:
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info("https://www.youtube.com/watch?v=jNQXAC9IVRw", download=False)
        # It could be in 'url' or we have to pick from 'formats'
        video_url = info.get('url')
        if not video_url and 'formats' in info:
            # find best format that has both video and audio or just the best one
            for f in reversed(info['formats']):
                if f.get('vcodec') != 'none' and f.get('acodec') != 'none':
                    video_url = f.get('url')
                    break
            if not video_url:
                video_url = info['formats'][-1].get('url')
                
        print(json.dumps({'title': info.get('title'), 'description': info.get('description'), 'url': video_url}))
except Exception as e:
    print(f"Error: {e}")
