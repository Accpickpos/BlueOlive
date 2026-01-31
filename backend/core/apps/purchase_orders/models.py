"""
PURCHASE ORDERS APP - Django Models
Complete purchase order management models

LOCATION: accpick_project/purchase_orders/models.py

Models in this file:
- PurchaseOrder
- PurchaseOrderLineItem
- BackOrder
- BackOrderLineItem
"""

from django.db import models
from django.core.validators import MinValueValidator
from django.contrib.auth import get_user_model
from decimal import Decimal
from apps.settings.models import TimeStampedModel, TaxCode

User = get_user_model()


# ============================================================================
# PURCHASE ORDER MODEL
# ============================================================================

class PurchaseOrder(TimeStampedModel):
    """
    Purchase order to supplier
    """
    
    # PO identification
    po_number = models.CharField(
        max_length=20,
        unique=True,
        help_text="Purchase order number"
    )
    po_date = models.DateField()
    
    # Supplier
    supplier = models.ForeignKey(
        'creditors.Creditor',
        on_delete=models.PROTECT,
        related_name='purchase_orders',
        null=True,
        blank=True
    )
    
    # Delivery details
    expected_delivery_date = models.DateField(
        null=True,
        blank=True,
        help_text="Expected delivery date"
    )
    delivery_address = models.TextField(
        blank=True,
        help_text="Delivery address (if different from default)"
    )
    
    # Order status
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('SENT', 'Sent to Supplier'),
        ('CONFIRMED', 'Confirmed by Supplier'),
        ('PARTIAL', 'Partially Received'),
        ('COMPLETE', 'Fully Received'),
        ('CANCELLED', 'Cancelled'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='DRAFT'
    )
    
    # Totals
    order_total = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        editable=False,
        help_text="Total order value (exclusive VAT)"
    )
    order_total_vat = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        editable=False,
        help_text="Total VAT"
    )
    order_total_inclusive = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        editable=False,
        help_text="Total including VAT"
    )
    
    # Receiving tracking
    total_quantity_ordered = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        editable=False
    )
    total_quantity_received = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        editable=False
    )
    
    # References
    supplier_reference = models.CharField(
        max_length=50,
        blank=True,
        help_text="Supplier's reference/quote number"
    )
    notes = models.TextField(blank=True)
    
    # Who created this PO
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='purchase_orders_created'
    )
    
    # Approval
    is_approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='purchase_orders_approved'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    
    # When sent to supplier
    sent_to_supplier_date = models.DateField(null=True, blank=True)
    
    class Meta:
        db_table = 'purchase_orders'
        ordering = ['-po_date', '-po_number']
        indexes = [
            models.Index(fields=['po_number']),
            models.Index(fields=['supplier']),
            models.Index(fields=['status']),
            models.Index(fields=['po_date']),
        ]
        verbose_name = 'Purchase Order'
        verbose_name_plural = 'Purchase Orders'
    
    def __str__(self):
        return f"PO-{self.po_number} - {self.supplier.name}"
    
    def save(self, *args, **kwargs):
        if not self.po_number:
            self.po_number = self._generate_po_number()
        super().save(*args, **kwargs)
    
    def _generate_po_number(self):
        """Generate next PO number"""
        last_po = PurchaseOrder.objects.order_by('-id').first()
        if last_po and last_po.po_number:
            try:
                num = int(last_po.po_number.split('-')[-1])
                return f"PO-{num + 1:06d}"
            except:
                pass
        return "PO-000001"
    
    def calculate_totals(self):
        """Calculate order totals from line items"""
        lines = self.line_items.all()
        
        self.total_quantity_ordered = sum(line.quantity_ordered for line in lines)
        self.total_quantity_received = sum(line.quantity_received for line in lines)
        
        self.order_total = sum(line.line_total_exclusive for line in lines)
        self.order_total_vat = sum(line.tax_amount for line in lines)
        self.order_total_inclusive = sum(line.line_total_inclusive for line in lines)
        
        # Update status based on quantities
        if self.total_quantity_received == 0:
            if self.status == 'PARTIAL':
                self.status = 'SENT'
        elif self.total_quantity_received >= self.total_quantity_ordered:
            self.status = 'COMPLETE'
        elif self.total_quantity_received > 0:
            self.status = 'PARTIAL'
        
        self.save()
    
    @property
    def is_fully_received(self):
        """Check if order is fully received"""
        return self.total_quantity_received >= self.total_quantity_ordered
    
    @property
    def outstanding_quantity(self):
        """Calculate outstanding quantity"""
        return self.total_quantity_ordered - self.total_quantity_received


