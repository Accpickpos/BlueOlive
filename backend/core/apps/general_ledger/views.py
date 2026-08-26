"""
General Ledger views.
API viewsets for general ledger operations.
"""

from datetime import date
from decimal import Decimal

from apps.shop_filter_mixin import ShopFilterMixin
from django.db.models import Avg, Count, F, Max, Min, Q, Sum
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import GLBatch, GLMast, GLSpread, GLStJnl, GLTran
from .serializers import (
    GLMastDetailSerializer,
    GLMastListSerializer,
    GLMastSerializer,
    GLSpreadDetailSerializer,
    GLSpreadListSerializer,
    GLSpreadSerializer,
    GLStJnlDetailSerializer,
    GLStJnlListSerializer,
    GLStJnlSerializer,
    GLTranDetailSerializer,
    GLTranListSerializer,
    GLTranSerializer,
)


class GLMastViewSet(ShopFilterMixin, viewsets.ModelViewSet):
    """
    ViewSet for managing General Ledger Master accounts.

    Provides CRUD operations plus additional actions:
    - summary: Get summary statistics for accounts
    - by_account_type: Filter accounts by type (Income Statement or Balance Sheet)
    - balance_summary: Get consolidated balance information
    - account_history: Get historical balances for an account
    """

    queryset = GLMast.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["type", "drorcr"]
    search_fields = ["accno", "name"]
    ordering_fields = ["accno", "name", "type", "drorcr", "balbfwd"]
    ordering = ["accno"]

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == "list":
            return GLMastListSerializer
        elif self.action == "retrieve":
            return GLMastDetailSerializer
        return GLMastSerializer

    def perform_destroy(self, instance):
        """
        Manual (§7.1 [711.htm], Deleting an Existing Account Category): "A
        General Ledger Account cannot be deleted: if there have been any
        transactions recorded in the account in the current month or
        current year[,] or where there is a batch entry relating to the
        account which has not been updated." Previously unenforced — DRF's
        default destroy() ran with no check at all.
        """
        today = date.today()
        has_transactions_this_year = GLTran.objects.filter(
            accno=instance.accno,
            date__year=today.year,
        ).exists()
        if has_transactions_this_year:
            raise ValidationError(
                f"Cannot delete account {instance.accno}: transactions were recorded "
                f"against this account in the current month or year."
            )

        has_unposted_batch_entries = GLBatch.objects.filter(
            accno=instance.accno,
            postdate__isnull=True,
        ).exists()
        if has_unposted_batch_entries:
            raise ValidationError(
                f"Cannot delete account {instance.accno}: there is an unposted batch "
                f"entry relating to this account."
            )

        super().perform_destroy(instance)

    @action(detail=False, methods=["get"])
    def summary(self, request):
        """Get summary statistics for all accounts."""
        accounts = self.get_queryset()

        total_debit_balance = accounts.filter(drorcr="D").aggregate(
            total=Sum("balbfwd")
        )["total"] or Decimal("0.00")

        total_credit_balance = accounts.filter(drorcr="C").aggregate(
            total=Sum("balbfwd")
        )["total"] or Decimal("0.00")

        income_stmt_count = accounts.filter(type="I").count()
        balance_sheet_count = accounts.filter(type="B").count()

        return Response(
            {
                "total_accounts": accounts.count(),
                "income_statement_accounts": income_stmt_count,
                "balance_sheet_accounts": balance_sheet_count,
                "total_debit_balance": float(total_debit_balance),
                "total_credit_balance": float(total_credit_balance),
                "balance_difference": float(total_debit_balance - total_credit_balance),
                "is_balanced": total_debit_balance == total_credit_balance,
            }
        )

    @action(detail=False, methods=["get"])
    def by_account_type(self, request):
        """Get accounts filtered by type."""
        account_type = request.query_params.get("type")
        if not account_type or account_type not in ["I", "B"]:
            return Response(
                {
                    "error": 'Invalid type. Use "I" for Income Statement or "B" for Balance Sheet.'
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        accounts = self.get_queryset().filter(type=account_type)
        page = self.paginate_queryset(accounts)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(accounts, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def balance_summary(self, request):
        """Get consolidated balance information for all periods."""
        accounts = self.get_queryset()

        periods = {}
        for i in range(1, 14):
            field_name = f"period{i}"
            total = accounts.aggregate(total=Sum(field_name))["total"] or Decimal(
                "0.00"
            )
            periods[field_name] = float(total)

        budgets = {}
        for i in range(1, 13):
            field_name = f"budget{i}"
            total = accounts.aggregate(total=Sum(field_name))["total"] or Decimal(
                "0.00"
            )
            budgets[field_name] = float(total)

        last_year = {}
        for i in range(1, 13):
            field_name = f"lastyear{i}"
            total = accounts.aggregate(total=Sum(field_name))["total"] or Decimal(
                "0.00"
            )
            last_year[field_name] = float(total)

        return Response(
            {
                "balbfwd_total": float(
                    accounts.aggregate(total=Sum("balbfwd"))["total"] or Decimal("0.00")
                ),
                "periods": periods,
                "budgets": budgets,
                "last_year": last_year,
            }
        )

    @action(detail=True, methods=["get"])
    def account_history(self, request, pk=None):
        """Get historical balances (all periods) for a specific account."""
        account = self.get_object()

        periods = []
        for i in range(1, 14):
            field_name = f"period{i}"
            periods.append(
                {"period": i, "balance": float(getattr(account, field_name))}
            )

        budgets = []
        for i in range(1, 13):
            field_name = f"budget{i}"
            budgets.append({"period": i, "budget": float(getattr(account, field_name))})

        last_year_data = []
        for i in range(1, 13):
            field_name = f"lastyear{i}"
            last_year_data.append(
                {"period": i, "last_year": float(getattr(account, field_name))}
            )

        return Response(
            {
                "account": account.accno,
                "name": account.name,
                "type": account.get_type_display(),
                "drorcr": account.get_drorcr_display(),
                "balbfwd": float(account.balbfwd),
                "periods": periods,
                "budgets": budgets,
                "last_year": last_year_data,
            }
        )


class GLTranViewSet(ShopFilterMixin, viewsets.ModelViewSet):
    """
    ViewSet for managing GL Transactions (Journal Entries).

    Provides CRUD operations plus additional actions:
    - by_batch: Get all transactions in a batch
    - by_account: Get all transactions for an account
    - by_date_range: Get transactions within a date range
    - batch_summary: Get summary for a batch of transactions
    - daily_summary: Get transaction summary for a specific date
    """

    queryset = GLTran.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["accno", "batchno", "date", "type", "source"]
    search_fields = ["reference", "details", "station"]
    ordering_fields = ["date", "accno", "amount", "batchno"]
    ordering = ["-date", "-time", "accno"]

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == "list":
            return GLTranListSerializer
        elif self.action == "retrieve":
            return GLTranDetailSerializer
        return GLTranSerializer

    @action(detail=False, methods=["get"])
    def by_batch(self, request):
        """Get all transactions in a specific batch."""
        batchno = request.query_params.get("batchno")
        if not batchno:
            return Response(
                {"error": "batchno parameter is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        transactions = self.get_queryset().filter(batchno=batchno)
        if not transactions.exists():
            return Response(
                {
                    "status": "no_data",
                    "message": f"No transactions found for batch {batchno}",
                    "data": [],
                }
            )

        page = self.paginate_queryset(transactions)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(transactions, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def by_account(self, request):
        """Get all transactions for a specific account."""
        accno = request.query_params.get("accno")
        if not accno:
            return Response(
                {"error": "accno parameter is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        transactions = self.get_queryset().filter(accno=accno)
        if not transactions.exists():
            return Response(
                {
                    "status": "no_data",
                    "message": f"No transactions found for account {accno}",
                    "data": [],
                }
            )

        page = self.paginate_queryset(transactions)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(transactions, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def by_date_range(self, request):
        """Get transactions within a date range."""
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")

        if not start_date or not end_date:
            return Response(
                {
                    "error": "Both start_date and end_date parameters are required (YYYY-MM-DD)"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        transactions = self.get_queryset().filter(
            date__gte=start_date, date__lte=end_date
        )

        if not transactions.exists():
            return Response(
                {
                    "status": "no_data",
                    "message": f"No transactions found between {start_date} and {end_date}",
                    "data": [],
                }
            )

        page = self.paginate_queryset(transactions)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(transactions, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def batch_summary(self, request):
        """Get summary for a batch of transactions."""
        batchno = request.query_params.get("batchno")
        if not batchno:
            return Response(
                {"error": "batchno parameter is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        transactions = self.get_queryset().filter(batchno=batchno)

        if not transactions.exists():
            return Response(
                {
                    "status": "no_data",
                    "message": f"No transactions found for batch {batchno}",
                }
            )

        total_debits = transactions.filter(type="D").aggregate(total=Sum("amount"))[
            "total"
        ] or Decimal("0.00")

        total_credits = transactions.filter(type="C").aggregate(total=Sum("amount"))[
            "total"
        ] or Decimal("0.00")

        return Response(
            {
                "batchno": batchno,
                "transaction_count": transactions.count(),
                "debit_count": transactions.filter(type="D").count(),
                "credit_count": transactions.filter(type="C").count(),
                "total_debits": float(total_debits),
                "total_credits": float(total_credits),
                "net_balance": float(total_debits - total_credits),
                "is_balanced": total_debits == total_credits,
                "date_range": {
                    "earliest": transactions.aggregate(min_date=Min("date"))[
                        "min_date"
                    ],
                    "latest": transactions.aggregate(max_date=Max("date"))["max_date"],
                },
            }
        )

    @action(detail=False, methods=["get"])
    def daily_summary(self, request):
        """Get transaction summary for a specific date."""
        date_str = request.query_params.get("date")
        if not date_str:
            return Response(
                {"error": "date parameter is required (YYYY-MM-DD)"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        transactions = self.get_queryset().filter(date=date_str)

        if not transactions.exists():
            return Response(
                {
                    "status": "no_data",
                    "message": f"No transactions found for date {date_str}",
                }
            )

        total_debits = transactions.filter(type="D").aggregate(total=Sum("amount"))[
            "total"
        ] or Decimal("0.00")

        total_credits = transactions.filter(type="C").aggregate(total=Sum("amount"))[
            "total"
        ] or Decimal("0.00")

        return Response(
            {
                "date": date_str,
                "transaction_count": transactions.count(),
                "debit_count": transactions.filter(type="D").count(),
                "credit_count": transactions.filter(type="C").count(),
                "total_debits": float(total_debits),
                "total_credits": float(total_credits),
                "net_balance": float(total_debits - total_credits),
                "is_balanced": total_debits == total_credits,
                "sources": dict(
                    transactions.values("source")
                    .annotate(count=Count("id"))
                    .values_list("source", "count")
                ),
            }
        )


class GLStJnlViewSet(ShopFilterMixin, viewsets.ModelViewSet):
    """
    ViewSet for managing GL Standing Journals.

    Provides CRUD operations plus additional actions:
    - by_account: Get all standing journals for an account
    - by_journal: Get a specific standing journal by journal number
    - active_journals: Get all active standing journals
    - by_period: Get standing journals by start period
    """

    queryset = GLStJnl.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["accno", "journalno", "drorcr", "stperiod", "nextperiod"]
    search_fields = ["details", "descriptor"]
    ordering_fields = ["accno", "journalno", "amount", "stperiod", "nextperiod"]
    ordering = ["accno", "journalno"]

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == "list":
            return GLStJnlListSerializer
        elif self.action == "retrieve":
            return GLStJnlDetailSerializer
        return GLStJnlSerializer

    @action(detail=False, methods=["get"])
    def by_account(self, request):
        """Get all standing journals for a specific account."""
        accno = request.query_params.get("accno")
        if not accno:
            return Response(
                {"error": "accno parameter is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        journals = self.get_queryset().filter(accno=accno)
        if not journals.exists():
            return Response(
                {
                    "status": "no_data",
                    "message": f"No standing journals found for account {accno}",
                    "data": [],
                }
            )

        page = self.paginate_queryset(journals)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(journals, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def by_journal(self, request):
        """Get a specific standing journal by journal number."""
        journalno = request.query_params.get("journalno")
        if not journalno:
            return Response(
                {"error": "journalno parameter is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        journals = self.get_queryset().filter(journalno=journalno)
        if not journals.exists():
            return Response(
                {
                    "status": "no_data",
                    "message": f"No standing journals found with journal number {journalno}",
                    "data": [],
                }
            )

        serializer = self.get_serializer(journals, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def active_journals(self, request):
        """Get all active standing journals (where timesbal < times)."""
        journals = self.get_queryset().filter(timesbal__lt=F("times"))

        if not journals.exists():
            return Response(
                {
                    "status": "no_data",
                    "message": "No active standing journals found",
                    "data": [],
                }
            )

        page = self.paginate_queryset(journals)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(journals, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def by_period(self, request):
        """Get standing journals by start period."""
        stperiod = request.query_params.get("stperiod")
        if not stperiod:
            return Response(
                {"error": "stperiod parameter is required (1-12)"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            stperiod = int(stperiod)
            if stperiod < 1 or stperiod > 12:
                raise ValueError
        except ValueError:
            return Response(
                {"error": "stperiod must be an integer between 1 and 12"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        journals = self.get_queryset().filter(stperiod=stperiod)

        if not journals.exists():
            return Response(
                {
                    "status": "no_data",
                    "message": f"No standing journals found for start period {stperiod}",
                    "data": [],
                }
            )

        page = self.paginate_queryset(journals)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(journals, many=True)
        return Response(serializer.data)


class GLSpreadViewSet(ShopFilterMixin, viewsets.ModelViewSet):
    """
    ViewSet for managing GL Spread Sheets.

    Provides CRUD operations plus additional actions:
    - summary: Get summary statistics for all spread sheets
    - by_account: Get spread sheet for a specific account
    - variance_analysis: Get variance between actuals and budgets
    """

    queryset = GLSpread.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["accno"]
    search_fields = ["accno", "name"]
    ordering_fields = [
        "accno",
        "name",
        "ytddebit",
        "ytdcredit",
        "curdebit",
        "curcredit",
    ]
    ordering = ["accno"]

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == "list":
            return GLSpreadListSerializer
        elif self.action == "retrieve":
            return GLSpreadDetailSerializer
        return GLSpreadSerializer

    @action(detail=False, methods=["get"])
    def summary(self, request):
        """Get summary statistics for all spread sheets."""
        spreads = self.get_queryset()

        total_ytd_debit = spreads.aggregate(total=Sum("ytddebit"))["total"] or Decimal(
            "0.00"
        )
        total_ytd_credit = spreads.aggregate(total=Sum("ytdcredit"))[
            "total"
        ] or Decimal("0.00")
        total_cur_debit = spreads.aggregate(total=Sum("curdebit"))["total"] or Decimal(
            "0.00"
        )
        total_cur_credit = spreads.aggregate(total=Sum("curcredit"))[
            "total"
        ] or Decimal("0.00")
        total_curbuddeb = spreads.aggregate(total=Sum("curbuddeb"))["total"] or Decimal(
            "0.00"
        )
        total_curbudcred = spreads.aggregate(total=Sum("curbudcred"))[
            "total"
        ] or Decimal("0.00")
        total_ytdbuddeb = spreads.aggregate(total=Sum("ytdbuddeb"))["total"] or Decimal(
            "0.00"
        )
        total_ytdbudcred = spreads.aggregate(total=Sum("ytdbudcred"))[
            "total"
        ] or Decimal("0.00")

        return Response(
            {
                "total_accounts": spreads.count(),
                "ytd_actual": {
                    "debit": float(total_ytd_debit),
                    "credit": float(total_ytd_credit),
                    "net": float(total_ytd_debit - total_ytd_credit),
                },
                "current_period_actual": {
                    "debit": float(total_cur_debit),
                    "credit": float(total_cur_credit),
                    "net": float(total_cur_debit - total_cur_credit),
                },
                "current_period_budget": {
                    "debit": float(total_curbuddeb),
                    "credit": float(total_curbudcred),
                    "net": float(total_curbuddeb - total_curbudcred),
                },
                "ytd_budget": {
                    "debit": float(total_ytdbuddeb),
                    "credit": float(total_ytdbudcred),
                    "net": float(total_ytdbuddeb - total_ytdbudcred),
                },
            }
        )

    @action(detail=False, methods=["get"])
    def by_account(self, request):
        """Get spread sheet for a specific account."""
        accno = request.query_params.get("accno")
        if not accno:
            return Response(
                {"error": "accno parameter is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            spread = self.get_queryset().get(accno=accno)
        except GLSpread.DoesNotExist:
            return Response(
                {
                    "status": "no_data",
                    "message": f"No spread sheet found for account {accno}",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = self.get_serializer(spread)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def variance_analysis(self, request):
        """Get variance between actuals and budgets."""
        spreads = self.get_queryset()

        results = []
        for spread in spreads:
            cur_actual_net = spread.curdebit - spread.curcredit
            cur_budget_net = spread.curbuddeb - spread.curbudcred
            ytd_actual_net = spread.ytddebit - spread.ytdcredit
            ytd_budget_net = spread.ytdbuddeb - spread.ytdbudcred

            cur_variance = cur_actual_net - cur_budget_net
            ytd_variance = ytd_actual_net - ytd_budget_net

            cur_variance_pct = 0
            if cur_budget_net != 0:
                cur_variance_pct = (cur_variance / cur_budget_net) * 100

            ytd_variance_pct = 0
            if ytd_budget_net != 0:
                ytd_variance_pct = (ytd_variance / ytd_budget_net) * 100

            results.append(
                {
                    "accno": spread.accno,
                    "name": spread.name,
                    "current_period": {
                        "actual_net": float(cur_actual_net),
                        "budget_net": float(cur_budget_net),
                        "variance": float(cur_variance),
                        "variance_pct": float(cur_variance_pct),
                    },
                    "ytd": {
                        "actual_net": float(ytd_actual_net),
                        "budget_net": float(ytd_budget_net),
                        "variance": float(ytd_variance),
                        "variance_pct": float(ytd_variance_pct),
                    },
                }
            )

        return Response(results)
