"""
Point of Sale models.
Based on the PointOfSale.pdf documentation.
"""
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from apps.settings.models import TimeStampedModel, SalesArea
from apps.debtors.models import Debtor
from apps.stock_control.models import StockItem


class CashSale(TimeStampedModel):
    """Cash sale transaction."""
    sale_number = models.CharField(max_length=20, unique=True, db_index=True)
    sale_date = models.DateField(db_index=True)
    sale_time = models.TimeField(auto_now_add=True)
    
    # Header Information
    customer_name = models.CharField(max_length=200, blank=True)
    delivery_address = models.CharField(max_length=200, blank=True)
    telephone = models.CharField(max_length=50, blank=True)
    order_number = models.CharField(max_length=50, blank=True)
    job_card_number = models.CharField(max_length=50, blank=True)
    
    sales_area = models.ForeignKey(
        SalesArea,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    cashier = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='cash_sales'
    )
    station_number = models.PositiveIntegerField(default=1)
    
    # Totals
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    vat_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Cost and Profit
    total_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    gross_profit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Payment
    cash_tendered = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    change_given = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # VAT
    vat_number = models.CharField(max_length=50, blank=True)
    
    # Status
    is_posted = models.BooleanField(default=False)
    is_cancelled = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-sale_date', '-sale_time']
        indexes = [
            models.Index(fields=['sale_date', 'cashier']),
            models.Index(fields=['station_number', 'sale_date']),
        ]
    
    def __str__(self):
        return f"Cash Sale {self.sale_number}"


class CashSaleLine(TimeStampedModel):
    """Cash sale line item."""
    cash_sale = models.ForeignKey(
        CashSale,
        on_delete=models.CASCADE,
        related_name='lines'
    )
    line_number = models.PositiveIntegerField()
    
    stock_code = models.CharField(max_length=13, blank=True)
    description = models.CharField(max_length=200)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    
    unit_price = models.DecimalField(max_digits=12, decimal_places=4)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    tax_code = models.PositiveIntegerField(default=1)
    
    # Calculated fields
    line_total = models.DecimalField(max_digits=12, decimal_places=2)
    vat_amount = models.DecimalField(max_digits=12, decimal_places=2)
    cost_price = models.DecimalField(max_digits=12, decimal_places=4, default=0)
    line_profit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    class Meta:
        ordering = ['line_number']
        unique_together = ['cash_sale', 'line_number']
    
    def __str__(self):
        return f"{self.cash_sale.sale_number} - Line {self.line_number}"


