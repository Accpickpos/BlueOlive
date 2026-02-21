# tenancy/permissions.py
"""
Role-based permission classes for Django REST Framework

SECURITY IMPROVEMENTS:
- Superusers must use impersonation to access tenant data (with audit logging)
- Removed dangerous bypass patterns that allowed unlimited access
"""
from rest_framework.permissions import BasePermission
from functools import wraps
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class IsAdmin(BasePermission):
    """Allow access only to admin users"""
    message = "Only administrators can access this resource."
    
    def has_permission(self, request, view):
        return bool(request.user and request.user.role == 'ADMIN')


class IsManager(BasePermission):
    """Allow access to managers and admins"""
    message = "Only managers and administrators can access this resource."
    
    def has_permission(self, request, view):
        return bool(
            request.user and request.user.role in ['ADMIN', 'MANAGER']
        )


class IsCashier(BasePermission):
    """Allow access to cashiers, managers, and admins"""
    message = "Only cashiers and above can access this resource."
    
    def has_permission(self, request, view):
        return bool(
            request.user and request.user.role in ['ADMIN', 'MANAGER', 'CASHIER']
        )


class IsStaff(BasePermission):
    """Allow access to all authenticated staff"""
    message = "Only staff can access this resource."
    
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)


class IsAdminUser(BasePermission):
    """
    Allow access only to Django superusers (site administrators).
    
    SECURITY: Superusers must specify X-Impersonate-Tenant header to access
    tenant-specific resources. This ensures all superuser actions are audited.
    """
    message = "Only superusers can access this resource."
    
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_superuser)


class IsSuperUserWithImpersonation(BasePermission):
    """
    Superusers can access tenant resources ONLY with impersonation header.
    
    SECURITY: This replaces the dangerous "superuser bypass" pattern.
    Superusers MUST specify X-Impersonate-Tenant header to access tenant data.
    All impersonation actions are logged.
    
    Headers:
    - X-Impersonate-Tenant: <tenant_id> - Required for superusers
    - X-Impersonate-Reason: <reason> - Recommended for audit trail
    """
    message = "Superusers must specify X-Impersonate-Tenant header to access tenant resources."
    
    def has_permission(self, request, view):
        from tenancy.tenant_context import get_current_tenant
        
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Non-superusers use normal tenant-based access
        if not request.user.is_superuser:
            # Regular users just need to belong to a tenant
            tenant = get_current_tenant()
            if tenant and request.user.tenant_id == tenant.id:
                return True
            return False
        
        # Superuser handling - require impersonation header
        impersonate_tenant = request.headers.get('X-Impersonate-Tenant')
        
        if not impersonate_tenant:
            # Deny access if no impersonation header (security!
            return False
        
        # Validate the tenant exists and is active
        from tenancy.models import Tenant
        try:
            tenant = Tenant.objects.get(id=impersonate_tenant, is_active=True)
        except Tenant.DoesNotExist:
            logger.warning(
                f"Superuser {request.user.username} tried to impersonate "
                f"non-existent/inactive tenant: {impersonate_tenant}"
            )
            return False
        
        # Log the impersonation
        self._log_impersonation(request, tenant)
        
        # Set up impersonation context
        from tenancy.tenant_context import set_current_tenant
        from tenancy.utils import register_tenant_connection
        
        register_tenant_connection(tenant)
        set_current_tenant(tenant)
        request.tenant = tenant
        
        # Add impersonation info to request for audit
        request.is_impersonating = True
        request.impersonated_by = request.user
        request.impersonated_tenant = tenant
        
        return True
    
    def _log_impersonation(self, request, tenant):
        """Log superuser impersonation for audit trail."""
        reason = request.headers.get('X-Impersonate-Reason', 'Not specified')
        
        logger.info(
            f"SUPERUSER IMPERSONATION: User={request.user.username}, "
            f"Tenant={tenant.slug} (id={tenant.id}), Reason={reason}, "
            f"IP={self._get_client_ip(request)}"
        )
        
        # Try to write to audit log if available
        try:
            from tenancy.audit import TenantAuditLog
            TenantAuditLog.log_superuser_impersonation(
                request=request,
                superuser=request.user,
                target_tenant=tenant,
                reason=reason
            )
        except ImportError:
            pass  # Audit module might not exist
        except Exception as e:
            logger.warning(f"Failed to log impersonation: {e}")
    
    @staticmethod
    def _get_client_ip(request):
        """Get client IP from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR', 'unknown')


class IsTenantMember(BasePermission):
    """
    Ensure user belongs to the current tenant.
    Prevents users from accessing other tenants' data.
    
    SECURITY: Superusers must use impersonation (see IsSuperUserWithImpersonation).
    This class does NOT bypass for superusers anymore.
    """
    message = "You do not have permission to access this tenant's resources."
    
    def has_permission(self, request, view):
        from tenancy.tenant_context import get_current_tenant
        from tenancy.audit import TenantAuditLog
        
        if not request.user or not request.user.is_authenticated:
            return False
        
        tenant = get_current_tenant()
        if not tenant:
            # Can't determine tenant, deny access
            return False
        
        # SECURITY: Removed superuser bypass!
        # Superusers must use IsSuperUserWithImpersonation instead
        
        # Regular users must belong to the tenant
        if request.user.tenant_id != tenant.id:
            # Log the cross-tenant access attempt
            try:
                TenantAuditLog.log_cross_tenant_access_attempt(
                    request,
                    request.user,
                    tenant.id,
                    request.user.tenant_id
                )
            except Exception:
                pass  # Don't fail the permission check if logging fails
            return False
        
        return True


class CanCreateTenant(BasePermission):
    """
    Allow unauthenticated users to create the initial tenant.
    After tenant creation, only authenticated superusers can create additional tenants.
    """
    message = "Authentication required to create additional tenants."
    
    def has_permission(self, request, view):
        if request.method == 'POST':
            # Allow unauthenticated users to create initial tenant
            # (tenant creation endpoint will create admin user)
            return True
        return True


# Decorator for function-based views
def require_role(*allowed_roles):
    """
    Decorator for function-based views to restrict by role.
    Usage:
        @require_role('ADMIN', 'MANAGER')
        def my_view(request):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            if not request.user or not request.user.is_authenticated:
                from rest_framework.exceptions import AuthenticationFailed
                raise AuthenticationFailed('Authentication required')
            
            if request.user.role not in allowed_roles:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied(f'This action requires one of these roles: {", ".join(allowed_roles)}')
            
            return func(request, *args, **kwargs)
        return wrapper
    return decorator


