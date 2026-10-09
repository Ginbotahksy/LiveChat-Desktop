import os
import sys
import requests
import subprocess
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import QMessageBox

GITHUB_API_URL = "https://api.github.com/repos/Ginbotahksy/LiveChat-Desktop/releases/latest"
CURRENT_VERSION = "1.0.4"

class UpdaterThread(QThread):
    update_ready_signal = pyqtSignal(str) # Emits the path to the downloaded update
    no_update_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, manual=False):
        super().__init__()
        self.manual = manual

    def run(self):
        try:
            # 1. Vérifier la dernière version sur GitHub
            response = requests.get(GITHUB_API_URL, timeout=10)
            response.raise_for_status()
            data = response.json()
            latest_version = data.get("tag_name", "").lstrip("v")
            
            if not latest_version:
                if self.manual: self.error_signal.emit("Impossible de déterminer la dernière version.")
                return

            if latest_version <= CURRENT_VERSION:
                # Déjà à jour
                if self.manual: self.no_update_signal.emit(f"Vous êtes déjà à jour (version {CURRENT_VERSION}).")
                return

            # 2. Chercher l'asset correspondant à la plateforme
            is_windows = sys.platform == "win32"
            target_asset = None
            
            for asset in data.get("assets", []):
                name = asset.get("name", "")
                if is_windows and name.endswith(".exe"):
                    target_asset = asset
                    break
                elif not is_windows and name.endswith(".deb"):
                    target_asset = asset
                    break
            
            if not target_asset:
                if self.manual: self.error_signal.emit("Aucun fichier d'installation trouvé pour votre système.")
                return
                
            download_url = target_asset.get("browser_download_url")
            
            # 3. Télécharger le fichier
            if is_windows:
                # Sur Windows, on le télécharge à côté de l'exécutable courant
                current_exe = sys.executable
                if getattr(sys, 'frozen', False):
                    base_dir = os.path.dirname(current_exe)
                    download_path = os.path.join(base_dir, "livechat-desktop-update.exe")
                else:
                    if self.manual: self.error_signal.emit("Mise à jour impossible en mode non compilé.")
                    return # Pas en mode compilé, on ne met pas à jour le code source
            else:
                # Sur Linux, on le télécharge dans /tmp
                download_path = f"/tmp/livechat-desktop_{latest_version}_amd64.deb"

            # Si le fichier existe déjà (ex: déjà téléchargé lors d'un lancement précédent)
            if os.path.exists(download_path):
                self.update_ready_signal.emit(download_path)
                return

            print(f"Téléchargement de la mise à jour {latest_version} depuis {download_url}...")
            dl_resp = requests.get(download_url, stream=True, timeout=15)
            dl_resp.raise_for_status()
            
            with open(download_path, 'wb') as f:
                for chunk in dl_resp.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print("Mise à jour téléchargée avec succès.")
            self.update_ready_signal.emit(download_path)

        except Exception as e:
            print(f"Erreur lors de la mise à jour: {e}")
            if self.manual: self.error_signal.emit(f"Erreur lors de la vérification : {e}")

def apply_windows_update():
    """Vérifie si une mise à jour est en attente d'installation sur Windows."""
    if sys.platform != "win32" or not getattr(sys, 'frozen', False):
        return

    current_exe = sys.executable
    base_dir = os.path.dirname(current_exe)
    update_exe = os.path.join(base_dir, "livechat-desktop-update.exe")
    old_exe = current_exe + ".old"

    # Nettoyage d'une ancienne version supprimée
    if os.path.exists(old_exe):
        try:
            os.remove(old_exe)
        except:
            pass

    # Application de la mise à jour
    if os.path.exists(update_exe):
        try:
            # On renomme le binaire actuellement en cours d'exécution
            os.rename(current_exe, old_exe)
            # On remplace par le nouveau
            os.rename(update_exe, current_exe)
            # On relance la nouvelle version
            subprocess.Popen([current_exe])
            # On quitte l'ancienne
            sys.exit(0)
        except Exception as e:
            print(f"Impossible d'appliquer la mise à jour Windows: {e}")

def prompt_linux_update(deb_path):
    """Affiche une popup pour installer la mise à jour Linux via pkexec."""
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Icon.Information)
    msg.setWindowTitle("Mise à jour disponible")
    msg.setText("Une nouvelle version de LiveChat Desktop a été téléchargée en arrière-plan.\n\nVoulez-vous l'installer maintenant ?\n(Votre mot de passe administrateur vous sera demandé)")
    msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
    
    if msg.exec() == QMessageBox.StandardButton.Yes:
        try:
            # pkexec ouvre nativement une fenêtre de mot de passe sous Linux/GNOME/KDE
            subprocess.Popen(["pkexec", "dpkg", "-i", deb_path])
        except Exception as e:
            print(f"Erreur d'installation: {e}")
