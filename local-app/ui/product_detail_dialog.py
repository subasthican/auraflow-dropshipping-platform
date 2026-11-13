import json
import shutil
import uuid
import zipfile
from decimal import Decimal
from pathlib import Path
from PIL import Image

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea,
    QWidget, QMessageBox, QFormLayout, QLineEdit, QComboBox, QDoubleSpinBox,
    QTextEdit, QFileDialog, QFrame, QSizePolicy, QAbstractSpinBox, QRadioButton,
    QButtonGroup, QSpinBox, QGridLayout, QCheckBox,
)
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt
from django.conf import settings
from products.models import StoreProduct
from ui.publish_dialog import PublishDialog
from ui.toast import show_toast


class ProductDetailDialog(QDialog):
    def __init__(self, product_id, parent=None, on_refresh=None, read_only: bool = False):
        super().__init__(parent)
        self.product_id = product_id
        self.on_refresh = on_refresh
        self.product = StoreProduct.objects.get(id=product_id)
        self.read_only = read_only

        self.all_images: list[str] = []

        self.setWindowTitle(f"Product: {self.product.title}")
        self.setModal(True)
        self.setMinimumWidth(700)
        self.setMinimumHeight(820)

        self._build_ui()
        self._load_existing_data()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Header
        title_label = QLabel(f"View / Edit — {self.product.title}")
        title_label.setStyleSheet("font-size: 22px; font-weight: 700; color: #e5e7eb;")
        layout.addWidget(title_label)

        # Form
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)
        form.setHorizontalSpacing(14)
        form.setVerticalSpacing(14)
        form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)

        self.edt_title = QLineEdit()
        self.edt_title.setMinimumHeight(28)
        self.edt_title.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.edt_title.setStyleSheet("border-radius: 10px; padding: 4px 8px;")
        form.addRow("Title", self.edt_title)

        self.edt_category = QLineEdit()
        self.edt_category.setMinimumHeight(28)
        self.edt_category.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.edt_category.setStyleSheet("border-radius: 10px; padding: 4px 8px;")
        form.addRow("Category", self.edt_category)

        price_row = QHBoxLayout()
        self.cmb_currency = QComboBox()
        self.cmb_currency.addItems(["USD", "GBP", "EUR", "AUD", "CAD", "LKR", "INR", "JPY", "CNY", "SGD"])
        self.cmb_currency.setFixedWidth(90)
        self.cmb_currency.setFixedHeight(28)
        self.cmb_currency.setStyleSheet("padding: 4px 8px; border-radius: 6px;")
        self.cmb_currency.currentTextChanged.connect(self._update_price_prefix)

        self.spn_price = QDoubleSpinBox()
        self.spn_price.setRange(0.00, 1_000_000.00)
        self.spn_price.setDecimals(2)
        self.spn_price.setSingleStep(0.50)
        self.spn_price.setMinimumHeight(28)
        self.spn_price.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.PlusMinus)
        price_row.addWidget(self.cmb_currency)
        price_row.addWidget(self.spn_price, 1)
        form.addRow("Price", price_row)

        status_row = QHBoxLayout()
        self.rb_status_active = QRadioButton("Active")
        self.rb_status_inactive = QRadioButton("Inactive")
        self.status_group = QButtonGroup(self)
        self.status_group.addButton(self.rb_status_active)
        self.status_group.addButton(self.rb_status_inactive)
        self.rb_status_active.setStyleSheet("padding: 4px 10px; border: 1px solid #3b82f6; border-radius: 6px;")
        self.rb_status_inactive.setStyleSheet("padding: 4px 10px; border: 1px solid #64748b; border-radius: 6px;")
        status_row.addWidget(self.rb_status_active)
        status_row.addWidget(self.rb_status_inactive)
        status_row.addStretch()
        form.addRow("Status", status_row)

        # Description with counter
        desc_label_row = QHBoxLayout()
        desc_label = QLabel("Description")
        self.desc_count_label = QLabel("(0 chars)")
        self.desc_count_label.setStyleSheet("color: #6b7280; font-size: 12px;")
        btn_clean_desc = QPushButton("Clean")
        btn_clean_desc.setFixedHeight(22)
        btn_clean_desc.clicked.connect(self._clean_description_clicked)
        btn_clean_desc.setStyleSheet("padding: 2px 8px; border-radius: 6px;")
        desc_label_row.addWidget(desc_label)
        desc_label_row.addWidget(self.desc_count_label)
        desc_label_row.addStretch()
        desc_label_row.addWidget(btn_clean_desc)

        self.txt_description = QTextEdit()
        self.txt_description.setMinimumHeight(100)
        self.txt_description.setMaximumHeight(100)
        self.txt_description.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.txt_description.setStyleSheet("border: 1px solid #94a3b8; border-radius: 8px; padding: 6px;")
        self.txt_description.textChanged.connect(self._update_desc_count)

        layout.addLayout(form)
        desc_container = QWidget()
        desc_v = QVBoxLayout(desc_container)
        desc_v.setContentsMargins(0, 0, 0, 0)
        desc_v.setSpacing(6)
        desc_v.addLayout(desc_label_row)
        desc_v.addWidget(self.txt_description)
        layout.addWidget(desc_container)
        layout.addSpacing(8)

        # Images section
        img_header = QHBoxLayout()
        img_label = QLabel("Product Images")
        img_label.setObjectName("MetricLabel")
        img_header.addWidget(img_label)
        self.img_count_label = QLabel("(0)")
        self.img_count_label.setStyleSheet("color: #6b7280; font-size: 12px;")
        img_header.addWidget(self.img_count_label)
        img_header.addStretch()
        layout.addLayout(img_header)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFixedHeight(170)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setStyleSheet("background: transparent; border: 1px solid gray;")
        self.scroll.setContentsMargins(8, 8, 8, 8)

        self.img_container = QWidget()
        self.img_container.setMinimumHeight(150)
        self.img_layout = QHBoxLayout(self.img_container)
        self.img_layout.setContentsMargins(8, 8, 8, 8)
        self.img_layout.setSpacing(8)
        self.img_layout.addStretch()
        self.scroll.setWidget(self.img_container)
        layout.addWidget(self.scroll)

        image_btns = QHBoxLayout()
        self.btn_choose_manual = QPushButton("+ Add Image")
        self.btn_choose_manual.setObjectName("TableActionBtn")
        self.btn_choose_manual.clicked.connect(self.handle_choose_image)
        image_btns.addWidget(self.btn_choose_manual)
        
        self.btn_download_photos = QPushButton("📥 Download Photos")
        self.btn_download_photos.setObjectName("TableActionBtn")
        self.btn_download_photos.setStyleSheet("background-color: #10b981; color: white; border: 1px solid #10b981; border-radius: 8px; padding: 8px; font-weight: 600;")
        self.btn_download_photos.clicked.connect(self.handle_download_photos)
        image_btns.addWidget(self.btn_download_photos)
        image_btns.addStretch()
        layout.addLayout(image_btns)

        # Actions
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.btn_publish = QPushButton("Publish...")
        self.btn_publish.setMinimumWidth(110)
        self.btn_publish.clicked.connect(self.open_publish_dialog)
        btn_layout.addWidget(self.btn_publish)

        self.btn_save = QPushButton("Save Changes")
        self.btn_save.setMinimumWidth(130)
        self.btn_save.setObjectName("GlowBtn")
        self.btn_save.clicked.connect(self.handle_save)
        btn_layout.addWidget(self.btn_save)

        self.btn_delete = QPushButton("Delete Product")
        self.btn_delete.setMinimumWidth(130)
        self.btn_delete.setStyleSheet("background-color: #dc2626; color: white; border: 1px solid #dc2626; border-radius: 8px; padding: 8px; font-weight: 600;")
        self.btn_delete.clicked.connect(self.on_delete_clicked)
        btn_layout.addWidget(self.btn_delete)

        btn_close = QPushButton("Close")
        btn_close.setMinimumWidth(100)
        btn_close.clicked.connect(self.reject)
        btn_layout.addWidget(btn_close)

        layout.addLayout(btn_layout)

        if self.read_only:
            self._set_read_only_state()

    def _load_existing_data(self):
        self.edt_title.setText(self.product.title)
        self.edt_category.setText(self.product.category)
        self.spn_price.setValue(float(self.product.selling_price))
        self.cmb_currency.setCurrentText(self.product.currency or "USD")
        self._update_price_prefix()
        if self.product.status == "active":
            self.rb_status_active.setChecked(True)
        else:
            self.rb_status_inactive.setChecked(True)
        self.txt_description.setPlainText(self.product.description or "")
        self._update_desc_count()
        self._load_images_from_product()

    def _load_images_from_product(self):
        while self.img_layout.count() > 1:
            item = self.img_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        paths = []
        if self.product.image_path:
            paths.append(self.product.image_path)
        if self.product.additional_images:
            try:
                extra = json.loads(self.product.additional_images)
                if isinstance(extra, list):
                    paths.extend(extra)
            except Exception:
                pass

        self.all_images = []
        for p in paths:
            if Path(p).exists():
                pix = QPixmap(p)
                if not pix.isNull():
                    self._add_image_preview(p, pix)
                    self.all_images.append(p)

        if not self.all_images:
            no_img = QLabel("No images")
            no_img.setStyleSheet("color: gray;")
            self.img_layout.insertWidget(0, no_img)

        self._update_img_count()

    def _currency_symbol(self, code: str) -> str:
        mapping = {
            "USD": "$", "GBP": "£", "EUR": "€", "AUD": "A$", "CAD": "C$",
            "LKR": "Rs", "INR": "₹", "JPY": "¥", "CNY": "¥", "SGD": "S$",
        }
        return mapping.get(code, code)

    def _update_price_prefix(self):
        sym = self._currency_symbol(self.cmb_currency.currentText())
        self.spn_price.setPrefix(f"{sym} ")

    def _update_desc_count(self):
        text = self.txt_description.toPlainText()
        self.desc_count_label.setText(f"({len(text)} chars)")

    def _clean_description_clicked(self):
        cleaned = self._clean_description_text(self.txt_description.toPlainText())
        self.txt_description.setPlainText(cleaned)
        self._update_desc_count()

    def _clean_description_text(self, text: str) -> str:
        if not text:
            return ""
        blacklist = [
            "No reviews", "Tell us why you're not interested", "Enter your email to continue",
            "Promo Codes", "View Description", "Buy with Apple Pay",
        ]
        for phrase in blacklist:
            text = text.replace(phrase, "")
        import re
        text = re.sub(r"\s+", " ", text).strip()
        return text[:1200]

    def _add_image_preview(self, img_path: str, pixmap: QPixmap):
        container = QWidget()
        container.setFixedSize(120, 145)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        preview = QLabel()
        preview.setFixedSize(120, 120)
        preview.setFrameStyle(QFrame.StyledPanel | QFrame.Plain)
        preview.setAlignment(Qt.AlignCenter)
        preview.setPixmap(pixmap.scaled(120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        preview.setStyleSheet("border: 2px solid #ddd;")
        layout.addWidget(preview)

        if not self.read_only:
            btn_remove = QPushButton("✕ Remove")
            btn_remove.setFixedHeight(20)
            btn_remove.setStyleSheet(
                """
                QPushButton { background: #ef4444; color: white; border: none; border-radius: 3px; font-size: 10px; padding: 2px; }
                QPushButton:hover { background: #dc2626; }
                """
            )
            btn_remove.clicked.connect(lambda checked, path=img_path, w=container: self._remove_image(path, w))
            layout.addWidget(btn_remove)

        self.img_layout.insertWidget(self.img_layout.count() - 1, container)

    def _remove_image(self, img_path: str, widget: QWidget):
        if self.read_only:
            return
        if img_path in self.all_images:
            self.all_images.remove(img_path)
        widget.deleteLater()
        self._update_img_count()

        if not self.all_images and self.img_layout.count() == 1:
            no_img = QLabel("No images")
            no_img.setStyleSheet("color: gray;")
            self.img_layout.insertWidget(0, no_img)

    def handle_choose_image(self):
        if self.read_only:
            return
        file_paths, _ = QFileDialog.getOpenFileNames(self, "Select Images", "", "Images (*.png *.jpg *.jpeg *.bmp)")
        if not file_paths:
            return

        if self.img_layout.count() > 1:
            first_item = self.img_layout.itemAt(0)
            if first_item and first_item.widget() and isinstance(first_item.widget(), QLabel):
                if first_item.widget().text() in ["No images", "No images found"]:
                    first_item.widget().deleteLater()

        for file_path in file_paths:
            pix = QPixmap(file_path)
            if not pix.isNull():
                temp_dir = Path(settings.APP_DATA_DIR) / "images" / "temp"
                temp_dir.mkdir(parents=True, exist_ok=True)
                ext = Path(file_path).suffix or ".jpg"
                temp_path = temp_dir / f"manual-{uuid.uuid4().hex}{ext}"
                shutil.copy2(file_path, temp_path)
                self._add_image_preview(str(temp_path), pix)
                self.all_images.append(str(temp_path))

        self._update_img_count()

    def _update_img_count(self):
        self.img_count_label.setText(f"({len(self.all_images)})")

    def handle_save(self):
        if self.read_only:
            return
        title = self.edt_title.text().strip()
        if not title:
            QMessageBox.warning(self, "Validation Error", "Please enter a product title.")
            self.edt_title.setFocus()
            return

        try:
            category = self.edt_category.text().strip()
            price = Decimal(str(self.spn_price.value()))
            status = "active" if self.rb_status_active.isChecked() else "inactive"
            currency = self.cmb_currency.currentText()
            description = self.txt_description.toPlainText().strip()

            dest_dir = Path(settings.APP_DATA_DIR) / "images"
            dest_dir.mkdir(parents=True, exist_ok=True)

            primary_image = ""
            additional_images: list[str] = []

            for idx, img_path in enumerate(self.all_images):
                src = Path(img_path)
                if not src.exists():
                    continue

                if str(src).startswith(str(dest_dir)):
                    dest_path = str(src)
                else:
                    ext = src.suffix or ".jpg"
                    dest_path = str(dest_dir / f"product-{uuid.uuid4().hex}{ext}")
                    shutil.copyfile(src, dest_path)

                if idx == 0:
                    primary_image = dest_path
                else:
                    additional_images.append(dest_path)

            self.product.title = title
            self.product.category = category
            self.product.selling_price = price
            self.product.status = status
            self.product.description = description
            self.product.currency = currency
            self.product.image_path = primary_image
            self.product.additional_images = json.dumps(additional_images)
            self.product.save()

            show_toast("Product updated successfully", parent=self, toast_type="success")
            if self.on_refresh:
                self.on_refresh()
            self.accept()
        except Exception as e:
            show_toast(f"Error: {str(e)}", parent=self, toast_type="error")

    def open_publish_dialog(self):
        if self.read_only:
            return
        dlg = PublishDialog(self.product, self)
        dlg.exec()

    def handle_download_photos(self):
        """Download all product photos with custom size options"""
        if not self.all_images:
            QMessageBox.warning(self, "No Images", "This product has no images to download.")
            return
        
        # Show size selection dialog
        size_dialog = PhotoDownloadDialog(len(self.all_images), self)
        if size_dialog.exec() != QDialog.Accepted:
            return
        
        width = size_dialog.width_value
        height = size_dialog.height_value
        maintain_aspect = size_dialog.maintain_aspect
        output_format = getattr(size_dialog, 'output_format', 'jpg')
        
        # Choose save location
        default_filename = self._sanitize_filename(self.product.title) + ".zip"
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
            
            product_name = self._sanitize_filename(self.product.title)
            
            # Process and resize images
            processed_files = []
            for idx, img_path in enumerate(self.all_images, start=1):
                if not Path(img_path).exists():
                    continue
                
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
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename by removing invalid characters"""
        import re
        # Remove invalid characters
        filename = re.sub(r'[<>:"/\\|?*]', '', filename)
        # Replace spaces with underscores
        filename = filename.replace(' ', '_')
        # Limit length
        return filename[:100]

    def on_delete_clicked(self):
        if self.read_only:
            return
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete '{self.product.title}'?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            try:
                self.product.delete()
                show_toast("Product deleted successfully", parent=self, toast_type="success")
                if self.on_refresh:
                    self.on_refresh()
                self.accept()
            except Exception as e:
                show_toast(f"Error: {str(e)}", parent=self, toast_type="error")

    def _set_read_only_state(self):
        self.edt_title.setReadOnly(True)
        self.edt_category.setReadOnly(True)
        self.cmb_currency.setEnabled(False)
        self.spn_price.setReadOnly(True)
        self.rb_status_active.setEnabled(False)
        self.rb_status_inactive.setEnabled(False)
        self.txt_description.setReadOnly(True)
        self.btn_choose_manual.hide()
        self.btn_download_photos.hide()
        self.btn_publish.hide()
        self.btn_save.hide()
        self.btn_delete.hide()


class PhotoDownloadDialog(QDialog):
    """Dialog for selecting photo download size and options"""
    
    def __init__(self, photo_count: int, parent=None):
        super().__init__(parent)
        self.photo_count = photo_count
        self.width_value = 2000
        self.height_value = 2000
        self.maintain_aspect = True
        self.output_format = "jpg"
        
        self.setWindowTitle("Download Photos Options")
        self.setModal(True)
        self.setMinimumWidth(400)
        
        self._build_ui()
    
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Header
        title = QLabel("📥 Download Photos")
        title.setStyleSheet("font-size: 18px; font-weight: 700; color: #e5e7eb;")
        layout.addWidget(title)
        
        info = QLabel(f"Preparing to download {self.photo_count} photo(s)")
        info.setStyleSheet("color: #9ca3af; font-size: 13px;")
        layout.addWidget(info)
        
        layout.addSpacing(10)
        
        # Size selection
        size_label = QLabel("Image Size")
        size_label.setStyleSheet("font-size: 14px; font-weight: 600; color: #e5e7eb;")
        layout.addWidget(size_label)
        
        # Preset buttons
        preset_layout = QGridLayout()
        preset_layout.setSpacing(8)
        
        presets = [
            ("Square 1000×1000", 1000, 1000),
            ("Square 2000×2000", 2000, 2000),
            ("Square 3000×3000", 3000, 3000),
            ("HD 1920×1080", 1920, 1080),
            ("4K 3840×2160", 3840, 2160),
            ("Original Size", 0, 0),
        ]
        
        self.preset_buttons = []
        for idx, (label, w, h) in enumerate(presets):
            btn = QPushButton(label)
            btn.setMinimumHeight(35)
            btn.setCheckable(True)
            if idx == 1:  # Default to 2000x2000
                btn.setChecked(True)
            btn.clicked.connect(lambda checked, width=w, height=h, button=btn: self._preset_clicked(width, height, button))
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #374151;
                    color: #e5e7eb;
                    border: 2px solid #4b5563;
                    border-radius: 8px;
                    padding: 6px;
                    font-weight: 500;
                }
                QPushButton:checked {
                    background-color: #3b82f6;
                    border-color: #2563eb;
                    color: white;
                }
                QPushButton:hover {
                    background-color: #4b5563;
                }
            """)
            row = idx // 2
            col = idx % 2
            preset_layout.addWidget(btn, row, col)
            self.preset_buttons.append(btn)
        
        layout.addLayout(preset_layout)
        
        layout.addSpacing(10)
        
        # Custom size
        custom_label = QLabel("Custom Size")
        custom_label.setStyleSheet("font-size: 13px; font-weight: 600; color: #e5e7eb;")
        layout.addWidget(custom_label)
        
        size_form = QHBoxLayout()
        size_form.setSpacing(10)
        
        width_label = QLabel("Width:")
        width_label.setStyleSheet("color: #9ca3af;")
        size_form.addWidget(width_label)
        
        self.width_spin = QSpinBox()
        self.width_spin.setRange(100, 10000)
        self.width_spin.setValue(2000)
        self.width_spin.setSuffix(" px")
        self.width_spin.setMinimumHeight(32)
        self.width_spin.setStyleSheet("padding: 4px 8px; border-radius: 6px;")
        self.width_spin.valueChanged.connect(self._custom_size_changed)
        size_form.addWidget(self.width_spin)
        
        x_label = QLabel("×")
        x_label.setStyleSheet("color: #9ca3af; font-weight: bold;")
        size_form.addWidget(x_label)
        
        height_label = QLabel("Height:")
        height_label.setStyleSheet("color: #9ca3af;")
        size_form.addWidget(height_label)
        
        self.height_spin = QSpinBox()
        self.height_spin.setRange(100, 10000)
        self.height_spin.setValue(2000)
        self.height_spin.setSuffix(" px")
        self.height_spin.setMinimumHeight(32)
        self.height_spin.setStyleSheet("padding: 4px 8px; border-radius: 6px;")
        self.height_spin.valueChanged.connect(self._custom_size_changed)
        size_form.addWidget(self.height_spin)
        
        size_form.addStretch()
        layout.addLayout(size_form)
        
        # Aspect ratio checkbox
        self.aspect_check = QCheckBox("Maintain aspect ratio (fit within dimensions)")
        self.aspect_check.setChecked(True)
        self.aspect_check.setStyleSheet("color: #9ca3af; font-size: 12px;")
        layout.addWidget(self.aspect_check)
        
        layout.addSpacing(10)
        
        # Format selection
        format_label = QLabel("Output Format")
        format_label.setStyleSheet("font-size: 13px; font-weight: 600; color: #e5e7eb;")
        layout.addWidget(format_label)
        
        format_layout = QHBoxLayout()
        self.cmb_format = QComboBox()
        self.cmb_format.addItems(["JPG", "JPEG", "PNG"])
        self.cmb_format.setCurrentText("JPG")
        self.cmb_format.setMinimumHeight(32)
        self.cmb_format.setStyleSheet("padding: 4px 8px; border-radius: 6px;")
        format_layout.addWidget(self.cmb_format)
        format_layout.addStretch()
        layout.addLayout(format_layout)
        
        layout.addSpacing(10)
        
        # Info text
        info_text = QLabel("💡 Photos will be saved in a ZIP file with the product name as the folder.")
        info_text.setWordWrap(True)
        info_text.setStyleSheet("color: #6b7280; font-size: 11px; padding: 8px; background-color: #1f2937; border-radius: 6px;")
        layout.addWidget(info_text)
        
        layout.addSpacing(10)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        btn_cancel = QPushButton("Cancel")
        btn_cancel.setMinimumWidth(100)
        btn_cancel.setMinimumHeight(36)
        btn_cancel.clicked.connect(self.reject)
        btn_cancel.setStyleSheet("padding: 8px 16px; border-radius: 6px;")
        btn_layout.addWidget(btn_cancel)
        
        btn_download = QPushButton("Download")
        btn_download.setMinimumWidth(120)
        btn_download.setMinimumHeight(36)
        btn_download.clicked.connect(self._on_download)
        btn_download.setStyleSheet("""
            background-color: #10b981;
            color: white;
            border: none;
            border-radius: 6px;
            padding: 8px 16px;
            font-weight: 600;
        """)
        btn_layout.addWidget(btn_download)
        
        layout.addLayout(btn_layout)
    
    def _preset_clicked(self, width: int, height: int, clicked_button: QPushButton):
        """Handle preset button clicks"""
        # Uncheck other buttons
        for btn in self.preset_buttons:
            if btn != clicked_button:
                btn.setChecked(False)
        
        if width == 0 and height == 0:
            # Original size - will be handled during processing
            self.width_spin.setValue(2000)
            self.height_spin.setValue(2000)
        else:
            self.width_spin.setValue(width)
            self.height_spin.setValue(height)
    
    def _custom_size_changed(self):
        """Uncheck all preset buttons when custom size is changed"""
        for btn in self.preset_buttons:
            btn.setChecked(False)
    
    def _on_download(self):
        """Save values and accept dialog"""
        self.width_value = self.width_spin.value()
        self.height_value = self.height_spin.value()
        self.maintain_aspect = self.aspect_check.isChecked()
        # Selected output format (jpg, jpeg, png)
        try:
            self.output_format = self.cmb_format.currentText().lower()
        except Exception:
            self.output_format = "jpg"
        self.accept()
