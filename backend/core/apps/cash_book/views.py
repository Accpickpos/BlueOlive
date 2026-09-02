"""
Cash Book Module Views (Refactored)
Handles all cash/bank transaction API endpoints with proper error handling and permissions
"""

from decimal import Decimal

from apps.common.mixins import ModuleFunctionPermissionMixin
from apps.common.permissions import BaseModelPermission
from apps.common.permissions import CanReconcile as CommonCanReconcile
from apps.shop_filter_mixin import ShopFilterMixin
from django.core.exceptions import ValidationError
from django.db import transaction as db_transaction
from django.db.models import Count, Prefetch, Q, Sum
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .business_services import CashBookTransactionService
from .models import (
    BankCharge,
    BankDeposit,
    BankReconciliation,
    BankReconciliationItem,
    BankTransfer,
    CashBookTransaction,
    CashFloat,
    CashWithdrawal,
    ExpenseCategory,
    ExpenseCategoryBalance,
    IncomeCategory,
    IncomeCategoryBalance,
    InterestReceived,
    OtherExpense,
    OtherIncome,
    UnpresentedCheque,
)
from .permissions import (
    CanCreateTransactions,
    CanModifyReconciledTransactions,
    CanReconcile,
    CanViewTransactions,
)
from .serializers import (
    AddReconciliationItemSerializer,
    BankChargeSerializer,
    BankDepositSerializer,
    BankReconciliationItemSerializer,
    BankReconciliationListSerializer,
    BankReconciliationSerializer,
    BankTransferSerializer,
    CashBookTransactionListSerializer,
    CashBookTransactionSerializer,
    CashFloatSerializer,
    CashWithdrawalSerializer,
    CompleteReconciliationSerializer,
    CreateBankChargeSerializer,
    CreateBankDepositSerializer,
    CreateBankReconciliationSerializer,
    CreateBankTransferSerializer,
    CreateCashWithdrawalSerializer,
    CreateInterestReceivedSerializer,
    CreateOtherExpenseSerializer,
    CreateOtherIncomeSerializer,
    CreateUnpresentedChequeSerializer,
    ExpenseCategoryBalanceSerializer,
    ExpenseCategorySerializer,
    IncomeCategoryBalanceSerializer,
    IncomeCategorySerializer,
    InterestReceivedSerializer,
    OtherExpenseSerializer,
    OtherIncomeSerializer,
    UnpresentedChequeListSerializer,
    UnpresentedChequeSerializer,
)
from .services import (
    BalanceCalculationService,
    ReconciliationService,
    SummaryService,
    TransactionService,
    VATService,
)


class IncomeCategoryViewSet(
    ModuleFunctionPermissionMixin, ShopFilterMixin, viewsets.ModelViewSet
):
    """API endpoint for Income Categories"""

    access_module = "cash_book"
    action_function_types = {
        "create": "MAINTENANCE",
        "update": "MAINTENANCE",
        "partial_update": "MAINTENANCE",
    }
    queryset = IncomeCategory.objects.all()
    serializer_class = IncomeCategorySerializer
    permission_classes = [IsAuthenticated, CanViewTransactions]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    search_fields = ["name", "number"]
    ordering_fields = ["number", "name"]
    ordering = ["number"]


class ExpenseCategoryViewSet(
    ModuleFunctionPermissionMixin, ShopFilterMixin, viewsets.ModelViewSet
):
    """
    API endpoint for Expense Categories. Previously unregistered — the
    frontend's cashBookApi.expenseCategories client and
    ENDPOINTS.CASH_BOOK.EXPENSE_CATEGORIES pointed at
    /cash-book/expense-categories/, but no route existed for it anywhere in
    cash_book/urls.py, so the Expense Categories maintenance page 404'd on
    every request.
    """

    access_module = "cash_book"
    action_function_types = {
        "create": "MAINTENANCE",
        "update": "MAINTENANCE",
        "partial_update": "MAINTENANCE",
    }
    queryset = ExpenseCategory.objects.all()
    serializer_class = ExpenseCategorySerializer
    permission_classes = [IsAuthenticated, CanViewTransactions]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    search_fields = ["name", "number"]
    ordering_fields = ["number", "name"]
    ordering = ["number"]


