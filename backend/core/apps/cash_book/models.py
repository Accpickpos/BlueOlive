"""
Cash Book Module Models
Handles cash/bank transactions, income, expenses, and bank reconciliation
"""
from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from decimal import Decimal
from apps.settings.models import TaxCode, ExpenseCategory, IncomeCategory
from .validators import (
    validate_positive_amount, validate_non_negative_amount,
    validate_transaction_date, validate_bank_account_number
)



class CashBookTransaction(models.Model):
    """Base model for all cash book transactions"""
    
    TRANSACTION_TYPE_CHOICES = [
        ('RECEIPT', 'Cash Receipt'),
        ('PAYMENT', 'Cash Payment'),
        ('DEPOSIT', 'Bank Deposit'),
        ('WITHDRAWAL', 'Bank Withdrawal'),
        ('TRANSFER', 'Bank Transfer'),
        ('BANK_CHARGE', 'Bank Charge'),
        ('INTEREST', 'Interest Received'),
        ('OTHER_INCOME', 'Other Income'),
        ('OTHER_EXPENSE', 'Other Expense'),
    ]
    
    ACCOUNT_TYPE_CHOICES = [
        ('CASH', 'Cash on Hand'),
        ('BANK', 'Bank Account'),
    ]
    
    # Transaction Details
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES)
    transaction_number = models.CharField(max_length=20, unique=True, db_index=True)
    transaction_date = models.DateField(db_index=True)
    
    # Account
    account_type = models.CharField(max_length=10, choices=ACCOUNT_TYPE_CHOICES, default='CASH')
    bank_account_number = models.CharField(max_length=50, blank=True, 
                                          help_text="For bank transactions",
                                          validators=[validate_bank_account_number])
    
    # Amount
    amount = models.DecimalField(max_digits=15, decimal_places=2, 
                                validators=[validate_positive_amount])
    
    # References
    reference = models.CharField(max_length=100, blank=True)
    description = models.CharField(max_length=200)
    
    # Reconciliation (for bank transactions)
    is_reconciled = models.BooleanField(default=False)
    reconciliation = models.ForeignKey('BankReconciliation', on_delete=models.SET_NULL, 
                                      null=True, blank=True, related_name='transactions')
    
    # Running Balance (updated by signals)
    running_balance_cash = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    running_balance_bank = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.CharField(max_length=50, blank=True)
    
    # Archive tracking
    is_archived = models.BooleanField(default=False)
    archive_month = models.DateField(null=True, blank=True)
    
    class Meta:
        db_table = 'cashbook_transactions'
        ordering = ['-transaction_date', '-transaction_number']
        indexes = [
            models.Index(fields=['transaction_type', '-transaction_date']),
            models.Index(fields=['transaction_number']),
            models.Index(fields=['is_reconciled']),
            models.Index(fields=['is_archived', 'archive_month']),
        ]
    
    def __str__(self):
        return f"{self.transaction_type} - {self.transaction_number}"
    
    def clean(self):
        """Validate transaction before save"""
        # Check if reconciled
        if self.pk:  # Only check on update
            original = CashBookTransaction.objects.get(pk=self.pk)
            if original.is_reconciled:
                raise ValidationError(
                    'Cannot modify a reconciled transaction. '
                    'If you need to make changes, unreconci le it first.'
                )
        
        # Validate bank account is set for bank transactions
        if self.account_type == 'BANK' and not self.bank_account_number:
            raise ValidationError(
                'Bank account number is required for bank transactions'
            )
    
    def can_be_modified(self) -> bool:
        """Check if transaction can be modified"""
        return not self.is_reconciled
    
    def can_be_deleted(self) -> bool:
        """Check if transaction can be deleted"""
        return not self.is_reconciled
    
    @property
    def is_debit(self):
        """Check if transaction is a debit (increases cash/bank)"""
        return self.transaction_type in ['RECEIPT', 'DEPOSIT', 'INTEREST', 'OTHER_INCOME']
    
    @property
    def is_credit(self):
        """Check if transaction is a credit (decreases cash/bank)"""
        return self.transaction_type in ['PAYMENT', 'WITHDRAWAL', 'TRANSFER', 
                                         'BANK_CHARGE', 'OTHER_EXPENSE']


