from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework import viewsets, status
from rest_framework.throttling import AnonRateThrottle
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie, csrf_exempt
from django.conf import settings
import logging

from django.contrib.auth import authenticate
from tenancy.tenant_context import get_current_tenant, set_current_tenant
from tenancy.audit import LoginAuditLog, UserAuditLog
from tenancy.jwt_authentication import TenantJWTAuthentication
from tenancy.models import Tenant
from shop_users.models import ShopUser
from shop_users.serializers import ShopUserSerializer

logger = logging.getLogger(__name__)


class LoginThrottle(AnonRateThrottle):
    """Rate limit login attempts to 5 per minute per IP"""
    scope = 'login'
    rate = '5/min'


@method_decorator(csrf_exempt, name='dispatch')
class GetCSRFTokenView(APIView):
    """
    GET endpoint to retrieve CSRF token for unauthenticated users.
    This is required for POST requests with CSRF protection enabled.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        try:
            if settings.DEBUG:
                logger.debug(f"GetCSRFTokenView called for {request.method} {request.path}")
            
            # Manually set CSRF cookie
            from django.middleware.csrf import get_token
            csrf_token = get_token(request)
            
            response = Response({'detail': 'CSRF token set in cookie'}, status=200)
            # The cookie is automatically set by Django's CSRF middleware,
            # but we can explicitly ensure it's there
            response['X-CSRFToken'] = csrf_token
            
            return response
        except Exception as e:
            logger.error(f"GetCSRFTokenView error: {str(e)}", exc_info=True)
            raise


class TenantTokenView(APIView):
    """
    Login view that authenticates users and sets JWT tokens in httpOnly cookies.
    """
    permission_classes = [AllowAny]
    throttle_classes = [LoginThrottle]

    @method_decorator(csrf_exempt, name='dispatch')
    def post(self, request):
        try:
            # Always prioritize tenant_slug from request over context
            tenant_slug = request.data.get('tenant_slug')
            tenant = None
            
            # If tenant_slug is provided, use it (takes precedence)
            if tenant_slug:
                try:
                    tenant = Tenant.objects.get(slug=tenant_slug)
                    set_current_tenant(tenant)
                    if settings.DEBUG:
                        logger.debug(f"Login: Using tenant from request: {tenant.name}")
                    
                    # Register the tenant database connection
                    from tenancy.utils import register_tenant_connection
                    register_tenant_connection(tenant)
                except Tenant.DoesNotExist:
                    logger.error(f"Tenant not found: {tenant_slug}")
                    LoginAuditLog.log_login_failed(request, username=request.data.get('username'))
                    raise AuthenticationFailed(f"Tenant '{tenant_slug}' not found")
            else:
                # Fall back to context tenant (for backward compatibility)
                tenant = get_current_tenant()
                if tenant and settings.DEBUG:
                    logger.debug(f"Login: Using tenant from context: {tenant.name}")
            
            if not tenant:
                LoginAuditLog.log_login_failed(request, username=request.data.get('username'))
                raise AuthenticationFailed("Tenant not resolved")

            username = request.data.get("username")
            password = request.data.get("password")

            if not username or not password:
                LoginAuditLog.log_login_failed(request, username=username)
                raise AuthenticationFailed("Missing credentials")

            if settings.DEBUG:
                logger.debug(f"Authenticating user: {username}")
            
            user = authenticate(
                request,
                username=username,
                password=password,
            )

            if not user:
                LoginAuditLog.log_login_failed(request, username=username)
                raise AuthenticationFailed("Invalid credentials")

            if not user.is_superuser and user.tenant_id != tenant.id:
                LoginAuditLog.log_login_failed(request, username=username)
                raise AuthenticationFailed("User does not belong to tenant")

            # Create tokens with tenant context
            refresh = RefreshToken()
            refresh['user_id'] = user.id
            refresh['username'] = user.username
            refresh['email'] = getattr(user, 'email', '')
            refresh['tenant_id'] = tenant.id
            refresh['tenant_slug'] = tenant.slug

            access_token = str(refresh.access_token)
            refresh_token = str(refresh)

            response = Response({
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "role": getattr(user, 'role', 'USER'),
                    "is_superuser": getattr(user, 'is_superuser', False),
                    "is_admin": getattr(user, 'role', '') == 'ADMIN' or getattr(user, 'is_superuser', False),
                }
            })

            # Set httpOnly cookies (secure, not accessible to JavaScript)
            # In DEBUG mode (local dev), use samesite='Lax' because samesite='None' requires HTTPS
            # In production, use samesite='None' for cross-origin cookie support
            is_secure = not settings.DEBUG
            samesite = 'Lax' if settings.DEBUG else 'None'
            
            response.set_cookie(
                key='access_token',
                value=access_token,
                max_age=int(settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds()),
                secure=is_secure,
                httponly=True,
                samesite=samesite,
                path='/',
            )
            
            response.set_cookie(
                key='refresh_token',
                value=refresh_token,
                max_age=int(settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds()),
                secure=is_secure,
                httponly=True,
                samesite=samesite,
                path='/',
            )

            # Log successful login
            LoginAuditLog.log_login(request, user)

            return response
        
        except AuthenticationFailed:
            raise
        except Exception as e:
            logger.error(f"Login error: {str(e)}", exc_info=True)
            raise AuthenticationFailed(f"Login failed: {str(e)}")


class CookieTokenRefreshView(TokenRefreshView):
    """
    Custom token refresh view that reads refresh token from httpOnly cookie
    instead of request body.
    
    This is the KEY FIX for your "No refresh token provided" error.
    """
    permission_classes = [AllowAny]
    authentication_classes = []  # No authentication needed for refresh
    
    @method_decorator(csrf_exempt, name='dispatch')
    def post(self, request, *args, **kwargs):
        """
        Override to get refresh token from cookie instead of body.
        """
        # Try to get refresh token from cookie
        refresh_token = request.COOKIES.get('refresh_token')
        
        if not refresh_token:
            logger.warning("Token refresh attempted without refresh_token cookie")
            return Response(
                {'detail': 'No refresh token provided'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        if settings.DEBUG:
            logger.debug("Attempting token refresh from cookie")
        
        # Add the token to request data for the parent class to process
        # Make request.data mutable
        if hasattr(request.data, '_mutable'):
            request.data._mutable = True
        request.data['refresh'] = refresh_token
        
        try:
            # Call parent's post method to handle token refresh
            response = super().post(request, *args, **kwargs)
            
            # If successful, set new tokens in cookies
            if response.status_code == 200:
                data = response.data
                access_token = data.get('access')
                new_refresh_token = data.get('refresh')  # New refresh token if rotation enabled
                
                is_secure = not settings.DEBUG
                
                # Set new access token cookie
                response.set_cookie(
                    key='access_token',
                    value=access_token,
                    max_age=int(settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds()),
                    secure=is_secure,
                    httponly=True,
                    samesite='Lax',
                    path='/',
                )
                
                # Set new refresh token cookie (if rotation is enabled)
                if new_refresh_token:
                    response.set_cookie(
                        key='refresh_token',
                        value=new_refresh_token,
                        max_age=int(settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds()),
                        secure=is_secure,
                        httponly=True,
                        samesite='Lax',
                        path='/',
                    )
                
                # Don't send tokens in response body (they're in cookies)
                response.data = {'detail': 'Token refreshed successfully'}
                
                if settings.DEBUG:
                    logger.debug("Token refresh successful")
            
            return response
            
        except (InvalidToken, TokenError) as e:
            logger.warning(f"Token refresh failed: {type(e).__name__}")
            return Response(
                {'detail': str(e)},
                status=status.HTTP_401_UNAUTHORIZED
            )
        except Exception as e:
            logger.error(f"Unexpected token refresh error: {str(e)}", exc_info=True)
            return Response(
                {'detail': 'Token refresh failed'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class LogoutView(APIView):
    """
    Logout by clearing cookies and blacklisting tokens.
    """
    permission_classes = [AllowAny]

    @method_decorator(csrf_exempt, name='dispatch')
    def post(self, request):
        try:
            # Get refresh token from cookie for blacklisting
            refresh_token = request.COOKIES.get('refresh_token')
            
            if refresh_token:
                try:
                    # Blacklist the refresh token
                    token = RefreshToken(refresh_token)
                    token.blacklist()
                    if settings.DEBUG:
                        logger.debug("Refresh token blacklisted")
                except Exception as e:
                    # Log but don't fail - still clear cookies
                    logger.warning(f"Failed to blacklist token: {str(e)}")
            
            # Log logout if user is authenticated
            if request.user and request.user.is_authenticated:
                LoginAuditLog.log_logout(request, request.user)
            
            # Create response
            response = Response(
                {'detail': 'Logout successful'},
                status=status.HTTP_200_OK
            )
            
            # Clear cookies
            # Use same samesite setting as when cookie was set
            samesite = 'Lax' if settings.DEBUG else 'None'
            response.delete_cookie('access_token', path='/', samesite=samesite)
            response.delete_cookie('refresh_token', path='/', samesite=samesite)
            
            return response
            
        except Exception as e:
            logger.error(f"Logout error: {str(e)}", exc_info=True)
            # Still clear cookies even if something fails
            response = Response(
                {'detail': 'Logout successful'},
                status=status.HTTP_200_OK
            )
            samesite = 'Lax' if settings.DEBUG else 'None'
            response.delete_cookie('access_token', path='/', samesite=samesite)
            response.delete_cookie('refresh_token', path='/', samesite=samesite)
            return response


class CurrentUserView(APIView):
    """Get current authenticated user information"""
    permission_classes = [IsAuthenticated]
    authentication_classes = [TenantJWTAuthentication]

    def get(self, request):
        try:
            user = request.user
            tenant = get_current_tenant()
            
            return Response({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'role': getattr(user, 'role', 'USER'),
                'is_superuser': user.is_superuser,
                'is_admin': getattr(user, 'role', '') == 'ADMIN' or user.is_superuser,
                'tenant': {
                    'id': tenant.id if tenant else None,
                    'name': tenant.name if tenant else None,
                    'slug': tenant.slug if tenant else None,
                } if tenant else None
            })
        except Exception as e:
            logger.error(f"Current user error: {str(e)}", exc_info=True)
            return Response(
                {'detail': 'Failed to get user information'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SignupView(APIView):
    """
    Tenant signup - creates new tenant, database, and admin user.
    """
    permission_classes = [AllowAny]
    throttle_classes = [LoginThrottle]

    @method_decorator(csrf_exempt, name='dispatch')
    def post(self, request):
        try:
            # Extract fields
            company_name = request.data.get('company_name')
            subdomain = request.data.get('subdomain')
            username = request.data.get('username')
            email = request.data.get('email')
            password = request.data.get('password')
            password_confirm = request.data.get('confirm_password')
            first_name = request.data.get('first_name', '')
            last_name = request.data.get('last_name', '')

            # ADD THIS DEBUG LOGGING
            if settings.DEBUG:
                logger.debug(f"Signup request data: {request.data}")
                logger.debug(f"company_name: {company_name}")
                logger.debug(f"subdomain: {subdomain}")
                logger.debug(f"username: {username}")
                logger.debug(f"email: {email}")
                logger.debug(f"password: {'***' if password else None}")
                logger.debug(f"confirm_password: {'***' if password_confirm else None}")

            # Validation - IMPROVED ERROR MESSAGE
            required_fields = {
                'company_name': company_name,
                'subdomain': subdomain,
                'username': username,
                'email': email,
                'password': password,
                'confirm_password': password_confirm,
            }
            
            missing_fields = [field for field, value in required_fields.items() if not value]
            
            if missing_fields:
                error_msg = f'Missing required fields: {", ".join(missing_fields)}'
                logger.warning(f"Signup validation failed: {error_msg}")
                return Response({'detail': error_msg}, status=400)

            # Rest of your validation...
            if password != password_confirm:
                return Response({'detail': 'Passwords do not match'}, status=400)

            if len(password) < 8:
                return Response({'detail': 'Password must be at least 8 characters'}, status=400)
            
            # Check if subdomain is available (main database check)
            if Tenant.objects.filter(subdomain=subdomain).exists():
                return Response({'detail': 'Subdomain already taken'}, status=400)

            # Create tenant
            from django.utils.text import slugify
            from tenancy.utils import create_tenant_database_postgres, register_tenant_connection
            
            tenant_slug = slugify(company_name)
            tenant_db_name = f"tenant_{subdomain}".replace('-', '_')
            
            # Get DB credentials from settings
            db_settings = settings.DATABASES.get('default', {})
            db_host = db_settings.get('HOST', 'localhost')
            db_port = db_settings.get('PORT', 5432)
            db_user = db_settings.get('USER', 'postgres')
            db_password = db_settings.get('PASSWORD', '')
            
            # Create tenant in main database
            tenant = Tenant.objects.create(
                name=company_name,
                slug=tenant_slug,
                subdomain=subdomain,
                db_name=tenant_db_name,
                db_user=db_user,
                db_password=db_password,
                db_host=db_host,
                db_port=int(db_port) if isinstance(db_port, str) else db_port,
                is_active=True,
                tenant_control=True,
            )
            logger.info(f"Created tenant: {tenant.name} (id={tenant.id})")

            # Create tenant database
            try:
                superuser_conn_info = {
                    'host': tenant.db_host,
                    'port': tenant.db_port,
                    'user': tenant.db_user,
                    'password': tenant.db_password,
                    'dbname': 'postgres'
                }
                create_tenant_database_postgres(tenant, superuser_conn_info)
                logger.info(f"Created tenant database: {tenant_db_name}")
            except Exception as e:
                logger.error(f"Failed to create tenant database: {str(e)}")
                tenant.delete()
                return Response({'detail': f'Failed to create tenant database: {str(e)}'}, status=500)

            # Register tenant connection
            register_tenant_connection(tenant)
            set_current_tenant(tenant)

            # Run migrations on tenant database
            try:
                from tenancy.shop_manager import migrate_tenant_database
                logger.info(f"Running migrations on tenant database: {tenant_db_name}")
                migrate_tenant_database(tenant)
                logger.info(f"✓ Migrations completed for tenant: {tenant.name}")
            except Exception as e:
                logger.error(f"Failed to run migrations on tenant database: {str(e)}")
                tenant.delete()
                return Response({'detail': f'Failed to run migrations: {str(e)}'}, status=500)

            # Ensure search_path is set for user creation
            try:
                from django.db import connections
                conn = connections[tenant.db_alias]
                conn.close()
                conn.connect()
                with conn.cursor() as cur:
                    cur.execute('SET search_path TO public')
            except Exception as e:
                logger.error(f"Failed to set search_path: {str(e)}")

            # Create user in tenant database
            try:
                user = ShopUser(
                    username=username,
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    tenant_id=tenant.id,
                    role='ADMIN',
                    is_staff=True,
                    is_superuser=True,
                )
                user.set_password(password)
                user.save(using=tenant.db_alias)
                logger.info(f"Created user: {username} in tenant {tenant.name}")
            except Exception as e:
                logger.error(f"Failed to create user: {str(e)}")
                tenant.delete()
                error_msg = str(e)
                if 'unique constraint' in error_msg.lower():
                    return Response({'detail': 'Username or email already exists in this tenant'}, status=400)
                return Response({'detail': f'Failed to create user: {error_msg}'}, status=500)

            # Create tokens
            if get_current_tenant() != tenant:
                logger.warning(f"Tenant context mismatch, resetting...")
                set_current_tenant(tenant)
            
            logger.info(f"Creating refresh token for user {user.id}")
            try:
                refresh = RefreshToken.for_user(user)
                logger.info(f"✓ Refresh token created successfully")
            except Exception as e:
                logger.error(f"Failed to create refresh token: {str(e)}")
                logger.warning(f"Attempting fallback table creation...")
                
                try:
                    from tenancy.shop_manager import verify_and_create_missing_tables
                    verify_and_create_missing_tables(tenant, tenant.db_alias)
                    logger.info(f"✓ Token tables created, retrying...")
                    refresh = RefreshToken.for_user(user)
                    logger.info(f"✓ Token created after fallback")
                except Exception as fallback_error:
                    logger.error(f"✗ Fallback failed: {str(fallback_error)}", exc_info=True)
                    tenant.delete()
                    return Response({'detail': f'Failed to create token: {str(fallback_error)}'}, status=500)
            
            refresh['tenant_id'] = tenant.id
            refresh['tenant_slug'] = tenant.slug

            access_token = refresh.access_token

            response = Response({
                'message': 'Account created successfully',
                'tenant_slug': tenant.slug,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'company_name': company_name,
                }
            }, status=201)

            # Set JWT tokens in httpOnly cookies
            is_secure = not settings.DEBUG
            
            response.set_cookie(
                'access_token',
                str(access_token),
                max_age=int(settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds()),
                httponly=True,
                secure=is_secure,
                samesite='Lax',
                path='/',
            )

            response.set_cookie(
                'refresh_token',
                str(refresh),
                max_age=int(settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds()),
                httponly=True,
                secure=is_secure,
                samesite='Lax',
                path='/',
            )

            return response

        except Exception as e:
            logger.error(f"Signup error: {str(e)}", exc_info=True)
            return Response({'detail': f'Signup failed: {str(e)}'}, status=500)


# ViewSet for user management
class ShopUserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing shop users.
    """
    queryset = ShopUser.objects.all()
    serializer_class = ShopUserSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [TenantJWTAuthentication]
    
    def get_queryset(self):
        """Filter users by current tenant"""
        tenant = get_current_tenant()
        if not tenant:
            return ShopUser.objects.none()
        
        # Query from tenant database
        return ShopUser.objects.using(tenant.db_alias).filter(tenant_id=tenant.id)
    
    def perform_create(self, serializer):
        """
        Automatically inherit role from creator if they are ADMIN.
        This ensures new users get admin privileges when created by an admin.
        """
        # Get the current user (creator)
        creator = self.request.user
        
        # Check if creator is ADMIN - inherit their role
        if getattr(creator, 'role', None) == 'ADMIN' or getattr(creator, 'is_superuser', False):
            # Admin users create other admins automatically
            serializer.save(role='ADMIN', is_staff=True)
        else:
            # Non-admins create users with default role (CASHIER)
            serializer.save()


