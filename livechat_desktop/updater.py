import os
import sys
import tempfile
import requests
import subprocess
from PyQt6.QtCore import QThread, QProcess, pyqtSignal
from PyQt6.QtWidgets import QMessageBox, QApplication

GITHUB_RELEASES_URL = "https://api.github.com/repos/Ginbotahksy/LiveChat-Desktop/releases"
# Seule source de la version : pyproject.toml la lit ici et la CI vérifie qu'elle correspond au tag
CURRENT_VERSION = "1.0.7"

IS_FROZEN = getattr(sys, 'frozen', False)
WINDOWS_UPDATE_NAME = "livechat-desktop-update.exe"


def parse_version(text):
    """'v1.0.10' -> (1, 0, 10). None si ce n'est pas un numéro de version (ex: tag 'vBox')."""
    try:
        return tuple(int(part) for part in text.strip().lstrip("vV").split("."))
    except (AttributeError, ValueError):
        return None


def restart_app():
    """Relance l'application dans un nouveau processus indépendant."""
    env = os.environ.copy()
    # Sans ça, le nouvel exe PyInstaller réutilise le dossier temporaire de l'ancien,
    # qui est supprimé quand l'ancien se ferme -> le nouveau plante au démarrage
    env["PYINSTALLER_RESET_ENVIRONMENT"] = "1"
    subprocess.Popen([sys.executable], env=env)


class UpdaterThread(QThread):
    update_ready_signal = pyqtSignal(str) # Emits the path to the downloaded update
    no_update_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int) # Pourcentage du téléchargement

    def __init__(self, manual=False):
        super().__init__()
        self.manual = manual

    def _latest_release(self):
        """Release publiée avec le plus grand numéro de version (ignore les tags du type 'vBox')."""
        response = requests.get(GITHUB_RELEASES_URL, params={"per_page": 30}, timeout=10)
        response.raise_for_status()
        releases = [
            r for r in response.json()
            if not r.get("draft") and not r.get("prerelease") and parse_version(r.get("tag_name", ""))
        ]
        if not releases:
            return None
        return max(releases, key=lambda r: parse_version(r["tag_name"]))

    def run(self):
        try:
            # 0. Seuls les exécutables compilés (.exe Windows, .deb Linux) savent se mettre à jour
            is_windows = sys.platform == "win32"
            is_linux = sys.platform.startswith("linux")
            if not IS_FROZEN or not (is_windows or is_linux):
                if self.manual: self.error_signal.emit("Mise à jour automatique indisponible hors version installée (pip/sources : pip install -U livechat-desktop).")
                return

            # 1. Vérifier la dernière version sur GitHub
            release = self._latest_release()
            if not release:
                if self.manual: self.error_signal.emit("Impossible de déterminer la dernière version.")
                return

            latest_version = release["tag_name"].lstrip("vV")
            if parse_version(latest_version) <= parse_version(CURRENT_VERSION):
                # Déjà à jour
                if self.manual: self.no_update_signal.emit(f"Vous êtes déjà à jour (version {CURRENT_VERSION}).")
                return

            # 2. Chercher l'asset correspondant à la plateforme
            extension = ".exe" if is_windows else ".deb"
            target_asset = next((a for a in release.get("assets", []) if a.get("name", "").endswith(extension)), None)
            if not target_asset:
                if self.manual: self.error_signal.emit("Aucun fichier d'installation trouvé pour votre système.")
                return

            download_url = target_asset.get("browser_download_url")
            expected_size = target_asset.get("size")

            # 3. Télécharger le fichier
            if is_windows:
                # Sur Windows, à côté de l'exécutable courant pour pouvoir le remplacer par simple renommage
                download_path = os.path.join(os.path.dirname(sys.executable), WINDOWS_UPDATE_NAME)
            else:
                download_path = os.path.join(tempfile.gettempdir(), f"livechat-desktop_{latest_version}_amd64.deb")

            # Déjà téléchargé lors d'un lancement précédent ? On ne le garde que s'il est complet
            if os.path.exists(download_path):
                if os.path.getsize(download_path) == expected_size:
                    self.update_ready_signal.emit(download_path)
                    return
                os.remove(download_path)

            print(f"Téléchargement de la mise à jour {latest_version} depuis {download_url}...")
            # On écrit dans un .part puis on renomme : un téléchargement coupé ne laisse jamais
            # un fichier incomplet qui serait pris pour une mise à jour prête
            part_path = download_path + ".part"
            with requests.get(download_url, stream=True, timeout=30) as dl_resp:
                dl_resp.raise_for_status()
                total = int(dl_resp.headers.get("content-length") or expected_size or 0)
                received = 0
                last_percent = -1
                with open(part_path, 'wb') as f:
                    for chunk in dl_resp.iter_content(chunk_size=1024 * 256):
                        f.write(chunk)
                        received += len(chunk)
                        if total:
                            percent = received * 100 // total
                            if percent != last_percent:
                                last_percent = percent
                                self.progress_signal.emit(percent)

            if expected_size and os.path.getsize(part_path) != expected_size:
                os.remove(part_path)
                raise IOError("téléchargement incomplet")

            os.replace(part_path, download_path)
            print("Mise à jour téléchargée avec succès.")
            self.update_ready_signal.emit(download_path)

        except Exception as e:
            print(f"Erreur lors de la mise à jour: {e}")
            if self.manual: self.error_signal.emit(f"Erreur lors de la vérification : {e}")

