"""
General Ledger views.
API viewsets for general ledger operations.
"""

from datetime import date
from decimal import Decimal

from apps.shop_filter_mixin import ShopFilterMixin
from django.db import transaction
from django.db.models import Avg, Count, F, Max, Min, Q, Sum
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import SAFE_METHODS, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .exceptions import GLPostingException
from .models import (
    GLBatch,
    GLIntegrationSettings,
    GLMast,
    GLParam,
    GLRep,
    GLSpread,
    GLStJnl,
    GLTran,
)
from .permissions import (
    CanManageGL,
    CanPerformPeriodEnd,
    CanPerformYearEnd,
    CanPostGLBatch,
    CanPostStandingJournal,
)
from .serializers import (
    GLBatchDetailSerializer,
    GLBatchListSerializer,
    GLBatchSerializer,
    GLIntegrationSettingsSerializer,
    GLMastDetailSerializer,
    GLMastListSerializer,
    GLMastSerializer,
    GLParamSerializer,
    GLRepDetailSerializer,
    GLRepListSerializer,
    GLRepSerializer,
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
from .services import GLPostingService


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

    def get_permissions(self):
        """Read (list/retrieve/summary/etc.) stays open to any authenticated
        user; create/update/delete require CanManageGL's Accountant/Admin
        role check."""
        if self.request.method in SAFE_METHODS:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAuthenticated, CanManageGL]
        return [permission() for permission in permission_classes]

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

    # Fields that identify *what* a ledger posting was — once a GLTran
    # exists it's a historical entry (there is no draft/posted distinction
    # on this model, unlike cash_book's is_reconciled), so these must not be
    # silently rewritten via PATCH/PUT after the fact.
    IMMUTABLE_FIELDS_ON_UPDATE = ("accno", "amount", "date", "type")

    def get_permissions(self):
        """Read (list/retrieve/by_batch/etc.) stays open to any authenticated
        user; create/update/delete require CanManageGL's Accountant/Admin
        role check."""
        if self.request.method in SAFE_METHODS:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAuthenticated, CanManageGL]
        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == "list":
            return GLTranListSerializer
        elif self.action == "retrieve":
            return GLTranDetailSerializer
        return GLTranSerializer

    def create(self, request, *args, **kwargs):
        """
        A single GLTran row can never satisfy the spec's "only journals in
        balance will be saved" rule — one row is one leg of a double-entry
        posting, not a complete transaction. Direct creation through this
        endpoint is blocked entirely; balanced postings must go through
        GLBatch capture (/general-ledger/batches/{batchno}/post/) or a
        Standing Journal (/general-ledger/standing-journals/post_due/).

        System-sourced postings (e.g. apps.gas.services.LedgerPostingService,
        the Integration Transfer pipeline) write GLTran via the ORM/
        GLPostingService directly and never go through this ViewSet, so
        blocking create() here does not affect them.
        """
        raise ValidationError(
            "Direct single-row GL postings are not permitted — a GL transaction "
            "must be part of a balanced journal. Use GLBatch capture "
            "(POST /general-ledger/batches/ then .../post/) or a Standing Journal "
            "instead."
        )

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        for field in self.IMMUTABLE_FIELDS_ON_UPDATE:
            if field in request.data and str(request.data[field]) != str(
                getattr(instance, field)
            ):
                raise ValidationError(
                    f"Cannot change '{field}' on an existing GL transaction "
                    f"— it is a historical ledger posting."
                )
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)

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

    def get_permissions(self):
        """Read stays open to any authenticated user; create/update/delete
        require CanManageGL's Accountant/Admin role check."""
        if self.request.method in SAFE_METHODS:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAuthenticated, CanManageGL]
        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == "list":
            return GLStJnlListSerializer
        elif self.action == "retrieve":
            return GLStJnlDetailSerializer
        return GLStJnlSerializer

    @staticmethod
    def _journal_balance(journalno, exclude_pk=None):
        """Sum amount by drorcr across every GLStJnl row sharing journalno
        (a standing journal is one journalno with 2+ lines, one row per
        account/leg — mirrors how a GLBatch groups lines by batchno).
        Returns (total_debit, total_credit)."""
        qs = GLStJnl.objects.filter(journalno=journalno)
        if exclude_pk is not None:
            qs = qs.exclude(pk=exclude_pk)
        total_debit = qs.filter(drorcr="D").aggregate(total=Sum("amount"))[
            "total"
        ] or Decimal("0.00")
        total_credit = qs.filter(drorcr="C").aggregate(total=Sum("amount"))[
            "total"
        ] or Decimal("0.00")
        return total_debit, total_credit

    def _validate_balance_with(self, journalno, drorcr, amount, exclude_pk=None):
        """Raise ValidationError if adding/editing this one line would leave
        journalno's full set of lines unbalanced. A standing journal is only
        meaningful as a complete, balanced set — a lone unbalanced leg must
        never be persisted, same rule as GLBatch/GLTran."""
        total_debit, total_credit = self._journal_balance(
            journalno, exclude_pk=exclude_pk
        )
        if drorcr == "D":
            total_debit += amount
        else:
            total_credit += amount
        if total_debit != total_credit:
            raise ValidationError(
                f"Journal {journalno} would not balance: debits={total_debit}, "
                f"credits={total_credit}. Standing journal lines must net to zero "
                "across the whole journalno before they can be saved — add the "
                "offsetting line(s) in the same request sequence, or adjust the amount."
            )

    def perform_create(self, serializer):
        self._validate_balance_with(
            serializer.validated_data["journalno"],
            serializer.validated_data["drorcr"],
            serializer.validated_data["amount"],
        )
        serializer.save()

    def perform_update(self, serializer):
        instance = serializer.instance
        journalno = serializer.validated_data.get("journalno", instance.journalno)
        drorcr = serializer.validated_data.get("drorcr", instance.drorcr)
        amount = serializer.validated_data.get("amount", instance.amount)
        self._validate_balance_with(journalno, drorcr, amount, exclude_pk=instance.pk)
        serializer.save()

    @action(detail=False, methods=["get"])
    def validate_balance(self, request):
        """Check whether a journalno's full set of lines currently balances."""
        journalno = request.query_params.get("journalno")
        if not journalno:
            return Response(
                {"error": "journalno parameter is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        total_debit, total_credit = self._journal_balance(journalno)
        return Response(
            {
                "journalno": journalno,
                "total_debit": float(total_debit),
                "total_credit": float(total_credit),
                "is_balanced": total_debit == total_credit,
            }
        )

    @action(
        detail=False,
        methods=["post"],
        permission_classes=[IsAuthenticated, CanPostStandingJournal],
    )
    def post_due(self, request):
        """
        Post every Standing Journal group (grouped by journalno) whose
        nextperiod matches GLParam.curperiod.

        Per group: re-validate the balance server-side (skip + report, never
        crash the whole run, on any group that doesn't balance — a bad
        journal shouldn't block every other due journal), post via
        GLPostingService.post_batch, increment timesbal on every row in the
        group, and advance nextperiod (wrapping 12 -> 1) unless timesbal has
        now reached times (that journal is complete and stops appearing in
        future post_due runs, same filter active_journals already uses:
        timesbal < times).
        """
        param, _ = GLParam.objects.select_for_update().get_or_create(pk=1)
        due_journalnos = (
            GLStJnl.objects.filter(
                nextperiod=param.curperiod, timesbal__lt=F("times")
            )
            .values_list("journalno", flat=True)
            .distinct()
        )

        posted, skipped_unbalanced, completed = [], [], []

        with transaction.atomic():
            for journalno in due_journalnos:
                rows = list(GLStJnl.objects.filter(journalno=journalno))
                total_debit = sum(r.amount for r in rows if r.drorcr == "D")
                total_credit = sum(r.amount for r in rows if r.drorcr == "C")
                if total_debit != total_credit:
                    skipped_unbalanced.append(journalno)
                    continue

                lines = [
                    {
                        "accno": r.accno,
                        "type": r.drorcr,
                        "amount": r.amount,
                        "reference": f"STJ{journalno}",
                        "details": r.details,
                    }
                    for r in rows
                ]
                try:
                    GLPostingService.post_batch(lines)
                except GLPostingException:
                    skipped_unbalanced.append(journalno)
                    continue

                posted.append(journalno)
                for r in rows:
                    r.timesbal += 1
                    if r.timesbal >= r.times:
                        completed.append(journalno)
                    else:
                        r.nextperiod = r.nextperiod % 12 + 1
                    r.save(update_fields=["timesbal", "nextperiod", "updated_at"])

        return Response(
            {
                "journals_posted": posted,
                "journals_skipped_unbalanced": skipped_unbalanced,
                "journals_completed": sorted(set(completed)),
            }
        )

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

    def get_permissions(self):
        """Read stays open to any authenticated user; create/update/delete
        require CanManageGL's Accountant/Admin role check."""
        if self.request.method in SAFE_METHODS:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAuthenticated, CanManageGL]
        return [permission() for permission in permission_classes]

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


class GLBatchViewSet(ShopFilterMixin, viewsets.ModelViewSet):
    """
    ViewSet for GL Batch staging entries — manual/human-captured journal
    lines awaiting review, grouped by batchno. This is the spec's staging
    unit: lines accumulate here first, get checked for balance, and only a
    balanced batchno can be transferred (posted) into GLTran.

    Provides CRUD for staging rows plus:
    - balance_check: running Dr/Cr totals for a batchno (client-side sanity check)
    - post: server-revalidated transfer of a balanced batchno into GLTran
    """

    queryset = GLBatch.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["accno", "batchno", "drorcr", "source", "period"]
    search_fields = ["reference", "details", "station"]
    ordering_fields = ["capturedat", "date", "batchno", "accno", "amount"]
    ordering = ["-capturedat", "batchno", "accno"]

    def get_permissions(self):
        """Read stays open to any authenticated user; create/update/delete
        require CanManageGL's Accountant/Admin role check."""
        if self.request.method in SAFE_METHODS:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAuthenticated, CanManageGL]
        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        if self.action == "list":
            return GLBatchListSerializer
        elif self.action == "retrieve":
            return GLBatchDetailSerializer
        return GLBatchSerializer

    def perform_update(self, serializer):
        """A batch line that has already been posted is a historical
        record, same rule as GLTran — don't allow editing it out from under
        the ledger it was transferred into."""
        if serializer.instance.postdate is not None:
            raise ValidationError(
                "This batch line has already been posted to the ledger and cannot "
                "be edited."
            )
        serializer.save()

    def perform_destroy(self, instance):
        if instance.postdate is not None:
            raise ValidationError(
                "This batch line has already been posted to the ledger and cannot "
                "be deleted."
            )
        super().perform_destroy(instance)

    @action(detail=False, methods=["get"])
    def balance_check(self, request):
        """Get running Dr/Cr totals for a batchno — lets the UI show
        balanced/unbalanced status before attempting to post."""
        batchno = request.query_params.get("batchno")
        if not batchno:
            return Response(
                {"error": "batchno parameter is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        lines = self.get_queryset().filter(batchno=batchno)
        if not lines.exists():
            return Response(
                {
                    "status": "no_data",
                    "message": f"No batch lines found for batch {batchno}",
                }
            )

        total_debit = lines.filter(drorcr="D").aggregate(total=Sum("amount"))[
            "total"
        ] or Decimal("0.00")
        total_credit = lines.filter(drorcr="C").aggregate(total=Sum("amount"))[
            "total"
        ] or Decimal("0.00")
        already_posted = lines.filter(postdate__isnull=False).exists()

        return Response(
            {
                "batchno": batchno,
                "line_count": lines.count(),
                "total_debit": float(total_debit),
                "total_credit": float(total_credit),
                "is_balanced": total_debit == total_credit,
                "already_posted": already_posted,
            }
        )

    @action(
        detail=False,
        methods=["post"],
        permission_classes=[IsAuthenticated, CanPostGLBatch],
    )
    def post(self, request):
        """
        Transfer a balanced batchno's lines into GLTran and update GLMast
        period balances, then stamp every line's postdate/postime.

        Balance is re-validated server-side regardless of what balance_check
        returned earlier — never trust the client. Rejects if unbalanced, if
        the batchno has no lines, or if any line was already posted.
        """
        batchno = request.data.get("batchno")
        if not batchno:
            return Response(
                {"error": "batchno is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():
            lines_qs = GLBatch.objects.select_for_update().filter(batchno=batchno)
            rows = list(lines_qs)
            if not rows:
                return Response(
                    {"error": f"No batch lines found for batch {batchno}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if any(r.postdate is not None for r in rows):
                return Response(
                    {"error": f"Batch {batchno} has already been posted."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            lines = [
                {
                    "accno": r.accno,
                    "type": r.drorcr,
                    "amount": r.amount,
                    "date": r.date,
                    "reference": r.reference,
                    "details": r.details,
                    "period": r.period,
                    "source": r.source,
                }
                for r in rows
            ]

            try:
                gl_batchno = GLPostingService.post_batch(lines)
            except GLPostingException as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

            now = timezone.now()
            for r in rows:
                r.postdate = now.date()
                r.postime = now.strftime("%H:%M")
            GLBatch.objects.bulk_update(rows, ["postdate", "postime"])

        return Response(
            {
                "batchno": batchno,
                "gl_batchno": gl_batchno,
                "lines_posted": len(rows),
            }
        )


class GLRepViewSet(ShopFilterMixin, viewsets.ModelViewSet):
    """
    ViewSet for GL Report Format rows (Maintenance only — defines the layout
    Income Statement/Balance Sheet reports are built from; does not itself
    compute anything, see general_ledger/reports.py for that).
    """

    queryset = GLRep.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["type", "fieldtype"]
    search_fields = ["name"]
    ordering_fields = ["type", "line"]
    ordering = ["type", "line"]

    def get_permissions(self):
        if self.request.method in SAFE_METHODS:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAuthenticated, CanManageGL]
        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        if self.action == "list":
            return GLRepListSerializer
        elif self.action == "retrieve":
            return GLRepDetailSerializer
        return GLRepSerializer


class _SingletonViewSetMixin:
    """Shared plumbing for a pk=1 singleton resource (GLParam,
    GLIntegrationSettings): get_object always resolves to the one row
    regardless of the URL pk, auto-creating it on first access, and
    list/create are disabled since there is exactly one row."""

    singleton_model = None

    def get_object(self):
        obj, _ = self.singleton_model.objects.get_or_create(pk=1)
        return obj

    def list(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_object())
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        raise ValidationError(
            f"{self.singleton_model.__name__} is a singleton — use PATCH on the "
            "existing row instead of creating a new one."
        )

    def destroy(self, request, *args, **kwargs):
        raise ValidationError(f"{self.singleton_model.__name__} cannot be deleted.")


class GLParamViewSet(_SingletonViewSetMixin, viewsets.ModelViewSet):
    """
    ViewSet for the GL Parameters singleton (current period/year, next batch
    number, retained earnings account). No create/delete — there is exactly
    one row. Also exposes the higher-risk period/year-end actions and a
    read-only system status enquiry.
    """

    singleton_model = GLParam
    queryset = GLParam.objects.all()
    serializer_class = GLParamSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.request.method in SAFE_METHODS:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAuthenticated, CanManageGL]
        return [permission() for permission in permission_classes]

    @action(detail=False, methods=["get"])
    def system_status(self, request):
        """Read-only enquiry: current period/year, outstanding (unposted)
        batch count, and the most recent posted transaction date."""
        param = self.get_object()
        outstanding_batches = GLBatch.objects.filter(postdate__isnull=True)
        last_transaction = GLTran.objects.aggregate(last_date=Max("date"))[
            "last_date"
        ]

        return Response(
            {
                "startper": param.startper,
                "curperiod": param.curperiod,
                "currentyr": param.currentyr,
                "adjusted": param.adjusted,
                "next_batchno": param.batchno + 1,
                "outstanding_batches": outstanding_batches.count(),
                "outstanding_batchnos": sorted(
                    set(outstanding_batches.values_list("batchno", flat=True))
                ),
                "last_transaction_date": last_transaction,
                "retained_earnings_accno": param.retained_earnings_accno,
            }
        )

    @action(
        detail=False,
        methods=["post"],
        permission_classes=[IsAuthenticated, CanPerformPeriodEnd],
    )
    def period_end(self, request):
        """
        Advance curperiod (wraps 13 -> 1). Guarded on there being no
        unposted GLBatch rows anywhere — an outstanding batch left behind at
        period end would post into the wrong period once finally
        transferred, silently corrupting that period's balances.
        """
        with transaction.atomic():
            param = GLParam.objects.select_for_update().get_or_create(pk=1)[0]
            outstanding = GLBatch.objects.filter(postdate__isnull=True)
            if outstanding.exists():
                return Response(
                    {
                        "error": "Cannot perform Period End — unposted batch entries "
                        "remain. Post or clear them first.",
                        "outstanding_batchnos": sorted(
                            set(outstanding.values_list("batchno", flat=True))
                        ),
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            previous_period = param.curperiod
            param.curperiod = param.curperiod % 13 + 1
            param.save(update_fields=["curperiod", "updated_at"])

        return Response(
            {"previous_period": previous_period, "curperiod": param.curperiod}
        )

    @action(
        detail=False,
        methods=["post"],
        permission_classes=[IsAuthenticated, CanPerformYearEnd],
    )
    def year_end(self, request):
        """
        Year End close. See general_ledger/services.py's GLPostingService
        docstring for the posting primitive this uses, and the plan's
        year-end algorithm for the full ordering rationale — in short:
        snapshot lastyear1..12 BEFORE any zeroing, post the Income Statement
        closing journal (which reads period1..13) BEFORE zeroing those
        accounts, then reset periods/advance the year. Reversing that order
        silently posts a zero net_income closing journal.
        """
        with transaction.atomic():
            param = GLParam.objects.select_for_update().get_or_create(pk=1)[0]

            if param.curperiod != 13:
                return Response(
                    {
                        "error": "Year End can only run from period 13 (the "
                        f"adjustment period) — current period is {param.curperiod}."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            outstanding = GLBatch.objects.filter(postdate__isnull=True)
            if outstanding.exists():
                return Response(
                    {
                        "error": "Cannot perform Year End — unposted batch entries "
                        "remain. Post or clear them first.",
                        "outstanding_batchnos": sorted(
                            set(outstanding.values_list("batchno", flat=True))
                        ),
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if not param.retained_earnings_accno:
                return Response(
                    {
                        "error": "GLParam.retained_earnings_accno is not configured — "
                        "set it before running Year End."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            accounts = list(GLMast.objects.select_for_update().all())
            by_accno = {a.accno: a for a in accounts}

            # 1. Snapshot BEFORE any zeroing, and persist immediately — step 4
            #    re-reads one account (retained earnings) fresh from the DB
            #    after posting, which would otherwise silently discard an
            #    in-memory-only snapshot on that one row.
            for account in accounts:
                for month in range(1, 13):
                    setattr(
                        account,
                        f"lastyear{month}",
                        getattr(account, f"period{month}"),
                    )
            GLMast.objects.bulk_update(
                accounts, [f"lastyear{m}" for m in range(1, 13)]
            )

            # 2. Compute each Income Statement account's signed contribution
            #    from its pre-closing balance (reads period1..13, so this
            #    must happen before step 4 zeroes them).
            income_accounts = [a for a in accounts if a.type == "I"]
            closing_lines = []
            net_income = Decimal("0.00")
            for account in income_accounts:
                balance = sum(
                    getattr(account, f"period{p}") for p in range(1, 14)
                )
                if balance == 0:
                    continue
                contribution = balance if account.drorcr == "C" else -balance
                net_income += contribution
                closing_lines.append(
                    {
                        "accno": account.accno,
                        "type": "C" if account.drorcr == "D" else "D",
                        "amount": abs(balance),
                        "reference": f"YE{param.currentyr}",
                        "details": f"Year end close - {account.name}"[:30],
                    }
                )

            # 3. Post the closing journal. GLPostingService.post_batch()
            #    fetches and saves its own GLMast rows internally, so this
            #    does not touch the `accounts` list's in-memory state.
            if closing_lines and net_income != 0:
                closing_lines.append(
                    {
                        "accno": param.retained_earnings_accno,
                        "type": "C" if net_income > 0 else "D",
                        "amount": abs(net_income),
                        "reference": f"YE{param.currentyr}",
                        "details": "Year end - retained earnings"[:30],
                    }
                )
                gl_batchno = GLPostingService.post_batch(closing_lines)
                # The retained earnings account's period balance just changed
                # in the DB via post_batch's own GLMast instance — refresh
                # this one row so step 4's balbfwd carry-forward includes it.
                retained_earnings_account = by_accno.get(
                    param.retained_earnings_accno
                )
                if retained_earnings_account is not None:
                    retained_earnings_account.refresh_from_db()
            else:
                gl_batchno = None

            # 4. Zero Income Statement periods/budgets (forced to exactly 0,
            #    not derived from post_batch's effect, since a closing entry
            #    was only posted for accounts with a non-zero balance).
            #    Carry forward Balance Sheet balances into balbfwd and zero
            #    their periods — using each account's own in-memory period
            #    values, which are still accurate except for the retained
            #    earnings account, refreshed just above.
            for account in accounts:
                update_fields = ["updated_at"]
                if account.type == "I":
                    for p in range(1, 14):
                        setattr(account, f"period{p}", Decimal("0.00"))
                        update_fields.append(f"period{p}")
                    for m in range(1, 13):
                        setattr(account, f"budget{m}", Decimal("0.00"))
                        update_fields.append(f"budget{m}")
                    account.save(update_fields=update_fields)
                elif account.type == "B":
                    total = sum(
                        getattr(account, f"period{p}") for p in range(1, 14)
                    )
                    account.balbfwd = account.balbfwd + total
                    update_fields.append("balbfwd")
                    for p in range(1, 14):
                        setattr(account, f"period{p}", Decimal("0.00"))
                        update_fields.append(f"period{p}")
                    account.save(update_fields=update_fields)

            previous_year = param.currentyr
            param.currentyr += 1
            param.curperiod = param.startper
            param.adjusted = "N"
            param.save(update_fields=["currentyr", "curperiod", "adjusted", "updated_at"])

        return Response(
            {
                "previous_year": previous_year,
                "currentyr": param.currentyr,
                "curperiod": param.curperiod,
                "net_income": float(net_income),
                "closing_gl_batchno": gl_batchno,
            }
        )


class GLIntegrationSettingsViewSet(_SingletonViewSetMixin, viewsets.ModelViewSet):
    """
    ViewSet for the GL Integration Settings singleton — control-account
    mapping used by the Integration Transfer pipeline (see
    general_ledger/integration.py). No create/delete — there is exactly one
    row.
    """

    singleton_model = GLIntegrationSettings
    queryset = GLIntegrationSettings.objects.all()
    serializer_class = GLIntegrationSettingsSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.request.method in SAFE_METHODS:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAuthenticated, CanManageGL]
        return [permission() for permission in permission_classes]
