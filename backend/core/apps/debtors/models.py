"""
Debtors (Customers) models.
Based on the Debtors.pdf documentation.
"""
from django.db import models
from django.db.models import Q
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import date
from django.utils import timezone
from apps.settings.models import TimeStampedModel, SalesArea, PostingStatusMixin



class Debtor(TimeStampedModel):
    """
    Debtor/Customer Master Record (DMAST table)
    
    Stores all customer account information, balances, and settings.
    Uses modern field names with legacy DBF column mappings for seamless import.
    """
    
    ACCOUNT_TYPE_CHOICES = [
        ('', 'Balance Brought Forward'),  # Legacy default - monthly balance aging
        ('O', 'Open Item'),               # Item-by-item transaction allocation
        ('C', 'Cash Customer'),           # Cash only, no credit
        ('N', 'Normal Credit'),           # Standard credit terms
        ('B', 'COD'),                     # Cash on delivery
    ]
    
    BLOCK_FLAG_CHOICES = [
        ('0', 'Active'),          # Normal trading account
        ('1', 'Credit Hold'),     # Over limit or payment issues
        ('2', 'Closed'),          # Account closed
        ('3', 'No Delivery'),     # Collection only
        ('Y', 'Blocked'),         # Legacy: general block
        ('N', 'Active Legacy'),   # Legacy: active
    ]
    
    INTEREST_FLAG_CHOICES = [
        ('Y', 'Yes - Charge Interest'),
        ('N', 'No - Do Not Charge'),
    ]
    
    PRICE_LEVEL_CHOICES = [
        (1, 'Retail'),
        (2, 'Trade'),
        (3, 'Wholesale'),
    ]
    
    # ==========================================
    # PRIMARY IDENTIFICATION
    # ==========================================
    
    # Primary key - legacy field name
    dno = models.IntegerField(
        unique=True,
        db_index=True,
        help_text="Debtor Account Number (DNO) - Numeric 5"
    )
    
    # ==========================================
    # BASIC INFORMATION
    # ==========================================
    
    # Basic Information
    dname = models.CharField(
        max_length=100,
        help_text="Customer/Debtor Name (DNAME) - Character 40"
    )
    
    dsname = models.CharField(
        max_length=20,
        blank=True,
        db_index=True,
        help_text="Short/Sort Name (DSNAME) - Character 5"
    )
    
    # ==========================================
    # CONTACT INFORMATION
    # ==========================================
    
    # Contact Information
    dcontact = models.CharField(
        max_length=50,
        blank=True,
        help_text="Contact Person (DCONTACT) - Character 20"
    )
    
    dtel = models.CharField(
        max_length=20,
        blank=True,
        help_text="Telephone Number (DTEL) - Character 15"
    )
    
    dtel2 = models.CharField(
        max_length=20,
        blank=True,
        help_text="Alternative Phone (TEL2) - Character 15"
    )
    
    dfax = models.CharField(
        max_length=20,
        blank=True,
        help_text="Fax Number (DFAX) - Character 15"
    )
    
    email = models.EmailField(
        blank=True,
        db_column='email',
        help_text="Email Address (EMAIL) - Character 50"
    )
    
    # ==========================================
    # POSTAL ADDRESS
    # ==========================================
    
    address_line1 = models.CharField(
        max_length=100,
        blank=True,
        db_column='dadd1',
        help_text="Postal Address Line 1 (DADD1) - Character 25"
    )
    
    address_line2 = models.CharField(
        max_length=100,
        blank=True,
        db_column='dadd2',
        help_text="Postal Address Line 2 (DADD2) - Character 25"
    )
    
    address_line3 = models.CharField(
        max_length=100,
        blank=True,
        db_column='dadd3',
        help_text="Postal Address Line 3 (DADD3) - Character 25"
    )
    
    postal_code = models.CharField(
        max_length=10,
        blank=True,
        db_column='dpcode',
        help_text="Postal Code (DPCODE) - Character 4"
    )
    
    # ==========================================
    # DELIVERY ADDRESS
    # ==========================================
    
    delivery_address1 = models.CharField(
        max_length=100,
        blank=True,
        db_column='delad1',
        help_text="Delivery Address Line 1 (DELAD1) - Character 25"
    )
    
    delivery_address2 = models.CharField(
        max_length=100,
        blank=True,
        db_column='delad2',
        help_text="Delivery Address Line 2 (DELAD2) - Character 25"
    )
    
    delivery_address3 = models.CharField(
        max_length=100,
        blank=True,
        db_column='delad3',
        help_text="Delivery Address Line 3 (DELAD3) - Character 25"
    )
    
    delivery_address4 = models.CharField(
        max_length=100,
        blank=True,
        db_column='delad4',
        help_text="Delivery Address Line 4 (DELAD4) - Character 25"
    )
    
    # ==========================================
    # BUSINESS IDENTIFIERS
    # ==========================================
    
    # Business Identifiers
    dtaxno = models.CharField(
        max_length=30,
        blank=True,
        help_text="Tax/Company Registration Number (DTAXNO) - Character 20"
    )
    
    vatref = models.CharField(
        max_length=20,
        blank=True,
        help_text="VAT Registration Number (VATREF) - Character 10"
    )
    
    # ==========================================
    # SALES AREA & SALESMAN
    # ==========================================
    
    # Sales Area
    darea = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(99)],
        help_text="Salesman/Area Number (DAREA) - Numeric 2"
    )
    
    # ==========================================
    # ACCOUNT CONFIGURATION
    # ==========================================
    
    # Account Configuration
    acctype = models.CharField(
        max_length=1,
        choices=ACCOUNT_TYPE_CHOICES,
        default='',
        help_text="Account Type (ACCTYPE) - Blank=Balance Forward, O=Open Item, C=Cash, N=Normal, B=COD",
        blank=True
    )
    
    price = models.IntegerField(
        default=1,
        choices=PRICE_LEVEL_CHOICES,
        validators=[MinValueValidator(1), MaxValueValidator(3)],
        help_text="Price Level (PRICE) - Numeric 1 (1=Retail, 2=Trade, 3=Wholesale)"
    )
    
    terms = models.IntegerField(
        default=30,
        validators=[MinValueValidator(0), MaxValueValidator(999)],
        help_text="Payment Terms in Days (TERMS) - Numeric 3"
    )
    
    # ==========================================
    # DISCOUNT SETTINGS
    # ==========================================
    
    ddiscper = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('100'))],
        help_text="Standard Discount % (DDISCPER) - Numeric 10.2"
    )
    
    pdisc = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('100'))],
        db_column='pdisc',
        help_text="Prompt Payment Discount % (PDISC) - Numeric 6.2"
    )
    
    discount_printable = models.CharField(
        max_length=1,
        choices=[('Y', 'Yes'), ('N', 'No')],
        default='N',
        db_column='discprn',
        help_text="Print Discount on Invoice (DISCPRN) - Y/N"
    )
    
    # ==========================================
    # CREDIT MANAGEMENT
    # ==========================================
    
    # Credit Management
    dclimit = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0'))],
        help_text="Credit Limit (DCLIMIT) - Numeric 12.2"
    )
    
    # ==========================================
    # ACCOUNT STATUS FLAGS
    # ==========================================
    
    # Account Status Flags
    blockflag = models.CharField(
        max_length=1,
        choices=BLOCK_FLAG_CHOICES,
        default='0',
        help_text="Block Account (BLOCKFLAG) - 0=Active, 1=Credit Hold, 2=Closed, 3=No Delivery"
    )
    
    dintflag = models.CharField(
        max_length=1,
        choices=INTEREST_FLAG_CHOICES,
        default='N',
        help_text="Charge Interest (DINTFLAG) - Y/N"
    )
    
    dposbal = models.CharField(
        max_length=1,
        choices=[('Y', 'Yes'), ('N', 'No')],
        default='Y',
        help_text="Print Account Balance on POS (DPOSBAL) - Y/N"
    )
    
    # ==========================================
    # AGING BALANCES (All in ZAR)
    # ==========================================
    
    # Aging Balances (All in ZAR)
    dbalbfwd = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Balance Brought Forward (DBALBFWD) - Numeric 10.2"
    )
    
    dcrnt = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Current Month Balance (DCRNT) - Numeric 10.2"
    )
    
    d30 = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="30 Days Balance (D30) - Numeric 10.2"
    )
    
    d60 = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="60 Days Balance (D60) - Numeric 10.2"
    )
    
    d90 = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="90 Days Balance (D90) - Numeric 10.2"
    )
    
    d120 = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="120 Days Balance (D120) - Numeric 10.2"
    )
    
    d150 = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="150 Days Balance (D150) - Numeric 10.2"
    )
    
    d180 = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="180+ Days Balance (D180) - Numeric 10.2"
    )
    
    # ==========================================
    # SALES & PROFIT STATISTICS
    # ==========================================
    
    # Sales & Profit Statistics
    dsalesm = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Sales Total for Current Month (DSALESM) - Numeric 10.2"
    )
    
    dsalesy = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Sales Total for Year (DSALESY) - Numeric 10.2"
    )
    
    dprofitm = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Profit for Current Month (DPROFITM) - Numeric 10.2"
    )
    
    dprofity = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Profit for Year (DPROFITY) - Numeric 10.2"
    )
    
    # ==========================================
    # PAYMENT TRACKING
    # ==========================================
    
    # Payment Tracking
    damtlpd = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Amount of Last Payment (DAMTLPD) - Numeric 10.2"
    )
    
    ddatlpd = models.DateField(
        null=True,
        blank=True,
        help_text="Date of Last Payment (DDATLPD) - Date 8"
    )
    
    # ==========================================
    # METADATA
    # ==========================================
    
    # Metadata
    dateopened = models.DateField(
        null=True,
        blank=True,
        help_text="Date Account Opened (DATEOPENED) - Date 8"
    )
    
    notes = models.TextField(
        blank=True,
        db_column='notes',
        help_text="Additional Notes (NOTES) - Memo field"
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text="Active status (for soft delete)"
    )
    
    class Meta:
        db_table = 'dmast'
        ordering = ['dno']
        verbose_name = 'Debtor'
        verbose_name_plural = 'Debtors'
        indexes = [
            models.Index(fields=['dno'], name='idx_dno'),
            models.Index(fields=['dsname'], name='idx_dsname'),
            models.Index(fields=['dname'], name='idx_dname'),
            models.Index(fields=['darea'], name='idx_darea'),
            models.Index(fields=['blockflag'], name='idx_blockflag'),
            models.Index(fields=['-dcrnt'], name='idx_balance_curr'),
            models.Index(fields=['is_active'], name='idx_is_active'),
        ]
    
    def __str__(self):
        return f"{self.dno} - {self.dname}"
    
    # ==========================================
    # VALIDATION
    # ==========================================
    
    def clean(self):
        """Validate debtor data according to business rules."""
        errors = {}
        
        # Credit limit validation
        if self.dclimit < 0:
            errors['dclimit'] = 'Credit limit cannot be negative.'
        
        # Discount validation
        if not 0 <= self.ddiscper <= 100:
            errors['ddiscper'] = 'Discount percentage must be between 0 and 100.'
        
        if not 0 <= self.pdisc <= 100:
            errors['pdisc'] = 'Prompt discount must be between 0 and 100.'
        
        # Price level validation
        if not 1 <= self.price <= 3:
            errors['price'] = 'Price level must be between 1 and 3.'
        
        # Payment terms validation
        if self.terms < 0:
            errors['terms'] = 'Payment terms cannot be negative.'
        
        # Cash customers should not have credit limit
        if self.acctype == 'C' and self.dclimit > 0:
            errors['dclimit'] = 'Cash customers should not have a credit limit.'
        
        # VAT number validation (South African format: 10 digits)
        if self.vatref and len(self.vatref.replace(' ', '')) not in [0, 10]:
            errors['vatref'] = 'VAT number should be 10 digits (South African format).'
        
        if errors:
            raise ValidationError(errors)
    
    def save(self, *args, **kwargs):
        """Validate and save."""
        self.full_clean()
        super().save(*args, **kwargs)
    
    # ==========================================
    # Computed Properties
    
    @property
    def total_balance(self):
        """Calculate total outstanding balance across all aging buckets."""
        return (
            self.dbalbfwd +
            self.dcrnt +
            self.d30 +
            self.d60 +
            self.d90 +
            self.d120 +
            self.d150 +
            self.d180
        )
    
    @property
    def overdue_balance(self):
        """Get balance over 30 days old (excluding current)."""
        return (
            self.d30 +
            self.d60 +
            self.d90 +
            self.d120 +
            self.d150 +
            self.d180
        )
    
    @property
    def is_over_credit_limit(self):
        """Check if customer has exceeded credit limit."""
        return self.total_balance > self.dclimit
    
    @property
    def credit_available(self):
        """Calculate available credit."""
        available = self.dclimit - self.total_balance
        return max(Decimal('0.00'), available)
    
    @property
    def is_blocked(self):
        """Check if account is blocked (any block status)."""
        return self.blockflag in ['1', '2', '3', 'Y']
    
    @property
    def is_trading(self):
        """Check if account is actively trading (not closed)."""
        return self.blockflag not in ['2'] and self.is_active
    
    @property
    def charges_interest(self):
        """Check if interest should be charged."""
        return self.dintflag == 'Y'
    
    # ==========================================
    # BUSINESS METHODS
    # ==========================================
    
    def get_aged_balance(self, days):
        """
        Get balance for specific age bucket.
        
        Args:
            days (int): Age bucket (0, 30, 60, 90, 120, 150, 180)
        
        Returns:
            Decimal: Balance for that age bucket
        """
        age_map = {
            0: self.dcrnt,
            30: self.d30,
            60: self.d60,
            90: self.d90,
            120: self.d120,
            150: self.d150,
            180: self.d180,
        }
        return age_map.get(days, Decimal('0.00'))
    
    def set_blocked(self, blocked=True, reason='1'):
        """
        Block or unblock account.
        
        Args:
            blocked (bool): True to block, False to unblock
            reason (str): Block reason code (1=Credit Hold, 2=Closed, 3=No Delivery)
        """
        if blocked:
            self.blockflag = reason if reason in ['1', '2', '3'] else '1'
        else:
            self.blockflag = '0'
        self.save(update_fields=['blockflag', 'updated_at'])
    
    def set_interest_flag(self, charge_interest=True):
        """
        Set whether to charge interest on overdue balances.
        
        Args:
            charge_interest (bool): True to charge interest, False otherwise
        """
        self.dintflag = 'Y' if charge_interest else 'N'
        self.save(update_fields=['dintflag', 'updated_at'])
    
    def update_last_payment(self, amount, payment_date=None):
        """
        Update last payment information.
        
        Args:
            amount (Decimal): Payment amount
            payment_date (date): Payment date (defaults to today)
        """
        self.damtlpd = amount
        self.ddatlpd = payment_date or date.today()
        self.save(update_fields=['damtlpd', 'ddatlpd', 'updated_at'])
    
    def get_aging_summary(self):
        """
        Get aging summary as a dictionary.
        
        Returns:
            dict: Aging buckets with labels and amounts
        """
        return {
            'current': {'label': 'Current', 'amount': self.dcrnt},
            '30_days': {'label': '30 Days', 'amount': self.d30},
            '60_days': {'label': '60 Days', 'amount': self.d60},
            '90_days': {'label': '90 Days', 'amount': self.d90},
            '120_days': {'label': '120 Days', 'amount': self.d120},
            '150_days': {'label': '150 Days', 'amount': self.d150},
            '180_days': {'label': '180+ Days', 'amount': self.d180},
            'total': {'label': 'Total Outstanding', 'amount': self.total_balance},
        }
    
    def check_credit_approval(self, amount):
        """
        Check if a transaction amount can be approved within credit limit.
        
        Args:
            amount (Decimal): Transaction amount
        
        Returns:
            tuple: (approved: bool, reason: str)
        """
        # Cash customers always approved
        if self.acctype == 'C':
            return (True, 'Cash customer')
        
        # Blocked accounts denied
        if self.is_blocked:
            return (False, f'Account blocked: {self.get_block_flag_display()}')
        
        # Check credit limit
        new_balance = self.total_balance + amount
        if new_balance > self.dclimit:
            return (False, f'Would exceed credit limit by R{new_balance - self.dclimit:.2f}')
        
        return (True, 'Approved')






