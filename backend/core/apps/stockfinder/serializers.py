from rest_framework import serializers
from .models import (
    StockFinderConfig,
    StockFinderSyncLog,
    StockFinderWebhookEvent,
    StockFinderStockItem,
    StockFinderSalesOrder,
    StockFinderSalesOrderLine,
    StockFinderPurchaseOrder,
    StockFinderPurchaseOrderLine,
)


class StockFinderConfigSerializer(serializers.ModelSerializer):
    """Serializer for Stockfinder configuration."""
    
    class Meta:
        model = StockFinderConfig
        fields = [
            'id', 'name', 'base_url', 'fitment_center_code',
            'auto_sync_stock', 'sync_interval_minutes', 'last_sync',
            'is_active', 'enable_custom_pricing',
            'custom_price_field_1', 'custom_price_field_2', 'custom_price_field_3',
            'webhook_enabled', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'last_sync']
    
    def validate(self, data):
        """Validate configuration settings."""
        if data.get('webhook_enabled') and not data.get('webhook_secret'):
            raise serializers.ValidationError({
                'webhook_secret': 'Webhook secret is required when webhooks are enabled.'
            })
        return data


class StockFinderSyncLogSerializer(serializers.ModelSerializer):
    """Serializer for sync logs."""
    
    config_name = serializers.CharField(source='config.name', read_only=True)
    
    class Meta:
        model = StockFinderSyncLog
        fields = [
            'id', 'sync_type', 'status', 'config', 'config_name',
            'items_processed', 'items_failed', 'error_message',
            'started_at', 'completed_at', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class StockFinderWebhookEventSerializer(serializers.ModelSerializer):
    """Serializer for webhook events."""
    
    class Meta:
        model = StockFinderWebhookEvent
        fields = [
            'id', 'event_type', 'event_id', 'payload',
            'processed', 'processing_error', 'processed_at', 'created_at'
        ]
        read_only_fields = ['id', 'event_id', 'processed', 'processed_at', 'created_at']


class StockFinderStockItemSerializer(serializers.ModelSerializer):
    """Serializer for stock items from Stockfinder."""
    
    local_stock_code = serializers.CharField(source='stock_code', read_only=True)
    
    class Meta:
        model = StockFinderStockItem
        fields = [
            'id', 'stockfinder_id', 'stock_code', 'description', 'category',
            'quantity_on_hand', 'quantity_available', 'quantity_allocated',
            'quantity_on_order', 'cost_price', 'retail_price', 'custom_pricing',
            'barcode', 'manufacturer_code', 'supplier_code',
            'local_stock_item', 'last_synced', 'is_active'
        ]
        read_only_fields = ['id', 'last_synced']


class StockFinderStockItemBulkSerializer(serializers.Serializer):
    """
    Serializer for bulk stock lookup requests.
    Used to query multiple SKUs at once.
    """
    stock_codes = serializers.ListField(
        child=serializers.CharField(max_length=50),
        min_length=1,
        max_length=500,
        help_text="List of stock codes to look up"
    )
    include_custom_pricing = serializers.BooleanField(
        default=False,
        help_text="Include custom pricing fields"
    )


class StockFinderSalesOrderLineSerializer(serializers.ModelSerializer):
    """Serializer for sales order lines."""
    
    class Meta:
        model = StockFinderSalesOrderLine
        fields = [
            'id', 'line_number', 'stock_code', 'description',
            'quantity', 'unit_price', 'tax_amount', 'line_total',
            'local_stock_item'
        ]


class StockFinderSalesOrderSerializer(serializers.ModelSerializer):
    """Serializer for sales orders from Stockfinder."""
    
    lines = StockFinderSalesOrderLineSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = StockFinderSalesOrder
        fields = [
            'id', 'stockfinder_order_id', 'order_number',
            'customer_name', 'customer_email', 'customer_phone',
            'vehicle_registration', 'vehicle_make', 'vehicle_model',
            'status', 'status_display', 'order_date', 'required_date',
            'notes', 'fitment_center', 'subtotal', 'tax_amount', 'total_amount',
            'local_job_card', 'local_invoice', 'lines', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class StockFinderSalesOrderCreateSerializer(serializers.Serializer):
    """
    Serializer for creating sales orders from webhook data.
    """
    stockfinder_order_id = serializers.CharField(max_length=50)
    customer_name = serializers.CharField(max_length=200)
    customer_email = serializers.EmailField(required=False, allow_blank=True)
    customer_phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    vehicle_registration = serializers.CharField(max_length=20, required=False, allow_blank=True)
    vehicle_make = serializers.CharField(max_length=50, required=False, allow_blank=True)
    vehicle_model = serializers.CharField(max_length=50, required=False, allow_blank=True)
    order_date = serializers.DateTimeField()
    required_date = serializers.DateField(required=False, allow_null=True)
    notes = serializers.CharField(required=False, allow_blank=True)
    fitment_center = serializers.CharField(max_length=100, required=False, allow_blank=True)
    lines = serializers.ListField(
        child=serializers.DictField(),
        min_length=1
    )


class StockFinderPurchaseOrderLineSerializer(serializers.ModelSerializer):
    """Serializer for purchase order lines."""
    
    class Meta:
        model = StockFinderPurchaseOrderLine
        fields = [
            'id', 'line_number', 'stock_code', 'description',
            'quantity', 'unit_cost', 'line_total', 'quantity_received'
        ]


class StockFinderPurchaseOrderSerializer(serializers.ModelSerializer):
    """Serializer for purchase orders from Stockfinder."""
    
    lines = StockFinderPurchaseOrderLineSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = StockFinderPurchaseOrder
        fields = [
            'id', 'stockfinder_po_id', 'local_po_number',
            'supplier_name', 'supplier_code', 'status', 'status_display',
            'order_date', 'expected_date', 'notes',
            'subtotal', 'tax_amount', 'total_amount',
            'local_purchase_order', 'lines', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class StockFinderPurchaseOrderCreateSerializer(serializers.Serializer):
    """
    Serializer for creating purchase orders from Stockfinder purchases.
    """
    stockfinder_po_id = serializers.CharField(max_length=50)
    supplier_name = serializers.CharField(max_length=200)
    supplier_code = serializers.CharField(max_length=50, required=False, allow_blank=True)
    order_date = serializers.DateTimeField()
    expected_date = serializers.DateField(required=False, allow_null=True)
    notes = serializers.CharField(required=False, allow_blank=True)
    lines = serializers.ListField(
        child=serializers.DictField(),
        min_length=1
    )


# Document Retrieval Serializers
class DocumentSearchSerializer(serializers.Serializer):
    """
    Serializer for document search queries.
    Supports filtering by date range and document number.
    """
    DOCUMENT_TYPES = [
        ('sales_order', 'Sales Order'),
        ('invoice', 'Invoice'),
        ('purchase_order', 'Purchase Order'),
        ('credit_note', 'Credit Note'),
    ]
    
    document_type = serializers.ChoiceField(
        choices=DOCUMENT_TYPES,
        help_text="Type of document to search"
    )
    start_date = serializers.DateField(
        required=False,
        help_text="Start of date range"
    )
    end_date = serializers.DateField(
        required=False,
        help_text="End of date range"
    )
    document_number = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Specific document number to search"
    )
    customer_name = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Filter by customer name (for sales orders/invoices)"
    )
    supplier_name = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Filter by supplier name (for purchase orders)"
    )
    page = serializers.IntegerField(default=1, min_value=1)
    page_size = serializers.IntegerField(default=20, min_value=1, max_value=100)


class DocumentResultSerializer(serializers.Serializer):
    """Serializer for document search results."""
    
    id = serializers.IntegerField()
    document_type = serializers.CharField()
    document_number = serializers.CharField()
    date = serializers.DateField()
    customer_name = serializers.CharField(required=False, allow_null=True)
    supplier_name = serializers.CharField(required=False, allow_null=True)
    status = serializers.CharField()
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2)
    tax_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
