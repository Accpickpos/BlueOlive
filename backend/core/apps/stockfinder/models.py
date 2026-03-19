from django.db import models
from django.conf import settings
from django.core.validators import URLValidator, MinValueValidator
from apps.settings.models import TimeStampedModel
from decimal import Decimal
import uuid


class StockFinderConfig(TimeStampedModel):
    """
    Configuration for Stockfinder API integration.
    Stores API credentials and settings for connecting to Stockfinder.
    """
    
    # Connection Settings
    name = models.CharField(
        max_length=100,
        default="Stockfinder API",
        help_text="Friendly name for this configuration"
    )
    base_url = models.URLField(
        help_text="Stockfinder API base URL (e.g., https://api.stockfinder.co.za)"
    )
    api_key = models.CharField(
        max_length=255,
        blank=True,
        help_text="API key for authentication"
    )
    api_secret = models.CharField(
        max_length=255,
        blank=True,
        help_text="API secret for authentication"
    )
    
    # Branch/Fitment Center Mapping
    fitment_center_code = models.CharField(
        max_length=50,
        blank=True,
        help_text="Code used to identify this branch in Stockfinder"
    )
    
    # Sync Settings
    auto_sync_stock = models.BooleanField(
        default=False,
        help_text="Enable automatic stock synchronization"
    )
    sync_interval_minutes = models.PositiveIntegerField(
        default=60,
        validators=[MinValueValidator(5)],
        help_text="Interval in minutes between automatic syncs"
    )
    last_sync = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp of last successful sync"
    )
    
    # Status
    is_active = models.BooleanField(
        default=True,
        help_text="Enable this configuration"
    )
    
    # Custom Pricing Fields
    enable_custom_pricing = models.BooleanField(
        default=False,
        help_text="Enable custom pricing fields from Stockfinder"
    )
    custom_price_field_1 = models.CharField(
        max_length=50,
        blank=True,
        help_text="Custom price field 1 name"
    )
    custom_price_field_2 = models.CharField(
        max_length=50,
        blank=True,
        help_text="Custom price field 2 name"
    )
    custom_price_field_3 = models.CharField(
        max_length=50,
        blank=True,
        help_text="Custom price field 3 name"
    )
    
    # Webhook Settings
    webhook_enabled = models.BooleanField(
        default=False,
        help_text="Enable webhook接收 for orders"
    )
    webhook_secret = models.CharField(
        max_length=255,
        blank=True,
        help_text="Secret for validating webhook requests"
    )
    
    class Meta:
        verbose_name = "Stockfinder Configuration"
        verbose_name_plural = "Stockfinder Configurations"
    
    def __str__(self):
        return f"{self.name} ({self.base_url})"


class StockFinderSyncLog(TimeStampedModel):
    """
    Log of synchronization operations with Stockfinder.
    """
    
    SYNC_TYPES = [
        ('stock', 'Stock Load'),
        ('sales_order', 'Sales Order'),
        ('purchase_order', 'Purchase Order'),
        ('document', 'Document Retrieval'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    sync_type = models.CharField(
        max_length=20,
        choices=SYNC_TYPES,
        help_text="Type of synchronization"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    config = models.ForeignKey(
        StockFinderConfig,
        on_delete=models.CASCADE,
        related_name='sync_logs'
    )
    items_processed = models.PositiveIntegerField(
        default=0
    )
    items_failed = models.PositiveIntegerField(
        default=0
    )
    error_message = models.TextField(
        blank=True,
        help_text="Error message if sync failed"
    )
    started_at = models.DateTimeField(
        null=True,
        blank=True
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True
    )
    request_data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Request payload"
    )
    response_data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Response payload"
    )
    
    class Meta:
        verbose_name = "Stockfinder Sync Log"
        verbose_name_plural = "Stockfinder Sync Logs"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.sync_type} - {self.status} - {self.created_at}"


