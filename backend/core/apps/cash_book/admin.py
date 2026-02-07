"""
Cash Book Module Admin Configuration
Enhanced with actions for validation, archiving, and balance verification
"""
from django.contrib import admin, messages
from django.utils import timezone
from decimal import Decimal
from datetime import date, timedelta
from django.db import transaction as db_transaction

from .models import (
    IncomeCategory, CashBookTransaction, OtherIncome, OtherExpense,
    BankDeposit, CashWithdrawal, BankTransfer, BankCharge, InterestReceived,
    BankReconciliation, BankReconciliationItem, CashFloat
)
from .services import (
    BalanceCalculationService, ReconciliationService
)


@admin.register(IncomeCategory)
class IncomeCategoryAdmin(admin.ModelAdmin):
    list_display = ('number', 'name', 'created_at')
    search_fields = ('number', 'name')
    ordering = ('number',)


@admin.register(CashBookTransaction)
class CashBookTransactionAdmin(admin.ModelAdmin):
    list_display = ('transaction_number', 'transaction_type', 'transaction_date',
                   'amount', 'account_type', 'is_reconciled', 'description')
    list_filter = ('transaction_type', 'account_type', 'is_reconciled', 'transaction_date')
    search_fields = ('transaction_number', 'description', 'reference')
    readonly_fields = ('running_balance_cash', 'running_balance_bank', 'is_reconciled',
                      'reconciliation', 'is_archived', 'archive_month', 'created_at', 'updated_at')
    date_hierarchy = 'transaction_date'
    actions = ['archive_transactions', 'verify_balances', 'mark_as_reconciled']
    
    fieldsets = (
        ('Transaction Details', {
            'fields': ('transaction_type', 'transaction_number', 'transaction_date',
                      'amount', 'description', 'reference')
        }),
        ('Account Information', {
            'fields': ('account_type', 'bank_account_number')
        }),
        ('Reconciliation', {
            'fields': ('is_reconciled', 'reconciliation')
        }),
        ('Running Balances', {
            'fields': ('running_balance_cash', 'running_balance_bank')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at', 'is_archived', 'archive_month')
        }),
    )
    
    def archive_transactions(self, request, queryset):
        """Archive selected transactions"""
        archive_month = (date.today().replace(day=1) - timedelta(days=1)).replace(day=1)
        
        updated = queryset.update(
            is_archived=True,
            archive_month=archive_month
        )
        
        self.message_user(
            request,
            f'{updated} transactions archived',
            messages.SUCCESS
        )
    archive_transactions.short_description = 'Archive selected transactions'
    
    def verify_balances(self, request, queryset):
        """Verify and recalculate balances for selected transactions"""
        with db_transaction.atomic():
            BalanceCalculationService.update_running_balances()
        
        self.message_user(
            request,
            'Balances recalculated for all transactions',
            messages.SUCCESS
        )
    verify_balances.short_description = 'Recalculate all running balances'
    
    def mark_as_reconciled(self, request, queryset):
        """Mark selected transactions as reconciled"""
        count = 0
        for txn in queryset:
            if not txn.is_reconciled:
                txn.is_reconciled = True
                txn.save(update_fields=['is_reconciled'])
                count += 1
        
        self.message_user(
            request,
            f'{count} transactions marked as reconciled',
            messages.SUCCESS
        )
    mark_as_reconciled.short_description = 'Mark as reconciled'


@admin.register(OtherIncome)
class OtherIncomeAdmin(admin.ModelAdmin):
    list_display = ('get_transaction_number', 'get_transaction_date', 'income_category',
                   'get_amount', 'paid_into')
    list_filter = ('paid_into', 'tax_code')
    search_fields = ('transaction__transaction_number', 'transaction__description')
    
    def get_transaction_number(self, obj):
        return obj.transaction.transaction_number
    get_transaction_number.short_description = 'Transaction #'
    
    def get_transaction_date(self, obj):
        return obj.transaction.transaction_date
    get_transaction_date.short_description = 'Date'
    
    def get_amount(self, obj):
        return obj.transaction.amount
    get_amount.short_description = 'Amount'


@admin.register(OtherExpense)
class OtherExpenseAdmin(admin.ModelAdmin):
    list_display = ('get_transaction_number', 'get_transaction_date', 'expense_category',
                   'get_amount', 'paid_from', 'petty_cash_slip_number')
    list_filter = ('paid_from', 'tax_code')
    search_fields = ('transaction__transaction_number', 'transaction__description',
                    'petty_cash_slip_number')
    
    def get_transaction_number(self, obj):
        return obj.transaction.transaction_number
    get_transaction_number.short_description = 'Transaction #'
    
    def get_transaction_date(self, obj):
        return obj.transaction.transaction_date
    get_transaction_date.short_description = 'Date'
    
    def get_amount(self, obj):
        return obj.transaction.amount
    get_amount.short_description = 'Amount'