class CashBookTransactionViewSet(
    ModuleFunctionPermissionMixin, ShopFilterMixin, viewsets.ReadOnlyModelViewSet
):
    """
    API endpoint for viewing cash book transactions
    Read-only - transactions created through specific endpoints
    """

    access_module = "cash_book"
    permission_classes = [IsAuthenticated, CanViewTransactions]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = [
        "transaction_type",
        "account_type",
        "is_reconciled",
        "transaction_date",
    ]
    search_fields = ["transaction_number", "description", "reference"]
    ordering_fields = ["transaction_date", "transaction_number"]
    ordering = ["-transaction_date", "-transaction_number"]

    def get_queryset(self):
        """Optimize query with select_related"""
        return (
            CashBookTransaction.objects.select_related("reconciliation")
            .prefetch_related(
                "other_income__income_category",
                "other_expense__expense_category",
                "bank_deposit",
                "cash_withdrawal",
                "bank_transfer",
                "bank_charge",
                "interest_received",
            )
            .all()
        )

    def get_serializer_class(self):
        if self.action == "list":
            return CashBookTransactionListSerializer
        return CashBookTransactionSerializer

    @action(detail=False, methods=["get"])
    def summary(self, request):
        """Get cash book summary for a period"""
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")

        if not start_date or not end_date:
            return Response(
                {"error": "start_date and end_date parameters are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            summary_data = SummaryService.get_period_summary(start_date, end_date)
            return Response(summary_data)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["get"])
    def breakdown(self, request):
        """Get transaction breakdown by type"""
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")

        if not start_date or not end_date:
            return Response(
                {"error": "start_date and end_date parameters are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            breakdown = SummaryService.get_transaction_breakdown(start_date, end_date)
            return Response(breakdown)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["get"])
    def bank_balances(self, request):
        """Get current balances for all bank accounts (optimized)"""
        from .services import BalanceCalculationService

        balances_data = BalanceCalculationService.get_account_balances()

        return Response({"accounts": balances_data, "timestamp": timezone.now()})

    @action(detail=False, methods=["get"])
    def current_balance(self, request):
        """Get current overall balances"""
        balances = BalanceCalculationService.get_current_balances()
        return Response(balances)

    @action(detail=True, methods=["patch"])
    def tag(self, request, pk=None):
        """
        Set a transaction's bank reconciliation tag (per spec CBTAG).
        This is the "tagging" workflow the manual describes for Bank
        Reconciliation: mark a bank transaction as Pending (outstanding —
        not yet on the bank statement), Reconciled, or Disputed. A
        reconciliation's outstanding deposit/cheque totals are then derived
        from transactions tagged 'P' (see BankReconciliationViewSet.
        outstanding_summary) instead of being hand-typed.
        """
        transaction = self.get_object()
        tag = request.data.get("bank_recon_tag")
        valid_tags = dict(CashBookTransaction._meta.get_field("bank_recon_tag").choices)
        if tag not in valid_tags:
            return Response(
                {"error": f"bank_recon_tag must be one of {list(valid_tags)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if transaction.is_reconciled:
            return Response(
                {"error": "Cannot re-tag a reconciled transaction."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        transaction.bank_recon_tag = tag
        transaction.save(update_fields=["bank_recon_tag"])
        return Response(CashBookTransactionSerializer(transaction).data)

    @action(detail=False, methods=["post"])
    def bulk_tag(self, request):
        """Tag multiple transactions at once (per spec CBTAG bulk tagging)."""
        transaction_ids = request.data.get("transaction_ids", [])
        tag = request.data.get("bank_recon_tag")
        valid_tags = dict(CashBookTransaction._meta.get_field("bank_recon_tag").choices)
        if tag not in valid_tags:
            return Response(
                {"error": f"bank_recon_tag must be one of {list(valid_tags)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not transaction_ids:
            return Response(
                {"error": "transaction_ids list is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        updated = CashBookTransaction.objects.filter(
            id__in=transaction_ids, is_reconciled=False
        ).update(bank_recon_tag=tag)
        return Response({"updated": updated})

    @action(detail=False, methods=["get"])
    def category_tax_analysis(self, request):
        """Category & Tax Analysis enquiry: income/expense by category with VAT split."""
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")
        if not start_date or not end_date:
            return Response(
                {"error": "start_date and end_date parameters are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        from .business_services import CashBookReportService

        return Response(
            CashBookReportService.get_category_tax_analysis(start_date, end_date)
        )

    @action(detail=False, methods=["get"])
    def control_summary(self, request):
        """Control Summary enquiry: period totals reconciling the cash book at a glance."""
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")
        if not start_date or not end_date:
            return Response(
                {"error": "start_date and end_date parameters are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        from .business_services import CashBookReportService

        return Response(CashBookReportService.get_control_summary(start_date, end_date))

    @action(detail=False, methods=["get"])
    def monthly_category_series(self, request):
        """Monthly Category Analysis enquiry: real per-month income/expense totals for a year."""
        year = request.query_params.get("year")
        if not year:
            return Response(
                {"error": "year parameter is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        from .business_services import CashBookReportService

        try:
            year = int(year)
        except ValueError:
            return Response(
                {"error": "year must be an integer"}, status=status.HTTP_400_BAD_REQUEST
            )
        return Response(CashBookReportService.get_monthly_category_series(year))


class OtherIncomeViewSet(
    ModuleFunctionPermissionMixin, ShopFilterMixin, viewsets.ModelViewSet
):
    """API endpoint for Other Income transactions"""

    access_module = "cash_book"
    serializer_class = OtherIncomeSerializer
    permission_classes = [
        IsAuthenticated,
        CanCreateTransactions,
        CanModifyReconciledTransactions,
    ]
    ordering = ["-transaction__transaction_date"]

    def get_queryset(self):
        return OtherIncome.objects.select_related(
            "transaction", "income_category"
        ).all()

    @db_transaction.atomic
    def create(self, request, *args, **kwargs):
        """
        Create other income transaction(s). `lines` (optional) supports the
        spec's multi-line deposit batch — several income categories
        captured in one submission — by creating one CashBookTransaction +
        OtherIncome per line, all sharing this submission's reference/
        paid_into/bank_account_number. Without `lines`, behaves exactly as
        before (single category line).
        """
        serializer = CreateOtherIncomeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            data = serializer.validated_data
            account_type = "BANK" if data.get("paid_into") == "BANK" else "CASH"
            lines = data.get("lines")
            if not lines:
                lines = [
                    {
                        "income_category_id": data["income_category_id"],
                        "value_excl_vat": data["value_excl_vat"],
                        "tax_code": data.get("tax_code", 1),
                        "description": data.get("description", ""),
                    }
                ]

            created = []
            for line in lines:
                # value_excl_vat + tax_code drive the base transaction;
                # VAT/total are computed authoritatively by
                # create_transaction() itself.
                base_transaction = CashBookTransactionService.create_transaction(
                    transaction_type="OTHER_INCOME",
                    transaction_date=data["transaction_date"],
                    value_excl_vat=line["value_excl_vat"],
                    tax_code=line.get("tax_code", data.get("tax_code", 1)),
                    audit_type=data.get("audit_type", 2),
                    category_id=data.get("category_id"),
                    reference=data.get("reference", ""),
                    description=line.get("description") or data.get("description", ""),
                    account_type=account_type,
                    bank_account_number=data.get("bank_account_number", ""),
                    created_by=request.user.username,
                )
                other_income = OtherIncome.objects.create(
                    transaction=base_transaction,
                    income_category_id=line["income_category_id"],
                    is_vat_inclusive=False,
                    vat_amount=base_transaction.tax_amount,
                    tax_code=line.get("tax_code", data.get("tax_code", 1)),
                    paid_into=data.get("paid_into", "CASH"),
                )
                created.append(other_income)

            response_data = OtherIncomeSerializer(created, many=True).data
            if len(created) == 1 and not data.get("lines"):
                return Response(response_data[0], status=status.HTTP_201_CREATED)
            return Response(response_data, status=status.HTTP_201_CREATED)

        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"error": f"Failed to create transaction: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class OtherExpenseViewSet(
    ModuleFunctionPermissionMixin, ShopFilterMixin, viewsets.ModelViewSet
):
    """API endpoint for Other Expense transactions"""

    access_module = "cash_book"
    serializer_class = OtherExpenseSerializer
    permission_classes = [
        IsAuthenticated,
        CanCreateTransactions,
        CanModifyReconciledTransactions,
    ]
    ordering = ["-transaction__transaction_date"]

    def get_queryset(self):
        return OtherExpense.objects.select_related(
            "transaction", "expense_category"
        ).all()

    @db_transaction.atomic
    def create(self, request, *args, **kwargs):
        """
        Create other expense transaction(s). `lines` (optional) supports
        the spec's multi-line petty cash batch — see
        OtherIncomeViewSet.create for the shared pattern.
        """
        serializer = CreateOtherExpenseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            data = serializer.validated_data
            account_type = "BANK" if data.get("paid_from") == "BANK" else "CASH"
            lines = data.get("lines")
            if not lines:
                lines = [
                    {
                        "expense_category_id": data["expense_category_id"],
                        "value_excl_vat": data["value_excl_vat"],
                        "tax_code": data.get("tax_code", 1),
                        "description": data.get("description", ""),
                    }
                ]

            created = []
            for line in lines:
                base_transaction = CashBookTransactionService.create_transaction(
                    transaction_type="OTHER_EXPENSE",
                    transaction_date=data["transaction_date"],
                    value_excl_vat=line["value_excl_vat"],
                    tax_code=line.get("tax_code", data.get("tax_code", 1)),
                    audit_type=data.get("audit_type", 4),
                    category_id=data.get("category_id"),
                    reference=data.get("reference", ""),
                    description=line.get("description") or data.get("description", ""),
                    account_type=account_type,
                    bank_account_number=data.get("bank_account_number", ""),
                    created_by=request.user.username,
                )
                other_expense = OtherExpense.objects.create(
                    transaction=base_transaction,
                    expense_category_id=line["expense_category_id"],
                    is_vat_inclusive=False,
                    vat_amount=base_transaction.tax_amount,
                    tax_code=line.get("tax_code", data.get("tax_code", 1)),
                    paid_from=data.get("paid_from", "CASH"),
                    petty_cash_slip_number=data.get("petty_cash_slip_number", ""),
                )
                created.append(other_expense)

            response_data = OtherExpenseSerializer(created, many=True).data
            if len(created) == 1 and not data.get("lines"):
                return Response(response_data[0], status=status.HTTP_201_CREATED)
            return Response(response_data, status=status.HTTP_201_CREATED)

        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"error": f"Failed to create transaction: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class BankDepositViewSet(
    ModuleFunctionPermissionMixin, ShopFilterMixin, viewsets.ModelViewSet
):
    """API endpoint for Bank Deposits"""

    access_module = "cash_book"
    serializer_class = BankDepositSerializer
    permission_classes = [
        IsAuthenticated,
        CanCreateTransactions,
        CanModifyReconciledTransactions,
    ]
    ordering = ["-transaction__transaction_date"]

    def get_queryset(self):
        return BankDeposit.objects.select_related("transaction").all()

    @db_transaction.atomic
    def create(self, request, *args, **kwargs):
        """Create bank deposit"""
        serializer = CreateBankDepositSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            data = serializer.validated_data

            # Prepare cash breakdown
            cash_breakdown = {
                "notes_200": data.get("notes_200", 0),
                "notes_100": data.get("notes_100", 0),
                "notes_50": data.get("notes_50", 0),
                "notes_20": data.get("notes_20", 0),
                "notes_10": data.get("notes_10", 0),
                "coins_5": data.get("coins_5", 0),
                "coins_2": data.get("coins_2", 0),
                "coins_1": data.get("coins_1", 0),
                "coins_050": data.get("coins_050", 0),
                "coins_020": data.get("coins_020", 0),
                "coins_010": data.get("coins_010", 0),
                "coins_005": data.get("coins_005", 0),
            }

            deposit = TransactionService.create_bank_deposit(
                transaction_date=data["transaction_date"],
                bank_account_number=data["bank_account_number"],
                bank_name=data["bank_name"],
                cash_amount=data["cash_amount"],
                cheque_amount=data["cheque_amount"],
                deposit_slip_number=data.get("deposit_slip_number", ""),
                branch=data.get("branch", ""),
                cash_breakdown=cash_breakdown,
                reference=data.get("reference", ""),
                created_by=request.user.username,
            )

            response_serializer = BankDepositSerializer(deposit)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)

        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"error": f"Failed to create deposit: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class CashWithdrawalViewSet(
    ModuleFunctionPermissionMixin, ShopFilterMixin, viewsets.ModelViewSet
):
    """API endpoint for Cash Withdrawals"""

    access_module = "cash_book"
    serializer_class = CashWithdrawalSerializer
    permission_classes = [
        IsAuthenticated,
        CanCreateTransactions,
        CanModifyReconciledTransactions,
    ]
    ordering = ["-transaction__transaction_date"]

    def get_queryset(self):
        return CashWithdrawal.objects.select_related("transaction").all()

    @db_transaction.atomic
    def create(self, request, *args, **kwargs):
        """
        Create cash withdrawal transaction. Previously this endpoint was
        non-functional: CashWithdrawalSerializer marks `transaction` as
        read-only with no way to set it, so the default ModelViewSet.create()
        could never succeed — CreateCashWithdrawalSerializer existed but was
        never wired to any view. Fixed by mirroring the working
        OtherIncomeViewSet/OtherExpenseViewSet pattern.
        """
        serializer = CreateCashWithdrawalSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            data = serializer.validated_data
            base_transaction = CashBookTransactionService.create_transaction(
                transaction_type="WITHDRAWAL",
                transaction_date=data["transaction_date"],
                value_excl_vat=data["value_excl_vat"],
                tax_code=data.get("tax_code", 1),
                audit_type=data.get("audit_type", 3),
                category_id=data.get("category_number"),
                reference=data.get("reference", ""),
                description=data.get("purpose", ""),
                account_type="BANK",
                bank_account_number=data["bank_account_number"],
                created_by=request.user.username,
            )
            withdrawal = CashWithdrawal.objects.create(
                transaction=base_transaction,
                withdrawal_slip_number=data.get("withdrawal_slip_number", ""),
                withdrawn_by=data["withdrawn_by"],
                purpose=data["purpose"],
            )
            return Response(
                CashWithdrawalSerializer(withdrawal).data,
                status=status.HTTP_201_CREATED,
            )
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class BankTransferViewSet(
    ModuleFunctionPermissionMixin, ShopFilterMixin, viewsets.ModelViewSet
):
    """API endpoint for Bank Transfers"""

    access_module = "cash_book"
    serializer_class = BankTransferSerializer
    permission_classes = [
        IsAuthenticated,
        CanCreateTransactions,
        CanModifyReconciledTransactions,
    ]
    ordering = ["-transaction__transaction_date"]

    def get_queryset(self):
        return BankTransfer.objects.select_related("transaction").all()

    @db_transaction.atomic
    def create(self, request, *args, **kwargs):
        """Create bank transfer transaction (see CashWithdrawalViewSet.create for why this override exists)."""
        serializer = CreateBankTransferSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            data = serializer.validated_data
            base_transaction = CashBookTransactionService.create_transaction(
                transaction_type="TRANSFER",
                transaction_date=data["transaction_date"],
                value_excl_vat=data["value_excl_vat"],
                tax_code=data.get("tax_code", 1),
                audit_type=data.get("audit_type", 3),
                category_id=data.get("category_number"),
                reference=data.get("reference", ""),
                description=data.get("description", "Bank transfer"),
                account_type="BANK",
                bank_account_number=data["from_account"],
                created_by=request.user.username,
            )
            transfer = BankTransfer.objects.create(
                transaction=base_transaction,
                from_account=data["from_account"],
                to_account=data["to_account"],
                transfer_reference=data.get("transfer_reference", ""),
                transfer_fee=data.get("transfer_fee", 0),
            )
            return Response(
                BankTransferSerializer(transfer).data, status=status.HTTP_201_CREATED
            )
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class BankChargeViewSet(
    ModuleFunctionPermissionMixin, ShopFilterMixin, viewsets.ModelViewSet
):
    """API endpoint for Bank Charges"""

    access_module = "cash_book"
    serializer_class = BankChargeSerializer
    permission_classes = [
        IsAuthenticated,
        CanCreateTransactions,
        CanModifyReconciledTransactions,
    ]
    ordering = ["-transaction__transaction_date"]

    def get_queryset(self):
        return BankCharge.objects.select_related("transaction").all()

    @db_transaction.atomic
    def create(self, request, *args, **kwargs):
        """Create bank charge transaction (see CashWithdrawalViewSet.create for why this override exists)."""
        serializer = CreateBankChargeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            data = serializer.validated_data
            base_transaction = CashBookTransactionService.create_transaction(
                transaction_type="BANK_CHARGE",
                transaction_date=data["transaction_date"],
                value_excl_vat=data["value_excl_vat"],
                tax_code=data.get("tax_code", 1),
                audit_type=data.get("audit_type", 4),
                category_id=data.get("category_number"),
                reference=data.get("reference", ""),
                description=data.get("description", ""),
                account_type="BANK",
                bank_account_number=data["bank_account_number"],
                created_by=request.user.username,
            )
            charge = BankCharge.objects.create(
                transaction=base_transaction,
                charge_type=data["charge_type"],
                statement_reference=data.get("statement_reference", ""),
            )
            return Response(
                BankChargeSerializer(charge).data, status=status.HTTP_201_CREATED
            )
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class InterestReceivedViewSet(
    ModuleFunctionPermissionMixin, ShopFilterMixin, viewsets.ModelViewSet
):
    """API endpoint for Interest Received"""

    access_module = "cash_book"
    serializer_class = InterestReceivedSerializer
    permission_classes = [
        IsAuthenticated,
        CanCreateTransactions,
        CanModifyReconciledTransactions,
    ]
    ordering = ["-transaction__transaction_date"]

    def get_queryset(self):
        return InterestReceived.objects.select_related("transaction").all()

    @db_transaction.atomic
    def create(self, request, *args, **kwargs):
        """Create interest received transaction (see CashWithdrawalViewSet.create for why this override exists)."""
        serializer = CreateInterestReceivedSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            data = serializer.validated_data
            base_transaction = CashBookTransactionService.create_transaction(
                transaction_type="INTEREST",
                transaction_date=data["transaction_date"],
                value_excl_vat=data["value_excl_vat"],
                tax_code=data.get("tax_code", 1),
                audit_type=data.get("audit_type", 2),
                category_id=data.get("category_number"),
                reference=data.get("reference", ""),
                description=data.get("description", "Interest received"),
                account_type="BANK",
                bank_account_number=data["bank_account_number"],
                created_by=request.user.username,
            )
            interest = InterestReceived.objects.create(
                transaction=base_transaction,
                interest_period_start=data["interest_period_start"],
                interest_period_end=data["interest_period_end"],
                interest_rate=data.get("interest_rate", 0),
            )
            return Response(
                InterestReceivedSerializer(interest).data,
                status=status.HTTP_201_CREATED,
            )
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class BankReconciliationViewSet(
    ModuleFunctionPermissionMixin, ShopFilterMixin, viewsets.ModelViewSet
):
    """API endpoint for Bank Reconciliations"""

    access_module = "cash_book"

    permission_classes = [IsAuthenticated, CanReconcile]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["bank_account_number", "status"]
    ordering = ["-reconciliation_date"]

    def get_queryset(self):
        return BankReconciliation.objects.prefetch_related(
            Prefetch(
                "items",
                queryset=BankReconciliationItem.objects.select_related("transaction"),
            )
        ).all()

    def get_serializer_class(self):
        if self.action == "list":
            return BankReconciliationListSerializer
        return BankReconciliationSerializer

    @db_transaction.atomic
    def create(self, request, *args, **kwargs):
        """Create new bank reconciliation"""
        serializer = CreateBankReconciliationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        from .services import TransactionNumberGenerator

        today = timezone.now().date()
        recon_count = BankReconciliation.objects.filter(
            reconciliation_date=today
        ).count()
        reconciliation_number = f"REC-{today.strftime('%Y%m%d')}-{recon_count + 1:05d}"

        try:
            reconciliation = BankReconciliation.objects.create(
                reconciliation_number=reconciliation_number,
                reconciliation_date=data["reconciliation_date"],
                bank_account_number=data["bank_account_number"],
                statement_date=data["statement_date"],
                statement_number=data.get("statement_number", ""),
                opening_balance=data["opening_balance"],
                closing_balance_per_statement=data["closing_balance_per_statement"],
                closing_balance_per_books=data["closing_balance_per_books"],
                notes=data.get("notes", ""),
                status="IN_PROGRESS",
            )

            response_serializer = BankReconciliationSerializer(reconciliation)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)

        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def add_item(self, request, pk=None):
        """Add reconciliation item"""
        reconciliation = self.get_object()

        if reconciliation.status == "COMPLETED":
            return Response(
                {"error": "Cannot modify completed reconciliation"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = AddReconciliationItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            item = BankReconciliationItem.objects.create(
                reconciliation=reconciliation,
                item_type=data["item_type"],
                transaction_id=data.get("transaction_id"),
                manual_date=data.get("manual_date"),
                manual_reference=data.get("manual_reference", ""),
                manual_description=data.get("manual_description", ""),
                manual_amount=data.get("manual_amount", Decimal("0")),
            )

            response_serializer = BankReconciliationItemSerializer(item)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        """Complete reconciliation"""
        reconciliation = self.get_object()

        serializer = CompleteReconciliationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            # Outstanding totals: use what was submitted, or derive them
            # from tagged ('P') transactions when the operator used the
            # tagging workflow instead of hand-typing the totals.
            if "outstanding_deposits" in data and "outstanding_cheques" in data:
                reconciliation.outstanding_deposits = data["outstanding_deposits"]
                reconciliation.outstanding_cheques = data["outstanding_cheques"]
            else:
                derived = ReconciliationService.get_outstanding_summary(
                    reconciliation.bank_account_number
                )
                reconciliation.outstanding_deposits = data.get(
                    "outstanding_deposits", derived["outstanding_deposits"]
                )
                reconciliation.outstanding_cheques = data.get(
                    "outstanding_cheques", derived["outstanding_cheques"]
                )
            reconciliation.bank_errors = data.get("bank_errors", Decimal("0"))
            reconciliation.book_errors = data.get("book_errors", Decimal("0"))
            reconciliation.notes = data.get("notes", reconciliation.notes)

            # Use service to complete with validation
            success, message = ReconciliationService.complete_reconciliation(
                reconciliation, completed_by=request.user.username
            )

            if not success:
                return Response({"error": message}, status=status.HTTP_400_BAD_REQUEST)

            response_serializer = BankReconciliationSerializer(reconciliation)
            return Response(response_serializer.data)

        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["get"])
    def outstanding_summary(self, request):
        """Preview the outstanding deposit/cheque totals tagged 'P' for a bank account."""
        bank_account_number = request.query_params.get("bank_account_number")
        if not bank_account_number:
            return Response(
                {"error": "bank_account_number parameter is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(
            ReconciliationService.get_outstanding_summary(bank_account_number)
        )

    @action(detail=True, methods=["post"])
    def month_end(self, request, pk=None):
        """
        Month End for Bank Reconciliation. Requires the reconciliation to
        already be COMPLETED — Month End closes the period, it doesn't
        reconcile it. At completion time, every transaction tagged 'R'
        (Reconciled) was already matched to this statement and marked
        is_reconciled (see ReconciliationService.complete_reconciliation);
        transactions still tagged 'P' (Pending) were never matched and are
        left as-is so they carry forward automatically into the next
        reconciliation. Month End just closes this period (REVIEWED) and
        reports what's carrying forward.
        """
        reconciliation = self.get_object()

        if reconciliation.status != "COMPLETED":
            return Response(
                {"error": "Reconciliation must be completed before Month End."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        carried_summary = ReconciliationService.get_outstanding_summary(
            reconciliation.bank_account_number
        )

        reconciliation.status = "REVIEWED"
        reconciliation.save(update_fields=["status"])

        return Response(
            {
                "reconciliation_number": reconciliation.reconciliation_number,
                "carried_forward_summary": carried_summary,
            }
        )


class CashFloatViewSet(
    ModuleFunctionPermissionMixin, ShopFilterMixin, viewsets.ModelViewSet
):
    """API endpoint for Cash Float management"""

    access_module = "cash_book"
    queryset = CashFloat.objects.all()
    serializer_class = CashFloatSerializer
    permission_classes = [IsAuthenticated, CanCreateTransactions]
    ordering = ["-float_date"]


class ExpenseCategoryBalanceViewSet(
    ModuleFunctionPermissionMixin, ShopFilterMixin, viewsets.ModelViewSet
):
    """API endpoint for expense category balances (per spec CBEXP)"""

    access_module = "cash_book"
    action_function_types = {
        "close_month": "TRANSACTIONS",
        "recalculate_mtd": "TRANSACTIONS",
    }
    queryset = ExpenseCategoryBalance.objects.select_related("expense_category")
    serializer_class = ExpenseCategoryBalanceSerializer
    permission_classes = [IsAuthenticated, CanViewTransactions]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["expense_category"]
    search_fields = ["expense_category__name"]
    ordering_fields = ["balance_month_to_date", "updated_at"]
    ordering = ["-balance_month_to_date"]

    @action(detail=True, methods=["patch"])
    def close_month(self, request, pk=None):
        """Close month for category balance"""
        balance = self.get_object()

        month = request.data.get("month")
        year = request.data.get("year")

        if not month or not year:
            return Response(
                {"error": "month and year are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            balance.set_month_balance(month, balance.balance_month_to_date)
            balance.balance_month_to_date = Decimal("0")
            balance.input_vat_month_to_date = Decimal("0")
            balance.save()

            serializer = self.get_serializer(balance)
            return Response(serializer.data)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def recalculate_mtd(self, request, pk=None):
        """Recalculate MTD balance from transactions"""
        balance = self.get_object()

        try:
            mtd_value, mtd_vat = balance.calculate_mtd_from_transactions()
            balance.save()

            serializer = self.get_serializer(balance)
            return Response(
                {
                    "balance": serializer.data,
                    "mtd_value": str(mtd_value),
                    "mtd_vat": str(mtd_vat),
                }
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class IncomeCategoryBalanceViewSet(
    ModuleFunctionPermissionMixin, ShopFilterMixin, viewsets.ModelViewSet
):
    """API endpoint for income category balances (per spec CBINC)"""

    access_module = "cash_book"
    action_function_types = {
        "close_month": "TRANSACTIONS",
        "recalculate_mtd": "TRANSACTIONS",
    }
    queryset = IncomeCategoryBalance.objects.select_related("income_category")
    serializer_class = IncomeCategoryBalanceSerializer
    permission_classes = [IsAuthenticated, CanViewTransactions]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["income_category"]
    search_fields = ["income_category__name"]
    ordering_fields = ["balance_month_to_date", "updated_at"]
    ordering = ["-balance_month_to_date"]

    @action(detail=True, methods=["patch"])
    def close_month(self, request, pk=None):
        """Close month for category balance"""
        balance = self.get_object()

        month = request.data.get("month")
        year = request.data.get("year")

        if not month or not year:
            return Response(
                {"error": "month and year are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            balance.set_month_balance(month, balance.balance_month_to_date)
            balance.balance_month_to_date = Decimal("0")
            balance.output_vat_month_to_date = Decimal("0")
            balance.save()

            serializer = self.get_serializer(balance)
            return Response(serializer.data)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def recalculate_mtd(self, request, pk=None):
        """Recalculate MTD balance from transactions"""
        balance = self.get_object()

        try:
            mtd_value, mtd_vat = balance.calculate_mtd_from_transactions()
            balance.save()

            serializer = self.get_serializer(balance)
            return Response(
                {
                    "balance": serializer.data,
                    "mtd_value": str(mtd_value),
                    "mtd_vat": str(mtd_vat),
                }
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class UnpresentedChequeViewSet(
    ModuleFunctionPermissionMixin, ShopFilterMixin, viewsets.ModelViewSet
):
    """API endpoint for unpresented cheques (per spec CBCHEQ)"""

    access_module = "cash_book"

    queryset = UnpresentedCheque.objects.all()
    serializer_class = UnpresentedChequeSerializer
    permission_classes = [IsAuthenticated, CanViewTransactions]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["is_presented", "tag", "is_stale", "requires_follow_up"]
    search_fields = ["cheque_number", "reference"]
    ordering_fields = ["cheque_date", "days_outstanding"]
    ordering = ["-cheque_date"]

    def get_serializer_class(self):
        if self.action == "list":
            return UnpresentedChequeListSerializer
        elif self.action == "create":
            return CreateUnpresentedChequeSerializer
        return UnpresentedChequeSerializer

    @action(detail=True, methods=["patch"])
    def mark_presented(self, request, pk=None):
        """Mark cheque as presented"""
        cheque = self.get_object()

        presented_date = request.data.get("presented_date")

        try:
            cheque.mark_as_presented(presented_date)
            serializer = UnpresentedChequeSerializer(cheque)
            return Response(serializer.data)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["get"])
    def reconciliation_summary(self, request):
        """Get unpresented cheques summary for bank reconciliation"""
        month_end_date = request.query_params.get("month_end_date")

        if not month_end_date:
            return Response(
                {"error": "month_end_date parameter is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            from datetime import datetime

            month_end = datetime.strptime(month_end_date, "%Y-%m-%d").date()
            summary = UnpresentedCheque.get_unpresented_summary(month_end)
            return Response(summary)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["post"])
    def bulk_mark_presented(self, request):
        """Mark multiple cheques as presented"""
        cheque_numbers = request.data.get("cheque_numbers", [])
        presented_date = request.data.get("presented_date")

        if not cheque_numbers:
            return Response(
                {"error": "cheque_numbers list is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            from cash_book.business_services import UnpresentedChequeService

            count = UnpresentedChequeService.mark_cheques_as_presented(
                cheque_numbers, presented_date
            )
            return Response(
                {"count": count, "message": f"{count} cheques marked as presented"}
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
