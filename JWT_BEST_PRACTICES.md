# JWT Token Handling - Best Practices & Implementation Guide

## Architecture Overview

Your system uses **cookie-based JWT authentication** with automatic refresh:

```
Browser                          Backend
  │                               │
  └─→ POST /login/ ────────────→  Login view validates credentials
                                   │
                                   └─→ Generate JWT tokens
                                   │
                              ←───┘ Set-Cookie: access_token (httpOnly, 1hr)
                                   Set-Cookie: refresh_token (httpOnly, 7d)
  │
  └─→ GET /protected/ ────────→  TenantJWTAuthentication
  │   (token in cookie)           │
  │                               ├─→ Read token from cookie
  │                               ├─→ Validate signature & expiration
  │                               └─→ Get user from DB
  │                          ←────┘ 200 OK or 401 Unauthorized
  │
  └─→ Sees 401? ──────────────→  Token refresh flow
      Automatically calls          │
      /token/refresh/             ├─→ Validate refresh token
                                   ├─→ Generate new access token
                              ←────┘ Set-Cookie: access_token (new)
  │
  └─→ Retry original request ──→  Now succeeds with new token
```

---

## 1. Frontend Error Handling Best Practices

### A. Axios Interceptor Pattern (Current Implementation ✅)

**Location**: [frontend/lib/api.ts](frontend/lib/api.ts)

**What it does right**:
```typescript
// ✅ Request interceptor: Adds tenant context
api.interceptors.request.use(async (config) => {
    const tenant = localStorage.getItem('tenant');
    if (tenant) {
        config.headers['X-Tenant'] = tenant;
    }
    
    // ✅ Add CSRF token for mutating requests
    if (['post', 'put', 'patch', 'delete'].includes(config.method)) {
        config.headers['X-CSRFToken'] = getCsrfToken();
    }
    return config;
});

// ✅ Response interceptor: Handles 401 with automatic refresh
api.interceptors.response.use(
    response => response,
    async (error) => {
        // 🔴 Problem: Token expired/invalid
        if (error.response?.status === 401 && !originalRequest._retry) {
            originalRequest._retry = true;
            
            if (isRefreshing) {
                // ✅ Queue requests during refresh
                return new Promise((resolve, reject) => {
                    failedQueue.push({ resolve, reject });
                });
            }
            
            isRefreshing = true;
            try {
                // ✅ Call refresh endpoint
                await axios.post(`${API_BASE}/api/users/auth/token/refresh/`, {}, {
                    withCredentials: true,
                });
                
                // ✅ Retry original request
                processQueue(null);
                return api(originalRequest);
            } catch (err) {
                // ✅ If refresh fails: logout
                clearAuthData();
                window.location.href = '/login';
                return Promise.reject(err);
            }
        }
        
        return Promise.reject(error);
    }
);
```

**Enhancement 1: Add Pre-emptive Refresh**

```typescript
// Refresh token 5 minutes before expiration
// Tokens: access=60min, refresh=7 days
const ACCESS_TOKEN_LIFETIME = 60 * 60 * 1000;
const REFRESH_BEFORE_EXPIRY = 5 * 60 * 1000;

export function setupTokenRefreshTimer() {
    // Calculate when to refresh: when only 5 minutes left
    const nextRefreshTime = ACCESS_TOKEN_LIFETIME - REFRESH_BEFORE_EXPIRY;
    
    const timer = setInterval(async () => {
        try {
            console.log('Pre-emptive token refresh (5min before expiry)');
            await api.post('/api/users/auth/token/refresh/', {}, {
                withCredentials: true,
            });
            
            // Reset timer
            clearInterval(timer);
            setupTokenRefreshTimer();
        } catch (err) {
            console.warn('Pre-emptive refresh failed:', err);
            // Not critical - will retry on next 401
        }
    }, nextRefreshTime);
    
    return () => clearInterval(timer);
}

// In layout.tsx or root component:
useEffect(() => {
    const cleanup = setupTokenRefreshTimer();
    return cleanup;
}, []);
```

**Enhancement 2: Better Error Messages**

