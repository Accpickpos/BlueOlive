# tenancy/auth_backends.py
from django.contrib.auth.backends import ModelBackend
from shop_users.models import ShopUser
from tenancy.tenant_context import get_current_tenant


class TenantAwareAuthBackend(ModelBackend):
    """
    Custom authentication backend that authenticates users within tenant context
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        tenant = get_current_tenant()
        
        if not tenant:
            # Try to get tenant from kwargs
            tenant_id = kwargs.get('tenant_id')
            if tenant_id:
                from tenancy.models import Tenant
                try:
                    tenant = Tenant.objects.get(id=tenant_id)
                except Tenant.DoesNotExist:
                    return None
        
        if not tenant:
            return None
        
        try:
            # Try to find user by username
            user = ShopUser.objects.filter(
                tenant_id=tenant.id,
                username=username
            ).first()
            
            # If not found, try email
            if not user:
                user = ShopUser.objects.filter(
                    tenant_id=tenant.id,
                    email=username
                ).first()
            
            if user and user.check_password(password):
                return user
                
        except ShopUser.DoesNotExist:
            return None
        
        return None
    
    def get_user(self, user_id):
        try:
            return ShopUser.objects.get(pk=user_id)
        except ShopUser.DoesNotExist:
            return None