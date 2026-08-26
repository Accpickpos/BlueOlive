"""
Debtors views.
API viewsets for all debtor-related operations.
Based on DMAST, DEBTRAN, DEBTOPEN, DPDC, DEBTORAUD tables.
"""

import logging
from datetime import date, timedelta
from decimal import Decimal

from apps.common.mixins import LookupActionMixin
from apps.common.permissions import BaseModelPermission, CanPostTransaction
from apps.pos.models import CashSale, CreditNote, Invoice, JobCard
from apps.purchase_orders.models import PurchaseOrder
from apps.shop_filter_mixin import ShopFilterMixin
from django.db import transaction as db_transaction
from django.db.models import Count, F, Q, Sum
from django.db.models.functions import TruncMonth
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import SAFE_METHODS, IsAuthenticated
from rest_framework.response import Response

from .filters import DebtorFilter, DebtorTransactionFilter
from .models import Darea, Debtopen, Debtor, DebtorAudit, DebtorTransaction, Dpdc
from .permissions import (
    CanChargeInterest,
    CanModifyDebtor,
    CanPostInvoice,
    HasDebtorPermission,
)
from .serializers import (
    AgeAnalysisSerializer,
    DareaSerializer,
    DebteopenSerializer,
    DebtOpenListSerializer,
    DebtorAuditSerializer,
    DebtorCreateUpdateSerializer,
    DebtorDetailSerializer,
    DebtorListSerializer,
    DebtorLookupSerializer,
    DebtorSummarySerializer,
    DebtorTransactionSerializer,
    DebtranListSerializer,
    DpdcSerializer,
)
from .services import DebtorService

logger = logging.getLogger(__name__)