class ProfileView(APIView):
    """
    Get or update the current user's profile.
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [TenantJWTAuthentication]

    def get(self, request):
        """Get current user's profile"""
        try:
            user = request.user
            tenant = get_current_tenant()
            
            return Response({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'role': getattr(user, 'role', 'USER'),
                'is_superuser': user.is_superuser,
                'is_staff': user.is_staff,
                'is_admin': getattr(user, 'role', '') == 'ADMIN' or user.is_superuser,
                'phone': getattr(user, 'phone', None),
                'shop_ids': getattr(user, 'shop_ids', []),
                'tenant': {
                    'id': tenant.id if tenant else None,
                    'name': tenant.name if tenant else None,
                    'slug': tenant.slug if tenant else None,
                } if tenant else None
            })
        except Exception as e:
            logger.error(f"Profile get error: {str(e)}", exc_info=True)
            return Response(
                {'detail': 'Failed to get profile'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def patch(self, request):
        """Update current user's profile"""
        try:
            user = request.user
            tenant = get_current_tenant()
            
            # Fields that can be updated
            updateable_fields = ['first_name', 'last_name', 'email', 'phone']
            
            # Update fields
            for field in updateable_fields:
                if field in request.data:
                    setattr(user, field, request.data[field])
            
            # Save to tenant database
            if tenant:
                user.save(using=tenant.db_alias)
            else:
                user.save()
            
            # Log the update
            UserAuditLog.log_user_updated(request, user)
            
            return Response({
                'detail': 'Profile updated successfully',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'phone': getattr(user, 'phone', None),
                }
            })
        except Exception as e:
            logger.error(f"Profile update error: {str(e)}", exc_info=True)
            return Response(
                {'detail': f'Failed to update profile: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def put(self, request):
        """Change password"""
        try:
            user = request.user
            tenant = get_current_tenant()
            
            current_password = request.data.get('current_password')
            new_password = request.data.get('new_password')
            new_password_confirm = request.data.get('new_password_confirm')
            
            if not all([current_password, new_password, new_password_confirm]):
                return Response(
                    {'detail': 'All password fields are required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check current password
            if not user.check_password(current_password):
                return Response(
                    {'detail': 'Current password is incorrect'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check new passwords match
            if new_password != new_password_confirm:
                return Response(
                    {'detail': 'New passwords do not match'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate password strength
            if len(new_password) < 8:
                return Response(
                    {'detail': 'Password must be at least 8 characters'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Set new password
            user.set_password(new_password)
            
            # Save to tenant database
            if tenant:
                user.save(using=tenant.db_alias)
            else:
                user.save()
            
            # Log the password change
            UserAuditLog.log_user_updated(request, user, changes={'password': 'changed'})
            
            return Response({
                'detail': 'Password changed successfully'
            })
        except Exception as e:
            logger.error(f"Password change error: {str(e)}", exc_info=True)
            return Response(
                {'detail': f'Failed to change password: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        

class UnifiedLoginView(APIView):
    """
    Unified login that works for both subdomain-based and explicit tenant_slug logins.
    """
    permission_classes = [AllowAny]
    throttle_classes = [LoginThrottle]

    @method_decorator(csrf_protect)
    def post(self, request):
        """
        Unified login endpoint.
        - For subdomain-based: tenant resolved from middleware
        - For explicit tenant: tenant_slug provided in request body
        """
        try:
            # Try to get tenant from request data first (explicit login)
            tenant_slug = request.data.get('tenant_slug')
            tenant = None
            
            if tenant_slug:
                # Explicit tenant provided
                try:
                    tenant = Tenant.objects.get(slug=tenant_slug)
                    set_current_tenant(tenant)
                    from tenancy.utils import register_tenant_connection
                    register_tenant_connection(tenant)
                    if settings.DEBUG:
                        logger.debug(f"Unified login: Using explicit tenant: {tenant.name}")
                except Tenant.DoesNotExist:
                    LoginAuditLog.log_login_failed(request, username=request.data.get('username'))
                    raise AuthenticationFailed(f"Tenant '{tenant_slug}' not found")
            else:
                # Try to get from context (subdomain-based)
                tenant = get_current_tenant()
                if tenant and settings.DEBUG:
                    logger.debug(f"Unified login: Using tenant from context: {tenant.name}")
            
            if not tenant:
                LoginAuditLog.log_login_failed(request, username=request.data.get('username'))
                raise AuthenticationFailed("Tenant not resolved. Provide tenant_slug or use subdomain.")

            username = request.data.get("username")
            password = request.data.get("password")

            if not username or not password:
                LoginAuditLog.log_login_failed(request, username=username)
                raise AuthenticationFailed("Missing credentials")

            user = authenticate(request, username=username, password=password)

            if not user:
                LoginAuditLog.log_login_failed(request, username=username)
                raise AuthenticationFailed("Invalid credentials")

            if not user.is_superuser and user.tenant_id != tenant.id:
                LoginAuditLog.log_login_failed(request, username=username)
                raise AuthenticationFailed("User does not belong to tenant")

            # Create tokens
            refresh = RefreshToken()
            refresh['user_id'] = user.id
            refresh['username'] = user.username
            refresh['email'] = getattr(user, 'email', '')
            refresh['tenant_id'] = tenant.id
            refresh['tenant_slug'] = tenant.slug

            access_token = str(refresh.access_token)
            refresh_token = str(refresh)

            response = Response({
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "role": getattr(user, 'role', 'USER'),
                    "is_superuser": user.is_superuser,
                },
                "tenant": {
                    "id": tenant.id,
                    "name": tenant.name,
                    "slug": tenant.slug,
                }
            })

            # Set cookies
            is_secure = not settings.DEBUG
            
            response.set_cookie(
                key='access_token',
                value=access_token,
                max_age=int(settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds()),
                secure=is_secure,
                httponly=True,
                samesite='Lax',
                path='/',
            )
            
            response.set_cookie(
                key='refresh_token',
                value=refresh_token,
                max_age=int(settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds()),
                secure=is_secure,
                httponly=True,
                samesite='Lax',
                path='/',
            )

            LoginAuditLog.log_login(request, user)

            return response
        
        except AuthenticationFailed:
            raise
        except Exception as e:
            logger.error(f"Unified login error: {str(e)}", exc_info=True)
            raise AuthenticationFailed(f"Login failed: {str(e)}")