"""
Django Admin configuration for Stockfinder integration.
"""
from django.contrib import admin
from .models import (
    StockFinderConfig,
    StockFinderSyncLog,
    StockFinderWebhookEvent,
    StockFinderStockItem,
    StockFinderSalesOrder,
    StockFinderSalesOrderLine,
    StockFinderPurchaseOrder,
    StockFinderPurchaseOrderLine,
)


@admin.register(StockFinderConfig)
class StockFinderConfigAdmin(admin.ModelAdmin):
    list_display = ['name', 'base_url', 'fitment_center_code', 'is_active', 'auto_sync_stock', 'last_sync']
    list_filter = ['is_active', 'auto_sync_stock', 'webhook_enabled']
    search_fields = ['name', 'base_url', 'fitment_center_code']
    readonly_fields = ['created_at', 'updated_at', 'last_sync']
    fieldsets = [
        ('Connection', {
            'fields': ['name', 'base_url', 'api_key', 'api_secret', 'fitment_center_code', 'is_active']
        }),
        ('Sync Settings', {
            'fields': ['auto_sync_stock', 'sync_interval_minutes', 'last_sync']
        }),
        ('Custom Pricing', {
            'fields': ['enable_custom_pricing', 'custom_price_field_1', 'custom_price_field_2', 'custom_price_field_3']
        }),
        ('Webhook', {
            'fields': ['webhook_enabled', 'webhook_secret']
        }),
    ]


@admin.register(StockFinderSyncLog)
class StockFinderSyncLogAdmin(admin.ModelAdmin):
    list_display = ['sync_type', 'status', 'config', 'items_processed', 'items_failed', 'started_at', 'completed_at']
    list_filter = ['sync_type', 'status', 'config']
    search_fields = ['config__name', 'error_message']
    readonly_fields = ['created_at', 'request_data', 'response_data']


@admin.register(StockFinderWebhookEvent)
class StockFinderWebhookEventAdmin(admin.ModelAdmin):
    list_display = ['event_type', 'event_id', 'processed', 'created_at', 'processed_at']
    list_filter = ['event_type', 'processed']
    search_fields = ['event_id', 'payload']
    readonly_fields = ['event_id', 'payload', 'processing_error', 'processed_at']


@admin.register(StockFinderStockItem)
class StockFinderStockItemAdmin(admin.ModelAdmin):
    list_display = ['stock_code', 'description', 'quantity_on_hand', 'quantity_available', 'cost_price', 'retail_price', 'last_synced']
    list_filter = ['is_active', 'category', 'last_synced']
    search_fields = ['stock_code', 'description', 'barcode', 'manufacturer_code']
    readonly_fields = ['last_synced', 'created_at', 'updated_at']


class StockFinderSalesOrderLineInline(admin.TabularInline):
    model = StockFinderSalesOrderLine
    extra = 0
    readonly_fields = ['line_number', 'stock_code', 'description', 'quantity', 'unit_price', 'line_total']


@admin.register(StockFinderSalesOrder)
class StockFinderSalesOrderAdmin(admin.ModelAdmin):
    list_display = ['stockfinder_order_id', 'customer_name', 'vehicle_registration', 'status', 'order_date', 'total_amount', 'local_job_card']
    list_filter = ['status', 'fitment_center', 'order_date']
    search_fields = ['stockfinder_order_id', 'customer_name', 'vehicle_registration', 'order_number']
    inlines = [StockFinderSalesOrderLineInline]
    readonly_fields = ['created_at', 'updated_at']


class StockFinderPurchaseOrderLineInline(admin.TabularInline):
    model = StockFinderPurchaseOrderLine
    extra = 0
    readonly_fields = ['line_number', 'stock_code', 'description', 'quantity', 'unit_cost', 'line_total']


@admin.register(StockFinderPurchaseOrder)
class StockFinderPurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ['stockfinder_po_id', 'supplier_name', 'status', 'order_date', 'total_amount', 'local_purchase_order']
    list_filter = ['status', 'order_date']
    search_fields = ['stockfinder_po_id', 'supplier_name', 'local_po_number']
    inlines = [StockFinderPurchaseOrderLineInline]
    readonly_fields = ['created_at', 'updated_at']