class Tender(TimeStampedModel):
    """Payment tender for cash sales and receipts."""
    
    TENDER_TYPE_CHOICES = [
        ('CASH', 'Cash'),
        ('CHEQUE', 'Cheque'),
        ('VOUCHER', 'Voucher'),
        ('SPEEDPOINT', 'Speedpoint/Card'),
        ('EFT', 'EFT'),
    ]
    
    # Link to transaction
    cash_sale = models.ForeignKey(
        CashSale,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='tenders'
    )
    # Could also link to debtor receipt, etc.
    
    tender_type = models.CharField(max_length=15, choices=TENDER_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    
    # For cheques
    drawer_name = models.CharField(max_length=200, blank=True)
    bank_name = models.CharField(max_length=100, blank=True)
    bank_account = models.CharField(max_length=50, blank=True)
    id_number = models.CharField(max_length=50, blank=True)
    telephone = models.CharField(max_length=50, blank=True)
    
    # For speedpoint
    card_type = models.CharField(max_length=50, blank=True)
    authorization_code = models.CharField(max_length=50, blank=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.tender_type} - {self.amount}"


class Laybye(TimeStampedModel):
    """Laybye (layaway) transaction (LBMAST equivalent)."""
    
    STATUS_CHOICES = [
        ('A', 'Active'),
        ('C', 'Completed'),
        ('X', 'Cancelled'),
        ('E', 'Expired'),
    ]
    
    laybye_number = models.CharField(max_length=20, unique=True, db_index=True)
    
    # Customer details
    customer_name = models.CharField(max_length=40)
    address_line1 = models.CharField(max_length=25, blank=True)
    address_line2 = models.CharField(max_length=25, blank=True)
    address_line3 = models.CharField(max_length=25, blank=True)
    telephone = models.CharField(max_length=15, blank=True)
    
    sales_area = models.ForeignKey(
        SalesArea,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    # Dates
    laybye_date = models.DateField()
    expiry_date = models.DateField()
    date_last_paid = models.DateField(null=True, blank=True)
    
    # Totals
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    deposit_amount = models.DecimalField(max_digits=12, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    balance_due = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Comments
    comment1 = models.CharField(max_length=30, blank=True)
    comment2 = models.CharField(max_length=30, blank=True)
    
    # Status
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='A')
    
    # Cancellation
    retention_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Percentage retained on cancellation"
    )
    refund_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    class Meta:
        ordering = ['-laybye_date']
        indexes = [
            models.Index(fields=['status', 'expiry_date']),
        ]
    
    def __str__(self):
        return f"Laybye {self.laybye_number}"


class LaybyeLine(TimeStampedModel):
    """Laybye transaction (LBTRAN equivalent)."""
    
    TRANSACTION_TYPE_CHOICES = [
        ('SP', 'Sale'),
        ('PM', 'Payment'),
        ('AD', 'Adjustment'),
        ('RT', 'Return'),
        ('OT', 'Other'),
    ]
    
    laybye = models.ForeignKey(
        Laybye,
        on_delete=models.CASCADE,
        related_name='transactions'
    )
    
    # Stock details
    stock_code = models.CharField(max_length=13, blank=True)
    
    # Prices and quantity
    cost_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    selling_price = models.DecimalField(max_digits=14, decimal_places=4)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Transaction info
    transaction_date = models.DateField()
    transaction_time = models.TimeField()
    transaction_type = models.CharField(max_length=2, choices=TRANSACTION_TYPE_CHOICES)
    
    # Operational
    station_number = models.PositiveIntegerField(null=True, blank=True)
    salesman_number = models.PositiveIntegerField(null=True, blank=True)
    
    # Calculated
    line_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    class Meta:
        ordering = ['transaction_date', 'transaction_time']
    
    def __str__(self):
        return f"{self.laybye.laybye_number} - {self.transaction_type}"


class LaybyelPayment(TimeStampedModel):
    """Payment on laybye."""
    laybye = models.ForeignKey(
        Laybye,
        on_delete=models.CASCADE,
        related_name='payments'
    )
    payment_date = models.DateField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    
    sales_area = models.ForeignKey(
        SalesArea,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    class Meta:
        ordering = ['payment_date']
    
    def __str__(self):
        return f"{self.laybye.laybye_number} - Payment {self.amount}"


class Quotation(TimeStampedModel):
    """Sales quotation."""
    
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('INVOICED', 'Invoiced'),
        ('EXPIRED', 'Expired'),
        ('CANCELLED', 'Cancelled'),
        ('JOB', 'Converted to Job'),
    ]
    
    PRICE_LEVEL_CHOICES = [
        (1, 'Selling Price 1'),
        (2, 'Selling Price 2'),
        (3, 'Selling Price 3'),
        ('COST', 'Cost Price'),
        ('MARKUP', 'Cost + Markup'),
        ('GP', 'Gross Profit %'),
    ]
    
    quotation_number = models.CharField(max_length=20, unique=True, db_index=True)
    quotation_date = models.DateField()
    expiry_date = models.DateField()
    
    # Customer details
    customer_name = models.CharField(max_length=200)
    address_line1 = models.CharField(max_length=25, blank=True)
    address_line2 = models.CharField(max_length=25, blank=True)
    address_line3 = models.CharField(max_length=25, blank=True)
    telephone = models.CharField(max_length=15, blank=True)
    
    # Debtor relationship
    debtor_account = models.ForeignKey(
        Debtor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='quotations'
    )
    
    sales_area = models.ForeignKey(
        SalesArea,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    station_number = models.PositiveIntegerField(default=1)
    
    # Comments
    comment1 = models.CharField(max_length=30, blank=True)
    comment2 = models.CharField(max_length=30, blank=True)
    
    # Pricing basis
    price_level = models.CharField(max_length=10, choices=PRICE_LEVEL_CHOICES, default=1)
    
    # Totals
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    vat_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    gross_profit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='ACTIVE')
    
    class Meta:
        ordering = ['-quotation_date']
        indexes = [
            models.Index(fields=['status', 'expiry_date']),
        ]
    
    def __str__(self):
        return f"Quotation {self.quotation_number}"


class QuotationLine(TimeStampedModel):
    """Quotation line item (QTRAN equivalent)."""
    quotation = models.ForeignKey(
        Quotation,
        on_delete=models.CASCADE,
        related_name='lines'
    )
    line_number = models.PositiveIntegerField()
    
    # Stock details
    stock_code = models.CharField(max_length=13, blank=True)
    description = models.CharField(max_length=200)
    quantity = models.DecimalField(max_digits=12, decimal_places=4)
    
    # Pricing
    unit_price = models.DecimalField(max_digits=12, decimal_places=4)
    discount_amount = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Tax and department
    tax_code = models.CharField(max_length=1, default='1')
    department = models.CharField(max_length=3, blank=True)
    
    # Comments
    comments = models.CharField(max_length=30, blank=True)
    
    # Calculated fields
    line_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    vat_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    class Meta:
        ordering = ['line_number']
        unique_together = ['quotation', 'line_number']
    
    def __str__(self):
        return f"{self.quotation.quotation_number} - Line {self.line_number}"


class Payout(TimeStampedModel):
    """Cash payout from till."""
    payout_date = models.DateField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payee = models.CharField(max_length=200, help_text="To whom paid")
    description = models.TextField(help_text="Description of goods/service")
    reference = models.CharField(max_length=100, blank=True)
    
    cashier = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='payouts'
    )
    station_number = models.PositiveIntegerField(default=1)
    
    class Meta:
        ordering = ['-payout_date']
    
    def __str__(self):
        return f"Payout {self.amount} to {self.payee}"


