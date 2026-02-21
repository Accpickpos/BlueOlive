# backend/core/apps/creditors/models.py
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
    VATMixin,
)

User = get_user_model()


# ============================================================================
# CREDITOR (SUPPLIER) MASTER
# Maps to: supmast.dbf
# ============================================================================

class Creditor(TimeStampedModel, ActiveModel):
    """Supplier/Creditor account master. Maps to SUPMAST."""

    ACCOUNT_CATEGORY_CHOICES = [
        ('BBF', 'Balance Brought Forward'),
        ('OI',  'Open Item'),
        ('',    'Not Set'),
    ]

    # --- Identification ---
    # DBF: SUPNO N(4) — stored as char to preserve leading formatting; DBF max is 9999
    supplier_number = models.CharField(max_length=4, unique=True, help_text="SUPNO — N(4) in DBF")
    # DBF: SUPNAME C(30)
    name            = models.CharField(max_length=30, help_text="SUPNAME")

    # --- Contact ---
    contact_person = models.CharField(max_length=20, blank=True, help_text="SUPCONT — C(20)")
    telephone      = models.CharField(max_length=15, blank=True, help_text="SUPTEL — C(15)")
    fax            = models.CharField(max_length=15, blank=True, help_text="SUPFAX — C(15)")
    email          = models.EmailField(max_length=60, blank=True, help_text="EMAIL — C(60)")

    # --- Physical address: 3 free-form lines matching SUPADD1/2/3 exactly ---
    physical_address_line1 = models.CharField(max_length=25, blank=True, help_text="SUPADD1 — C(25)")
    physical_address_line2 = models.CharField(max_length=25, blank=True, help_text="SUPADD2 — C(25)")
    physical_address_line3 = models.CharField(max_length=25, blank=True, help_text="SUPADD3 — C(25)")

    # --- Postal address: 3 free-form lines matching SUPPADD1/2/3 exactly ---
    postal_address_line1 = models.CharField(max_length=20, blank=True, help_text="SUPPADD1 — C(20)")
    postal_address_line2 = models.CharField(max_length=20, blank=True, help_text="SUPPADD2 — C(20)")
    postal_address_line3 = models.CharField(max_length=20, blank=True, help_text="SUPPADD3 — C(20)")

    # --- Account settings ---
    our_account_number = models.CharField(max_length=15, blank=True, help_text="SUPOURACC — C(15)")

    # FIX #1: nullable FK + raw-days fallback so import never crashes on missing CreditTerms records
    credit_terms = models.ForeignKey(
        CreditTerms, on_delete=models.PROTECT, related_name='creditors',
        null=True, blank=True,
        help_text="FK to CreditTerms. Null if not yet matched — use payment_terms_days instead."
    )
    payment_terms_days = models.PositiveSmallIntegerField(
        default=30,
        help_text="Raw payment terms days (SUPTERMS). Used when credit_terms FK is not set."
    )

    # DBF: ACCTYPE C(1) — 'B'=BBF, 'O'=Open Item, ' '/''=Not Set
    account_category = models.CharField(
        max_length=4, choices=ACCOUNT_CATEGORY_CHOICES, default='BBF', blank=True,
        help_text="ACCTYPE C(1). Legacy may be blank — treated as BBF."
    )
    # No DBF source for sales_area; Django-only linkage
    sales_area = models.ForeignKey(
        SalesArea, on_delete=models.SET_NULL, null=True, blank=True, related_name='suppliers'
    )
    update_selling_price_on_receipt = models.BooleanField(
        default=False, help_text="UPDSTKSP — auto-update selling prices on GRN"
    )
    prompt_payment_discount_percent = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="SUPDISC"
    )

    # --- Banking ---
    bank_name      = models.CharField(max_length=10, blank=True, help_text="BANK — C(10)")
    branch_code    = models.CharField(max_length=10, blank=True, help_text="BANKCODE — C(10)")
    account_number = models.CharField(max_length=15, blank=True, help_text="BANKACC — C(15)")

    # --- System-generated balances (editable=False) ---
    balance_brought_forward = models.DecimalField(
        max_digits=15, decimal_places=2, default=0, editable=False,
        help_text="SUPBALBFWD"
    )
    # FIX #2: renamed from current_balance → total_outstanding_balance
    total_outstanding_balance = models.DecimalField(
        max_digits=15, decimal_places=2, default=0, editable=False,
        help_text="Sum of all aging buckets (calculated)."
    )
    balance_current  = models.DecimalField(max_digits=15, decimal_places=2, default=0, editable=False, help_text="SUPCRNT")
    balance_30_days  = models.DecimalField(max_digits=15, decimal_places=2, default=0, editable=False, help_text="SUP30")
    balance_60_days  = models.DecimalField(max_digits=15, decimal_places=2, default=0, editable=False, help_text="SUP60")
    balance_90_days  = models.DecimalField(max_digits=15, decimal_places=2, default=0, editable=False, help_text="SUP90")
    balance_120_days = models.DecimalField(max_digits=15, decimal_places=2, default=0, editable=False, help_text="SUP120")
    balance_150_days = models.DecimalField(max_digits=15, decimal_places=2, default=0, editable=False, help_text="SUP150")
    # FIX #12: no legacy source — DBF stops at SUP150; always 0 on import
    balance_180_days = models.DecimalField(
        max_digits=15, decimal_places=2, default=0, editable=False,
        help_text="180+ days. No legacy DBF source (DBF stops at SUP150). Always 0 on import."
    )
    last_paid_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0, editable=False, help_text="SUPPMT")
    last_paid_date   = models.DateField(null=True, blank=True, editable=False, help_text="SUPPMTDATE")
    purchases_mtd    = models.DecimalField(max_digits=15, decimal_places=2, default=0, editable=False, help_text="SUPURCHMTD")
    purchases_ytd    = models.DecimalField(max_digits=15, decimal_places=2, default=0, editable=False, help_text="SUPURCHYTD")

    class Meta:
        db_table = 'creditors'
        ordering = ['supplier_number']
        indexes = [
            models.Index(fields=['supplier_number']),
            models.Index(fields=['name']),
            models.Index(fields=['is_active']),
        ]
        verbose_name = 'Creditor'
        verbose_name_plural = 'Creditors'

    def __str__(self):
        return f"{self.supplier_number} - {self.name}"

    def clean(self):
        super().clean()
        if not self.name or not self.name.strip():
            raise ValidationError({'name': 'Creditor name is required'})

    def save(self, *args, **kwargs):
        self.full_clean()
        self.total_outstanding_balance = (
            self.balance_current  + self.balance_30_days  + self.balance_60_days  +
            self.balance_90_days  + self.balance_120_days + self.balance_150_days +
            self.balance_180_days
        )
        super().save(*args, **kwargs)

    def get_effective_terms_days(self):
        """Return terms in days — FK if set, else raw integer."""
        if self.credit_terms_id:
            return self.credit_terms.days
        return self.payment_terms_days

    def recalculate_aged_balances(self):
        """Recalculate aging buckets from open items. Call after posting or at period close."""
        today = timezone.now().date()
        for attr in ('balance_current', 'balance_30_days', 'balance_60_days',
                     'balance_90_days', 'balance_120_days', 'balance_150_days', 'balance_180_days'):
            setattr(self, attr, Decimal('0'))

        for item in self.open_items.filter(is_fully_allocated=False):
            if not item.due_date:
                self.balance_current += item.balance_due
                continue
            days = (today - item.due_date).days
            if days <= 0:    self.balance_current  += item.balance_due
            elif days <= 30: self.balance_30_days  += item.balance_due
            elif days <= 60: self.balance_60_days  += item.balance_due
            elif days <= 90: self.balance_90_days  += item.balance_due
            elif days <= 120: self.balance_120_days += item.balance_due
            elif days <= 150: self.balance_150_days += item.balance_due
            else:             self.balance_180_days += item.balance_due

        self.save()