@admin.register(BankDeposit)
class BankDepositAdmin(admin.ModelAdmin):
    list_display = ('get_transaction_number', 'get_transaction_date', 'bank_name',
                   'cash_amount', 'cheque_amount', 'get_total_amount', 'deposit_slip_number')
    search_fields = ('transaction__transaction_number', 'deposit_slip_number', 'bank_name')
    readonly_fields = ('calculated_cash_total',)
    
    fieldsets = (
        ('Deposit Details', {
            'fields': ('bank_name', 'branch', 'deposit_slip_number',
                      'cash_amount', 'cheque_amount')
        }),
        ('Cash Breakdown', {
            'fields': (('notes_200', 'notes_100', 'notes_50'),
                      ('notes_20', 'notes_10'),
                      ('coins_5', 'coins_2', 'coins_1'),
                      ('coins_050', 'coins_020', 'coins_010', 'coins_005'),
                      'calculated_cash_total')
        }),
    )
    
    def get_transaction_number(self, obj):
        return obj.transaction.transaction_number
    get_transaction_number.short_description = 'Transaction #'
    
    def get_transaction_date(self, obj):
        return obj.transaction.transaction_date
    get_transaction_date.short_description = 'Date'
    
    def get_total_amount(self, obj):
        return obj.transaction.amount
    get_total_amount.short_description = 'Total'


@admin.register(CashWithdrawal)
class CashWithdrawalAdmin(admin.ModelAdmin):
    list_display = ('get_transaction_number', 'get_transaction_date', 'get_amount',
                   'withdrawn_by', 'purpose', 'withdrawal_slip_number')
    search_fields = ('transaction__transaction_number', 'withdrawal_slip_number',
                    'withdrawn_by', 'purpose')
    
    def get_transaction_number(self, obj):
        return obj.transaction.transaction_number
    get_transaction_number.short_description = 'Transaction #'
    
    def get_transaction_date(self, obj):
        return obj.transaction.transaction_date
    get_transaction_date.short_description = 'Date'
    
    def get_amount(self, obj):
        return obj.transaction.amount
    get_amount.short_description = 'Amount'


@admin.register(BankTransfer)
class BankTransferAdmin(admin.ModelAdmin):
    list_display = ('get_transaction_number', 'get_transaction_date', 'from_account',
                   'to_account', 'get_amount', 'transfer_fee')
    search_fields = ('transaction__transaction_number', 'from_account', 'to_account',
                    'transfer_reference')
    
    def get_transaction_number(self, obj):
        return obj.transaction.transaction_number
    get_transaction_number.short_description = 'Transaction #'
    
    def get_transaction_date(self, obj):
        return obj.transaction.transaction_date
    get_transaction_date.short_description = 'Date'
    
    def get_amount(self, obj):
        return obj.transaction.amount
    get_amount.short_description = 'Amount'


@admin.register(BankCharge)
class BankChargeAdmin(admin.ModelAdmin):
    list_display = ('get_transaction_number', 'get_transaction_date', 'charge_type',
                   'get_amount', 'statement_reference')
    list_filter = ('charge_type',)
    search_fields = ('transaction__transaction_number', 'statement_reference')
    
    def get_transaction_number(self, obj):
        return obj.transaction.transaction_number
    get_transaction_number.short_description = 'Transaction #'
    
    def get_transaction_date(self, obj):
        return obj.transaction.transaction_date
    get_transaction_date.short_description = 'Date'
    
    def get_amount(self, obj):
        return obj.transaction.amount
    get_amount.short_description = 'Amount'


@admin.register(InterestReceived)
class InterestReceivedAdmin(admin.ModelAdmin):
    list_display = ('get_transaction_number', 'get_transaction_date', 'get_amount',
                   'interest_period_start', 'interest_period_end', 'interest_rate')
    search_fields = ('transaction__transaction_number',)
    
    def get_transaction_number(self, obj):
        return obj.transaction.transaction_number
    get_transaction_number.short_description = 'Transaction #'
    
    def get_transaction_date(self, obj):
        return obj.transaction.transaction_date
    get_transaction_date.short_description = 'Date'
    
    def get_amount(self, obj):
        return obj.transaction.amount
    get_amount.short_description = 'Amount'


class BankReconciliationItemInline(admin.TabularInline):
    model = BankReconciliationItem
    extra = 0
    readonly_fields = ('amount', 'description')


