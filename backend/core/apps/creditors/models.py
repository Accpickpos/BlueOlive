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
- SupplierMonthlyPurchase (monthly purchase statistics)
- ExpenseMonthlyTotal (monthly expense totals)
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
    SalesArea
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
    account_number = models.CharField(
        max_length=20,
        unique=True,
        help_text="Account number (alias for supplier_number)"
    )
    name = models.CharField(max_length=200)
    short_name = models.CharField(max_length=50, blank=True, help_text="Short name for display")
    
    # Contact
    contact_person = models.CharField(max_length=100, blank=True)
    telephone = models.CharField(max_length=20, blank=True)
    telephone1 = models.CharField(max_length=20, blank=True, help_text="Primary telephone")
    telephone2 = models.CharField(max_length=20, blank=True, help_text="Secondary telephone")
    fax = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    
    # Physical address
    physical_address_line1 = models.CharField(max_length=100, blank=True)
    physical_address_line2 = models.CharField(max_length=100, blank=True)
    physical_address_line3 = models.CharField(max_length=100, blank=True)
    physical_city = models.CharField(max_length=50, blank=True)
    physical_province = models.CharField(max_length=50, blank=True)
    physical_code = models.CharField(max_length=10, blank=True)
    physical_postal_code = models.CharField(max_length=10, blank=True, help_text="Physical postal code")
    
    # Postal address
    postal_address_line1 = models.CharField(max_length=100, blank=True)
    postal_address_line2 = models.CharField(max_length=100, blank=True)
    postal_address_line3 = models.CharField(max_length=100, blank=True)
    postal_city = models.CharField(max_length=50, blank=True)
    postal_province = models.CharField(max_length=50, blank=True)
    postal_code = models.CharField(max_length=10, blank=True)
    postal_postal_code = models.CharField(max_length=10, blank=True, help_text="Postal postal code")
    
    # Account settings
    our_account_number = models.CharField(
        max_length=50,
        blank=True,
        help_text="Our account number with this supplier"
    )
    account_type = models.CharField(
        max_length=10,
        choices=ACCOUNT_CATEGORY_CHOICES,
        default='BBF',
        help_text="Account type (alias for account_category)"
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
    
    # VAT details
    vat_number = models.CharField(max_length=50, blank=True, help_text="VAT registration number")
    
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
    bank_branch_code = models.CharField(max_length=20, blank=True, help_text="Bank branch code")
    account_number = models.CharField(max_length=50, blank=True)
    bank_account_number = models.CharField(max_length=50, blank=True, help_text="Bank account number")
    
    # === SYSTEM GENERATED FIELDS ===
    
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
    amount_last_paid = models.DecimalField(max_digits=15, decimal_places=2, default=0, editable=False, help_text="Amount last paid (alias)")
    last_paid_date = models.DateField(null=True, blank=True, editable=False)
    date_last_paid = models.DateField(null=True, blank=True, editable=False, help_text="Date last paid (alias)")
    
    purchases_mtd = models.DecimalField(max_digits=15, decimal_places=2, default=0, editable=False)
    purchases_ytd = models.DecimalField(max_digits=15, decimal_places=2, default=0, editable=False)
    
    rfc_outstanding_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0, editable=False)
    
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
    
    def get_total_balance(self):
        """Calculate total balance across all aging periods"""
        return (
            self.balance_current + self.balance_30_days + self.balance_60_days +
            self.balance_90_days + self.balance_120_days + self.balance_150_days +
            self.balance_180_days
        )
    
    def get_total_balance_with_rfc(self):
        """Calculate total balance including RFC outstanding amount"""
        return self.get_total_balance() + self.rfc_outstanding_amount
    
    def get_account_type_display(self):
        """Return readable account type (alias for account_category display)"""
        return self.get_account_category_display()
    
    def get_credit_terms_display(self):
        """Return credit terms display"""
        return str(self.credit_terms) if self.credit_terms else ""
    
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


# ============================================================================
# CREDITOR TRANSACTION BASE
# ============================================================================

