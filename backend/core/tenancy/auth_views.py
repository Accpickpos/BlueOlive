# tenancy/auth_views.py
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import authenticate
from shop_users.models import ShopUser
from tenancy.models import Tenant
from tenancy.tenant_context import get_current_tenant
import logging

logger = logging.getLogger(__name__)


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom JWT serializer that includes tenant information in the token
    """
    def validate(self, attrs):
        # Get the tenant from context (set by middleware)
        tenant = get_current_tenant()
        
        # Standard authentication
        data = super().validate(attrs)
        
        # Add custom claims
        refresh = self.get_token(self.user)
        
        # Add tenant information to the token
        if tenant:
            refresh['tenant_id'] = tenant.id
            refresh['tenant_slug'] = tenant.slug
        
        # Add user information
        refresh['user_id'] = self.user.id
        refresh['username'] = self.user.username
        refresh['email'] = self.user.email
        refresh['role'] = self.user.role
        
        data['refresh'] = str(refresh)
        data['access'] = str(refresh.access_token)
        
        # Add user data to response
        data['user'] = {
            'id': self.user.id,
            'username': self.user.username,
            'email': self.user.email,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'role': self.user.role,
        }
        
        if tenant:
            data['tenant'] = {
                'id': tenant.id,
                'name': tenant.name,
                'slug': tenant.slug,
                'subdomain': tenant.subdomain,
            }
        
        return data


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom JWT login view that handles tenant-aware authentication
    """
    serializer_class = CustomTokenObtainPairSerializer


@api_view(['POST'])
@permission_classes([AllowAny])
def tenant_login(request):
    """
    Tenant-aware login endpoint
    Expects: username/email, password, and optionally tenant_slug
    """
    username = request.data.get('username') or request.data.get('email')
    password = request.data.get('password')
    tenant_slug = request.data.get('tenant_slug')
    
    if not username or not password:
        return Response(
            {'error': 'Username/email and password are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Get tenant from context or request data
    tenant = get_current_tenant()
    if not tenant and tenant_slug:
        try:
            tenant = Tenant.objects.get(slug=tenant_slug)
        except Tenant.DoesNotExist:
            return Response(
                {'error': 'Invalid tenant'},
                status=status.HTTP_404_NOT_FOUND
            )

    if not tenant:
        return Response(
            {'error': 'Tenant not specified'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Set tenant context for this request
    from tenancy.tenant_context import set_current_tenant
    from tenancy.utils import register_tenant_connection
    set_current_tenant(tenant)
    register_tenant_connection(tenant)
    
    # Try to find user by username or email
    try:
        from tenancy.utils import register_tenant_connection
        register_tenant_connection(tenant)

        user = ShopUser.objects.using(tenant.db_alias).filter(tenant_id=tenant.id).filter(
            username=username
        ).first()

        if not user:
            user = ShopUser.objects.using(tenant.db_alias).filter(tenant_id=tenant.id).filter(
                email=username
            ).first()
        
        if not user:
            return Response(
                {'error': 'Invalid credentials'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Check password
        if not user.check_password(password):
            return Response(
                {'error': 'Invalid credentials'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        if not user.is_active:
            return Response(
                {'error': 'User account is disabled'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Generate tokens
        refresh = RefreshToken.for_user(user)
        
        # Add custom claims
        refresh['tenant_id'] = tenant.id
        refresh['tenant_slug'] = tenant.slug
        refresh['user_id'] = user.id
        refresh['username'] = user.username
        refresh['email'] = user.email
        refresh['role'] = user.role
        
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'role': user.role,
            },
            'tenant': {
                'id': tenant.id,
                'name': tenant.name,
                'slug': tenant.slug,
                'subdomain': tenant.subdomain,
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return Response(
            {'error': 'An error occurred during login'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    """
    Logout endpoint that blacklists the refresh token
    """
    try:
        refresh_token = request.data.get('refresh')
        if refresh_token:
            token = RefreshToken(refresh_token)

            # Get tenant from token claims
            tenant_slug = token.get('tenant_slug')
            if tenant_slug:
                try:
                    from tenancy.models import Tenant
                    tenant = Tenant.objects.get(slug=tenant_slug)
                    # Set tenant context
                    from tenancy.tenant_context import set_current_tenant
                    from tenancy.utils import register_tenant_connection
                    set_current_tenant(tenant)
                    register_tenant_connection(tenant)
                except Tenant.DoesNotExist:
                    pass  # If tenant not found, proceed without context

            token.blacklist()
            return Response(
                {'message': 'Logout successful'},
                status=status.HTTP_200_OK
            )
        return Response(
            {'error': 'Refresh token is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        return Response(
            {'error': 'Invalid token'},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_profile(request):
    """
    Get current user profile
    """
    user = request.user
    tenant = get_current_tenant()
    
    return Response({
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'role': user.role,
        },
        'tenant': {
            'id': tenant.id,
            'name': tenant.name,
            'slug': tenant.slug,
            'subdomain': tenant.subdomain,
        } if tenant else None
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_token(request):
    """
    Verify if a token is valid
    """
    from rest_framework_simplejwt.tokens import AccessToken
    from rest_framework_simplejwt.exceptions import TokenError
    
    token = request.data.get('token')
    if not token:
        return Response(
            {'error': 'Token is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        AccessToken(token)
        return Response({'valid': True}, status=status.HTTP_200_OK)
    except TokenError:
        return Response({'valid': False}, status=status.HTTP_401_UNAUTHORIZED)