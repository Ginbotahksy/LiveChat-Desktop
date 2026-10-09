import re
import os
import json
import requests
from .base import MediaProvider

class YouTubeProvider(MediaProvider):
    YOUTUBE_URL_REGEX = r'(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?|shorts)\/|.*[?&]v=)|youtu\.be\/)([^"&?\/\s]{11})'
    YOUTUBE_POST_REGEX = r'(?:youtube\.com|youtu\.be)\/post\/([a-zA-Z0-9_-]+)'
    
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
        return bool(re.search(self.YOUTUBE_URL_REGEX, url)) or bool(re.search(self.YOUTUBE_POST_REGEX, url))

    def process(self, url: str, data: dict, window_size: tuple) -> dict:
        if re.search(self.YOUTUBE_POST_REGEX, url):
            return self._process_post(url)
        else:
            return self._process_video(url, data, window_size)

    def _process_video(self, url: str, data: dict, window_size: tuple) -> dict:
        match = re.search(self.YOUTUBE_URL_REGEX, url)
        if not match:
            return {}
            
        video_id = match.group(1)
        embed_url = f"{self.YOUTUBE_EMBED_BASE}{video_id}{self.YOUTUBE_EMBED_PARAMS}"
        html = self.youtube_html_template.replace("{embed_url}", embed_url)
        
        current_format = data.get('format', 'illustration')
        if "/shorts/" in url:
            if current_format == "fullscreen":
                web_size = (int(window_size[1] * 9 / 16), window_size[1])
            else:
                web_size = (int(self.YOUTUBE_DEFAULT_HEIGHT * 9 / 16), self.YOUTUBE_DEFAULT_HEIGHT)
        else:
            if current_format == "fullscreen":
                web_size = (window_size[0], window_size[1])
            else:
                web_size = (self.YOUTUBE_DEFAULT_WIDTH, self.YOUTUBE_DEFAULT_HEIGHT)
            
        return {
            "embed_url": embed_url,
            "html": html,
            "web_size": web_size
        }

    def _process_post(self, url: str) -> dict:
        result = {}
        headers = {}
        cookies = {'CONSENT': 'YES+cb.20210328-17-p0.en+FX+433'}
        try:
            resp = requests.get(url, headers=headers, cookies=cookies, timeout=10)
            if resp.status_code == 200:
                html = resp.text
                
                # We try to extract ytInitialData
                initial_data_match = re.search(r'var ytInitialData = ({.*?});</script>', html)
                if initial_data_match:
                    yt_data = json.loads(initial_data_match.group(1))
                    
                    try:
                        microformat = yt_data.get('microformat', {}).get('microformatDataRenderer', {})
                        description = microformat.get('description', '')
                        
                        if description:
                            result["top_text"] = description
                            
                        # Try to get the images
                        post_details = microformat.get('postDetails', {}).get('discussionForumPosting', {})
                        images = post_details.get('image', [])
                        
                        if images:
                            result["url"] = images[0]
                            result["type"] = "image"
                            result["lien"] = None
                        else:
                            # Fallback to thumbnail
                            thumbnails = microformat.get('thumbnail', {}).get('thumbnails', [])
                            if thumbnails:
                                best_thumbnail = sorted(thumbnails, key=lambda x: x.get('width', 0), reverse=True)[0]
                                result["url"] = best_thumbnail.get('url')
                                result["type"] = "image"
                                result["lien"] = None
                    except Exception as e:
                        print("Erreur parsing ytInitialData YouTube Post:", e)
        except Exception as e:
            print("Erreur extraction YouTube Post:", e)
            
        return result
