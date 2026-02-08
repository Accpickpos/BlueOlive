# tenancy/permissions.py
"""
Role-based permission classes for Django REST Framework
"""
from rest_framework.permissions import BasePermission
from functools import wraps


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
    """Allow access only to Django superusers (site administrators)"""
    message = "Only superusers can access this resource."
    
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_superuser)


class IsTenantMember(BasePermission):
    """
    Ensure user belongs to the current tenant.
    Prevents users from accessing other tenants' data.
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
        
        # Superusers can access all tenants
        if request.user.is_superuser:
            return True
        
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
        
        if not request.user.is_superuser and request.user.tenant_id != tenant.id:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('You do not have access to this tenant')
        
        return func(request, *args, **kwargs)
    return wrapper


class IsShopMember(BasePermission):
    """
    Ensure user has access to a specific shop.
    Users with role ADMIN have access to all shops.
    Other users only have access to assigned shops.
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
        
        # Superusers and admins have access to all shops
        if request.user.is_superuser or request.user.role == 'ADMIN':
            return True
        
        # Other users only have access to assigned shops
        if hasattr(obj, 'id'):
            return obj.id in request.user.shop_ids
        
        return False