# ============================================================================
# ABSTRACT TRANSACTION BASE
# ============================================================================

class CreditorTransaction(PostingStatusMixin, TimeStampedModel):
    """Abstract base for all creditor transaction models."""

    TRANSACTION_TYPE_CHOICES = [
        ('GR', 'Goods Received Note'),   # suptran STYPE='GR' or 'IN'
        ('IN', 'Expense Invoice'),        # suptran STYPE='IN'
        ('CN', 'Credit Note'),            # suptran STYPE='CN'
        ('PY', 'Payment'),               # suptran STYPE='PY'
        ('DJ', 'Debit Journal'),          # suptran STYPE='DJ'
        ('CJ', 'Credit Journal'),         # suptran STYPE='CJ'
    ]

    creditor = models.ForeignKey(Creditor, on_delete=models.PROTECT, related_name='%(class)s_set')

    # --- System-set on save() — never entered by user ---
    transaction_type   = models.CharField(max_length=2, choices=TRANSACTION_TYPE_CHOICES, editable=False, help_text="STYPE C(2) — set by save()")
    transaction_number = models.CharField(max_length=10, unique=True, editable=False, help_text="STRANO C(10) — auto-generated")
    # due_date is auto-calculated from transaction_date + creditor terms; shown read-only
    due_date           = models.DateField(null=True, blank=True, editable=False, help_text="SDUEDATE — auto-set from creditor terms")
    # total_amount is rolled up from line items on posting
    total_amount       = models.DecimalField(max_digits=15, decimal_places=2, default=0, editable=False, help_text="STTOT — rolled up from line items")

    # --- User-entered ---
    transaction_date      = models.DateField(help_text="STDATE")
    transaction_reference = models.CharField(max_length=20, blank=True, help_text="STREF C(20)")
    additional_reference  = models.CharField(max_length=200, blank=True, help_text="Django-only, no DBF source")

    # --- Session-captured on save (not entered by user) ---
    grn_number      = models.PositiveIntegerField(null=True, blank=True, editable=False, help_text="GRNNO N(6) — set by GRN process")
    station         = models.CharField(max_length=2, blank=True, editable=False, help_text="STATION C(2) — set from session")
    created_by_user = models.CharField(max_length=20, blank=True, editable=False, help_text="USER C(20) — set from logged-in user")

    class Meta:
        abstract = True
        ordering = ['-transaction_date', '-transaction_number']

    def clean(self):
        super().clean()
        if self.due_date and self.transaction_date and self.due_date < self.transaction_date:
            raise ValidationError({'due_date': 'Due date must be on or after transaction date'})

    def _set_due_date(self):
        if not self.due_date and self.creditor_id:
            from datetime import timedelta
            days = self.creditor.get_effective_terms_days()
            if days:
                self.due_date = self.transaction_date + timedelta(days=days)

    def get_age_in_days(self):
        if not self.due_date:
            return None
        return (timezone.now().date() - self.due_date).days

    def get_age_bucket(self):
        age = self.get_age_in_days()
        if age is None:      return None
        if age <= 0:         return 'current'
        elif age <= 30:      return '30'
        elif age <= 60:      return '60'
        elif age <= 90:      return '90'
        elif age <= 120:     return '120'
        elif age <= 150:     return '150'
        else:                return '180'


# Shared ageing bucket mixin (avoids repeating 7 DecimalFields on every subclass)
# All buckets are system-calculated at period close — never user-entered.
class AgedBalanceMixin(models.Model):
    age_current = models.DecimalField(max_digits=15, decimal_places=2, default=0, editable=False)
    age_30      = models.DecimalField(max_digits=15, decimal_places=2, default=0, editable=False)
    age_60      = models.DecimalField(max_digits=15, decimal_places=2, default=0, editable=False)
    age_90      = models.DecimalField(max_digits=15, decimal_places=2, default=0, editable=False)
    age_120     = models.DecimalField(max_digits=15, decimal_places=2, default=0, editable=False)
    age_150     = models.DecimalField(max_digits=15, decimal_places=2, default=0, editable=False)
    age_180     = models.DecimalField(max_digits=15, decimal_places=2, default=0, editable=False)

    class Meta:
        abstract = True


# ============================================================================
# GOODS RECEIVED NOTE
# Maps to: suptran.dbf (STYPE = 'IN' / 'GRN')
# ============================================================================

