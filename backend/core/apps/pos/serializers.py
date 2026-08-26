"""
Point of Sale serializers.
Complete serializers for all POS-related models based on PointOfSale.pdf
"""

import logging
from datetime import date
from decimal import Decimal

from apps.debtors.models import Debtor
from apps.settings.models import SalesArea
from django.db import transaction as db_transaction
from rest_framework import serializers

from .models import (
    CashACheque,
    CashControl,
    CashReturn,
    CashReturnLine,
    CashSale,
    CashSaleLine,
    CreditNote,
    CreditNoteLine,
    Invoice,
    InvoiceLine,
    JobCard,
    JobCardLine,
    Laybye,
    LaybyeLine,
    LaybyePayment,
    Payout,
    Quotation,
    QuotationLine,
    ReceiptOnAccount,
    Repair,
    Tender,
    TransactionQuery,
)
from .price_validation_service import PriceValidationService

logger = logging.getLogger(__name__)


class SalesAreaSimpleSerializer(serializers.ModelSerializer):
    """Simple sales area serializer for nested use."""

    class Meta:
        model = SalesArea
        fields = ["id", "number", "name"]


class TenderSerializer(serializers.ModelSerializer):
    """Serializer for payment tenders."""

    tender_type_display = serializers.CharField(
        source="get_tender_type_display", read_only=True
    )

    class Meta:
        model = Tender
        fields = "__all__"
        read_only_fields = ["created_at", "updated_at"]


class CashSaleLineSerializer(serializers.ModelSerializer):
    """Serializer for cash sale line items with price validation."""

    available_prices = serializers.SerializerMethodField(read_only=True)
    price_validation = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = CashSaleLine
        fields = [
            "id",
            "line_number",
            "stock_code",
            "description",
            "quantity",
            "unit_price",
            "discount_percentage",
            "tax_code",
            "line_total",
            "vat_amount",
            "cost_price",
            "line_profit",
            "available_prices",
            "price_validation",
        ]
        extra_kwargs = {
            "line_number": {"required": False},
        }
        read_only_fields = [
            "line_total",
            "vat_amount",
            "line_profit",
            "available_prices",
            "price_validation",
        ]

    def to_internal_value(self, data):
        return super().to_internal_value(data)

    def get_available_prices(self, obj):
        """Get available price levels from StockItem."""
        if not obj.stock_code:
            return None

        try:
            prices = PriceValidationService.get_valid_prices_for_item(obj.stock_code)
            return {
                "price_level_1": float(prices.get("selling_price_1", 0)),
                "markup_1": float(prices.get("markup_percent_1", 0)),
                "price_level_2": float(prices.get("selling_price_2", 0)),
                "markup_2": float(prices.get("markup_percent_2", 0)),
                "price_level_3": float(prices.get("selling_price_3", 0)),
                "markup_3": float(prices.get("markup_percent_3", 0)),
                "cost_price": float(prices.get("cost_price", 0)),
                "maximum_discount": float(prices.get("maximum_discount", 0)),
                "has_special_deal": prices.get("special_deal") is not None,
            }
        except Exception:
            return None

    def get_price_validation(self, obj):
        """Get price validation results."""
        if not obj.stock_code or not obj.unit_price:
            return None

        try:
            result = PriceValidationService.validate_line_item_price(
                stock_code=obj.stock_code,
                quantity=obj.quantity,
                unit_price=obj.unit_price,
                discount_percent=obj.discount_percentage or 0,
                price_level=1,
            )
            return {
                "is_valid": result["is_valid"],
                "warnings": result.get("warnings", []),
                "suggestions": result.get("suggestions", []),
            }
        except Exception:
            return None

    def validate_quantity(self, value):
        """Validate quantity is positive."""
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than zero.")
        return value

    def validate(self, data):
        """Validate unit price against stock item pricing."""
        stock_code = data.get("stock_code")
        unit_price = data.get("unit_price")
        quantity = data.get("quantity", 1)
        discount_percent = data.get("discount_percentage", 0)

        if stock_code and unit_price:
            try:
                result = PriceValidationService.validate_line_item_price(
                    stock_code=stock_code,
                    quantity=quantity,
                    unit_price=unit_price,
                    discount_percent=discount_percent,
                    price_level=1,
                    transaction_date=date.today(),
                )

                # Add warnings to context for later access
                if not result["price_valid"]:
                    self.context["price_warnings"] = result.get("warnings", [])

                if not result["discount_valid"]:
                    raise serializers.ValidationError(
                        f"Discount {discount_percent}% exceeds maximum allowed for this item. "
                        f"Maximum: {result.get('max_discount_allowed')}%"
                    )

            except Exception as e:
                # Don't fail if stock item doesn't exist - it might be a manual entry
                if "not found" in str(e):
                    pass
                else:
                    raise

        return data


