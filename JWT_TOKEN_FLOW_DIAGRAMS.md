# JWT Token Error Recovery Flow Diagram

## 1. Happy Path - Token Valid

```
┌─────────────────────────────────────────────────────────────┐
│ User Makes Request to Protected Endpoint                     │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ↓
┌──────────────────────────────────────┐
│ Frontend axios interceptor           │
│ Adds withCredentials: true           │
│ (access_token sent in cookie)        │
└──────────────────────┬───────────────┘
                       │
                       ↓
┌──────────────────────────────────────┐
│ Backend TenantJWTAuthentication      │
│ Step 1: Get token from cookie        │
│ Step 2: Validate signature & exp     │
│ Step 3: Get user from DB             │
│ Step 4: Validate tenant context      │
└──────────────────────┬───────────────┘
                       │
                       ↓ ✅ All valid
┌──────────────────────────────────────┐
│ Request Proceeds                      │
│ response.status = 200                 │
└──────────────────────────────────────┘
```

---

## 2. Token Expired - Automatic Refresh

```
┌────────────────────────────────────────────────────┐
│ User Makes Request to Protected Endpoint            │
│ (access_token in cookie is EXPIRED)                │
└─────────────────────┬──────────────────────────────┘
                      │
                      ↓
┌─────────────────────────────────────────────────────┐
│ Backend TenantJWTAuthentication                      │
│ AccessToken(token) raises TokenError               │
│ (exp claim in past)                                 │
└─────────────────────┬──────────────────────────────┘
                      │
                      ↓ TokenError → AuthenticationFailed
┌─────────────────────────────────────────────────────┐
│ Response: 401 Unauthorized                          │
└─────────────────────┬──────────────────────────────┘
                      │
                      ↓
┌─────────────────────────────────────────────────────┐
│ Frontend axios response interceptor                  │
│ Catches 401                                         │
│ Checks:                                             │
│  - Not already retried? ✓                          │
│  - Not logging out? ✓                              │
│  - Not a status check? ✓                           │
└─────────────────────┬──────────────────────────────┘
                      │
                      ↓
┌─────────────────────────────────────────────────────┐
│ Frontend calls:                                      │
│ POST /api/users/auth/token/refresh/                │
│ (refresh_token sent in cookie)                      │
└─────────────────────┬──────────────────────────────┘
                      │
                      ↓
┌─────────────────────────────────────────────────────┐
│ Backend CookieTokenRefreshView                       │
│ Step 1: Get refresh_token from cookie              │
│ Step 2: Validate with RefreshToken()               │
│ Step 3: Generate new access_token                  │
│ Step 4: Set new tokens in httpOnly cookies         │
└─────────────────────┬──────────────────────────────┘
                      │
                      ↓ ✅ Refresh successful
┌─────────────────────────────────────────────────────┐
│ Response: 200 OK                                    │
│ (new access_token in cookie)                        │
└─────────────────────┬──────────────────────────────┘
                      │
                      ↓
┌─────────────────────────────────────────────────────┐
│ Frontend retries original request                    │
│ (with new access_token in cookie)                   │
└─────────────────────┬──────────────────────────────┘
                      │
                      ↓
┌─────────────────────────────────────────────────────┐
│ Backend TenantJWTAuthentication                      │
│ Token validation succeeds ✅                        │
└─────────────────────┬──────────────────────────────┘
                      │
                      ↓
┌─────────────────────────────────────────────────────┐
│ Request Proceeds                                    │
│ response.status = 200                               │
└─────────────────────────────────────────────────────┘
```

---

## 3. Both Tokens Expired - User Must Login

```
┌────────────────────────────────────────────────────┐
│ User Makes Request to Protected Endpoint            │
│ (both access_token AND refresh_token are EXPIRED)  │
└─────────────────────┬──────────────────────────────┘
                      │
                      ↓
┌─────────────────────────────────────────────────────┐
│ Backend returns: 401 Unauthorized                    │
└─────────────────────┬──────────────────────────────┘
                      │
                      ↓
┌─────────────────────────────────────────────────────┐
│ Frontend attempts token refresh:                     │
│ POST /api/users/auth/token/refresh/                │
│ (refresh_token in cookie is also EXPIRED)          │
└─────────────────────┬──────────────────────────────┘
                      │
                      ↓
┌─────────────────────────────────────────────────────┐
│ Backend CookieTokenRefreshView                       │
│ RefreshToken(refresh_token) raises TokenError      │
│ (exp claim in past)                                │
└─────────────────────┬──────────────────────────────┘
                      │
                      ↓
┌─────────────────────────────────────────────────────┐
│ Response: 401 Unauthorized                          │
│ "Invalid or expired refresh token"                  │
└─────────────────────┬──────────────────────────────┘
                      │
                      ↓
┌─────────────────────────────────────────────────────┐
│ Frontend response interceptor catches 401           │
│ Calls clearAuthData()                               │
│  - Clears CSRF token cache                          │
│  - Clears rate limit cache                          │
│ Redirects to /login page                            │
└─────────────────────┬──────────────────────────────┘
                      │
                      ↓
┌─────────────────────────────────────────────────────┐
│ User Sees Login Form                                │
│ ✅ Can enter credentials and login                 │
│ ✅ No JWT required to call login endpoint          │
│    (public endpoint: AllowAny)                      │
└─────────────────────────────────────────────────────┘
```

