"""
Cash Book Module Serializers
"""
from rest_framework import serializers
from .models import (
    IncomeCategory, CashBookTransaction, OtherIncome, OtherExpense,
    BankDeposit, CashWithdrawal, BankTransfer, BankCharge, InterestReceived,
    BankReconciliation, BankReconciliationItem, CashFloat
)


class IncomeCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = IncomeCategory
        fields = '__all__'


class CashBookTransactionSerializer(serializers.ModelSerializer):
    is_debit = serializers.BooleanField(read_only=True)
    is_credit = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = CashBookTransaction
        fields = '__all__'
        read_only_fields = ('running_balance_cash', 'running_balance_bank', 
                           'is_reconciled', 'reconciliation', 'is_archived', 'archive_month')


class CashBookTransactionListSerializer(serializers.ModelSerializer):
    """Simplified serializer for transaction listings"""
    is_debit = serializers.BooleanField(read_only=True)
    is_credit = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = CashBookTransaction
        fields = ('id', 'transaction_type', 'transaction_number', 'transaction_date',
                 'amount', 'description', 'reference', 'account_type', 
                 'is_reconciled', 'is_debit', 'is_credit')


# Other Income Serializers
class OtherIncomeSerializer(serializers.ModelSerializer):
    transaction = CashBookTransactionSerializer(read_only=True)
    category_name = serializers.CharField(source='income_category.name', read_only=True)
    
    class Meta:
        model = OtherIncome
        fields = '__all__'
        read_only_fields = ('transaction',)


class CreateOtherIncomeSerializer(serializers.Serializer):
    transaction_date = serializers.DateField()
    income_category_id = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    is_vat_inclusive = serializers.BooleanField(default=True)
    tax_code = serializers.IntegerField(default=1)
    description = serializers.CharField(max_length=200)
    reference = serializers.CharField(max_length=100, required=False, allow_blank=True)
    paid_into = serializers.ChoiceField(choices=['CASH', 'BANK'], default='CASH')
    bank_account_number = serializers.CharField(max_length=50, required=False, allow_blank=True)


# Other Expense Serializers
class OtherExpenseSerializer(serializers.ModelSerializer):
    transaction = CashBookTransactionSerializer(read_only=True)
    category_name = serializers.CharField(source='expense_category.name', read_only=True)
    
    class Meta:
        model = OtherExpense
        fields = '__all__'
        read_only_fields = ('transaction',)


class CreateOtherExpenseSerializer(serializers.Serializer):
    transaction_date = serializers.DateField()
    expense_category_id = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    is_vat_inclusive = serializers.BooleanField(default=True)
    tax_code = serializers.IntegerField(default=1)
    description = serializers.CharField(max_length=200)
    reference = serializers.CharField(max_length=100, required=False, allow_blank=True)
    paid_from = serializers.ChoiceField(choices=['CASH', 'BANK'], default='CASH')
    bank_account_number = serializers.CharField(max_length=50, required=False, allow_blank=True)
    petty_cash_slip_number = serializers.CharField(max_length=20, required=False, allow_blank=True)


# Bank Deposit Serializers
class BankDepositSerializer(serializers.ModelSerializer):
    transaction = CashBookTransactionSerializer(read_only=True)
    calculated_cash_total = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    
    class Meta:
        model = BankDeposit
        fields = '__all__'
        read_only_fields = ('transaction',)


class CreateBankDepositSerializer(serializers.Serializer):
    transaction_date = serializers.DateField()
    bank_account_number = serializers.CharField(max_length=50)
    bank_name = serializers.CharField(max_length=100)
    branch = serializers.CharField(max_length=100, required=False, allow_blank=True)
    deposit_slip_number = serializers.CharField(max_length=50, required=False, allow_blank=True)
    
    cash_amount = serializers.DecimalField(max_digits=15, decimal_places=2, default=0)
    cheque_amount = serializers.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Notes/coins breakdown (optional)
    notes_200 = serializers.IntegerField(default=0, required=False)
    notes_100 = serializers.IntegerField(default=0, required=False)
    notes_50 = serializers.IntegerField(default=0, required=False)
    notes_20 = serializers.IntegerField(default=0, required=False)
    notes_10 = serializers.IntegerField(default=0, required=False)
    coins_5 = serializers.IntegerField(default=0, required=False)
    coins_2 = serializers.IntegerField(default=0, required=False)
    coins_1 = serializers.IntegerField(default=0, required=False)
    coins_050 = serializers.IntegerField(default=0, required=False)
    coins_020 = serializers.IntegerField(default=0, required=False)
    coins_010 = serializers.IntegerField(default=0, required=False)
    coins_005 = serializers.IntegerField(default=0, required=False)
    
    reference = serializers.CharField(max_length=100, required=False, allow_blank=True)
    description = serializers.CharField(max_length=200, default='Bank deposit')


