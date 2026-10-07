import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from livechat_desktop.overlay import Overlay

app = QApplication(sys.argv)
overlay = Overlay()
# On affiche l'overlay normalement
overlay.show()

tests = [
    # 1. Fullscreen Image with Text
    {"url": "https://http.cat/200", "type": "image", "format": "fullscreen", "text": "Test 1: Image en Plein Écran (avec texte). L'image doit prendre tout l'espace moins ce texte.", "lien": None},
    
    # 2. Classic Image with Text
    {"url": "https://http.cat/200", "type": "image", "format": "illustration", "text": "Test 2: Image en mode Classique. Le bloc image + texte doit prendre 85% de l'écran.", "lien": None},
    
    # 3. Fullscreen Image NO Text
    {"url": "https://http.cat/404", "type": "image", "format": "fullscreen", "text": None, "lien": None},
    
    # 4. YouTube Classic
    {"url": None, "type": "video", "format": "illustration", "text": "Test 4: YouTube en mode Classique (vidéo + texte).", "lien": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
    
    # 5. Generic Web Fullscreen
    {"url": None, "type": "web", "format": "fullscreen", "text": "Test 5: Page Steam en Plein Écran. Doit laisser la place au texte.", "lien": "https://store.steampowered.com/app/2445980/GRebels/"},
]

current_test = 0

def run_next_test():
    global current_test
    if current_test < len(tests):
        print(f"\n--- Lancement Test {current_test+1} ---")
        try:
            overlay.handle_media(tests[current_test])
        except Exception as e:
            print(f"Exception: {e}")
        current_test += 1
        # On attend 7 secondes avant le prochain test pour laisser le temps de bien voir
        QTimer.singleShot(7000, run_next_test) 
    else:
        print("\nFin des tests. Fermeture dans 3s.")
        QTimer.singleShot(3000, app.quit)

# Démarrage du premier test après 1 seconde
QTimer.singleShot(1000, run_next_test)
app.exec()
