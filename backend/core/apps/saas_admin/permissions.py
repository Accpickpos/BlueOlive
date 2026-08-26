"""
SaaS Admin — Permission Classes

This app manages ALL tenants platform-wide (tenant CRUD, cross-tenant CSV
import, cross-tenant user management), so its endpoints must be restricted
to genuine platform superusers — not merely tenant-level staff.

Why not `rest_framework.permissions.IsAdminUser`:
    DRF's stock IsAdminUser only checks `request.user.is_staff`. In this
    codebase, ShopUser.save() (see shop_users/models.py) sets
    `self.is_staff = role in ("ADMIN", "MANAGER", "STAFF")` for ANY tenant
    employee above cashier level. That means a regular tenant staff member
    — from ANY tenant — satisfies the stock IsAdminUser check and could
    reach these cross-tenant, "superuser only" endpoints. Use
    IsPlatformSuperuser below instead, everywhere in this app.

Why not `apps.common.permissions.IsAdminUser`:
    That class checks `role == "admin"`, which is still a *tenant-level*
    admin check (any tenant's admin passes), not a *platform* superuser
    check. This app needs the latter since it operates across all tenants.
"""

from rest_framework import permissions


class IsPlatformSuperuser(permissions.BasePermission):
    """
    Allows access only to authenticated Django superusers, i.e. real
    platform/SaaS administrators (request.user.is_superuser=True) —
    as created via `createsuperuser_admin` / User.objects.create_superuser().

    Deliberately does NOT accept `is_staff` or any tenant `role` value:
    both are set on ordinary tenant employees and would let a regular
    (non-superuser) user from any tenant manage every other tenant.
    """

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_superuser
        )
