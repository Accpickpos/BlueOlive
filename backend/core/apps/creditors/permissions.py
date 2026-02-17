"""
Custom permissions for creditors app.
Role-based access control for sensitive operations.
Allows MANAGER and ADMIN roles to maintain and update creditor data.
"""
from rest_framework import permissions


class HasCreditorPermission(permissions.BasePermission):
    """
    Permission class to check if user has access to creditor data.
    All authenticated users can read
    MANAGER and ADMIN can modify.
    """
    
    def has_permission(self, request, view):
        """Check if user is authenticated and authorized."""
        # Must be authenticated
        if not request.user or not request.user.is_authenticated:
            return False
        
        # GET requests allowed for authenticated users
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # POST/PUT/DELETE requires MANAGER or ADMIN role
        return (
            request.user.is_superuser or
            (hasattr(request.user, 'role') and request.user.role in ['ADMIN', 'MANAGER']) or
            request.user.groups.filter(name__in=['creditors_admin', 'creditors_manager', 'admin']).exists()
        )
    
    def has_object_permission(self, request, view, obj):
        """Check if user has permission to access specific creditor."""
        if not request.user or not request.user.is_authenticated:
            return False
        
        # GET requests allowed for authenticated users
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Modifications require MANAGER or ADMIN
        return (
            request.user.is_superuser or
            (hasattr(request.user, 'role') and request.user.role in ['ADMIN', 'MANAGER']) or
            request.user.groups.filter(name__in=['creditors_admin', 'creditors_manager', 'admin']).exists()
        )


class CanModifyCreditor(permissions.BasePermission):
    """
    Permission to modify creditor (block/unblock, change credit limit, etc).
    Allows MANAGER and ADMIN roles.
    """
    
    def has_permission(self, request, view):
        """Check if user can modify creditors."""
        if not request.user or not request.user.is_authenticated:
            return False
        
        # ADMIN and MANAGER roles can modify creditors
        return (
            request.user.is_superuser or
            (hasattr(request.user, 'role') and request.user.role in ['ADMIN', 'MANAGER']) or
            request.user.groups.filter(name__in=['creditors_admin', 'creditors_manager', 'admin']).exists()
        )


class CanReceiveGoods(permissions.BasePermission):
    """
    Permission to receive goods (Goods Received Note creation).
    Allows MANAGER and ADMIN roles.
    """
    
    def has_permission(self, request, view):
        """Check if user can receive goods."""
        if not request.user or not request.user.is_authenticated:
            return False
        
        # ADMIN and MANAGER can create GRNs
        return (
            request.user.is_superuser or
            (hasattr(request.user, 'role') and request.user.role in ['ADMIN', 'MANAGER']) or
            request.user.groups.filter(name__in=['creditors_admin', 'creditors_manager', 'purchasing', 'admin']).exists()
        )


class CanPostCreditorInvoice(permissions.BasePermission):
    """
    Permission to post creditor invoices (financial operation).
    Allows MANAGER and ADMIN roles.
    """
    
    def has_permission(self, request, view):
        """Check if user can post invoices."""
        if not request.user or not request.user.is_authenticated:
            return False
        
        # ADMIN and MANAGER roles can post creditor invoices
        return (
            request.user.is_superuser or
            (hasattr(request.user, 'role') and request.user.role in ['ADMIN', 'MANAGER']) or
            request.user.groups.filter(name__in=['invoicing', 'creditors_admin', 'creditors_manager', 'admin']).exists()
        )


class CanPostCreditorPayment(permissions.BasePermission):
    """
    Permission to post creditor payments (financial operation).
    Allows MANAGER and ADMIN roles.
    """
    
    def has_permission(self, request, view):
        """Check if user can post payments."""
        if not request.user or not request.user.is_authenticated:
            return False
        
        # ADMIN and MANAGER roles can post payments
        return (
            request.user.is_superuser or
            (hasattr(request.user, 'role') and request.user.role in ['ADMIN', 'MANAGER']) or
            request.user.groups.filter(name__in=['finance', 'creditors_admin', 'creditors_manager', 'admin']).exists()
        )


class CanReconcileCreditor(permissions.BasePermission):
    """
    Permission to reconcile creditor accounts (match invoices to receipts).
    Allows MANAGER and ADMIN roles.
    """
    
    def has_permission(self, request, view):
        """Check if user can reconcile accounts."""
        if not request.user or not request.user.is_authenticated:
            return False
        
        # ADMIN and MANAGER can reconcile
        return (
            request.user.is_superuser or
            (hasattr(request.user, 'role') and request.user.role in ['ADMIN', 'MANAGER']) or
            request.user.groups.filter(name__in=['finance', 'creditors_admin', 'creditors_manager', 'admin']).exists()
        )
