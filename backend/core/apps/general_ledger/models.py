from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.settings.models import TimeStampedModel


class GLMast(TimeStampedModel):
    """General Ledger Master - Accounts Details from Maintenance Balances"""
    
    ACCOUNT_TYPE_CHOICES = [
        ('I', 'Income Statement'),
        ('B', 'Balance Sheet'),
    ]
    
    DEBIT_CREDIT_CHOICES = [
        ('D', 'Debit'),
        ('C', 'Credit'),
    ]
    
    # Account Details
    accno = models.BigIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(99999999)],
        unique=True,
        help_text="Account Number (8 digits)"
    )
    name = models.CharField(
        max_length=30,
        help_text="Account Name"
    )
    type = models.CharField(
        max_length=1,
        choices=ACCOUNT_TYPE_CHOICES,
        help_text="Income Statement or Balance Sheet"
    )
    drorcr = models.CharField(
        max_length=1,
        choices=DEBIT_CREDIT_CHOICES,
        help_text="Debit or Credit"
    )
    repline = models.IntegerField(
        help_text="Report line number"
    )
    
    # Balance B/F (Balance Brought Forward)
    balbfwd = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0.00,
        help_text="Balance Brought Forward"
    )
    
    # Period Balances (13 periods for monthly + one additional)
    period1 = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0.00,
        help_text="Period 1 Balance"
    )
    period2 = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0.00,
        help_text="Period 2 Balance"
    )
    period3 = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0.00,
        help_text="Period 3 Balance"
    )
    period4 = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0.00,
        help_text="Period 4 Balance"
    )
    period5 = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0.00,
        help_text="Period 5 Balance"
    )
    period6 = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0.00,
        help_text="Period 6 Balance"
    )
    period7 = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0.00,
        help_text="Period 7 Balance"
    )
    period8 = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0.00,
        help_text="Period 8 Balance"
    )
    period9 = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0.00,
        help_text="Period 9 Balance"
    )
    period10 = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0.00,
        help_text="Period 10 Balance"
    )
    period11 = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0.00,
        help_text="Period 11 Balance"
    )
    period12 = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0.00,
        help_text="Period 12 Balance"
    )
    period13 = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0.00,
        help_text="Period 13 Balance"
    )
    
    # Budget Fields (12 months)
    budget1 = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0.00,
        help_text="Budget Period 1"
    )
    budget2 = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0.00,
        help_text="Budget Period 2"
    )
    budget3 = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0.00,
        help_text="Budget Period 3"
    )
    budget4 = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0.00,
        help_text="Budget Period 4"
    )
    budget5 = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0.00,
        help_text="Budget Period 5"
    )
    budget6 = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0.00,
        help_text="Budget Period 6"
    )
    budget7 = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0.00,
        help_text="Budget Period 7"
    )
    budget8 = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0.00,
        help_text="Budget Period 8"
    )
    budget9 = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0.00,
        help_text="Budget Period 9"
    )
    budget10 = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0.00,
        help_text="Budget Period 10"
    )
    budget11 = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0.00,
        help_text="Budget Period 11"
    )
    budget12 = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0.00,
        help_text="Budget Period 12"
    )
    
    # Last Year Fields (Year-to-date balances - 12 months)
    lastyear1 = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0.00,
        help_text="Last Year Period 1 Balance"
    )
    lastyear2 = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0.00,
        help_text="Last Year Period 2 Balance"
    )
    lastyear3 = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0.00,
        help_text="Last Year Period 3 Balance"
    )
    lastyear4 = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0.00,
        help_text="Last Year Period 4 Balance"
    )
    lastyear5 = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0.00,
        help_text="Last Year Period 5 Balance"
    )
    lastyear6 = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0.00,
        help_text="Last Year Period 6 Balance"
    )
    lastyear7 = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0.00,
        help_text="Last Year Period 7 Balance"
    )
    lastyear8 = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0.00,
        help_text="Last Year Period 8 Balance"
    )
    lastyear9 = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0.00,
        help_text="Last Year Period 9 Balance"
    )
    lastyear10 = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0.00,
        help_text="Last Year Period 10 Balance"
    )
    lastyear11 = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0.00,
        help_text="Last Year Period 11 Balance"
    )
    lastyear12 = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0.00,
        help_text="Last Year Period 12 Balance"
    )
    
    class Meta:
        ordering = ['accno']
        verbose_name = "GL Master Account"
        verbose_name_plural = "GL Master Accounts"
        indexes = [
            models.Index(fields=['accno']),
            models.Index(fields=['type']),
            models.Index(fields=['drorcr']),
        ]
    
    def __str__(self):
        return f"{self.accno} - {self.name}"


