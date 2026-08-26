from decimal import Decimal

from apps.common.mixins import LookupActionMixin
from apps.shop_filter_mixin import ShopFilterMixin
from django.db import transaction
from django.db.models import F, Q, Sum
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
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
        """Return all pricing information for a stock item."""
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
        return Response(data)

    @action(detail=True, methods=["get"])
    def transactions(self, request, pk=None):
        """Return transaction history for a stock item, newest first."""
        item = self.get_object()
        qs = item.transactions.select_related(
            "department", "debtor", "supplier"
        ).order_by("-transaction_date", "-id")

        # Optional date range filtering
        date_from = request.query_params.get("date_from")
        date_to = request.query_params.get("date_to")
        tx_type = request.query_params.get("type")
        if date_from:
            qs = qs.filter(transaction_date__gte=date_from)
        if date_to:
            qs = qs.filter(transaction_date__lte=date_to)
        if tx_type:
            qs = qs.filter(transaction_type=tx_type)

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

    @action(detail=True, methods=["post"], url_path="adjust-stock")
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

        item.quantity_on_hand = F("quantity_on_hand") + qty
        item.save(update_fields=["quantity_on_hand"])
        item.refresh_from_db()

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

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user.username)

    def get_queryset(self):
        qs = super().get_queryset()
        date_from = self.request.query_params.get("date_from")
        date_to = self.request.query_params.get("date_to")
        if date_from:
            qs = qs.filter(transaction_date__gte=date_from)
        if date_to:
            qs = qs.filter(transaction_date__lte=date_to)
        return qs


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

    @action(detail=True, methods=["post"], url_path="update-stock")
    def update_stock(self, request, pk=None):
        """Apply counted quantities as adjustments to stock QOH."""
        take = self.get_object()
        if take.status not in ("COMPLETED", "IN_PROGRESS"):
            return Response(
                {
                    "error": "Stock take must be COMPLETED or IN_PROGRESS to update stock."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        items = take.items.select_related("stock_item")
        updated = 0
        for item in items:
            if not item.is_counted and not take.set_uncounted_to_zero:
                continue
            counted = item.quantity_counted
            if take.reset_negatives_to_zero and counted < 0:
                counted = 0

            stock_item = item.stock_item
            adjustment = Decimal(str(counted)) - stock_item.quantity_on_hand

            stock_item.quantity_on_hand = counted
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

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        return self._transition(
            pk, ["PENDING"], "APPROVED", "approved_date", "approved_by"
        )

    @action(detail=True, methods=["post"])
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

    @action(detail=True, methods=["post"])
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

    @action(detail=True, methods=["post"])
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

    @action(detail=True, methods=["post"])
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

    @action(detail=True, methods=["post"])
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
