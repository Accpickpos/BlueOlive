from django.contrib.auth.models import UserManager
from tenancy.tenant_context import get_current_tenant

class TenantUserManager(UserManager):
    """
    Custom manager that automatically filters users by current tenant
    """
    def get_queryset(self):
        qs = super().get_queryset()
        tenant = get_current_tenant()
        
        # If we're in a tenant context, only show users from that tenant
        if tenant:
            return qs.filter(tenant_id=tenant.id)
        
        # Otherwise (admin/superuser context), show all users
        return qs
    
    def create_user(self, username, email=None, password=None, **extra_fields):
        """Create a regular user with tenant"""
        tenant = extra_fields.get('tenant_id') or get_current_tenant()
        tenant_id = tenant.id if hasattr(tenant, 'id') else tenant
        
        if not tenant_id and not extra_fields.get('is_superuser', False):
            raise ValueError('Regular users must have a tenant')
        
        extra_fields.setdefault('tenant_id', tenant_id)
        return super().create_user(username, email, password, **extra_fields)
    
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        """Create a superuser without tenant"""
        extra_fields['tenant_id'] = None  # Superusers don't belong to tenants
        return super().create_superuser(username, email, password, **extra_fields)