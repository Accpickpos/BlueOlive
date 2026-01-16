# tenancy/admin.py
from django.contrib import admin
from django.conf import settings
from tenancy.models import Tenant
from tenancy.models import Shop
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

        if not change:
            tenant = obj.tenant
            # Ensure tenant DB connection exists
            register_tenant_connection(tenant)

            # 🔸 Create schema and migrate inside tenant DB
            create_shop_schema(tenant, obj.schema_name)