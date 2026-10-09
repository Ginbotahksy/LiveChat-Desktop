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
                
                raw_name = guild.get('name', 'Serveur inconnu')
                import re
                clean_name = re.sub(r'[^\x00-\x7F\xC0-\xFF]', '', raw_name).strip() or raw_name
                action = QAction(clean_name, self.menu)
                action.setCheckable(True)
                action.setChecked(guild_id in config_manager.active_rooms)
                # On utilise lambda avec paramètre par défaut pour figer la valeur de guild_id
                action.triggered.connect(lambda checked, gid=guild_id: self.toggle_room(gid))
                self.menu.addAction(action)
                
        self.menu.addSeparator()
        
        self.action_update = QAction(getattr(self, "update_action_text", "Vérifier les mises à jour"), self.menu)
        self.action_update.triggered.connect(self.check_updates)
        self.menu.addAction(self.action_update)
        
        quit_action = QAction("Quitter LiveChat Python", self.menu)
        quit_action.triggered.connect(QApplication.instance().quit)
        self.menu.addAction(quit_action)

    def check_updates(self):
        from livechat_desktop.updater import UpdaterThread, prompt_linux_update
        import sys
        from PyQt6.QtWidgets import QMessageBox
        
        self.update_action_text = "Vérification..."
        if hasattr(self, "action_update"):
            self.action_update.setText(self.update_action_text)
            self.action_update.setEnabled(False)
            self.action_update.setIcon(QApplication.style().standardIcon(QApplication.style().StandardPixmap.SP_BrowserReload))
            
        self._manual_updater = UpdaterThread(manual=True)
        
        def reset_action(text, icon_pixmap=None, checkable=False):
            self.update_action_text = text
            if hasattr(self, "action_update"):
                self.action_update.setText(self.update_action_text)
                self.action_update.setEnabled(True)
                self.action_update.setCheckable(checkable)
                self.action_update.setChecked(checkable)
                if icon_pixmap:
                    self.action_update.setIcon(QApplication.style().standardIcon(icon_pixmap))
                else:
                    self.action_update.setIcon(QIcon())
        
        def on_update_ready(path):
            reset_action("Mise à jour prête !")
            if sys.platform != "win32":
                prompt_linux_update(path)
            else:
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Icon.Information)
                msg.setWindowTitle("Mise à jour prête")
                msg.setText("La mise à jour a été téléchargée.\nVoulez-vous redémarrer l'application pour l'appliquer maintenant ?")
                msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                if msg.exec() == QMessageBox.StandardButton.Yes:
                    import subprocess
                    subprocess.Popen([sys.executable] + sys.argv[1:])
                    QApplication.instance().quit()
                
        def on_no_update(msg):
            # Utilise la coche de validation native du menu (checkable=True) sans icône externe
            reset_action("À jour", checkable=True)
            
        def on_error(msg):
            # Affiche juste l'erreur dans le menu, sans popup bloquante
            reset_action("Erreur", QApplication.style().StandardPixmap.SP_MessageBoxWarning)
            
        self._manual_updater.update_ready_signal.connect(on_update_ready)
        self._manual_updater.no_update_signal.connect(on_no_update)
        self._manual_updater.error_signal.connect(on_error)
        self._manual_updater.start()

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
