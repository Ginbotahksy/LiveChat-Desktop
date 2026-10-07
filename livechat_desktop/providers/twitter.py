import re
import requests
from .base import MediaProvider

class TwitterProvider(MediaProvider):
    TWITTER_URL_REGEX = r'(?:twitter\.com|x\.com)\/[^\/]+\/status\/(\d+)'
    FXTWITTER_API_BASE = "https://api.fxtwitter.com/status/"
    API_TIMEOUT = 5

    def can_handle(self, url: str) -> bool:
        return "x.com" in url or "twitter.com" in url

    def process(self, url: str, data: dict, window_size: tuple) -> dict:
        match = re.search(self.TWITTER_URL_REGEX, url)
        if not match:
            return {}

        tweet_id = match.group(1)
        result = {}
        
        try:
            resp = requests.get(f"{self.FXTWITTER_API_BASE}{tweet_id}", timeout=self.API_TIMEOUT)
            if resp.status_code == 200:
                api_data = resp.json()
                tweet = api_data.get("tweet", {})
                if not tweet:
                    return {}
                    
                xt_text = tweet.get("text")
                if xt_text:
                    result["top_text"] = xt_text
                    
                media = tweet.get("media", {}).get("all", [])
                if media:
                    first_media = media[0]
                    m_type = "video" if first_media.get("type") in ("video", "gif") else "image"
                    m_url = first_media.get("url")
                    
                    result["url"] = m_url
                    result["type"] = m_type
                    result["lien"] = None
        except Exception as e:
            print("Erreur extraction Twitter:", e)
            
        return result
