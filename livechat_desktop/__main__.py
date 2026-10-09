import sys
import os
import builtins

if os.environ.get("LIVECHAT_DEBUG") != "1":
    builtins.print = lambda *args, **kwargs: None
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon

# Obligatoire pour garantir que Wayland ne capture pas l'overlay et laisse passer les clics
# Obligatoire pour garantir que Wayland ne capture pas l'overlay et laisse passer les clics (uniquement sur Linux)
if sys.platform.startswith('linux'):
    os.environ['QT_QPA_PLATFORM'] = 'xcb'

from livechat_desktop.socket_manager import SocketManager
from livechat_desktop.overlay import Overlay
from livechat_desktop.tray import TrayManager
from livechat_desktop.updater import UpdaterThread, apply_windows_update, prompt_linux_update

# Garder une référence globale au thread pour éviter le garbage collection
updater_thread = None



def register_custom_protocol():
    """Enregistre le protocole electron-app:// pour capter le retour Discord sur Windows et Linux."""
    if sys.platform == "win32":
        try:
            import winreg
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\electron-app")
            winreg.SetValue(key, "", winreg.REG_SZ, "URL:Electron App Protocol")
            winreg.SetValueEx(key, "URL Protocol", 0, winreg.REG_SZ, "")
            
            command_key = winreg.CreateKey(key, r"shell\open\command")
            winreg.SetValue(command_key, "", winreg.REG_SZ, f'"{sys.executable}" "%1"')
        except Exception as e:
            pass
    elif sys.platform.startswith("linux"):
        try:
            import os
            desktop_file = os.path.expanduser("~/.local/share/applications/livechat-desktop-handler.desktop")
            os.makedirs(os.path.dirname(desktop_file), exist_ok=True)
            with open(desktop_file, "w") as f:
                f.write(f"[Desktop Entry]\nName=LiveChat Protocol Handler\nExec={sys.executable} %U\nType=Application\nTerminal=false\nMimeType=x-scheme-handler/electron-app;\n")
            import subprocess
            subprocess.run(["xdg-mime", "default", "livechat-desktop-handler.desktop", "x-scheme-handler/electron-app"], check=False)
        except:
            pass

def handle_protocol_args():
    """Si l'app est lancée via electron-app://, on sauvegarde l'ID et on prévient l'utilisateur."""
    if len(sys.argv) > 1 and sys.argv[1].startswith("electron-app://auth/?id="):
        try:
            user_id = sys.argv[1].split("=")[-1].strip("/")
            from livechat_desktop.config import config_manager
            config_manager.set_user_id(user_id)
            
            from PyQt6.QtWidgets import QApplication, QMessageBox
            app = QApplication(sys.argv)
            msg = QMessageBox()
            msg.setWindowTitle("Connexion réussie")
            msg.setText("Connexion validée !\nVeuillez fermer cette fenêtre, puis QUITTER et RELANCER LiveChat depuis la barre des tâches pour appliquer la connexion.")
            msg.exec()
            sys.exit(0)
        except Exception as e:
            sys.exit(1)

# ----- INJECTION -----
handle_protocol_args()
register_custom_protocol()

def main():
    app = QApplication(sys.argv)
    
    # Configuration de l'icône globale de l'application
    icon_path = os.path.join(os.path.dirname(__file__), 'assets', 'icons', 'wilson_maillard.png')
    app.setWindowIcon(QIcon(icon_path))
    
    # Initialisation des différents modules de l'infrastructure
    overlay = Overlay()
    socket_manager = SocketManager()
    tray_manager = TrayManager(app.style(), socket_manager, overlay)
    
    # Connexion des signaux (Events)
    socket_manager.media_signal.connect(overlay.handle_media)
    socket_manager.stop_signal.connect(overlay.hide_all)
    socket_manager.guilds_updated_signal.connect(tray_manager.update_menu)
    
    # Application de la mise à jour Windows si présente (renommage et redémarrage)
    apply_windows_update()
    
    # Démarrage du thread réseau
    socket_manager.start()
    
    # Lancement de la vérification des mises à jour en arrière-plan
    global updater_thread
    updater_thread = UpdaterThread()
    updater_thread.update_ready_signal.connect(lambda path: prompt_linux_update(path) if sys.platform != "win32" else None)
    updater_thread.start()

    
    # Lancement de la boucle d'événements Qt
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
