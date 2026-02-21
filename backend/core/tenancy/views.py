from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from .models import Tenant, Shop
from .serializers import TenantSerializer, ShopSerializer
from tenancy.tenant_context import get_current_tenant
from tenancy.permissions import IsAdmin, IsTenantMember, CanCreateTenant
import logging

logger = logging.getLogger(__name__)

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

    def get_serializer_class(self):
        """
        Use TenantSerializer for creation with password validation.
        Use TenantListSerializer for read operations (no password field).
        """
        from tenancy.serializers import TenantListSerializer
        if self.action in ['create', 'update', 'partial_update']:
            return TenantSerializer  # Include password field for creation/update
        return TenantListSerializer  # Exclude password for read operations

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
            # Query from public database, not tenant database
            return Shop.objects.using('default').filter(tenant=tenant)
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

    @action(detail=True, methods=['get'], permission_classes=[IsTenantMember])
    def check_setup_status(self, request, pk=None):
        """
        Check the setup status of a shop.
        Returns the current setup status: 'pending', 'ready', or 'failed'.
        """
        shop = self.get_object()
        return Response({
            'id': shop.id,
            'name': shop.name,
            'setup_status': shop.setup_status,
            'is_ready': shop.setup_status == 'ready',
            'message': {
                'pending': 'Shop is being set up. This may take a few moments...',
                'ready': 'Shop is ready for use!',
                'failed': 'Shop setup failed. Please contact support.',
            }.get(shop.setup_status, 'Unknown status')
        })

    def get_serializer_class(self):
        """
        Use ShopSerializer for all operations.
        ShopSerializer is lightweight for list/retrieve and comprehensive for create/update.
        """
        # ShopSerializer works for all actions - no need for separate serializers
        return ShopSerializer


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


# =============================================================================
# Shop Switching Views - Multi-Shop User Management
# =============================================================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def switch_shop(request):
    """
    Allow users to switch between their accessible shops.
    
    Request body:
        {
            "shop_id": 123
        }
    
    Returns:
        Success message with new shop details
    """
    user = request.user
    shop_id = request.data.get('shop_id')
    
    if not shop_id:
        return Response(
            {'error': 'shop_id is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validate user has access to this shop
    if not user.can_access_shop(shop_id):
        return Response(
            {'error': 'You do not have access to this shop'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        shop = Shop.objects.using('default').get(id=shop_id, is_active=True)
    except Shop.DoesNotExist:
        return Response(
            {'error': 'Shop not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Update session
    request.session['current_shop_id'] = shop.id
    request.session['current_shop_schema'] = shop.schema_name
    
    # Update user object for current request
    user.current_shop_id = shop.id
    
    logger.info(f"User {user.id} switched to shop {shop.id} ({shop.name})")
    
    return Response({
        'message': f'Switched to {shop.name}',
        'shop': {
            'id': shop.id,
            'name': shop.name,
            'schema_name': shop.schema_name
        }
    })


@api_view(['GET'])
def get_accessible_shops(request):
    """
    Get list of shops user has access to.
    
    Returns:
        List of shops with their details and current status
    """
    import traceback
    
    # Check authentication manually
    if not request.user or not request.user.is_authenticated:
        return Response(
            {'error': 'Authentication required'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    user = request.user
    
    try:
        shops = user.get_active_shops()
        
        current_shop_id = getattr(user, 'current_shop_id', None)
        
        if not current_shop_id:
            current_shop_id = request.session.get('current_shop_id')
        
        shop_list = [{
            'id': shop.id,
            'name': shop.name,
            'schema_name': shop.schema_name,
            'is_head_office': shop.is_head_office,
            'is_current': shop.id == current_shop_id
        } for shop in shops]
        
        return Response(shop_list)
    
    except Exception as e:
        error_detail = traceback.format_exc()
        logger.error(f"Error getting accessible shops for user {user.id}: {e}\n{error_detail}")
        # Only expose traceback in DEBUG mode
        from django.conf import settings
        response_data = {'error': 'Failed to get accessible shops', 'detail': str(e)}
        if settings.DEBUG:
            response_data['trace'] = error_detail[:2000]
        return Response(
            response_data,
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_current_shop(request):
    """
    Get the current active shop for the authenticated user.
    """
    user = request.user
    
    # Try to get from user object first
    shop_id = getattr(user, 'current_shop_id', None)
    
    if not shop_id:
        shop_id = request.session.get('current_shop_id')
    
    if not shop_id:
        return Response(
            {'error': 'No current shop set'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    try:
        shop = Shop.objects.using('default').get(id=shop_id, is_active=True)
        return Response({
            'id': shop.id,
            'name': shop.name,
            'schema_name': shop.schema_name,
            'is_head_office': shop.is_head_office
        })
    except Shop.DoesNotExist:
        return Response(
            {'error': 'Current shop not found or inactive'},
            status=status.HTTP_404_NOT_FOUND
        )