class StockFinderWebhookEvent(TimeStampedModel):
    """
    Webhook events received from Stockfinder.
    """
    
    EVENT_TYPES = [
        ('order_created', 'Order Created'),
        ('order_updated', 'Order Updated'),
        ('order_cancelled', 'Order Cancelled'),
        ('stock_updated', 'Stock Updated'),
    ]
    
    event_type = models.CharField(
        max_length=30,
        choices=EVENT_TYPES
    )
    event_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True
    )
    payload = models.JSONField(
        default=dict
    )
    processed = models.BooleanField(
        default=False
    )
    processing_error = models.TextField(
        blank=True
    )
    processed_at = models.DateTimeField(
        null=True,
        blank=True
    )
    
    class Meta:
        verbose_name = "Stockfinder Webhook Event"
        verbose_name_plural = "Stockfinder Webhook Events"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.event_type} - {self.event_id}"


class StockFinderStockItem(TimeStampedModel):
    """
    Cached stock items retrieved from Stockfinder.
    These are synced from the Stockfinder system for quick lookup.
    """
    
    # Stockfinder identifiers
    stockfinder_id = models.CharField(
        max_length=50,
        unique=True,
        help_text="Stockfinder's unique item ID"
    )
    stock_code = models.CharField(
        max_length=13,
        db_index=True,
        help_text="Item stock code/SKU"
    )
    description = models.CharField(
        max_length=255,
        help_text="Item description"
    )
    category = models.CharField(
        max_length=100,
        blank=True,
        help_text="Item category"
    )
    
    # Stock Information
    quantity_on_hand = models.DecimalField(
        max_digits=14,
        decimal_places=4,
        default=0,
        validators=[MinValueValidator(0)]
    )
    quantity_available = models.DecimalField(
        max_digits=14,
        decimal_places=4,
        default=0,
        help_text="Available quantity (on hand - allocated)"
    )
    quantity_allocated = models.DecimalField(
        max_digits=14,
        decimal_places=4,
        default=0
    )
    quantity_on_order = models.DecimalField(
        max_digits=14,
        decimal_places=4,
        default=0
    )
    
    # Pricing
    cost_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )
    retail_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )
    
    # Custom Pricing Fields (JSON for flexibility)
    custom_pricing = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional custom pricing fields"
    )
    
    # Additional Info
    barcode = models.CharField(
        max_length=50,
        blank=True
    )
    manufacturer_code = models.CharField(
        max_length=50,
        blank=True,
        help_text="Manufacturer's part number"
    )
    supplier_code = models.CharField(
        max_length=50,
        blank=True,
        help_text="Supplier's stock code"
    )
    
    # Linking to local stock
    local_stock_item = models.ForeignKey(
        'stock_control.StockItem',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='stockfinder_sync'
    )
    
    # Metadata
    last_synced = models.DateTimeField(
        auto_now=True
    )
    is_active = models.BooleanField(
        default=True
    )
    
    class Meta:
        verbose_name = "Stockfinder Stock Item"
        verbose_name_plural = "Stockfinder Stock Items"
        ordering = ['stock_code']
        indexes = [
            models.Index(fields=['stock_code']),
            models.Index(fields=['description']),
        ]
    
    def __str__(self):
        return f"{self.stock_code} - {self.description}"


