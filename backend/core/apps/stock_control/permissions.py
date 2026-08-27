"""
Stock Control Module Permissions
Mirrors apps/gas/permissions.py's role-tier pattern (Cashier < Accountant < Admin).

Manual stock adjustments, stock-take application, and branch transfers all
move physical stock between/within shops — gated a tier above plain
IsAuthenticated. Branch transfer invoicing (issue/mark_paid) commits an
inter-branch financial obligation, so it's gated one tier higher still.
"""

from rest_framework import permissions


class IsStockMover(permissions.BasePermission):
    """Required for actions that move physical stock quantities."""

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        return (
            hasattr(request.user, "groups")
            and request.user.groups.filter(
                name__in=["Cashier", "Accountant", "Admin"]
            ).exists()
        )


class IsStockAccountant(permissions.BasePermission):
    """Required for branch-transfer invoicing actions (issue / mark_paid)."""

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        return (
            hasattr(request.user, "groups")
            and request.user.groups.filter(name__in=["Accountant", "Admin"]).exists()
        )
