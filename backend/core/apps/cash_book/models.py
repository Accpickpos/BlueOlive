"""
Cash Book Module Models
Handles cash/bank transactions, income, expenses, and bank reconciliation
"""
from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.utils import timezone
from decimal import Decimal
from apps.settings.models import TaxCode, ExpenseCategory, IncomeCategory, VATMixin, ReconciliationMixin
from .validators import (
    validate_positive_amount, validate_non_negative_amount,
    validate_transaction_date, validate_bank_account_number
)




class CashBookTransaction(VATMixin, ReconciliationMixin, models.Model):
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
    
    # Amount (legacy field - keep for backward compatibility)
    amount = models.DecimalField(max_digits=15, decimal_places=2, 
                                validators=[validate_positive_amount])
    
    # Category & Audit Fields (per spec)
    category_id = models.IntegerField(blank=True, null=True, 
                                     help_text="Category number from spec CATNO")
    audit_type = models.IntegerField(default=2, 
                                    choices=[(1, 'Accounts Receivable Receipts'),
                                            (2, 'Sundry Income'),
                                            (3, 'Accounts Payable Payments'),
                                            (4, 'Expenses')],
                                    help_text="GL account classification per CBAUDIT")
    bank_recon_tag = models.CharField(max_length=1, default='U',
                                     choices=[('R', 'Reconciled'),
                                             ('P', 'Pending'),
                                             ('D', 'Disputed'),
                                             ('U', 'Unreconciled')],
                                     help_text="Bank reconciliation tag per CBTAG")
    
    # References
    reference = models.CharField(max_length=20, blank=True, 
                                help_text="Additional reference per CBREF (max 20 chars)")
    description = models.CharField(max_length=200)
    
    # Reconciliation (for bank transactions) - FK reference retained for backward compatibility
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
            models.Index(fields=['audit_type', '-transaction_date']),
            models.Index(fields=['bank_recon_tag']),
            models.Index(fields=['category_id']),
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
                    'If you need to make changes, unreconcile it first.'
                )
        
        # Validate VAT integrity (per spec: TOTAL = VALUE + TAX)
        if self.value_excl_vat and self.tax_amount:
            expected_total = self.value_excl_vat + self.tax_amount
            if abs(self.total_incl_vat - expected_total) > Decimal('0.01'):
                raise ValidationError(
                    f'VAT calculation error: VALUE ({self.value_excl_vat}) + TAX ({self.tax_amount}) '
                    f'should equal TOTAL ({self.total_incl_vat})'
                )
        
        # Validate bank account is set for bank transactions
        if self.account_type == 'BANK' and not self.bank_account_number:
            raise ValidationError(
                'Bank account number is required for bank transactions'
            )
        
        # Validate transaction date is not in future
        if self.transaction_date > timezone.now().date():
            raise ValidationError('Transaction date cannot be in the future')
    
    def can_be_modified(self) -> bool:
        """Check if transaction can be modified"""
        return not self.is_reconciled
    
    def can_be_deleted(self) -> bool:
        """Check if transaction can be deleted"""
        return not self.is_reconciled
    
    def get_audit_type_display_name(self) -> str:
        """Get human-readable audit type name per spec CBAUDIT"""
        audit_map = {
            1: 'Accounts Receivable Receipts',
            2: 'Sundry Income',
            3: 'Accounts Payable Payments',
            4: 'Expenses'
        }
        return audit_map.get(self.audit_type, 'Unknown')
    
    def get_recon_tag_display(self) -> str:
        """Get human-readable reconciliation tag per spec CBTAG"""
        tag_map = {
            'R': 'Reconciled',
            'P': 'Pending',
            'D': 'Disputed',
            'U': 'Unreconciled'
        }
        return tag_map.get(self.bank_recon_tag, 'Unknown')
    
    @property
    def is_debit(self):
        """Check if transaction is a debit (increases cash/bank)"""
        return self.transaction_type in ['RECEIPT', 'DEPOSIT', 'INTEREST', 'OTHER_INCOME']
    
    @property
    def is_credit(self):
        """Check if transaction is a credit (decreases cash/bank)"""
        return self.transaction_type in ['PAYMENT', 'WITHDRAWAL', 'TRANSFER', 
                                         'BANK_CHARGE', 'OTHER_EXPENSE']
    
    @property
    def get_gl_account(self) -> str:
        """Get GL account code based on audit_type (per spec mapping)"""
        gl_accounts = {
            1: '1100',  # Accounts Receivable
            2: '2000',  # Sundry Income
            3: '2100',  # Accounts Payable
            4: '4000',  # Operating Expenses
        }
        return gl_accounts.get(self.audit_type, '9999')


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


