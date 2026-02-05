from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QProgressBar
from PySide6.QtCore import QUrl, Qt
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEnginePage
import logging

logger = logging.getLogger(__name__)


class EbayOAuthDialog(QDialog):
    def __init__(self, auth_url: str, redirect_uri: str, parent=None):
        super().__init__(parent)
        self.redirect_uri = redirect_uri
        self.auth_code = None
        self.setWindowTitle("Connect to eBay")
        self.setModal(True)
        self.resize(900, 700)
        self._build_ui(auth_url)

    def _build_ui(self, auth_url: str):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Info bar
        info_bar = QLabel("Sign in to eBay to connect your account")
        info_bar.setObjectName("InfoBar")
        info_bar.setStyleSheet(
            "background: #3b82f6; color: white; padding: 12px; font-size: 13px; font-weight: 600;"
        )
        info_bar.setAlignment(Qt.AlignCenter)
        layout.addWidget(info_bar)

        # Progress bar (hidden until loading)
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)  # Indeterminate
        self.progress.setMaximumHeight(3)
        self.progress.setTextVisible(False)
        self.progress.hide()
        layout.addWidget(self.progress)

        # Web view
        self.web_view = QWebEngineView()
        self.web_view.setPage(CustomWebPage(self))
        self.web_view.page().urlChanged.connect(self._on_url_changed)
        self.web_view.loadStarted.connect(lambda: self.progress.show())
        self.web_view.loadFinished.connect(lambda: self.progress.hide())
        layout.addWidget(self.web_view)

        # Cancel button
        btn_cancel = QPushButton("Cancel")
        btn_cancel.setObjectName("TableActionBtn")
        btn_cancel.clicked.connect(self.reject)
        btn_cancel.setMaximumWidth(100)
        btn_cancel.setStyleSheet("margin: 10px;")
        layout.addWidget(btn_cancel, alignment=Qt.AlignRight)

        # Load eBay OAuth page
        self.web_view.load(QUrl(auth_url))

    def _on_url_changed(self, url: QUrl):
        """Intercept redirect callback with authorization code."""
        url_str = url.toString()
        logger.info(f"URL changed: {url_str}")
        
        if url_str.startswith(self.redirect_uri):
            # Parse query parameters
            query = url.query()
            params = dict(item.split("=") for item in query.split("&") if "=" in item)
            
            if "code" in params:
                self.auth_code = params["code"]
                logger.info(f"Authorization code received: {self.auth_code[:10]}...")
                self.accept()
            elif "error" in params:
                error_desc = params.get("error_description", params["error"])
                logger.error(f"OAuth error: {error_desc}")
                self.reject()


class CustomWebPage(QWebEnginePage):
    """Custom page to handle navigation and console messages."""
    
    def javaScriptConsoleMessage(self, level, message, lineNumber, sourceID):
        """Log JavaScript console messages for debugging."""
        logger.debug(f"JS Console [{level}]: {message}")
