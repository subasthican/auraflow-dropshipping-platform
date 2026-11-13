from django.shortcuts import render
from .services import get_sales_metrics, get_supplier_performance
from products.models import StoreProduct

def dashboard_view(request):
    sales = get_sales_metrics()
    suppliers = get_supplier_performance()
    active_products_count = StoreProduct.objects.filter(status='active').count()
    
    context = {
        'sales': sales,
        'suppliers': suppliers,
        'active_products_count': active_products_count
    }
    return render(request, 'analytics/dashboard.html', context)
