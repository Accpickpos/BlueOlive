from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from .models import Tenant, Shop
from .serializers import TenantSerializer, ShopSerializer
from tenancy.tenant_context import get_current_tenant
from tenancy.permissions import IsAdmin, IsTenantMember, CanCreateTenant

@api_view(['GET'])
def current_tenant(request):
    host = request.get_host().split(":")[0]
    parts = host.split(".")
    if len(parts) > 2:
        subdomain = parts[0]
    elif len(parts) == 2 and parts[1] == "localhost":
        subdomain = parts[0]
    else:
        subdomain = None

    tenant_key = request.headers.get("X-Tenant") or subdomain
    if tenant_key:
        tenant = None
        try:
            tenant = Tenant.objects.get(slug=tenant_key)
        except Tenant.DoesNotExist:
            # Try to find by shop name
            try:
                shop = Shop.objects.get(name=tenant_key)
                tenant = shop.tenant
            except Shop.DoesNotExist:
                pass
        if tenant:
            return Response({'name': tenant.name, 'slug': tenant.slug})
    return Response({'tenant': None})

@api_view(['GET'])
def tenant_shops(request):
    tenant = get_current_tenant()
    if tenant:
        shops = tenant.shops.all().values('id', 'name')
        return Response(list(shops))
    return Response([])

@api_view(['GET'])
def all_shops(request):
    """
    Public endpoint to list all shops with their subdomains.
    Used for the "Find Your Shop" page.
    No authentication required.
    """
    try:
        # Get all tenants with their shops
        shops_data = []
        tenants = Tenant.objects.prefetch_related('shops').all()
        
        for tenant in tenants:
            for shop in tenant.shops.all():
                shops_data.append({
                    'id': shop.id,
                    'name': shop.name,
                    'subdomain': tenant.slug,  # Use tenant slug as subdomain
                })
        
        return Response(shops_data)
    except Exception as e:
        return Response({'error': str(e)}, status=400)

class TenantViewSet(viewsets.ModelViewSet):
    queryset = Tenant.objects.all()
    serializer_class = TenantSerializer
    permission_classes = [IsAdmin]

    def get_permissions(self):
        """
        Only superusers can create, modify, or delete tenants.
        Regular authenticated users can view their own tenant.
        """
        if self.action == 'create':
            return [CanCreateTenant()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [IsAdmin()]
        else:  # list, retrieve
            return [permissions.IsAuthenticated]

    # perform_create removed since serializer.create handles user creation


class ShopViewSet(viewsets.ModelViewSet):
    serializer_class = ShopSerializer
    permission_classes = [IsTenantMember]

    def get_queryset(self):
        """
        Only show shops from the current tenant.
        Superusers can see all shops.
        """
        tenant = get_current_tenant()
        if tenant:
            return Shop.objects.filter(tenant=tenant)
        return Shop.objects.none()
    
    def get_permissions(self):
        """
        Enforce tenant membership and role-based permissions:
        - create: Admin only
        - update/delete: Admin only
        - list/retrieve: All tenant members
        """
        from tenancy.permissions import IsAdmin
        
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdmin()]
        else:
            return [IsTenantMember()]


# ============================================================================
# SUPERUSER TENANT MANAGEMENT ENDPOINTS
# ============================================================================

class TenantManagementViewSet(viewsets.ModelViewSet):
    """
    Superuser-only API for managing all tenants.
    Only Django superusers can access these endpoints.
    """
    queryset = Tenant.objects.all()
    serializer_class = TenantSerializer
    permission_classes = [IsAdminUser]  # Must be Django superuser
    
    def get_queryset(self):
        """Superusers see all tenants."""
        return Tenant.objects.all()
    
    def create(self, request, *args, **kwargs):
        """Create a new tenant."""
        if not request.user.is_superuser:
            return Response(
                {'detail': 'Only superusers can create tenants.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().create(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """Delete a tenant."""
        if not request.user.is_superuser:
            return Response(
                {'detail': 'Only superusers can delete tenants.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)


@api_view(['GET', 'POST'])
@permission_classes([IsAdminUser])
def superuser_dashboard(request):
    """
    Superuser dashboard: Get statistics about all tenants.
    """
    if not request.user.is_superuser:
        return Response(
            {'detail': 'Only superusers can access this.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Get tenant statistics
    tenant_count = Tenant.objects.count()
    shop_count = Shop.objects.count()
    active_tenants = Tenant.objects.filter(is_active=True).count()
    
    return Response({
        'user': request.user.username,
        'is_superuser': True,
        'total_tenants': tenant_count,
        'active_tenants': active_tenants,
        'total_shops': shop_count,
        'tenants': TenantSerializer(
            Tenant.objects.all(),
            many=True
        ).data
    })


@api_view(['POST'])
@permission_classes([IsAdminUser])
def create_tenant_and_shop(request):
    """
    Superuser endpoint to create a tenant and its first shop in one go.
    
    Request body:
    {
        "tenant_name": "ACME Corporation",
        "tenant_subdomain": "acme",
        "shop_name": "Main Store",
        "shop_code": "MAIN"
    }
    """
    if not request.user.is_superuser:
        return Response(
            {'detail': 'Only superusers can create tenants.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    tenant_name = request.data.get('tenant_name')
    subdomain = request.data.get('tenant_subdomain')
    shop_name = request.data.get('shop_name')
    shop_code = request.data.get('shop_code')
    
    if not all([tenant_name, subdomain, shop_name, shop_code]):
        return Response(
            {'detail': 'Missing required fields.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Create tenant
        tenant = Tenant.objects.create(
            name=tenant_name,
            slug=subdomain
        )
        
        # Create shop
        shop = Shop.objects.create(
            tenant=tenant,
            name=shop_name,
            schema_name=f"{subdomain}_shop",
            subdomain=subdomain,
            shop_code=shop_code
        )
        
        return Response({
            'status': 'success',
            'tenant': TenantSerializer(tenant).data,
            'shop': ShopSerializer(shop).data
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response(
            {'detail': f'Error creating tenant: {str(e)}'},
            status=status.HTTP_400_BAD_REQUEST
        )

