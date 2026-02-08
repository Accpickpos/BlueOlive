"""
Cash Book Module Permissions
Role-based access control for cash book operations
"""
from rest_framework import permissions
from typing import List


class CashBookPermission(permissions.BasePermission):
    """Base permission for cash book operations"""
    
    def has_permission(self, request, view):
        """Check if user is authenticated"""
        return bool(request.user and request.user.is_authenticated)


class IsCashier(permissions.BasePermission):
    """Permission for cashier role - can create and view transactions"""
    
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        
        return hasattr(request.user, 'groups') and \
               request.user.groups.filter(name__in=['Cashier', 'Accountant', 'Admin']).exists()


class IsAccountant(permissions.BasePermission):
    """Permission for accountant role - can create, view, and reconcile"""
    
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        
        return hasattr(request.user, 'groups') and \
               request.user.groups.filter(name__in=['Accountant', 'Admin']).exists()


class IsAdmin(permissions.BasePermission):
    """Permission for admin role - full access"""
    
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        
        return request.user.is_staff and request.user.is_superuser


class CanViewTransactions(permissions.BasePermission):
    """Permission to view transactions - read-only"""
    
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        
        # All authenticated users can view
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Only cashier and above can create/edit
        return hasattr(request.user, 'groups') and \
               request.user.groups.filter(name__in=['Cashier', 'Accountant', 'Admin']).exists()


class CanCreateTransactions(permissions.BasePermission):
    """Permission to create transactions"""
    
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        
        # Read operations allowed for all authenticated users
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Create/Edit operations require cashier role or higher
        return hasattr(request.user, 'groups') and \
               request.user.groups.filter(name__in=['Cashier', 'Accountant', 'Admin']).exists()


class CanReconcile(permissions.BasePermission):
    """Permission to perform reconciliation - accountant only"""
    
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        
        # Read operations allowed for all authenticated users
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Reconciliation operations require accountant role or higher
        return hasattr(request.user, 'groups') and \
               request.user.groups.filter(name__in=['Accountant', 'Admin']).exists()


class CanModifyReconciledTransactions(permissions.BasePermission):
    """Permission to modify reconciled transactions - admin only"""
    
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        
        # Read operations allowed for all authenticated users
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Modification of reconciled transactions requires admin
        return request.user.is_staff and request.user.is_superuser
    
    def has_object_permission(self, request, view, obj):
        """Check object-level permission"""
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # If transaction is reconciled, only admin can modify
        if hasattr(obj, 'is_reconciled') and obj.is_reconciled:
            return request.user.is_staff and request.user.is_superuser
        
        # If transaction has reconciliation parent, check parent
        if hasattr(obj, 'transaction') and hasattr(obj.transaction, 'is_reconciled'):
            if obj.transaction.is_reconciled:
                return request.user.is_staff and request.user.is_superuser
        
        return True


def get_user_role(user) -> str:
    """
    Get the highest permission role for a user.
    
    Returns: 'admin', 'accountant', 'cashier', 'viewer', or 'none'
    """
    if not user or not user.is_authenticated:
        return 'none'
    
    if user.is_staff and user.is_superuser:
        return 'admin'
    
    if not hasattr(user, 'groups'):
        return 'none'
    
    group_names = list(user.groups.values_list('name', flat=True))
    
    if 'Accountant' in group_names:
        return 'accountant'
    
    if 'Cashier' in group_names:
        return 'cashier'
    
    if 'Viewer' in group_names:
        return 'viewer'
    
    return 'none'


def get_user_permissions(user) -> List[str]:
    """
    Get list of all permissions for a user.
    
    Returns: List of permission strings
    """
    role = get_user_role(user)
    
    permissions_map = {
        'admin': [
            'view_transactions',
            'create_transactions',
            'edit_transactions',
            'delete_transactions',
            'reconcile',
            'archive',
            'view_reports',
            'manage_users',
        ],
        'accountant': [
            'view_transactions',
            'create_transactions',
            'edit_transactions',
            'reconcile',
            'view_reports',
        ],
        'cashier': [
            'view_transactions',
            'create_transactions',
            'edit_transactions',
        ],
        'viewer': [
            'view_transactions',
            'view_reports',
        ],
        'none': [],
    }
    
    return permissions_map.get(role, [])
