from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox,
    QPushButton, QMessageBox
)
from PySide6.QtCore import Qt

from shipments.models import Shipment
from orders.models import SupplierOrder
from shipments.ml.predictor import predictor
from ui.toast import show_toast


class ShipmentCreateDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("New Shipment")
        self.setModal(True)
        self.setMinimumWidth(600)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        title = QLabel("Create Shipment")
        title.setObjectName("SectionTitle")
        layout.addWidget(title)

        row = QHBoxLayout()
        self.cmb_supplier_order = QComboBox()
        self._so_map = {}
        for so in SupplierOrder.objects.all():
            key = f"Order #{so.customer_order.id}"
            self._so_map[key] = so
            self.cmb_supplier_order.addItem(key)
        row.addWidget(QLabel("Supplier Order"))
        row.addWidget(self.cmb_supplier_order, 1)

        layout.addLayout(row)

        row2 = QHBoxLayout()
        self.edt_courier = QLineEdit()
        row2.addWidget(QLabel("Courier"))
        row2.addWidget(self.edt_courier, 1)

        self.edt_tracking = QLineEdit()
        row2.addWidget(QLabel("Tracking"))
        row2.addWidget(self.edt_tracking, 1)
        layout.addLayout(row2)

        row3 = QHBoxLayout()
        self.cmb_status = QComboBox()
        self.cmb_status.addItems(["pending", "in_transit", "out_for_delivery", "delivered", "returned", "delayed"])
        row3.addWidget(QLabel("Status"))
        row3.addWidget(self.cmb_status)
        layout.addLayout(row3)

        footer = QHBoxLayout()
        btn_cancel = QPushButton("Cancel")
        btn_ok = QPushButton("Create")
        btn_ok.setObjectName("GlowBtn")
        btn_cancel.clicked.connect(self.reject)
        btn_ok.clicked.connect(self._handle_create)
        footer.addStretch()
        footer.addWidget(btn_cancel)
        footer.addWidget(btn_ok)
        layout.addLayout(footer)

    def _handle_create(self):
        if self.cmb_supplier_order.count() == 0:
            QMessageBox.warning(self, "Validation", "No supplier orders available.")
            return
        courier = self.edt_courier.text().strip()
        tracking = self.edt_tracking.text().strip()
        if not courier or not tracking:
            QMessageBox.warning(self, "Validation", "Courier and tracking are required.")
            return
        try:
            so = self._so_map.get(self.cmb_supplier_order.currentText())
            Shipment.objects.create(
                supplier_order=so,
                courier_name=courier,
                tracking_number=tracking,
                shipment_status=self.cmb_status.currentText(),
            )
            show_toast("Shipment created", parent=self, toast_type="success")
            self.accept()
        except Exception as e:
            show_toast(f"Error: {e}", parent=self, toast_type="error")


class ShipmentDetailDialog(QDialog):
    def __init__(self, shipment_id: int, parent=None, on_refresh=None):
        super().__init__(parent)
        self.shipment = Shipment.objects.get(id=shipment_id)
        self.on_refresh = on_refresh
        self.setWindowTitle(f"Shipment {self.shipment.tracking_number}")
        self.setModal(True)
        self.setMinimumWidth(600)
        self._build_ui()
        self._load()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        title = QLabel("View / Edit Shipment")
        title.setObjectName("SectionTitle")
        layout.addWidget(title)

        row = QHBoxLayout()
        self.edt_courier = QLineEdit()
        row.addWidget(QLabel("Courier"))
        row.addWidget(self.edt_courier, 1)

        self.edt_tracking = QLineEdit()
        row.addWidget(QLabel("Tracking"))
        row.addWidget(self.edt_tracking, 1)
        layout.addLayout(row)

        row2 = QHBoxLayout()
        self.cmb_status = QComboBox()
        self.cmb_status.addItems(["pending", "in_transit", "out_for_delivery", "delivered", "returned", "delayed"])
        row2.addWidget(QLabel("Status"))
        row2.addWidget(self.cmb_status)
        layout.addLayout(row2)

        # Risk info
        risk_row = QHBoxLayout()
        self.lbl_risk = QLabel("Risk: --%  |  Delay: -- days")
        self.lbl_risk.setStyleSheet("color:#6b7280;")
        risk_row.addWidget(self.lbl_risk)
        risk_row.addStretch()
        layout.addLayout(risk_row)

        footer = QHBoxLayout()
        btn_refresh_risk = QPushButton("Refresh Risk")
        btn_close = QPushButton("Close")
        btn_delete = QPushButton("Delete")
        btn_save = QPushButton("Save")
        btn_save.setObjectName("GlowBtn")
        btn_delete.setStyleSheet("background-color:#dc2626; color:white; border:1px solid #dc2626; border-radius:8px; padding:6px; font-weight:600;")
        btn_refresh_risk.clicked.connect(self._handle_refresh_risk)
        btn_close.clicked.connect(self.reject)
        btn_delete.clicked.connect(self._handle_delete)
        btn_save.clicked.connect(self._handle_save)
        footer.addStretch()
        footer.addWidget(btn_refresh_risk)
        footer.addWidget(btn_close)
        footer.addWidget(btn_delete)
        footer.addWidget(btn_save)
        layout.addLayout(footer)

    def _load(self):
        self.edt_courier.setText(self.shipment.courier_name)
        self.edt_tracking.setText(self.shipment.tracking_number)
        self.cmb_status.setCurrentText(self.shipment.shipment_status)
        self._update_risk_label()

    def _handle_save(self):
        try:
            self.shipment.courier_name = self.edt_courier.text().strip()
            self.shipment.tracking_number = self.edt_tracking.text().strip()
            self.shipment.shipment_status = self.cmb_status.currentText()
            self.shipment.save()
            if self.on_refresh:
                self.on_refresh()
            show_toast("Shipment updated", parent=self, toast_type="success")
            self.accept()
        except Exception as e:
            show_toast(f"Error: {e}", parent=self, toast_type="error")

    def _update_risk_label(self):
        prob = float(self.shipment.delay_probability or 0.0) * 100.0
        days = int(self.shipment.expected_delay_days or 0)
        self.lbl_risk.setText(f"Risk: {prob:.1f}%  |  Delay: {days} days")

    def _handle_refresh_risk(self):
        try:
            features = {
                "supplier_rating": 4.2,
                "estimated_delivery_days": 10,
                "historical_supplier_delay_rate": 0.15,
            }
            prob, days = predictor.predict(features)
            self.shipment.delay_probability = float(prob)
            self.shipment.expected_delay_days = int(days)
            self.shipment.save()
            self._update_risk_label()
            if self.on_refresh:
                self.on_refresh()
            show_toast("Risk scores refreshed", parent=self, toast_type="success")
        except Exception as e:
            show_toast(f"Error: {e}", parent=self, toast_type="error")

    def _handle_delete(self):
        from PySide6.QtWidgets import QMessageBox
        reply = QMessageBox.question(self, "Confirm", "Delete this shipment?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                self.shipment.delete()
                if self.on_refresh:
                    self.on_refresh()
                show_toast("Shipment deleted", parent=self, toast_type="success")
                self.accept()
            except Exception as e:
                show_toast(f"Error: {e}", parent=self, toast_type="error")
