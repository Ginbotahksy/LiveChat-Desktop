import os
import json

CONFIG_PATH = os.path.expanduser("~/.config/livechat-desktop/configLiveChat.json")

class ConfigManager:
    def __init__(self):
        self.user_id = None
        self.active_rooms = set()
        self.load_config()

    def load_config(self):
        print("Chemin recherché pour la config :", CONFIG_PATH)
        if os.path.exists(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.user_id = data.get('userId')
                self.active_rooms = set(data.get('activeRooms', []))
                print("Configuration chargée depuis :", CONFIG_PATH)
            except Exception as e:
                print("Erreur lors du chargement de la config :", e)

    def save_config(self):
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        try:
            config = {
                'userId': self.user_id,
                'activeRooms': list(self.active_rooms)
            }
            with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
            print("Configuration enregistrée à :", CONFIG_PATH)
        except Exception as e:
            print("Erreur lors de la sauvegarde de la config :", e)

    def set_user_id(self, user_id):
        self.user_id = user_id
        self.save_config()

config_manager = ConfigManager()
