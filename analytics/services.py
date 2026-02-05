from django.db.models import Sum, Avg, Count, F
from django.utils import timezone
from datetime import timedelta
from orders.models import CustomerOrder, OrderItem, SupplierOrder
from shipments.models import Shipment
from products.models import StoreProduct

def get_sales_metrics():
    """
    Calculates key sales metrics: revenue, order count, best sellers.
    """
    total_revenue = CustomerOrder.objects.filter(payment_status=True).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    order_count = CustomerOrder.objects.count()
    
    # Best selling products
    best_sellers = OrderItem.objects.values('store_product__title').annotate(
        total_sold=Sum('quantity')
    ).order_by('-total_sold')[:5]
    
    return {
        'total_revenue': total_revenue,
        'order_count': order_count,
        'best_sellers': list(best_sellers)
    }

def get_supplier_performance():
    """
    Calculates supplier performance metrics: avg delivery time, delay rate.
    """
    metrics = SupplierOrder.objects.values('supplier_product__supplier_name').annotate(
        avg_price=Avg('supplier_product__supplier_price'),
        order_count=Count('id')
    )
    
    # Calculate delay rate from shipments
    # This is a bit more complex in standard SQL, but we can do it with Django
    supplier_perf = []
    for m in metrics:
        name = m['supplier_product__supplier_name']
        shipments = Shipment.objects.filter(supplier_order__supplier_product__supplier_name=name)
        total_shipments = shipments.count()
        delayed_shipments = shipments.filter(shipment_status='delayed').count()
        
        delay_rate = (delayed_shipments / total_shipments) if total_shipments > 0 else 0
        
        supplier_perf.append({
            'name': name,
            'avg_price': m['avg_price'],
            'order_count': m['order_count'],
            'delay_rate': delay_rate
        })
        
    return supplier_perf