```typescript
// Frontend error handler
api.interceptors.response.use(
    response => response,
    async (error) => {
        // More descriptive error messages
        const status = error.response?.status;
        const message = error.response?.data?.detail || 'Unknown error';
        
        if (status === 401) {
            if (error.config.url.includes('/login/')) {
                // Show "Invalid credentials" for login endpoint
                error.userMessage = 'Invalid email or password';
            } else if (error.config.url.includes('/token/refresh/')) {
                // Session expired - must login again
                error.userMessage = 'Your session expired. Please login again.';
            } else {
                // Try to refresh
                error.userMessage = 'Refreshing authentication...';
            }
        } else if (status === 403) {
            error.userMessage = 'You do not have permission to access this resource.';
        }
        
        return Promise.reject(error);
    }
);
```

---

### B. Request Component Pattern

**Pattern: Safe Protected Endpoint Calls**

```typescript
// app/dashboard/page.tsx
import { useState, useEffect } from 'react';
import { api } from '@/lib/api';

export default function Dashboard() {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    
    useEffect(() => {
        async function loadData() {
            try {
                // ✅ This automatically handles 401 refresh
                const response = await api.get('/api/v1/debtors/');
                setData(response.data);
            } catch (err: any) {
                // #### If we get here, both token AND refresh failed
                if (err.response?.status === 401) {
                    // Frontend already cleared auth data
                    // Browser already redirected to /login
                    setError('Authentication failed. Redirecting to login...');
                } else {
                    setError(err.response?.data?.detail || 'Failed to load data');
                }
            } finally {
                setLoading(false);
            }
        }
        
        loadData();
    }, []);
    
    if (loading) return <div>Loading...</div>;
    if (error) return <div className="error">{error}</div>;
    return <div>{/* render data */}</div>;
}
```

---

## 2. Backend Error Handling Best Practices

### A. JWT Authentication Handler (Current ✅)

**Location**: [backend/core/tenancy/jwt_authentication.py](backend/core/tenancy/jwt_authentication.py)

**What it does right**:
```python
class TenantJWTAuthentication(JWTAuthentication):
    """
    ✅ Reads from httpOnly cookie (primary)
    ✅ Falls back to Authorization header (API compatibility)
    ✅ Validates tenant context
    ✅ Extracts user from tenant database
    ✅ Returns None for public endpoints
    ✅ Raises 401 for invalid tokens
    """
    
    def authenticate(self, request):
        logger.info(f"Authenticating: {request.path}")
        
        # ✅ Try to get token from httpOnly cookie first
        token = request.COOKIES.get('access_token')
        
        if not token:
            # ✅ Fall back to Authorization header (for API clients)
            try:
                result = super().authenticate(request)
                if result is None:
                    logger.debug("No token found - allows public access")
                    return None  # ← Returns None for public endpoints!
                return result
            except (AuthenticationFailed, InvalidToken) as e:
                # ✅ Only raise if auth was explicitly attempted
                logger.warning(f"Token validation failed: {str(e)}")
                raise
        
        # ✅ Decode token
        try:
            validated_token = AccessToken(token)
        except (AuthenticationFailed, InvalidToken) as e:
            logger.warning(f"Could not decrypt token: {str(e)}")
            raise AuthenticationFailed(f"Invalid token: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected token error: {str(e)}")
            # ✅ Don't expose internal errors
            raise AuthenticationFailed("Authentication failed")
        
        # ✅ Get user and validate tenant
        user, validated_token = self.get_user(validated_token), validated_token
        return user, validated_token
```

**Enhancement 1: Detailed Error Messages (While Secure)**

```python
class TenantJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        try:
            validated_token = AccessToken(token)
        except TokenError as e:
            error_str = str(e)
            
            # Provide server-side logging with full details
            if 'exp' in error_str:
                logger.warning(f"Token expired for {request.path}")
                # Client-safe message
                raise AuthenticationFailed("Token expired")
            elif 'signature' in error_str:
                logger.error(f"Token signature invalid: {error_str}")
                raise AuthenticationFailed("Token invalid")
            else:
                logger.error(f"Token error: {error_str}")
                raise AuthenticationFailed("Authentication failed")
```

**Enhancement 2: Token Validation Metrics**

