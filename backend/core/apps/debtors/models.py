"""
DEBTORS APP - Django Models
API-first design for customer/debtor management

Models:
- Debtor (Customer Account)
- DebtorTransaction (Base for all transactions)
- Invoice
- InvoiceLineItem
- CreditNote
- CreditNoteLineItem
- DebtorReceipt
- DebtorJournal
- PostDatedCheque
- DebtorOpenItem (for Open Item accounting)
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth import get_user_model
from decimal import Decimal
from apps.settings.models import (
    SalesArea,
    SalesDepartment,
    TaxCode,
    CreditTerms,
    TimeStampedModel,
    ActiveModel
)

User = get_user_model()


# ============================================================================
# DEBTOR ACCOUNT MODEL
# ============================================================================

class Debtor(TimeStampedModel, ActiveModel):
    """
    Customer/Debtor Account
    Supports both Balance Brought Forward and Open Item accounting
    """
    
    ACCOUNT_CATEGORY_CHOICES = [
        ('BBF', 'Balance Brought Forward'),
        ('OI', 'Open Item'),
        ('CASH', 'Cash Customer'),
    ]
    
    # === USER INPUT FIELDS ===
    
    # Account identification
    account_number = models.CharField(
        max_length=20,
        unique=True,
        help_text="Customer account number"
    )
    name = models.CharField(max_length=200)
    search_name = models.CharField(
        max_length=50,
        db_index=True,
        help_text="Quick search name (first 5 chars)"
    )
    
    # Contact information
    contact_person = models.CharField(max_length=100, blank=True)
    telephone_1 = models.CharField(max_length=20, blank=True)
    telephone_2 = models.CharField(max_length=20, blank=True)
    fax = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    additional_info = models.CharField(
        max_length=200,
        blank=True,
        help_text="E.g., Cell number"
    )
    
    # Addresses
    postal_address_line1 = models.CharField(max_length=100, blank=True)
    postal_address_line2 = models.CharField(max_length=100, blank=True)
    postal_city = models.CharField(max_length=50, blank=True)
    postal_province = models.CharField(max_length=50, blank=True)
    postal_code = models.CharField(max_length=10, blank=True)
    postal_country = models.CharField(max_length=50, default='South Africa')
    
    delivery_address_line1 = models.CharField(max_length=100, blank=True)
    delivery_address_line2 = models.CharField(max_length=100, blank=True)
    delivery_city = models.CharField(max_length=50, blank=True)
    delivery_province = models.CharField(max_length=50, blank=True)
    delivery_code = models.CharField(max_length=10, blank=True)
    delivery_country = models.CharField(max_length=50, default='South Africa')
    
    # Foreign Keys to Core models
    area_salesman = models.ForeignKey(
        SalesArea,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='debtors'
    )
    
    # Account settings
    trade_discount_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="% discount applied at POS"
    )
    credit_limit = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        help_text="Maximum credit allowed"
    )
    
    PRICE_CODE_CHOICES = [
        (1, 'Price Level 1'),
        (2, 'Price Level 2'),
        (3, 'Price Level 3'),
    ]
    price_code = models.PositiveSmallIntegerField(
        choices=PRICE_CODE_CHOICES,
        default=1,
        help_text="Which price level to use"
    )
    
    charge_interest = models.BooleanField(
        default=False,
        help_text="Charge interest on overdue accounts"
    )
    
    account_category = models.CharField(
        max_length=10,
        choices=ACCOUNT_CATEGORY_CHOICES,
        default='BBF',
        help_text="Accounting method"
    )
    
    vat_tax_reference = models.CharField(
        max_length=50,
        blank=True,
        help_text="SARS VAT Number"
    )
    
    credit_terms = models.ForeignKey(
        CreditTerms,
        on_delete=models.PROTECT,
        related_name='debtors',
        help_text="Payment terms (30/60/90 days)"
    )
    
    prompt_discount_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Early payment discount %"
    )
    print_discount_on_invoices = models.BooleanField(
        default=True,
        help_text="Show prompt discount on invoices"
    )
    print_balance_on_pos_docs = models.BooleanField(
        default=True,
        help_text="Print balance on invoices/receipts"
    )
    
    # Block status
    BLOCK_STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('BLOCK_ALL', 'Block All Transactions'),
        ('BLOCK_SALES', 'Block Sales Only'),
        ('BLOCK_RECEIPTS', 'Block Receipts Only'),
    ]
    block_status = models.CharField(
        max_length=20,
        choices=BLOCK_STATUS_CHOICES,
        default='ACTIVE',
        help_text="Account block status"
    )
    
    # === SYSTEM GENERATED FIELDS ===
    
    # Current balances (BBF method)
    current_balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        editable=False,
        help_text="Total outstanding balance"
    )
    balance_current = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        editable=False
    )
    balance_30_days = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        editable=False
    )
    balance_60_days = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        editable=False
    )
    balance_90_days = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        editable=False
    )
    balance_120_days = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        editable=False
    )
    balance_150_days = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        editable=False
    )
    balance_180_days = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        editable=False
    )
    
    # Last payment info
    last_paid_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        editable=False
    )
    last_paid_date = models.DateField(null=True, blank=True, editable=False)
    
    # Sales statistics
    sales_mtd = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        editable=False,
        help_text="Sales Month-to-Date"
    )
    sales_ytd = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        editable=False,
        help_text="Sales Year-to-Date"
    )
    profit_mtd = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        editable=False,
        help_text="Profit Month-to-Date"
    )
    profit_ytd = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        editable=False,
        help_text="Profit Year-to-Date"
    )
    
    class Meta:
        db_table = 'debtors'
        ordering = ['account_number']
        indexes = [
            models.Index(fields=['account_number']),
            models.Index(fields=['search_name']),
            models.Index(fields=['name']),
            models.Index(fields=['is_active']),
            models.Index(fields=['account_category']),
            models.Index(fields=['area_salesman']),
        ]
        verbose_name = 'Debtor'
        verbose_name_plural = 'Debtors'
    
    def __str__(self):
        return f"{self.account_number} - {self.name}"
    
    def save(self, *args, **kwargs):
        # Auto-generate search name from first 5 chars
        if not self.search_name:
            self.search_name = self.name[:5].upper()
        
        # Calculate current balance
        self.current_balance = (
            self.balance_current +
            self.balance_30_days +
            self.balance_60_days +
            self.balance_90_days +
            self.balance_120_days +
            self.balance_150_days +
            self.balance_180_days
        )
        
        super().save(*args, **kwargs)
    
    @property
    def is_over_credit_limit(self):
        """Check if account exceeds credit limit"""
        return self.current_balance > self.credit_limit
    
    @property
    def available_credit(self):
        """Calculate available credit"""
        return max(Decimal('0'), self.credit_limit - self.current_balance)
    
    @property
    def is_blocked(self):
        """Check if any blocking is active"""
        return self.block_status != 'ACTIVE'


# ============================================================================
# DEBTOR TRANSACTION BASE MODEL
# ============================================================================

class DebtorTransaction(TimeStampedModel):
    """
    Base model for all debtor transactions
    Abstract model - not created as table
    """
    
    TRANSACTION_TYPE_CHOICES = [
        ('INV', 'Invoice'),
        ('CN', 'Credit Note'),
        ('RCT', 'Receipt'),
        ('DJ', 'Debit Journal'),
        ('CJ', 'Credit Journal'),
        ('INT', 'Interest Charge'),
    ]
    
    debtor = models.ForeignKey(
        Debtor,
        on_delete=models.PROTECT,
        related_name='%(class)s_set'
    )
    
    transaction_type = models.CharField(
        max_length=10,
        choices=TRANSACTION_TYPE_CHOICES
    )
    transaction_number = models.CharField(
        max_length=20,
        unique=True,
        help_text="Auto-generated transaction number"
    )
    transaction_date = models.DateField()
    
    # References
    transaction_reference = models.CharField(
        max_length=50,
        blank=True,
        help_text="External reference"
    )
    additional_reference = models.CharField(
        max_length=200,
        blank=True,
        help_text="Additional info"
    )
    
    # Amounts
    total_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )
    
    # Status
    is_posted = models.BooleanField(
        default=False,
        help_text="Has been posted to ledger"
    )
    posted_at = models.DateTimeField(null=True, blank=True, editable=False)
    posted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_posted'
    )
    
    class Meta:
        abstract = True
        ordering = ['-transaction_date', '-transaction_number']
    
    def __str__(self):
        return f"{self.transaction_type} {self.transaction_number}"


# ============================================================================
# INVOICE MODEL
# ============================================================================

class Invoice(DebtorTransaction):
    """
    Sales Invoice
    """
    
    # Order information (if from order system)
    order_number = models.CharField(max_length=20, blank=True)
    
    # Tax handling
    INCLUSIVE_EXCLUSIVE_CHOICES = [
        ('INC', 'Inclusive of VAT'),
        ('EXC', 'Exclusive of VAT'),
    ]
    inclusive_exclusive = models.CharField(
        max_length=3,
        choices=INCLUSIVE_EXCLUSIVE_CHOICES,
        default='INC'
    )
    
    # Calculated totals
    subtotal = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        editable=False
    )
    total_discount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        editable=False
    )
    total_tax = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        editable=False
    )
    total_gross_profit = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        editable=False
    )
    
    # Ageing (for BBF accounts)
    age_current = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    age_30 = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    age_60 = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    age_90 = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    age_120 = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    age_150 = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    age_180 = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    class Meta:
        db_table = 'debtor_invoices'
        verbose_name = 'Invoice'
        verbose_name_plural = 'Invoices'
        indexes = [
            models.Index(fields=['debtor', 'transaction_date']),
            models.Index(fields=['is_posted']),
            models.Index(fields=['transaction_number']),
        ]
    
    def save(self, *args, **kwargs):
        self.transaction_type = 'INV'
        
        # Auto-generate transaction number if not set
        if not self.transaction_number:
            self.transaction_number = self._generate_invoice_number()
        
        super().save(*args, **kwargs)
    
    def _generate_invoice_number(self):
        """Generate next invoice number"""
        last_invoice = Invoice.objects.order_by('-id').first()
        if last_invoice and last_invoice.transaction_number:
            try:
                last_num = int(last_invoice.transaction_number.split('-')[-1])
                return f"INV-{last_num + 1:06d}"
            except:
                pass
        return f"INV-000001"
    
    def calculate_totals(self):
        """Calculate all totals from line items"""
        lines = self.line_items.all()
        
        self.subtotal = sum(line.subtotal for line in lines)
        self.total_discount = sum(line.discount_amount for line in lines)
        self.total_tax = sum(line.tax_amount for line in lines)
        self.total_amount = sum(line.line_total for line in lines)
        self.total_gross_profit = sum(line.gross_profit for line in lines)
        
        self.save()


# ============================================================================
# INVOICE LINE ITEM MODEL
# ============================================================================

class InvoiceLineItem(TimeStampedModel):
    """
    Line item on invoice
    """
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name='line_items'
    )
    line_number = models.PositiveSmallIntegerField(default=1)
    
    # === USER INPUT ===
    stock_item = models.ForeignKey(
        'stock_control.StockItem',
        on_delete=models.PROTECT,
        related_name='invoice_lines'
    )
    quantity = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    unit_price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Selling price per unit"
    )
    discount_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    tax_code = models.ForeignKey(
        TaxCode,
        on_delete=models.PROTECT
    )
    
    # === SYSTEM CALCULATED ===
    cost_price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        editable=False,
        help_text="Cost price from stock item"
    )
    subtotal = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        editable=False
    )
    discount_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        editable=False
    )
    tax_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        editable=False
    )
    line_total = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        editable=False
    )
    gross_profit = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        editable=False
    )
    gross_profit_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        editable=False
    )
    
    class Meta:
        db_table = 'debtor_invoice_line_items'
        ordering = ['line_number']
        unique_together = [['invoice', 'line_number']]
    
    def save(self, *args, **kwargs):
        # Get cost price from stock item
        if not self.cost_price:
            self.cost_price = self.stock_item.cost_price
        
        # Calculate amounts
        self.subtotal = self.quantity * self.unit_price
        self.discount_amount = self.subtotal * (self.discount_percent / 100)
        
        subtotal_after_discount = self.subtotal - self.discount_amount
        self.tax_amount = subtotal_after_discount * (self.tax_code.rate / 100)
        self.line_total = subtotal_after_discount + self.tax_amount
        
        # Calculate gross profit
        total_cost = self.cost_price * self.quantity
        self.gross_profit = subtotal_after_discount - total_cost
        
        if subtotal_after_discount > 0:
            self.gross_profit_percent = (self.gross_profit / subtotal_after_discount) * 100
        else:
            self.gross_profit_percent = 0
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Line {self.line_number}: {self.stock_item.description}"


# ============================================================================
# CREDIT NOTE MODEL
# ============================================================================

class CreditNote(DebtorTransaction):
    """
    Credit Note (Sales Return)
    """
    
    # Link to original invoice (optional)
    original_invoice = models.ForeignKey(
        Invoice,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='credit_notes'
    )
    
    INCLUSIVE_EXCLUSIVE_CHOICES = [
        ('INC', 'Inclusive of VAT'),
        ('EXC', 'Exclusive of VAT'),
    ]
    inclusive_exclusive = models.CharField(
        max_length=3,
        choices=INCLUSIVE_EXCLUSIVE_CHOICES,
        default='INC'
    )
    
    # Calculated totals
    subtotal = models.DecimalField(max_digits=15, decimal_places=2, default=0, editable=False)
    total_tax = models.DecimalField(max_digits=15, decimal_places=2, default=0, editable=False)
    
    # Ageing (for BBF accounts)
    age_current = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    age_30 = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    age_60 = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    age_90 = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    age_120 = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    age_150 = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    age_180 = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    class Meta:
        db_table = 'debtor_credit_notes'
        verbose_name = 'Credit Note'
        verbose_name_plural = 'Credit Notes'
    
    def save(self, *args, **kwargs):
        self.transaction_type = 'CN'
        
        if not self.transaction_number:
            self.transaction_number = self._generate_cn_number()
        
        super().save(*args, **kwargs)
    
    def _generate_cn_number(self):
        """Generate next credit note number"""
        last_cn = CreditNote.objects.order_by('-id').first()
        if last_cn and last_cn.transaction_number:
            try:
                last_num = int(last_cn.transaction_number.split('-')[-1])
                return f"CN-{last_num + 1:06d}"
            except:
                pass
        return f"CN-000001"


class CreditNoteLineItem(TimeStampedModel):
    """Line items for credit note"""
    credit_note = models.ForeignKey(
        CreditNote,
        on_delete=models.CASCADE,
        related_name='line_items'
    )
    line_number = models.PositiveSmallIntegerField(default=1)
    
    stock_item = models.ForeignKey(
        'stock_control.StockItem',
        on_delete=models.PROTECT,
        related_name='credit_note_lines'
    )
    quantity = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    unit_price = models.DecimalField(max_digits=15, decimal_places=2)
    tax_code = models.ForeignKey(TaxCode, on_delete=models.PROTECT)
    
    # Calculated
    cost_price = models.DecimalField(max_digits=15, decimal_places=2, editable=False)
    subtotal = models.DecimalField(max_digits=15, decimal_places=2, editable=False)
    tax_amount = models.DecimalField(max_digits=15, decimal_places=2, editable=False)
    line_total = models.DecimalField(max_digits=15, decimal_places=2, editable=False)
    
    class Meta:
        db_table = 'debtor_credit_note_line_items'
        ordering = ['line_number']
        unique_together = [['credit_note', 'line_number']]
    
    def save(self, *args, **kwargs):
        if not self.cost_price:
            self.cost_price = self.stock_item.cost_price
        
        self.subtotal = self.quantity * self.unit_price
        self.tax_amount = self.subtotal * (self.tax_code.rate / 100)
        self.line_total = self.subtotal + self.tax_amount
        
        super().save(*args, **kwargs)


# ============================================================================
# DEBTOR RECEIPT MODEL
# ============================================================================

class DebtorReceipt(DebtorTransaction):
    """
    Receipt from Debtor
    """
    
    # Receipt details
    amount_due = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Amount that was due"
    )
    amount_tendered = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Actual amount received"
    )
    settlement_discount_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        editable=False
    )
    settlement_discount_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        editable=False
    )
    
    # Payment method
    payment_method = models.ForeignKey(
        'settings.PaymentMethod',
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )
    
    # For Open Item: is this unallocated?
    is_unallocated = models.BooleanField(
        default=False,
        help_text="Unallocated receipt (OI only)"
    )
    
    # Ageing allocation (for BBF)
    age_current = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    age_30 = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    age_60 = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    age_90 = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    age_120 = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    age_150 = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    age_180 = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    class Meta:
        db_table = 'debtor_receipts'
        verbose_name = 'Debtor Receipt'
        verbose_name_plural = 'Debtor Receipts'
    
    def save(self, *args, **kwargs):
        self.transaction_type = 'RCT'
        
        if not self.transaction_number:
            self.transaction_number = self._generate_receipt_number()
        
        # Calculate settlement discount
        self.settlement_discount_amount = self.amount_due - self.amount_tendered
        if self.amount_due > 0:
            self.settlement_discount_percent = (
                self.settlement_discount_amount / self.amount_due
            ) * 100
        
        self.total_amount = self.amount_tendered
        
        super().save(*args, **kwargs)
    
    def _generate_receipt_number(self):
        """Generate next receipt number"""
        last_receipt = DebtorReceipt.objects.order_by('-id').first()
        if last_receipt and last_receipt.transaction_number:
            try:
                last_num = int(last_receipt.transaction_number.split('-')[-1])
                return f"RCT-{last_num + 1:06d}"
            except:
                pass
        return f"RCT-000001"


# ============================================================================
# JOURNAL ENTRY MODEL
# ============================================================================

class DebtorJournal(DebtorTransaction):
    """
    Debit or Credit Journal Entry
    """
    
    JOURNAL_TYPE_CHOICES = [
        ('DEBIT', 'Debit Journal'),
        ('CREDIT', 'Credit Journal'),
    ]
    journal_type = models.CharField(
        max_length=10,
        choices=JOURNAL_TYPE_CHOICES
    )
    
    journal_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2
    )
    
    # Ageing allocation
    age_current = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    age_30 = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    age_60 = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    age_90 = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    age_120 = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    age_150 = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    age_180 = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    class Meta:
        db_table = 'debtor_journals'
        verbose_name = 'Debtor Journal'
        verbose_name_plural = 'Debtor Journals'
    
    def save(self, *args, **kwargs):
        self.transaction_type = 'DJ' if self.journal_type == 'DEBIT' else 'CJ'
        
        if not self.transaction_number:
            self.transaction_number = self._generate_journal_number()
        
        self.total_amount = self.journal_amount
        
        super().save(*args, **kwargs)
    
    def _generate_journal_number(self):
        """Generate next journal number"""
        prefix = 'DJ' if self.journal_type == 'DEBIT' else 'CJ'
        last_journal = DebtorJournal.objects.filter(
            journal_type=self.journal_type
        ).order_by('-id').first()
        
        if last_journal and last_journal.transaction_number:
            try:
                last_num = int(last_journal.transaction_number.split('-')[-1])
                return f"{prefix}-{last_num + 1:06d}"
            except:
                pass
        return f"{prefix}-000001"


# ============================================================================
# OPEN ITEM MODEL (for Open Item accounting)
# ============================================================================

class DebtorOpenItem(models.Model):
    """
    Tracks individual open items for Open Item accounting
    Links receipts to specific invoices/credit notes
    """
    debtor = models.ForeignKey(
        Debtor,
        on_delete=models.CASCADE,
        related_name='open_items'
    )
    
    # Link to source transaction
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='open_items'
    )
    credit_note = models.ForeignKey(
        CreditNote,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='open_items'
    )
    journal = models.ForeignKey(
        DebtorJournal,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='open_items'
    )
    
    transaction_date = models.DateField()
    transaction_type = models.CharField(max_length=10)
    transaction_number = models.CharField(max_length=20)
    
    original_amount = models.DecimalField(max_digits=15, decimal_places=2)
    balance_due = models.DecimalField(max_digits=15, decimal_places=2)
    
    # Ageing
    age_period = models.PositiveSmallIntegerField(
        default=0,
        help_text="0=Current, 1=30, 2=60, etc."
    )
    
    is_fully_allocated = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'debtor_open_items'
        ordering = ['transaction_date']
        indexes = [
            models.Index(fields=['debtor', 'is_fully_allocated']),
            models.Index(fields=['transaction_date']),
        ]


class OpenItemAllocation(models.Model):
    """
    Tracks allocation of receipts to open items
    """
    receipt = models.ForeignKey(
        DebtorReceipt,
        on_delete=models.CASCADE,
        related_name='allocations'
    )
    open_item = models.ForeignKey(
        DebtorOpenItem,
        on_delete=models.CASCADE,
        related_name='allocations'
    )
    
    amount_paid = models.DecimalField(max_digits=15, decimal_places=2)
    settlement_discount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )
    
    allocated_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'open_item_allocations'


# ============================================================================
# POST DATED CHEQUE MODEL
# ============================================================================

class PostDatedCheque(TimeStampedModel):
    """
    Post-dated cheque tracking (informational only)
    """
    debtor = models.ForeignKey(
        Debtor,
        on_delete=models.CASCADE,
        related_name='post_dated_cheques'
    )
    
    cheque_date = models.DateField(help_text="Date cheque can be banked")
    cheque_amount = models.DecimalField(max_digits=15, decimal_places=2)
    cheque_number = models.CharField(max_length=50, blank=True)
    bank_name = models.CharField(max_length=100, blank=True)
    
    is_processed = models.BooleanField(
        default=False,
        help_text="Has been processed as receipt"
    )
    processed_date = models.DateField(null=True, blank=True)
    receipt = models.ForeignKey(
        DebtorReceipt,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='from_pdc'
    )
    
    class Meta:
        db_table = 'post_dated_cheques'
        ordering = ['cheque_date']
        indexes = [
            models.Index(fields=['debtor', 'is_processed']),
            models.Index(fields=['cheque_date']),
        ]
    
    def __str__(self):
        return f"PDC {self.cheque_date} - {self.debtor.name} - {self.cheque_amount}"


# ============================================================================
# INTEREST CHARGE MODEL
# ============================================================================

class InterestCharge(DebtorTransaction):
    """
    Interest charged on overdue accounts
    """
    interest_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Interest rate % used"
    )
    
    period_from = models.PositiveSmallIntegerField(
        help_text="From which ageing period (1=30days, 2=60days)"
    )
    
    class Meta:
        db_table = 'interest_charges'
    
    def save(self, *args, **kwargs):
        self.transaction_type = 'INT'
        
        if not self.transaction_number:
            last_int = InterestCharge.objects.order_by('-id').first()
            if last_int and last_int.transaction_number:
                try:
                    last_num = int(last_int.transaction_number.split('-')[-1])
                    self.transaction_number = f"INT-{last_num + 1:06d}"
                except:
                    self.transaction_number = f"INT-000001"
            else:
                self.transaction_number = f"INT-000001"
        
        super().save(*args, **kwargs)