class GLTran(TimeStampedModel):
    """GL Transaction - Transaction Details for Journal Entries"""
    
    TRANSACTION_TYPE_CHOICES = [
        ('D', 'Debit'),
        ('C', 'Credit'),
    ]
    
    # Common journal entry sources
    SOURCE_CHOICES = [
        ('M', 'Manual'),
        ('S', 'System'),
        ('I', 'Import'),
        ('B', 'Bank'),
        ('O', 'Other'),
    ]
    
    # Account Reference - links to GL Master account
    accno = models.BigIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(99999999)],
        help_text="Account Number (8 digits)"
    )
    
    # Batch Information
    batchno = models.BigIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(99999999)],
        help_text="Batch Number (8 digits) - groups related transactions"
    )
    
    # Transaction Details
    date = models.DateField(help_text="Transaction date")
    time = models.TimeField(null=True, blank=True, help_text="Transaction time (HH:MM)")
    
    # Transaction Classification
    type = models.CharField(
        max_length=1,
        choices=TRANSACTION_TYPE_CHOICES,
        help_text="Debit or Credit"
    )
    
    source = models.CharField(
        max_length=1,
        choices=SOURCE_CHOICES,
        default='M',
        help_text="Journal entry source (Manual, System, Import, Bank, Other)"
    )
    
    # Location and Reference
    station = models.CharField(
        max_length=2,
        blank=True,
        help_text="Station/Workstation number"
    )
    
    reference = models.CharField(
        max_length=10,
        blank=True,
        help_text="Transaction reference code/voucher number"
    )
    
    # Description
    details = models.CharField(
        max_length=30,
        blank=True,
        help_text="Transaction details/description"
    )
    
    # Amount
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Transaction amount"
    )
    
    class Meta:
        ordering = ['-date', '-time', 'accno']
        verbose_name = "GL Transaction"
        verbose_name_plural = "GL Transactions"
        indexes = [
            models.Index(fields=['accno', 'date']),
            models.Index(fields=['batchno']),
            models.Index(fields=['date']),
            models.Index(fields=['type']),
            models.Index(fields=['source']),
            models.Index(fields=['reference']),
        ]
    
    def __str__(self):
        return f"Batch {self.batchno} - Acct {self.accno} - {self.date} - {self.amount}"


class GLParam(TimeStampedModel):
    """GL Parameter - General Ledger System Parameters Setup"""
    
    # Start Period
    startper = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(12)],
        default=1,
        help_text="Start period (1-12)"
    )
    
    # Batch Number
    batchno = models.BigIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(99999999)],
        default=0,
        help_text="Batch # (numeric, 8 digits max)"
    )
    
    # Current Period
    curperiod = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(13)],
        default=1,
        help_text="Current period (1-13)"
    )
    
    # Adjusted Flag
    adjusted = models.CharField(
        max_length=1,
        choices=[('Y', 'Yes'), ('N', 'No')],
        default='N',
        help_text="Has database been adjusted (Y/N)"
    )
    
    # Current Year
    currentyr = models.IntegerField(
        validators=[MinValueValidator(1900), MaxValueValidator(9999)],
        default=2026,
        help_text="Current Year (4 digits)"
    )
    
    class Meta:
        verbose_name = "GL Parameter"
        verbose_name_plural = "GL Parameters"
    
    def __str__(self):
        return f"GL Parameters - Year {self.currentyr}, Period {self.curperiod}"


