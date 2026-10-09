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
                    
                xt_text = tweet.get("text", "")
                
                # Gestion des Quote Tweets (republications avec citation)
                quote = tweet.get("quote")
                if quote:
                    quote_author = quote.get("author", {}).get("screen_name", "unknown")
                    quote_text = quote.get("text", "")
                    if xt_text:
                        xt_text += "\n\n"
                    xt_text += f"🔁 @{quote_author} : {quote_text}"
                
                if xt_text:
                    result["top_text"] = xt_text
                    
                media = tweet.get("media", {}).get("all", [])
                
                # Si le tweet principal n'a pas de média mais que la citation en a un
                if not media and quote:
                    media = quote.get("media", {}).get("all", [])
                    
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
