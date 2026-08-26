"""
General Ledger Module Permissions
Role-based access control for GL operations. Mirrors apps/cash_book/permissions.py's
role-tier pattern (Cashier < Accountant < Admin) — GL master accounts, transactions,
standing journals and spread sheets are core financial records, so create/update/
delete require an Accountant or Admin (or equivalent legacy group), while read
access (list/retrieve and the read-only summary/report actions) stays open to any
authenticated tenant user.
"""

from rest_framework import permissions


class CanManageGL(permissions.BasePermission):
    """
    Permission for GLMast/GLTran/GLStJnl/GLSpread write operations.

    Read (GET/HEAD/OPTIONS — list, retrieve, and the read-only report/summary
    actions) is allowed for any authenticated user. Create/update/delete
    require an ADMIN/MANAGER/ACCOUNTANT role or an equivalent group
    membership, matching the role/group check convention used by
    apps/debtors/permissions.py and apps/creditors/permissions.py.
    """

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False

        if request.method in permissions.SAFE_METHODS:
            return True

        return (
            request.user.is_superuser
            or (
                hasattr(request.user, "role")
                and request.user.role in ["ADMIN", "MANAGER", "ACCOUNTANT"]
            )
            or (
                hasattr(request.user, "groups")
                and request.user.groups.filter(
                    name__in=["Accountant", "Admin", "GLSupervisor"]
                ).exists()
            )
        )