class GLRep(TimeStampedModel):
    """GL Report - Report Format Configuration"""
    
    REPORT_TYPE_CHOICES = [
        ('I', 'Income Statement'),
        ('B', 'Balance Sheet'),
    ]
    
    FIELD_TYPE_CHOICES = [
        ('H', 'Heading'),
        ('T', 'Total'),
        ('D', 'Detail'),
        ('S', 'Subtotal'),
    ]
    
    PRINT_DETAIL_CHOICES = [
        ('D', 'Double'),
        ('S', 'Single'),
        ('N', 'None'),
    ]
    
    # Report Type
    type = models.CharField(
        max_length=1,
        choices=REPORT_TYPE_CHOICES,
        help_text="Income Statement or Balance Sheet"
    )
    
    # Field Type
    fieldtype = models.CharField(
        max_length=1,
        choices=FIELD_TYPE_CHOICES,
        help_text="Type of heading (Heading, Total, Detail, Subtotal)"
    )
    
    # Line Number
    line = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(9999)],
        help_text="Line # (1-9999)"
    )
    
    # Print Detail Setting
    printdet = models.CharField(
        max_length=10,
        choices=PRINT_DETAIL_CHOICES,
        default='N',
        help_text="Double/Single/None line format"
    )
    
    # Heading/Total Name
    name = models.CharField(
        max_length=30,
        help_text="Heading/Total name"
    )
    
    # Start Line
    start = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(9999)],
        help_text="Start line #"
    )
    
    # End Line for Calculation
    endcalc = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(9999)],
        help_text="End line # for calculation"
    )
    
    class Meta:
        ordering = ['type', 'line']
        verbose_name = "GL Report Format"
        verbose_name_plural = "GL Report Formats"
        indexes = [
            models.Index(fields=['type', 'line']),
            models.Index(fields=['type']),
            models.Index(fields=['fieldtype']),
        ]
    
    def __str__(self):
        return f"{self.get_type_display()} - Line {self.line}: {self.name}"


class GLBatch(TimeStampedModel):
    """GL Batch - Batch Transaction Details"""
    
    DEBIT_CREDIT_CHOICES = [
        ('D', 'Debit'),
        ('C', 'Credit'),
    ]
    
    SOURCE_CHOICES = [
        ('M', 'Manual'),
        ('S', 'System'),
        ('I', 'Import'),
        ('B', 'Bank'),
        ('O', 'Other'),
    ]
    
    # Account Reference
    accno = models.BigIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(99999999)],
        help_text="Account # (8 digits)"
    )
    
    # Batch Number
    batchno = models.BigIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(99999999)],
        help_text="Batch # (8 digits)"
    )
    
    # Capture Date/Time
    capturedat = models.DateField(
        help_text="Date captured"
    )
    
    # Transaction Date/Time
    date = models.DateField(
        help_text="Transaction date"
    )
    
    time = models.CharField(
        max_length=5,
        blank=True,
        help_text="Transaction time (HH:MM)"
    )
    
    # Debit or Credit
    drorcr = models.CharField(
        max_length=1,
        choices=DEBIT_CREDIT_CHOICES,
        help_text="Debit or Credit"
    )
    
    # Journal Entry Source
    source = models.CharField(
        max_length=1,
        choices=SOURCE_CHOICES,
        default='M',
        help_text="Journal entry source"
    )
    
    # Station/Workstation Number
    station = models.CharField(
        max_length=2,
        blank=True,
        help_text="Station # (2 characters)"
    )
    
    # Transaction Reference
    reference = models.CharField(
        max_length=10,
        blank=True,
        help_text="Transaction reference"
    )
    
    # Transaction Details
    details = models.CharField(
        max_length=30,
        blank=True,
        help_text="Transaction Details"
    )
    
    # Amount
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Value (transaction amount)"
    )
    
    # Post Date/Time
    postdate = models.DateField(
        null=True,
        blank=True,
        help_text="Date posted"
    )
    
    postime = models.CharField(
        max_length=5,
        blank=True,
        help_text="Time posted (HH:MM)"
    )
    
    # Period to Post
    period = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(13)],
        help_text="Period to post to (1-13)"
    )
    
    class Meta:
        ordering = ['-capturedat', 'batchno', 'accno']
        verbose_name = "GL Batch Transaction"
        verbose_name_plural = "GL Batch Transactions"
        indexes = [
            models.Index(fields=['batchno']),
            models.Index(fields=['accno', 'date']),
            models.Index(fields=['capturedat']),
            models.Index(fields=['postdate']),
            models.Index(fields=['drorcr']),
            models.Index(fields=['source']),
        ]
    
    def __str__(self):
        return f"Batch {self.batchno} - Acct {self.accno} - {self.amount}"