class StockFinderSalesOrder(TimeStampedModel):
    """
    Sales orders received from Stockfinder.
    """
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Stockfinder identifiers
    stockfinder_order_id = models.CharField(
        max_length=50,
        unique=True,
        help_text="Stockfinder's order ID"
    )
    order_number = models.CharField(
        max_length=50,
        blank=True,
        help_text="Local order number"
    )
    
    # Customer Info
    customer_name = models.CharField(
        max_length=200
    )
    customer_email = models.EmailField(
        blank=True
    )
    customer_phone = models.CharField(
        max_length=20,
        blank=True
    )
    vehicle_registration = models.CharField(
        max_length=20,
        blank=True,
        help_text="Vehicle registration number"
    )
    vehicle_make = models.CharField(
        max_length=50,
        blank=True
    )
    vehicle_model = models.CharField(
        max_length=50,
        blank=True
    )
    
    # Order Details
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    order_date = models.DateTimeField()
    required_date = models.DateTimeField(
        null=True,
        blank=True
    )
    notes = models.TextField(
        blank=True
    )
    
    # Fitment Center
    fitment_center = models.CharField(
        max_length=100,
        blank=True,
        help_text="Fitment center name/code"
    )
    
    # Financials
    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )
    tax_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )
    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )
    
    # Link to local systems
    local_job_card = models.ForeignKey(
        'pos.JobCard',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='stockfinder_orders'
    )
    local_invoice = models.ForeignKey(
        'pos.Invoice',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='stockfinder_orders'
    )
    
    class Meta:
        verbose_name = "Stockfinder Sales Order"
        verbose_name_plural = "Stockfinder Sales Orders"
        ordering = ['-order_date']
    
    def __str__(self):
        return f"Order {self.stockfinder_order_id} - {self.customer_name}"


class StockFinderSalesOrderLine(TimeStampedModel):
    """
    Line items for Stockfinder sales orders.
    """
    
    order = models.ForeignKey(
        StockFinderSalesOrder,
        on_delete=models.CASCADE,
        related_name='lines'
    )
    line_number = models.PositiveIntegerField(
        default=1
    )
    stock_code = models.CharField(
        max_length=13,
        help_text="Item stock code"
    )
    description = models.CharField(
        max_length=255
    )
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=1
    )
    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )
    tax_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )
    line_total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )
    
    # Link to local
    local_stock_item = models.ForeignKey(
        'stock_control.StockItem',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    class Meta:
        verbose_name = "Stockfinder Order Line"
        verbose_name_plural = "Stockfinder Order Lines"
        ordering = ['line_number']
    
    def __str__(self):
        return f"Line {self.line_number} - {self.stock_code}"


class StockFinderPurchaseOrder(TimeStampedModel):
    """
    Purchase orders sent to Stockfinder or created from Stockfinder purchases.
    """
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent to Supplier'),
        ('confirmed', 'Confirmed'),
        ('received', 'Received'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Stockfinder identifiers
    stockfinder_po_id = models.CharField(
        max_length=50,
        unique=True,
        help_text="Stockfinder's PO ID"
    )
    local_po_number = models.CharField(
        max_length=50,
        blank=True,
        help_text="Local purchase order number"
    )
    
    # Supplier Info
    supplier_name = models.CharField(
        max_length=200
    )
    supplier_code = models.CharField(
        max_length=50,
        blank=True
    )
    
    # Order Details
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    order_date = models.DateTimeField()
    expected_date = models.DateField(
        null=True,
        blank=True
    )
    notes = models.TextField(
        blank=True
    )
    
    # Financials
    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )
    tax_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )
    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )
    
    # Link to local
    local_purchase_order = models.ForeignKey(
        'purchase_orders.PurchaseOrder',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='stockfinder_orders'
    )
    
    class Meta:
        verbose_name = "Stockfinder Purchase Order"
        verbose_name_plural = "Stockfinder Purchase Orders"
        ordering = ['-order_date']
    
    def __str__(self):
        return f"PO {self.stockfinder_po_id} - {self.supplier_name}"


class StockFinderPurchaseOrderLine(TimeStampedModel):
    """
    Line items for Stockfinder purchase orders.
    """
    
    order = models.ForeignKey(
        StockFinderPurchaseOrder,
        on_delete=models.CASCADE,
        related_name='lines'
    )
    line_number = models.PositiveIntegerField(
        default=1
    )
    stock_code = models.CharField(
        max_length=13
    )
    description = models.CharField(
        max_length=255
    )
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=1
    )
    unit_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )
    line_total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )
    quantity_received = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )
    
    class Meta:
        verbose_name = "Stockfinder PO Line"
        verbose_name_plural = "Stockfinder PO Lines"
        ordering = ['line_number']
    
    def __str__(self):
        return f"PO Line {self.line_number} - {self.stock_code}"