class GoodsReceivedNote(AgedBalanceMixin, CreditorTransaction):
    """Stock received from supplier."""

    INCL_EXCL = [('INC', 'Inclusive of VAT'), ('EXC', 'Exclusive of VAT')]

    # --- User-entered ---
    supplier_invoice_number = models.CharField(max_length=50)
    inclusive_exclusive     = models.CharField(max_length=3, choices=INCL_EXCL, default='EXC')
    surcharge_amount        = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    # --- System-calculated on post (rolled up from GRNLineItem) ---
    subtotal       = models.DecimalField(max_digits=15, decimal_places=2, default=0, editable=False, help_text="STSUB — sum of line subtotals")
    total_vat      = models.DecimalField(max_digits=15, decimal_places=2, default=0, editable=False, help_text="STGST — sum of line VAT amounts")
    total_quantity = models.DecimalField(max_digits=15, decimal_places=2, default=0, editable=False, help_text="Sum of quantity_received across all lines")

    class Meta:
        db_table = 'goods_received_notes'
        verbose_name = 'Goods Received Note'
        verbose_name_plural = 'Goods Received Notes'
        indexes = [
            # Composite index for creditor aging queries
            models.Index(fields=['creditor', 'transaction_date'], name='grn_cred_dt_idx'),
            # Index for transaction_type filtering
            models.Index(fields=['transaction_type'], name='grn_type_idx'),
            # Index for posted status filtering
            models.Index(fields=['is_posted'], name='grn_posted_idx'),
        ]

    def save(self, *args, **kwargs):
        self.transaction_type = 'GR'  # STYPE='GR' in suptran.dbf
        if not self.transaction_number:
            last = GoodsReceivedNote.objects.order_by('-id').first()
            try:
                num = int(last.transaction_number.split('-')[-1]) + 1 if last else 1
            except (ValueError, AttributeError, IndexError):
                num = 1
            self.transaction_number = f"GRN-{num:06d}"
        self._set_due_date()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.transaction_number} - {self.creditor.name}"


class GRNLineItem(TimeStampedModel):
    grn         = models.ForeignKey(GoodsReceivedNote, on_delete=models.CASCADE, related_name='line_items')
    line_number = models.PositiveSmallIntegerField(default=1)
    stock_item  = models.ForeignKey('stock_control.StockItem', on_delete=models.PROTECT, related_name='grn_lines')

    quantity_received = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    unit_cost         = models.DecimalField(max_digits=15, decimal_places=2)
    tax_code          = models.ForeignKey(TaxCode, on_delete=models.PROTECT)

    previous_cost = models.DecimalField(max_digits=15, decimal_places=2, editable=False, default=0)
    line_subtotal = models.DecimalField(max_digits=15, decimal_places=2, editable=False, default=0)
    tax_amount    = models.DecimalField(max_digits=15, decimal_places=2, editable=False, default=0)
    line_total    = models.DecimalField(max_digits=15, decimal_places=2, editable=False, default=0)

    class Meta:
        db_table = 'grn_line_items'
        ordering = ['line_number']
        unique_together = [['grn', 'line_number']]

    def save(self, *args, **kwargs):
        if not self.previous_cost:
            self.previous_cost = self.stock_item.cost_price
        self.line_subtotal = self.quantity_received * self.unit_cost
        self.tax_amount    = self.line_subtotal * (self.tax_code.rate / 100)
        self.line_total    = self.line_subtotal + self.tax_amount
        super().save(*args, **kwargs)

    def __str__(self):
        return f"GRN {self.grn.transaction_number} L{self.line_number} — {self.stock_item.stock_code}"


# ============================================================================
# CREDITOR INVOICE (expense invoices, not stock)
# Maps to: supexpt.dbf / suptran.dbf (STYPE = 'INV')
# ============================================================================

class CreditorInvoice(AgedBalanceMixin, CreditorTransaction):
    """Expense invoice (electricity, rent, etc.). Maps to SUPEXPT."""

    INCL_EXCL = [('INC', 'Inclusive of VAT'), ('EXC', 'Exclusive of VAT')]

    supplier_invoice_number = models.CharField(max_length=50, help_text="TRANO in supexpt")
    inclusive_exclusive     = models.CharField(max_length=3, choices=INCL_EXCL, default='INC')
    station_no_area         = models.CharField(max_length=2, blank=True, help_text="SOURCE in supexpt")

    # FIX #10: tax_indicator was missing from original
    tax_indicator = models.PositiveSmallIntegerField(
        default=1,
        help_text="TAXIND in supexpt. 1=standard VAT, 0=exempt/zero-rated."
    )

    related_grn = models.ForeignKey(
        GoodsReceivedNote, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='related_expense_invoices',
        help_text="GRNNO in supexpt"
    )

    subtotal  = models.DecimalField(max_digits=15, decimal_places=2, default=0, editable=False, help_text="VALUE/STSUB")
    total_vat = models.DecimalField(max_digits=15, decimal_places=2, default=0, editable=False, help_text="INVAT/STGST")

    class Meta:
        db_table = 'creditor_invoices'
        verbose_name = 'Creditor Invoice'
        verbose_name_plural = 'Creditor Invoices'

    def save(self, *args, **kwargs):
        self.transaction_type = 'INV'
        if not self.transaction_number:
            last = CreditorInvoice.objects.order_by('-id').first()
            try:
                num = int(last.transaction_number.split('-')[-1]) + 1 if last else 1
            except (ValueError, AttributeError, IndexError):
                num = 1
            self.transaction_number = f"SUPINV-{num:06d}"
        self._set_due_date()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.transaction_number} - {self.creditor.name}"


class CreditorInvoiceLineItem(TimeStampedModel):
    invoice     = models.ForeignKey(CreditorInvoice, on_delete=models.CASCADE, related_name='line_items')
    line_number = models.PositiveSmallIntegerField(default=1)

    expense_category = models.ForeignKey(
        ExpenseCategory, on_delete=models.PROTECT,
        limit_choices_to={'category_type__in': ['BOTH', 'CREDITORS']},
        related_name='creditor_invoice_lines',
        help_text="EXPCAT in supexpt"
    )
    amount   = models.DecimalField(max_digits=15, decimal_places=2)
    tax_code = models.ForeignKey(TaxCode, on_delete=models.PROTECT)

    tax_amount = models.DecimalField(max_digits=15, decimal_places=2, editable=False, default=0)
    line_total = models.DecimalField(max_digits=15, decimal_places=2, editable=False, default=0)

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
# Maps to: suptran.dbf (STYPE = 'CN')
# ============================================================================

