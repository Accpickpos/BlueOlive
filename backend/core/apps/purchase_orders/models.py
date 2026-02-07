from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta


class PurchaseOrder(models.Model):
    """Purchase Order header"""
    
    STATUS_CHOICES = [
        ('OUTSTANDING', 'Outstanding'),
        ('PARTIALLY_RECEIVED', 'Partially Received'),
        ('FULLY_RECEIVED', 'Fully Received'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    PRICING_METHOD_CHOICES = [
        ('COST', 'At Cost Price'),
        ('RETAIL', 'At Retail Price'),
    ]
    
    order_number = models.AutoField(primary_key=True)
    supplier = models.ForeignKey(
        'creditors.Creditor',
        on_delete=models.PROTECT,
        related_name='purchase_orders'
    )
    
    # Dates
    order_date = models.DateField(default=timezone.now)
    delivery_date = models.DateField(help_text="Expected delivery date")
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OUTSTANDING')
    
    # Pricing
    pricing_method = models.CharField(
        max_length=10,
        choices=PRICING_METHOD_CHOICES,
        default='COST',
        help_text="Price items at cost or retail"
    )
    
    # Totals
    total_quantity_ordered = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_quantity_received = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_quantity_outstanding = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    total_value_exclusive = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_value_vat = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_value_inclusive = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Outstanding values
    outstanding_value_exclusive = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    outstanding_value_vat = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    outstanding_value_inclusive = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Flags
    is_back_order = models.BooleanField(default=False, help_text="Created from delivery variance")
    parent_order = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='back_orders',
        help_text="Original order if this is a back order"
    )
    
    # Notes
    notes = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'purchase_orders'
        ordering = ['-order_date', '-order_number']
        indexes = [
            models.Index(fields=['supplier', 'status']),
            models.Index(fields=['delivery_date']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"PO {self.order_number} - {self.supplier.name} - {self.order_date}"

    def calculate_totals(self):
        """Calculate order totals from line items"""
        lines = self.line_items.all()
        
        self.total_quantity_ordered = sum(line.quantity_ordered for line in lines)
        self.total_quantity_received = sum(line.quantity_received for line in lines)
        self.total_quantity_outstanding = sum(line.quantity_outstanding for line in lines)
        
        self.total_value_exclusive = sum(line.total_exclusive for line in lines)
        self.total_value_vat = sum(line.total_vat for line in lines)
        self.total_value_inclusive = sum(line.total_inclusive for line in lines)
        
        self.outstanding_value_exclusive = sum(line.outstanding_exclusive for line in lines)
        self.outstanding_value_vat = sum(line.outstanding_vat for line in lines)
        self.outstanding_value_inclusive = sum(line.outstanding_inclusive for line in lines)
        
        # Update status
        if self.total_quantity_received == 0:
            self.status = 'OUTSTANDING'
        elif self.total_quantity_received >= self.total_quantity_ordered:
            self.status = 'FULLY_RECEIVED'
        else:
            self.status = 'PARTIALLY_RECEIVED'
        
        self.save()

    def cancel(self):
        """Cancel the purchase order"""
        if self.status == 'FULLY_RECEIVED':
            raise ValueError("Cannot cancel a fully received order")
        
        self.status = 'CANCELLED'
        self.cancelled_at = timezone.now()
        self.save()
        
        # Update stock on order quantities
        for line in self.line_items.all():
            stock_item = line.stock_item
            stock_item.quantity_on_order -= line.quantity_outstanding
            stock_item.save()


class PurchaseOrderLine(models.Model):
    """Purchase Order line items"""
    
    purchase_order = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.CASCADE,
        related_name='line_items'
    )
    line_number = models.IntegerField()
    
    stock_item = models.ForeignKey(
        'stock_control.StockItem',
        on_delete=models.PROTECT,
        related_name='purchase_order_lines'
    )
    
    # Quantities
    quantity_ordered = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)])
    quantity_received = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    quantity_outstanding = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Pricing
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    tax_code = models.IntegerField(default=1)  # 1=14%, 2=0%
    
    # Line totals (ordered)
    total_exclusive = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_vat = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_inclusive = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Outstanding totals
    outstanding_exclusive = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    outstanding_vat = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    outstanding_inclusive = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Stock info at time of order
    quantity_on_hand_at_order = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    monthly_sales_at_order = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Flags
    is_fully_received = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'purchase_order_lines'
        ordering = ['line_number']
        unique_together = ['purchase_order', 'line_number']
        indexes = [
            models.Index(fields=['stock_item']),
            models.Index(fields=['is_fully_received']),
        ]

    def __str__(self):
        return f"PO {self.purchase_order.order_number} - Line {self.line_number}: {self.stock_item.stock_code}"

    def calculate_totals(self):
        """Calculate line totals"""
        # Ordered totals
        self.total_exclusive = self.quantity_ordered * self.unit_cost
        if self.tax_code == 1:
            self.total_vat = self.total_exclusive * Decimal('0.14')
        else:
            self.total_vat = Decimal('0')
        self.total_inclusive = self.total_exclusive + self.total_vat
        
        # Outstanding totals
        self.quantity_outstanding = self.quantity_ordered - self.quantity_received
        self.outstanding_exclusive = self.quantity_outstanding * self.unit_cost
        if self.tax_code == 1:
            self.outstanding_vat = self.outstanding_exclusive * Decimal('0.14')
        else:
            self.outstanding_vat = Decimal('0')
        self.outstanding_inclusive = self.outstanding_exclusive + self.outstanding_vat
        
        # Check if fully received
        self.is_fully_received = self.quantity_received >= self.quantity_ordered
        
        self.save()

    def receive_stock(self, quantity, actual_cost=None):
        """
        Receive stock for this line item
        
        Args:
            quantity: Quantity being received
            actual_cost: Actual cost if different from ordered cost
        
        Returns:
            dict: Variance information if any
        """
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        
        if self.quantity_received + quantity > self.quantity_ordered:
            raise ValueError("Cannot receive more than ordered quantity")
        
        # Update received quantity
        self.quantity_received += quantity
        self.calculate_totals()
        
        # Check for variance
        variance = {}
        if actual_cost and actual_cost != self.unit_cost:
            variance['cost_variance'] = {
                'ordered_cost': float(self.unit_cost),
                'actual_cost': float(actual_cost),
                'difference': float(actual_cost - self.unit_cost),
                'quantity': float(quantity)
            }
        
        if self.is_fully_received and self.quantity_received < self.quantity_ordered:
            variance['quantity_variance'] = {
                'ordered': float(self.quantity_ordered),
                'received': float(self.quantity_received),
                'short': float(self.quantity_ordered - self.quantity_received)
            }
        
        return variance


