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
    
    Supports multiple identification methods:
    1. Subdomain: tenant1.example.com
    2. Custom domain: custom-domain.com
    3. Header: X-Tenant-Slug
    4. Development: localhost with tenant parameter or default tenant
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
                # Register tenant database connection
                register_tenant_connection(tenant)
                
                # Set tenant context
                set_current_tenant(tenant)
                
                # Identify and set shop (if applicable)
                shop = self._identify_shop(request, tenant)
                if shop:
                    set_current_shop(shop.schema_name)
                    request.shop = shop
                
                request.tenant = tenant
                logger.debug(f"Tenant set: {tenant.name} (shop: {shop.name if shop else 'None'})")
            else:
                # No tenant found
                request.tenant = None
                request.shop = None
                logger.warning("No tenant identified for request")
        
        except Exception as e:
            logger.error(f"Error in tenant middleware: {str(e)}")
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
        Priority: JWT Token > Domain/Subdomain > Header (development only) > Query Parameter
        
        SECURITY: JWT token is authoritative source of tenant (signed by server)
        Headers/queries are NOT trusted for tenant identification
        """
        # Method 0: Try to extract tenant from JWT token first (MOST SECURE)
        tenant = self._get_tenant_from_jwt(request)
        if tenant:
            logger.debug(f"Tenant from JWT token: {tenant.slug}")
            return tenant
        
        # Get the host
        host = request.get_host().split(':')[0]  # Remove port if present
        logger.debug(f"Parsing host: {host}")
        
        # Method 1: Check for development/localhost
        if self._is_local_host(host):
            return self._handle_localhost(request)
        
        # Method 2: Check for custom domain
        tenant = self._get_tenant_by_domain(host)
        if tenant:
            logger.debug(f"Tenant from custom domain: {tenant.slug}")
            return tenant
        
        # Method 3: Extract from subdomain
        tenant = self._get_tenant_from_subdomain(host)
        if tenant:
            logger.debug(f"Tenant from subdomain: {tenant.slug}")
            return tenant
        
        logger.warning(f"No tenant found for host: {host}")
        return None
    
    def _get_tenant_from_jwt(self, request):
        """
        Extract and validate tenant from JWT token in httpOnly cookie.
        This is the most secure method as JWT is signed by the server.
        """
        try:
            access_token = request.COOKIES.get('access_token')
            if not access_token:
                return None
            
            from rest_framework_simplejwt.tokens import AccessToken
            token = AccessToken(access_token)
            tenant_id = token.get('tenant_id')
            
            if tenant_id:
                from tenancy.models import Tenant
                tenant = Tenant.objects.filter(id=tenant_id).first()
                if tenant:
                    logger.debug(f"JWT token validated for tenant_id={tenant_id}")
                    return tenant
                else:
                    logger.warning(f"JWT has invalid tenant_id={tenant_id}")
        except Exception as e:
            logger.debug(f"JWT extraction failed (expected for non-authenticated requests): {str(e)}")
        
        return None
    
    def _is_local_host(self, host):
        """Check if host is localhost or IP address."""
        local_hosts = ['localhost', '127.0.0.1', '0.0.0.0', '[::1]']
        
        # Check exact matches
        if host in local_hosts:
            return True
        
        # Check if it's an IP address (simple check)
        ip_pattern = re.compile(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$')
        if ip_pattern.match(host):
            return True
        
        return False
    
    def _handle_localhost(self, request):
        """
        Handle localhost development scenarios.
        
        Options:
        1. Use query parameter: ?tenant=acme
        2. Use default tenant from settings
        3. Use first active tenant
        """
        # Option 1: Check for tenant query parameter
        tenant_param = request.GET.get('tenant')
        if tenant_param:
            logger.debug(f"Using tenant from query param: {tenant_param}")
            tenant = self._get_tenant_by_slug(tenant_param)
            if tenant:
                return tenant
        
        # Option 2: Use default tenant from settings
        default_tenant_slug = getattr(settings, 'DEFAULT_TENANT_SLUG', None)
        if default_tenant_slug:
            logger.debug(f"Using default tenant from settings: {default_tenant_slug}")
            tenant = self._get_tenant_by_slug(default_tenant_slug)
            if tenant:
                return tenant
        
        # Option 3: Use first active tenant (development only!)
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
            logger.warning("MAIN_DOMAIN not configured in settings")
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
        
        logger.debug(f"Extracted subdomain: {subdomain}")
        return self._get_tenant_by_slug(subdomain)
    
    def _get_tenant_by_slug(self, slug):
        """Get tenant by slug."""
        try:
            return Tenant.objects.get(slug=slug, is_active=True)
        except Tenant.DoesNotExist:
            logger.warning(f"Tenant not found: {slug}")
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
        Identify shop from request.
        
        Methods:
        1. Header: X-Shop-Slug
        2. Query parameter: ?shop=downtown
        3. Session: request.session.get('shop_id')
        4. Default shop for tenant
        """
        # Method 1: Check header
        shop_slug = request.headers.get('X-Shop-Slug')
        if shop_slug:
            try:
                return Shop.objects.get(
                    tenant=tenant,
                    subdomain=shop_slug,
                    is_active=True
                )
            except Shop.DoesNotExist:
                logger.warning(f"Shop not found: {shop_slug}")
        
        # Method 2: Check query parameter
        shop_param = request.GET.get('shop')
        if shop_param:
            try:
                # Try by subdomain first
                return Shop.objects.get(
                    tenant=tenant,
                    subdomain=shop_param,
                    is_active=True
                )
            except Shop.DoesNotExist:
                # Try by ID
                try:
                    return Shop.objects.get(
                        tenant=tenant,
                        id=int(shop_param),
                        is_active=True
                    )
                except (Shop.DoesNotExist, ValueError):
                    logger.warning(f"Shop not found: {shop_param}")
        
        # Method 3: Check session
        if hasattr(request, 'session') and 'shop_id' in request.session:
            try:
                return Shop.objects.get(
                    tenant=tenant,
                    id=request.session['shop_id'],
                    is_active=True
                )
            except Shop.DoesNotExist:
                logger.warning(f"Shop from session not found: {request.session['shop_id']}")
        
        # Method 4: Use default shop if configured
        default_shop = getattr(settings, 'USE_DEFAULT_SHOP', False)
        if default_shop:
            shop = Shop.objects.filter(tenant=tenant, is_active=True).first()
            if shop:
                logger.debug(f"Using default shop: {shop.subdomain or shop.name}")
                return shop
        
        return None


class TenantRequiredMiddleware:
    """
    Middleware to enforce that a valid tenant must be identified.
    Returns 404 if no tenant is found.
    
    Place this AFTER TenantMiddleware in MIDDLEWARE.
    """
    
    # Paths that don't require a tenant
    EXEMPT_PATHS = [
        '/health/',
        '/metrics/',
        '/static/',
        '/media/',
    ]
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Check if path is exempt
        if self._is_exempt(request.path):
            return self.get_response(request)
        
        # Check if tenant is set
        if not hasattr(request, 'tenant') or request.tenant is None:
            logger.error(f"No tenant for path: {request.path}")
            
            if request.path.startswith('/api/'):
                return JsonResponse({
                    'error': 'Tenant not found',
                    'detail': 'Please specify a valid tenant'
                }, status=404)
            else:
                return HttpResponseNotFound(
                    '<h1>Tenant Not Found</h1>'
                    '<p>Please access this application through a valid tenant domain.</p>'
                )
        
        return self.get_response(request)
    
    def _is_exempt(self, path):
        """Check if path is exempt from tenant requirement."""
        for exempt_path in self.EXEMPT_PATHS:
            if path.startswith(exempt_path):
                return True
        return False