---

## 4. Token Completely Invalid (Corrupted/Tampered)

```
┌───────────────────────────────────────────────────────┐
│ User Makes Request to Protected Endpoint              │
│ (access_token is CORRUPTED/TAMPERED)                │
└──────────────────────┬────────────────────────────────┘
                       │
                       ↓
┌──────────────────────────────────────────────────────┐
│ Backend TenantJWTAuthentication                      │
│ AccessToken(token) is called                        │
│ JWT signature verification FAILS                    │
│ (token was modified, or wrong SECRET_KEY)           │
└──────────────────────┬───────────────────────────────┘
                       │
                       ↓
┌──────────────────────────────────────────────────────┐
│ TokenBackendError: "Token is invalid or expired"     │
│ Converted to InvalidToken exception                  │
└──────────────────────┬───────────────────────────────┘
                       │
                       ↓
┌──────────────────────────────────────────────────────┐
│ TenantJWTAuthentication catches exception            │
│ Raises AuthenticationFailed                          │
└──────────────────────┬───────────────────────────────┘
                       │
                       ↓
┌──────────────────────────────────────────────────────┐
│ Response: 401 Unauthorized                           │
│ Message: "Token validation error"                    │
└──────────────────────┬───────────────────────────────┘
                       │
                       ↓
┌──────────────────────────────────────────────────────┐
│ Frontend Interceptor                                 │
│ Attempts token refresh (same as #3 above)           │
│ If refresh also fails: Redirect to login            │
│ ✅ User can login (public endpoint)                 │
└──────────────────────────────────────────────────────┘
```

---

## 5. Multiple 401s - Request Queuing

```
┌──────────────────────────────────────┐
│ Request 1 to /api/users/               │
│ Returns 401                            │
└─────────────────────┬──────────────────┘
                      │
                      ↓ isRefreshing = true
┌──────────────────────────────────────┐
│ Request 2 to /api/tenants/             │
│ Also gets 401                          │
│ Sees isRefreshing = true               │
│ Don't call refresh again - QUEUE it    │
└─────────────────────┬──────────────────┘
                      │
                      ↓
┌──────────────────────────────────────┐
│ failedQueue = [Request1, Request2]     │
│ Waiting for token refresh to complete  │
└─────────────────────┬──────────────────┘
                      │
                      ↓
┌──────────────────────────────────────┐
│ Request 1: POST /token/refresh/        │
│ Succeeds with new token                │
│ isRefreshing = false                   │
└─────────────────────┬──────────────────┘
                      │
                      ↓
┌──────────────────────────────────────┐
│ processQueue() called                  │
│ Retries Request 1 and Request 2       │
│ Both succeed with new token            │
└──────────────────────────────────────┘

Result: Only ONE /token/refresh/ call
        Multiple endpoints waiting
        All retry together when done
```

---

## 6. Login Flow - Public Endpoint

```
┌─────────────────────────────────────┐
│ User Navigates to /login page         │
│ Frontend checks isAuthenticated()      │
└──────────────┬──────────────────────┘
               │
               ↓
┌──────────────────────────────────────┐
│ GET /api/v1/users/auth/profile/      │
│ (status check - no auth required)    │
└──────────────┬──────────────────────┘
               │
               ↓ (always returns 401 if no token)
┌──────────────────────────────────────┐
│ Response: 401 - Expected              │
│ (Frontend suppresses this error)      │
└──────────────┬──────────────────────┘
               │
               ↓
┌──────────────────────────────────────┐
│ Show Login Form                       │
│ User enters email + password          │
└──────────────┬──────────────────────┘
               │
               ↓
┌───────────────────────────────────────────────┐
│ POST /api/v1/users/auth/login/                │
│ {                                              │
│   "username": "user@example.com",              │
│   "password": "password123",                   │
│   "tenant_slug": "my-shop"                     │
│ }                                              │
│ ✅ NO JWT REQUIRED (public endpoint)          │
└──────────────┬────────────────────────────────┘
               │
               ↓
┌────────────────────────────────────────────────┐
│ Backend UnifiedLoginView                       │
│ Step 1: Validate credentials                   │
│ Step 2: Find user in tenant DB                 │
│ Step 3: Generate JWT with tenant_id in claims │
│ Step 4: Set access_token and refresh_token     │
│         in httpOnly cookies                    │
└──────────────┬────────────────────────────────┘
               │
               ↓
┌────────────────────────────────────────────────┐
│ Response: 200 OK                                │
│ {                                               │
│   "access": "eyJhbGciOiJIUzI1NiIs...",         │
│   "refresh": "eyJhbGciOiJIUzI1NiIs...",        │
│   "tenant_slug": "my-shop",                    │
│   "user": { ... }                              │
│ }                                               │
│ Headers: Set-Cookie: access_token=... (httpOnly)│
│          Set-Cookie: refresh_token=... (httpOnly│
└──────────────┬────────────────────────────────┘
               │
               ↓
┌────────────────────────────────────────────────┐
│ Frontend                                        │
│ Stores tokens (already in cookies)              │
│ Sets localStorage['tenant'] = 'my-shop'         │
│ Redirects to /dashboard                         │
└──────────────┬────────────────────────────────┘
               │
               ↓
┌────────────────────────────────────────────────┐
│ GET /dashboard                                 │
│ access_token in cookie sent automatically       │
│ Backend validates token → Success               │
│ Dashboard displays user data                    │
└────────────────────────────────────────────────┘
```

