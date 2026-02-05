import sys
import os
import django

# Initialize Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QStackedWidget, QFrame, QGraphicsDropShadowEffect
from PySide6.QtCore import Qt, QSize, QPointF
from PySide6.QtGui import QColor, QPainter, QRadialGradient, QBrush, QIcon, QPainterPath
import qtawesome as qta

from ui.dashboard import DashboardView
from ui.views import ProductsView, OrdersView, ShipmentsView, AccountsView
from ui.automation import AutomationView
from ui.settings import SettingsView
from core.scheduler import BackgroundWorker
from ui.theme_engine import AuraTheme, get_qss

class AuraWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AURAFLOW PRO")
        self.resize(1280, 850)
        
        # Default Theme
        self.current_theme = AuraTheme.DARK
        
        self.setAttribute(Qt.WA_TranslucentBackground)
        # Use native window frame to get standard close/minimize/maximize controls
        self.setWindowFlags(Qt.Window)
        
        self.central = QWidget()
        self.central.setObjectName("CentralWidget")
        self.setCentralWidget(self.central)
        
        self.main_layout = QHBoxLayout(self.central)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Sidebar
        self.sidebar = QWidget()
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setFixedWidth(280)
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(20, 50, 20, 50)
        sidebar_layout.setSpacing(5)
        
        logo_box = QHBoxLayout()
        logo_icon = QLabel()
        logo_icon.setPixmap(qta.icon("fa5s.tint", color="#00FFD1").pixmap(28, 28))
        self.logo_text = QLabel("AURAFLOW")
        self.logo_text.setObjectName("Logo")
        logo_box.addWidget(logo_icon)
        logo_box.addWidget(self.logo_text)
        logo_box.addStretch()
        sidebar_layout.addLayout(logo_box)
        sidebar_layout.addSpacing(30)

        # Native window controls are provided by the OS when using Qt.Window

        self.btn_dashboard = self._create_nav("Dashboard", "fa5s.th-large")
        self.btn_products = self._create_nav("Products", "fa5s.box")
        self.btn_orders = self._create_nav("Orders", "fa5s.receipt")
        self.btn_shipments = self._create_nav("Shipments", "fa5s.truck")
        self.btn_accounts = self._create_nav("Accounts", "fa5s.link")
        self.btn_automation = self._create_nav("Automation", "fa5s.robot")
        self.btn_settings = self._create_nav("Settings", "fa5s.cog")

        self.nav_btns = [
            self.btn_dashboard, self.btn_products, self.btn_orders,
            self.btn_shipments, self.btn_accounts, self.btn_automation, self.btn_settings
        ]
        
        for btn in self.nav_btns:
            sidebar_layout.addWidget(btn)
            btn.clicked.connect(self.handle_nav)

        sidebar_layout.addStretch()

        self.main_layout.addWidget(self.sidebar)

        # Content Stack
        self.content_stack = QStackedWidget()
        self.main_layout.addWidget(self.content_stack)

        # Views
        self.settings_view = SettingsView()
        self.settings_view.theme_changed.connect(self.update_theme) # Connect Theme Signal
        
        self.views = [
            DashboardView(), ProductsView(), OrdersView(), 
            ShipmentsView(), AccountsView(), AutomationView(), self.settings_view
        ]
        for v in self.views:
            self.content_stack.addWidget(v)

        # Initial View
        self.btn_dashboard.setChecked(True)
        self.content_stack.setCurrentIndex(0)

        # Apply Initial Theme
        self.setStyleSheet(get_qss(self.current_theme))
        self.refresh_nav_icons()
            
        self.worker = BackgroundWorker(interval=300)
        self.worker.start()

    def _create_nav(self, text, icon):
        btn = QPushButton(text)
        btn.setObjectName("SidebarButton")
        btn.setCheckable(True)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setProperty("icon_name", icon)
        btn.setIconSize(QSize(20, 20))
        return btn

    def handle_nav(self):
        source = self.sender()
        for i, btn in enumerate(self.nav_btns):
            is_active = (btn == source)
            btn.setChecked(is_active)
            if is_active:
                self.content_stack.setCurrentIndex(i)
        self.refresh_nav_icons()


    def update_theme(self, theme_name):
        self.current_theme = AuraTheme.LIGHT if theme_name == "Light Aura" else AuraTheme.DARK
        self.setStyleSheet(get_qss(self.current_theme))
        self.refresh_nav_icons()
        self.update() # Trigger repaint for Background

    def refresh_nav_icons(self):
        """Sync sidebar icon colors to the current theme and active state."""
        for btn in self.nav_btns:
            icon_name = btn.property("icon_name")
            if not icon_name:
                continue
            is_active = btn.isChecked()
            color = self.current_theme['text_primary'] if is_active else self.current_theme['text_secondary']
            btn.setIcon(qta.icon(icon_name, color=color))

    def paintEvent(self, event):
        painter = QPainter(self)
        try:
            painter.setRenderHint(QPainter.Antialiasing)
            rect = self.rect()
            path = QPainterPath()
            path.addRoundedRect(rect, 40, 40)
            painter.setClipPath(path)
            
            # Use Theme Base color
            painter.fillRect(rect, QColor(self.current_theme['bg_base']))
            
            # Dynamic Mesh Gradient based on theme
            opacity = self.current_theme['mesh_opacity']
            primary = QColor(self.current_theme['color_primary'])
            secondary = QColor(self.current_theme['color_secondary'])
            accent = QColor(self.current_theme['color_accent'])

            g1 = QRadialGradient(QPointF(0, 0), rect.width() * 1.4)
            g1.setColorAt(0, QColor(primary.red(), primary.green(), primary.blue(), opacity))
            g1.setColorAt(0.6, QColor(primary.red(), primary.green(), primary.blue(), int(opacity * 0.35)))
            g1.setColorAt(1, QColor(0, 0, 0, 0))
            painter.fillRect(rect, QBrush(g1))
            
            g2 = QRadialGradient(QPointF(rect.width(), rect.height()), rect.width() * 1.1)
            g2.setColorAt(0, QColor(secondary.red(), secondary.green(), secondary.blue(), max(0, opacity - 10)))
            g2.setColorAt(0.5, QColor(accent.red(), accent.green(), accent.blue(), max(0, opacity - 25)))
            g2.setColorAt(1, QColor(0, 0, 0, 0))
            painter.fillRect(rect, QBrush(g2))
        finally:
            painter.end()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_pos)
            event.accept()

    def closeEvent(self, event):
        self.worker.stop()
        self.worker.wait()
        event.accept()

def main():
    app = QApplication(sys.argv)
    window = AuraWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