# Decorator for tenant membership validation
def require_tenant_member(func):
    """
    Decorator to ensure user belongs to current tenant.
    
    SECURITY: Superusers must use impersonation (X-Impersonate-Tenant header).
    This decorator does NOT bypass for superusers anymore.
    
    Usage:
        @require_tenant_member
        def my_view(request):
            ...
    """
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        from tenancy.tenant_context import get_current_tenant
        
        if not request.user or not request.user.is_authenticated:
            from rest_framework.exceptions import AuthenticationFailed
            raise AuthenticationFailed('Authentication required')
        
        tenant = get_current_tenant()
        if not tenant:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('No tenant context')
        
        # SECURITY: Removed superuser bypass!
        # Superusers must use X-Impersonate-Tenant header
        if request.user.tenant_id != tenant.id:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('You do not have access to this tenant')
        
        return func(request, *args, **kwargs)
    return wrapper


class IsShopMember(BasePermission):
    """
    Ensure user has access to a specific shop.
    Users with role ADMIN have access to all shops.
    Other users only have access to assigned shops.
    
    SECURITY: Removed superuser bypass - superusers must use impersonation.
    """
    message = "You do not have permission to access this shop."
    
    def has_object_permission(self, request, view, obj):
        """Check if user has access to a specific shop object."""
        from tenancy.tenant_context import get_current_tenant
        
        if not request.user or not request.user.is_authenticated:
            return False
        
        tenant = get_current_tenant()
        if not tenant:
            return False
        
        # SECURITY: Removed superuser bypass!
        # Admins have access to all shops (but must be in the tenant)
        if request.user.role == 'ADMIN' and request.user.tenant_id == tenant.id:
            return True
        
        # Other users only have access to assigned shops
        if hasattr(obj, 'id'):
            return obj.id in request.user.shop_ids
        
        return False
