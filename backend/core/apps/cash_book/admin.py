"""
Cash Book Module Admin Configuration
Enhanced with actions for validation, archiving, and balance verification
"""

from datetime import date, timedelta

from django.contrib import admin, messages
from django.db import transaction as db_transaction
from django.utils import timezone

from .models import (
    BankCharge,
    BankDeposit,
    BankReconciliation,
    BankReconciliationItem,
    BankTransfer,
    CashBookTransaction,
    CashFloat,
    CashWithdrawal,
    ExpenseCategoryBalance,
    IncomeCategory,
    IncomeCategoryBalance,
    InterestReceived,
    OtherExpense,
    OtherIncome,
    UnpresentedCheque,
)
from .services import BalanceCalculationService, ReconciliationService


@admin.register(IncomeCategory)
class IncomeCategoryAdmin(admin.ModelAdmin):
    list_display = ("number", "name", "created_at")
    search_fields = ("number", "name")
    ordering = ("number",)


@admin.register(CashBookTransaction)
class CashBookTransactionAdmin(admin.ModelAdmin):
    list_display = (
        "transaction_number",
        "transaction_date",
        "transaction_type",
        "value_excl_vat",
        "tax_amount",
        "total_incl_vat",
        "audit_type",
        "bank_recon_tag",
        "is_reconciled",
        "description",
    )
    list_filter = (
        "transaction_type",
        "account_type",
        "is_reconciled",
        "transaction_date",
        "audit_type",
        "bank_recon_tag",
    )
    search_fields = ("transaction_number", "description", "reference")
    readonly_fields = (
        "running_balance_cash",
        "running_balance_bank",
        "is_reconciled",
        "reconciliation",
        "is_archived",
        "archive_month",
        "created_at",
        "updated_at",
        "transaction_number",
    )
    date_hierarchy = "transaction_date"
    actions = ["archive_transactions", "verify_balances", "mark_as_reconciled"]

    fieldsets = (
        (
            "Transaction Details",
            {
                "fields": (
                    "transaction_number",
                    "transaction_type",
                    "transaction_date",
                    "reference",
                    "description",
                )
            },
        ),
        (
            "Amount & VAT (per spec CBTRAN)",
            {
                "fields": (
                    "value_excl_vat",
                    "tax_amount",
                    "total_incl_vat",
                    "amount",
                )  # legacy field
            },
        ),
        (
            "Audit & Classification",
            {"fields": ("audit_type", "category_id", "bank_recon_tag")},
        ),
        ("Account Information", {"fields": ("account_type", "bank_account_number")}),
        ("Reconciliation", {"fields": ("is_reconciled", "reconciliation")}),
        (
            "Running Balances",
            {"fields": ("running_balance_cash", "running_balance_bank")},
        ),
        (
            "Metadata",
            {
                "fields": (
                    "created_by",
                    "created_at",
                    "updated_at",
                    "is_archived",
                    "archive_month",
                )
            },
        ),
    )

    def archive_transactions(self, request, queryset):
        """Archive selected transactions"""
        archive_month = (date.today().replace(day=1) - timedelta(days=1)).replace(day=1)

        updated = queryset.update(is_archived=True, archive_month=archive_month)

        self.message_user(request, f"{updated} transactions archived", messages.SUCCESS)

    archive_transactions.short_description = "Archive selected transactions"

    def verify_balances(self, request, queryset):
        """Verify and recalculate balances for selected transactions"""
        with db_transaction.atomic():
            BalanceCalculationService.update_running_balances()

        self.message_user(
            request, "Balances recalculated for all transactions", messages.SUCCESS
        )

    verify_balances.short_description = "Recalculate all running balances"

    def mark_as_reconciled(self, request, queryset):
        """Mark selected transactions as reconciled"""
        count = 0
        for txn in queryset:
            if not txn.is_reconciled:
                txn.is_reconciled = True
                txn.save(update_fields=["is_reconciled"])
                count += 1

        self.message_user(
            request, f"{count} transactions marked as reconciled", messages.SUCCESS
        )

    mark_as_reconciled.short_description = "Mark as reconciled"