class OtherIncome(models.Model):
    """Other income transactions (non-sales revenue)"""
    transaction = models.OneToOneField(CashBookTransaction, on_delete=models.CASCADE, 
                                      related_name='other_income')
    
    # Income Details
    income_category = models.ForeignKey(IncomeCategory, on_delete=models.PROTECT)
    
    # Tax
    is_vat_inclusive = models.BooleanField(default=True)
    vat_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    tax_code = models.IntegerField(default=1, help_text="1=14%, 2=0%")
    
    # Payment method
    paid_into = models.CharField(max_length=20, choices=[
        ('CASH', 'Cash Till'),
        ('BANK', 'Bank Account')
    ], default='CASH')
    
    class Meta:
        db_table = 'other_income'
        verbose_name = 'Other Income'
        verbose_name_plural = 'Other Income'
    
    def __str__(self):
        return f"Income {self.transaction.transaction_number}"


class OtherExpense(models.Model):
    """Other expense transactions (cash/petty cash expenses)"""
    transaction = models.OneToOneField(CashBookTransaction, on_delete=models.CASCADE, 
                                      related_name='other_expense')
    
    # Expense Details
    expense_category = models.ForeignKey('settings.ExpenseCategory', on_delete=models.PROTECT)
    
    # Tax
    is_vat_inclusive = models.BooleanField(default=True)
    vat_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    tax_code = models.IntegerField(default=1)
    
    # Payment method
    paid_from = models.CharField(max_length=20, choices=[
        ('CASH', 'Cash Till'),
        ('BANK', 'Bank Account')
    ], default='CASH')
    
    # Petty cash slip
    petty_cash_slip_number = models.CharField(max_length=20, blank=True)
    
    class Meta:
        db_table = 'other_expenses'
        verbose_name = 'Other Expense'
    
    def __str__(self):
        return f"Expense {self.transaction.transaction_number}"


class BankDeposit(models.Model):
    """Bank deposits (cash to bank transfers)"""
    transaction = models.OneToOneField(CashBookTransaction, on_delete=models.CASCADE, 
                                      related_name='bank_deposit')
    
    # Deposit Details
    deposit_slip_number = models.CharField(max_length=50, blank=True)
    bank_name = models.CharField(max_length=100)
    branch = models.CharField(max_length=100, blank=True)
    
    # Components
    cash_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    cheque_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Breakdown of cash/coins (optional)
    notes_200 = models.IntegerField(default=0)
    notes_100 = models.IntegerField(default=0)
    notes_50 = models.IntegerField(default=0)
    notes_20 = models.IntegerField(default=0)
    notes_10 = models.IntegerField(default=0)
    coins_5 = models.IntegerField(default=0)
    coins_2 = models.IntegerField(default=0)
    coins_1 = models.IntegerField(default=0)
    coins_050 = models.IntegerField(default=0, verbose_name='50c coins')
    coins_020 = models.IntegerField(default=0, verbose_name='20c coins')
    coins_010 = models.IntegerField(default=0, verbose_name='10c coins')
    coins_005 = models.IntegerField(default=0, verbose_name='5c coins')
    
    class Meta:
        db_table = 'bank_deposits'
        verbose_name = 'Bank Deposit'
    
    def __str__(self):
        return f"Deposit {self.transaction.transaction_number}"
    
    @property
    def calculated_cash_total(self):
        """Calculate total from notes/coins breakdown"""
        total = Decimal('0')
        total += self.notes_200 * Decimal('200')
        total += self.notes_100 * Decimal('100')
        total += self.notes_50 * Decimal('50')
        total += self.notes_20 * Decimal('20')
        total += self.notes_10 * Decimal('10')
        total += self.coins_5 * Decimal('5')
        total += self.coins_2 * Decimal('2')
        total += self.coins_1 * Decimal('1')
        total += self.coins_050 * Decimal('0.50')
        total += self.coins_020 * Decimal('0.20')
        total += self.coins_010 * Decimal('0.10')
        total += self.coins_005 * Decimal('0.05')
        return total


