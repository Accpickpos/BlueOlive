# tenancy/middleware.py
import logging
import re

from django.conf import settings
from django.db import connections
from django.http import HttpResponseNotFound, JsonResponse
from tenancy.models import Shop, Tenant
from tenancy.tenant_context import clear_current, set_current_shop, set_current_tenant
from tenancy.utils import register_tenant_connection

logger = logging.getLogger(__name__)


class TenantMiddleware:
    """
    Middleware to identify tenant and shop from the request.

    SECURITY MODEL:
    - JWT token is the AUTHORITATIVE source of tenant (signed by server)
    - Domain/subdomain for unauthenticated requests
    - Headers/query params ONLY in DEBUG mode

    Identification Priority:
    1. JWT Token (most secure - production)
    2. Custom domain (production)
    3. Subdomain (production)
    4. Development localhost (DEBUG mode only)

    Architecture:
    - Runs BEFORE authentication middleware
    - Sets up tenant context for authentication
    - Each tenant has separate database
    - Shops are schemas within tenant database
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Clear any existing context
        clear_current()

        try:
            # Identify tenant
            tenant = self._identify_tenant(request)

            if tenant:
                # Identify and set shop FIRST (before registering connection)
                # This ensures proper shop-specific schema is used
                shop = self._identify_shop(request, tenant)
                if shop:
                    set_current_shop(shop.schema_name)
                    request.shop = shop
                    # Register tenant database connection with the correct shop schema
                    # This is CRITICAL for multi-shop data isolation within a tenant
                    register_tenant_connection(tenant, shop=shop)
                else:
                    # DEBUG: Log when no shop is found
                    if settings.DEBUG:
                        logger.debug(
                            f"[TenantMiddleware] No shop identified for tenant {tenant.name}"
                        )
                    # Still register the tenant's base DB connection (public schema /
                    # first shop fallback, see register_tenant_connection) even without
                    # a shop. set_current_tenant() below is unconditional, and
                    # TenantDatabaseRouter routes ANY TENANT_APP_LABELS model (e.g.
                    # token_blacklist, checked on every /token/refresh/) to
                    # tenant.db_alias regardless of shop — leaving the alias
                    # unregistered here raised ConnectionDoesNotExist for those queries.
                    register_tenant_connection(tenant)
                    request.shop = None

                # Set tenant context
                set_current_tenant(tenant)

                request.tenant = tenant
                if settings.DEBUG:
                    logger.debug(
                        f"Tenant set: {tenant.name} (shop: {shop.name if shop else 'None'})"
                    )
            else:
                # No tenant found
                request.tenant = None
                request.shop = None
                if settings.DEBUG:
                    logger.debug("No tenant identified for request")
                else:
                    logger.warning(f"No tenant identified for {request.get_host()}")

        except Exception as e:
            logger.error(f"Error in tenant middleware: {str(e)}", exc_info=True)
            request.tenant = None
            request.shop = None

        # Process request
        response = self.get_response(request)

        # Clear context after request
        clear_current()

        return response

    def _identify_tenant(self, request):
        """
        Identify tenant from request using multiple methods.
        Priority: JWT Token > Domain/Subdomain > Development localhost

        SECURITY:
        - JWT token is authoritative source (signed by server)
        - Domain/subdomain for unauthenticated requests
        - Query params ONLY in DEBUG mode
        """
        # Method 0: Try to extract tenant from JWT token first (MOST SECURE)
        tenant = self._get_tenant_from_jwt(request)
        if tenant:
            if settings.DEBUG:
                logger.debug(f"Tenant from JWT token: {tenant.slug}")
            return tenant

        # Get the host
        host = request.get_host().split(":")[0]  # Remove port if present
        if settings.DEBUG:
            logger.debug(f"Parsing host: {host}")

        # Method 1: Check for localhost/development
        if self._is_local_host(host):
            return self._handle_localhost(request)

        # Method 2: Check for custom domain (PRODUCTION)
        tenant = self._get_tenant_by_domain(host)
        if tenant:
            if settings.DEBUG:
                logger.debug(f"Tenant from custom domain: {tenant.slug}")
            return tenant

        # Method 3: Extract from subdomain (PRODUCTION)
        tenant = self._get_tenant_from_subdomain(host)
        if tenant:
            if settings.DEBUG:
                logger.debug(f"Tenant from subdomain: {tenant.slug}")
            return tenant

        if settings.DEBUG:
            logger.debug(f"No tenant found for host: {host}")
        else:
            logger.warning(f"No tenant found for host: {host}")

        return None

    def _get_tenant_from_jwt(self, request):
        """
        Extract and validate tenant from JWT token in httpOnly cookie.
        This is the most secure method as JWT is signed by the server.

        SECURITY: Only accepts tokens from httpOnly cookies (not headers).
        """
        try:
            access_token = request.COOKIES.get("access_token")
            if not access_token:
                return None

            from rest_framework_simplejwt.tokens import AccessToken

            token = AccessToken(access_token)
            tenant_id = token.get("tenant_id")

            if tenant_id:
                # CRITICAL: Check is_active to prevent inactive tenant access
                tenant = Tenant.objects.filter(id=tenant_id, is_active=True).first()
                if tenant:
                    if settings.DEBUG:
                        logger.debug(f"JWT token validated for tenant_id={tenant_id}")
                    return tenant
                else:
                    logger.warning(f"JWT has invalid or inactive tenant_id={tenant_id}")
        except Exception as e:
            # This is expected for non-authenticated requests
            if settings.DEBUG:
                logger.debug(
                    f"JWT extraction failed (expected for public endpoints): {type(e).__name__}"
                )

        return None

    def _is_local_host(self, host):
        """
        Check if host is localhost or IP address.
        Used to enable development-mode features.
        """
        # This is a comparison list of hostnames a request might arrive as,
        # not a server bind address.
        local_hosts = ["localhost", "127.0.0.1", "0.0.0.0", "[::1]"]  # nosec

        # Check exact matches
        if host in local_hosts:
            return True

        # Check if it's a private IP address
        ip_pattern = re.compile(r"^(\d{1,3}\.){3}\d{1,3}$")
        if ip_pattern.match(host):
            # Simple private IP check
            parts = host.split(".")
            first = int(parts[0])
            if (
                first == 10
                or first == 127
                or (first == 172 and 16 <= int(parts[1]) <= 31)
                or (first == 192 and int(parts[1]) == 168)
            ):
                return True

        return False

    def _handle_localhost(self, request):
        """
        Handle localhost development scenarios.

        SECURITY: Only runs for localhost/local IPs

        Priority:
        1. Query parameter: ?tenant=acme (DEBUG mode only)
        2. Default tenant from settings
        3. First active tenant (DEBUG mode only, last resort)
        """
        # Option 1: Check for tenant query parameter (DEBUG only)
        if settings.DEBUG:
            tenant_param = request.GET.get("tenant")
            if tenant_param:
                if settings.DEBUG:
                    logger.debug(f"Using tenant from query param: {tenant_param}")
                tenant = self._get_tenant_by_slug(tenant_param)
                if tenant:
                    return tenant

        # Option 2: Use default tenant from settings
        if getattr(settings, "USE_DEFAULT_TENANT", False):
            default_slug = getattr(settings, "DEFAULT_TENANT_SLUG", None)
            if default_slug:
                if settings.DEBUG:
                    logger.debug(f"Using default tenant from settings: {default_slug}")
                tenant = self._get_tenant_by_slug(default_slug)
                if tenant:
                    return tenant

        # Option 3: Use first active tenant (DEBUG mode only, last resort)
        if settings.DEBUG:
            tenant = Tenant.objects.filter(is_active=True).first()
            if tenant:
                logger.debug(f"Using first active tenant (DEV mode): {tenant.slug}")
                return tenant

        logger.warning("No tenant available for localhost")
        return None

    def _get_tenant_from_subdomain(self, host):
        """
        Extract tenant from subdomain.
        Examples:
        - acme.example.com -> 'acme'
        - retail.myapp.com -> 'retail'
        """
        # Get the main domain from settings
        main_domain = getattr(settings, "MAIN_DOMAIN", None)

        if not main_domain:
            if settings.DEBUG:
                logger.debug("MAIN_DOMAIN not configured in settings")
            return None

        # Check if host ends with main domain
        if not host.endswith(main_domain):
            return None

        # Extract subdomain
        subdomain = host.replace(f".{main_domain}", "")

        # Ignore 'www'
        if subdomain == "www":
            return None

        # Ignore if no subdomain
        if subdomain == host or "." in subdomain:
            return None

        if settings.DEBUG:
            logger.debug(f"Extracted subdomain: {subdomain}")
        return self._get_tenant_by_slug(subdomain)

    def _get_tenant_by_slug(self, slug):
        """Get tenant by slug."""
        try:
            return Tenant.objects.get(slug=slug, is_active=True)
        except Tenant.DoesNotExist:
            if settings.DEBUG:
                logger.debug(f"Tenant not found: {slug}")
            return None

    def _get_tenant_by_domain(self, domain):
        """Get tenant by custom domain."""
        try:
            return Tenant.objects.get(custom_domain=domain, is_active=True)
        except Tenant.DoesNotExist:
            return None
        except Exception:
            # custom_domain field might not exist
            return None

    def _identify_shop(self, request, tenant):
        """
        Identify shop from request with proper authorization.

        SECURITY MODEL:
        - Authenticated users: Can use session, user context
        - Unauthenticated users: Only default shop (if configured)
        - Development mode: Headers/query params allowed (DEBUG only)

        Priority:
        1. Authenticated user's current shop (from user object)
        2. Session shop (authenticated users only)
        3. Development headers/query (DEBUG mode only)
        4. Default shop fallback
        """
        import logging

        logger = logging.getLogger(__name__)

        shop = None

        # METHOD 0: Extract shop directly from JWT token (highest priority)
        # This enables fully stateless, pre-auth shop identification
        if not shop:
            access_token = request.COOKIES.get("access_token")
            if access_token:
                try:
                    from rest_framework_simplejwt.tokens import AccessToken

                    token = AccessToken(access_token)
                    shop_id = token.get("current_shop_id")
                    logger.debug(
                        f"[_identify_shop] Method 0 - Token has current_shop_id: {shop_id}"
                    )
                    if shop_id:
                        shop = Shop.objects.filter(
                            tenant=tenant, id=shop_id, is_active=True
                        ).first()
                        if shop and settings.DEBUG:
                            logger.debug(
                                f"[_identify_shop] Shop from JWT token: {shop.name}"
                            )
                except Exception as e:
                    if settings.DEBUG:
                        logger.debug(
                            f"[_identify_shop] JWT shop extraction failed: {e}"
                        )

        # DEBUG: Log the tenant details
        logger.debug(
            f"[_identify_shop] Starting with tenant={tenant.name}, tenant.shops.count={tenant.shops.count()}"
        )

        # Method 1: From session FIRST (most reliable - set during login/switch)
        # IMPORTANT: Read session directly, don't require authentication
        # This ensures correct shop is used even before auth middleware runs
        if (
            not shop
            and hasattr(request, "session")
            and "current_shop_id" in request.session
        ):
            try:
                session_shop_id = request.session.get("current_shop_id")
                if session_shop_id:
                    logger.debug(
                        f"[_identify_shop] Session has current_shop_id={session_shop_id}"
                    )
                    shop = Shop.objects.get(
                        tenant=tenant, id=session_shop_id, is_active=True
                    )
                    if settings.DEBUG:
                        logger.debug(f"Shop from session: {shop.name}")
            except Shop.DoesNotExist:
                logger.warning(f"Session shop not found: {session_shop_id}")
                # Clear invalid shop from session
                request.session.pop("current_shop_id", None)
                request.session.pop("current_shop_schema", None)

        # Method 2: From authenticated user's context (only if session not set)
        # Note: JWT may have overwritten this to first shop, so session should take priority
        if not shop and hasattr(request, "user") and request.user.is_authenticated:
            # Get shop from user's current context (could be from JWT claims)
            shop_id = getattr(request.user, "current_shop_id", None)
            if shop_id:
                logger.debug(f"[_identify_shop] User has current_shop_id={shop_id}")
                try:
                    shop = Shop.objects.get(tenant=tenant, id=shop_id, is_active=True)
                    if settings.DEBUG:
                        logger.debug(f"Shop from user context: {shop.name}")
                except Shop.DoesNotExist:
                    logger.warning(f"User's shop {shop_id} not found")

        # Method 3: From X-Shop-ID header (can be used in both DEBUG and production)
        # This header is sent by the frontend from localStorage 'currentShopId'
        if not shop:
            shop_id_header = request.headers.get("X-Shop-ID")
            if shop_id_header:
                try:
                    shop = Shop.objects.get(
                        tenant=tenant, id=int(shop_id_header), is_active=True
                    )
                    logger.debug(
                        f"Shop from X-Shop-ID header: {shop.name} (id={shop.id}, schema={shop.schema_name})"
                    )
                    # Also set in session for future requests
                    request.session["current_shop_id"] = shop.id
                    request.session["current_shop_schema"] = shop.schema_name
                except (Shop.DoesNotExist, ValueError) as e:
                    logger.warning(
                        f"Shop not found for X-Shop-ID header: {shop_id_header} - {e}"
                    )

        # Method 4: Development mode - allow header/query param override
        # SECURITY: Only in DEBUG mode
        if not shop and settings.DEBUG:
            shop = self._identify_shop_dev(request, tenant)

        # Method 4: Default shop fallback
        if not shop:
            default_shop_enabled = getattr(settings, "USE_DEFAULT_SHOP", False)
            logger.debug(
                f"[_identify_shop] USE_DEFAULT_SHOP={default_shop_enabled}, current shop={shop}"
            )
            if default_shop_enabled:
                # Query from default database (Shop model is in main DB)
                logger.debug(
                    f"[_identify_shop] Attempting to get default shop for tenant={tenant.name}"
                )
                shop = (
                    Shop.objects.using("default")
                    .filter(tenant=tenant, is_active=True)
                    .first()
                )
                if shop:
                    logger.debug(
                        f"[_identify_shop] Found default shop: {shop.name} (schema: {shop.schema_name})"
                    )
                else:
                    logger.warning(
                        f"[_identify_shop] No default shop found for tenant {tenant.name}"
                    )
                if shop and settings.DEBUG:
                    logger.debug(
                        f"[TenantMiddleware] Using default shop: {shop.subdomain or shop.name} (schema: {shop.schema_name})"
                    )

        logger.debug(
            f"[_identify_shop] Final shop result: {shop.name if shop else None}"
        )
        return shop

    def _identify_shop_dev(self, request, tenant):
        """
        Development-only shop identification from headers/query params.

        SECURITY: Only runs when DEBUG=True (enforced by caller).
        """
        import logging

        logger = logging.getLogger(__name__)

        # Check header - X-Shop-ID (numeric ID)
        shop_id = request.headers.get("X-Shop-ID")
        if shop_id:
            try:
                shop = Shop.objects.get(tenant=tenant, id=int(shop_id), is_active=True)
                logger.debug(
                    f"Shop from X-Shop-ID header (DEV): {shop.name} (id={shop.id}, schema={shop.schema_name})"
                )
                return shop
            except (Shop.DoesNotExist, ValueError):
                logger.warning(f"Shop not found for X-Shop-ID header: {shop_id}")

        # Check header - X-Shop-Slug (subdomain/slug)
        shop_slug = request.headers.get("X-Shop-Slug")
        if shop_slug:
            try:
                shop = Shop.objects.get(
                    tenant=tenant, subdomain=shop_slug, is_active=True
                )
                logger.debug(f"Shop from header (DEV): {shop.name}")
                return shop
            except Shop.DoesNotExist:
                logger.warning(f"Shop not found in header: {shop_slug}")

        # Check query parameter
        shop_param = request.GET.get("shop")
        if shop_param:
            try:
                # Try by subdomain first
                shop = Shop.objects.get(
                    tenant=tenant, subdomain=shop_param, is_active=True
                )
                logger.debug(f"Shop from query param (DEV): {shop.name}")
                return shop
            except Shop.DoesNotExist:
                # Try by ID
                try:
                    shop = Shop.objects.get(
                        tenant=tenant, id=int(shop_param), is_active=True
                    )
                    logger.debug(f"Shop from query param ID (DEV): {shop.name}")
                    return shop
                except (Shop.DoesNotExist, ValueError):
                    logger.warning(f"Shop not found: {shop_param}")

        return None


class AddonAccessMiddleware:
    """
    Blocks requests to an optional-addon app's URL prefix (cash_book,
    general_ledger, gas, stockfinder - see settings.OPTIONAL_ADDON_APPS) for
    a tenant that hasn't enabled it.

    Placed after TenantMiddleware in MIDDLEWARE so request.tenant is already
    set. Gates at the URL layer (rather than each app's own permission
    classes) because core/urls.py wires every app's routes unconditionally
    for every request - a disabled addon's tables may not even exist in a
    given tenant's shop schema, so without this the first query would 500
    with ProgrammingError instead of a clean 403.

    Runs BEFORE authentication, so an unauthenticated caller (e.g. the
    Stockfinder webhook, which is AllowAny) is still gated correctly -
    request.tenant is resolved from the Host header regardless of auth.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.prefix_map = getattr(settings, "ADDON_URL_PREFIXES", {})

    def __call__(self, request):
        addon = self._required_addon(request.path)
        if addon:
            tenant = getattr(request, "tenant", None)
            enabled = getattr(tenant, "enabled_addons", None) or []
            if not tenant or addon not in enabled:
                return JsonResponse(
                    {"error": f"The '{addon}' addon is not enabled for this account."},
                    status=403,
                )
        return self.get_response(request)

    def _required_addon(self, path):
        for addon, prefixes in self.prefix_map.items():
            if any(path.startswith(prefix) for prefix in prefixes):
                return addon
        return None