def apply_windows_update():
    """Vérifie si une mise à jour est en attente d'installation sur Windows."""
    if sys.platform != "win32" or not IS_FROZEN:
        return

    current_exe = sys.executable
    base_dir = os.path.dirname(current_exe)
    update_exe = os.path.join(base_dir, WINDOWS_UPDATE_NAME)
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
            # On renomme le binaire actuellement en cours d'exécution (Windows l'autorise, pas la suppression)
            os.rename(current_exe, old_exe)
        except Exception as e:
            print(f"Impossible d'appliquer la mise à jour Windows: {e}")
            return
        try:
            # On remplace par le nouveau
            os.rename(update_exe, current_exe)
        except Exception as e:
            print(f"Impossible d'appliquer la mise à jour Windows: {e}")
            # On remet l'ancien exe en place pour ne pas se retrouver sans application
            os.rename(old_exe, current_exe)
            return
        # On relance la nouvelle version et on quitte l'ancienne
        restart_app()
        sys.exit(0)

# Référence globale : sinon le QProcess est détruit (et pkexec tué) dès la fin de la fonction
_install_process = None

def prompt_linux_update(deb_path):
    """Affiche une popup pour installer la mise à jour Linux via pkexec, puis relance l'application."""
    global _install_process
    if _install_process is not None:
        return  # Une installation est déjà en cours (vérification auto + manuelle en même temps)

    msg = QMessageBox()
    msg.setIcon(QMessageBox.Icon.Information)
    msg.setWindowTitle("Mise à jour disponible")
    msg.setText("Une nouvelle version de LiveChat Desktop a été téléchargée en arrière-plan.\n\nVoulez-vous l'installer maintenant ?\n(Votre mot de passe administrateur vous sera demandé)")
    msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
    if msg.exec() != QMessageBox.StandardButton.Yes:
        return

    def on_finished(exit_code, _status):
        global _install_process
        _install_process = None
        if exit_code == 0:
            try:
                os.remove(deb_path)
            except OSError:
                pass
            QMessageBox.information(None, "Mise à jour installée", "La mise à jour est installée, LiveChat va redémarrer.")
            restart_app()
            QApplication.instance().quit()
        elif exit_code != 126:  # 126 = l'utilisateur a annulé la demande de mot de passe
            QMessageBox.warning(None, "Échec de la mise à jour", f"L'installation a échoué (code {exit_code}).")

    # QProcess plutôt que subprocess : on est prévenu de la fin de l'installation sans bloquer l'interface
    # pkexec ouvre nativement une fenêtre de mot de passe sous Linux/GNOME/KDE
    def on_error(error):
        global _install_process
        if error == QProcess.ProcessError.FailedToStart:
            _install_process = None
            QMessageBox.warning(None, "Échec de la mise à jour", f"pkexec introuvable, installez la mise à jour à la main :\nsudo dpkg -i {deb_path}")

    _install_process = QProcess()
    _install_process.finished.connect(on_finished)
    _install_process.errorOccurred.connect(on_error)
    _install_process.start("pkexec", ["dpkg", "-i", deb_path])
