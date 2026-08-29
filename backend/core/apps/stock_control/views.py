from decimal import Decimal, InvalidOperation

from apps.common.mixins import LookupActionMixin
from apps.shop_filter_mixin import ShopFilterMixin
from django.db import transaction
from django.db.models import Case, Count, DecimalField, F, Q, Sum, When
from django.db.models.functions import ExtractHour
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import (
    Branch,
    BranchStock,
    BranchTransfer,
    BranchTransferInvoice,
    BranchTransferItem,
    ContractPricing,
    FuturePricing,
    GroupOrder,
    GroupOrderItem,
    OneTouchLookupKey,
    PackBundle,
    PackBundleIngredient,
    ShrinkWrap,
    SpecialDeal,
    StockItem,
    StockMonthlyStatistic,
    StockMovementLedger,
    StockTake,
    StockTakeItem,
    StockTransaction,
)
from .serializers import (
    BranchSerializer,
    BranchStockSerializer,
    BranchTransferInvoiceSerializer,
    BranchTransferItemSerializer,
    BranchTransferListSerializer,
    BranchTransferSerializer,
    ContractPricingSerializer,
    FuturePricingSerializer,
    GroupOrderItemSerializer,
    GroupOrderListSerializer,
    GroupOrderSerializer,
    OneTouchLookupKeySerializer,
    PackBundleIngredientSerializer,
    PackBundleSerializer,
    ShrinkWrapSerializer,
    SpecialDealSerializer,
    StockItemListSerializer,
    StockItemSerializer,
    StockMonthlyStatisticSerializer,
    StockMovementLedgerSerializer,
    StockTakeItemSerializer,
    StockTakeListSerializer,
    StockTakeSerializer,
    StockTransactionSerializer,
)
from .permissions import IsStockAccountant, IsStockMover
from .services import StockTransactionService

# ─────────────────────────────────────────────
# StockItem
# ─────────────────────────────────────────────


