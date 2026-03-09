# tenancy/admin.py
from django.contrib import admin
from django.conf import settings
from tenancy.models import Tenant
from tenancy.models import Shop
from tenancy.models import ShopConfiguration
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