class PurchaseOrderReceipt(models.Model):
    """Record of stock receipts against purchase orders"""
    
    purchase_order = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.PROTECT,
        related_name='receipts'
    )
    receipt_date = models.DateField(default=timezone.now)
    invoice_number = models.CharField(max_length=50, help_text="Supplier's invoice number")
    
    # Link to creditor GRN if integrated
    creditor_grn = models.ForeignKey(
        'creditors.GoodsReceivedNote',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='purchase_order_receipts',
        help_text="Link to Goods Received Note for accounting"
    )
    
    # Totals received in this receipt
    total_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_value_exclusive = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_value_vat = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_value_inclusive = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Variance tracking
    has_variance = models.BooleanField(default=False)
    variance_notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'purchase_order_receipts'
        ordering = ['-receipt_date']
        indexes = [
            models.Index(fields=['purchase_order', 'receipt_date']),
        ]

    def __str__(self):
        return f"Receipt for PO {self.purchase_order.order_number} - {self.receipt_date}"
    
    def calculate_totals(self):
        """Calculate receipt totals from line items"""
        lines = self.line_items.all()
        
        self.total_quantity = sum(line.quantity_received for line in lines)
        self.total_value_exclusive = sum(line.line_exclusive for line in lines)
        self.total_value_vat = sum(line.line_vat for line in lines)
        self.total_value_inclusive = sum(line.line_inclusive for line in lines)
        
        self.save()


