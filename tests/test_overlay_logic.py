import sys
from PyQt6.QtWidgets import QApplication
from livechat_desktop.overlay import Overlay

app = QApplication(sys.argv)
o = Overlay()
data = {'url': None, 'type': 'image', 'format': 'illustration', 'duration': 2000, 'text': 'dfrge', 'lien': 'https://store.steampowered.com/app/2445980/GRebels/'}
# We just want to see the prints up to Processed duration
o.hide_all = lambda: None
o.show = lambda: None
o.timer.start = lambda d: print(f"Timer started with {d}")
try:
    o.handle_media(data)
except Exception as e:
    print(e)
