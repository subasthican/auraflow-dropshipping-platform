from django.contrib import admin
from .models import CustomerOrder, OrderItem, SupplierOrder

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

@admin.register(CustomerOrder)
class CustomerOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer_id', 'total_amount', 'status', 'payment_status', 'order_date')
    list_filter = ('status', 'payment_status')
    search_fields = ('customer_id',)
    inlines = [OrderItemInline]

@admin.register(SupplierOrder)
class SupplierOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer_order', 'supplier_product', 'order_status', 'created_at')
    list_filter = ('order_status',)
    search_fields = ('supplier_order_reference',)
