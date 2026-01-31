# apps/shop_filter_mixin.py
"""
Mixin to filter business data by user's assigned shops.
Used by all business apps (cash_book, creditors, purchase_orders, stock_control).
"""


class ShopFilterMixin:
    """
    Filters querysets to only return data from shops the user has access to.
    
    For admin users: returns all data from all shops in the tenant
    For other users: returns only data from their assigned shops
    """
    
    def get_queryset(self):
        """Override get_queryset to filter by user's assigned shops."""
        queryset = super().get_queryset()
        
        # Get the current user
        user = self.request.user
        
        # If user is superuser or admin, return all data
        if user.is_superuser or user.role == 'ADMIN':
            return queryset
        
        # Filter by user's assigned shops
        if hasattr(user, 'shop_ids') and user.shop_ids:
            # Assuming business models have a 'shop_id' or 'shop' foreign key
            if 'shop' in [f.name for f in queryset.model._meta.get_fields()]:
                return queryset.filter(shop_id__in=user.shop_ids)
            elif 'shop_id' in [f.name for f in queryset.model._meta.get_fields()]:
                return queryset.filter(shop_id__in=user.shop_ids)
        
        # If user has no shop access, return empty queryset
        return queryset.none()
