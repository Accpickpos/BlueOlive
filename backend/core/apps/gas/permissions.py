"""
Gas Module Permissions
Mirrors apps/cash_book/permissions.py's role-tier pattern (Cashier < Accountant < Admin).

Writing off a deposit or flagging a dispute forgives money owed to the shop —
gated behind Accountant/Admin so a cashier can't unilaterally do it.
Refunds and billed-for-replacement (a real, VAT-charged sale) only need Cashier.
"""

from rest_framework import permissions

# Per-tenant enable/disable for the whole gas app is enforced at the URL
# layer by tenancy.middleware.AddonAccessMiddleware (settings.OPTIONAL_ADDON_APPS
# / Tenant.enabled_addons), not here — a request never reaches these viewsets
# at all if 'gas' isn't enabled for the tenant. This used to be a
# GasFeatureEnabled permission class reading the never-populated
# SubscriptionPlan.features['gas'] (dead: no signup path ever creates a
# Subscription row, so it always defaulted to allowed) — replaced rather than
# left alongside the real mechanism.


class IsGasCashier(permissions.BasePermission):
    """Can create checkouts and process refunded / billed_for_replacement returns."""

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        return (
            hasattr(request.user, "groups")
            and request.user.groups.filter(
                name__in=["Cashier", "Accountant", "Admin"]
            ).exists()
        )


class IsGasAccountant(permissions.BasePermission):
    """Required for written_off and disputed reconciliation states."""

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        return (
            hasattr(request.user, "groups")
            and request.user.groups.filter(name__in=["Accountant", "Admin"]).exists()
        )


# Reconciliation states that require IsGasAccountant instead of IsGasCashier.
ACCOUNTANT_GATED_STATES = frozenset({"WRITTEN_OFF", "DISPUTED"})