class TenantRequiredMiddleware:
    """
    Middleware to enforce that a valid tenant must be identified.
    Returns 404 if no tenant is found.

    USAGE: Place this AFTER TenantMiddleware in MIDDLEWARE setting.

    Configuration:
    - EXEMPT_PATHS: List of paths that don't require a tenant
    - Can be customized via settings.TENANT_EXEMPT_PATHS
    """

    # Default paths that don't require a tenant
    DEFAULT_EXEMPT_PATHS = [
        "/health/",
        "/metrics/",
        "/static/",
        "/media/",
        "/admin/",  # Django admin uses default DB
    ]

    def __init__(self, get_response):
        self.get_response = get_response
        # Allow customization via settings
        self.exempt_paths = getattr(
            settings, "TENANT_EXEMPT_PATHS", self.DEFAULT_EXEMPT_PATHS
        )

    def __call__(self, request):
        # Check if path is exempt
        if self._is_exempt(request.path):
            return self.get_response(request)

        # Check if tenant is set
        if not hasattr(request, "tenant") or request.tenant is None:
            logger.error(
                f"No tenant for path: {request.path} from {request.get_host()}"
            )

            if request.path.startswith("/api/"):
                return JsonResponse(
                    {
                        "error": "Tenant not found",
                        "detail": "Please specify a valid tenant domain or subdomain",
                    },
                    status=404,
                )
            else:
                return HttpResponseNotFound(
                    "<h1>Tenant Not Found</h1>"
                    "<p>Please access this application through a valid tenant domain.</p>"
                )

        return self.get_response(request)

    def _is_exempt(self, path):
        """Check if path is exempt from tenant requirement."""
        for exempt_path in self.exempt_paths:
            if path.startswith(exempt_path):
                return True
        return False