class ExpenseCategoryBalance(models.Model):
    """Tracks monthly balances for expense categories"""
    
    expense_category = models.OneToOneField(ExpenseCategory, on_delete=models.CASCADE, 
                                            related_name='balance')
    
    # Current Month To Date
    balance_month_to_date = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    input_vat_month_to_date = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Monthly Balances
    balance_month_01 = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    balance_month_02 = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    balance_month_03 = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    balance_month_04 = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    balance_month_05 = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    balance_month_06 = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    balance_month_07 = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    balance_month_08 = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    balance_month_09 = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    balance_month_10 = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    balance_month_11 = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    balance_month_12 = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'expense_category_balances'
        verbose_name = 'Expense Category Balance'
        verbose_name_plural = 'Expense Category Balances'
    
    def __str__(self):
        return f"Balance - {self.expense_category.name}"
    
    @property
    def year_to_date_balance(self):
        """Calculate year-to-date balance per spec EXP1-EXP12"""
        return (
            self.balance_month_01 + self.balance_month_02 + self.balance_month_03 +
            self.balance_month_04 + self.balance_month_05 + self.balance_month_06 +
            self.balance_month_07 + self.balance_month_08 + self.balance_month_09 +
            self.balance_month_10 + self.balance_month_11 + self.balance_month_12
        )
    
    def get_monthly_balances(self):
        """Return monthly balances as a dictionary per spec"""
        return {
            'month_01': self.balance_month_01,
            'month_02': self.balance_month_02,
            'month_03': self.balance_month_03,
            'month_04': self.balance_month_04,
            'month_05': self.balance_month_05,
            'month_06': self.balance_month_06,
            'month_07': self.balance_month_07,
            'month_08': self.balance_month_08,
            'month_09': self.balance_month_09,
            'month_10': self.balance_month_10,
            'month_11': self.balance_month_11,
            'month_12': self.balance_month_12,
        }
    
    def get_month_balance(self, month_num: int) -> Decimal:
        """Get balance for specific month (1-12) per spec"""
        field_name = f'balance_month_{month_num:02d}'
        return getattr(self, field_name, Decimal('0'))
    
    def set_month_balance(self, month_num: int, value: Decimal):
        """Set balance for specific month (1-12) with validation"""
        field_name = f'balance_month_{month_num:02d}'
        if hasattr(self, field_name):
            setattr(self, field_name, value)
            self.save()
    
    def calculate_mtd_from_transactions(self):
        """Recalculate EXPMTD from actual transactions (per spec business logic)"""
        from django.utils import timezone
        from datetime import date
        today = timezone.now().date()
        current_month_start = date(today.year, today.month, 1)
        
        transactions = CashBookTransaction.objects.filter(
            other_expense__expense_category=self.expense_category,
            transaction_date__gte=current_month_start,
            transaction_date__lte=today
        )
        
        mtd_balance = sum(t.value_excl_vat for t in transactions if t.value_excl_vat)
        mtd_vat = sum(t.tax_amount for t in transactions if t.tax_amount)
        
        self.balance_month_to_date = mtd_balance
        self.input_vat_month_to_date = mtd_vat
        return mtd_balance, mtd_vat


