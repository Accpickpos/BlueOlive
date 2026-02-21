# apps/shop_filter_mixin.py
"""
Mixins to filter business data by user's assigned shops.
Used by all business apps (cash_book, creditors, purchase_orders, stock_control).
"""

from django.db import models
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class ShopFilterMixin:
    """
    Filters querysets to only return data from shops the user has access to.
    
    For admin users: returns all data from all shops in the tenant
    For other users: returns only data from their assigned shops
    
    This mixin should be used with ModelViewSet or APIView classes.
    """
    
    def get_queryset(self):
        """Override get_queryset to filter by user's assigned shops."""
        queryset = super().get_queryset()
        
        # Get the current user
        user = self.request.user
        
        # If user is superuser or admin, return all data
        if user.is_superuser or user.role == 'ADMIN':
            return queryset
        
        # Get current shop from user or session
        shop_id = getattr(user, 'current_shop_id', None)
        
        if not shop_id:
            # Try to get from session
            shop_id = self.request.session.get('current_shop_id')
        
        if not shop_id:
            # No shop access - return empty queryset
            logger.warning(f"User {user.id} has no current_shop_id set, returning empty queryset")
            return queryset.none()
        
        # Validate user still has access to this shop
        if not user.can_access_shop(shop_id):
            logger.warning(f"User {user.id} cannot access shop {shop_id}, returning empty queryset")
            return queryset.none()
        
        # Filter by shop_id
        return self._filter_by_shop(queryset, shop_id)
    
    def _filter_by_shop(self, queryset, shop_id):
        """
        Filter queryset by shop_id field.
        Checks multiple possible field names for compatibility.
        """
        # Check for shop_id field
        if 'shop_id' in [f.name for f in queryset.model._meta.get_fields()]:
            return queryset.filter(shop_id=shop_id)
        
        # Check for shop FK
        if 'shop' in [f.name for f in queryset.model._meta.get_fields()]:
            return queryset.filter(shop_id=shop_id)
        
        # No shop field found - log warning and return all
        if settings.DEBUG:
            logger.debug(f"Model {queryset.model.__name__} has no shop_id field - returning all data")
        
        return queryset
    
    def perform_create(self, serializer):
        """
        Automatically assign current shop on create.
        Ensures all new records are associated with the current shop.
        """
        if hasattr(self.request, 'user') and self.request.user.is_authenticated:
            user = self.request.user
            shop_id = getattr(user, 'current_shop_id', None)
            
            if not shop_id:
                shop_id = self.request.session.get('current_shop_id')
            
            if shop_id:
                # Only set if not already provided and model has shop_id
                if 'shop_id' not in serializer.validated_data:
                    if 'shop' not in serializer.validated_data:
                        serializer.validated_data['shop_id'] = shop_id
                        if settings.DEBUG:
                            logger.debug(f"Auto-assigned shop_id={shop_id} on create for {queryset.model.__name__}")
        
        super().perform_create(serializer)
    
    def get_serializer_context(self):
        """
        Add shop context to serializer for additional validation if needed.
        """
        context = super().get_serializer_context()
        
        if hasattr(self.request, 'user') and self.request.user.is_authenticated:
            user = self.request.user
            shop_id = getattr(user, 'current_shop_id', None)
            
            if not shop_id:
                shop_id = self.request.session.get('current_shop_id')
            
            if shop_id:
                context['current_shop_id'] = shop_id
        
        return context


class ShopContextMixin:
    """
    Provides helper methods for accessing current shop context in views.
    """
    
    def get_current_shop_id(self):
        """
        Get the current shop ID from user or session.
        """
        user = self.request.user
        
        if hasattr(user, 'current_shop_id') and user.current_shop_id:
            return user.current_shop_id
        
        return self.request.session.get('current_shop_id')
    
    def get_current_shop(self):
        """
        Get the current shop object.
        """
        from tenancy.models import Shop
        
        shop_id = self.get_current_shop_id()
        
        if shop_id:
            return Shop.objects.using('default').filter(
                id=shop_id,
                is_active=True
            ).first()
        
        return None
    
    def validate_shop_access(self, shop_id):
        """
        Validate that the current user has access to the specified shop.
        """
        user = self.request.user
        
        # Admins have full access
        if user.is_superuser or user.role == 'ADMIN':
            return True
        
        return user.can_access_shop(shop_id)