class CreditorTransaction(TimeStampedModel):
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
    
    transaction_reference = models.CharField(max_length=50, blank=True)
    additional_reference = models.CharField(max_length=200, blank=True)
    
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    is_posted = models.BooleanField(default=False)
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
        return f"{self.transaction_number} - {self.creditor.name}"


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
    """Open items for open item accounting"""
    
    creditor = models.ForeignKey(Creditor, on_delete=models.CASCADE, related_name='open_items')
    
    grn = models.ForeignKey(GoodsReceivedNote, on_delete=models.CASCADE, null=True, blank=True, related_name='open_items')
    invoice = models.ForeignKey(CreditorInvoice, on_delete=models.CASCADE, null=True, blank=True, related_name='open_items')
    credit_note = models.ForeignKey(CreditorCreditNote, on_delete=models.CASCADE, null=True, blank=True, related_name='open_items')
    journal = models.ForeignKey(CreditorJournal, on_delete=models.CASCADE, null=True, blank=True, related_name='open_items')
    
    transaction_date = models.DateField()
    transaction_type = models.CharField(max_length=10)
    transaction_number = models.CharField(max_length=20)
    
    original_amount = models.DecimalField(max_digits=15, decimal_places=2)
    balance_due = models.DecimalField(max_digits=15, decimal_places=2)
    
    age_period = models.PositiveSmallIntegerField(default=0)
    is_fully_allocated = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'creditor_open_items'
        ordering = ['transaction_date']
        verbose_name = 'Creditor Open Item'
        verbose_name_plural = 'Creditor Open Items'


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


# ============================================================================
# RFC (RETURN FOR CREDIT)
# ============================================================================

class RFC(TimeStampedModel):
    """Return for Credit to supplier"""
    
    creditor = models.ForeignKey(Creditor, on_delete=models.PROTECT, related_name='rfcs')
    rfc_number = models.CharField(max_length=20, unique=True)
    return_date = models.DateField()
    
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
    unit_cost = models.DecimalField(max_digits=15, decimal_places=2, editable=False)
    tax_code = models.ForeignKey(TaxCode, on_delete=models.PROTECT)
    
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
# MONTHLY STATISTICS MODELS
# ============================================================================

class SupplierMonthlyPurchase(TimeStampedModel):
    """Monthly purchase statistics by supplier"""
    
    supplier = models.ForeignKey(
        Creditor,
        on_delete=models.CASCADE,
        related_name='monthly_purchases'
    )
    
    year = models.PositiveSmallIntegerField()
    month = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(12)]
    )
    
    total_purchases = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        editable=False
    )
    
    quantity_purchased = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        editable=False
    )
    
    number_of_transactions = models.PositiveIntegerField(default=0, editable=False)
    
    class Meta:
        db_table = 'supplier_monthly_purchases'
        ordering = ['-year', '-month']
        unique_together = [['supplier', 'year', 'month']]
        verbose_name = 'Supplier Monthly Purchase'
        verbose_name_plural = 'Supplier Monthly Purchases'
        indexes = [
            models.Index(fields=['supplier', 'year', 'month']),
            models.Index(fields=['-year', '-month']),
        ]
    
    def __str__(self):
        return f"{self.supplier.name} - {self.month:02d}/{self.year}"


class ExpenseMonthlyTotal(TimeStampedModel):
    """Monthly expense totals by category"""
    
    expense_category = models.ForeignKey(
        ExpenseCategory,
        on_delete=models.CASCADE,
        related_name='monthly_totals'
    )
    
    year = models.PositiveSmallIntegerField()
    month = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(12)]
    )
    
    total_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        editable=False
    )
    
    total_vat = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        editable=False
    )
    
    number_of_invoices = models.PositiveIntegerField(default=0, editable=False)
    
    class Meta:
        db_table = 'expense_monthly_totals'
        ordering = ['-year', '-month']
        unique_together = [['expense_category', 'year', 'month']]
        verbose_name = 'Expense Monthly Total'
        verbose_name_plural = 'Expense Monthly Totals'
        indexes = [
            models.Index(fields=['expense_category', 'year', 'month']),
            models.Index(fields=['-year', '-month']),
        ]
    
    def __str__(self):
        return f"{self.expense_category.category_name} - {self.month:02d}/{self.year}"