class DebtorTransactionQuerySet(models.QuerySet):
    """Custom QuerySet for DebtorTransaction with business logic helpers."""
    
    def invoices(self):
        """Filter to invoice and cash sale transactions (revenue-generating)."""
        return self.filter(transaction_type__in=['IN', 'CS'])
    
    def payments(self):
        """Filter to payment and receipt transactions (inbound money)."""
        return self.filter(transaction_type__in=['PM', 'RCP'])
    
    def credits(self):
        """Filter to credit notes, returns, and refunds (reductions)."""
        return self.filter(transaction_type__in=['CN', 'CR', 'RF'])
    
    def journal_entries(self):
        """Filter to manual journal entries."""
        return self.filter(transaction_type__in=['JD', 'JC'])
    
    def interest_charges(self):
        """Filter to interest charge transactions."""
        return self.filter(transaction_type__in=['INT'])
    
    def by_period(self, start_date, end_date):
        """Filter transactions within a date range."""
        return self.filter(transaction_date__range=[start_date, end_date])
    
    def outstanding(self):
        """Filter to outstanding (unallocated) transactions."""
        return self.filter(is_allocated=False)
    
    def allocated(self):
        """Filter to fully allocated transactions."""
        return self.filter(is_allocated=True)
    
    def by_source(self, source):
        """Filter transactions by source type."""
        return self.filter(source_type=source)
    
    def aging_analysis(self, as_of_date=None):
        """
        Get aging analysis of outstanding transactions.
        Returns aggregated amounts by age bucket.
        """
        from django.db.models import Sum, Q
        from datetime import timedelta
        
        as_of = as_of_date or date.today()
        
        outstanding = self.filter(is_allocated=False)
        
        return outstanding.aggregate(
            current=Sum(
                'total_amount',
                filter=Q(transaction_date__gte=as_of - timedelta(days=30))
            ),
            days_30_60=Sum(
                'total_amount',
                filter=Q(transaction_date__gte=as_of - timedelta(days=60))
                & Q(transaction_date__lt=as_of - timedelta(days=30))
            ),
            days_60_90=Sum(
                'total_amount',
                filter=Q(transaction_date__gte=as_of - timedelta(days=90))
                & Q(transaction_date__lt=as_of - timedelta(days=60))
            ),
            days_90_plus=Sum(
                'total_amount',
                filter=Q(transaction_date__lt=as_of - timedelta(days=90))
            ),
        )


