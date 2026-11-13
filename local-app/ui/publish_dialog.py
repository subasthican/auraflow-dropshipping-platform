from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton
)
from PySide6.QtCore import Qt

from ui.toast import show_toast
from marketplaces.ebay_client import publish_product, EbayCredentials
from core.models import MarketplaceAccount


class PublishDialog(QDialog):
    def __init__(self, product, parent=None):
        super().__init__(parent)
        self.product = product
        self.setWindowTitle("Publish Listing")
        self.setModal(True)
        self.setMinimumWidth(420)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        title = QLabel(f"Publish '{self.product.title}'")
        title.setObjectName("SectionTitle")
        layout.addWidget(title)

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Marketplace"))
        self.cmb_marketplace = QComboBox()
        self.cmb_marketplace.addItems(["eBay"])
        row1.addWidget(self.cmb_marketplace, 1)
        layout.addLayout(row1)

        row_account = QHBoxLayout()
        row_account.addWidget(QLabel("Account"))
        self.cmb_account = QComboBox()
        row_account.addWidget(self.cmb_account, 1)
        layout.addLayout(row_account)

        hint = QLabel("Use the Accounts tab to connect eBay before publishing.")
        hint.setObjectName("BodySecondary")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        btn_row = QHBoxLayout()
        btn_cancel = QPushButton("Cancel")
        self.btn_publish = QPushButton("Publish")
        self.btn_publish.setObjectName("GlowBtn")
        btn_cancel.clicked.connect(self.reject)
        self.btn_publish.clicked.connect(self._handle_publish)
        btn_row.addStretch()
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(self.btn_publish)
        layout.addLayout(btn_row)

        self._load_accounts()

    def _load_accounts(self):
        self.accounts = list(
            MarketplaceAccount.objects.filter(marketplace="ebay", status="connected").order_by("-created_at")
        )
        self.cmb_account.clear()
        if self.accounts:
            for acc in self.accounts:
                label = f"{acc.account_name} ({acc.environment})"
                self.cmb_account.addItem(label)
            self.btn_publish.setEnabled(True)
        else:
            self.cmb_account.addItem("No connected accounts")
            self.btn_publish.setEnabled(False)

    def _handle_publish(self):
        marketplace = self.cmb_marketplace.currentText()
        if marketplace == "eBay":
            if not getattr(self, "accounts", None):
                show_toast("Connect an eBay account first (Accounts tab)", parent=self, toast_type="error")
                return
            idx = self.cmb_account.currentIndex()
            account = self.accounts[idx] if 0 <= idx < len(self.accounts) else None
            if not account:
                show_toast("Select an account to publish", parent=self, toast_type="error")
                return
            creds = EbayCredentials(
                client_id=account.client_id,
                client_secret=account.client_secret,
                refresh_token=account.refresh_token,
                environment=account.environment or "sandbox",
            )
            result = publish_product(self.product, self._collect_images(), creds)
            if result.success:
                show_toast(f"Published to eBay (Listing {result.listing_id})", parent=self, toast_type="success")
                self.accept()
            else:
                show_toast(f"Publish failed: {result.error}", parent=self, toast_type="error")
        else:
            show_toast("Unsupported marketplace", parent=self, toast_type="error")

    def _load_accounts(self):
        self.accounts = list(MarketplaceAccount.objects.filter(marketplace="ebay", status="connected"))
        self.cmb_account.clear()
        if not self.accounts:
            self.cmb_account.addItem("No eBay accounts connected", -1)
            self.btn_publish.setEnabled(False)
        else:
            for acc in self.accounts:
                label = f"{acc.account_name} ({acc.environment})"
                self.cmb_account.addItem(label, acc.id)
            self.btn_publish.setEnabled(True)

    def _collect_images(self):
        images = []
        if self.product.image_path:
            images.append(self.product.image_path)
        try:
            import json
            if self.product.additional_images:
                extra = json.loads(self.product.additional_images)
                if isinstance(extra, list):
                    images.extend(extra)
        except Exception:
            pass
        return images