class StockItemViewSet(LookupActionMixin, ShopFilterMixin, viewsets.ModelViewSet):
    """
    CRUD for stock items with filtering, search, and helper actions.

    List filters:  ?department=&supplier=&is_active=&search=
    Custom actions:
      GET  /stock-items/{pk}/pricing/          — all prices + deals + future pricing
      GET  /stock-items/{pk}/transactions/     — movement history
      GET  /stock-items/{pk}/monthly-stats/    — monthly sales breakdown
      GET  /stock-items/low-stock/             — items at or below reorder qty
      GET  /stock-items/needs-reorder/         — alias for low-stock
      POST /stock-items/{pk}/adjust-stock/     — manual qty adjustment
      GET  /stock-items/lookup/?search=&limit= — thin typeahead for line-item pickers
    """

    queryset = StockItem.objects.select_related(
        "department", "supplier", "tax_code", "last_supplier"
    ).prefetch_related("special_deals", "future_prices")
    permission_classes = [IsAuthenticated]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["department", "supplier", "is_active", "tax_code", "kvi_flag"]
    search_fields = [
        "stock_code",
        "description",
        "supplier_code",
        "bin_number",
        "barcode",
    ]
    ordering_fields = [
        "stock_code",
        "description",
        "quantity_on_hand",
        "cost_price",
        "selling_price_1",
    ]
    ordering = ["stock_code"]
    lookup_serializer_class = StockItemListSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return StockItemListSerializer
        return StockItemSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user.username)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user.username)

    def perform_destroy(self, instance):
        """
        Manual (§3.1 [311.htm]): "Accpick only allows a stock item to be
        deleted when there is no stock on hand, nor any stock movement for
        the current period." Previously unenforced — deletion was only
        incidentally blocked by PROTECT on FKs referencing StockItem
        (unrelated to QOH or "current period").
        """
        from rest_framework.exceptions import ValidationError

        if instance.quantity_on_hand != 0:
            raise ValidationError(
                f"Cannot delete stock item {instance.stock_code}: quantity on hand is "
                f"{instance.quantity_on_hand}, not zero."
            )

        today = timezone.now().date()
        has_movement_this_period = StockTransaction.objects.filter(
            stock_item=instance,
            transaction_date__year=today.year,
            transaction_date__month=today.month,
        ).exists()
        if has_movement_this_period:
            raise ValidationError(
                f"Cannot delete stock item {instance.stock_code}: it has stock movement "
                f"in the current period."
            )

        super().perform_destroy(instance)

    @action(detail=True, methods=["get"])
    def pricing(self, request, pk=None):
        """
        Return all pricing information for a stock item. Pass ?debtor=<id>
        to also resolve an active ContractPricing entry for that debtor
        (priority: item-specific -> department -> supplier).
        """
        item = self.get_object()
        data = {
            "stock_code": item.stock_code,
            "cost_price": item.cost_price,
            "average_cost": item.average_cost,
            "selling_price_1": item.selling_price_1,
            "selling_price_2": item.selling_price_2,
            "selling_price_3": item.selling_price_3,
            "markup_1": item.markup_1,
            "markup_2": item.markup_2,
            "markup_3": item.markup_3,
            "gross_profit_pct_1": item.calculate_gross_profit(1),
            "gross_profit_pct_2": item.calculate_gross_profit(2),
            "gross_profit_pct_3": item.calculate_gross_profit(3),
            "active_special_deal": None,
            "contract_price": None,
            "future_prices": FuturePricingSerializer(
                item.future_prices.filter(is_applied=False).order_by("effective_date"),
                many=True,
            ).data,
        }
        today = timezone.now().date()
        deal = item.special_deals.filter(
            start_date__lte=today, end_date__gte=today, is_active=True
        ).first()
        if deal:
            data["active_special_deal"] = SpecialDealSerializer(deal).data

        debtor_id = request.query_params.get("debtor")
        if debtor_id:
            contract = self._find_contract_pricing(item, debtor_id, today)
            if contract:
                data["contract_price"] = contract.get_price(stock_item=item)
        return Response(data)

    @staticmethod
    def _find_contract_pricing(item, debtor_id, today):
        """Priority: item-specific -> department -> supplier."""
        base_qs = (
            ContractPricing.objects.filter(debtor_id=debtor_id, is_active=True)
            .filter(Q(valid_from__isnull=True) | Q(valid_from__lte=today))
            .filter(Q(valid_until__isnull=True) | Q(valid_until__gte=today))
        )
        for field, value in (
            ("stock_item", item.pk),
            ("department", item.department_id),
            ("supplier", item.supplier_id),
        ):
            if value is None:
                continue
            contract = base_qs.filter(**{field: value}).first()
            if contract:
                return contract
        return None

    @action(detail=True, methods=["get"])
    def transactions(self, request, pk=None):
        """
        Return transaction history for a stock item, newest first.
        ?debtor=<id> filters to that debtor's transactions only (Stock
        Item History's Debtor split).
        """
        item = self.get_object()
        qs = item.transactions.select_related(
            "department", "debtor", "supplier"
        ).order_by("-transaction_date", "-id")

        # Optional date range filtering
        date_from = request.query_params.get("date_from")
        date_to = request.query_params.get("date_to")
        tx_type = request.query_params.get("type")
        debtor_id = request.query_params.get("debtor")
        if date_from:
            qs = qs.filter(transaction_date__gte=date_from)
        if date_to:
            qs = qs.filter(transaction_date__lte=date_to)
        if tx_type:
            qs = qs.filter(transaction_type=tx_type)
        if debtor_id:
            qs = qs.filter(debtor_id=debtor_id)

        page = self.paginate_queryset(qs)
        if page is not None:
            return self.get_paginated_response(
                StockTransactionSerializer(page, many=True).data
            )
        return Response(StockTransactionSerializer(qs, many=True).data)

    @action(detail=True, methods=["get"])
    def monthly_stats(self, request, pk=None):
        item = self.get_object()
        qs = item.monthly_stats.order_by("-year", "-month")
        return Response(StockMonthlyStatisticSerializer(qs, many=True).data)

    @action(detail=True, methods=["get"], url_path="debtor-breakdown")
    def debtor_breakdown(self, request, pk=None):
        """Sales of this item grouped by debtor (Stock Item History's Debtor split)."""
        item = self.get_object()
        rows = (
            item.transactions.filter(
                transaction_type__in=["SALE", "SALE_RETURN"], debtor__isnull=False
            )
            .values("debtor_id", "debtor__dname")
            .annotate(
                total_quantity=Sum("quantity_out") - Sum("quantity_in"),
                total_value=Sum(
                    Case(
                        When(transaction_type="SALE_RETURN", then=-F("value")),
                        default=F("value"),
                        output_field=DecimalField(max_digits=14, decimal_places=4),
                    )
                ),
            )
            .order_by("-total_value")
        )
        return Response(list(rows))

    @action(detail=True, methods=["get"], url_path="used-in-bundles")
    def used_in_bundles(self, request, pk=None):
        """Reverse lookup: which packs/bundles use this item as an ingredient, and how much."""
        item = self.get_object()
        rows = item.used_in_bundles.select_related("pack_bundle__stock_item")
        data = [
            {
                "pack_bundle_stock_code": row.pack_bundle.stock_item.stock_code,
                "pack_bundle_description": row.pack_bundle.stock_item.description,
                "quantity_required": row.quantity,
                "cost_at_creation": row.cost_at_creation,
            }
            for row in rows
        ]
        return Response(data)

    @action(detail=False, methods=["get"])
    def low_stock(self, request):
        """Items where available quantity <= reorder quantity."""
        items = [
            item
            for item in StockItem.objects.filter(is_active=True)
            if item.needs_reordering()
        ]
        return Response(StockItemListSerializer(items, many=True).data)

    @action(detail=False, methods=["get"], url_path="needs-reorder")
    def needs_reorder(self, request):
        return self.low_stock(request)

    @action(
        detail=True,
        methods=["post"],
        url_path="adjust-stock",
        permission_classes=[IsAuthenticated, IsStockMover],
    )
    def adjust_stock(self, request, pk=None):
        """
        Manual stock adjustment.
        Body: { "quantity": <signed float>, "comments": "..." }
        Positive quantity = stock in; negative = stock out.
        """
        item = self.get_object()
        qty = request.data.get("quantity")
        if qty is None:
            return Response(
                {"error": "quantity is required."}, status=status.HTTP_400_BAD_REQUEST
            )
        try:
            qty = float(qty)
        except (TypeError, ValueError):
            return Response(
                {"error": "quantity must be a number."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if qty == 0:
            return Response(
                {"error": "quantity must be non-zero."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        tx_data = {
            "transaction_type": "ADJUSTMENT",
            "stock_item": item.stock_code,
            "transaction_date": timezone.now().date(),
            "quantity_in": max(qty, 0),
            "quantity_out": max(-qty, 0),
            "quantity_balance": float(item.quantity_on_hand) + qty,
            "unit_cost": float(item.average_cost),
            "comments": request.data.get("comments", "Manual adjustment"),
        }
        serializer = StockTransactionSerializer(data=tx_data)
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by=request.user.username)

        # Plain arithmetic, not F("quantity_on_hand") + qty: StockItem's
        # pre_save signal (validate_qty_allocation) reads
        # instance.quantity_on_hand directly, and an unresolved F()
        # expression there isn't a concrete Decimal yet, which crashes
        # every call to this action with a TypeError.
        item.quantity_on_hand = item.quantity_on_hand + Decimal(str(qty))
        item.save(update_fields=["quantity_on_hand"])

        return Response(
            {
                "message": f"Stock adjusted by {qty}.",
                "new_quantity_on_hand": item.quantity_on_hand,
                "transaction": serializer.data,
            }
        )


# ─────────────────────────────────────────────
# SpecialDeal
# ─────────────────────────────────────────────


class SpecialDealViewSet(ShopFilterMixin, viewsets.ModelViewSet):
    queryset = SpecialDeal.objects.select_related("stock_item")
    serializer_class = SpecialDealSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["stock_item", "is_active"]
    ordering_fields = ["start_date", "end_date"]

    @action(detail=False, methods=["get"], url_path="active-today")
    def active_today(self, request):
        """Return all special deals valid today."""
        today = timezone.now().date()
        qs = SpecialDeal.objects.filter(
            start_date__lte=today, end_date__gte=today, is_active=True
        ).select_related("stock_item")
        return Response(SpecialDealSerializer(qs, many=True).data)

    # DecimalField(max_digits=5, decimal_places=2) on special_markup_1/2/3
    MARKUP_FIELD_LIMIT = Decimal("999.99")

    @action(
        detail=False,
        methods=["post"],
        url_path="bulk-department",
        permission_classes=[IsAuthenticated, IsStockMover],
    )
    def bulk_department(self, request):
        """
        Create a SpecialDeal for every active stock item in a department,
        each priced by adjusting THAT item's own current selling prices —
        mirrors the manual per-item flow, applied department-wide in one
        call rather than one row at a time.

        Body: { department, start_date, end_date,
                increase_decrease: '+'|'-', percentage_rand: 'P'|'R',
                amount }
        'P' applies amount as a percentage of each item's own price;
        'R' applies amount as a flat Rand value across all items.
        """
        department_id = request.data.get("department")
        start_date = request.data.get("start_date")
        end_date = request.data.get("end_date")
        increase_decrease = request.data.get("increase_decrease")
        percentage_rand = request.data.get("percentage_rand")

        errors = {}
        if not department_id:
            errors["department"] = "This field is required."
        if not start_date:
            errors["start_date"] = "This field is required."
        if not end_date:
            errors["end_date"] = "This field is required."
        if increase_decrease not in ("+", "-"):
            errors["increase_decrease"] = "Must be '+' or '-'."
        if percentage_rand not in ("P", "R"):
            errors["percentage_rand"] = "Must be 'P' or 'R'."
        try:
            amount = Decimal(str(request.data.get("amount")))
        except (TypeError, ValueError, InvalidOperation):
            errors["amount"] = "Must be a number."
        if errors:
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)

        items = StockItem.objects.filter(department_id=department_id, is_active=True)
        if not items.exists():
            return Response(
                {"error": "No active stock items found in that department."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        sign = Decimal("1") if increase_decrease == "+" else Decimal("-1")
        deals = []
        for item in items:
            prices = {}
            for level in (1, 2, 3):
                base = getattr(item, f"selling_price_{level}")
                delta = (
                    (base * amount / Decimal("100"))
                    if percentage_rand == "P"
                    else amount
                )
                prices[level] = max(Decimal("0"), base + sign * delta)

            markups = {}
            for level in (1, 2, 3):
                if item.cost_price > 0:
                    raw = ((prices[level] - item.cost_price) / item.cost_price) * 100
                    markups[level] = max(
                        -self.MARKUP_FIELD_LIMIT, min(self.MARKUP_FIELD_LIMIT, raw)
                    )
                else:
                    markups[level] = Decimal("0")

            deals.append(
                SpecialDeal(
                    stock_item=item,
                    special_cost_price=item.cost_price,
                    special_selling_price_1=prices[1],
                    special_selling_price_2=prices[2],
                    special_selling_price_3=prices[3],
                    special_markup_1=markups[1],
                    special_markup_2=markups[2],
                    special_markup_3=markups[3],
                    start_date=start_date,
                    end_date=end_date,
                    is_active=True,
                )
            )

        with transaction.atomic():
            SpecialDeal.objects.bulk_create(deals)

        return Response(
            {
                "message": f"Created {len(deals)} special deal(s) for department {department_id}.",
                "count": len(deals),
            },
            status=status.HTTP_201_CREATED,
        )


# ─────────────────────────────────────────────
# FuturePricing
# ─────────────────────────────────────────────


class FuturePricingViewSet(ShopFilterMixin, viewsets.ModelViewSet):
    queryset = FuturePricing.objects.select_related("stock_item")
    serializer_class = FuturePricingSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["stock_item", "is_applied"]
    ordering_fields = ["effective_date"]

    @action(detail=True, methods=["post"], url_path="apply")
    def apply(self, request, pk=None):
        """Apply future pricing to the stock item immediately."""
        fp = self.get_object()
        if fp.is_applied:
            return Response(
                {"error": "Already applied."}, status=status.HTTP_400_BAD_REQUEST
            )
        fp.apply()
        return Response(
            {
                "message": "Future pricing applied.",
                "stock_code": fp.stock_item.stock_code,
            }
        )


# ─────────────────────────────────────────────
# ShrinkWrap
# ─────────────────────────────────────────────


class ShrinkWrapViewSet(ShopFilterMixin, viewsets.ModelViewSet):
    queryset = ShrinkWrap.objects.select_related("shrink_pack_code", "bulk_pack_code")
    serializer_class = ShrinkWrapSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["shrink_pack_code", "bulk_pack_code"]


# ─────────────────────────────────────────────
# PackBundle
# ─────────────────────────────────────────────


class PackBundleViewSet(ShopFilterMixin, viewsets.ModelViewSet):
    queryset = PackBundle.objects.prefetch_related("ingredients__ingredient_stock")
    serializer_class = PackBundleSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=["post"], url_path="recalculate-cost")
    def recalculate_cost(self, request, pk=None):
        bundle = self.get_object()
        total = bundle.calculate_total_cost()
        return Response({"total_cost": total})


class PackBundleIngredientViewSet(ShopFilterMixin, viewsets.ModelViewSet):
    queryset = PackBundleIngredient.objects.select_related("ingredient_stock")
    serializer_class = PackBundleIngredientSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["pack_bundle", "ingredient_stock"]


# ─────────────────────────────────────────────
# StockTransaction
# ─────────────────────────────────────────────


class StockTransactionViewSet(ShopFilterMixin, viewsets.ModelViewSet):
    """
    CRUD for stock transactions.

    INCOMING/RETURN/MANUFACTURE creates are delegated to
    StockTransactionService, which moves quantity_on_hand atomically as
    part of the same request — posting one of these types through the
    plain serializer (as every other transaction type still does) would
    create the record without ever touching stock. Writes require
    IsStockMover, matching every other stock-moving action in this app.
    """

    queryset = StockTransaction.objects.select_related(
        "stock_item", "department", "tax_code", "debtor", "supplier"
    )
    serializer_class = StockTransactionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = [
        "stock_item",
        "transaction_type",
        "transaction_date",
        "department",
        "debtor",
        "supplier",
    ]
    ordering_fields = ["transaction_date", "id"]
    ordering = ["-transaction_date", "-id"]

    STOCK_MOVING_TYPES = ("INCOMING", "RETURN", "MANUFACTURE")

    def get_permissions(self):
        if self.action == "create":
            return [IsAuthenticated(), IsStockMover()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        data = serializer.validated_data
        tx_type = data.get("transaction_type")
        username = self.request.user.username

        if tx_type not in self.STOCK_MOVING_TYPES:
            serializer.save(created_by=username)
            return

        try:
            if tx_type == "INCOMING":
                tx = StockTransactionService.create_incoming_transaction(
                    stock_item=data["stock_item"],
                    quantity=data.get("quantity_in") or 0,
                    unit_cost=data.get("unit_cost") or 0,
                    supplier=data.get("supplier"),
                    comments=data.get("comments", "") or "",
                    transaction_date=data.get("transaction_date"),
                    created_by=username,
                )
            elif tx_type == "RETURN":
                tx = StockTransactionService.create_return_transaction(
                    stock_item=data["stock_item"],
                    quantity=data.get("quantity_out") or 0,
                    unit_cost=data.get("unit_cost") or 0,
                    supplier=data.get("supplier"),
                    comments=data.get("comments", "") or "",
                    transaction_date=data.get("transaction_date"),
                    created_by=username,
                )
            else:  # MANUFACTURE
                tx = StockTransactionService.create_manufacture_transaction(
                    bundle_stock_item=data["stock_item"],
                    quantity=data.get("quantity_in") or 0,
                    unit_cost=data.get("unit_cost") or None,
                    comments=data.get("comments", "") or "",
                    transaction_date=data.get("transaction_date"),
                    created_by=username,
                )
        except ValueError as e:
            raise DRFValidationError(str(e))
        serializer.instance = tx

    def get_queryset(self):
        qs = super().get_queryset()
        date_from = self.request.query_params.get("date_from")
        date_to = self.request.query_params.get("date_to")
        if date_from:
            qs = qs.filter(transaction_date__gte=date_from)
        if date_to:
            qs = qs.filter(transaction_date__lte=date_to)
        return qs

    # ── Enquiry aggregations ────────────────────────────────────────────
    # All reuse filter_queryset(get_queryset()) so date_from/date_to (from
    # get_queryset above) and department/debtor/supplier/stock_item (from
    # filterset_fields) are already available on every one of these for
    # free, on top of the type filter each applies itself.

    @action(detail=False, methods=["get"], url_path="stock-contribution")
    def stock_contribution(self, request):
        """Each item's share of total SALE value. ?department=&date_from=&date_to="""
        qs = self.filter_queryset(self.get_queryset()).filter(transaction_type="SALE")
        rows = list(
            qs.values("stock_item_id", "stock_item__description")
            .annotate(total_quantity=Sum("quantity_out"), total_value=Sum("value"))
            .order_by("-total_value")
        )
        grand_total = sum((r["total_value"] or Decimal("0")) for r in rows) or Decimal("1")
        for r in rows:
            r["contribution_pct"] = round(
                float((r["total_value"] or Decimal("0")) / grand_total) * 100, 2
            )
        return Response(rows)

    @action(detail=False, methods=["get"], url_path="sales-by-department")
    def sales_by_department(self, request):
        """SALE transactions grouped by department. ?date_from=&date_to="""
        qs = self.filter_queryset(self.get_queryset()).filter(transaction_type="SALE")
        rows = (
            qs.values("department_id", "department__name")
            .annotate(total_quantity=Sum("quantity_out"), total_value=Sum("value"))
            .order_by("-total_value")
        )
        return Response(list(rows))

    @action(detail=False, methods=["get"], url_path="hourly-analysis")
    def hourly_analysis(self, request):
        """SALE transactions bucketed by hour of day. ?date_from=&date_to=&department="""
        qs = self.filter_queryset(self.get_queryset()).filter(
            transaction_type="SALE", transaction_time__isnull=False
        )
        rows = (
            qs.annotate(hour=ExtractHour("transaction_time"))
            .values("hour")
            .annotate(
                total_quantity=Sum("quantity_out"),
                total_value=Sum("value"),
                transaction_count=Count("id"),
            )
            .order_by("hour")
        )
        return Response(list(rows))

    @action(detail=False, methods=["get"], url_path="purchase-history")
    def purchase_history(self, request):
        """INCOMING transactions. ?supplier=&stock_item=&date_from=&date_to="""
        qs = (
            self.filter_queryset(self.get_queryset())
            .filter(transaction_type="INCOMING")
            .order_by("-transaction_date", "-id")
        )
        page = self.paginate_queryset(qs)
        if page is not None:
            return self.get_paginated_response(
                StockTransactionSerializer(page, many=True).data
            )
        return Response(StockTransactionSerializer(qs, many=True).data)

    @action(detail=False, methods=["get"], url_path="top-sellers")
    def top_sellers(self, request):
        """Best-selling items by quantity. ?department=&date_from=&date_to=&limit="""
        qs = self.filter_queryset(self.get_queryset()).filter(transaction_type="SALE")
        try:
            limit = int(request.query_params.get("limit", 20))
        except (TypeError, ValueError):
            limit = 20
        rows = (
            qs.values("stock_item_id", "stock_item__description")
            .annotate(total_quantity=Sum("quantity_out"), total_value=Sum("value"))
            .order_by("-total_quantity")[:limit]
        )
        return Response(list(rows))


# ─────────────────────────────────────────────
# StockMovementLedger
# ─────────────────────────────────────────────


class StockMovementLedgerViewSet(ShopFilterMixin, viewsets.ReadOnlyModelViewSet):
    """Read-only ledger — entries are created by the system during transactions."""

    queryset = StockMovementLedger.objects.select_related("stock_item")
    serializer_class = StockMovementLedgerSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["stock_item", "movement_type", "movement_date"]
    ordering_fields = ["movement_date", "movement_time"]
    ordering = ["movement_date", "movement_time"]


# ─────────────────────────────────────────────
# StockTake
# ─────────────────────────────────────────────


class StockTakeViewSet(ShopFilterMixin, viewsets.ModelViewSet):
    """
    Manage stock take sessions.

    Custom actions:
      POST /stock-takes/{pk}/complete/          — mark as COMPLETED
      POST /stock-takes/{pk}/update-stock/      — apply counted quantities to QOH
      GET  /stock-takes/{pk}/variance-report/   — items with non-zero variance
    """

    queryset = StockTake.objects.prefetch_related("items__stock_item")
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["status"]
    ordering_fields = ["stock_take_date"]
    ordering = ["-stock_take_date"]

    def get_serializer_class(self):
        if self.action == "list":
            return StockTakeListSerializer
        return StockTakeSerializer

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        take = self.get_object()
        if take.status != "IN_PROGRESS":
            return Response(
                {"error": f"Cannot complete a stock take with status '{take.status}'."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        take.status = "COMPLETED"
        take.completed_at = timezone.now()
        take.save(update_fields=["status", "completed_at"])
        return Response(
            {"message": "Stock take completed.", "completed_at": take.completed_at}
        )

    @action(
        detail=True,
        methods=["post"],
        url_path="update-stock",
        permission_classes=[IsAuthenticated, IsStockMover],
    )
    def update_stock(self, request, pk=None):
        """
        Apply counted quantities as adjustments to stock QOH.

        Body: { "mode": "overwrite" | "additive" }, default "overwrite".
        - overwrite: quantity_counted IS the new QOH (unless the take is
          After-Trading, see below).
        - additive: quantity_counted is a DELTA added to current QOH,
          for stock takes captured as "+" counts rather than absolute
          readings. Mutually exclusive with an After-Trading take (v1 -
          combining them is ambiguous and wasn't asked for).

        When take.is_after_trading (real sales/receipts happened between
        the physical count and this call), the count alone isn't the
        correct target: target = counted + net stock movement recorded
        since trading_start_date (excluding other STOCK_TAKE rows), so
        those movements aren't clobbered by the count.
        """
        take = self.get_object()
        if take.status not in ("COMPLETED", "IN_PROGRESS"):
            return Response(
                {
                    "error": "Stock take must be COMPLETED or IN_PROGRESS to update stock."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        mode = request.data.get("mode", "overwrite")
        if mode not in ("overwrite", "additive"):
            return Response(
                {"error": "mode must be 'overwrite' or 'additive'."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if mode == "additive" and take.is_after_trading:
            return Response(
                {
                    "error": "additive mode cannot be combined with an After-Trading stock take."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        if take.is_after_trading and not take.trading_start_date:
            return Response(
                {"error": "trading_start_date is required when is_after_trading is set."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        items = take.items.select_related("stock_item")
        updated = 0
        alias = take._state.db or "default"
        with transaction.atomic(using=alias):
            for item in items:
                if not item.is_counted and not take.set_uncounted_to_zero:
                    continue
                counted = item.quantity_counted
                if take.reset_negatives_to_zero and counted < 0:
                    counted = 0

                stock_item = StockItem.objects.select_for_update().get(
                    pk=item.stock_item_id
                )

                if mode == "additive":
                    target = stock_item.quantity_on_hand + counted
                elif take.is_after_trading:
                    movements = (
                        StockTransaction.objects.filter(
                            stock_item=stock_item,
                            created_at__gte=take.trading_start_date,
                        )
                        .exclude(transaction_type="STOCK_TAKE")
                        .aggregate(total_in=Sum("quantity_in"), total_out=Sum("quantity_out"))
                    )
                    net_movement = (movements["total_in"] or Decimal("0")) - (
                        movements["total_out"] or Decimal("0")
                    )
                    target = counted + net_movement
                else:
                    target = counted

                adjustment = target - stock_item.quantity_on_hand

                stock_item.quantity_on_hand = target
                stock_item.save(update_fields=["quantity_on_hand"])
                item.calculate_variance()

                if adjustment != 0:
                    StockTransaction.objects.create(
                        transaction_type="STOCK_TAKE",
                        stock_item=stock_item,
                        transaction_date=take.stock_take_date,
                        quantity_in=adjustment if adjustment > 0 else Decimal("0"),
                        quantity_out=-adjustment if adjustment < 0 else Decimal("0"),
                        unit_cost=item.cost_price_at_count,
                        comments=f"Stock take #{take.id}"[:30],
                    )

                updated += 1
            take.status = "UPDATED"
            take.save(update_fields=["status"])
        return Response({"message": f"Stock updated for {updated} items."})

    @action(detail=True, methods=["get"], url_path="variance-report")
    def variance_report(self, request, pk=None):
        take = self.get_object()
        items = take.items.exclude(variance_quantity=0).select_related("stock_item")
        return Response(StockTakeItemSerializer(items, many=True).data)


class StockTakeItemViewSet(ShopFilterMixin, viewsets.ModelViewSet):
    queryset = StockTakeItem.objects.select_related("stock_take", "stock_item")
    serializer_class = StockTakeItemSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["stock_take", "stock_item", "is_counted"]

    @action(detail=True, methods=["post"])
    def count(self, request, pk=None):
        """Record a counted quantity for this item."""
        item = self.get_object()
        qty = request.data.get("quantity_counted")
        if qty is None:
            return Response(
                {"error": "quantity_counted is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            item.quantity_counted = float(qty)
        except (TypeError, ValueError):
            return Response(
                {"error": "quantity_counted must be a number."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        item.is_counted = True
        item.count_date = timezone.now()
        item.calculate_variance()
        return Response(StockTakeItemSerializer(item).data)


# ─────────────────────────────────────────────
# ContractPricing
# ─────────────────────────────────────────────


class ContractPricingViewSet(ShopFilterMixin, viewsets.ModelViewSet):
    queryset = ContractPricing.objects.select_related(
        "debtor", "stock_item", "department", "supplier"
    )
    serializer_class = ContractPricingSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = [
        "debtor",
        "stock_item",
        "department",
        "supplier",
        "pricing_method",
        "is_active",
    ]

    @action(detail=False, methods=["get"], url_path="active-for")
    def active_for(self, request):
        """
        Resolve the active contract price for ?debtor=&stock_item=
        (priority: item-specific -> department -> supplier), honoring
        valid_from/valid_until.
        """
        debtor_id = request.query_params.get("debtor")
        stock_code = request.query_params.get("stock_item")
        if not debtor_id or not stock_code:
            return Response(
                {"error": "debtor and stock_item are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            item = StockItem.objects.get(pk=stock_code)
        except StockItem.DoesNotExist:
            return Response(
                {"error": f"Unknown stock item '{stock_code}'."},
                status=status.HTTP_404_NOT_FOUND,
            )
        contract = StockItemViewSet._find_contract_pricing(
            item, debtor_id, timezone.now().date()
        )
        if not contract:
            return Response({"contract_price": None})
        return Response(
            {
                "contract_price": contract.get_price(stock_item=item),
                "contract": ContractPricingSerializer(contract).data,
            }
        )


# ─────────────────────────────────────────────
# OneTouchLookupKey
# ─────────────────────────────────────────────


class OneTouchLookupKeyViewSet(ShopFilterMixin, viewsets.ModelViewSet):
    queryset = OneTouchLookupKey.objects.select_related("stock_item")
    serializer_class = OneTouchLookupKeySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["stock_item"]


# ─────────────────────────────────────────────
# StockMonthlyStatistic
# ─────────────────────────────────────────────


class StockMonthlyStatisticViewSet(ShopFilterMixin, viewsets.ModelViewSet):
    queryset = StockMonthlyStatistic.objects.select_related("stock_item")
    serializer_class = StockMonthlyStatisticSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["stock_item", "year", "month"]
    ordering_fields = ["year", "month"]
    ordering = ["-year", "-month"]


# ─────────────────────────────────────────────
# Branch
# ─────────────────────────────────────────────


class BranchViewSet(ShopFilterMixin, viewsets.ModelViewSet):
    """
    Manage branches/locations.

    Custom actions:
      GET /branches/{pk}/stock/     — all stock levels at this branch
    """

    queryset = Branch.objects.all()
    serializer_class = BranchSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["branch_type", "is_active", "is_default"]
    search_fields = ["branch_code", "branch_name"]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user.username)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user.username)

    @action(detail=True, methods=["get"])
    def stock(self, request, pk=None):
        branch = self.get_object()
        qs = branch.branch_stocks.select_related("stock_item")
        search = request.query_params.get("search")
        if search:
            qs = qs.filter(
                Q(stock_item__stock_code__icontains=search)
                | Q(stock_item__description__icontains=search)
            )
        page = self.paginate_queryset(qs)
        if page is not None:
            return self.get_paginated_response(
                BranchStockSerializer(page, many=True).data
            )
        return Response(BranchStockSerializer(qs, many=True).data)


# ─────────────────────────────────────────────
# BranchStock
# ─────────────────────────────────────────────


class BranchStockViewSet(ShopFilterMixin, viewsets.ModelViewSet):
    queryset = BranchStock.objects.select_related("branch", "stock_item")
    serializer_class = BranchStockSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["branch", "stock_item"]

    @action(detail=False, methods=["get"], url_path="low-stock")
    def low_stock(self, request):
        """Branch stock lines where available quantity <= reorder level."""
        qs = (
            BranchStock.objects.select_related("branch", "stock_item")
            .annotate(avail=F("quantity") - F("quantity_allocated"))
            .filter(avail__lte=F("reorder_level"))
        )
        branch = request.query_params.get("branch")
        if branch:
            qs = qs.filter(branch=branch)
        return Response(BranchStockSerializer(qs, many=True).data)


# ─────────────────────────────────────────────
# GroupOrder
# ─────────────────────────────────────────────


class GroupOrderViewSet(ShopFilterMixin, viewsets.ModelViewSet):
    """
    Manage group orders.

    Custom actions:
      POST /group-orders/{pk}/recalculate-total/
    """

    queryset = GroupOrder.objects.select_related("branch").prefetch_related(
        "items__stock_item"
    )
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["branch", "status"]
    ordering_fields = ["order_date", "total_amount"]
    ordering = ["-order_date"]

    def get_serializer_class(self):
        if self.action == "list":
            return GroupOrderListSerializer
        return GroupOrderSerializer

    @action(detail=True, methods=["post"], url_path="recalculate-total")
    def recalculate_total(self, request, pk=None):
        order = self.get_object()
        total = order.calculate_total_amount()
        return Response(
            {"group_order_number": order.group_order_number, "total_amount": total}
        )


class GroupOrderItemViewSet(ShopFilterMixin, viewsets.ModelViewSet):
    queryset = GroupOrderItem.objects.select_related("group_order", "stock_item")
    serializer_class = GroupOrderItemSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["group_order", "stock_item"]


# ─────────────────────────────────────────────
# BranchTransfer
# ─────────────────────────────────────────────


class BranchTransferViewSet(ShopFilterMixin, viewsets.ModelViewSet):
    """
    Manage inter-branch transfers (IBT).

    Status transitions via dedicated actions:
      POST /branch-transfers/{pk}/approve/
      POST /branch-transfers/{pk}/dispatch/
      POST /branch-transfers/{pk}/receive/
      POST /branch-transfers/{pk}/cancel/
    """

    queryset = BranchTransfer.objects.select_related(
        "from_branch",
        "to_branch",
        "requested_by",
        "approved_by",
        "dispatched_by",
        "received_by",
    ).prefetch_related("items__stock_item")
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["from_branch", "to_branch", "status", "transfer_type"]
    ordering_fields = ["requested_date"]
    ordering = ["-requested_date"]

    def get_serializer_class(self):
        if self.action == "list":
            return BranchTransferListSerializer
        return BranchTransferSerializer

    def perform_create(self, serializer):
        # DRAFT (the model default) has no transition action to move it
        # forward — a transfer only becomes actionable once it's PENDING, so
        # start it there instead of leaving it stuck.
        serializer.save(requested_by=self.request.user, status="PENDING")

    def _transition(self, pk, allowed_from, new_status, timestamp_field, user_field):
        transfer = self.get_object()
        if transfer.status not in allowed_from:
            return Response(
                {
                    "error": f"Cannot transition from '{transfer.status}' to '{new_status}'."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        transfer.status = new_status
        setattr(transfer, timestamp_field, timezone.now())
        setattr(transfer, user_field, self.request.user)
        transfer.save(update_fields=["status", timestamp_field, user_field])
        return Response(BranchTransferSerializer(transfer).data)

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAuthenticated, IsStockMover],
    )
    def approve(self, request, pk=None):
        return self._transition(
            pk, ["PENDING"], "APPROVED", "approved_date", "approved_by"
        )

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAuthenticated, IsStockMover],
    )
    def dispatch(self, request, pk=None):
        """
        Dispatch the transfer: decrements BranchStock at from_branch for each
        item and records quantity_dispatched. Optionally accepts per-item
        dispatched quantities in body: { "items": [ { "id": <BranchTransferItemId>,
        "quantity_dispatched": <n> } ] } — defaults to quantity_requested for
        any item not specified.
        """
        transfer = self.get_object()
        if transfer.status not in ("APPROVED",):
            return Response(
                {
                    "error": f"Cannot transition from '{transfer.status}' to 'DISPATCHED'."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        item_overrides = {
            entry["id"]: entry["quantity_dispatched"]
            for entry in request.data.get("items", [])
            if "id" in entry and "quantity_dispatched" in entry
        }

        with transaction.atomic():
            for item in transfer.items.select_related("stock_item").select_for_update():
                qty = Decimal(str(item_overrides.get(item.id, item.quantity_requested)))

                branch_stock = (
                    BranchStock.objects.select_for_update()
                    .filter(branch=transfer.from_branch, stock_item=item.stock_item)
                    .first()
                )
                available = branch_stock.quantity if branch_stock else Decimal("0")
                if qty > available:
                    return Response(
                        {
                            "error": f"Insufficient stock for {item.stock_item.stock_code} at "
                            f"{transfer.from_branch.branch_code}: requested {qty}, available {available}."
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                item.quantity_dispatched = qty
                item.save(update_fields=["quantity_dispatched"])

                branch_stock.quantity = F("quantity") - qty
                branch_stock.save(update_fields=["quantity"])

            transfer.status = "DISPATCHED"
            transfer.dispatched_date = timezone.now()
            transfer.dispatched_by = request.user
            transfer.save(update_fields=["status", "dispatched_date", "dispatched_by"])

        transfer.refresh_from_db()
        return Response(BranchTransferSerializer(transfer).data)

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAuthenticated, IsStockMover],
    )
    def receive(self, request, pk=None):
        """
        Mark transfer as received: increments BranchStock at to_branch for each
        item. Optionally accepts per-item received quantities in body:
        { "items": [ { "id": <BranchTransferItemId>, "quantity_received": <n> } ] }
        — defaults to quantity_dispatched for any item not specified.
        """
        transfer = self.get_object()
        if transfer.status not in ("DISPATCHED", "IN_TRANSIT"):
            return Response(
                {
                    "error": f"Cannot receive a transfer with status '{transfer.status}'."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        item_overrides = {
            entry["id"]: entry["quantity_received"]
            for entry in request.data.get("items", [])
            if "id" in entry and "quantity_received" in entry
        }

        with transaction.atomic():
            for item in transfer.items.select_related("stock_item").select_for_update():
                qty = Decimal(
                    str(item_overrides.get(item.id, item.quantity_dispatched))
                )

                item.quantity_received = qty
                item.save()  # save() also recalculates `variance`

                branch_stock, _ = BranchStock.objects.select_for_update().get_or_create(
                    branch=transfer.to_branch, stock_item=item.stock_item
                )
                branch_stock.quantity = F("quantity") + qty
                branch_stock.save(update_fields=["quantity"])

            transfer.status = "RECEIVED"
            transfer.received_date = timezone.now()
            transfer.received_by = request.user
            transfer.save(update_fields=["status", "received_date", "received_by"])

        transfer.refresh_from_db()
        return Response(BranchTransferSerializer(transfer).data)

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAuthenticated, IsStockMover],
    )
    def cancel(self, request, pk=None):
        transfer = self.get_object()
        if transfer.status in ("COMPLETED", "CANCELLED"):
            return Response(
                {"error": f"Cannot cancel a transfer with status '{transfer.status}'."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        transfer.status = "CANCELLED"
        transfer.save(update_fields=["status"])
        return Response(
            {
                "message": "Transfer cancelled.",
                "transfer_number": transfer.transfer_number,
            }
        )


class BranchTransferItemViewSet(ShopFilterMixin, viewsets.ModelViewSet):
    queryset = BranchTransferItem.objects.select_related("transfer", "stock_item")
    serializer_class = BranchTransferItemSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["transfer", "stock_item"]


# ─────────────────────────────────────────────
# BranchTransferInvoice
# ─────────────────────────────────────────────


class BranchTransferInvoiceViewSet(ShopFilterMixin, viewsets.ModelViewSet):
    queryset = BranchTransferInvoice.objects.select_related("transfer")
    serializer_class = BranchTransferInvoiceSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["status", "invoice_date"]
    ordering_fields = ["invoice_date"]
    ordering = ["-invoice_date"]

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAuthenticated, IsStockAccountant],
    )
    def issue(self, request, pk=None):
        invoice = self.get_object()
        if invoice.status != "DRAFT":
            return Response(
                {"error": "Only DRAFT invoices can be issued."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        invoice.status = "ISSUED"
        invoice.save(update_fields=["status"])
        return Response(BranchTransferInvoiceSerializer(invoice).data)

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAuthenticated, IsStockAccountant],
    )
    def mark_paid(self, request, pk=None):
        invoice = self.get_object()
        if invoice.status != "ISSUED":
            return Response(
                {"error": "Only ISSUED invoices can be marked as paid."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        invoice.status = "PAID"
        invoice.save(update_fields=["status"])
        return Response(BranchTransferInvoiceSerializer(invoice).data)
