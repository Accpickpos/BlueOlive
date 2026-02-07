from django.contrib import admin
from django.db.models import Sum, F, DecimalField
from django.db.models.functions import Coalesce
from .models import (
    StockItem, SpecialDeal, FuturePricing, ShrinkWrap, PackBundle,
    PackBundleIngredient, StockTransaction, StockTake, StockTakeItem,
    ContractPricing, OneTouchLookupKey, StockMonthlyStatistic,
    SalesDepartment, SalesArea
)


class StockItemInlineAdmin(admin.TabularInline):
    model = StockItem
    extra = 0
    fields = ['stock_code', 'description', 'cost_price', 'selling_price_1', 'quantity_on_hand', 'is_active']
    readonly_fields = ['stock_code']


@admin.register(SalesDepartment)
class SalesDepartmentAdmin(admin.ModelAdmin):
    list_display = ['number', 'name', 'active_items', 'stock_value']
    list_filter = ['created_at']
    search_fields = ['name', 'number']
    readonly_fields = ['created_at', 'updated_at']
    
    def active_items(self, obj):
        return obj.stock_items.filter(is_active=True).count()
    active_items.short_description = 'Active Items'
    
    def stock_value(self, obj):
        total = obj.stock_items.aggregate(
            total=Coalesce(Sum(F('quantity_on_hand') * F('cost_price'), output_field=DecimalField()), 0)
        )['total']
        return f"R {total:,.2f}"
    stock_value.short_description = 'Total Stock Value'


@admin.register(SalesArea)
class SalesAreaAdmin(admin.ModelAdmin):
    list_display = ['number', 'name']
    search_fields = ['name', 'number']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(StockItem)