# Cash Withdrawal Serializers
class CashWithdrawalSerializer(serializers.ModelSerializer):
    transaction = CashBookTransactionSerializer(read_only=True)
    
    class Meta:
        model = CashWithdrawal
        fields = '__all__'
        read_only_fields = ('transaction',)


class CreateCashWithdrawalSerializer(serializers.Serializer):
    transaction_date = serializers.DateField()
    bank_account_number = serializers.CharField(max_length=50)
    amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    withdrawal_slip_number = serializers.CharField(max_length=50, required=False, allow_blank=True)
    withdrawn_by = serializers.CharField(max_length=100)
    purpose = serializers.CharField(max_length=200)
    reference = serializers.CharField(max_length=100, required=False, allow_blank=True)


# Bank Transfer Serializers
class BankTransferSerializer(serializers.ModelSerializer):
    transaction = CashBookTransactionSerializer(read_only=True)
    
    class Meta:
        model = BankTransfer
        fields = '__all__'
        read_only_fields = ('transaction',)


class CreateBankTransferSerializer(serializers.Serializer):
    transaction_date = serializers.DateField()
    from_account = serializers.CharField(max_length=50)
    to_account = serializers.CharField(max_length=50)
    amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    transfer_reference = serializers.CharField(max_length=100, required=False, allow_blank=True)
    transfer_fee = serializers.DecimalField(max_digits=15, decimal_places=2, default=0, required=False)
    description = serializers.CharField(max_length=200, default='Bank transfer')


# Bank Charge Serializers
class BankChargeSerializer(serializers.ModelSerializer):
    transaction = CashBookTransactionSerializer(read_only=True)
    
    class Meta:
        model = BankCharge
        fields = '__all__'
        read_only_fields = ('transaction',)


class CreateBankChargeSerializer(serializers.Serializer):
    transaction_date = serializers.DateField()
    bank_account_number = serializers.CharField(max_length=50)
    amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    charge_type = serializers.ChoiceField(choices=[
        'MONTHLY_FEE', 'TRANSACTION_FEE', 'ATM_FEE', 'OVERDRAFT', 'CARD_FEE', 'OTHER'
    ])
    statement_reference = serializers.CharField(max_length=100, required=False, allow_blank=True)
    description = serializers.CharField(max_length=200, required=False)


# Interest Received Serializers
class InterestReceivedSerializer(serializers.ModelSerializer):
    transaction = CashBookTransactionSerializer(read_only=True)
    
    class Meta:
        model = InterestReceived
        fields = '__all__'
        read_only_fields = ('transaction',)


class CreateInterestReceivedSerializer(serializers.Serializer):
    transaction_date = serializers.DateField()
    bank_account_number = serializers.CharField(max_length=50)
    amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    interest_period_start = serializers.DateField()
    interest_period_end = serializers.DateField()
    interest_rate = serializers.DecimalField(max_digits=5, decimal_places=2, default=0)
    reference = serializers.CharField(max_length=100, required=False, allow_blank=True)
    description = serializers.CharField(max_length=200, default='Interest received')


# Bank Reconciliation Serializers
class BankReconciliationItemSerializer(serializers.ModelSerializer):
    amount = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    description = serializers.CharField(read_only=True)
    
    class Meta:
        model = BankReconciliationItem
        fields = '__all__'
        read_only_fields = ('reconciliation',)


class BankReconciliationSerializer(serializers.ModelSerializer):
    items = BankReconciliationItemSerializer(many=True, read_only=True)
    is_balanced = serializers.BooleanField(read_only=True)
    difference = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    
    class Meta:
        model = BankReconciliation
        fields = '__all__'
        read_only_fields = ('reconciliation_number', 'completed_at', 'completed_by')


class BankReconciliationListSerializer(serializers.ModelSerializer):
    is_balanced = serializers.BooleanField(read_only=True)
    difference = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    
    class Meta:
        model = BankReconciliation
        fields = ('id', 'reconciliation_number', 'reconciliation_date', 'statement_date',
                 'bank_account_number', 'closing_balance_per_statement', 
                 'closing_balance_per_books', 'status', 'is_balanced', 'difference')


