# tenancy/jwt_authentication.py
import logging

from django.conf import settings
from rest_framework.exceptions import PermissionDenied
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import AuthenticationFailed, InvalidToken
from rest_framework_simplejwt.tokens import AccessToken
from shop_users.models import ShopUser
from tenancy.models import Tenant
from tenancy.tenant_context import get_current_tenant, set_current_tenant
from tenancy.utils import register_tenant_connection

logger = logging.getLogger(__name__)


class TenantJWTAuthentication(JWTAuthentication):
    """
    Custom JWT authentication that validates tenant context.
    Reads JWT from httpOnly cookies (secure) instead of headers.

    Architecture:
    - Each tenant has a separate database
    - Within each tenant DB, shops exist as PostgreSQL schemas
    - Main database stores Tenant model
    - ShopUser exists in each tenant DB's public schema

    Flow:
    1. Extract JWT from cookie or Authorization header
    2. Validate CSRF token (for cookie-based auth)
    3. Validate token structure
    4. Load Tenant from main DB using tenant_id from token
    5. Register tenant database connection
    6. Query ShopUser from tenant DB public schema
    7. Validate user-tenant relationship
    """

    # Safe methods that don't require CSRF (these are read-only/secure)
    SAFE_METHODS = ("GET", "HEAD", "OPTIONS")

    def get_raw_token(self, request):
        """
        Override to get JWT from httpOnly cookie instead of Authorization header.
        Falls back to Authorization header for API compatibility.
        """
        # Try httpOnly cookie first (web app)
        token = request.COOKIES.get("access_token")
        if token:
            if settings.DEBUG:
                logger.debug(f"JWT token found in cookie, length={len(token)}")
            return token.encode("utf-8")

        # Fall back to Authorization header (API clients)
        if settings.DEBUG:
            logger.debug("No cookie token, checking Authorization header")

        # Manually extract from header to avoid super() issues
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        if not auth_header:
            return None

        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return None

        return parts[1].encode("utf-8")

    def _validate_csrf(self, request):
        """
        Validate CSRF token for cookie-based authentication.

        For state-changing methods (POST, PUT, PATCH, DELETE), CSRF is required.
        For safe methods (GET, HEAD, OPTIONS), CSRF is optional.

        This protects against CSRF attacks when JWT is stored in cookies.

        NOTE: Public auth endpoints (signup, login, etc.) are exempted from CSRF
        validation because they use @csrf_exempt decorator at the view level.
        """
        # Define public auth endpoints that don't require CSRF validation
        # These endpoints use @csrf_exempt at the view level
        # Use full path for matching since request.path includes /api/v1/ prefix
        public_auth_paths = [
            "/users/auth/signup/",
            "/users/auth/login/",
            "/users/auth/csrf/",
            "/users/auth/token/refresh/",
            "/users/auth/logout/",
            "/users/auth/unified-login/",
            "/auth/signup/",
            "/auth/login/",
            "/auth/csrf/",
            "/auth/token/refresh/",
            "/auth/logout/",
            "/auth/unified-login/",
            # Shop creation endpoint - JWT authentication is sufficient
            "/tenants/shops/",
            "/tenants/shops",
            "/shops/",
            "/shops",
        ]

        # Check if this is a public auth endpoint
        request_path = request.path
        for path in public_auth_paths:
            if request_path.endswith(path) or path in request_path:
                if settings.DEBUG:
                    logger.debug(
                        f"Skipping CSRF validation for public auth endpoint: {request_path}"
                    )
                return True

        # Check if this is a state-changing request
        # Check if this is a state-changing request
        method = request.method
        if method in self.SAFE_METHODS:
            # Safe methods don't require CSRF validation
            return True

        # For state-changing methods, check CSRF token
        # Try multiple sources for CSRF token
        csrf_token = None

        # 1. Check X-CSRFToken header (common for AJAX)
        csrf_token = request.headers.get("X-CSRFToken") or request.META.get(
            "HTTP_X_CSRFTOKEN"
        )

        # 2. Check CSRF cookie
        if not csrf_token:
            csrf_token = request.COOKIES.get("csrftoken")

        # 3. Check request body (as fallback)
        if not csrf_token:
            csrf_token = request.POST.get("csrfmiddlewaretoken")

        # Validate CSRF token
        if not csrf_token:
            logger.warning("CSRF token missing for state-changing request")
            return False

        # Get the expected CSRF token from Django's cookie (NOT a new token)
        try:
            # Use request.META['CSRF_COOKIE'] which contains the original token
            # NOT get_csrf_token() which generates a NEW token each time!
            expected_csrf = request.META.get("CSRF_COOKIE")

            # If not in META, try to get from cookie directly
            if not expected_csrf:
                expected_csrf = request.COOKIES.get("csrftoken")

            if not expected_csrf:
                # If we can't find the original token, log and fail
                logger.warning("No CSRF cookie found in request")
                return False
        except Exception as e:
            logger.error(f"Error getting CSRF token: {e}")
            return False

        # Constant-time comparison to prevent timing attacks
        if not self._constant_time_compare(csrf_token, expected_csrf):
            logger.warning(
                f"CSRF token mismatch: got {csrf_token[:10]}..., expected {expected_csrf[:10]}..."
            )
            return False

        return True

    def _constant_time_compare(self, val1, val2):
        """
        Constant-time string comparison to prevent timing attacks.
        """
        if isinstance(val1, str):
            val1 = val1.encode("utf-8")
        if isinstance(val2, str):
            val2 = val2.encode("utf-8")

        if len(val1) != len(val2):
            return False

        result = 0
        for c1, c2 in zip(val1, val2):
            result |= c1 ^ c2
        return result == 0

    def authenticate(self, request):
        """
        Authenticate using JWT from cookie or Authorization header.
        Returns None if no authentication is attempted (allows public endpoints).
        Raises AuthenticationFailed if authentication is attempted but fails.
        """
        # Skip authentication entirely for public auth endpoints
        public_auth_paths = [
            "/users/auth/signup/",
            "/users/auth/login/",
            "/users/auth/csrf/",
            "/users/auth/token/refresh/",
            "/users/auth/logout/",
            "/users/auth/unified-login/",
            "/auth/signup/",
            "/auth/login/",
            "/auth/csrf/",
            "/auth/token/refresh/",
            "/auth/logout/",
            "/auth/unified-login/",
        ]
        request_path = request.path
        for path in public_auth_paths:
            if request_path.endswith(path) or path in request_path:
                if settings.DEBUG:
                    logger.debug(
                        f"Skipping authentication for public endpoint: {request_path}"
                    )
                return None

        if settings.DEBUG:
            logger.debug(f"Authentication attempt on: {request.path}")
            logger.debug(f"Request cookies: {list(request.COOKIES.keys())}")

        try:
            # Get raw token
            raw_token = self.get_raw_token(request)
            if raw_token is None:
                logger.debug("No token found, allowing anonymous access")
                return None

            # Track if token came from cookie
            cookie_token = request.COOKIES.get("access_token")

            # Validate the token first
            try:
                validated_token = AccessToken(raw_token)
            except Exception as e:
                # Token is invalid/expired - this is NOT an authentication failure
                # This is normal for unauthenticated users with stale cookies
                # Let the request through to be handled by permission classes
                if settings.DEBUG:
                    logger.debug(
                        f"Invalid/expired token, allowing anonymous: {type(e).__name__}"
                    )
                return None

            # If token came from cookie, validate CSRF
            # Skip CSRF if using Authorization header (standard API practice)
            auth_header = request.META.get("HTTP_AUTHORIZATION", "")
            if cookie_token and not auth_header.startswith("Bearer "):
                if not self._validate_csrf(request):
                    logger.warning("CSRF validation failed for cookie-based JWT")
                    raise AuthenticationFailed("CSRF validation failed")

            logger.debug("Token validated successfully")

            # Get user from tenant database
            # This will also set up tenant context
            user = self.get_user(validated_token)

            # Validate tenant context
            self._validate_tenant_context(user, validated_token)

            # Validate shop membership. TenantMiddleware resolves request.shop
            # BEFORE authentication runs (including from the client-supplied
            # X-Shop-ID header), with no way to check membership since the real
            # user isn't known yet at that point. Now that we have the actual
            # authenticated user, enforce that they can access the resolved shop.
            self._validate_shop_access(request, user)

            if settings.DEBUG:
                logger.debug(f"JWT authentication successful for user: {user.username}")

            return user, validated_token

        except (AuthenticationFailed, InvalidToken, PermissionDenied) as e:
            logger.warning(f"Authentication failed: {type(e).__name__} - {str(e)}")
            raise
        except Exception as e:
            logger.error(
                f"Unexpected authentication error: {type(e).__name__}: {str(e)}",
                exc_info=True,
            )
            raise AuthenticationFailed("Authentication error")

    def _validate_tenant_context(self, user, validated_token):
        """
        Validate that token tenant matches context tenant and user belongs to tenant.

        This is called AFTER get_user() has already set up the tenant context.
        """
        token_tenant_id = validated_token.get("tenant_id")

        if not token_tenant_id:
            raise AuthenticationFailed("Token missing tenant information")

        # Get current tenant (should already be set by get_user)
        current_tenant = get_current_tenant()

        if not current_tenant:
            # This shouldn't happen if get_user() worked correctly
            logger.error("No tenant in context after get_user()")
            raise AuthenticationFailed("Tenant context not set")

        # Validate token tenant matches context tenant
        if current_tenant.id != token_tenant_id:
            logger.warning(
                f"Tenant mismatch: token={token_tenant_id}, context={current_tenant.id}"
            )
            raise AuthenticationFailed("Tenant mismatch")

        # Validate user belongs to tenant
        if hasattr(user, "tenant_id") and user.tenant_id != token_tenant_id:
            logger.warning(
                f"User {user.id} does not belong to tenant {token_tenant_id}"
            )
            raise AuthenticationFailed("User does not belong to this tenant")

    def _validate_shop_access(self, request, user):
        """
        Validate that the now-known authenticated user actually has access
        to the shop TenantMiddleware resolved for this request.

        TenantMiddleware._identify_shop() sets request.shop before this
        authenticate() call runs, using (in priority order) the JWT's
        current_shop_id claim, the session, or the client-supplied X-Shop-ID
        header/query param - none of which are validated against shop
        membership at that point because request.user is still
        AnonymousUser (this app never calls django.contrib.auth.login()).
        This is the first point in the request lifecycle where the real
        user is available, so membership is enforced here using the same
        ShopUser.can_access_shop() helper IsShopMember relies on.
        """
        shop = getattr(request, "shop", None)
        if shop is None:
            # No shop was resolved for this request - nothing to validate
            # (e.g. onboarding, or endpoints that don't need a shop).
            return

        if not user.can_access_shop(shop.id):
            logger.warning(
                f"User {user.id} (tenant={getattr(user, 'tenant_id', None)}) "
                f"attempted to access shop {shop.id} without membership"
            )
            raise PermissionDenied("You do not have access to this shop")

    def get_user(self, validated_token):
        """
        Get user from tenant database public schema.

        Critical Steps:
        1. Extract user_id and tenant_id from token
        2. Query Tenant from main database
        3. Register tenant database connection (REQUIRED!)
        4. Set tenant in context
        5. Query ShopUser from tenant DB public schema

        Note: tenant_id in token is REQUIRED for security and performance.
        We do NOT search across all tenants.
        """
        user_id = validated_token.get("user_id")
        if user_id is None:
            raise InvalidToken("Token contained no recognizable user identification")

        token_tenant_id = validated_token.get("tenant_id")
        token_tenant_slug = validated_token.get("tenant_slug")
        token_shop_id = validated_token.get(
            "current_shop_id"
        )  # Check for current_shop_id (from CustomTokenObtainPairSerializer)

        if settings.DEBUG:
            logger.debug(
                f"[JWT] token_tenant_id={token_tenant_id}, token_tenant_slug={token_tenant_slug}, token_shop_id={token_shop_id}"
            )

        if not token_tenant_id and not token_tenant_slug:
            raise InvalidToken("Token missing tenant information")

        try:
            # Step 1: Get tenant from main database
            if token_tenant_slug:
                tenant = Tenant.objects.get(slug=token_tenant_slug)
            else:
                tenant = Tenant.objects.get(id=token_tenant_id)

            if settings.DEBUG:
                logger.debug(f"Loaded tenant: {tenant.slug} (id={tenant.id})")

            # Step 2: CRITICAL - Register tenant database connection
            # This tells Django about the tenant's database
            register_tenant_connection(tenant)

            # Step 3: Set tenant in thread-local context
            set_current_tenant(tenant)

            if settings.DEBUG:
                logger.debug(
                    f"Tenant context set: {tenant.slug}, db_alias: {tenant.db_alias}"
                )

            # Step 4: Query user from tenant DB public schema
            # Using tenant.db_alias to route query to correct database
            user = ShopUser.objects.using(tenant.db_alias).get(id=user_id)

            # DEBUG: Set shop_id from token onto user object for middleware to use
            token_shop_id = validated_token.get("current_shop_id")
            if token_shop_id:
                user.current_shop_id = token_shop_id
                if settings.DEBUG:
                    logger.debug(f"[JWT] Set user.current_shop_id = {token_shop_id}")
            else:
                # Try to get from session (set by auth backend)
                # This is handled in middleware, but let's check token for accessible shops
                accessible_shops = validated_token.get("accessible_shops", [])
                if accessible_shops:
                    # Set first accessible shop as current
                    user.current_shop_id = accessible_shops[0].get("id")
                    if settings.DEBUG:
                        logger.debug(
                            f"[JWT] Set user.current_shop_id from token = {user.current_shop_id}"
                        )

            # Also check for current_shop_id in token claims
            current_shop = validated_token.get("current_shop")
            if current_shop and not getattr(user, "current_shop_id", None):
                user.current_shop_id = current_shop.get("id")
                if settings.DEBUG:
                    logger.debug(
                        f"[JWT] Set user.current_shop_id from current_shop claim = {user.current_shop_id}"
                    )

            if settings.DEBUG:
                logger.debug(f"Found user: {user.username} (id={user.id})")

            # Step 5: Validate user is active
            if not user.is_active:
                raise AuthenticationFailed("User is inactive")

            return user

        except Tenant.DoesNotExist:
            logger.error(
                f"Tenant not found: id={token_tenant_id}, slug={token_tenant_slug}"
            )
            raise AuthenticationFailed("Invalid tenant")
        except ShopUser.DoesNotExist:
            logger.error(f"User {user_id} not found in tenant {tenant.slug}")
            raise AuthenticationFailed("User not found")
        except Exception as e:
            logger.error(
                f"Error loading user: {type(e).__name__} - {str(e)}", exc_info=True
            )
            raise AuthenticationFailed("Authentication failed")