class Repair(TimeStampedModel):
    """Repair voucher (REPMAST equivalent)."""
    
    STATUS_CHOICES = [
        ('C', 'Created'),
        ('I', 'Issued to Supplier'),
        ('R', 'Received from Supplier'),
        ('V', 'Invoiced'),
        ('X', 'Cancelled'),
    ]
    
    repair_number = models.CharField(max_length=20, unique=True, db_index=True)
    
    # Customer details
    customer_name = models.CharField(max_length=40)
    address_line1 = models.CharField(max_length=25, blank=True)
    address_line2 = models.CharField(max_length=25, blank=True)
    telephone = models.CharField(max_length=15, blank=True)
    contact_person = models.CharField(max_length=20, blank=True)
    customer_reference = models.CharField(max_length=10, blank=True)
    
    # Order details
    order_number = models.CharField(max_length=10, blank=True)
    date_received = models.DateField(null=True, blank=True)
    date_required = models.DateField()
    quoted_value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    # Repair details (REP table equivalent)
    repair_details = models.TextField(blank=True)
    
    # Supplier details
    supplier_number = models.PositiveIntegerField(null=True, blank=True)
    date_sent = models.DateField(null=True, blank=True)
    date_returned = models.DateField(null=True, blank=True)
    
    # Repair costs
    repair_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )
    selling_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    # Comments
    comment1 = models.CharField(max_length=30, blank=True)
    comment2 = models.CharField(max_length=30, blank=True)
    comment3 = models.CharField(max_length=30, blank=True)
    comment4 = models.CharField(max_length=30, blank=True)
    supplier_comment = models.CharField(max_length=25, blank=True)
    
    # Status
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='C')
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"Repair {self.repair_number}"


class RepairLine(TimeStampedModel):
    """Repair transaction details (REPTRAN equivalent)."""
    
    TRANSACTION_TYPE_CHOICES = [
        ('IS', 'Issue'),
        ('RC', 'Receipt'),
        ('AD', 'Adjustment'),
        ('RT', 'Return'),
        ('OT', 'Other'),
    ]
    
    repair = models.ForeignKey(
        Repair,
        on_delete=models.CASCADE,
        related_name='transactions'
    )
    
    # Transaction details
    transaction_type = models.CharField(max_length=2, choices=TRANSACTION_TYPE_CHOICES)
    transaction_date = models.DateField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Supplier reference
    supplier_number = models.PositiveIntegerField(null=True, blank=True)
    
    # Additional info
    comment = models.CharField(max_length=25, blank=True)
    transport_mode = models.CharField(max_length=15, blank=True)
    station_number = models.PositiveIntegerField(null=True, blank=True)
    
    # Captured info
    date_captured = models.DateField(auto_now_add=True)
    time_captured = models.TimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['transaction_date']
    
    def __str__(self):
        return f"{self.repair.repair_number} - {self.transaction_type}"