@admin.register(OtherIncome)
class OtherIncomeAdmin(admin.ModelAdmin):
    list_display = (
        "get_transaction_number",
        "get_transaction_date",
        "income_category",
        "get_amount",
        "paid_into",
    )
    list_filter = ("paid_into", "tax_code")
    search_fields = ("transaction__transaction_number", "transaction__description")

    def get_transaction_number(self, obj):
        return obj.transaction.transaction_number

    get_transaction_number.short_description = "Transaction #"

    def get_transaction_date(self, obj):
        return obj.transaction.transaction_date

    get_transaction_date.short_description = "Date"

    def get_amount(self, obj):
        return obj.transaction.amount

    get_amount.short_description = "Amount"


@admin.register(OtherExpense)
class OtherExpenseAdmin(admin.ModelAdmin):
    list_display = (
        "get_transaction_number",
        "get_transaction_date",
        "expense_category",
        "get_amount",
        "paid_from",
        "petty_cash_slip_number",
    )
    list_filter = ("paid_from", "tax_code")
    search_fields = (
        "transaction__transaction_number",
        "transaction__description",
        "petty_cash_slip_number",
    )

    def get_transaction_number(self, obj):
        return obj.transaction.transaction_number

    get_transaction_number.short_description = "Transaction #"

    def get_transaction_date(self, obj):
        return obj.transaction.transaction_date

    get_transaction_date.short_description = "Date"

    def get_amount(self, obj):
        return obj.transaction.amount

    get_amount.short_description = "Amount"


@admin.register(BankDeposit)
class BankDepositAdmin(admin.ModelAdmin):
    list_display = (
        "get_transaction_number",
        "get_transaction_date",
        "bank_name",
        "cash_amount",
        "cheque_amount",
        "get_total_amount",
        "deposit_slip_number",
    )
    search_fields = (
        "transaction__transaction_number",
        "deposit_slip_number",
        "bank_name",
    )
    readonly_fields = ("calculated_cash_total",)

    fieldsets = (
        (
            "Deposit Details",
            {
                "fields": (
                    "bank_name",
                    "branch",
                    "deposit_slip_number",
                    "cash_amount",
                    "cheque_amount",
                )
            },
        ),
        (
            "Cash Breakdown",
            {
                "fields": (
                    ("notes_200", "notes_100", "notes_50"),
                    ("notes_20", "notes_10"),
                    ("coins_5", "coins_2", "coins_1"),
                    ("coins_050", "coins_020", "coins_010", "coins_005"),
                    "calculated_cash_total",
                )
            },
        ),
    )

    def get_transaction_number(self, obj):
        return obj.transaction.transaction_number

    get_transaction_number.short_description = "Transaction #"

    def get_transaction_date(self, obj):
        return obj.transaction.transaction_date

    get_transaction_date.short_description = "Date"

    def get_total_amount(self, obj):
        return obj.transaction.amount

    get_total_amount.short_description = "Total"


@admin.register(CashWithdrawal)
class CashWithdrawalAdmin(admin.ModelAdmin):
    list_display = (
        "get_transaction_number",
        "get_transaction_date",
        "get_amount",
        "withdrawn_by",
        "purpose",
        "withdrawal_slip_number",
    )
    search_fields = (
        "transaction__transaction_number",
        "withdrawal_slip_number",
        "withdrawn_by",
        "purpose",
    )

    def get_transaction_number(self, obj):
        return obj.transaction.transaction_number

    get_transaction_number.short_description = "Transaction #"

    def get_transaction_date(self, obj):
        return obj.transaction.transaction_date

    get_transaction_date.short_description = "Date"

    def get_amount(self, obj):
        return obj.transaction.amount

    get_amount.short_description = "Amount"


