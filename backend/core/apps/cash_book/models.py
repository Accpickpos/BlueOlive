"""
CASHBOOK APP - Django Models
Complete cash book and banking models

LOCATION: accpick_project/cashbook/models.py

Models in this file:
- OtherIncomeTransaction (non-debtor income)
- OtherIncomeLineItem
- OtherExpenseTransaction (non-creditor expenses)
- OtherExpenseLineItem
- BankReconciliation
- UnpresentedCheque
- PostDatedChequeRegister
"""

from django.db import models
from django.core.validators import MinValueValidator
from django.contrib.auth import get_user_model
from decimal import Decimal
from apps.settings.models import (
    IncomeCategory,
    ExpenseCategory,
    TaxCode,
    PaymentMethod,
    TimeStampedModel
)

User = get_user_model()


# ============================================================================
# CASHBOOK TRANSACTION BASE
# ============================================================================

class CashBookTransaction(TimeStampedModel):
    """Base for all cash book transactions (abstract)"""
    
    TRANSACTION_TYPE_CHOICES = [
        ('INCOME', 'Other Income'),
        ('EXPENSE', 'Other Expense'),
    ]
    
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES)
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
    
    # Bank reconciliation
    is_reconciled = models.BooleanField(
        default=False,
        help_text="Matched with bank statement"
    )
    reconciled_at = models.DateTimeField(null=True, blank=True)
    reconciliation = models.ForeignKey(
        'BankReconciliation',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_set'
    )
    
    class Meta:
        abstract = True
        ordering = ['-transaction_date', '-transaction_number']


# ============================================================================
# OTHER INCOME TRANSACTION
# ============================================================================

class OtherIncomeTransaction(CashBookTransaction):
    """
    Income not from debtors
    Examples: Interest received, Rent income, Rebates
    """
    
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
    total_vat = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        editable=False
    )
    
    class Meta:
        db_table = 'cashbook_other_income'
        verbose_name = 'Other Income Transaction'
        verbose_name_plural = 'Other Income Transactions'
    
    def save(self, *args, **kwargs):
        self.transaction_type = 'INCOME'
        if not self.transaction_number:
            self.transaction_number = self._generate_number()
        super().save(*args, **kwargs)
    
    def _generate_number(self):
        last = OtherIncomeTransaction.objects.order_by('-id').first()
        if last and last.transaction_number:
            try:
                num = int(last.transaction_number.split('-')[-1])
                return f"INC-{num + 1:06d}"
            except:
                pass
        return "INC-000001"
    
    def calculate_totals(self):
        """Calculate totals from line items"""
        lines = self.line_items.all()
        self.subtotal = sum(line.amount for line in lines)
        self.total_vat = sum(line.tax_amount for line in lines)
        self.total_amount = sum(line.line_total for line in lines)
        self.save()
    
    def __str__(self):
        return f"{self.transaction_number} - {self.transaction_date}"


class OtherIncomeLineItem(TimeStampedModel):
    """Line items for other income"""
    
    income_transaction = models.ForeignKey(
        OtherIncomeTransaction,
        on_delete=models.CASCADE,
        related_name='line_items'
    )
    line_number = models.PositiveSmallIntegerField(default=1)
    
    income_category = models.ForeignKey(
        IncomeCategory,
        on_delete=models.PROTECT,
        related_name='cashbook_lines'
    )
    description = models.CharField(max_length=200, blank=True)
    
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    tax_code = models.ForeignKey(TaxCode, on_delete=models.PROTECT)
    
    # Calculated
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
    
    class Meta:
        db_table = 'cashbook_other_income_lines'
        ordering = ['line_number']
        unique_together = [['income_transaction', 'line_number']]
        verbose_name = 'Other Income Line Item'
        verbose_name_plural = 'Other Income Line Items'
    
    def save(self, *args, **kwargs):
        self.tax_amount = self.amount * (self.tax_code.rate / 100)
        self.line_total = self.amount + self.tax_amount
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Line {self.line_number}: {self.income_category.name}"


# ============================================================================
# OTHER EXPENSE TRANSACTION
# ============================================================================

