from django.contrib import admin
from .models import Shipment

@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    list_display = ('tracking_number', 'courier_name', 'shipment_status', 'expected_delivery_date', 'delay_probability')
    list_filter = ('shipment_status', 'courier_name')
    search_fields = ('tracking_number', 'courier_name')
