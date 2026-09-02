"""
SaaS Admin — serializers.

Kept separate from tenancy.serializers (used by tenants' own self-service
TenantViewSet/ShopViewSet) so that fields only relevant cross-tenant
(is_active, tenant/tenant_name) can never leak into what a tenant admin can
read/write about their own tenant or shop records.
"""

from django.conf import settings
from rest_framework import serializers
from tenancy.serializers import ShopSerializer, TenantSerializer


class PlatformTenantSerializer(TenantSerializer):
    """
    TenantSerializer plus is_active and enabled_addons, for the
    platform-owner API only. enabled_addons is where a tenant's optional
    addons (cash_book/general_ledger/gas/stockfinder) actually get toggled -
    see TenantViewSet.perform_update, which provisions any newly-enabled
    addon into the tenant's existing shops.
    """

    class Meta(TenantSerializer.Meta):
        fields = TenantSerializer.Meta.fields + ["is_active", "enabled_addons"]

    def validate_enabled_addons(self, value):
        allowed = set(getattr(settings, "OPTIONAL_ADDON_APPS", []))
        enabled = set(value or [])
        unknown = enabled - allowed
        if unknown:
            raise serializers.ValidationError(
                f"Unknown addon(s): {sorted(unknown)}. Must be a subset of {sorted(allowed)}."
            )

        dependencies = getattr(settings, "ADDON_DEPENDENCIES", {})
        for addon, required in dependencies.items():
            if addon in enabled:
                missing = [r for r in required if r not in enabled]
                if missing:
                    raise serializers.ValidationError(
                        f"Addon '{addon}' requires {missing} to also be enabled."
                    )
        return value


class PlatformShopSerializer(ShopSerializer):
    """
    ShopSerializer plus tenant/tenant_name, for the platform-owner API only,
    which lists/creates shops across every tenant (unlike the tenant
    self-service ShopViewSet, which is always scoped to the caller's own
    tenant and has no need to name it).
    """

    tenant = serializers.IntegerField(source="tenant_id", read_only=True)
    tenant_name = serializers.CharField(source="tenant.name", read_only=True)

    class Meta(ShopSerializer.Meta):
        fields = ShopSerializer.Meta.fields + ["tenant", "tenant_name"]
