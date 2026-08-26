from rest_framework import serializers

from .models import (
    StockFinderPurchaseOrder,
    StockFinderPurchaseOrderLine,
    StockFinderSalesOrder,
    StockFinderSalesOrderLine,
)


class StockFinderSalesOrderLineSerializer(serializers.ModelSerializer):
    """Serializer for sales order lines."""

    class Meta:
        model = StockFinderSalesOrderLine
        fields = [
            "id",
            "line_number",
            "stock_code",
            "description",
            "quantity",
            "unit_price",
            "tax_amount",
            "line_total",
        ]


class StockFinderSalesOrderSerializer(serializers.ModelSerializer):
    """Serializer for sales orders from Stockfinder."""

    lines = StockFinderSalesOrderLineSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = StockFinderSalesOrder
        fields = [
            "id",
            "stockfinder_order_id",
            "order_number",
            "customer_name",
            "customer_email",
            "customer_phone",
            "vehicle_registration",
            "vehicle_make",
            "vehicle_model",
            "status",
            "status_display",
            "order_date",
            "required_date",
            "notes",
            "fitment_center",
            "subtotal",
            "tax_amount",
            "total_amount",
            "local_job_card",
            "local_invoice",
            "lines",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "subtotal",
            "tax_amount",
            "total_amount",
        ]


class StockFinderSalesOrderCreateSerializer(serializers.Serializer):
    """
    Serializer for creating a sales order from Stockfinder data.
    """

    stockfinder_order_id = serializers.CharField(max_length=50)
    customer_name = serializers.CharField(max_length=200)
    customer_email = serializers.EmailField(required=False, allow_blank=True)
    customer_phone = serializers.CharField(
        max_length=20, required=False, allow_blank=True
    )
    vehicle_registration = serializers.CharField(
        max_length=20, required=False, allow_blank=True
    )
    vehicle_make = serializers.CharField(
        max_length=50, required=False, allow_blank=True
    )
    vehicle_model = serializers.CharField(
        max_length=50, required=False, allow_blank=True
    )
    order_date = serializers.DateTimeField()
    required_date = serializers.DateTimeField(required=False, allow_null=True)
    notes = serializers.CharField(required=False, allow_blank=True)
    fitment_center = serializers.CharField(
        max_length=100, required=False, allow_blank=True
    )
    lines = serializers.ListField(
        child=serializers.DictField(child=serializers.CharField(allow_blank=True)),
        required=False,
        default=list,
    )


class StockFinderPurchaseOrderLineSerializer(serializers.ModelSerializer):
    """Serializer for purchase order lines."""

    class Meta:
        model = StockFinderPurchaseOrderLine
        fields = [
            "id",
            "line_number",
            "stock_code",
            "description",
            "quantity",
            "unit_cost",
            "line_total",
            "quantity_received",
        ]


class StockFinderPurchaseOrderSerializer(serializers.ModelSerializer):
    """Serializer for purchase orders from Stockfinder."""

    lines = StockFinderPurchaseOrderLineSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = StockFinderPurchaseOrder
        fields = [
            "id",
            "stockfinder_po_id",
            "local_po_number",
            "supplier_name",
            "supplier_code",
            "status",
            "status_display",
            "order_date",
            "expected_date",
            "notes",
            "subtotal",
            "tax_amount",
            "total_amount",
            "local_purchase_order",
            "lines",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "subtotal",
            "tax_amount",
            "total_amount",
        ]


class StockFinderPurchaseOrderCreateSerializer(serializers.Serializer):
    """
    Serializer for creating a purchase order from Stockfinder data.
    """

    stockfinder_po_id = serializers.CharField(max_length=50)
    supplier_name = serializers.CharField(max_length=200)
    supplier_code = serializers.CharField(
        max_length=50, required=False, allow_blank=True
    )
    order_date = serializers.DateTimeField()
    expected_date = serializers.DateField(required=False, allow_null=True)
    notes = serializers.CharField(required=False, allow_blank=True)
    lines = serializers.ListField(
        child=serializers.DictField(child=serializers.CharField(allow_blank=True)),
        required=False,
        default=list,
    )
