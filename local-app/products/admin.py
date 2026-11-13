from django.contrib import admin
from .models import StoreProduct, SupplierProduct

class SupplierProductInline(admin.TabularInline):
    model = SupplierProduct
    extra = 1

@admin.register(StoreProduct)
class StoreProductAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'selling_price', 'status', 'created_at')
    list_filter = ('status', 'category')
    search_fields = ('title', 'description')
    inlines = [SupplierProductInline]

@admin.register(SupplierProduct)
class SupplierProductAdmin(admin.ModelAdmin):
    list_display = ('supplier_name', 'store_product', 'supplier_price', 'estimated_delivery_days', 'reliability_score')
    list_filter = ('supplier_name',)
    search_fields = ('supplier_name', 'supplier_sku')
