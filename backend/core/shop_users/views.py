from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework import viewsets
from rest_framework.throttling import AnonRateThrottle
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
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


class GetCSRFTokenView(APIView):
    """
    GET endpoint to retrieve CSRF token for unauthenticated users.
    This is required for POST requests with CSRF protection enabled.
    """
    permission_classes = [AllowAny]

    @method_decorator(ensure_csrf_cookie)
    def get(self, request):
        return Response({'detail': 'CSRF token set in cookie'}, status=200)


class TenantTokenView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [LoginThrottle]

    @method_decorator(csrf_protect)
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
                    logger.info(f"Login: Using tenant from request slug: {tenant.name} (slug={tenant_slug})")
                    
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
                if tenant:
                    logger.info(f"Login: Using tenant from context: {tenant.name}")
            
            if not tenant:
                LoginAuditLog.log_login_failed(request, username=request.data.get('username'))
                raise AuthenticationFailed("Tenant not resolved")

            username = request.data.get("username")
            password = request.data.get("password")

            if not username or not password:
                LoginAuditLog.log_login_failed(request, username=username)
                raise AuthenticationFailed("Missing credentials")

            logger.info(f"About to authenticate user: {username}")
            user = authenticate(
                request,
                username=username,
                password=password,
            )
            logger.info(f"Authentication result: {user}")

            if not user:
                LoginAuditLog.log_login_failed(request, username=username)
                raise AuthenticationFailed("Invalid credentials")

            # User object is already properly loaded from auth backend
            # No need to reload

            if not user.is_superuser and user.tenant_id != tenant.id:
                LoginAuditLog.log_login_failed(request, username=username)
                raise AuthenticationFailed("User does not belong to tenant")

            # Create tokens manually to avoid database queries
            from rest_framework_simplejwt.tokens import RefreshToken
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
                }
            })

            # Set httpOnly cookies (secure, not accessible to JavaScript)
            response.set_cookie(
                key='access_token',
                value=access_token,
                max_age=3600,  # 1 hour
                secure=not request.is_secure().__class__.__name__ == 'False',  # HTTPS only in production
                httponly=True,  # Not accessible to JavaScript (XSS protection)
                samesite='Strict',  # CSRF protection
                path='/',
            )
            
            response.set_cookie(
                key='refresh_token',
                value=refresh_token,
                max_age=604800,  # 7 days
                secure=not request.is_secure().__class__.__name__ == 'False',
                httponly=True,
                samesite='Strict',
                path='/',
            )

            # Log successful login
            LoginAuditLog.log_login(request, user)

            return response
        
        except AuthenticationFailed:
            raise
        except Exception as e:
            import traceback
            logger.error(f"Login error: {str(e)}\n{traceback.format_exc()}")
            raise AuthenticationFailed(f"Login failed: {str(e)}")


class LogoutView(APIView):
    """Logout by clearing cookies"""
    permission_classes = [AllowAny]

    def post(self, request):
        # Log logout
        if request.user and request.user.is_authenticated:
            LoginAuditLog.log_logout(request, request.user)
        
        response = Response({"message": "Logged out successfully"})
        
        # Clear authentication cookies with same settings as login
        response.delete_cookie(
            key='access_token',
            path='/',
            samesite='Strict',
        )
        response.delete_cookie(
            key='refresh_token',
            path='/',
            samesite='Strict',
        )
        
        return response