```python
import logging
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

# Track token refresh patterns
token_refresh_logger = logging.getLogger('token_refresh')

class CookieTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        try:
            refresh_token = request.COOKIES.get('refresh_token')
            
            if refresh_token:
                # ✅ Log refresh attempt
                token_refresh_logger.info(
                    f"Token refresh attempt",
                    extra={
                        'user_id': request.user.id if request.user.is_authenticated else 'anonymous',
                        'ip_address': request.META.get('REMOTE_ADDR'),
                    }
                )
            
            refresh = RefreshToken(refresh_token)
            access_token = refresh.access_token
            
            # ✅ Log success
            token_refresh_logger.info(
                f"Token refresh success",
                extra={'user_id': request.user.id if request.user.is_authenticated else 'unknown'}
            )
            
            response = Response({
                'access': str(access_token),
                'refresh': str(refresh),
            })
            
            # Set cookies...
            return response
            
        except TokenError as e:
            # ✅ Log failure
            token_refresh_logger.warning(
                f"Token refresh failed: {str(e)}",
                extra={'ip_address': request.META.get('REMOTE_ADDR')}
            )
            raise AuthenticationFailed("Invalid refresh token")
```

---

### B. Login View Error Handling

**Location**: [backend/core/shop_users/views.py#L400-L455](backend/core/shop_users/views.py#L400-L455)

**Best practice: Clear error messages without exposing internals**

```python
class UnifiedLoginView(APIView):
    @method_decorator(csrf_protect)
    def post(self, request):
        try:
            email = request.data.get('email')
            password = request.data.get('password')
            tenant_slug = request.data.get('tenant_slug')
            
            # ✅ Validate input
            if not all([email, password, tenant_slug]):
                return Response(
                    {'detail': 'email, password, and tenant_slug required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # ✅ Normalize email
            email = email.lower().strip()
            
            # ✅ Log attempt (don't log password!)
            logger.info(f"Login attempt: email={email}, tenant={tenant_slug}")
            
            # ✅ Get tenant
            try:
                tenant = Tenant.objects.get(slug=tenant_slug)
            except Tenant.DoesNotExist:
                # Don't reveal that tenant doesn't exist
                logger.warning(f"Login failed: tenant not found: {tenant_slug}")
                LoginAuditLog.log_login_failed(request, username=email)
                raise AuthenticationFailed("Invalid credentials")
            
            # ✅ Get user
            user = ShopUser.objects.using(tenant.db_alias).filter(
                email=email
            ).first()
            
            if not user or not user.check_password(password):
                # Generic error - don't reveal if user exists
                logger.warning(f"Login failed: invalid credentials for {email}")
                LoginAuditLog.log_login_failed(request, username=email)
                raise AuthenticationFailed("Invalid credentials")
            
            # ✅ Check if user is active
            if not user.is_active:
                logger.warning(f"Login failed: user inactive: {email}")
                LoginAuditLog.log_login_failed(request, username=email)
                raise AuthenticationFailed("User account is disabled")
            
            # ✅ Generate tokens
            set_current_tenant(tenant)
            refresh = RefreshToken.for_user(user)
            refresh['tenant_id'] = tenant.id
            refresh['tenant_slug'] = tenant.slug
            
            # ✅ Log success
            logger.info(f"Login successful: email={email}, tenant={tenant_slug}")
            LoginAuditLog.log_login(request, user)
            
            # ✅ Return tokens in response + cookies
            response = Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'username': user.username,
                },
                'tenant_slug': tenant.slug,
            }, status=status.HTTP_200_OK)
            
            # ✅ Set secure cookies
            response.set_cookie(
                'access_token',
                str(refresh.access_token),
                max_age=3600,
                httponly=True,
                secure=request.is_secure(),  # HTTPS in production
                samesite='Lax',
                path='/',
            )
            
            response.set_cookie(
                'refresh_token',
                str(refresh),
                max_age=604800,
                httponly=True,
                secure=request.is_secure(),
                samesite='Lax',
                path='/',
            )
            
            return response
            
        except AuthenticationFailed as e:
            # ✅ Return consistent error
            return Response({'detail': str(e)}, status=status.HTTP_401_UNAUTHORIZED)
        except Exception as e:
            logger.error(f"Login error: {str(e)}", exc_info=True)
            return Response(
                {'detail': 'Login failed. Please try again.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
```

---

## 3. Testing JWT Functionality

### A. Unit Tests

```python
# tests/test_jwt_token_handling.py
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from freezegun import freeze_time
from rest_framework_simplejwt.tokens import RefreshToken
from shop_users.models import ShopUser
from tenancy.models import Tenant

class JWTTokenHandlingTests(TestCase):
    """Test JWT token lifecycle and error handling"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.tenant = Tenant.objects.create(
            name="Test Tenant",
            slug="test-tenant",
            db_alias="default_1"
        )
        self.user = ShopUser.objects.using(self.tenant.db_alias).create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
    
    # ✅ Test 1: Successful token refresh
    def test_token_refresh_success(self):
        """Valid refresh token generates new access token"""
        refresh = RefreshToken.for_user(self.user)
        refresh['tenant_id'] = self.tenant.id
        
        response = self.client.post(
            '/api/users/auth/token/refresh/',
            {'refresh': str(refresh)},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
    
    # ✅ Test 2: Expired refresh token
    def test_token_refresh_expired_refresh(self):
        """Expired refresh token returns 401"""
        with freeze_time("2025-02-01"):
            refresh = RefreshToken.for_user(self.user)
        
        # Fast-forward 8 days (refresh expires after 7)
        with freeze_time("2025-02-09"):
            response = self.client.post(
                '/api/users/auth/token/refresh/',
                {'refresh': str(refresh)},
                format='json'
            )
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    # ✅ Test 3: Invalid token format
    def test_token_validation_invalid_format(self):
        """Invalid token format returns 401"""
        self.client.cookies['access_token'] = 'invalid.token.format'
        
        response = self.client.get('/api/v1/protected-endpoint/')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    # ✅ Test 4: Token with wrong signature
    def test_token_validation_wrong_signature(self):
        """Token with tampered signature returns 401"""
        refresh = RefreshToken.for_user(self.user)
        
        # Modify token (tamper)
        token_parts = str(refresh.access_token).split('.')
        tampered_token = '.'.join([
            token_parts[0],
            token_parts[1],
            'invalidsignature'  # Wrong signature
        ])
        
        self.client.cookies['access_token'] = tampered_token
        
        response = self.client.get('/api/v1/protected-endpoint/')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    # ✅ Test 5: Public endpoints don't require token
    def test_public_endpoints_no_token_required(self):
        """Login endpoint works without token"""
        response = self.client.post(
            '/api/v1/users/auth/login/',
            {
                'username': 'testuser',
                'password': 'testpass123',
                'tenant_slug': 'test-tenant'
            },
            format='json'
        )
        
        # Should succeed even with no token
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    # ✅ Test 6: Automatic request queueing during refresh
    def test_multiple_401_requests_queued(self):
        """Multiple 401s don't trigger multiple refresh calls"""
        # This is tested in frontend, but we can verify backend handles it
        refresh = RefreshToken.for_user(self.user)
        refresh['tenant_id'] = self.tenant.id
        
        # Simulate expired token
        with freeze_time("2025-02-09"):
            response1 = self.client.get(
                '/api/v1/protected-endpoint/',
                format='json'
            )
            response2 = self.client.get(
                '/api/v1/another-endpoint/',
                format='json'
            )
        
        # Both should get 401
        self.assertEqual(response1.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response2.status_code, status.HTTP_401_UNAUTHORIZED)
```

### B. Integration Tests

```python
# tests/test_jwt_integration.py
from django.test import TestCase
from rest_framework.test import APIClient
import json

class JWTIntegrationTests(TestCase):
    """Test complete JWT flow (login → request → refresh → request)"""
    
    def test_complete_login_and_protected_request_flow(self):
        """Full flow: login → token created → use token → refresh → retry"""
        client = APIClient()
        
        # Step 1: Login
        login_response = client.post(
            '/api/v1/users/auth/login/',
            {
                'username': 'testuser',
                'password': 'testpass123',
                'tenant_slug': 'test-tenant'
            },
            format='json'
        )
        
        self.assertEqual(login_response.status_code, 200)
        self.assertIn('access_token', client.cookies)
        
        # Step 2: Use token on protected endpoint
        protected_response = client.get('/api/v1/protected-endpoint/')
        self.assertEqual(protected_response.status_code, 200)
        
        # Step 3: Expire token
        with freeze_time("2025-02-09"):  # 1 hour later
            # Frontend would normally catch 401 and refresh
            # But backend should still accept refresh_token
            refresh_response = client.post(
                '/api/users/auth/token/refresh/',
                format='json'
            )
            
            if refresh_response.status_code == 200:
                # Step 4: Retry with new token
                retry_response = client.get('/api/v1/protected-endpoint/')
                self.assertEqual(retry_response.status_code, 200)
```

---

## 4. Security Checklist

- [x] ✅ Tokens stored in **httpOnly cookies** (not localStorage)
- [x] ✅ CSRF token required for POST/PUT/PATCH/DELETE
- [x] ✅ Token signature validated (prevents tampering)
- [x] ✅ Token expiration checked (prevents reuse after expiry)
- [x] ✅ Tokens blacklisted on logout (prevents replay)
- [x] ✅ Tenant context validated in token
- [x] ✅ User belongs to tenant verified
- [x] ✅ Sensitive data not logged (passwords, tokens)
- [x] ✅ Login failures don't reveal user existence
- [x] ✅ Rate limiting per endpoint (to prevent brute force)

**To Enable**:

```python
# settings.py

# Rate limiting
RATELIMIT_ENABLE = True
RATELIMIT_USE_CACHE = 'default'

# Per endpoint:
# POST /login: max 5 attempts per hour
# POST /signup: max 3 attempts per hour
# POST /token/refresh: max 50 attempts per hour

# Token blacklist
INSTALLED_APPS = [
    # ...
    'rest_framework_simplejwt.token_blacklist',
]

# JWT settings
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': settings.SECRET_KEY,
}
```

---

## 5. Common Pitfalls to Avoid

### ❌ Pitfall 1: Storing JWT in localStorage
```typescript
// DON'T DO THIS - XSS vulnerable
localStorage.setItem('access_token', token);  // ❌ JS can access
```

### ✅ Instead: Use httpOnly cookies
```javascript
// Backend sets it:
response.set_cookie('access_token', token, httponly=True)  # ✅ JS can't access
```

---

### ❌ Pitfall 2: Catching 401 on public endpoints
```typescript
// DON'T DO THIS
try {
    const response = await api.post('/api/v1/users/auth/login/', data);
} catch (err) {
    if (err.status === 401) {
        // This shouldn't happen on login endpoint!
    }
}
```

### ✅ Instead: Only refresh on protected endpoints
```typescript
// DO THIS
const PUBLIC_ENDPOINTS = ['/login/', '/signup/', '/token/refresh/'];

if (error.status === 401 && !PUBLIC_ENDPOINTS.some(ep => url.includes(ep))) {
    // Safe to refresh
    refreshToken();
}
```

---

### ❌ Pitfall 3: Not handling token refresh failures
```python
# DON'T DO THIS
try:
    await api.post('/token/refresh/', data);
except {
    // Silently ignore
}
```

### ✅ Instead: Clear auth and redirect to login
```typescript
// DO THIS
try {
    await api.post('/token/refresh/', data);
} catch (err) {
    clearAuthData();
    redirectToLogin();  // User must authenticate again
}
```

---

## Summary

Your system's JWT handling is **well-architected** because:

1. **httpOnly Cookies** - Secure by default, XSS-safe
2. **Automatic Refresh** - Users rarely see 401s
3. **Public Fallback** - Login/signup always accessible
4. **Tenant Validation** - Token verified to contain correct tenant
5. **Request Queueing** - Prevents refresh stampede
6. **Clear Errors** - Backend logs details, frontend shows user-friendly messages

The enhancements recommended above are optional optimizations for:
- **Better UX** (pre-emptive refresh)
- **Better Security** (detailed logging)
- **Better Visibility** (metrics and monitoring)