class CashWithdrawal(models.Model):
    """Cash withdrawals from bank"""
    transaction = models.OneToOneField(CashBookTransaction, on_delete=models.CASCADE, 
                                      related_name='cash_withdrawal')
    
    # Withdrawal Details
    withdrawal_slip_number = models.CharField(max_length=50, blank=True)
    withdrawn_by = models.CharField(max_length=100)
    purpose = models.CharField(max_length=200)
    
    class Meta:
        db_table = 'cash_withdrawals'
        verbose_name = 'Cash Withdrawal'
    
    def __str__(self):
        return f"Withdrawal {self.transaction.transaction_number}"


class BankTransfer(models.Model):
    """Transfers between bank accounts"""
    transaction = models.OneToOneField(CashBookTransaction, on_delete=models.CASCADE, 
                                      related_name='bank_transfer')
    
    # Transfer Details
    from_account = models.CharField(max_length=50)
    to_account = models.CharField(max_length=50)
    transfer_reference = models.CharField(max_length=100, blank=True)
    
    # Fees
    transfer_fee = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    class Meta:
        db_table = 'bank_transfers'
        verbose_name = 'Bank Transfer'
    
    def __str__(self):
        return f"Transfer {self.transaction.transaction_number}"


class BankCharge(models.Model):
    """Bank charges and fees"""
    transaction = models.OneToOneField(CashBookTransaction, on_delete=models.CASCADE, 
                                      related_name='bank_charge')
    
    # Charge Details
    charge_type = models.CharField(max_length=100, choices=[
        ('MONTHLY_FEE', 'Monthly Account Fee'),
        ('TRANSACTION_FEE', 'Transaction Fee'),
        ('ATM_FEE', 'ATM Fee'),
        ('OVERDRAFT', 'Overdraft Charge'),
        ('CARD_FEE', 'Card Fee'),
        ('OTHER', 'Other Charge'),
    ])
    statement_reference = models.CharField(max_length=100, blank=True)
    
    class Meta:
        db_table = 'bank_charges'
        verbose_name = 'Bank Charge'
    
    def __str__(self):
        return f"Bank Charge {self.transaction.transaction_number}"


class InterestReceived(models.Model):
    """Interest received from bank accounts"""
    transaction = models.OneToOneField(CashBookTransaction, on_delete=models.CASCADE, 
                                      related_name='interest_received')
    
    # Interest Details
    interest_period_start = models.DateField()
    interest_period_end = models.DateField()
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    class Meta:
        db_table = 'interest_received'
        verbose_name = 'Interest Received'
    
    def __str__(self):
        return f"Interest {self.transaction.transaction_number}"


