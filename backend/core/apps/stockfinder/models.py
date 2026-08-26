from apps.settings.models import TimeStampedModel
from django.conf import settings
from django.db import models


class StockFinderSalesOrder(TimeStampedModel):
    """
    Sales orders received from Stockfinder.
    These are orders that Stockfinder sends to this app via API.
    """

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("accepted", "Accepted"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    # Stockfinder identifiers
    stockfinder_order_id = models.CharField(
        max_length=50, unique=True, help_text="Stockfinder's order ID"
    )
    order_number = models.CharField(
        max_length=50, blank=True, help_text="Local order number"
    )

    # Customer Info
    customer_name = models.CharField(max_length=200)
    customer_email = models.EmailField(blank=True)
    customer_phone = models.CharField(max_length=20, blank=True)
    vehicle_registration = models.CharField(
        max_length=20, blank=True, help_text="Vehicle registration number"
    )
    vehicle_make = models.CharField(max_length=50, blank=True)
    vehicle_model = models.CharField(max_length=50, blank=True)

    # Order Details
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    order_date = models.DateTimeField()
    required_date = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    # Fitment Center
    fitment_center = models.CharField(
        max_length=100, blank=True, help_text="Fitment center name/code"
    )

    # Financials
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Link to local systems
    local_job_card = models.ForeignKey(
        "pos.JobCard",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="stockfinder_orders",
    )
    local_invoice = models.ForeignKey(
        "pos.Invoice",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="stockfinder_orders",
    )

    class Meta:
        verbose_name = "Stockfinder Sales Order"
        verbose_name_plural = "Stockfinder Sales Orders"
        ordering = ["-order_date"]

    def __str__(self):
        return f"Order {self.stockfinder_order_id} - {self.customer_name}"


class StockFinderSalesOrderLine(TimeStampedModel):
    """
    Line items for Stockfinder sales orders.
    """

    order = models.ForeignKey(
        StockFinderSalesOrder, on_delete=models.CASCADE, related_name="lines"
    )
    line_number = models.PositiveIntegerField(default=1)
    stock_code = models.CharField(max_length=13, help_text="Item stock code")
    description = models.CharField(max_length=255)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    line_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Link to local
    local_stock_item = models.ForeignKey(
        "stock_control.StockItem", on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        verbose_name = "Stockfinder Order Line"
        verbose_name_plural = "Stockfinder Order Lines"
        ordering = ["line_number"]

    def __str__(self):
        return f"Line {self.line_number} - {self.stock_code}"


class StockFinderPurchaseOrder(TimeStampedModel):
    """
    Purchase orders received from Stockfinder.
    """

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("sent", "Sent to Supplier"),
        ("confirmed", "Confirmed"),
        ("received", "Received"),
        ("cancelled", "Cancelled"),
    ]

    # Stockfinder identifiers
    stockfinder_po_id = models.CharField(
        max_length=50, unique=True, help_text="Stockfinder's PO ID"
    )
    local_po_number = models.CharField(
        max_length=50, blank=True, help_text="Local purchase order number"
    )

    # Supplier Info
    supplier_name = models.CharField(max_length=200)
    supplier_code = models.CharField(max_length=50, blank=True)

    # Order Details
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    order_date = models.DateTimeField()
    expected_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)

    # Financials
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Link to local
    local_purchase_order = models.ForeignKey(
        "purchase_orders.PurchaseOrder",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="stockfinder_orders",
    )

    class Meta:
        verbose_name = "Stockfinder Purchase Order"
        verbose_name_plural = "Stockfinder Purchase Orders"
        ordering = ["-order_date"]

    def __str__(self):
        return f"PO {self.stockfinder_po_id} - {self.supplier_name}"


class StockFinderPurchaseOrderLine(TimeStampedModel):
    """
    Line items for Stockfinder purchase orders.
    """

    order = models.ForeignKey(
        StockFinderPurchaseOrder, on_delete=models.CASCADE, related_name="lines"
    )
    line_number = models.PositiveIntegerField(default=1)
    stock_code = models.CharField(max_length=13)
    description = models.CharField(max_length=255)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    line_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    quantity_received = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        verbose_name = "Stockfinder PO Line"
        verbose_name_plural = "Stockfinder PO Lines"
        ordering = ["line_number"]

    def __str__(self):
        return f"PO Line {self.line_number} - {self.stock_code}"
