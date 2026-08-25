from rest_framework import serializers
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone
from .models import (
    PurchaseOrder, PurchaseOrderLine, PurchaseOrderReceipt,
    PurchaseOrderReceiptLine, BackOrder, PurchaseOrderTemplate,
    PurchaseOrderTemplateLine
)


class PurchaseOrderLineSerializer(serializers.ModelSerializer):
    """Serializer for purchase order line items"""
    stock_code = serializers.CharField(source='stock_item.stock_code', read_only=True)
    stock_description = serializers.CharField(source='stock_item.description', read_only=True)
    supplier_code = serializers.CharField(source='stock_item.supplier_code', read_only=True)
    
    # Calculated fields
    quantity_on_hand = serializers.DecimalField(
        source='stock_item.quantity_on_hand',
        read_only=True,
        max_digits=10,
        decimal_places=2
    )
    current_cost = serializers.DecimalField(
        source='stock_item.cost_price',
        read_only=True,
        max_digits=10,
        decimal_places=2
    )
    
    class Meta:
        model = PurchaseOrderLine
        fields = '__all__'
        read_only_fields = [
            'quantity_delivered', 'quantity_outstanding', 'total_exclusive', 'total_vat',
            'total_inclusive', 'outstanding_exclusive', 'outstanding_vat', 'outstanding_inclusive',
            'quantity_on_hand_at_order', 'monthly_sales_at_order', 'is_fully_received',
            'created_at', 'updated_at'
        ]


class PurchaseOrderListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for purchase order lists"""
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_overdue = serializers.SerializerMethodField()
    
    class Meta:
        model = PurchaseOrder
        fields = [
            'order_number', 'supplier', 'supplier_name', 'order_date', 'delivery_date',
            'status', 'status_display', 'quantity_ordered', 'total_quantity_outstanding',
            'outstanding_value_inclusive', 'is_overdue', 'is_back_order'
        ]

    def get_is_overdue(self, obj):
        if obj.status in ['F', 'C']:
            return False
        return obj.delivery_date < timezone.now().date()


class PurchaseOrderDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for purchase orders"""
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    supplier_account = serializers.CharField(source='supplier.our_account_number', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    pricing_method_display = serializers.CharField(source='get_pricing_method_display', read_only=True)
    
    line_items = PurchaseOrderLineSerializer(many=True, read_only=True)
    
    is_overdue = serializers.SerializerMethodField()
    days_until_delivery = serializers.SerializerMethodField()
    completion_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = PurchaseOrder
        fields = '__all__'
        read_only_fields = [
            'status', 'quantity_ordered', 'total_quantity_received', 'total_quantity_outstanding',
            'total_value_exclusive', 'total_value_vat', 'total_value_inclusive',
            'outstanding_value_exclusive', 'outstanding_value_vat', 'outstanding_value_inclusive',
            'cancelled_at', 'created_at', 'updated_at'
        ]

    def get_is_overdue(self, obj):
        if obj.status in ['F', 'C']:
            return False
        return obj.delivery_date < timezone.now().date()

    def get_days_until_delivery(self, obj):
        delta = obj.delivery_date - timezone.now().date()
        return delta.days

    def get_completion_percentage(self, obj):
        if obj.quantity_ordered == 0:
            return 0
        return (obj.total_quantity_received / obj.quantity_ordered) * 100


class PurchaseOrderCreateLineSerializer(serializers.Serializer):
    """Serializer for creating PO line items"""
    stock_item = serializers.CharField()
    quantity_ordered = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal('0.01'))
    unit_cost = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    tax_code = serializers.IntegerField(default=1)


class PurchaseOrderCreateSerializer(serializers.Serializer):
    """Serializer for creating purchase orders"""
    supplier = serializers.IntegerField()
    order_date = serializers.DateField(required=False)
    delivery_date = serializers.DateField()
    pricing_method = serializers.ChoiceField(
        choices=PurchaseOrder.PRICING_METHOD_CHOICES,
        default='COST'
    )
    notes = serializers.CharField(required=False, allow_blank=True)
    
    # Options for line item extraction
    extract_all_items = serializers.BooleanField(default=False, required=False)
    extract_below_reorder = serializers.BooleanField(default=False, required=False)
    department = serializers.IntegerField(required=False, allow_null=True)
    
    # Manual line items
    line_items = serializers.ListField(
        child=PurchaseOrderCreateLineSerializer(),
        required=False,
        allow_empty=True
    )
    
    def validate(self, data):
        """Validate that we have either extraction options or manual line items"""
        has_extraction = data.get('extract_all_items') or data.get('extract_below_reorder')
        has_manual = bool(data.get('line_items'))
        
        if not has_extraction and not has_manual:
            raise serializers.ValidationError(
                "Must provide either extraction options or manual line items"
            )
        
        return data


class PurchaseOrderReceiptLineSerializer(serializers.ModelSerializer):
    """Serializer for receipt line items"""
    stock_code = serializers.CharField(
        source='purchase_order_line.stock_item.stock_code',
        read_only=True
    )
    stock_description = serializers.CharField(
        source='purchase_order_line.stock_item.description',
        read_only=True
    )
    ordered_cost = serializers.DecimalField(
        source='purchase_order_line.base_price',
        read_only=True,
        max_digits=10,
        decimal_places=2
    )
    
    class Meta:
        model = PurchaseOrderReceiptLine
        fields = '__all__'
        read_only_fields = [
            'line_exclusive', 'line_vat', 'line_inclusive',
            'has_cost_variance', 'cost_variance_amount', 'created_at'
        ]


