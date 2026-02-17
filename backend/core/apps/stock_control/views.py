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
    StockMonthlyStatistic, Branch, BranchStock, GroupOrder, GroupOrderItem,
    BranchTransfer, BranchTransferItem, BranchTransferInvoice
)
from .serializers import (
    SalesDepartmentSerializer, SalesAreaSerializer, StockItemListSerializer,
    StockItemDetailSerializer, StockItemCreateUpdateSerializer, SpecialDealSerializer,
    FuturePricingSerializer, ShrinkWrapSerializer, PackBundleSerializer,
    PackBundleIngredientSerializer, PackBundleCreateSerializer, StockTransactionSerializer,
    StockTransactionCreateSerializer, StockTakeSerializer, StockTakeItemSerializer,
    StockTakeCountSerializer, ContractPricingSerializer, OneTouchLookupKeySerializer,
    StockMonthlyStatisticSerializer, PriceAdjustmentSerializer, StockValuationSerializer,
    ManufactureItemSerializer, BranchSerializer, BranchStockSerializer, BranchStockDetailSerializer,
    GroupOrderSerializer, GroupOrderDetailSerializer, GroupOrderItemSerializer,
    BranchTransferSerializer, BranchTransferDetailSerializer, BranchTransferItemSerializer,
    BranchTransferInvoiceSerializer, BranchTransferInvoiceDetailSerializer
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


class ShrinkWrapViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Shrink/Wrap relationships (Bulk to Unit conversion)
    
    list: Get all shrink wrap relationships
    create: Create new relationship
    retrieve: Get relationship details
    update: Update relationship
    partial_update: Partially update relationship
    destroy: Delete relationship
    """
    queryset = ShrinkWrap.objects.select_related('shrink_pack_code', 'bulk_pack_code').all()
    serializer_class = ShrinkWrapSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['shrink_pack_code', 'bulk_pack_code']
    search_fields = ['shrink_pack_code__stock_code', 'bulk_pack_code__stock_code']


class PackBundleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Pack/Bundle (BOM - Bill of Materials)
    
    list: Get all pack/bundles
    create: Create new pack/bundle with ingredients
    retrieve: Get pack/bundle details
    update: Update pack/bundle
    partial_update: Partially update pack/bundle
    destroy: Delete pack/bundle
    """
    queryset = PackBundle.objects.select_related('stock_item').prefetch_related('ingredients').all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['stock_item']
    search_fields = ['stock_item__stock_code', 'stock_item__description']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return PackBundleCreateSerializer
        return PackBundleSerializer
    
    @action(detail=True, methods=['patch'])
    def update_total_cost(self, request, pk=None):
        """Recalculate total cost from ingredients"""
        bundle = self.get_object()
        total_cost = bundle.calculate_total_cost()
        return Response({
            'total_cost': float(total_cost),
            'message': 'Total cost updated'
        })


class StockTransactionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Stock Transactions (Transaction Ledger)
    
    list: Get all transactions
    create: Create new transaction
    retrieve: Get transaction details
    """
    queryset = StockTransaction.objects.select_related('stock_item', 'department', 'debtor', 'supplier').all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['stock_item', 'transaction_type', 'transaction_date']
    ordering_fields = ['transaction_date', 'created_at']
    ordering = ['-transaction_date']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return StockTransactionCreateSerializer
        return StockTransactionSerializer
    
    @action(detail=False, methods=['get'])
    def running_balance(self, request):
        """Get running balance for a stock item"""
        stock_code = request.query_params.get('stock_code')
        if not stock_code:
            return Response(
                {'error': 'stock_code parameter required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            stock_item = StockItem.objects.get(stock_code=stock_code)
        except StockItem.DoesNotExist:
            return Response(
                {'error': f'Stock item {stock_code} not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        transactions = StockTransaction.objects.filter(
            stock_item=stock_item
        ).order_by('transaction_date')
        
        serializer = StockTransactionSerializer(transactions, many=True)
        return Response({
            'stock_code': stock_code,
            'current_qoh': float(stock_item.quantity_on_hand),
            'transactions': serializer.data
        })


class StockTakeViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Stock Take (Physical Inventory Count)
    
    list: Get all stock takes
    create: Create new stock take
    retrieve: Get stock take details
    update: Update stock take
    partial_update: Partially update stock take
    """
    queryset = StockTake.objects.prefetch_related('items').all()
    serializer_class = StockTakeSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status']
    ordering_fields = ['stock_take_date']
    ordering = ['-stock_take_date']
    
    @action(detail=True, methods=['post'])
    def add_item(self, request, pk=None):
        """Add or update a counted item to stock take"""
        stock_take = self.get_object()
        serializer = StockTakeCountSerializer(data=request.data)
        
        if serializer.is_valid():
            stock_item = serializer.validated_data['stock_item']
            quantity_counted = serializer.validated_data['quantity_counted']
            add_to_previous = serializer.validated_data.get('add_to_previous', False)
            
            item, created = StockTakeItem.objects.get_or_create(
                stock_take=stock_take,
                stock_item=stock_item,
                defaults={
                    'quantity_on_hand': stock_item.quantity_on_hand,
                    'cost_price_at_count': stock_item.cost_price
                }
            )
            
            if add_to_previous and not created:
                quantity_counted += item.quantity_counted
            
            item.quantity_counted = quantity_counted
            item.is_counted = True
            item.count_date = timezone.now()
            item.calculate_variance()
            
            return Response(
                StockTakeItemSerializer(item).data,
                status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Mark stock take as completed"""
        stock_take = self.get_object()
        
        if stock_take.status != 'IN_PROGRESS':
            return Response(
                {'error': 'Can only complete stock takes in progress'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        stock_take.status = 'COMPLETED'
        stock_take.completed_at = timezone.now()
        stock_take.save()
        
        return Response(StockTakeSerializer(stock_take).data)
    
    @action(detail=True, methods=['post'])
    def post_to_inventory(self, request, pk=None):
        """Post stock take results to update inventory"""
        stock_take = self.get_object()
        
        if stock_take.status != 'COMPLETED':
            return Response(
                {'error': 'Can only post completed stock takes'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        updated_items = []
        for item in stock_take.items.all():
            stock_item = item.stock_item
            variance = item.quantity_counted - item.quantity_on_hand
            
            if variance != 0:
                # Create adjustment transaction
                StockTransaction.objects.create(
                    transaction_type='STOCK_TAKE',
                    stock_item=stock_item,
                    transaction_date=stock_take.stock_take_date,
                    quantity_in=variance if variance > 0 else 0,
                    quantity_out=abs(variance) if variance < 0 else 0,
                    value=abs(variance) * stock_item.cost_price,
                    comments=f'Stock take {stock_take.id} adjustment',
                    created_by=request.user.username if request.user.is_authenticated else 'system'
                )
                
                # Update stock item
                stock_item.quantity_on_hand = item.quantity_counted
                stock_item.closing_stock_balance = item.quantity_counted
                stock_item.save()
                updated_items.append(stock_item.stock_code)
        
        stock_take.status = 'UPDATED'
        stock_take.save()
        
        return Response({
            'message': 'Stock take posted to inventory',
            'stock_take_id': stock_take.id,
            'updated_items': updated_items,
            'total_updated': len(updated_items)
        })


class ContractPricingViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Contract Pricing (Debtor-specific pricing)
    
    list: Get all contracts
    create: Create new contract
    retrieve: Get contract details
    update: Update contract
    partial_update: Partially update contract
    destroy: Delete contract
    """
    queryset = ContractPricing.objects.select_related('debtor', 'stock_item', 'department', 'supplier').all()
    serializer_class = ContractPricingSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['debtor', 'pricing_method', 'is_active']
    search_fields = ['debtor__name', 'stock_item__stock_code']


class OneTouchLookupKeyViewSet(viewsets.ModelViewSet):
    """
    ViewSet for One-Touch POS Shortcuts
    
    list: Get all lookup keys
    create: Create new lookup key
    retrieve: Get lookup key details
    update: Update lookup key
    partial_update: Partially update lookup key
    destroy: Delete lookup key
    """
    queryset = OneTouchLookupKey.objects.select_related('stock_item').all()
    serializer_class = OneTouchLookupKeySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['key_character', 'stock_item__stock_code', 'stock_item__description']
    
    @action(detail=False, methods=['get'])
    def lookup_by_key(self, request):
        """Quick lookup by single character key"""
        key = request.query_params.get('key', '').upper()
        
        if not key or len(key) != 1:
            return Response(
                {'error': 'key parameter must be a single character'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            lookup_key = OneTouchLookupKey.objects.get(key_character=key)
            serializer = self.get_serializer(lookup_key)
            return Response(serializer.data)
        except OneTouchLookupKey.DoesNotExist:
            return Response(
                {'error': f'No lookup key found for character {key}'},
                status=status.HTTP_404_NOT_FOUND
            )


class StockMonthlyStatisticViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Stock Monthly Statistics (Read-only)
    
    list: Get all monthly statistics
    retrieve: Get monthly statistic details
    """
    queryset = StockMonthlyStatistic.objects.select_related('stock_item').all()
    serializer_class = StockMonthlyStatisticSerializer
    permission_classes = [IsAuthenticated]


# ============================================================================
# Phase 1: Branch Management ViewSets
# ============================================================================

class BranchViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Branch Management
    
    list: Get all branches
    create: Create new branch
    retrieve: Get branch details
    update: Update branch
    partial_update: Partially update branch
    destroy: Deactivate branch
    """
    queryset = Branch.objects.all()
    serializer_class = BranchSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'is_default', 'branch_type']
    search_fields = ['branch_code', 'branch_name', 'address']
    ordering_fields = ['branch_code', 'branch_name', 'created_at']
    ordering = ['branch_code']
    lookup_field = 'branch_code'


class BranchStockViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Branch Stock Management
    
    list: Get all branch stocks
    create: Create new branch stock entry
    retrieve: Get branch stock details
    update: Update branch stock
    partial_update: Partially update branch stock
    destroy: Delete branch stock entry
    
    Custom Actions:
    - adjust/: Adjust stock quantity
    """
    queryset = BranchStock.objects.select_related('branch', 'stock_item').all()
    serializer_class = BranchStockSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['branch', 'stock_item']
    search_fields = ['branch__branch_code', 'stock_item__stock_code', 'stock_item__description']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return BranchStockDetailSerializer
        return BranchStockSerializer
    
    @action(detail=True, methods=['post'])
    def adjust(self, request, pk=None):
        """Adjust stock quantity at branch"""
        branch_stock = self.get_object()
        adjustment_type = request.data.get('adjustment_type')  # 'ADD' or 'SUBTRACT'
        quantity = Decimal(str(request.data.get('quantity', 0)))
        reason = request.data.get('reason', '')
        
        if adjustment_type == 'ADD':
            branch_stock.quantity += quantity
        elif adjustment_type == 'SUBTRACT':
            branch_stock.quantity = max(Decimal('0'), branch_stock.quantity - quantity)
        else:
            return Response(
                {'error': 'adjustment_type must be ADD or SUBTRACT'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        branch_stock.save()
        
        # Create transaction record
        StockTransaction.objects.create(
            transaction_type='ADJUSTMENT',
            stock_item=branch_stock.stock_item,
            quantity_in=quantity if adjustment_type == 'ADD' else 0,
            quantity_out=quantity if adjustment_type == 'SUBTRACT' else 0,
            reference=f"Branch {branch_stock.branch.branch_code}: {reason}",
            comments=reason
        )
        
        serializer = self.get_serializer(branch_stock)
        return Response(serializer.data)


# ============================================================================
# Phase 3: Group Order ViewSets
# ============================================================================

class GroupOrderViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Group Orders
    
    list: Get all group orders
    create: Create new group order
    retrieve: Get group order details
    update: Update group order
    partial_update: Partially update group order
    destroy: Delete group order
    
    Custom Actions:
    - submit/: Submit group order for processing
    - cancel/: Cancel group order
    """
    queryset = GroupOrder.objects.select_related('branch', 'created_by').prefetch_related('items').all()
    serializer_class = GroupOrderSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'branch']
    search_fields = ['group_order_number']
    ordering_fields = ['order_date', 'group_order_number', 'created_at']
    ordering = ['-order_date']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return GroupOrderDetailSerializer
        return GroupOrderSerializer
    
    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        """Submit group order for processing"""
        group_order = self.get_object()
        
        if group_order.status != 'DRAFT':
            return Response(
                {'error': 'Only draft orders can be submitted'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        group_order.status = 'ACTIVE'
        group_order.save()
        
        serializer = self.get_serializer(group_order)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel group order"""
        group_order = self.get_object()
        
        if group_order.status not in ['DRAFT', 'ACTIVE']:
            return Response(
                {'error': 'Only draft or active orders can be cancelled'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        group_order.status = 'CANCELLED'
        group_order.save()
        
        serializer = self.get_serializer(group_order)
        return Response(serializer.data)


# ============================================================================
# Phase 4: IBT - Inter-Branch Transfer ViewSets
# ============================================================================

class BranchTransferViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Branch Transfers (IBT)
    
    list: Get all branch transfers
    create: Create new transfer request
    retrieve: Get transfer details
    update: Update transfer
    partial_update: Partially update transfer
    destroy: Delete transfer (only draft)
    
    Custom Actions:
    - submit/: Submit transfer for approval
    - approve/: Approve transfer
    - dispatch/: Dispatch transfer items
    - receive/: Receive transfer items
    - cancel/: Cancel transfer
    - pending/: List pending approvals
    - in_transit/: List currently in-transit transfers
    """
    queryset = BranchTransfer.objects.select_related(
        'from_branch', 'to_branch', 'requested_by', 'approved_by',
        'dispatched_by', 'received_by'
    ).prefetch_related('items').all()
    serializer_class = BranchTransferSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'from_branch', 'to_branch', 'transfer_type']
    search_fields = ['transfer_number']
    ordering_fields = ['requested_date', 'transfer_number', 'status']
    ordering = ['-requested_date']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return BranchTransferDetailSerializer
        return BranchTransferSerializer
    
    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        """Submit transfer for approval"""
        transfer = self.get_object()
        
        if transfer.status != 'DRAFT':
            return Response(
                {'error': 'Can only submit draft transfers'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not transfer.items.exists():
            return Response(
                {'error': 'Transfer must have at least one item'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        transfer.status = 'PENDING'
        transfer.save()
        
        serializer = self.get_serializer(transfer)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve transfer"""
        transfer = self.get_object()
        
        if transfer.status != 'PENDING':
            return Response(
                {'error': 'Can only approve pending transfers'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check stock availability at source
        for item in transfer.items.all():
            branch_stock = BranchStock.objects.get(
                branch=transfer.from_branch,
                stock_item=item.stock_item
            )
            if branch_stock.quantity < item.quantity_requested:
                return Response(
                    {'error': f'Insufficient stock for {item.stock_item.stock_code}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        transfer.status = 'APPROVED'
        transfer.approved_by = request.user
        transfer.approved_date = timezone.now()
        transfer.save()
        
        serializer = self.get_serializer(transfer)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def dispatch(self, request, pk=None):
        """Dispatch transfer - reduce source stock"""
        transfer = self.get_object()
        
        if transfer.status != 'APPROVED':
            return Response(
                {'error': 'Can only dispatch approved transfers'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        for item in transfer.items.all():
            # Deduct from source branch
            branch_stock = BranchStock.objects.get(
                branch=transfer.from_branch,
                stock_item=item.stock_item
            )
            branch_stock.quantity -= item.quantity_requested
            branch_stock.save()
            
            item.quantity_dispatched = item.quantity_requested
            item.save()
            
            # Create stock transaction
            StockTransaction.objects.create(
                transaction_type='IBT_OUT',
                stock_item=item.stock_item,
                quantity_out=item.quantity_requested,
                reference=transfer.transfer_number,
                comments=f"Dispatched from {transfer.from_branch.branch_code} to {transfer.to_branch.branch_code}"
            )
        
        transfer.status = 'DISPATCHED'
        transfer.dispatched_by = request.user
        transfer.dispatched_date = timezone.now()
        transfer.save()
        
        serializer = self.get_serializer(transfer)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def receive(self, request, pk=None):
        """Receive transfer - add to destination stock"""
        transfer = self.get_object()
        
        if transfer.status != 'DISPATCHED':
            return Response(
                {'error': 'Can only receive dispatched transfers'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        for item in transfer.items.all():
            quantity_received = Decimal(str(request.data.get(f'quantity_received_{item.id}', item.quantity_dispatched)))
            
            # Add to destination branch
            branch_stock, created = BranchStock.objects.get_or_create(
                branch=transfer.to_branch,
                stock_item=item.stock_item,
                defaults={'quantity': 0}
            )
            branch_stock.quantity += quantity_received
            branch_stock.save()
            
            item.quantity_received = quantity_received
            item.save()
            
            # Create stock transaction
            StockTransaction.objects.create(
                transaction_type='IBT_IN',
                stock_item=item.stock_item,
                quantity_in=quantity_received,
                reference=transfer.transfer_number,
                comments=f"Received at {transfer.to_branch.branch_code} from {transfer.from_branch.branch_code}"
            )
        
        transfer.status = 'RECEIVED'
        transfer.received_by = request.user
        transfer.received_date = timezone.now()
        transfer.save()
        
        serializer = self.get_serializer(transfer)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel transfer (only before dispatch)"""
        transfer = self.get_object()
        
        if transfer.status in ['DISPATCHED', 'IN_TRANSIT', 'RECEIVED', 'COMPLETED', 'CANCELLED']:
            return Response(
                {'error': 'Cannot cancel transfer in current status'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        transfer.status = 'CANCELLED'
        transfer.save()
        
        serializer = self.get_serializer(transfer)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def pending(self, request):
        """Get all pending approvals"""
        transfers = self.queryset.filter(status='PENDING')
        serializer = self.get_serializer(transfers, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def in_transit(self, request):
        """Get all currently in-transit transfers"""
        transfers = self.queryset.filter(status__in=['DISPATCHED', 'IN_TRANSIT'])
        serializer = self.get_serializer(transfers, many=True)
        return Response(serializer.data)


# ============================================================================
# Phase 5: IBI - Inter-Branch Invoicing ViewSets
# ============================================================================

class BranchTransferInvoiceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Branch Transfer Invoices (IBI)
    
    list: Get all IBI invoices
    create: Create new IBI invoice
    retrieve: Get invoice details
    update: Update invoice
    partial_update: Partially update invoice
    destroy: Delete invoice (only draft)
    
    Custom Actions:
    - issue/: Issue invoice
    - mark_paid/: Mark invoice as paid
    - generate_from_transfer/: Generate invoice from transfer
    """
    queryset = BranchTransferInvoice.objects.select_related('transfer').all()
    serializer_class = BranchTransferInvoiceSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status']
    search_fields = ['invoice_number', 'transfer__transfer_number']
    ordering_fields = ['invoice_date', 'invoice_number']
    ordering = ['-invoice_date']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return BranchTransferInvoiceDetailSerializer
        return BranchTransferInvoiceSerializer
    
    @action(detail=True, methods=['post'])
    def issue(self, request, pk=None):
        """Issue invoice"""
        invoice = self.get_object()
        
        if invoice.status != 'DRAFT':
            return Response(
                {'error': 'Only draft invoices can be issued'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        invoice.status = 'ISSUED'
        invoice.save()
        
        serializer = self.get_serializer(invoice)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def mark_paid(self, request, pk=None):
        """Mark invoice as paid"""
        invoice = self.get_object()
        
        if invoice.status not in ['ISSUED']:
            return Response(
                {'error': 'Can only mark issued invoices as paid'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        invoice.status = 'PAID'
        invoice.save()
        
        serializer = self.get_serializer(invoice)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def generate_from_transfer(self, request):
        """Generate invoice from transfer"""
        transfer_id = request.data.get('transfer_id')
        
        try:
            transfer = BranchTransfer.objects.get(id=transfer_id)
        except BranchTransfer.DoesNotExist:
            return Response(
                {'error': 'Transfer not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if invoice already exists
        if hasattr(transfer, 'invoice'):
            return Response(
                {'error': 'Invoice already exists for this transfer'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Calculate totals from transfer items
        subtotal = Decimal('0')
        for item in transfer.items.all():
            line_total = item.quantity_received * item.stock_item.cost_price
            subtotal += line_total
        
        # Calculate VAT (assuming 15% VAT)
        vat_amount = subtotal * Decimal('0.15')
        total_amount = subtotal + vat_amount
        
        # Generate invoice number
        invoice_count = BranchTransferInvoice.objects.count() + 1
        invoice_number = f"IBI-{timezone.now().year}-{invoice_count:04d}"
        
        invoice = BranchTransferInvoice.objects.create(
            transfer=transfer,
            invoice_number=invoice_number,
            subtotal=subtotal,
            vat_amount=vat_amount,
            total_amount=total_amount,
            status='DRAFT'
        )
        
        serializer = self.get_serializer(invoice)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['stock_item', 'year', 'month']
    ordering_fields = ['year', 'month']
    ordering = ['-year', '-month']