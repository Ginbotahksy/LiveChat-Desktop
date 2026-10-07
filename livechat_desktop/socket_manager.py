import os
import socketio
from PyQt6.QtCore import QThread, pyqtSignal
from livechat_desktop.config import config_manager

class SocketManager(QThread):
    # Signaux pour communiquer avec l'interface graphique (Overlay)
    media_signal = pyqtSignal(dict)
    stop_signal = pyqtSignal()
    guilds_updated_signal = pyqtSignal(list)
    
    def __init__(self):
        super().__init__()
        self.sio = socketio.Client()
        self.bot_client_id = None
        self.client_guilds = []
        
        self.setup_events()

    def setup_events(self):
        @self.sio.on('connect')
        def on_connect():
            print("Connecté au serveur Socket")
            print("Vérification de user_id :", config_manager.user_id)
            if config_manager.user_id:
                print("Envoi de get-my-guilds avec l'id :", config_manager.user_id)
                self.get_my_guilds()
            else:
                print("Aucun user_id trouvé dans config_manager!")

        @self.sio.on('bot-config')
        def on_bot_config(config):
            print("Config reçue du bot :", config)
            self.bot_client_id = config.get('clientId')
            self.guilds_updated_signal.emit(self.client_guilds)

        @self.sio.on('list-guilds')
        def on_list_guilds(guilds):
            print(f"Liste des serveurs reçue ({len(guilds)} serveurs)")
            self.client_guilds = guilds
            
            # On rejoint les rooms actives
            for room_id in list(config_manager.active_rooms):
                if any(g.get('id') == room_id for g in guilds):
                    print(f"Rejoint la room active : {room_id}")
                    self.join_room(room_id)
                else:
                    config_manager.active_rooms.remove(room_id)
            
            config_manager.save_config()
            self.guilds_updated_signal.emit(self.client_guilds)

        @self.sio.on('display-media')
        def on_display_media(data):
            self.media_signal.emit(data)
            
        @self.sio.on('stop')
        def on_stop():
            self.stop_signal.emit()

    def get_my_guilds(self):
        if config_manager.user_id:
            self.sio.emit("get-my-guilds", config_manager.user_id)

    def join_room(self, guild_id):
        self.sio.emit("join-server-room", guild_id)

    def leave_room(self, guild_id):
        self.sio.emit("leave-server-room", guild_id)

    def run(self):
        socket_url = os.environ.get("SOCKET_URL", "http://iceboxer.hd.free.fr:8080")
        try:
            self.sio.connect(socket_url)
            self.sio.wait()
        except Exception as e:
            print("SocketIO Error:", e)