class OtherExpenseTransaction(CashBookTransaction):
    """
    Expenses not from creditors
    Examples: Bank charges, Petty cash, Salaries, Sundry expenses
    """
    
    INCLUSIVE_EXCLUSIVE_CHOICES = [
        ('INC', 'Inclusive of VAT'),
        ('EXC', 'Exclusive of VAT'),
    ]
    inclusive_exclusive = models.CharField(
        max_length=3,
        choices=INCLUSIVE_EXCLUSIVE_CHOICES,
        default='INC'
    )
    
    payment_method = models.ForeignKey(
        PaymentMethod,
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )
    
    # Calculated totals
    subtotal = models.DecimalField(
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
    
    class Meta:
        db_table = 'cashbook_other_expense'
        verbose_name = 'Other Expense Transaction'
        verbose_name_plural = 'Other Expense Transactions'
    
    def save(self, *args, **kwargs):
        self.transaction_type = 'EXPENSE'
        if not self.transaction_number:
            self.transaction_number = self._generate_number()
        super().save(*args, **kwargs)
    
    def _generate_number(self):
        last = OtherExpenseTransaction.objects.order_by('-id').first()
        if last and last.transaction_number:
            try:
                num = int(last.transaction_number.split('-')[-1])
                return f"EXP-{num + 1:06d}"
            except:
                pass
        return "EXP-000001"
    
    def calculate_totals(self):
        """Calculate totals from line items"""
        lines = self.line_items.all()
        self.subtotal = sum(line.amount for line in lines)
        self.total_vat = sum(line.tax_amount for line in lines)
        self.total_amount = sum(line.line_total for line in lines)
        self.save()
    
    def __str__(self):
        return f"{self.transaction_number} - {self.transaction_date}"


class OtherExpenseLineItem(TimeStampedModel):
    """Line items for other expenses"""
    
    expense_transaction = models.ForeignKey(
        OtherExpenseTransaction,
        on_delete=models.CASCADE,
        related_name='line_items'
    )
    line_number = models.PositiveSmallIntegerField(default=1)
    
    expense_category = models.ForeignKey(
        ExpenseCategory,
        on_delete=models.PROTECT,
        limit_choices_to={'category_type__in': ['BOTH', 'CASHBOOK']},
        related_name='cashbook_lines'
    )
    description = models.CharField(max_length=200, blank=True)
    
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    tax_code = models.ForeignKey(TaxCode, on_delete=models.PROTECT)
    
    # Calculated
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
    
    class Meta:
        db_table = 'cashbook_other_expense_lines'
        ordering = ['line_number']
        unique_together = [['expense_transaction', 'line_number']]
        verbose_name = 'Other Expense Line Item'
        verbose_name_plural = 'Other Expense Line Items'
    
    def save(self, *args, **kwargs):
        self.tax_amount = self.amount * (self.tax_code.rate / 100)
        self.line_total = self.amount + self.tax_amount
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Line {self.line_number}: {self.expense_category.name}"


# ============================================================================
# BANK RECONCILIATION
# ============================================================================

class BankReconciliation(TimeStampedModel):
    """
    Bank reconciliation session
    Matches cash book with bank statement
    """
    
    reconciliation_date = models.DateField()
    statement_date = models.DateField(help_text="Bank statement date")
    
    bank_statement_balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Closing balance as per bank statement"
    )
    
    # System calculated
    cashbook_balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        editable=False,
        help_text="Balance as per cash book"
    )
    
    # Reconciling items
    unpresented_cheques_total = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        editable=False,
        help_text="Total unpresented cheques"
    )
    outstanding_deposits_total = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        editable=False,
        help_text="Deposits not yet on bank statement"
    )
    
    # Final balance
    reconciled_balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        editable=False,
        help_text="Should match bank statement"
    )
    
    difference = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        editable=False,
        help_text="Difference (should be zero)"
    )
    
    is_balanced = models.BooleanField(
        default=False,
        editable=False,
        help_text="Reconciliation is balanced"
    )
    
    STATUS_CHOICES = [
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='IN_PROGRESS'
    )
    
    notes = models.TextField(blank=True)
    
    performed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bank_reconciliations'
    )
    
    class Meta:
        db_table = 'bank_reconciliations'
        ordering = ['-reconciliation_date']
        verbose_name = 'Bank Reconciliation'
        verbose_name_plural = 'Bank Reconciliations'
    
    def __str__(self):
        return f"Reconciliation {self.reconciliation_date} - {self.status}"
    
    def calculate_balances(self):
        """Calculate reconciliation balances"""
        # This would be calculated based on transactions
        # For now, just calculate difference
        self.difference = abs(self.reconciled_balance - self.bank_statement_balance)
        self.is_balanced = (self.difference < Decimal('0.01'))  # Allow for rounding
        self.save()


