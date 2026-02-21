# JWT Token Problems - Quick Reference Guide

## TL;DR - How the System Handles JWT Problems

Your system has **automatic token refresh**. When tokens expire or are invalid:

1. ✅ Frontend catches 401
2. ✅ Automatically calls `/api/users/auth/token/refresh/` (uses refresh token from cookie)
3. ✅ Gets new access token
4. ✅ Retries the original request
5. ✈️ If both tokens expired: User redirected to login (always accessible)

---

## Common JWT Issues & Fixes

### Issue 1: "Token validation failed" - 401 on Protected Endpoint

**What Happened**:
- Access token is expired (valid for 60 minutes only)
- OR access token is corrupted/tampered

**Automatic Fix**:
- ✅ Frontend automatically calls token refresh
- ✅ Gets new access token from backend
- ✅ Retries request

**Manual Fix (if needed)**:
```bash
# Navigate browser to any protected page
# Frontend automatically refreshes token

# Or manually:
curl -X POST http://localhost:8000/api/users/auth/token/refresh/ \
  --cookies-file cookies.txt --cookie-jar cookies.txt
```

**Code Location**:
- Backend: [backend/core/shop_users/views.py#L236-L284](backend/core/shop_users/views.py#L236-L284)
- Frontend: [frontend/lib/api.ts#L230-L265](frontend/lib/api.ts#L230-L265)

---

### Issue 2: TenantJWTAuthentication Decode Fails (275 bytes)

**What's the 275 bytes?**
- That's a normal JWT size with tenant claims
- If it fails to decode, one of these happened:
  1. Token signature is invalid (SECRET_KEY mismatch)
  2. Token is corrupted (truncated, modified)
  3. Token is expired (exp claim in the past)
  4. Token was issued by different backend

**Diagnostic**:
```bash
# Check backend SECRET_KEY is same across all servers
python manage.py shell
>>> from django.conf import settings
>>> print(settings.SECRET_KEY)

# Check token structure (don't trust output, just validate it exists)
# Token format: xxx.yyy.zzz (3 parts separated by dots)
```

**Fix**:
1. Clear browser cookies
2. Login again - this creates fresh tokens
3. Verify backend SECRET_KEY is consistent

**Code Location**:
- Authentication: [backend/core/tenancy/jwt_authentication.py#L65-L87](backend/core/tenancy/jwt_authentication.py#L65-L87)
- Token validation: [backend/core/tenancy/jwt_authentication.py#L138-L210](backend/core/tenancy/jwt_authentication.py#L138-L210)

---

### Issue 3: 401 on Login or Signup (Should Never Happen)

**What's Wrong**:
- Login/Signup are public endpoints - they NEVER require auth
- If you get 401 on `/api/v1/users/auth/login/`:
  - Something is wrong with your endpoint configuration
  - OR a middleware is incorrectly requiring auth

**Check**:
```python
# backend/core/shop_users/views.py - UnifiedLoginView

class UnifiedLoginView(APIView):
    # Should NOT have permission_classes
    # Should default to AllowAny
    
    @method_decorator(csrf_protect)
    def post(self, request):
        # No @permission_classes decorator
        # No login_required decorator
```

**Fix**:
Remove any `@permission_classes` or `@login_required` from:
- `UnifiedLoginView`
- `SignupView`
- `CookieTokenRefreshView`

Also check `settings.py` REST_FRAMEWORK config:
```python
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'tenancy.jwt_authentication.TenantJWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',  # ← Should be AllowAny by default
    ],
}
```

---

### Issue 4: "Tenant not found" - 401 After Token Refresh

**What Happened**:
- Token contains `tenant_id` from original login
- But that tenant was deleted from database
- Backend can't find tenant to load user

**Fix**:
1. Check if tenant exists:
```bash
python manage.py shell
>>> from tenancy.models import Tenant
>>> Tenant.objects.filter(id=<tenant_id_from_error>).exists()
```

2. If tenant deleted but data still exists:
```bash
# Recreate tenant
python manage.py shell
>>> from tenancy.models import Tenant
>>> Tenant.objects.create(id=1, name="My Shop", slug="my-shop", db_alias="default_1")
```

3. If tenant is gone:
```bash
# User must login again (public endpoint)
# Login will find user in existing tenant
```

**Code Location**:
- [backend/core/tenancy/jwt_authentication.py#L157-L170](backend/core/tenancy/jwt_authentication.py#L157-L170)

---

### Issue 5: "User not found" - 401 After Token Refresh

**What Happened**:
- Token contains `user_id` from original login
- But user was deleted from tenant database
- Backend can't load user to attach to request

**Fix**:
1. Check if user exists:
```bash
python manage.py shell
>>> from shop_users.models import ShopUser
>>> ShopUser.objects.filter(id=<user_id>).exists()
```

2. If user was deleted:
```bash
# User must login again with different account
# OR recreate the user
```

**Code Location**:
- [backend/core/tenancy/jwt_authentication.py#L196-L210](backend/core/tenancy/jwt_authentication.py#L196-L210)

---

### Issue 6: Rate Limiting (429) Blocks Login

**What Happened**:
- Too many login attempts from same IP
- Backend returns 429 Too Many Requests
- Even though login endpoint is public

**How Frontend Handles**:
```typescript
// api.ts - automatically retries after delay
if (error.response?.status === 429) {
    // For auth endpoints: retry once after 2 seconds
    if (endpoint.includes('/auth/')) {
        await sleep(2000);
        return retry();
    }
    
    // If still 429: mark endpoint as rate-limited for 15 seconds
    markEndpointRateLimited(endpoint, 15);
}
```

**Manual Fix**:
```bash
# Wait 15 seconds (your code does this automatically)

# Or clear rate limit cache in backend
# (if using external rate limiter like Redis)
redis-cli FLUSHDB
```

**Code Location**:
- Frontend handling: [frontend/lib/api.ts#L195-L228](frontend/lib/api.ts#L195-L228)

---

## Status Codes and What They Mean

| Status | Endpoint | Meaning | Action |
|--------|----------|---------|--------|
| 200 | Any | Success | Continue |
| 401 | Protected | Not authenticated | Frontend refreshes token, retries |
| 401 | `/login/` | Invalid credentials | Show "Wrong password" error |
| 401 | `/profile/` | Not authenticated | Expected - show login form |
| 401 | `/token/refresh/` | Both tokens expired | Redirect to login (must log in again) |
| 403 | Protected | Not authorized (wrong tenant) | User doesn't belong here |
| 429 | Any | Rate limited | Wait 15 seconds, retry |
| 500 | Any | Server error | Check backend logs |

---

## How to Debug Token Issues

### 1. Check If Token Is In Cookie

**Browser DevTools**:
```
F12 → Application → Cookies → localhost:3000
Look for:
- access_token
- refresh_token
- csrftoken
```

### 2. Decode Token (Without Trust!)

```bash
# Token format: header.payload.signature
# You can decode payload (NOT verify!) with:
# echo "PAYLOAD_PART" | base64 -d | jq

# But DON'T modify and re-use! Signature verification will fail.

# Better: Use https://jwt.io (but don't paste secret!)
```

### 3. Check Token Expiration

```python
# Backend
python manage.py shell
>>> from rest_framework_simplejwt.tokens import AccessToken
>>> token = AccessToken("your_token_string")
>>> token.payload  # {'exp': 1234567890, 'user_id': 1, ...}
>>> import datetime
>>> datetime.datetime.fromtimestamp(token['exp'])
```

### 4. Check Backend Logs

```bash
# If using Docker
docker logs backend

# If using local Django
# Configure logging in settings.py
LOGGING = {
    'version': 1,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'tenancy.jwt_authentication': {
            'handlers': ['console'],
            'level': 'DEBUG',  # ← Set to DEBUG
        },
    },
}
```

### 5. Check Frontend DevTools Network Tab

```
F12 → Network → Filter by "login" or "refresh"
- Request Headers: See if cookies being sent
- Response Headers: See if Set-Cookie present
- Response Body: See error message
```

---

## Testing Token Refresh

### Test 1: Manual Token Refresh

```bash
# 1. Login and capture tokens
curl -X POST http://localhost:8000/api/v1/users/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"user@example.com","password":"pass","tenant_slug":"tenant"}' \
  -c cookies.txt

# 2. Should see access_token and refresh_token in cookies file
cat cookies.txt

# 3. Call refresh endpoint
curl -X POST http://localhost:8000/api/users/auth/token/refresh/ \
  -b cookies.txt -c cookies.txt

# 4. Should return new access_token (in Set-Cookie header)
```

### Test 2: Use Expired Token

```bash
# 1. Login
# 2. Wait for access_token to expire (60 minutes in production, ~1 second in testing)
# 3. Make request to protected endpoint
# 4. Should automatically refresh and succeed

# Or in Django tests:
from freezegun import freeze_time
with freeze_time("2025-02-12 12:00:00"):
    token = RefreshToken.for_user(user)

with freeze_time("2025-02-12 13:01:00"):  # 1 hour later
    # Token should be expired now
    AccessToken(str(token.access_token))  # Should raise TokenError
```

### Test 3: Test Refresh Token Expiration

```python
# Django shell
>>> from freezegun import freeze_time
>>> from rest_framework_simplejwt.tokens import RefreshToken
>>> 
>>> user = ShopUser.objects.first()
>>> with freeze_time("2025-02-05"):
...     refresh = RefreshToken.for_user(user)
...     refresh_str = str(refresh)
>>> 
>>> # Now fast-forward 8 days (refresh expires after 7)
>>> with freeze_time("2025-02-13"):
...     try:
...         RefreshToken(refresh_str)
...     except TokenError as e:
...         print(f"Token expired as expected: {e}")
```

---

## When Users Can Always Access (No Auth Required)

These endpoints work even with all tokens expired/invalid:

```
✅ POST /api/v1/users/auth/login/
   - Enter username and password
   - Backend validates and returns new tokens

✅ POST /api/v1/users/auth/signup/
   - Create new account and tenant
   - Returns new tokens for the new user

✅ GET /api/v1/users/auth/csrf/
   - Get CSRF token for form protection
   - No auth required

✅ POST /api/v1/users/auth/token/refresh/
   - Refresh access token using refresh token
   - No auth required (uses refresh token from cookie)
```

All other endpoints:
- 🔐 Protected by default
- Return 401 if not authenticated
- Frontend automatically handles 401 by refreshing
- If refresh also fails: user redirected to login

---

## Emergency: Completely Clear Auth

If you need to completely clear authentication (e.g., security incident):

### Frontend Only
```typescript
// In browser console
localStorage.setItem('tenant', '');
// Then refresh page - will redirect to login
```

### Backend Only
```bash
# As Django superuser
python manage.py shell
>>> from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
>>> # Blacklist all outstanding tokens
>>> for token in OutstandingToken.objects.all():
...     BlacklistedToken.objects.get_or_create(token=token)
```

### Complete Reset
```bash
# 1. Clear browser cookies
DevTools → Application → Storage → Clear all

# 2. Logout via backend (invalidates tokens)
POST /api/v1/users/auth/logout/

# 3. Login again (fresh tokens)
```

---

## Architecture Decision: Why httpOnly Cookies?

Your system uses **httpOnly cookies** instead of Authorization headers because:

| Aspect | httpOnly Cookie | Authorization Header |
|--------|-----------------|----------------------|
| XSS Protection | ✅ High (JS can't access) | ❌ Low (JS reads from memory) |
| CSRF Protection | ✅ Requires CSRF token | ❌ Requires custom header |
| Refresh Handling | ✅ Automatic (browser sends) | ❌ Manual (JS must handle) |
| Mobile Apps | ⚠️ Works but awkward | ✅ Standard |
| API Tools (curl) | ⚠️ Needs `-b` flag | ✅ Standard |
| Security Standards | ✅ OWASP recommended | ⚠️ Less preferred |

---

## Key Files Reference

| File | Purpose |
|------|---------|
| [frontend/lib/api.ts](frontend/lib/api.ts) | Axios setup, request/response interceptors, auto refresh |
| [backend/core/tenancy/jwt_authentication.py](backend/core/tenancy/jwt_authentication.py) | Token validation, tenant verification |
| [backend/core/shop_users/views.py#L236-L284](backend/core/shop_users/views.py#L236-L284) | Token refresh endpoint |
| [backend/core/shop_users/views.py#L400-L455](backend/core/shop_users/views.py#L400-L455) | Login endpoint |
| [backend/core/shop_users/views.py#L673-L720](backend/core/shop_users/views.py#L673-L720) | Signup endpoint |
| [backend/core/core/settings.py#L129-L150](backend/core/core/settings.py#L129-L150) | JWT configuration |

---

## Still Having Issues?

1. **Check the logs** - JWT authentication logs everything
2. **Open DevTools** - See cookies and network requests
3. **Test manually** - Use curl to test endpoints
4. **Read error message** - Backend returns specific error text
5. **Review architecture** - See [JWT_TOKEN_HANDLING_GUIDE.md](JWT_TOKEN_HANDLING_GUIDE.md)
6. **Check diagrams** - See [JWT_TOKEN_FLOW_DIAGRAMS.md](JWT_TOKEN_FLOW_DIAGRAMS.md)

