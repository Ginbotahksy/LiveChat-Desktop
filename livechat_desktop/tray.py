import os
import webbrowser
import urllib.parse
from PyQt6.QtWidgets import QSystemTrayIcon, QMenu, QApplication
from PyQt6.QtGui import QAction, QIcon
from livechat_desktop.config import config_manager

class TrayManager:
    def __init__(self, style, socket_manager, overlay):
        self.tray_icon = QSystemTrayIcon()
        
        # Load custom icon if available
        icon_path = os.path.join(os.path.dirname(__file__), 'assets', 'icons', 'romain_guillon.jpg')
        if os.path.exists(icon_path):
            self.tray_icon.setIcon(QIcon(icon_path))
        else:
            # Fallback system icon
            self.tray_icon.setIcon(style.standardIcon(style.StandardPixmap.SP_ComputerIcon))
        
        self.menu = QMenu()
        self.tray_icon.setContextMenu(self.menu)
        
        self.socket_manager = socket_manager
        self.overlay = overlay
        
        self.update_menu([])
        self.tray_icon.show()

    def update_menu(self, guilds):
        self.menu.clear()
        
        # User status
        status_text = f"Connecté: {config_manager.user_id}" if config_manager.user_id else "Non connecté"
        action_status = self.menu.addAction(status_text)
        action_status.setEnabled(True)  # GNOME masque parfois les éléments désactivés
        
        if not config_manager.user_id and self.socket_manager.bot_client_id:
            action_login = self.menu.addAction("Se connecter à Discord")
            action_login.triggered.connect(self.login_discord)
            
        if config_manager.user_id:
            action_refresh = self.menu.addAction("Recharger la liste des serveurs")
            action_refresh.triggered.connect(self.socket_manager.get_my_guilds)
            
            action_logout = self.menu.addAction("Se déconnecter")
            action_logout.triggered.connect(self.logout)
            
        self.menu.addSeparator()
        
        action_rooms = self.menu.addAction("Rooms disponibles :")
        action_rooms.setEnabled(True)
        
        if not guilds:
            label = self.menu.addAction("Aucune room disponible")
            label.setEnabled(True)
        else:
            for guild in guilds:
                guild_id = guild.get('id')
                action = QAction(guild.get('name', 'Serveur inconnu'), self.menu)
                action.setCheckable(True)
                action.setChecked(guild_id in config_manager.active_rooms)
                # On utilise lambda avec paramètre par défaut pour figer la valeur de guild_id
                action.triggered.connect(lambda checked, gid=guild_id: self.toggle_room(gid))
                self.menu.addAction(action)
                
        self.menu.addSeparator()
        
        quit_action = QAction("Quitter LiveChat Python", self.menu)
        quit_action.triggered.connect(QApplication.instance().quit)
        self.menu.addAction(quit_action)

    def login_discord(self):
        redirect_uri = urllib.parse.quote("http://iceboxer.hd.free.fr:8080/callback")
        auth_url = f"https://discord.com/api/oauth2/authorize?client_id={self.socket_manager.bot_client_id}&redirect_uri={redirect_uri}&response_type=code&scope=identify%20guilds"
        webbrowser.open(auth_url)

    def logout(self):
        config_manager.set_user_id(None)
        config_manager.active_rooms.clear()
        config_manager.save_config()
        self.socket_manager.client_guilds = []
        self.update_menu([])

    def toggle_room(self, guild_id):
        if guild_id in config_manager.active_rooms:
            config_manager.active_rooms.remove(guild_id)
            self.socket_manager.leave_room(guild_id)
        else:
            config_manager.active_rooms.add(guild_id)
            self.socket_manager.join_room(guild_id)
        
        config_manager.save_config()
        # Rafraîchir le menu pour mettre à jour les cases cochées
        self.update_menu(self.socket_manager.client_guilds)
