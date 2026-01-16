from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import ShopUser

@admin.register(ShopUser)
class ShopUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'tenant_id', 'shop_id', 'role', 'is_active', 'is_staff']
    list_filter = ['tenant_id', 'shop_id', 'role', 'is_active', 'is_staff', 'date_joined']
    search_fields = ['username', 'email', 'first_name', 'last_name', 'phone']
    
    fieldsets = UserAdmin.fieldsets + (
        ('Tenant & Role Information', {
            'fields': ('tenant_id', 'shop_id', 'role', 'phone')
        }),
    )
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Tenant & Role Information', {
            'fields': ('tenant_id', 'shop_id', 'role', 'phone')
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Superusers see all users
        if request.user.is_superuser:
            return qs
        # Other staff only see users from their tenant
        if hasattr(request.user, 'tenant_id') and request.user.tenant_id:
            return qs.filter(tenant_id=request.user.tenant_id)
        return qs.none()