class PurchaseOrderReceiptSerializer(serializers.ModelSerializer):
    """Serializer for purchase order receipts"""
    supplier_name = serializers.CharField(source='purchase_order.supplier.name', read_only=True)
    line_items = PurchaseOrderReceiptLineSerializer(many=True, read_only=True)
    
    class Meta:
        model = PurchaseOrderReceipt
        fields = '__all__'
        read_only_fields = [
            'total_quantity', 'total_value_exclusive', 'total_value_vat',
            'total_value_inclusive', 'has_variance', 'created_at'
        ]


class StockReceiptLineSerializer(serializers.Serializer):
    """Serializer for receiving stock against PO lines"""
    purchase_order_line_id = serializers.IntegerField()
    quantity_received = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal('0.01'))
    actual_unit_cost = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)


class StockReceiptSerializer(serializers.Serializer):
    """Serializer for receiving stock against purchase order"""
    purchase_order = serializers.IntegerField()
    receipt_date = serializers.DateField(required=False)
    invoice_number = serializers.CharField(max_length=50)
    
    # Line items to receive
    line_items = serializers.ListField(child=StockReceiptLineSerializer())
    
    # Options
    update_supplier_account = serializers.BooleanField(default=True)
    create_back_order = serializers.BooleanField(default=False, help_text="Create back order for short deliveries")
    
    def validate_line_items(self, value):
        """Validate that quantities don't exceed ordered quantities"""
        if not value:
            raise serializers.ValidationError("At least one line item required")
        return value


class BackOrderSerializer(serializers.ModelSerializer):
    """Serializer for back orders"""
    original_order_number = serializers.IntegerField(source='original_order.order_number', read_only=True)
    back_order_number = serializers.IntegerField(source='back_order.order_number', read_only=True)
    supplier_name = serializers.CharField(source='back_order.supplier.name', read_only=True)
    
    class Meta:
        model = BackOrder
        fields = '__all__'
        read_only_fields = ['created_at']


class PurchaseOrderTemplateLineSerializer(serializers.ModelSerializer):
    """Serializer for template line items"""
    stock_code = serializers.CharField(source='stock_item.stock_code', read_only=True)
    stock_description = serializers.CharField(source='stock_item.description', read_only=True)
    current_cost = serializers.DecimalField(
        source='stock_item.cost_price',
        read_only=True,
        max_digits=10,
        decimal_places=2
    )
    
    class Meta:
        model = PurchaseOrderTemplateLine
        fields = '__all__'
        read_only_fields = ['created_at']


class PurchaseOrderTemplateSerializer(serializers.ModelSerializer):
    """Serializer for purchase order templates"""
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    line_items = PurchaseOrderTemplateLineSerializer(many=True, read_only=True)
    
    class Meta:
        model = PurchaseOrderTemplate
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class PurchaseOrderTemplateCreateSerializer(serializers.Serializer):
    """Serializer for creating templates"""
    template_name = serializers.CharField(max_length=100)
    supplier = serializers.IntegerField()
    description = serializers.CharField(required=False, allow_blank=True)
    default_delivery_days = serializers.IntegerField(default=7)
    pricing_method = serializers.ChoiceField(
        choices=PurchaseOrder.PRICING_METHOD_CHOICES,
        default='COST'
    )
    
    line_items = serializers.ListField(
        child=serializers.DictField(),
        help_text="List of stock items with default quantities"
    )


class OutstandingPOReportSerializer(serializers.Serializer):
    """Serializer for outstanding PO reports"""
    order_number = serializers.IntegerField()
    supplier_name = serializers.CharField()
    order_date = serializers.DateField()
    delivery_date = serializers.DateField()
    days_overdue = serializers.IntegerField()
    total_value = serializers.DecimalField(max_digits=12, decimal_places=2)
    outstanding_value = serializers.DecimalField(max_digits=12, decimal_places=2)
    line_count = serializers.IntegerField()


class StockOnOrderSerializer(serializers.Serializer):
    """Serializer for stock on order report"""
    stock_code = serializers.CharField()
    description = serializers.CharField()
    quantity_on_hand = serializers.DecimalField(max_digits=10, decimal_places=2)
    quantity_on_order = serializers.DecimalField(max_digits=10, decimal_places=2)
    reorder_quantity = serializers.DecimalField(max_digits=10, decimal_places=2)
    orders = serializers.ListField(
        child=serializers.DictField(),
        help_text="List of orders for this item"
    )


class PreOrderReportSerializer(serializers.Serializer):
    """Serializer for pre-order planning report"""
    stock_code = serializers.CharField()
    description = serializers.CharField()
    supplier_name = serializers.CharField()
    quantity_on_hand = serializers.DecimalField(max_digits=10, decimal_places=2)
    reorder_quantity = serializers.DecimalField(max_digits=10, decimal_places=2)
    monthly_sales_avg = serializers.DecimalField(max_digits=10, decimal_places=2)
    suggested_order_qty = serializers.DecimalField(max_digits=10, decimal_places=2)
    last_cost = serializers.DecimalField(max_digits=10, decimal_places=2)
    estimated_value = serializers.DecimalField(max_digits=12, decimal_places=2)


class DeliveryVarianceReportSerializer(serializers.Serializer):
    """Serializer for delivery variance report"""
    order_number = serializers.IntegerField()
    supplier_name = serializers.CharField()
    stock_code = serializers.CharField()
    description = serializers.CharField()
    quantity_ordered = serializers.DecimalField(max_digits=10, decimal_places=2)
    quantity_received = serializers.DecimalField(max_digits=10, decimal_places=2)
    quantity_short = serializers.DecimalField(max_digits=10, decimal_places=2)
    ordered_cost = serializers.DecimalField(max_digits=10, decimal_places=2)
    actual_cost = serializers.DecimalField(max_digits=10, decimal_places=2)
    cost_variance = serializers.DecimalField(max_digits=10, decimal_places=2)
    value_variance = serializers.DecimalField(max_digits=12, decimal_places=2)