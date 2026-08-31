from apps.settings.models import SalesDepartment
from rest_framework import serializers

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

# ─────────────────────────────────────────────
# Minimal / nested serializers (read-only)
# ─────────────────────────────────────────────


class StockItemMinimalSerializer(serializers.ModelSerializer):
    """Lightweight representation used when embedding inside other serializers."""

    class Meta:
        model = StockItem
        fields = [
            "stock_code",
            "description",
            "selling_price_1",
            "cost_price",
            "quantity_on_hand",
        ]


class BranchMinimalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = ["branch_code", "branch_name", "branch_type"]


class SalesDepartmentMinimalSerializer(serializers.ModelSerializer):
    """
    Lightweight nested department representation. Several frontend
    enquiries/reports group stock items by department name (e.g.
    item.department_detail?.name) but neither StockItem serializer ever
    exposed it — every grouping silently collapsed into "Unassigned".
    """

    class Meta:
        model = SalesDepartment
        fields = ["id", "number", "name"]


# ─────────────────────────────────────────────
# SpecialDeal
# ─────────────────────────────────────────────


class SpecialDealSerializer(serializers.ModelSerializer):
    is_valid_today = serializers.SerializerMethodField()

    class Meta:
        model = SpecialDeal
        fields = [
            "id",
            "stock_item",
            "special_cost_price",
            "special_selling_price_1",
            "special_selling_price_2",
            "special_selling_price_3",
            "special_markup_1",
            "special_markup_2",
            "special_markup_3",
            "start_date",
            "end_date",
            "is_active",
            "is_valid_today",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def get_is_valid_today(self, obj):
        return obj.is_valid_today()

    def validate(self, data):
        if data.get("end_date") and data.get("start_date"):
            if data["end_date"] < data["start_date"]:
                raise serializers.ValidationError(
                    "end_date must be on or after start_date."
                )
        return data


# ─────────────────────────────────────────────
# FuturePricing
# ─────────────────────────────────────────────


class FuturePricingSerializer(serializers.ModelSerializer):
    class Meta:
        model = FuturePricing
        fields = [
            "id",
            "stock_item",
            "future_cost_price",
            "future_selling_price_1",
            "future_selling_price_2",
            "future_selling_price_3",
            "future_markup_1",
            "future_markup_2",
            "future_markup_3",
            "effective_date",
            "is_applied",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


# ─────────────────────────────────────────────
# ShrinkWrap
# ─────────────────────────────────────────────


class ShrinkWrapSerializer(serializers.ModelSerializer):
    shrink_pack_code_detail = StockItemMinimalSerializer(
        source="shrink_pack_code", read_only=True
    )
    bulk_pack_code_detail = StockItemMinimalSerializer(
        source="bulk_pack_code", read_only=True
    )

    class Meta:
        model = ShrinkWrap
        fields = [
            "id",
            "shrink_pack_code",
            "shrink_pack_code_detail",
            "bulk_pack_code",
            "bulk_pack_code_detail",
            "invoice_bulk_value",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


# ─────────────────────────────────────────────
# PackBundle & Ingredients
# ─────────────────────────────────────────────


class PackBundleIngredientSerializer(serializers.ModelSerializer):
    ingredient_stock_detail = StockItemMinimalSerializer(
        source="ingredient_stock", read_only=True
    )
    ingredient_value = serializers.SerializerMethodField()

    class Meta:
        model = PackBundleIngredient
        fields = [
            "id",
            "pack_bundle",
            "ingredient_stock",
            "ingredient_stock_detail",
            "quantity",
            "cost_at_creation",
            "ingredient_value",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def get_ingredient_value(self, obj):
        return obj.get_ingredient_value()


class PackBundleSerializer(serializers.ModelSerializer):
    ingredients = PackBundleIngredientSerializer(many=True, read_only=True)

    class Meta:
        model = PackBundle
        fields = ["stock_item", "total_cost", "ingredients", "created_at", "updated_at"]
        read_only_fields = ["created_at", "updated_at"]


# ─────────────────────────────────────────────
# StockItem  (full + list)
# ─────────────────────────────────────────────


class StockItemSerializer(serializers.ModelSerializer):
    available_quantity = serializers.ReadOnlyField()
    special_deals = SpecialDealSerializer(many=True, read_only=True)
    future_prices = FuturePricingSerializer(many=True, read_only=True)
    department_detail = SalesDepartmentMinimalSerializer(source="department", read_only=True)

    class Meta:
        model = StockItem
        fields = [
            # Identity
            "stock_code",
            "description",
            "is_active",
            # Relations
            "department",
            "department_detail",
            "supplier",
            "supplier_code",
            "last_supplier",
            "tax_code",
            # Pricing
            "cost_price",
            "average_cost",
            "selling_price_1",
            "selling_price_2",
            "selling_price_3",
            "markup_1",
            "markup_2",
            "markup_3",
            # Quantities
            "quantity_on_hand",
            "quantity_allocated",
            "quantity_sale_order",
            "quantity_on_order",
            "quantity_counted",
            "available_quantity",
            "reorder_quantity",
            "default_selling_quantity",
            # Settings
            "allow_negative_quantities",
            "maximum_discount_percent",
            # Sales stats
            "sales_mtd_quantity",
            "sales_mtd_value",
            "sales_ytd_quantity",
            "sales_ytd_value",
            "gross_profit_mtd",
            "gross_profit_ytd",
            # Purchase stats
            "purchased_mtd_quantity",
            "purchased_ytd_quantity",
            # Balances
            "balance_bfwd_quantity",
            "balance_bfwd_value",
            "closing_stock_balance",
            "job_card_bfwd_value",
            "laybye_bfwd_value",
            "rfc_bfwd_value",
            # Physical
            "bin_number",
            "weight",
            "pack_code",
            "kvi_flag",
            "stock_count_flag",
            "barcode",
            # Dates
            "date_last_purchased",
            "date_last_sold",
            # Audit
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
            # Nested
            "special_deals",
            "future_prices",
        ]
        read_only_fields = ["created_at", "updated_at", "available_quantity"]


class StockItemListSerializer(serializers.ModelSerializer):
    available_quantity = serializers.ReadOnlyField()
    department_detail = SalesDepartmentMinimalSerializer(source="department", read_only=True)

    class Meta:
        model = StockItem
        fields = [
            "stock_code",
            "description",
            "department",
            "department_detail",
            "supplier",
            "cost_price",
            "selling_price_1",
            "quantity_on_hand",
            "quantity_counted",
            "available_quantity",
            "allow_negative_quantities",
            "reorder_quantity",
            "is_active",
            "tax_code",
            "barcode",
        ]


# ─────────────────────────────────────────────
# StockTransaction
# ─────────────────────────────────────────────


class StockTransactionSerializer(serializers.ModelSerializer):
    stock_item_detail = StockItemMinimalSerializer(source="stock_item", read_only=True)
    stock_item = serializers.SlugRelatedField(
        queryset=StockItem.objects.all(), slug_field="stock_code"
    )

    class Meta:
        model = StockTransaction
        fields = [
            "id",
            "transaction_type",
            "stock_item",
            "stock_item_detail",
            "transaction_date",
            "transaction_time",
            "transaction_number",
            "quantity_in",
            "quantity_out",
            "quantity_balance",
            "discount",
            "unit_cost",
            "unit_price",
            "value",
            "department",
            "tax_code",
            "debtor",
            "supplier",
            "station_number",
            "comments",
            "created_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def validate(self, data):
        qty_in = data.get("quantity_in", 0)
        qty_out = data.get("quantity_out", 0)
        if qty_in < 0 or qty_out < 0:
            raise serializers.ValidationError(
                "quantity_in and quantity_out must be non-negative."
            )
        if qty_in > 0 and qty_out > 0:
            raise serializers.ValidationError(
                "A transaction should have either quantity_in or quantity_out, not both."
            )
        return data


# ─────────────────────────────────────────────
# StockMovementLedger
# ─────────────────────────────────────────────


class StockMovementLedgerSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockMovementLedger
        fields = [
            "id",
            "stock_item",
            "movement_date",
            "movement_time",
            "movement_type",
            "transaction_number",
            "details",
            "supplier_details",
            "record_reference",
            "quantity_in",
            "quantity_out",
            "balance",
            "brought_forward",
            "per_unit_cost",
            "created_at",
        ]
        read_only_fields = ["created_at"]


# ─────────────────────────────────────────────
# StockTake
# ─────────────────────────────────────────────


class StockTakeItemSerializer(serializers.ModelSerializer):
    stock_item_detail = StockItemMinimalSerializer(source="stock_item", read_only=True)

    class Meta:
        model = StockTakeItem
        fields = [
            "id",
            "stock_take",
            "stock_item",
            "stock_item_detail",
            "quantity_on_hand",
            "quantity_counted",
            "variance_quantity",
            "variance_value",
            "cost_price_at_count",
            "is_counted",
            "count_date",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "variance_quantity",
            "variance_value",
            "created_at",
            "updated_at",
        ]


class StockTakeSerializer(serializers.ModelSerializer):
    items = StockTakeItemSerializer(many=True, read_only=True)
    item_count = serializers.SerializerMethodField()

    class Meta:
        model = StockTake
        fields = [
            "id",
            "stock_take_date",
            "status",
            "description",
            "reset_negatives_to_zero",
            "set_uncounted_to_zero",
            "is_after_trading",
            "trading_start_date",
            "created_by",
            "completed_at",
            "item_count",
            "items",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at", "completed_at"]

    def get_item_count(self, obj):
        return obj.items.count()


class StockTakeListSerializer(serializers.ModelSerializer):
    item_count = serializers.SerializerMethodField()

    class Meta:
        model = StockTake
        fields = [
            "id",
            "stock_take_date",
            "status",
            "description",
            "item_count",
            "created_by",
            "created_at",
        ]

    def get_item_count(self, obj):
        return obj.items.count()


# ─────────────────────────────────────────────
# ContractPricing
# ─────────────────────────────────────────────


class ContractPricingSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContractPricing
        fields = [
            "id",
            "debtor",
            "stock_item",
            "department",
            "supplier",
            "pricing_method",
            "contract_price",
            "markup_percent",
            "discount_percent",
            "last_selling_price",
            "last_updated_date",
            "valid_from",
            "valid_until",
            "is_fixed_pricing",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def validate(self, data):
        method = data.get(
            "pricing_method", getattr(self.instance, "pricing_method", None)
        )
        if (
            method == "ACTUAL"
            and not data.get("contract_price")
            and not getattr(self.instance, "contract_price", None)
        ):
            raise serializers.ValidationError(
                {"contract_price": "Required when pricing_method is ACTUAL."}
            )
        if (
            method == "COST_MARKUP"
            and data.get("markup_percent") is None
            and getattr(self.instance, "markup_percent", None) is None
        ):
            raise serializers.ValidationError(
                {"markup_percent": "Required when pricing_method is COST_MARKUP."}
            )
        return data


# ─────────────────────────────────────────────
# OneTouchLookupKey
# ─────────────────────────────────────────────


class OneTouchLookupKeySerializer(serializers.ModelSerializer):
    class Meta:
        model = OneTouchLookupKey
        fields = ["id", "key_character", "stock_item", "created_at", "updated_at"]
        read_only_fields = ["created_at", "updated_at"]

    def validate_key_character(self, value):
        if not value.isupper() or not value.isalpha():
            raise serializers.ValidationError(
                "key_character must be a single uppercase letter (A-Z)."
            )
        return value


# ─────────────────────────────────────────────
# StockMonthlyStatistic
# ─────────────────────────────────────────────


class StockMonthlyStatisticSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockMonthlyStatistic
        fields = [
            "id",
            "stock_item",
            "year",
            "month",
            "quantity_sold",
            "value_sold",
            "profit_value",
            "profit_percent",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


# ─────────────────────────────────────────────
# Branch
# ─────────────────────────────────────────────


class BranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = [
            "branch_code",
            "branch_name",
            "branch_type",
            "address",
            "contact_phone",
            "is_active",
            "is_default",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
        ]
        read_only_fields = ["created_at", "updated_at"]


# ─────────────────────────────────────────────
# BranchStock
# ─────────────────────────────────────────────


class BranchStockSerializer(serializers.ModelSerializer):
    available_quantity = serializers.ReadOnlyField()
    stock_item_detail = StockItemMinimalSerializer(source="stock_item", read_only=True)
    branch_detail = BranchMinimalSerializer(source="branch", read_only=True)

    class Meta:
        model = BranchStock
        fields = [
            "id",
            "branch",
            "branch_detail",
            "stock_item",
            "stock_item_detail",
            "quantity",
            "quantity_allocated",
            "available_quantity",
            "reorder_level",
            "reorder_quantity",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at", "available_quantity"]


# ─────────────────────────────────────────────
# GroupOrder
# ─────────────────────────────────────────────


class GroupOrderItemSerializer(serializers.ModelSerializer):
    stock_item_detail = StockItemMinimalSerializer(source="stock_item", read_only=True)

    class Meta:
        model = GroupOrderItem
        fields = [
            "id",
            "group_order",
            "stock_item",
            "stock_item_detail",
            "quantity",
            "unit_price",
            "line_total",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["line_total", "created_at", "updated_at"]


class GroupOrderSerializer(serializers.ModelSerializer):
    items = GroupOrderItemSerializer(many=True, read_only=True)
    branch_detail = BranchMinimalSerializer(source="branch", read_only=True)

    class Meta:
        model = GroupOrder
        fields = [
            "id",
            "group_order_number",
            "order_date",
            "status",
            "branch",
            "branch_detail",
            "notes",
            "total_amount",
            "created_by",
            "items",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["total_amount", "created_at", "updated_at"]


class GroupOrderListSerializer(serializers.ModelSerializer):
    branch_detail = BranchMinimalSerializer(source="branch", read_only=True)

    class Meta:
        model = GroupOrder
        fields = [
            "id",
            "group_order_number",
            "order_date",
            "status",
            "branch",
            "branch_detail",
            "total_amount",
        ]


# ─────────────────────────────────────────────
# BranchTransfer
# ─────────────────────────────────────────────


class BranchTransferItemSerializer(serializers.ModelSerializer):
    stock_item_detail = StockItemMinimalSerializer(source="stock_item", read_only=True)

    class Meta:
        model = BranchTransferItem
        fields = [
            "id",
            "transfer",
            "stock_item",
            "stock_item_detail",
            "quantity_requested",
            "quantity_dispatched",
            "quantity_received",
            "variance",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["variance", "created_at", "updated_at"]


class BranchTransferSerializer(serializers.ModelSerializer):
    items = BranchTransferItemSerializer(many=True, read_only=True)
    from_branch_detail = BranchMinimalSerializer(source="from_branch", read_only=True)
    to_branch_detail = BranchMinimalSerializer(source="to_branch", read_only=True)

    class Meta:
        model = BranchTransfer
        fields = [
            "id",
            "transfer_number",
            "from_branch",
            "from_branch_detail",
            "to_branch",
            "to_branch_detail",
            "status",
            "transfer_type",
            "requested_by",
            "approved_by",
            "dispatched_by",
            "received_by",
            "requested_date",
            "approved_date",
            "dispatched_date",
            "received_date",
            "notes",
            "items",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "approved_date",
            "dispatched_date",
            "received_date",
            "created_at",
            "updated_at",
        ]

    def validate(self, data):
        from_b = data.get("from_branch", getattr(self.instance, "from_branch", None))
        to_b = data.get("to_branch", getattr(self.instance, "to_branch", None))
        if from_b and to_b and from_b == to_b:
            raise serializers.ValidationError(
                "from_branch and to_branch must be different."
            )
        return data


class BranchTransferListSerializer(serializers.ModelSerializer):
    from_branch_detail = BranchMinimalSerializer(source="from_branch", read_only=True)
    to_branch_detail = BranchMinimalSerializer(source="to_branch", read_only=True)

    class Meta:
        model = BranchTransfer
        fields = [
            "id",
            "transfer_number",
            "from_branch",
            "from_branch_detail",
            "to_branch",
            "to_branch_detail",
            "status",
            "transfer_type",
            "requested_date",
        ]


# ─────────────────────────────────────────────
# BranchTransferInvoice
# ─────────────────────────────────────────────


class BranchTransferInvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = BranchTransferInvoice
        fields = [
            "id",
            "transfer",
            "invoice_number",
            "invoice_date",
            "status",
            "subtotal",
            "vat_amount",
            "total_amount",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]