class CreditorCreditNote(AgedBalanceMixin, CreditorTransaction):
    """Credit note received from supplier."""

    INCL_EXCL = [('INC', 'Inclusive of VAT'), ('EXC', 'Exclusive of VAT')]

    supplier_credit_note_number = models.CharField(max_length=50)
    inclusive_exclusive         = models.CharField(max_length=3, choices=INCL_EXCL, default='EXC')
    original_grn = models.ForeignKey(
        GoodsReceivedNote, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='credit_notes'
    )

    subtotal  = models.DecimalField(max_digits=15, decimal_places=2, default=0, editable=False)
    total_vat = models.DecimalField(max_digits=15, decimal_places=2, default=0, editable=False)

    class Meta:
        db_table = 'creditor_credit_notes'
        verbose_name = 'Creditor Credit Note'
        verbose_name_plural = 'Creditor Credit Notes'

    def save(self, *args, **kwargs):
        self.transaction_type = 'CN'
        if not self.transaction_number:
            last = CreditorCreditNote.objects.order_by('-id').first()
            try:
                num = int(last.transaction_number.split('-')[-1]) + 1 if last else 1
            except (ValueError, AttributeError, IndexError):
                num = 1
            self.transaction_number = f"SUPCN-{num:06d}"
        self._set_due_date()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.transaction_number} - {self.creditor.name}"


class CreditorCreditNoteLineItem(TimeStampedModel):
    credit_note = models.ForeignKey(CreditorCreditNote, on_delete=models.CASCADE, related_name='line_items')
    line_number = models.PositiveSmallIntegerField(default=1)

    stock_item        = models.ForeignKey('stock_control.StockItem', on_delete=models.PROTECT, related_name='creditor_cn_lines')
    quantity_returned = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    unit_cost         = models.DecimalField(max_digits=15, decimal_places=2)
    tax_code          = models.ForeignKey(TaxCode, on_delete=models.PROTECT)

    line_subtotal = models.DecimalField(max_digits=15, decimal_places=2, editable=False, default=0)
    tax_amount    = models.DecimalField(max_digits=15, decimal_places=2, editable=False, default=0)
    line_total    = models.DecimalField(max_digits=15, decimal_places=2, editable=False, default=0)

    class Meta:
        db_table = 'creditor_credit_note_line_items'
        ordering = ['line_number']
        unique_together = [['credit_note', 'line_number']]

    def save(self, *args, **kwargs):
        self.line_subtotal = self.quantity_returned * self.unit_cost
        self.tax_amount    = self.line_subtotal * (self.tax_code.rate / 100)
        self.line_total    = self.line_subtotal + self.tax_amount
        super().save(*args, **kwargs)


# ============================================================================
# CREDITOR PAYMENT
# Maps to: suptran.dbf (STYPE = 'PA' / 'PM' / 'PAY')
# ============================================================================

class CreditorPayment(AgedBalanceMixin, CreditorTransaction):
    """Payment made to supplier."""

    # --- User-entered ---
    amount_due     = models.DecimalField(max_digits=15, decimal_places=2)
    amount_paid    = models.DecimalField(max_digits=15, decimal_places=2)
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.PROTECT, null=True, blank=True)
    is_unallocated = models.BooleanField(default=False)

    # --- System-calculated on save ---
    settlement_discount_amount  = models.DecimalField(max_digits=15, decimal_places=2, default=0, editable=False, help_text="amount_due - amount_paid")
    settlement_discount_percent = models.DecimalField(max_digits=5,  decimal_places=2, default=0, editable=False, help_text="(discount / amount_due) * 100")

    class Meta:
        db_table = 'creditor_payments'
        verbose_name = 'Creditor Payment'
        verbose_name_plural = 'Creditor Payments'

    def save(self, *args, **kwargs):
        self.transaction_type = 'PY'  # STYPE='PY' in suptran.dbf
        if not self.transaction_number:
            last = CreditorPayment.objects.order_by('-id').first()
            try:
                num = int(last.transaction_number.split('-')[-1]) + 1 if last else 1
            except (ValueError, AttributeError, IndexError):
                num = 1
            self.transaction_number = f"SUPPAY-{num:06d}"
        self.settlement_discount_amount = self.amount_due - self.amount_paid
        if self.amount_due > 0:
            self.settlement_discount_percent = (self.settlement_discount_amount / self.amount_due) * 100
        self.total_amount = self.amount_paid
        self._set_due_date()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.transaction_number} — {self.creditor.name} R{self.amount_paid}"


# ============================================================================
# CREDITOR JOURNAL
# Maps to: suptran.dbf (STYPE = 'DJ' / 'CJ')
# ============================================================================

class CreditorJournal(AgedBalanceMixin, CreditorTransaction):
    """Debit or credit journal adjustment."""

    # --- User-entered ---
    # DJ=Debit Journal, CJ=Credit Journal — drives transaction_type on save
    JOURNAL_TYPE_CHOICES = [('DJ', 'Debit Journal'), ('CJ', 'Credit Journal')]
    journal_type   = models.CharField(max_length=2, choices=JOURNAL_TYPE_CHOICES)
    journal_amount = models.DecimalField(max_digits=15, decimal_places=2)

    class Meta:
        db_table = 'creditor_journals'
        verbose_name = 'Creditor Journal'
        verbose_name_plural = 'Creditor Journals'

    def save(self, *args, **kwargs):
        # journal_type IS the STYPE (DJ/CJ) — copy directly
        self.transaction_type = self.journal_type
        self.total_amount = self.journal_amount
        if not self.transaction_number:
            prefix = 'SUPDJ' if self.journal_type == 'DJ' else 'SUPCJ'
            last = CreditorJournal.objects.filter(journal_type=self.journal_type).order_by('-id').first()
            try:
                num = int(last.transaction_number.split('-')[-1]) + 1 if last else 1
            except (ValueError, AttributeError, IndexError):
                num = 1
            self.transaction_number = f"{prefix}-{num:04d}"
        self._set_due_date()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.transaction_number} ({self.journal_type}) — {self.creditor.name}"


# ============================================================================
# SUPPLIER LEDGER ENTRY  (FIX #3)
# Direct 1:1 mapping of suptran.dbf.
# All 89 legacy suptran records import here. Individual entries can later be
# promoted to the typed models above via a management command.
# ============================================================================