class StockItemAdmin(admin.ModelAdmin):
    list_display = ['stock_code', 'description', 'department', 'cost_price', 'selling_price_1', 'quantity_on_hand', 'is_active']
    list_filter = ['department', 'supplier', 'is_active', 'created_at']
    search_fields = ['stock_code', 'description', 'supplier_code']
    readonly_fields = ['created_at', 'updated_at', 'sales_mtd_quantity', 'sales_mtd_value', 'sales_ytd_quantity', 'sales_ytd_value']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('stock_code', 'description', 'department', 'supplier', 'supplier_code', 'bin_number')
        }),
        ('Pricing', {
            'fields': ('cost_price', 'average_cost', 'selling_price_1', 'selling_price_2', 'selling_price_3', 'markup_1', 'markup_2', 'markup_3')
        }),
        ('Stock Control', {
            'fields': ('quantity_on_hand', 'quantity_counted', 'quantity_on_order', 'reorder_quantity', 'default_selling_quantity', 'allow_negative_quantities')
        }),
        ('Configuration', {
            'fields': ('tax_code', 'maximum_discount_percent', 'is_active')
        }),
        ('Statistics', {
            'fields': ('sales_mtd_quantity', 'sales_mtd_value', 'sales_ytd_quantity', 'sales_ytd_value', 'date_last_purchased', 'date_last_sold'),
            'classes': ('collapse',)
        }),
        ('System', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    ordering = ['stock_code']


@admin.register(SpecialDeal)
class SpecialDealAdmin(admin.ModelAdmin):
    list_display = ['stock_item', 'start_date', 'end_date', 'special_selling_price_1', 'is_active', 'is_valid_today']
    list_filter = ['is_active', 'start_date', 'end_date']
    search_fields = ['stock_item__stock_code', 'stock_item__description']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'start_date'
    
    fieldsets = (
        ('Item', {
            'fields': ('stock_item',)
        }),
        ('Pricing', {
            'fields': ('special_cost_price', 'special_selling_price_1', 'special_selling_price_2', 'special_selling_price_3', 'special_markup_1', 'special_markup_2', 'special_markup_3')
        }),
        ('Period', {
            'fields': ('start_date', 'end_date', 'is_active')
        }),
        ('System', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(FuturePricing)
class FuturePricingAdmin(admin.ModelAdmin):
    list_display = ['stock_item', 'effective_date', 'future_selling_price_1', 'is_applied']
    list_filter = ['is_applied', 'effective_date']
    search_fields = ['stock_item__stock_code', 'stock_item__description']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'effective_date'
    
    fieldsets = (
        ('Item', {
            'fields': ('stock_item',)
        }),
        ('Pricing', {
            'fields': ('future_cost_price', 'future_selling_price_1', 'future_selling_price_2', 'future_selling_price_3', 'future_markup_1', 'future_markup_2', 'future_markup_3')
        }),
        ('Application', {
            'fields': ('effective_date', 'is_applied')
        }),
        ('System', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ShrinkWrap)
class ShrinkWrapAdmin(admin.ModelAdmin):
    list_display = ['shrink_pack_code', 'quantity_in_bulk', 'bulk_pack_code']
    search_fields = ['shrink_pack_code__stock_code', 'bulk_pack_code__stock_code']
    readonly_fields = ['created_at', 'updated_at']


class PackBundleIngredientInline(admin.TabularInline):
    model = PackBundleIngredient
    extra = 1
    fields = ['ingredient_stock', 'quantity', 'cost_at_creation']
    raw_id_fields = ['ingredient_stock']


@admin.register(PackBundle)
class PackBundleAdmin(admin.ModelAdmin):
    list_display = ['stock_item', 'total_cost', 'ingredient_count']
    search_fields = ['stock_item__stock_code', 'stock_item__description']
    readonly_fields = ['created_at', 'updated_at', 'total_cost']
    inlines = [PackBundleIngredientInline]
    
    def ingredient_count(self, obj):
        return obj.ingredients.count()
    ingredient_count.short_description = 'Ingredients'


@admin.register(StockTransaction)
class StockTransactionAdmin(admin.ModelAdmin):
    list_display = ['transaction_date', 'transaction_type', 'stock_item', 'quantity_in', 'quantity_out', 'reference']
    list_filter = ['transaction_type', 'transaction_date', 'stock_item__department']
    search_fields = ['stock_item__stock_code', 'reference', 'transaction_number']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'transaction_date'
    
    fieldsets = (
        ('Transaction', {
            'fields': ('transaction_type', 'transaction_date', 'transaction_number', 'stock_item')
        }),
        ('Quantities', {
            'fields': ('quantity_in', 'quantity_out', 'quantity_balance')
        }),
        ('Pricing', {
            'fields': ('unit_cost', 'unit_price')
        }),
        ('Details', {
            'fields': ('reference', 'station_number')
        }),
        ('System', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ['transaction_type', 'stock_item', 'transaction_date']
        return self.readonly_fields


class StockTakeItemInline(admin.TabularInline):
    model = StockTakeItem
    extra = 0
    fields = ['stock_item', 'quantity_on_hand', 'quantity_counted', 'variance_quantity', 'variance_value', 'is_counted']
    readonly_fields = ['quantity_on_hand', 'variance_quantity', 'variance_value']


@admin.register(StockTake)
class StockTakeAdmin(admin.ModelAdmin):
    list_display = ['stock_take_date', 'status', 'item_count', 'counted_items', 'created_by']
    list_filter = ['status', 'stock_take_date', 'is_after_trading']
    readonly_fields = ['created_at', 'updated_at', 'completed_at']
    inlines = [StockTakeItemInline]
    date_hierarchy = 'stock_take_date'
    
    fieldsets = (
        ('Stock Take', {
            'fields': ('stock_take_date', 'status', 'description', 'created_by')
        }),
        ('Options', {
            'fields': ('reset_negatives_to_zero', 'set_uncounted_to_zero', 'is_after_trading', 'trading_start_date')
        }),
        ('System', {
            'fields': ('created_at', 'updated_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )
    
    def item_count(self, obj):
        return obj.items.count()
    item_count.short_description = 'Total Items'
    
    def counted_items(self, obj):
        return obj.items.filter(is_counted=True).count()
    counted_items.short_description = 'Counted Items'


@admin.register(ContractPricing)
class ContractPricingAdmin(admin.ModelAdmin):
    list_display = ['debtor', 'pricing_method', 'stock_item', 'contract_price', 'is_active']
    list_filter = ['pricing_method', 'is_active', 'created_at']
    search_fields = ['debtor__account_number', 'stock_item__stock_code']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Debtor', {
            'fields': ('debtor', 'pricing_method')
        }),
        ('Item Selection', {
            'fields': ('stock_item', 'department', 'supplier')
        }),
        ('Pricing', {
            'fields': ('contract_price', 'markup_percent', 'discount_percent', 'is_fixed_pricing')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('System', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(OneTouchLookupKey)
class OneTouchLookupKeyAdmin(admin.ModelAdmin):
    list_display = ['key_character', 'stock_item']
    search_fields = ['key_character', 'stock_item__stock_code']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(StockMonthlyStatistic)
class StockMonthlyStatisticAdmin(admin.ModelAdmin):
    list_display = ['stock_item', 'year', 'month', 'quantity_sold', 'value_sold', 'profit_percent']
    list_filter = ['year', 'month', 'stock_item__department']
    search_fields = ['stock_item__stock_code']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = None