class DebtorTransactionManager(models.Manager):
    """Custom manager for DebtorTransaction."""
    
    def get_queryset(self):
        """Return custom QuerySet."""
        return DebtorTransactionQuerySet(self.model, using=self._db)
    
    # Proxy methods for convenience
    def invoices(self):
        return self.get_queryset().invoices()
    
    def payments(self):
        return self.get_queryset().payments()
    
    def credits(self):
        return self.get_queryset().credits()
    
    def journal_entries(self):
        return self.get_queryset().journal_entries()
    
    def interest_charges(self):
        return self.get_queryset().interest_charges()
    
    def by_period(self, start_date, end_date):
        return self.get_queryset().by_period(start_date, end_date)
    
    def outstanding(self):
        return self.get_queryset().outstanding()
    
    def allocated(self):
        return self.get_queryset().allocated()
    
    def by_source(self, source):
        return self.get_queryset().by_source(source)
    
    def aging_analysis(self, as_of_date=None):
        return self.get_queryset().aging_analysis(as_of_date)


class DebtorTransaction(TimeStampedModel):
    """
    Debtor Transactions (DEBTRAN table)
    
    All postings to debtor accounts including invoices, cash sales,
    credit notes, receipts, and interest charges.
    """
    
    TRANSACTION_TYPE_CHOICES = [
        ('IN', 'Invoice'),
        ('CN', 'Credit Note'),
        ('CS', 'Cash Sale'),
        ('CR', 'Cash Return'),
        ('PM', 'Payment'),
        ('RCP', 'Receipt'),
        ('INT', 'Interest Charge'),
        ('JD', 'Journal Debit'),
        ('JC', 'Journal Credit'),
        ('RF', 'Refund'),
    ]
    
    VAT_STATUS_CHOICES = [
        ('S', 'Standard Rated (15%)'),
        ('E', 'Exempt'),
        ('Z', 'Zero Rated'),
    ]
    
    # Custom manager
    objects = DebtorTransactionManager()
    
    # ==========================================
    # FOREIGN KEYS
    # ==========================================
    
    debtor = models.ForeignKey(
        Debtor,
        on_delete=models.PROTECT,
        related_name='transactions',
        db_column='dno',
        help_text="Debtor Account Number (DNO)"
    )
    
    # ==========================================
    # TRANSACTION IDENTIFICATION
    # ==========================================
    
    transaction_number = models.CharField(
        max_length=6,
        db_index=True,
        db_column='dtrano',
        help_text="Transaction Number (DTRANO) - Numeric 6"
    )
    
    transaction_type = models.CharField(
        max_length=3,
        choices=TRANSACTION_TYPE_CHOICES,
        db_column='dtype',
        help_text="Transaction Type (DTYPE) - Character 3"
    )
    
    transaction_date = models.DateField(
        db_index=True,
        db_column='dtdate',
        help_text="Transaction Date (DTDATE) - Date 8"
    )
    
    transaction_time = models.TimeField(
        null=True,
        blank=True,
        db_column='time',
        help_text="Transaction Time (TIME) - Character 8 (HH:MM:SS)"
    )
    
    # ==========================================
    # FINANCIAL AMOUNTS
    # ==========================================
    
    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        db_column='dtsub',
        help_text="Subtotal Excl. VAT (DTSUB) - Numeric 12.2"
    )
    
    vat_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        db_column='dtgst',
        help_text="VAT Amount (DTGST) - Numeric 12.2"
    )
    
    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        db_column='dttot',
        help_text="Transaction Total Incl. VAT (DTTOT) - Numeric 12.2"
    )
    
    vat_status = models.CharField(
        max_length=1,
        choices=VAT_STATUS_CHOICES,
        default='S',
        db_column='dtaxstat',
        help_text="VAT Status (DTAXSTAT) - Character 1"
    )
    
    # ==========================================
    # SOURCE & REFERENCES
    # ==========================================
    
    source_station = models.PositiveIntegerField(
        default=0,
        validators=[MaxValueValidator(99)],
        db_column='source',
        help_text="Station/Till Number (SOURCE) - Numeric 2"
    )
    
    order_number = models.CharField(
        max_length=10,
        blank=True,
        db_column='ordno',
        help_text="Order Number (ORDNO) - Character 10"
    )
    
    customer_reference = models.CharField(
        max_length=10,
        blank=True,
        db_column='custref',
        help_text="Customer Reference (CUSTREF) - Character 10"
    )
    
    vat_reference = models.CharField(
        max_length=10,
        blank=True,
        db_column='vatref',
        help_text="VAT Reference (VATREF) - Character 10"
    )
    
    station = models.CharField(
        max_length=5,
        blank=True,
        db_column='station',
        help_text="Station Code (STATION) - Character 2"
    )
    
    # ==========================================
    # DELIVERY/DESCRIPTION DETAILS
    # ==========================================
    
    description_line1 = models.CharField(
        max_length=100,
        blank=True,
        db_column='del1',
        help_text="Delivery/Description Line 1 (DEL1) - Character 25"
    )
    
    description_line2 = models.CharField(
        max_length=100,
        blank=True,
        db_column='del2',
        help_text="Delivery/Description Line 2 (DEL2) - Character 25"
    )
    
    description_line3 = models.CharField(
        max_length=100,
        blank=True,
        db_column='del3',
        help_text="Delivery/Description Line 3 (DEL3) - Character 25"
    )
    
    description_line4 = models.CharField(
        max_length=100,
        blank=True,
        db_column='del4',
        help_text="Delivery/Description Line 4 (DEL4) - Character 25"
    )
    
    # ==========================================
    # SOURCE TRACKING
    # ==========================================
    
    SOURCE_CHOICES = [
        ('POS', 'Point of Sale'),
        ('INVOICE', 'Invoice Entry'),
        ('IMPORT', 'Bulk Import'),
        ('MANUAL', 'Manual Entry'),
    ]
    
    source_type = models.CharField(
        max_length=20,
        choices=SOURCE_CHOICES,
        default='POS',
        help_text="Source of transaction (POS, Invoice, Import, Manual)"
    )
    
    source_reference = models.CharField(
        max_length=100,
        blank=True,
        help_text="Link to original record (invoice ID, import batch ID, etc)"
    )
    
    # ==========================================
    # ALLOCATION STATUS
    # ==========================================
    
    is_allocated = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Whether transaction has been fully allocated/paid"
    )
    
    # ==========================================
    # STATUS
    # ==========================================
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('posted', 'Posted'),
        ('void', 'Void'),
        ('reversed', 'Reversed'),
    ]
    
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='posted',
        help_text="Transaction status"
    )
    
    created_by = models.CharField(
        max_length=50,
        blank=True,
        help_text="User who created transaction"
    )
    
    class Meta:
        db_table = 'debtran'
        ordering = ['-transaction_date', '-transaction_number']
        verbose_name = 'Debtor Transaction'
        verbose_name_plural = 'Debtor Transactions'
        unique_together = [['debtor', 'transaction_number', 'transaction_date']]
        indexes = [
            models.Index(fields=['debtor', '-transaction_date'], name='idx_deb_tran_date'),
            models.Index(fields=['transaction_type', '-transaction_date'], name='idx_tran_type_date'),
            models.Index(fields=['transaction_number'], name='idx_dtrano'),
            models.Index(fields=['status'], name='idx_tran_status'),
            models.Index(fields=['source_type'], name='idx_tran_source_type'),
            models.Index(fields=['is_allocated'], name='idx_tran_allocated'),
            models.Index(fields=['debtor', 'is_allocated', '-transaction_date'], name='idx_deb_alloc_date'),
        ]
    
    def __str__(self):
        return f"{self.transaction_number} - {self.debtor.name} ({self.transaction_date})"
    
    def clean(self):
        """Validate transaction data."""
        errors = {}
        
        # Amount validations
        if self.subtotal < 0 and self.transaction_type not in ['CN', 'CR', 'RF']:
            errors['subtotal'] = 'Subtotal cannot be negative for this transaction type.'
        
        if self.vat_amount < 0:
            errors['vat_amount'] = 'VAT amount cannot be negative.'
        
        # Total should equal subtotal + VAT
        expected_total = self.subtotal + self.vat_amount
        if abs(self.total_amount - expected_total) > Decimal('0.01'):
            errors['total_amount'] = f'Total should equal subtotal + VAT (expected {expected_total})'
        
        # Credit notes and returns should have negative amounts
        if self.transaction_type in ['CN', 'CR', 'RF'] and self.total_amount > 0:
            errors['total_amount'] = 'Credit transactions should have negative amounts'
        
        if errors:
            raise ValidationError(errors)
    
    def save(self, *args, **kwargs):
        """Validate and save."""
        self.full_clean()
        super().save(*args, **kwargs)
    
    @property
    def is_debit(self):
        """Check if transaction increases customer balance (debit)."""
        return self.transaction_type in ['IN', 'CS', 'JD', 'INT']
    
    @property
    def is_credit(self):
        """Check if transaction decreases customer balance (credit)."""
        return self.transaction_type in ['CN', 'CR', 'PM', 'RCP', 'JC', 'RF']
    
    @property
    def signed_amount(self):
        """Get amount with correct sign (positive for debits, negative for credits)."""
        return self.total_amount if self.is_debit else -abs(self.total_amount)


