from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton, QLineEdit, QComboBox, QCheckBox, QScrollArea
from PySide6.QtCore import Qt, Signal
from ui.views import apply_aura_shadow

class SettingsView(QWidget):
    theme_changed = Signal(str) # Signal to notify MainWindow
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(40, 40, 40, 40)
        self.layout.setSpacing(30)
        
        title = QLabel("Settings")
        title.setObjectName("PageTitle")
        self.layout.addWidget(title)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")
        
        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: transparent;")
        self.scroll_layout = QVBoxLayout(scroll_content)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout.setSpacing(30)
        
        # 1. Appearance / Theme
        appearance_sec = QFrame()
        appearance_sec.setObjectName("ContentCard")
        apply_aura_shadow(appearance_sec)
        app_layout = QVBoxLayout(appearance_sec)
        app_layout.setContentsMargins(30,30,30,30)
        
        lbl_sec = QLabel("Interface Aesthetic")
        lbl_sec.setObjectName("SectionTitle")
        app_layout.addWidget(lbl_sec)
        
        theme_row = QHBoxLayout()
        theme_row.addWidget(QLabel("Platform Theme Mode"))
        theme_row.addStretch()
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark Aura", "Light Aura"])
        self.theme_combo.setFixedWidth(200)
        self.theme_combo.currentTextChanged.connect(self.on_theme_select)
        theme_row.addWidget(self.theme_combo)
        app_layout.addLayout(theme_row)
        
        self.scroll_layout.addWidget(appearance_sec)
        
        # 2. General Settings
        gen_sec = QFrame()
        gen_sec.setObjectName("ContentCard")
        apply_aura_shadow(gen_sec)
        gen_layout = QVBoxLayout(gen_sec)
        gen_layout.setContentsMargins(30,30,30,30)
        gen_layout.addWidget(QLabel("System Logic"))
        
        sync_row = QHBoxLayout()
        sync_row.addWidget(QLabel("Neural Sync Pulse"))
        sync_row.addStretch()
        sync_check = QCheckBox()
        sync_check.setChecked(True)
        sync_row.addWidget(sync_check)
        gen_layout.addLayout(sync_row)
        
        self.scroll_layout.addWidget(gen_sec)
        
        self.scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        self.layout.addWidget(scroll)

    def on_theme_select(self, theme_name):
        self.theme_changed.emit(theme_name)
