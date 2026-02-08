"""
Cash Book Module Serializers
"""
from rest_framework import serializers
from .models import (
    IncomeCategory, CashBookTransaction, OtherIncome, OtherExpense,
    BankDeposit, CashWithdrawal, BankTransfer, BankCharge, InterestReceived,
    BankReconciliation, BankReconciliationItem, CashFloat, ExpenseCategoryBalance,
    IncomeCategoryBalance, UnpresentedCheque
)


class IncomeCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = IncomeCategory
        fields = '__all__'


class CashBookTransactionSerializer(serializers.ModelSerializer):
    is_receipt = serializers.BooleanField(read_only=True)
    is_payment = serializers.BooleanField(read_only=True)
    audit_type_name = serializers.SerializerMethodField(read_only=True)
    recon_tag_name = serializers.SerializerMethodField(read_only=True)
    gl_account = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = CashBookTransaction
        fields = ('id', 'transaction_type', 'transaction_number', 'transaction_date',
                 'amount', 'value_excl_vat', 'tax_amount', 'total_incl_vat',
                 'audit_type', 'audit_type_name', 'category_id', 'gl_account',
                 'reference', 'description', 'account_type', 'bank_account_number',
                 'bank_recon_tag', 'recon_tag_name', 'is_reconciled', 'reconciliation',
                 'running_balance_cash', 'running_balance_bank', 'is_receipt', 'is_payment',
                 'is_archived', 'archive_month', 'created_by', 'created_at', 'updated_at')
        read_only_fields = ('running_balance_cash', 'running_balance_bank', 
                           'is_reconciled', 'reconciliation', 'is_archived', 'archive_month',
                           'transaction_number', 'created_at', 'updated_at')
    
    def get_audit_type_name(self, obj):
        """Return human-readable audit type name"""
        audit_names = {
            1: 'Accounts Receivable Receipts',
            2: 'Sundry Income',
            3: 'Accounts Payable Payments',
            4: 'Expenses'
        }
        return audit_names.get(obj.audit_type, 'Unknown')
    
    def get_recon_tag_name(self, obj):
        """Return human-readable reconciliation tag"""
        tag_names = {
            'R': 'Reconciled',
            'P': 'Pending',
            'D': 'Disputed',
            'U': 'Unreconciled'
        }
        return tag_names.get(obj.bank_recon_tag, 'Unknown')
    
    def get_gl_account(self, obj):
        """Return GL account code based on audit type"""
        gl_accounts = {
            1: '1100',
            2: '2000',
            3: '2100',
            4: '4000'
        }
        return gl_accounts.get(obj.audit_type, '9999')