@admin.register(BankReconciliation)
class BankReconciliationAdmin(admin.ModelAdmin):
    list_display = ('reconciliation_number', 'reconciliation_date', 'bank_account_number',
                   'closing_balance_per_statement', 'closing_balance_per_books',
                   'status', 'is_balanced')
    list_filter = ('status', 'bank_account_number', 'reconciliation_date')
    search_fields = ('reconciliation_number', 'bank_account_number', 'statement_number')
    readonly_fields = ('reconciliation_number', 'is_balanced', 'difference',
                      'completed_at', 'completed_by', 'created_at', 'updated_at')
    inlines = [BankReconciliationItemInline]
    date_hierarchy = 'reconciliation_date'
    actions = ['complete_reconciliation', 'validate_reconciliation']
    
    fieldsets = (
        ('Reconciliation Details', {
            'fields': ('reconciliation_number', 'reconciliation_date', 'bank_account_number',
                      'statement_date', 'statement_number', 'status')
        }),
        ('Balances', {
            'fields': ('opening_balance', 'closing_balance_per_statement',
                      'closing_balance_per_books', 'is_balanced', 'difference')
        }),
        ('Reconciliation Items', {
            'fields': ('outstanding_deposits', 'outstanding_cheques',
                      'bank_errors', 'book_errors')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Completion', {
            'fields': ('completed_at', 'completed_by')
        }),
    )
    
    def complete_reconciliation(self, request, queryset):
        """Complete selected reconciliations"""
        success_count = 0
        error_count = 0
        
        for reconciliation in queryset.filter(status='IN_PROGRESS'):
            success, message = ReconciliationService.complete_reconciliation(
                reconciliation,
                completed_by=request.user.username
            )
            
            if success:
                success_count += 1
            else:
                error_count += 1
        
        if success_count:
            self.message_user(
                request,
                f'{success_count} reconciliations completed',
                messages.SUCCESS
            )
        
        if error_count:
            self.message_user(
                request,
                f'{error_count} reconciliations failed validation',
                messages.ERROR
            )
    complete_reconciliation.short_description = 'Complete selected reconciliations'
    
    def validate_reconciliation(self, request, queryset):
        """Validate that selected reconciliations balance"""
        unbalanced = []
        
        for reconciliation in queryset:
            is_valid, message = ReconciliationService.validate_reconciliation(reconciliation)
            if not is_valid:
                unbalanced.append(f"{reconciliation.reconciliation_number}: {message}")
        
        if unbalanced:
            error_msg = "Validation failed for:\n" + "\n".join(unbalanced[:5])
            if len(unbalanced) > 5:
                error_msg += f"\n... and {len(unbalanced) - 5} more"
            self.message_user(request, error_msg, messages.ERROR)
        else:
            self.message_user(
                request,
                'All selected reconciliations are valid',
                messages.SUCCESS
            )
    validate_reconciliation.short_description = 'Validate selected reconciliations'


@admin.register(BankReconciliationItem)
class BankReconciliationItemAdmin(admin.ModelAdmin):
    list_display = ('reconciliation', 'item_type', 'amount', 'is_resolved')
    list_filter = ('item_type', 'is_resolved')
    search_fields = ('reconciliation__reconciliation_number', 'manual_description')
    readonly_fields = ('amount', 'description')


@admin.register(CashFloat)
class CashFloatAdmin(admin.ModelAdmin):
    list_display = ('float_date', 'opening_float', 'cash_sales', 'expected_cash',
                   'counted_cash', 'variance', 'is_balanced', 'counted_by')
    list_filter = ('is_balanced', 'float_date')
    search_fields = ('counted_by',)
    readonly_fields = ('expected_cash', 'calculated_counted_cash', 'variance', 'is_balanced',
                      'created_at', 'updated_at')
    date_hierarchy = 'float_date'
    
    fieldsets = (
        ('Float Details', {
            'fields': ('float_date', 'opening_float')
        }),
        ('Cash Movements', {
            'fields': ('cash_sales', 'cash_receipts', 'cash_payments', 'banked_amount')
        }),
        ('Cash Count', {
            'fields': (('notes_200', 'notes_100', 'notes_50'),
                      ('notes_20', 'notes_10'),
                      ('coins_5', 'coins_2', 'coins_1'),
                      ('coins_050', 'coins_020', 'coins_010', 'coins_005'))
        }),
        ('Reconciliation', {
            'fields': ('expected_cash', 'counted_cash', 'calculated_counted_cash',
                      'variance', 'is_balanced', 'variance_notes', 'counted_by')
        }),
    )