class SupplierLedgerEntry(TimeStampedModel):
    """
    Raw creditor ledger. Direct mapping to suptran.dbf.

        SUPNO    → creditor (FK via supplier_number)
        STRANO   → transaction_number
        STDATE   → transaction_date
        SDUEDATE → due_date
        STYPE    → transaction_type
        STSUB    → subtotal
        STGST    → vat_amount
        STTOT    → total_amount
        STREF    → reference
        GRNNO    → grn_number
        STATION  → station
        USER     → created_by_user
    """

    # suptran.dbf: STYPE C(2) — exact 2-char codes used in DBF
    STYPE_CHOICES = [
        ('GR', 'Goods Received'),    ('IN', 'Invoice/GRN'),
        ('CN', 'Credit Note'),       ('PY', 'Payment'),
        ('DJ', 'Debit Journal'),     ('CJ', 'Credit Journal'),
    ]

    creditor           = models.ForeignKey(Creditor, on_delete=models.PROTECT, related_name='ledger_entries', help_text="SUPNO N(4)")
    transaction_number = models.CharField(max_length=10, db_index=True, help_text="STRANO C(10)")
    transaction_date   = models.DateField(db_index=True, help_text="STDATE")
    due_date           = models.DateField(null=True, blank=True, help_text="SDUEDATE")
    transaction_type   = models.CharField(max_length=2, choices=STYPE_CHOICES, help_text="STYPE C(2)")

    subtotal     = models.DecimalField(max_digits=15, decimal_places=2, default=0, help_text="STSUB")
    vat_amount   = models.DecimalField(max_digits=15, decimal_places=2, default=0, help_text="STGST")
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0, help_text="STTOT")

    reference       = models.CharField(max_length=20, blank=True, help_text="STREF")
    grn_number      = models.PositiveIntegerField(null=True, blank=True, help_text="GRNNO")
    station         = models.CharField(max_length=2,  blank=True, help_text="STATION")
    created_by_user = models.CharField(max_length=20, blank=True, help_text="USER")

    class Meta:
        db_table = 'supplier_ledger_entries'
        ordering = ['-transaction_date', 'transaction_number']
        unique_together = [['creditor', 'transaction_number']]
        indexes = [
            models.Index(fields=['creditor', '-transaction_date']),
            models.Index(fields=['transaction_type']),
            models.Index(fields=['grn_number']),
        ]
        verbose_name = 'Supplier Ledger Entry'
        verbose_name_plural = 'Supplier Ledger Entries'

    def __str__(self):
        return f"{self.transaction_number} ({self.transaction_type}) — {self.creditor.supplier_number}"


# ============================================================================
# OPEN ITEM MODELS
# Maps to: supopen.dbf
# ============================================================================

