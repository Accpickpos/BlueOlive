# JWT Token Problem Handling Guide

## Overview

Your BlueOlive system has a **multi-layered approach** to handle JWT token problems while ensuring users can always login or create new tenants. Here's how it works:

---

## 1. Token Storage & Security Architecture

### Frontend (Next.js)
- **Location**: httpOnly cookies (secure, not accessible to JavaScript)
- **Set by**: Backend on login/signup response
- **Sent automatically**: With every request via `withCredentials: true`
- **No Authorization header needed**: Cookies handle authentication

### Backend (Django)
- **Token lifetime**: 
  - Access token: 60 minutes
  - Refresh token: 7 days
- **Blacklist on logout**: Tokens are invalidated immediately
- **Storage**: Stored in secure httpOnly cookies and can be read from cookies or Authorization header

---

## 2. JWT Problem Handling Flow

### A. Token Decoding Issues (Invalid/Expired Tokens)

**Location**: [backend/core/tenancy/jwt_authentication.py#L43-L87](backend/core/tenancy/jwt_authentication.py#L43-L87)

```python
# If token decode fails, this is caught:
try:
    validated_token = AccessToken(token)  # Validates token signature & expiration
except (AuthenticationFailed, InvalidToken) as e:
    logger.warning(f"Token validation failed: {str(e)}")
    raise  # Returns 401 to frontend
```

**What happens**:
- `AccessToken(token)` fails if token is:
  - Expired (exp claim in the past)
  - Tampered with (signature invalid)
  - Corrupted/malformed (not valid JWT format)
- Returns `401 Unauthorized`
- Frontend catches 401 and attempts token refresh

---

### B. Frontend Token Refresh on 401

**Location**: [frontend/lib/api.ts#L232-L265](frontend/lib/api.ts#L232-L265)

```typescript
// Automatic token refresh when 401 occurs
if (error.response?.status === 401 && originalRequest && !originalRequest._retry) {
  originalRequest._retry = true;
  
  if (isRefreshing) {
    // Queue requests while refresh in progress
    return new Promise((resolve, reject) => {
      failedQueue.push({ resolve, reject });
    });
  }
  
  isRefreshing = true;
  
  try {
    // Call refresh endpoint - uses httpOnly cookies
    await axios.post(`${API_BASE}/api/users/auth/token/refresh/`, {}, {
      withCredentials: true,
    });
    
    // Retry original request with new access token
    return api(originalRequest);
  } catch (err) {
    // Refresh failed - clear auth and reject
    clearAuthData();
    return Promise.reject(err);
  }
}
```

**Key Features**:
- ✅ Uses `refresh_token` from httpOnly cookie (automatic)
- ✅ Queues subsequent requests while refresh is in progress
- ✅ Only retries once per request (prevents infinite loops)
- ✅ Suppresses error logs for expected 401s (status checks)

---

### C. Backend Token Refresh Endpoint

**Location**: [backend/core/shop_users/views.py#L245-L284](backend/core/shop_users/views.py#L245-L284)

```python
class CookieTokenRefreshView(TokenRefreshView):
    """
    Reads refresh_token from httpOnly cookie.
    Returns new access_token in httpOnly cookie.
    """
    
    def post(self, request):
        # 1. Get refresh token (tries body first, then cookie)
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            refresh_token = request.COOKIES.get('refresh_token')
        
        # 2. Validate and regenerate
        try:
            refresh = RefreshToken(refresh_token)
            access_token = refresh.access_token
        except TokenError as e:
            raise AuthenticationFailed(f"Invalid or expired refresh token: {str(e)}")
        
        # 3. Set new tokens in httpOnly cookies (secure)
        response.set_cookie('access_token', str(access_token), max_age=3600, httponly=True)
        response.set_cookie('refresh_token', str(refresh), max_age=604800, httponly=True)
        
        return response
```

**Handles**:
- ✅ Expired access tokens (generates new one)
- ✅ Expired refresh tokens (rejects with 401)
- ✅ Token rotation (creates new refresh token)
- ✅ Token blacklisting (old tokens can't refresh)

---

## 3. TenantJWTAuthentication Token Decoding (275 bytes)

**Location**: [backend/core/tenancy/jwt_authentication.py#L65-L87](backend/core/tenancy/jwt_authentication.py#L65-L87)

### What causes 275-byte tokens to fail decoding?

The TenantJWTAuthentication does 3 validation steps:

```python
# Step 1: Extract token from cookie/header
token = request.COOKIES.get('access_token')

# Step 2: Decode and validate signature
validated_token = AccessToken(token)  # Can fail here if:
                                       # - Token is corrupted
                                       # - Signature is invalid
                                       # - Token is expired
                                       # - Token has wrong SECRET_KEY

# Step 3: Extract tenant info and validate
token_tenant_id = validated_token.get('tenant_id')
tenant = Tenant.objects.get(id=token_tenant_id)  # Can fail if tenant deleted
```

### How it handles decode failures:

```python
except (AuthenticationFailed, InvalidToken) as e:
    logger.warning(f"Token validation failed: {str(e)}")
    raise  # Returns 401 to frontend

except Exception as e:
    logger.error(f"Failed to decode token: {str(e)}")
    raise AuthenticationFailed(f"Token validation error: {str(e)}")
```

**Resolution**: Frontend catches 401, attempts token refresh with `CookieTokenRefreshView`

---

## 4. Protected Endpoints Return 401 - Recovery Path

**Location**: [frontend/lib/api.ts#L210-L265](frontend/lib/api.ts#L210-L265)

### What happens:

```
User Request to Protected Endpoint
    ↓
Frontend adds access_token from cookie to request
    ↓
Backend TenantJWTAuthentication validates token
    ↓
❌ Token EXPIRED or INVALID?
    ↓
Return 401 Unauthorized
    ↓
Frontend Interceptor Catches 401
    ↓
Calls /api/users/auth/token/refresh/ with refresh_token from cookie
    ↓
✅ Backend generates new access_token
    ↓
Frontend retries original request with new token
    ↓
✅ Request succeeds
```

### Failure Cases:

```
If Refresh Token is also EXPIRED/INVALID:
    ↓
Token refresh returns 401
    ↓
Frontend calls clearAuthData()
    ↓
Redirects to login page
    ↓
✅ User can Login OR Create Tenant (no auth required)
```

---

## 5. Login & Signup - Always Accessible (No Auth Required)

**Location**: 
- Login: [backend/core/shop_users/views.py#L400-L455](backend/core/shop_users/views.py#L400-L455)
- Signup: [backend/core/shop_users/views.py#L673-L720](backend/core/shop_users/views.py#L673-L720)

### Public Endpoints (No JWT required):

```python
# Frontend api.ts - Public endpoints never require auth
const PUBLIC_ENDPOINTS = [
    '/api/v1/users/auth/login/',      # ✅ Login
    '/api/v1/users/auth/signup/',     # ✅ Signup
    '/api/v1/users/auth/csrf/',       # ✅ CSRF token
    '/api/v1/users/auth/token/refresh/',  # ✅ Token refresh
];
```

These endpoints have **no permission restrictions**:

```python
# Backend - CustomTokenObtainPairView
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    # No permission_classes - defaults to AllowAny

# Backend - SignupView
class SignupView(APIView):
    # No permission_classes specified - AllowAny by default
```

### Login Flow (Even with Expired Tokens):

```
1. User navigates to /login
   ↓
2. Frontend tries /api/v1/users/auth/profile/ (status check)
   ↓
3. Returns 401 (expected - shows login page)
   ↓
4. User submits login form
   ↓
5. Frontend POST /api/v1/users/auth/login/ 
   (no JWT required - public endpoint)
   ↓
6. Backend validates credentials
   ✓ If valid: Returns new tokens in httpOnly cookies
   ✗ If invalid: Returns 401 "Invalid credentials"
   ↓
7. Frontend stored tokens, redirects to dashboard
```

### Signup Flow (Create Tenant):

```
1. User navigates to /signup
   ↓
2. Frontend POST /api/v1/users/auth/signup/
   (no JWT required - public endpoint)
   ↓
3. Backend:
   - Validates email not duplicate
   - Creates new tenant
   - Creates new user in tenant
   - Generates tokens
   ✓ If valid: Returns tokens in httpOnly cookies
   ✗ If invalid: Returns error details
   ↓
4. Frontend stores tokens, redirects to dashboard
```

---

## 6. Rate Limiting Handling

**Location**: [frontend/lib/api.ts#L195-L228](frontend/lib/api.ts#L195-L228)

When server returns `429 Too Many Requests`:

```typescript
if (error.response?.status === 429) {
    // For auth endpoints: retry once after 2 seconds
    if (endpoint.includes('/auth/') && !originalRequest._rateLimitRetry) {
        originalRequest._rateLimitRetry = true;
        await new Promise(resolve => setTimeout(resolve, 2000));
        return api(originalRequest);  // Retry once
    }
    
    // If retry fails: mark endpoint as rate-limited for 15 seconds
    markEndpointRateLimited(endpoint, 15);
    
    return Promise.reject(error);
}
```

**Result**: Users can still login, but may need to wait 15 seconds if rate limited

---

## 7. Current Token Validation Flow

```
Request → Middleware Sets Tenant Context
              ↓
          TenantJWTAuthentication.authenticate()
              ↓
          ┌─────────────────────────────────────────┐
          │ Try cookie (access_token)               │
          └─────────────────────────────────────────┘
              ✓ Found         ✗ Not Found
              ↓               ↓
          AccessToken()    Try Authorization
          validation       header (fallback)
              ↓               ↓
          ┌──────────────────┐
          │ Valid or Error?  │
          └──────────────────┘
          ✓ Valid: Return user → Continue
          ✗ Invalid/Expired: AuthenticationFailed → 401
          ✓ No token: Return None → Public access OK
```

---

## 8. Best Practices Your System Already Implements

✅ **httpOnly Cookies**: Tokens not accessible to JavaScript (XSS protection)
✅ **CSRF Protection**: CSRF token fetched for POST/PUT/PATCH/DELETE
✅ **Token Rotation**: RefreshToken generates new tokens on refresh
✅ **Token Blacklisting**: Logged-out tokens can't be reused
✅ **Error Handling**: Clear 401/403 responses for authentication issues
✅ **Request Queueing**: Multiple 401s don't trigger multiple refresh requests
✅ **Public Endpoints**: Login/signup always accessible regardless of token state
✅ **Tenant Isolation**: Token validation includes tenant context
✅ **Logging**: Debug logging for troubleshooting token issues
✅ **Graceful Degradation**: Falls back to Authorization header if cookie missing

---

## 9. Recommended Improvements

### A. Enhanced Error Messages
Instead of generic "Invalid or expired refresh token", specify the issue:

```python
try:
    refresh = RefreshToken(refresh_token)
except TokenError as e:
    if "token_type" in str(e):
        msg = "Token expired. Please login again."
    elif "signature" in str(e):
        msg = "Token corrupted. Please login again."
    else:
        msg = f"Authentication failed: {str(e)}"
    raise AuthenticationFailed(msg)
```

### B. Token Refresh Metrics
Track how often token refresh happens to detect:
- Too many 401s (possible token tampering)
- Very short token lifetimes (JWT issue)

```python
class CookieTokenRefreshView(TokenRefreshView):
    def post(self, request):
        # Log refresh activity
        logger.info(f"Token refresh: user={request.user.id if hasattr(request, 'user') else 'unknown'}")
        # ... rest of method
```

### C. Pre-emptive Refresh
Refresh token 5 minutes before expiration instead of waiting for 401:

```typescript
// Frontend - after login
const ACCESS_TOKEN_LIFETIME = 60 * 60 * 1000; // 60 minutes
const REFRESH_BEFORE_EXPIRY = 5 * 60 * 1000; // 5 minutes before expiry

setTimeout(() => {
    api.post('/api/users/auth/token/refresh/', {}, {
        withCredentials: true,
    }).catch(() => {});
}, ACCESS_TOKEN_LIFETIME - REFRESH_BEFORE_EXPIRY);
```

### D. Token Validation on App Load
Check token validity when app first loads:

```typescript
// frontend/app/layout.tsx or initial component
useEffect(() => {
    isAuthenticated().then(auth => {
        if (!auth) {
            // Try refresh before showing login
            api.post('/api/users/auth/token/refresh/', {}, {
                withCredentials: true,
            }).catch(() => {
                // Even refresh failed - redirect to login
            });
        }
    });
}, []);
```

---

## 10. Troubleshooting Matrix

| Problem | Cause | Solution |
|---------|-------|----------|
| 275-byte token won't decode | Token corrupted or using wrong SECRET_KEY on backend | Check DEBUG mode in settings, ensure SECRET_KEY consistent |
| 401 on protected endpoints | Token expired or invalid | Frontend automatically attempts refresh |
| Refresh also returns 401 | Refresh token expired (7+ days old) | User must login again (public endpoint) |
| Can't login | Database connection issue, user doesn't exist | Check backend logs, verify credentials |
| Can't create tenant (signup) | Subdomain taken, invalid email | Check error response details, use different subdomain |
| Persistent 401 loop | Refresh token blacklisted | Clear browser cookies, logout via backend endpoint |
| Rate limiting blocks login | Too many login attempts | Wait 15 seconds, retry |

---

## 11. Summary

Your system ensures users can **always login or create new tenants** because:

1. **Login/Signup are public endpoints** - Never require authentication
2. **Multi-layer error handling**:
   - Token decode fails → 401 returned
   - Frontend catches 401 → Attempts refresh
   - Refresh fails → Redirect to login (public, always accessible)
3. **Graceful fallbacks**:
   - Cookie missing → Try Authorization header
   - Token invalid → Return None (allow public access)
   - Refresh token expired → Clear auth, redirect to login
4. **Smart retry logic**:
   - Queue requests during refresh (avoid thundering herd)
   - Only retry once (prevent infinite loops)
   - Rate limit detection and handling

**Result**: Even with all JWT tokens expired/invalid, users can always:
- ✅ Login with credentials
- ✅ Create new tenant (signup)
- ✅ Access public endpoints
