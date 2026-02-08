"""
Debtors (Customers) models.
Based on the Debtors.pdf documentation.
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import date
from apps.settings.models import TimeStampedModel, SalesArea


class Debtor(TimeStampedModel):
    """Customer/Debtor account."""
    
    ACCOUNT_CATEGORY_CHOICES = [
        ('', 'Balance Brought Forward'),
        ('O', 'Open Item'),
        ('C', 'Cash Customer'),
    ]
    
    account_number = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    search_name = models.CharField(max_length=50, db_index=True)
    
    # Contact Information
    contact_person = models.CharField(max_length=100, blank=True)
    telephone1 = models.CharField(max_length=50, blank=True)
    telephone2 = models.CharField(max_length=50, blank=True)
    fax = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    additional_info = models.TextField(blank=True)
    
    # Postal Address
    postal_address_line1 = models.CharField(max_length=200, blank=True)
    postal_address_line2 = models.CharField(max_length=200, blank=True)
    postal_address_line3 = models.CharField(max_length=200, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    
    # Delivery Address
    delivery_address_line1 = models.CharField(max_length=200, blank=True)
    delivery_address_line2 = models.CharField(max_length=200, blank=True)
    delivery_address_line3 = models.CharField(max_length=200, blank=True)
    delivery_code = models.CharField(max_length=20, blank=True)
    
    # Business Details
    vat_number = models.CharField(max_length=50, blank=True)
    
    # Sales Information
    sales_area = models.ForeignKey(
        SalesArea,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='debtors'
    )
    
    # Account Settings
    account_category = models.CharField(
        max_length=1,
        choices=ACCOUNT_CATEGORY_CHOICES,
        default='',
        help_text="Blank=Balance Forward, O=Open Item, C=Cash"
    )
    trade_discount = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    credit_limit = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )
    price_level = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(3)]
    )
    
    # Terms
    terms = models.PositiveIntegerField(
        default=30,
        help_text="Payment terms in days (0, 30, 60, 90)"
    )
    prompt_discount_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    print_discount_on_invoice = models.BooleanField(default=False)
    
    # Settings
    charge_interest = models.BooleanField(default=False)
    print_balance_on_documents = models.BooleanField(default=True)
    
    # Block Status
    is_blocked = models.BooleanField(default=False)
    block_reason = models.CharField(max_length=200, blank=True)
    block_invoicing = models.BooleanField(default=False)
    block_receipts = models.BooleanField(default=False)
    
    # Balances (calculated fields - updated by transactions)
    current_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    balance_30_days = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    balance_60_days = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    balance_90_days = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    balance_120_days = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    balance_150_days = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    balance_180_days = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    # Denormalized field for performance: cached total of all aging buckets
    total_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0, db_index=True)
    
    # Statistics
    last_payment_date = models.DateField(null=True, blank=True)
    last_payment_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    sales_mtd = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    sales_ytd = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    is_active = models.BooleanField(default=True)
    
    # Audit fields
    blocked_by = models.CharField(max_length=200, blank=True, help_text="User who blocked this account")
    blocked_date = models.DateTimeField(null=True, blank=True)
    unblocked_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['account_number']
        indexes = [
            models.Index(fields=['search_name']),
            models.Index(fields=['sales_area']),
            models.Index(fields=['is_active']),
            models.Index(fields=['is_blocked']),
            models.Index(fields=['total_balance']),
        ]
    
    def __str__(self):
        return f"{self.account_number} - {self.name}"
    
    def clean(self):
        """Validate debtor data."""
        # Credit limit must be non-negative
        if self.credit_limit < 0:
            raise ValidationError({'credit_limit': 'Credit limit cannot be negative.'})
        
        # Trade discount must be between 0-100
        if not 0 <= self.trade_discount <= 100:
            raise ValidationError({'trade_discount': 'Trade discount must be between 0 and 100.'})
        
        # Prompt discount must be between 0-100
        if not 0 <= self.prompt_discount_percentage <= 100:
            raise ValidationError({'prompt_discount_percentage': 'Discount percentage must be between 0 and 100.'})
        
        # Price level must be 1-3
        if not 1 <= self.price_level <= 3:
            raise ValidationError({'price_level': 'Price level must be between 1 and 3.'})
        
        # Terms must be valid (0, 30, 60, 90)
        valid_terms = [0, 30, 60, 90]
        if self.terms not in valid_terms:
            raise ValidationError({'terms': f'Terms must be one of: {valid_terms}.'})
        
        # Cannot have credit limit if cash customer
        if self.account_category == 'C' and self.credit_limit > 0:
            raise ValidationError({'credit_limit': 'Cash customers should not have a credit limit.'})
        
        # Block reason required if blocked
        if self.is_blocked and not self.block_reason:
            raise ValidationError({'block_reason': 'Block reason is required when blocking an account.'})
    
    def save(self, *args, **kwargs):
        """Save and update total_balance denormalized field."""
        # Update denormalized total_balance
        self.total_balance = (
            self.current_balance +
            self.balance_30_days +
            self.balance_60_days +
            self.balance_90_days +
            self.balance_120_days +
            self.balance_150_days +
            self.balance_180_days
        )
        super().save(*args, **kwargs)
    
    def recalculate_total_balance(self):
        """Recalculate and save total_balance."""
        self.total_balance = (
            self.current_balance +
            self.balance_30_days +
            self.balance_60_days +
            self.balance_90_days +
            self.balance_120_days +
            self.balance_150_days +
            self.balance_180_days
        )
        self.save(update_fields=['total_balance'])


class AuditLog(TimeStampedModel):
    """Audit log for sensitive debtor changes."""
    
    CHANGE_TYPE_CHOICES = [
        ('BLOCK', 'Account Blocked'),
        ('UNBLOCK', 'Account Unblocked'),
        ('CREDIT_LIMIT', 'Credit Limit Changed'),
        ('INTEREST', 'Interest Charged'),
        ('PAYMENT', 'Payment Recorded'),
        ('BALANCE', 'Balance Adjusted'),
    ]
    
    debtor = models.ForeignKey(
        Debtor,
        on_delete=models.CASCADE,
        related_name='audit_logs'
    )
    change_type = models.CharField(max_length=20, choices=CHANGE_TYPE_CHOICES)
    old_value = models.TextField(blank=True)
    new_value = models.TextField(blank=True)
    changed_by = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['debtor', 'created_at']),
            models.Index(fields=['change_type', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.debtor.account_number} - {self.change_type}"


class DebtorTransaction(TimeStampedModel):
    """Base class for debtor transactions."""
    
    TRANSACTION_TYPE_CHOICES = [
        ('INV', 'Invoice'),
        ('CRN', 'Credit Note'),
        ('CSH', 'Cash Sale'),
        ('CSR', 'Cash Return'),
        ('RCT', 'Receipt'),
        ('SDI', 'Settlement Discount'),
        ('INT', 'Interest Charge'),
        ('DBJ', 'Debit Journal'),
        ('CRJ', 'Credit Journal'),
        ('LAY', 'Laybye Sale'),
    ]
    
    debtor = models.ForeignKey(
        Debtor,
        on_delete=models.PROTECT,
        related_name='transactions'
    )
    transaction_type = models.CharField(max_length=3, choices=TRANSACTION_TYPE_CHOICES)
    transaction_number = models.CharField(max_length=20, db_index=True)
    transaction_date = models.DateField(db_index=True)
    
    # Amounts
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    vat_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    
    # References
    reference = models.CharField(max_length=100, blank=True)
    additional_reference = models.CharField(max_length=200, blank=True)
    
    # Ageing (for balance brought forward accounts)
    age_current = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    age_30 = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    age_60 = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    age_90 = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    age_120 = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    age_150 = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    age_180 = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # For open item accounts
    is_allocated = models.BooleanField(default=False)
    balance_due = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    
    class Meta:
        ordering = ['-transaction_date', '-created_at']
        indexes = [
            models.Index(fields=['debtor', 'transaction_date']),
            models.Index(fields=['transaction_type', 'transaction_date']),
            models.Index(fields=['is_allocated']),
        ]
    
    def __str__(self):
        return f"{self.transaction_type} {self.transaction_number} - {self.debtor.name}"
    
    def clean(self):
        """Validate transaction data."""
        if self.total_amount <= 0 and self.transaction_type != 'CRN':
            raise ValidationError('Transaction amount must be greater than zero.')
        
        if self.amount > self.total_amount:
            raise ValidationError('Amount cannot exceed total amount.')


class Invoice(TimeStampedModel):
    """Customer invoice with state machine workflow."""
    
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('POSTED', 'Posted'),
        ('PAID', 'Paid'),
        ('PARTIAL_PAID', 'Partially Paid'),
        ('OVERDUE', 'Overdue'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    debtor = models.ForeignKey(Debtor, on_delete=models.PROTECT, related_name='invoices')
    invoice_number = models.CharField(max_length=20, unique=True, db_index=True)
    invoice_date = models.DateField(db_index=True)
    
    # Header Information
    delivery_name = models.CharField(max_length=200, blank=True)
    delivery_address_line1 = models.CharField(max_length=200, blank=True)
    delivery_address_line2 = models.CharField(max_length=200, blank=True)
    delivery_telephone = models.CharField(max_length=50, blank=True)
    order_number = models.CharField(max_length=50, blank=True)
    customer_reference = models.CharField(max_length=50, blank=True)
    job_card_number = models.CharField(max_length=50, blank=True)
    
    sales_area = models.ForeignKey(
        SalesArea,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    # Totals
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    vat_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Cost and Profit
    total_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    gross_profit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Status and Workflow
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    is_posted = models.BooleanField(default=False)  # Kept for backwards compatibility
    is_cancelled = models.BooleanField(default=False)  # Kept for backwards compatibility
    
    # Payment tracking
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    paid_date = models.DateField(null=True, blank=True)
    
    class Meta:
        ordering = ['-invoice_date', '-invoice_number']
        indexes = [
            models.Index(fields=['debtor', 'invoice_date']),
            models.Index(fields=['is_posted']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"Invoice {self.invoice_number}"
    
    def clean(self):
        """Validate invoice state."""
        # Cannot modify posted invoices
        if self.is_posted and self.pk:
            orig = Invoice.objects.get(pk=self.pk)
            if orig.is_posted and self.total_amount != orig.total_amount:
                raise ValidationError('Cannot modify amounts on posted invoices.')
        
        # Amount paid cannot exceed total
        if self.amount_paid > self.total_amount:
            raise ValidationError('Amount paid cannot exceed total invoice amount.')
    
    def can_be_posted(self):
        """Check if invoice can be posted."""
        return self.status == 'DRAFT' and self.total_amount > 0 and not self.is_cancelled
    
    def mark_as_posted(self):
        """Transition invoice to posted state."""
        if not self.can_be_posted():
            raise ValidationError(f'Invoice cannot be posted (current status: {self.status})')
        self.status = 'POSTED'
        self.is_posted = True
        self.save()
    
    def mark_as_paid(self):
        """Mark invoice as fully paid."""
        if self.status in ['CANCELLED']:
            raise ValidationError(f'Cannot mark {self.status} invoice as paid')
        self.status = 'PAID'
        self.amount_paid = self.total_amount
        self.paid_date = date.today()
        self.save()
    
    def mark_as_cancelled(self, reason=''):
        """Cancel invoice."""
        if self.status == 'PAID':
            raise ValidationError('Cannot cancel a paid invoice')
        self.status = 'CANCELLED'
        self.is_cancelled = True
        self.save()


class InvoiceLine(TimeStampedModel):
    """Invoice line item."""
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='lines')
    line_number = models.PositiveIntegerField()
    
    stock_code = models.CharField(max_length=13, blank=True)
    description = models.CharField(max_length=200)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    
    unit_price = models.DecimalField(max_digits=12, decimal_places=4)
    discount_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0
    )
    tax_code = models.PositiveIntegerField(default=1)
    
    # Calculated fields
    line_total = models.DecimalField(max_digits=12, decimal_places=2)
    vat_amount = models.DecimalField(max_digits=12, decimal_places=2)
    cost_price = models.DecimalField(max_digits=12, decimal_places=4, default=0)
    line_profit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    class Meta:
        ordering = ['line_number']
        unique_together = ['invoice', 'line_number']
    
    def __str__(self):
        return f"{self.invoice.invoice_number} - Line {self.line_number}"
    
    def clean(self):
        """Validate line item data."""
        if self.quantity <= 0:
            raise ValidationError('Quantity must be greater than zero.')
        if self.unit_price < 0:
            raise ValidationError('Unit price cannot be negative.')
        if not 0 <= self.discount_percentage <= 100:
            raise ValidationError('Discount percentage must be between 0 and 100.')
        if self.cost_price < 0:
            raise ValidationError('Cost price cannot be negative.')


class PostDatedCheque(TimeStampedModel):
    """Post-dated cheques for debtors."""
    debtor = models.ForeignKey(
        Debtor,
        on_delete=models.CASCADE,
        related_name='post_dated_cheques'
    )
    cheque_date = models.DateField(db_index=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    reference = models.CharField(max_length=100, blank=True)
    is_processed = models.BooleanField(default=False)
    processed_date = models.DateField(null=True, blank=True)
    
    class Meta:
        ordering = ['cheque_date']
        indexes = [
            models.Index(fields=['debtor', 'is_processed']),
            models.Index(fields=['cheque_date', 'is_processed']),
        ]
    
    def __str__(self):
        return f"PDC {self.debtor.name} - {self.cheque_date}"
    
    def clean(self):
        """Validate PDC data."""
        if self.amount <= 0:
            raise ValidationError('PDC amount must be greater than zero.')
        if self.cheque_date < date.today() and not self.is_processed:
            raise ValidationError('Cheque date cannot be in the past for unprocessed cheques.')