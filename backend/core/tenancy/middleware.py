# tenancy/middleware.py
import logging
import re
from django.db import connections
from django.http import HttpResponseNotFound, JsonResponse
from django.conf import settings
from tenancy.models import Tenant, Shop
from tenancy.tenant_context import (
    set_current_tenant, 
    set_current_shop, 
    clear_current
)
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
                else:
                    # DEBUG: Log when no shop is found
                    if settings.DEBUG:
                        logger.debug(f"[TenantMiddleware] No shop identified for tenant {tenant.name}")
                
                # Register tenant database connection with the correct shop schema
                # This is CRITICAL for multi-shop data isolation within a tenant
                register_tenant_connection(tenant, shop=shop)
                
                # Set tenant context
                set_current_tenant(tenant)
                
                request.tenant = tenant
                if settings.DEBUG:
                    logger.debug(f"Tenant set: {tenant.name} (shop: {shop.name if shop else 'None'})")
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
        host = request.get_host().split(':')[0]  # Remove port if present
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
            access_token = request.COOKIES.get('access_token')
            if not access_token:
                return None
            
            from rest_framework_simplejwt.tokens import AccessToken
            token = AccessToken(access_token)
            tenant_id = token.get('tenant_id')
            
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
                logger.debug(f"JWT extraction failed (expected for public endpoints): {type(e).__name__}")
        
        return None
    
    def _is_local_host(self, host):
        """
        Check if host is localhost or IP address.
        Used to enable development-mode features.
        """
        local_hosts = ['localhost', '127.0.0.1', '0.0.0.0', '[::1]']
        
        # Check exact matches
        if host in local_hosts:
            return True
        
        # Check if it's a private IP address
        ip_pattern = re.compile(r'^(\d{1,3}\.){3}\d{1,3}$')
        if ip_pattern.match(host):
            # Simple private IP check
            parts = host.split('.')
            first = int(parts[0])
            if first == 10 or first == 127 or (first == 172 and 16 <= int(parts[1]) <= 31) or (first == 192 and int(parts[1]) == 168):
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
            tenant_param = request.GET.get('tenant')
            if tenant_param:
                if settings.DEBUG:
                    logger.debug(f"Using tenant from query param: {tenant_param}")
                tenant = self._get_tenant_by_slug(tenant_param)
                if tenant:
                    return tenant
        
        # Option 2: Use default tenant from settings
        if getattr(settings, 'USE_DEFAULT_TENANT', False):
            default_slug = getattr(settings, 'DEFAULT_TENANT_SLUG', None)
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
        main_domain = getattr(settings, 'MAIN_DOMAIN', None)
        
        if not main_domain:
            if settings.DEBUG:
                logger.debug("MAIN_DOMAIN not configured in settings")
            return None
        
        # Check if host ends with main domain
        if not host.endswith(main_domain):
            return None
        
        # Extract subdomain
        subdomain = host.replace(f'.{main_domain}', '')
        
        # Ignore 'www'
        if subdomain == 'www':
            return None
        
        # Ignore if no subdomain
        if subdomain == host or '.' in subdomain:
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
        shop = None
        
        # Method 1: From authenticated user's context
        if hasattr(request, 'user') and request.user.is_authenticated:
            # Get shop from user's current context (could be from JWT claims)
            shop_id = getattr(request.user, 'current_shop_id', None)
            if shop_id:
                try:
                    shop = Shop.objects.get(
                        tenant=tenant,
                        id=shop_id,
                        is_active=True
                    )
                    if settings.DEBUG:
                        logger.debug(f"Shop from user context: {shop.name}")
                except Shop.DoesNotExist:
                    logger.warning(f"User's shop {shop_id} not found")
        
        # Method 2: From session (shop_id is set when user switches shops)
        # IMPORTANT: Read session directly, don't require authentication
        # This ensures correct shop is used even before auth middleware runs
        if not shop and hasattr(request, 'session') and 'current_shop_id' in request.session:
            try:
                session_shop_id = request.session.get('current_shop_id')
                if session_shop_id:
                    shop = Shop.objects.get(
                        tenant=tenant,
                        id=session_shop_id,
                        is_active=True
                    )
                    if settings.DEBUG:
                        logger.debug(f"Shop from session: {shop.name}")
            except Shop.DoesNotExist:
                logger.warning(f"Session shop not found: {session_shop_id}")
                # Clear invalid shop from session
                request.session.pop('current_shop_id', None)
                request.session.pop('current_shop_schema', None)
        
        # Method 3: Development mode - allow header/query param override
        # SECURITY: Only in DEBUG mode
        if not shop and settings.DEBUG:
            shop = self._identify_shop_dev(request, tenant)
        
        # Method 4: Default shop fallback
        if not shop:
            default_shop_enabled = getattr(settings, 'USE_DEFAULT_SHOP', False)
            if settings.DEBUG:
                logger.debug(f"[TenantMiddleware] USE_DEFAULT_SHOP={default_shop_enabled}, current shop={shop}")
            if default_shop_enabled:
                # Query from default database (Shop model is in main DB)
                shop = Shop.objects.using('default').filter(
                    tenant=tenant, 
                    is_active=True
                ).first()
                if shop and settings.DEBUG:
                    logger.debug(f"[TenantMiddleware] Using default shop: {shop.subdomain or shop.name} (schema: {shop.schema_name})")
        
        return shop
    
    def _identify_shop_dev(self, request, tenant):
        """
        Development-only shop identification from headers/query params.
        
        SECURITY: Only runs when DEBUG=True (enforced by caller).
        """
        # Check header
        shop_slug = request.headers.get('X-Shop-Slug')
        if shop_slug:
            try:
                shop = Shop.objects.get(
                    tenant=tenant,
                    subdomain=shop_slug,
                    is_active=True
                )
                logger.debug(f"Shop from header (DEV): {shop.name}")
                return shop
            except Shop.DoesNotExist:
                logger.warning(f"Shop not found in header: {shop_slug}")
        
        # Check query parameter
        shop_param = request.GET.get('shop')
        if shop_param:
            try:
                # Try by subdomain first
                shop = Shop.objects.get(
                    tenant=tenant,
                    subdomain=shop_param,
                    is_active=True
                )
                logger.debug(f"Shop from query param (DEV): {shop.name}")
                return shop
            except Shop.DoesNotExist:
                # Try by ID
                try:
                    shop = Shop.objects.get(
                        tenant=tenant,
                        id=int(shop_param),
                        is_active=True
                    )
                    logger.debug(f"Shop from query param ID (DEV): {shop.name}")
                    return shop
                except (Shop.DoesNotExist, ValueError):
                    logger.warning(f"Shop not found: {shop_param}")
        
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
        '/health/',
        '/metrics/',
        '/static/',
        '/media/',
        '/admin/',  # Django admin uses default DB
    ]
    
    def __init__(self, get_response):
        self.get_response = get_response
        # Allow customization via settings
        self.exempt_paths = getattr(
            settings, 
            'TENANT_EXEMPT_PATHS', 
            self.DEFAULT_EXEMPT_PATHS
        )
    
    def __call__(self, request):
        # Check if path is exempt
        if self._is_exempt(request.path):
            return self.get_response(request)
        
        # Check if tenant is set
        if not hasattr(request, 'tenant') or request.tenant is None:
            logger.error(f"No tenant for path: {request.path} from {request.get_host()}")
            
            if request.path.startswith('/api/'):
                return JsonResponse({
                    'error': 'Tenant not found',
                    'detail': 'Please specify a valid tenant domain or subdomain'
                }, status=404)
            else:
                return HttpResponseNotFound(
                    '<h1>Tenant Not Found</h1>'
                    '<p>Please access this application through a valid tenant domain.</p>'
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
        '/health/',
        '/metrics/',
        '/static/',
        '/media/',
        '/admin/',
        '/api/auth/',           # Authentication endpoints
        '/auth/',               # Auth endpoints
        '/api/v1/auth/',        # API auth
        '/tenants/shops/',      # Shop listing
        '/shops/list/',         # Shop list endpoint
    ]
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Skip validation for exempt paths
        if self._is_exempt(request.path):
            return self.get_response(request)
        
        # Only validate for authenticated requests
        if hasattr(request, 'user') and request.user.is_authenticated:
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
        if user.is_superuser or user.role == 'ADMIN':
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
            logger.info(f"User {user.id} has no active shop access - allowing during onboarding")
            # Don't set current_shop_id - it will be null
            # The frontend should handle showing an onboarding wizard
            return None  # Allow access
        
        # Validate current session shop
        session_shop_id = request.session.get('current_shop_id')
        
        if session_shop_id:
            # Check if session shop is still valid
            if not user.can_access_shop(session_shop_id):
                # Session shop access was revoked - clear and redirect
                logger.info(f"User {user.id} shop access revoked for shop {session_shop_id}, switching")
                request.session.pop('current_shop_id', None)
                request.session.pop('current_shop_schema', None)
                
                # Set first available shop as current
                new_shop = accessible_shops[0]
                request.session['current_shop_id'] = new_shop.id
                request.session['current_shop_schema'] = new_shop.schema_name
                user.current_shop_id = new_shop.id
                
                return JsonResponse({
                    'error': 'SHOP_ACCESS_REVOKED',
                    'message': f'Your access to the previous shop has been revoked. You have been switched to {new_shop.name}.',
                    'current_shop': {
                        'id': new_shop.id,
                        'name': new_shop.name
                    }
                }, status=200)  # 200 with warning instead of 403
        
        # Set current shop if not set
        if not getattr(user, 'current_shop_id', None):
            if session_shop_id:
                user.current_shop_id = session_shop_id
            else:
                # Auto-select first shop
                first_shop = accessible_shops[0]
                request.session['current_shop_id'] = first_shop.id
                request.session['current_shop_schema'] = first_shop.schema_name
                user.current_shop_id = first_shop.id
                
                if settings.DEBUG:
                    logger.debug(f"Auto-selected shop {first_shop.name} for user {user.id}")
        
        # CRITICAL: Re-register database connection with correct shop schema
        # This ensures all subsequent queries use the correct shop's schema
        # TenantMiddleware runs before authentication, so we need to fix the schema here
        current_shop_id = getattr(user, 'current_shop_id', None)
        if current_shop_id:
            tenant = getattr(request, 'tenant', None)
            if tenant:
                try:
                    shop = Shop.objects.get(id=current_shop_id, tenant=tenant, is_active=True)
                    # Close existing connection to force reconnect with new schema
                    if tenant.db_alias in connections:
                        connections[tenant.db_alias].close()
                    # Re-register with correct shop schema
                    register_tenant_connection(tenant, shop=shop)
                    set_current_shop(shop.schema_name)
                    if settings.DEBUG:
                        logger.debug(f"Re-registered connection with shop schema: {shop.schema_name}")
                except Shop.DoesNotExist:
                    logger.warning(f"Current shop {current_shop_id} not found")
        
        return None  # Valid