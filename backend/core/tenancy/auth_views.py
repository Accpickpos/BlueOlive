# tenancy/auth_views.py
import logging

from core.throttling import PublicReadThrottle
from django.contrib.auth import authenticate
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from shop_users.models import ShopUser
from tenancy.models import Tenant
from tenancy.tenant_context import get_current_tenant

logger = logging.getLogger(__name__)


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom JWT serializer that includes tenant and shop information in the token
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
            refresh["tenant_id"] = tenant.id
            refresh["tenant_slug"] = tenant.slug

        # Add user information
        refresh["user_id"] = self.user.id
        refresh["username"] = self.user.username
        refresh["email"] = self.user.email
        refresh["role"] = self.user.role

        # Add shop information - get user's accessible shops
        # OPTIMIZATION: Only put current_shop in access token (small)
        # Full accessible_shops list goes in refresh token only
        try:
            # Get accessible shops for this user
            accessible_shops = list(self.user.get_active_shops())

            if accessible_shops:
                # Set current shop - prefer head office or first shop
                current_shop = None
                for shop in accessible_shops:
                    if shop.is_head_office:
                        current_shop = shop
                        break

                if not current_shop:
                    current_shop = accessible_shops[0]

                # Add current shop to ACCESS token (for quick access - used by Method 0)
                # Get the access token and add claims to it
                access_token = refresh.access_token
                access_token["current_shop_id"] = current_shop.id
                access_token["current_shop_schema"] = current_shop.schema_name

                # Also add to refresh token (for reference)
                refresh["current_shop_id"] = current_shop.id
                refresh["current_shop_schema"] = current_shop.schema_name

                # Full shop list in refresh token only (larger, but fetched less frequently)
                shop_list = [
                    {"id": shop.id, "name": shop.name, "schema_name": shop.schema_name}
                    for shop in accessible_shops
                ]
                refresh["accessible_shops"] = shop_list

                # Add current shop to response (both tokens)
                data["current_shop"] = {
                    "id": current_shop.id,
                    "name": current_shop.name,
                    "schema_name": current_shop.schema_name,
                }
        except Exception as e:
            logger.warning(
                f"Could not get accessible shops for user {self.user.id}: {e}"
            )

        data["refresh"] = str(refresh)
        data["access"] = str(refresh.access_token)

        # Add user data to response
        data["user"] = {
            "id": self.user.id,
            "username": self.user.username,
            "email": self.user.email,
            "first_name": self.user.first_name,
            "last_name": self.user.last_name,
            "role": self.user.role,
        }

        if tenant:
            data["tenant"] = {
                "id": tenant.id,
                "name": tenant.name,
                "slug": tenant.slug,
                "subdomain": tenant.subdomain,
            }

        return data


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom JWT login view that handles tenant-aware authentication
    """

    serializer_class = CustomTokenObtainPairSerializer


@api_view(["POST"])
@permission_classes([AllowAny])
def tenant_login(request):
    """
    Tenant-aware login endpoint
    Expects: username/email, password, and optionally tenant_slug
    """
    username = request.data.get("username") or request.data.get("email")
    password = request.data.get("password")
    tenant_slug = request.data.get("tenant_slug")
    selected_shop_id = request.data.get(
        "shop_id"
    )  # Get selected shop from login request

    if not username or not password:
        return Response(
            {"error": "Username/email and password are required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Get tenant from context or request data
    tenant = get_current_tenant()
    if not tenant and tenant_slug:
        try:
            tenant = Tenant.objects.get(slug=tenant_slug, is_active=True)
        except Tenant.DoesNotExist:
            return Response(
                {"error": "Invalid tenant"}, status=status.HTTP_404_NOT_FOUND
            )

    if not tenant:
        return Response(
            {"error": "Tenant not specified"}, status=status.HTTP_400_BAD_REQUEST
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

        user = (
            ShopUser.objects.using(tenant.db_alias)
            .filter(tenant_id=tenant.id)
            .filter(username=username)
            .first()
        )

        if not user:
            user = (
                ShopUser.objects.using(tenant.db_alias)
                .filter(tenant_id=tenant.id)
                .filter(email=username)
                .first()
            )

        if not user:
            return Response(
                {"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED
            )

        # Check password
        if not user.check_password(password):
            return Response(
                {"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED
            )

        if not user.is_active:
            return Response(
                {"error": "User account is disabled"}, status=status.HTTP_403_FORBIDDEN
            )

        # Set default shop in session - get user's accessible shops
        # Use selected_shop_id if provided and user has access to it
        try:
            # DEBUG: Log user details
            logger.debug(
                f"[LOGIN] User {user.id} (role={user.role}, tenant_id={user.tenant_id}, shop_ids={getattr(user, 'shop_ids', [])})"
            )

            accessible_shops = user.get_active_shops()

            # DEBUG: Log accessible shops
            shop_count = (
                accessible_shops.count()
                if hasattr(accessible_shops, "count")
                else len(list(accessible_shops))
            )
            logger.debug(
                f"[LOGIN] Found {shop_count} accessible shops for user {user.id}"
            )

            # Check if selected_shop_id was provided and user has access to it
            default_shop = None
            if selected_shop_id:
                for shop in accessible_shops:
                    if shop.id == int(selected_shop_id):
                        default_shop = shop
                        break

            # If user has only ONE shop, automatically use that
            if not default_shop and len(accessible_shops) == 1:
                default_shop = accessible_shops[0]

            # Otherwise use first accessible shop (for users with multiple shops)
            if not default_shop and accessible_shops:
                default_shop = accessible_shops[0]

            if default_shop:
                request.session["current_shop_id"] = default_shop.id
                request.session["current_shop_schema"] = default_shop.schema_name
                # Also set on user object for immediate use
                user.current_shop_id = default_shop.id
                # Re-register tenant connection with the correct shop schema
                register_tenant_connection(tenant, shop=default_shop)
            else:
                accessible_shops = []
        except Exception as e:
            logger.warning(f"Could not set default shop for user {user.id}: {e}")
            default_shop = None
            accessible_shops = []

        # Generate tokens
        refresh = RefreshToken.for_user(user)

        # Add custom claims
        refresh["tenant_id"] = tenant.id
        refresh["tenant_slug"] = tenant.slug
        refresh["user_id"] = user.id
        refresh["username"] = user.username
        refresh["email"] = user.email
        refresh["role"] = user.role
        # Add current_shop_id to ACCESS token (for Method 0 to work)
        if default_shop:
            access_token = refresh.access_token
            access_token["current_shop_id"] = default_shop.id
            access_token["current_shop_schema"] = default_shop.schema_name
            # Also add to refresh for reference
            refresh["current_shop_id"] = default_shop.id
            refresh["current_shop_schema"] = default_shop.schema_name

        return Response(
            {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "role": user.role,
                },
                "tenant": {
                    "id": tenant.id,
                    "name": tenant.name,
                    "slug": tenant.slug,
                    "subdomain": tenant.subdomain,
                },
                "shop": (
                    {
                        "id": default_shop.id,
                        "name": default_shop.name,
                        "schema_name": default_shop.schema_name,
                    }
                    if default_shop
                    else None
                ),
                "accessible_shops": (
                    [
                        {"id": s.id, "name": s.name, "schema_name": s.schema_name}
                        for s in accessible_shops
                    ]
                    if accessible_shops
                    else []
                ),
            },
            status=status.HTTP_200_OK,
        )

    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return Response(
            {"error": "An error occurred during login"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout(request):
    """
    Logout endpoint that blacklists the refresh token
    """
    try:
        refresh_token = request.data.get("refresh")
        if refresh_token:
            token = RefreshToken(refresh_token)

            # Get tenant from token claims
            tenant_slug = token.get("tenant_slug")
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
            return Response({"message": "Logout successful"}, status=status.HTTP_200_OK)
        return Response(
            {"error": "Refresh token is required"}, status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        return Response({"error": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def user_profile(request):
    """
    Get current user profile
    """
    try:
        user = request.user

        # Check if user is authenticated
        if not user or not user.is_authenticated:
            return Response(
                {"error": "User not authenticated"}, status=status.HTTP_401_UNAUTHORIZED
            )

        tenant = None
        tenant_data = None

        # Try to get current tenant
        try:
            tenant = get_current_tenant()
        except Exception as e:
            logger.warning(f"Failed to get current tenant: {str(e)}")
            # Continue without tenant data if we can't get it

        # Build tenant response
        if tenant:
            try:
                tenant_data = {
                    "id": tenant.id,
                    "name": tenant.name,
                    "slug": tenant.slug,
                    "subdomain": tenant.subdomain,
                }
            except Exception as e:
                logger.warning(f"Failed to serialize tenant data: {str(e)}")
                tenant_data = None

        # Build user response
        user_data = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "role": getattr(user, "role", "CASHIER"),  # Default to CASHIER if not set
            "is_staff": user.is_staff,
            "is_superuser": user.is_superuser,
            "is_active": user.is_active,
        }

        # Include tenant_id if user has one
        if hasattr(user, "tenant_id") and user.tenant_id:
            user_data["tenant_id"] = user.tenant_id

        return Response(
            {
                "user": user_data,
                "tenant": tenant_data,
            }
        )

    except Exception as e:
        logger.error(f"Error fetching user profile: {str(e)}", exc_info=True)
        return Response(
            {"error": "Failed to fetch user profile", "detail": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([AllowAny])
# Intentionally AllowAny: this only confirms whether a token is currently
# valid and doesn't leak claim contents, so it's safe to expose publicly
# for client-side token health checks. Still throttled per-IP (reusing the
# same AnonRateThrottle pattern as PublicReadThrottle/LoginThrottle) so it
# can't be hammered as a cheap validity oracle.
@throttle_classes([PublicReadThrottle])
def verify_token(request):
    """
    Verify if a token is valid
    """
    from rest_framework_simplejwt.exceptions import TokenError
    from rest_framework_simplejwt.tokens import AccessToken

    token = request.data.get("token")
    if not token:
        return Response(
            {"error": "Token is required"}, status=status.HTTP_400_BAD_REQUEST
        )

    try:
        AccessToken(token)
        return Response({"valid": True}, status=status.HTTP_200_OK)
    except TokenError:
        return Response({"valid": False}, status=status.HTTP_401_UNAUTHORIZED)