class DebtorViewSet(LookupActionMixin, ShopFilterMixin, viewsets.ModelViewSet):
    """
    ViewSet for managing debtors (customers) - DMAST table.
    """

    queryset = Debtor.objects.all()
    lookup_field = "dno"
    lookup_serializer_class = DebtorLookupSerializer
    permission_classes = [IsAuthenticated, HasDebtorPermission]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = DebtorFilter
    search_fields = ["dno", "dname", "dsname", "dcontact"]
    ordering_fields = ["dno", "dname", "dcrnt", "created_at"]
    ordering = ["dno"]

    def get_permissions(self):
        """
        Read (list/retrieve/lookup/summary/etc — SAFE_METHODS) stays open to
        any authenticated user via HasDebtorPermission's own SAFE_METHODS
        bypass. Writes (create/update/partial_update/destroy and the POST
        actions below: block/unblock/convert_category) additionally require
        CanModifyDebtor's ADMIN/MANAGER role check.
        """
        if self.request.method in SAFE_METHODS:
            permission_classes = [IsAuthenticated, HasDebtorPermission]
        else:
            permission_classes = [IsAuthenticated, HasDebtorPermission, CanModifyDebtor]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """Override to add logging for debugging 500 errors."""
        logger.info(
            f"[DebtorsList] Starting get_queryset for user {self.request.user.id}"
        )
        try:
            queryset = super().get_queryset()
            logger.info(
                f"[DebtorsList] Queryset after super().get_queryset(): {queryset.query}"
            )
            return queryset
        except Exception as e:
            logger.error(
                f"[DebtorsList] Error in get_queryset: {type(e).__name__}: {str(e)}",
                exc_info=True,
            )
            raise

    def get_serializer_class(self):
        if self.action == "list":
            return DebtorListSerializer
        elif self.action in ["create", "update", "partial_update"]:
            return DebtorCreateUpdateSerializer
        return DebtorDetailSerializer

    def perform_destroy(self, instance):
        """
        Manual (§2.1, Account Details Maintenance): "Deletion is not
        permitted when: an account has a balance, or where transactions
        were posted to this account for the current month." Previously
        unenforced — DRF's default destroy() ran with no check at all.
        """
        from rest_framework.exceptions import ValidationError

        if instance.total_balance != 0:
            raise ValidationError(
                f"Cannot delete debtor {instance.dno}: account has an outstanding balance "
                f"of {instance.total_balance}."
            )

        today = date.today()
        has_transactions_this_month = DebtorTransaction.objects.filter(
            debtor=instance,
            transaction_date__year=today.year,
            transaction_date__month=today.month,
        ).exists()
        if has_transactions_this_month:
            raise ValidationError(
                f"Cannot delete debtor {instance.dno}: transactions were posted to this "
                f"account in the current month."
            )

        super().perform_destroy(instance)

    @action(detail=True, methods=["get"])
    def transactions(self, request, pk=None):
        """Get all transactions for a debtor (DEBTRAN)."""
        try:
            debtor = self.get_object()

            start_date = request.query_params.get("start_date")
            end_date = request.query_params.get("end_date")
            transaction_type = request.query_params.get("transaction_type")

            # FIX: use 'debtor' FK and correct field names from DebtorTransaction model
            transactions = DebtorTransaction.objects.filter(debtor=debtor)

            if start_date:
                transactions = transactions.filter(transaction_date__gte=start_date)
            if end_date:
                transactions = transactions.filter(transaction_date__lte=end_date)
            if transaction_type:
                transactions = transactions.filter(transaction_type=transaction_type)

            transactions = transactions.order_by("-transaction_date")

            page = self.paginate_queryset(transactions)
            if page is not None:
                serializer = DebtorTransactionSerializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = DebtorTransactionSerializer(transactions, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {"status": "error", "message": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=False, methods=["get"])
    def summary(self, request):
        """Get summary statistics for all debtors."""
        try:
            debtors = self.get_queryset()

            total_debtors = debtors.count()
            active_debtors = debtors.filter(is_active=True).count()
            # FIX: block_flag values for blocked accounts are '1','2','3','Y' per model
            blocked_debtors = debtors.filter(blockflag__in=["1", "2", "3", "Y"]).count()

            aggregates = debtors.aggregate(
                total_balance=Sum("dcrnt"),
                current_balance=Sum("dcrnt"),
                d30_total=Sum("d30"),
                d60_total=Sum("d60"),
                d90_total=Sum("d90"),
            )

            overdue_120_plus = sum(
                [
                    debtors.aggregate(Sum("d120"))["d120__sum"] or Decimal("0.00"),
                    debtors.aggregate(Sum("d150"))["d150__sum"] or Decimal("0.00"),
                    debtors.aggregate(Sum("d180"))["d180__sum"] or Decimal("0.00"),
                ]
            )

            data = {
                "total_debtors": total_debtors,
                "active_debtors": active_debtors,
                "blocked_debtors": blocked_debtors,
                "total_balance": float(aggregates["total_balance"] or Decimal("0.00")),
                "current_balance": float(
                    aggregates["current_balance"] or Decimal("0.00")
                ),
                "overdue_30": float(aggregates["d30_total"] or Decimal("0.00")),
                "overdue_60": float(aggregates["d60_total"] or Decimal("0.00")),
                "overdue_90": float(aggregates["d90_total"] or Decimal("0.00")),
                "overdue_120_plus": float(overdue_120_plus),
            }

            serializer = DebtorSummarySerializer(data)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {"status": "error", "message": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=True, methods=["post"])
    def block(self, request, pk=None):
        """Block a debtor account."""
        try:
            debtor = self.get_object()
            debtor.set_blocked(True)
            return Response(
                {
                    "status": "success",
                    "message": f"Debtor {debtor.dno} blocked successfully",
                }
            )
        except Exception as e:
            return Response(
                {"status": "error", "message": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=True, methods=["post"])
    def unblock(self, request, pk=None):
        """Unblock a debtor account."""
        try:
            debtor = self.get_object()
            debtor.set_blocked(False)
            return Response(
                {
                    "status": "success",
                    "message": f"Debtor {debtor.dno} unblocked successfully",
                }
            )
        except Exception as e:
            return Response(
                {"status": "error", "message": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=True, methods=["get"])
    def balance_details(self, request, pk=None):
        """Get detailed balance breakdown for debtor."""
        try:
            debtor = self.get_object()
            balance_data = {
                "customer_number": debtor.dno,
                "name": debtor.dname,
                "credit_limit": float(debtor.dclimit),
                "balance_breakdown": {
                    "current": float(debtor.dcrnt),
                    "30_days": float(debtor.d30),
                    "60_days": float(debtor.d60),
                    "90_days": float(debtor.d90),
                    "120_days": float(debtor.d120),
                    "150_days": float(debtor.d150),
                    "180_days": float(debtor.d180),
                },
                "total_balance": float(debtor.total_balance),
                "available_credit": float(debtor.dclimit - debtor.total_balance),
                "credit_utilization_pct": float(
                    (debtor.total_balance / debtor.dclimit * 100)
                    if debtor.dclimit > 0
                    else 0
                ),
                "is_blocked": debtor.is_blocked,
                "is_active": debtor.is_active,
                "last_payment": {
                    "date": debtor.ddatlpd,
                    "amount": float(debtor.damtlpd),
                },
                "sales": {
                    "mtd": float(debtor.dsalesm),
                    "ytd": float(debtor.dsalesy),
                },
            }
            return Response(balance_data)
        except Exception as e:
            return Response(
                {"status": "error", "message": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=False, methods=["get"], url_path="age-analysis")
    def age_analysis(self, request):
        """Get age analysis summary for all debtors."""
        try:
            debtors = self.get_queryset()

            aggregates = debtors.aggregate(
                total_current=Sum("dcrnt"),
                total_30=Sum("d30"),
                total_60=Sum("d60"),
                total_90=Sum("d90"),
                total_120=Sum("d120"),
                total_150=Sum("d150"),
                total_180=Sum("d180"),
            )

            total_balance = sum(
                [
                    aggregates["total_current"] or Decimal("0.00"),
                    aggregates["total_30"] or Decimal("0.00"),
                    aggregates["total_60"] or Decimal("0.00"),
                    aggregates["total_90"] or Decimal("0.00"),
                    aggregates["total_120"] or Decimal("0.00"),
                    aggregates["total_150"] or Decimal("0.00"),
                    aggregates["total_180"] or Decimal("0.00"),
                ]
            )

            def calc_pct(value):
                if total_balance > 0:
                    return float(value or 0) / float(total_balance) * 100
                return 0

            data = {
                "cutoff_date": request.query_params.get("cutoff_date")
                or str(date.today()),
                "total_balance": float(total_balance),
                "buckets": [
                    {
                        "label": "Current",
                        "amount": float(aggregates["total_current"] or 0),
                        "percentage": calc_pct(aggregates["total_current"]),
                    },
                    {
                        "label": "1-30 Days",
                        "amount": float(aggregates["total_30"] or 0),
                        "percentage": calc_pct(aggregates["total_30"]),
                    },
                    {
                        "label": "31-60 Days",
                        "amount": float(aggregates["total_60"] or 0),
                        "percentage": calc_pct(aggregates["total_60"]),
                    },
                    {
                        "label": "61-90 Days",
                        "amount": float(aggregates["total_90"] or 0),
                        "percentage": calc_pct(aggregates["total_90"]),
                    },
                    {
                        "label": "90+ Days",
                        "amount": float(
                            (aggregates["total_120"] or 0)
                            + (aggregates["total_150"] or 0)
                            + (aggregates["total_180"] or 0)
                        ),
                        "percentage": calc_pct(
                            (aggregates["total_120"] or 0)
                            + (aggregates["total_150"] or 0)
                            + (aggregates["total_180"] or 0)
                        ),
                    },
                ],
            }

            return Response(data)
        except Exception as e:
            return Response(
                {"status": "error", "message": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=False, methods=["get"], url_path="top-accounts")
    def top_accounts(self, request):
        """Get top debtor accounts by balance."""
        try:
            limit = int(request.query_params.get("limit", 10))
            sort_by = request.query_params.get("sort_by", "balance")

            debtors = self.get_queryset()

            if sort_by == "balance":
                debtors = debtors.order_by("-dcrnt")[:limit]
            elif sort_by == "overdue":
                debtors = debtors.annotate(
                    overdue=F("d30")
                    + F("d60")
                    + F("d90")
                    + F("d120")
                    + F("d150")
                    + F("d180")
                ).order_by("-overdue")[:limit]
            else:
                debtors = debtors.order_by("-dsalesy")[:limit]

            results = [
                {
                    "id": d.id,
                    "customer_number": d.dno,
                    "name": d.dname,
                    "balance_current": float(d.dcrnt),
                    "total_balance": float(d.total_balance),
                    "overdue_balance": float(d.overdue_balance),
                    "credit_limit": float(d.dclimit),
                }
                for d in debtors
            ]

            return Response(results)
        except Exception as e:
            return Response(
                {"status": "error", "message": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=False, methods=["get"])
    def invoices(self, request):
        """Get invoice records for debtors."""
        import logging

        logger = logging.getLogger(__name__)
        try:
            debtor_id = request.query_params.get("debtor")
            start_date = request.query_params.get("start_date")
            end_date = request.query_params.get("end_date")

            # Handle limit parameter with proper error handling
            limit_param = request.query_params.get("limit", "100")
            try:
                limit = int(limit_param)
            except (ValueError, TypeError):
                limit = 100
            limit = min(max(limit, 1), 1000)  # Clamp between 1 and 1000

            logger.info(
                f"Fetching invoices with debtor_id={debtor_id}, start={start_date}, end={end_date}, limit={limit}"
            )

            # FIX: use correct field names from DebtorTransaction model
            invoices = DebtorTransaction.objects.filter(transaction_type="IN")

            if debtor_id:
                invoices = invoices.filter(debtor_id=debtor_id)
            if start_date:
                invoices = invoices.filter(transaction_date__gte=start_date)
            if end_date:
                invoices = invoices.filter(transaction_date__lte=end_date)

            invoices = invoices.order_by("-transaction_date")[:limit]

            serializer = DebtorTransactionSerializer(invoices, many=True)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error fetching invoices: {str(e)}", exc_info=True)
            return Response(
                {"status": "error", "message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=["post"])
    def convert_category(self, request, pk=None):
        """Convert debtor to a different category."""
        try:
            debtor = self.get_object()
            new_category = request.data.get("category")

            if not new_category:
                return Response(
                    {"error": "Category is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            debtor.acctype = new_category
            debtor.save(update_fields=["acctype"])

            return Response(
                {
                    "status": "success",
                    "message": f"Debtor {debtor.dno} converted to category {new_category}",
                }
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["get"])
    def sales_history(self, request, pk=None):
        """Get sales history for a debtor."""
        try:
            debtor = self.get_object()

            start_date = request.query_params.get("start_date")
            end_date = request.query_params.get("end_date")

            # FIX: use correct FK and field names
            transactions = DebtorTransaction.objects.filter(debtor=debtor)

            if start_date:
                transactions = transactions.filter(transaction_date__gte=start_date)
            if end_date:
                transactions = transactions.filter(transaction_date__lte=end_date)

            monthly_sales = (
                transactions.filter(transaction_type__in=["IN", "CS"])
                .annotate(month=TruncMonth("transaction_date"))
                .values("month")
                .annotate(
                    total_sales=Sum("total_amount"), transaction_count=Count("id")
                )
                .order_by("month")
            )

            results = [
                {
                    "month": item["month"].strftime("%Y-%m") if item["month"] else None,
                    "total_sales": float(item["total_sales"] or 0),
                    "transaction_count": item["transaction_count"],
                }
                for item in monthly_sales
            ]

            return Response(results)
        except Exception as e:
            return Response(
                {"status": "error", "message": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class DebtorTransactionViewSet(ShopFilterMixin, viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for debtor transactions (DEBTRAN).
    """

    queryset = DebtorTransaction.objects.all()
    serializer_class = DebtorTransactionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = DebtorTransactionFilter
    # FIX: use correct field names from DebtorTransaction model
    ordering_fields = ["transaction_date", "total_amount"]
    ordering = ["-transaction_date"]

    def get_queryset(self):
        # FIX: select_related uses correct FK name 'debtor'
        return super().get_queryset().select_related("debtor")

    @action(detail=False, methods=["get"])
    def summary(self, request):
        """Get transaction summary by type."""
        try:
            summary = (
                self.get_queryset()
                .values("transaction_type")
                .annotate(count=Count("id"), total=Sum("total_amount"))
                .order_by("transaction_type")
            )
            return Response(list(summary))
        except Exception as e:
            return Response(
                {"status": "error", "message": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=False, methods=["get"])
    def monthly_trends(self, request):
        """Get monthly transaction trends for the past year."""
        try:
            trends = (
                self.get_queryset()
                .filter(transaction_date__gte=date.today() - timedelta(days=365))
                .annotate(month=TruncMonth("transaction_date"))
                .values("month", "transaction_type")
                .annotate(count=Count("id"), total=Sum("total_amount"))
                .order_by("month", "transaction_type")
            )
            return Response(list(trends))
        except Exception as e:
            return Response(
                {"status": "error", "message": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=False, methods=["get"])
    def aging_summary(self, request):
        """Get aging summary for all outstanding transactions."""
        try:
            aging = DebtorTransaction.objects.aging_analysis()
            return Response(aging)
        except Exception as e:
            return Response(
                {"status": "error", "message": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=False, methods=["get"])
    def debtor_summary(self, request):
        """Get summary of outstanding balance by debtor."""
        try:
            # FIX: use correct FK 'debtor' and field names
            summary = (
                self.get_queryset()
                .filter(transaction_type__in=["IN", "CS"], is_allocated=False)
                .values("debtor", "debtor__name")
                .annotate(
                    outstanding=Sum("total_amount"), transaction_count=Count("id")
                )
                .order_by("-outstanding")
            )
            return Response(list(summary))
        except Exception as e:
            return Response(
                {"status": "error", "message": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(
        detail=False,
        methods=["post"],
        permission_classes=[IsAuthenticated, CanPostInvoice],
    )
    def post_receipt(self, request):
        """Record a receipt (payment) against a debtor's account."""
        try:
            debtor = Debtor.objects.get(pk=request.data.get("debtor_id"))
            amount = Decimal(str(request.data.get("amount", 0)))
            trans = DebtorService.post_receipt(
                debtor=debtor,
                amount=amount,
                custref=request.data.get("reference_number", ""),
            )
            return Response(
                DebtorTransactionSerializer(trans).data, status=status.HTTP_201_CREATED
            )
        except Debtor.DoesNotExist:
            return Response(
                {"status": "error", "message": "Debtor not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except ValueError as e:
            return Response(
                {"status": "error", "message": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response(
                {"status": "error", "message": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(
        detail=False,
        methods=["post"],
        permission_classes=[IsAuthenticated, CanPostInvoice],
    )
    def post_debit(self, request):
        """Post a debit journal (increases the amount owing)."""
        try:
            debtor = Debtor.objects.get(pk=request.data.get("debtor_id"))
            amount = Decimal(str(request.data.get("amount", 0)))
            trans = DebtorService.post_journal(
                debtor=debtor,
                journal_type="JD",
                amount=amount,
                custref=request.data.get("description", ""),
            )
            return Response(
                DebtorTransactionSerializer(trans).data, status=status.HTTP_201_CREATED
            )
        except Debtor.DoesNotExist:
            return Response(
                {"status": "error", "message": "Debtor not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except ValueError as e:
            return Response(
                {"status": "error", "message": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response(
                {"status": "error", "message": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(
        detail=False,
        methods=["post"],
        permission_classes=[IsAuthenticated, CanPostInvoice],
    )
    def post_credit(self, request):
        """Post a credit journal (reduces the amount owing)."""
        try:
            debtor = Debtor.objects.get(pk=request.data.get("debtor_id"))
            amount = Decimal(str(request.data.get("amount", 0)))
            trans = DebtorService.post_journal(
                debtor=debtor,
                journal_type="JC",
                amount=amount,
                custref=request.data.get("description", ""),
            )
            return Response(
                DebtorTransactionSerializer(trans).data, status=status.HTTP_201_CREATED
            )
        except Debtor.DoesNotExist:
            return Response(
                {"status": "error", "message": "Debtor not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except ValueError as e:
            return Response(
                {"status": "error", "message": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response(
                {"status": "error", "message": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(
        detail=False,
        methods=["post"],
        permission_classes=[IsAuthenticated, CanChargeInterest],
    )
    def charge_interest(self, request):
        """
        Charge interest on a single debtor's overdue balance. If `amount` is
        given, that value is charged directly; otherwise it's computed from
        the debtor's aged balances via DebtorService.calculate_interest.
        """
        try:
            debtor = Debtor.objects.get(pk=request.data.get("debtor_id"))
            raw_amount = request.data.get("amount")
            interest = (
                Decimal(str(raw_amount))
                if raw_amount
                else DebtorService.calculate_interest(debtor)
            )
            if interest <= 0:
                return Response(
                    {"status": "error", "message": "No interest to charge"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            trans = DebtorService.post_debtran(
                debtor=debtor,
                dtype="INT",
                dttot=interest,
                dtsub=interest,
                dtgst=Decimal("0.00"),
                custref="Interest Charge",
            )
            return Response(
                DebtorTransactionSerializer(trans).data, status=status.HTTP_201_CREATED
            )
        except Debtor.DoesNotExist:
            return Response(
                {"status": "error", "message": "Debtor not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except ValueError as e:
            return Response(
                {"status": "error", "message": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response(
                {"status": "error", "message": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class DebteopenViewSet(ShopFilterMixin, viewsets.ModelViewSet):
    """
    ViewSet for open item transactions (DEBTOPEN).
    """

    queryset = Debtopen.objects.all()
    serializer_class = DebteopenSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    # FIX: 'customer_number' → 'dno' to match Debtopen model FK
    filterset_fields = ["dno", "type", "posted", "ageflag"]
    ordering_fields = ["date", "total"]
    ordering = ["-date"]

    def get_queryset(self):
        # FIX: select_related uses correct FK name 'dno'
        return super().get_queryset().select_related("dno")

    @action(detail=False, methods=["get"])
    def outstanding(self, request):
        """Get all outstanding open items."""
        try:
            outstanding = self.get_queryset().filter(balancedue__gt=0, posted="Y")

            page = self.paginate_queryset(outstanding)
            if page is not None:
                serializer = DebteopenSerializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = DebteopenSerializer(outstanding, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {"status": "error", "message": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAuthenticated, CanPostInvoice],
    )
    def allocate(self, request, pk=None):
        """Allocate payment against a single open item."""
        try:
            open_item = self.get_object()
            allocation_amount = Decimal(str(request.data.get("amount", 0)))

            if allocation_amount <= 0:
                return Response(
                    {
                        "status": "error",
                        "message": "Allocation amount must be greater than zero",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if allocation_amount > open_item.balancedue:
                return Response(
                    {
                        "status": "error",
                        "message": "Allocation cannot exceed balance due",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            open_item.balancedue -= allocation_amount
            open_item.save(update_fields=["balancedue"])

            return Response(
                {
                    "status": "success",
                    "message": "Payment allocated successfully",
                    "new_balance": float(open_item.balancedue),
                }
            )
        except Exception as e:
            return Response(
                {"status": "error", "message": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(
        detail=False,
        methods=["post"],
        url_path="allocate",
        permission_classes=[IsAuthenticated, CanPostInvoice],
    )
    def allocate_receipt(self, request):
        """
        Batch-allocate a single receipt across one or more open items for a
        debtor. Payload: {debtor_id, receipt_amount, allocations: [{open_item_id, amount}, ...]}
        """
        debtor_id = request.data.get("debtor_id")
        allocations = request.data.get("allocations") or []

        if not allocations:
            return Response(
                {"status": "error", "message": "No allocations provided"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        receipt_id = request.data.get("receipt_transaction_id") or request.data.get(
            "receipt_id"
        )

        results = []
        try:
            with db_transaction.atomic():
                # Route through the same DebtorTransaction the receipt was
                # posted against — required now that allocations persist a
                # ReceiptAllocation row (FK to DebtorTransaction). Falls back
                # to synthesizing one for callers that only ever used this
                # endpoint's old "just reduce balancedue" behavior without
                # posting a receipt first.
                if receipt_id:
                    receipt_transaction = DebtorTransaction.objects.get(
                        pk=receipt_id, debtor_id=debtor_id
                    )
                else:
                    debtor = Debtor.objects.select_for_update().get(pk=debtor_id)
                    total_amount = sum(Decimal(str(a["amount"])) for a in allocations)
                    receipt_transaction = DebtorService.post_receipt(
                        debtor=debtor, amount=total_amount
                    )

                for alloc in allocations:
                    open_item = Debtopen.objects.select_for_update().get(
                        pk=alloc["open_item_id"], dno_id=debtor_id
                    )
                    DebtorService.apply_receipt_allocation(
                        open_item=open_item,
                        amount_paid=alloc["amount"],
                        settlement_discount=alloc.get("settlement_discount", 0),
                        receipt_transaction=receipt_transaction,
                    )
                    results.append(
                        {
                            "open_item_id": open_item.id,
                            "new_balance": float(open_item.balancedue),
                        }
                    )

            return Response({"status": "success", "allocations": results})
        except Debtopen.DoesNotExist:
            return Response(
                {"status": "error", "message": "Open item not found for this debtor"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except (ValueError, KeyError) as e:
            return Response(
                {"status": "error", "message": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class DpdcViewSet(ShopFilterMixin, viewsets.ModelViewSet):
    """
    ViewSet for post-dated cheques (DPDC).
    """

    queryset = Dpdc.objects.all()
    serializer_class = DpdcSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    # 'dno' is correct — matches Dpdc model FK
    filterset_fields = ["dno", "status", "date"]
    ordering_fields = ["date", "amount"]
    ordering = ["date"]

    def get_queryset(self):
        return super().get_queryset().select_related("dno")

    @action(detail=False, methods=["get"])
    def active(self, request):
        """Get all outstanding post-dated cheques."""
        try:
            active = self.get_queryset().filter(status="OUTSTANDING")

            page = self.paginate_queryset(active)
            if page is not None:
                serializer = DpdcSerializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = DpdcSerializer(active, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {"status": "error", "message": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=False, methods=["get"])
    def due_today(self, request):
        """Get PDCs due today."""
        try:
            today = date.today()
            pdcs = self.get_queryset().filter(date=today, status="OUTSTANDING")

            if not pdcs.exists():
                return Response(
                    {
                        "status": "no_data",
                        "message": "No post-dated cheques due today",
                        "data": [],
                    }
                )

            serializer = DpdcSerializer(pdcs, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {"status": "error", "message": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=True, methods=["post"])
    def process(self, request, pk=None):
        """Mark cheque as received (banked, awaiting clearance)."""
        try:
            pdc = self.get_object()

            if pdc.status == "CLEARED":
                return Response(
                    {"status": "error", "message": "PDC already cleared"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            pdc.status = "RECEIVED"
            pdc.received_date = date.today()
            pdc.save(update_fields=["status", "received_date"])

            return Response({"status": "success", "message": "PDC marked as received"})
        except Exception as e:
            return Response(
                {"status": "error", "message": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        """Mark a post-dated cheque as dishonoured."""
        try:
            pdc = self.get_object()

            if pdc.status == "DISHONOURED":
                return Response(
                    {"error": "PDC already marked dishonoured"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if pdc.status == "CLEARED":
                return Response(
                    {"error": "Cannot dishonour a cleared PDC"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            pdc.status = "DISHONOURED"
            pdc.save(update_fields=["status"])

            return Response(
                {"status": "success", "message": "PDC marked as dishonoured"}
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class DebtorAuditViewSet(ShopFilterMixin, viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for debtor audit records (DEBTORAUD).
    """

    queryset = DebtorAudit.objects.all()
    serializer_class = DebtorAuditSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    # FIX: 'customer_number' → 'dno' to match DebtorAudit model FK
    filterset_fields = ["dno", "type", "date"]
    ordering_fields = ["date"]
    ordering = ["-date"]

    def get_queryset(self):
        # FIX: select_related uses correct FK name 'dno'
        return super().get_queryset().select_related("dno")


class DareaViewSet(ShopFilterMixin, viewsets.ModelViewSet):
    """
    ViewSet for sales area/salesman data (DAREA).
    """

    queryset = Darea.objects.all()
    serializer_class = DareaSerializer
    permission_classes = [IsAuthenticated]
    ordering_fields = ["darea", "dareaname"]
    ordering = ["darea"]


class DocumentSearchViewSet(viewsets.ViewSet):
    """
    Unified document search endpoint for Stockfinder API integration.
    """

    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"], url_path="search")
    def search(self, request):
        try:
            doc_type = request.query_params.get("type", "all").lower()
            doc_number = request.query_params.get("number", "").strip()
            date_from = request.query_params.get("date_from")
            date_to = request.query_params.get("date_to")
            debtor_id = request.query_params.get("debtor_id")
            doc_status = request.query_params.get("status")

            results = {
                "invoices": [],
                "credit_notes": [],
                "cash_sales": [],
                "purchase_orders": [],
                "job_cards": [],
                "total_documents": 0,
            }

            if doc_type in ["invoice", "all"]:
                invoices = Invoice.objects.all()
                if doc_number:
                    invoices = invoices.filter(invoice_number__icontains=doc_number)
                if debtor_id:
                    invoices = invoices.filter(debtor__dno=debtor_id)
                if doc_status:
                    invoices = invoices.filter(status=doc_status)
                if date_from:
                    invoices = invoices.filter(invoice_date__gte=date_from)
                if date_to:
                    invoices = invoices.filter(invoice_date__lte=date_to)
                invoices = invoices.select_related("debtor").values(
                    "id",
                    "invoice_number",
                    "invoice_date",
                    "debtor__name",
                    "total_amount",
                    "status",
                )[:50]
                results["invoices"] = [
                    {
                        "document_id": inv["id"],
                        "document_number": inv["invoice_number"],
                        "document_type": "invoice",
                        "document_date": inv["invoice_date"],
                        "customer": inv["debtor__name"],
                        "amount": float(inv["total_amount"]),
                        "status": inv["status"],
                    }
                    for inv in invoices
                ]

            if doc_type in ["credit_note", "all"]:
                credit_notes = CreditNote.objects.all()
                if doc_number:
                    credit_notes = credit_notes.filter(
                        credit_number__icontains=doc_number
                    )
                if debtor_id:
                    credit_notes = credit_notes.filter(debtor_account=debtor_id)
                if date_from:
                    credit_notes = credit_notes.filter(credit_date__gte=date_from)
                if date_to:
                    credit_notes = credit_notes.filter(credit_date__lte=date_to)
                credit_notes = credit_notes.values(
                    "id",
                    "credit_number",
                    "credit_date",
                    "customer_name",
                    "total_amount",
                    "is_posted",
                )[:50]
                results["credit_notes"] = [
                    {
                        "document_id": cn["id"],
                        "document_number": cn["credit_number"],
                        "document_type": "credit_note",
                        "document_date": cn["credit_date"],
                        "customer": cn["customer_name"],
                        "amount": float(cn["total_amount"]),
                        "status": "POSTED" if cn["is_posted"] else "DRAFT",
                    }
                    for cn in credit_notes
                ]

            if doc_type in ["cash_sale", "all"]:
                cash_sales = CashSale.objects.all()
                if doc_number:
                    cash_sales = cash_sales.filter(sale_number__icontains=doc_number)
                if date_from:
                    cash_sales = cash_sales.filter(sale_date__gte=date_from)
                if date_to:
                    cash_sales = cash_sales.filter(sale_date__lte=date_to)
                cash_sales = cash_sales.values(
                    "id",
                    "sale_number",
                    "sale_date",
                    "customer_name",
                    "total_amount",
                    "is_posted",
                )[:50]
                results["cash_sales"] = [
                    {
                        "document_id": cs["id"],
                        "document_number": cs["sale_number"],
                        "document_type": "cash_sale",
                        "document_date": cs["sale_date"],
                        "customer": cs["customer_name"],
                        "amount": float(cs["total_amount"]),
                        "status": "POSTED" if cs["is_posted"] else "DRAFT",
                    }
                    for cs in cash_sales
                ]

            if doc_type in ["purchase_order", "all"]:
                purchase_orders = PurchaseOrder.objects.all()
                if doc_number:
                    purchase_orders = purchase_orders.filter(
                        po_number__icontains=doc_number
                    )
                if doc_status:
                    purchase_orders = purchase_orders.filter(status=doc_status)
                if date_from:
                    purchase_orders = purchase_orders.filter(po_date__gte=date_from)
                if date_to:
                    purchase_orders = purchase_orders.filter(po_date__lte=date_to)
                purchase_orders = purchase_orders.select_related("supplier").values(
                    "id",
                    "po_number",
                    "po_date",
                    "supplier__cname",
                    "total_amount",
                    "status",
                )[:50]
                results["purchase_orders"] = [
                    {
                        "document_id": po["id"],
                        "document_number": po["po_number"],
                        "document_type": "purchase_order",
                        "document_date": po["po_date"],
                        "supplier": po["supplier__cname"],
                        "amount": float(po["total_amount"]),
                        "status": po["status"],
                    }
                    for po in purchase_orders
                ]

            if doc_type in ["job_card", "all"]:
                job_cards = JobCard.objects.all()
                if doc_number:
                    job_cards = job_cards.filter(job_number__icontains=doc_number)
                if doc_status:
                    job_cards = job_cards.filter(status=doc_status)
                if date_from:
                    job_cards = job_cards.filter(job_date__gte=date_from)
                if date_to:
                    job_cards = job_cards.filter(job_date__lte=date_to)
                job_cards = job_cards.values(
                    "id",
                    "job_number",
                    "job_date",
                    "customer_name",
                    "total_amount",
                    "status",
                )[:50]
                results["job_cards"] = [
                    {
                        "document_id": jc["id"],
                        "document_number": jc["job_number"],
                        "document_type": "job_card",
                        "document_date": jc["job_date"],
                        "customer": jc["customer_name"],
                        "amount": float(jc["total_amount"]),
                        "status": jc["status"],
                    }
                    for jc in job_cards
                ]

            results["total_documents"] = (
                len(results["invoices"])
                + len(results["credit_notes"])
                + len(results["cash_sales"])
                + len(results["purchase_orders"])
                + len(results["job_cards"])
            )

            return Response(results)

        except Exception as e:
            return Response(
                {"status": "error", "message": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
