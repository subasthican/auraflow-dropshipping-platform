from pathlib import Path
import json
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QLabel,
    QFrame,
)
from PySide6.QtCore import Qt, QUrl
from PySide6.QtWebEngineWidgets import QWebEngineView


class BrowserDialog(QDialog):
    """Lightweight in-app browser with bookmarks."""

    def __init__(self, start_url: str = "https://www.ebay.com", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Browser")
        self.resize(1100, 750)

        self.start_url = start_url
        self.bookmark_path = (
            Path(__file__).resolve().parent.parent / "ApplicationData" / "browser_bookmarks.json"
        )
        self.bookmarks = []

        self._load_bookmarks()
        self._build_ui()
        self.load_url(self.start_url)

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(10)

        # Top nav bar
        nav = QHBoxLayout()
        nav.setSpacing(8)

        self.btn_back = QPushButton("←")
        self.btn_back.setFixedWidth(36)
        self.btn_back.clicked.connect(self.on_back)
        nav.addWidget(self.btn_back)

        self.btn_forward = QPushButton("→")
        self.btn_forward.setFixedWidth(36)
        self.btn_forward.clicked.connect(self.on_forward)
        nav.addWidget(self.btn_forward)

        self.btn_reload = QPushButton("Reload")
        self.btn_reload.clicked.connect(self.on_reload)
        nav.addWidget(self.btn_reload)

        self.txt_url = QLineEdit()
        self.txt_url.setPlaceholderText("Enter URL (https://...)")
        self.txt_url.returnPressed.connect(self.on_go)
        nav.addWidget(self.txt_url, stretch=1)

        self.btn_go = QPushButton("Go")
        self.btn_go.setObjectName("GlowBtn")
        self.btn_go.clicked.connect(self.on_go)
        nav.addWidget(self.btn_go)

        self.btn_add = QPushButton("☆ Add Bookmark")
        self.btn_add.clicked.connect(self.on_add_bookmark)
        nav.addWidget(self.btn_add)

        root.addLayout(nav)

        # Main area with bookmarks panel + web view
        body = QHBoxLayout()
        body.setSpacing(10)

        self.bookmark_panel = QFrame()
        self.bookmark_panel.setObjectName("ContentCard")
        self.bookmark_panel.setFixedWidth(260)
        panel_layout = QVBoxLayout(self.bookmark_panel)
        panel_layout.setContentsMargins(10, 10, 10, 10)
        panel_layout.setSpacing(8)

        lbl_bm = QLabel("Bookmarks")
        lbl_bm.setObjectName("SectionTitle")
        panel_layout.addWidget(lbl_bm)

        self.list_bookmarks = QListWidget()
        self.list_bookmarks.itemDoubleClicked.connect(self.on_open_bookmark)
        panel_layout.addWidget(self.list_bookmarks, stretch=1)

        btns_row = QHBoxLayout()
        btns_row.setSpacing(6)
        self.btn_open = QPushButton("Open")
        self.btn_open.clicked.connect(self.on_open_selected)
        btns_row.addWidget(self.btn_open)

        self.btn_remove = QPushButton("Remove")
        self.btn_remove.clicked.connect(self.on_remove_bookmark)
        btns_row.addWidget(self.btn_remove)

        panel_layout.addLayout(btns_row)

        body.addWidget(self.bookmark_panel)

        self.web_view = QWebEngineView()
        self.web_view.urlChanged.connect(self._sync_url_bar)
        body.addWidget(self.web_view, stretch=1)

        root.addLayout(body, stretch=1)

        self._populate_bookmarks()

    def _normalize_url(self, raw: str) -> str:
        text = raw.strip()
        if not text:
            return ""
        if not text.startswith("http://") and not text.startswith("https://"):
            text = "https://" + text
        return text

    def load_url(self, raw_url: str):
        url = self._normalize_url(raw_url)
        if url:
            self.web_view.load(QUrl(url))
            self.txt_url.setText(url)

    def on_back(self):
        if self.web_view.history().canGoBack():
            self.web_view.back()

    def on_forward(self):
        if self.web_view.history().canGoForward():
            self.web_view.forward()

    def on_reload(self):
        self.web_view.reload()

    def on_go(self):
        self.load_url(self.txt_url.text())

    def on_add_bookmark(self):
        current_url = self.web_view.url().toString() or self.txt_url.text()
        url = self._normalize_url(current_url)
        if not url:
            return
        title = url
        # Avoid duplicates
        if any(bm.get("url") == url for bm in self.bookmarks):
            return
        self.bookmarks.append({"title": title, "url": url})
        self._save_bookmarks()
        self._populate_bookmarks()

    def on_open_bookmark(self, item: QListWidgetItem):
        url = item.data(Qt.UserRole)
        if url:
            self.load_url(url)

    def on_open_selected(self):
        item = self.list_bookmarks.currentItem()
        if item:
            self.on_open_bookmark(item)

    def on_remove_bookmark(self):
        item = self.list_bookmarks.currentItem()
        if not item:
            return
        url = item.data(Qt.UserRole)
        self.bookmarks = [bm for bm in self.bookmarks if bm.get("url") != url]
        self._save_bookmarks()
        self._populate_bookmarks()

    def _sync_url_bar(self, qurl: QUrl):
        self.txt_url.setText(qurl.toString())

    def _populate_bookmarks(self):
        self.list_bookmarks.clear()
        for bm in self.bookmarks:
            item = QListWidgetItem(bm.get("title") or bm.get("url"))
            item.setData(Qt.UserRole, bm.get("url"))
            self.list_bookmarks.addItem(item)

    def _load_bookmarks(self):
        try:
            self.bookmark_path.parent.mkdir(parents=True, exist_ok=True)
            if self.bookmark_path.exists():
                with self.bookmark_path.open("r", encoding="utf-8") as fh:
                    self.bookmarks = json.load(fh)
            else:
                self.bookmarks = [
                    {"title": "eBay", "url": "https://www.ebay.com"},
                    {"title": "Google", "url": "https://www.google.com"},
                ]
                self._save_bookmarks()
        except Exception:
            self.bookmarks = []

    def _save_bookmarks(self):
        try:
            self.bookmark_path.parent.mkdir(parents=True, exist_ok=True)
            with self.bookmark_path.open("w", encoding="utf-8") as fh:
                json.dump(self.bookmarks, fh, indent=2)
        except Exception:
            pass
