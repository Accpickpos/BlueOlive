"""
Django Admin Configuration for Settings App
Registers settings-specific models for Django admin interface

Note: Some models (SalesDepartment, SalesArea, IncomeCategory, ExpenseCategory) 
are shared with other apps and registered in their respective admin files.
"""
from django.contrib import admin
from django.contrib.auth import get_user_model
from .models import (
    TaxCode,
    CostingCategory,
    PaymentMethod,
    CreditTerms,
    SystemConfiguration,
    DepartmentMonthlyStats,
    SalesAreaMonthlyStats,
    APIKey,
)

User = get_user_model()


# ═══════════════════════════════════════════════════════════════════════════
# Inline Admin Classes
# ═══════════════════════════════════════════════════════════════════════════


class CreatedUpdatedByAdminMixin(admin.ModelAdmin):
    """Mixin to display created_by and updated_by fields"""
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by')
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


# ═══════════════════════════════════════════════════════════════════════════
# Tax Code Admin
# ═══════════════════════════════════════════════════════════════════════════


@admin.register(TaxCode)
class TaxCodeAdmin(CreatedUpdatedByAdminMixin, admin.ModelAdmin):
    list_display = ('code', 'description', 'rate', 'is_default', 'is_active')
    list_filter = ('is_active', 'is_default')
    search_fields = ('code', 'description')
    ordering = ('code',)
    list_editable = ('is_active',)
    readonly_fields = ('deactivated_at', 'deactivated_by')


# ═══════════════════════════════════════════════════════════════════════════
# Costing Category Admin
# ═══════════════════════════════════════════════════════════════════════════


@admin.register(CostingCategory)
class CostingCategoryAdmin(CreatedUpdatedByAdminMixin, admin.ModelAdmin):
    list_display = ('name', 'costing_method', 'pricing_method', 'description', 'is_active')
    list_filter = ('is_active', 'costing_method', 'pricing_method')
    search_fields = ('name', 'description')
    ordering = ('name',)
    list_editable = ('is_active',)
    readonly_fields = ('deactivated_at', 'deactivated_by')


# ═══════════════════════════════════════════════════════════════════════════
# Payment Method Admin
# ═══════════════════════════════════════════════════════════════════════════


@admin.register(PaymentMethod)
class PaymentMethodAdmin(CreatedUpdatedByAdminMixin, admin.ModelAdmin):
    list_display = ('code', 'name', 'requires_reference', 'is_electronic', 'is_active')
    list_filter = ('is_active', 'is_electronic')
    search_fields = ('name', 'code')
    ordering = ('code',)
    list_editable = ('is_active',)
    readonly_fields = ('deactivated_at', 'deactivated_by')


# ═══════════════════════════════════════════════════════════════════════════
# Credit Terms Admin
# ═══════════════════════════════════════════════════════════════════════════


@admin.register(CreditTerms)
class CreditTermsAdmin(CreatedUpdatedByAdminMixin, admin.ModelAdmin):
    list_display = ('days', 'description', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('description', 'days')
    ordering = ('days',)
    list_editable = ('is_active',)
    readonly_fields = ('deactivated_at', 'deactivated_by')


# ═══════════════════════════════════════════════════════════════════════════
# System Configuration Admin
# ═══════════════════════════════════════════════════════════════════════════


@admin.register(SystemConfiguration)
class SystemConfigurationAdmin(CreatedUpdatedByAdminMixin, admin.ModelAdmin):
    list_display = ('shop_name', 'shop_email', 'shop_vat_number', 'current_financial_year', 'current_period')
    list_filter = ('current_financial_year', 'current_period')
    fieldsets = (
        ('Shop Information', {
            'fields': ('shop_name', 'shop_address', 'shop_phone', 'shop_email', 'shop_vat_number', 'shop_registration_number')
        }),
        ('Tax Settings', {
            'fields': ('default_tax_code',)
        }),
        ('Financial Settings', {
            'fields': ('current_financial_year', 'current_period', 'ageing_periods')
        }),
        ('Business Rules', {
            'fields': ('enable_negative_stock', 'auto_post_transactions', 'charge_interest_on_overdue', 'default_interest_rate')
        }),
        ('Display Settings', {
            'fields': ('date_format', 'currency_symbol', 'decimal_places')
        }),
        ('Audit', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by')


# ═══════════════════════════════════════════════════════════════════════════
# Department Monthly Stats Admin (Read-only)
# ═══════════════════════════════════════════════════════════════════════════


@admin.register(DepartmentMonthlyStats)
class DepartmentMonthlyStatsAdmin(admin.ModelAdmin):
    list_display = ('department', 'year', 'month', 'sales_value', 'profit_value', 'profit_percent')
    list_filter = ('year', 'month')
    search_fields = ('department__name',)
    ordering = ('-year', '-month', 'department')
    readonly_fields = ('department', 'year', 'month', 'sales_value', 'profit_value', 'profit_percent')
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


# ═══════════════════════════════════════════════════════════════════════════
# Sales Area Monthly Stats Admin (Read-only)
# ═══════════════════════════════════════════════════════════════════════════


@admin.register(SalesAreaMonthlyStats)
class SalesAreaMonthlyStatsAdmin(admin.ModelAdmin):
    list_display = ('sales_area', 'year', 'month', 'sales_value', 'profit_value', 'commission_earned')
    list_filter = ('year', 'month')
    search_fields = ('sales_area__name',)
    ordering = ('-year', '-month', 'sales_area')
    readonly_fields = ('sales_area', 'year', 'month', 'sales_value', 'profit_value', 'commission_earned')
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


# ═══════════════════════════════════════════════════════════════════════════
# API Key Admin
# ═══════════════════════════════════════════════════════════════════════════


@admin.register(APIKey)
class APIKeyAdmin(CreatedUpdatedByAdminMixin, admin.ModelAdmin):
    list_display = ('name', 'key_display', 'tenant', 'external_service', 'status', 'expires_at', 'last_used')
    list_filter = ('status', 'external_service')
    search_fields = ('name', 'tenant__name', 'external_service')
    ordering = ('-created_at',)
    list_editable = ('status',)
    readonly_fields = ('key', 'created_at', 'updated_at', 'created_by', 'updated_by', 'last_used')
    fieldsets = (
        (None, {
            'fields': ('name', 'key', 'tenant', 'external_service', 'status')
        }),
        ('Validity', {
            'fields': ('expires_at',)
        }),
        ('Usage', {
            'fields': ('last_used',)
        }),
        ('Audit', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )
    
    def key_display(self, obj):
        """Show masked key for security"""
        if obj.key:
            return f"••••••••{obj.key[-4:]}"
        return "No key"
    key_display.short_description = "API Key"