@admin.register(BankTransfer)
class BankTransferAdmin(admin.ModelAdmin):
    list_display = (
        "get_transaction_number",
        "get_transaction_date",
        "from_account",
        "to_account",
        "get_amount",
        "transfer_fee",
    )
    search_fields = (
        "transaction__transaction_number",
        "from_account",
        "to_account",
        "transfer_reference",
    )

    def get_transaction_number(self, obj):
        return obj.transaction.transaction_number

    get_transaction_number.short_description = "Transaction #"

    def get_transaction_date(self, obj):
        return obj.transaction.transaction_date

    get_transaction_date.short_description = "Date"

    def get_amount(self, obj):
        return obj.transaction.amount

    get_amount.short_description = "Amount"


@admin.register(BankCharge)
class BankChargeAdmin(admin.ModelAdmin):
    list_display = (
        "get_transaction_number",
        "get_transaction_date",
        "charge_type",
        "get_amount",
        "statement_reference",
    )
    list_filter = ("charge_type",)
    search_fields = ("transaction__transaction_number", "statement_reference")

    def get_transaction_number(self, obj):
        return obj.transaction.transaction_number

    get_transaction_number.short_description = "Transaction #"

    def get_transaction_date(self, obj):
        return obj.transaction.transaction_date

    get_transaction_date.short_description = "Date"

    def get_amount(self, obj):
        return obj.transaction.amount

    get_amount.short_description = "Amount"


@admin.register(InterestReceived)
class InterestReceivedAdmin(admin.ModelAdmin):
    list_display = (
        "get_transaction_number",
        "get_transaction_date",
        "get_amount",
        "interest_period_start",
        "interest_period_end",
        "interest_rate",
    )
    search_fields = ("transaction__transaction_number",)

    def get_transaction_number(self, obj):
        return obj.transaction.transaction_number

    get_transaction_number.short_description = "Transaction #"

    def get_transaction_date(self, obj):
        return obj.transaction.transaction_date

    get_transaction_date.short_description = "Date"

    def get_amount(self, obj):
        return obj.transaction.amount

    get_amount.short_description = "Amount"


class BankReconciliationItemInline(admin.TabularInline):
    model = BankReconciliationItem
    extra = 0
    readonly_fields = ("amount", "description")


@admin.register(BankReconciliation)
class BankReconciliationAdmin(admin.ModelAdmin):
    list_display = (
        "reconciliation_number",
        "reconciliation_date",
        "bank_account_number",
        "closing_balance_per_statement",
        "closing_balance_per_books",
        "status",
        "is_balanced",
    )
    list_filter = ("status", "bank_account_number", "reconciliation_date")
    search_fields = ("reconciliation_number", "bank_account_number", "statement_number")
    readonly_fields = (
        "reconciliation_number",
        "is_balanced",
        "difference",
        "completed_at",
        "completed_by",
        "created_at",
        "updated_at",
    )
    inlines = [BankReconciliationItemInline]
    date_hierarchy = "reconciliation_date"
    actions = ["complete_reconciliation", "validate_reconciliation"]

    fieldsets = (
        (
            "Reconciliation Details",
            {
                "fields": (
                    "reconciliation_number",
                    "reconciliation_date",
                    "bank_account_number",
                    "statement_date",
                    "statement_number",
                    "status",
                )
            },
        ),
        (
            "Balances",
            {
                "fields": (
                    "opening_balance",
                    "closing_balance_per_statement",
                    "closing_balance_per_books",
                    "is_balanced",
                    "difference",
                )
            },
        ),
        (
            "Reconciliation Items",
            {
                "fields": (
                    "outstanding_deposits",
                    "outstanding_cheques",
                    "bank_errors",
                    "book_errors",
                )
            },
        ),
        ("Notes", {"fields": ("notes",)}),
        ("Completion", {"fields": ("completed_at", "completed_by")}),
    )

    def complete_reconciliation(self, request, queryset):
        """Complete selected reconciliations"""
        success_count = 0
        error_count = 0

        for reconciliation in queryset.filter(status="IN_PROGRESS"):
            success, message = ReconciliationService.complete_reconciliation(
                reconciliation, completed_by=request.user.username
            )

            if success:
                success_count += 1
            else:
                error_count += 1

        if success_count:
            self.message_user(
                request, f"{success_count} reconciliations completed", messages.SUCCESS
            )

        if error_count:
            self.message_user(
                request,
                f"{error_count} reconciliations failed validation",
                messages.ERROR,
            )

    complete_reconciliation.short_description = "Complete selected reconciliations"

    def validate_reconciliation(self, request, queryset):
        """Validate that selected reconciliations balance"""
        unbalanced = []

        for reconciliation in queryset:
            is_valid, message = ReconciliationService.validate_reconciliation(
                reconciliation
            )
            if not is_valid:
                unbalanced.append(f"{reconciliation.reconciliation_number}: {message}")

        if unbalanced:
            error_msg = "Validation failed for:\n" + "\n".join(unbalanced[:5])
            if len(unbalanced) > 5:
                error_msg += f"\n... and {len(unbalanced) - 5} more"
            self.message_user(request, error_msg, messages.ERROR)
        else:
            self.message_user(
                request, "All selected reconciliations are valid", messages.SUCCESS
            )

    validate_reconciliation.short_description = "Validate selected reconciliations"