# ============================================================================
# UNPRESENTED CHEQUE
# ============================================================================

class UnpresentedCheque(TimeStampedModel):
    """
    Cheques issued but not yet presented to bank
    Carried forward in bank reconciliation
    """
    
    cheque_number = models.CharField(max_length=50)
    cheque_date = models.DateField()
    payee = models.CharField(max_length=200, help_text="Who the cheque is made out to")
    
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    
    # When issued
    issued_date = models.DateField()
    issued_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cheques_issued'
    )
    
    # When presented/cleared
    is_presented = models.BooleanField(default=False)
    presented_date = models.DateField(null=True, blank=True)
    
    # Link to reconciliation where it cleared
    cleared_in_reconciliation = models.ForeignKey(
        BankReconciliation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cleared_cheques'
    )
    
    # Reference
    reference = models.CharField(max_length=200, blank=True)
    
    class Meta:
        db_table = 'unpresented_cheques'
        ordering = ['cheque_date', 'cheque_number']
        indexes = [
            models.Index(fields=['is_presented']),
            models.Index(fields=['cheque_date']),
        ]
        verbose_name = 'Unpresented Cheque'
        verbose_name_plural = 'Unpresented Cheques'
    
    def __str__(self):
        status = "Presented" if self.is_presented else "Unpresented"
        return f"Cheque {self.cheque_number} - {self.payee} - {status}"


# ============================================================================
# POST DATED CHEQUE REGISTER
# ============================================================================

class PostDatedChequeRegister(TimeStampedModel):
    """
    Central register of post-dated cheques from debtors
    Links to debtor PDCs for tracking and banking
    """
    
    debtor = models.ForeignKey(
        'debtors.Debtor',
        on_delete=models.PROTECT,
        related_name='pdc_register'
    )
    
    pdc = models.ForeignKey(
        'debtors.PostDatedCheque',
        on_delete=models.CASCADE,
        related_name='register_entries',
        help_text="Link to debtor's post-dated cheque"
    )
    
    # Quick reference fields (denormalized for reporting)
    cheque_date = models.DateField(help_text="Date on cheque")
    cheque_amount = models.DecimalField(max_digits=15, decimal_places=2)
    cheque_number = models.CharField(max_length=50, blank=True)
    bank_name = models.CharField(max_length=100, blank=True)
    
    # When to bank it
    banking_date = models.DateField(
        help_text="Date to present cheque to bank"
    )
    
    # Status
    STATUS_CHOICES = [
        ('PENDING', 'Awaiting Banking Date'),
        ('READY', 'Ready to Bank'),
        ('BANKED', 'Banked'),
        ('BOUNCED', 'Bounced/Returned'),
        ('CANCELLED', 'Cancelled'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING'
    )
    
    is_banked = models.BooleanField(default=False)
    banked_date = models.DateField(null=True, blank=True)
    banked_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pdcs_banked'
    )
    
    # If bounced
    is_bounced = models.BooleanField(default=False)
    bounce_date = models.DateField(null=True, blank=True)
    bounce_reason = models.CharField(max_length=200, blank=True)
    
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'pdc_register'
        ordering = ['banking_date', 'cheque_date']
        indexes = [
            models.Index(fields=['banking_date']),
            models.Index(fields=['status']),
            models.Index(fields=['is_banked']),
        ]
        verbose_name = 'PDC Register Entry'
        verbose_name_plural = 'PDC Register Entries'
    
    def __str__(self):
        return f"PDC {self.cheque_number} - {self.debtor.name} - {self.banking_date}"
    
    @property
    def is_ready_to_bank(self):
        """Check if ready to bank (date has arrived)"""
        from django.utils import timezone
        today = timezone.now().date()
        return not self.is_banked and self.banking_date <= today and self.status == 'PENDING'