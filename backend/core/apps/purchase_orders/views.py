from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Sum, F, Count, Prefetch
from django.utils import timezone
from decimal import Decimal
from datetime import datetime, timedelta

from apps.creditors.models import Creditor, GoodsReceivedNote, GRNLineItem
from apps.stock_control.models import StockItem, StockTransaction

from .models import (
    PurchaseOrder, PurchaseOrderLine, PurchaseOrderReceipt,
    PurchaseOrderReceiptLine, BackOrder, PurchaseOrderTemplate,
    PurchaseOrderTemplateLine
)
from .serializers import (
    PurchaseOrderListSerializer, PurchaseOrderDetailSerializer,
    PurchaseOrderCreateSerializer, PurchaseOrderLineSerializer,
    PurchaseOrderReceiptSerializer, PurchaseOrderReceiptLineSerializer,
    StockReceiptSerializer, BackOrderSerializer,
    PurchaseOrderTemplateSerializer, PurchaseOrderTemplateCreateSerializer,
    OutstandingPOReportSerializer, StockOnOrderSerializer,
    PreOrderReportSerializer, DeliveryVarianceReportSerializer
)


class PurchaseOrderViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Purchase Order management
    
    list: Get all purchase orders
    create: Create new purchase order
    retrieve: Get purchase order details
    update: Update purchase order
    partial_update: Partially update purchase order
    destroy: Delete purchase order
    """
    queryset = PurchaseOrder.objects.select_related('supplier').prefetch_related('line_items').all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['supplier', 'status', 'order_date', 'delivery_date']
    search_fields = ['order_number', 'supplier__name']
    ordering_fields = ['order_number', 'order_date', 'delivery_date', 'total_value_inclusive']
    ordering = ['-order_date']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return PurchaseOrderListSerializer
        elif self.action == 'create':
            return PurchaseOrderCreateSerializer
        return PurchaseOrderDetailSerializer
    
    def create(self, request, *args, **kwargs):
        """Create purchase order with options for item extraction"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        
        from creditors.models import Supplier
        from stock_control.models import StockItem
        
        supplier = Supplier.objects.get(account_number=data['supplier'])
        
        # Create purchase order
        order = PurchaseOrder.objects.create(
            supplier=supplier,
            order_date=data.get('order_date', timezone.now().date()),
            delivery_date=data['delivery_date'],
            pricing_method=data.get('pricing_method', 'COST'),
            notes=data.get('notes', '')
        )
        
        line_number = 1
        
        # Extract items based on options
        if data.get('extract_all_items'):
            items = StockItem.objects.filter(supplier=supplier, is_active=True)
            
            if data.get('department'):
                items = items.filter(sales_department_id=data['department'])
            
            for item in items:
                self._create_order_line(order, line_number, item, data['pricing_method'])
                line_number += 1
        
        elif data.get('extract_below_reorder'):
            items = StockItem.objects.filter(
                supplier=supplier,
                is_active=True,
                quantity_on_hand__lte=F('reorder_quantity')
            )
            
            if data.get('department'):
                items = items.filter(sales_department_id=data['department'])
            
            for item in items:
                # Calculate suggested order quantity
                shortfall = item.reorder_quantity - item.quantity_on_hand
                suggested_qty = max(shortfall, item.sales_mtd_quantity or 0)
                
                self._create_order_line(
                    order, line_number, item,
                    data['pricing_method'],
                    quantity=suggested_qty
                )
                line_number += 1
        
        # Manual line items
        if data.get('line_items'):
            for line_data in data['line_items']:
                stock_item = StockItem.objects.get(stock_code=line_data['stock_item'])
                
                unit_cost = line_data.get('unit_cost')
                if not unit_cost:
                    unit_cost = stock_item.cost_price if data['pricing_method'] == 'COST' else stock_item.retail_price_1
                
                PurchaseOrderLine.objects.create(
                    purchase_order=order,
                    line_number=line_number,
                    stock_item=stock_item,
                    quantity_ordered=line_data['quantity_ordered'],
                    unit_cost=unit_cost,
                    tax_code=line_data.get('tax_code', 1),
                    quantity_on_hand_at_order=stock_item.quantity_on_hand,
                    monthly_sales_at_order=stock_item.sales_mtd_quantity
                )
                line_number += 1
        
        # Calculate totals and update stock on order
        order.calculate_totals()
        self._update_stock_on_order(order)
        
        return Response(
            PurchaseOrderDetailSerializer(order).data,
            status=status.HTTP_201_CREATED
        )
    
    def _create_order_line(self, order, line_number, stock_item, pricing_method, quantity=None):
        """Helper to create order line"""
        if pricing_method == 'COST':
            unit_cost = stock_item.cost_price
        else:
            unit_cost = stock_item.retail_price_1
        
        if not quantity:
            quantity = stock_item.sales_mtd_quantity or 1
        
        PurchaseOrderLine.objects.create(
            purchase_order=order,
            line_number=line_number,
            stock_item=stock_item,
            quantity_ordered=quantity,
            unit_cost=unit_cost,
            tax_code=stock_item.tax_code,
            quantity_on_hand_at_order=stock_item.quantity_on_hand,
            monthly_sales_at_order=stock_item.sales_mtd_quantity
        )
    
    def _update_stock_on_order(self, order):
        """Update stock item on-order quantities"""
        for line in order.line_items.all():
            stock_item = line.stock_item
            stock_item.quantity_on_order += line.quantity_outstanding
            stock_item.save()
    
    @action(detail=True, methods=['post'])
    def cancel_order(self, request, pk=None):
        """Cancel a purchase order"""
        order = self.get_object()
        
        if order.status == 'FULLY_RECEIVED':
            return Response(
                {'error': 'Cannot cancel fully received order'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if order.status == 'CANCELLED':
            return Response(
                {'error': 'Order already cancelled'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update stock on order quantities
        for line in order.line_items.all():
            stock_item = line.stock_item
            stock_item.quantity_on_order -= line.quantity_outstanding
            stock_item.save()
        
        # Cancel order
        order.status = 'CANCELLED'
        order.save()
        
        return Response({
            'message': 'Purchase order cancelled successfully',
            'order': PurchaseOrderDetailSerializer(order).data
        })
    
    @action(detail=True, methods=['post'])
    def receive_stock(self, request, pk=None):
        """Receive stock against purchase order"""
        order = self.get_object()
        
        serializer = StockReceiptSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        
        # Create GRN
        receipt = PurchaseOrderReceipt.objects.create(
            purchase_order=order,
            receipt_date=data.get('receipt_date', timezone.now().date()),
            invoice_number=data['invoice_number']
        )
        
        receipt_line_number = 1
        has_variance = False
        
        for line_data in data['line_items']:
            po_line = PurchaseOrderLine.objects.get(id=line_data['purchase_order_line_id'])
            
            if po_line.purchase_order != order:
                return Response(
                    {'error': f'Line {po_line.id} does not belong to this order'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            quantity = line_data['quantity_received']
            actual_cost = line_data.get('actual_unit_cost', po_line.unit_cost)
            
            # Check variance
            if quantity != po_line.quantity_outstanding or actual_cost != po_line.unit_cost:
                has_variance = True
            
            # Create receipt line
            receipt_line = PurchaseOrderReceiptLine.objects.create(
                receipt=receipt,
                purchase_order_line=po_line,
                quantity_received=quantity,
                actual_unit_cost=actual_cost
            )
            receipt_line_number += 1
            
            # Update PO line
            po_line.quantity_received += quantity
            po_line.quantity_outstanding = po_line.quantity_ordered - po_line.quantity_received
            po_line.save()
            
            # Update stock item quantity
            stock_item = po_line.stock_item
            stock_item.quantity_on_hand += quantity
            stock_item.quantity_on_order -= quantity
            
            # Update cost if different
            if actual_cost != stock_item.cost_price:
                stock_item.cost_price = actual_cost
                # Update selling prices based on markup if supplier has auto-update enabled
                if order.supplier.update_selling_price_on_receipt:
                    stock_item.calculate_markups()
            
            stock_item.save()
            
            # Create stock transaction
            StockTransaction.objects.create(
                transaction_type='INCOMING',
                stock_item=stock_item,
                quantity_in=quantity,
                unit_cost=actual_cost,
                transaction_number=f"GRN-{receipt.id}",
                reference=f"PO {order.order_number} - {data['invoice_number']}"
            )
        
        # Calculate receipt totals
        receipt.has_variance = has_variance
        receipt.calculate_totals()
        
        # Update order status
        order.calculate_totals()
        
        # Update to creditors if requested
        if data.get('update_supplier_account', True):
            # Create Goods Received Note
            grn = GoodsReceivedNote.objects.create(
                creditor=order.supplier,
                transaction_date=receipt.receipt_date,
                supplier_invoice_number=data['invoice_number'],
                total_amount=receipt.total_inclusive
            )
            
            # Create GRN line items
            for idx, receipt_line in enumerate(receipt.line_items.all(), 1):
                GRNLineItem.objects.create(
                    grn=grn,
                    line_number=idx,
                    stock_item=receipt_line.purchase_order_line.stock_item,
                    quantity_received=receipt_line.quantity_received,
                    unit_cost=receipt_line.actual_unit_cost,
                    tax_code_id=receipt_line.purchase_order_line.tax_code
                )
            
            receipt.creditor_grn = grn
            receipt.save()
        
        # Create back order if requested and there are short deliveries
        if data.get('create_back_order'):
            short_lines = [
                line for line in order.line_items.all()
                if line.quantity_outstanding > 0
            ]
            
            if short_lines:
                back_order = PurchaseOrder.objects.create(
                    supplier=order.supplier,
                    order_date=timezone.now().date(),
                    delivery_date=timezone.now().date() + timedelta(days=7),
                    pricing_method=order.pricing_method,
                    is_back_order=True,
                    parent_order=order,
                    notes=f"Back order from PO {order.order_number}"
                )
                
                bo_line_number = 1
                for line in short_lines:
                    PurchaseOrderLine.objects.create(
                        purchase_order=back_order,
                        line_number=bo_line_number,
                        stock_item=line.stock_item,
                        quantity_ordered=line.quantity_outstanding,
                        unit_cost=line.unit_cost,
                        tax_code=line.tax_code,
                        quantity_on_hand_at_order=line.stock_item.quantity_on_hand,
                        monthly_sales_at_order=line.stock_item.sales_mtd_quantity
                    )
                    bo_line_number += 1
                
                back_order.calculate_totals()
                self._update_stock_on_order(back_order)
        
        return Response({
            'message': 'Stock received successfully',
            'receipt': PurchaseOrderReceiptSerializer(receipt).data,
            'order': PurchaseOrderDetailSerializer(order).data
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'])
    def outstanding(self, request):
        """Get all outstanding purchase orders"""
        orders = self.get_queryset().exclude(status__in=['FULLY_RECEIVED', 'CANCELLED'])
        
        # Filter by overdue if requested
        if request.query_params.get('overdue') == 'true':
            orders = orders.filter(delivery_date__lt=timezone.now().date())
        
        serializer = PurchaseOrderListSerializer(orders, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_supplier(self, request):
        """Get orders grouped by supplier"""
        supplier_id = request.query_params.get('supplier')
        
        if not supplier_id:
            return Response(
                {'error': 'Supplier ID required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        orders = self.get_queryset().filter(supplier_id=supplier_id)
        
        status_filter = request.query_params.get('status')
        if status_filter:
            orders = orders.filter(status=status_filter)
        
        serializer = PurchaseOrderListSerializer(orders, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def delivery_variance_report(self, request):
        """Generate delivery variance report"""
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        queryset = self.get_queryset()
        
        if start_date:
            queryset = queryset.filter(order_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(order_date__lte=end_date)
        
        variances = []
        
        for order in queryset:
            for line in order.line_items.all():
                if line.quantity_received != line.quantity_ordered:
                    # Find the receipt with variance
                    for receipt_line in line.receipt_lines.all():
                        variance_data = {
                            'order_number': order.order_number,
                            'supplier_name': order.supplier.name,
                            'stock_code': line.stock_item.stock_code,
                            'description': line.stock_item.description,
                            'quantity_ordered': line.quantity_ordered,
                            'quantity_received': receipt_line.quantity_received,
                            'quantity_short': line.quantity_ordered - receipt_line.quantity_received,
                            'ordered_cost': line.unit_cost,
                            'actual_cost': receipt_line.actual_unit_cost,
                            'cost_variance': receipt_line.actual_unit_cost - line.unit_cost,
                            'value_variance': (
                                (receipt_line.actual_unit_cost - line.unit_cost) *
                                receipt_line.quantity_received
                            )
                        }
                        variances.append(variance_data)
        
        serializer = DeliveryVarianceReportSerializer(variances, many=True)
        return Response(serializer.data)


class PurchaseOrderReceiptViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Goods Received Notes (Read-only)
    
    Receipts are created through the purchase order receive_stock action
    """
    queryset = PurchaseOrderReceipt.objects.select_related('purchase_order', 'creditor_transaction').prefetch_related('line_items').all()
    serializer_class = PurchaseOrderReceiptSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['purchase_order', 'receipt_date', 'has_variance']
    ordering_fields = ['receipt_date', 'id']
    ordering = ['-receipt_date']


class BackOrderViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Back Orders (Read-only)
    
    Back orders are created automatically from delivery variances
    """
    queryset = BackOrder.objects.select_related('original_order', 'back_order').all()
    serializer_class = BackOrderSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['original_order', 'back_order']
    ordering = ['-created_date']


class PurchaseOrderTemplateViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Purchase Order Templates
    
    list: Get all templates
    create: Create new template
    retrieve: Get template details
    update: Update template
    partial_update: Partially update template
    destroy: Delete template
    """
    queryset = PurchaseOrderTemplate.objects.select_related('supplier').prefetch_related('line_items').all()
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['template_name', 'supplier__name']
    ordering_fields = ['template_name', 'created_at']
    ordering = ['template_name']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return PurchaseOrderTemplateCreateSerializer
        return PurchaseOrderTemplateSerializer
    
    def create(self, request, *args, **kwargs):
        """Create template with line items"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        
        supplier = Creditor.objects.get(id=data['supplier'])
        
        template = PurchaseOrderTemplate.objects.create(
            template_name=data['template_name'],
            supplier=supplier,
            description=data.get('description', ''),
            default_delivery_days=data.get('default_delivery_days', 7),
            pricing_method=data.get('pricing_method', 'COST')
        )
        
        for idx, line_data in enumerate(data['line_items'], 1):
            stock_item = StockItem.objects.get(stock_code=line_data['stock_item'])
            
            PurchaseOrderTemplateLine.objects.create(
                template=template,
                line_number=idx,
                stock_item=stock_item,
                default_quantity=line_data['default_quantity']
            )
        
        return Response(
            PurchaseOrderTemplateSerializer(template).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['post'])
    def create_order_from_template(self, request, pk=None):
        """Create purchase order from template"""
        template = self.get_object()
        
        delivery_date_str = request.data.get('delivery_date')
        if delivery_date_str:
            from datetime import datetime
            delivery_date = datetime.strptime(delivery_date_str, '%Y-%m-%d').date()
        else:
            delivery_date = None
        
        order = template.create_order(delivery_date)
        
        # Update stock on order
        for line in order.line_items.all():
            stock_item = line.stock_item
            stock_item.quantity_on_order += line.quantity_outstanding
            stock_item.save()
        
        return Response({
            'message': 'Purchase order created from template',
            'order': PurchaseOrderDetailSerializer(order).data
        }, status=status.HTTP_201_CREATED)


class PurchaseOrderReportViewSet(viewsets.ViewSet):
    """ViewSet for purchase order reports"""
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def stock_on_order(self, request):
        """Report showing stock on order"""
        from stock_control.models import StockItem
        
        items = StockItem.objects.filter(quantity_on_order__gt=0)
        
        supplier_id = request.query_params.get('supplier')
        if supplier_id:
            items = items.filter(supplier_id=supplier_id)
        
        report_data = []
        
        for item in items:
            # Get all outstanding orders for this item
            orders = []
            po_lines = PurchaseOrderLine.objects.filter(
                stock_item=item,
                quantity_outstanding__gt=0,
                purchase_order__status__in=['OUTSTANDING', 'PARTIALLY_RECEIVED']
            ).select_related('purchase_order')
            
            for line in po_lines:
                orders.append({
                    'order_number': line.purchase_order.order_number,
                    'supplier': line.purchase_order.supplier.name,
                    'quantity': float(line.quantity_outstanding),
                    'delivery_date': line.purchase_order.delivery_date
                })
            
            report_data.append({
                'stock_code': item.stock_code,
                'description': item.description,
                'quantity_on_hand': item.quantity_on_hand,
                'quantity_on_order': item.quantity_on_order,
                'reorder_quantity': item.reorder_quantity,
                'orders': orders
            })
        
        serializer = StockOnOrderSerializer(report_data, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def pre_order_report(self, request):
        """Pre-order planning report"""
        from stock_control.models import StockItem
        
        supplier_id = request.query_params.get('supplier')
        
        # Items below reorder level
        items = StockItem.objects.filter(
            quantity_on_hand__lte=F('reorder_quantity'),
            is_active=True
        )
        
        if supplier_id:
            items = items.filter(supplier_id=supplier_id)
        
        report_data = []
        
        for item in items:
            shortfall = item.reorder_quantity - item.quantity_on_hand
            suggested_qty = max(shortfall, item.sales_mtd_quantity or 0)
            
            report_data.append({
                'stock_code': item.stock_code,
                'description': item.description,
                'supplier_name': item.supplier.name if item.supplier else '',
                'quantity_on_hand': item.quantity_on_hand,
                'reorder_quantity': item.reorder_quantity,
                'monthly_sales_avg': item.sales_mtd_quantity,
                'suggested_order_qty': suggested_qty,
                'last_cost': item.cost_price,
                'estimated_value': suggested_qty * item.cost_price
            })
        
        serializer = PreOrderReportSerializer(report_data, many=True)
        return Response(serializer.data)