class CreditorOpenItem(models.Model):
    """
    Open items for open item accounting. Maps to SUPOPEN.

    FIX #4: FK link validation only fires for is_legacy=False records.
    Legacy imports set is_legacy=True and supply only transaction_number/type.
    """

    creditor = models.ForeignKey(Creditor, on_delete=models.CASCADE, related_name='open_items')

    # Typed transaction FKs (populated for new app-created records)
    grn          = models.ForeignKey(GoodsReceivedNote,  on_delete=models.CASCADE, null=True, blank=True, related_name='open_items')
    invoice      = models.ForeignKey(CreditorInvoice,    on_delete=models.CASCADE, null=True, blank=True, related_name='open_items')
    credit_note  = models.ForeignKey(CreditorCreditNote, on_delete=models.CASCADE, null=True, blank=True, related_name='open_items')
    journal      = models.ForeignKey(CreditorJournal,    on_delete=models.CASCADE, null=True, blank=True, related_name='open_items')
    ledger_entry = models.ForeignKey(
        SupplierLedgerEntry, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='open_items',
        help_text="Set for legacy-imported records without a typed transaction."
    )

    transaction_date   = models.DateField(help_text="DATE")
    due_date           = models.DateField(null=True, blank=True)
    transaction_type   = models.CharField(max_length=2, help_text="TYPE C(2)")
    transaction_number = models.CharField(max_length=10, help_text="TRANO C(10)")

    # --- System-maintained — never user-entered ---
    original_amount    = models.DecimalField(max_digits=14, decimal_places=2, editable=False, help_text="TOTAL N(14,2) — copied from transaction on creation")
    balance_due        = models.DecimalField(max_digits=14, decimal_places=2, editable=False, help_text="BALANCEDUE N(14,2) — reduced by each payment allocation")
    age_period         = models.PositiveSmallIntegerField(default=0, editable=False, help_text="Ageing period bucket — set by ageing run")
    ageing_flag        = models.CharField(max_length=1, blank=True, editable=False, help_text="AGEFLAG C(1) — set by ageing run")
    is_fully_allocated = models.BooleanField(default=False, editable=False, help_text="Set True when balance_due reaches zero")

    # FIX #4: distinguishes legacy imports from app-created records
    is_legacy = models.BooleanField(
        default=False,
        help_text="True for records imported from supopen.dbf. Skips FK link validation."
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'creditor_open_items'
        ordering = ['transaction_date']
        unique_together = [['creditor', 'transaction_number', 'transaction_type']]
        indexes = [
            models.Index(fields=['creditor', '-transaction_date']),
            models.Index(fields=['is_fully_allocated']),
        ]
        verbose_name = 'Creditor Open Item'
        verbose_name_plural = 'Creditor Open Items'

    def clean(self):
        super().clean()
        if not self.is_legacy:
            links = [self.grn, self.invoice, self.credit_note, self.journal]
            if sum(1 for x in links if x is not None) != 1:
                raise ValidationError(
                    'Exactly one transaction (GRN, Invoice, Credit Note, or Journal) must be linked.'
                )
        if self.balance_due > self.original_amount:
            raise ValidationError({'balance_due': 'Balance due cannot exceed original amount'})

    def get_age_bucket(self):
        if not self.due_date:
            return 'current'
        days = (timezone.now().date() - self.due_date).days
        if days <= 0:    return 'current'
        elif days <= 30:  return '30'
        elif days <= 60:  return '60'
        elif days <= 90:  return '90'
        elif days <= 120: return '120'
        elif days <= 150: return '150'
        else:             return '180'

    def __str__(self):
        return f"OpenItem {self.transaction_number} — {self.creditor.supplier_number} (bal: {self.balance_due})"


class OpenItemAllocation(models.Model):
    """Payment allocations to open items."""

    payment   = models.ForeignKey(CreditorPayment,  on_delete=models.CASCADE, related_name='allocations')
    open_item = models.ForeignKey(CreditorOpenItem, on_delete=models.CASCADE, related_name='allocations')

    amount_paid         = models.DecimalField(max_digits=15, decimal_places=2)
    settlement_discount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    allocated_at        = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'creditor_open_item_allocations'
        indexes = [
            models.Index(fields=['payment']),
            models.Index(fields=['open_item']),
        ]

    def clean(self):
        super().clean()
        existing = self.open_item.allocations.exclude(pk=self.pk).aggregate(
            total=models.Sum('amount_paid') + models.Sum('settlement_discount')
        )['total'] or Decimal('0')
        if existing + self.amount_paid + self.settlement_discount > self.open_item.balance_due:
            raise ValidationError('Total allocation exceeds balance due')

    def __str__(self):
        return f"{self.payment.transaction_number} → {self.open_item.transaction_number}"


# ============================================================================
# OPEN ITEM AUDIT
# Maps to: supoaud.dbf
# ============================================================================

class OpenItemAudit(TimeStampedModel):
    """
    Audit trail of open item changes. Maps to SUPOAUD.
    ENTIRELY system-written — created automatically when open items are
    allocated or reversed. No user should edit these records.
    """

    creditor           = models.ForeignKey(Creditor, on_delete=models.CASCADE, related_name='open_item_audits')
    transaction_number = models.CharField(max_length=10, editable=False, help_text="TRANO C(10)")
    transaction_type   = models.CharField(max_length=2, editable=False, help_text="TYPE C(2)")

    this_transaction_type   = models.CharField(max_length=2, editable=False, help_text="THISTYPE C(2)")
    # FIX #9: IntegerField — THISTRAN is N(6) integer in DBF, not decimal
    this_transaction_number = models.IntegerField(editable=False, help_text="THISTRAN — N(6) in DBF")

    transaction_date = models.DateField(editable=False, help_text="DATE")
    amount           = models.DecimalField(max_digits=14, decimal_places=2, editable=False, help_text="AMOUNT N(14,2)")

    audit_timestamp = models.DateTimeField(auto_now_add=True, editable=False)
    audit_notes     = models.TextField(blank=True, editable=False)

    class Meta:
        db_table = 'open_item_audits'
        ordering = ['-audit_timestamp']
        indexes = [
            models.Index(fields=['creditor', '-audit_timestamp']),
            models.Index(fields=['transaction_number']),
        ]
        verbose_name = 'Open Item Audit'
        verbose_name_plural = 'Open Item Audits'

    def __str__(self):
        return f"{self.creditor.supplier_number} — {self.transaction_number} ({self.transaction_date})"


# ============================================================================
# RFC (RETURN FOR CREDIT)
# Maps to: supcrmas.dbf (master) + supcrtrn.dbf (lines)
# ============================================================================

class RFC(TimeStampedModel):
    """Return for Credit to supplier. Maps to SUPCRMAS."""

    STATUS_CHOICES = [
        ('PE', 'Pending with Supplier'),   # DBF 'A' maps to 'PE' on import
        ('CR', 'Credit Note Received'),    # DBF 'C'
        ('RE', 'Stock Replaced'),          # DBF 'R'
        ('CA', 'Cancelled'),               # DBF 'X'
    ]

    creditor   = models.ForeignKey(Creditor, on_delete=models.PROTECT, related_name='rfcs')
    # DBF: RFCNO N(6) — stored as char for display consistency
    rfc_number = models.CharField(max_length=6, unique=True, help_text="RFCNO — N(6) in DBF")

    # FIX #5: nullable — no return_date equivalent in supcrmas.dbf; set from DATESENT on import
    return_date   = models.DateField(null=True, blank=True, help_text="No DBF source — set from DATESENT on import.")
    date_sent     = models.DateField(null=True, blank=True, help_text="DATESENT")
    date_returned = models.DateField(null=True, blank=True, help_text="DATERETN — date credit note received")

    status = models.CharField(max_length=2, choices=STATUS_CHOICES, default='PE', help_text="STATUS C(2)")

    # --- System-calculated — rolled up from RFCLineItem on save ---
    total_value_exclusive = models.DecimalField(max_digits=15, decimal_places=2, default=0, editable=False, help_text="Sum of line_value_exclusive across all line items")
    total_value_inclusive = models.DecimalField(max_digits=15, decimal_places=2, default=0, editable=False, help_text="Sum of line_value_inclusive across all line items")

    class Meta:
        db_table = 'rfcs'
        verbose_name = 'RFC (Return For Credit)'
        verbose_name_plural = 'RFCs (Returns For Credit)'

    def __str__(self):
        return f"RFC-{self.rfc_number} — {self.creditor.name}"


class RFCLineItem(TimeStampedModel):
    """Line items on an RFC. Maps to SUPCRTRN."""

    rfc         = models.ForeignKey(RFC, on_delete=models.CASCADE, related_name='line_items')
    line_number = models.PositiveSmallIntegerField(default=1)

    # supcrtrn: CODE C(13)
    stock_item        = models.ForeignKey('stock_control.StockItem', on_delete=models.PROTECT, related_name='rfc_lines', help_text="CODE C(13)")
    quantity_returned = models.DecimalField(max_digits=10, decimal_places=2, help_text="QTYRFC N(10,2)")
    quantity_credited = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="QTYCRED N(10,2)")

    # FIX #6: QTY field was missing from original
    quantity_stock = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        help_text="QTY N(10,2) — actual stock movement quantity in supcrtrn"
    )

    # supcrtrn has VAL N(12,2) not a separate unit_cost — unit_cost derived from stock
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2, editable=False, default=0, help_text="Pulled from stock_item.cost_price on save")
    # VAL is the line value stored directly in supcrtrn
    line_value = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="VAL N(12,2)")
    tax_code   = models.ForeignKey(TaxCode, on_delete=models.PROTECT)

    # supcrtrn: TIME is C(5) e.g. "08:30" — stored as char
    rfc_line_date = models.DateField(null=True, blank=True, help_text="DATE — date this line was processed in supcrtrn")
    rfc_line_time = models.CharField(max_length=5, blank=True, help_text="TIME C(5) — stored as HH:MM string from supcrtrn")

    original_transaction_type = models.CharField(max_length=2,  blank=True, help_text="TYPE C(2)")
    original_transaction_date = models.DateField(null=True, blank=True,     help_text="PURCHDATE")
    supplier_reference_number = models.CharField(max_length=10, blank=True, help_text="SUPREFNO C(10)")
    reason = models.TextField(blank=True, help_text="COMMENT C(30) — stored as text for flexibility")

    # --- System-calculated on save ---
    line_value_exclusive = models.DecimalField(max_digits=15, decimal_places=2, editable=False, default=0)
    tax_amount           = models.DecimalField(max_digits=15, decimal_places=2, editable=False, default=0)
    line_value_inclusive = models.DecimalField(max_digits=15, decimal_places=2, editable=False, default=0)

    class Meta:
        db_table = 'rfc_line_items'
        ordering = ['line_number']
        unique_together = [['rfc', 'line_number']]

    def save(self, *args, **kwargs):
        if not self.unit_cost:
            self.unit_cost = self.stock_item.cost_price
        # Use line_value (VAL from DBF) if set; otherwise calculate from quantity * unit_cost
        if not self.line_value:
            self.line_value = self.quantity_returned * self.unit_cost
        self.line_value_exclusive = self.line_value
        self.tax_amount           = self.line_value_exclusive * (self.tax_code.rate / 100)
        self.line_value_inclusive = self.line_value_exclusive + self.tax_amount
        super().save(*args, **kwargs)

    def __str__(self):
        return f"RFC {self.rfc.rfc_number} L{self.line_number} — {self.stock_item.stock_code}"