class CreateBankReconciliationSerializer(serializers.Serializer):
    reconciliation_date = serializers.DateField()
    bank_account_number = serializers.CharField(max_length=50)
    statement_date = serializers.DateField()
    statement_number = serializers.CharField(max_length=50, required=False, allow_blank=True)
    opening_balance = serializers.DecimalField(max_digits=15, decimal_places=2)
    closing_balance_per_statement = serializers.DecimalField(max_digits=15, decimal_places=2)
    closing_balance_per_books = serializers.DecimalField(max_digits=15, decimal_places=2)
    notes = serializers.CharField(required=False, allow_blank=True)


class AddReconciliationItemSerializer(serializers.Serializer):
    item_type = serializers.ChoiceField(choices=[
        'OUTSTANDING_DEPOSIT', 'OUTSTANDING_CHEQUE', 'BANK_ERROR', 'BOOK_ERROR',
        'UNRECORDED_BANK', 'UNRECORDED_BOOK'
    ])
    transaction_id = serializers.IntegerField(required=False, allow_null=True)
    manual_date = serializers.DateField(required=False, allow_null=True)
    manual_reference = serializers.CharField(max_length=100, required=False, allow_blank=True)
    manual_description = serializers.CharField(max_length=200, required=False, allow_blank=True)
    manual_amount = serializers.DecimalField(max_digits=15, decimal_places=2, required=False, default=0)


class CompleteReconciliationSerializer(serializers.Serializer):
    outstanding_deposits = serializers.DecimalField(max_digits=15, decimal_places=2)
    outstanding_cheques = serializers.DecimalField(max_digits=15, decimal_places=2)
    bank_errors = serializers.DecimalField(max_digits=15, decimal_places=2, default=0)
    book_errors = serializers.DecimalField(max_digits=15, decimal_places=2, default=0)
    notes = serializers.CharField(required=False, allow_blank=True)


# Cash Float Serializers
class CashFloatSerializer(serializers.ModelSerializer):
    expected_cash = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    calculated_counted_cash = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    
    class Meta:
        model = CashFloat
        fields = '__all__'


class CreateCashFloatSerializer(serializers.Serializer):
    float_date = serializers.DateField()
    opening_float = serializers.DecimalField(max_digits=15, decimal_places=2)
    cash_sales = serializers.DecimalField(max_digits=15, decimal_places=2, default=0)
    cash_receipts = serializers.DecimalField(max_digits=15, decimal_places=2, default=0)
    cash_payments = serializers.DecimalField(max_digits=15, decimal_places=2, default=0)
    banked_amount = serializers.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Cash breakdown
    notes_200 = serializers.IntegerField(default=0)
    notes_100 = serializers.IntegerField(default=0)
    notes_50 = serializers.IntegerField(default=0)
    notes_20 = serializers.IntegerField(default=0)
    notes_10 = serializers.IntegerField(default=0)
    coins_5 = serializers.IntegerField(default=0)
    coins_2 = serializers.IntegerField(default=0)
    coins_1 = serializers.IntegerField(default=0)
    coins_050 = serializers.IntegerField(default=0)
    coins_020 = serializers.IntegerField(default=0)
    coins_010 = serializers.IntegerField(default=0)
    coins_005 = serializers.IntegerField(default=0)
    
    variance_notes = serializers.CharField(required=False, allow_blank=True)
    counted_by = serializers.CharField(max_length=100, required=False, allow_blank=True)


# Report Serializers
class CashBookSummarySerializer(serializers.Serializer):
    """Summary of cash book for a period"""
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    
    opening_balance_cash = serializers.DecimalField(max_digits=15, decimal_places=2)
    opening_balance_bank = serializers.DecimalField(max_digits=15, decimal_places=2)
    
    total_receipts = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_payments = serializers.DecimalField(max_digits=15, decimal_places=2)
    
    closing_balance_cash = serializers.DecimalField(max_digits=15, decimal_places=2)
    closing_balance_bank = serializers.DecimalField(max_digits=15, decimal_places=2)
    
    transaction_count = serializers.IntegerField()


class BankAccountBalanceSerializer(serializers.Serializer):
    """Current balance for bank accounts"""
    bank_account_number = serializers.CharField()
    current_balance = serializers.DecimalField(max_digits=15, decimal_places=2)
    unreconciled_items = serializers.IntegerField()
    last_reconciliation_date = serializers.DateField(allow_null=True)