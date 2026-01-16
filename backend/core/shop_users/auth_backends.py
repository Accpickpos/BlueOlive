"""
Multi-tenant authentication backend for ShopUser model.

This backend implements tenant-aware authentication with the following rules:
1. Superusers can authenticate from any tenant context
2. Regular users can only authenticate within their assigned tenant
3. If no tenant context exists, only superusers can authenticate

Security features:
- Timing attack protection via dummy password checks
- Rate limiting support hooks
- Comprehensive authentication logging
- Active tenant validation on every request
"""

import logging
from django.contrib.auth.backends import BaseBackend
from django.core.cache import cache
from django.utils import timezone
from tenancy.tenant_context import get_current_tenant

logger = logging.getLogger(__name__)


class ShopUserBackend(BaseBackend):
    """
    Custom authentication backend for multi-tenant ShopUser model.
    
    Supports:
    - Tenant-isolated user authentication
    - Superuser bypass for cross-tenant access
    - Security hardening against timing attacks
    """
    
    # Rate limiting settings
    MAX_LOGIN_ATTEMPTS = 5
    LOCKOUT_DURATION = 300  # 5 minutes in seconds
    
    def user_can_authenticate(self, user):
        """
        Reject users with is_active=False. Custom user models that don't have
        that attribute are allowed.
        """
        return getattr(user, 'is_active', True)
    
    def _check_rate_limit(self, username, request=None):
        """
        Check if the user has exceeded login attempt limits.
        
        Args:
            username: The username attempting to authenticate
            request: The HTTP request object (optional, used for IP logging)
            
        Returns:
            tuple: (is_allowed: bool, attempts_remaining: int)
        """
        cache_key = f'login_attempts:{username}'
        attempts = cache.get(cache_key, 0)
        
        if attempts >= self.MAX_LOGIN_ATTEMPTS:
            logger.warning(
                f'Rate limit exceeded for username: {username}, '
                f'IP: {self._get_client_ip(request)}'
            )
            return False, 0
        
        return True, self.MAX_LOGIN_ATTEMPTS - attempts
    
    def _record_failed_attempt(self, username, request=None):
        """
        Record a failed login attempt for rate limiting.
        
        Args:
            username: The username that failed authentication
            request: The HTTP request object (optional)
        """
        cache_key = f'login_attempts:{username}'
        attempts = cache.get(cache_key, 0)
        cache.set(cache_key, attempts + 1, self.LOCKOUT_DURATION)
        
        logger.info(
            f'Failed login attempt #{attempts + 1} for username: {username}, '
            f'IP: {self._get_client_ip(request)}'
        )
    
    def _clear_failed_attempts(self, username):
        """
        Clear failed login attempts after successful authentication.
        
        Args:
            username: The username to clear attempts for
        """
        cache_key = f'login_attempts:{username}'
        cache.delete(cache_key)
    
    def _get_client_ip(self, request):
        """
        Extract client IP address from request.
        
        Args:
            request: The HTTP request object
            
        Returns:
            str: Client IP address or 'unknown'
        """
        if not request:
            return 'unknown'
        
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', 'unknown')
        return ip
    
    def _perform_dummy_password_check(self):
        """
        Perform a dummy password check to prevent timing attacks.
        
        This ensures that failed authentication attempts take approximately
        the same time regardless of whether the user exists or not.
        """
        from .models import ShopUser
        # Create a temporary user instance and hash a dummy password
        dummy_user = ShopUser()
        dummy_user.set_password('dummy_password_for_timing_protection')
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Authenticate a user based on username, password, and tenant context.
        
        Args:
            request: The HTTP request object
            username: The username to authenticate
            password: The password to check
            **kwargs: Additional keyword arguments
            
        Returns:
            ShopUser instance if authentication succeeds, None otherwise
        """
        from .models import ShopUser
        
        # Validate input parameters
        if username is None or password is None:
            logger.debug('Authentication failed: missing username or password')
            return None
        
        # Check rate limiting
        is_allowed, attempts_remaining = self._check_rate_limit(username, request)
        if not is_allowed:
            logger.warning(
                f'Authentication blocked due to rate limiting: {username}, '
                f'IP: {self._get_client_ip(request)}'
            )
            return None
        
        tenant = get_current_tenant()
        logger.info(f"Authenticate called for username: {username}, current tenant: {tenant.name if tenant else 'None'}")
        authenticated_user = None
        
        # Strategy 1: Try to authenticate as superuser (tenant-independent)
        try:
            user = ShopUser._base_manager.get(username=username, is_superuser=True)
            if user.check_password(password) and self.user_can_authenticate(user):
                authenticated_user = user
                logger.info(
                    f'Superuser authenticated: {username}, '
                    f'tenant: {tenant.name if tenant else "None"}, '
                    f'IP: {self._get_client_ip(request)}'
                )
        except ShopUser.DoesNotExist:
            # Run dummy password check to prevent timing attacks
            self._perform_dummy_password_check()
        
        # If superuser authentication succeeded, return early
        if authenticated_user:
            self._clear_failed_attempts(username)
            return authenticated_user
        
        # Strategy 2: Try tenant-specific authentication
        if not tenant:
            # If no tenant context, only superusers can login
            logger.info(
                f'Authentication failed: no tenant context for non-superuser {username}, '
                f'IP: {self._get_client_ip(request)}'
            )
            self._record_failed_attempt(username, request)
            return None
        
        try:
            user = ShopUser.objects.get(username=username)
            logger.debug(f"Found user: {username}, user tenant_id: {user.tenant_id}, current tenant id: {tenant.id if tenant else 'None'}")
            logger.debug(f"User {username} shop_id: {user.shop_id}")
            password_valid = user.check_password(password)
            can_auth = self.user_can_authenticate(user)
            logger.debug(f"Password valid: {password_valid}, can authenticate: {can_auth}")
            if password_valid and can_auth:
                authenticated_user = user
                logger.info(
                    f'Tenant user authenticated: {username}, '
                    f'tenant: {tenant.name}, '
                    f'IP: {self._get_client_ip(request)}'
                )
            else:
                logger.info(
                    f'Authentication failed: invalid credentials for user {username}, '
                    f'password valid: {password_valid}, active: {can_auth}, '
                    f'tenant: {tenant.name}, '
                    f'IP: {self._get_client_ip(request)}'
                )
        except ShopUser.DoesNotExist:
            # Run dummy password check to prevent timing attacks
            self._perform_dummy_password_check()
            logger.info(
                f'Authentication failed: user not found in tenant, '
                f'username: {username}, '
                f'tenant: {tenant.name}, '
                f'IP: {self._get_client_ip(request)}'
            )
        
        # Handle authentication result
        if authenticated_user:
            self._clear_failed_attempts(username)
            return authenticated_user
        else:
            self._record_failed_attempt(username, request)
            return None
    
    def get_user(self, user_id):
        """
        Retrieve a user by ID and validate against current tenant context.
        
        This method is called on every request to retrieve the authenticated user
        from the session. It enforces tenant isolation by validating that regular
        users can only be retrieved within their assigned tenant context.
        
        Args:
            user_id: The primary key of the user to retrieve
            
        Returns:
            ShopUser instance if found and valid, None otherwise
        """
        from .models import ShopUser
        
        try:
            # Use base manager to bypass tenant filters
            user = ShopUser._base_manager.get(pk=user_id)
            logger.debug(f"User {user.username} tenant_id: {user.tenant_id}, shop_id: {user.shop_id}")
        except ShopUser.DoesNotExist:
            logger.debug(f'get_user failed: user_id {user_id} not found')
            return None
        
        # Check if user is active
        if not self.user_can_authenticate(user):
            logger.debug(
                f'get_user failed: user {user.username} (id={user_id}) is not active'
            )
            return None
        
        # Superusers can access from any tenant context
        if user.is_superuser:
            return user
        
        # Regular users must match current tenant
        user_tenant = user.get_tenant()
        if user_tenant:
            tenant = get_current_tenant()
            logger.debug(f"get_user: user {user.username} (id={user_id}), user tenant: {user_tenant.name}, current tenant: {tenant.name if tenant else 'None'}")

            if not tenant:
                logger.warning(
                    f'get_user failed: no tenant context for user {user.username} (id={user_id})'
                )
                return None

            if tenant != user_tenant:
                logger.warning(
                    f'get_user failed: tenant mismatch for user {user.username} (id={user_id}), '
                    f'user tenant: {user_tenant.name}, current tenant: {tenant.name}'
                )
                return None
        
        return user