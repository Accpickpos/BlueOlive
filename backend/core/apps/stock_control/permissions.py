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
        return getattr(request.user, "role", None) in (
            "CASHIER",
            "MANAGER",
            "ACCOUNTANT",
            "ADMIN",
        )


class IsStockAccountant(permissions.BasePermission):
    """Required for branch-transfer invoicing actions (issue / mark_paid)."""

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        return getattr(request.user, "role", None) in ("MANAGER", "ACCOUNTANT", "ADMIN")


class StockConsolidationEnabledMixin:
    """
    Gates every action on a ViewSet behind Tenant.enable_stock_consolidation.

    Unlike the whole-app OPTIONAL_ADDON_APPS toggle (enforced at the URL
    layer by tenancy.middleware.AddonAccessMiddleware), Stock Consolidation
    (inter-branch transfers) is a sub-feature of the mandatory stock_control
    app, so it's gated per-ViewSet instead. Overrides check_permissions
    (not permission_classes) so it still applies to @action methods that
    declare their own permission_classes (e.g. approve/dispatch/receive),
    which would otherwise bypass a class-level permission_classes entry.
    """

    def check_permissions(self, request):
        super().check_permissions(request)
        tenant = getattr(request, "tenant", None)
        if not getattr(tenant, "enable_stock_consolidation", True):
            self.permission_denied(
                request,
                message="Stock Consolidation (inter-branch transfers) is disabled for this account.",
                code="stock_consolidation_disabled",
            )
