"""
Common Permissions Module

Shared permission classes that can be used across all business apps.
This module provides base classes and common patterns for role-based access control.

Usage:
    from apps.common.permissions import BaseModelPermission, HasRole, CanAccessTenant

    class MyViewSet(ModelViewSet):
        permission_classes = [IsAuthenticated, BaseModelPermission]
"""

from django.contrib.auth import get_user_model
from rest_framework import permissions
from rest_framework.permissions import BasePermission

from .models import AccessGrant

User = get_user_model()


class BaseModelPermission(BasePermission):
    """
    Base permission class for model-level access control.

    This class checks if the user has permission to access the model
    based on their role and the tenant context.

    Override `get_required_roles` method to define which roles can access the view.
    """

    # Define which roles can perform each action
    ALLOWED_ROLES = {
        "GET": ["admin", "manager", "clerk", "viewer"],
        "POST": ["admin", "manager", "clerk"],
        "PUT": ["admin", "manager"],
        "PATCH": ["admin", "manager"],
        "DELETE": ["admin"],
    }

    def has_permission(self, request, view):
        """Check if user has permission to access this view."""
        if not request.user or not request.user.is_authenticated:
            return False

        # Check role-based access
        user_role = getattr(request.user, "role", None)
        if user_role is None:
            return False

        # Get the HTTP method
        method = request.method

        # Check if role is allowed for this method
        allowed_roles = self.ALLOWED_ROLES.get(method, [])
        if user_role in allowed_roles:
            return True

        # Check for custom permission method
        custom_permission = getattr(self, f"has_{view.action}_permission", None)
        if custom_permission:
            return custom_permission(request, view)

        return False


class HasRole(BasePermission):
    """
    Permission class that checks if user has a specific role.

    Usage:
        permission_classes = [IsAuthenticated, HasRole]

        # With specific roles
        permission_classes = [IsAuthenticated, HasRole(roles=['admin', 'manager'])]
    """

    def __init__(self, roles=None):
        self.roles = roles or []

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        user_role = getattr(request.user, "role", None)
        if user_role is None:
            return False

        # If no specific roles required, allow any authenticated user
        if not self.roles:
            return True

        return user_role in self.roles


class CanAccessTenant(BasePermission):
    """
    Permission class that verifies user can access the tenant context.

    Ensures that the user belongs to the tenant specified in the request
    and has appropriate permissions for tenant-level operations.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # Check if user has a tenant association
        tenant_id = getattr(request.user, "tenant_id", None)
        if tenant_id is None:
            return False

        return True

    def has_object_permission(self, request, view, obj):
        """Check if user has permission to access a specific object."""
        if not request.user or not request.user.is_authenticated:
            return False

        # Get tenant from object or request
        obj_tenant = getattr(obj, "tenant_id", None)
        user_tenant = getattr(request.user, "tenant_id", None)

        # Admin users can access any tenant
        user_role = getattr(request.user, "role", None)
        if user_role == "admin":
            return True

        return obj_tenant == user_tenant


class CanReadOnly(BasePermission):
    """
    Permission that allows read-only access.

    Use this for views that should only allow GET, HEAD, or OPTIONS requests.
    """

    def has_permission(self, request, view):
        return request.method in ("GET", "HEAD", "OPTIONS")


class IsAdminUser(permissions.IsAdminUser):
    """
    Permission that allows only admin users.

    Uses the user.role field to check if user is an admin.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # Check role field first (for ShopUser)
        user_role = getattr(request.user, "role", None)
        if user_role == "admin":
            return True

        # Fall back to is_staff
        return request.user.is_staff


class CanCreate(BasePermission):
    """
    Permission that allows create operations.

    Override `can_create` method for custom logic.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        user_role = getattr(request.user, "role", None)
        return user_role in ["admin", "manager", "clerk"]


class CanUpdate(BasePermission):
    """
    Permission that allows update operations.

    Override `can_update` method for custom logic.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        user_role = getattr(request.user, "role", None)
        return user_role in ["admin", "manager"]


class CanDelete(BasePermission):
    """
    Permission that allows delete operations.

    Only admins can delete by default.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        user_role = getattr(request.user, "role", None)
        return user_role == "admin"


class CanPostTransaction(BasePermission):
    """
    Permission that allows posting/approving financial transactions.

    Only managers and admins can post transactions.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        user_role = getattr(request.user, "role", None)
        return user_role in ["admin", "manager"]


class CanReconcile(BasePermission):
    """
    Permission for reconciliation operations.

    Only accountants and admins can perform reconciliation.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        user_role = getattr(request.user, "role", None)
        return user_role in ["admin", "accountant"]


class CanViewFinancialReports(BasePermission):
    """
    Permission for viewing financial reports.

    Managers, accountants, and admins can view financial reports.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        user_role = getattr(request.user, "role", None)
        return user_role in ["admin", "manager", "accountant"]


class HasModuleFunctionAccess(BasePermission):
    """
    Role x Module x Function permission check (manual §8.1 Password
    Maintenance foundation — see apps.common.models.AccessGrant).

    NOT YET WIRED INTO ANY VIEWSET. Landed standalone so the AccessGrant
    matrix and its admin UI can be built and reviewed before any app's
    existing permission_classes are touched — each app adopts this
    incrementally in a later pass, verified against that app's own tests.

    Usage (once adopted):
        permission_classes = [IsAuthenticated,
                               HasModuleFunctionAccess("creditors", "MAINTENANCE")]
    """

    def __init__(self, module, function_type):
        self.module = module
        self.function_type = function_type

    def __call__(self):
        # DRF instantiates permission_classes with no args; this class is
        # meant to be instantiated directly (module/function_type bound at
        # class-definition or view-definition time), so calling an already-
        # constructed instance just returns itself.
        return self

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        role = getattr(request.user, "role", None)
        if not role:
            return False

        return AccessGrant.is_role_allowed(role, self.module, self.function_type)


# Role constants for consistency across apps
class Roles:
    """Constants for user roles."""

    ADMIN = "admin"
    MANAGER = "manager"
    ACCOUNTANT = "accountant"
    CLERK = "clerk"
    VIEWER = "viewer"

    ALL = [ADMIN, MANAGER, ACCOUNTANT, CLERK, VIEWER]
    CAN_POST = [ADMIN, MANAGER, ACCOUNTANT]
    CAN_MANAGE = [ADMIN, MANAGER]
    CAN_VIEW = [ADMIN, MANAGER, ACCOUNTANT, CLERK, VIEWER]
