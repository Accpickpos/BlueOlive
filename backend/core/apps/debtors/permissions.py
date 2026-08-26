"""
Custom permissions for debtors app.
Role-based access control for sensitive operations.
"""

from rest_framework import permissions


class HasDebtorPermission(permissions.BasePermission):
    """
    Permission class to check if user has access to debtor data.
    Override in specific implementations for tenant isolation.
    """

    def has_permission(self, request, view):
        """Check if user is authenticated and authorized."""
        # Must be authenticated
        if not request.user or not request.user.is_authenticated:
            return False

        # GET requests allowed for authenticated users
        if request.method in permissions.SAFE_METHODS:
            return True

        # POST/PUT/DELETE requires additional checks
        # This should be extended to check user roles/groups
        # Example: return request.user.groups.filter(name='debtors_manager').exists()
        return True

    def has_object_permission(self, request, view, obj):
        """Check if user has permission to access specific debtor."""
        if not request.user or not request.user.is_authenticated:
            return False

        # This is where you'd add tenant isolation
        # Example: return obj.tenant == request.user.tenant
        return True


class CanModifyDebtor(permissions.BasePermission):
    """
    Permission to modify debtor (block/unblock, change credit limit, etc).
    Allows MANAGER and ADMIN roles.
    """

    def has_permission(self, request, view):
        """Check if user can modify debtors."""
        if not request.user or not request.user.is_authenticated:
            return False

        # ADMIN and MANAGER roles can modify debtors
        # Also check for legacy group-based permissions
        return (
            request.user.is_superuser
            or (
                hasattr(request.user, "role")
                and request.user.role in ["ADMIN", "MANAGER"]
            )
            or request.user.groups.filter(
                name__in=["debtors_admin", "admin", "debtors_manager"]
            ).exists()
        )


class CanPostInvoice(permissions.BasePermission):
    """
    Permission to post invoices (financial operation).
    Allows ADMIN and MANAGER roles.
    """

    def has_permission(self, request, view):
        """Check if user can post invoices."""
        if not request.user or not request.user.is_authenticated:
            return False

        # ADMIN and MANAGER roles can post invoices
        return (
            request.user.is_superuser
            or (
                hasattr(request.user, "role")
                and request.user.role in ["ADMIN", "MANAGER"]
            )
            or request.user.groups.filter(
                name__in=["invoicing", "debtors_admin", "debtors_manager", "admin"]
            ).exists()
        )


class CanChargeInterest(permissions.BasePermission):
    """
    Permission to charge interest (finance operation).
    Usually restricted to MANAGER and ADMIN roles.
    """

    def has_permission(self, request, view):
        """Check if user can charge interest."""
        if not request.user or not request.user.is_authenticated:
            return False

        # ADMIN and MANAGER can charge interest
        return (
            request.user.is_superuser
            or (
                hasattr(request.user, "role")
                and request.user.role in ["ADMIN", "MANAGER"]
            )
            or request.user.groups.filter(
                name__in=["finance", "debtors_admin", "debtors_manager", "admin"]
            ).exists()
        )


class CanAgeBalances(permissions.BasePermission):
    """
    Permission to run month-end aging process.
    Usually restricted to finance managers.
    """

    def has_permission(self, request, view):
        """Check if user can age balances."""
        if not request.user or not request.user.is_authenticated:
            return False

        # This is a critical operation - restrict to superusers and finance
        return (
            request.user.is_superuser
            or request.user.groups.filter(name__in=["finance", "admin"]).exists()
        )
