"""
CREDITORS APP - Django Models
Complete supplier/creditor management models

LOCATION: accpick_project/creditors/models.py

Models in this file:
- Creditor (supplier account)
- GoodsReceivedNote (stock received from supplier)
- GRNLineItem
- CreditorInvoice (expense invoice from supplier)
- CreditorInvoiceLineItem
- CreditorCreditNote (credit from supplier)
- CreditorCreditNoteLineItem
- CreditorPayment (payment to supplier)
- CreditorJournal (debit/credit adjustments)
- CreditorOpenItem (for open item accounting)
- OpenItemAllocation (payment allocations)
- RFC (Return For Credit to supplier)
- RFCLineItem
- CreditorTransactionLine (generic line item for transactions)
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from decimal import Decimal
from apps.settings.models import (
    ExpenseCategory,
    TaxCode,
    CreditTerms,
    PaymentMethod,
    TimeStampedModel,
    ActiveModel,
    SalesArea,
    PostingStatusMixin,
    VATMixin
)

User = get_user_model()


# ============================================================================
# CREDITOR (SUPPLIER) ACCOUNT MODEL
# ============================================================================

class Creditor(TimeStampedModel, ActiveModel):
    """
    Supplier/Creditor account
    """
    
    ACCOUNT_CATEGORY_CHOICES = [
        ('BBF', 'Balance Brought Forward'),
        ('OI', 'Open Item'),
    ]
    
    # === USER INPUT FIELDS ===
    
    supplier_number = models.CharField(
        max_length=20,
        unique=True,
        help_text="Supplier account number"
    )
    name = models.CharField(max_length=200)
    
    # Contact
    contact_person = models.CharField(max_length=100, blank=True)
    telephone = models.CharField(max_length=20, blank=True)
    fax = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    
    # Physical address
    physical_address_line1 = models.CharField(max_length=100, blank=True)
    physical_address_line2 = models.CharField(max_length=100, blank=True)
    physical_city = models.CharField(max_length=50, blank=True)
    physical_province = models.CharField(max_length=50, blank=True)
    physical_code = models.CharField(max_length=10, blank=True)
    
    # Postal address
    postal_address_line1 = models.CharField(max_length=100, blank=True)
    postal_address_line2 = models.CharField(max_length=100, blank=True)
    postal_city = models.CharField(max_length=50, blank=True)
    postal_province = models.CharField(max_length=50, blank=True)
    postal_code = models.CharField(max_length=10, blank=True)
    
    # Account settings
    our_account_number = models.CharField(
        max_length=50,
        blank=True,
        help_text="Our account number with this supplier"
    )
    credit_terms = models.ForeignKey(
        CreditTerms,
        on_delete=models.PROTECT,
        related_name='creditors'
    )
    account_category = models.CharField(
        max_length=10,
        choices=ACCOUNT_CATEGORY_CHOICES,
        default='BBF'
    )
    
    # Sales area tracking
    sales_area = models.ForeignKey(
        SalesArea,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='suppliers',
        help_text="Sales area/territory for supplier"
    )
    
    update_selling_price_on_receipt = models.BooleanField(
        default=True,
        help_text="Auto-update selling prices when receiving stock"
    )
    
    prompt_payment_discount_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    # Banking details
    bank_name = models.CharField(max_length=100, blank=True)
    branch_code = models.CharField(max_length=20, blank=True)
    account_number = models.CharField(max_length=50, blank=True)
    
    # === SYSTEM GENERATED FIELDS ===
    
    # CRITICAL: Balance Brought Forward (opening balance from previous period)
    balance_brought_forward = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        editable=False,
        help_text="Opening balance from previous period (SUPBALBFWD from legacy)"
    )
    
    current_balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        editable=False
    )
    balance_current = models.DecimalField(max_digits=15, decimal_places=2, default=0, editable=False)
    balance_30_days = models.DecimalField(max_digits=15, decimal_places=2, default=0, editable=False)
    balance_60_days = models.DecimalField(max_digits=15, decimal_places=2, default=0, editable=False)
    balance_90_days = models.DecimalField(max_digits=15, decimal_places=2, default=0, editable=False)
    balance_120_days = models.DecimalField(max_digits=15, decimal_places=2, default=0, editable=False)
    balance_150_days = models.DecimalField(max_digits=15, decimal_places=2, default=0, editable=False)
    balance_180_days = models.DecimalField(max_digits=15, decimal_places=2, default=0, editable=False)
    
    last_paid_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0, editable=False)
    last_paid_date = models.DateField(null=True, blank=True, editable=False)
    
    purchases_mtd = models.DecimalField(max_digits=15, decimal_places=2, default=0, editable=False)
    purchases_ytd = models.DecimalField(max_digits=15, decimal_places=2, default=0, editable=False)
    
    class Meta:
        db_table = 'creditors'
        ordering = ['supplier_number']
        indexes = [
            models.Index(fields=['supplier_number']),
            models.Index(fields=['name']),
            models.Index(fields=['is_active']),
            models.Index(fields=['sales_area']),
        ]
        verbose_name = 'Creditor'
        verbose_name_plural = 'Creditors'
    
    def __str__(self):
        return f"{self.supplier_number} - {self.name}"
    
    def clean(self):
        """Validate creditor data"""
        super().clean()
        if not self.name or not self.name.strip():
            raise ValidationError({'name': 'Creditor name is required'})
    
    def save(self, *args, **kwargs):
        """Override save to validate and calculate current balance"""
        self.full_clean()
        self.current_balance = (
            self.balance_current + self.balance_30_days + self.balance_60_days +
            self.balance_90_days + self.balance_120_days + self.balance_150_days +
            self.balance_180_days
        )
        super().save(*args, **kwargs)
    
    def recalculate_aged_balances(self):
        """
        Recalculate aged balances from all open items based on due dates.
        This should be called after transactions are posted or as part of period closing.
        
        BUSINESS LOGIC:
        - Current: Due date <= today - 0 days
        - 30 Days: Due date > today - 30 days AND <= today - 0 days
        - 60 Days: Due date > today - 60 days AND <= today - 30 days
        - etc.
        """
        from django.utils import timezone
        from datetime import timedelta
        
        today = timezone.now().date()
        
        # Reset all aging buckets
        self.balance_current = 0
        self.balance_30_days = 0
        self.balance_60_days = 0
        self.balance_90_days = 0
        self.balance_120_days = 0
        self.balance_150_days = 0
        self.balance_180_days = 0
        
        # Get all unpaid open items for this creditor
        open_items = self.open_items.filter(is_fully_allocated=False)
        
        for item in open_items:
            if not item.due_date:
                # If no due date, classify as current
                self.balance_current += item.balance_due
                continue
            
            days_overdue = (today - item.due_date).days
            
            if days_overdue <= 0:
                self.balance_current += item.balance_due
            elif days_overdue <= 30:
                self.balance_30_days += item.balance_due
            elif days_overdue <= 60:
                self.balance_60_days += item.balance_due
            elif days_overdue <= 90:
                self.balance_90_days += item.balance_due
            elif days_overdue <= 120:
                self.balance_120_days += item.balance_due
            elif days_overdue <= 150:
                self.balance_150_days += item.balance_due
            else:
                self.balance_180_days += item.balance_due
        
        # Recalculate total
        self.current_balance = (
            self.balance_current + self.balance_30_days + self.balance_60_days +
            self.balance_90_days + self.balance_120_days + self.balance_150_days +
            self.balance_180_days
        )
        
        self.save()


# ============================================================================
# CREDITOR TRANSACTION BASE
# ============================================================================

class CreditorTransaction(PostingStatusMixin, TimeStampedModel):
    """Base for all creditor transactions (abstract)"""
    
    TRANSACTION_TYPE_CHOICES = [
        ('GRN', 'Goods Received Note'),
        ('INV', 'Expense Invoice'),
        ('CN', 'Credit Note'),
        ('PAY', 'Payment'),
        ('DJ', 'Debit Journal'),
        ('CJ', 'Credit Journal'),
    ]
    
    creditor = models.ForeignKey(
        Creditor,
        on_delete=models.PROTECT,
        related_name='%(class)s_set'
    )
    
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPE_CHOICES)
    transaction_number = models.CharField(max_length=20, unique=True)
    transaction_date = models.DateField()
    
    # CRITICAL: Due date for aged balance calculations (from legacy SDUEDATE)
    due_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date invoice/GRN is due; used for aged balance calculations"
    )
    
    transaction_reference = models.CharField(max_length=50, blank=True)
    additional_reference = models.CharField(max_length=200, blank=True)
    
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    class Meta:
        abstract = True
        ordering = ['-transaction_date', '-transaction_number']
    
    def clean(self):
        """Validate transaction data"""
        super().clean()
        # Validate due_date >= transaction_date
        if self.due_date and self.transaction_date:
            if self.due_date < self.transaction_date:
                raise ValidationError(
                    {'due_date': 'Due date must be on or after transaction date'}
                )
    
    def get_age_in_days(self):
        """Calculate number of days from due date to today"""
        if not self.due_date:
            return None
        from django.utils import timezone
        return (timezone.now().date() - self.due_date).days
    
    def get_age_bucket(self):
        """Determine which aging bucket this transaction falls into"""
        age = self.get_age_in_days()
        if age is None:
            return None
        if age <= 30:
            return 'current'
        elif age <= 60:
            return '30'
        elif age <= 90:
            return '60'
        elif age <= 120:
            return '90'
        elif age <= 150:
            return '120'
        else:
            return '150'


# ============================================================================
# GOODS RECEIVED NOTE (GRN)
# ============================================================================

class GoodsReceivedNote(CreditorTransaction):
    """
    Stock received from supplier
    """
    
    supplier_invoice_number = models.CharField(
        max_length=50,
        help_text="Supplier's invoice number"
    )
    
    INCLUSIVE_EXCLUSIVE_CHOICES = [
        ('INC', 'Inclusive of VAT'),
        ('EXC', 'Exclusive of VAT'),
    ]
    inclusive_exclusive = models.CharField(
        max_length=3,
        choices=INCLUSIVE_EXCLUSIVE_CHOICES,
        default='EXC'
    )
    
    surcharge_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        help_text="E.g., transport, insurance (exclusive VAT)"
    )
    
    # Calculated totals
    subtotal = models.DecimalField(max_digits=15, decimal_places=2, default=0, editable=False)
    total_vat = models.DecimalField(max_digits=15, decimal_places=2, default=0, editable=False)
    total_quantity = models.DecimalField(max_digits=15, decimal_places=2, default=0, editable=False)
    
    # Ageing (BBF)
    age_current = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    age_30 = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    age_60 = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    age_90 = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    age_120 = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    age_150 = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    age_180 = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    class Meta:
        db_table = 'goods_received_notes'
        verbose_name = 'Goods Received Note'
        verbose_name_plural = 'Goods Received Notes'
    
    def save(self, *args, **kwargs):
        self.transaction_type = 'GRN'
        if not self.transaction_number:
            self.transaction_number = self._generate_number()
        # Set due_date based on credit terms if not already set
        if not self.due_date and self.creditor.credit_terms:
            from datetime import timedelta
            self.due_date = self.transaction_date + timedelta(days=self.creditor.credit_terms.days)
        super().save(*args, **kwargs)
    
    def _generate_number(self):
        last = GoodsReceivedNote.objects.order_by('-id').first()
        if last and last.transaction_number:
            try:
                num = int(last.transaction_number.split('-')[-1])
                return f"GRN-{num + 1:06d}"
            except:
                pass
        return "GRN-000001"
    
    def __str__(self):
        return f"{self.transaction_number} - {self.creditor.name}"


class GRNLineItem(TimeStampedModel):
    """Line items on GRN"""
    
    grn = models.ForeignKey(
        GoodsReceivedNote,
        on_delete=models.CASCADE,
        related_name='line_items'
    )
    line_number = models.PositiveSmallIntegerField(default=1)
    
    stock_item = models.ForeignKey(
        'stock_control.StockItem',
        on_delete=models.PROTECT,
        related_name='grn_lines'
    )
    quantity_received = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    unit_cost = models.DecimalField(max_digits=15, decimal_places=2)
    tax_code = models.ForeignKey(TaxCode, on_delete=models.PROTECT)
    
    # Calculated
    previous_cost = models.DecimalField(max_digits=15, decimal_places=2, editable=False)
    line_subtotal = models.DecimalField(max_digits=15, decimal_places=2, editable=False)
    tax_amount = models.DecimalField(max_digits=15, decimal_places=2, editable=False)
    line_total = models.DecimalField(max_digits=15, decimal_places=2, editable=False)
    
    class Meta:
        db_table = 'grn_line_items'
        ordering = ['line_number']
        unique_together = [['grn', 'line_number']]
    
    def save(self, *args, **kwargs):
        if not self.previous_cost:
            self.previous_cost = self.stock_item.cost_price
        
        self.line_subtotal = self.quantity_received * self.unit_cost
        self.tax_amount = self.line_subtotal * (self.tax_code.rate / 100)
        self.line_total = self.line_subtotal + self.tax_amount
        super().save(*args, **kwargs)


# ============================================================================
# CREDITOR INVOICE (Expenses)
# ============================================================================

class CreditorInvoice(CreditorTransaction):
    """
    Invoice for expenses (not stock)
    E.g., electricity, telephone, rent
    Maps to SUPEXPT in legacy system
    """
    
    supplier_invoice_number = models.CharField(max_length=50)
    
    INCLUSIVE_EXCLUSIVE_CHOICES = [
        ('INC', 'Inclusive of VAT'),
        ('EXC', 'Exclusive of VAT'),
    ]
    inclusive_exclusive = models.CharField(
        max_length=3,
        choices=INCLUSIVE_EXCLUSIVE_CHOICES,
        default='INC'
    )
    
    # Station/Area reference (SOURCE field)
    station_no_area = models.CharField(
        max_length=2,
        blank=True,
        help_text="Station No. / Area reference"
    )
    
    # Related GRN if applicable
    related_grn = models.ForeignKey(
        GoodsReceivedNote,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='related_expense_invoices',
        help_text="Goods Received Note number if applicable"
    )
    
    subtotal = models.DecimalField(max_digits=15, decimal_places=2, default=0, editable=False)
    total_vat = models.DecimalField(max_digits=15, decimal_places=2, default=0, editable=False)
    
    # Ageing
    age_current = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    age_30 = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    age_60 = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    age_90 = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    age_120 = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    age_150 = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    age_180 = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    class Meta:
        db_table = 'creditor_invoices'
        verbose_name = 'Creditor Invoice'
        verbose_name_plural = 'Creditor Invoices'
    
    def save(self, *args, **kwargs):
        self.transaction_type = 'INV'
        if not self.transaction_number:
            last = CreditorInvoice.objects.order_by('-id').first()
            if last and last.transaction_number:
                try:
                    num = int(last.transaction_number.split('-')[-1])
                    self.transaction_number = f"SUPINV-{num + 1:06d}"
                except:
                    self.transaction_number = "SUPINV-000001"
            else:
                self.transaction_number = "SUPINV-000001"
        # Set due_date based on credit terms if not already set
        if not self.due_date and self.creditor.credit_terms:
            from datetime import timedelta
            self.due_date = self.transaction_date + timedelta(days=self.creditor.credit_terms.days)
        super().save(*args, **kwargs)


class CreditorInvoiceLineItem(TimeStampedModel):
    """Line items for expense invoices"""
    
    invoice = models.ForeignKey(
        CreditorInvoice,
        on_delete=models.CASCADE,
        related_name='line_items'
    )
    line_number = models.PositiveSmallIntegerField(default=1)
    
    expense_category = models.ForeignKey(
        ExpenseCategory,
        on_delete=models.PROTECT,
        limit_choices_to={'category_type__in': ['BOTH', 'CREDITORS']},
        related_name='creditor_invoice_lines'
    )
    
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    tax_code = models.ForeignKey(TaxCode, on_delete=models.PROTECT)
    
    tax_amount = models.DecimalField(max_digits=15, decimal_places=2, editable=False)
    line_total = models.DecimalField(max_digits=15, decimal_places=2, editable=False)
    
    class Meta:
        db_table = 'creditor_invoice_line_items'
        ordering = ['line_number']
        unique_together = [['invoice', 'line_number']]
    
    def save(self, *args, **kwargs):
        self.tax_amount = self.amount * (self.tax_code.rate / 100)
        self.line_total = self.amount + self.tax_amount
        super().save(*args, **kwargs)


# ============================================================================
# CREDITOR CREDIT NOTE
# ============================================================================

class CreditorCreditNote(CreditorTransaction):
    """Credit note from supplier"""
    
    supplier_credit_note_number = models.CharField(max_length=50)
    
    INCLUSIVE_EXCLUSIVE_CHOICES = [
        ('INC', 'Inclusive of VAT'),
        ('EXC', 'Exclusive of VAT'),
    ]
    inclusive_exclusive = models.CharField(
        max_length=3,
        choices=INCLUSIVE_EXCLUSIVE_CHOICES,
        default='EXC'
    )
    
    original_grn = models.ForeignKey(
        GoodsReceivedNote,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='credit_notes'
    )
    
    subtotal = models.DecimalField(max_digits=15, decimal_places=2, default=0, editable=False)
    total_vat = models.DecimalField(max_digits=15, decimal_places=2, default=0, editable=False)
    
    # Ageing
    age_current = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    age_30 = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    age_60 = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    age_90 = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    age_120 = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    age_150 = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    age_180 = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    class Meta:
        db_table = 'creditor_credit_notes'
        verbose_name = 'Creditor Credit Note'
        verbose_name_plural = 'Creditor Credit Notes'
    
    def save(self, *args, **kwargs):
        self.transaction_type = 'CN'
        if not self.transaction_number:
            last = CreditorCreditNote.objects.order_by('-id').first()
            if last and last.transaction_number:
                try:
                    num = int(last.transaction_number.split('-')[-1])
                    self.transaction_number = f"SUPCN-{num + 1:06d}"
                except:
                    self.transaction_number = "SUPCN-000001"
            else:
                self.transaction_number = "SUPCN-000001"
        # Set due_date based on credit terms if not already set
        if not self.due_date and self.creditor.credit_terms:
            from datetime import timedelta
            self.due_date = self.transaction_date + timedelta(days=self.creditor.credit_terms.days)
        super().save(*args, **kwargs)


class CreditorCreditNoteLineItem(TimeStampedModel):
    """Line items for credit notes"""
    
    credit_note = models.ForeignKey(
        CreditorCreditNote,
        on_delete=models.CASCADE,
        related_name='line_items'
    )
    line_number = models.PositiveSmallIntegerField(default=1)
    
    stock_item = models.ForeignKey(
        'stock_control.StockItem',
        on_delete=models.PROTECT,
        related_name='creditor_cn_lines'
    )
    quantity_returned = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    unit_cost = models.DecimalField(max_digits=15, decimal_places=2)
    tax_code = models.ForeignKey(TaxCode, on_delete=models.PROTECT)
    
    line_subtotal = models.DecimalField(max_digits=15, decimal_places=2, editable=False)
    tax_amount = models.DecimalField(max_digits=15, decimal_places=2, editable=False)
    line_total = models.DecimalField(max_digits=15, decimal_places=2, editable=False)
    
    class Meta:
        db_table = 'creditor_credit_note_line_items'
        ordering = ['line_number']
        unique_together = [['credit_note', 'line_number']]
    
    def save(self, *args, **kwargs):
        self.line_subtotal = self.quantity_returned * self.unit_cost
        self.tax_amount = self.line_subtotal * (self.tax_code.rate / 100)
        self.line_total = self.line_subtotal + self.tax_amount
        super().save(*args, **kwargs)


# ============================================================================
# CREDITOR PAYMENT
# ============================================================================

class CreditorPayment(CreditorTransaction):
    """Payment to supplier"""
    
    amount_due = models.DecimalField(max_digits=15, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=15, decimal_places=2)
    
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
    
    payment_method = models.ForeignKey(
        PaymentMethod,
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )
    
    is_unallocated = models.BooleanField(default=False)
    
    # Ageing
    age_current = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    age_30 = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    age_60 = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    age_90 = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    age_120 = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    age_150 = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    age_180 = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    class Meta:
        db_table = 'creditor_payments'
        verbose_name = 'Creditor Payment'
        verbose_name_plural = 'Creditor Payments'
    
    def save(self, *args, **kwargs):
        self.transaction_type = 'PAY'
        if not self.transaction_number:
            last = CreditorPayment.objects.order_by('-id').first()
            if last and last.transaction_number:
                try:
                    num = int(last.transaction_number.split('-')[-1])
                    self.transaction_number = f"SUPPAY-{num + 1:06d}"
                except:
                    self.transaction_number = "SUPPAY-000001"
            else:
                self.transaction_number = "SUPPAY-000001"
        
        self.settlement_discount_amount = self.amount_due - self.amount_paid
        if self.amount_due > 0:
            self.settlement_discount_percent = (self.settlement_discount_amount / self.amount_due) * 100
        
        self.total_amount = self.amount_paid
        super().save(*args, **kwargs)


# ============================================================================
# CREDITOR JOURNAL
# ============================================================================

class CreditorJournal(CreditorTransaction):
    """Journal adjustment"""
    
    JOURNAL_TYPE_CHOICES = [
        ('DEBIT', 'Debit Journal'),
        ('CREDIT', 'Credit Journal'),
    ]
    journal_type = models.CharField(max_length=10, choices=JOURNAL_TYPE_CHOICES)
    journal_amount = models.DecimalField(max_digits=15, decimal_places=2)
    
    # Ageing
    age_current = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    age_30 = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    age_60 = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    age_90 = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    age_120 = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    age_150 = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    age_180 = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    class Meta:
        db_table = 'creditor_journals'
        verbose_name = 'Creditor Journal'
        verbose_name_plural = 'Creditor Journals'
    
    def save(self, *args, **kwargs):
        self.transaction_type = 'DJ' if self.journal_type == 'DEBIT' else 'CJ'
        self.total_amount = self.journal_amount
        
        if not self.transaction_number:
            prefix = 'SUPDJ' if self.journal_type == 'DEBIT' else 'SUPCJ'
            last = CreditorJournal.objects.filter(journal_type=self.journal_type).order_by('-id').first()
            if last and last.transaction_number:
                try:
                    num = int(last.transaction_number.split('-')[-1])
                    self.transaction_number = f"{prefix}-{num + 1:06d}"
                except:
                    self.transaction_number = f"{prefix}-000001"
            else:
                self.transaction_number = f"{prefix}-000001"
        
        super().save(*args, **kwargs)


# ============================================================================
# OPEN ITEM MODELS
# ============================================================================

class CreditorOpenItem(models.Model):
    """Open items for open item accounting. Maps to SUPOPEN in legacy system"""
    
    creditor = models.ForeignKey(Creditor, on_delete=models.CASCADE, related_name='open_items')
    
    grn = models.ForeignKey(GoodsReceivedNote, on_delete=models.CASCADE, null=True, blank=True, related_name='open_items')
    invoice = models.ForeignKey(CreditorInvoice, on_delete=models.CASCADE, null=True, blank=True, related_name='open_items')
    credit_note = models.ForeignKey(CreditorCreditNote, on_delete=models.CASCADE, null=True, blank=True, related_name='open_items')
    journal = models.ForeignKey(CreditorJournal, on_delete=models.CASCADE, null=True, blank=True, related_name='open_items')
    
    transaction_date = models.DateField()
    
    # ADDED: Due date for aging (from transaction)
    due_date = models.DateField(
        null=True,
        blank=True,
        help_text="Due date for aged balance calculation"
    )
    
    transaction_type = models.CharField(max_length=10)
    transaction_number = models.CharField(max_length=20)
    
    original_amount = models.DecimalField(max_digits=15, decimal_places=2)
    balance_due = models.DecimalField(max_digits=15, decimal_places=2)
    
    age_period = models.PositiveSmallIntegerField(default=0)
    ageing_flag = models.CharField(
        max_length=1,
        blank=True,
        help_text="Ageing flag (AGEGLAG field from legacy system)"
    )
    is_fully_allocated = models.BooleanField(default=False)
    
    # ADDED: Tracking and validation
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'creditor_open_items'
        ordering = ['transaction_date']
        verbose_name = 'Creditor Open Item'
        verbose_name_plural = 'Creditor Open Items'
        # ADDED: Unique constraint  to prevent duplicate open items
        unique_together = [['creditor', 'transaction_number', 'transaction_type']]
        indexes = [
            models.Index(fields=['creditor', '-transaction_date']),
            models.Index(fields=['is_fully_allocated']),
        ]
    
    def clean(self):
        """Validate open item data"""
        super().clean()
        # Validate that only one transaction type is linked
        transaction_links = [self.grn, self.invoice, self.credit_note, self.journal]
        if sum(1 for x in transaction_links if x is not None) != 1:
            raise ValidationError(
                'Exactly one transaction type (GRN, Invoice, Credit Note, or Journal) must be linked'
            )
        # Validate balance_due <= original_amount
        if self.balance_due > self.original_amount:
            raise ValidationError(
                {'balance_due': 'Balance due cannot exceed original amount'}
            )
    
    def get_age_in_days(self):
        """Get number of days overdue"""
        if not self.due_date:
            return None
        from django.utils import timezone
        return (timezone.now().date() - self.due_date).days
    
    def get_age_bucket(self):
        """Get aging bucket for this item"""
        age = self.get_age_in_days()
        if age is None:
            return 'current'
        if age <= 0:
            return 'current'
        elif age <= 30:
            return '30'
        elif age <= 60:
            return '60'
        elif age <= 90:
            return '90'
        elif age <= 120:
            return '120'
        elif age <= 150:
            return '150'
        else:
            return '180'


class OpenItemAllocation(models.Model):
    """Payment allocations to open items"""
    
    payment = models.ForeignKey(CreditorPayment, on_delete=models.CASCADE, related_name='allocations')
    open_item = models.ForeignKey(CreditorOpenItem, on_delete=models.CASCADE, related_name='allocations')
    
    amount_paid = models.DecimalField(max_digits=15, decimal_places=2)
    settlement_discount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    allocated_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'creditor_open_item_allocations'
        verbose_name = 'Open Item Allocation'
        verbose_name_plural = 'Open Item Allocations'
        indexes = [
            models.Index(fields=['payment']),
            models.Index(fields=['open_item']),
        ]
    
    def clean(self):
        """Validate allocation does not exceed balance due"""
        super().clean()
        # Check if total allocations would exceed balance_due
        total_allocated = self.open_item.allocations.exclude(
            pk=self.pk
        ).aggregate(
            total=models.Sum('amount_paid') + models.Sum('settlement_discount')
        )['total'] or Decimal('0')
        
        total_with_new = total_allocated + self.amount_paid + self.settlement_discount
        
        if total_with_new > self.open_item.balance_due:
            raise ValidationError(
                f'Total allocation ({total_with_new}) exceeds balance due ({self.open_item.balance_due})'
            )


# ============================================================================
# RFC (RETURN FOR CREDIT)
# ============================================================================

class RFC(TimeStampedModel):
    """Return for Credit to supplier"""
    
    creditor = models.ForeignKey(Creditor, on_delete=models.PROTECT, related_name='rfcs')
    rfc_number = models.CharField(max_length=20, unique=True)
    return_date = models.DateField()
    
    # ADDED: Date tracking for RFC lifecycle (from legacy SUPMAST)
    date_sent = models.DateField(
        null=True,
        blank=True,
        help_text="Date RFC was sent to supplier (DATESENT)"
    )
    date_returned = models.DateField(
        null=True,
        blank=True,
        help_text="Date credit note was received from supplier (DATERETN)"
    )
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending with Supplier'),
        ('CREDITED', 'Credit Note Received'),
        ('REPLACED', 'Stock Replaced'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    total_value_exclusive = models.DecimalField(max_digits=15, decimal_places=2, default=0, editable=False)
    total_value_inclusive = models.DecimalField(max_digits=15, decimal_places=2, default=0, editable=False)
    
    class Meta:
        db_table = 'rfcs'
        verbose_name = 'RFC (Return For Credit)'
        verbose_name_plural = 'RFCs (Returns For Credit)'
    
    def __str__(self):
        return f"RFC-{self.rfc_number} - {self.creditor.name}"


class RFCLineItem(TimeStampedModel):
    """Line items on RFC"""
    
    rfc = models.ForeignKey(RFC, on_delete=models.CASCADE, related_name='line_items')
    line_number = models.PositiveSmallIntegerField(default=1)
    
    stock_item = models.ForeignKey('stock_control.StockItem', on_delete=models.PROTECT, related_name='rfc_lines')
    quantity_returned = models.DecimalField(max_digits=15, decimal_places=2)
    
    # ADDED: Quantity for credit (may differ from returned qty - from legacy QTYCRED)
    quantity_credited = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Quantity approved for credit (QTYCRED) - may differ from returned"
    )
    
    unit_cost = models.DecimalField(max_digits=15, decimal_places=2, editable=False)
    tax_code = models.ForeignKey(TaxCode, on_delete=models.PROTECT)
    
    # ADDED: Original transaction tracking (from legacy SUPCRTRN)
    original_transaction_type = models.CharField(
        max_length=2,
        blank=True,
        help_text="Type of original purchase transaction (TYPE)"
    )
    original_transaction_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date of original purchase (PURCHDATE)"
    )
    original_transaction_time = models.TimeField(
        null=True,
        blank=True,
        help_text="Time of original purchase (TIME)"
    )
    
    # ADDED: Supplier reference tracking
    supplier_reference_number = models.CharField(
        max_length=20,
        blank=True,
        help_text="Supplier's reference number (SUPREFNO)"
    )
    
    reason = models.TextField(blank=True)
    
    line_value_exclusive = models.DecimalField(max_digits=15, decimal_places=2, editable=False)
    tax_amount = models.DecimalField(max_digits=15, decimal_places=2, editable=False)
    line_value_inclusive = models.DecimalField(max_digits=15, decimal_places=2, editable=False)
    
    class Meta:
        db_table = 'rfc_line_items'
        ordering = ['line_number']
        unique_together = [['rfc', 'line_number']]
    
    def save(self, *args, **kwargs):
        if not self.unit_cost:
            self.unit_cost = self.stock_item.cost_price
        
        self.line_value_exclusive = self.quantity_returned * self.unit_cost
        self.tax_amount = self.line_value_exclusive * (self.tax_code.rate / 100)
        self.line_value_inclusive = self.line_value_exclusive + self.tax_amount
        super().save(*args, **kwargs)


# ============================================================================
# CREDITOR TRANSACTION LINE ITEM (Generic)
# ============================================================================

class CreditorTransactionLine(TimeStampedModel):
    """Generic line item for creditor transactions using ContentType for polymorphism"""
    
    # Generic foreign key to link to any CreditorTransaction subclass
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    transaction = GenericForeignKey('content_type', 'object_id')
    
    line_number = models.PositiveSmallIntegerField(default=1)
    
    stock_item = models.ForeignKey(
        'stock_control.StockItem',
        on_delete=models.PROTECT,
        related_name='transaction_lines',
        null=True,
        blank=True
    )
    
    expense_category = models.ForeignKey(
        ExpenseCategory,
        on_delete=models.PROTECT,
        related_name='transaction_lines',
        null=True,
        blank=True
    )
    
    quantity = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )
    
    unit_cost = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )
    
    tax_code = models.ForeignKey(
        TaxCode,
        on_delete=models.PROTECT,
        related_name='transaction_lines'
    )
    
    tax_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        editable=False
    )
    
    amount_exclusive = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )
    
    amount_inclusive = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        editable=False
    )
    
    class Meta:
        db_table = 'creditor_transaction_lines'
        ordering = ['line_number']
    
    def save(self, *args, **kwargs):
        if self.amount_exclusive:
            self.tax_amount = self.amount_exclusive * (self.tax_code.rate / 100)
            self.amount_inclusive = self.amount_exclusive + self.tax_amount
        elif self.quantity and self.unit_cost:
            self.amount_exclusive = self.quantity * self.unit_cost
            self.tax_amount = self.amount_exclusive * (self.tax_code.rate / 100)
            self.amount_inclusive = self.amount_exclusive + self.tax_amount
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        if self.stock_item:
            return f"Line {self.line_number} - {self.stock_item.stock_code}"
        elif self.expense_category:
            return f"Line {self.line_number} - {self.expense_category.category_name}"
        return f"Line {self.line_number}"


# ============================================================================
# EXPENSE CATEGORY MONTHLY BALANCE
# ============================================================================

class ExpenseCategoryMonthlyBalance(TimeStampedModel):
    """
    Expense Category balances per month
    Maps to SUPEXP in legacy system
    Tracks monthly expenses by category with month-to-date and monthly history
    """
    
    expense_category = models.ForeignKey(
        ExpenseCategory,
        on_delete=models.CASCADE,
        related_name='monthly_balances'
    )
    
    year = models.PositiveIntegerField()
    month = models.PositiveSmallIntegerField(choices=[(i, i) for i in range(1, 13)])
    
    # Month-to-date balances
    expense_mtd = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        help_text="Expense balance month to date (EXPMTD)"
    )
    
    input_vat_mtd = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        help_text="Input VAT month to date (EXPINVAT)"
    )
    
    # Monthly purchase history (EXP1 through EXP12)
    exp_month_1 = models.DecimalField(max_digits=15, decimal_places=2, default=0, help_text="January purchases")
    exp_month_2 = models.DecimalField(max_digits=15, decimal_places=2, default=0, help_text="February purchases")
    exp_month_3 = models.DecimalField(max_digits=15, decimal_places=2, default=0, help_text="March purchases")
    exp_month_4 = models.DecimalField(max_digits=15, decimal_places=2, default=0, help_text="April purchases")
    exp_month_5 = models.DecimalField(max_digits=15, decimal_places=2, default=0, help_text="May purchases")
    exp_month_6 = models.DecimalField(max_digits=15, decimal_places=2, default=0, help_text="June purchases")
    exp_month_7 = models.DecimalField(max_digits=15, decimal_places=2, default=0, help_text="July purchases")
    exp_month_8 = models.DecimalField(max_digits=15, decimal_places=2, default=0, help_text="August purchases")
    exp_month_9 = models.DecimalField(max_digits=15, decimal_places=2, default=0, help_text="September purchases")
    exp_month_10 = models.DecimalField(max_digits=15, decimal_places=2, default=0, help_text="October purchases")
    exp_month_11 = models.DecimalField(max_digits=15, decimal_places=2, default=0, help_text="November purchases")
    exp_month_12 = models.DecimalField(max_digits=15, decimal_places=2, default=0, help_text="December purchases")
    
    class Meta:
        db_table = 'expense_category_monthly_balances'
        ordering = ['-year', '-month']
        unique_together = [['expense_category', 'year', 'month']]
        verbose_name = 'Expense Category Monthly Balance'
        verbose_name_plural = 'Expense Category Monthly Balances'
        indexes = [
            models.Index(fields=['expense_category', 'year', 'month']),
            models.Index(fields=['year', 'month']),
        ]
    
    def __str__(self):
        return f"{self.expense_category.category_name} - {self.year}-{self.month:02d}"
    
    def get_monthly_values(self):
        """Return all 12 months as list for iteration"""
        return [
            self.exp_month_1, self.exp_month_2, self.exp_month_3, self.exp_month_4,
            self.exp_month_5, self.exp_month_6, self.exp_month_7, self.exp_month_8,
            self.exp_month_9, self.exp_month_10, self.exp_month_11, self.exp_month_12
        ]


# ============================================================================
# OPEN ITEM AUDIT
# ============================================================================

class OpenItemAudit(TimeStampedModel):
    """
    Open item audit file for tracking changes to open items
    Maps to SUPOAUD in legacy system
    """
    
    creditor = models.ForeignKey(
        Creditor,
        on_delete=models.CASCADE,
        related_name='open_item_audits'
    )
    
    # Original transaction reference
    transaction_number = models.CharField(
        max_length=20,
        help_text="Original transaction number (TRANO)"
    )
    transaction_type = models.CharField(
        max_length=10,
        help_text="Original transaction type (TYPE)"
    )
    
    # Current transaction being processed
    this_transaction_type = models.CharField(
        max_length=10,
        help_text="This transaction type (THISTYPE)"
    )
    this_transaction_number = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        help_text="This transaction number (THISTRAN)"
    )
    
    transaction_date = models.DateField(
        help_text="Transaction date (DATE)"
    )
    
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Amount (AMOUNT)"
    )
    
    audit_timestamp = models.DateTimeField(
        auto_now_add=True,
        editable=False,
        help_text="When this audit record was created"
    )
    
    audit_notes = models.TextField(
        blank=True,
        help_text="Additional audit notes"
    )
    
    class Meta:
        db_table = 'open_item_audits'
        ordering = ['-audit_timestamp']
        verbose_name = 'Open Item Audit'
        verbose_name_plural = 'Open Item Audits'
        indexes = [
            models.Index(fields=['creditor', '-audit_timestamp']),
            models.Index(fields=['transaction_number']),
        ]
    
    def __str__(self):
        return f"{self.creditor.supplier_number} - {self.transaction_number} ({self.transaction_date})"