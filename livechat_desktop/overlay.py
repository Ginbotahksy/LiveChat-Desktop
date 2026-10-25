import requests
from PyQt6.QtCore import Qt, QTimer, QUrl, QRect, QSize
from PyQt6.QtWidgets import QMainWindow, QLabel, QVBoxLayout, QWidget, QApplication
from PyQt6.QtGui import QPixmap, QFont, QFontMetrics
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineSettings
from livechat_desktop.providers import process_link

class Overlay(QMainWindow):
    # --- CONFIGURATION & CONSTANTS ---
    # Part de la zone utile de l'écran (hors barre des tâches) occupée par le bloc texte + média
    BOX_RATIO_DEFAULT = 0.80
    BOX_RATIO_FULLSCREEN = 1.0

    # Les textes ne peuvent pas dépasser cette part de la hauteur du bloc : au-delà on réduit la police
    MAX_TEXT_HEIGHT_SHARE = 0.45
    MIN_FONT_SIZE = 12
    FONT_SHRINK_STEP = 0.9
    MIN_MEDIA_HEIGHT = 100
    SPACING = 10

    DEFAULT_DURATION_BOT = 2000
    IMAGE_DOWNLOAD_TIMEOUT = 10

    TEXT_LEN_SHORT = 50
    TEXT_LEN_MED = 100
    TEXT_LEN_LONG = 200

    FONT_SCALE_SHORT = 0.02
    FONT_SCALE_MED = 0.018
    FONT_SCALE_LONG = 0.015
    FONT_SCALE_XLONG = 0.012

    DEFAULT_ASPECT_RATIO = 16 / 9

    def __init__(self):
        super().__init__()

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool |
            Qt.WindowType.WindowTransparentForInput
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Zone utile de l'écran : la barre des tâches est exclue par le système
        self.setGeometry(QApplication.primaryScreen().availableGeometry())

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(self.SPACING)

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.hide()

        self.top_text_label = QLabel()
        self.top_text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.top_text_label.setWordWrap(True)
        self.top_text_label.hide()

        self.bottom_text_label = QLabel()
        self.bottom_text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.bottom_text_label.setWordWrap(True)
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

        self.current_format = 'illustration'
        self.media_box = QSize(self.width(), self.height())

    # --- CALCUL DE LA MISE EN PAGE ---
    # Tout est calculé à partir de la taille de l'écran, sans dépendre de la taille
    # courante des widgets (qui est fausse tant que la fenêtre n'a pas été affichée).

    def _base_font_size(self, text, box_width):
        length = len(text)
        if length < self.TEXT_LEN_SHORT: fs_factor = self.FONT_SCALE_SHORT
        elif length < self.TEXT_LEN_MED: fs_factor = self.FONT_SCALE_MED
        elif length < self.TEXT_LEN_LONG: fs_factor = self.FONT_SCALE_LONG
        else: fs_factor = self.FONT_SCALE_XLONG
        return max(self.MIN_FONT_SIZE, int(box_width * fs_factor))

    def _measure_text(self, text, font_size, max_width):
        """Retourne la taille (QSize) exacte du label une fois le texte rendu avec ce style."""
        font = QFont(self.font())
        font.setPixelSize(font_size)
        font.setBold(True)
        padding = font_size // 3
        inner_width = max(1, max_width - 2 * padding)
        rect = QFontMetrics(font).boundingRect(
            QRect(0, 0, inner_width, 100000),
            int(Qt.AlignmentFlag.AlignCenter) | int(Qt.TextFlag.TextWordWrap),
            text,
        )
        # Petite marge pour éviter un retour à la ligne différent dû aux arrondis
        width = min(max_width, rect.width() + 2 * padding + 4)
        return QSize(width, rect.height() + 2 * padding)

    def _compute_layout(self, top_text, bottom_text):
        """
        Calcule le bloc maximal (80% ou 100% de la zone utile), la taille des textes,
        puis la place restante pour le média (stockée dans self.media_box).
        Retourne {texte: (font_size, QSize)} pour les textes présents.
        """
        ratio = self.BOX_RATIO_FULLSCREEN if self.current_format == 'fullscreen' else self.BOX_RATIO_DEFAULT
        box_w = int(self.width() * ratio)
        box_h = int(self.height() * ratio)

        texts = [t for t in (top_text, bottom_text) if t]
        font_sizes = {t: self._base_font_size(t, box_w) for t in texts}
        max_text_h = int(box_h * self.MAX_TEXT_HEIGHT_SHARE)

        # On réduit la police tant que les textes prennent trop de place
        while True:
            sizes = {t: self._measure_text(t, font_sizes[t], box_w) for t in texts}
            total_text_h = sum(s.height() for s in sizes.values())
            if total_text_h <= max_text_h or all(fs <= self.MIN_FONT_SIZE for fs in font_sizes.values()):
                break
            font_sizes = {t: max(self.MIN_FONT_SIZE, int(fs * self.FONT_SHRINK_STEP)) for t, fs in font_sizes.items()}

        media_h = box_h - total_text_h - self.SPACING * len(texts)
        self.media_box = QSize(box_w, max(self.MIN_MEDIA_HEIGHT, media_h))
        return {t: (font_sizes[t], sizes[t]) for t in texts}

    def _fit_in_media_box(self, width, height):
        """Plus grande taille qui tient dans la zone média en gardant le ratio."""
        if width <= 0 or height <= 0:
            width, height = self.DEFAULT_ASPECT_RATIO, 1
        return QSize(int(width * 1000), int(height * 1000)).scaled(self.media_box, Qt.AspectRatioMode.KeepAspectRatio)

    def _setup_label(self, label, text, font_size, size):
        padding = font_size // 3
        radius = font_size // 4
        label.setStyleSheet(f"color: white; font-size: {font_size}px; font-weight: bold; background-color: rgba(0,0,0,150); padding: {padding}px; border-radius: {radius}px;")
        label.setText(text)
        label.setFixedSize(size)
        label.show()

    @staticmethod
    def _clean_text(text):
        # Nettoyage des espaces multiples tout en conservant les sauts de ligne voulus
        if not text:
            return None
        return "\n".join(" ".join(line.split()) for line in text.splitlines()).strip() or None

    def on_video_size_changed(self, size=None):
        if size is None or not size.isValid():
            size = self.video_widget.videoSink().videoSize()
        if size.width() > 0 and size.height() > 0:
            self.video_widget.setFixedSize(self._fit_in_media_box(size.width(), size.height()))

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
            # Taille provisoire en 16:9, corrigée dès que la vraie taille de la vidéo est connue
            self.video_widget.setFixedSize(self._fit_in_media_box(self.DEFAULT_ASPECT_RATIO, 1))
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
        # Suit un éventuel changement de résolution / de barre des tâches
        self.setGeometry(QApplication.primaryScreen().availableGeometry())

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

        top_text = None
        bottom_text = text
        provider_result = {}

        # PROCESSEUR DE LIENS (Twitter, YouTube, TikTok...)
        self.current_js_injection = None
        if lien:
            provider_result = process_link(lien, data, (self.width(), self.height()))
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

        top_text = self._clean_text(top_text)
        bottom_text = self._clean_text(bottom_text)
        text_layout = self._compute_layout(top_text, bottom_text)
        print(f"DEBUG: Media box: {self.media_box.width()}x{self.media_box.height()}")

        if top_text:
            self._setup_label(self.top_text_label, top_text, *text_layout[top_text])
        if bottom_text:
            self._setup_label(self.bottom_text_label, bottom_text, *text_layout[bottom_text])

        if lien:
            embed_url = provider_result.get("embed_url", lien)
            web_size = provider_result.get("web_size")
            html = provider_result.get("html")

            if is_generic_web:
                # La page web générique prend toute la zone média
                self.web_view.setFixedSize(self.media_box)
            elif web_size:
                self.web_view.setFixedSize(self._fit_in_media_box(*web_size))
            else:
                self.web_view.setFixedSize(self._fit_in_media_box(self.DEFAULT_ASPECT_RATIO, 1))

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
                    resp = requests.get(url, timeout=self.IMAGE_DOWNLOAD_TIMEOUT)
                    if resp.status_code == 200:
                        pixmap = QPixmap()
                        pixmap.loadFromData(resp.content)
                        if not pixmap.isNull():
                            target = self._fit_in_media_box(pixmap.width(), pixmap.height())
                            self.image_label.setPixmap(pixmap.scaled(target, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                            self.image_label.show()
                        else:
                            print("Image illisible:", url)
                    else:
                        print(f"Image non téléchargée ({resp.status_code}):", url)
                except Exception as e:
                    print("Error image:", e)
            elif media_type in ('video', 'audio'):
                self.play_direct_video(url, duration)

        if not lien and media_type not in ('video', 'audio'):
            if duration:
                self.timer.start(duration)

        self.show()
