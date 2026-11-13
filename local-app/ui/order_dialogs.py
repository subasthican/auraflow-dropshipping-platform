from decimal import Decimal
from typing import List, Tuple

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox, QCheckBox,
    QPushButton, QTableWidget, QTableWidgetItem, QWidget, QSpinBox, QHeaderView,
    QMessageBox
)
from PySide6.QtCore import Qt

from orders.models import CustomerOrder, OrderItem
from products.models import StoreProduct
from ui.toast import show_toast


class OrderCreateDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("New Order")
        self.setModal(True)
        self.setMinimumWidth(700)
        self.items: List[Tuple[StoreProduct, int]] = []
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        title = QLabel("Create Customer Order")
        title.setObjectName("SectionTitle")
        layout.addWidget(title)

        # Basic fields
        row = QHBoxLayout()
        self.edt_customer = QLineEdit()
        self.edt_customer.setPlaceholderText("Customer ID")
        row.addWidget(QLabel("Customer"))
        row.addWidget(self.edt_customer, 1)

        self.cmb_status = QComboBox()
        self.cmb_status.addItems(["pending", "processing", "shipped", "delivered", "cancelled"])
        row.addWidget(QLabel("Status"))
        row.addWidget(self.cmb_status)

        self.chk_paid = QCheckBox("Paid")
        row.addWidget(self.chk_paid)
        row.addStretch()
        layout.addLayout(row)

        # Item adder
        add_row = QHBoxLayout()
        self.cmb_product = QComboBox()
        products = list(StoreProduct.objects.all())
        self._product_map = {f"{p.title} (${p.selling_price:.2f})": p for p in products}
        self.cmb_product.addItems(list(self._product_map.keys()))
        add_row.addWidget(QLabel("Product"))
        add_row.addWidget(self.cmb_product, 1)

        self.spn_qty = QSpinBox()
        self.spn_qty.setRange(1, 1000)
        self.spn_qty.setValue(1)
        add_row.addWidget(QLabel("Qty"))
        add_row.addWidget(self.spn_qty)

        btn_add = QPushButton("Add Item")
        btn_add.setObjectName("TableActionBtn")
        btn_add.clicked.connect(self._handle_add_item)
        add_row.addWidget(btn_add)
        layout.addLayout(add_row)

        # Items table
        self.tbl_items = QTableWidget(0, 4)
        self.tbl_items.setHorizontalHeaderLabels(["Product", "Price", "Qty", "Remove"])
        self.tbl_items.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl_items.verticalHeader().setVisible(False)
        self.tbl_items.setShowGrid(False)
        layout.addWidget(self.tbl_items)

        # Total + actions
        footer = QHBoxLayout()
        self.lbl_total = QLabel("Total: $0.00")
        footer.addWidget(self.lbl_total)
        footer.addStretch()

        btn_ok = QPushButton("Create")
        btn_cancel = QPushButton("Cancel")
        btn_ok.setObjectName("GlowBtn")
        btn_cancel.clicked.connect(self.reject)
        btn_ok.clicked.connect(self._handle_create)
        footer.addWidget(btn_cancel)
        footer.addWidget(btn_ok)
        layout.addLayout(footer)

    def _handle_add_item(self):
        key = self.cmb_product.currentText()
        product = self._product_map.get(key)
        qty = int(self.spn_qty.value())
        if not product:
            return
        self.items.append((product, qty))
        self._refresh_items_table()

    def _refresh_items_table(self):
        self.tbl_items.setRowCount(len(self.items))
        for i, (p, qty) in enumerate(self.items):
            self.tbl_items.setItem(i, 0, QTableWidgetItem(p.title))
            self.tbl_items.setItem(i, 1, QTableWidgetItem(f"${p.selling_price:.2f}"))
            self.tbl_items.setItem(i, 2, QTableWidgetItem(str(qty)))
            btn = QPushButton("Remove")
            btn.setObjectName("TableActionBtn")
            btn.clicked.connect(lambda _=False, idx=i: self._remove_item(idx))
            self.tbl_items.setCellWidget(i, 3, btn)
        self._update_total()

    def _remove_item(self, idx: int):
        if 0 <= idx < len(self.items):
            self.items.pop(idx)
            self._refresh_items_table()

    def _update_total(self):
        total = sum(Decimal(str(p.selling_price)) * qty for p, qty in self.items)
        self.lbl_total.setText(f"Total: ${total:.2f}")

    def _handle_create(self):
        customer_id = self.edt_customer.text().strip()
        if not customer_id:
            QMessageBox.warning(self, "Validation", "Customer ID is required.")
            self.edt_customer.setFocus()
            return
        if not self.items:
            QMessageBox.warning(self, "Validation", "Add at least one item.")
            return
        try:
            total = sum(Decimal(str(p.selling_price)) * qty for p, qty in self.items)
            order = CustomerOrder.objects.create(
                customer_id=customer_id,
                total_amount=total,
                status=self.cmb_status.currentText(),
                payment_status=self.chk_paid.isChecked(),
            )
            for p, qty in self.items:
                OrderItem.objects.create(
                    order=order,
                    store_product=p,
                    quantity=qty,
                    selling_price=Decimal(str(p.selling_price)),
                )
            show_toast(f"Order #{order.id} created", parent=self, toast_type="success")
            self.accept()
        except Exception as e:
            show_toast(f"Error: {e}", parent=self, toast_type="error")


