import os
import shutil
import uuid
import re
import json
from pathlib import Path
from decimal import Decimal
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit, QComboBox, QDoubleSpinBox,
    QPushButton, QLabel, QFileDialog, QFrame, QMessageBox, QTextEdit, QScrollArea, QWidget,
    QAbstractSpinBox, QRadioButton, QButtonGroup, QSizePolicy,
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QPixmap

from django.conf import settings
from products.models import StoreProduct


class ProductCreateDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("New Product")
        self.setModal(True)
        self.setMinimumWidth(650)
        self.setMinimumHeight(750)

        self.created_product = None
        self.selected_image_path = ""
        self.all_images = []  # Store all downloaded image paths
        self.currency = "USD"

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        title = QLabel("Add Product from Supplier")
        title.setObjectName("SectionTitle")
        layout.addWidget(title)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)
        form.setHorizontalSpacing(16)
        form.setVerticalSpacing(16)
        # Ensure all non-fixed fields grow to align nicely
        form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)

        # URL field with autofill
        url_row = QHBoxLayout()
        url_row.setSpacing(10)
        url_row.setContentsMargins(0, 0, 0, 0)
        self.edt_url = QLineEdit()
        self.edt_url.setPlaceholderText("Paste product URL from any website")
        self.edt_url.setMinimumHeight(28)
        self.edt_url.setMaximumHeight(28)
        self.edt_url.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.edt_url.setStyleSheet("border-radius: 10px; padding: 4px 8px;")
        self.btn_fetch = QPushButton("Auto-fill")
        self.btn_fetch.setObjectName("GlowBtn")
        self.btn_fetch.setFixedWidth(145)
        self.btn_fetch.setFixedHeight(28)
        self.btn_fetch.setStyleSheet("font-weight: 700; font-size: 14px; padding: 4px 10px;")
        self.btn_fetch.clicked.connect(self.handle_autofill)
        url_row.addWidget(self.edt_url, 1)
        url_row.addWidget(self.btn_fetch)
        form.addRow("URL", url_row)

        self.edt_title = QLineEdit()
        self.edt_title.setPlaceholderText("Product title")
        self.edt_title.setMinimumHeight(28)
        self.edt_title.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.edt_title.setStyleSheet("border-radius: 10px; padding: 4px 8px;")
        form.addRow("Title", self.edt_title)

        self.edt_category = QLineEdit()
        self.edt_category.setPlaceholderText("Category (optional)")
        self.edt_category.setMinimumHeight(28)
        self.edt_category.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.edt_category.setStyleSheet("border-radius: 10px; padding: 4px 8px;")
        form.addRow("Category", self.edt_category)

        # Price with currency converter
        price_row = QHBoxLayout()
        self.cmb_currency = QComboBox()
        self.cmb_currency.addItems(["USD", "GBP", "EUR", "AUD", "CAD", "LKR", "INR", "JPY", "CNY", "SGD"])
        self.cmb_currency.setFixedWidth(90)
        self.cmb_currency.setFixedHeight(28)
        self.cmb_currency.setStyleSheet("padding: 4px 8px; border-radius: 6px;")
        self.cmb_currency.currentTextChanged.connect(self.convert_currency)
        
        self.spn_price = QDoubleSpinBox()
        self.spn_price.setRange(0.00, 1_000_000.00)
        self.spn_price.setDecimals(2)
        self.spn_price.setSingleStep(0.50)
        self.spn_price.setValue(0.00)
        self.spn_price.setMinimumHeight(28)
        # Show currency symbol inside the field
        self.spn_price.setPrefix("$ ")
        self.spn_price.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.PlusMinus)
        
        price_row.addWidget(self.cmb_currency)
        price_row.addWidget(self.spn_price, 1)
        form.addRow("Price", price_row)
        
        # Conversion info (small helper text)
        self.lbl_conversion_info = QLabel("")
        self.lbl_conversion_info.setStyleSheet("color: #6b7280; font-size: 12px;")
        form.addRow("", self.lbl_conversion_info)
        
        # Store original scraped price and currency for conversion
        self.original_price = 0.00
        self.original_currency = "USD"

        # Status as segmented radio buttons
        status_row = QHBoxLayout()
        self.rb_status_active = QRadioButton("Active")
        self.rb_status_inactive = QRadioButton("Inactive")
        self.rb_status_active.setChecked(True)
        self.rb_status_active.setFixedHeight(28)
        self.rb_status_inactive.setFixedHeight(28)
        self.status_group = QButtonGroup(self)
        self.status_group.addButton(self.rb_status_active)
        self.status_group.addButton(self.rb_status_inactive)
        self.rb_status_active.setStyleSheet("padding: 4px 10px; border: 1px solid #3b82f6; border-radius: 6px;")
        self.rb_status_inactive.setStyleSheet("padding: 4px 10px; border: 1px solid #64748b; border-radius: 6px;")
        status_row.addWidget(self.rb_status_active)
        status_row.addWidget(self.rb_status_inactive)
        status_row.addStretch()
        form.addRow("Status", status_row)

        # Description with counter and better styling
        desc_label_layout = QHBoxLayout()
        desc_label = QLabel("Description")
        self.desc_count_label = QLabel("(0 chars)")
        self.desc_count_label.setStyleSheet("color: #6b7280; font-size: 12px;")
        btn_clean_desc = QPushButton("Clean")
        btn_clean_desc.setFixedHeight(22)
        btn_clean_desc.clicked.connect(self._clean_description_clicked)
        btn_clean_desc.setStyleSheet("padding: 2px 8px; border-radius: 6px;")
        desc_label_layout.addWidget(desc_label)
        desc_label_layout.addWidget(self.desc_count_label)
        desc_label_layout.addStretch()
        desc_label_layout.addWidget(btn_clean_desc)

        self.txt_description = QTextEdit()
        self.txt_description.setPlaceholderText("Product description customers will love")
        # Fix height and size policy so it doesn't overlap following widgets
        self.txt_description.setMinimumHeight(100)
        self.txt_description.setMaximumHeight(100)
        self.txt_description.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.txt_description.setStyleSheet("border: 1px solid #94a3b8; border-radius: 8px; padding: 6px;")
        self.txt_description.textChanged.connect(self._update_desc_count)

        layout.addLayout(form)
        # Put description in its own container to guarantee stacking order
        desc_container = QWidget()
        desc_v = QVBoxLayout(desc_container)
        desc_v.setContentsMargins(0, 0, 0, 0)
        desc_v.setSpacing(6)
        desc_v.addLayout(desc_label_layout)
        desc_v.addWidget(self.txt_description)
        layout.addWidget(desc_container)
        # Add spacing so next section (images) never overlaps
        layout.addSpacing(10)

        # All images preview area with count
        img_header = QHBoxLayout()
        img_header.setContentsMargins(0, 0, 0, 0)
        img_label = QLabel("Product Images")
        img_label.setObjectName("MetricLabel")
        img_header.addWidget(img_label)
        
        self.img_count_label = QLabel("(0)")
        self.img_count_label.setStyleSheet("color: #6b7280; font-size: 12px;")
        img_header.addWidget(self.img_count_label)
        img_header.addStretch()
        layout.addLayout(img_header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFixedHeight(160)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("background: transparent; border: 1px solid gray;")
        scroll.setContentsMargins(8, 8, 8, 8)

        self.img_container = QWidget()
        self.img_container.setMinimumHeight(150)
        self.img_layout = QHBoxLayout(self.img_container)
        self.img_layout.setContentsMargins(8, 8, 8, 8)
        self.img_layout.setSpacing(8)
        self.img_layout.addStretch()
        scroll.setWidget(self.img_container)
        layout.addWidget(scroll)

        btn_choose_manual = QPushButton("+ Add Image Manually")
        btn_choose_manual.setObjectName("TableActionBtn")
        btn_choose_manual.clicked.connect(self.handle_choose_image)
        layout.addWidget(btn_choose_manual)

        # Buttons
        btns = QHBoxLayout()
        btns.addStretch()
        self.btn_cancel = QPushButton("Cancel")
        self.btn_ok = QPushButton("Create")
        btns.addWidget(self.btn_cancel)
        btns.addWidget(self.btn_ok)
        layout.addLayout(btns)

        self.btn_cancel.clicked.connect(self.reject)
        self.btn_ok.clicked.connect(self.handle_create)

    def handle_autofill(self):
        url = self.edt_url.text().strip()
        if not url:
            QMessageBox.warning(self, "URL Required", "Please enter a product URL first.")
            return
        
        # Show loading feedback
        self.btn_fetch.setText("Fetching...")
        self.btn_fetch.setEnabled(False)
        
        try:
            data = self._fetch_product_from_url(url)
            if data:
                if data.get("title"):
                    self.edt_title.setText(data["title"])
                if data.get("price"):
                    self.spn_price.setValue(float(data["price"]))
                    self.original_price = float(data["price"])
                if data.get("currency"):
                    self.cmb_currency.setCurrentText(data["currency"])
                    self.original_currency = data["currency"]
                    # Update price prefix and conversion info
                    self._update_price_prefix()
                    self._update_conversion_info()
                if data.get("category"):
                    self.edt_category.setText(data["category"])
                if data.get("description"):
                    cleaned = self._clean_description_text(data["description"])
                    self.txt_description.setPlainText(cleaned)
                    self._update_desc_count()
                if data.get("images"):
                    self._download_all_images(data["images"])
                QMessageBox.information(self, "Success", f"Fetched {len(self.all_images)} images and product details!")
            else:
                QMessageBox.warning(self, "No Data", "Could not extract product information from this URL.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to fetch product: {str(e)}")
        finally:
            self.btn_fetch.setText("Auto-fill")
            self.btn_fetch.setEnabled(True)
    
    def convert_currency(self):
        """Convert price when currency is changed."""
        if self.original_price == 0:
            return
        
        from_currency = self.original_currency
        to_currency = self.cmb_currency.currentText()
        
        if from_currency == to_currency:
            self.spn_price.setValue(self.original_price)
            self._update_price_prefix()
            self._update_conversion_info()
            return
        
        try:
            # Use exchangerate-api.com (free, no API key needed)
            url = f"https://api.exchangerate-api.com/v4/latest/{from_currency}"
            response = requests.get(url, timeout=5)
            data = response.json()
            
            if "rates" in data and to_currency in data["rates"]:
                rate = data["rates"][to_currency]
                converted = self.original_price * rate
                self.spn_price.setValue(round(converted, 2))
                self._update_price_prefix()
                self._update_conversion_info(rate=rate)
        except Exception as e:
            print(f"Currency conversion failed: {e}")
            # Keep current value if conversion fails

    def _currency_symbol(self, code: str) -> str:
        mapping = {
            "USD": "$", "GBP": "£", "EUR": "€", "AUD": "A$", "CAD": "C$",
            "LKR": "Rs", "INR": "₹", "JPY": "¥", "CNY": "¥", "SGD": "S$",
        }
        return mapping.get(code, code)

    def _update_price_prefix(self):
        sym = self._currency_symbol(self.cmb_currency.currentText())
        self.spn_price.setPrefix(f"{sym} ")

    def _update_conversion_info(self, rate: float | None = None):
        if self.original_price and self.original_currency:
            base_sym = self._currency_symbol(self.original_currency)
            target = self.cmb_currency.currentText()
            txt = f"Converted from {base_sym} {self.original_price:.2f} ({self.original_currency})"
            if rate:
                txt += f" @ rate {rate:.4f}"
            self.lbl_conversion_info.setText(txt)

    def _update_desc_count(self):
        text = self.txt_description.toPlainText()
        self.desc_count_label.setText(f"({len(text)} chars)")

    def _clean_description_clicked(self):
        text = self.txt_description.toPlainText()
        cleaned = self._clean_description_text(text)
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
        # Normalize whitespace
        text = re.sub(r"\s+", " ", text).strip()
        # Keep reasonable length
        return text[:1200]

    def _fetch_product_from_url(self, url: str) -> dict:
        """Scrape complete product data from the given URL - all images, description, currency."""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        # Follow redirects for short URLs (like ebay.us)
        response = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
        response.raise_for_status()
        
        # Get the final URL after redirects
        final_url = response.url
        is_ebay = 'ebay.com' in final_url or 'ebay.us' in url or 'ebay.co.uk' in final_url or 'ebay.' in final_url
        
        soup = BeautifulSoup(response.content, 'html.parser')
        data = {}
        
        # Extract title - eBay specific selectors first
        title_selectors = []
        if is_ebay:
            title_selectors.extend([
                'h1.x-item-title__mainTitle',
                'h1[class*="x-item-title"]',
                'span[class*="ux-textspans--BOLD"]',
                '.it-ttl',
            ])
        
        title_selectors.extend([
            'h1[class*="product"]', 'h1[class*="title"]', '[class*="product-title"]',
            '[class*="ProductTitle"]', 'h1[itemprop="name"]', 'h1',
        ])
        
        for selector in title_selectors:
            elem = soup.select_one(selector)
            if elem and elem.get_text(strip=True):
                data["title"] = elem.get_text(strip=True)[:255]
                break
        
        # Extract price with currency - eBay specific first
        price_selectors = []
        if is_ebay:
            price_selectors.extend([
                '.x-price-primary span[class*="ux-textspans"]',
                '[class*="x-price-primary"]',
                '[itemprop="price"]',
                '.notranslate',
            ])
        
        price_selectors.extend([
            '[class*="price"]', '[class*="Price"]', '[itemprop="price"]',
            'span[class*="amount"]', '[data-price]',
        ])
        
        currency = "USD"
        for selector in price_selectors:
            elem = soup.select_one(selector)
            if elem:
                price_text = elem.get_text(strip=True)
                # Detect currency
                if '€' in price_text or 'EUR' in price_text:
                    currency = "EUR"
                elif '£' in price_text or 'GBP' in price_text:
                    currency = "GBP"
                elif '¥' in price_text or 'JPY' in price_text:
                    currency = "JPY"
                elif '₹' in price_text or 'INR' in price_text:
                    currency = "INR"
                elif '$' in price_text or 'USD' in price_text:
                    currency = "USD"
                elif 'A$' in price_text or 'AU$' in price_text or 'AUD' in price_text:
                    currency = "AUD"
                
                # Extract number
                match = re.search(r'[\d,]+\.?\d*', price_text.replace(',', ''))
                if match:
                    try:
                        data["price"] = float(match.group(0))
                        data["currency"] = currency
                        break
                    except:
                        pass
        
        # Extract category
        category = None
        breadcrumb = soup.select_one('[class*="breadcrumb"]')
        if breadcrumb:
            cats = [a.get_text(strip=True) for a in breadcrumb.find_all('a')]
            if cats:
                category = cats[-1] if len(cats) == 1 else cats[-2] if len(cats) > 1 else cats[0]
        if not category:
            meta_cat = soup.find('meta', property='product:category')
            if meta_cat:
                category = meta_cat.get('content', '')
        data["category"] = category[:100] if category else ""
        
        # Extract full description - enhanced with eBay
        desc_selectors = []
        if is_ebay:
            desc_selectors.extend([
                '[class*="x-item-description"]',
                '#viTabs_0_panel',
                'iframe[id*="desc"]',  # eBay often uses iframes
                '.ds_div',
            ])
        
        desc_selectors.extend([
            '[class*="description"]', '[class*="Description"]',
            '[itemprop="description"]', '#description', '.product-description',
            '[id*="description"]', '[class*="product-info"]',
            '[class*="details"]', '[class*="Details"]',
            'meta[name="description"]', 'meta[property="og:description"]',
        ])
        
        description = ""
        for selector in desc_selectors:
            if selector.startswith('meta'):
                elem = soup.select_one(selector)
                if elem:
                    desc_text = elem.get('content', '')
                    if len(desc_text) > 50:
                        description = desc_text[:2000]
                        break
            else:
                elem = soup.select_one(selector)
                if elem:
                    desc_text = elem.get_text(separator='\n', strip=True)
                    if len(desc_text) > 100:
                        description = desc_text[:2000]
                        break
        
        # Fallback: Get from JSON-LD
        if not description and json_ld_script:
            try:
                ld_data = json.loads(json_ld_script.string)
                if isinstance(ld_data, dict) and 'description' in ld_data:
                    description = str(ld_data['description'])[:2000]
            except:
                pass
        
        data["description"] = description
        
        # Extract ALL product images - enhanced detection including eBay
        images = []
        seen_urls = set()
        seen_base_urls = set()  # Track base URLs without size parameters
        
        def clean_url_for_comparison(url):
            """Remove size parameters to detect duplicates."""
            # Remove common size parameters like _200x200, -300x300, etc.
            import re
            cleaned = re.sub(r'[-_]\d+x\d+', '', url)
            cleaned = re.sub(r'\?.*$', '', cleaned)  # Remove query params
            cleaned = re.sub(r'_(small|medium|large|thumb|thumbnail|s-l\d+)', '', cleaned, flags=re.IGNORECASE)
            return cleaned
        
        def upgrade_ebay_image_url(url):
            """Upgrade eBay image URL to highest quality."""
            if 'ebayimg.com' in url or 'ebaystatic.com' in url:
                # Replace size parameters with s-l1600 for high-res
                url = re.sub(r's-l\d+', 's-l1600', url)
                url = re.sub(r'\$_\d+\.', '$_57.', url)  # High quality variant
            return url
        
        # Strategy 1: Check for JSON-LD structured data
        json_ld_script = soup.find('script', type='application/ld+json')
        if json_ld_script:
            try:
                ld_data = json.loads(json_ld_script.string)
                if isinstance(ld_data, dict) and 'image' in ld_data:
                    img_data = ld_data['image']
                    if isinstance(img_data, list):
                        for img in img_data:
                            if isinstance(img, str):
                                images.append(img)
                            elif isinstance(img, dict) and 'url' in img:
                                images.append(img['url'])
                    elif isinstance(img_data, str):
                        images.append(img_data)
            except:
                pass
        
        # Strategy 2: Find gallery/carousel containers - eBay specific first
        gallery_selectors = []
        if is_ebay:
            gallery_selectors.extend([
                '.ux-image-carousel',
                '[class*="ux-image-filmstrip"]',
                '.filmstrip',
                '#mainImgHldr',
                'div[class*="image-treatment"]',
                'ul[class*="ux-image-carousel-container"]',
                'div[class*="ux-image-grid"]',
            ])
        
        gallery_selectors.extend([
            '[class*="gallery"]', '[class*="Gallery"]',
            '[class*="slider"]', '[class*="Slider"]',
            '[id*="gallery"]', '[id*="product-gallery"]',
        ])
        
        found_in_gallery = False
        for selector in gallery_selectors:
            container = soup.select_one(selector)
            if container:
                found_in_gallery = True
                # For eBay, also check for buttons and divs with data attributes
                if is_ebay:
                    # Check for thumbnail buttons with data attributes
                    for button in container.find_all(['button', 'div'], attrs={'data-zoom-src': True}):
                        img_url = button.get('data-zoom-src')
                        if img_url:
                            if img_url.startswith('//'):
                                img_url = 'https:' + img_url
                            img_url = upgrade_ebay_image_url(img_url)
                            base_url = clean_url_for_comparison(img_url)
                            if (base_url not in seen_base_urls and
                                'placeholder' not in img_url.lower()):
                                images.append(img_url)
                                seen_base_urls.add(base_url)
                
                for img in container.find_all('img'):
                    # Prefer high-res versions
                    img_url = (
                        img.get('data-zoom-src') or img.get('data-large-image') or 
                        img.get('data-zoom-image') or img.get('data-full-size') or 
                        img.get('data-original') or img.get('data-src') or img.get('src')
                    )
                    
                    if img_url:
                        # Clean URL
                        if img_url.startswith('//'):
                            img_url = 'https:' + img_url
                        elif img_url.startswith('/'):
                            parsed = urlparse(final_url)
                            img_url = f"{parsed.scheme}://{parsed.netloc}{img_url}"
                        
                        # Upgrade eBay images to high-res
                        if is_ebay:
                            img_url = upgrade_ebay_image_url(img_url)
                        
                        # Check for duplicates based on base URL
                        base_url = clean_url_for_comparison(img_url)
                        
                        if (base_url not in seen_base_urls and
                            'placeholder' not in img_url.lower() and
                            'icon' not in img_url.lower() and
                            'logo' not in img_url.lower() and
                            not img_url.endswith('.svg') and
                            not img_url.endswith('.gif')):
                            images.append(img_url)
                            seen_urls.add(img_url)
                            seen_base_urls.add(base_url)
                
                # If we found images in gallery, stop looking elsewhere
                if images:
                    break
        
        # Strategy 3: Only if no gallery found, look for product images
        if not found_in_gallery or len(images) < 2:
            img_selectors = []
            if is_ebay:
                img_selectors.extend([
                    'img[id*="icImg"]',
                    'img.img-fluid',
                ])
            
            img_selectors.extend([
                'img[itemprop="image"]',
                'img[class*="product-image"]', 
                'img[class*="ProductImage"]',
            ])
            
            for selector in img_selectors:
                for elem in soup.select(selector):
                    img_url = (
                        elem.get('data-zoom-src') or elem.get('data-large-image') or 
                        elem.get('data-zoom-image') or elem.get('data-src') or elem.get('src')
                    )
                    if img_url:
                        if img_url.startswith('//'):
                            img_url = 'https:' + img_url
                        elif img_url.startswith('/'):
                            parsed = urlparse(final_url)
                            img_url = f"{parsed.scheme}://{parsed.netloc}{img_url}"
                        
                        # Upgrade eBay images to high-res
                        if is_ebay:
                            img_url = upgrade_ebay_image_url(img_url)
                        
                        base_url = clean_url_for_comparison(img_url)
                        if (base_url not in seen_base_urls and 
                            'placeholder' not in img_url.lower() and
                            'logo' not in img_url.lower() and
                            not img_url.endswith('.svg') and
                            not img_url.endswith('.gif')):
                            images.append(img_url)
                            seen_base_urls.add(base_url)
        
        # Limit to 50 images (increased from 12 to handle eBay listings with many images)
        data["images"] = images[:50]
        return data

    def _download_all_images(self, img_urls: list):
        """Download all product images and display previews with remove buttons."""
        # Clear existing previews
        while self.img_layout.count() > 1:  # Keep the stretch
            item = self.img_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self.all_images = []
        temp_dir = Path(settings.APP_DATA_DIR) / "images" / "temp"
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        
        for idx, img_url in enumerate(img_urls):
            try:
                response = requests.get(img_url, headers=headers, timeout=10)
                response.raise_for_status()
                
                # Save with original resolution
                ext = Path(urlparse(img_url).path).suffix or '.jpg'
                temp_path = temp_dir / f"img-{uuid.uuid4().hex}{ext}"
                temp_path.write_bytes(response.content)
                
                # Preview with remove button
                pix = QPixmap(str(temp_path))
                if not pix.isNull():
                    self._add_image_preview(str(temp_path), pix)
                    self.all_images.append(str(temp_path))
            except Exception as e:
                print(f"Failed to download image {idx}: {e}")
                continue
        
        # Update count
        self.img_count_label.setText(f"({len(self.all_images)})")
        
        if not self.all_images:
            no_img = QLabel("No images found")
            no_img.setStyleSheet("color: gray;")
            self.img_layout.insertWidget(0, no_img)
    
    def _add_image_preview(self, img_path: str, pixmap: QPixmap):
        """Add an image preview with remove button."""
        container = QWidget()
        container.setFixedSize(120, 145)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        
        # Image preview
        preview = QLabel()
        preview.setFixedSize(120, 120)
        preview.setFrameStyle(QFrame.StyledPanel | QFrame.Plain)
        preview.setAlignment(Qt.AlignCenter)
        preview.setPixmap(pixmap.scaled(120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        preview.setStyleSheet("border: 2px solid #ddd;")
        layout.addWidget(preview)
        
        # Remove button
        btn_remove = QPushButton("✕ Remove")
        btn_remove.setFixedHeight(20)
        btn_remove.setStyleSheet("""
            QPushButton {
                background: #ef4444;
                color: white;
                border: none;
                border-radius: 3px;
                font-size: 10px;
                padding: 2px;
            }
            QPushButton:hover {
                background: #dc2626;
            }
        """)
        btn_remove.clicked.connect(lambda checked, path=img_path, w=container: self._remove_image(path, w))
        layout.addWidget(btn_remove)
        
        self.img_layout.insertWidget(self.img_layout.count() - 1, container)
    
    def _remove_image(self, img_path: str, widget: QWidget):
        """Remove an image from the list."""
        if img_path in self.all_images:
            self.all_images.remove(img_path)
        widget.deleteLater()
        
        # Update count
        self.img_count_label.setText(f"({len(self.all_images)})")
        
        # Show message if no images left
        if not self.all_images and self.img_layout.count() == 1:
            no_img = QLabel("No images")
            no_img.setStyleSheet("color: gray;")
            self.img_layout.insertWidget(0, no_img)

    def handle_choose_image(self):
        """Add images manually to the gallery."""
        file_paths, _ = QFileDialog.getOpenFileNames(self, "Select Images", "", "Images (*.png *.jpg *.jpeg *.bmp)")
        if not file_paths:
            return
        
        # Clear "No images" message if present
        if self.img_layout.count() > 1:
            first_item = self.img_layout.itemAt(0)
            if first_item and first_item.widget() and isinstance(first_item.widget(), QLabel):
                if first_item.widget().text() in ["No images", "No images found"]:
                    first_item.widget().deleteLater()
        
        # Add each selected image
        for file_path in file_paths:
            pix = QPixmap(file_path)
            if not pix.isNull():
                # Copy to temp
                temp_dir = Path(settings.APP_DATA_DIR) / "images" / "temp"
                temp_dir.mkdir(parents=True, exist_ok=True)
                ext = Path(file_path).suffix
                temp_path = temp_dir / f"manual-{uuid.uuid4().hex}{ext}"
                shutil.copy2(file_path, temp_path)
                
                self._add_image_preview(str(temp_path), pix)
                self.all_images.append(str(temp_path))
        
        # Update count
        self.img_count_label.setText(f"({len(self.all_images)})")

    def handle_create(self):
        title = self.edt_title.text().strip()
        if not title:
            QMessageBox.warning(self, "Validation Error", "Please enter a product title.")
            self.edt_title.setFocus()
            return
        
        try:
            category = self.edt_category.text().strip()
            price = Decimal(str(self.spn_price.value()))
            status = 'active' if self.rb_status_active.isChecked() else 'inactive'
            currency = self.cmb_currency.currentText()
            description = self.txt_description.toPlainText().strip()

            # Save primary image (first one)
            primary_image = ""
            if self.all_images:
                dest_dir = Path(settings.APP_DATA_DIR) / "images"
                dest_dir.mkdir(parents=True, exist_ok=True)
                ext = Path(self.all_images[0]).suffix
                dest_name = f"product-{uuid.uuid4().hex}{ext}"
                primary_image = str(dest_dir / dest_name)
                shutil.copyfile(self.all_images[0], primary_image)

            # Save additional images
            additional_images = []
            for img_path in self.all_images[1:]:
                dest_dir = Path(settings.APP_DATA_DIR) / "images"
                ext = Path(img_path).suffix
                dest_name = f"product-{uuid.uuid4().hex}{ext}"
                dest_path = str(dest_dir / dest_name)
                shutil.copyfile(img_path, dest_path)
                additional_images.append(dest_path)

            self.created_product = StoreProduct.objects.create(
                title=title,
                category=category,
                selling_price=price,
                status=status,
                description=description,
                image_path=primary_image,
                currency=currency,
                additional_images=json.dumps(additional_images),
            )
            QMessageBox.information(self, "Success", f"Product '{title}' created successfully!")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create product: {str(e)}")

