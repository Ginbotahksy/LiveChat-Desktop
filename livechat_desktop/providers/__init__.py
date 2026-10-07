from .twitter import TwitterProvider
from .youtube import YouTubeProvider
from .tiktok import TikTokProvider
from .generic import GenericProvider

# Initialisation des providers dans l'ordre de priorité
PROVIDERS = [
    TwitterProvider(),
    YouTubeProvider(),
    TikTokProvider(),
    GenericProvider() # Fallback qui gère tout ou presque
]

def process_link(lien, data, window_size):
    """
    Routage vers le bon provider selon l'URL.
    Retourne un dictionnaire contenant les modifications de 'data' ou 
    des instructions spécifiques de rendu (html, embed_url, web_size).
    """
    if not lien:
        return {}
        
    for provider in PROVIDERS:
        if provider.can_handle(lien):
            return provider.process(lien, data, window_size)
            
    return {}
