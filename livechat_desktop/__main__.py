import sys
import os
import builtins

if os.environ.get("LIVECHAT_DEBUG") != "1":
    builtins.print = lambda *args, **kwargs: None
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon

# Obligatoire pour garantir que Wayland ne capture pas l'overlay et laisse passer les clics
os.environ['QT_QPA_PLATFORM'] = 'xcb'

from livechat_desktop.socket_manager import SocketManager
from livechat_desktop.overlay import Overlay
from livechat_desktop.tray import TrayManager

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
    
    # Démarrage du thread réseau
    socket_manager.start()
    
    # Lancement de la boucle d'événements Qt
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