class PurchaseOrderLineItem(TimeStampedModel):
    """
    Line items on purchase order
    """
    
    purchase_order = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.CASCADE,
        related_name='line_items'
    )
    line_number = models.PositiveSmallIntegerField(default=1)
    
    # Stock item
    stock_item = models.ForeignKey(
        'stock_control.StockItem',
        on_delete=models.PROTECT,
        related_name='po_lines'
    )
    
    # Order details
    quantity_ordered = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Quantity ordered"
    )
    unit_cost = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Cost per unit (quoted price)"
    )
    tax_code = models.ForeignKey(
        TaxCode,
        on_delete=models.PROTECT,
        help_text="VAT code"
    )
    
    # Receiving tracking
    quantity_received = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        help_text="Quantity received so far"
    )
    quantity_outstanding = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        editable=False,
        help_text="Still to be received"
    )
    
    # Calculated amounts
    line_total_exclusive = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        editable=False,
        help_text="Line total (exclusive VAT)"
    )
    tax_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        editable=False,
        help_text="VAT amount"
    )
    line_total_inclusive = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        editable=False,
        help_text="Line total (inclusive VAT)"
    )
    
    # Line status
    is_complete = models.BooleanField(
        default=False,
        editable=False,
        help_text="Fully received"
    )
    
    # Notes
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'purchase_order_line_items'
        ordering = ['line_number']
        unique_together = [['purchase_order', 'line_number']]
        verbose_name = 'Purchase Order Line Item'
        verbose_name_plural = 'Purchase Order Line Items'
    
    def save(self, *args, **kwargs):
        # Calculate amounts
        self.line_total_exclusive = self.quantity_ordered * self.unit_cost
        self.tax_amount = self.line_total_exclusive * (self.tax_code.rate / 100)
        self.line_total_inclusive = self.line_total_exclusive + self.tax_amount
        
        # Calculate outstanding
        self.quantity_outstanding = self.quantity_ordered - self.quantity_received
        self.is_complete = (self.quantity_received >= self.quantity_ordered)
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Line {self.line_number}: {self.stock_item.stock_code} x {self.quantity_ordered}"


# ============================================================================
# BACK ORDER MODEL
# ============================================================================

class BackOrder(TimeStampedModel):
    """
    Back order - items ordered by customers but not in stock
    """
    
    backorder_number = models.CharField(
        max_length=20,
        unique=True,
        help_text="Back order number"
    )
    backorder_date = models.DateField()
    
    # Customer
    debtor = models.ForeignKey(
        'debtors.Debtor',
        on_delete=models.PROTECT,
        related_name='back_orders'
    )
    
    # Original sales order reference
    original_order_number = models.CharField(
        max_length=50,
        blank=True,
        help_text="Original sales order/invoice number"
    )
    
    # Status
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('ORDERED', 'Ordered from Supplier'),
        ('PARTIAL', 'Partially Received'),
        ('READY', 'Ready to Deliver'),
        ('COMPLETE', 'Delivered to Customer'),
        ('CANCELLED', 'Cancelled'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING'
    )
    
    # Linked purchase order (if created)
    purchase_order = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='back_orders'
    )
    
    # Totals
    total_quantity = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        editable=False
    )
    total_value = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        editable=False
    )
    
    # Customer notification
    customer_notified = models.BooleanField(
        default=False,
        help_text="Customer notified of back order"
    )
    notification_date = models.DateField(null=True, blank=True)
    
    # Expected availability
    expected_availability_date = models.DateField(
        null=True,
        blank=True,
        help_text="When stock expected"
    )
    
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'back_orders'
        ordering = ['-backorder_date']
        indexes = [
            models.Index(fields=['backorder_number']),
            models.Index(fields=['debtor']),
            models.Index(fields=['status']),
        ]
        verbose_name = 'Back Order'
        verbose_name_plural = 'Back Orders'
    
    def __str__(self):
        return f"BO-{self.backorder_number} - {self.debtor.name}"
    
    def save(self, *args, **kwargs):
        if not self.backorder_number:
            self.backorder_number = self._generate_bo_number()
        super().save(*args, **kwargs)
    
    def _generate_bo_number(self):
        """Generate next back order number"""
        last_bo = BackOrder.objects.order_by('-id').first()
        if last_bo and last_bo.backorder_number:
            try:
                num = int(last_bo.backorder_number.split('-')[-1])
                return f"BO-{num + 1:06d}"
            except:
                pass
        return "BO-000001"
    
    def calculate_totals(self):
        """Calculate totals from line items"""
        lines = self.line_items.all()
        self.total_quantity = sum(line.quantity_backordered for line in lines)
        self.total_value = sum(line.line_value for line in lines)
        self.save()


class BackOrderLineItem(TimeStampedModel):
    """
    Line items on back order
    """
    
    back_order = models.ForeignKey(
        BackOrder,
        on_delete=models.CASCADE,
        related_name='line_items'
    )
    line_number = models.PositiveSmallIntegerField(default=1)
    
    # Stock item
    stock_item = models.ForeignKey(
        'stock_control.StockItem',
        on_delete=models.PROTECT,
        related_name='backorder_lines'
    )
    
    # Quantities
    quantity_backordered = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Quantity on back order"
    )
    quantity_fulfilled = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        help_text="Quantity fulfilled so far"
    )
    quantity_outstanding = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        editable=False,
        help_text="Still outstanding"
    )
    
    # Pricing (at time of back order)
    unit_selling_price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Selling price promised to customer"
    )
    line_value = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        editable=False
    )
    
    # Status
    is_complete = models.BooleanField(
        default=False,
        editable=False
    )
    
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'back_order_line_items'
        ordering = ['line_number']
        unique_together = [['back_order', 'line_number']]
        verbose_name = 'Back Order Line Item'
        verbose_name_plural = 'Back Order Line Items'
    
    def save(self, *args, **kwargs):
        # Calculate outstanding and value
        self.quantity_outstanding = self.quantity_backordered - self.quantity_fulfilled
        self.line_value = self.quantity_backordered * self.unit_selling_price
        self.is_complete = (self.quantity_fulfilled >= self.quantity_backordered)
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Line {self.line_number}: {self.stock_item.stock_code} x {self.quantity_backordered}"