class GLStJnl(TimeStampedModel):
    """GL Standing Journal - Standing Details Period Posting"""
    
    DEBIT_CREDIT_CHOICES = [
        ('D', 'Debit'),
        ('C', 'Credit'),
    ]
    
    # Account Reference
    accno = models.BigIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(99999999)],
        help_text="Account # (8 digits)"
    )
    
    # Transaction Details
    details = models.CharField(
        max_length=30,
        help_text="Transaction details"
    )
    
    # Debit or Credit
    drorcr = models.CharField(
        max_length=1,
        choices=DEBIT_CREDIT_CHOICES,
        help_text="Debit or Credit"
    )
    
    # Amount
    amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        help_text="Value (transaction amount)"
    )
    
    # Frequency - # of times to occur
    frequency = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(9)],
        help_text="# of times to occur (1-9)"
    )
    
    # Start Period
    stperiod = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(12)],
        help_text="Start period (1-12)"
    )
    
    # Times - # of times to apply
    times = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(999)],
        help_text="# of times to apply (1-999)"
    )
    
    # Times Balance - Total of times
    timesbal = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(999)],
        default=0,
        help_text="Total of times (0-999)"
    )
    
    # Next Period
    nextperiod = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(12)],
        help_text="Next period (1-12)"
    )
    
    # Descriptor/Reference
    descriptor = models.CharField(
        max_length=30,
        blank=True,
        help_text="Reference descriptor"
    )
    
    # Journal Number
    journalno = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(999999)],
        help_text="Journal # (6 digits max)"
    )
    
    class Meta:
        ordering = ['accno', 'journalno']
        verbose_name = "GL Standing Journal"
        verbose_name_plural = "GL Standing Journals"
        indexes = [
            models.Index(fields=['accno']),
            models.Index(fields=['journalno']),
            models.Index(fields=['stperiod']),
            models.Index(fields=['drorcr']),
        ]
    
    def __str__(self):
        return f"Journal {self.journalno} - Acct {self.accno} - {self.amount}"


class GLSpread(TimeStampedModel):
    """GL Spread - Account Spread Sheet with YTD and Current Period Balances"""
    
    # Account Reference
    accno = models.BigIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(99999999)],
        unique=True,
        help_text="Account # (8 digits)"
    )
    
    # Account Name
    name = models.CharField(
        max_length=30,
        help_text="Account Name"
    )
    
    # Year-to-date Debit
    ytddebit = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0.00,
        help_text="Year-to-date debit"
    )
    
    # Year-to-date Credit
    ytdcredit = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0.00,
        help_text="Year-to-date credit"
    )
    
    # Current Period Debit
    curdebit = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0.00,
        help_text="Current period debit"
    )
    
    # Current Period Credit
    curcredit = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0.00,
        help_text="Current period credit"
    )
    
    # Current Budget Debit
    curbuddeb = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0.00,
        help_text="Current budget debit"
    )
    
    # Current Budget Credit
    curbudcred = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0.00,
        help_text="Current budget credit"
    )
    
    # Year-to-date Budget Debit
    ytdbuddeb = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0.00,
        help_text="Year-to-date budget debit"
    )
    
    # Year-to-date Budget Credit
    ytdbudcred = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0.00,
        help_text="Year-to-date budget credit"
    )
    
    class Meta:
        ordering = ['accno']
        verbose_name = "GL Spread Sheet"
        verbose_name_plural = "GL Spread Sheets"
        indexes = [
            models.Index(fields=['accno']),
        ]
    
    def __str__(self):
        return f"{self.accno} - {self.name}"