class CashBookTransactionListSerializer(serializers.ModelSerializer):
    """Simplified serializer for transaction listings"""
    is_receipt = serializers.BooleanField(read_only=True)
    is_payment = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = CashBookTransaction
        fields = ('id', 'transaction_type', 'transaction_number', 'transaction_date',
                 'value_excl_vat', 'total_incl_vat', 'description', 'reference', 'account_type', 
                 'audit_type', 'bank_recon_tag', 'is_reconciled', 'is_receipt', 'is_payment')


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
    value_excl_vat = serializers.DecimalField(max_digits=12, decimal_places=2)
    tax_amount = serializers.DecimalField(max_digits=12, decimal_places=2, 
                                         required=False, allow_null=True)
    total_incl_vat = serializers.DecimalField(max_digits=12, decimal_places=2)
    tax_code = serializers.IntegerField(default=1, help_text="1=14%, 2=0%, 3=Exempt, 4=Foreign")
    audit_type = serializers.IntegerField(default=2, help_text="2 = Sundry Income")
    category_id = serializers.IntegerField(required=False, allow_null=True)
    description = serializers.CharField(max_length=200)
    reference = serializers.CharField(max_length=20, required=False, allow_blank=True)
    paid_into = serializers.ChoiceField(choices=['CASH', 'BANK'], default='CASH')
    bank_account_number = serializers.CharField(max_length=50, required=False, allow_blank=True)
    bank_recon_tag = serializers.ChoiceField(choices=['R', 'P', 'D', 'U'], 
                                            default='U', required=False)


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
    value_excl_vat = serializers.DecimalField(max_digits=12, decimal_places=2)
    tax_amount = serializers.DecimalField(max_digits=12, decimal_places=2,
                                        required=False, allow_null=True)
    total_incl_vat = serializers.DecimalField(max_digits=12, decimal_places=2)
    tax_code = serializers.IntegerField(default=1, help_text="1=14%, 2=0%, 3=Exempt, 4=Foreign")
    audit_type = serializers.IntegerField(default=4, help_text="4 = Expenses")
    category_id = serializers.IntegerField(required=False, allow_null=True)
    description = serializers.CharField(max_length=200)
    reference = serializers.CharField(max_length=20, required=False, allow_blank=True)
    paid_from = serializers.ChoiceField(choices=['CASH', 'BANK'], default='CASH')
    bank_account_number = serializers.CharField(max_length=50, required=False, allow_blank=True)
    petty_cash_slip_number = serializers.CharField(max_length=20, required=False, allow_blank=True)
    bank_recon_tag = serializers.ChoiceField(choices=['R', 'P', 'D', 'U'],
                                            default='U', required=False)


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
    value_excl_vat = serializers.DecimalField(max_digits=12, decimal_places=2)
    tax_amount = serializers.DecimalField(max_digits=12, decimal_places=2,
                                         required=False, allow_null=True)
    total_incl_vat = serializers.DecimalField(max_digits=12, decimal_places=2)
    audit_type = serializers.IntegerField(default=1, help_text="1 = Accounts Receivable")
    category_id = serializers.IntegerField(required=False, allow_null=True)
    tax_code = serializers.IntegerField(default=1)
    
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
    
    reference = serializers.CharField(max_length=20, required=False, allow_blank=True)
    description = serializers.CharField(max_length=200, default='Bank deposit')
    bank_recon_tag = serializers.ChoiceField(choices=['R', 'P', 'D', 'U'],
                                            default='U', required=False)


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
    value_excl_vat = serializers.DecimalField(max_digits=12, decimal_places=2)
    vat_amount = serializers.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_incl_vat = serializers.DecimalField(max_digits=12, decimal_places=2)
    withdrawal_slip_number = serializers.CharField(max_length=50, required=False, allow_blank=True)
    withdrawn_by = serializers.CharField(max_length=100)
    purpose = serializers.CharField(max_length=200)
    reference = serializers.CharField(max_length=20, required=False, allow_blank=True)
    audit_type = serializers.IntegerField(default=3)
    category_number = serializers.IntegerField(required=False, allow_null=True)
    tax_code = serializers.IntegerField(default=1)


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
    value_excl_vat = serializers.DecimalField(max_digits=12, decimal_places=2)
    vat_amount = serializers.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_incl_vat = serializers.DecimalField(max_digits=12, decimal_places=2)
    transfer_reference = serializers.CharField(max_length=100, required=False, allow_blank=True)
    transfer_fee = serializers.DecimalField(max_digits=15, decimal_places=2, default=0, required=False)
    description = serializers.CharField(max_length=200, default='Bank transfer')
    reference = serializers.CharField(max_length=20, required=False, allow_blank=True)
    audit_type = serializers.IntegerField(default=3)
    category_number = serializers.IntegerField(required=False, allow_null=True)
    tax_code = serializers.IntegerField(default=1)


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
    value_excl_vat = serializers.DecimalField(max_digits=12, decimal_places=2)
    vat_amount = serializers.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_incl_vat = serializers.DecimalField(max_digits=12, decimal_places=2)
    charge_type = serializers.ChoiceField(choices=[
        'MONTHLY_FEE', 'TRANSACTION_FEE', 'ATM_FEE', 'OVERDRAFT', 'CARD_FEE', 'OTHER'
    ])
    statement_reference = serializers.CharField(max_length=100, required=False, allow_blank=True)
    description = serializers.CharField(max_length=200, required=False)
    reference = serializers.CharField(max_length=20, required=False, allow_blank=True)
    audit_type = serializers.IntegerField(default=4)
    category_number = serializers.IntegerField(required=False, allow_null=True)
    tax_code = serializers.IntegerField(default=1)


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
    value_excl_vat = serializers.DecimalField(max_digits=12, decimal_places=2)
    vat_amount = serializers.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_incl_vat = serializers.DecimalField(max_digits=12, decimal_places=2)
    interest_period_start = serializers.DateField()
    interest_period_end = serializers.DateField()
    interest_rate = serializers.DecimalField(max_digits=5, decimal_places=2, default=0)
    reference = serializers.CharField(max_length=20, required=False, allow_blank=True)
    description = serializers.CharField(max_length=200, default='Interest received')
    audit_type = serializers.IntegerField(default=2)
    category_number = serializers.IntegerField(required=False, allow_null=True)
    tax_code = serializers.IntegerField(default=1)


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


