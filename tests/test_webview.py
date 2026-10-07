import sys
from PyQt6.QtCore import QTimer, QUrl, Qt
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtWebEngineWidgets import QWebEngineView

class Overlay(QMainWindow):
    def __init__(self):
        super().__init__()
        self.web_view = QWebEngineView(self)
        self.setCentralWidget(self.web_view)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.hide_all)
        self.web_view.loadFinished.connect(self.on_load)
        
    def hide_all(self):
        print("HIDE ALL CALLED")
        self.timer.stop()
        self.web_view.hide()
        self.web_view.setUrl(QUrl("about:blank"))
        self.hide()
        QApplication.quit()

    def show_url(self, url):
        print("SHOW URL CALLED")
        self.web_view.setUrl(QUrl(url))
        self.web_view.show()
        self.show()
        self.timer.start(2000)
        
    def on_load(self, ok):
        print("LOAD FINISHED", ok)

app = QApplication(sys.argv)
o = Overlay()
o.show_url("https://wikipedia.org")
sys.exit(app.exec())
