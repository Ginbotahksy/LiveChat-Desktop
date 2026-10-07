import re
import os
from .base import MediaProvider

class YouTubeProvider(MediaProvider):
    YOUTUBE_URL_REGEX = r'(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/)([^"&?\/\s]{11})'
    YOUTUBE_EMBED_BASE = "https://www.youtube-nocookie.com/embed/"
    YOUTUBE_EMBED_PARAMS = "?autoplay=1&controls=0&showinfo=0&rel=0&iv_load_policy=3&enablejsapi=1"
    YOUTUBE_DEFAULT_WIDTH = 1280
    YOUTUBE_DEFAULT_HEIGHT = 720

    def __init__(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        template_path = os.path.join(script_dir, 'scripts', 'youtube_embed.html')
        with open(template_path, 'r', encoding='utf-8') as f:
            self.youtube_html_template = f.read()

    def can_handle(self, url: str) -> bool:
        return bool(re.search(self.YOUTUBE_URL_REGEX, url))

    def process(self, url: str, data: dict, window_size: tuple) -> dict:
        match = re.search(self.YOUTUBE_URL_REGEX, url)
        if not match:
            return {}
            
        video_id = match.group(1)
        embed_url = f"{self.YOUTUBE_EMBED_BASE}{video_id}{self.YOUTUBE_EMBED_PARAMS}"
        html = self.youtube_html_template.replace("{embed_url}", embed_url)
        
        current_format = data.get('format', 'illustration')
        if current_format == "fullscreen":
            web_size = (window_size[0], window_size[1])
        else:
            web_size = (self.YOUTUBE_DEFAULT_WIDTH, self.YOUTUBE_DEFAULT_HEIGHT)
            
        return {
            "embed_url": embed_url,
            "html": html,
            "web_size": web_size
        }
