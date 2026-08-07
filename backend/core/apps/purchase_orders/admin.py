from django.contrib import admin
from .models import (
    PurchaseOrder, PurchaseOrderLine, PurchaseOrderReceipt,
    PurchaseOrderReceiptLine, BackOrder, PurchaseOrderTemplate,
    PurchaseOrderTemplateLine
)


class PurchaseOrderLineInline(admin.TabularInline):
    model = PurchaseOrderLine
    extra = 0
    readonly_fields = (
        'quantity_delivered', 'quantity_outstanding', 'total_exclusive',
        'total_vat', 'total_inclusive', 'outstanding_exclusive',
        'outstanding_vat', 'outstanding_inclusive', 'is_fully_received',
        'created_at', 'updated_at'
    )


class PurchaseOrderReceiptLineInline(admin.TabularInline):
    model = PurchaseOrderReceiptLine
    extra = 0
    readonly_fields = (
        'line_exclusive', 'line_vat', 'line_inclusive',
        'has_cost_variance', 'cost_variance_amount', 'created_at'
    )


class PurchaseOrderTemplateLineInline(admin.TabularInline):
    model = PurchaseOrderTemplateLine
    extra = 1


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = (
        'order_number', 'supplier', 'order_date', 'delivery_date',
        'status', 'quantity_ordered', 'total_value_inclusive'
    )
    list_filter = ('status', 'order_date', 'delivery_date', 'supplier')
    search_fields = ('order_number', 'supplier__name')
    readonly_fields = (
        'order_number', 'status', 'quantity_ordered', 'total_quantity_received',
        'total_quantity_outstanding', 'total_value_exclusive', 'total_value_vat',
        'total_value_inclusive', 'outstanding_value_exclusive', 'outstanding_value_vat',
        'outstanding_value_inclusive', 'created_at', 'updated_at', 'cancelled_at'
    )
    inlines = [PurchaseOrderLineInline]
    fieldsets = (
        ('Order Details', {
            'fields': ('order_number', 'supplier', 'order_date', 'delivery_date', 'pricing_method')
        }),
        ('Status', {
            'fields': ('status', 'is_back_order', 'parent_order')
        }),
        ('Totals', {
            'fields': (
                ('quantity_ordered', 'total_quantity_received', 'total_quantity_outstanding'),
                ('total_value_exclusive', 'total_value_vat', 'total_value_inclusive'),
                ('outstanding_value_exclusive', 'outstanding_value_vat', 'outstanding_value_inclusive')
            )
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'cancelled_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(PurchaseOrderLine)
class PurchaseOrderLineAdmin(admin.ModelAdmin):
    list_display = (
        'purchase_order', 'line_number', 'stock_item', 'quantity',
        'quantity_delivered', 'base_price', 'total_exclusive'
    )
    list_filter = ('purchase_order', 'is_fully_received', 'created_at')
    search_fields = ('purchase_order__order_number', 'stock_item__stock_code')
    readonly_fields = (
        'quantity_delivered', 'quantity_outstanding', 'total_exclusive',
        'total_vat', 'total_inclusive', 'outstanding_exclusive',
        'outstanding_vat', 'outstanding_inclusive', 'is_fully_received',
        'created_at', 'updated_at'
    )


@admin.register(PurchaseOrderReceipt)
class PurchaseOrderReceiptAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'purchase_order', 'receipt_date', 'invoice_number',
        'total_quantity', 'total_value_inclusive', 'has_variance'
    )
    list_filter = ('receipt_date', 'has_variance', 'purchase_order__supplier')
    search_fields = ('invoice_number', 'purchase_order__order_number')
    readonly_fields = (
        'total_quantity', 'total_value_exclusive', 'total_value_vat',
        'total_value_inclusive', 'created_at'
    )
    inlines = [PurchaseOrderReceiptLineInline]
    fieldsets = (
        ('Receipt Details', {
            'fields': ('purchase_order', 'receipt_date', 'invoice_number')
        }),
        ('Totals', {
            'fields': (
                ('total_quantity',),
                ('total_value_exclusive', 'total_value_vat', 'total_value_inclusive')
            )
        }),
        ('Variance', {
            'fields': ('has_variance', 'variance_notes')
        }),
        ('Integration', {
            'fields': ('creditor_grn',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )


@admin.register(PurchaseOrderReceiptLine)
class PurchaseOrderReceiptLineAdmin(admin.ModelAdmin):
    list_display = (
        'receipt', 'purchase_order_line', 'quantity_received',
        'actual_unit_cost', 'line_inclusive'
    )
    list_filter = ('receipt__receipt_date', 'has_cost_variance')
    search_fields = ('receipt__id', 'purchase_order_line__stock_item__stock_code')
    readonly_fields = (
        'line_exclusive', 'line_vat', 'line_inclusive',
        'has_cost_variance', 'cost_variance_amount', 'created_at'
    )


@admin.register(BackOrder)
class BackOrderAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'original_order', 'back_order', 'created_date', 'reason'
    )
    list_filter = ('created_date',)
    search_fields = ('original_order__order_number', 'back_order__order_number')
    readonly_fields = ('created_at',)


@admin.register(PurchaseOrderTemplate)
class PurchaseOrderTemplateAdmin(admin.ModelAdmin):
    list_display = (
        'template_name', 'supplier', 'default_delivery_days',
        'pricing_method', 'is_active', 'created_at'
    )
    list_filter = ('is_active', 'pricing_method', 'supplier')
    search_fields = ('template_name', 'supplier__name')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [PurchaseOrderTemplateLineInline]
    fieldsets = (
        ('Template Details', {
            'fields': ('template_name', 'supplier', 'description')
        }),
        ('Settings', {
            'fields': ('default_delivery_days', 'pricing_method', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(PurchaseOrderTemplateLine)
class PurchaseOrderTemplateLineAdmin(admin.ModelAdmin):
    list_display = (
        'template', 'line_number', 'stock_item', 'default_quantity'
    )
    list_filter = ('template',)
    search_fields = ('template__template_name', 'stock_item__stock_code')
    readonly_fields = ('created_at',)
