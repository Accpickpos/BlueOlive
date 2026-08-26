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
        
        import logging
        logger = logging.getLogger(__name__)
        
        logger.debug(f"[ShopFilterMixin] User {user.id}, role={user.role}, is_superuser={user.is_superuser}")
        
        # If user is superuser or admin, return all data
        if user.is_superuser or user.role == 'ADMIN':
            logger.debug(f"[ShopFilterMixin] User {user.id} is admin - returning all data")
            return queryset
        
        # Get current shop from user or session
        shop_id = getattr(user, 'current_shop_id', None)
        
        logger.debug(f"[ShopFilterMixin] User {user.id} current_shop_id (from user obj) = {shop_id}")
        
        if not shop_id:
            # Try to get from session
            shop_id = self.request.session.get('current_shop_id')
            logger.debug(f"[ShopFilterMixin] User {user.id} current_shop_id (from session) = {shop_id}")
        
        # FIX: If still no shop_id, try to get from user's assigned shops (shop_ids)
        if not shop_id:
            shop_ids_list = getattr(user, 'shop_ids', []) or []
            if shop_ids_list:
                # Use first assigned shop as current
                shop_id = shop_ids_list[0]
                logger.debug(f"[ShopFilterMixin] User {user.id} using first assigned shop: {shop_id}")
                # Set it on user object for future requests
                user.current_shop_id = shop_id
        
        if not shop_id:
            # No shop access - return empty queryset
            logger.warning(f"User {user.id} has no current_shop_id set, returning empty queryset")
            return queryset.none()
        
        # Validate user still has access to this shop
        if not user.can_access_shop(shop_id):
            logger.warning(f"User {user.id} cannot access shop {shop_id}, returning empty queryset")
            return queryset.none()
        
        logger.debug(f"[ShopFilterMixin] User {user.id} filtering by shop_id = {shop_id}")
        
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
        
        # FIX: Models without shop_id field - check if data is shop-specific
        # For StockItem and similar models that don't have shop_id:
        # - If user is admin, return all
        # - If user is non-admin, return all (they should see all items in their tenant)
        # The shop filtering for stock is handled at the schema level, not per-shop
        model_name = queryset.model.__name__
        non_shop_models = ['StockItem', 'SalesDepartment', 'TaxCode', 'Creditor', 'Debtor']
        
        if model_name in non_shop_models:
            logger.debug(f"[ShopFilterMixin] Model {model_name} has no shop_id - returning all (tenant-level data)")
            return queryset
        
        # No shop field found - log warning and return all
        if settings.DEBUG:
            logger.debug(f"[ShopFilterMixin] Model {queryset.model.__name__} has no shop_id field - returning all data")
        
        return queryset
    
    def perform_create(self, serializer):
        """
        Automatically assign current shop on create.
        Ensures all new records are associated with the current shop.
        """
        # Check if serializer has Meta attribute to identify the model
        model_name = None
        if hasattr(serializer, 'Meta') and hasattr(serializer.Meta, 'model'):
            model_name = serializer.Meta.model.__name__
        else:
            # For serializers without Meta (like DebtorCreateUpdateSerializer which uses serializers.Serializer)
            # try to determine model from the serializer class name
            class_name = serializer.__class__.__name__
            logger.debug(f"[ShopFilterMixin] perform_create: Serializer {class_name} has no Meta - checking class name")
            
            # Map serializer class names to model names
            serializer_to_model = {
                'DebtorCreateUpdateSerializer': 'Debtor',
                'DebtorListSerializer': 'Debtor',
                'DebtorDetailSerializer': 'Debtor',
                'CreditorCreateUpdateSerializer': 'Creditor',
                'CreditorListSerializer': 'Creditor',
                'StockItemSerializer': 'StockItem',
                'SalesDepartmentSerializer': 'SalesDepartment',
                'JobCardListSerializer': 'JobCard',
                'JobCardDetailSerializer': 'JobCard',
            }
            model_name = serializer_to_model.get(class_name)
        
        logger.debug(f"[ShopFilterMixin] perform_create: Identified model_name={model_name}")
        
        # DIAGNOSTIC: Log all fields in validated_data before processing
        if settings.DEBUG:
            logger.debug(f"[ShopFilterMixin] perform_create: validated_data keys = {list(serializer.validated_data.keys())}")
        
        # Models that don't have shop_id field - these are tenant-level models
        # DIAGNOSTIC: Add JobCard to the list - it doesn't have shop_id field
        # POS transaction models below also have no shop_id field. Their viewsets
        # don't override perform_create, so without this they'd hit the "assign
        # current shop" branch and inject an invalid shop_id kwarg into
        # validated_data, raising TypeError on save() for any shop-scoped user.
        non_shop_models = [
            'StockItem', 'SalesDepartment', 'TaxCode', 'Creditor', 'Debtor', 'JobCard',
            'Repair', 'CashACheque', 'CashReturn', 'CreditNote', 'ReceiptOnAccount',
            'TransactionQuery', 'Quotation',
        ]
        
        # Remove shop_id from validated_data for models that don't support it
        if model_name and model_name in non_shop_models:
            if 'shop_id' in serializer.validated_data:
                logger.debug(f"[ShopFilterMixin] perform_create: Removing shop_id for {model_name}")
                del serializer.validated_data['shop_id']
            if 'shop' in serializer.validated_data:
                del serializer.validated_data['shop']
        else:
            # For models that support shop_id, assign current shop
            if hasattr(self.request, 'user') and self.request.user.is_authenticated:
                user = self.request.user
                shop_id = getattr(user, 'current_shop_id', None)
                
                if not shop_id:
                    shop_id = self.request.session.get('current_shop_id')
                
                # FIX: If still no shop_id, try to get from user's assigned shops (shop_ids)
                if not shop_id:
                    shop_ids_list = getattr(user, 'shop_ids', []) or []
                    if shop_ids_list:
                        shop_id = shop_ids_list[0]
                        logger.debug(f"[ShopFilterMixin] perform_create: Using first assigned shop {shop_id}")
                
                if shop_id:
                    # Only set if not already provided and model has shop_id field
                    if 'shop_id' not in serializer.validated_data:
                        if 'shop' not in serializer.validated_data:
                            serializer.validated_data['shop_id'] = shop_id
                            if settings.DEBUG:
                                logger.debug(f"Auto-assigned shop_id={shop_id} on create for {model_name or 'unknown model'}")
        
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
