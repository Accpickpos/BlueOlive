"""
Debtors (Customers) models.
Based on the Debtors.pdf documentation.
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import date
from apps.settings.models import TimeStampedModel, SalesArea, PostingStatusMixin


class Debtor(TimeStampedModel):
    """Debtor/Customer Master File (DMAST table).
    
    Stores all customer account information, balances, and settings.
    Maps from legacy DMAST table structure.
    """
    
    ACCOUNT_CATEGORY_CHOICES = [
        ('', 'Balance Brought Forward'),
        ('O', 'Open Item'),
        ('C', 'Cash Customer'),
    ]
    
    INTEREST_FLAG_CHOICES = [
        ('Y', 'Yes - Charge Interest'),
        ('N', 'No - Do Not Charge'),
    ]
    
    # Account Identification (DMAST fields)
    dno = models.PositiveIntegerField(
        primary_key=False,
        unique=True,
        db_index=True,
        help_text="Debtor Account Number (DNO) - Numeric 5"
    )
    dname = models.CharField(
        max_length=40,
        help_text="Debtors Name (DNAME) - Character 40"
    )
    dsname = models.CharField(
        max_length=5,
        db_index=True,
        help_text="Short/Sort Name (DSNAME) - Character 5"
    )
    
    # Contact Information
    dcontact = models.CharField(
        max_length=20,
        blank=True,
        help_text="Contact Person (DCONTACT) - Character 20"
    )
    dtel = models.CharField(
        max_length=15,
        blank=True,
        help_text="Telephone # (DTEL) - Character 15"
    )
    dfax = models.CharField(
        max_length=15,
        blank=True,
        help_text="Fax # (DFAX) - Character 15"
    )
    
    # Postal Address
    dadd1 = models.CharField(
        max_length=25,
        blank=True,
        help_text="Postal Address Line 1 (DADD1) - Character 25"
    )
    dadd2 = models.CharField(
        max_length=25,
        blank=True,
        help_text="Postal Address Line 2 (DADD2) - Character 25"
    )
    dadd3 = models.CharField(
        max_length=25,
        blank=True,
        help_text="Postal Address Line 3 (DADD3) - Character 25"
    )
    dpcode = models.CharField(
        max_length=4,
        blank=True,
        help_text="Postal Code (DPCODE) - Character 4"
    )
    
    # Delivery Address
    delad1 = models.CharField(
        max_length=25,
        blank=True,
        help_text="Delivery Address Line 1 (DELAD1) - Character 25"
    )
    delad2 = models.CharField(
        max_length=25,
        blank=True,
        help_text="Delivery Address Line 2 (DELAD2) - Character 25"
    )
    delad3 = models.CharField(
        max_length=25,
        blank=True,
        help_text="Delivery Address Line 3 (DELAD3) - Character 25"
    )
    delad4 = models.CharField(
        max_length=25,
        blank=True,
        help_text="Delivery Address Line 4 (DELAD4) - Character 25"
    )
    
    # Business Identifiers
    dtaxno = models.CharField(
        max_length=20,
        blank=True,
        help_text="Tax No. (DTAXNO) - Character 20"
    )
    
    # Sales Area & Salesman
    darea = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(99)],
        help_text="Salesman/Area # (DAREA) - Numeric 2"
    )
    
    # Account Configuration
    acctype = models.CharField(
        max_length=1,
        choices=ACCOUNT_CATEGORY_CHOICES,
        default='',
        help_text="Account Category/Type (ACCTYPE) - Blank=Balance Forward, O=Open Item, C=Cash"
    )
    price = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(3)],
        help_text="Price Level (PRICE) - Numeric 1 (1, 2, or 3)"
    )
    terms = models.PositiveIntegerField(
        default=30,
        validators=[MinValueValidator(0), MaxValueValidator(999)],
        help_text="Payment Terms (TERMS) - Numeric 3 (in days)"
    )
    
    # Discount Settings
    ddiscper = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Discount % (DDISCPER) - Numeric 10.2"
    )
    pdisc = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Prompt Discount (PDISC) - Numeric 6.2"
    )
    discprn = models.CharField(
        max_length=1,
        choices=[('Y', 'Yes'), ('N', 'No')],
        default='N',
        help_text="Print Discount on Invoice (DISCPRN) - Character 1"
    )
    
    # Credit Limit
    dclimit = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Credit Limit (DCLIMIT) - Numeric 12.2"
    )
    
    # Interest & Block Flags
    dintflag = models.CharField(
        max_length=1,
        choices=INTEREST_FLAG_CHOICES,
        default='N',
        help_text="Charge Interest Y/N (DINTFLAG) - Character 1"
    )
    blockflag = models.CharField(
        max_length=1,
        choices=[('Y', 'Blocked'), ('N', 'Active')],
        default='N',
        help_text="Block Account (BLOCKFLAG) - Character 1"
    )
    dposbal = models.CharField(
        max_length=1,
        choices=[('Y', 'Yes'), ('N', 'No')],
        default='Y',
        help_text="Print Account Balance on POS (DPOSBAL) - Character 1"
    )
    
    # Account Balances (DMAST aging buckets)
    dbalbfwd = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Balance B/F from Previous Month (DBALBFWD) - Numeric 10.2"
    )
    dcrnt = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Current Balance (DCRNT) - Numeric 10.2"
    )
    d30 = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="30 Day Balance (D30) - Numeric 10.2"
    )
    d60 = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="60 Day Balance (D60) - Numeric 10.2"
    )
    d90 = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="90 Day Balance (D90) - Numeric 10.2"
    )
    d120 = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="120 Day Balance (D120) - Numeric 10.2"
    )
    d150 = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="150 Day Balance (D150) - Numeric 10.2"
    )
    d180 = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="180 Day Balance (D180) - Numeric 10.2"
    )
    
    # Sales & Profit Statistics
    dsalesm = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Sales Total for Month (DSALESM) - Numeric 10.2"
    )
    dsalesy = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Sales Total for Year (DSALESY) - Numeric 10.2"
    )
    dprofitm = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Profit for Month (DPROFITM) - Numeric 10.2"
    )
    dprofity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Profit for Year (DPROFITY) - Numeric 10.2"
    )
    
    # Payment Tracking
    damtlpd = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Amount Last Paid (DAMTLPD) - Numeric 10.2"
    )
    ddatlpd = models.DateField(
        null=True,
        blank=True,
        help_text="Date Last Paid (DDATLPD) - Date 8"
    )
    
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['dno']
        verbose_name = 'Debtor Master (DMAST)'
        verbose_name_plural = 'Debtor Masters (DMAST)'
        indexes = [
            models.Index(fields=['dsname']),
            models.Index(fields=['darea']),
            models.Index(fields=['is_active']),
            models.Index(fields=['blockflag']),
        ]
    
    def __str__(self):
        return f"{self.dno} - {self.dname}"
    
    def clean(self):
        """Validate debtor data."""
        # Credit limit must be non-negative
        if self.dclimit < 0:
            raise ValidationError({'dclimit': 'Credit limit cannot be negative.'})
        
        # Discount percentages must be 0-100
        if not 0 <= self.ddiscper <= 100:
            raise ValidationError({'ddiscper': 'Discount percentage must be between 0 and 100.'})
        
        if not 0 <= self.pdisc <= 100:
            raise ValidationError({'pdisc': 'Prompt discount must be between 0 and 100.'})
        
        # Price level must be 1-3
        if not 1 <= self.price <= 3:
            raise ValidationError({'price': 'Price level must be between 1 and 3.'})
        
        # Terms must be non-negative
        if self.terms < 0:
            raise ValidationError({'terms': 'Payment terms must be non-negative.'})
        
        # Cash customers should not have credit limit
        if self.acctype == 'C' and self.dclimit > 0:
            raise ValidationError({'dclimit': 'Cash customers should not have a credit limit.'})
    
    def save(self, *args, **kwargs):
        """Save debtor record."""
        self.full_clean()
        super().save(*args, **kwargs)
    
    def get_total_balance(self):
        """Calculate total balance across all aging buckets."""
        return (
            self.dcrnt + self.d30 + self.d60 + self.d90 +
            self.d120 + self.d150 + self.d180
        )
    
    def get_overdue_balance(self):
        """Get balance over 30 days old."""
        return (
            self.d30 + self.d60 + self.d90 +
            self.d120 + self.d150 + self.d180
        )
    
    def get_aged_balance(self, days):
        """Get  balance for specific age bucket."""
        if days == 0:
            return self.dcrnt
        elif days == 30:
            return self.d30
        elif days == 60:
            return self.d60
        elif days == 90:
            return self.d90
        elif days == 120:
            return self.d120
        elif days == 150:
            return self.d150
        elif days == 180:
            return self.d180
        return Decimal(0)
    
    def is_blocked(self):
        """Check if account is blocked."""
        return self.blockflag == 'Y'
    
    def set_blocked(self, blocked=True):
        """Block or unblock account."""
        self.blockflag = 'Y' if blocked else 'N'
        self.save(update_fields=['blockflag'])
    
    def set_interest_flag(self, charge_interest=True):
        """Set whether to charge interest."""
        self.dintflag = 'Y' if charge_interest else 'N'
        self.save(update_fields=['dintflag'])


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
    """Debtor Transactions (DEBTRAN table).
    
    Transactions on invoice sales, cash sales, C/N, Cash/Ret, Debtors Receipts.
    Tracks all postings to debtor accounts.
    """
    
    TRANSACTION_TYPE_CHOICES = [
        ('IN', 'Invoice'),
        ('CN', 'Credit Note'),
        ('CS', 'Cash Sale'),
        ('CR', 'Cash Return'),
        ('RCP', 'Receipt'),
        ('INT', 'Interest Charge'),
        ('JD', 'Journal Debit'),
        ('JC', 'Journal Credit'),
    ]
    
    VAT_STATUS_CHOICES = [
        ('S', 'Taxable'),
        ('E', 'Exempt'),
        ('Z', 'Zero Rated'),
    ]
    
    # Foreign Key to Debtor
    dno = models.ForeignKey(
        Debtor,
        on_delete=models.PROTECT,
        related_name='debtran_transactions',
        help_text="Debtor account number (DNO)"
    )
    
    # Transaction Identification
    dtrano = models.CharField(
        max_length=6,
        db_index=True,
        help_text="Transaction # (DTRANO) - Numeric 6"
    )
    dtype = models.CharField(
        max_length=3,
        choices=TRANSACTION_TYPE_CHOICES,
        help_text="Transaction Type (DTYPE) - Character 3"
    )
    dtdate = models.DateField(
        db_index=True,
        help_text="Transaction Date (DTDATE) - Date 8"
    )
    time = models.TimeField(
        null=True,
        blank=True,
        help_text="Transaction Time (TIME) - Character 8 (HH:MM:SS)"
    )
    
    # Amounts
    dtsub = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Total Excl. VAT (DTSUB) - Numeric 12.2"
    )
    dtgst = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="VAT (DTGST) - Numeric 12.2"
    )
    dttot = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Transaction Total (DTTOT) - Numeric 12.2"
    )
    dtaxstat = models.CharField(
        max_length=1,
        choices=VAT_STATUS_CHOICES,
        default='S',
        help_text="VAT Status (DTAXSTAT) - Character 1"
    )
    
    # Source & References
    source = models.PositiveIntegerField(
        default=0,
        validators=[MaxValueValidator(99)],
        help_text="Station No. (SOURCE) - Numeric 2"
    )
    ordno = models.CharField(
        max_length=10,
        blank=True,
        help_text="Order # (ORDNO) - Character 10"
    )
    custref = models.CharField(
        max_length=10,
        blank=True,
        help_text="Customer Ref (CUSTREF) - Character 10"
    )
    
    # Delivery Details
    del1 = models.CharField(
        max_length=25,
        blank=True,
        help_text="Delivery Details Line 1 (DEL1) - Character 25"
    )
    del2 = models.CharField(
        max_length=25,
        blank=True,
        help_text="Delivery Details Line 2 (DEL2) - Character 25"
    )
    del3 = models.CharField(
        max_length=25,
        blank=True,
        help_text="Delivery Details Line 3 (DEL3) - Character 25"
    )
    del4 = models.CharField(
        max_length=25,
        blank=True,
        help_text="Delivery Details Line 4 (DEL4) - Character 25"
    )
    
    class Meta:
        ordering = ['-dtdate', '-dtrano']
        verbose_name = 'Debtor Transaction (DEBTRAN)'
        verbose_name_plural = 'Debtor Transactions (DEBTRAN)'
        unique_together = ['dno', 'dtrano', 'dtdate']
        indexes = [
            models.Index(fields=['dno', 'dtdate']),
            models.Index(fields=['dtype', 'dtdate']),
            models.Index(fields=['dtdate']),
        ]
    
    def __str__(self):
        return f"DEBTRAN {self.dno.dno} - {self.dtrano} ({self.dtdate})"
    
    def clean(self):
        """Validate transaction data."""
        if self.dtsub < 0:
            raise ValidationError('Amount excl. VAT cannot be negative.')
        if self.dtgst < 0:
            raise ValidationError('VAT amount cannot be negative.')
        if self.dttot <= 0 and self.dtype != 'CN':
            raise ValidationError('Transaction total must be greater than zero.')
    
    def save(self, *args, **kwargs):
        """Validate before saving."""
        self.full_clean()
        super().save(*args, **kwargs)


class Invoice(PostingStatusMixin, TimeStampedModel):
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


class Darea(TimeStampedModel):
    """Sales Area/Salesman & Sales total per sales area per month (DAREA table)."""
    
    darea = models.CharField(
        max_length=2,
        unique=True,
        primary_key=True,
        help_text="Salesman/area number"
    )
    dareaname = models.CharField(
        max_length=20,
        help_text="Salesman/area name"
    )
    
    # Monthly sales totals
    arsls1 = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Total sales for month 1",
        validators=[MinValueValidator(0)]
    )
    arsls2 = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Total sales for month 2",
        validators=[MinValueValidator(0)]
    )
    arsls3 = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Total sales for month 3",
        validators=[MinValueValidator(0)]
    )
    arsls4 = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Total sales for month 4",
        validators=[MinValueValidator(0)]
    )
    arsls5 = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Total sales for month 5",
        validators=[MinValueValidator(0)]
    )
    arsls6 = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Total sales for month 6",
        validators=[MinValueValidator(0)]
    )
    arsls7 = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Total sales for month 7",
        validators=[MinValueValidator(0)]
    )
    arsls8 = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Total sales for month 8",
        validators=[MinValueValidator(0)]
    )
    arsls9 = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Total sales for month 9",
        validators=[MinValueValidator(0)]
    )
    arsls10 = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Total sales for month 10",
        validators=[MinValueValidator(0)]
    )
    arsls11 = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Total sales for month 11",
        validators=[MinValueValidator(0)]
    )
    arsls12 = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Total sales for month 12",
        validators=[MinValueValidator(0)]
    )
    
    class Meta:
        ordering = ['darea']
        verbose_name = 'Daily Area Sales (DAREA)'
        verbose_name_plural = 'Daily Area Sales (DAREA)'
    
    def __str__(self):
        return f"DAREA {self.darea} - {self.dareaname}"
    
    def get_total_sales(self):
        """Calculate total sales for all months."""
        return (
            self.arsls1 + self.arsls2 + self.arsls3 + self.arsls4 +
            self.arsls5 + self.arsls6 + self.arsls7 + self.arsls8 +
            self.arsls9 + self.arsls10 + self.arsls11 + self.arsls12
        )
    
    def get_monthly_sales(self):
        """Return a list of monthly sales values."""
        return [
            self.arsls1, self.arsls2, self.arsls3, self.arsls4,
            self.arsls5, self.arsls6, self.arsls7, self.arsls8,
            self.arsls9, self.arsls10, self.arsls11, self.arsls12
        ]


class Dpdc(TimeStampedModel):
    """Post-dated cheques (DPDC table).
    
    Tracks post-dated cheques received from debtors.
    """
    
    STATUS_CHOICES = [
        ('A', 'Active'),
        ('I', 'Inactive'),
        ('P', 'Processed'),
        ('C', 'Cancelled'),
    ]
    
    # Foreign Key to Debtor
    dno = models.ForeignKey(
        Debtor,
        on_delete=models.CASCADE,
        related_name='dpdc_cheques',
        help_text="Debtor account number (DNO)"
    )
    
    # Cheque Information
    date = models.DateField(
        db_index=True,
        help_text="Date of cheque (DATE) - Date 8"
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Cheque value (AMOUNT) - Numeric 10.2"
    )
    status = models.CharField(
        max_length=1,
        choices=STATUS_CHOICES,
        default='A',
        help_text="Status: A=Active, I=Inactive, P=Processed, C=Cancelled"
    )
    
    class Meta:
        ordering = ['date']
        verbose_name = 'Post-Dated Cheque (DPDC)'
        verbose_name_plural = 'Post-Dated Cheques (DPDC)'
        indexes = [
            models.Index(fields=['dno', 'date']),
            models.Index(fields=['status', 'date']),
        ]
    
    def __str__(self):
        return f"DPDC {self.dno.dno} - {self.date} - {self.amount}"
    
    def clean(self):
        """Validate DPDC data."""
        if self.amount <= 0:
            raise ValidationError('Cheque amount must be greater than zero.')
        if self.date < date.today() and self.status == 'A':
            raise ValidationError('Active cheque date cannot be in the past.')
    
    def save(self, *args, **kwargs):
        """Validate before saving."""
        self.full_clean()
        super().save(*args, **kwargs)


class Debtopen(TimeStampedModel):
    """Open item transactions (DEBTOPEN table).
    
    Tracks open item postings for debtors using open item accounting.
    Each transaction is allocated individually to receipts.
    """
    
    TRANSACTION_TYPE_CHOICES = [
        ('IN', 'Invoice'),
        ('CN', 'Credit Note'),
        ('PY', 'Payment'),
        ('JD', 'Journal Debit'),
        ('JC', 'Journal Credit'),
        ('DM', 'Debit Memo'),
        ('CM', 'Credit Memo'),
    ]
    
    AGEING_CHOICES = [
        ('0', 'Current'),
        ('1', '30 Days'),
        ('2', '60 Days'),
        ('3', '90 Days'),
        ('4', '120+ Days'),
    ]
    
    POSTED_CHOICES = [
        ('Y', 'Yes'),
        ('N', 'No'),
    ]
    
    # Foreign Key to Debtor
    dno = models.ForeignKey(
        Debtor,
        on_delete=models.CASCADE,
        related_name='debtopen_items',
        help_text="Debtor number (DNO)"
    )
    
    # Transaction Identification
    dtrano = models.CharField(
        max_length=6,
        help_text="Transaction number (DTRANO) - Character 6"
    )
    type = models.CharField(
        max_length=2,
        choices=TRANSACTION_TYPE_CHOICES,
        help_text="Transaction type (TYPE) - Character 2"
    )
    date = models.DateField(
        db_index=True,
        help_text="Date of transaction (DATE) - Date 8"
    )
    
    # Amounts
    total = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Original transaction total (TOTAL) - Numeric 14.2"
    )
    balancedue = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Balance due on transaction (BALANCEDUE) - Numeric 14.2"
    )
    
    # Status
    ageflag = models.CharField(
        max_length=1,
        choices=AGEING_CHOICES,
        default='0',
        help_text="Aging flag (AGEFLAG) - Character 1"
    )
    posted = models.CharField(
        max_length=10,  # Extended size for compatibility
        default='N',
        help_text="Posted status (POSTED) - Character 10 (Y/N)"
    )
    
    class Meta:
        ordering = ['date', 'dtrano']
        verbose_name = 'Open Item Transaction (DEBTOPEN)'
        verbose_name_plural = 'Open Item Transactions (DEBTOPEN)'
        unique_together = ['dno', 'dtrano']
        indexes = [
            models.Index(fields=['dno', 'date']),
            models.Index(fields=['posted', 'ageflag']),
            models.Index(fields=['date', 'ageflag']),
        ]
    
    def __str__(self):
        return f"DEBTOPEN {self.dno.dno} - {self.dtrano} ({self.date})"
    
    def clean(self):
        """Validate open item transaction data."""
        if self.total < 0:
            raise ValidationError('Transaction total cannot be negative.')
        if self.balancedue < 0:
            raise ValidationError('Balance due cannot be negative.')
        if self.balancedue > self.total:
            raise ValidationError('Balance due cannot exceed original transaction total.')
    
    def save(self, *args, **kwargs):
        """Validate before saving."""
        self.full_clean()
        super().save(*args, **kwargs)
    
    def get_allocated_amount(self):
        """Calculate allocated amount (total - balance due)."""
        return self.total - self.balancedue
    
    def is_fully_allocated(self):
        """Check if fully allocated."""
        return self.balancedue == 0


class DebtorAudit(models.Model):
    """Debtor Audit file (DEBTORAUD table).
    
    Tracks audit of transactions associated with debtor accounts.
    Records all changes and postings for audit trail.
    """
    
    TRANSACTION_TYPE_CHOICES = [
        ('IN', 'Invoice'),
        ('CR', 'Credit Note'),
        ('PA', 'Payment'),
        ('AD', 'Adjustment'),
        ('DM', 'Debit Memo'),
        ('CM', 'Credit Memo'),
    ]
    
    # Foreign Key to Debtor
    dno = models.ForeignKey(
        Debtor,
        on_delete=models.CASCADE,
        related_name='debtoraud_records',
        help_text="Debtor number (DNO)"
    )
    
    # Transaction Information
    dtrano = models.CharField(
        max_length=6,
        help_text="Transaction number (DTRANO) - Character 6"
    )
    type = models.CharField(
        max_length=2,
        choices=TRANSACTION_TYPE_CHOICES,
        help_text="Transaction type (TYPE) - Character 2"
    )
    thistype = models.CharField(
        max_length=2,
        choices=TRANSACTION_TYPE_CHOICES,
        help_text="Current transaction type (THISTYPE) - Character 2"
    )
    thistran = models.CharField(
        max_length=6,
        help_text="Current transaction type identifier (THISTRAN) - Character 6"
    )
    
    # Audit Date and Amount
    date = models.DateField(
        db_index=True,
        help_text="Audit date (DATE) - Date 8"
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Audit amount (AMOUNT) - Numeric 12.2"
    )
    
    class Meta:
        ordering = ['date', 'dtrano']
        verbose_name = 'Debtor Audit (DEBTORAUD)'
        verbose_name_plural = 'Debtor Audits (DEBTORAUD)'
        unique_together = ['dno', 'dtrano', 'date']
        indexes = [
            models.Index(fields=['dno', 'date']),
            models.Index(fields=['date', 'type']),
            models.Index(fields=['type']),
        ]
    
    def __str__(self):
        return f"DEBTORAUD {self.dno.dno} - {self.dtrano} ({self.date})"
    
    def clean(self):
        """Validate debtor audit data."""
        if self.amount < 0:
            raise ValidationError('Amount cannot be negative.')
    
    def save(self, *args, **kwargs):
        """Validate before saving."""
        self.full_clean()
        super().save(*args, **kwargs)


class SalesOrder(TimeStampedModel):
    """Sales order (SORDER equivalent)."""
    
    STATUS_CHOICES = [
        ('O', 'Outstanding'),
        ('P', 'Partially Invoiced'),
        ('I', 'Invoiced'),
        ('C', 'Cancelled'),
        ('H', 'On Hold'),
    ]
    
    DELIVERY_OPTION_CHOICES = [
        ('D', 'Delivery'),
        ('C', 'Collection'),
        ('M', 'Mail'),
        ('X', 'Collect Later'),
    ]
    
    sales_order_number = models.CharField(max_length=20, unique=True, db_index=True)
    
    # Date and time ordered
    order_date = models.DateField()
    order_time = models.TimeField(null=True, blank=True)
    
    # Debtor details
    debtor = models.ForeignKey(
        Debtor,
        on_delete=models.PROTECT,
        related_name='sales_orders'
    )
    customer_name = models.CharField(max_length=40, blank=True)
    
    # Delivery address
    delivery_address_line1 = models.CharField(max_length=20, blank=True)
    delivery_address_line2 = models.CharField(max_length=20, blank=True)
    delivery_address_line3 = models.CharField(max_length=20, blank=True)
    
    # Date and time required
    date_required = models.DateField(null=True, blank=True)
    time_required = models.TimeField(null=True, blank=True)
    
    # Customer reference
    customer_reference = models.CharField(max_length=10, blank=True)
    order_number = models.CharField(max_length=10, blank=True)
    
    # Transaction tracking
    transaction_number = models.PositiveIntegerField(null=True, blank=True)
    
    # Operational details
    delivery_option = models.CharField(max_length=1, choices=DELIVERY_OPTION_CHOICES, default='D')
    salesman_number = models.PositiveIntegerField(null=True, blank=True)
    station_number = models.CharField(max_length=2, blank=True)
    
    # Order value
    value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Status
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='O')
    
    class Meta:
        ordering = ['-order_date', 'sales_order_number']
        indexes = [
            models.Index(fields=['debtor', 'status']),
            models.Index(fields=['order_date']),
            models.Index(fields=['status']),
        ]
        verbose_name = 'Sales Order (SORDER)'
        verbose_name_plural = 'Sales Orders (SORDER)'
    
    def __str__(self):
        return f"Sales Order {self.sales_order_number} - {self.customer_name}"


class SalesOrderLine(TimeStampedModel):
    """Sales order line item (SORDTRN equivalent)."""
    
    sales_order = models.ForeignKey(
        SalesOrder,
        on_delete=models.CASCADE,
        related_name='lines'
    )
    line_number = models.PositiveIntegerField()
    
    # Stock details
    stock_code = models.CharField(max_length=13)
    
    # Quantity and pricing
    quantity = models.DecimalField(max_digits=12, decimal_places=4)
    selling_price = models.DecimalField(max_digits=12, decimal_places=4)
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Comments
    comments = models.CharField(max_length=30, blank=True)
    
    # Calculated fields
    line_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    class Meta:
        ordering = ['line_number']
        unique_together = ['sales_order', 'line_number']
        verbose_name = 'Sales Order Line (SORDTRN)'
        verbose_name_plural = 'Sales Order Lines (SORDTRN)'
        indexes = [
            models.Index(fields=['stock_code']),
        ]
    
    def __str__(self):
        return f"{self.sales_order.sales_order_number} - Line {self.line_number}: {self.stock_code}"


class JobCosting(TimeStampedModel):
    """Job Costing Card (JMAST table) - Track job details and costs."""
    
    JOB_STATUS_CHOICES = [
        ('A', 'Active'),
        ('C', 'Cancelled'),
        ('D', 'Complete'),
    ]
    
    # Primary key
    job_number = models.CharField(
        max_length=6,
        unique=True,
        db_index=True,
        help_text="Job # (6 digits)"
    )
    
    # Job Dates and Times
    job_date = models.DateField(
        db_index=True,
        help_text="Date of Job"
    )
    time_start = models.CharField(
        max_length=5,
        blank=True,
        help_text="Time Job Started (HH:MM format)"
    )
    
    # Customer Information
    customer_name = models.CharField(
        max_length=40,
        help_text="Customer Name"
    )
    
    # Address
    address_line1 = models.CharField(
        max_length=25,
        blank=True,
        help_text="Address Line 1"
    )
    address_line2 = models.CharField(
        max_length=25,
        blank=True,
        help_text="Address Line 2"
    )
    address_line3 = models.CharField(
        max_length=25,
        blank=True,
        help_text="Address Line 3"
    )
    
    # Order and Vehicle Details
    order_number = models.CharField(
        max_length=10,
        blank=True,
        help_text="Order Number"
    )
    vehicle_registration = models.CharField(
        max_length=10,
        blank=True,
        help_text="Vehicle Registration Number"
    )
    vehicle_make_model = models.CharField(
        max_length=15,
        blank=True,
        help_text="Make & Model of Vehicle"
    )
    odometer_reading = models.DecimalField(
        max_digits=7,
        decimal_places=0,
        null=True,
        blank=True,
        help_text="Odometer Reading (Kms)"
    )
    
    # Contact Details
    telephone = models.CharField(
        max_length=25,
        blank=True,
        help_text="Telephone Number"
    )
    contact_person = models.CharField(
        max_length=20,
        blank=True,
        help_text="Contact person"
    )
    
    # Job Status
    status = models.CharField(
        max_length=1,
        choices=JOB_STATUS_CHOICES,
        default='A',
        help_text="Job status: A=Active, C=Cancelled, D=Complete"
    )
    
    # Job Values
    total_value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Total value of job"
    )
    
    # Salesforce Information
    salesman_number = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MaxValueValidator(99)],
        help_text="Salesperson number (2 digits)"
    )
    station_number = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MaxValueValidator(99)],
        help_text="Station/Till number (2 digits)"
    )
    
    # Debtor Reference
    debtor = models.ForeignKey(
        Debtor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='job_costings',
        help_text="Debtor account number"
    )
    
    # Completion Information
    completion_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date completed"
    )
    time_completed = models.CharField(
        max_length=5,
        blank=True,
        help_text="Time completed (HH:MM format)"
    )
    amount_charged = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Amount charged out"
    )
    
    # Transaction Information
    transaction_number = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MaxValueValidator(999999)],
        help_text="Transaction number (6 digits)"
    )
    transaction_type = models.CharField(
        max_length=1,
        blank=True,
        help_text="Transaction type"
    )
    
    # Operational Details
    station_completion = models.CharField(
        max_length=2,
        blank=True,
        help_text="Station number (Character, 2 digits)"
    )
    operator_number = models.CharField(
        max_length=10,
        blank=True,
        help_text="Operator number"
    )
    
    # Comments
    comment_line1 = models.CharField(
        max_length=30,
        blank=True,
        help_text="Comment line 1"
    )
    comment_line2 = models.CharField(
        max_length=30,
        blank=True,
        help_text="Comment line 2"
    )
    comment_line3 = models.CharField(
        max_length=30,
        blank=True,
        help_text="Comment line 3"
    )
    comment_line4 = models.CharField(
        max_length=30,
        blank=True,
        help_text="Comment line 4"
    )
    
    class Meta:
        ordering = ['-job_date', '-job_number']
        verbose_name = 'Job Costing (JMAST)'
        verbose_name_plural = 'Job Costing Records (JMAST)'
        indexes = [
            models.Index(fields=['job_date']),
            models.Index(fields=['debtor', 'job_date']),
            models.Index(fields=['status', 'job_date']),
            models.Index(fields=['vehicle_registration']),
        ]
    
    def __str__(self):
        return f"Job {self.job_number} - {self.customer_name} ({self.job_date})"
    
    def clean(self):
        """Validate job costing data."""
        if self.total_value < 0:
            raise ValidationError('Total value cannot be negative.')
        if self.amount_charged < 0:
            raise ValidationError('Amount charged cannot be negative.')
        if self.amount_charged > self.total_value and self.total_value > 0:
            raise ValidationError('Amount charged cannot exceed total job value.')
        if self.completion_date and self.job_date > self.completion_date:
            raise ValidationError('Completion date cannot be before job date.')
        if self.status == 'D' and not self.completion_date:
            raise ValidationError('Completion date is required when job status is Complete.')
    
    def mark_complete(self):
        """Mark job as complete."""
        self.status = 'D'
        if not self.completion_date:
            self.completion_date = date.today()
        self.save()
    
    def cancel_job(self):
        """Cancel job."""
        self.status = 'C'
        self.save()


class JobCostingTransaction(TimeStampedModel):
    """Job Costing Transaction Details (JTRAN table) - Track items/costs on a job."""
    
    job_costing = models.ForeignKey(
        JobCosting,
        on_delete=models.CASCADE,
        related_name='transactions',
        help_text="Job # (6 digits)"
    )
    
    # Stock/Item Details
    code = models.CharField(
        max_length=13,
        help_text="Stock Code"
    )
    
    # Quantity and Pricing
    quantity = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        help_text="Quantity of item"
    )
    selling_price = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        help_text="Selling price per unit"
    )
    discount = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Discount percentage"
    )
    
    # Cost Information
    cost_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Cost price per unit"
    )
    
    # Classification
    department = models.CharField(
        max_length=3,
        blank=True,
        help_text="Department # (3 characters)"
    )
    tax_code = models.CharField(
        max_length=1,
        blank=True,
        help_text="Tax code"
    )
    
    # Comments
    comments = models.CharField(
        max_length=30,
        blank=True,
        help_text="Comment on transaction"
    )
    
    # Transaction Date
    transaction_date = models.DateField(
        db_index=True,
        help_text="Date of transaction"
    )
    
    class Meta:
        ordering = ['transaction_date', 'created_at']
        verbose_name = 'Job Costing Transaction (JTRAN)'
        verbose_name_plural = 'Job Costing Transactions (JTRAN)'
        indexes = [
            models.Index(fields=['job_costing', 'transaction_date']),
            models.Index(fields=['code']),
            models.Index(fields=['department']),
        ]
    
    def __str__(self):
        return f"JTRAN - Job {self.job_costing.job_number} - {self.code} ({self.transaction_date})"
    
    def clean(self):
        """Validate job costing transaction data."""
        if self.quantity < 0:
            raise ValidationError('Quantity cannot be negative.')
        if self.selling_price < 0:
            raise ValidationError('Selling price cannot be negative.')
        if self.cost_price < 0:
            raise ValidationError('Cost price cannot be negative.')
        if not 0 <= self.discount <= 100:
            raise ValidationError('Discount must be between 0 and 100.')
        if self.transaction_date > date.today():
            raise ValidationError('Transaction date cannot be in the future.')
    
    def get_line_total(self):
        """Calculate line total (quantity * selling_price * (1 - discount/100))."""
        discount_factor = Decimal(1) - (self.discount / Decimal(100))
        return self.quantity * self.selling_price * discount_factor
    
    def get_line_cost(self):
        """Calculate line cost (quantity * cost_price)."""
        return self.quantity * self.cost_price
    
    def get_line_profit(self):
        """Calculate line profit (line_total - line_cost)."""
        return self.get_line_total() - self.get_line_cost()


class JobPerson(TimeStampedModel):
    """Job Operator/Person (JPERSON table) - Operators who work on jobs."""
    
    operator_number = models.CharField(
        max_length=10,
        unique=True,
        db_index=True,
        primary_key=False,
        help_text="Operator number"
    )
    operator_name = models.CharField(
        max_length=20,
        help_text="Operator name"
    )
    
    class Meta:
        ordering = ['operator_number']
        verbose_name = 'Job Operator (JPERSON)'
        verbose_name_plural = 'Job Operators (JPERSON)'
        indexes = [
            models.Index(fields=['operator_number']),
            models.Index(fields=['operator_name']),
        ]
    
    def __str__(self):
        return f"{self.operator_number} - {self.operator_name}"


class JobPrinting(TimeStampedModel):
    """Job Printing Configuration (JPRINT table) - Station assignments for job document printing."""
    
    station = models.CharField(
        max_length=2,
        unique=True,
        db_index=True,
        primary_key=False,
        help_text="Station number"
    )
    
    # Printer assignments
    job_cards_station = models.CharField(
        max_length=1,
        blank=True,
        help_text="Station number for job cards printing"
    )
    job_invoices_station = models.CharField(
        max_length=1,
        blank=True,
        help_text="Station number for job invoices printing"
    )
    job_reports_station = models.CharField(
        max_length=1,
        blank=True,
        help_text="Station number for job reports printing"
    )
    
    class Meta:
        ordering = ['station']
        verbose_name = 'Job Printing Configuration (JPRINT)'
        verbose_name_plural = 'Job Printing Configurations (JPRINT)'
        indexes = [
            models.Index(fields=['station']),
        ]
    
    def __str__(self):
        return f"JPRINT - Station {self.station}"