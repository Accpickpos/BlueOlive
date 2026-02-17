# tenancy/middleware.py
import logging
import re
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
                # Register tenant database connection (CRITICAL!)
                register_tenant_connection(tenant)
                
                # Set tenant context
                set_current_tenant(tenant)
                
                # Identify and set shop (if applicable)
                shop = self._identify_shop(request, tenant)
                if shop:
                    set_current_shop(shop.schema_name)
                    request.shop = shop
                
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
        
        # Method 2: From session (ONLY for authenticated users)
        if not shop and hasattr(request, 'session') and 'shop_id' in request.session:
            # SECURITY: Only allow session shop for authenticated users
            if hasattr(request, 'user') and request.user.is_authenticated:
                try:
                    shop = Shop.objects.get(
                        tenant=tenant,
                        id=request.session['shop_id'],
                        is_active=True
                    )
                    if settings.DEBUG:
                        logger.debug(f"Shop from session: {shop.name}")
                except Shop.DoesNotExist:
                    logger.warning(f"Session shop not found: {request.session['shop_id']}")
            else:
                if settings.DEBUG:
                    logger.debug("Ignoring session shop for unauthenticated user")
        
        # Method 3: Development mode - allow header/query param override
        # SECURITY: Only in DEBUG mode
        if not shop and settings.DEBUG:
            shop = self._identify_shop_dev(request, tenant)
        
        # Method 4: Default shop fallback
        if not shop:
            default_shop_enabled = getattr(settings, 'USE_DEFAULT_SHOP', False)
            if default_shop_enabled:
                # Query from default database (Shop model is in main DB)
                shop = Shop.objects.using('default').filter(
                    tenant=tenant, 
                    is_active=True
                ).first()
                if shop and settings.DEBUG:
                    logger.debug(f"Using default shop: {shop.subdomain or shop.name}")
        
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