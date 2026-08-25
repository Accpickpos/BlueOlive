"""
Rentals Module Permissions
Mirrors apps/cash_book/permissions.py's role-tier pattern (Cashier < Accountant < Admin).

Writing off a deposit or flagging a dispute forgives money owed to the shop —
gated behind Accountant/Admin so a cashier can't unilaterally do it.
Refunds and billed-for-replacement (a real, VAT-charged sale) only need Cashier.
"""
from rest_framework import permissions

from tenancy.tenant_context import get_current_tenant


class RentalsFeatureEnabled(permissions.BasePermission):
    """
    Per-tenant kill switch (T10, /plan-ceo-review Section 1) — gates the whole
    rentals app behind SubscriptionPlan.features['rentals'], so a bad pilot
    bug can be disabled for one tenant without a redeploy affecting anyone
    else. Mirrors the existing plan.features.get('pos') pattern
    (tenancy/management/commands/seed_subscriptions.py:196).
    """
    message = "Rentals is not enabled for this account."

    def has_permission(self, request, view):
        tenant = get_current_tenant()
        if not tenant:
            return False
        subscription = getattr(tenant, 'subscription', None)
        if not subscription or not subscription.plan:
            # No billing system is wired into signup yet (no code path ever
            # creates a Subscription row), so every tenant is in this state.
            # Treat it like every other SubscriptionPlan.features flag in the
            # codebase, which is defined but never actually enforced anywhere.
            return True
        return bool(subscription.plan.features.get('rentals', False))


class IsRentalCashier(permissions.BasePermission):
    """Can create checkouts and process refunded / billed_for_replacement returns."""

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        return hasattr(request.user, 'groups') and \
            request.user.groups.filter(name__in=['Cashier', 'Accountant', 'Admin']).exists()


class IsRentalAccountant(permissions.BasePermission):
    """Required for written_off and disputed reconciliation states."""

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        return hasattr(request.user, 'groups') and \
            request.user.groups.filter(name__in=['Accountant', 'Admin']).exists()


# Reconciliation states that require IsRentalAccountant instead of IsRentalCashier.
ACCOUNTANT_GATED_STATES = frozenset({'WRITTEN_OFF', 'DISPUTED'})
