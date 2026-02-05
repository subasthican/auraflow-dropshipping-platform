from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton, QScrollArea
from PySide6.QtCore import Qt
from ui.views import apply_aura_shadow

class AutomationRuleCard(QFrame):
    def __init__(self, name, description, status, parent=None):
        super().__init__(parent)
        self.setObjectName("RuleCard")
        apply_aura_shadow(self, blur=30, alpha=15)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(12)
        
        header = QHBoxLayout()
        lbl_name = QLabel(name)
        lbl_name.setObjectName("SectionTitle")
        header.addWidget(lbl_name)
        header.addStretch()
        
        lbl_status = QLabel(status.upper())
        lbl_status.setObjectName("StatusLabel")
        lbl_status.setProperty("status", status)
        header.addWidget(lbl_status)
        layout.addLayout(header)
        
        lbl_desc = QLabel(description)
        lbl_desc.setObjectName("BodySecondary")
        lbl_desc.setStyleSheet("font-size: 14px;")
        lbl_desc.setWordWrap(True)
        layout.addWidget(lbl_desc)
        
        btn = QPushButton("CONFIGURE")
        btn.setObjectName("TableActionBtn")
        btn.setCursor(Qt.PointingHandCursor)
        layout.addSpacing(10)
        layout.addWidget(btn, 0, Qt.AlignRight)

class AutomationView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(40, 40, 40, 40)
        self.layout.setSpacing(30)
        
        title_box = QVBoxLayout()
        title = QLabel("Automation")
        title.setObjectName("PageTitle")
        title_box.addWidget(title)
        
        sub = QLabel("Orchestrate your AI-driven logistics and fulfillment pulses.")
        sub.setObjectName("BodySecondary")
        sub.setStyleSheet("font-size: 15px; margin-top: -10px;")
        title_box.addWidget(sub)
        self.layout.addLayout(title_box)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")
        
        content = QWidget()
        content.setStyleSheet("background: transparent;")
        grid = QVBoxLayout(content)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(20)
        
        rules = [
            ("Predictive Sourcing", "Automatically select the most reliable supplier based on historical delivery glass-data.", "Active"),
            ("Smart Fulfillment", "Route orders through low-risk shipping lanes and carriers.", "Active"),
            ("Inventory Pulse", "Real-time stock synchronization across global endpoints.", "Inactive")
        ]
        
        for name, desc, status in rules:
            grid.addWidget(AutomationRuleCard(name, desc, status))
            
        grid.addStretch()
        scroll.setWidget(content)
        self.layout.addWidget(scroll)
