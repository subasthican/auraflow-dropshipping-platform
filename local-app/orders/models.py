from django.db import models
from products.models import StoreProduct, SupplierProduct

class CustomerOrder(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("shipped", "Shipped"),
        ("delivered", "Delivered"),
        ("cancelled", "Cancelled"),
    ]

    customer_id = models.CharField(max_length=100)  # Assuming external customer system ID
    order_date = models.DateTimeField(auto_now_add=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    payment_status = models.BooleanField(default=False)
    source = models.CharField(max_length=50, default="manual")
    external_id = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        unique_together = ("source", "external_id")

    def __str__(self):
        return f"Order #{self.id} [{self.source}] - {self.customer_id}"

class OrderItem(models.Model):
    order = models.ForeignKey(CustomerOrder, on_delete=models.CASCADE, related_name='items')
    store_product = models.ForeignKey(StoreProduct, on_delete=models.SET_NULL, null=True)
    quantity = models.PositiveIntegerField(default=1)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} x {self.store_product.title if self.store_product else 'Deleted Product'}"

class SupplierOrder(models.Model):
    ORDER_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('placed', 'Placed'),
        ('failed', 'Failed'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
    ]

    customer_order = models.OneToOneField(CustomerOrder, on_delete=models.CASCADE, related_name='supplier_order')
    supplier_product = models.ForeignKey(SupplierProduct, on_delete=models.SET_NULL, null=True)
    supplier_order_reference = models.CharField(max_length=255, blank=True)
    order_status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Supplier Order for Customer Order #{self.customer_order.id}"
