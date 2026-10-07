from .base import MediaProvider

class GenericProvider(MediaProvider):
    GENERIC_WEB_WIDTH_RATIO = 0.85
    GENERIC_WEB_HEIGHT_RATIO = 0.85

    def can_handle(self, url: str) -> bool:
        return True # Fallback for everything else

    def process(self, url: str, data: dict, window_size: tuple) -> dict:
        max_w = int(window_size[0] * self.GENERIC_WEB_WIDTH_RATIO)
        max_h = int(window_size[1] * self.GENERIC_WEB_HEIGHT_RATIO)
        
        return {
            "type": "web",
            "embed_url": url,
            "web_size": (max_w, max_h),
            "is_generic_web": True
        }
