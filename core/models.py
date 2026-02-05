from django.db import models


class MarketplaceAccount(models.Model):
    MARKETPLACE_CHOICES = [
        ("ebay", "eBay"),
    ]

    STATUS_CHOICES = [
        ("connected", "Connected"),
        ("disconnected", "Disconnected"),
    ]

    marketplace = models.CharField(max_length=50, choices=MARKETPLACE_CHOICES, default="ebay")
    account_name = models.CharField(max_length=120)
    client_id = models.CharField(max_length=255)
    client_secret = models.CharField(max_length=255)
    refresh_token = models.TextField(blank=True)
    environment = models.CharField(max_length=20, default="sandbox")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="connected")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.get_marketplace_display()} - {self.account_name}"