class DebtorOpenItem(TimeStampedModel):
    """
    Open Item Transactions (DEBTOPEN table)
    
    Tracks individual transactions for debtors using open item accounting.
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
    
    AGING_CHOICES = [
        ('0', 'Current'),
        ('1', '30 Days'),
        ('2', '60 Days'),
        ('3', '90 Days'),
        ('4', '120+ Days'),
    ]
    
    # ==========================================
    # FOREIGN KEYS & IDENTIFICATION
    # ==========================================
    
    debtor = models.ForeignKey(
        Debtor,
        on_delete=models.CASCADE,
        related_name='open_items',
        db_column='dno',
        help_text="Debtor Number (DNO)"
    )
    
    transaction_number = models.CharField(
        max_length=6,
        db_column='dtrano',
        help_text="Transaction Number (DTRANO) - Character 6"
    )
    
    transaction_type = models.CharField(
        max_length=2,
        choices=TRANSACTION_TYPE_CHOICES,
        db_column='type',
        help_text="Transaction Type (TYPE) - Character 2"
    )
    
    transaction_date = models.DateField(
        db_index=True,
        db_column='date',
        help_text="Transaction Date (DATE) - Date 8"
    )
    
    # ==========================================
    # FINANCIAL AMOUNTS
    # ==========================================
    
    original_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))],
        db_column='total',
        help_text="Original Transaction Total (TOTAL) - Numeric 14.2"
    )
    
    balance_due = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))],
        db_column='balancedue',
        help_text="Current Balance Due (BALANCEDUE) - Numeric 14.2"
    )
    
    # ==========================================
    # STATUS & AGING
    # ==========================================
    
    age_flag = models.CharField(
        max_length=1,
        choices=AGING_CHOICES,
        default='0',
        db_column='ageflag',
        help_text="Aging Flag (AGEFLAG) - 0=Current, 1=30, 2=60, 3=90, 4=120+"
    )
    
    posted = models.CharField(
        max_length=10,
        default='Y',
        db_column='posted',
        help_text="Posted Status (POSTED) - Y/N"
    )
    
    due_date = models.DateField(
        null=True,
        blank=True,
        help_text="Payment due date"
    )
    
    fully_paid = models.BooleanField(
        default=False,
        help_text="Fully allocated/paid flag"
    )
    
    class Meta:
        db_table = 'debtopen'
        ordering = ['transaction_date', 'transaction_number']
        verbose_name = 'Open Item Transaction'
        verbose_name_plural = 'Open Item Transactions'
        unique_together = [['debtor', 'transaction_number']]
        indexes = [
            models.Index(fields=['debtor', 'transaction_date'], name='idx_dopen_deb_date'),
            models.Index(fields=['posted', 'age_flag'], name='idx_dopen_post_age'),
            models.Index(fields=['transaction_date', 'age_flag'], name='idx_dopen_date_age'),
            models.Index(fields=['fully_paid'], name='idx_dopen_paid'),
        ]
    
    def __str__(self):
        return f"{self.transaction_number} - {self.debtor.name} (Due: R{self.balance_due})"
    
    def clean(self):
        """Validate open item data."""
        errors = {}
        
        if self.original_amount < 0:
            errors['original_amount'] = 'Original amount cannot be negative.'
        
        if self.balance_due < 0:
            errors['balance_due'] = 'Balance due cannot be negative.'
        
        if self.balance_due > self.original_amount:
            errors['balance_due'] = 'Balance due cannot exceed original amount.'
        
        if errors:
            raise ValidationError(errors)
    
    def save(self, *args, **kwargs):
        """Validate and save."""
        # Auto-calculate due date if not set
        if not self.due_date and self.debtor and self.transaction_date:
            self.due_date = self.transaction_date + timezone.timedelta(
                days=self.debtor.payment_terms
            )
        
        # Auto-update aging flag
        self.update_age_flag()
        
        # Mark as fully paid if balance is zero
        if self.balance_due == 0:
            self.fully_paid = True
        
        self.full_clean()
        super().save(*args, **kwargs)
    
    @property
    def allocated_amount(self):
        """Calculate amount allocated (original - balance due)."""
        return self.original_amount - self.balance_due
    
    @property
    def days_overdue(self):
        """Calculate days past due date."""
        if not self.due_date:
            return 0
        if self.due_date >= date.today():
            return 0
        return (date.today() - self.due_date).days
    
    def update_age_flag(self):
        """Update aging flag based on days overdue."""
        days = self.days_overdue
        
        if days <= 0:
            self.age_flag = '0'  # Current
        elif days <= 30:
            self.age_flag = '1'  # 30 days
        elif days <= 60:
            self.age_flag = '2'  # 60 days
        elif days <= 90:
            self.age_flag = '3'  # 90 days
        else:
            self.age_flag = '4'  # 120+ days
    
    def allocate_payment(self, amount):
        """
        Allocate a payment against this open item.
        
        Args:
            amount (Decimal): Payment amount to allocate
        
        Returns:
            Decimal: Unused portion of payment (if any)
        """
        if amount <= 0:
            return Decimal('0.00')
        
        # Allocate up to balance due
        allocation = min(amount, self.balance_due)
        self.balance_due -= allocation
        
        # Mark as fully paid if balance is zero
        if self.balance_due == 0:
            self.fully_paid = True
        
        self.save()
        
        # Return unused portion
        return amount - allocation


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
        ('AL', 'Allocation'),
    ]
    
    # Foreign Key to Debtor
    dno = models.ForeignKey(
        Debtor,
        on_delete=models.CASCADE,
        related_name='debtoraud_records',
        db_column='dno',
        help_text="Debtor number (DNO)"
    )
    
    # Transaction Information
    dtrano = models.CharField(
        max_length=6,
        db_column='dtrano',
        help_text="Transaction number (DTRANO) - Character 6"
    )
    type = models.CharField(
        max_length=2,
        choices=TRANSACTION_TYPE_CHOICES,
        db_column='type',
        help_text="Transaction type (TYPE) - Character 2"
    )
    thistype = models.CharField(
        max_length=2,
        choices=TRANSACTION_TYPE_CHOICES,
        db_column='thistype',
        help_text="Current transaction type (THISTYPE) - Character 2"
    )
    thistran = models.CharField(
        max_length=6,
        db_column='thistran',
        help_text="Current transaction type identifier (THISTRAN) - Character 6"
    )
    
    # Audit Date and Amount
    date = models.DateField(
        db_index=True,
        db_column='date',
        help_text="Audit date (DATE) - Date 8"
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))],
        db_column='amount',
        help_text="Audit amount (AMOUNT) - Numeric 12.2"
    )
    
    # Additional tracking fields
    performed_by = models.CharField(
        max_length=50,
        blank=True,
        help_text="User who performed the action"
    )
    
    notes = models.TextField(
        blank=True,
        help_text="Audit notes"
    )
    
    class Meta:
        db_table = 'debtoraud'
        ordering = ['-date', '-dtrano']
        verbose_name = 'Debtor Audit (DEBTORAUD)'
        verbose_name_plural = 'Debtor Audits (DEBTORAUD)'
        unique_together = [['dno', 'dtrano', 'date']]
        indexes = [
            models.Index(fields=['dno', 'date'], name='idx_daud_deb_date'),
            models.Index(fields=['date', 'type'], name='idx_daud_date_type'),
            models.Index(fields=['type'], name='idx_daud_type'),
        ]
    
    def __str__(self):
        return f"DEBTORAUD {self.dno.customer_number} - {self.dtrano} ({self.date})"
    
    def clean(self):
        """Validate debtor audit data."""
        if self.amount < 0:
            raise ValidationError({'amount': 'Amount cannot be negative.'})
    
    def save(self, *args, **kwargs):
        """Validate before saving."""
        self.full_clean()
        super().save(*args, **kwargs)
    
    @staticmethod
    def log_transaction(debtor, transaction_number, transaction_type, amount, 
                       current_type=None, current_transaction=None, 
                       performed_by='', notes=''):
        """
        Create an audit log entry.
        
        Args:
            debtor: Debtor instance
            transaction_number: Transaction number
            transaction_type: Type of transaction
            amount: Transaction amount
            current_type: Current transaction type (for allocations)
            current_transaction: Current transaction number (for allocations)
            performed_by: Username of person performing action
            notes: Additional notes
        
        Returns:
            DebtorAudit: Created audit record
        """
        return DebtorAudit.objects.create(
            dno=debtor,
            dtrano=transaction_number,
            type=transaction_type,
            thistype=current_type or transaction_type,
            thistran=current_transaction or transaction_number,
            date=date.today(),
            amount=amount,
            performed_by=performed_by,
            notes=notes
        )


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