"""
SaaS Admin — Tenant Management API
Dedicated REST API for managing tenants and shops.
All endpoints require platform superuser (IsPlatformSuperuser) permission.
This API is completely separate from business logic APIs.
"""

from django.conf import settings
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from tenancy.models import Shop, Tenant

from .auth import PlatformOwnerJWTAuthentication
from .permissions import IsPlatformSuperuser
from .serializers import PlatformShopSerializer, PlatformTenantSerializer


class TenantViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing tenants.

    Provides CRUD operations for tenants.
    - LIST: Returns all tenants
    - RETRIEVE: Returns a single tenant by ID
    - CREATE: Creates a new tenant (auto-provisions database)
    - UPDATE/PARTIAL_UPDATE: Updates tenant details
    - DESTROY: Deactivates a tenant (soft delete)

    All operations require IsPlatformSuperuser permission.
    """

    authentication_classes = [PlatformOwnerJWTAuthentication]
    permission_classes = [IsPlatformSuperuser]
    queryset = Tenant.objects.all()
    serializer_class = PlatformTenantSerializer
    lookup_field = "id"

    def perform_update(self, serializer):
        """
        If this update grows enabled_addons (a platform owner turning an
        addon on for an already-provisioned tenant), retroactively migrate
        it into every existing shop of that tenant. Shrinking the set never
        un-migrates anything (destructive, not supported) - it only cuts off
        access via AddonAccessMiddleware / frontend nav.
        """
        old_addons = set(serializer.instance.enabled_addons or [])
        tenant = serializer.save()
        newly_enabled = set(tenant.enabled_addons or []) - old_addons

        if newly_enabled:
            from tenancy.tasks import provision_addon_async

            for addon in newly_enabled:
                provision_addon_async.delay(tenant.id, addon)

    def destroy(self, request, *args, **kwargs):
        """
        Soft delete a tenant by setting is_active to False.
        This preserves all data while preventing access.
        """
        tenant = self.get_object()
        tenant.is_active = False
        tenant.save()

        return Response(
            {"message": f'Tenant "{tenant.name}" has been deactivated.'},
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"])
    def activate(self, request, pk=None):
        """Activate a deactivated tenant."""
        tenant = self.get_object()
        tenant.is_active = True
        tenant.save()

        return Response(
            {"message": f'Tenant "{tenant.name}" has been activated.'},
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"])
    def deactivate(self, request, pk=None):
        """Deactivate a tenant (soft delete)."""
        tenant = self.get_object()
        tenant.is_active = False
        tenant.save()

        return Response(
            {"message": f'Tenant "{tenant.name}" has been deactivated.'},
            status=status.HTTP_200_OK,
        )


class ShopViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing shops under a tenant.

    Provides CRUD operations for shops.
    - LIST: Returns all shops (optionally filtered by tenant)
    - RETRIEVE: Returns a single shop by ID
    - CREATE: Creates a new shop (auto-provisions schema)
    - UPDATE/PARTIAL_UPDATE: Updates shop details
    - DESTROY: Deactivates a shop

    All operations require IsPlatformSuperuser permission.
    """

    authentication_classes = [PlatformOwnerJWTAuthentication]
    permission_classes = [IsPlatformSuperuser]
    queryset = Shop.objects.all()
    serializer_class = PlatformShopSerializer
    lookup_field = "id"

    def get_queryset(self):
        """Filter shops by tenant if tenant_id is provided."""
        queryset = Shop.objects.all()
        tenant_id = self.request.query_params.get("tenant_id")

        if tenant_id:
            queryset = queryset.filter(tenant_id=tenant_id)

        return queryset

    def create(self, request, *args, **kwargs):
        """
        Create a shop for an arbitrary tenant, given tenant_id in the body.

        ShopSerializer.create() (tenancy/serializers.py) reads the target
        tenant from tenant_context.get_current_tenant() - a thread-local
        that TenantMiddleware normally derives from the caller's own JWT/
        subdomain. The platform owner's JWT carries no tenant at all (see
        tenancy/platform_auth.py), so that thread-local would otherwise be
        None in production, or silently "the first active tenant" in DEBUG
        (see TenantMiddleware._handle_localhost) - neither of which is the
        tenant_id the owner actually asked for. Resolve it explicitly here
        instead of trusting whatever middleware guessed.
        """
        tenant_id = request.data.get("tenant_id")
        if not tenant_id:
            return Response(
                {"error": "tenant_id is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            tenant = Tenant.objects.get(id=tenant_id, is_active=True)
        except Tenant.DoesNotExist:
            return Response(
                {"error": f"Tenant with id {tenant_id} not found or inactive"},
                status=status.HTTP_404_NOT_FOUND,
            )

        from tenancy.tenant_context import set_current_tenant
        from tenancy.utils import register_tenant_connection

        register_tenant_connection(tenant)
        set_current_tenant(tenant)

        return super().create(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """
        Soft delete a shop by setting is_active to False.
        """
        shop = self.get_object()
        shop.is_active = False
        shop.save()

        return Response(
            {"message": f'Shop "{shop.name}" has been deactivated.'},
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"])
    def activate(self, request, pk=None):
        """Activate a deactivated shop."""
        shop = self.get_object()
        shop.is_active = True
        shop.save()

        return Response(
            {"message": f'Shop "{shop.name}" has been activated.'},
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"])
    def deactivate(self, request, pk=None):
        """Deactivate a shop (soft delete)."""
        shop = self.get_object()
        shop.is_active = False
        shop.save()

        return Response(
            {"message": f'Shop "{shop.name}" has been deactivated.'},
            status=status.HTTP_200_OK,
        )


class TenantStatsViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for getting tenant statistics.

    Provides read-only statistics about tenants and shops.
    - LIST: Returns summary statistics for all tenants
    - RETRIEVE: Returns statistics for a specific tenant
    """

    authentication_classes = [PlatformOwnerJWTAuthentication]
    permission_classes = [IsPlatformSuperuser]
    queryset = Tenant.objects.all()
    lookup_field = "id"

    def list(self, request):
        """Get overall tenant statistics."""
        total_tenants = Tenant.objects.count()
        active_tenants = Tenant.objects.filter(is_active=True).count()
        inactive_tenants = total_tenants - active_tenants
        total_shops = Shop.objects.count()
        active_shops = Shop.objects.filter(is_active=True).count()

        return Response(
            {
                "total_tenants": total_tenants,
                "active_tenants": active_tenants,
                "inactive_tenants": inactive_tenants,
                "total_shops": total_shops,
                "active_shops": active_shops,
            }
        )

    def retrieve(self, request, id=None):
        """Get statistics for a specific tenant."""
        tenant = self.get_object()

        shops = tenant.shops.all()
        total_shops = shops.count()
        active_shops = shops.filter(is_active=True).count()

        return Response(
            {
                "tenant_id": tenant.id,
                "tenant_name": tenant.name,
                "tenant_slug": tenant.slug,
                "tenant_is_active": tenant.is_active,
                "total_shops": total_shops,
                "active_shops": active_shops,
                "created_at": tenant.created_at,
            }
        )
