from pathlib import Path
import json
import shutil
import uuid
import zipfile
from PIL import Image
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QTableWidget, QTableWidgetItem, QHeaderView, QGraphicsDropShadowEffect, QPushButton, QStackedWidget, QMessageBox, QDialog, QLineEdit, QComboBox, QFileDialog
from PySide6.QtGui import QColor, QPixmap
from PySide6.QtCore import Qt
import qtawesome as qta
from django.conf import settings
from products.models import StoreProduct
from orders.models import CustomerOrder
from shipments.models import Shipment
from core.models import MarketplaceAccount
from ui.dialogs import ProductCreateDialog
from ui.product_detail_dialog import ProductDetailDialog, PhotoDownloadDialog
from ui.order_dialogs import OrderCreateDialog, OrderDetailDialog
from ui.shipment_dialogs import ShipmentCreateDialog, ShipmentDetailDialog
from ui.publish_dialog import PublishDialog
from ui.oauth_dialog import EbayOAuthDialog
from ui.browser_dialog import BrowserDialog
from ui.toast import show_toast

def apply_aura_shadow(widget, blur=35, alpha=20):
    sh = QGraphicsDropShadowEffect()
    sh.setBlurRadius(blur)
    sh.setXOffset(0)
    sh.setYOffset(12)
    sh.setColor(QColor(0, 0, 0, alpha))
    widget.setGraphicsEffect(sh)

class EmptyStateWidget(QFrame):
    def __init__(self, title, description, parent=None):
        super().__init__(parent)
        self.setObjectName("ContentCard")
        apply_aura_shadow(self)
        self.setMinimumHeight(280)
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(20)
        layout.setContentsMargins(40, 40, 40, 40)
        
        # Icon (circle with gradient look)
        icon_label = QLabel("∘")
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("font-size: 64px; color: #cbd5e1; font-weight: 300;")
        layout.addWidget(icon_label)
        
        lbl_title = QLabel(title)
        lbl_title.setObjectName("SectionTitle")
        lbl_title.setAlignment(Qt.AlignCenter)
        
        lbl_desc = QLabel(description)
        lbl_desc.setObjectName("BodySecondary")
        lbl_desc.setStyleSheet("font-size: 14px; color: #64748b; line-height: 1.6;")
        lbl_desc.setAlignment(Qt.AlignCenter)
        lbl_desc.setWordWrap(True)
        
        layout.addWidget(lbl_title)
        layout.addWidget(lbl_desc)
        layout.addStretch()