class IncomeCategoryBalance(models.Model):
    """Tracks monthly balances for income categories"""
    
    income_category = models.OneToOneField(IncomeCategory, on_delete=models.CASCADE, 
                                           related_name='balance')
    
    # Current Month To Date
    balance_month_to_date = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    output_vat_month_to_date = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Monthly Balances
    balance_month_01 = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    balance_month_02 = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    balance_month_03 = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    balance_month_04 = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    balance_month_05 = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    balance_month_06 = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    balance_month_07 = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    balance_month_08 = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    balance_month_09 = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    balance_month_10 = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    balance_month_11 = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    balance_month_12 = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'income_category_balances'
        verbose_name = 'Income Category Balance'
        verbose_name_plural = 'Income Category Balances'
    
    def __str__(self):
        return f"Balance - {self.income_category.name}"
    
    @property
    def year_to_date_balance(self):
        """Calculate year-to-date balance per spec INC1-INC12"""
        return (
            self.balance_month_01 + self.balance_month_02 + self.balance_month_03 +
            self.balance_month_04 + self.balance_month_05 + self.balance_month_06 +
            self.balance_month_07 + self.balance_month_08 + self.balance_month_09 +
            self.balance_month_10 + self.balance_month_11 + self.balance_month_12
        )
    
    def get_monthly_balances(self):
        """Return monthly balances as a dictionary per spec"""
        return {
            'month_01': self.balance_month_01,
            'month_02': self.balance_month_02,
            'month_03': self.balance_month_03,
            'month_04': self.balance_month_04,
            'month_05': self.balance_month_05,
            'month_06': self.balance_month_06,
            'month_07': self.balance_month_07,
            'month_08': self.balance_month_08,
            'month_09': self.balance_month_09,
            'month_10': self.balance_month_10,
            'month_11': self.balance_month_11,
            'month_12': self.balance_month_12,
        }
    
    def get_month_balance(self, month_num: int) -> Decimal:
        """Get balance for specific month (1-12) per spec"""
        field_name = f'balance_month_{month_num:02d}'
        return getattr(self, field_name, Decimal('0'))
    
    def set_month_balance(self, month_num: int, value: Decimal):
        """Set balance for specific month (1-12) with validation"""
        field_name = f'balance_month_{month_num:02d}'
        if hasattr(self, field_name):
            setattr(self, field_name, value)
            self.save()
    
    def calculate_mtd_from_transactions(self):
        """Recalculate INCMTD from actual transactions (per spec business logic)"""
        from django.utils import timezone
        from datetime import date
        today = timezone.now().date()
        current_month_start = date(today.year, today.month, 1)
        
        transactions = CashBookTransaction.objects.filter(
            other_income__income_category=self.income_category,
            transaction_date__gte=current_month_start,
            transaction_date__lte=today
        )
        
        mtd_balance = sum(t.value_excl_vat for t in transactions if t.value_excl_vat)
        mtd_vat = sum(t.tax_amount for t in transactions if t.tax_amount)
        
        self.balance_month_to_date = mtd_balance
        self.output_vat_month_to_date = mtd_vat
        return mtd_balance, mtd_vat