class UserShopValidationMiddleware:
    """
    Validates user-shop association on every request.
    Ensures:
    1. User has valid shop access
    2. Shop is active
    3. Session shop is valid
    4. Handles edge cases (revoked access, expired associations)

    This middleware should be placed AFTER TenantMiddleware and authentication.
    """

    # Paths that don't require shop validation
    EXEMPT_PATHS = [
        "/health/",
        "/metrics/",
        "/static/",
        "/media/",
        "/admin/",
        "/api/auth/",  # Authentication endpoints
        "/auth/",  # Auth endpoints
        "/api/v1/auth/",  # API auth
        "/tenants/shops/",  # Shop listing
        "/shops/list/",  # Shop list endpoint
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Skip validation for exempt paths
        if self._is_exempt(request.path):
            return self.get_response(request)

        # Only validate for authenticated requests
        if hasattr(request, "user") and request.user.is_authenticated:
            validation_result = self._validate_user_shop(request)

            if validation_result is not None:
                return validation_result

        return self.get_response(request)

    def _is_exempt(self, path):
        """Check if path is exempt from shop validation."""
        for exempt in self.EXEMPT_PATHS:
            if path.startswith(exempt):
                return True
        return False

    def _validate_user_shop(self, request):
        """
        Validate user has valid shop access.
        Returns None if valid, JsonResponse if invalid.

        Note: Allows access during onboarding (new users without shops).
        """
        user = request.user

        # Skip validation for admin/superuser users - they can access without shops
        if user.is_superuser or user.role == "ADMIN":
            return None

        # Check if user has any active shop access
        try:
            accessible_shops = list(user.get_active_shops())
        except Exception as e:
            logger.warning(f"Error getting accessible shops for user {user.id}: {e}")
            accessible_shops = []

        # Allow users without shops during onboarding
        # They can access the app but will be limited
        if not accessible_shops:
            # Allow access but log warning - user might be in onboarding
            logger.info(
                f"User {user.id} has no active shop access - allowing during onboarding"
            )
            # Don't set current_shop_id - it will be null
            # The frontend should handle showing an onboarding wizard
            return None  # Allow access

        # Validate current session shop
        session_shop_id = request.session.get("current_shop_id")

        if session_shop_id:
            # Check if session shop is still valid
            if not user.can_access_shop(session_shop_id):
                # Session shop access was revoked - clear and redirect
                logger.info(
                    f"User {user.id} shop access revoked for shop {session_shop_id}, switching"
                )
                request.session.pop("current_shop_id", None)
                request.session.pop("current_shop_schema", None)

                # Set first available shop as current
                new_shop = accessible_shops[0]
                request.session["current_shop_id"] = new_shop.id
                request.session["current_shop_schema"] = new_shop.schema_name
                user.current_shop_id = new_shop.id

                return JsonResponse(
                    {
                        "error": "SHOP_ACCESS_REVOKED",
                        "message": f"Your access to the previous shop has been revoked. You have been switched to {new_shop.name}.",
                        "current_shop": {"id": new_shop.id, "name": new_shop.name},
                    },
                    status=200,
                )  # 200 with warning instead of 403

        # Set current shop if not set
        if not getattr(user, "current_shop_id", None):
            if session_shop_id:
                user.current_shop_id = session_shop_id
            else:
                # Auto-select first shop
                first_shop = accessible_shops[0]
                request.session["current_shop_id"] = first_shop.id
                request.session["current_shop_schema"] = first_shop.schema_name
                user.current_shop_id = first_shop.id

                if settings.DEBUG:
                    logger.debug(
                        f"Auto-selected shop {first_shop.name} for user {user.id}"
                    )

        # CRITICAL: Re-register database connection with correct shop schema
        # This ensures all subsequent queries use the correct shop's schema
        # TenantMiddleware runs before authentication, so we need to fix the schema here
        current_shop_id = getattr(user, "current_shop_id", None)
        if current_shop_id:
            tenant = getattr(request, "tenant", None)
            if tenant:
                try:
                    shop = Shop.objects.get(
                        id=current_shop_id, tenant=tenant, is_active=True
                    )
                    # Close existing connection to force reconnect with new schema
                    if tenant.db_alias in connections:
                        connections[tenant.db_alias].close()
                    # Re-register with correct shop schema
                    register_tenant_connection(tenant, shop=shop)
                    set_current_shop(shop.schema_name)
                    if settings.DEBUG:
                        logger.debug(
                            f"Re-registered connection with shop schema: {shop.schema_name}"
                        )
                except Shop.DoesNotExist:
                    logger.warning(f"Current shop {current_shop_id} not found")

        return None  # Valid


# ============================================================================
# SUBSCRIPTION MIDDLEWARE
# ============================================================================


class SubscriptionMiddleware:
    """
    Middleware to enforce subscription status on tenant requests.

    Checks subscription status on every request and:
    - Allows access for active subscriptions
    - Shows warning for trial subscriptions nearing expiry
    - Shows warning for past due subscriptions
    - Blocks access for expired/cancelled/suspended subscriptions

    Configuration (via settings):
    - SUBSCRIPTION_EXEMPT_PATHS: Paths that don't require subscription check
    - SUBSCRIPTION_GRACE_DAYS: Days to allow access after expiration (default: 3)
    - SUBSCRIPTION_WARNING_DAYS: Days before expiration to show warning (default: 7)
    """

    # Default paths that don't require subscription check
    DEFAULT_EXEMPT_PATHS = [
        "/health/",
        "/metrics/",
        "/static/",
        "/media/",
        "/admin/",
        "/api/v1/subscription/",  # Subscription API
        "/api/v1/auth/",  # Authentication
    ]

    # Statuses that allow full access
    ALLOWED_STATUSES = ["TRIAL", "ACTIVE"]

    # Statuses that show warning but allow access
    WARNING_STATUSES = ["PAST_DUE"]

    # Statuses that block access
    BLOCKED_STATUSES = ["CANCELLED", "EXPIRED", "SUSPENDED"]

    def __init__(self, get_response):
        self.get_response = get_response
        # Allow customization via settings
        self.exempt_paths = getattr(
            settings, "SUBSCRIPTION_EXEMPT_PATHS", self.DEFAULT_EXEMPT_PATHS
        )
        self.grace_days = getattr(settings, "SUBSCRIPTION_GRACE_DAYS", 3)
        self.warning_days = getattr(settings, "SUBSCRIPTION_WARNING_DAYS", 7)

    def __call__(self, request):
        # Check if path is exempt
        if self._is_exempt(request.path):
            return self.get_response(request)

        # Check if tenant is available
        tenant = getattr(request, "tenant", None)
        if not tenant:
            # No tenant means no subscription check needed
            return self.get_response(request)

        # Skip for admin users (they should always have access)
        if hasattr(request, "user") and request.user.is_authenticated:
            if request.user.is_superuser or getattr(request.user, "is_admin", False):
                return self.get_response(request)

        # Check subscription status
        subscription_status = self._check_subscription(tenant, request)

        if subscription_status["blocked"]:
            # Return subscription blocked response
            return self._blocked_response(request, subscription_status)

        # Add subscription info to request for views to use
        request.subscription = subscription_status

        # Add warning header if needed
        if subscription_status.get("warning"):
            # Continue with warning
            pass

        return self.get_response(request)

    def _is_exempt(self, path):
        """Check if path is exempt from subscription check."""
        for exempt_path in self.exempt_paths:
            if path.startswith(exempt_path):
                return True
        return False

    def _check_subscription(self, tenant, request):
        """
        Check tenant's subscription status.

        Returns dict with:
        - blocked: bool - whether access should be blocked
        - status: str - subscription status
        - warning: str - warning message if applicable
        - subscription: Subscription object if exists
        - days_remaining: int - days remaining in billing period
        """
        from django.utils import timezone
        from tenancy.models import Subscription

        result = {
            "blocked": False,
            "status": None,
            "warning": None,
            "subscription": None,
            "days_remaining": 0,
        }

        try:
            subscription = Subscription.objects.get(tenant=tenant)
            result["subscription"] = subscription
            result["status"] = subscription.status
            result["days_remaining"] = subscription.days_remaining

            # Check if blocked
            if subscription.status in self.BLOCKED_STATUSES:
                result["blocked"] = True
                result["warning"] = f"Subscription is {subscription.status.lower()}"
                return result

            # Check for expired
            if subscription.is_expired and subscription.status not in ["TRIAL"]:
                result["blocked"] = True
                result["warning"] = "Subscription has expired"
                return result

            # Check for warnings
            if subscription.status in self.WARNING_STATUSES:
                result["warning"] = (
                    "Subscription payment is past due. Please update payment method."
                )

            # Check if trial is expiring soon
            if subscription.status == "TRIAL" and subscription.trial_end_date:
                days_until_trial_end = (
                    subscription.trial_end_date - timezone.now().date()
                ).days
                if days_until_trial_end <= self.warning_days:
                    result["warning"] = (
                        f"Trial expires in {days_until_trial_end} days. Subscribe to continue using the system."
                    )

            # Check if subscription is expiring soon
            days_remaining = subscription.days_remaining
            if days_remaining <= self.warning_days and subscription.status == "ACTIVE":
                result["warning"] = (
                    f"Subscription expires in {days_remaining} days. Please renew to avoid interruption."
                )

            return result

        except Subscription.DoesNotExist:
            # No subscription found - allow access with warning
            result["warning"] = (
                "No active subscription. Please subscribe to continue using the system."
            )
            # For now, we don't block access without subscription
            # This can be changed to block by setting blocked = True
            return result

    def _blocked_response(self, request, subscription_status):
        """
        Return subscription blocked response.

        Returns JSON response for API requests or HTML page for regular requests.
        """
        from django.http import JsonResponse
        from django.utils import timezone

        status = subscription_status.get("status", "UNKNOWN")
        warning = subscription_status.get("warning", "Subscription access blocked")

        # Check if there's a grace period. Previously this only checked
        # self.grace_days > 0 with no comparison against elapsed time, so
        # any EXPIRED tenant got unconditional, indefinite access as long as
        # SUBSCRIPTION_GRACE_DAYS was configured — the grace period never
        # actually ended.
        subscription = subscription_status.get("subscription")
        if subscription and status == "EXPIRED" and self.grace_days > 0:
            days_since_expiry = (timezone.now().date() - subscription.end_date).days
            if days_since_expiry <= self.grace_days:
                # Still within the grace period — allow access.
                return self.get_response(request)

        if request.path.startswith("/api/"):
            return JsonResponse(
                {
                    "error": "SUBSCRIPTION_BLOCKED",
                    "status": status,
                    "message": warning,
                    "subscription": {
                        "status": status,
                        "days_remaining": subscription_status.get("days_remaining", 0),
                    },
                },
                status=403,
            )

        # For HTML requests, return a simple message
        # In production, you'd render a proper template
        return JsonResponse(
            {
                "error": "SUBSCRIPTION_BLOCKED",
                "status": status,
                "message": warning,
                "action": "Please contact support or renew your subscription.",
            },
            status=403,
        )


def check_tenant_subscription(tenant):
    """
    Utility function to check if a tenant has an active subscription.

    Args:
        tenant: Tenant object

    Returns:
        dict with subscription status
    """
    from django.utils import timezone
    from tenancy.models import Subscription

    try:
        subscription = Subscription.objects.get(tenant=tenant)

        return {
            "has_subscription": True,
            "is_active": subscription.status in ["TRIAL", "ACTIVE"],
            "status": subscription.status,
            "can_access": subscription.can_access,
            "days_remaining": subscription.days_remaining,
            "trial_end_date": subscription.trial_end_date,
            "end_date": subscription.end_date,
            "plan_name": subscription.plan.name if subscription.plan else None,
        }

    except Subscription.DoesNotExist:
        return {
            "has_subscription": False,
            "is_active": False,
            "status": "NONE",
            "can_access": False,
        }


def require_active_subscription(view_func):
    """
    Decorator to require an active subscription for a view.

    Usage:
        @require_active_subscription
        def my_view(request):
            ...
    """
    from functools import wraps

    from django.http import JsonResponse

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        tenant = getattr(request, "tenant", None)

        if not tenant:
            return JsonResponse({"error": "No tenant context"}, status=400)

        subscription_status = check_tenant_subscription(tenant)

        if not subscription_status["can_access"]:
            return JsonResponse(
                {
                    "error": "SUBSCRIPTION_REQUIRED",
                    "message": "An active subscription is required to access this resource.",
                    "subscription_status": subscription_status,
                },
                status=403,
            )

        # Add subscription status to request
        request.subscription_status = subscription_status

        return view_func(request, *args, **kwargs)

    return wrapper