class BaseDataView(QWidget):
    def __init__(self, title_text, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(40, 40, 40, 40)
        self.layout.setSpacing(30)
        
        self.header_layout = QHBoxLayout()
        title = QLabel(title_text)
        title.setObjectName("PageTitle")
        self.header_layout.addWidget(title)
        self.header_layout.addStretch()
        
        self.add_btn = QPushButton(f"New {title_text[:-1]}")
        self.add_btn.setObjectName("GlowBtn")
        self.add_btn.clicked.connect(self.on_add_clicked)
        self.header_layout.addWidget(self.add_btn)
        self.layout.addLayout(self.header_layout)
        
        self.container = QStackedWidget()
        self.layout.addWidget(self.container)
        
        self.card = QFrame()
        self.card.setObjectName("ContentCard")
        apply_aura_shadow(self.card)
        self.card_layout = QVBoxLayout(self.card)
        self.card_layout.setContentsMargins(20, 20, 20, 20)
        
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.card_layout.addWidget(self.table)
        
        self.empty_state = EmptyStateWidget(f"No {title_text} Detected", f"Synchronize your platform states to visualize live {title_text.lower()}.")
        
        self.container.addWidget(self.card)
        self.container.addWidget(self.empty_state)

    def check_data(self, count):
        self.container.setCurrentIndex(1 if count == 0 else 0)

    def on_add_clicked(self):
        QMessageBox.information(self, "Action", "This action is not implemented yet.")

class ProductsView(BaseDataView):
    def __init__(self, parent=None):
        super().__init__("Products", parent)
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels(["Image", "Title", "Category", "Price", "Status", "View", "Download", "Edit", "Publish", "Delete"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.load_products()

    def load_products(self):
        import json
        products = list(StoreProduct.objects.all())
        self.check_data(len(products))
        self.table.setRowCount(len(products))
        for i, p in enumerate(products):
            # Image preview with count
            img_container = QWidget()
            img_layout = QVBoxLayout(img_container)
            img_layout.setContentsMargins(5, 5, 5, 5)
            
            img_label = QLabel()
            img_label.setAlignment(Qt.AlignCenter)
            if p.image_path and Path(p.image_path).exists():
                pixmap = QPixmap(p.image_path).scaledToHeight(50, Qt.SmoothTransformation)
                img_label.setPixmap(pixmap)
            else:
                img_label.setText("No Image")
                img_label.setStyleSheet("color: #6b7280; font-size: 12px;")
            img_layout.addWidget(img_label)
            
            # Count additional images
            additional_count = 0
            if p.additional_images:
                try:
                    additional_list = json.loads(p.additional_images)
                    additional_count = len(additional_list) if isinstance(additional_list, list) else 0
                except:
                    additional_count = 0
            
            total_images = 1 if p.image_path else 0
            total_images += additional_count
            
            img_count = QLabel(f"{total_images} image{'s' if total_images != 1 else ''}")
            img_count.setAlignment(Qt.AlignCenter)
            img_count.setStyleSheet("color: #6b7280; font-size: 11px; margin-top: 4px;")
            img_layout.addWidget(img_count)
            
            self.table.setCellWidget(i, 0, img_container)
            
            self.table.setItem(i, 1, QTableWidgetItem(p.title))
            self.table.setItem(i, 2, QTableWidgetItem(p.category))
            self.table.setItem(i, 3, QTableWidgetItem(f"${p.selling_price:.2f}"))

            status_item = QTableWidgetItem(p.status.upper())
            if p.status == "active":
                status_item.setBackground(QColor("#10b981"))
            else:
                status_item.setBackground(QColor("#94a3b8"))
            status_item.setForeground(QColor("#ffffff"))
            self.table.setItem(i, 4, status_item)

            # View button (read-only dialog)
            btn_view = QPushButton("View")
            btn_view.setObjectName("TableActionBtn")
            btn_view.clicked.connect(lambda _=False, pid=p.id: self.on_view_clicked(pid))
            self.table.setCellWidget(i, 5, btn_view)

            # Download Photos button
            btn_download = QPushButton("📥 Photos")
            btn_download.setObjectName("TableActionBtn")
            btn_download.setStyleSheet("background-color: #10b981; color: white;")
            btn_download.clicked.connect(lambda _=False, pid=p.id: self.on_download_photos_clicked(pid))
            self.table.setCellWidget(i, 6, btn_download)

            # Edit button
            btn_edit = QPushButton("Edit")
            btn_edit.setObjectName("TableActionBtn")
            btn_edit.clicked.connect(lambda _=False, pid=p.id: self.on_edit_clicked(pid))
            self.table.setCellWidget(i, 7, btn_edit)

            # Publish button
            btn_publish = QPushButton("Publish")
            btn_publish.setObjectName("TableActionBtn")
            btn_publish.clicked.connect(lambda _=False, pid=p.id: self.on_publish_clicked(pid))
            self.table.setCellWidget(i, 8, btn_publish)
            
            # Delete button
            btn_delete = QPushButton("Delete")
            btn_delete.setObjectName("TableActionBtn")
            btn_delete.setStyleSheet("color: #ef4444;")
            btn_delete.clicked.connect(lambda _=False, pid=p.id: self.on_delete_clicked(pid))
            self.table.setCellWidget(i, 9, btn_delete)

    def on_add_clicked(self):
        dlg = ProductCreateDialog(self)
        if dlg.exec() == QDialog.Accepted and dlg.created_product:
            self.load_products()

    def on_view_clicked(self, product_id):
        dlg = ProductDetailDialog(product_id, self, on_refresh=self.load_products, read_only=True)
        dlg.exec()
    
    def on_download_photos_clicked(self, product_id):
        """Download all product photos with custom size options"""
        try:
            product = StoreProduct.objects.get(id=product_id)
        except StoreProduct.DoesNotExist:
            show_toast("Product not found", parent=self, toast_type="error")
            return
        
        # Collect all images
        all_images = []
        if product.image_path and Path(product.image_path).exists():
            all_images.append(product.image_path)
        
        if product.additional_images:
            try:
                extra = json.loads(product.additional_images)
                if isinstance(extra, list):
                    for img_path in extra:
                        if Path(img_path).exists():
                            all_images.append(img_path)
            except Exception:
                pass
        
        if not all_images:
            QMessageBox.warning(self, "No Images", "This product has no images to download.")
            return
        
        # Show size selection dialog
        size_dialog = PhotoDownloadDialog(len(all_images), self)
        if size_dialog.exec() != QDialog.Accepted:
            return
        
        width = size_dialog.width_value
        height = size_dialog.height_value
        maintain_aspect = size_dialog.maintain_aspect
        output_format = getattr(size_dialog, 'output_format', 'jpg')
        
        # Sanitize product name
        import re
        product_name = re.sub(r'[<>:"/\\|?*]', '', product.title)
        product_name = product_name.replace(' ', '_')[:100]
        
        # Choose save location
        default_filename = product_name + ".zip"
        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Photos Archive",
            default_filename,
            "ZIP Archive (*.zip)"
        )
        
        if not save_path:
            return
        
        try:
            # Create a temporary directory for resized images
            temp_dir = Path(settings.APP_DATA_DIR) / "temp" / f"download_{uuid.uuid4().hex}"
            temp_dir.mkdir(parents=True, exist_ok=True)
            
            # Process and resize images
            processed_files = []
            for idx, img_path in enumerate(all_images, start=1):
                try:
                    # Open and resize image
                    img = Image.open(img_path)
                    
                    if maintain_aspect:
                        # Maintain aspect ratio, fit within dimensions
                        img.thumbnail((width, height), Image.Resampling.LANCZOS)
                    else:
                        # Exact size, ignore aspect ratio
                        img = img.resize((width, height), Image.Resampling.LANCZOS)
                    
                    # Use selected output format
                    ext = f".{output_format}"
                    output_filename = f"{product_name}_{idx}{ext}"
                    output_path = temp_dir / output_filename
                    
                    # Convert RGBA to RGB if saving as JPEG/JPG
                    if output_format in ['jpg', 'jpeg'] and img.mode in ('RGBA', 'LA', 'P'):
                        rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                        if img.mode == 'P':
                            img = img.convert('RGBA')
                        rgb_img.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                        img = rgb_img
                    
                    # Save with format-specific settings
                    if output_format == 'png':
                        img.save(output_path, format='PNG', optimize=True)
                    else:
                        img.save(output_path, format='JPEG', quality=95)
                    processed_files.append((output_filename, output_path))
                    
                except Exception as e:
                    print(f"Error processing image {img_path}: {e}")
                    continue
            
            if not processed_files:
                shutil.rmtree(temp_dir, ignore_errors=True)
                QMessageBox.warning(self, "Error", "Failed to process any images.")
                return
            
            # Create ZIP archive with product name as root folder
            with zipfile.ZipFile(save_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for filename, file_path in processed_files:
                    # Add to ZIP with product name folder
                    arcname = f"{product_name}/{filename}"
                    zipf.write(file_path, arcname)
            
            # Clean up temporary directory
            shutil.rmtree(temp_dir, ignore_errors=True)
            
            show_toast(
                f"Downloaded {len(processed_files)} photo(s) to {Path(save_path).name}",
                parent=self,
                toast_type="success"
            )
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to download photos: {str(e)}")
    
    def on_edit_clicked(self, product_id):
        dlg = ProductDetailDialog(product_id, self, on_refresh=self.load_products, read_only=False)
        dlg.exec()

    def on_publish_clicked(self, product_id):
        try:
            product = StoreProduct.objects.get(id=product_id)
        except StoreProduct.DoesNotExist:
            show_toast("Product not found", parent=self, toast_type="error")
            return
        dlg = PublishDialog(product, self)
        dlg.exec()
    
    def on_delete_clicked(self, product_id):
        reply = QMessageBox.question(self, "Confirm Delete", 
                                     "Are you sure you want to delete this product?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                StoreProduct.objects.get(id=product_id).delete()
                self.load_products()
                show_toast("Product deleted successfully", parent=self, toast_type="success")
            except Exception as e:
                show_toast(f"Error: {str(e)}", parent=self, toast_type="error")


class OrdersView(BaseDataView):
    def __init__(self, parent=None):
        super().__init__("Orders", parent)
        
        # Add Sync Orders button
        self.btn_sync = QPushButton("Sync Orders")
        self.btn_sync.setObjectName("GlowBtn")
        self.btn_sync.clicked.connect(self.sync_orders_from_ebay)
        self.header_layout.insertWidget(1, self.btn_sync)
        
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(["ID", "Source", "Customer", "Amount", "Status", "View", "Edit", "Delete"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.load_orders()

    def load_orders(self):
        orders = list(CustomerOrder.objects.all())
        self.check_data(len(orders))
        self.table.setRowCount(len(orders))
        for i, o in enumerate(orders):
            self.table.setItem(i, 0, QTableWidgetItem(f"#{o.id}"))
            self.table.setItem(i, 1, QTableWidgetItem(o.source.upper()))
            self.table.setItem(i, 2, QTableWidgetItem(o.customer_id))
            self.table.setItem(i, 3, QTableWidgetItem(f"${o.total_amount:.2f}"))
            
            status_item = QTableWidgetItem(o.status.upper())
            status_colors = {
                "pending": "#f59e0b",
                "processing": "#3b82f6",
                "shipped": "#8b5cf6",
                "delivered": "#10b981",
                "cancelled": "#ef4444",
            }
            bg_color = status_colors.get(o.status, "#64748b")
            status_item.setBackground(QColor(bg_color))
            status_item.setForeground(QColor("#ffffff"))
            self.table.setItem(i, 4, status_item)

            btn_view = QPushButton("View")
            btn_view.setObjectName("TableActionBtn")
            btn_view.clicked.connect(lambda _=False, oid=o.id: self.on_view_clicked(oid))
            self.table.setCellWidget(i, 5, btn_view)

            btn_edit = QPushButton("Edit")
            btn_edit.setObjectName("TableActionBtn")
            btn_edit.clicked.connect(lambda _=False, oid=o.id: self.on_edit_clicked(oid))
            self.table.setCellWidget(i, 6, btn_edit)

            btn_delete = QPushButton("Delete")
            btn_delete.setObjectName("TableActionBtn")
            btn_delete.setStyleSheet("color: #ef4444;")
            btn_delete.clicked.connect(lambda _=False, oid=o.id: self.on_delete_clicked(oid))
            self.table.setCellWidget(i, 7, btn_delete)

    def on_add_clicked(self):
        dlg = OrderCreateDialog(self)
        if dlg.exec() == QDialog.Accepted:
            self.load_orders()

    def on_view_clicked(self, order_id: int):
        dlg = OrderDetailDialog(order_id, self, on_refresh=self.load_orders, read_only=True)
        dlg.exec()

    def on_edit_clicked(self, order_id: int):
        dlg = OrderDetailDialog(order_id, self, on_refresh=self.load_orders, read_only=False)
        dlg.exec()

    def on_delete_clicked(self, order_id: int):
        reply = QMessageBox.question(self, "Confirm Delete", 
                                     "Are you sure you want to delete this order?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                CustomerOrder.objects.get(id=order_id).delete()
                self.load_orders()
                show_toast("Order deleted successfully", parent=self, toast_type="success")
            except Exception as e:
                show_toast(f"Error: {str(e)}", parent=self, toast_type="error")

    def sync_orders_from_ebay(self):
        from marketplaces.ebay_client import fetch_orders, EbayCredentials

        accounts = list(
            MarketplaceAccount.objects.filter(marketplace="ebay", status="connected")
        )
        if not accounts:
            show_toast("Connect an eBay account first (Accounts tab)", parent=self, toast_type="error")
            return

        synced = 0
        for acc in accounts:
            creds = EbayCredentials(
                client_id=acc.client_id,
                client_secret=acc.client_secret,
                refresh_token=acc.refresh_token,
                environment=acc.environment or "sandbox",
            )
            ebay_orders = fetch_orders(creds)
            for eo in ebay_orders:
                # Avoid duplicates
                if not CustomerOrder.objects.filter(source="ebay", external_id=eo.order_id).exists():
                    CustomerOrder.objects.create(
                        customer_id=eo.buyer_id,
                        total_amount=eo.total,
                        status=eo.status,
                        source="ebay",
                        external_id=eo.order_id,
                    )
                    synced += 1

        self.load_orders()
        show_toast(f"Synced {synced} new order(s) from eBay", parent=self, toast_type="success")

class ShipmentsView(BaseDataView):
    def __init__(self, parent=None):
        super().__init__("Shipments", parent)
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Ref", "Courier", "Stage", "Risk", "View", "Delete"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.load_shipments()

    def load_shipments(self):
        shipments = list(Shipment.objects.all())
        self.check_data(len(shipments))
        self.table.setRowCount(len(shipments))
        for i, s in enumerate(shipments):
            self.table.setItem(i, 0, QTableWidgetItem(s.tracking_number))
            self.table.setItem(i, 1, QTableWidgetItem(s.courier_name))
            
            status_item = QTableWidgetItem(s.shipment_status.upper())
            status_colors = {
                "pending": "#f59e0b",
                "in_transit": "#3b82f6",
                "out_for_delivery": "#8b5cf6",
                "delivered": "#10b981",
                "returned": "#64748b",
                "delayed": "#ef4444",
            }
            bg_color = status_colors.get(s.shipment_status, "#64748b")
            status_item.setBackground(QColor(bg_color))
            status_item.setForeground(QColor("#ffffff"))
            self.table.setItem(i, 2, status_item)

            risk = s.delay_probability * 100
            risk_item = QTableWidgetItem(f"{risk:.1f}%")
            risk_bg = "#ef4444" if risk > 35 else "#10b981"
            risk_item.setBackground(QColor(risk_bg))
            risk_item.setForeground(QColor("#ffffff"))
            self.table.setItem(i, 3, risk_item)

            btn_view = QPushButton("View")
            btn_view.setObjectName("TableActionBtn")
            btn_view.clicked.connect(lambda _=False, sid=s.id: self.on_view_clicked(sid))
            self.table.setCellWidget(i, 4, btn_view)

            btn_delete = QPushButton("Delete")
            btn_delete.setObjectName("TableActionBtn")
            btn_delete.setStyleSheet("color: #ef4444;")
            btn_delete.clicked.connect(lambda _=False, sid=s.id: self.on_delete_clicked(sid))
            self.table.setCellWidget(i, 5, btn_delete)

    def on_add_clicked(self):
        dlg = ShipmentCreateDialog(self)
        if dlg.exec() == QDialog.Accepted:
            self.load_shipments()

    def on_view_clicked(self, shipment_id: int):
        dlg = ShipmentDetailDialog(shipment_id, self, on_refresh=self.load_shipments)
        dlg.exec()

    def on_delete_clicked(self, shipment_id: int):
        reply = QMessageBox.question(self, "Confirm Delete", 
                                     "Are you sure you want to delete this shipment?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                Shipment.objects.get(id=shipment_id).delete()
                self.load_shipments()
                show_toast("Shipment deleted successfully", parent=self, toast_type="success")
            except Exception as e:
                show_toast(f"Error: {str(e)}", parent=self, toast_type="error")


class AccountsView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(40, 40, 40, 40)
        self.layout.setSpacing(30)

        header = QHBoxLayout()
        title = QLabel("Accounts")
        title.setObjectName("PageTitle")
        header.addWidget(title)
        header.addStretch()
        self.layout.addLayout(header)

        # Marketplace quick-actions row
        quick_row = QHBoxLayout()
        quick_row.setSpacing(12)

        ebay_btn = QPushButton(" Connect eBay")
        ebay_btn.setObjectName("GlowBtn")
        ebay_btn.setMinimumHeight(40)
        ebay_btn.setIcon(qta.icon("fa5s.shopping-bag", color="#0f172a"))
        ebay_btn.setIconSize(QPixmap(20, 20).size())
        ebay_btn.clicked.connect(self.open_connect_dialog)
        quick_row.addWidget(ebay_btn)

        browser_btn = QPushButton(" Browser")
        browser_btn.setObjectName("GlowBtn")
        browser_btn.setMinimumHeight(40)
        browser_btn.setIcon(qta.icon("fa5s.globe", color="#0f172a"))
        browser_btn.setIconSize(QPixmap(20, 20).size())
        browser_btn.clicked.connect(self.open_browser)
        quick_row.addWidget(browser_btn)

        quick_row.addStretch()
        self.layout.addLayout(quick_row)

        self.container = QStackedWidget()
        self.layout.addWidget(self.container)

        self.card = QFrame()
        self.card.setObjectName("ContentCard")
        apply_aura_shadow(self.card)
        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(20, 20, 20, 20)

        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Marketplace",
            "Account",
            "Environment",
            "Status",
            "Remove",
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        card_layout.addWidget(self.table)

        self.empty_state = EmptyStateWidget(
            "No Accounts Connected",
            "Connect your marketplace accounts to publish listings and sync orders.",
        )

        self.container.addWidget(self.card)
        self.container.addWidget(self.empty_state)

        self.load_accounts()

    def load_accounts(self):
        accounts = list(MarketplaceAccount.objects.all().order_by("-created_at"))
        self.container.setCurrentIndex(1 if not accounts else 0)
        self.table.setRowCount(len(accounts))
        for i, acc in enumerate(accounts):
            self.table.setItem(i, 0, QTableWidgetItem(acc.get_marketplace_display()))
            self.table.setItem(i, 1, QTableWidgetItem(acc.account_name))
            self.table.setItem(i, 2, QTableWidgetItem(acc.environment))

            status_item = QTableWidgetItem(acc.status.upper())
            bg_color = "#10b981" if acc.status == "connected" else "#ef4444"
            status_item.setBackground(QColor(bg_color))
            status_item.setForeground(QColor("#ffffff"))
            self.table.setItem(i, 3, status_item)

            btn_remove = QPushButton("Remove")
            btn_remove.setObjectName("TableActionBtn")
            btn_remove.setStyleSheet("color: #ef4444;")
            btn_remove.clicked.connect(lambda _=False, aid=acc.id: self.remove_account(aid))
            self.table.setCellWidget(i, 4, btn_remove)

    def open_browser(self):
        dlg = BrowserDialog(parent=self)
        dlg.exec()

    def open_connect_dialog(self):
        """Opens OAuth flow in embedded browser."""
        from marketplaces.ebay_client import generate_oauth_url, exchange_code_for_token
        
        # Step 1: Get eBay app credentials
        dialog = QDialog(self)
        dialog.setWindowTitle("eBay App Setup")
        dialog.setModal(True)
        dialog.setMinimumWidth(460)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        info = QLabel("Enter your eBay Developer App credentials.\nYou can get these from developer.ebay.com")
        info.setObjectName("BodySecondary")
        info.setWordWrap(True)
        layout.addWidget(info)

        layout.addWidget(QLabel("Account Name"))
        edt_name = QLineEdit()
        edt_name.setPlaceholderText("e.g. Main Store")
        layout.addWidget(edt_name)

        layout.addWidget(QLabel("Client ID (App ID)"))
        edt_client_id = QLineEdit()
        edt_client_id.setPlaceholderText("Your eBay App ID")
        layout.addWidget(edt_client_id)

        layout.addWidget(QLabel("Client Secret"))
        edt_client_secret = QLineEdit()
        edt_client_secret.setEchoMode(QLineEdit.Password)
        edt_client_secret.setPlaceholderText("Your eBay Cert ID")
        layout.addWidget(edt_client_secret)

        layout.addWidget(QLabel("Environment"))
        cmb_env = QComboBox()
        cmb_env.addItems(["sandbox", "production"])
        layout.addWidget(cmb_env)

        btn_row = QHBoxLayout()
        btn_cancel = QPushButton("Cancel")
        btn_next = QPushButton("Next: Sign In")
        btn_next.setObjectName("GlowBtn")
        btn_cancel.clicked.connect(dialog.reject)
        btn_next.clicked.connect(dialog.accept)
        btn_row.addStretch()
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_next)
        layout.addLayout(btn_row)

        if dialog.exec() != QDialog.Accepted:
            return

        account_name = edt_name.text().strip()
        client_id = edt_client_id.text().strip()
        client_secret = edt_client_secret.text().strip()
        environment = cmb_env.currentText()

        if not account_name or not client_id or not client_secret:
            show_toast("All fields are required", parent=self, toast_type="error")
            return

        # Step 2: Open OAuth browser
        redirect_uri = "https://localhost:8080/callback"  # eBay requires HTTPS for OAuth
        auth_url, state = generate_oauth_url(client_id, redirect_uri, environment)

        oauth_dialog = EbayOAuthDialog(auth_url, redirect_uri, self)
        if oauth_dialog.exec() != QDialog.Accepted or not oauth_dialog.auth_code:
            show_toast("OAuth cancelled", parent=self, toast_type="error")
            return

        # Step 3: Exchange code for tokens
        tokens = exchange_code_for_token(
            client_id, client_secret, oauth_dialog.auth_code, redirect_uri, environment
        )
        if not tokens:
            show_toast("Failed to get tokens", parent=self, toast_type="error")
            return

        # Step 4: Save account
        try:
            MarketplaceAccount.objects.create(
                marketplace="ebay",
                account_name=account_name,
                client_id=client_id,
                client_secret=client_secret,
                refresh_token=tokens["refresh_token"],
                environment=environment,
                status="connected",
            )
            show_toast(f"✓ {account_name} connected via OAuth", parent=self, toast_type="success")
            self.load_accounts()
        except Exception as exc:
            show_toast(f"Failed to save: {exc}", parent=self, toast_type="error")

    def remove_account(self, account_id: int):
        reply = QMessageBox.question(
            self,
            "Remove Account",
            "Disconnect this account?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            try:
                MarketplaceAccount.objects.filter(id=account_id).delete()
                show_toast("Account removed", parent=self, toast_type="success")
                self.load_accounts()
            except Exception as exc:
                show_toast(f"Failed to remove: {exc}", parent=self, toast_type="error")