class CashSaleListSerializer(serializers.ModelSerializer):
    """Serializer for cash sale list view."""

    cashier_name = serializers.CharField(source="cashier.username", read_only=True)
    sales_area_name = serializers.CharField(source="sales_area.name", read_only=True)
    line_count = serializers.SerializerMethodField()

    class Meta:
        model = CashSale
        fields = [
            "id",
            "sale_number",
            "sale_date",
            "sale_time",
            "customer_name",
            "cashier",
            "cashier_name",
            "station_number",
            "sales_area_name",
            "total_amount",
            "gross_profit",
            "line_count",
            "is_posted",
            "is_cancelled",
            "created_at",
        ]

    def get_line_count(self, obj):
        """Get number of line items."""
        return obj.lines.count()


class CashSaleDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for cash sale."""

    lines = CashSaleLineSerializer(many=True, read_only=True)
    tenders = TenderSerializer(many=True, read_only=True)
    sales_area_detail = SalesAreaSimpleSerializer(source="sales_area", read_only=True)
    cashier_name = serializers.CharField(source="cashier.username", read_only=True)

    class Meta:
        model = CashSale
        fields = "__all__"
        read_only_fields = [
            "subtotal",
            "discount_percentage",
            "vat_amount",
            "total_amount",
            "total_cost",
            "gross_profit",
            "change_given",
            "is_posted",
            "created_at",
            "updated_at",
        ]


class CashSaleCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating cash sales with price validation."""

    lines = CashSaleLineSerializer(many=True)
    tenders = TenderSerializer(many=True, required=False)

    class Meta:
        model = CashSale
        fields = [
            "id",
            "sale_number",
            "sale_date",
            "customer_name",
            "delivery_address",
            "telephone",
            "order_number",
            "job_card_number",
            "sales_area",
            "cashier",
            "station_number",
            "cash_tendered",
            "vat_number",
            "lines",
            "tenders",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make all fields optional for creation
        for field_name in self.fields:
            if self.fields[field_name].required:
                self.fields[field_name].required = False

    def validate(self, attrs):
        return super().validate(attrs)

    def validate_sale_number(self, value):
        """Validate or generate sale number."""
        if not value:
            # Generate a unique sale number
            import uuid

            value = f"CS-{uuid.uuid4().hex[:8].upper()}"
        if CashSale.objects.filter(sale_number=value).exists():
            raise serializers.ValidationError("Sale number already exists.")
        return value

    def validate_lines(self, value):
        """Validate at least one line item."""
        if not value:
            raise serializers.ValidationError("Sale must have at least one line item.")
        return value

    @db_transaction.atomic
    def create(self, validated_data):
        """Create cash sale with lines and tenders, validating prices."""
        # Generate sale_number if not provided
        if not validated_data.get("sale_number"):
            import uuid

            sale_number = f"CS-{uuid.uuid4().hex[:8].upper()}"
            # Ensure unique
            while CashSale.objects.filter(sale_number=sale_number).exists():
                sale_number = f"CS-{uuid.uuid4().hex[:8].upper()}"
            validated_data["sale_number"] = sale_number

        lines_data = validated_data.pop("lines")
        tenders_data = validated_data.pop("tenders", [])

        # Create cash sale
        cash_sale = CashSale.objects.create(**validated_data)

        # Calculate totals
        subtotal = Decimal("0.00")
        vat_total = Decimal("0.00")
        cost_total = Decimal("0.00")
        price_warnings = []

        # Create line items
        for idx, line_data in enumerate(lines_data, start=1):
            line_data["line_number"] = idx

            quantity = line_data["quantity"]
            unit_price = line_data["unit_price"]
            discount_pct = line_data.get("discount_percentage", Decimal("0.00"))
            tax_code = line_data.get("tax_code", 1)
            cost_price = line_data.get("cost_price", Decimal("0.00"))
            stock_code = line_data.get("stock_code")

            # Validate price if stock code provided
            if stock_code:
                try:
                    validation_result = PriceValidationService.validate_line_item_price(
                        stock_code=stock_code,
                        quantity=quantity,
                        unit_price=unit_price,
                        discount_percent=discount_pct,
                        price_level=1,
                        transaction_date=validated_data.get("sale_date", date.today()),
                    )

                    if validation_result.get("warnings"):
                        price_warnings.extend(validation_result["warnings"])

                    # Log variance if price doesn't match
                    if not validation_result["price_valid"]:
                        actual_price = validation_result["price_info"].get(
                            "standard_price", Decimal(0)
                        )
                        if actual_price > 0:
                            variance = (
                                (unit_price - actual_price) / actual_price * 100
                            ).quantize(Decimal("0.01"))
                            PriceValidationService.log_price_variance(
                                stock_code=stock_code,
                                unit_price=unit_price,
                                price_level=1,
                                variance_percent=variance,
                                reason="Manual POS entry",
                            )
                except Exception:
                    # Continue if stock item validation fails - this is
                    # advisory price-variance logging, not a hard requirement
                    # for the sale to go through.
                    logger.warning(
                        "Price validation failed for %s", stock_code, exc_info=True
                    )

            # Calculate line totals
            line_subtotal = quantity * unit_price
            discount_amount = line_subtotal * (discount_pct / 100)
            line_total_before_vat = line_subtotal - discount_amount

            # Calculate VAT
            vat_rate = Decimal("0.14") if tax_code == 1 else Decimal("0.00")
            line_vat = line_total_before_vat * vat_rate
            line_total = line_total_before_vat + line_vat

            # Calculate profit
            line_cost = quantity * cost_price
            line_profit = line_total_before_vat - line_cost

            line_data["line_total"] = line_total
            line_data["vat_amount"] = line_vat
            line_data["line_profit"] = line_profit

            CashSaleLine.objects.create(cash_sale=cash_sale, **line_data)

            subtotal += line_total_before_vat
            vat_total += line_vat
            cost_total += line_cost

        # Update cash sale totals
        cash_sale.subtotal = subtotal
        cash_sale.vat_amount = vat_total
        cash_sale.total_amount = subtotal + vat_total
        cash_sale.total_cost = cost_total
        cash_sale.gross_profit = subtotal - cost_total
        cash_sale.change_given = cash_sale.cash_tendered - cash_sale.total_amount
        cash_sale.save()

        # Create tenders
        for tender_data in tenders_data:
            Tender.objects.create(cash_sale=cash_sale, **tender_data)

        # Store warnings in cache for response
        if price_warnings:
            self.context["price_warnings"] = price_warnings

        return cash_sale


class LaybyeLineSerializer(serializers.ModelSerializer):
    """Serializer for laybye line items."""

    class Meta:
        model = LaybyeLine
        fields = "__all__"
        read_only_fields = ["line_total", "vat_amount"]


class LaybyePaymentSerializer(serializers.ModelSerializer):
    """Serializer for laybye payments."""

    class Meta:
        model = LaybyePayment
        fields = "__all__"
        read_only_fields = ["created_at", "updated_at"]


class LaybyeListSerializer(serializers.ModelSerializer):
    """Serializer for laybye list view."""

    status_display = serializers.CharField(source="get_status_display", read_only=True)
    sales_area_name = serializers.CharField(source="sales_area.name", read_only=True)

    class Meta:
        model = Laybye
        fields = [
            "id",
            "laybye_number",
            "customer_name",
            "telephone",
            "laybye_date",
            "expiry_date",
            "total_amount",
            "deposit_amount",
            "amount_paid",
            "balance_due",
            "status",
            "status_display",
            "sales_area_name",
            "created_at",
        ]


class LaybyeDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for laybye."""

    lines = LaybyeLineSerializer(many=True, read_only=True)
    payments = LaybyePaymentSerializer(many=True, read_only=True)
    sales_area_detail = SalesAreaSimpleSerializer(source="sales_area", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Laybye
        fields = "__all__"
        read_only_fields = [
            "amount_paid",
            "balance_due",
            "refund_amount",
            "created_at",
            "updated_at",
        ]


class LaybyeCreateLineSerializer(serializers.Serializer):
    """One stock line on a new laybye — feeds LaybyeService.create_laybye."""

    stock_code = serializers.CharField(
        max_length=13, required=False, allow_blank=True, default=""
    )
    description = serializers.CharField(
        max_length=200, required=False, allow_blank=True, default=""
    )
    quantity = serializers.DecimalField(
        max_digits=10, decimal_places=2, min_value=Decimal("0.01")
    )
    unit_price = serializers.DecimalField(
        max_digits=12, decimal_places=4, min_value=Decimal("0")
    )
    discount_percentage = serializers.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("0")
    )
    tax_code = serializers.IntegerField(default=1)
    cost_price = serializers.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0")
    )
    transaction_type = serializers.ChoiceField(
        choices=LaybyeLine.TRANSACTION_TYPE_CHOICES, default="SP"
    )
    transaction_date = serializers.DateField(required=False)
    transaction_time = serializers.TimeField(required=False)
    station_number = serializers.IntegerField(required=False, allow_null=True)
    salesman_number = serializers.IntegerField(required=False, allow_null=True)


class LaybyeCreateSerializer(serializers.Serializer):
    """
    Creates a laybye header plus its stock lines in one request. Separate
    from LaybyeDetailSerializer because `lines` is read_only there — this is
    the only path that reaches LaybyeService.create_laybye, which is what
    actually reserves the goods into "laybye stock" (LAYBYE_IN movement).
    """

    laybye_number = serializers.CharField(
        max_length=20, required=False, allow_blank=True, default=""
    )
    customer_name = serializers.CharField(max_length=40)
    address_line1 = serializers.CharField(
        max_length=25, required=False, allow_blank=True, default=""
    )
    address_line2 = serializers.CharField(
        max_length=25, required=False, allow_blank=True, default=""
    )
    address_line3 = serializers.CharField(
        max_length=25, required=False, allow_blank=True, default=""
    )
    telephone = serializers.CharField(
        max_length=15, required=False, allow_blank=True, default=""
    )
    debtor_account_number = serializers.IntegerField(required=False, allow_null=True)
    sales_area = serializers.PrimaryKeyRelatedField(
        queryset=SalesArea.objects.all(), required=False, allow_null=True
    )
    laybye_date = serializers.DateField(required=False)
    expiry_date = serializers.DateField()
    deposit_amount = serializers.DecimalField(
        max_digits=12, decimal_places=2, min_value=Decimal("0")
    )
    comment1 = serializers.CharField(
        max_length=30, required=False, allow_blank=True, default=""
    )
    comment2 = serializers.CharField(
        max_length=30, required=False, allow_blank=True, default=""
    )
    lines = LaybyeCreateLineSerializer(many=True)

    def validate_lines(self, value):
        if not value:
            raise serializers.ValidationError("At least one line item is required.")
        return value


class QuotationLineSerializer(serializers.ModelSerializer):
    """Serializer for quotation line items."""

    class Meta:
        model = QuotationLine
        fields = "__all__"
        read_only_fields = ["line_total", "vat_amount"]


class QuotationListSerializer(serializers.ModelSerializer):
    """Serializer for quotation list view."""

    status_display = serializers.CharField(source="get_status_display", read_only=True)
    sales_area_name = serializers.CharField(source="sales_area.name", read_only=True)

    class Meta:
        model = Quotation
        fields = [
            "id",
            "quotation_number",
            "quotation_date",
            "expiry_date",
            "customer_name",
            "telephone",
            "total_amount",
            "gross_profit",
            "status",
            "status_display",
            "sales_area_name",
            "created_at",
        ]


class QuotationDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for quotation."""

    lines = QuotationLineSerializer(many=True, read_only=True)
    sales_area_detail = SalesAreaSimpleSerializer(source="sales_area", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Quotation
        fields = "__all__"
        read_only_fields = [
            "subtotal",
            "vat_amount",
            "total_amount",
            "gross_profit",
            "created_at",
            "updated_at",
        ]


class QuotationLineCreateSerializer(serializers.ModelSerializer):
    """Writable line item serializer for quotation creation (QuotationLineSerializer's
    'lines' field on QuotationDetailSerializer is read_only, so a dedicated nested
    serializer is needed here - mirrors CreditNoteLineSerializer/CashReturnLineSerializer).
    """

    class Meta:
        model = QuotationLine
        fields = [
            "line_number",
            "stock_code",
            "description",
            "quantity",
            "unit_price",
            "discount_percentage",
            "cost_price",
            "tax_code",
            "department",
            "comments",
            "line_total",
            "vat_amount",
        ]
        read_only_fields = ["line_total", "vat_amount"]


class QuotationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a quotation with line items in one request."""

    lines = QuotationLineCreateSerializer(many=True)

    class Meta:
        model = Quotation
        fields = [
            "quotation_number",
            "quotation_date",
            "expiry_date",
            "customer_name",
            "address_line1",
            "address_line2",
            "address_line3",
            "telephone",
            "debtor_account",
            "sales_area",
            "station_number",
            "comment1",
            "comment2",
            "price_level",
            "lines",
        ]

    def validate_quotation_number(self, value):
        """Validate unique quotation number."""
        if Quotation.objects.filter(quotation_number=value).exists():
            raise serializers.ValidationError("Quotation number already exists.")
        return value

    @db_transaction.atomic
    def create(self, validated_data):
        """Create quotation with lines, computing totals and gross profit."""
        lines_data = validated_data.pop("lines")

        quotation = Quotation.objects.create(**validated_data)

        subtotal = Decimal("0.00")
        vat_total = Decimal("0.00")
        cost_total = Decimal("0.00")

        for idx, line_data in enumerate(lines_data, start=1):
            line_data["line_number"] = idx

            quantity = line_data["quantity"]
            unit_price = line_data["unit_price"]
            discount_percentage = line_data.get("discount_percentage") or Decimal("0")
            cost_price = line_data.get("cost_price") or Decimal("0")
            tax_code = line_data.get("tax_code", 1)

            gross_line = quantity * unit_price
            discount_amount = gross_line * discount_percentage / Decimal("100")
            line_subtotal = gross_line - discount_amount
            vat_rate = Decimal("0.14") if tax_code == 1 else Decimal("0.00")
            line_vat = line_subtotal * vat_rate
            line_total = line_subtotal + line_vat

            line_data["line_total"] = line_total
            line_data["vat_amount"] = line_vat

            QuotationLine.objects.create(quotation=quotation, **line_data)

            subtotal += line_subtotal
            vat_total += line_vat
            cost_total += quantity * cost_price

        quotation.subtotal = subtotal
        quotation.vat_amount = vat_total
        quotation.total_amount = subtotal + vat_total
        quotation.gross_profit = subtotal - cost_total
        quotation.save()

        return quotation


class PayoutSerializer(serializers.ModelSerializer):
    """Serializer for cash payouts."""

    cashier_name = serializers.CharField(source="cashier.username", read_only=True)

    class Meta:
        model = Payout
        fields = "__all__"
        read_only_fields = ["created_at", "updated_at"]

    def validate_amount(self, value):
        """Validate amount is positive."""
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero.")
        return value


class RepairSerializer(serializers.ModelSerializer):
    """Serializer for repair vouchers."""

    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Repair
        fields = "__all__"
        read_only_fields = ["debtor", "created_at", "updated_at"]


class JobCardLineSerializer(serializers.ModelSerializer):
    """Serializer for job card line items."""

    class Meta:
        model = JobCardLine
        fields = "__all__"
        read_only_fields = ["line_total", "vat_amount", "line_profit"]


class JobCardListSerializer(serializers.ModelSerializer):
    """Serializer for job card list view."""

    status_display = serializers.CharField(source="get_status_display", read_only=True)
    sales_area_name = serializers.CharField(source="sales_area.name", read_only=True)

    class Meta:
        model = JobCard
        fields = [
            "id",
            "job_number",
            "job_date",
            "customer_name",
            "telephone",
            "registration_number",
            "subtotal",
            "total_amount",
            "gross_profit",
            "status",
            "status_display",
            "sales_area_name",
            "created_at",
        ]


class JobCardDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for job card."""

    lines = JobCardLineSerializer(many=True, read_only=True)
    sales_area_detail = SalesAreaSimpleSerializer(source="sales_area", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = JobCard
        fields = [
            "id",
            "job_number",
            "job_date",
            "customer_name",
            "address",
            "telephone",
            "contact_person",
            "order_number",
            "registration_number",
            "job_description",
            "sales_area",
            "sales_area_detail",
            "operator_number",
            "subtotal",
            "vat_amount",
            "total_amount",
            "total_cost",
            "gross_profit",
            "status",
            "status_display",
            "cancellation_reason",
            "debtor_account_number",
            "lines",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "subtotal",
            "vat_amount",
            "total_amount",
            "total_cost",
            "gross_profit",
            "created_at",
            "updated_at",
        ]


class CashControlSerializer(serializers.ModelSerializer):
    """Serializer for cash control records."""

    cashier_name = serializers.CharField(source="cashier.username", read_only=True)

    class Meta:
        model = CashControl
        fields = "__all__"
        read_only_fields = ["created_at", "updated_at"]


class CashControlSummarySerializer(serializers.Serializer):
    """Serializer for cash control summary."""

    control_date = serializers.DateField()
    total_sales = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_refunds = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_receipts = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_payouts = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_credits = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_cashed_cheques = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_new_laybyes = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_laybye_receipts = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_cancelled_laybyes = serializers.DecimalField(max_digits=12, decimal_places=2)
    cash_expected = serializers.DecimalField(max_digits=12, decimal_places=2)
    cash_takings = serializers.DecimalField(max_digits=12, decimal_places=2)
    cheque_takings = serializers.DecimalField(max_digits=12, decimal_places=2)
    speedpoint_takings = serializers.DecimalField(max_digits=12, decimal_places=2)


class CashControlHourSerializer(serializers.Serializer):
    """One hour's worth of cash sale movement, for the hourly analysis facility."""

    hour = serializers.IntegerField()
    transaction_count = serializers.IntegerField()
    total_value = serializers.DecimalField(max_digits=12, decimal_places=2)


class CashControlHourlySerializer(serializers.Serializer):
    """Sales movement on a 24-hour basis for a given date (legacy 'Hourly Analysis')."""

    date = serializers.DateField()
    hours = CashControlHourSerializer(many=True)


class ReceiptOnAccountSerializer(serializers.ModelSerializer):
    """Serializer for receipt on account."""

    cashier_name = serializers.CharField(source="cashier.username", read_only=True)
    tender_type_display = serializers.CharField(
        source="get_tender_type_display", read_only=True
    )

    class Meta:
        model = ReceiptOnAccount
        fields = "__all__"
        read_only_fields = [
            "total_amount",
            "is_posted",
            "debtor_transaction",
            "is_cancelled",
            "cancel_reason",
            "cancelled_at",
            "created_at",
            "updated_at",
        ]

    def validate(self, data):
        """Calculate total amount."""
        amount = data.get("amount", Decimal("0.00"))
        settlement_discount = data.get("settlement_discount", Decimal("0.00"))
        data["total_amount"] = amount - settlement_discount
        return data


class CreditNoteLineSerializer(serializers.ModelSerializer):
    """Serializer for credit note line items."""

    class Meta:
        model = CreditNoteLine
        fields = [
            "id",
            "line_number",
            "stock_code",
            "description",
            "quantity",
            "unit_price",
            "tax_code",
            "line_total",
            "vat_amount",
        ]
        read_only_fields = ["line_total", "vat_amount"]


class CreditNoteListSerializer(serializers.ModelSerializer):
    """Serializer for credit note list view."""

    cashier_name = serializers.CharField(source="cashier.username", read_only=True)
    refund_type_display = serializers.CharField(
        source="get_refund_type_display", read_only=True
    )

    class Meta:
        model = CreditNote
        fields = [
            "id",
            "credit_number",
            "credit_date",
            "customer_name",
            "debtor_account",
            "total_amount",
            "refund_type",
            "refund_type_display",
            "cashier_name",
            "is_posted",
            "created_at",
        ]


class CreditNoteDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for credit note."""

    lines = CreditNoteLineSerializer(many=True, read_only=True)
    cashier_name = serializers.CharField(source="cashier.username", read_only=True)

    class Meta:
        model = CreditNote
        fields = "__all__"
        read_only_fields = [
            "subtotal",
            "vat_amount",
            "total_amount",
            "is_posted",
            "is_cancelled",
            "cancel_reason",
            "cancelled_at",
            "created_at",
            "updated_at",
        ]


class CreditNoteCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating credit notes."""

    lines = CreditNoteLineSerializer(many=True)

    class Meta:
        model = CreditNote
        fields = [
            "credit_number",
            "credit_date",
            "customer_name",
            "debtor_account",
            "original_sale_number",
            "reason",
            "sales_area",
            "refund_type",
            "cashier",
            "station_number",
            "lines",
        ]

    def validate_credit_number(self, value):
        """Validate unique credit number."""
        if CreditNote.objects.filter(credit_number=value).exists():
            raise serializers.ValidationError("Credit number already exists.")
        return value

    @db_transaction.atomic
    def create(self, validated_data):
        """Create credit note with lines."""
        lines_data = validated_data.pop("lines")

        credit_note = CreditNote.objects.create(**validated_data)

        subtotal = Decimal("0.00")
        vat_total = Decimal("0.00")

        for idx, line_data in enumerate(lines_data, start=1):
            line_data["line_number"] = idx

            quantity = line_data["quantity"]
            unit_price = line_data["unit_price"]
            tax_code = line_data.get("tax_code", 1)

            line_subtotal = quantity * unit_price
            vat_rate = Decimal("0.14") if tax_code == 1 else Decimal("0.00")
            line_vat = line_subtotal * vat_rate
            line_total = line_subtotal + line_vat

            line_data["line_total"] = line_total
            line_data["vat_amount"] = line_vat

            CreditNoteLine.objects.create(credit_note=credit_note, **line_data)

            subtotal += line_subtotal
            vat_total += line_vat

        credit_note.subtotal = subtotal
        credit_note.vat_amount = vat_total
        credit_note.total_amount = subtotal + vat_total
        credit_note.save()

        return credit_note


class CashReturnLineSerializer(serializers.ModelSerializer):
    """Serializer for cash return line items."""

    class Meta:
        model = CashReturnLine
        fields = [
            "id",
            "line_number",
            "stock_code",
            "description",
            "quantity",
            "unit_price",
            "tax_code",
            "line_total",
            "vat_amount",
        ]
        read_only_fields = ["line_total", "vat_amount"]


class CashReturnSerializer(serializers.ModelSerializer):
    """Serializer for cash returns."""

    lines = CashReturnLineSerializer(many=True, read_only=True)
    cashier_name = serializers.CharField(source="cashier.username", read_only=True)

    class Meta:
        model = CashReturn
        fields = "__all__"
        read_only_fields = [
            "subtotal",
            "vat_amount",
            "total_amount",
            "is_posted",
            "is_cancelled",
            "cancel_reason",
            "cancelled_at",
            "created_at",
            "updated_at",
        ]


class CashReturnCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating cash returns (header + lines in one request)."""

    lines = CashReturnLineSerializer(many=True)

    class Meta:
        model = CashReturn
        fields = [
            "return_number",
            "return_date",
            "original_sale_number",
            "customer_name",
            "reason",
            "cashier",
            "station_number",
            "lines",
        ]

    def validate_return_number(self, value):
        if CashReturn.objects.filter(return_number=value).exists():
            raise serializers.ValidationError("Return number already exists.")
        return value

    @db_transaction.atomic
    def create(self, validated_data):
        lines_data = validated_data.pop("lines")

        cash_return = CashReturn.objects.create(**validated_data)

        subtotal = Decimal("0.00")
        vat_total = Decimal("0.00")

        for idx, line_data in enumerate(lines_data, start=1):
            line_data["line_number"] = idx

            quantity = line_data["quantity"]
            unit_price = line_data["unit_price"]
            tax_code = line_data.get("tax_code", 1)

            line_subtotal = quantity * unit_price
            vat_rate = Decimal("0.14") if tax_code == 1 else Decimal("0.00")
            line_vat = line_subtotal * vat_rate
            line_total = line_subtotal + line_vat

            line_data["line_total"] = line_total
            line_data["vat_amount"] = line_vat

            CashReturnLine.objects.create(cash_return=cash_return, **line_data)

            subtotal += line_subtotal
            vat_total += line_vat

        cash_return.subtotal = subtotal
        cash_return.vat_amount = vat_total
        cash_return.total_amount = subtotal + vat_total
        cash_return.save()

        return cash_return


class CashAChequeSerializer(serializers.ModelSerializer):
    """Serializer for cash a cheque."""

    cashier_name = serializers.CharField(source="cashier.username", read_only=True)

    class Meta:
        model = CashACheque
        fields = "__all__"
        read_only_fields = [
            "is_processed",
            "is_cancelled",
            "cancel_reason",
            "cancelled_at",
            "created_at",
            "updated_at",
        ]

    def validate(self, data):
        """Calculate cash paid."""
        cheque_amount = data.get("cheque_amount", Decimal("0.00"))
        commission = data.get("commission", Decimal("0.00"))
        data["cash_paid"] = cheque_amount - commission
        return data


class TransactionQuerySerializer(serializers.ModelSerializer):
    """Serializer for transaction queries."""

    transaction_type_display = serializers.CharField(
        source="get_transaction_type_display", read_only=True
    )
    query_status_display = serializers.CharField(
        source="get_query_status_display", read_only=True
    )
    assigned_to_name = serializers.CharField(
        source="assigned_to.username", read_only=True, allow_null=True
    )
    resolved_by_name = serializers.CharField(
        source="resolved_by.username", read_only=True, allow_null=True
    )

    class Meta:
        model = TransactionQuery
        fields = "__all__"
        read_only_fields = ["created_at", "updated_at"]


class InvoiceLineSerializer(serializers.ModelSerializer):
    """Serializer for invoice line items."""

    def to_representation(self, instance):
        """Add detailed error handling for serialization."""
        try:
            return super().to_representation(instance)
        except Exception as e:
            logger.error(
                f"Error serializing InvoiceLine {instance.id}: {type(e).__name__}: {str(e)}",
                exc_info=True,
            )
            raise

    def validate(self, data):
        """
        Enforce maximum discount % and surface below-cost/price warnings,
        mirroring CashSaleLineSerializer.validate() — same manual-documented
        rule ("Where a maximum discount has been set... this may not be
        exceeded"), previously only enforced on CashSaleLine.
        """
        stock_code = data.get("stock_code")
        unit_price = data.get("unit_price")
        quantity = data.get("quantity", 1)
        discount_percent = data.get("discount_percentage", 0)

        if stock_code and unit_price:
            try:
                result = PriceValidationService.validate_line_item_price(
                    stock_code=stock_code,
                    quantity=quantity,
                    unit_price=unit_price,
                    discount_percent=discount_percent,
                    price_level=1,
                    transaction_date=date.today(),
                )

                if not result["price_valid"]:
                    self.context["price_warnings"] = result.get("warnings", [])

                if not result["discount_valid"]:
                    raise serializers.ValidationError(
                        f"Discount {discount_percent}% exceeds maximum allowed for this item. "
                        f"Maximum: {result.get('max_discount_allowed')}%"
                    )

            except Exception as e:
                # Don't fail if stock item doesn't exist - it might be a manual entry
                if "not found" in str(e):
                    pass
                else:
                    raise

        return data

    class Meta:
        model = InvoiceLine
        fields = [
            "id",
            "line_number",
            "stock_code",
            "description",
            "quantity",
            "unit_price",
            "discount_percentage",
            "tax_code",
            "vat_rate",
            "line_total",
            "vat_amount",
            "cost_price",
            "line_cost",
            "line_profit",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "line_total",
            "vat_amount",
            "line_cost",
            "line_profit",
            "created_at",
            "updated_at",
        ]


class InvoiceListSerializer(serializers.ModelSerializer):
    """Serializer for invoice list view."""

    debtor_name = serializers.CharField(source="debtor.dname", read_only=True)
    debtor_account_number = serializers.CharField(source="debtor.dno", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Invoice
        fields = [
            "id",
            "invoice_number",
            "invoice_date",
            "due_date",
            "debtor",
            "debtor_name",
            "debtor_account_number",
            "total_amount",
            "amount_paid",
            "balance_due",
            "status",
            "status_display",
            "is_posted",
            "is_overdue",
            "created_at",
        ]
        read_only_fields = ["is_posted", "balance_due", "is_overdue", "created_at"]


class InvoiceDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for invoice with line items."""

    debtor_name = serializers.CharField(source="debtor.dname", read_only=True)
    debtor_account_number = serializers.CharField(source="debtor.dno", read_only=True)
    lines = InvoiceLineSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    profit_margin = serializers.ReadOnlyField()
    balance_due = serializers.ReadOnlyField()
    is_overdue = serializers.ReadOnlyField()
    days_overdue = serializers.ReadOnlyField()
    requires_cash_tender = serializers.ReadOnlyField()

    def to_representation(self, instance):
        """Add detailed error handling for serialization."""
        try:
            return super().to_representation(instance)
        except Exception as e:
            logger.error(
                f"Error serializing Invoice {instance.id}: {type(e).__name__}: {str(e)}",
                exc_info=True,
            )
            # Log debtor info
            if instance.debtor:
                logger.error(
                    f"Debtor: id={instance.debtor.id}, dno={instance.debtor.dno}, dname={instance.debtor.dname}"
                )
            # Log lines count
            lines_count = instance.lines.count()
            logger.error(f"Invoice has {lines_count} lines")
            raise

    class Meta:
        model = Invoice
        fields = [
            "id",
            "invoice_number",
            "invoice_date",
            "due_date",
            "debtor",
            "debtor_name",
            "debtor_account_number",
            "delivery_name",
            "delivery_address_line1",
            "delivery_address_line2",
            "delivery_telephone",
            "order_number",
            "customer_reference",
            "job_card_number",
            "sales_area",
            "subtotal",
            "discount_amount",
            "vat_amount",
            "total_amount",
            "total_cost",
            "gross_profit",
            "profit_margin",
            "status",
            "status_display",
            "is_posted",
            "posted_date",
            "amount_paid",
            "paid_date",
            "balance_due",
            "is_overdue",
            "days_overdue",
            "requires_cash_tender",
            "created_by",
            "notes",
            "lines",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "is_posted",
            "posted_date",
            "profit_margin",
            "balance_due",
            "is_overdue",
            "days_overdue",
            "requires_cash_tender",
            "created_at",
            "updated_at",
        ]


class InvoiceCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating invoice."""

    # Accept debtor_account_number and convert to debtor ID
    debtor_account_number = serializers.CharField(write_only=True, required=False)
    # Explicitly define debtor as not required since we convert from debtor_account_number
    # Use a custom field that allows setting via to_internal_value
    debtor = serializers.PrimaryKeyRelatedField(
        queryset=Debtor.objects.none(),  # Set in __init__ to avoid circular imports
        required=False,  # Not required as input - set via debtor_account_number
        help_text="Customer/Debtor (can be provided via debtor_account_number)",
    )
    # Accept both 'lines' and 'line_items' for line items (frontend uses 'line_items')
    lines = InvoiceLineSerializer(many=True, required=False, write_only=True)
    line_items = InvoiceLineSerializer(many=True, required=False, write_only=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set queryset here to avoid circular import issues
        from apps.debtors.models import Debtor

        self.fields["debtor"].queryset = Debtor.objects.all()

    def to_internal_value(self, data):
        """Convert debtor_account_number to debtor, and merge line_items -> lines."""
        ret = super().to_internal_value(data)

        # Merge line_items into lines if lines not provided (frontend compatibility)
        if "line_items" in ret and "lines" not in ret:
            ret["lines"] = ret.pop("line_items")
        elif "line_items" in ret:
            ret.pop("line_items")

        # Handle debtor_account_number -> debtor conversion
        debtor_account_number = data.get("debtor_account_number")
        if debtor_account_number:
            from apps.debtors.models import Debtor

            try:
                debtor = Debtor.objects.get(dno=int(debtor_account_number))
                ret["debtor"] = debtor
            except Debtor.DoesNotExist:
                raise serializers.ValidationError(
                    {
                        "debtor_account_number": f"Debtor with account number {debtor_account_number} not found"
                    }
                )
            except ValueError:
                raise serializers.ValidationError(
                    {
                        "debtor_account_number": "Invalid account number format. Must be a number."
                    }
                )

        # Remove debtor_account_number from validated_data as it's not a model field
        ret.pop("debtor_account_number", None)

        return ret

    def create(self, validated_data):
        """Create invoice with line items."""
        lines_data = validated_data.pop("lines", [])

        # Set default sales_area if not provided
        if "sales_area" not in validated_data or not validated_data.get("sales_area"):
            from apps.settings.models import SalesArea

            default_sales_area = SalesArea.objects.filter(is_active=True).first()
            if default_sales_area:
                validated_data["sales_area"] = str(default_sales_area.number).zfill(2)
            else:
                # Fallback: use a default sales area code
                validated_data["sales_area"] = "01"

        with db_transaction.atomic():
            invoice = Invoice.objects.create(**validated_data)

            # Trade Discount (manual §2.1: "Enter % discount (if any) by which
            # each line item at POS will automatically be reduced") — applied
            # as the default when a line doesn't specify its own discount,
            # matching the DOS Discount % prompt being pre-filled but
            # editable. Cash Sales aren't debtor-account transactions, so
            # this only applies to Invoice.
            debtor = validated_data.get("debtor")
            trade_discount = debtor.ddiscper if debtor and debtor.ddiscper else None

            for line_data in lines_data:
                if trade_discount and "discount_percentage" not in line_data:
                    line_data["discount_percentage"] = trade_discount
                InvoiceLine.objects.create(invoice=invoice, **line_data)

        return invoice

    def update(self, instance, validated_data):
        """Update invoice with line items."""
        lines_data = validated_data.pop("lines", None)

        with db_transaction.atomic():
            # Update invoice fields
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()

            # Update line items if provided
            if lines_data is not None:
                instance.lines.all().delete()
                for line_data in lines_data:
                    InvoiceLine.objects.create(invoice=instance, **line_data)

        return instance

    class Meta:
        model = Invoice
        fields = [
            "invoice_number",
            "invoice_date",
            "due_date",
            "debtor",
            "debtor_account_number",  # Frontend uses this
            "delivery_name",
            "delivery_address_line1",
            "delivery_address_line2",
            "delivery_telephone",
            "order_number",
            "customer_reference",
            "job_card_number",
            "sales_area",
            "created_by",  # Frontend can set this for salesman
            "subtotal",
            "discount_amount",
            "vat_amount",
            "total_amount",
            "total_cost",
            "gross_profit",
            "status",
            "notes",
            "lines",
            "line_items",  # Frontend uses this (alias for lines)
        ]
