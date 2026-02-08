# tenancy/jwt_authentication.py
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, AuthenticationFailed
from shop_users.models import ShopUser
from tenancy.models import Tenant
from tenancy.tenant_context import get_current_tenant
import logging

logger = logging.getLogger(__name__)


class TenantJWTAuthentication(JWTAuthentication):
    """
    Custom JWT authentication that validates tenant context.
    Reads JWT from httpOnly cookies (secure) instead of headers.
    """
    
    def get_raw_token(self, request):
        """
        Override to get JWT from httpOnly cookie instead of Authorization header.
        Falls back to Authorization header for API compatibility.
        """
        try:
            logger.info(f"get_raw_token() called")
            logger.info(f"Cookies: {list(request.COOKIES.keys())}")
            
            # Try to get from httpOnly cookie first
            token = request.COOKIES.get('access_token')
            if token:
                logger.info(f"JWT token found in cookie, length={len(token)}")
                return token.encode()
            
            logger.warning("JWT token not in cookie, checking Authorization header")
            # Fall back to Authorization header (for API clients)
            result = super().get_raw_token(request)
            logger.info(f"Authorization header result: {result is not None}")
            return result
        except Exception as e:
            logger.error(f"get_raw_token() exception: {str(e)}")
            raise
    
    def authenticate(self, request):
        """
        Authenticate using JWT from cookie or Authorization header.
        Returns None if authentication is not attempted (allows public endpoints to work).
        Only raises AuthenticationFailed if authentication is attempted but fails.
        """
        logger.info(f"TenantJWTAuthentication.authenticate() called, path={request.path}")
        logger.info(f"Request cookies: {list(request.COOKIES.keys())}")
        
        try:
            # Try to get token from httpOnly cookie first
            token = request.COOKIES.get('access_token')
            if not token:
                logger.debug("No access_token in cookies, checking Authorization header")
                # Fall back to parent's method which checks Authorization header
                try:
                    result = super().authenticate(request)
                    if result is None:
                        logger.debug("No Authorization header found, allowing public/anonymous access")
                        return None
                except (AuthenticationFailed, InvalidToken) as e:
                    # Authentication was attempted but failed - propagate the error
                    logger.warning(f"Authorization header authentication failed: {str(e)}")
                    raise
                except Exception as e:
                    # Log unexpected errors, but for authentication we return None (not authenticated)
                    logger.debug(f"Authorization header check failed: {str(e)}")
                    return None
            else:
                logger.debug(f"Token found in cookie, length={len(token)}")
                # Decode the token manually
                from rest_framework_simplejwt.tokens import AccessToken
                try:
                    validated_token = AccessToken(token)
                    logger.debug(f"Token validated successfully")
                    result = self.get_user(validated_token), validated_token
                except (AuthenticationFailed, InvalidToken) as e:
                    logger.warning(f"Token validation failed: {str(e)}")
                    raise
                except Exception as e:
                    logger.error(f"Failed to decode token: {str(e)}")
                    raise AuthenticationFailed(f"Token validation error: {str(e)}")
            
            if result is None:
                logger.debug(f"JWT authentication returned None")
                return None
            
            user, validated_token = result
            logger.info(f"JWT authenticated user: {user.username}, token_tenant_id={validated_token.get('tenant_id')}")
            
            # Get tenant from token
            token_tenant_id = validated_token.get('tenant_id')
            token_tenant_slug = validated_token.get('tenant_slug')
            
            # Get current tenant from context (set by middleware)
            current_tenant = get_current_tenant()
            
            # Validate tenant context
            if current_tenant:
                # If there's a current tenant, validate it matches the token
                if token_tenant_id and current_tenant.id != token_tenant_id:
                    logger.warning(
                        f"Tenant mismatch: token has {token_tenant_id}, "
                        f"context has {current_tenant.id}"
                    )
                    raise AuthenticationFailed('Tenant mismatch')
            elif token_tenant_id:
                # If no current tenant in context but token has one,
                # try to load it (for API calls without middleware)
                try:
                    tenant = Tenant.objects.get(id=token_tenant_id)
                    from tenancy.tenant_context import set_current_tenant
                    set_current_tenant(tenant)
                except Tenant.DoesNotExist:
                    raise AuthenticationFailed('Invalid tenant in token')
            
            # Validate user belongs to tenant
            if hasattr(user, 'tenant_id') and token_tenant_id:
                if user.tenant_id != token_tenant_id:
                    raise AuthenticationFailed('User does not belong to this tenant')
            
            return user, validated_token
            
        except (AuthenticationFailed, InvalidToken) as e:
            # Authentication was attempted but failed - propagate the error
            raise
        except Exception as e:
            logger.error(f"Unexpected JWT authentication error: {str(e)}")
            # For unexpected errors during authentication, log and return None
            # This prevents 500 errors on authentication issues
            return None
    
    def get_user(self, validated_token):
        """
        Override to get user from ShopUser model (from tenant database)
        """
        try:
            user_id = validated_token.get('user_id')
            if user_id is None:
                raise InvalidToken('Token contained no recognizable user identification')

            # Log tenant context
            tenant = get_current_tenant()
            token_tenant_id = validated_token.get('tenant_id')
            token_tenant_slug = validated_token.get('tenant_slug')
            logger.info(f"JWT get_user: user_id={user_id}, context_tenant={tenant}, token_tenant_id={token_tenant_id}, token_tenant_slug={token_tenant_slug}")

            # If token has tenant info, use it (most reliable)
            if token_tenant_id or token_tenant_slug:
                try:
                    if token_tenant_slug:
                        tenant = Tenant.objects.get(slug=token_tenant_slug)
                    elif token_tenant_id:
                        tenant = Tenant.objects.get(id=token_tenant_id)
                    
                    from tenancy.tenant_context import set_current_tenant
                    from tenancy.utils import register_tenant_connection
                    register_tenant_connection(tenant)
                    set_current_tenant(tenant)
                    logger.info(f"Set tenant from token: {tenant.slug}")
                except Tenant.DoesNotExist:
                    logger.error(f"Tenant from token not found: id={token_tenant_id}, slug={token_tenant_slug}")
                    raise AuthenticationFailed('Tenant not found')
            else:
                # Token doesn't have tenant info - try to find user in any tenant
                # This handles old tokens created before tenant info was added
                logger.warning(f"Token has no tenant info, searching for user {user_id} across all tenants")
                user_found = None
                found_tenant = None
                
                for search_tenant in Tenant.objects.all():
                    try:
                        from tenancy.utils import register_tenant_connection
                        register_tenant_connection(search_tenant)
                        test_user = ShopUser.objects.using(search_tenant.db_alias).get(id=user_id)
                        user_found = test_user
                        found_tenant = search_tenant
                        logger.info(f"Found user {user_id} in tenant: {search_tenant.slug}")
                        break
                    except ShopUser.DoesNotExist:
                        continue
                
                if found_tenant:
                    from tenancy.tenant_context import set_current_tenant
                    from tenancy.utils import register_tenant_connection
                    register_tenant_connection(found_tenant)
                    set_current_tenant(found_tenant)
                    tenant = found_tenant
                else:
                    logger.error(f"User {user_id} not found in any tenant")
                    raise AuthenticationFailed('User not found in any tenant')

            # Get user from tenant database
            if tenant:
                logger.info(f"Querying user from tenant DB: {tenant.db_alias}")
                user = ShopUser.objects.using(tenant.db_alias).get(id=user_id)
            else:
                logger.warning(f"No tenant context for user {user_id}, querying main DB")
                user = ShopUser.objects.get(id=user_id)

            if not user.is_active:
                raise AuthenticationFailed('User is inactive')

            return user

        except ShopUser.DoesNotExist:
            logger.error(f"JWT get_user: User {user_id} not found")
            raise AuthenticationFailed('User not found')