---

## 7. Token Validation Decision Tree

```
                    Request Received
                          │
                          ↓
           ┌──────────────────────────┐
           │ Is this a public endpoint?│
           │ (login, signup, csrf)     │
           └───┬──────────────┬────────┘
           YES │              │ NO
               ↓              ↓
            ┌─────────┐  ┌──────────────────────────┐
            │ Skip    │  │ Get access_token from    │
            │ Auth    │  │ cookie or header?        │
            └─────────┘  └───┬──────────────┬───────┘
                          YES│              │
                             ↓              ↓ NO
                        ┌──────────────┐ ┌──────────────────┐
                        │ Access Token │ │ Return None      │
                        │ (string)     │ │ (Anonymous user) │
                        └───┬──────────┘ │Allow public      │
                            │            │access            │
                            ↓            └──────────────────┘
                    ┌──────────────────────────┐
                    │ Validate token:          │
                    │ - Signature check        │
                    │ - Expiration check (exp)│
                    │ - Token not blacklisted  │
                    └───┬────────────┬─────────┘
                    VALID│           │ INVALID
                        ↓            ↓
                  ┌─────────────────────────────┐
                  │ Raise AuthenticationFailed  │
                  │ (401 to frontend)           │
                  │ → Frontend attempts refresh │
                  │ → If refresh fails: login   │
                  └─────────────────────────────┘
                        │
                        ↓
                   ┌──────────────┐
                   │ Get User from │
                   │ token claims: │
                   │ - user_id     │
                   │ - tenant_id   │
                   └───┬───────┬──┘
                   FOUND│      │ NOT FOUND
                       ↓      ↓
                   ┌──────┐ ┌─────────────────────┐
                   │Return│ │ Raise               │
                   │User  │ │ AuthenticationFailed│
                   └──────┘ │ (401)               │
                            └─────────────────────┘
```

---

## 8. Recovery Path Summary

```
ANY JWT PROBLEM
(expired, invalid, corrupted, missing)
        │
        ↓
    401 Returned
        │
        ↓
Frontend Catches 401
        │
        ├─ Is it a status check?
        │  └─ Yes: Suppress, show login form
        │
        ├─ Is it a public endpoint?
        │  └─ Yes: Allow, no refresh needed
        │
        └─ Is it a protected endpoint?
           └─ Yes: Attempt token refresh
               │
               ├─ Refresh succeeds?
               │  └─ Yes: Retry request, continue
               │
               └─ Refresh fails?
                  └─ No: Redirect to /login
                     (public endpoint - always accessible)
                     User can:
                     ✓ Login with credentials
                     ✓ Create new tenant (signup)
```

---

## 9. Cookie Lifecycle

```
┌─────────────────────────────────────────────┐
│ LOGIN or SIGNUP Response from Backend        │
│ Set-Cookie: access_token=...                │
│   max_age=3600 (1 hour)                      │
│   httponly=true                              │
│   Path=/                                     │
│   SameSite=Lax                               │
│                                              │
│ Set-Cookie: refresh_token=...               │
│   max_age=604800 (7 days)                    │
│   httponly=true                              │
│   Path=/                                     │
│   SameSite=Lax                               │
└────────┬────────────────────────────────────┘
         │
         ↓
    Browsers stores in httpOnly cookies
    (Not accessible to JavaScript)
         │
         ↓
┌────────────────────────────────────────┐
│ Every request (with withCredentials)    │
│ Cookies sent automatically:             │
│ Cookie: access_token=...                │
│ Cookie: refresh_token=...               │
│ (Browser adds automatically)             │
│ (JavaScript cannot read them)            │
└────────┬─────────────────────────────────┘
         │
         ├─ Protected Endpoint (1 hour later)
         │  └─ access_token expired
         │     └─ 401 returned
         │        └─ Call refresh endpoint
         │           └─ New tokens set in cookies
         │
         └─ No Activity (7 days)
            └─ refresh_token expires
               └─ Next Access: 401
                  └─ Refresh fails
                     └─ Redirect to login
                        └─ User must login again
```

