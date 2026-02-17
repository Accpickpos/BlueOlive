"""
API Key Authentication for external integrations (e.g., Stockfinder).
Based on Django REST Framework's TokenAuthentication.

SECURITY IMPROVEMENTS:
- API keys are now bound to specific tenants
- Returns a service user instead of None for proper permission checking
- Validates tenant context to prevent cross-tenant access
"""
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.utils import timezone
from django.conf import settings
from .models import APIKey
from tenancy.tenant_context import get_current_tenant
from tenancy.utils import register_tenant_connection
import logging

logger = logging.getLogger(__name__)


class APIKeyAuthentication(TokenAuthentication):
    """
    Custom authentication class for API key authentication.
    
    Accepts API keys in the Authorization header:
    Authorization: ApiKey <api_key>
    
    Also supports X-API-Key header for convenience:
    X-API-Key: <api_key>
    
    SECURITY:
    - API keys are tenant-bound (each key belongs to one tenant)
    - Validates that the request's tenant matches the API key's tenant
    - Returns a service user for proper permission checking
    """
    
    keyword = 'ApiKey'
    model = APIKey
    
    def authenticate(self, request):
        """
        Authenticate the request using an API key.
        
        Returns:
            tuple: (user, auth) if authenticated, None otherwise
        """
        # Try standard Authorization header first
        auth = self.get_authorization_header(request).split()
        
        if not auth:
            # Try custom X-API-Key header
            key = request.META.get('HTTP_X_API_KEY')
            if key:
                auth = [self.keyword.encode(), key.encode()]
            else:
                return None
        
        if len(auth) == 1:
            msg = 'Invalid token header. No credentials provided.'
            raise AuthenticationFailed(msg)
        elif len(auth) > 2:
            msg = 'Invalid token header. Token string should not contain spaces.'
            raise AuthenticationFailed(msg)
        
        try:
            token = auth[1].decode()
        except UnicodeDecodeError:
            msg = 'Invalid token header. Token string should not contain invalid characters.'
            raise AuthenticationFailed(msg)
        
        return self.authenticate_credentials(token, request)
    
    def authenticate_credentials(self, key, request=None):
        """
        Authenticate the API key with tenant validation.
        
        Args:
            key: API key string
            request: HTTP request object
        
        Returns:
            tuple: (service_user, api_key) if valid
        
        Raises:
            AuthenticationFailed: If key is invalid, expired, or tenant mismatch
        """
        try:
            # Select related tenant for efficient queries
            api_key = APIKey.objects.select_related('tenant').get(key=key)
        except APIKey.DoesNotExist:
            raise AuthenticationFailed('Invalid API key.')
        
        # Check if API key is valid (status and expiration)
        if not api_key.is_valid:
            raise AuthenticationFailed('API key is not active or has expired.')
        
        # SECURITY: Validate tenant binding
        if request:
            # Get tenant from request (set by TenantMiddleware)
            request_tenant = getattr(request, 'tenant', None)
            
            if request_tenant is None:
                # Try to get from tenant context
                request_tenant = get_current_tenant()
            
            # Validate tenant match
            if request_tenant and api_key.tenant_id != request_tenant.id:
                logger.warning(
                    f"Tenant mismatch: API key tenant={api_key.tenant_id}, "
                    f"request tenant={request_tenant.id}"
                )
                raise AuthenticationFailed(
                    'API key does not belong to this tenant'
                )
            
            # If no tenant context yet, set it up from the API key's tenant
            if not request_tenant:
                # Register the API key's tenant connection
                register_tenant_connection(api_key.tenant)
                
                # Import and set tenant context
                from tenancy.tenant_context import set_current_tenant
                set_current_tenant(api_key.tenant)
                
                # Store tenant on request for later use
                request.tenant = api_key.tenant
        
        # Create or get service user for this API key
        # This allows proper permission checking based on user.role
        service_user = self._get_or_create_service_user(api_key)
        
        # Record usage
        if request:
            client_ip = self.get_client_ip(request)
            self._record_usage(api_key, client_ip)
        
        # Return (service_user, api_key) instead of (None, api_key)
        # This enables proper permission checking using request.user.role
        return (service_user, api_key)
    
    def _get_or_create_service_user(self, api_key):
        """
        Create or get a service user for the API key.
        
        Service users are created in the tenant's database and are used
        to enable proper permission checking for API key authentication.
        
        Args:
            api_key: APIKey instance
        
        Returns:
            ShopUser instance (service user)
        """
        # Import here to avoid circular imports
        from shop_users.models import ShopUser
        
        # Generate service username from external service name
        service_username = f"svc_{api_key.external_service.lower().replace(' ', '_')}"
        
        try:
            # Try to get existing service user from tenant database
            service_user = ShopUser.objects.using(api_key.tenant.db_alias).get(
                username=service_username
            )
            
            # Ensure user is active
            if not service_user.is_active:
                service_user.is_active = True
                service_user.save(using=api_key.tenant.db_alias)
            
            return service_user
            
        except ShopUser.DoesNotExist:
            # Create new service user
            service_user = ShopUser.objects.using(api_key.tenant.db_alias).create(
                username=service_username,
                email=f"{api_key.external_service.lower().replace(' ', '.')}@api.local",
                is_active=True,
                role='API_SERVICE',  # Custom role for API service accounts
                first_name=api_key.external_service,
                last_name='API Service',
            )
            
            if settings.DEBUG:
                logger.debug(
                    f"Created service user '{service_username}' in tenant "
                    f"'{api_key.tenant.slug}'"
                )
            
            return service_user
    
    def _record_usage(self, api_key, ip_address):
        """
        Record API key usage (last used timestamp and IP).
        
        Args:
            api_key: APIKey instance
            ip_address: Client IP address string
        """
        api_key.last_used = timezone.now()
        api_key.last_ip = ip_address
        api_key.save(update_fields=['last_used', 'last_ip'])
    
    @staticmethod
    def get_client_ip(request):
        """
        Get client IP address from request.
        
        Handles proxies and load balancers.
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