# ============================================================================
# EXPENSE CATEGORY MONTHLY BALANCE
# Maps to: supexp.dbf
# FIX #7: Removed contradictory 'month' field. supexp has ONE row per category
# with 12 monthly columns. Model now matches that structure exactly:
# one row per (expense_category, year) with exp_month_1..12 columns.
# ============================================================================

class ExpenseCategoryMonthlyBalance(TimeStampedModel):
    """
    Expense category totals per year. Maps to SUPEXP.
    One row per (expense_category, year); columns EXP1–12 = January–December.
    NOTE: supexp.dbf has no 'year' column — the year field is Django-only (for multi-year support).
    Legacy import assigns year from the financial period being imported.
    EXPCATNAME C(20) is stored here to avoid joining to ExpenseCategory on every read.
    """

    expense_category = models.ForeignKey(
        ExpenseCategory, on_delete=models.CASCADE,
        related_name='monthly_balances', help_text="EXPCAT N(8)"
    )
    # supexp.dbf has EXPCATNAME C(20) — stored as a denormalised cache field
    expense_category_name = models.CharField(
        max_length=20, blank=True,
        help_text="EXPCATNAME C(20) — denormalised name from supexp.dbf"
    )
    # Django-only: supexp has no year column; set during import
    year = models.PositiveIntegerField(help_text="Financial year — Django-only, no DBF source")

    # --- System-accumulated — updated automatically when transactions post ---
    expense_mtd   = models.DecimalField(max_digits=15, decimal_places=2, default=0, editable=False, help_text="EXPMTD — month-to-date total, reset at period close")
    input_vat_mtd = models.DecimalField(max_digits=15, decimal_places=2, default=0, editable=False, help_text="EXPINVAT — input VAT MTD")

    exp_month_1  = models.DecimalField(max_digits=15, decimal_places=2, default=0, editable=False, help_text="EXP1  Jan")
    exp_month_2  = models.DecimalField(max_digits=15, decimal_places=2, default=0, editable=False, help_text="EXP2  Feb")
    exp_month_3  = models.DecimalField(max_digits=15, decimal_places=2, default=0, editable=False, help_text="EXP3  Mar")
    exp_month_4  = models.DecimalField(max_digits=15, decimal_places=2, default=0, editable=False, help_text="EXP4  Apr")
    exp_month_5  = models.DecimalField(max_digits=15, decimal_places=2, default=0, editable=False, help_text="EXP5  May")
    exp_month_6  = models.DecimalField(max_digits=15, decimal_places=2, default=0, editable=False, help_text="EXP6  Jun")
    exp_month_7  = models.DecimalField(max_digits=15, decimal_places=2, default=0, editable=False, help_text="EXP7  Jul")
    exp_month_8  = models.DecimalField(max_digits=15, decimal_places=2, default=0, editable=False, help_text="EXP8  Aug")
    exp_month_9  = models.DecimalField(max_digits=15, decimal_places=2, default=0, editable=False, help_text="EXP9  Sep")
    exp_month_10 = models.DecimalField(max_digits=15, decimal_places=2, default=0, editable=False, help_text="EXP10 Oct")
    exp_month_11 = models.DecimalField(max_digits=15, decimal_places=2, default=0, editable=False, help_text="EXP11 Nov")
    exp_month_12 = models.DecimalField(max_digits=15, decimal_places=2, default=0, editable=False, help_text="EXP12 Dec")

    class Meta:
        db_table = 'expense_category_monthly_balances'
        unique_together = [['expense_category', 'year']]
        ordering = ['-year', 'expense_category']
        indexes = [
            models.Index(fields=['expense_category', 'year']),
            models.Index(fields=['year']),
        ]
        verbose_name = 'Expense Category Monthly Balance'
        verbose_name_plural = 'Expense Category Monthly Balances'

    def __str__(self):
        return f"{self.expense_category} — {self.year}"

    def get_month(self, n):
        if not 1 <= n <= 12:
            raise ValueError("Month must be 1–12")
        return getattr(self, f'exp_month_{n}')

    def set_month(self, n, value):
        if not 1 <= n <= 12:
            raise ValueError("Month must be 1–12")
        setattr(self, f'exp_month_{n}', value)

    def get_annual_total(self):
        return sum(self.get_month(i) for i in range(1, 13))



# ============================================================================
# EXPENSE CATEGORY TRANSACTION
# Maps to: supexpt.dbf
# Each row is a single expense posting to an expense category.
# ============================================================================