class JobCard(TimeStampedModel):
    """Job card for work orders."""
    
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('INVOICED', 'Invoiced'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    job_number = models.CharField(max_length=20, unique=True, db_index=True)
    job_date = models.DateField()
    
    # Customer details
    customer_name = models.CharField(max_length=200)
    address = models.TextField(blank=True)
    telephone = models.CharField(max_length=50, blank=True)
    contact_person = models.CharField(max_length=100, blank=True)
    order_number = models.CharField(max_length=50, blank=True)
    
    # Job details
    registration_number = models.CharField(max_length=50, blank=True)
    job_description = models.TextField(blank=True)
    
    sales_area = models.ForeignKey(
        SalesArea,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    operator_number = models.PositiveIntegerField(null=True, blank=True)
    
    # Totals
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    vat_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    total_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    gross_profit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='ACTIVE')
    
    # Cancellation
    cancellation_reason = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-job_date']
        indexes = [
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"Job {self.job_number}"


class JobCardLine(TimeStampedModel):
    """Job card line item."""
    job_card = models.ForeignKey(
        JobCard,
        on_delete=models.CASCADE,
        related_name='lines'
    )
    line_number = models.PositiveIntegerField()
    
    stock_code = models.CharField(max_length=13, blank=True)
    description = models.CharField(max_length=200)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    
    unit_price = models.DecimalField(max_digits=12, decimal_places=4)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    tax_code = models.PositiveIntegerField(default=1)
    
    line_total = models.DecimalField(max_digits=12, decimal_places=2)
    vat_amount = models.DecimalField(max_digits=12, decimal_places=2)
    cost_price = models.DecimalField(max_digits=12, decimal_places=4, default=0)
    line_profit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    class Meta:
        ordering = ['line_number']
        unique_together = ['job_card', 'line_number']
    
    def __str__(self):
        return f"{self.job_card.job_number} - Line {self.line_number}"


class ReceiptOnAccount(TimeStampedModel):
    """Receipt on account for debtor payments at POS."""
    receipt_number = models.CharField(max_length=20, unique=True, db_index=True)
    receipt_date = models.DateField(db_index=True)
    
    # Debtor details
    debtor_account = models.CharField(max_length=20, db_index=True)
    debtor_name = models.CharField(max_length=200)
    
    # Amounts
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    settlement_discount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Payment details
    tender_type = models.CharField(
        max_length=15,
        choices=[
            ('CASH', 'Cash'),
            ('CHEQUE', 'Cheque'),
            ('SPEEDPOINT', 'Speedpoint/Card'),
            ('EFT', 'EFT'),
        ]
    )
    
    # For cheques
    cheque_number = models.CharField(max_length=50, blank=True)
    bank_name = models.CharField(max_length=100, blank=True)
    
    # For speedpoint
    card_type = models.CharField(max_length=50, blank=True)
    authorization_code = models.CharField(max_length=50, blank=True)
    
    reference = models.CharField(max_length=200, blank=True)
    
    # POS details
    cashier = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='receipts_on_account'
    )
    station_number = models.PositiveIntegerField(default=1)
    
    # Status
    is_posted = models.BooleanField(default=False)
    is_cancelled = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-receipt_date']
        indexes = [
            models.Index(fields=['debtor_account', 'receipt_date']),
            models.Index(fields=['is_posted']),
        ]
    
    def __str__(self):
        return f"Receipt {self.receipt_number} - {self.debtor_name}"


class CreditNote(TimeStampedModel):
    """Credit note for returns."""
    credit_number = models.CharField(max_length=20, unique=True, db_index=True)
    credit_date = models.DateField(db_index=True)
    
    # Customer details (can be cash customer or debtor)
    customer_name = models.CharField(max_length=200, blank=True)
    debtor_account = models.CharField(max_length=20, blank=True, db_index=True)
    
    # Original sale reference
    original_sale_number = models.CharField(max_length=20, blank=True)
    reason = models.TextField(blank=True)
    
    sales_area = models.ForeignKey(
        SalesArea,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    # Totals
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    vat_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Refund method
    refund_type = models.CharField(
        max_length=15,
        choices=[
            ('CASH', 'Cash'),
            ('ACCOUNT', 'Credit to Account'),
            ('REPLACEMENT', 'Replacement'),
        ],
        default='CASH'
    )
    
    # POS details
    cashier = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='credit_notes'
    )
    station_number = models.PositiveIntegerField(default=1)
    
    # Status
    is_posted = models.BooleanField(default=False)
    is_cancelled = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-credit_date']
        indexes = [
            models.Index(fields=['debtor_account', 'credit_date']),
            models.Index(fields=['is_posted']),
        ]
    
    def __str__(self):
        return f"Credit Note {self.credit_number}"


class CreditNoteLine(TimeStampedModel):
    """Credit note line item."""
    credit_note = models.ForeignKey(
        CreditNote,
        on_delete=models.CASCADE,
        related_name='lines'
    )
    line_number = models.PositiveIntegerField()
    
    stock_code = models.CharField(max_length=13, blank=True)
    description = models.CharField(max_length=200)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    
    unit_price = models.DecimalField(max_digits=12, decimal_places=4)
    tax_code = models.PositiveIntegerField(default=1)
    
    # Calculated fields
    line_total = models.DecimalField(max_digits=12, decimal_places=2)
    vat_amount = models.DecimalField(max_digits=12, decimal_places=2)
    
    class Meta:
        ordering = ['line_number']
        unique_together = ['credit_note', 'line_number']
    
    def __str__(self):
        return f"{self.credit_note.credit_number} - Line {self.line_number}"


class CashReturn(TimeStampedModel):
    """Cash return/refund for cash sales."""
    return_number = models.CharField(max_length=20, unique=True, db_index=True)
    return_date = models.DateField(db_index=True)
    
    # Original sale reference
    original_sale_number = models.CharField(max_length=20)
    customer_name = models.CharField(max_length=200, blank=True)
    reason = models.TextField()
    
    # Amounts
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    vat_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # POS details
    cashier = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='cash_returns'
    )
    station_number = models.PositiveIntegerField(default=1)
    
    # Status
    is_posted = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-return_date']
        indexes = [
            models.Index(fields=['original_sale_number']),
        ]
    
    def __str__(self):
        return f"Cash Return {self.return_number}"


