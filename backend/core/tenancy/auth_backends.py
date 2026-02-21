# tenancy/auth_backends.py
"""
Custom authentication backend for tenant-aware authentication.

SECURITY IMPROVEMENTS:
- Removed dangerous fallback to default database
- Only allows authentication within proper tenant context
"""
from django.contrib.auth.backends import ModelBackend
from django.conf import settings
from shop_users.models import ShopUser
from tenancy.tenant_context import get_current_tenant
from tenancy.utils import register_tenant_connection
import logging

logger = logging.getLogger(__name__)


class TenantAwareAuthBackend(ModelBackend):
    """
    Custom authentication backend that authenticates users within tenant context.
    
    SECURITY: This backend requires a valid tenant context to authenticate.
    There is NO fallback to default database to prevent cross-tenant access.
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None or password is None:
            return None
        
        tenant = get_current_tenant()
        
        if not tenant:
            # Try to get tenant from kwargs (for programmatic auth)
            tenant_id = kwargs.get('tenant_id')
            if tenant_id:
                from tenancy.models import Tenant
                try:
                    tenant = Tenant.objects.get(id=tenant_id)
                    register_tenant_connection(tenant)
                except Tenant.DoesNotExist:
                    return None
        
        if not tenant:
            # SECURITY: No fallback - require tenant context
            if settings.DEBUG:
                logger.debug("No tenant context for authentication - denied")
            return None
        
        if settings.DEBUG:
            logger.debug(f"Authenticating {username} in tenant: {tenant.slug} (DB: {tenant.db_alias})")
        
        try:
            # CRITICAL: Query from TENANT database using .using()
            # Try to find user by username
            user = ShopUser.objects.using(tenant.db_alias).filter(
                username=username
            ).first()
            
            # If not found, try email
            if not user:
                user = ShopUser.objects.using(tenant.db_alias).filter(
                    email=username
                ).first()
            
            if not user:
                if settings.DEBUG:
                    logger.debug(f"User {username} not found in tenant {tenant.slug}")
                return None
            
            # Verify user belongs to this tenant
            if user.tenant_id != tenant.id:
                if settings.DEBUG:
                    logger.warning(f"User {username} found but belongs to different tenant")
                return None
            
            # Check password
            if user.check_password(password):
                if settings.DEBUG:
                    logger.debug(f"✓ User {username} authenticated successfully")
                return user
            else:
                if settings.DEBUG:
                    logger.debug(f"✗ Invalid password for {username}")
                return None
                
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}", exc_info=True)
            return None
    
    def get_user(self, user_id):
        """
        Get user by ID from tenant database.
        
        SECURITY: No fallback to default database. This prevents
        users from default DB accessing tenant data.
        """
        tenant = get_current_tenant()
        
        if not tenant:
            # SECURITY: Removed dangerous fallback!
            # Only allow if explicitly enabled via setting (not recommended)
            if getattr(settings, 'ALLOW_DEFAULT_DB_FALLBACK', False):
                logger.warning("SECURITY: Using default DB fallback (should be disabled!)")
                try:
                    return ShopUser.objects.get(pk=user_id)
                except ShopUser.DoesNotExist:
                    return None
            
            # Default: deny access
            logger.error(
                f"SECURITY: Auth get_user called without tenant context for user {user_id}. "
                f"Access denied. Set ALLOW_DEFAULT_DB_FALLBACK=True only for debugging."
            )
            return None
        
        try:
            # CRITICAL: Query from TENANT database
            return ShopUser.objects.using(tenant.db_alias).get(pk=user_id)
        except ShopUser.DoesNotExist:
            if settings.DEBUG:
                logger.debug(f"User {user_id} not found in tenant {tenant.slug}")
            return None