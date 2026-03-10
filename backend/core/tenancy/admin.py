# tenancy/admin.py
from django.contrib import admin
from django.conf import settings
from tenancy.models import Tenant, Shop, ShopConfiguration, SubscriptionPlan, Subscription, SubscriptionPayment
from tenancy.audit import AuditLog
from tenancy.utils import provision_tenant
from tenancy.shop_manager import create_shop_schema
from tenancy.utils import register_tenant_connection


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "db_name", "created_at")
    readonly_fields = ("created_at",)
    search_fields = ("name", "slug")

    def save_model(self, request, obj, form, change):
        """
        When a new tenant is saved in admin:
        - Save tenant metadata
        - Automatically create the tenant database
        - Run migrations
        """
        super().save_model(request, obj, form, change)

        if not change:  # Only when creating, not editing
            superuser_conn_info = {
                "host": settings.DATABASES["default"]["HOST"],
                "port": settings.DATABASES["default"]["PORT"],
                "user": settings.DATABASES["default"]["USER"],
                "password": settings.DATABASES["default"]["PASSWORD"],
            }
            # 🔸 Create DB + register connection + run migrations
            provision_tenant(obj, superuser_conn_info)


@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    list_display = ("name", "tenant", "schema_name", "subdomain", "created_at")
    readonly_fields = ("created_at",)
    search_fields = ("name", "schema_name", "tenant__name")

    def save_model(self, request, obj, form, change):
        """
        When a new Shop is created in admin:
        - Connect to tenant DB
        - Create schema inside that DB
        - Run migrations for that schema
        """
        super().save_model(request, obj, form, change)


@admin.register(ShopConfiguration)
class ShopConfigurationAdmin(admin.ModelAdmin):
    """Admin for per-shop period-end configuration"""
    list_display = ('shop', 'enable_auto_day_end', 'enable_auto_month_end', 
                   'enable_auto_year_end', 'current_period', 'current_financial_year')
    list_filter = ('enable_auto_day_end', 'enable_auto_month_end', 'enable_auto_year_end')
    search_fields = ('shop__name', 'shop__tenant__name')
    raw_id_fields = ('shop',)
    
    fieldsets = (
        ('Shop', {
            'fields': ('shop',)
        }),
        ('Period End Tracking', {
            'fields': ('last_day_end_date', 'last_month_end_date', 'last_year_end_date')
        }),
        ('Day-End Settings', {
            'fields': ('enable_auto_day_end', 'day_end_time', 'day_end_day_of_week')
        }),
        ('Month-End Settings', {
            'fields': ('enable_auto_month_end', 'month_end_day', 'month_end_time')
        }),
        ('Year-End Settings', {
            'fields': ('enable_auto_year_end', 'year_end_month', 'year_end_day', 'year_end_time')
        }),
        ('Accounting Period', {
            'fields': ('current_financial_year', 'current_period')
        }),
    )


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """
    Read-only audit log viewer for security monitoring.
    Allows admins to review security events without modification.
    """
    list_display = ('timestamp', 'user', 'action', 'resource_type', 'ip_address', 'success')
    list_filter = ('action', 'success', 'timestamp', 'tenant_id')
    search_fields = ('user__username', 'ip_address', 'resource_id')
    readonly_fields = ('timestamp', 'user', 'action', 'resource_type', 'resource_id', 
                       'ip_address', 'user_agent', 'tenant_id', 'details', 'success', 'error_message')
    
    def has_add_permission(self, request):
        """Prevent manual audit log creation"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Prevent audit log deletion - logs are immutable for compliance"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Prevent audit log modification"""
        return False

        if not change:
            tenant = obj.tenant
            # Ensure tenant DB connection exists
            register_tenant_connection(tenant)

            # 🔸 Create schema and migrate inside tenant DB
            create_shop_schema(tenant, obj.schema_name)


# ============================================================================
# SUBSCRIPTION ADMIN
# ============================================================================