class CashReturnLine(TimeStampedModel):
    """Cash return line item."""
    cash_return = models.ForeignKey(
        CashReturn,
        on_delete=models.CASCADE,
        related_name='lines'
    )
    line_number = models.PositiveIntegerField()
    
    stock_code = models.CharField(max_length=13, blank=True)
    description = models.CharField(max_length=200)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    
    unit_price = models.DecimalField(max_digits=12, decimal_places=4)
    tax_code = models.PositiveIntegerField(default=1)
    
    # Calculated fields
    line_total = models.DecimalField(max_digits=12, decimal_places=2)
    vat_amount = models.DecimalField(max_digits=12, decimal_places=2)
    
    class Meta:
        ordering = ['line_number']
        unique_together = ['cash_return', 'line_number']
    
    def __str__(self):
        return f"{self.cash_return.return_number} - Line {self.line_number}"


class CashACheque(TimeStampedModel):
    """Cash a cheque transaction."""
    transaction_number = models.CharField(max_length=20, unique=True, db_index=True)
    transaction_date = models.DateField(db_index=True)
    
    # Customer details
    drawer_name = models.CharField(max_length=200)
    id_number = models.CharField(max_length=50)
    telephone = models.CharField(max_length=50, blank=True)
    address = models.TextField(blank=True)
    
    # Cheque details
    cheque_number = models.CharField(max_length=50)
    bank_name = models.CharField(max_length=100)
    branch_code = models.CharField(max_length=20, blank=True)
    account_number = models.CharField(max_length=50, blank=True)
    
    # Amounts
    cheque_amount = models.DecimalField(max_digits=12, decimal_places=2)
    commission = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    cash_paid = models.DecimalField(max_digits=12, decimal_places=2)
    
    # POS details
    cashier = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='cashed_cheques'
    )
    station_number = models.PositiveIntegerField(default=1)
    
    # Status
    is_processed = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-transaction_date']
        indexes = [
            models.Index(fields=['drawer_name']),
            models.Index(fields=['cheque_number']),
        ]
    
    def __str__(self):
        return f"Cash Cheque {self.transaction_number} - {self.drawer_name}"