class OrderDetailDialog(QDialog):
    def __init__(self, order_id: int, parent=None, on_refresh=None, read_only: bool = False):
        super().__init__(parent)
        from orders.models import CustomerOrder
        self.order = CustomerOrder.objects.get(id=order_id)
        self.on_refresh = on_refresh
        self.read_only = read_only
        self.setWindowTitle(f"Order #{self.order.id}")
        self.setModal(True)
        self.setMinimumWidth(720)
        self.items: List[Tuple[StoreProduct, int]] = []
        self._build_ui()
        self._load_order()
        if self.read_only:
            self._set_read_only_state(True)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        header = QLabel("View / Edit Order")
        header.setObjectName("SectionTitle")
        layout.addWidget(header)

        # Supplier order status / action
        so_row = QHBoxLayout()
        self.lbl_supplier_order = QLabel("")
        self.btn_create_supplier_order = QPushButton("Create Supplier Order")
        self.btn_create_supplier_order.setObjectName("TableActionBtn")
        self.btn_create_supplier_order.clicked.connect(self._handle_create_supplier_order)
        so_row.addWidget(self.lbl_supplier_order, 1)
        so_row.addWidget(self.btn_create_supplier_order)
        layout.addLayout(so_row)

        row = QHBoxLayout()
        self.edt_customer = QLineEdit()
        row.addWidget(QLabel("Customer"))
        row.addWidget(self.edt_customer, 1)

        self.cmb_status = QComboBox()
        self.cmb_status.addItems(["pending", "processing", "shipped", "delivered", "cancelled"])
        row.addWidget(QLabel("Status"))
        row.addWidget(self.cmb_status)

        self.chk_paid = QCheckBox("Paid")
        row.addWidget(self.chk_paid)
        row.addStretch()
        layout.addLayout(row)

        # Item editor
        add_row = QHBoxLayout()
        self.cmb_product = QComboBox()
        products = list(StoreProduct.objects.all())
        self._product_map = {f"{p.title} (${p.selling_price:.2f})": p for p in products}
        self.cmb_product.addItems(list(self._product_map.keys()))
        add_row.addWidget(QLabel("Product"))
        add_row.addWidget(self.cmb_product, 1)

        self.spn_qty = QSpinBox()
        self.spn_qty.setRange(1, 1000)
        self.spn_qty.setValue(1)
        add_row.addWidget(QLabel("Qty"))
        add_row.addWidget(self.spn_qty)

        btn_add = QPushButton("Add Item")
        btn_add.setObjectName("TableActionBtn")
        btn_add.clicked.connect(self._handle_add_item)
        add_row.addWidget(btn_add)
        layout.addLayout(add_row)

        self.tbl_items = QTableWidget(0, 5)
        self.tbl_items.setHorizontalHeaderLabels(["Product", "Price", "Qty", "Remove", "ID"])  # ID hidden
        self.tbl_items.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl_items.verticalHeader().setVisible(False)
        self.tbl_items.setShowGrid(False)
        layout.addWidget(self.tbl_items)

        footer = QHBoxLayout()
        self.lbl_total = QLabel("Total: $0.00")
        footer.addWidget(self.lbl_total)
        footer.addStretch()

        btn_save = QPushButton("Save Changes")
        btn_delete = QPushButton("Delete Order")
        btn_close = QPushButton("Close")
        btn_save.setObjectName("GlowBtn")
        btn_delete.setStyleSheet("background-color:#dc2626; color:white; border:1px solid #dc2626; border-radius:8px; padding:6px; font-weight:600;")
        btn_save.clicked.connect(self._handle_save)
        btn_delete.clicked.connect(self._handle_delete)
        btn_close.clicked.connect(self.reject)
        footer.addWidget(btn_close)
        footer.addWidget(btn_delete)
        footer.addWidget(btn_save)
        layout.addLayout(footer)

        # Store references for read-only toggling
        self._btn_save = btn_save
        self._btn_delete = btn_delete
        self._add_row_widget_refs = {
            "cmb_product": self.cmb_product,
            "spn_qty": self.spn_qty,
        }

    def _load_order(self):
        self.edt_customer.setText(self.order.customer_id)
        self.cmb_status.setCurrentText(self.order.status)
        self.chk_paid.setChecked(bool(self.order.payment_status))
        # Load items
        from orders.models import OrderItem
        self.items = []
        for it in OrderItem.objects.filter(order=self.order):
            p = it.store_product
            qty = int(it.quantity)
            if p:
                self.items.append((p, qty))
        self._refresh_items_table()
        self._refresh_supplier_order()

    def _handle_add_item(self):
        key = self.cmb_product.currentText()
        product = self._product_map.get(key)
        qty = int(self.spn_qty.value())
        if not product:
            return
        self.items.append((product, qty))
        self._refresh_items_table()

    def _refresh_items_table(self):
        self.tbl_items.setRowCount(len(self.items))
        for i, (p, qty) in enumerate(self.items):
            self.tbl_items.setItem(i, 0, QTableWidgetItem(p.title))
            self.tbl_items.setItem(i, 1, QTableWidgetItem(f"${p.selling_price:.2f}"))
            self.tbl_items.setItem(i, 2, QTableWidgetItem(str(qty)))
            btn = QPushButton("Remove")
            btn.setObjectName("TableActionBtn")
            btn.clicked.connect(lambda _=False, idx=i: self._remove_item(idx))
            self.tbl_items.setCellWidget(i, 3, btn)
            self.tbl_items.setItem(i, 4, QTableWidgetItem(""))
        self._update_total()

    def _remove_item(self, idx: int):
        if 0 <= idx < len(self.items):
            self.items.pop(idx)
            self._refresh_items_table()

    def _update_total(self):
        total = sum(Decimal(str(p.selling_price)) * qty for p, qty in self.items)
        self.lbl_total.setText(f"Total: ${total:.2f}")

    def _handle_save(self):
        try:
            if self.read_only:
                return
            customer_id = self.edt_customer.text().strip()
            if not customer_id:
                QMessageBox.warning(self, "Validation", "Customer ID is required.")
                return
            self.order.customer_id = customer_id
            self.order.status = self.cmb_status.currentText()
            self.order.payment_status = self.chk_paid.isChecked()
            self.order.total_amount = sum(Decimal(str(p.selling_price)) * qty for p, qty in self.items)
            self.order.save()

            # Replace items for simplicity
            from orders.models import OrderItem
            OrderItem.objects.filter(order=self.order).delete()
            for p, qty in self.items:
                OrderItem.objects.create(
                    order=self.order,
                    store_product=p,
                    quantity=qty,
                    selling_price=Decimal(str(p.selling_price)),
                )
            show_toast("Order updated", parent=self, toast_type="success")
            if self.on_refresh:
                self.on_refresh()
            self.accept()
        except Exception as e:
            show_toast(f"Error: {e}", parent=self, toast_type="error")

    def _handle_delete(self):
        if self.read_only:
            return
        reply = QMessageBox.question(self, "Confirm", "Delete this order?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                self.order.delete()
                show_toast("Order deleted", parent=self, toast_type="success")
                if self.on_refresh:
                    self.on_refresh()
                self.accept()
            except Exception as e:
                show_toast(f"Error: {e}", parent=self, toast_type="error")

    def _set_read_only_state(self, enabled: bool):
        self.edt_customer.setReadOnly(enabled)
        self.cmb_status.setEnabled(not enabled)
        self.chk_paid.setEnabled(not enabled)
        # Disable add item controls
        self.cmb_product.setEnabled(not enabled)
        self.spn_qty.setEnabled(not enabled)
        # Hide save/delete when read-only
        self._btn_save.setVisible(not enabled)
        self._btn_delete.setVisible(not enabled)
        # Disable remove buttons in items table
        rows = self.tbl_items.rowCount()
        for i in range(rows):
            w = self.tbl_items.cellWidget(i, 3)
            if w:
                w.setEnabled(not enabled)

    def _refresh_supplier_order(self):
        try:
            from orders.models import SupplierOrder
            so = getattr(self.order, 'supplier_order', None)
            if so is None:
                self.lbl_supplier_order.setText("No supplier order linked")
                self.btn_create_supplier_order.setVisible(not self.read_only)
            else:
                txt = f"Supplier Order: {so.supplier_order_reference or '(ref pending)'} | Status: {so.order_status}"
                self.lbl_supplier_order.setText(txt)
                self.btn_create_supplier_order.setVisible(False)
        except Exception:
            self.lbl_supplier_order.setText("No supplier order linked")
            self.btn_create_supplier_order.setVisible(not self.read_only)

    def _handle_create_supplier_order(self):
        if self.read_only:
            return
        try:
            from orders.models import SupplierOrder
            so = getattr(self.order, 'supplier_order', None)
            if so is not None:
                QMessageBox.information(self, "Info", "Supplier order already exists.")
                return
            so = SupplierOrder.objects.create(customer_order=self.order)
            show_toast("Supplier order created", parent=self, toast_type="success")
            self._refresh_supplier_order()
        except Exception as e:
            show_toast(f"Error: {e}", parent=self, toast_type="error")