class ProfileView(APIView):
    """Get current user profile - used for authentication checks"""
    authentication_classes = [TenantJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Return current user profile if authenticated"""
        if not request.user or not request.user.is_authenticated:
            raise AuthenticationFailed('Not authenticated')
        
        user = request.user
        is_admin = user.is_superuser or (hasattr(user, 'role') and user.role == 'ADMIN')
        
        return Response({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "tenant_id": user.tenant_id,
            "is_superuser": user.is_superuser,
            "is_admin": is_admin,
        })


class ShopUserViewSet(viewsets.ModelViewSet):
    serializer_class = ShopUserSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        """
        Assign permissions based on action:
        - list/retrieve: IsTenantMember (see own tenant users)
        - create: IsManager (only managers can create users)
        - update/partial_update: IsManager (only managers can modify users)
        - destroy: IsAdmin (only admins can delete users)
        """
        from tenancy.permissions import IsAdmin, IsManager, IsTenantMember
        
        if self.action == 'create':
            return [IsManager()]
        elif self.action in ['update', 'partial_update']:
            return [IsManager()]
        elif self.action == 'destroy':
            return [IsAdmin()]
        else:  # list, retrieve
            return [IsTenantMember()]

    def get_queryset(self):
        from tenancy.permissions import IsTenantMember
        tenant = get_current_tenant()
        if tenant:
            # Query from tenant database, not main database
            # Check if user is superuser OR has ADMIN role
            is_admin = self.request.user.is_superuser or (hasattr(self.request.user, 'role') and self.request.user.role == 'ADMIN')
            if is_admin:
                return ShopUser.objects.using(tenant.db_alias).filter(tenant_id=tenant.id)
            # Regular users can only see their own data
            return ShopUser.objects.using(tenant.db_alias).filter(tenant_id=tenant.id, id=self.request.user.id)
        return ShopUser.objects.none()

    def perform_create(self, serializer):
        tenant = get_current_tenant()
        if tenant:
            serializer.save(tenant_id=tenant.id)
        else:
            raise AuthenticationFailed("Tenant context required")

class UnifiedLoginView(APIView):
    """
    Unified login endpoint that searches across all tenants.
    User provides email + password, backend finds their tenant.
    Returns tenant slug and JWT token.
    
    No tenant_slug needed in request - works from any domain.
    """
    permission_classes = [AllowAny]
    throttle_classes = [LoginThrottle]

    @method_decorator(csrf_protect)
    def post(self, request):
        try:
            email = request.data.get('email')
            password = request.data.get('password')

            if not email or not password:
                LoginAuditLog.log_login_failed(request, username=email)
                raise AuthenticationFailed("Email and password are required")

            # Search through all tenants to find the user
            user_found = None
            user_tenant = None
            
            tenants = Tenant.objects.all()
            logger.info(f"Searching for user '{email}' across {tenants.count()} tenants")
            
            for tenant in tenants:
                try:
                    # Register tenant connection
                    from tenancy.utils import register_tenant_connection
                    register_tenant_connection(tenant)
                    set_current_tenant(tenant)
                    
                    # Try to find user in this tenant
                    user = authenticate(
                        request,
                        username=email,
                        password=password,
                    )
                    
                    if user and user.is_active:
                        user_found = user
                        user_tenant = tenant
                        logger.info(f"User '{email}' found in tenant: {tenant.name}")
                        break
                except Exception as e:
                    logger.debug(f"Error checking tenant {tenant.slug}: {str(e)}")
                    continue

            if not user_found:
                LoginAuditLog.log_login_failed(request, username=email)
                raise AuthenticationFailed("Invalid credentials")

            if not user_tenant:
                LoginAuditLog.log_login_failed(request, username=email)
                raise AuthenticationFailed("User tenant not found")

            # Set the tenant context for token generation
            set_current_tenant(user_tenant)
            from tenancy.utils import register_tenant_connection
            register_tenant_connection(user_tenant)

            # Generate tokens with tenant info embedded
            refresh = RefreshToken.for_user(user_found)
            
            # Add tenant information to tokens so JWT auth can use it
            # These custom claims will be included in both refresh and access tokens
            refresh['tenant_id'] = user_tenant.id
            refresh['tenant_slug'] = user_tenant.slug
            
            # Get the access token (it inherits the claims from refresh)
            access_token = refresh.access_token

            # Log successful login
            LoginAuditLog.log_login(request, user_found)

            response = Response({
                'access': str(access_token),
                'refresh': str(refresh),
                'tenant_slug': user_tenant.slug,  # Important: tell frontend which subdomain to use
                'user': {
                    'id': user_found.id,
                    'username': user_found.username,
                    'email': user_found.email,
                    'is_admin': user_found.is_superuser or (hasattr(user_found, 'role') and user_found.role == 'ADMIN'),
                }
            })

            # Set JWT token in httpOnly cookie
            response.set_cookie(
                'access_token',
                str(refresh.access_token),
                max_age=86400,  # 24 hours
                httponly=True,
                secure=False,  # Set to True in production with HTTPS
                samesite='Lax',
                path='/',
            )

            response.set_cookie(
                'refresh_token',
                str(refresh),
                max_age=2592000,  # 30 days
                httponly=True,
                secure=False,  # Set to True in production with HTTPS
                samesite='Lax',
                path='/',
            )

            return response

        except AuthenticationFailed as e:
            return Response({'detail': str(e)}, status=401)
        except Exception as e:
            logger.error(f"Unified login error: {str(e)}", exc_info=True)
            LoginAuditLog.log_login_failed(request, username=request.data.get('email'))
            return Response({'detail': f'Login failed: {str(e)}'}, status=400)


class SignupView(APIView):
    """
    User registration endpoint - allows users to create their own account and tenant.
    """
    permission_classes = [AllowAny]

    @method_decorator(csrf_protect)
    def post(self, request):
        """
        Register a new user and create their tenant.
        
        Request body:
        {
            "email": "user@example.com",
            "username": "username",
            "password": "password123",
            "confirm_password": "password123",
            "first_name": "John",
            "last_name": "Doe",
            "company_name": "My Company",  # Used as tenant name
            "subdomain": "mycompany"  # Tenant subdomain
        }
        """
        try:
            email = request.data.get('email', '').strip()
            username = request.data.get('username', '').strip()
            password = request.data.get('password', '')
            confirm_password = request.data.get('confirm_password', '')
            first_name = request.data.get('first_name', '').strip()
            last_name = request.data.get('last_name', '').strip()
            company_name = request.data.get('company_name', '').strip()
            subdomain = request.data.get('subdomain', '').strip().lower()

            # Validation
            if not all([email, username, password, company_name, subdomain]):
                return Response(
                    {'detail': 'Missing required fields: email, username, password, company_name, subdomain'},
                    status=400
                )

            if password != confirm_password:
                return Response({'detail': 'Passwords do not match'}, status=400)

            if len(password) < 8:
                return Response({'detail': 'Password must be at least 8 characters'}, status=400)

            # Check if subdomain is available (main database check)
            if Tenant.objects.filter(subdomain=subdomain).exists():
                return Response({'detail': 'Subdomain already taken'}, status=400)

            # Create tenant
            from django.utils.text import slugify
            from django.conf import settings
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

            # Create user in tenant database
            try:
                user = ShopUser(
                    username=username,
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    tenant_id=tenant.id,
                    role='ADMIN',  # First user is admin
                    is_staff=True,
                    is_superuser=True,
                )
                user.set_password(password)
                user.save(using=tenant.db_alias)
                logger.info(f"Created user: {username} in tenant {tenant.name}")
            except Exception as e:
                logger.error(f"Failed to create user: {str(e)}")
                # Delete tenant if user creation fails
                tenant.delete()
                error_msg = str(e)
                if 'unique constraint' in error_msg.lower():
                    return Response({'detail': 'Username or email already exists in this tenant'}, status=400)
                return Response({'detail': f'Failed to create user: {error_msg}'}, status=500)

            # Create tokens
            refresh = RefreshToken.for_user(user)
            refresh['tenant_id'] = tenant.id
            refresh['tenant_slug'] = tenant.slug

            access_token = refresh.access_token

            response = Response({
                'message': 'Account created successfully',
                'access': str(access_token),
                'refresh': str(refresh),
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
            response.set_cookie(
                'access_token',
                str(access_token),
                max_age=86400,
                httponly=True,
                secure=False,
                samesite='Lax',
                path='/',
            )

            response.set_cookie(
                'refresh_token',
                str(refresh),
                max_age=2592000,
                httponly=True,
                secure=False,
                samesite='Lax',
                path='/',
            )

            return response

        except Exception as e:
            logger.error(f"Signup error: {str(e)}", exc_info=True)
            return Response({'detail': f'Signup failed: {str(e)}'}, status=500)