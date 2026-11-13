from .models import SupplierProduct

def get_best_supplier(store_product):
    """
    Selects the best supplier for a given store product based on a weighted score.
    Weights:
    - Price: 40%
    - Delivery Time: 30%
    - Reliability: 30%
    """
    suppliers = SupplierProduct.objects.filter(store_product=store_product)
    
    if not suppliers.exists():
        return None

    # Calculate min/max for normalization if needed, or use a simpler scoring
    # For simplicity, we'll use a direct scoring approach
    
    scored_suppliers = []
    
    for supplier in suppliers:
        # Score Price (Lower is better, so we use inverse or relative)
        # Assuming most prices are in a similar range for the same product
        # Here we'll just use a simple relative score or a direct formula
        # Let's assume we want to minimize (price * 0.4 + delivery * 0.3) and maximize (reliability * 0.3)
        
        # Simple score: 100 - (normalized price) - (normalized delivery) + (normalized reliability)
        # But without normalization across all products, we use a relative score if possible
        
        price_score = float(supplier.supplier_price)
        delivery_score = float(supplier.estimated_delivery_days)
        reliability_score = supplier.reliability_score
        
        # We want to MINIMIZE this combined cost-time value
        # cost_time_index = (price_score * 0.4) + (delivery_score * 0.3)
        
        # And MAXIMIZE reliability, so we subtract it from the cost index
        final_score = (price_score * 0.4) + (delivery_score * 0.3) - (reliability_score * 0.3)
        
        scored_suppliers.append((supplier, final_score))
    
    # Sort by lowest score (best)
    scored_suppliers.sort(key=lambda x: x[1])
    
    return scored_suppliers[0][0]
