from datetime import datetime
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QTableWidget, QTableWidgetItem, QHeaderView, QGraphicsDropShadowEffect
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QColor
from analytics.services import get_sales_metrics
from products.models import StoreProduct

def apply_aura_shadow(widget, blur=30, alpha=20):
    sh = QGraphicsDropShadowEffect()
    sh.setBlurRadius(blur)
    sh.setXOffset(0)
    sh.setYOffset(12)
    sh.setColor(QColor(0, 0, 0, alpha))
    widget.setGraphicsEffect(sh)

class MetricCard(QFrame):
    def __init__(self, title, value, parent=None):
        super().__init__(parent)
        self.setObjectName("MetricCard")
        self.setFixedSize(260, 140)
        apply_aura_shadow(self)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(10)
        
        lbl_title = QLabel(title.upper())
        lbl_title.setObjectName("MetricLabel")
        
        lbl_value = QLabel(value)
        lbl_value.setObjectName("MetricValue")
        
        layout.addWidget(lbl_title)
        layout.addWidget(lbl_value)
        layout.addStretch()

class DashboardView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(40, 40, 40, 40) # Standardized margins
        self.layout.setSpacing(40)
        
        # Header
        header = QHBoxLayout()
        title_vbox = QVBoxLayout()
        title = QLabel("Overview")
        title.setObjectName("PageTitle")
        title_vbox.addWidget(title)
        
        self.lbl_status = QLabel(f"● PULSE ACTIVE • {datetime.now().strftime('%H:%M:%S')}")
        self.lbl_status.setStyleSheet("color: #00FFD1; font-weight: 800; font-size: 11px; letter-spacing: 1.5px;")
        title_vbox.addWidget(self.lbl_status)
        header.addLayout(title_vbox)
        header.addStretch()
        self.layout.addLayout(header)
        
        # Metric Grid
        self.metrics_container = QWidget()
        self.metrics_layout = QHBoxLayout(self.metrics_container)
        self.metrics_layout.setContentsMargins(0, 0, 0, 0)
        self.metrics_layout.setSpacing(24)
        self.layout.addWidget(self.metrics_container)
        
        # Content Section
        self.content_container = QWidget()
        self.content_layout = QVBoxLayout(self.content_container)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(30)
        self.layout.addWidget(self.content_container)
        
        self.refresh_data()

    def refresh_data(self):
        sales = get_sales_metrics()
        active_count = StoreProduct.objects.filter(status='active').count()
        
        for i in reversed(range(self.metrics_layout.count())): 
            item = self.metrics_layout.itemAt(i).widget()
            if item: item.setParent(None)
            
        self.metrics_layout.addWidget(MetricCard("Revenue", f"${sales['total_revenue']:,.2f}"))
        self.metrics_layout.addWidget(MetricCard("Orders", f"{sales['order_count']:,}"))
        self.metrics_layout.addWidget(MetricCard("SKUs", f"{active_count}"))
        self.metrics_layout.addStretch()

        for i in reversed(range(self.content_layout.count())):
            item = self.content_layout.itemAt(i).widget()
            if item: item.setParent(None)
            
        self.add_table_card("Trending Performance", sales['best_sellers'], ["Entity", "Volume"], ["store_product__title", "total_sold"])

    def add_table_card(self, title_text, data, headers, fields):
        card = QFrame()
        card.setObjectName("ContentCard")
        apply_aura_shadow(card)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(30, 30, 30, 30)
        
        title = QLabel(title_text)
        title.setObjectName("SectionTitle")
        card_layout.addWidget(title)
        
        if not data:
            empty = QLabel("Pulse sync in progress...")
            empty.setStyleSheet("color: rgba(255, 255, 255, 100); padding: 20px 0;")
            card_layout.addWidget(empty)
        else:
            table = QTableWidget(len(data), len(headers))
            table.setHorizontalHeaderLabels(headers)
            table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            table.verticalHeader().setVisible(False)
            table.setShowGrid(False)
            table.setFixedHeight(240)
            table.setEditTriggers(QTableWidget.NoEditTriggers)
            
            for i, item in enumerate(data):
                for j, field in enumerate(fields):
                    table.setItem(i, j, QTableWidgetItem(str(item[field])))
            card_layout.addWidget(table)
        self.content_layout.addWidget(card)
