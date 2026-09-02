"""
POS Module Permissions
Role-based access control for point-of-sale operations.

Mirrors apps/cash_book/permissions.py's role-tier pattern (Cashier <
Accountant < Admin) and apps/gas/permissions.py's IsGasCashier /
IsGasAccountant group-checking convention.

Normal POS usage (list/retrieve/create/update — ringing up a sale, taking
a laybye deposit, raising a quotation, posting an invoice) stays open to
any authenticated user, exactly as it behaved before this module had any
permission classes at all. Only actions that reverse or destroy a
transaction already recorded as money taken or owed — cancelling/voiding/
deleting a CashSale, Invoice, Laybye, Quotation, CreditNote, CashReturn,
Cash-a-Cheque or Receipt on Account, or clearing a CashControl record —
are gated behind an Accountant/Admin role tier below. This keeps the fix
scoped to "add the missing elevated tier for sensitive state-changing
actions" without breaking day-to-day cashier usage that previously had no
group requirement at all.
"""

from rest_framework import permissions


class IsPOSAccountant(permissions.BasePermission):
    """
    Required for state-reversing POS actions: cancel/void/destroy a
    transaction, or clear a CashControl record. A cashier can ring up and
    view transactions, but unwinding money already taken/owed needs an
    Accountant or Admin — mirrors cash_book.permissions.IsAccountant /
    CanReconcile and gas.permissions.IsGasAccountant.
    """

    message = "Only an Accountant or Admin can perform this action."

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        return getattr(request.user, "role", None) in ("MANAGER", "ACCOUNTANT", "ADMIN")


# Actions — both the default ModelViewSet "destroy" and the various
# custom @action names used across pos/views.py — that reverse or destroy
# an already-recorded transaction and therefore need IsPOSAccountant
# rather than plain IsAuthenticated.
ELEVATED_ACTIONS = frozenset(
    {
        "destroy",
        "cancel",
        "cancel_sale",
        "cancel_laybye",
        "void",
        "clear",
    }
)


class POSPermissionMixin:
    """
    Mix into a POS ViewSet ahead of viewsets.ModelViewSet (or
    ReadOnlyModelViewSet): routes ELEVATED_ACTIONS (cancel/void/destroy/
    clear) through IsAuthenticated + IsPOSAccountant; every other action
    keeps using the ViewSet's own `permission_classes` (IsAuthenticated)
    unchanged, so ordinary create/list/retrieve/update for authenticated
    cashiers is not affected.
    """

    def get_permissions(self):
        if getattr(self, "action", None) in ELEVATED_ACTIONS:
            return [permissions.IsAuthenticated(), IsPOSAccountant()]
        return super().get_permissions()
