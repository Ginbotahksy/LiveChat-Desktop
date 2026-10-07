import re
import os
from .base import MediaProvider

class TikTokProvider(MediaProvider):
    TIKTOK_URL_REGEX = r'tiktok\.com\/.*\/video\/([0-9]+)'
    TIKTOK_EMBED_BASE = "https://www.tiktok.com/embed/v2/"
    TIKTOK_ASPECT_RATIO = 9 / 16
    TIKTOK_DEFAULT_WIDTH = 405
    TIKTOK_DEFAULT_HEIGHT = 720

    def __init__(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        script_path = os.path.join(script_dir, 'scripts', 'tiktok_bypass.js')
        with open(script_path, 'r', encoding='utf-8') as f:
            self.js_bypass_script = f.read()

    def can_handle(self, url: str) -> bool:
        return bool(re.search(self.TIKTOK_URL_REGEX, url))

    def process(self, url: str, data: dict, window_size: tuple) -> dict:
        match = re.search(self.TIKTOK_URL_REGEX, url)
        if not match:
            return {}
            
        video_id = match.group(1)
        embed_url = f"{self.TIKTOK_EMBED_BASE}{video_id}"
        
        current_format = data.get('format', 'illustration')
        if current_format == "fullscreen":
            h = window_size[1]
            w = int(h * self.TIKTOK_ASPECT_RATIO)
            web_size = (w, h)
        else:
            web_size = (self.TIKTOK_DEFAULT_WIDTH, self.TIKTOK_DEFAULT_HEIGHT)
            
        return {
            "embed_url": embed_url,
            "web_size": web_size,
            "js_injection": self.js_bypass_script
        }