@admin.register(BankReconciliationItem)
class BankReconciliationItemAdmin(admin.ModelAdmin):
    list_display = ("reconciliation", "item_type", "amount", "is_resolved")
    list_filter = ("item_type", "is_resolved")
    search_fields = ("reconciliation__reconciliation_number", "manual_description")
    readonly_fields = ("amount", "description")


@admin.register(CashFloat)
class CashFloatAdmin(admin.ModelAdmin):
    list_display = (
        "float_date",
        "opening_float",
        "cash_sales",
        "expected_cash",
        "counted_cash",
        "variance",
        "is_balanced",
        "counted_by",
    )
    list_filter = ("is_balanced", "float_date")
    search_fields = ("counted_by",)
    readonly_fields = (
        "expected_cash",
        "calculated_counted_cash",
        "variance",
        "is_balanced",
        "created_at",
        "updated_at",
    )
    date_hierarchy = "float_date"

    fieldsets = (
        ("Float Details", {"fields": ("float_date", "opening_float")}),
        (
            "Cash Movements",
            {
                "fields": (
                    "cash_sales",
                    "cash_receipts",
                    "cash_payments",
                    "banked_amount",
                )
            },
        ),
        (
            "Cash Count",
            {
                "fields": (
                    ("notes_200", "notes_100", "notes_50"),
                    ("notes_20", "notes_10"),
                    ("coins_5", "coins_2", "coins_1"),
                    ("coins_050", "coins_020", "coins_010", "coins_005"),
                )
            },
        ),
        (
            "Reconciliation",
            {
                "fields": (
                    "expected_cash",
                    "counted_cash",
                    "calculated_counted_cash",
                    "variance",
                    "is_balanced",
                    "variance_notes",
                    "counted_by",
                )
            },
        ),
    )


