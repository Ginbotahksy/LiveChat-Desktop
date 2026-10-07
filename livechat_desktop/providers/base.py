class MediaProvider:
    """
    Classe de base (interface) pour tous les fournisseurs de médias.
    Normalise le traitement des liens entrants.
    """
    
    def can_handle(self, url: str) -> bool:
        """Retourne True si ce fournisseur peut gérer l'URL donnée."""
        raise NotImplementedError("doit être implémenté par la classe fille")

    def process(self, url: str, data: dict, window_size: tuple) -> dict:
        """
        Traite l'URL et retourne un dictionnaire contenant les instructions 
        de rendu (embed_url, html, web_size, js_injection, etc.) ou les 
        modifications à apporter à l'objet `data` (url, type, etc.).
        """
        raise NotImplementedError("doit être implémenté par la classe fille")
