from django.contrib import admin

from .models import (
    StockFinderConfig,
    StockFinderPurchaseOrder,
    StockFinderPurchaseOrderLine,
    StockFinderSalesOrder,
    StockFinderSalesOrderLine,
)


@admin.register(StockFinderConfig)
class StockFinderConfigAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "base_url",
        "fitment_center_code",
        "is_active",
        "auto_sync_stock",
    ]
    list_filter = ["is_active", "auto_sync_stock", "webhook_enabled"]
    readonly_fields = ["created_at", "updated_at", "last_sync"]


class StockFinderSalesOrderLineInline(admin.TabularInline):
    model = StockFinderSalesOrderLine
    extra = 0
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(StockFinderSalesOrder)
class StockFinderSalesOrderAdmin(admin.ModelAdmin):
    list_display = [
        "stockfinder_order_id",
        "customer_name",
        "vehicle_registration",
        "status",
        "order_date",
        "total_amount",
    ]
    list_filter = ["status", "fitment_center", "order_date"]
    search_fields = [
        "stockfinder_order_id",
        "customer_name",
        "vehicle_registration",
        "order_number",
    ]
    inlines = [StockFinderSalesOrderLineInline]
    readonly_fields = ["created_at", "updated_at"]
    fields = [
        "stockfinder_order_id",
        "order_number",
        "customer_name",
        "customer_email",
        "customer_phone",
        "vehicle_registration",
        "vehicle_make",
        "vehicle_model",
        "status",
        "order_date",
        "required_date",
        "notes",
        "fitment_center",
        "subtotal",
        "tax_amount",
        "total_amount",
        "local_job_card",
        "local_invoice",
        "created_at",
        "updated_at",
    ]


class StockFinderPurchaseOrderLineInline(admin.TabularInline):
    model = StockFinderPurchaseOrderLine
    extra = 0
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(StockFinderPurchaseOrder)
class StockFinderPurchaseOrderAdmin(admin.ModelAdmin):
    list_display = [
        "stockfinder_po_id",
        "supplier_name",
        "status",
        "order_date",
        "total_amount",
    ]
    list_filter = ["status", "order_date"]
    search_fields = ["stockfinder_po_id", "supplier_name", "local_po_number"]
    inlines = [StockFinderPurchaseOrderLineInline]
    readonly_fields = ["created_at", "updated_at"]
    fields = [
        "stockfinder_po_id",
        "local_po_number",
        "supplier_name",
        "supplier_code",
        "status",
        "order_date",
        "expected_date",
        "notes",
        "subtotal",
        "tax_amount",
        "total_amount",
        "local_purchase_order",
        "created_at",
        "updated_at",
    ]