# Expense Category Balance Serializers
class ExpenseCategoryBalanceSerializer(serializers.ModelSerializer):
    get_monthly_balances = serializers.SerializerMethodField(read_only=True)
    year_to_date_balance = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = ExpenseCategoryBalance
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')
    
    def get_monthly_balances(self, obj):
        return obj.get_monthly_balances


class UpdateExpenseCategoryBalanceSerializer(serializers.Serializer):
    """Serializer for updating expense category balances"""
    balance_month_to_date = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    input_vat_month_to_date = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    
    balance_month_01 = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    balance_month_02 = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    balance_month_03 = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    balance_month_04 = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    balance_month_05 = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    balance_month_06 = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    balance_month_07 = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    balance_month_08 = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    balance_month_09 = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    balance_month_10 = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    balance_month_11 = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    balance_month_12 = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)


# Income Category Balance Serializers
class IncomeCategoryBalanceSerializer(serializers.ModelSerializer):
    get_monthly_balances = serializers.SerializerMethodField(read_only=True)
    year_to_date_balance = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = IncomeCategoryBalance
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')
    
    def get_monthly_balances(self, obj):
        return obj.get_monthly_balances


class UpdateIncomeCategoryBalanceSerializer(serializers.Serializer):
    """Serializer for updating income category balances"""
    balance_month_to_date = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    output_vat_month_to_date = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    
    balance_month_01 = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    balance_month_02 = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    balance_month_03 = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    balance_month_04 = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    balance_month_05 = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    balance_month_06 = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    balance_month_07 = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    balance_month_08 = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    balance_month_09 = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    balance_month_10 = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    balance_month_11 = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    balance_month_12 = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)


# Unpresented Cheque Serializers
class UnpresentedChequeSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnpresentedCheque
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')


class UnpresentedChequeListSerializer(serializers.ModelSerializer):
    """Simplified serializer for cheque listings"""
    class Meta:
        model = UnpresentedCheque
        fields = ('id', 'cheque_number', 'cheque_date', 'value', 'total', 
                 'tag', 'is_presented', 'presented_date', 'month_end_date')


class CreateUnpresentedChequeSerializer(serializers.Serializer):
    cheque_number = serializers.CharField(max_length=20)
    cheque_date = serializers.DateField()
    reference = serializers.CharField(max_length=20, required=False, allow_blank=True)
    value = serializers.DecimalField(max_digits=10, decimal_places=2)
    tax_code = serializers.IntegerField(default=1)
    total = serializers.DecimalField(max_digits=10, decimal_places=2)
    month_end_date = serializers.DateField()
    tag = serializers.ChoiceField(choices=['R', 'P', 'D', 'U'], default='U')


class MarkChequeAsPresentedSerializer(serializers.Serializer):
    presented_date = serializers.DateField(required=False, allow_null=True)