class BankReconciliation(models.Model):
    """Bank reconciliation records"""
    
    STATUS_CHOICES = [
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('REVIEWED', 'Reviewed'),
    ]
    
    # Reconciliation Details
    reconciliation_number = models.CharField(max_length=20, unique=True, db_index=True)
    reconciliation_date = models.DateField()
    bank_account_number = models.CharField(max_length=50)
    
    # Statement Details
    statement_date = models.DateField()
    statement_number = models.CharField(max_length=50, blank=True)
    
    # Balances
    opening_balance = models.DecimalField(max_digits=15, decimal_places=2)
    closing_balance_per_statement = models.DecimalField(max_digits=15, decimal_places=2)
    closing_balance_per_books = models.DecimalField(max_digits=15, decimal_places=2)
    
    # Reconciliation Items
    outstanding_deposits = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    outstanding_cheques = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    bank_errors = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    book_errors = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='IN_PROGRESS')
    
    # Notes
    notes = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    completed_by = models.CharField(max_length=50, blank=True)
    
    class Meta:
        db_table = 'bank_reconciliations'
        ordering = ['-reconciliation_date', '-reconciliation_number']
        indexes = [
            models.Index(fields=['bank_account_number', '-reconciliation_date']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"Reconciliation {self.reconciliation_number} - {self.statement_date}"
    
    @property
    def is_balanced(self):
        """Check if reconciliation balances"""
        calculated_balance = (
            self.closing_balance_per_statement + 
            self.outstanding_deposits - 
            self.outstanding_cheques + 
            self.bank_errors - 
            self.book_errors
        )
        return abs(calculated_balance - self.closing_balance_per_books) < Decimal('0.01')
    
    @property
    def difference(self):
        """Calculate difference between statement and books"""
        calculated_balance = (
            self.closing_balance_per_statement + 
            self.outstanding_deposits - 
            self.outstanding_cheques + 
            self.bank_errors - 
            self.book_errors
        )
        return self.closing_balance_per_books - calculated_balance


class BankReconciliationItem(models.Model):
    """Individual items in bank reconciliation"""
    
    ITEM_TYPE_CHOICES = [
        ('OUTSTANDING_DEPOSIT', 'Outstanding Deposit'),
        ('OUTSTANDING_CHEQUE', 'Outstanding Cheque'),
        ('BANK_ERROR', 'Bank Error'),
        ('BOOK_ERROR', 'Book Error'),
        ('UNRECORDED_BANK', 'Unrecorded Bank Transaction'),
        ('UNRECORDED_BOOK', 'Unrecorded Book Transaction'),
    ]
    
    reconciliation = models.ForeignKey(BankReconciliation, on_delete=models.CASCADE, 
                                      related_name='items')
    
    # Item Details
    item_type = models.CharField(max_length=30, choices=ITEM_TYPE_CHOICES)
    transaction = models.ForeignKey(CashBookTransaction, on_delete=models.SET_NULL, 
                                   null=True, blank=True, related_name='reconciliation_items')
    
    # Manual Entry (if no transaction linked)
    manual_date = models.DateField(null=True, blank=True)
    manual_reference = models.CharField(max_length=100, blank=True)
    manual_description = models.CharField(max_length=200, blank=True)
    manual_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Resolution
    is_resolved = models.BooleanField(default=False)
    resolution_notes = models.TextField(blank=True)
    resolved_date = models.DateField(null=True, blank=True)
    
    class Meta:
        db_table = 'bank_reconciliation_items'
        ordering = ['reconciliation', 'item_type']
    
    def __str__(self):
        return f"{self.reconciliation.reconciliation_number} - {self.item_type}"
    
    @property
    def amount(self):
        """Get amount from transaction or manual entry"""
        if self.transaction:
            return self.transaction.amount
        return self.manual_amount
    
    @property
    def description(self):
        """Get description from transaction or manual entry"""
        if self.transaction:
            return self.transaction.description
        return self.manual_description


class CashFloat(models.Model):
    """Cash float/till management"""
    
    float_date = models.DateField(unique=True, db_index=True)
    
    # Opening
    opening_float = models.DecimalField(max_digits=15, decimal_places=2)
    
    # Cash movements
    cash_sales = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    cash_receipts = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    cash_payments = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Banking
    banked_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Counted cash
    counted_cash = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Cash breakdown
    notes_200 = models.IntegerField(default=0)
    notes_100 = models.IntegerField(default=0)
    notes_50 = models.IntegerField(default=0)
    notes_20 = models.IntegerField(default=0)
    notes_10 = models.IntegerField(default=0)
    coins_5 = models.IntegerField(default=0)
    coins_2 = models.IntegerField(default=0)
    coins_1 = models.IntegerField(default=0)
    coins_050 = models.IntegerField(default=0)
    coins_020 = models.IntegerField(default=0)
    coins_010 = models.IntegerField(default=0)
    coins_005 = models.IntegerField(default=0)
    
    # Variance
    variance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    variance_notes = models.TextField(blank=True)
    
    # Status
    is_balanced = models.BooleanField(default=False)
    counted_by = models.CharField(max_length=100, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'cash_floats'
        ordering = ['-float_date']
        verbose_name = 'Cash Float'
    
    def __str__(self):
        return f"Cash Float - {self.float_date}"
    
    @property
    def expected_cash(self):
        """Calculate expected cash in till"""
        return (
            self.opening_float + 
            self.cash_sales + 
            self.cash_receipts - 
            self.cash_payments - 
            self.banked_amount
        )
    
    @property
    def calculated_counted_cash(self):
        """Calculate total from notes/coins breakdown"""
        total = Decimal('0')
        total += self.notes_200 * Decimal('200')
        total += self.notes_100 * Decimal('100')
        total += self.notes_50 * Decimal('50')
        total += self.notes_20 * Decimal('20')
        total += self.notes_10 * Decimal('10')
        total += self.coins_5 * Decimal('5')
        total += self.coins_2 * Decimal('2')
        total += self.coins_1 * Decimal('1')
        total += self.coins_050 * Decimal('0.50')
        total += self.coins_020 * Decimal('0.20')
        total += self.coins_010 * Decimal('0.10')
        total += self.coins_005 * Decimal('0.05')
        return total