class UnpresentedCheque(models.Model):
    """
    Tracks unpresented cheques (per spec CBCHEQ)
    Cheques issued but not yet presented at bank after month-end
    
    Field mapping:
    CBTRANO -> cheque_number (6 numeric)
    CBREF -> reference (20 char)
    DATE -> cheque_date (date)
    VALUE -> value (10,2 numeric)
    TAX -> tax_code (10,2 numeric)
    TOTAL -> total (10,2 numeric)
    CBTAG -> tag (1 char)
    """
    
    TAG_CHOICES = [
        ('R', 'Reconciled'),
        ('P', 'Pending'),
        ('D', 'Disputed'),
        ('U', 'Unreconciled'),
    ]
    
    # Cheque Details (per spec CBCHEQ)
    cheque_number = models.CharField(max_length=6, unique=True, db_index=True,
                                     help_text="Transaction # per spec CBTRANO")
    cheque_date = models.DateField(db_index=True,
                                   help_text="Transaction date per spec DATE")
    reference = models.CharField(max_length=20, blank=True,
                                help_text="Additional ref per spec CBREF")
    
    # Amounts (per spec: VALUE, TAX, TOTAL)
    value = models.DecimalField(max_digits=10, decimal_places=2,
                               help_text="Value excluding VAT per spec VALUE")
    tax_code = models.IntegerField(default=1,
                                  help_text="Tax code per spec TAX (field size 10,2)")
    total = models.DecimalField(max_digits=10, decimal_places=2,
                               help_text="Total including VAT per spec TOTAL")
    
    # Reconciliation Tag (per spec CBTAG)
    tag = models.CharField(max_length=1, choices=TAG_CHOICES, default='U',
                          help_text="Bank reconciliation tag per spec CBTAG")
    
    # Bank Presentation Status
    is_presented = models.BooleanField(default=False, db_index=True,
                                      help_text="Has cheque been presented at bank")
    presented_date = models.DateField(null=True, blank=True,
                                     help_text="Date cheque appeared on bank statement")
    
    # Month-end tracking (per spec: relates to reconciliation period)
    month_end_date = models.DateField(db_index=True,
                                     help_text="Month-end date this cheque relates to")
    
    # Aging tracking
    days_outstanding = models.IntegerField(default=0,
                                          help_text="Days since cheque date")
    is_stale = models.BooleanField(default=False, db_index=True,
                                  help_text="True if >6 months old (stale cheque)")
    requires_follow_up = models.BooleanField(default=False,
                                            help_text="True if >3 months outstanding")
    
    # Notes for dispute/resolution
    notes = models.TextField(blank=True,
                            help_text="Dispute notes or resolution information")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'unpresented_cheques'
        verbose_name = 'Unpresented Cheque'
        verbose_name_plural = 'Unpresented Cheques'
        ordering = ['-cheque_date', '-cheque_number']
        indexes = [
            models.Index(fields=['cheque_number']),
            models.Index(fields=['-cheque_date']),
            models.Index(fields=['tag']),
            models.Index(fields=['is_presented']),
            models.Index(fields=['is_stale']),
            models.Index(fields=['requires_follow_up']),
        ]
    
    def __str__(self):
        return f"Cheque {self.cheque_number} - {self.cheque_date}"
    
    def clean(self):
        """Validate cheque per spec business rules"""
        # Validate VAT integrity: TOTAL should equal VALUE + TAX proportional
        if self.value and self.tax_code and self.total:
            # Tax code field actually contains numeric 10,2 per spec, but we treat it as code
            # The total validation ensures amount consistency
            if self.total < self.value:
                raise ValidationError(
                    f'Total ({self.total}) must be >= Value ({self.value})'
                )
        
        # Cheque date cannot be in future
        if self.cheque_date > timezone.now().date():
            raise ValidationError('Cheque date cannot be in the future')
        
        # Month-end date should reference the period month
        if self.month_end_date < self.cheque_date:
            raise ValidationError(
                'Month-end date must be on or after cheque date'
            )
    
    def save(self, *args, **kwargs):
        """Override save to calculate aging fields"""
        from django.utils import timezone
        from datetime import timedelta
        
        today = timezone.now().date()
        self.days_outstanding = (today - self.cheque_date).days
        
        # Flag stale cheques (>6 months / 180 days)
        self.is_stale = self.days_outstanding > 180
        
        # Flag for follow-up if >3 months (90 days) and not presented
        if not self.is_presented:
            self.requires_follow_up = self.days_outstanding > 90
        
        super().save(*args, **kwargs)
    
    def mark_as_presented(self, presented_date=None):
        """Mark cheque as presented at bank"""
        if presented_date is None:
            presented_date = timezone.now().date()
        
        self.is_presented = True
        self.presented_date = presented_date
        self.tag = 'R'  # Mark as reconciled
        self.requires_follow_up = False
        self.save()
    
    def get_age_in_months(self) -> int:
        """Get how many months the cheque has been outstanding"""
        return self.days_outstanding // 30
    
    def is_overdue_for_follow_up(self) -> bool:
        """Check if cheque requires follow-up (>3 months outstanding)"""
        return self.days_outstanding > 90 and not self.is_presented
    
    @classmethod
    def get_unpresented_summary(cls, as_of_date=None):
        """Get summary of all unpresented cheques for reconciliation"""
        if as_of_date is None:
            as_of_date = timezone.now().date()
        
        unpresented = cls.objects.filter(
            is_presented=False,
            cheque_date__lte=as_of_date
        )
        
        return {
            'count': unpresented.count(),
            'total_value': unpresented.aggregate(
                total=models.Sum('value')
            )['total'] or Decimal('0'),
            'by_age': {
                'stale': unpresented.filter(is_stale=True).count(),
                'follow_up': unpresented.filter(requires_follow_up=True).count(),
                'current': unpresented.filter(
                    days_outstanding__lte=90
                ).count(),
            }
        }