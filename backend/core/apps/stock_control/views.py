from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Sum, F, Count, DecimalField
from django.db.models.functions import Coalesce
from django.utils import timezone
from decimal import Decimal
from datetime import datetime, timedelta

from .models import (
    SalesDepartment, SalesArea, StockItem, SpecialDeal, FuturePricing,
    ShrinkWrap, PackBundle, PackBundleIngredient, StockTransaction,
    StockTake, StockTakeItem, ContractPricing, OneTouchLookupKey,
    StockMonthlyStatistic
)
from .serializers import (
    SalesDepartmentSerializer, SalesAreaSerializer, StockItemListSerializer,
    StockItemDetailSerializer, StockItemCreateUpdateSerializer, SpecialDealSerializer,
    FuturePricingSerializer, ShrinkWrapSerializer, PackBundleSerializer,
    PackBundleIngredientSerializer, PackBundleCreateSerializer, StockTransactionSerializer,
    StockTransactionCreateSerializer, StockTakeSerializer, StockTakeItemSerializer,
    StockTakeCountSerializer, ContractPricingSerializer, OneTouchLookupKeySerializer,
    StockMonthlyStatisticSerializer, PriceAdjustmentSerializer, StockValuationSerializer,
    ManufactureItemSerializer
)


class SalesDepartmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Sales Departments
    
    list: Get all departments
    create: Create new department
    retrieve: Get department details
    update: Update department
    partial_update: Partially update department
    destroy: Delete department
    """
    queryset = SalesDepartment.objects.all()
    serializer_class = SalesDepartmentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['department_name', 'department_number']
    ordering_fields = ['department_number', 'department_name']
    ordering = ['department_number']
    
    @action(detail=True, methods=['get'])
    def stock_items(self, request, pk=None):
        """Get all stock items in this department"""
        department = self.get_object()
        items = StockItem.objects.filter(department=department)
        serializer = StockItemListSerializer(items, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def sales_statistics(self, request, pk=None):
        """Get sales statistics for this department"""
        department = self.get_object()
        items = StockItem.objects.filter(department=department)
        
        stats = {
            'total_items': items.count(),
            'active_items': items.filter(is_active=True).count(),
            'total_stock_value': sum(item.quantity_on_hand * item.cost_price for item in items),
            'mtd_sales': sum(item.sales_mtd_value for item in items),
            'ytd_sales': sum(item.sales_ytd_value for item in items),
        }
        
        return Response(stats)


class SalesAreaViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Sales Areas/Salesmen
    
    list: Get all areas
    create: Create new area
    retrieve: Get area details
    update: Update area
    partial_update: Partially update area
    destroy: Delete area
    """
    queryset = SalesArea.objects.all()
    serializer_class = SalesAreaSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['area_name', 'area_number']
    ordering_fields = ['area_number', 'area_name']
    ordering = ['area_number']


class StockItemViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Stock Items
    
    list: Get all stock items (lightweight)
    create: Create new stock item
    retrieve: Get detailed stock item
    update: Update stock item
    partial_update: Partially update stock item
    destroy: Delete stock item
    """
    queryset = StockItem.objects.select_related('department', 'supplier').all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['department', 'supplier', 'is_active', 'tax_code']
    search_fields = ['stock_code', 'description', 'supplier_code']
    ordering_fields = ['stock_code', 'description', 'cost_price', 'selling_price_1', 'quantity_on_hand']
    ordering = ['stock_code']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return StockItemListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return StockItemCreateUpdateSerializer
        return StockItemDetailSerializer
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """Advanced search with multiple criteria"""
        query = request.query_params.get('q', '')
        search_type = request.query_params.get('type', 'all')  # all, code, description, supplier_code
        
        queryset = self.get_queryset()
        
        if search_type == 'code':
            queryset = queryset.filter(stock_code__icontains=query)
        elif search_type == 'description':
            queryset = queryset.filter(description__icontains=query)
        elif search_type == 'supplier_code':
            queryset = queryset.filter(supplier_code__icontains=query)
        else:  # all
            queryset = queryset.filter(
                Q(stock_code__icontains=query) |
                Q(description__icontains=query) |
                Q(supplier_code__icontains=query)
            )
        
        serializer = StockItemListSerializer(queryset[:50], many=True)  # Limit to 50 results
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def bulk_lookup(self, request):
        """
        Fast bulk lookup for stock items - supports multiple lookup types.
        
        OPTION 1: Single lookup type (recommended)
        POST /api/stock-control/stock-items/bulk_lookup/
        {
            "lookup_by": "stock_code",  // or "supplier_code" or "description"
            "values": ["SKU001", "SKU002", "SKU003"],
            "include_fields": ["stock_code", "description", "quantity_on_hand", ...]  // optional
        }
        
        OPTION 2: Mixed lookup types
        {
            "lookup_by": "mixed",
            "values": [
                {"key": "SKU001", "type": "stock_code"},
                {"key": "SUP-ABC", "type": "supplier_code"},
                {"key": "Electronic", "type": "description"}
            ],
            "include_fields": [...]  // optional
        }
        
        BACKWARD COMPATIBILITY: Old format still works
        {
            "stock_codes": ["SKU001", "SKU002"],  // Maps to lookup_by='stock_code'
            "include_fields": [...]
        }
        """
        # Backward compatibility: convert old stock_codes format to new values format
        stock_codes = request.data.get('stock_codes')
        if stock_codes is not None:
            values = stock_codes
            lookup_by = 'stock_code'
        else:
            lookup_by = request.data.get('lookup_by', 'stock_code')
            values = request.data.get('values', [])
        
        include_fields = request.data.get('include_fields')
        
        # Validate input
        if not values:
            return Response(
                {'error': 'values is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not isinstance(values, list):
            return Response(
                {'error': 'values must be a list'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if len(values) > 500:
            return Response(
                {'error': 'Maximum 500 values per request'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate lookup_by parameter
        valid_lookup_types = ['stock_code', 'supplier_code', 'description', 'mixed']
        if lookup_by not in valid_lookup_types:
            return Response(
                {'error': f'lookup_by must be one of: {", ".join(valid_lookup_types)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Handle mixed lookup type
        if lookup_by == 'mixed':
            return self._handle_mixed_lookup(values, include_fields)
        
        # Handle single lookup type
        return self._handle_single_lookup(lookup_by, values, include_fields)
    
    def _handle_single_lookup(self, lookup_by, values, include_fields):
        """Handle single lookup type (stock_code, supplier_code, or description)"""
        
        # Build query based on lookup type
        if lookup_by == 'stock_code':
            items = StockItem.objects.filter(
                stock_code__in=values
            ).select_related('department', 'supplier')
            lookup_key = 'stock_code'
            lookup_field = 'stock_code'
            
        elif lookup_by == 'supplier_code':
            items = StockItem.objects.filter(
                supplier_code__in=values
            ).select_related('department', 'supplier')
            lookup_key = 'supplier_code'
            lookup_field = 'supplier_code'
            
        elif lookup_by == 'description':
            # For description, we need to do case-insensitive matching
            from django.db.models import Q
            query = Q()
            for value in values:
                query |= Q(description__icontains=value)
            items = StockItem.objects.filter(query).select_related('department', 'supplier')
            lookup_key = 'description'
            lookup_field = 'description'
        
        # Create lookup dict (handling multiple items with same value)
        items_dict = {}
        for item in items:
            key_value = getattr(item, lookup_field)
            if key_value not in items_dict:
                items_dict[key_value] = []
            items_dict[key_value].append(item)
        
        # Build response maintaining order and including nulls for missing values
        result = []
        for value in values:
            matches = items_dict.get(value, [])
            
            if not matches:
                result.append({
                    lookup_key: value,
                    'found': False,
                    'data': None
                })
            else:
                # For supplier_code and description, multiple items may match
                # Return first match, but note count
                item = matches[0]
                serialized = StockItemListSerializer(item).data
                
                # Filter to requested fields if specified
                if include_fields:
                    filtered_data = {
                        k: v for k, v in serialized.items() 
                        if k in include_fields or k == 'stock_code'
                    }
                else:
                    filtered_data = serialized
                
                result.append({
                    lookup_key: value,
                    'found': True,
                    'match_count': len(matches),  # Show if multiple items matched
                    'data': filtered_data
                })
        
        return Response({
            'lookup_by': lookup_by,
            'count': len([r for r in result if r['found']]),
            'total': len(result),
            'results': result
        })
    
    def _handle_mixed_lookup(self, values, include_fields):
        """Handle mixed lookup types in single request"""
        
        if not all(isinstance(v, dict) and 'key' in v and 'type' in v for v in values):
            return Response(
                {'error': 'mixed lookup requires list of {key, type} objects'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Build comprehensive query to fetch all potential matches
        from django.db.models import Q
        
        query = Q()
        for item in values:
            lookup_type = item.get('type')
            key_value = item.get('key')
            
            if lookup_type == 'stock_code':
                query |= Q(stock_code=key_value)
            elif lookup_type == 'supplier_code':
                query |= Q(supplier_code=key_value)
            elif lookup_type == 'description':
                query |= Q(description__icontains=key_value)
        
        all_items = StockItem.objects.filter(query).select_related('department', 'supplier')
        
        # Build lookup dicts for each type
        by_stock_code = {item.stock_code: item for item in all_items}
        by_supplier_code = {}
        by_description = {}
        
        for item in all_items:
            if item.supplier_code:
                if item.supplier_code not in by_supplier_code:
                    by_supplier_code[item.supplier_code] = []
                by_supplier_code[item.supplier_code].append(item)
            
            if item.description:
                if item.description.lower() not in by_description:
                    by_description[item.description.lower()] = []
                by_description[item.description.lower()].append(item)
        
        # Build response
        result = []
        for lookup_item in values:
            lookup_type = lookup_item.get('type')
            key_value = lookup_item.get('key')
            item = None
            match_count = 0
            
            if lookup_type == 'stock_code':
                item = by_stock_code.get(key_value)
                match_count = 1 if item else 0
            elif lookup_type == 'supplier_code':
                matches = by_supplier_code.get(key_value, [])
                if matches:
                    item = matches[0]
                    match_count = len(matches)
            elif lookup_type == 'description':
                matches = by_description.get(key_value.lower(), [])
                if matches:
                    item = matches[0]
                    match_count = len(matches)
            
            if item is None:
                result.append({
                    'lookup_key': key_value,
                    'lookup_type': lookup_type,
                    'found': False,
                    'data': None
                })
            else:
                serialized = StockItemListSerializer(item).data
                
                if include_fields:
                    filtered_data = {
                        k: v for k, v in serialized.items() 
                        if k in include_fields or k == 'stock_code'
                    }
                else:
                    filtered_data = serialized
                
                result.append({
                    'lookup_key': key_value,
                    'lookup_type': lookup_type,
                    'found': True,
                    'match_count': match_count,
                    'data': filtered_data
                })
        
        return Response({
            'lookup_by': 'mixed',
            'count': len([r for r in result if r['found']]),
            'total': len(result),
            'results': result
        })
    
    @action(detail=True, methods=['get'])
    def movement_history(self, request, pk=None):
        """Get movement history for a stock item"""
        stock_item = self.get_object()
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        transactions = StockTransaction.objects.filter(stock_item=stock_item)
        
        if start_date:
            transactions = transactions.filter(transaction_date__gte=start_date)
        if end_date:
            transactions = transactions.filter(transaction_date__lte=end_date)
        
        serializer = StockTransactionSerializer(transactions, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def sales_history(self, request, pk=None):
        """Get sales history for a stock item"""
        stock_item = self.get_object()
        
        # Get monthly statistics
        stats = StockMonthlyStatistic.objects.filter(stock_item=stock_item).order_by('-year', '-month')
        serializer = StockMonthlyStatisticSerializer(stats, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def below_reorder(self, request):
        """Get items below reorder level"""
        items = StockItem.objects.filter(
            quantity_on_hand__lte=F('reorder_quantity'),
            is_active=True
        ).exclude(reorder_quantity=0)
        
        serializer = StockItemListSerializer(items, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def negative_stock(self, request):
        """Get items with negative stock"""
        items = StockItem.objects.filter(quantity_on_hand__lt=0)
        serializer = StockItemListSerializer(items, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def slow_movers(self, request):
        """Get slow-moving items based on last sale date"""
        days = int(request.query_params.get('days', 90))
        cutoff_date = timezone.now().date() - timedelta(days=days)
        
        items = StockItem.objects.filter(
            Q(date_last_sold__lt=cutoff_date) | Q(date_last_sold__isnull=True),
            quantity_on_hand__gt=0,
            is_active=True
        )
        
        serializer = StockItemListSerializer(items, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def bulk_price_adjustment(self, request):
        """Bulk price adjustment for multiple items"""
        serializer = PriceAdjustmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        
        # Build queryset
        queryset = StockItem.objects.all()
        if data.get('department'):
            queryset = queryset.filter(department=data['department'])
        if data.get('supplier'):
            queryset = queryset.filter(supplier=data['supplier'])
        
        # Calculate adjustment multiplier
        amount = data['amount']
        if data['value_type'] == 'PERCENTAGE':
            if data['adjustment_type'] == 'INCREASE':
                multiplier = 1 + (amount / 100)
            else:
                multiplier = 1 - (amount / 100)
        else:  # RAND
            multiplier = None  # We'll add/subtract directly
        
        # Apply adjustments
        updated_count = 0
        for item in queryset:
            if data['price_type'] == 'COST':
                if multiplier:
                    item.cost_price = item.cost_price * Decimal(str(multiplier))
                else:
                    if data['adjustment_type'] == 'INCREASE':
                        item.cost_price = item.cost_price + amount
                    else:
                        item.cost_price = max(0, item.cost_price - amount)
            else:  # SELLING
                price_levels = data.get('price_levels', [1, 2, 3])
                for level in price_levels:
                    current_price = getattr(item, f'selling_price_{level}')
                    if multiplier:
                        new_price = current_price * Decimal(str(multiplier))
                    else:
                        if data['adjustment_type'] == 'INCREASE':
                            new_price = current_price + amount
                        else:
                            new_price = max(0, current_price - amount)
                    setattr(item, f'selling_price_{level}', new_price)
            
            item.save()
            updated_count += 1
        
        return Response({
            'message': f'Successfully updated {updated_count} items',
            'updated_count': updated_count
        })
    
    @action(detail=True, methods=['post'])
    def adjust_quantity(self, request, pk=None):
        """Adjust quantity for a stock item"""
        stock_item = self.get_object()
        new_quantity = Decimal(request.data.get('quantity', 0))
        reference = request.data.get('reference', 'Manual adjustment')
        
        # Create adjustment transaction
        quantity_diff = new_quantity - stock_item.quantity_on_hand
        
        transaction_data = {
            'transaction_type': 'ADJUSTMENT',
            'stock_item': stock_item.stock_code,
            'quantity_in': quantity_diff if quantity_diff > 0 else 0,
            'quantity_out': abs(quantity_diff) if quantity_diff < 0 else 0,
            'unit_cost': stock_item.cost_price,
            'reference': reference
        }
        
        transaction_serializer = StockTransactionCreateSerializer(data=transaction_data)
        transaction_serializer.is_valid(raise_exception=True)
        transaction_serializer.save()
        
        return Response({
            'message': 'Quantity adjusted successfully',
            'old_quantity': stock_item.quantity_on_hand,
            'new_quantity': new_quantity,
            'adjustment': quantity_diff
        })


class SpecialDealViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Special Deals
    
    list: Get all special deals
    create: Create new special deal
    retrieve: Get special deal details
    update: Update special deal
    partial_update: Partially update special deal
    destroy: Delete special deal
    """
    queryset = SpecialDeal.objects.select_related('stock_item').all()
    serializer_class = SpecialDealSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['stock_item', 'is_active']
    ordering_fields = ['start_date', 'end_date']
    ordering = ['-start_date']
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get currently active special deals"""
        today = timezone.now().date()
        deals = SpecialDeal.objects.filter(
            start_date__lte=today,
            end_date__gte=today,
            is_active=True
        )
        serializer = self.get_serializer(deals, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def bulk_create_department(self, request):
        """Create special deals for entire department"""
        department_id = request.data.get('department')
        adjustment_type = request.data.get('adjustment_type')  # + or -
        value_type = request.data.get('value_type')  # P or R
        amount = Decimal(request.data.get('amount', 0))
        price_levels = request.data.get('price_levels', [1, 2, 3])
        start_date = request.data.get('start_date')
        end_date = request.data.get('end_date')
        
        items = StockItem.objects.filter(department_id=department_id, is_active=True)
        created_deals = []
        
        for item in items:
            deal_data = {
                'stock_item': item.stock_code,
                'special_cost_price': item.cost_price,
                'start_date': start_date,
                'end_date': end_date,
                'is_active': True
            }
            
            # Calculate special prices
            for level in price_levels:
                current_price = getattr(item, f'selling_price_{level}')
                
                if value_type == 'P':  # Percentage
                    if adjustment_type == '+':
                        new_price = current_price * (1 + amount / 100)
                    else:
                        new_price = current_price * (1 - amount / 100)
                else:  # Rand
                    if adjustment_type == '+':
                        new_price = current_price + amount
                    else:
                        new_price = max(0, current_price - amount)
                
                deal_data[f'special_selling_price_{level}'] = new_price
                
                # Calculate markup
                if item.cost_price > 0:
                    markup = ((new_price - item.cost_price) / item.cost_price) * 100
                    deal_data[f'special_markup_{level}'] = markup
            
            deal = SpecialDeal.objects.create(**deal_data)
            created_deals.append(deal)
        
        serializer = self.get_serializer(created_deals, many=True)
        return Response({
            'message': f'Created {len(created_deals)} special deals',
            'deals': serializer.data
        }, status=status.HTTP_201_CREATED)


class FuturePricingViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Future Pricing
    
    list: Get all future prices
    create: Create new future price
    retrieve: Get future price details
    update: Update future price
    partial_update: Partially update future price
    destroy: Delete future price
    """
    queryset = FuturePricing.objects.select_related('stock_item').all()
    serializer_class = FuturePricingSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['stock_item', 'is_applied']
    ordering_fields = ['effective_date']
    ordering = ['effective_date']
    
    @action(detail=False, methods=['post'])
    def apply_future_prices(self, request):
        """Apply future prices that are due"""
        cutoff_date = request.data.get('cutoff_date', timezone.now().date())
        
        future_prices = FuturePricing.objects.filter(
            effective_date__lte=cutoff_date,
            is_applied=False
        )
        
        updated_count = 0
        for fp in future_prices:
            item = fp.stock_item
            item.cost_price = fp.future_cost_price
            item.selling_price_1 = fp.future_selling_price_1
            item.selling_price_2 = fp.future_selling_price_2
            item.selling_price_3 = fp.future_selling_price_3
            item.markup_1 = fp.future_markup_1
            item.markup_2 = fp.future_markup_2
            item.markup_3 = fp.future_markup_3
            item.save()
            
            fp.is_applied = True
            fp.save()
            updated_count += 1
        
        return Response({
            'message': f'Applied {updated_count} future prices',
            'updated_count': updated_count
        })