@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    """Admin for subscription plans."""
    list_display = ('name', 'slug', 'price', 'billing_period_days', 'max_shops', 'max_users', 'is_active', 'is_trial', 'sort_order')
    list_filter = ('is_active', 'is_trial', 'billing_period_days')
    search_fields = ('name', 'slug', 'description')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description')
        }),
        ('Pricing', {
            'fields': ('price', 'setup_fee', 'billing_period_days')
        }),
        ('Limits', {
            'fields': ('max_shops', 'max_users', 'max_invoices_per_month')
        }),
        ('Features', {
            'fields': ('features',)
        }),
        ('Settings', {
            'fields': ('is_active', 'is_trial', 'sort_order')
        }),
    )


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """Admin for subscriptions."""
    list_display = ('tenant', 'plan', 'status', 'start_date', 'end_date', 'auto_renew', 'created_at')
    list_filter = ('status', 'auto_renew', 'plan')
    search_fields = ('tenant__name', 'tenant__slug', 'gateway_subscription_id')
    readonly_fields = ('created_at', 'updated_at', 'current_period_start', 'current_period_end', 'invoices_this_period')
    raw_id_fields = ('tenant',)
    
    fieldsets = (
        ('Tenant & Plan', {
            'fields': ('tenant', 'plan')
        }),
        ('Status', {
            'fields': ('status', 'auto_renew', 'cancelled_at')
        }),
        ('Dates', {
            'fields': ('start_date', 'end_date', 'trial_end_date', 'current_period_start', 'current_period_end')
        }),
        ('Usage', {
            'fields': ('invoices_this_period',)
        }),
        ('Gateway', {
            'fields': ('gateway_customer_id', 'gateway_subscription_id'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['activate_subscriptions', 'deactivate_subscriptions', 'extend_trials']
    
    def activate_subscriptions(self, request, queryset):
        updated = queryset.update(status='ACTIVE', auto_renew=True)
        self.message_user(request, f"{updated} subscriptions activated.")
    activate_subscriptions.short_description = "Activate selected subscriptions"
    
    def deactivate_subscriptions(self, request, queryset):
        updated = queryset.update(status='CANCELLED', auto_renew=False)
        self.message_user(request, f"{updated} subscriptions cancelled.")
    deactivate_subscriptions.short_description = "Cancel selected subscriptions"
    
    def extend_trials(self, request, queryset):
        from datetime import timedelta
        from django.utils import timezone
        today = timezone.now().date()
        extended = 0
        for sub in queryset:
            if sub.status == 'TRIAL':
                new_trial_end = sub.trial_end_date + timedelta(days=7) if sub.trial_end_date else today + timedelta(days=7)
                sub.trial_end_date = new_trial_end
                sub.save()
                extended += 1
        self.message_user(request, f"Extended trial for {extended} subscriptions.")
    extend_trials.short_description = "Extend trial by 7 days"


@admin.register(SubscriptionPayment)
class SubscriptionPaymentAdmin(admin.ModelAdmin):
    """Admin for subscription payments."""
    list_display = ('subscription', 'amount', 'currency', 'status', 'payment_method', 'paid_at', 'created_at')
    list_filter = ('status', 'payment_method', 'currency')
    search_fields = ('subscription__tenant__name', 'gateway_payment_id', 'gateway_reference', 'invoice_number')
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('subscription',)
    
    fieldsets = (
        ('Payment', {
            'fields': ('subscription', 'amount', 'currency', 'payment_method')
        }),
        ('Status', {
            'fields': ('status', 'paid_at', 'failed_at')
        }),
        ('Gateway', {
            'fields': ('gateway_payment_id', 'gateway_reference'),
            'classes': ('collapse',)
        }),
        ('Invoice', {
            'fields': ('description', 'invoice_number')
        }),
    )
    
    actions = ['mark_as_succeeded', 'mark_as_failed', 'refund_payments']
    
    def mark_as_succeeded(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(status='SUCCEEDED', paid_at=timezone.now().date())
        self.message_user(request, f"{updated} payments marked as succeeded.")
    mark_as_succeeded.short_description = "Mark as succeeded"
    
    def mark_as_failed(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(status='FAILED', failed_at=timezone.now().date())
        self.message_user(request, f"{updated} payments marked as failed.")
    mark_as_failed.short_description = "Mark as failed"
    
    def refund_payments(self, request, queryset):
        updated = queryset.filter(status='SUCCEEDED').update(status='REFUNDED')
        self.message_user(request, f"Refunded {updated} payments.")
    refund_payments.short_description = "Refund selected payments"