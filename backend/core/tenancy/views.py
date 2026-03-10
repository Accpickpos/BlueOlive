from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from datetime import date, timedelta
from .models import Tenant, Shop, ShopConfiguration, SubscriptionPlan, Subscription, SubscriptionPayment
from .serializers import (
    TenantSerializer, ShopSerializer, ShopConfigurationSerializer,
    SubscriptionPlanSerializer, SubscriptionSerializer, SubscriptionDetailSerializer,
    SubscriptionCreateSerializer, SubscriptionPaymentSerializer, SubscriptionCancelSerializer
)
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
    tenant = None
    if tenant_key:
        try:
            tenant = Tenant.objects.get(slug=tenant_key)
        except Tenant.DoesNotExist:
            # Try to find by shop name
            try:
                shop = Shop.objects.get(name=tenant_key)
                tenant = shop.tenant
            except Shop.DoesNotExist:
                pass
    
    # If no tenant found from subdomain/header, try user context
    if not tenant and request.user.is_authenticated:
        if hasattr(request.user, 'tenant_id') and request.user.tenant_id:
            try:
                tenant = Tenant.objects.get(id=request.user.tenant_id)
            except Tenant.DoesNotExist:
                pass
    
    if tenant:
        # Return full tenant details using the serializer
        from .serializers import TenantListSerializer
        serializer = TenantListSerializer(tenant)
        return Response(serializer.data)
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
        - list/retrieve: Admin only (ADMIN and MANAGER can see shops - see ShopUser.has_shop_access)
        """
        from tenancy.permissions import IsAdmin
        
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'list', 'retrieve']:
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


class ShopConfigurationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for per-shop period-end configuration.
    
    Endpoints:
    - GET /shop-config/ - List all shop configurations
    - POST /shop-config/ - Create configuration for a shop
    - GET /shop-config/{id}/ - Get configuration details
    - PATCH /shop-config/{id}/ - Update configuration
    - GET /shop-config/by-shop/{shop_id}/ - Get config for specific shop
    """
    queryset = ShopConfiguration.objects.using('default').all()
    serializer_class = ShopConfigurationSerializer
    lookup_field = 'pk'
    
    def get_queryset(self):
        return ShopConfiguration.objects.using('default').all()
    
    @action(detail=False, methods=['get'], url_path='by-shop/(?P<shop_id>[^/.]+)')
    def by_shop(self, request, shop_id=None):
        """Get configuration for a specific shop"""
        try:
            config = ShopConfiguration.objects.using('default').get(shop_id=shop_id)
            serializer = self.get_serializer(config)
            return Response(serializer.data)
        except ShopConfiguration.DoesNotExist:
            return Response(
                {'error': 'Configuration not found for this shop'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['get'])
    def current_shop_config(self, request):
        """Get configuration for the current shop (from session/user)"""
        from tenancy.tenant_context import get_current_shop_id
        shop_id = get_current_shop_id(request)
        
        if not shop_id:
            return Response(
                {'error': 'No shop selected'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        config, created = ShopConfiguration.objects.using('default').get_or_create(
            shop_id=shop_id,
            defaults={
                'current_financial_year': date.today().year,
                'current_period': 1
            }
        )
        serializer = self.get_serializer(config)
        return Response(serializer.data)
    
    def perform_create(self, serializer):
        serializer.save()
    
    def perform_update(self, serializer):
        serializer.save()


# ============================================================================
# SUBSCRIPTION VIEWS
# ============================================================================

class SubscriptionPlanViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing subscription plans.
    
    Endpoints:
    - GET /plans/ - List all active plans
    - POST /plans/ - Create a new plan (admin only)
    - GET /plans/{id}/ - Get plan details
    - PUT /plans/{id}/ - Update plan
    - DELETE /plans/{id}/ - Deactivate plan
    """
    queryset = SubscriptionPlan.objects.all()
    serializer_class = SubscriptionPlanSerializer
    permission_classes = [IsAdminUser]
    
    def get_queryset(self):
        queryset = SubscriptionPlan.objects.all()
        # Filter by active status
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        # Filter trial plans
        is_trial = self.request.query_params.get('is_trial')
        if is_trial is not None:
            queryset = queryset.filter(is_trial=is_trial.lower() == 'true')
        return queryset
    
    @action(detail=False, methods=['get'])
    def public(self, request):
        """Get only public (non-trial) active plans for display."""
        plans = SubscriptionPlan.objects.filter(is_active=True, is_trial=False).order_by('sort_order', 'price')
        serializer = SubscriptionPlanSerializer(plans, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def trial(self, request):
        """Get trial plans."""
        plans = SubscriptionPlan.objects.filter(is_active=True, is_trial=True)
        serializer = SubscriptionPlanSerializer(plans, many=True)
        return Response(serializer.data)


class SubscriptionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing subscriptions.
    
    Endpoints:
    - GET /subscriptions/ - List subscriptions
    - POST /subscriptions/ - Create new subscription
    - GET /subscriptions/{id}/ - Get subscription details
    - PUT /subscriptions/{id}/ - Update subscription
    - DELETE /subscriptions/{id}/ - Cancel subscription
    - POST /subscriptions/{id}/cancel/ - Cancel subscription with reason
    - POST /subscriptions/{id}/renew/ - Manual renewal
    - POST /subscriptions/{id}/change-plan/ - Change subscription plan
    """
    queryset = Subscription.objects.all()
    permission_classes = [IsAdminUser]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return SubscriptionCreateSerializer
        elif self.action in ['retrieve', 'update', 'partial_update']:
            return SubscriptionDetailSerializer
        return SubscriptionSerializer
    
    def get_queryset(self):
        queryset = Subscription.objects.select_related('tenant', 'plan').all()
        # Filter by tenant
        tenant_id = self.request.query_params.get('tenant_id')
        if tenant_id:
            queryset = queryset.filter(tenant_id=tenant_id)
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        return queryset
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        Cancel a subscription.
        
        Request body:
        {
            "immediately": false,  // Cancel now or at end of period
            "reason": "Optional reason for cancellation"
        }
        """
        subscription = self.get_object()
        serializer = SubscriptionCancelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        immediately = serializer.validated_data.get('immediately', False)
        reason = serializer.validated_data.get('reason', '')
        
        if subscription.status in ['CANCELLED', 'EXPIRED']:
            return Response(
                {'error': 'Subscription is already cancelled or expired'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if immediately:
            subscription.status = 'CANCELLED'
            subscription.cancelled_at = date.today()
            subscription.auto_renew = False
            subscription.save()
            logger.info(f"Subscription {subscription.id} cancelled immediately by {reason}")
        else:
            subscription.auto_renew = False
            subscription.save()
            logger.info(f"Subscription {subscription.id} marked for cancellation at end of period")
        
        return Response(SubscriptionSerializer(subscription).data)
    
    @action(detail=True, methods=['post'])
    def renew(self, request, pk=None):
        """
        Manually renew a subscription.
        Extends the subscription by one billing period.
        """
        subscription = self.get_object()
        
        if subscription.status == 'CANCELLED':
            # Reactivate cancelled subscription
            subscription.status = 'ACTIVE'
            subscription.cancelled_at = None
            subscription.auto_renew = True
        
        # Extend the end date
        new_end_date = subscription.end_date + timedelta(days=subscription.plan.billing_period_days)
        subscription.end_date = new_end_date
        subscription.current_period_end = new_end_date
        subscription.status = 'ACTIVE'
        subscription.save()
        
        logger.info(f"Subscription {subscription.id} renewed until {new_end_date}")
        return Response(SubscriptionSerializer(subscription).data)
    
    @action(detail=True, methods=['post'])
    def change_plan(self, request, pk=None):
        """
        Change the subscription plan.
        
        Request body:
        {
            "plan_id": 1  // ID of the new plan
        }
        """
        subscription = self.get_object()
        plan_id = request.data.get('plan_id')
        
        if not plan_id:
            return Response(
                {'error': 'plan_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            new_plan = SubscriptionPlan.objects.get(id=plan_id, is_active=True)
        except SubscriptionPlan.DoesNotExist:
            return Response(
                {'error': 'Plan not found or inactive'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Update subscription with new plan
        old_plan = subscription.plan
        subscription.plan = new_plan
        subscription.auto_renew = True
        subscription.status = 'ACTIVE'
        subscription.save()
        
        logger.info(f"Subscription {subscription.id} changed from {old_plan.name} to {new_plan.name}")
        return Response(SubscriptionDetailSerializer(subscription).data)
    
    @action(detail=False, methods=['get'])
    def current(self, request):
        """Get the current tenant's subscription."""
        tenant = get_current_tenant()
        if not tenant:
            return Response(
                {'error': 'No tenant context'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            subscription = Subscription.objects.select_related('tenant', 'plan').get(tenant=tenant)
            serializer = SubscriptionDetailSerializer(subscription)
            return Response(serializer.data)
        except Subscription.DoesNotExist:
            return Response(
                {'error': 'No active subscription found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def suspend(self, request, pk=None):
        """Suspend a subscription (admin action)."""
        subscription = self.get_object()
        subscription.status = 'SUSPENDED'
        subscription.save()
        logger.info(f"Subscription {subscription.id} suspended")
        return Response(SubscriptionSerializer(subscription).data)
    
    @action(detail=True, methods=['post'])
    def reactivate(self, request, pk=None):
        """Reactivate a suspended subscription (admin action)."""
        subscription = self.get_object()
        subscription.status = 'ACTIVE'
        subscription.save()
        logger.info(f"Subscription {subscription.id} reactivated")
        return Response(SubscriptionSerializer(subscription).data)


class SubscriptionPaymentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing subscription payments.
    
    Endpoints:
    - GET /payments/ - List payments
    - POST /payments/ - Record a new payment
    - GET /payments/{id}/ - Get payment details
    - PUT /payments/{id}/ - Update payment
    - DELETE /payments/{id}/ - Delete payment
    - POST /payments/{id}/process/ - Process payment
    - POST /payments/{id}/refund/ - Refund payment
    """
    queryset = SubscriptionPayment.objects.all()
    serializer_class = SubscriptionPaymentSerializer
    permission_classes = [IsAdminUser]
    
    def get_queryset(self):
        queryset = SubscriptionPayment.objects.select_related('subscription', 'subscription__tenant').all()
        # Filter by subscription
        subscription_id = self.request.query_params.get('subscription_id')
        if subscription_id:
            queryset = queryset.filter(subscription_id=subscription_id)
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        return queryset
    
    @action(detail=True, methods=['post'])
    def process(self, request, pk=None):
        """
        Process a pending payment.
        
        Request body:
        {
            "gateway_payment_id": "payfast_xxx",
            "status": "SUCCEEDED"
        }
        """
        payment = self.get_object()
        gateway_payment_id = request.data.get('gateway_payment_id', '')
        new_status = request.data.get('status', 'SUCCEEDED')
        
        if payment.status != 'PENDING' and payment.status != 'PROCESSING':
            return Response(
                {'error': 'Payment cannot be processed in current state'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        payment.gateway_payment_id = gateway_payment_id or payment.gateway_payment_id
        payment.status = new_status
        
        if new_status == 'SUCCEEDED':
            payment.paid_at = date.today()
            # Extend subscription
            subscription = payment.subscription
            new_end_date = subscription.end_date + timedelta(days=subscription.plan.billing_period_days)
            subscription.end_date = new_end_date
            subscription.current_period_end = new_end_date
            subscription.status = 'ACTIVE'
            subscription.save()
        elif new_status == 'FAILED':
            payment.failed_at = date.today()
        
        payment.save()
        logger.info(f"Payment {payment.id} processed with status {new_status}")
        return Response(SubscriptionPaymentSerializer(payment).data)
    
    @action(detail=True, methods=['post'])
    def refund(self, request, pk=None):
        """
        Refund a payment.
        
        Request body:
        {
            "reason": "Customer request"
        }
        """
        payment = self.get_object()
        
        if payment.status != 'SUCCEEDED':
            return Response(
                {'error': 'Only succeeded payments can be refunded'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        payment.status = 'REFUNDED'
        payment.save()
        logger.info(f"Payment {payment.id} refunded")
        return Response(SubscriptionPaymentSerializer(payment).data)
    
    @action(detail=False, methods=['get'])
    def tenant_payments(self, request):
        """Get payments for the current tenant."""
        tenant = get_current_tenant()
        if not tenant:
            return Response(
                {'error': 'No tenant context'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            subscription = Subscription.objects.get(tenant=tenant)
            payments = SubscriptionPayment.objects.filter(subscription=subscription).order_by('-created_at')
            serializer = SubscriptionPaymentSerializer(payments, many=True)
            return Response(serializer.data)
        except Subscription.DoesNotExist:
            return Response([])

