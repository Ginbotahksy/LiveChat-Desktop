import re
import requests
from PyQt6.QtCore import Qt, QTimer, QUrl
from PyQt6.QtWidgets import QMainWindow, QLabel, QVBoxLayout, QWidget, QApplication
from PyQt6.QtGui import QPixmap
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineSettings
from livechat_desktop.providers import process_link

class Overlay(QMainWindow):
    # --- CONFIGURATION & CONSTANTS ---
    MAX_WIDTH_RATIO = 0.85
    MEDIA_SCALE_WITH_TEXT = 0.70
    MEDIA_SCALE_NO_TEXT = 0.85
    
    DEFAULT_DURATION_BOT = 2000
    
    TEXT_LEN_SHORT = 50
    TEXT_LEN_MED = 100
    TEXT_LEN_LONG = 200
    
    FONT_SCALE_SHORT = 0.02
    FONT_SCALE_MED = 0.018
    FONT_SCALE_LONG = 0.015
    FONT_SCALE_XLONG = 0.012
    
    DEFAULT_WEB_WIDTH = 1280
    DEFAULT_WEB_HEIGHT = 720
    
    BOTTOM_MARGIN = 120 # Remonte le contenu pour ne pas chevaucher la barre des tâches

    def __init__(self):
        super().__init__()
        
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool |
            Qt.WindowType.WindowTransparentForInput
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        screen = QApplication.primaryScreen().geometry()
        self.setGeometry(screen)
        
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.setContentsMargins(0, 0, 0, self.BOTTOM_MARGIN)
        
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.hide()
        
        self.top_text_label = QLabel()
        self.top_text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.top_text_label.hide()
        
        self.bottom_text_label = QLabel()
        self.bottom_text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.bottom_text_label.hide()
        
        self.video_widget = QVideoWidget()
        self.video_widget.videoSink().videoSizeChanged.connect(self.on_video_size_changed)
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        self.media_player.setVideoOutput(self.video_widget)
        self.video_widget.hide()
        
        # Le navigateur intégré (remplace l'iframe de l'ancien client)
        self.web_view = QWebEngineView()
        self.web_view.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.web_view.page().setBackgroundColor(Qt.GlobalColor.transparent)
        # Autoriser l'autoplay des vidéos sans interaction utilisateur
        self.web_view.settings().setAttribute(QWebEngineSettings.WebAttribute.PlaybackRequiresUserGesture, False)
        self.web_view.hide()
        self.web_view.loadFinished.connect(self.on_web_load_finished)
        self.web_view.titleChanged.connect(self.on_title_changed)
        
        self.layout.addWidget(self.top_text_label, alignment=Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.image_label, alignment=Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.video_widget, alignment=Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.web_view, alignment=Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.bottom_text_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.hide_all)

    def _get_text_height(self):
        h = 0
        if not self.top_text_label.isHidden():
            h += self.top_text_label.height() + self.layout.spacing()
        if not self.bottom_text_label.isHidden():
            h += self.bottom_text_label.height() + self.layout.spacing()
        return h

    def _get_media_max_height(self, has_text):
        is_fullscreen = getattr(self, 'current_format', 'illustration') == 'fullscreen'
        
        if is_fullscreen:
            base_h = self.height() - getattr(self, 'current_bottom_margin', 0)
        else:
            base_h = int(self.height() * self.MAX_WIDTH_RATIO) # 85% de l'écran
            
        if has_text:
            return max(100, base_h - self._get_text_height() - 20)
        return base_h

    def on_video_size_changed(self, size=None):
        if size is None or not size.isValid():
            size = self.video_widget.videoSink().videoSize()
        if size.width() > 0 and size.height() > 0:
            scale_factor = getattr(self, 'media_scale_factor', self.MEDIA_SCALE_NO_TEXT)
            has_text = scale_factor != self.MEDIA_SCALE_NO_TEXT
            
            is_fullscreen = getattr(self, 'current_format', 'illustration') == 'fullscreen'
            if is_fullscreen:
                max_w = self.width()
            else:
                max_w = int(self.width() * self.MAX_WIDTH_RATIO)
                
            max_h = self._get_media_max_height(has_text)
                
            scaled = size.scaled(max_w, max_h, Qt.AspectRatioMode.KeepAspectRatio)
            self.video_widget.setFixedSize(scaled)

    def on_title_changed(self, title):
        if title == "VIDEO_ENDED":
            self.hide_all()

    def on_web_load_finished(self, ok):
        if not ok: return
        js_code = getattr(self, 'current_js_injection', None)
        if js_code:
            self.web_view.page().runJavaScript(js_code)



    def hide_all(self):
        self.timer.stop()
        self.image_label.hide()
        self.video_widget.hide()
        self.top_text_label.hide()
        self.bottom_text_label.hide()
        self.web_view.hide()
        self.web_view.setUrl(QUrl("about:blank"))
        self.media_player.stop()
        try:
            self.media_player.mediaStatusChanged.disconnect(self.on_media_status_changed)
        except:
            pass
        self.hide()

    def play_direct_video(self, direct_url, duration=None):
        try:
            self.media_player.setSource(QUrl(direct_url))
            self.video_widget.show()
            self.media_player.play()
            if duration:
                self.timer.start(duration)
            else:
                self.media_player.mediaStatusChanged.connect(self.on_media_status_changed)
        except Exception as e:
            print("Erreur lecteur vidéo:", e)
            
    def on_media_status_changed(self, status):
        print(f"DEBUG: Media status changed to {status}")
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            print("DEBUG: EndOfMedia reached, hiding all.")
            self.hide_all()
            try:
                self.media_player.mediaStatusChanged.disconnect(self.on_media_status_changed)
            except:
                pass

    def handle_media(self, data):
        print(f"DEBUG: Media received: {data}")
        self.hide_all()
        
        url = data.get('url')
        lien = data.get('lien')
        text = data.get('text')
        media_type = data.get('type')
        duration_raw = data.get('duration')
        try:
            duration = int(duration_raw) if duration_raw is not None else None
        except ValueError:
            duration = None
        self.current_format = data.get('format', 'illustration')
        
        if self.current_format == 'fullscreen':
            self.current_bottom_margin = 0
            self.layout.setContentsMargins(0, 0, 0, 0)
        else:
            self.current_bottom_margin = self.BOTTOM_MARGIN
            self.layout.setContentsMargins(0, 0, 0, self.BOTTOM_MARGIN)
        
        top_text = None
        bottom_text = text
        provider_result = {}
        
        # PROCESSEUR DE LIENS (Twitter, YouTube, TikTok...)
        self.current_js_injection = None
        if lien:
            usable_window_size = (self.width(), self.height() - self.current_bottom_margin)
            provider_result = process_link(lien, data, usable_window_size)
            self.current_js_injection = provider_result.get("js_injection")
            
            # Application des modifs de données (ex: Twitter convertit le lien en url direct media)
            if "url" in provider_result: url = provider_result["url"]
            if "type" in provider_result: media_type = provider_result["type"]
            if "lien" in provider_result: lien = provider_result["lien"]
            if "top_text" in provider_result: top_text = provider_result["top_text"]

        # --- WORKAROUND ---
        # Le bot distant (sur iceboxer) envoie par défaut duration=2000 si non précisé.
        # On l'ignore pour les vidéos et les liens pour les laisser se terminer naturellement.
        # SAUF pour les pages web génériques où on laisse le timer s'appliquer.
        is_generic_web = provider_result.get("is_generic_web", False)
        
        # Si c'est une page web générique, on s'assure qu'il y a un timer
        if is_generic_web and not duration:
            duration = self.DEFAULT_DURATION_BOT
            
        if ((lien and not is_generic_web) or media_type in ('video', 'audio')) and duration == self.DEFAULT_DURATION_BOT:
            duration = None
            
        print(f"DEBUG: Processed duration is: {duration}")
        
        has_text = bool(top_text or bottom_text)
        self.media_scale_factor = self.MEDIA_SCALE_WITH_TEXT if has_text else self.MEDIA_SCALE_NO_TEXT
        if self.current_format == 'fullscreen':
            # Protection contre la barre des tâches si on a du texte en bas
            self.current_bottom_margin = 60 if bottom_text else 0
            self.layout.setContentsMargins(0, 0, 0, self.current_bottom_margin)
        
        def setup_label(label, t):
            if not t: return
            
            # Nettoyage des espaces multiples tout en conservant les sauts de ligne voulus
            t = "\n".join(" ".join(line.split()) for line in t.splitlines()).strip()
            
            length = len(t)
            # Base text sizes on screen width for perfect scaling
            if length < self.TEXT_LEN_SHORT: fs_factor = self.FONT_SCALE_SHORT
            elif length < self.TEXT_LEN_MED: fs_factor = self.FONT_SCALE_MED
            elif length < self.TEXT_LEN_LONG: fs_factor = self.FONT_SCALE_LONG
            else: fs_factor = self.FONT_SCALE_XLONG
            
            font_size = int(self.width() * fs_factor)
            padding = int(font_size / 3)
            radius = int(font_size / 4)
            
            label.setStyleSheet(f"color: white; font-size: {font_size}px; font-weight: bold; background-color: rgba(0,0,0,150); padding: {padding}px; border-radius: {radius}px;")
            label.setWordWrap(True)
            label.setMaximumWidth(int(self.width() * self.MAX_WIDTH_RATIO))
            label.setText(t)
            label.adjustSize() # Ensure it calculates its own bounds AFTER text is set
            label.setMinimumHeight(label.sizeHint().height())
            label.show()

        setup_label(self.top_text_label, top_text)
        setup_label(self.bottom_text_label, bottom_text)
            
        if lien:
            embed_url = provider_result.get("embed_url", lien)
            web_size = provider_result.get("web_size")
            html = provider_result.get("html")
            
            if web_size:
                max_h = self._get_media_max_height(has_text)
                is_fullscreen = self.current_format == 'fullscreen'
                target_w = self.width() if is_fullscreen else int(self.width() * self.MAX_WIDTH_RATIO)
                
                if provider_result.get("is_generic_web", False):
                    # La page web générique prend tout l'espace ciblé
                    self.web_view.setFixedSize(target_w, max_h)
                else:
                    if web_size[1] > 0:
                        ratio = web_size[0] / web_size[1]
                        if abs(web_size[0] - self.width()) < 10: 
                            self.web_view.setFixedSize(target_w, max_h)
                        else:
                            new_w = int(max_h * ratio)
                            # S'assurer de ne pas dépasser la largeur cible
                            if new_w > target_w:
                                new_w = target_w
                                max_h = int(new_w / ratio)
                            self.web_view.setFixedSize(new_w, max_h)
                    else:
                        self.web_view.setFixedSize(target_w, max_h)
            else:
                self.web_view.setFixedSize(self.DEFAULT_WEB_WIDTH, self.DEFAULT_WEB_HEIGHT)
                
            if html:
                self.web_view.setHtml(html, QUrl("http://localhost"))
            else:
                self.web_view.setUrl(QUrl(embed_url))
                
            self.web_view.show()
            if duration:
                self.timer.start(duration)
            
        elif url:
            if media_type == 'image':
                try:
                    resp = requests.get(url)
                    if resp.status_code == 200:
                        pixmap = QPixmap()
                        pixmap.loadFromData(resp.content)
                        scale_factor = getattr(self, 'media_scale_factor', self.MEDIA_SCALE_NO_TEXT)
                        has_text = scale_factor != self.MEDIA_SCALE_NO_TEXT
                        max_h = self._get_media_max_height(has_text)
                        
                        is_fullscreen = self.current_format == 'fullscreen'
                        target_w = self.width() if is_fullscreen else int(self.width() * self.MAX_WIDTH_RATIO)
                        
                        scaled_pix = pixmap.scaled(target_w, max_h, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                        self.image_label.setPixmap(scaled_pix)
                        self.image_label.show()
                except Exception as e:
                    print("Error image:", e)
            elif media_type in ('video', 'audio'):
                self.play_direct_video(url, duration)
        
        if not lien and media_type not in ('video', 'audio'):
            if duration:
                self.timer.start(duration)
            elif media_type == 'image' or text:
                pass
            
        self.show()
