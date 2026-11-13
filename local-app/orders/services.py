from django.db import transaction
from .models import CustomerOrder, SupplierOrder, OrderItem
from products.services import get_best_supplier
from shipments.models import Shipment

def process_customer_order(customer_order_id):
    """
    Processes a customer order by selecting the best supplier for each item
    and creating a supplier order.
    For simplicity in this version, we assume one primary supplier per customer order
    based on the first item's best supplier.
    """
    try:
        with transaction.atomic():
            customer_order = CustomerOrder.objects.get(id=customer_order_id)
            
            if customer_order.status != 'pending':
                return False, "Order already processed"

            # Identify the store product (assuming single product per order for automation)
            # In a real system, we might split or pick the best overall supplier
            first_item = customer_order.items.first()
            if not first_item:
                return False, "No items in order"

            best_supplier_product = get_best_supplier(first_item.store_product)
            
            if not best_supplier_product:
                customer_order.status = 'processing' # Or mark for manual review
                customer_order.save()
                return False, "No supplier found for product"

            # Create Supplier Order
            supplier_order = SupplierOrder.objects.create(
                customer_order=customer_order,
                supplier_product=best_supplier_product,
                order_status='pending'
            )

            # Update customer order status
            customer_order.status = 'processing'
            customer_order.save()

            # Trigger supplier placement (Simulated for now)
            # place_order_with_supplier(supplier_order)

            return True, supplier_order

    except Exception as e:
        return False, str(e)

def link_shipment_to_supplier_order(supplier_order_id, tracking_number, courier_name):
    """
    Links a tracking number to a supplier order and creates a shipment.
    """
    try:
        supplier_order = SupplierOrder.objects.get(id=supplier_order_id)
        
        shipment = Shipment.objects.create(
            supplier_order=supplier_order,
            tracking_number=tracking_number,
            courier_name=courier_name,
            shipment_status='pending'
        )
        
        supplier_order.order_status = 'shipped'
        supplier_order.save()
        
        customer_order = supplier_order.customer_order
        customer_order.status = 'shipped'
        customer_order.save()
        
        return True, shipment
    except Exception as e:
        return False, str(e)
