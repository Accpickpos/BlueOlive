# shop_users/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import ShopUser


@admin.register(ShopUser)
class ShopUserAdmin(UserAdmin):
    """
    Admin interface for ShopUser model
    """

    list_display = [
        "username",
        "email",
        "first_name",
        "last_name",
        "tenant_id",
        "role",
        "is_active",
        "is_staff",
    ]
    list_filter = [
        "is_active",
        "is_staff",
        "role",
        "tenant_id",
    ]  # Changed from 'tenant' to 'tenant_id'
    search_fields = ["username", "email", "first_name", "last_name"]
    ordering = ["username"]

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name", "email", "phone")}),
        (
            "Tenant info",
            {"fields": ("tenant_id", "role", "shop_ids")},
        ),  # Added shop_ids
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "username",
                    "email",
                    "password1",
                    "password2",
                    "tenant_id",
                    "role",
                    "shop_ids",
                ),
            },
        ),
    )

    def get_queryset(self, request):
        """
        Optionally filter users based on superuser status
        """
        qs = super().get_queryset(request)
        # Superusers see all users, others see only their tenant
        if request.user.is_superuser:
            return qs
        if hasattr(request.user, "tenant_id"):
            return qs.filter(tenant_id=request.user.tenant_id)
        return qs.none()

    # Optional: Display tenant name instead of just ID
    def tenant_name(self, obj):
        """Display tenant name in list view"""
        if obj.tenant:
            return obj.tenant.name
        return f"Tenant #{obj.tenant_id}"

    tenant_name.short_description = "Tenant"

    # You can replace tenant_id with tenant_name in list_display if you prefer:
    # list_display = ['username', 'email', 'first_name', 'last_name', 'tenant_name', 'role', 'is_active', 'is_staff']
