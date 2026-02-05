from django.db import models

class StoreProduct(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=100, blank=True)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default='USD', blank=True)
    image_path = models.CharField(max_length=500, blank=True)  # Primary image
    additional_images = models.TextField(blank=True)  # JSON array of additional image paths
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='inactive')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

class SupplierProduct(models.Model):
    store_product = models.ForeignKey(StoreProduct, on_delete=models.CASCADE, related_name='suppliers')
    supplier_name = models.CharField(max_length=255)
    supplier_product_url = models.URLField()
    supplier_sku = models.CharField(max_length=100)
    supplier_price = models.DecimalField(max_digits=10, decimal_places=2)
    estimated_delivery_days = models.IntegerField()
    supplier_rating = models.FloatField(default=0.0)
    reliability_score = models.FloatField(default=0.0)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.supplier_name} - {self.store_product.title}"
