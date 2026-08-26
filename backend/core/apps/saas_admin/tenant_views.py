"""
SaaS Admin — Tenant Management API
Dedicated REST API for managing tenants and shops.
All endpoints require platform superuser (IsPlatformSuperuser) permission.
This API is completely separate from business logic APIs.
"""

from django.conf import settings
from rest_framework import status, viewsets
from rest_framework.response import Response
from tenancy.models import Shop, Tenant
from tenancy.serializers import TenantSerializer

from .permissions import IsPlatformSuperuser


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

    permission_classes = [IsPlatformSuperuser]
    queryset = Tenant.objects.all()
    serializer_class = TenantSerializer
    lookup_field = "id"

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

    def activate(self, request, pk=None):
        """Activate a deactivated tenant."""
        tenant = self.get_object()
        tenant.is_active = True
        tenant.save()

        return Response(
            {"message": f'Tenant "{tenant.name}" has been activated.'},
            status=status.HTTP_200_OK,
        )

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

    permission_classes = [IsPlatformSuperuser]
    queryset = Shop.objects.all()
    lookup_field = "id"

    def get_serializer_class(self):
        """Use the Tenant serializer for Shop model."""
        from tenancy.serializers import ShopSerializer

        return ShopSerializer

    def get_queryset(self):
        """Filter shops by tenant if tenant_id is provided."""
        queryset = Shop.objects.all()
        tenant_id = self.request.query_params.get("tenant_id")

        if tenant_id:
            queryset = queryset.filter(tenant_id=tenant_id)

        return queryset

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

    def activate(self, request, pk=None):
        """Activate a deactivated shop."""
        shop = self.get_object()
        shop.is_active = True
        shop.save()

        return Response(
            {"message": f'Shop "{shop.name}" has been activated.'},
            status=status.HTTP_200_OK,
        )

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
