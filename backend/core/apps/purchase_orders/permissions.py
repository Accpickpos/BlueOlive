"""
Purchase Orders Module Permissions
Mirrors apps/gas/permissions.py's role-tier pattern (Cashier < Accountant < Admin).

Receiving stock against a PO (and reversing on-order quantities on cancel)
moves physical stock and, when update_supplier_account is set, commits a
supplier account balance — gated a tier above plain IsAuthenticated so a
regular authenticated user can't move stock or supplier balances just by
knowing the endpoint.
"""

from rest_framework import permissions


class IsPurchaseOrderStockMover(permissions.BasePermission):
    """Required for actions that move physical stock or on-order quantities."""

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        return getattr(request.user, "role", None) in (
            "CASHIER",
            "MANAGER",
            "ACCOUNTANT",
            "ADMIN",
        )


class IsPurchaseOrderAdmin(permissions.BasePermission):
    """
    Required for utilities that bulk-recompute data across every stock item
    (e.g. resyncing on-order quantities) rather than acting on a single order —
    gated to Admin only, one tier above IsPurchaseOrderStockMover.
    """

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        return getattr(request.user, "role", None) == "ADMIN"