@admin.register(ExpenseCategoryBalance)
class ExpenseCategoryBalanceAdmin(admin.ModelAdmin):
    """Admin for expense category balances (per spec CBEXP)"""

    list_display = (
        "expense_category",
        "balance_month_to_date",
        "input_vat_month_to_date",
        "year_to_date_balance",
        "updated_at",
    )
    list_filter = ("expense_category", "updated_at")
    search_fields = ("expense_category__name",)
    readonly_fields = ("year_to_date_balance", "created_at", "updated_at")

    fieldsets = (
        ("Category Information", {"fields": ("expense_category",)}),
        (
            "Month-to-Date (per spec CBEXP)",
            {"fields": ("balance_month_to_date", "input_vat_month_to_date")},
        ),
        (
            "Monthly Balances (EXP1-EXP12 per spec)",
            {
                "fields": (
                    ("balance_month_01", "balance_month_02", "balance_month_03"),
                    ("balance_month_04", "balance_month_05", "balance_month_06"),
                    ("balance_month_07", "balance_month_08", "balance_month_09"),
                    ("balance_month_10", "balance_month_11", "balance_month_12"),
                )
            },
        ),
        ("Summary", {"fields": ("year_to_date_balance",), "classes": ("collapse",)}),
        (
            "Metadata",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )


@admin.register(IncomeCategoryBalance)
class IncomeCategoryBalanceAdmin(admin.ModelAdmin):
    """Admin for income category balances (per spec CBINC)"""

    list_display = (
        "income_category",
        "balance_month_to_date",
        "output_vat_month_to_date",
        "year_to_date_balance",
        "updated_at",
    )
    list_filter = ("income_category", "updated_at")
    search_fields = ("income_category__name",)
    readonly_fields = ("year_to_date_balance", "created_at", "updated_at")

    fieldsets = (
        ("Category Information", {"fields": ("income_category",)}),
        (
            "Month-to-Date (per spec CBINC)",
            {"fields": ("balance_month_to_date", "output_vat_month_to_date")},
        ),
        (
            "Monthly Balances (INC1-INC12 per spec)",
            {
                "fields": (
                    ("balance_month_01", "balance_month_02", "balance_month_03"),
                    ("balance_month_04", "balance_month_05", "balance_month_06"),
                    ("balance_month_07", "balance_month_08", "balance_month_09"),
                    ("balance_month_10", "balance_month_11", "balance_month_12"),
                )
            },
        ),
        ("Summary", {"fields": ("year_to_date_balance",), "classes": ("collapse",)}),
        (
            "Metadata",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )


@admin.register(UnpresentedCheque)
class UnpresentedChequeAdmin(admin.ModelAdmin):
    """Admin for unpresented cheques (per spec CBCHEQ)"""

    list_display = (
        "cheque_number",
        "cheque_date",
        "value",
        "total",
        "tag",
        "is_presented",
        "days_outstanding",
        "is_stale",
        "requires_follow_up",
    )
    list_filter = (
        "tag",
        "is_presented",
        "is_stale",
        "requires_follow_up",
        "cheque_date",
    )
    search_fields = ("cheque_number", "reference")
    readonly_fields = (
        "days_outstanding",
        "is_stale",
        "requires_follow_up",
        "created_at",
        "updated_at",
    )
    date_hierarchy = "cheque_date"
    actions = ["mark_as_presented", "flag_for_follow_up"]

    fieldsets = (
        (
            "Cheque Details (per spec CBCHEQ)",
            {"fields": ("cheque_number", "cheque_date", "reference")},
        ),
        ("Amounts (per spec)", {"fields": ("value", "tax_code", "total")}),
        ("Reconciliation (per spec CBTAG)", {"fields": ("tag", "month_end_date")}),
        ("Bank Status", {"fields": ("is_presented", "presented_date")}),
        (
            "Aging Analysis",
            {"fields": ("days_outstanding", "is_stale", "requires_follow_up")},
        ),
        ("Notes", {"fields": ("notes",), "classes": ("collapse",)}),
        (
            "Metadata",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def mark_as_presented(self, request, queryset):
        """Mark selected cheques as presented"""
        count = 0
        for cheque in queryset.filter(is_presented=False):
            cheque.mark_as_presented()
            count += 1

        self.message_user(
            request, f"{count} cheques marked as presented", messages.SUCCESS
        )

    mark_as_presented.short_description = "Mark selected as presented"

    def flag_for_follow_up(self, request, queryset):
        """Manually flag cheques for follow-up"""
        count = queryset.filter(requires_follow_up=False).update(
            requires_follow_up=True
        )
        self.message_user(
            request, f"{count} cheques flagged for follow-up", messages.SUCCESS
        )

    flag_for_follow_up.short_description = "Flag for follow-up"