class PurchaseOrderReceiptLine(models.Model):
    """Line items for purchase order receipts"""
    
    receipt = models.ForeignKey(
        PurchaseOrderReceipt,
        on_delete=models.CASCADE,
        related_name='line_items'
    )
    purchase_order_line = models.ForeignKey(
        PurchaseOrderLine,
        on_delete=models.PROTECT,
        related_name='receipt_lines'
    )
    
    quantity_received = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)])
    actual_unit_cost = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    
    # Calculated values
    line_exclusive = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    line_vat = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    line_inclusive = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Variance flags
    has_cost_variance = models.BooleanField(default=False)
    cost_variance_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'purchase_order_receipt_lines'

    def __str__(self):
        return f"Receipt {self.receipt.id} - {self.purchase_order_line.stock_item.stock_code}"
    
    def calculate_totals(self):
        """Calculate line totals from quantity and cost"""
        self.line_exclusive = self.quantity_received * self.actual_unit_cost
        tax_code = self.purchase_order_line.tax_code
        
        if tax_code == 1:
            self.line_vat = self.line_exclusive * Decimal('0.14')
        else:
            self.line_vat = Decimal('0')
        
        self.line_inclusive = self.line_exclusive + self.line_vat
        
        # Check for cost variance
        if self.actual_unit_cost != self.purchase_order_line.unit_cost:
            self.has_cost_variance = True
            self.cost_variance_amount = (self.actual_unit_cost - self.purchase_order_line.unit_cost) * self.quantity_received
        
        self.save()


class BackOrder(models.Model):
    """
    Back orders created from delivery variances
    Separate model to track the back order creation process
    """
    
    original_order = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.PROTECT,
        related_name='created_back_orders'
    )
    back_order = models.OneToOneField(
        PurchaseOrder,
        on_delete=models.CASCADE,
        related_name='back_order_info'
    )
    
    created_date = models.DateField(default=timezone.now)
    reason = models.TextField(help_text="Reason for back order (short delivery, etc)")
    
    # Original receipt that triggered back order
    triggering_receipt = models.ForeignKey(
        PurchaseOrderReceipt,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'back_orders'

    def __str__(self):
        return f"Back Order PO {self.back_order.order_number} from PO {self.original_order.order_number}"


class PurchaseOrderTemplate(models.Model):
    """
    Template for recurring purchase orders or pre-configured orders
    """
    
    template_name = models.CharField(max_length=100, unique=True)
    supplier = models.ForeignKey(
        'creditors.Creditor',
        on_delete=models.PROTECT,
        related_name='po_templates'
    )
    description = models.TextField(blank=True)
    
    # Default settings
    default_delivery_days = models.IntegerField(default=7, help_text="Days from order to delivery")
    pricing_method = models.CharField(max_length=10, choices=PurchaseOrder.PRICING_METHOD_CHOICES, default='COST')
    
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'purchase_order_templates'
        ordering = ['template_name']

    def __str__(self):
        return f"{self.template_name} - {self.supplier.name}"

    def create_order(self, delivery_date=None):
        """Create a purchase order from this template"""
        from datetime import timedelta
        
        if not delivery_date:
            delivery_date = timezone.now().date() + timedelta(days=self.default_delivery_days)
        
        order = PurchaseOrder.objects.create(
            supplier=self.supplier,
            delivery_date=delivery_date,
            pricing_method=self.pricing_method,
            notes=f"Created from template: {self.template_name}"
        )
        
        # Copy template lines
        for template_line in self.line_items.all():
            PurchaseOrderLine.objects.create(
                purchase_order=order,
                line_number=template_line.line_number,
                stock_item=template_line.stock_item,
                quantity_ordered=template_line.default_quantity,
                unit_cost=template_line.stock_item.cost_price,
                tax_code=template_line.stock_item.tax_code,
                quantity_on_hand_at_order=template_line.stock_item.quantity_on_hand,
                monthly_sales_at_order=template_line.stock_item.sales_mtd_quantity
            )
        
        order.calculate_totals()
        return order


class PurchaseOrderTemplateLine(models.Model):
    """Line items for purchase order templates"""
    
    template = models.ForeignKey(
        PurchaseOrderTemplate,
        on_delete=models.CASCADE,
        related_name='line_items'
    )
    line_number = models.IntegerField()
    stock_item = models.ForeignKey(
        'stock_control.StockItem',
        on_delete=models.PROTECT,
        related_name='po_template_lines'
    )
    default_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        help_text="Default quantity to order"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'purchase_order_template_lines'
        ordering = ['line_number']
        unique_together = ['template', 'line_number']

    def __str__(self):
        return f"{self.template.template_name} - Line {self.line_number}"