class ExpenseCategoryTransaction(TimeStampedModel):
    """
    Individual expense postings that feed into ExpenseCategoryMonthlyBalance.
    Maps to SUPEXPT.

    Fields:
        EXPCAT   N(8)  → expense_category FK
        DATE     D(8)  → transaction_date
        TRANO    C(10) → transaction_number (links to suptran STRANO)
        SUPNO    N(4)  → creditor FK
        VALUE    N(10,2) → amount_exclusive
        INVAT    N(10,2) → input_vat_amount
        TOTAL    N(10,2) → amount_inclusive
        SOURCE   C(2)  → source_type ('GR','IN','CN', etc.)
        GRNNO    N(6)  → grn_number
        TAXIND   N(1)  → tax_indicator (0=no tax, 1=taxable)
    """

    expense_category  = models.ForeignKey(
        ExpenseCategory, on_delete=models.CASCADE,
        related_name='expense_transactions', help_text="EXPCAT N(8)"
    )
    creditor = models.ForeignKey(
        'Creditor', on_delete=models.PROTECT,
        related_name='expense_transactions', help_text="SUPNO N(4)"
    )
    transaction_date   = models.DateField(help_text="DATE")
    transaction_number = models.CharField(max_length=10, db_index=True, help_text="TRANO C(10)")

    # --- User/source fields ---
    amount_exclusive  = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="VALUE N(10,2) — expense amount excl. VAT")
    tax_indicator = models.PositiveSmallIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(9)],
        help_text="TAXIND N(1) — 0=no tax, 1=taxable"
    )
    source_type  = models.CharField(max_length=2, blank=True, help_text="SOURCE C(2) — same codes as suptran STYPE")
    grn_number   = models.PositiveIntegerField(null=True, blank=True, help_text="GRNNO N(6)")

    # --- System-calculated on save ---
    input_vat_amount  = models.DecimalField(max_digits=10, decimal_places=2, default=0, editable=False, help_text="INVAT N(10,2) — calculated from amount_exclusive × tax rate")
    amount_inclusive  = models.DecimalField(max_digits=10, decimal_places=2, default=0, editable=False, help_text="TOTAL N(10,2) — amount_exclusive + input_vat_amount")

    class Meta:
        db_table = 'expense_category_transactions'
        ordering = ['-transaction_date', 'transaction_number']
        indexes = [
            models.Index(fields=['expense_category', '-transaction_date']),
            models.Index(fields=['creditor', '-transaction_date']),
            models.Index(fields=['transaction_number']),
            models.Index(fields=['grn_number']),
        ]
        verbose_name = 'Expense Category Transaction'
        verbose_name_plural = 'Expense Category Transactions'

    def __str__(self):
        return f"{self.transaction_number} — {self.expense_category} ({self.transaction_date})"


# ============================================================================
# SUPPLIER PAYMENT ORDER  (FIX #11)
# Maps to: suppo.dbf
# Note: suppo.dbf has NO SUPNO field — cannot link to a specific creditor.
# The creditor FK below is optional; legacy imports leave it null.
# ============================================================================

class SupplierPaymentOrder(TimeStampedModel):
    """
    Scheduled outgoing supplier payment / post-dated cheque.
    Maps to SUPPO. Legacy records have creditor=None (no SUPNO in DBF).
    """

    creditor = models.ForeignKey(
        Creditor, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='payment_orders',
        help_text="Optional — suppo.dbf has no SUPNO so legacy records have this as null."
    )
    payment_date = models.DateField(help_text="DATE")
    amount       = models.DecimalField(
        max_digits=15, decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="AMOUNT"
    )

    detail_line1 = models.CharField(max_length=25, blank=True, help_text="DETAIL1")
    detail_line2 = models.CharField(max_length=25, blank=True, help_text="DETAIL2")
    detail_line3 = models.CharField(max_length=25, blank=True, help_text="DETAIL3")

    # --- System-set when the payment run processes this order ---
    is_processed   = models.BooleanField(default=False, editable=False, help_text="Set True by payment run")
    processed_date = models.DateField(null=True, blank=True, editable=False, help_text="Set by payment run on processing")

    class Meta:
        db_table = 'supplier_payment_orders'
        ordering = ['payment_date']
        indexes = [
            models.Index(fields=['payment_date', 'is_processed']),
            models.Index(fields=['creditor', 'is_processed']),
        ]
        verbose_name = 'Supplier Payment Order'
        verbose_name_plural = 'Supplier Payment Orders'

    def __str__(self):
        sup = self.creditor.name if self.creditor_id else 'Unknown'
        return f"PayOrder {self.payment_date} — {sup} R{self.amount}"


# ============================================================================
# CREDITOR TRANSACTION LINE (Generic, ContentType polymorphism)
# ============================================================================

class CreditorTransactionLine(TimeStampedModel):
    """Generic line item for any creditor transaction type."""

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id    = models.PositiveIntegerField()
    transaction  = GenericForeignKey('content_type', 'object_id')

    line_number      = models.PositiveSmallIntegerField(default=1)
    stock_item       = models.ForeignKey('stock_control.StockItem', on_delete=models.PROTECT, related_name='transaction_lines', null=True, blank=True)
    expense_category = models.ForeignKey(ExpenseCategory, on_delete=models.PROTECT, related_name='transaction_lines', null=True, blank=True)

    quantity  = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    unit_cost = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    tax_code  = models.ForeignKey(TaxCode, on_delete=models.PROTECT, related_name='transaction_lines')

    tax_amount       = models.DecimalField(max_digits=15, decimal_places=2, default=0, editable=False)
    amount_exclusive = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    amount_inclusive = models.DecimalField(max_digits=15, decimal_places=2, default=0, editable=False)

    class Meta:
        db_table = 'creditor_transaction_lines'
        ordering = ['line_number']

    def save(self, *args, **kwargs):
        if self.amount_exclusive:
            self.tax_amount      = self.amount_exclusive * (self.tax_code.rate / 100)
            self.amount_inclusive = self.amount_exclusive + self.tax_amount
        elif self.quantity and self.unit_cost:
            self.amount_exclusive = self.quantity * self.unit_cost
            self.tax_amount       = self.amount_exclusive * (self.tax_code.rate / 100)
            self.amount_inclusive = self.amount_exclusive + self.tax_amount
        super().save(*args, **kwargs)

    def __str__(self):
        if self.stock_item:
            return f"Line {self.line_number} — {self.stock_item.stock_code}"
        if self.expense_category:
            return f"Line {self.line_number} — {self.expense_category}"
        return f"Line {self.line_number}"