class TransactionQuery(TimeStampedModel):
    """Transaction query/enquiry system."""
    query_number = models.CharField(max_length=20, unique=True, db_index=True)
    query_date = models.DateField(db_index=True)
    
    # Query details
    transaction_type = models.CharField(
        max_length=20,
        choices=[
            ('CASH_SALE', 'Cash Sale'),
            ('INVOICE', 'Invoice'),
            ('RECEIPT', 'Receipt on Account'),
            ('CREDIT_NOTE', 'Credit Note'),
            ('LAYBYE', 'Laybye'),
            ('QUOTATION', 'Quotation'),
            ('JOB_CARD', 'Job Card'),
            ('REPAIR', 'Repair'),
            ('PAYOUT', 'Payout'),
        ]
    )
    transaction_number = models.CharField(max_length=20, db_index=True)
    
    # Query raised by
    customer_name = models.CharField(max_length=200, blank=True)
    contact_number = models.CharField(max_length=50, blank=True)
    
    # Query details
    query_description = models.TextField()
    query_status = models.CharField(
        max_length=20,
        choices=[
            ('OPEN', 'Open'),
            ('IN_PROGRESS', 'In Progress'),
            ('RESOLVED', 'Resolved'),
            ('CLOSED', 'Closed'),
        ],
        default='OPEN'
    )
    
    # Resolution
    resolution_notes = models.TextField(blank=True)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_queries'
    )
    resolved_date = models.DateField(null=True, blank=True)
    
    # Assigned to
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_queries'
    )
    
    class Meta:
        ordering = ['-query_date']
        verbose_name_plural = 'Transaction Queries'
        indexes = [
            models.Index(fields=['query_status', 'query_date']),
            models.Index(fields=['transaction_number']),
        ]
    
    def __str__(self):
        return f"Query {self.query_number} - {self.transaction_type}"


class CashControl(TimeStampedModel):
    """Daily cash control totals per cashier."""
    control_date = models.DateField(db_index=True)
    cashier = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    station_number = models.PositiveIntegerField(default=1)
    
    # Transactions
    cash_sales_count = models.PositiveIntegerField(default=0)
    cash_sales_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    cash_refunds_count = models.PositiveIntegerField(default=0)
    cash_refunds_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    invoices_count = models.PositiveIntegerField(default=0)
    invoices_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    credits_count = models.PositiveIntegerField(default=0)
    credits_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    receipts_count = models.PositiveIntegerField(default=0)
    receipts_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    settlement_discount_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Laybyes
    new_laybyes_count = models.PositiveIntegerField(default=0)
    new_laybyes_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    cancelled_laybyes_count = models.PositiveIntegerField(default=0)
    cancelled_laybyes_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    laybye_receipts_count = models.PositiveIntegerField(default=0)
    laybye_receipts_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    laybye_refunds_count = models.PositiveIntegerField(default=0)
    laybye_refunds_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    completed_laybyes_count = models.PositiveIntegerField(default=0)
    completed_laybyes_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Payouts
    payouts_count = models.PositiveIntegerField(default=0)
    payouts_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Cash a Cheque
    cashed_cheques_count = models.PositiveIntegerField(default=0)
    cashed_cheques_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Takings by type
    cash_takings = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    cheque_takings = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    voucher_takings = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    speedpoint_takings = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Refunds by type
    cash_refunds = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    cheque_refunds = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    voucher_refunds = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Rounding
    rounding_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Abandoned transactions
    abandoned_count = models.PositiveIntegerField(default=0)
    abandoned_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Cleared flag
    is_cleared = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-control_date', 'cashier']
        unique_together = ['control_date', 'cashier', 'station_number']
        indexes = [
            models.Index(fields=['control_date', 'is_cleared']),
        ]
    
    def __str__(self):
        return f"Cash Control {self.control_date} - {self.cashier.username}"