from django.db import models
from orders.models import SupplierOrder

class Shipment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_transit', 'In Transit'),
        ('out_for_delivery', 'Out for Delivery'),
        ('delivered', 'Delivered'),
        ('returned', 'Returned'),
        ('delayed', 'Delayed'),
    ]

    supplier_order = models.ForeignKey(SupplierOrder, on_delete=models.CASCADE, related_name='shipments')
    courier_name = models.CharField(max_length=100)
    tracking_number = models.CharField(max_length=255)
    shipment_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    shipped_date = models.DateTimeField(null=True, blank=True)
    delivered_date = models.DateTimeField(null=True, blank=True)
    expected_delivery_date = models.DateTimeField(null=True, blank=True)
    
    # ML Prediction fields
    delay_probability = models.FloatField(default=0.0)
    expected_delay_days = models.IntegerField(default=0)

    def __str__(self):
        return f"Shipment {self.tracking_number} - {self.courier_name}"
